use near_sdk::{near_bindgen, PanicOnDefault, serde_json};
use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::UnorderedMap;
use near_sdk::serde::{Serialize, Deserialize};

near_sdk::setup_alloc!();

#[derive(Debug, Serialize, Deserialize, BorshDeserialize, BorshSerialize)]
#[serde(crate = "near_sdk::serde")]
pub struct Combinations {
    c123: usize,
    c234: usize,
    c345: usize,
}

#[derive(Debug, Serialize, Deserialize, BorshDeserialize, BorshSerialize)]
#[serde(crate = "near_sdk::serde")]
pub struct Attributes {
    in_game_ad_clicks: usize,
    google_links: usize,
    pop_up_ads: usize,
    video_ads: usize,
    banner_ads: usize,
}

#[derive(Debug, Serialize, BorshDeserialize, BorshSerialize)]
#[serde(crate = "near_sdk::serde")]
pub struct Channel {
    item_id: String,
    first_interaction: Attributes,
    last_interaction: Attributes,
    shapley_value: Combinations,
}

#[near_bindgen]
#[derive(PanicOnDefault, BorshDeserialize, BorshSerialize)]
pub struct Contract {
    adv_channel: UnorderedMap<String, Channel>,
}

#[near_bindgen]
impl Contract {
    #[init]
    pub fn init() -> Self {
        Self {
            adv_channel: UnorderedMap::new(b'a')
        }
    }

    pub fn add_item(&mut self,
                    item_id: String,
                    first_interaction: String,
                    last_interaction: String,
                    shapley_value: String,
    ) {
        let first_interaction: Attributes = serde_json::from_slice(first_interaction.as_bytes()).unwrap();
        let last_interaction: Attributes = serde_json::from_slice(last_interaction.as_bytes()).unwrap();
        let shapley_value: Combinations = serde_json::from_slice(shapley_value.as_bytes()).unwrap();
        self.adv_channel.insert(&item_id.clone(), &Channel {
            item_id,
            first_interaction,
            last_interaction,
            shapley_value,
        });
    }

    pub fn get_item(&self, item_id: String) -> String {
        match self.adv_channel.get(&item_id) {
            Some(val) => {
                serde_json::to_string(&val).unwrap()
            }
            None => "not found".to_string()
        }
    }

    pub fn all_keys(&self) -> String {
        let all_keys = self.adv_channel.keys_as_vector();
        let mut res_string: String = "".into();
        for k in all_keys.iter() {
            let res_key = format!("{};", k);
            res_string.push_str(&res_key);
        }
        res_string
    }

    pub fn get_item_oracle(&self) -> String {
        "item oracle success".to_string()
    }
}