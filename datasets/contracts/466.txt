#![cfg_attr(not(feature = "std"), no_std)]

extern crate alloc;

use ink_lang as ink;
use pink_extension as pink;

#[ink::contract(env = pink_extension::PinkEnvironment)]
mod sub_transactor {
    use super::pink;
    use alloc::{str::FromStr, string::String, string::ToString, vec::Vec};
    use hex_literal::hex;
    use ink_storage::traits::{PackedLayout, SpreadLayout};
    use paralib::ToArray;
    use pink::{chain_extension::signing::sign, http_post, PinkEnvironment};
    use pink_web3::transports::resolve_ready;
    use primitive_types::H256;
    use scale::{Decode, Encode};

    #[ink(storage)]
    pub struct SubTransactor {
        rpc_node: String,
    }

    impl SubTransactor {
        #[ink(constructor)]
        pub fn default() -> Self {
            Self {
                rpc_node: "http://localhost:9933".into(),
            }
        }

        #[ink(message)]
        pub fn get_genesis_hash(&self) {
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
            ink_env::test::register_contract::<SubTransactor>(hash1.as_ref());

            // Deploy Transactor(phat contract)
            let mut transactor = SubTransactorRef::default()
                .code_hash(hash1)
                .endowment(0)
                .salt_bytes([0u8; 0])
                .instantiate()
                .expect("failed to deploy SubTransactor");

            transactor.get_genesis_hash();
        }
    }
}
