#![cfg_attr(not(feature = "std"), no_std)]
extern crate alloc;
use ink_lang as ink;

pub use self::authority_management::{
    AuthorityManagement,
};
#[ink::contract]
mod authority_management{
    use alloc::string::String;
    use ink_prelude::vec::Vec;
    use ink_prelude::collections::BTreeMap;
    use ink_storage::{collections::HashMap as StorageHashMap};

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct AuthorityManagement {
        owner:AccountId,
        index:u64,
        authority_map:StorageHashMap<u64,String>,

    }

    impl AuthorityManagement{
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                owner:Self::env().caller(),
                index: 0,
                authority_map : StorageHashMap::new(),
            }
        }

        fn only_core(&self,sender:AccountId) {
            assert_eq!(self.owner, sender);
        }

        #[ink(message)]
        pub fn add_authority(&mut self, name: String) -> bool {
            self.only_core(Self::env().caller());
            self.authority_map.insert(self.index, name);
            self.index += 1;
            true
        }

        #[ink(message)]
        pub fn list_authority(&self) -> Vec<String> {
            let mut authority_vec = Vec::new();
            let mut iter = self.authority_map.values();
            let mut authority = iter.next();
            while authority.is_some() {
                authority_vec.push(authority.unwrap().clone());
                authority = iter.next();
            }
            authority_vec
        }

        #[ink(message)]
        pub fn query_authority_by_index(&self, index: u64) -> String {
            self.authority_map.get(&index).unwrap().clone()
        }

    }
}
