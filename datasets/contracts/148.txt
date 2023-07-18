#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;
pub use self::endDate::EndDate;

#[ink::contract]
pub mod endDate {
    use ink_prelude::collections::BTreeMap;
    #[derive(Debug, PartialEq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {

    }

    pub type Result<T> = core::result::Result<T, Error>;

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct EndDate {
        /// Stores a single `bool` value on the storage.
        /// Gets contract end date
        end_date: BTreeMap<AccountId, u64>,
    }

    impl EndDate {
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self { end_date:Default::default() }
        }

        #[ink(message)]
        pub fn get_end_date(&self, address: AccountId) -> u64 {
            self.end_date[&address]
        }

        #[ink(message)]
        pub fn set_end_date(&mut self, end_date: u64) -> Result<()> {
            //todo: only let smart contracts do this 
            let caller = self.env().caller();
            self.end_date.insert(caller, end_date);
            Ok(())
        }
        




    }

}
