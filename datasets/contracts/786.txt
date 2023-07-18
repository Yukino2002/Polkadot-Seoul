#![cfg_attr(not(feature = "std"), no_std)]

extern crate alloc;

use ink_lang as ink;

#[ink::contract(env = pink_extension::PinkEnvironment)]
mod evm_transator {
    use alloc::{string::String, string::ToString, vec::Vec};
    use ink_storage::traits::{PackedLayout, SpreadLayout};
    use paralib::ToArray;
    use pink_web3::ethabi::{Bytes, Uint};
    use pink_web3::keys::pink::KeyPair;
    use pink_web3::signing::Key;
    use scale::{Decode, Encode};

    #[ink(storage)]
    pub struct EvmTransactor {
        owner: AccountId,
        key: [u8; 32],
        config: Option<Config>,
    }

    #[derive(Encode, Decode, Debug, PackedLayout, SpreadLayout)]
    #[cfg_attr(
        feature = "std",
        derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout)
    )]
    struct Config {
        rpc: String,
        evm_contract: [u8; 20],
    }

    #[derive(Encode, Decode, Debug, PartialEq, Eq)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        BadOrigin,
        NotConfigurated,
        KeyRetired,
        KeyNotRetiredYet,
        UpstreamFailed,
        BadAbi,
        FailedToGetStorage,
        FailedToDecodeStorage,
        FailedToEstimateGas,
    }

    type Result<T> = core::result::Result<T, Error>;

    impl EvmTransactor {
        #[ink(constructor)]
        pub fn default() -> Self {
            Self {
                owner: Self::env().caller(),
                config: None,
                key: Self::key_pair().private_key(),
            }
        }

        /// Configures the transactor
        #[ink(message)]
        pub fn config(&mut self, rpc: String, evm_contract: H160) -> Result<()> {
            self.ensure_owner()?;
            self.config = Some(Config {
                rpc,
                evm_contract: evm_contract.into(),
            });
            Ok(())
        }

        /// Import a private key to override the interior account
        #[ink(message)]
        pub fn set_account(&mut self, private_key: Vec<u8>) -> H160 {
            self.key = private_key.to_array();
            self.wallet()
        }

        /// Returns the wallet address the transactor used to submit transactions
        #[ink(message)]
        pub fn wallet(&self) -> H160 {
            let keypair: KeyPair = self.key.into();
            keypair.address()
        }

        /// Returns BadOrigin error if the caller is not the owner
        fn ensure_owner(&self) -> Result<()> {
            if self.env().caller() == self.owner {
                Ok(())
            } else {
                Err(Error::BadOrigin)
            }
        }

        /// Derives the key pair on the fly
        fn key_pair() -> pink_web3::keys::pink::KeyPair {
            pink_web3::keys::pink::KeyPair::derive_keypair(b"rollup-transactor")
        }
        /// Polls message from the target EVM contract
        #[ink(message)]
        pub fn message(&self) -> Result<String> {
            let Config { rpc, evm_contract } =
                self.config.as_ref().ok_or(Error::NotConfigurated)?;

            let contract = EvmContractClient::connect(rpc, evm_contract.clone().into())?;

            contract.message()
        }

        /// Sends message to the target EVM contract
        #[ink(message)]
        pub fn deposit(
            &self,
            token_rid: H256,
            amount: Uint,
            recipient_address: Vec<u8>,
        ) -> Result<H256> {
            let Config { rpc, evm_contract } =
                self.config.as_ref().ok_or(Error::NotConfigurated)?;

            let contract = EvmContractClient::connect(rpc, evm_contract.clone().into())?;

            let chain_id = 1;

            let tx = contract.deposit(
                self.key.into(),
                chain_id,
                token_rid,
                amount,
                recipient_address,
            )?;
            Ok(tx)
        }
    }

    use pink_web3::api::{Eth, Namespace};
    use pink_web3::contract::tokens::Tokenize;
    use pink_web3::contract::{Contract, Options};
    use pink_web3::ethabi::Token;
    use pink_web3::transports::{resolve_ready, PinkHttp};
    use pink_web3::types::{Res, H160, H256};

    /// The client to submit transaction to the Evm evm_contract contract
    struct EvmContractClient {
        contract: Contract<PinkHttp>,
    }

    impl EvmContractClient {
        fn connect(rpc: &String, address: H160) -> Result<EvmContractClient> {
            let eth = Eth::new(PinkHttp::new(rpc));
            let contract =
                Contract::from_json(eth, address, include_bytes!("../res/evm_contract.abi.json"))
                    .or(Err(Error::BadAbi))?;

            Ok(EvmContractClient { contract })
        }

        /// Calls the EVM contract function `message`
        fn message(&self) -> Result<String> {
            let a: String = resolve_ready(self.contract.query(
                "_resourceIDToHandlerAddress",
                (),
                None,
                Options::default(),
                None,
            ))
            .expect("FIXME: query failed");
            Ok(a)
        }

        /// Calls the EVM contract function `update`,
        /// returns the transaction id if it succeed
        ///
        /// # Arguments
        ///
        /// * `dest_chain_id` - ID of chain deposit originated from.
        /// * `token_rid` - resource id used to find address of token handler to be used for deposit
        /// * `data` - Addition data to be passed to special handler
        ///
        /// # Examples
        ///
        /// ```
        ///
        /// ```
        fn deposit(
            &self,
            signer: KeyPair,
            dest_chain_id: u8,
            token_rid: H256,
            amount: Uint,
            recipient_address: Bytes,
        ) -> Result<H256> {
            let data = Self::compose_deposite_data(amount, recipient_address);
            let params = (dest_chain_id, token_rid, data);
            // Estiamte gas before submission
            let gas = resolve_ready(self.contract.estimate_gas(
                "deposit",
                params.clone(),
                signer.address(),
                Options::default(),
            ))
            .expect("FIXME: failed to estiamte gas");

            dbg!(gas);

            // Actually submit the tx (no guarantee for success)
            let tx_id = resolve_ready(self.contract.signed_call(
                "deposit",
                params,
                Options::with(|opt| opt.gas = Some(gas)),
                signer,
            ))
            .expect("FIXME: submit failed");
            Ok(tx_id)
        }

        /// Composes the `data` argument to the chainbridge `deposit` function
        ///
        ///
        /// The signature of the solidity `deposit` function is as follows:
        ///
        /// ```
        /// function deposit(uint8 destinationChainID,
        ///     bytes32 resourceID,
        ///     bytes calldata data)
        /// external payable whenNotPaused;
        /// ```
        ///  
        /// `Data` passed into the function should be constructed as follows:
        /// * `amount`                      uint256     bytes   0 - 32
        /// * `recipientAddress length`     uint256     bytes  32 - 64
        /// * `recipientAddress`            bytes       bytes  64 - END
        fn compose_deposite_data(amount: Uint, recipient_address: Bytes) -> Bytes {
            let ra_len = recipient_address.len();
            [
                amount.to_be_fixed_bytes(),
                ra_len.to_be_fixed_bytes(),
                recipient_address,
            ]
            .concat()
        }
    }

    trait ToBeBytes {
        fn to_be_fixed_bytes(&self) -> Bytes;
    }

    impl ToBeBytes for Uint {
        fn to_be_fixed_bytes(&self) -> Bytes {
            let mut a: [u8; 32] = [0; 32];
            self.to_big_endian(&mut a);
            a.into()
        }
    }

    /// FIXME: can be lossy
    impl ToBeBytes for usize {
        fn to_be_fixed_bytes(&self) -> Bytes {
            let uint = Uint::from(*self as u32);
            uint.to_be_fixed_bytes()
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use dotenv::dotenv;
        use hex_literal::hex;
        use ink_lang as ink;

        #[ink::test]
        fn it_works() {
            dotenv().ok();
            use std::env;

            pink_extension_runtime::mock_ext::mock_all_ext();
            pink_extension::chain_extension::mock::mock_derive_sr25519_key(|_| {
                hex!["4c5d4f158b3d691328a1237d550748e019fe499ebf3df7467db6fa02a0818821"].to_vec()
            });

            // Register contracts
            let hash1 = ink_env::Hash::try_from([10u8; 32]).unwrap();
            ink_env::test::register_contract::<EvmTransactor>(hash1.as_ref());

            // Deploy Transactor(phat contract)
            let mut transactor = EvmTransactorRef::default()
                .code_hash(hash1)
                .endowment(0)
                .salt_bytes([0u8; 0])
                .instantiate()
                .expect("failed to deploy EvmTransactor");

            let rpc =
                "https://eth-goerli.g.alchemy.com/v2/lLqSMX_1unN9Xrdy_BB9LLZRgbrXwZv2".to_string();
            let bridge_contract_addr: H160 =
                hex!("056c0e37d026f9639313c281250ca932c9dbe921").into();

            dbg!(&bridge_contract_addr);
            dbg!(&rpc);
            transactor.config(rpc, bridge_contract_addr).unwrap();
            let secret_key = env::vars().find(|x| x.0 == "SECRET_KEY").unwrap().1;
            let secret_bytes = hex::decode(secret_key).unwrap();

            transactor.set_account(secret_bytes);

            assert_eq!(
                transactor.wallet(),
                hex!("25d0aFBC1Ad376136420aF0B5Aa74123359b9b77").into()
            );

            let token_rid: H256 =
                hex!("00e6dfb61a2fb903df487c401663825643bb825d41695e63df8af6162ab145a6").into();
            // 1 PHA
            let amount = Uint::from(1_000_000_000_000_000_000_u128);
            let recipient_address: Bytes =
                hex!("000101008eaf04151687736326c9fea17e25fc5287613693c912909cb226aa4794f26a48")
                    .into();
            let tx_id = transactor
                .deposit(token_rid, amount, recipient_address)
                .unwrap();
            // https://goerli.etherscan.io/tx/0xc064af26458ca91b86af128ba86d9cdcee51397cebebc714df8fc182b298ab11
            dbg!(tx_id);
        }
    }
}
