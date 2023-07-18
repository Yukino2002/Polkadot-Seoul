#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
mod staking_contract {
    use ink::prelude::vec::*;
    use openbrush::contracts::psp22::*;
    use openbrush::traits::Storage;

    #[ink(storage)]
    #[derive(Storage, Default)]
    pub struct StakingContract {
        #[storage_field]
        psp22: psp22::Data
    }

    impl PSP22 for StakingContract {}

    impl psp22::Internal for StakingContract {
        fn _do_safe_transfer_check(
            &mut self,
            _from: &AccountId,
            _to: &AccountId,
            _value: &Balance,
            _data: &Vec<u8>,
        ) -> Result<(), PSP22Error> {
            Ok(())
        }
    }

    impl StakingContract {
        #[ink(constructor)]
        pub fn new(_total_supply: Balance) -> Self {
            let mut contract = Self::default();
            contract
                ._mint_to(Self::env().caller(), 10_000_000)
                .expect("Minting failed");
            contract
        }
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;
        use openbrush::test_utils::*;

        #[ink::test]
        fn constructor_works() {
            let accounts = accounts();
            let mint_amount = 10_000_000;

            let staking_contract = StakingContract::new(mint_amount);

            let alice_balance = staking_contract.balance_of(accounts.alice);
            assert_eq!(alice_balance, mint_amount);
        }

        #[ink::test]
        fn transfer_works() {
            let accounts = accounts();
            let mint_amount = 10_000_000;
            let transfer_amount = 1_000;

            let mut staking_contract = StakingContract::new(mint_amount);
            let result = staking_contract.transfer(accounts.bob, transfer_amount, Vec::<u8>::new());

            let alice_balance = staking_contract.balance_of(accounts.alice);
            let bob_balance = staking_contract.balance_of(accounts.bob);

            assert!(result.is_ok());
            assert_eq!(alice_balance, mint_amount - transfer_amount);
            assert_eq!(bob_balance, transfer_amount);
        }

    }
}
