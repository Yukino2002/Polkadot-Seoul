#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
pub mod bhc22_contract {
    use bho_common::traits::bhc22::extensions::{
        burnable::*,
        mintable::*,
    };
    use ink_lang::codegen::{
        EmitEvent,
        Env,
    };
    use ink_prelude::{
        string::String,
        vec::Vec,
    };
    use ink_storage::traits::SpreadAllocate;
    use openbrush::{
        contracts::{
            ownable::*,
            psp22::extensions::metadata::*,
        },
        modifiers,
    };

    /// Event emitted when a token transfer occurs.
    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        from: Option<AccountId>,
        #[ink(topic)]
        to: Option<AccountId>,
        value: Balance,
    }

    #[ink(event)]
    pub struct Approval {
        #[ink(topic)]
        owner: AccountId,
        #[ink(topic)]
        spender: AccountId,
        value: Balance,
    }

    #[ink(storage)]
    #[derive(Default, SpreadAllocate, PSP22Storage, PSP22MetadataStorage, OwnableStorage)]
    pub struct BHC22Contract {
        #[PSP22StorageField]
        psp22: PSP22Data,
        #[PSP22MetadataStorageField]
        psp22_metadata: PSP22MetadataData,
        #[OwnableStorageField]
        ownable: OwnableData,
    }

    impl PSP22Internal for BHC22Contract {
        fn _emit_transfer_event(&self, _from: Option<AccountId>, _to: Option<AccountId>, _amount: Balance) {
            self.env().emit_event(Transfer {
                from: _from,
                to: _to,
                value: _amount,
            });
        }

        fn _emit_approval_event(&self, _owner: AccountId, _spender: AccountId, _amount: Balance) {
            self.env().emit_event(Approval {
                owner: _owner,
                spender: _spender,
                value: _amount,
            })
        }
    }

    // impl Ownable for BHC22Contract {}

    impl PSP22 for BHC22Contract {}

    impl BHC22Contract {
        #[ink(constructor)]
        pub fn new(name: Option<String>, symbol: Option<String>, decimals: u8, initial_supply: Balance) -> Self {
            ink_lang::utils::initialize_contract(|instance: &mut Self| {
                instance._init_with_metadata(name, symbol, decimals);
                instance
                    ._mint(instance.env().caller(), initial_supply)
                    .expect("Failed to mint initial supply");
                instance._init_with_owner(instance.env().caller());
            })
        }

        #[ink(constructor)]
        pub fn new_with_owner_and_endowments(
            name: Option<String>,
            symbol: Option<String>,
            decimals: u8,
            owner: AccountId,
            endowments: Vec<(AccountId, Balance)>,
        ) -> Self {
            ink_lang::utils::initialize_contract(|instance: &mut Self| {
                instance._init_with_metadata(name, symbol, decimals);
                for endowment in endowments {
                    instance
                        ._mint(endowment.0, endowment.1)
                        .expect("Failed to mint initial endowment");
                }
                instance._init_with_owner(owner);
            })
        }

        fn _init_with_metadata(&mut self, name: Option<String>, symbol: Option<String>, decimals: u8) {
            self.psp22_metadata.name = name;
            self.psp22_metadata.symbol = symbol;
            self.psp22_metadata.decimals = decimals;
        }
    }

    impl BHC22Mintable for BHC22Contract {
        #[ink(message)]
        #[modifiers(only_owner)]
        fn mint(&mut self, account: AccountId, amount: Balance) -> Result<(), PSP22Error> {
            self._mint(account, amount)
        }
    }

    impl BHC22Burnable for BHC22Contract {
        #[ink(message)]
        fn burn(&mut self, account: AccountId, amount: Balance) -> Result<(), PSP22Error> {
            let caller = self.env().caller();
            if caller != account {
                // "Burn from" case
                let allowance = self.allowance(account, caller);
                if allowance < amount {
                    return Err(PSP22Error::InsufficientAllowance)
                }
                self._approve_from_to(account, caller, allowance - amount)?;
            }
            self._burn_from(account, amount)
        }
    }
}
