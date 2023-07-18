//! This contract allows users to send tips to registered typto receivers backed by storage on blockchain.
//!
//! The contract provides methods to [tip users][send_tip].
//!
//! [send_tip]: struct.Contract.html#method.send_tip

// use std::sync::atomic::{AtomicBool, Ordering};
// use std::sync::Arc;
// use std::thread;

use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::{
    collections::{UnorderedMap},
    env,
    json_types::U128,
    log,
    near_bindgen,
    AccountId,
    Promise,
};

#[global_allocator]
static ALLOC: near_sdk::wee_alloc::WeeAlloc = near_sdk::wee_alloc::WeeAlloc::INIT;

#[derive(BorshDeserialize, BorshSerialize)]
enum ReceiverKind {
    Verified,
    Pending
}

#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Contract {
    pub verified_receivers: UnorderedMap<String, AccountId>,
    pub pending_receivers: UnorderedMap<String, AccountId>,
    pub registered_receiver_id: Option<(AccountId, ReceiverKind)>,
}

impl Default for Contract {
    fn default() -> Self {
        Self {
            verified_receivers: UnorderedMap::new(b"verified_receivers".to_vec()),
            pending_receivers: UnorderedMap::new(b"pending_receivers".to_vec()),
            registered_receiver_id: None,
        }
    }
}

#[near_bindgen]
impl Contract {
    #[init]
    pub fn new() -> Self {
        assert!(!env::state_exists(), "Already initialized");
        Self {
            verified_receivers: UnorderedMap::new(b"verified_receivers".to_vec()),
            pending_receivers: UnorderedMap::new(b"pending_receivers".to_vec()),
            registered_receiver_id: None,
        }
    }

    fn get_balance(&self) -> u128 {
        env::account_balance()
    }

    fn get_receiver_id(&mut self, receiver_alias: &String) -> &Option<(AccountId, ReceiverKind)> {
        if self.registered_receiver_id.is_some() {
            let registered_receiver_id: (AccountId, ReceiverKind) = self.registered_receiver_id.unwrap();
            return &Some((registered_receiver_id.0, registered_receiver_id.1))
        }
        for k in self.pending_receivers.keys() {
            if &k == receiver_alias {
                let registered_receiver_id = self.pending_receivers.get(&receiver_alias).unwrap();
                self.registered_receiver_id = Some((registered_receiver_id, ReceiverKind::Pending));
                return &self.registered_receiver_id
            }
        }
        for k in self.verified_receivers.keys() {
            if &k == receiver_alias {
                let registered_receiver_id = self.verified_receivers.get(&receiver_alias).unwrap();
                self.registered_receiver_id = Some((registered_receiver_id, ReceiverKind::Verified));
                return &self.registered_receiver_id
            }
        }
        &None
    }
    
    fn register_pending_receiver(&mut self, receiver_alias: String, tip_amount: U128) {
        // TODO:
        // Should deploy subaccount to pending_receivers.typto.{testnet, near} and do one of 2 things:
        //   1. Deploy a contract on the subaccount, and have the account deleted and funds returned to 
        //      the original address
        //   2. Add account to a data structure that maps account to expiration date at which time the  
        //      subaccount will be deleted and funds returned to original address

        // FIXME: What's this AccountId functionality? Copied from https://github.com/NEAR-labs/contracts.near-linkdrop/blob/d10e1b1dfab1d0f767c6357e7355bf280d40dcf9/contracts/linkdrop/src/create_user_account.rs
        // let account_id = AccountId::new_unchecked(format!("{}.{}", receiver_alias.replace(".", "-"), "testnet"));
        let account_id = format!("{}.{}", receiver_alias.replace(".", "-"), ".typto.testnet");
        let clone = account_id.to_string().clone();
        let promise = Promise::new(account_id)
            .create_account()
            .transfer(env::attached_deposit());
            // .transfer(env::attached_deposit())
            // TODO: deploy to pending_receivers contract `Register`
            // .deploy_contract(PENDING_RECEIVERS.to_vec())
            //     .function_call(
            //         "new".to_string(),
            //         b"{}".to_vec(),
            //         0,
            //         Gas(20_000_000_000_000),
            //     )
            //     .function_call(
            //         "return_funds_and_self_destruct_pending_expiration"
            //     );
        let clone_2 = clone.clone();
        self.pending_receivers.insert(&receiver_alias, &clone_2);
        self.registered_receiver_id = Some((clone, ReceiverKind::Pending));
    }

    #[payable]
    pub fn send_tip(&mut self, receiver_alias: String, tip_amount: U128) {
        if let receiver_id = self.get_receiver_id(&receiver_alias).unwrap().0 {
            assert!(self.get_balance() >= tip_amount.0, "Insufficient funds");
            assert!(env::is_valid_account_id(env::signer_account_id().as_bytes()), "Invalid receiver account");
            let cloned_receiver_id = receiver_id.clone();
            Promise::new(receiver_id).transfer(tip_amount.0);
            log!("Transferred {} tokens from {} to {}", tip_amount.0, env::signer_account_id(), cloned_receiver_id);
        } else {
            // TODO: This shouldn't happen, as send_tip shuoldn't be exposed unless receiver is registered
        }
    }

    pub fn verify(
        &self,
        receiver_alias: &String,
        verified_receiver_id: AccountId
    ) {
        // TODO: 
        // 1. Assert that the signer id ends with .typto.{near, testnet}
        // 2. Lookup receiver_alias to get the `pending_receiver_id`
        // 3. call pending_receivers contract `Register.verify()`
        // 4. Upon verify confirmation (Promise?):
        //      1. Delete pending_receivers subaccount/contract with `verified_receiver_id` designated
        //          as the beneficiary
        //      2. Upon completion of 4.1 (Promise?)
        //          1. Pop alias from `pending_receivers` and insert to `verified_receivers`
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::MockedBlockchain;
    use near_sdk::{testing_env, VMContext};

    fn alice() -> AccountId {
        "alice.testnet".to_string()
    }
    fn bob() -> AccountId {
        "bob.testnet".to_string()
    }

    fn get_context(predecessor_account_id: String, storage_usage: u64) -> VMContext {
        VMContext {
            current_account_id: bob(), // Recipient of the transaction
            signer_account_id: alice(), // Originator of the transaction
            signer_account_pk: vec![0, 1, 2],
            predecessor_account_id,
            input: vec![],
            block_index: 0,
            block_timestamp: 0,
            account_balance: 0,
            account_locked_balance: 0,
            storage_usage,
            attached_deposit: 0,
            prepaid_gas: 10u64.pow(18),
            random_seed: vec![0, 1, 2],
            is_view: false,
            output_data_receivers: vec![],
            epoch_height: 19,
        }
    }

    #[test]
    fn test_register_pending_receiver() {
        let mut context = get_context(alice(), 0);
        const AMOUNT_TO_SEND: u128 = 1_000_000_000_000_000_000_000_000;
        context.account_balance = AMOUNT_TO_SEND;
        testing_env!(context.clone());
        let mut contract = Contract::new();
        contract.register_pending_receiver(bob(), U128(AMOUNT_TO_SEND));
        // let site = format!("{}{}", &bob(), ".com");
        // contract.send_tip(site, U128(AMOUNT_TO_SEND));
        // assert_eq!(contract.get_balance(), 0, "Account balance should be liquidated.");
    }

    // #[test]
    // fn test_get_receiver_id() {
    //     let mut context = get_context(alice(), 0);
    //     const AMOUNT_TO_SEND: u128 = 1_000_000_000_000_000_000_000_000;
    //     context.account_balance = AMOUNT_TO_SEND;
    //     testing_env!(context.clone());
    //     let mut contract = Contract::new();
    //     contract.register_receiver(bob());
    //     let newbob: String = bob();
    //     let site = format!("{}{}", &newbob, ".com");
    //     println!("should be true {}", contract.get_receiver_id(&site));
    //     // contract.register_receiver(alice());
    //     let _alice: String = alice();
    //     println!("should be false {}", contract.get_receiver_id(&_alice));
    //     // assert_eq!(contract.get_balance(), 0, "Account balance should be liquidated.");
    // }

    // #[test]
    // fn test_get_balance() {
    //     let mut context = get_context(alice(), 0);
    //     const AMOUNT_TO_SEND: u128 = 1_000_000_000_000_000_000_000_000;
    //     context.account_balance = AMOUNT_TO_SEND;
    //     testing_env!(context.clone());
    //     let mut contract = Contract::new();
    //     contract.register_receiver(bob());
    //     assert_eq!(contract.get_balance(), AMOUNT_TO_SEND, "Account balance should be equal to initial balance.");
    // }

    // #[test]
    // #[should_panic]
    // fn test_panic_user_not_registered() {
    //     let mut context = get_context(alice(), 0);
    //     const AMOUNT_TO_SEND: u128 = 1_000_000_000_000_000_000_000_000;
    //     context.account_balance = AMOUNT_TO_SEND;
    //     testing_env!(context.clone());
    //     let mut contract = Contract::new();
    //     contract.send_tip(bob(), AMOUNT_TO_SEND);
    // }

    // #[test]
    // #[should_panic]
    // fn test_panic_insufficient_funds() {
    //     let mut context = get_context(alice(), 0);
    //     const AMOUNT_TO_SEND: u128 = 1_000_000_000_000_000_000_000_000;
    //     const ACCOUNT_BALANCE: u128 = 1;
    //     context.account_balance = ACCOUNT_BALANCE;
    //     testing_env!(context.clone());
    //     let mut contract = Contract::new();
    //     contract.send_tip(bob(), AMOUNT_TO_SEND);
    // }
}