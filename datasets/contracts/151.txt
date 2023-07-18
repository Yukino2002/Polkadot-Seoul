/*
 * ggQuest Profiles Smart Contract
 *
 */

mod events;

use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::{LookupMap, UnorderedSet};
use near_sdk::json_types::U128;
use near_sdk::serde::{Deserialize, Serialize};
use near_sdk::{env, near_bindgen, require, AccountId, Balance, PanicOnDefault, Promise};

use crate::events::{
    AddOperatorLog, AddSupportedThirdPartyLog, BurnLog, DecreaseReputationLog, EventLog,
    EventLogVariant, IncreaseReputationLog, LinkThirdPartyToProfileLog, MintLog, RemoveOperatorLog,
    UnlinkThirdPartyToProfileLog, UpdateLog,
};

pub const GGQUEST_METADATA_SPEC: &str = "1.0.0";
pub const GGQUEST_STANDARD_NAME: &str = "ggProfiles";

pub type ThirdPartyId = String;

#[derive(BorshDeserialize, BorshSerialize, Serialize, Clone)]
#[serde(crate = "near_sdk::serde")]
pub struct ThirdParty {
    pub third_party_id: ThirdPartyId,
    pub user_id: U128,
}

#[derive(BorshDeserialize, BorshSerialize, Serialize, Clone)]
#[serde(crate = "near_sdk::serde")]
pub struct ProfileData {
    // Data of the user
    pub pseudo: String,
    pub profile_picture_url: String,
    pub cover_picture_url: String,
    pub is_registered: bool,

    // Reuptation
    pub gained_reputation: U128,
    pub lost_reputation: U128,

    // Associated third partires (e.g. Discord, Twitch, etc.)
    pub linked_third_parties: Vec<ThirdParty>,
}

#[derive(BorshDeserialize, BorshSerialize, Serialize, Deserialize, Clone)]
#[serde(crate = "near_sdk::serde")]
pub struct UpdatableByUserData {
    // Struct to facilitate ProfileData modifications by users
    pub pseudo: String,
    pub profile_picture_url: String,
    pub cover_picture_url: String,
}

/// Helper structure for keys of the persistent collections.
#[derive(BorshSerialize)]
pub enum StorageKey {
    ProfileDataPerOwner,
    OperatorStatusPerOwner,
    TakenPseudos,
    RegisteredAccounts,
    ThirdParties,
}

// Define the contract structure
#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize, PanicOnDefault)]
pub struct Contract {
    pub name: String,
    pub ticker: String,
    pub profiles: LookupMap<AccountId, ProfileData>,
    pub operators: LookupMap<AccountId, bool>,
    pub taken_pseudos: UnorderedSet<String>,
    pub registered_accounts: UnorderedSet<AccountId>,
    // Supported thirdParties (Twitch, Discord, Steam...)
    pub third_parties: UnorderedSet<String>,
}

// Implement the contract structure
#[near_bindgen]
impl Contract {
    #[init]
    pub fn new(name: String, ticker: String) -> Self {
        let mut operators =
            LookupMap::new(StorageKey::OperatorStatusPerOwner.try_to_vec().unwrap());

        operators.insert(&env::predecessor_account_id(), &true);

        Self {
            name,
            ticker,
            profiles: LookupMap::new(StorageKey::ProfileDataPerOwner.try_to_vec().unwrap()),
            operators,
            taken_pseudos: UnorderedSet::new(StorageKey::TakenPseudos.try_to_vec().unwrap()),
            registered_accounts: UnorderedSet::new(
                StorageKey::RegisteredAccounts.try_to_vec().unwrap(),
            ),
            third_parties: UnorderedSet::new(StorageKey::ThirdParties.try_to_vec().unwrap()),
        }
    }

    // Operator functions
    #[payable]
    pub fn add_operator(&mut self, account_id: AccountId) {
        assert!(self.is_caller_operator(), "Only operator can add operator");

        //measure the initial storage being used on the contract
        let initial_storage_usage = env::storage_usage();

        self.operators.insert(&account_id, &true);

        //calculate the required storage which was the used - initial
        let required_storage_in_bytes = env::storage_usage() - initial_storage_usage;

        //refund any excess storage if the user attached too much. Panic if they didn't attach enough to cover the required.
        self.refund_deposit(required_storage_in_bytes);

        // Emit operator event
        self.emit_event(EventLogVariant::AddOperator(AddOperatorLog {
            operator: account_id.clone(),
        }));
    }

    pub fn remove_operator(&mut self, account_id: AccountId) {
        assert!(
            self.is_caller_operator(),
            "Only operator can remove operator"
        );
        self.operators.remove(&account_id);

        // Emit emove operator event
        self.emit_event(EventLogVariant::RemoveOperator(RemoveOperatorLog {
            operator: account_id.clone(),
        }));
    }

    // Operator view functions
    pub fn is_operator(&self, account_id: AccountId) -> bool {
        self.operators.get(&account_id).unwrap_or(false)
    }

    // Operator private functions
    fn is_caller_operator(&self) -> bool {
        self.operators
            .get(&env::predecessor_account_id())
            .unwrap_or(false)
    }

    // Soulbound NFT functions
    #[payable]
    pub fn mint(&mut self, data: UpdatableByUserData) {
        assert!(
            !self.is_registered_account(env::predecessor_account_id()),
            "Account already registered"
        );

        //measure the initial storage being used on the contract
        let initial_storage_usage = env::storage_usage();

        let pseudo = data.pseudo.clone();

        self.internal_set_user_data(data);

        self.registered_accounts
            .insert(&env::predecessor_account_id());

        //calculate the required storage which was the used - initial
        let required_storage_in_bytes = env::storage_usage() - initial_storage_usage;

        //refund any excess storage if the user attached too much. Panic if they didn't attach enough to cover the required.
        self.refund_deposit(required_storage_in_bytes);

        // Emit Mint NFT event
        self.emit_event(EventLogVariant::Mint(MintLog {
            account_id: env::predecessor_account_id().clone(),
            pseudo,
        }));
    }

    pub fn burn(&mut self, account_id: AccountId) {
        assert!(
            self.is_caller_operator(),
            "Only operators have rights to delete user's data"
        );

        let profile_data = self
            .profiles
            .get(&account_id)
            .expect("Account not registered");

        self.taken_pseudos.remove(&profile_data.pseudo);
        self.profiles.remove(&account_id);
        self.registered_accounts.remove(&account_id);

        // Emit Burn NFT event
        self.emit_event(EventLogVariant::Burn(BurnLog { account_id }));
    }

    #[payable]
    pub fn update(&mut self, data: UpdatableByUserData) {
        assert!(
            self.is_registered_account(env::predecessor_account_id()),
            "Account not registered"
        );

        //measure the initial storage being used on the contract
        let initial_storage_usage = env::storage_usage();

        let pseudo = data.pseudo.clone();

        self.internal_set_user_data(data);

        //calculate the required storage which was the used - initial
        let required_storage_in_bytes = env::storage_usage() - initial_storage_usage;

        //refund any excess storage if the user attached too much. Panic if they didn't attach enough to cover the required.
        self.refund_deposit(required_storage_in_bytes);

        // Emit Update user data event
        self.emit_event(EventLogVariant::Update(UpdateLog {
            account_id: env::predecessor_account_id().clone(),
            pseudo,
        }));
    }

    pub fn increase_reputation(&mut self, account_id: AccountId, amount: U128) {
        assert!(
            self.is_caller_operator(),
            "Only operator have permission to increase reputation"
        );

        let mut profile_data = self
            .profiles
            .get(&account_id)
            .expect("Account not registered");

        profile_data.gained_reputation = U128(profile_data.gained_reputation.0 + amount.0);

        self.profiles.insert(&account_id, &profile_data);

        // Emit Increase reputation event
        self.emit_event(EventLogVariant::IncreaseReputation(IncreaseReputationLog {
            account_id,
            amount,
        }));
    }

    pub fn decrease_reputation(&mut self, account_id: AccountId, amount: U128) {
        assert!(
            self.is_caller_operator(),
            "Only operator have permission to decrease reputation"
        );

        let mut profile_data = self
            .profiles
            .get(&account_id)
            .expect("Account not registered");

        profile_data.lost_reputation = U128(profile_data.lost_reputation.0 + amount.0);

        self.profiles.insert(&account_id, &profile_data);

        // Emit Decrease reputation event
        self.emit_event(EventLogVariant::DecreaseReputation(DecreaseReputationLog {
            account_id,
            amount,
        }));
    }

    // SB NFT View functions
    pub fn get_reputation(&self, account_id: AccountId) -> (U128, U128) {
        let profile_data = self
            .profiles
            .get(&account_id)
            .expect("Account not registered");

        (profile_data.gained_reputation, profile_data.lost_reputation)
    }

    // Third party functions
    #[payable]
    pub fn add_third_party(&mut self, third_party_name: String) {
        assert!(
            self.is_caller_operator(),
            "Only operator can add third party"
        );

        //measure the initial storage being used on the contract
        let initial_storage_usage = env::storage_usage();

        self.third_parties.insert(&third_party_name);

        //calculate the required storage which was the used - initial
        let required_storage_in_bytes = env::storage_usage() - initial_storage_usage;

        //refund any excess storage if the user attached too much. Panic if they didn't attach enough to cover the required.
        self.refund_deposit(required_storage_in_bytes);

        // Emit Add third party event
        self.emit_event(EventLogVariant::AddSupportedThirdParty(
            AddSupportedThirdPartyLog {
                name: third_party_name,
            },
        ));
    }

    #[payable]
    pub fn link_third_party_to_profile(
        &mut self,
        account_id: AccountId,
        third_party_id: &String,
        third_party_user_id: U128,
    ) {
        assert!(
            self.is_caller_operator(),
            "Only operator can link third party to profile"
        );

        assert!(
            self.third_parties.contains(&third_party_id),
            "Third party not found"
        );

        let mut profile_data = self
            .profiles
            .get(&account_id)
            .expect("Account not registered");

        profile_data.linked_third_parties.iter().for_each(|t| {
            assert!(
                t.third_party_id != third_party_id.clone(),
                "Third party already linked to profile"
            )
        });

        profile_data.linked_third_parties.push(ThirdParty {
            third_party_id: third_party_id.clone(),
            user_id: third_party_user_id,
        });

        self.profiles.insert(&account_id, &profile_data);

        // Emit Link third party to profile event
        self.emit_event(EventLogVariant::LinkThirdPartyToProfile(
            LinkThirdPartyToProfileLog {
                account_id,
                third_party_id: third_party_id.clone(),
                third_party_user_id,
            },
        ));
    }

    pub fn unlink_third_party_from_profile(
        &mut self,
        account_id: AccountId,
        third_party_id: String,
    ) {
        assert!(
            self.is_caller_operator(),
            "Only operator can unlink third party from profile"
        );

        let mut profile_data = self
            .profiles
            .get(&account_id)
            .expect("Account not registered");

        let mut index = None;

        profile_data
            .linked_third_parties
            .iter()
            .enumerate()
            .for_each(|(i, t)| {
                if t.third_party_id == third_party_id {
                    index = Some(i);
                }
            });

        if let Some(i) = index {
            profile_data.linked_third_parties.remove(i);
        }

        self.profiles.insert(&account_id, &profile_data);

        // Emit Unlink third party from profile event
        self.emit_event(EventLogVariant::UnlinkThirdPartyToProfile(
            UnlinkThirdPartyToProfileLog {
                account_id,
                third_party_id,
            },
        ));
    }

    // Third party view functions
    pub fn get_third_parties(&self) -> Vec<String> {
        self.third_parties.to_vec()
    }

    pub fn get_registered_accounts(&self) -> Vec<AccountId> {
        self.registered_accounts.iter().collect()
    }

    pub fn has_profile_data(&self, account_id: AccountId) -> bool {
        self.profiles.contains_key(&account_id)
    }

    pub fn is_available_pseudo(&self, pseudo: String) -> bool {
        !self.taken_pseudos.contains(&pseudo)
    }

    pub fn get_profile_data(&self, account_id: AccountId) -> ProfileData {
        self.profiles
            .get(&account_id)
            .expect("Account not registered")
    }

    // SB NFT Private functions
    fn is_registered_account(&self, account_id: AccountId) -> bool {
        self.registered_accounts.contains(&account_id)
    }

    fn is_taken_pseudo(&self, pseudo: String) -> bool {
        self.taken_pseudos.contains(&pseudo)
    }

    fn internal_set_user_data(&mut self, data: UpdatableByUserData) {
        require!(data.pseudo.len() > 0, "Pseudo cannot be empty");

        // Get the profile data or create a new one if it doesn't exist
        let mut profile_data = self
            .profiles
            .get(&env::predecessor_account_id())
            .unwrap_or_else(|| {
                require!(
                    !self.is_taken_pseudo(data.pseudo.clone()),
                    "Pseudo already taken by another account"
                );

                self.taken_pseudos.insert(&data.pseudo.clone());

                ProfileData {
                    pseudo: data.pseudo.clone(),
                    profile_picture_url: "".to_string(),
                    cover_picture_url: "".to_string(),
                    is_registered: true,
                    gained_reputation: U128(0),
                    lost_reputation: U128(0),
                    linked_third_parties: Vec::new(),
                }
            });

        // Check if pseudo is already taken by another account
        require!(
            !self.is_taken_pseudo(data.pseudo.clone()) || profile_data.pseudo == data.pseudo,
            "Pseudo is not available"
        );

        // Update pseudo if modified
        if profile_data.pseudo != data.pseudo {
            self.taken_pseudos.remove(&profile_data.pseudo);
            self.taken_pseudos.insert(&data.pseudo);
        }

        // Update profile data
        profile_data.pseudo = data.pseudo.clone();
        profile_data.profile_picture_url = data.profile_picture_url.clone();
        profile_data.cover_picture_url = data.cover_picture_url.clone();

        self.profiles
            .insert(&env::predecessor_account_id(), &profile_data);
    }

    //refund the initial deposit based on the amount of storage that was used up
    fn refund_deposit(&mut self, storage_used: u64) {
        //get how much it would cost to store the information
        let required_cost = env::storage_byte_cost() * Balance::from(storage_used);
        //get the attached deposit
        let attached_deposit = env::attached_deposit();

        //make sure that the attached deposit is greater than or equal to the required cost
        assert!(
            required_cost <= attached_deposit,
            "Must attach {} yoctoNEAR to cover storage",
            required_cost,
        );

        //get the refund amount from the attached deposit - required cost
        let refund = attached_deposit - required_cost;

        //if the refund is greater than 1 yocto NEAR, we refund the predecessor that amount
        if refund > 1 {
            Promise::new(env::predecessor_account_id()).transfer(refund);
        }
    }

    // Utility method to emit an event
    fn emit_event(&self, event_log_variant: EventLogVariant) {
        let log: EventLog = EventLog {
            standard: GGQUEST_STANDARD_NAME.to_string(),
            version: GGQUEST_METADATA_SPEC.to_string(),
            event: event_log_variant,
        };

        // Log the serialized json.
        env::log_str(&log.to_string());
    }
}

/*
 * Inline tests for the code above
 */
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn get_default_greeting() {
        let contract = Contract::default();
    }
}
