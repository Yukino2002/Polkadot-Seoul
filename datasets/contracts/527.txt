#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
mod storage {

    #[ink(storage)]
    pub struct Storage {
        value: Balance,
    }

    impl Storage {
        #[ink(constructor)]
        pub fn new(init_value: Balance) -> Self {
            Self { value: init_value }
        }

        #[ink(constructor)]
        pub fn default() -> Self {
            Self::new(Default::default())
        }

        #[ink(message)]
        pub fn set(&mut self, new_number: Balance) {
            self.value = new_number;
        }

        #[ink(message)]
        pub fn get(&self) -> Balance {
            self.value
        }

    }

    #[cfg(test)]
    mod tests {
        use super::*;

        use ink_lang as ink;

        #[ink::test]
        fn it_should_init_with_default() {
            let storage = Storage::default();
            assert_eq!(storage.get(), 0u128)
        }

        #[ink::test]
        fn constructor_works() {
            let storage = Storage::new(5u128);
            assert_eq!(storage.get(), 5u128)
        }

        #[ink::test]
        fn getter_works() {
            let storage = Storage::new(10);
            storage.get();
        }

        #[ink::test]
        fn setter_works() {
            let mut storage = Storage::new(10);
            storage.set(15);
            assert_eq!(storage.get(), 15u128)
        }

    }

}
