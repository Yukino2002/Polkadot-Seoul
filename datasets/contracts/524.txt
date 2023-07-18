#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

pub mod traits;

#[openbrush::contract]
pub mod task_manager {
    use openbrush::{
        contracts::psp34::{
            extensions::{
                enumerable::*,
                metadata::*,
            },
            PSP34Error,
        },
        storage::Mapping,
        traits::{
            Storage,
            String,
        },
    };
    use sbt::traits::SBTRef;
    use crate::traits::*;

    #[ink(storage)]
    #[derive(Storage)]
    pub struct TaskManager {
        #[storage_field]
        psp34: psp34::Data<Balances>,
        #[storage_field]
        metadata: Data,
        next_id: u32,
        deadlines: Mapping<Id, u64>,
        completed: Mapping<Id, ()>,
        score: Mapping<AccountId, u32>,
        total_score: u32,
        evaluated: Mapping<(Id, AccountId), ()>,
        sbt: AccountId,
    }

    impl PSP34 for TaskManager {}
    impl PSP34Enumerable for TaskManager {}
    impl PSP34Metadata for TaskManager {}

    impl TaskManagerTrait for TaskManager {
        #[ink(message)]
        fn get_score(&self, account: AccountId) -> u32 {
            self.score.get(&account).unwrap_or(0)
        }

        #[ink(message)]
        fn get_total_score(&self) -> u32 {
            self.total_score
        }
    }

    impl TaskManager {
        #[ink(constructor)]
        pub fn new(sbt: AccountId) -> Self {
            let mut _instance = TaskManager {
                psp34: psp34::Data::default(),
                metadata: Data::default(),
                next_id: 0,
                deadlines: Mapping::default(),
                completed: Mapping::default(),
                score: Mapping::default(),
                total_score: 0,
                evaluated: Mapping::default(),
                sbt,
            };

            let collection_id = _instance.collection_id();
            _instance._set_attribute(collection_id.clone(), String::from("name"), String::from("TaskManager"));
            _instance._set_attribute(collection_id, String::from("symbol"), String::from("Proposals"));
            _instance
        }

        #[ink(message)]
        pub fn create_task(&mut self, deadline: u64) -> Result<(), PSP34Error> {
            if SBTRef::balance_of(&self.sbt, Self::env().caller()) == 0 {
                return Err(PSP34Error::Custom("Not a member".into()))
            }
            if deadline < Self::env().block_timestamp() {
                return Err(PSP34Error::Custom("Deadline is in the past".into()))
            }
            self._mint_to(Self::env().caller(), Id::U32(self.next_id))?;
            self.deadlines.insert(&Id::U32(self.next_id), &deadline);
            self.next_id += 1;
            Ok(())
        }

        #[ink(message)]
        pub fn complete_task(&mut self, id: Id) -> Result<(), PSP34Error> {
            if SBTRef::balance_of(&self.sbt, Self::env().caller()) == 0 {
                return Err(PSP34Error::Custom("Not a member".into()))
            }
            if self.owner_of(id.clone()).unwrap() != Self::env().caller() {
                return Err(PSP34Error::Custom("Task is owned by others".into()))
            }
            if self.completed.get(&id).is_some() {
                return Err(PSP34Error::Custom("Task is completed".into()))
            }
            self.completed.insert(&id, &());
            Ok(())
        }

        #[ink(message)]
        pub fn get_deadline(&self, id: Id) -> u64 {
            self.deadlines.get(&id).unwrap()
        }

        #[ink(message)]
        pub fn is_completed(&self, id: Id) -> bool {
            self.completed.get(&id).is_some()
        }

        #[ink(message)]
        pub fn get_score(&self, account: AccountId) -> u32 {
            self.score.get(&account).unwrap_or(0)
        }

        #[ink(message)]
        pub fn get_total_score(&self) -> u32 {
            self.total_score
        }

        #[ink(message)]
        pub fn is_evaluated(&self, id: Id, account: AccountId) -> bool {
            self.evaluated.get(&(id, account)).is_some()
        }

        #[ink(message)]
        pub fn evaluate_task(&mut self, id: Id, evaluation: u32) -> Result<(), PSP34Error> {
            if SBTRef::balance_of(&self.sbt, Self::env().caller()) == 0 {
                return Err(PSP34Error::Custom("Not a member".into()))
            }
            if self.owner_of(id.clone()).is_none() {
                return Err(PSP34Error::Custom("Task does not exist".into()))
            }
            if self.completed.get(&id).is_none() {
                return Err(PSP34Error::Custom("Task is not completed".into()))
            }
            let caller = Self::env().caller();
            if self.owner_of(id.clone()).unwrap() == caller {
                return Err(PSP34Error::Custom("Cannot self evaluate".into()))
            }
            if evaluation > 100 {
                return Err(PSP34Error::Custom("Score must be between 0 and 100".into()))
            }
            if self.evaluated.get(&(id.clone(), caller)).is_some() {
                return Err(PSP34Error::Custom("Already evaluated".into()))
            }

            let evaluator_score = self.score.get(&caller);
            let total_score = if self.total_score == 0 {
                SBTRef::total_supply(&self.sbt) as u32
            } else {
                self.total_score
            };
            let weighted_evaluation = evaluation * evaluator_score.unwrap_or(1) / total_score;
            let task_owner = self.owner_of(id.clone()).unwrap();
            let current_score = self.score.get(&task_owner).unwrap_or(0);
            self.score.insert(&task_owner, &(current_score + weighted_evaluation));
            self.total_score += weighted_evaluation;

            self.score.insert(&caller, &(evaluator_score.unwrap_or(0) + 1));
            self.total_score += 1;
            self.evaluated.insert(&(id, caller), &());
            Ok(())
        }
    }
}
