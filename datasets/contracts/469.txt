#![cfg_attr(not(feature = "std"), no_std)]

mod helpers;

use ink_lang as ink;

#[ink::contract]
mod bridge_cherry_contract {
    const CHER_TOKEN: &'static str = "";

    use crate::helpers::utils::{MultiChainAddrHash, U256};
    use ink_storage::Mapping;

    #[ink(storage)]
    #[derive(ink_storage::traits::SpreadAllocate)]
    pub struct Bridge {
        owner: ink_env::AccountId,
        total_supply: Mapping<MultiChainAddrHash, U256>,
        balances: Mapping<(MultiChainAddrHash, MultiChainAddrHash), U256>,
        allowances: Mapping<(MultiChainAddrHash, MultiChainAddrHash, MultiChainAddrHash), U256>,
    }

    #[ink(event)]
    pub struct BridgeCherryComplex {
        #[ink(topic)]
        token_amount: U256,
        #[ink(topic)]
        recipient: MultiChainAddrHash,
    }

    #[ink(event)]
    pub struct BridgeCherrySimple {
        token_amount: String,
        recipient: String,
    }

    #[ink(event)]
    pub struct BridgeInComplex {
        #[ink(topic)]
        token_address: MultiChainAddrHash,
        #[ink(topic)]
        token_amount: U256,
        #[ink(topic)]
        recipient: MultiChainAddrHash,
        #[ink(topic)]
        from_chain: Option<U256>,
    }

    #[ink(event)]
    pub struct BridgeInSimple {
        token_address: String,
        token_amount: String,
        recipient: String,
        from_chain: Option<String>,
    }

    #[ink(event)]
    pub struct BridgeOutComplex {
        #[ink(topic)]
        token_address: MultiChainAddrHash,
        #[ink(topic)]
        token_amount: U256,
        #[ink(topic)]
        recipient: MultiChainAddrHash,
        #[ink(topic)]
        target_chain: Option<U256>,
    }

    #[ink(event)]
    pub struct BridgeOutSimple {
        token_address: String,
        token_amount: String,
        recipient: String,
        target_chain: Option<String>,
    }

    #[ink(event)]
    pub struct Initiate {
        initiated: bool,
        by: String,
        initial_balance: String,
    }

    #[ink(event)]
    pub struct Approval {
        #[ink(topic)]
        owner: String,
        #[ink(topic)]
        spender: String,
        value_decimal: String,
        value_hex: String,
    }

    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        from: Option<String>,
        #[ink(topic)]
        to: Option<String>,
        value_decimal: String,
        value_hex: String,
    }

    #[derive(scale::Encode, scale::Decode, scale_info::TypeInfo)]
    pub enum BridgeContractError {
        ErrorApproving(String),
        ErrorTransferringFrom(String),
        ErrorTransferringTo(String),
        ErrorTransferringFromTo(String),
    }

    impl Bridge {
        #[ink(constructor)]
        pub fn new(initial_token: MultiChainAddrHash, initial_supply: U256) -> Self {
            ink_lang::utils::initialize_contract(|contract| {
                Self::new_init(contract, initial_token, initial_supply)
            })
        }

        fn new_init(&mut self, initial_token: MultiChainAddrHash, initial_supply: U256) {
            let caller = self.env().caller();
            let caller_arr: &[u8] = caller.as_ref();

            let addr_multi: MultiChainAddrHash = caller_arr.into();

            self.balances
                .insert((&addr_multi, &initial_token), &initial_supply);
            self.total_supply.insert(initial_token, &initial_supply);

            Self::env().emit_event(Initiate {
                initiated: true,
                by: addr_multi.to_string(),
                initial_balance: initial_supply.to_decimal(),
            });
        }

        #[ink(message)]
        pub fn get_balance_of(&self, token: String, owner: String) -> Option<U256> {
            let mcah: MultiChainAddrHash = owner.into();
            let tcah: MultiChainAddrHash = token.into();

            self.balances.get((mcah, tcah))
        }

        #[ink(message)]
        pub fn get_allowance_of(
            &self,
            owner: String,
            spender: String,
            token: String,
        ) -> Option<U256> {
            let mcah_owner: MultiChainAddrHash = owner.into();
            let mcah_spender: MultiChainAddrHash = spender.into();
            let tcah: MultiChainAddrHash = token.into();

            self.allowances.get((mcah_owner, mcah_spender, tcah))
        }

        fn transfer_from_to(
            &mut self,
            from: &MultiChainAddrHash,
            to: &MultiChainAddrHash,
            token: &MultiChainAddrHash,
            value: &U256,
        ) -> Result<(), BridgeContractError> {
            let from_balance = self
                .get_balance_of(token.to_string(), from.clone().to_string())
                .unwrap();

            if U256::a_greater_than_b(&value, &from_balance) {
                return Err(BridgeContractError::ErrorTransferringFromTo(
                    "Not enough funds".to_string(),
                ));
            }

            let sub_from = U256::subtract_b_from_a(&from_balance, &value);

            self.balances.insert((from, token), &sub_from);

            let to_balance = self
                .get_balance_of(to.to_string(), token.to_string())
                .unwrap();

            let sub_to = U256::subtract_b_from_a(&to_balance, &value);

            self.balances.insert((to, token), &sub_to);

            Self::env().emit_event(Transfer {
                from: Some(from.to_string()),
                to: Some(to.to_string()),
                value_decimal: value.to_decimal(),
                value_hex: value.to_hex(),
            });

            Ok(())
        }

        pub fn transfer_from(
            &mut self,
            from: &MultiChainAddrHash,
            to: &MultiChainAddrHash,
            token: &MultiChainAddrHash,
            value: &U256,
        ) -> Result<(), BridgeContractError> {
            let caller = self.env().caller();

            let caller_arr: &[u8] = caller.as_ref();

            let owner: MultiChainAddrHash = caller_arr.into();

            let allowance =
                self.get_allowance_of(from.to_string(), owner.to_string(), token.to_string());

            match allowance {
                Some(all) => {
                    if U256::a_greater_than_b(value, &all) {
                        return Err(BridgeContractError::ErrorTransferringFrom(
                            "Insufficient Allowance".to_string(),
                        ));
                    }

                    self.transfer_from_to(from, to, token, value)?;

                    let sub = U256::subtract_b_from_a(&all, value);

                    self.allowances.insert((from, to, token), &sub);
                }
                None => {
                    return Err(BridgeContractError::ErrorTransferringFrom(
                        "No such allowance".to_string(),
                    ))
                }
            }

            Ok(())
        }

        pub fn transfer(
            &mut self,
            to: &MultiChainAddrHash,
            token: &MultiChainAddrHash,
            value: &U256,
        ) -> Result<(), BridgeContractError> {
            let owner = self.env().caller();
            let owner_ref: &[u8] = owner.as_ref();

            let ohac: MultiChainAddrHash = owner_ref.into();

            self.transfer_from_to(&ohac, to, token, value)
        }

        #[ink(message)]
        pub fn approve(
            &mut self,
            spender: MultiChainAddrHash,
            token: MultiChainAddrHash,
            value: U256,
        ) {
            let owner = self.env().caller();

            let caller_arr: &[u8] = owner.as_ref();

            let owner: MultiChainAddrHash = caller_arr.into();

            self.allowances.insert((&owner, &spender, &token), &value);
            self.env().emit_event(Approval {
                owner: owner.to_string(),
                spender: spender.to_string(),
                value_decimal: value.to_decimal(),
                value_hex: value.to_hex(),
            });
        }

        #[ink(message)]
        pub fn bridge_cherry(
            &mut self,
            token_amount: U256,
            recipient: MultiChainAddrHash,
        ) -> Result<(), BridgeContractError> {
            let token: MultiChainAddrHash = CHER_TOKEN.clone().to_string().into();

            self.transfer(&recipient, &token, &token_amount)?;

            Self::env().emit_event(BridgeCherryComplex {
                token_amount,
                recipient,
            });

            Ok(())
        }

        #[ink(message)]
        pub fn bridge_cherry_string(
            &mut self,
            token_amount_str: String,
            recipient_str: String,
            emit_simple: bool,
        ) -> Result<(), BridgeContractError> {
            let token_amount = token_amount_str.clone().into();
            let recipient = recipient_str.clone().into();

            self.bridge_cherry(token_amount, recipient)?;

            if emit_simple {
                Self::env().emit_event(BridgeCherrySimple {
                    token_amount: token_amount_str,
                    recipient: recipient_str,
                });
            }

            Ok(())
        }

        #[ink(message)]
        pub fn bridge_in(
            &mut self,
            token_address: MultiChainAddrHash,
            token_amount: U256,
            recipient: MultiChainAddrHash,
            from_chain: U256,
        ) -> Result<(), BridgeContractError> {
            self.transfer(&recipient, &token_address, &token_amount)?;

            Self::env().emit_event(BridgeInComplex {
                token_address,
                token_amount,
                recipient,
                from_chain: Some(from_chain),
            });

            Ok(())
        }

        #[ink(message)]
        pub fn bridge_in_string(
            &mut self,
            token_address_str: String,
            token_amount_str: String,
            recipient_str: String,
            from_chain_str: String,
            emit_simple: bool,
        ) -> Result<(), BridgeContractError> {
            let token_address = token_address_str.clone().into();
            let token_amount = token_amount_str.clone().into();
            let recipient: MultiChainAddrHash = recipient_str.clone().into();
            let from_chain = from_chain_str.clone().into();

            self.bridge_in(token_address, token_amount, recipient, from_chain)?;

            let caller = self.env().caller();
            let token_address: MultiChainAddrHash = (caller.as_ref() as &[u8]).into();

            if emit_simple {
                Self::env().emit_event(BridgeInSimple {
                    token_address: token_address.to_string(),
                    token_amount: token_amount_str,
                    recipient: recipient_str,
                    from_chain: Some(from_chain_str),
                });
            }

            Ok(())
        }

        #[ink(message)]
        pub fn bridge_out(
            &mut self,
            token_address: MultiChainAddrHash,
            token_amount: U256,
            target_chain: U256,
        ) -> Result<(), BridgeContractError> {
            let caller = self.env().caller();
            let from: MultiChainAddrHash = (caller.as_ref() as &[u8]).into();

            let contract_hash = self.env().own_code_hash().unwrap();
            let to = (contract_hash.as_ref() as &[u8]).into();

            self.transfer_from(&from, &to, &token_address, &token_amount)?;

            Self::env().emit_event(BridgeOutComplex {
                token_address,
                token_amount,
                recipient: to,
                target_chain: Some(target_chain),
            });

            Ok(())
        }

        #[ink(message)]
        pub fn bridge_out_string(
            &mut self,
            token_address_str: String,
            token_amount_str: String,
            target_chain_str: String,
            emit_simple: bool,
        ) -> Result<(), BridgeContractError> {
            let token_address = token_address_str.clone().into();
            let token_amount = token_amount_str.clone().into();
            let target_chain = target_chain_str.clone().into();

            self.bridge_out(token_address, token_amount, target_chain)?;

            let caller = self.env().caller();
            let recipient: MultiChainAddrHash = (caller.as_ref() as &[u8]).into();

            if emit_simple {
                Self::env().emit_event(BridgeOutSimple {
                    token_address: token_address_str,
                    token_amount: token_amount_str,
                    recipient: recipient.to_string(),
                    target_chain: Some(target_chain_str),
                });
            }

            Ok(())
        }
    }
}
