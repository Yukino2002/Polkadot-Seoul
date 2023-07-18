#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
pub mod factory_teasury_manager {

    use treasury_manager::TreasuryManagerRef;

    use ink_lang::codegen::Env;
    use polkadot_europe::traits::factory::*;

    use ink_lang::ToAccountId;

    use ink_prelude::{vec, vec::Vec};
    use ink_storage::traits::{PackedLayout, SpreadLayout};
    use ink_storage::traits::{SpreadAllocate, StorageLayout};

    use openbrush::{
        contracts::{access_control::*, traits::errors::PSP22Error, traits::psp22::PSP22Ref},
        modifiers,
        storage::Mapping,
        traits::{Storage, String},
    };

    //Treasury Manager
    // 0x953eaa1a62a4917abbec2361cbc491fa06d18361fe5fc1ca8eb454bc7be7ece0

    #[ink(storage)]
    #[derive(Default, SpreadAllocate, Storage)]
    pub struct FactoryTeasuryManager {
        #[storage_field]
        access: access_control::Data,
        admin: AccountId,
        version: u32,
        treasury_manager_code_hash: Hash,
        treasury_manager_owners_map: Mapping<AccountId, AccountId>, //owner=>treasury_manager
        treasury_manager_owners_vec: Vec<AccountId>,
    }

    const ADMIN: RoleType = ink_lang::selector_id!("ADMIN");

    impl AccessControl for FactoryTeasuryManager {}

    impl Factory for FactoryTeasuryManager {
        //
        #[ink(message, payable)]
        fn launch_treasury_manager(
            &mut self,
            contract_administrator: AccountId,
            contract_manager: AccountId,
            treasury_token_symbol: String,
            treasury_token_address: AccountId,
            usdt_token_address: AccountId,
            oracle_dex_address: AccountId,
            liabilities_threshold_level: u8,
        ) {
            let total_balance = self.env().balance();
            let salt = self.version.to_be_bytes();
            let caller = self.env().caller();

            if !self.treasury_manager_owners_vec.contains(&caller) {
                self.treasury_manager_owners_vec.push(caller);
            }

            let new_treasury_manager = TreasuryManagerRef::new(
                contract_administrator,
                contract_manager,
                treasury_token_symbol,
                treasury_token_address,
                usdt_token_address,
                oracle_dex_address,
                liabilities_threshold_level,
            )
            .endowment(total_balance / 2)
            .code_hash(self.treasury_manager_code_hash)
            .salt_bytes(salt)
            .instantiate()
            .unwrap_or_else(|error| {
                panic!(
                    "failed at instantiating the treasury manager contract: {:?}",
                    error
                )
            });

            let contract_address = new_treasury_manager.to_account_id();
            self.treasury_manager_owners_map
                .insert(&caller, &contract_address);
            self.version += 1;
        }

        #[ink(message)]
        fn get_owners(&self) -> Vec<AccountId> {
            self.treasury_manager_owners_vec.clone()
        }

        #[ink(message)]
        fn get_owner_contract_address(&self, owner: AccountId) -> AccountId {
            self.treasury_manager_owners_map
                .get(&owner)
                .unwrap_or_default()
        }
    }

    impl FactoryTeasuryManager {
        //
        #[ink(constructor)]
        pub fn new(treasury_manager_code_hash: Hash) -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut Self| {
                let caller = instance.env().caller();
                instance._init_with_admin(caller);
                instance
                    .grant_role(ADMIN, caller)
                    .expect("Should grant the ADMIN role");
                instance.admin = caller;
                instance.version = 0;
                instance.treasury_manager_code_hash = treasury_manager_code_hash;
                instance.treasury_manager_owners_map = Default::default();
                instance.treasury_manager_owners_vec = Default::default();
            })
        }

        #[ink(message)]
        pub fn get_treasury_manager_code_hash(&self) -> Hash {
            self.treasury_manager_code_hash
        }

        #[ink(message)]
        pub fn get_version(&self) -> u32 {
            self.version
        }

        #[ink(message)]
        pub fn get_admin(&self) -> AccountId {
            self.admin
        }

        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn set_treasury_manager_code_hash(
            &mut self,
            new_treasury_manager_code_hash: Hash,
        ) -> Result<(), AccessControlError> {
            self.treasury_manager_code_hash = new_treasury_manager_code_hash;
            self.version = 0;
            Ok(())
        }
    }
}
