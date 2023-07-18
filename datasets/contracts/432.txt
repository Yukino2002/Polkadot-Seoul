//! An example basic contract for crowd funding

#![cfg_attr(not(feature = "std"), no_std)]

#[ink::contract]
mod crowdfund {
    use ink::storage::Mapping;
    use ink::prelude::vec::Vec;
    type String = Vec<u8>;

    #[ink(storage)]
    #[derive(Default)]
    pub struct Crowdfund {
        // Name of the fundraiser event
        name: String,
        // Owner of the fundraiser.
        // It is the account that deploys the contract and the one who receives the funds
        owner: AccountId,
        // Target amount to raise
        target: Balance,
        // Mapping of donors to amount donated
        donations: Mapping<AccountId, Balance>,
    }

    /// Event emitted when a donation is made
    #[ink(event)]
    pub struct Donation {
        #[ink(topic)]
        donor: AccountId,
        value: Balance,
    }

    /// The crowdfund error types.
    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        /// Returned if some account other than the owner tries to withdraw.
        CallerNotOwner,
        /// Returned if crowd fund target is not reached yet.
        TargetNotReached,
    }

    pub type Result<T> = core::result::Result<T, Error>;

    impl Crowdfund {
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        pub fn new(name: String, target: Balance) -> Self {
            Self {
                name,
                owner: Self::env().caller(),
                target,
                donations: Default::default(),
            }
        }

        /// Returns the name of the fundraiser.
        #[ink(message)]
        pub fn name(&self) -> String {
            self.name.clone()
        }

        /// Returns the owner of the crowd fund.
        #[ink(message)]
        pub fn owner(&self) -> AccountId {
            self.owner
        }

        /// Returns the crowd fund target.
        #[ink(message)]
        pub fn target(&self) -> Balance {
            self.target
        }

        /// Returns the amount raised.
        #[ink(message)]
        pub fn raised(&self) -> Balance {
            self.env().balance()
        }

        /// Returns the donation amount for the donor account
        ///
        /// Returns `0` if the account is non-existent.
        #[ink(message)]
        pub fn donation_of(&self, donor: AccountId) -> Balance {
            self.donations.get(donor).unwrap_or_default()
        }

        #[ink(message, payable)]
        pub fn donate(&mut self) -> Result<()> {
            let donor = self.env().caller();
            let value = self.env().transferred_value();
            self.donations.insert(&donor, &value);

            self.env().emit_event(Donation {
                donor,
                value,
            });
            Ok(())
        }

        #[ink(message)]
        pub fn withdraw(&mut self) -> Result<()> {
            let caller = self.env().caller();
            if caller != self.owner {
                return Err(Error::CallerNotOwner)
            }
            if self.raised() < self.target {
                return Err(Error::TargetNotReached)
            }
            self.env().terminate_contract(self.owner)
        }
    }

    #[cfg(test)]
    mod tests {
        // Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        fn default_accounts(
        ) -> ink::env::test::DefaultAccounts<ink::env::DefaultEnvironment> {
            ink::env::test::default_accounts::<ink::env::DefaultEnvironment>()
        }

        fn set_account_balance(account: AccountId, balance: Balance) {
            ink::env::test::set_account_balance::<ink::env::DefaultEnvironment>(
                account, balance,
            );
        }

        fn set_sender(sender: AccountId) {
            ink::env::test::set_caller::<ink::env::DefaultEnvironment>(sender);
        }

        fn contract_id() -> AccountId {
            let accounts = default_accounts();
            let contract_id = accounts.charlie;
            ink::env::test::set_callee::<ink::env::DefaultEnvironment>(contract_id);
            contract_id
        }

        // We test a simple use case of our contract.
        #[ink::test]
        fn new_works() {
            let crowdfund = Crowdfund::new(String::from("Test"), 10);
            assert_eq!(crowdfund.name(), "Test");
            assert_eq!(crowdfund.target(), 10);
        }

        #[ink::test]
        fn donate_works() {
            let accounts = default_accounts();
            set_account_balance(accounts.alice, 50_000);
            set_account_balance(accounts.bob, 100_000);

            let mut crowdfund = Crowdfund::new(String::from("Test"), 10_000_000);
            let contract_id = contract_id();
            set_account_balance(contract_id, 0);

            set_sender(accounts.alice);
            ink::env::pay_with_call!(crowdfund.donate(), 15_000).expect("");
            set_sender(accounts.bob);
            ink::env::pay_with_call!(crowdfund.donate(), 25_000).expect("");
     
            assert_eq!(crowdfund.donation_of(accounts.alice), 15_000);
            assert_eq!(crowdfund.donation_of(accounts.bob), 25_000);
            assert_eq!(crowdfund.donation_of(accounts.eve), 0);
            assert_eq!(crowdfund.raised(), 40_000);
        }
    }
}
