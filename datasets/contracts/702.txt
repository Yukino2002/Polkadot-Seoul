#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
mod erc20 {

    #[cfg(not(feature = "ink-as-dependency"))]
    use ink_storage::collections::HashMap;

    // storage
    #[ink(storage)]
    pub struct Erc20 {
        total_supply: Balance,
        balances: HashMap<AccountId, Balance>,
        // stores (owner, spender) -> allowed balance
        allowances: HashMap<(AccountId, AccountId), Balance>,
    }

    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        from: Option<AccountId>,
        #[ink(topic)]
        to: Option<AccountId>,
        #[ink(topic)]
        value: Balance,
    }
    #[ink(event)]
    pub struct Approval {
        #[ink(topic)]
        owner: AccountId,
        #[ink(topic)]
        spender: AccountId,
        #[ink(topic)]
        value: Balance,
    }

    impl Erc20 {
        #[ink(constructor)]
        pub fn new(initial_supply: Balance) -> Self {
            let mut balances: HashMap<AccountId, Balance> = HashMap::new();
            let caller = Self::env().caller();

            // initial supply
            balances.insert(caller, initial_supply);

            // emit balance transfer event
            Self::env().emit_event(Transfer {
                from: None,
                to: Some(caller),
                value: initial_supply,
            });

            Self {
                total_supply: initial_supply,
                balances,
                allowances: HashMap::new(),
            }
        }

        #[ink(message)]
        pub fn total_supply(&self) -> Balance {
            self.total_supply
        }

        #[ink(message)]
        pub fn balance_of(&self, owner: AccountId) -> Balance {
            self.balance_of_or_zero(&owner)
        }

        #[ink(message)]
        pub fn transfer(&mut self, to: AccountId, value: Balance) -> bool {
            self.transfer_from_to(self.env().caller(), to, value)
        }

        #[ink(message)]
        pub fn approve(&mut self, spender: AccountId, value: Balance) -> bool {
            let owner = self.env().caller();
            self.allowances.insert((owner, spender), value);

            self.env().emit_event(Approval {
                owner,
                spender,
                value,
            });

            true
        }

        #[link(message)]
        pub fn allowance(&self, owner: AccountId, spender: AccountId) -> Balance {
            self.allowance_of_or_zero(&owner, &spender)
        }

        #[ink(message)]
        pub fn transfer_from(&mut self, from: AccountId, to: AccountId, value: Balance) -> bool {
            let owner = self.env().caller();
            let allowance = self.allowance(owner, from);

            // if spender does not have enough allowance, early exit
            if allowance < value {
                return false;
            }

            // check if the spender has enough amount
            if self.balance_of(from) < value {
                return false;
            }

            self.transfer_from_to(from, to, value);
            self.allowances.insert((owner, from), allowance - value);

            true
        }

        /**
         * Private methods
         * */
        fn balance_of_or_zero(&self, owner: &AccountId) -> Balance {
            *self.balances.get(owner).unwrap_or(&0)
        }

        fn set_balance_of(&mut self, account: AccountId, value: Balance) {
            self.balances.insert(account, value);
        }

        fn transfer_from_to(&mut self, from: AccountId, to: AccountId, value: Balance) -> bool {
            let from_balance = self.balance_of(from);
            let to_balance = self.balance_of(to);

            if from_balance < value {
                return false;
            }

            // update balances
            self.set_balance_of(from, from_balance - value);
            self.set_balance_of(to, to_balance + value);

            self.env().emit_event(Transfer {
                from: Some(from),
                to: Some(to),
                value,
            });

            true
        }

        fn allowance_of_or_zero(&self, owner: &AccountId, spender: &AccountId) -> Balance {
            *self.allowances.get(&(*owner, *spender)).unwrap_or(&0)
        }
    }

    /// Tests
    #[cfg(test)]
    mod lib_tests {
        use super::*;
        use ink_lang as ink;

        #[ink::test]
        fn new_works() {
            let erc20 = Erc20::new(1000);
            assert_eq!(erc20.total_supply(), 1000);
        }

        #[ink::test]
        fn balance_works() {
            let erc20 = Erc20::new(100);
            assert_eq!(erc20.balance_of(AccountId::from([0x1; 32])), 100);
            assert_eq!(erc20.balance_of(AccountId::from([0x2; 32])), 0);
        }

        #[ink::test]
        fn transfer_works() {
            let mut erc20 = Erc20::new(100);

            // before
            assert_eq!(erc20.balance_of(AccountId::from([0x1; 32])), 100);
            assert_eq!(erc20.balance_of(AccountId::from([0x2; 32])), 0);

            // transfer
            erc20.transfer(AccountId::from([0x2; 32]), 19);

            // after
            assert_eq!(erc20.balance_of(AccountId::from([0x1; 32])), 81);
            assert_eq!(erc20.balance_of(AccountId::from([0x2; 32])), 19);
        }

        #[ink::test]
        fn transfer_with_allowance_works() {
            let mut contract = Erc20::new(100);
            let account_a = AccountId::from([0x1; 32]);
            let account_b = AccountId::from([0x2; 32]);
            let account_c = AccountId::from([0x3; 32]);

            // before
            assert_eq!(contract.balance_of(account_a), 100);
            assert_eq!(contract.balance_of(account_b), 0);
            assert_eq!(contract.balance_of(account_c), 0);

            // transfer funds to other user
            contract.transfer(account_b, 80);
            assert_eq!(contract.balance_of(account_a), 20);
            assert_eq!(contract.balance_of(account_b), 80);

            // approve
            contract.approve(account_b, 200);
            assert_eq!(contract.allowance(account_a, account_b), 200);

            // initiate transfer
            assert!(contract.transfer_from(account_b, account_c, 50));

            // after
            assert_eq!(contract.balance_of(account_a), 20);
            assert_eq!(contract.balance_of(account_b), 30);
            assert_eq!(contract.balance_of(account_c), 50);
            assert_eq!(contract.allowance(account_a, account_b), 150);
        }

        #[ink::test]
        fn non_approved_transfer_does_not_work() {
            let mut contract = Erc20::new(100);

            // before
            assert_eq!(contract.balance_of(AccountId::from([0x1; 32])), 100);
            assert_eq!(contract.balance_of(AccountId::from([0x2; 32])), 0);

            // transfer before approval
            assert!(!contract.transfer_from(
                AccountId::from([0x1; 32]),
                AccountId::from([0x0; 32]),
                50
            ));

            // before, same as before
            assert_eq!(contract.balance_of(AccountId::from([0x1; 32])), 100);
            assert_eq!(contract.balance_of(AccountId::from([0x2; 32])), 0);
        }
    }
}
