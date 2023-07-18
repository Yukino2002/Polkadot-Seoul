#![cfg_attr(not(feature = "std"), no_std)]

#[openbrush::contract]
mod flipper_one {
    use communication_base::communication_base::{CommunicationBase, CommunicationBaseRef};
    use contract_helper::common::common_logics::*;
    use contract_helper::traits::contract_base::contract_base::*;
    use contract_helper::traits::types::types::*;
    use ink::prelude::string::{String, ToString};
    use ink::prelude::vec::Vec;
    
    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct FlipperOne {
        /// Stores a single `bool` value on the storage.
        value: bool,
        dao_address: Option<AccountId>,
        command_list: Vec<String>,
        communication_base_address: AccountId,
    }

    impl ContractBase for FlipperOne {
        #[ink(message)]
        fn get_dao_address(&self) -> Option<AccountId> {
            self.dao_address
        }

        #[ink(message)]
        fn get_caller_check_specs(&self, command: String) -> Option<CallerCheckSpecs> {
            match command.as_str() {
                "test_a1_function" => Some(CallerCheckSpecs::DaoMemeber),
                _ => None,
            }
        }

        #[ink(message)]
        fn get_data(&self, target_function: String) -> Vec<Vec<u8>> {
            let mut result: Vec<Vec<u8>> = Vec::new();
            result
        }

        fn _set_dao_address_impl(
            &mut self,
            dao_address: AccountId,
        ) -> core::result::Result<(), ContractBaseError> {
            self.dao_address = Some(dao_address);
            Ok(())
        }

        fn _get_command_list(&self) -> &Vec<String> {
            &self.command_list
        }

        fn _function_calling_switch(
            &mut self,
            command: String,
            vec_of_parameters: Vec<String>,
        ) -> core::result::Result<(), ContractBaseError> {
            match command.as_str() {
                "circuler_flip" => self._circuler_flip(vec_of_parameters),
                _ => Err(ContractBaseError::CommnadNotFound),
            }
        }
    }

    impl FlipperOne {
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        pub fn new(init_value: bool,communication_base_address:AccountId) -> Self {
            Self { 
                value: init_value,
                dao_address: None,
                command_list: [
                    "circuler_flip".to_string(),
                ]
                .to_vec(),
                communication_base_address: communication_base_address,
            }
        }


        /// A message that can be called on instantiated contracts.
        /// This one flips the value of the stored `bool` from `true`
        /// to `false` and vice versa.
        #[ink(message)]
        pub fn flip(&mut self) {
            self.value = !self.value;
        }

        /// Simply returns the current value of our `bool`.
        #[ink(message)]
        pub fn get(&self) -> bool {
            self.value
        }

        pub fn _circuler_flip(&mut self, mut vec_of_parameters:Vec<String>) -> Result<(), ContractBaseError> {
            self.flip();

            if vec_of_parameters.len() >= 1 && vec_of_parameters[0] != "" {
                let mut param_string:String = "".to_string();
                let to_string = vec_of_parameters[0].clone();
                vec_of_parameters.remove(0);
                for i in 0.. vec_of_parameters.len() {
                    if i >= 1{
                        param_string = param_string + ",";
                    }
                    param_string = param_string + &vec_of_parameters[i];
                }
                let mut instance: CommunicationBaseRef =
                ink::env::call::FromAccountId::from_account_id(self.communication_base_address);
                instance.call_execute_interface_of_function(
                    convert_string_to_accountid(&to_string),
                    "circuler_flip".to_string(),
                    param_string
                )
            }
            else{
                Ok(())
            }
        }
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        /// We test if the default constructor does its job.
        #[ink::test]
        fn default_works() {
            let flipper_one = FlipperOne::default();
            assert_eq!(flipper_one.get(), false);
        }

        /// We test a simple use case of our contract.
        #[ink::test]
        fn it_works() {
            let mut flipper_one = FlipperOne::new(false);
            assert_eq!(flipper_one.get(), false);
            flipper_one.flip();
            assert_eq!(flipper_one.get(), true);
        }
    }
}
