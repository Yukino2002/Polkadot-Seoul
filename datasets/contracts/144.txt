#![cfg_attr(not(feature = "std"), no_std)]
use ink_lang as ink;

#[ink::contract]
mod todo {
    use ink_prelude::string::String;
    use ink_prelude::vec::Vec;
    use ink_storage::traits::{PackedLayout, SpreadLayout};

    // Structure to store Todo information
    #[derive(Clone, Debug, scale::Encode, scale::Decode, SpreadLayout, PackedLayout)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct Task {
        title: String,
        description: String,
        completed: bool, 
        id: u32,
        account_id: AccountId
    }

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct Todos {
        user: AccountId,
        task: Vec<Task>
    }

    impl Todos {
        #[ink(constructor)]
        pub fn new(_task: Option<Vec<String>> ) -> Self {
            let user = Self::env().caller();
            let mut task: Vec<Task> = Vec::new();

            task.push(Task {
                title: String::from(""),
                description: String::from(""),
                completed: false,
                id: 0,
                account_id: user
            });

            Self {
                user,
                task
            }
        }

        #[ink(constructor)]
        pub fn default() -> Self {
            Self::new(Default::default())
        }

        /// A message that can be called on instantiated contracts.
        /// To add a new task
        #[ink(message)]
        pub fn add_task(&mut self, account_id: AccountId, title: String, description: String) {
            let id = self.task.len()+1;
            self.task.push(Task {
                title,
                description,
                completed: false,
                id: id.try_into().unwrap(),
                account_id
            });
        }

        /// Update an existing task
        #[ink(message)]
        pub fn update_task(&mut self, id: u32, completed: bool) {
            let task = self.task.iter_mut().find(|task| task.id == id).unwrap();
            task.completed = completed;
        }

        /// Simply returns all the tasks.
        #[ink(message)]
        pub fn get_tasks(&self) -> Vec<Task> {
            self.task.clone()
        }
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        /// Imports `ink_lang` so we can use `#[ink::test]`.
        use ink_lang as ink;

        /// We test if the default constructor does its job.
        #[ink::test]
        fn default_works() {
            let mut todos = Todos::default();
            todos.task.push(Task { title: String::from("this is a title"), description: String::from("this is a description"), completed: false, id: 0, account_id: AccountId::from([0x0; 32]) });
            assert_eq!(todos.get_tasks()[1].title, { "this is a title" });
        }
    }
}
