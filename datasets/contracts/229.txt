#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

pub use self::oracle::{
    Oracle,
    OracleRef,
};

use ink_storage::traits::{SpreadAllocate};
use ink_env::call::FromAccountId;

#[ink::contract]
pub mod oracle {
    use ink_storage::{
        traits::{SpreadAllocate},
        Mapping,
    };
    use ink_prelude::string::String;

    #[derive(Debug, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum OracleError {
        Custom(String),
    }

    #[ink(storage)]
    #[derive(Default, SpreadAllocate)]
    pub struct Oracle {
        values: Mapping<String, String>,
        owner: AccountId,
    }

    impl Oracle {
        #[ink(constructor)]
        pub fn new() -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut Self| {
                instance.owner = Self::env().caller();
                instance.values = Mapping::default();
            })
        }

        #[ink(message)]
        pub fn get(&self, key: String) -> String {
            return self.values.get(key).unwrap_or(String::from(""));
        }

        #[ink(message)]
        pub fn set(&mut self, key: String, value: String) {
            // TODO: Use Openbrush::ownable
            let caller = self.env().caller();
            assert_eq!(caller, self.owner);

            self.values.insert(
                key,
                &value,
            )
        }

        #[ink(message)]
        pub fn get_floor_price(&self, id: String) -> Result<Balance, OracleError> {
            let floor_price_res = self.get(id).parse::<Balance>();
            if floor_price_res.is_err() {
                // return Err(OracleError::Custom(String::from("Price not found")));
                // Just using a mocked value here
                return Ok(1000000);
            }
            let floor_price = floor_price_res.unwrap();
            Ok(floor_price)
        }

        #[ink(message)]
        pub fn account_id(&self) -> AccountId {
            self.env().account_id()
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use ink_lang as ink;

        #[ink::test]
        fn sample_test() {
            let mut oracle = Oracle::new();
            assert_eq!(oracle.get(String::from("foo")), String::from(""));

            oracle.set(String::from("foo"), String::from("bar"));
            assert_eq!(oracle.get(String::from("foo")), String::from("bar"));

            oracle.set(String::from("test"), String::from("1337"));
            assert_eq!(oracle.get(String::from("test")).parse::<u32>().unwrap(), 1337);
            assert_eq!(oracle.get_floor_price(String::from("test")).unwrap(), 1337);
        }
    }
}

// https://github.com/paritytech/ink/issues/1149
impl SpreadAllocate for OracleRef {
    fn allocate_spread(_ptr: &mut ink_primitives::KeyPtr) -> Self {
        FromAccountId::from_account_id([0; 32].into())
    }
}
