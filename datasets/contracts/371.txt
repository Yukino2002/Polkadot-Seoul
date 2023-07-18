use std::collections::HashMap;
use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::{LazyOption, LookupMap, UnorderedMap, UnorderedSet};
use near_sdk::json_types::{Base64VecU8, U128};
use near_sdk::serde::{Deserialize, Serialize};
use near_sdk::{CryptoHash, PanicOnDefault, Promise, PromiseOrValue};
use near_sdk::{env, near_bindgen, ext_contract, AccountId, Balance};
pub use common_types::policy::{AllPolicies, IsAvailableResponseData, LimitationData, PolicyData};
pub use common_types::types::{NFTContractMetadata, Token, TokenLicense, TokenMetadata};
pub use common_types::types::{LicenseToken, FilterOpt};
pub use common_types::utils::*;
pub use common_types::types::{InventoryLicense, JsonAssetToken, SKUAvailability};
pub use common_types::types::{ExtendedInventoryMetadata, FullInventory, InventoryContractMetadata};
use common_types::types::ShrinkedLicenseToken;

use crate::internal::*;
pub use crate::metadata::*;
pub use crate::mint::*;
pub use crate::nft_core::*;
pub use crate::approval::*;
pub use crate::royalty::*;
pub use crate::events::*;
pub use crate::license::*;

mod internal;
pub mod approval;
mod enumeration; 
pub mod metadata;
pub mod mint;
pub mod nft_core;
mod royalty; 
mod events;
pub mod license;
mod tests;

/// This spec can be treated like a version of the standard.
pub const NFT_METADATA_SPEC: &str = "nft-1.0.0";
/// This is the name of the NFT standard we're using
pub const NFT_STANDARD_NAME: &str = "nep171";
/// This spec can be treated like a version of the standard.
pub const NFT_LICENSE_SPEC: &str = "nftsentry-1.0.0";
/// This is the name of the NFT standard we're using
pub const NFT_LICENSE_STANDARD_NAME: &str = "nepTBD";
pub const MAX_LIMIT: u64 = 1_000_000;

#[derive(BorshDeserialize, BorshSerialize, Serialize, Deserialize, Clone)]
#[serde(crate = "near_sdk::serde")]
pub struct BenefitConfig {
    account_id: AccountId,
    fee_milli_percent_amount: u32,
}

#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize, PanicOnDefault)]
pub struct Contract {
    //contract owner
    pub owner_id: AccountId,
    pub inventory_id: AccountId,
    pub policy_contract: AccountId,
    pub benefit_config: Option<BenefitConfig>,

    //keeps track of all the token IDs for a given account
    pub tokens_per_owner: LookupMap<AccountId, UnorderedSet<TokenId>>,
    pub tokens_per_asset: LookupMap<String, UnorderedSet<TokenId>>,

    //keeps track of the token struct for a given token ID
    pub tokens_by_id: UnorderedMap<TokenId, Token>,

    //keeps track of the token metadata for a given token ID
    // pub token_metadata_by_id: UnorderedMap<TokenId, TokenMetadata>,

    //keeps track of the token license for a given token ID
    // pub token_license_by_id: UnorderedMap<TokenId, TokenLicense>,

    //keeps track of the token license for a given token ID
    // pub token_proposed_license_by_id: UnorderedMap<TokenId, TokenLicense>,

    //keeps track of the metadata for the contract
    pub metadata: LazyOption<NFTContractMetadata>,
}

#[ext_contract(inventory_contract)]
pub trait InventoryContract {
    fn inventory_metadata(&self) -> ExtendedInventoryMetadata;
    fn on_nft_mint(&mut self, token_id: String, token_count: u64) -> Option<String>;
    fn asset_token(&self, token_id: String) -> Option<JsonAssetToken>;
    fn asset_tokens(&self, from_index: Option<U128>, limit: Option<u64>) -> Vec<JsonAssetToken>;
}

#[ext_contract(policy_rules_contract)]
pub trait PolicyRulesContract {
    fn check_transition(
        &self, inventory: FullInventory, old: ShrinkedLicenseToken, new: ShrinkedLicenseToken,
        policy_rules: Option<Vec<LimitationData>>, upgrade_rules: Option<Vec<PolicyData>>
    ) -> Result<IsAvailableResponseData, String>;
    fn check_new(
        &self, inventory: FullInventory, new: ShrinkedLicenseToken, policy_rules: Option<Vec<LimitationData>>,
        upgrade_rules: Option<Vec<PolicyData>>) -> IsAvailableResponseData;
}

/// Helper structure for keys of the persistent collections.
#[derive(BorshSerialize)]
pub enum StorageKey {
    TokensPerOwner,
    TokensPerAsset,
    TokensPerAssetInner { asset_hash: CryptoHash },
    TokenPerOwnerInner { account_id_hash: CryptoHash },
    TokensById,
    TokenMetadataById,
    TokenLicenseById,
    TokenProposedLicenseById,
    NFTContractMetadata,
    TokensPerType,
    TokensPerTypeInner { token_type_hash: CryptoHash },
    TokenTypesLocked,
}

#[near_bindgen]
impl Contract {
    /*
        initialization function (can only be called once).
        this initializes the contract with default metadata so the
        user doesn't have to manually type metadata.
    */
    #[init]
    pub fn new_default_meta(owner_id: AccountId, inventory_id: AccountId) -> Self {
        //calls the other function "new: with some default metadata and the owner_id passed in 
        Self::new(
            owner_id,
            inventory_id,
            None,
            NFTContractMetadata {
                spec: "nft-1.0.0".to_string(),
                name: "NFTSentry Contract 0.0.1".to_string(),
                symbol: "SENTRY".to_string(),
                icon: None,
                base_uri: None,
                reference: None,
                reference_hash: None,
            },
            None,
        )
    }

    /*
        initialization function (can only be called once).
        this initializes the contract with metadata that was passed in and
        the owner_id. 
    */
    #[init]
    pub fn new(owner_id: AccountId, inventory_id: AccountId,
               benefit_config: Option<BenefitConfig>, metadata: NFTContractMetadata, policy_contract: Option<AccountId>) -> Self {
        //create a variable of type Self with all the fields initialized.
        let this = Self {
            //Storage keys are simply the prefixes used for the collections. This helps avoid data collision
            tokens_per_owner: LookupMap::new(StorageKey::TokensPerOwner.try_to_vec().unwrap()),
            tokens_per_asset: LookupMap::new(StorageKey::TokensPerAsset.try_to_vec().unwrap()),
            tokens_by_id: UnorderedMap::new(StorageKey::TokensById.try_to_vec().unwrap()),
            // token_metadata_by_id: UnorderedMap::new(
            //     StorageKey::TokenMetadataById.try_to_vec().unwrap(),
            // ),
            // token_license_by_id: UnorderedMap::new(
            //     StorageKey::TokenLicenseById.try_to_vec().unwrap(),
            // ),
            // token_proposed_license_by_id: UnorderedMap::new(
            //     StorageKey::TokenProposedLicenseById.try_to_vec().unwrap(),
            // ),
            //set the owner_id field equal to the passed in owner_id. 
            owner_id,
            inventory_id,
            metadata: LazyOption::new(
                StorageKey::NFTContractMetadata.try_to_vec().unwrap(),
                Some(&metadata),
            ),
            policy_contract: policy_contract.unwrap_or(AccountId::new_unchecked("policies.rocketscience.testnet".to_string())),
            benefit_config,
        };

        //return the Contract object
        this
    }

    #[init]
    #[payable]
    pub fn restore(owner_id: AccountId, inventory_id: AccountId,
                   benefit_config: Option<BenefitConfig>, metadata: NFTContractMetadata,
                   tokens: Vec<LicenseToken>, policy_contract: Option<AccountId>) -> Self {
        // let initial_storage_usage = env::storage_usage();
        // Restore metadata
        let mut this = Self::new(owner_id, inventory_id, benefit_config, metadata.clone(), policy_contract);

        let _logs = this._restore_data(metadata, tokens);

        //calculate the required storage which was the used - initial
        // let required_storage_in_bytes = env::storage_usage() - initial_storage_usage;

        //refund any excess storage if the user attached too much. Panic if they didn't attach enough to cover the required.
        // let _ = refund_deposit(required_storage_in_bytes, None, None);

        // Do not log mints
        // for log in logs {
        //     this.log_event(&log.to_string())
        // }

        this
    }

    #[payable]
    fn _restore_data(&mut self, metadata: NFTContractMetadata, tokens: Vec<LicenseToken>) -> Vec<EventLog> {
        let mut logs: Vec<EventLog> = Vec::new();

        self.metadata.replace(&metadata);

        for mut token in tokens {
            token.migrate_metadata_from();
            let mint_res = self.internal_mint(token);
            if mint_res.is_err() {
                unsafe {
                    env::panic_str(&*mint_res.unwrap_err_unchecked())
                }
            }
            logs.push(mint_res.unwrap());
        }

        logs
    }

    pub fn clean(&self, keys: Vec<Base64VecU8>) {
        let sender = env::predecessor_account_id();
        if sender != self.owner_id && sender != env::current_account_id() {
            env::panic_str("Unauthorized")
        }
        for key in keys.iter() {
            env::storage_remove(&key.0);
        }
    }
}