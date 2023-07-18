#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

/// This is a simple `PSP-22` which will be used as a stable coin and a collateral token in our lending contract
#[openbrush::contract]
pub mod weth9 {
    use openbrush::contracts::psp22::extensions::metadata::*;
    use ink_prelude::string::String;
    // use lending_project::traits::stable_coin::*;
    use ink_storage::traits::SpreadAllocate;
    use crabswap::impls::weth9::*;

    /// Define the storage for PSP22 data and Metadata data
    #[ink(storage)]
    #[derive(Default, SpreadAllocate, PSP22Storage, PSP22MetadataStorage)]
    pub struct Weth9Contract {
        #[PSP22StorageField]
        psp22: PSP22Data,
        #[PSP22MetadataStorageField]
        metadata: PSP22MetadataData,
    }

    /// implement PSP22 Trait for our coin
    impl PSP22 for Weth9Contract {}

    /// implement PSP22Metadata Trait for our coin
    impl PSP22Metadata for Weth9Contract {}

    impl Weth9 for Weth9Contract{}

    // It forces the compiler to check that you implemented all super traits
    // impl StableCoin for StableCoinContract {}

    impl Weth9Contract {
        /// constructor with name and symbol
        #[ink(constructor)]
        pub fn new(name: Option<String>, symbol: Option<String>) -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut Weth9Contract| {
                instance.metadata.name = name;
                instance.metadata.symbol = symbol;
                instance.metadata.decimals = 12;
                let total_supply = 0 * 10_u128.pow(instance.metadata.decimals.into()); //不可手工增发,
                assert!(instance._mint(instance.env().caller(), total_supply).is_ok());
            })
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use ink_env::DefaultEnvironment;
        use ink_lang as ink;

        fn default_accounts(
        ) -> ink_env::test::DefaultAccounts<ink_env::DefaultEnvironment> {
            ink_env::test::default_accounts::<Environment>()
        }

        fn set_next_caller(caller: AccountId) {
            ink_env::test::set_caller::<Environment>(caller);
        }

        #[ink::test]
        fn register_works() {
            let default_accounts = default_accounts();

            set_next_caller(default_accounts.alice);
            let weth9_contract = Weth9Contract::new(Some(String::from("weth9")),Some(String::from("weth91")));
            assert_eq!(weth9_contract.metadata.name,Some(String::from("weth9")));
        }

        #[ink::test]
        fn test_deposit() {
            let accounts = default_accounts();
            set_next_caller(accounts.alice);
            let mut weth9_contract = Weth9Contract::new(Some(String::from("weth9")),Some(String::from("weth91")));
            ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(1000);
            assert_eq!(weth9_contract.deposit(),Ok(()));
            let balance = weth9_contract.balance_of(accounts.alice);
            assert_eq!(balance,1000u128,"balance not correct!");
            let contract_account_id = ink_env::test::callee::<ink_env::DefaultEnvironment>();
            let native_balance:Balance = ink_env::test::get_account_balance::<ink_env::DefaultEnvironment>(contract_account_id).unwrap();
            // assert_eq!(native_balance,1000u128,"native balance not correct!");
        }

        #[ink::test]
        fn test_withdraw() {
            let accounts = default_accounts();
            set_next_caller(accounts.alice);
            let mut weth9_contract = Weth9Contract::new(Some(String::from("weth9")),Some(String::from("weth91")));
            ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(1000);
            assert_eq!(weth9_contract.deposit(),Ok(()));
            let balance = weth9_contract.balance_of(accounts.alice);
            assert_eq!(balance,1000u128,"balance not correct!");
            assert_eq!(weth9_contract.withdraw(800u128),Ok(()));
            let balance = weth9_contract.balance_of(accounts.alice);
            assert_eq!(balance,1000u128-800u128,"balance not correct!");
        }

        // #[ink::test]
        // fn transfer_works() {
        //     let accounts = default_accounts();
        //     let name = Hash::from([0x99; 32]);

        //     set_next_caller(accounts.alice);

        //     let mut contract = DomainNameService::new();
        //     assert_eq!(contract.register(name), Ok(()));

        //     // Test transfer of owner.
        //     assert_eq!(contract.transfer(name, accounts.bob), Ok(()));

        //     // Owner is bob, alice `set_address` should fail.
        //     assert_eq!(
        //         contract.set_address(name, accounts.bob),
        //         Err(Error::CallerIsNotOwner)
        //     );

        //     set_next_caller(accounts.bob);
        //     // Now owner is bob, `set_address` should be successful.
        //     assert_eq!(contract.set_address(name, accounts.bob), Ok(()));
        //     assert_eq!(contract.get_address(name), accounts.bob);
        // }
    }
}
