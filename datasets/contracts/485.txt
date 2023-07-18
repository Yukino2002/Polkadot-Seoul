/*
 * This is an example of a Rust smart contract with two simple, symmetric functions:
 *
 * 1. set_greeting: accepts a greeting, such as "howdy", and records it for the user (account_id)
 *    who sent the request
 * 2. get_greeting: accepts an account_id and returns the greeting saved for it, defaulting to
 *    "Hello"
 *
 * Learn more about writing NEAR smart contracts with Rust:
 * https://github.com/near/near-sdk-rs
 *
 */

// To conserve gas, efficient serialization is achieved through Borsh (http://borsh.io/)
use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::{env, near_bindgen, setup_alloc};
use near_sdk::collections::LookupMap;

setup_alloc!();

// Structs in Rust are similar to other languages, and may include impl keyword as shown below
// Note: the names of the structs are not important when calling the smart contract, but the function names are
#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize)]
pub struct Profil {
    records: LookupMap<String, String>,
    title: String,
    desc: String,
    img: String,
}

impl Default for Profil {
  fn default() -> Self {
    Self {
      records: LookupMap::new(b"a".to_vec()),
      title: String::from("No Title"),
      desc: String::from("No Desc"),
      img: String::from("No Img"),
    }
  }
}

#[near_bindgen]
impl Profil {
    pub fn get_title(&self, account_id: String) -> String {
        match self.records.get(&account_id) {
            Some(title) => title,
            None => "No Title".to_string(),
        }
    }

    pub fn get_desc(&self, account_id: String) -> String {
        match self.records.get(&account_id) {
            Some(desc) => desc,
            None => "No Desc".to_string(),
        }
    }


    pub fn get_img(&self, account_id: String) -> String {
        match self.records.get(&account_id) {
            Some(img) => img,
            None => "No Img".to_string(),
        }
    }
    
    pub fn set_title(&mut self, message: String) {
        let account_id = env::signer_account_id();
        let title = format!("{} for account {}", message, account_id);
        env::log(title.as_bytes());

        self.records.insert(&account_id, &title);
    }

    pub fn set_desc(&mut self, message: String) {
        let account_id = env::signer_account_id();
        let desc = format!("{} for account {}", message, account_id);
        env::log(desc.as_bytes());

        self.records.insert(&account_id, &desc);
    }

    pub fn set_img(&mut self, image_link: String) {
        let account_id = env::signer_account_id();
        env::log(image_link.as_bytes());

        self.records.insert(&account_id, &image_link);
    }
}

/*
 * TEST
 * Learn more about Rust tests: https://doc.rust-lang.org/book/ch11-01-writing-tests.html
 *
 * To run from contract directory:
 * cargo test -- --nocapture
 *
 * From project root, to run in combination with frontend tests:
 * yarn test
 *
 */
#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::MockedBlockchain;
    use near_sdk::{testing_env, VMContext};

    // mock the context for testing, notice "signer_account_id" that was accessed above from env::
    fn get_context(input: Vec<u8>, is_view: bool) -> VMContext {
        VMContext {
            current_account_id: "alice_near".to_string(),
            signer_account_id: "bob_near".to_string(),
            signer_account_pk: vec![0, 1, 2],
            predecessor_account_id: "carol_near".to_string(),
            input,
            block_index: 0,
            block_timestamp: 0,
            account_balance: 0,
            account_locked_balance: 0,
            storage_usage: 0,
            attached_deposit: 0,
            prepaid_gas: 10u64.pow(18),
            random_seed: vec![0, 1, 2],
            is_view,
            output_data_receivers: vec![],
            epoch_height: 19,
        }
    }

    #[test]
    fn set_then_get_title() {
        let context = get_context(vec![], false);
        testing_env!(context);
        let mut contract = Profil::default();
        contract.set_title("Title".to_string());
        assert_eq!(
            "Title for account bob_near".to_string(),
            contract.get_title("bob_near".to_string())
        );
    }

    #[test]
    fn get_default_title() {
        let context = get_context(vec![], true);
        testing_env!(context);
        let contract = Profil::default();
        assert_eq!(
            "No Title".to_string(),
            contract.get_title("francis.near".to_string())
        );
    }

    #[test]
    fn set_then_get_desc() {
        let context = get_context(vec![], false);
        testing_env!(context);
        let mut contract = Profil::default();
        contract.set_desc("A Desc".to_string());
        assert_eq!(
            "A Desc for account bob_near".to_string(),
            contract.get_desc("bob_near".to_string())
        );
    }

    #[test]
    fn get_default_desc() {
        let context = get_context(vec![], true);
        testing_env!(context);
        let contract = Profil::default();
        assert_eq!(
            "No Desc".to_string(),
            contract.get_desc("francis.near".to_string())
        );
    }


    #[test]
    fn set_then_get_img() {
        let context = get_context(vec![], false);
        testing_env!(context);
        let mut contract = Profil::default();
        contract.set_img("https://ipfs.fleek.co/ipfs/bafkreifui6q2p7yuk5kmprajbqd6a7xljkhl4mh6tcjalxnjquf7zs77ve".to_string());
        assert_eq!(
            "https://ipfs.fleek.co/ipfs/bafkreifui6q2p7yuk5kmprajbqd6a7xljkhl4mh6tcjalxnjquf7zs77ve".to_string(),
            contract.get_img("bob_near".to_string())
        );
    }

    #[test]
    fn get_default_img() {
        let context = get_context(vec![], true);
        testing_env!(context);
        let contract = Profil::default();
        assert_eq!(
            "No Img".to_string(),
            contract.get_img("francis.near".to_string())
        );
    }

}
