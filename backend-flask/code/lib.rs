#![cfg_attr(not(feature = "std"), no_std, no_main)]
#[ink::contract]
mod contract_name {

    #[ink(storage)]
    pub struct ContractName {
        value1: Value<u32>,
        value2: Value<u32>,
    }

    impl ContractName {
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                value1: Value::new(3),
                value2: Value::new(7),
            }
        }

        #[ink(message)]
        pub fn get_sum(&self) -> u32 {
            *self.value1 + *self.value2
        }
    }
}