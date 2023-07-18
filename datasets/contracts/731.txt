#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
mod pallet {

    use polkadot_europe::traits::factory::*;
    use polkadot_europe::traits::tr_manager::*;

    use ink_prelude::{vec, vec::Vec};
    use ink_storage::traits::{SpreadAllocate, StorageLayout};

    use ink_storage::traits::{PackedLayout, SpreadLayout};
    use openbrush::{
        contracts::{access_control::*, traits::errors::PSP22Error, traits::psp22::PSP22Ref},
        modifiers,
        storage::Mapping,
        traits::{Storage, String},
    };

    //
    #[ink(storage)]
    #[derive(Default, SpreadAllocate, Storage)]
    pub struct Pallet {
        #[storage_field]
        access: access_control::Data,
        admin: AccountId,
        factory_addr: AccountId,
        treasury_manager_addr: AccountId,
        treasury_token_address: AccountId,
    }

    const ADMIN: RoleType = ink_lang::selector_id!("ADMIN");

    impl AccessControl for Pallet {}

    impl Pallet {
        //
        #[ink(constructor)]
        pub fn new(factory_address: AccountId, treasury_token_address: AccountId) -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut Self| {
                let caller = instance.env().caller();
                instance._init_with_admin(caller);
                instance
                    .grant_role(ADMIN, caller)
                    .expect("Should grant the ADMIN role");
                instance.admin = caller;
                instance.factory_addr = factory_address;
                instance.treasury_manager_addr = Default::default();
                instance.treasury_token_address = treasury_token_address;
            })
        }

        #[ink(message)]
        pub fn get_treasury_manager_address(&self) -> AccountId {
            self.treasury_manager_addr
        }

        #[ink(message)]
        pub fn get_favtory_address(&self) -> AccountId {
            self.factory_addr
        }

        #[ink(message)]
        pub fn get_admin(&self) -> AccountId {
            self.admin
        }

        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn set_admin_here_and_manager_for_tm(
            &mut self,
            account: AccountId,
        ) -> Result<(), AccessControlError> {
            self.set_treasury_contract_manager(account);

            self.renounce_role(ADMIN, self.admin);
            self.grant_role(ADMIN, account)
                .expect("Should grant admin's role");

            self.admin = account;
            Ok(())
        }

        // *** FACTORY ***/
        ///Launch new treasury_manager
        #[ink(message, payable)]
        #[modifiers(only_role(ADMIN))]
        pub fn launch_treasury_manager(
            &mut self,
            // contract_administrator: AccountId,
            contract_manager: AccountId,
            treasury_token_symbol: String,
            treasury_token_address: AccountId,
            usdt_token_address: AccountId,
            oracle_dex_address: AccountId,
            liabilities_threshold_level: u8,
        ) -> Result<(), AccessControlError> {
            self.env()
                .transfer(self.factory_addr, self.env().transferred_value());

            FactoryRef::launch_treasury_manager(
                &self.factory_addr,
                self.env().account_id(),
                contract_manager,
                treasury_token_symbol,
                treasury_token_address,
                usdt_token_address,
                oracle_dex_address,
                liabilities_threshold_level,
            );

            self.retrieve_treasury_manager_address();

            Ok(())
        }

        ///Get treasury_manager_address
        #[ink(message)]
        pub fn retrieve_treasury_manager_address(&mut self) -> AccountId {
            self.treasury_manager_addr =
                FactoryRef::get_owner_contract_address(&self.factory_addr, self.env().account_id());
            self.treasury_manager_addr
        }

        ///Get treasury_manager owners addresses
        #[ink(message)]
        pub fn retrieve_treasury_manager_owners(&self) -> Vec<AccountId> {
            FactoryRef::get_owners(&self.factory_addr).clone()
        }
        // *** FACTORY ***/
        // *** TREASURY MANAGER ***/
        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn add_new_voted_job(
            &mut self,
            title: String,
            applicant: AccountId,
            requested_token: AccountId,
            value_in_usd: bool,
            requested_value: Balance,
            payment_type: PaymentType,
            payment_schedule: Vec<u64>,
            payee_accounts: Vec<AccountId>,
        ) -> Result<(), AccessControlError> {
            TreasureManagerRef::add_job(
                &self.treasury_manager_addr,
                title,
                applicant,
                requested_token,
                value_in_usd,
                requested_value,
                payment_type,
                payment_schedule,
                payee_accounts,
            );

            Ok(())
        }

        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn set_treasury_contract_manager(
            &mut self,
            account: AccountId,
        ) -> Result<(), AccessControlError> {
            TreasureManagerRef::set_manager(&self.treasury_manager_addr, account);

            Ok(())
        }

        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn remove_job(&mut self, id: u32) -> Result<(), AccessControlError> {
            TreasureManagerRef::remove_job_info(&self.treasury_manager_addr, id);

            Ok(())
        }

        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn withdraw_funds_from_treasury_manager(
            &mut self,
            amount: Balance,
        ) -> Result<(), AccessControlError> {
            TreasureManagerRef::admin_withdrawal(&self.treasury_manager_addr, amount);

            Ok(())
        }

        #[ink(message)]
        #[modifiers(only_role(ADMIN))]
        pub fn deposit_funds_to_treasury_manager(
            &mut self,
            amount: Balance,
        ) -> Result<(), AccessControlError> {
            //APPROVE FIRST
            PSP22Ref::approve(
                &self.treasury_token_address,
                self.treasury_manager_addr,
                amount,
            )
            .expect("Approval for depositing treasury_token did not go as planned");

            TreasureManagerRef::make_deposit(&self.treasury_manager_addr, amount);

            Ok(())
        }
        // *** TREASURY MANAGER ***/
    }
}
