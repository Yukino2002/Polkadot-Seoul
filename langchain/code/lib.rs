#![cfg_attr(not(feature = "std"), no_std, no_main)]
#[ink::contract]
mod contract_name {
    #[ink(storage)]
    pub struct Contract {
        value1: i32,
        value2: i32,
    }

    impl Contract {
        #[ink(constructor)]
        pub fn new() -> Self {
            Self { value1: 1, value2: 2 }
        }

        #[ink(message)]
        pub fn get_sum(&self) -> i32 {
            self.value1 + self.value2
        }
    }
}