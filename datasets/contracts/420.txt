#![deny(unsafe_code)]
#![cfg_attr(not(feature = "std"), no_std)]
//! ## Koins (\ˈkȯin\) 🪙
//!
//! Koins is a smart-contract built as an experiment to see how we could build a simple and secure
//! points system for current applications we have today.
//!
//! for example, imagine that we have an application where users own coins
//! and they can do things inside the application using these points/coins like buying in-app items
//! or transferring these Coins between them ...etc.
//! and they can obtain these Coins by purchasing them from the system in **fiat currencies**.
//!
//! To build such a system we need a lot of security concerns like how do we secure our database?
//! how do we ensure that no one will play sneaky and modify the coins for a specific account
//! in our database? maybe it is not you, but someone else in your team could do so!
//!
//! This idea of storing your payments on a blockchain sounds very good!
//! but nor you or your team has the time or the experience to build, manage, and lunch your own chain!
//! it is not hard, to be honest with you with `Substrate` now, but it costs a lot in the real world
//! to manage and update the chain and to keep it going/working.
//!
//! ### The Idea 💡
//!
//! The idea behind this contract is to simply I asked myself, could we have a way to utilize
//! blockchain more in our current app implementations? I'm not referring here to `dApps`
//! but I'm pointing to an application that is centralized in one way or in another.
//!
//! This Smart Contract ensures everything that gets preserved is 100% correct.
//! it is very simple only 2 methods (if we didn't count increment or decrement)
//! few lines of code, and with everything documented.
//!
//! ### Current use-case
//!
//! I'm currently building `Owlchat` in my free time and at the weekends,
//! and for anyone who does not know about `Owlchat`, it is a mobile chat application where you can
//! match with other peoples from around the world based on your interests.
//! you can read more about Owlchat here at [Owlchat Whitepaper draft](#todo).
//!
//! Owlchat is a privacy-focused metadata-free end-to-end encrypted chat application (a lot of hyphens here :D)
//! but anyway .. into the point, Owlchat needed a Points/Coins system, where a user uses these points
//! to do a match with another person (1 Coin = 1 Match), and these Coins can be purchased
//! using in-app payment systems, like say Google Pay or Apple Pay!
//!
//! Next, after deploying the contract on a smart contract chain like `Edgeware`,
//! when a user purchases these coins the system will send a TX to the smart contract with
//! the account public key and the amount of the coins.
//!
//! And whenever the user wants to do a Match, the server simply does a simple check to query the smart contract
//! with a fee-less RPC to the chain, and if the user have coins, the server can run the matching algorithm!
//! Yes, it is that simple!
//!
//! ### Ownership
//!
//! The account that will deploy the contract will gain ownership access
//! over anything that requires mutations.
//!
//! ### Open Questions 🤔
//!
//! 1. Currently, any TXs require the smart-contract owner to have a balance to execute the transaction.
//! how do we do the transaction efficiently to lower any fees?
//! since with every user do a match we do a TX!
//!
//! 2. How to secure the smart-contract owner account private key on a server environment? hardware-wallets?
//!
//! If you have any improvements or questions, please feel free to chat with me or open a new issue will be very welcome!
//!
//! For Internal Implementation: see the [`koins`](crate::koins) module.
use ink_lang as ink;

#[ink::contract]
pub mod koins {
    /// Koins, store your users coins easily on blockchain smart contract.
    #[ink(storage)]
    pub struct Koins {
        /// Contract owner.
        ///
        /// Used as access control over `&mut self` methods.
        owner: AccountId,
        /// HashMap Datastore between the users public keys and amount of coins.
        store: ink_storage::collections::HashMap<AccountId, u32>,
    }

    #[ink(impl)]
    impl Koins {
        /// Create a new contract!
        ///
        /// The `caller` of this constructor will be set as the Owner of the contract.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                store: Default::default(),
                owner: Self::env().caller(),
            }
        }

        /// Adds `coins` to the `account`.
        ///
        /// if the account is not already in the storage, will be set with `coins`.
        ///
        /// Returns the total coins the account owns.
        ///
        /// ### Note
        /// In case of overflow the account's coins will be set to the maximum value.
        ///
        /// ### Panics
        /// this message will panic on runtime if the `caller` is not the `owner` of the contract.
        #[ink(message)]
        pub fn add_coins(&mut self, account: AccountId, coins: u32) -> u32 {
            self.ensure_ownership();
            let new_value = self
                .store
                .entry(account)
                .and_modify(|v| *v = v.checked_add(coins).unwrap_or(u32::MAX))
                .or_insert(coins);

            *new_value
        }

        /// Returns how many coins this account owns.
        ///
        /// In case if this account is not seen before, returns `Zero`.
        #[ink(message)]
        pub fn get_coins(&self, account: AccountId) -> u32 {
            let value = self.store.get(&account).unwrap_or(&0);

            *value
        }

        /// An Easy way to just increment an account coins by one, simpley doing a read, increment, and
        /// write in a one call.
        ///
        /// ### Note
        /// In case of overflow the account's coins will be set to the maximum value.
        ///
        /// ### Panics
        /// this message will panic on runtime if the `caller` is not the `owner` of the contract.//
        #[ink(message)]
        pub fn increment(&mut self, account: AccountId) -> u32 {
            self.ensure_ownership();
            let new_value = self
                .store
                .entry(account)
                .and_modify(|v| *v = v.checked_add(1).unwrap_or(u32::MAX))
                .or_insert(1);

            *new_value
        }

        /// An Easy way to decrement the account coins by one.
        ///
        /// ### Note
        /// In case of unerflow the account's coins will be set to `Zero`.
        ///
        /// ### Panics
        /// this message will panic on runtime if the `caller` is not the `owner` of the contract.
        #[ink(message)]
        pub fn decrement(&mut self, account: AccountId) -> u32 {
            self.ensure_ownership();
            let new_value = self
                .store
                .entry(account)
                .and_modify(|v| *v = v.checked_sub(1).unwrap_or(0))
                .or_insert(0);

            *new_value
        }

        /// a helper method to ensure that the caller is the owner of the contract.
        ///
        /// panics otherwise which will stop the execution of the contract.
        fn ensure_ownership(&self) {
            let caller = self.env().caller();
            assert!(self.owner.eq(&caller), "unauthorized caller");
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use ink_env::{call, test};
        use ink_lang as ink;

        type Accounts = test::DefaultAccounts<Environment>;

        #[ink::test]
        fn happy_path() {
            set_from_owner();
            let mut koins = Koins::new();
            let accounts = default_accounts();

            assert_eq!(koins.get_coins(accounts.bob), 0);
            assert_eq!(koins.add_coins(accounts.bob, 42), 42);
            assert_eq!(koins.get_coins(accounts.bob), 42);

            // totally different account
            assert_eq!(koins.get_coins(accounts.eve), 0);
        }

        #[ink::test]
        fn add_coins() {
            set_from_owner();
            let mut koins = Koins::new();
            let accounts = default_accounts();

            assert_eq!(koins.get_coins(accounts.bob), 0);
            assert_eq!(koins.add_coins(accounts.bob, 100), 100);
            assert_eq!(koins.get_coins(accounts.bob), 100);

            assert_eq!(koins.add_coins(accounts.bob, 50), 150);
            assert_eq!(koins.get_coins(accounts.bob), 150);
        }

        #[ink::test]
        fn increment_decrement() {
            set_from_owner();
            let mut koins = Koins::new();
            let accounts = default_accounts();

            // new account not seen before.
            assert_eq!(koins.increment(accounts.bob), 1);
            // check again.
            assert_eq!(koins.get_coins(accounts.bob), 1);
            assert_eq!(koins.add_coins(accounts.bob, 100), 101);
            assert_eq!(koins.get_coins(accounts.bob), 101);

            // decrement account.
            assert_eq!(koins.decrement(accounts.bob), 100);
            assert_eq!(koins.get_coins(accounts.bob), 100);
            // decrement account that not seen before.
            assert_eq!(koins.decrement(accounts.eve), 0);
            assert_eq!(koins.decrement(accounts.eve), 0);
        }

        #[ink::test]
        #[should_panic(expected = "unauthorized caller")]
        fn not_the_owner() {
            set_from_owner();
            let mut koins = Koins::new();

            let accounts = default_accounts();

            assert_eq!(koins.get_coins(accounts.bob), 0);
            assert_eq!(koins.add_coins(accounts.bob, 42), 42);
            assert_eq!(koins.get_coins(accounts.bob), 42);

            set_from_noowner();

            let not_really_new_value = koins.add_coins(accounts.bob, 100);
            assert_eq!(not_really_new_value, 42);
        }

        fn set_sender(sender: AccountId) {
            test::push_execution_context::<Environment>(
                sender,
                [42u8; 32].into(),
                1000000,
                1000000,
                test::CallData::new(call::Selector::new([0x00; 4])), // dummy
            );
        }

        fn set_from_owner() {
            let accounts = default_accounts();
            set_sender(accounts.alice);
        }

        fn set_from_noowner() {
            let accounts = default_accounts();
            set_sender(accounts.django);
        }

        fn default_accounts() -> Accounts {
            test::default_accounts()
                .expect("Test environment is expected to be initialized.")
        }
    }
}
