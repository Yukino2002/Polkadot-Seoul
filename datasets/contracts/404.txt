use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::serde::{Deserialize, Serialize};
use near_sdk::{env, near_bindgen, Promise};
use std::collections::HashMap;

pub type AccountId = String;

//once the user has logged in with his near credentials,
// he is able to update his account details
#[derive(Clone, Serialize, Deserialize, BorshDeserialize, BorshSerialize, Debug)]
#[serde(crate = "near_sdk::serde")]
pub struct AppUser {
  id: u32,
  name: String,
  username: AccountId,
  usertype: String,
  contact: String,
}

impl AppUser {
  // we initialize the fields we shall use when adding a new user
  pub fn new(id: u32, name: String, usertype: String, contact: String) -> Self {
    AppUser {
      id,
      name,
      username: env::signer_account_id().to_string(),
      usertype,
      contact,
    }
  }
}

// Properties
#[derive(Clone, Serialize, Deserialize, BorshDeserialize, BorshSerialize, Debug)]
#[serde(crate = "near_sdk::serde")]
pub struct Property {
  id: String,
  property_name: String,
  price: u128,
  location: String,
  owner: AccountId,
  status: String,
  description: String,
  images: Vec<String>,
}

impl Property {
  // initialization to be called inside the function dealing with the addition of properties
  pub fn new(
    id: String,
    property_name: String,
    price: u128,
    location: String,
    description: String,
    images: Vec<String>,
  ) -> Self {
    Property {
      id,
      property_name,
      price,
      location,
      owner: env::signer_account_id().to_string(),
      status: "available".to_string(),
      description,
      images,
    }
  }
}

#[near_bindgen]
#[derive(Clone, Default, BorshDeserialize, BorshSerialize, Debug)]

pub struct Contract {
  account_owner: AccountId,
  // users collection
  users: HashMap<String, AppUser>,
  // user properties collection
  user_properties: HashMap<String, Property>,
}

#[near_bindgen]
impl Contract {
  #[init]
  pub fn new(account_owner: AccountId) -> Self {
    let users: HashMap<String, AppUser> = HashMap::new();
    let user_properties: HashMap<String, Property> = HashMap::new();

    Contract {
      account_owner,
      users,
      user_properties,
    }
  }

  // works only if the user is logged in
  // allows the users to fill in their data
  pub fn reg_user(&mut self, name: String, usertype: String, contact: String) {
    // identification taking the current length of the hashmap and making sure it's an unsigned integer
    let id = self.users.len() as u32;
    // getting the account id of the currently signed in user
    let username = env::signer_account_id().to_string();
    // making sure you don't register twice. though no new data could be added again coz in our logic,
    // trying to insert a hashmap with a key that allready exists only edit's the data.
    // anyway i thought it would bring a nicer experience doing it like this
    match self.users.get(&username) {
      Some(_) => env::log_str("you can't register your data twice"),
      None => {
        self
          .users
          .insert(username, AppUser::new(id, name, usertype, contact));
        env::log_str("your data has been registered successfully");
      }
    }
  }

  // addition of a new property
  // I decided to include the image... storing a fake directory in the url for now.
  // when the customer views the properties

  pub fn new_property(
    &mut self,
    id: String,
    property_name: String,
    price: u128,
    location: String,
    description: String,
    images: Vec<String>,
  ) -> String {
    match self.user_properties.get_mut(&id) {
      #[allow(unused_variables)]
      Some(id) => {
        env::log_str("Hash Clash, try again...");
        "property_exist".to_string()
      }
      None => {
        self.user_properties.insert(
          id.to_string(),
          Property::new(id, property_name, price, location, description, images),
        );
        env::log_str("property_added_successfully");
        "property_added".to_string()
      }
    }
  }

  /*
    // counting the number of overall properties added
    pub fn count_properties(&mut self) -> usize {
      self.user_properties.len()
    }
  */
  pub fn edit_account(&mut self, name: String, usertype: String, contact: String) -> String {
    // inserting a value to the hashmap with the same key automatically edits the value of the hashmap.
    // we will use this to implement the editing of user details
    // your near account acts as the key hence its the onnly yhing that cant be changed
    let username = env::signer_account_id().to_string();
    // we want to make sure that the user id gets retained.
    match self.users.get(&username) {
      // we access the key using the match function and wrap our value inside Some
      Some(value) => {
        // i think we now have access to the data we need to manipulate
        let id = value.id;
        // inserting the same key in a hashmap edits it.
        if username == env::signer_account_id().to_string() {
          self
            .users
            .insert(username, AppUser::new(id, name, usertype, contact));
          env::log_str("Your Data has been edited successfully");
          "data_edited_successfully".to_string()
        } else {
          env::log_str("you need to be logged in to this account");
          "kindly_log_in".to_string()
        }
      }
      None => {
        // this means that when the user logged in, he didn't update his account details.
        // in this case when we try to get it returns None
        env::log_str("you cant edit null data");
        "null_data".to_string()
      }
    }
  }

  /*
  // viewing my account details
  pub fn view_account(&self) -> Option<&AppUser> {
    let username = env::signer_account_id().to_string();
    match &self.users.get(&username) {
      Some(value) => return Some(value),
      None => return None,
    }
  }

  */

  pub fn view_account(&self) -> HashMap<String, &AppUser> {
    let mut user_account = HashMap::new();
    let logged_in_account = env::signer_account_id().to_string();
    match &self.users.get(&logged_in_account) {
      Some(value) => {
        user_account.insert(env::signer_account_id().to_string(), value.clone());
        user_account
      }
      None => {
        env::log_str("invalid account");
        user_account
      }
    }
  }

  pub fn list_properties(&self) -> &HashMap<String, Property> {
    &self.user_properties
  }

  // list owners properties
  pub fn my_properties(&self) -> HashMap<String, &Property> {
    let mut my_properties = HashMap::new();
    for (key, value) in &self.user_properties {
      if value.owner == env::signer_account_id().to_string() {
        my_properties.insert(value.id.to_string(), value);
      }
    }
    my_properties
  }

  pub fn buy_property(&mut self, id: String) -> String {
    let a_near: u128 = 1_000_000_000_000_000_000_000_000;
    let properties = &mut self.user_properties;
    match self.user_properties.get_mut(&id) {
      Some(property) => {
        if property.status == "awaiting_verification" || property.status == "bought" {
          env::log_str("the property has either been bought or is awaiting verification");
          "awaiting_verification".to_string()
        } else {
          let signer_account_balance: u128 = env::account_balance();
          if signer_account_balance < property.price {
            env::log_str("sorry, you dont have enough money to make this transaction");
            "not_enough_money".to_string()
          } else {
            // 0702 597 349
            Promise::new(env::current_account_id()).transfer(property.price * a_near);
            env::log_str("transaction successful, verify property to complete the transaction");
            property.owner = env::signer_account_id().to_string();
            "transaction_successful".to_string()
          }
        }
      }
      None => {
        env::log_str("no property found with that id");
        "no_property".to_string()
      }
    }
  }
}

#[cfg(test)]
mod tests {
  use super::*;
  use near_sdk::test_utils::VMContextBuilder;
  use near_sdk::{testing_env, AccountId};

  fn get_context(predecessor: AccountId) -> VMContextBuilder {
    let mut builder = VMContextBuilder::new();
    builder.signer_account_id(predecessor);
    builder.account_balance(1_000_000_000_000_000_000_000_000_000_000);
    builder
  }

  #[test]
  fn reg_user() {
    let felix = AccountId::new_unchecked("felix.testnet".to_string());
    let context = get_context(felix.clone());
    testing_env!(context.build());

    let mut contract = Contract::new(felix.to_string());
    contract.reg_user(
      "Felix Awere".to_string(),
      "Agent".to_string(),
      "0731862583".to_string(),
    );
    let result = contract.users.len();
    assert_eq!(result, 1);
  }

  #[test]
  fn check_user_registered_once() {
    let felix = AccountId::new_unchecked("felix.testnet".to_string());
    let molly = AccountId::new_unchecked("molly.testnet".to_string());

    let context = get_context(felix.clone());
    let context2 = get_context(molly.clone());
    testing_env!(context.build());
    testing_env!(context2.build());

    let mut user1 = Contract::new(felix.to_string());
    let mut user2 = Contract::new(molly.to_string());

    user1.reg_user(
      "Felix Awere".to_string(),
      "Agent".to_string(),
      "0731862583".to_string(),
    );
    user2.reg_user(
      "Molly Achieng".to_string(),
      "Agent".to_string(),
      "0731862583".to_string(),
    );
    let mut result = user1.users.len();
    assert_eq!(result, 1);
    result = user2.users.len();
    assert_eq!(result, 1);
    user2.reg_user(
      "Molly Achieng".to_string(),
      "Agent".to_string(),
      "0731862583".to_string(),
    );
    result = user2.users.len();
    assert_eq!(result, 1);
  }

  #[test]
  fn test_property_added() {
    let felix = AccountId::new_unchecked("felix.testnet".to_string());
    let context = get_context(felix.clone());
    testing_env!(context.build());

    let mut user1 = Contract::new(felix.to_string());
    user1.new_property(
      "ytyTYhYrE788".to_string(),
      "39 Riara".to_string(),
      30_000,
      "Nairobi".to_string(),
      "a very nice house to spend in pet friendly".to_string(),
      vec![
        "path_to_image1".to_string(),
        "path_to_image2".to_string(),
        "path_to_image3".to_string(),
        "path_to_image4".to_string(),
        "path_to_image5".to_string(),
      ],
    );
    user1.new_property(
      "ytyTYhYrE588".to_string(),
      "48 Mango".to_string(),
      300_000,
      "Nairobi".to_string(),
      "a very nice house to spend in pet friendly".to_string(),
      vec![
        "path_to_image1".to_string(),
        "path_to_image2".to_string(),
        "path_to_image3".to_string(),
        "path_to_image4".to_string(),
        "path_to_image5".to_string(),
      ],
    );
    let result = user1.user_properties.len();
    assert_eq!(result, 2);
  }

  #[test]
  fn test_property_bought() {
    let felix = AccountId::new_unchecked("felix.testnet".to_string());
    let context = get_context(felix.clone());
    testing_env!(context.build());

    let mut user1 = Contract::new(felix.to_string());
    user1.new_property(
      "ytyTYhYrE788".to_string(),
      "39 Riara".to_string(),
      30_000,
      "Nairobi".to_string(),
      "a very nice house to spend in pet friendly".to_string(),
      vec![
        "path_to_image1".to_string(),
        "path_to_image2".to_string(),
        "path_to_image3".to_string(),
        "path_to_image4".to_string(),
        "path_to_image5".to_string(),
      ],
    );
    user1.buy_property("ytyTYhYrE788".to_string());
    let properties = user1.list_properties();
    let bought = "ytyTYhYrE788".to_string();
    match user1.user_properties.get(&bought) {
      Some(val) => {
        assert_eq!(val.id, "ytyTYhYrE788".to_string());
      }
      None => {
        env::log_str("not found");
      }
    }
  }

  #[test]
  fn view_user() {
    let felix = AccountId::new_unchecked("felix.testnet".to_string());
    let context = get_context(felix.clone());
    testing_env!(context.build());

    let mut contract = Contract::new(felix.to_string());
    println!("{:?}", contract);
    contract.reg_user(
      "Felix Awere".to_string(),
      "Agent".to_string(),
      "0731862583".to_string(),
    );
    println!("{:?}", contract.view_account());
    let my_details = contract.view_account();
    let current = env::signer_account_id().to_string();
    match contract.users.get(&current) {
      Some(val) => {
        assert_eq!(
          env::signer_account_id().to_string(),
          val.username.to_string()
        );
      }
      None => {
        env::log_str("nothing");
      }
    }
  }

  #[test]
  fn view_my_properties() {
    let felix = AccountId::new_unchecked("felix.testnet".to_string());
    let context = get_context(felix.clone());
    testing_env!(context.build());

    let mut user1 = Contract::new(felix.to_string());
    user1.new_property(
      "ytyTYhYrE788".to_string(),
      "39 Riara".to_string(),
      30_000,
      "Nairobi".to_string(),
      "a very nice house to spend in pet friendly".to_string(),
      vec![
        "path_to_image1".to_string(),
        "path_to_image2".to_string(),
        "path_to_image3".to_string(),
        "path_to_image4".to_string(),
        "path_to_image5".to_string(),
      ],
    );
    user1.new_property(
      "ytyTYhYrE788".to_string(),
      "48 Mango".to_string(),
      300_000,
      "Nairobi".to_string(),
      "a very nice house to spend in pet friendly".to_string(),
      vec![
        "path_to_image1".to_string(),
        "path_to_image2".to_string(),
        "path_to_image3".to_string(),
        "path_to_image4".to_string(),
        "path_to_image5".to_string(),
      ],
    );

    let my_properties = user1.my_properties();
    // println!("{:?}", my_properties);
    for (key, value) in my_properties {
      println!("{:?}", value);
      assert_eq!(value.owner, env::signer_account_id().to_string());
    }
  }
}
