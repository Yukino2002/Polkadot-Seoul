//! # Asset ERC721
//!
//! This is an ERC721 Asset Implementation
//!
//! ## Overview
//!
//! This contract manage a supply chain of assets
//!
//! ## Error Handling
//!
//! Any function that modifies the state returns a Result type and does not changes the state
//! if the Error occurs.
//! The errors are defined as an Enum type. Any other error or invariant violation
//! triggers a panic and therefore rolls back the transaction.
//!

#![cfg_attr(not(feature = "std"), no_std)]
use ink_lang as ink;


#[ink::contract]
mod asset_erc721 {
    #[cfg(not(feature = "ink-as-dependency"))]
    use ink_storage::collections::{
        hashmap::Entry,
        HashMap as StorageHashMap,
    };
    use scale::{
        Decode,
        Encode,
    };

    /// Asset ID
    pub type AssetId = u32;

    #[ink(storage)]
    #[derive(Default)]
    pub struct AssetErc721 {
        /// Mapping from asset to owner.
        asset_owner: StorageHashMap<AssetId, AccountId>,
        /// Main description of the asset
        asset_description: StorageHashMap<AssetId,Hash>,
        /// Main photo of the asset - Ipfs Address
        asset_photo: StorageHashMap<AssetId, Hash>,
        /// Category of the asset
        asset_category: StorageHashMap<AssetId, u32>,
        /// Stores the id and description to the allowed categories of assets
        asset_category_description: StorageHashMap<AssetId,Hash>,
        /// Location of the asset
        asset_location: StorageHashMap<AssetId,Hash>,
        // Additional Metadata of the Asset
        asset_metadata: StorageHashMap<AssetId, Hash>,
        // Stores the  assets validation from an administrator role
        asset_validation: StorageHashMap<AssetId, AccountId>,
        /// Stores the proxy accounts for the assets, a proxy can manage the asset on behalf of the owner
        asset_proxy: StorageHashMap<AssetId, AccountId>,
        /// Counter of the assets owned from the accounts
        account_owned_assets: StorageHashMap<AccountId, u32>,
        /// Store the proxy accounts that can manage all the assets of the owner
        account_proxy: StorageHashMap<(AccountId, AccountId), bool>,
        /// Mapping the role of an account (0 = Producer, 1= Wholesaler, 2 = Retailer, 3 = Final Buyer, 4=Shipper, 5=Administrator)
        account_role: StorageHashMap<AccountId, u32>,
    }

    #[derive(Encode, Decode, Debug, PartialEq, Eq, Copy, Clone)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        NotOwner,
        NotAdministrator,
        NotApproved,
        AssetExists,
        AssetNotFound,
        CannotInsert,
        CannotRemove,
        CannotFetchValue,
        NotAllowed,
        DuplicatedData,
        CategoryNotFound
    }

    /// Event emitted when a asset transfer occurs.
    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        from: Option<AccountId>,
        #[ink(topic)]
        to: Option<AccountId>,
        #[ink(topic)]
        id: AssetId,
    }

    /// Event emitted when a asset approve occurs.
    #[ink(event)]
    pub struct ProxyUpdated {
        #[ink(topic)]
        from: AccountId,
        #[ink(topic)]
        to: AccountId,
        #[ink(topic)]
        id: AssetId,
    }
    /// Event emitted when an asset is updated
    #[ink(event)]
    pub struct AssetUpdate {
        #[ink(topic)]
        from: AccountId,
        #[ink(topic)]
        id: AssetId,
    }
    /// Event emitted when a role is updated
    #[ink(event)]
    pub struct RoleUpdate {
        #[ink(topic)]
        from: AccountId,
        #[ink(topic)]
        id: AccountId,
    }

    /// Event emitted when an operator is enabled or disabled for an owner.
    /// The operator can manage all NFTs of the owner.
    #[ink(event)]
    pub struct ApprovalForAll {
        #[ink(topic)]
        owner: AccountId,
        #[ink(topic)]
        operator: AccountId,
        approved: bool,
    }

    impl AssetErc721 {
        /// Creates a new ERC721 asset contract.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                asset_owner: Default::default(),
                asset_description: Default::default(),
                asset_photo: Default::default(),
                asset_location: Default::default(),
                asset_category: Default::default(),
                asset_category_description: Default::default(),
                asset_metadata: Default::default(),
                asset_proxy: Default::default(),
                asset_validation: Default::default(),
                account_owned_assets: Default::default(),
                account_proxy: Default::default(),
                account_role: Default::default(),
            }
        }
        /// Creates a new asset.
        #[ink(message)]
        pub fn asset_new(&mut self, id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            self.add_asset_to(&caller, id)?;
            self.env().emit_event(Transfer {
                from: Some(AccountId::from([0x0; 32])),
                to: Some(caller),
                id,
            });
            Ok(())
        }
        /// Verifies if an asset id is present in the storage, it returns true/false
        #[ink(message)]
        pub fn asset_verify(&self, id: AssetId) -> bool{
            self.asset_owner.contains_key(&id)
        }
        /// Returns the owner of an asset id
        #[ink(message)]
        pub fn asset_get_owner(&self, id: AssetId) -> Option<AccountId> {
            self.asset_owner.get(&id).cloned()
        }
        #[ink(message)]
        /// Adds the description of an asset, only the owner can do it
        pub fn asset_description_new(&mut self,  id: AssetId, desc: Hash) -> Result<(), Error> {
            let caller = self.env().caller();
            let Self {
                asset_owner,
                asset_description,
                ..
            } = self;
            //check if asset id is present in the storage and belongs to the signer
            let _occupied = match asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(occupied) => occupied,
            };
            // search for description storage
            let _assetdescription = match asset_description.entry(id) {
                Entry::Vacant(_) => "",
                Entry::Occupied(_assetdescription) => return Err(Error::DuplicatedData),
            };
            // add description if not already present
            if self.asset_description.insert(id, desc).is_some() {
                return Err(Error::CannotInsert)
            };
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Returns the description of an asset id
        #[ink(message)]
        pub fn asset_description_get(&self, id: AssetId) ->Option<Hash> {
            self.asset_description.get(&id).cloned() 
        } 
        /// Verifies if an asset description is present in the storage
        #[ink(message)]
        pub fn asset_description_verify(&self, id: AssetId) -> bool{
            self.asset_description.contains_key(&id)
        }
        /// Removes the description of an asset, only the owner can do it
        #[ink(message)]
        pub fn asset_description_delete(&mut self,  id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=5 {
                return Err(Error::NotOwner)
            };
            // search for description 
            let assetdescription = match self.asset_description.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(assetdescription) => assetdescription,
            };
            // remove description
            assetdescription.remove_entry();
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Adds the IPFS address of an asset's photo, only the owner can do it
        #[ink(message)]
        pub fn asset_photo_new(&mut self,  id: AssetId, photoipfs: Hash) -> Result<(), Error> {
            let caller = self.env().caller();
            let Self {
                asset_owner,
                asset_photo,
                ..
            } = self;
            //check if asset id is present in the storage and belongs to the signer
            let _occupied = match asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(occupied) => occupied,
            };
            // search for photo storage
            let _assetphoto = match asset_photo.entry(id) {
                Entry::Vacant(_) => "",
                Entry::Occupied(_assetphoto) => return Err(Error::DuplicatedData),
            };
            // add photo ipfs address if not already present
            if self.asset_photo.insert(id, photoipfs).is_some() {
                return Err(Error::CannotInsert)
            };
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Returns the ipfs address of the asset's photo 
        #[ink(message)]
        pub fn asset_photo_get(&self, id: AssetId) ->  Option<Hash>{
           self.asset_photo.get(&id).cloned()
        }
        /// Verifies the IPFS address of the asset photo is stored
        #[ink(message)]
        pub fn asset_photo_verify(&self, id: AssetId) -> bool{
            self.asset_photo.contains_key(&id)
        }
        /// Removes  the ipfs address of an asset's photo, only the owner can do it
        #[ink(message)]
        pub fn asset_photo_delete(&mut self,  id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotOwner)
            };
            // search for photo ipfs address
            let assetphoto = match self.asset_photo.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(assetphoto) => assetphoto,
            };
            // remove photo ipfs address
            assetphoto.remove_entry();
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Stores the  category of an asset, only owner can do it, the category id must be already stored using "categoryDescriptionNew"
        #[ink(message)]
        pub fn asset_category_new(&mut self,  id: AssetId, categoryid: u32) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotOwner)
            };
            // search for asset_category_description in the storage
            let _categorydescription = match self.asset_category_description.entry(categoryid) {
                Entry::Vacant(_) => return Err(Error::CategoryNotFound),
                Entry::Occupied(categorydescription) => categorydescription,
            };
            // search for asset category in the storage to avoid duplicated entries
            let _assetcategory = match self.asset_category.entry(id) {
                Entry::Vacant(_) => 0,
                Entry::Occupied(_assetcategory) => return Err(Error::DuplicatedData),
            };
            //store the asset category
            if self.asset_category.insert(id, categoryid).is_some() {
                return Err(Error::CannotInsert)
            };
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Verifies if an asset category is present in the storage, it returns true/false
        #[ink(message)]
        pub fn asset_category_verify(&self, id: AssetId) -> bool{
             self.asset_category.contains_key(&id)
         }
        /// Removes the category of an asset, only the owner can do it
        #[ink(message)]
        pub fn asset_category_delete(&mut self,  id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotOwner)
            };
            // search for category
            let assetcategory = match self.asset_category.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(assetcategory) => assetcategory,
            };
            // remove category
            assetcategory.remove_entry();
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Adds the  location of an asset by coordinates in decimal format, comma separated: xxx.xxxxxxx,yyyy.yyyyyy only owner can do it
        #[ink(message)]
        pub fn asset_location_new(&mut self,  id: AssetId, location: Hash) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer or is a shipper
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=4{
                return Err(Error::NotOwner)
            };
            // search for location storage
            let _assetlocation = match self.asset_location.entry(id) {
                Entry::Vacant(_) => "",
                Entry::Occupied(_assetlocation) => return Err(Error::DuplicatedData),
            };
            // add location if not already present
            if self.asset_location.insert(id, location).is_some() {
                return Err(Error::CannotInsert)
            };
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Returns the location coordinates of an asset
        #[ink(message)]
        pub fn asset_location_get(&self, id: AssetId) ->  Option<Hash>{
           self.asset_location.get(&id).cloned()
        }
        /// Verify if there is a location stored for an asset id
        #[ink(message)]
        pub fn asset_location_verify(&self, id: AssetId) -> bool{
            self.asset_location.contains_key(&id)
        }
        /// Remove the location of an asset id, only the owner can do it
        #[ink(message)]
        pub fn asset_location_delete(&mut self,  id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=4 {
                return Err(Error::NotOwner)
            };
            // search for location
            let assetlocation = match self.asset_location.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(assetlocation) => assetlocation,
            };
            // remove description
            assetlocation.remove_entry();
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Add other metadata to an asset as ipfs address, only the owner can do it
        #[ink(message)]
        pub fn asset_metadata_new(&mut self,  id: AssetId, metadata: Hash) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotOwner)
            };
            // search for metadata storage
            let _assetmetadata = match self.asset_metadata.entry(id) {
                Entry::Vacant(_) => "",
                Entry::Occupied(_assetmetadata) => return Err(Error::DuplicatedData),
            };
            // add metadata if not already present
            if self.asset_metadata.insert(id, metadata).is_some() {
                return Err(Error::CannotInsert)
            };
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Returns the metada ipfs address of an asset
        #[ink(message)]
        pub fn asset_metadata_get(&self, id: AssetId) ->  Option<Hash>{
           self.asset_metadata.get(&id).cloned()
        }
        /// Verifies if there is metadata stored for an asset id
        #[ink(message)]
        pub fn asset_metadata_verify(&self, id: AssetId) -> bool{
            self.asset_metadata.contains_key(&id)
        }
        /// Removes metadata of an asset id, only the owner can do it
        #[ink(message)]
        pub fn asset_metadata_delete(&mut self,  id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            //check if asset id is present in the storage and belongs to the signer
            let asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            if asset.get() != &caller  && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotOwner)
            };
            // search for metadata
            let assetmetadata = match self.asset_metadata.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(assetmetadata) => assetmetadata
            };
            // remove description
            assetmetadata.remove_entry();
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Validate an asset from an administrator account
        #[ink(message)]
        pub fn asset_validation_new(&mut self,  id: AssetId, accountid: AccountId) -> Result<(), Error> {
            let caller = self.env().caller();
            // check for administrator 
            let administrator=AssetErc721::administrator_accountid().unwrap();
            if administrator != caller && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotAdministrator)
            }
            //check if asset id is present in the storage
            let _asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            // search for validation storage to avoid duplicated entries
            let _assetvalidation= match self.asset_validation.entry(id) {
                Entry::Vacant(_) => "",
                Entry::Occupied(_assetvalidation) => return Err(Error::DuplicatedData),
            };
            // add validation if not already present
            if self.asset_validation.insert(id, accountid).is_some() {
                return Err(Error::CannotInsert)
            };
            // emit event to report the update
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Returns the validation account of an asset
        #[ink(message)]
        pub fn asset_validation_get(&self, id: AssetId) ->  Option<AccountId>{
           self.asset_validation.get(&id).cloned()
        }
        /// Verify if there is a validation stored for an asset id
        #[ink(message)]
        pub fn asset_validation_verify(&self, id: AssetId) -> bool{
            self.asset_validation.contains_key(&id)
        }
        /// Remove the validation of an asset id, only an administrator can do it
        #[ink(message)]
        pub fn asset_validation_delete(&mut self,  id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            // check for administrator 
            let administrator=AssetErc721::administrator_accountid().unwrap();
            if administrator != caller && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotAdministrator)
            }
            //check if asset id is present in the storage
            let _asset = match self.asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(asset) => asset,
            };
            // search for validation
            let assetvalidation = match self.asset_validation.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(assetvalidation) => assetvalidation,
            };
            // remove validation
            assetvalidation.remove_entry();
            // emits event for asset updated
            self.env().emit_event(AssetUpdate {
                from: caller,
                id,
            });
            Ok(())
        }
        /// Add a category description, you can store categories for an asset that are not yet stored here.
        #[ink(message)]
        pub fn category_description_new(&mut self,  id: u32, description: Hash) -> Result<(), Error> {
            let caller = self.env().caller();
            // check for administrator 
            let administrator=AssetErc721::administrator_accountid().unwrap();
            if administrator != caller && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotAdministrator)
            }
            // search for category description storage
            let _category_description = match self.asset_category_description.entry(id) {
                Entry::Vacant(_) => "",
                Entry::Occupied(_category_description) => return Err(Error::DuplicatedData),
            };
            // add category description if not already present
            if self.asset_category_description.insert(id, description).is_some() {
                return Err(Error::CannotInsert)
            };
            Ok(())
        }
        /// Returns the description of an asset category 
        #[ink(message)]
        pub fn category_description_get(&self, id: AssetId) ->  Option<Hash>{
           self.asset_category_description.get(&id).cloned()
        }
        /// Verifies if there is a category description stored, returns true/false
        #[ink(message)]
        pub fn category_description_verify(&self, id: u32) -> bool{
            self.asset_category_description.contains_key(&id)
        }
        /// Removes the metadata of an asset id, only the owner can do it
        #[ink(message)]
        pub fn category_description_delete(&mut self,  id: u32) -> Result<(), Error> {
            let caller = self.env().caller();
            // check for administrator 
            let administrator=AssetErc721::administrator_accountid().unwrap();
            if administrator != caller && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotAdministrator)
            }
            //check if the category is present
            let category = match self.asset_category_description.entry(id) {
                Entry::Vacant(_) => return Err(Error::CategoryNotFound),
                Entry::Occupied(category) => category,
            };
            // remove category
            category.remove_entry();
            Ok(())
        }
        /// Deletes an existing asset. Only the owner can do it
        #[ink(message)]
        pub fn asset_delete(&mut self, id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            let Self {
                asset_owner,
                account_owned_assets,
                ..
            } = self;
            // check if asset id is store
            let occupied = match asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(occupied) => occupied,
            };
            // check if the assets belongs to signer
            if occupied.get() != &caller {
                return Err(Error::NotOwner)
            };
            //decreate counter assets owned
            decrease_counter_of(account_owned_assets, &caller)?;
            // remove asset
            occupied.remove_entry();
            self.env().emit_event(Transfer {
                from: Some(caller),
                to: Some(AccountId::from([0x0; 32])),
                id,
            });
            Ok(())
        } 
        /// Writes new role operator, only administrator can do it
        #[ink(message)]
        pub fn account_role_new(&mut self,  accountid: AccountId, role: u32) -> Result<(), Error> {
            let caller = self.env().caller();
            let administrator=AssetErc721::administrator_accountid().unwrap();
            // check for administrator 
            if administrator != caller && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotAdministrator)
            }
            // check fo valid role (0-9)
            if role>5{
                return Err(Error::CannotInsert)
            }
            // search for role in storage
            let _operatorrole = match self.account_role.entry(accountid) {
                Entry::Vacant(_) => 0,
                Entry::Occupied(_operatorrole) => return Err(Error::DuplicatedData),
            };
            //store the role
            if self.account_role.insert(accountid, role).is_some() {
                return Err(Error::CannotInsert)
            };
            // emits event
            self.env().emit_event(RoleUpdate {
                from: caller,
                id: accountid,
            });
            Ok(())
        }
        /// Returns the account role (0 = Producer, 1= Wholesaler, 2 = Retailer, 3 = Final Buyer, 4=Shipper, 5=Administrator)
        #[ink(message)]
        pub fn account_role_get(&self, accountid: AccountId) ->  Option<u32>{
           self.account_role.get(&accountid).cloned()
        }
         /// Verifies if there is a role stored for the operator
         #[ink(message)]
         pub fn account_role_verify(&self, accountid: AccountId) -> bool{
             self.account_role.contains_key(&accountid)
         }
        /// Removes an operator role, only the Administrator can do it
        #[ink(message)]
        pub fn account_role_delete(&mut self,  accountid: AccountId) -> Result<(), Error> {
            let caller = self.env().caller();
            let administrator=AssetErc721::administrator_accountid().unwrap();
            // check for administrator 
            if administrator != caller && self.account_role_get(caller).unwrap()!=5{
                return Err(Error::NotAdministrator)
            }
            // search for role in storage
            let operatorrole = match self.account_role.entry(accountid) {
                Entry::Vacant(_) => return Err(Error::CannotRemove),
                Entry::Occupied(operatorrole) => operatorrole,
            };
            // remove role
            operatorrole.remove_entry();
            self.env().emit_event(RoleUpdate {
                from: caller,
                id: accountid,
            });
            Ok(())
        }
        /// Returns the number of the assets owneed from an account
        /// This represents the amount of unique assets the owner has.
        #[ink(message)]
        pub fn account_assets_number(&self, owner: AccountId) -> u32 {
            self.account_assets_number_or_zero(&owner)
        }

        /// Returns the deletegated account ID for this asset if any.
        #[ink(message)]
        pub fn asset_get_delegated_account(&self, id: AssetId) -> Option<AccountId> {
            self.asset_proxy.get(&id).cloned()    
        }
        /// Delegate or undelegate an account to manage all the asset on behalf of the caller
        #[ink(message)]
        pub fn account_delegate_for_all_asset(&mut self,to: AccountId,approved: bool,) -> Result<(), Error> {
            self.proxy_for_all_assets(to, approved)?;
            Ok(())
        }
        /// Returns `true` if the operator is approved by the owner to manage any asset.
        #[ink(message)]
        pub fn account_verify_delegated_for_all_asset(&self, owner: AccountId, operator: AccountId) -> bool {
            self.check_proxy_for_all(owner, operator)
        }
        /// Delegate an account to transfer the specified asset on behalf of the caller.
        #[ink(message)]
        pub fn account_delegate_single_asset(&mut self, to: AccountId, id: AssetId) -> Result<(), Error> {
            self.delegate_for_single_asset(&to, id)?;
            Ok(())
        }
        /// Transfers the asset from the caller to a different account.
        #[ink(message)]
        pub fn asset_transfer(
            &mut self,
            destination: AccountId,
            id: AssetId,
        ) -> Result<(), Error> {
            let caller = self.env().caller();
            self.asset_transfer_from(&caller, &destination, id)?;
            Ok(())
        }

        /// Transfer approved of owned asset.
        #[ink(message)]
        pub fn transfer_from(
            &mut self,
            from: AccountId,
            to: AccountId,
            id: AssetId,
        ) -> Result<(), Error> {
            self.asset_transfer_from(&from, &to, id)?;
            Ok(())
        }
        /// Transfers asset `id` `from` the sender to the `to` AccountId.
        fn asset_transfer_from(
            &mut self,
            from: &AccountId,
            to: &AccountId,
            id: AssetId,
        ) -> Result<(), Error> {
            let caller = self.env().caller();
            if !self.exists(id) {
                return Err(Error::AssetNotFound)
            };
            if !self.approved_or_owner(Some(caller), id)  && self.account_role_get(caller).unwrap()!=5 {
                return Err(Error::NotApproved)
            };
            self.clear_proxy_asset(id)?;
            self.asset_remove_from(from, id)?;
            self.add_asset_to(to, id)?;
            self.env().emit_event(Transfer {
                from: Some(*from),
                to: Some(*to),
                id,
            });
            Ok(())
        }
       /// Get hard coded super administrator AccountId ###### CUSTOMIZE ADMINISTRATOR #######
        fn  administrator_accountid() -> Option<AccountId> {   
            //Administrator hexadecimal Account 
            //Alice account decoding 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY in hex: 0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d
            let accountid32: [u8;32] = hex_literal::hex!["d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"].into();
            Some(ink_env::AccountId::from(accountid32))
        }
        /// Removes asset `id` from the owner.
        fn asset_remove_from(
            &mut self,
            from: &AccountId,
            id: AssetId,
        ) -> Result<(), Error> {
            let Self {
                asset_owner,
                account_owned_assets,
                ..
            } = self;
            let occupied = match asset_owner.entry(id) {
                Entry::Vacant(_) => return Err(Error::AssetNotFound),
                Entry::Occupied(occupied) => occupied,
            };
            decrease_counter_of(account_owned_assets, from)?;
            occupied.remove_entry();
            Ok(())
        }

        /// Adds the asset `id` to the `to` AccountID.
        fn add_asset_to(&mut self, to: &AccountId, id: AssetId) -> Result<(), Error> {
            let Self {
                asset_owner,
                account_owned_assets,
                ..
            } = self;
            let vacant_asset_owner = match asset_owner.entry(id) {
                Entry::Vacant(vacant) => vacant,
                Entry::Occupied(_) => return Err(Error::AssetExists),
            };
            if *to == AccountId::from([0x0; 32]) {
                return Err(Error::NotAllowed)
            };
            let entry = account_owned_assets.entry(*to);
            increase_counter_of(entry);
            vacant_asset_owner.insert(*to);
            Ok(())
        }
        /// Approves or disapproves the operator to transfer all assets of the caller.
        fn proxy_for_all_assets(
            &mut self,
            to: AccountId,
            approved: bool,
        ) -> Result<(), Error> {
            let caller = self.env().caller();
            if to == caller {
                return Err(Error::NotAllowed)
            }
            self.env().emit_event(ApprovalForAll {
                owner: caller,
                operator: to,
                approved,
            });
            if self.check_proxy_for_all(caller, to) {
                let status = self
                    .account_proxy
                    .get_mut(&(caller, to))
                    .ok_or(Error::CannotFetchValue)?;
                *status = approved;
                Ok(())
            } else {
                match self.account_proxy.insert((caller, to), approved) {
                    Some(_) => Err(Error::CannotInsert),
                    None => Ok(()),
                }
            }
        }

        /// Approves the passed AccountId to transfer the specified asset on behalf of the message's sender.
        fn delegate_for_single_asset(&mut self, to: &AccountId, id: AssetId) -> Result<(), Error> {
            let caller = self.env().caller();
            let owner = self.asset_get_owner(id);
            if !(owner == Some(caller)
                || self.check_proxy_for_all(owner.expect("Error with AccountId"), caller))
            {
                return Err(Error::NotAllowed)
            };
            if *to == AccountId::from([0x0; 32]) {
                return Err(Error::NotAllowed)
            };

            if self.asset_proxy.insert(id, *to).is_some() {
                return Err(Error::CannotInsert)
            };
            self.env().emit_event(ProxyUpdated {
                from: caller,
                to: *to,
                id,
            });
            Ok(())
        }

        /// Removes existing approval from asset `id`.
        fn clear_proxy_asset(&mut self, id: AssetId) -> Result<(), Error> {
            if !self.asset_proxy.contains_key(&id) {
                return Ok(())
            };
            match self.asset_proxy.take(&id) {
                Some(_res) => Ok(()),
                None => Err(Error::CannotRemove),
            }
        }

        // Returns the total number of assets from an account.
        fn account_assets_number_or_zero(&self, of: &AccountId) -> u32 {
            *self.account_owned_assets.get(of).unwrap_or(&0)
        }

        /// Gets an operator on other Account's behalf.
        fn check_proxy_for_all(&self, owner: AccountId, operator: AccountId) -> bool {
            *self
                .account_proxy
                .get(&(owner, operator))
                .unwrap_or(&false)
        }

        /// Returns true if the AccountId `from` is the owner of asset `id`
        /// or it has been approved on behalf of the asset `id` owner.
        fn approved_or_owner(&self, from: Option<AccountId>, id: AssetId) -> bool {
            let owner = self.asset_get_owner(id);
            from != Some(AccountId::from([0x0; 32]))
                && (from == owner
                    || from == self.asset_proxy.get(&id).cloned()
                    || self.check_proxy_for_all(
                        owner.expect("Error with AccountId"),
                        from.expect("Error with AccountId"),
                    ))
        }

        /// Returns true if asset `id` exists or false if it does not.
        fn exists(&self, id: AssetId) -> bool {
            self.asset_owner.get(&id).is_some() && self.asset_owner.contains_key(&id)
        }
    }

    fn decrease_counter_of(
        hmap: &mut StorageHashMap<AccountId, u32>,
        of: &AccountId,
    ) -> Result<(), Error> {
        let count = (*hmap).get_mut(of).ok_or(Error::CannotFetchValue)?;
        *count -= 1;
        Ok(())
    }

    /// Increase asset counter from the `of` AccountId.
    fn increase_counter_of(entry: Entry<AccountId, u32>) {
        entry.and_modify(|v| *v += 1).or_insert(1);
    }

    /// Unit tests
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;
        use ink_env::{
            call,
            test,
        };
        use ink_lang as ink;

        #[ink::test]
        fn mint_works() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Asset 1 does not exists.
            assert_eq!(asseterc721.asset_get_owner(1), None);
            // Alice does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 0);
            // Create asset Id 1.
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
        }

        #[ink::test]
        fn mint_existing_should_fail() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1.
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // The first Transfer event takes place
            assert_eq!(1, ink_env::test::recorded_events().count());
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Alice owns asset Id 1.
            assert_eq!(asseterc721.asset_get_owner(1), Some(accounts.alice));
            // Cannot create  asset Id if it exists.
            // Bob cannot own asset Id 1.
            assert_eq!(asseterc721.asset_new(1), Err(Error::AssetExists));
        }

        #[ink::test]
        fn transfer_works() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1 for Alice
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Alice owns asset 1
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Bob does not owns any asset
            assert_eq!(asseterc721.account_assets_number(accounts.bob), 0);
            // The first Transfer event takes place
            assert_eq!(1, ink_env::test::recorded_events().count());
            // Alice transfers asset 1 to Bob
            assert_eq!(asseterc721.asset_transfer(accounts.bob, 1), Ok(()));
            // The second Transfer event takes place
            assert_eq!(2, ink_env::test::recorded_events().count());
            // Bob owns asset 1
            assert_eq!(asseterc721.account_assets_number(accounts.bob), 1);
        }

        #[ink::test]
        fn invalid_transfer_should_fail() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Transfer asset fails if it does not exists.
            assert_eq!(asseterc721.asset_transfer(accounts.bob, 2), Err(Error::AssetNotFound));
            // Asset Id 2 does not exists.
            assert_eq!(asseterc721.asset_get_owner(2), None);
            // Create asset Id 2.
            assert_eq!(asseterc721.asset_new(2), Ok(()));
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Asset Id 2 is owned by Alice.
            assert_eq!(asseterc721.asset_get_owner(2), Some(accounts.alice));
            // Get contract address
            let callee = ink_env::account_id::<ink_env::DefaultEnvironment>()
                .unwrap_or([0x0; 32].into());
            // Create call
            let mut data =
                ink_env::test::CallData::new(ink_env::call::Selector::new([0x00; 4])); // account_assets_number
            data.push_arg(&accounts.bob);
            // Push the new execution context to set Bob as caller
            ink_env::test::push_execution_context::<ink_env::DefaultEnvironment>(
                accounts.bob,
                callee,
                1000000,
                1000000,
                data,
            );
            // Bob cannot transfer not owned assets.
            assert_eq!(asseterc721.asset_transfer(accounts.eve, 2), Err(Error::NotApproved));
        }

        #[ink::test]
        fn approved_transfer_works() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1.
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Asset Id 1 is owned by Alice.
            assert_eq!(asseterc721.asset_get_owner(1), Some(accounts.alice));
            // Approve asset Id 1 transfer for Bob on behalf of Alice.
            assert_eq!(asseterc721.account_delegate_single_asset(accounts.bob, 1), Ok(()));
            // Get contract address.
            let callee = ink_env::account_id::<ink_env::DefaultEnvironment>()
                .unwrap_or([0x0; 32].into());
            // Create call
            let mut data =
                ink_env::test::CallData::new(ink_env::call::Selector::new([0x00; 4])); // account_assets_number
            data.push_arg(&accounts.bob);
            // Push the new execution context to set Bob as caller
            ink_env::test::push_execution_context::<ink_env::DefaultEnvironment>(
                accounts.bob,
                callee,
                1000000,
                1000000,
                data,
            );
            // Bob transfers asset Id 1 from Alice to Eve.
            assert_eq!(
                asseterc721.transfer_from(accounts.alice, accounts.eve, 1),
                Ok(())
            );
            // AssetId 3 is owned by Eve.
            assert_eq!(asseterc721.asset_get_owner(1), Some(accounts.eve));
            // Alice does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 0);
            // Bob does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.bob), 0);
            // Eve owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.eve), 1);
        }

        #[ink::test]
        fn approved_for_all_works() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1.
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Create asset Id 2.
            assert_eq!(asseterc721.asset_new(2), Ok(()));
            // Alice owns 2 assets.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 2);
            // Approve asset Id 1 transfer for Bob on behalf of Alice.
            assert_eq!(asseterc721.account_delegate_for_all_asset(accounts.bob, true), Ok(()));
            // Bob is an approved operator for Alice
            assert_eq!(
                asseterc721.check_proxy_for_all(accounts.alice, accounts.bob),
                true
            );
            // Get contract address.
            let callee = ink_env::account_id::<ink_env::DefaultEnvironment>()
                .unwrap_or([0x0; 32].into());
            // Create call
            let mut data =
                ink_env::test::CallData::new(ink_env::call::Selector::new([0x00; 4])); // account_assets_number
            data.push_arg(&accounts.bob);
            // Push the new execution context to set Bob as caller
            ink_env::test::push_execution_context::<ink_env::DefaultEnvironment>(
                accounts.bob,
                callee,
                1000000,
                1000000,
                data,
            );
            // Bob transfers asset Id 1 from Alice to Eve.
            assert_eq!(
                asseterc721.transfer_from(accounts.alice, accounts.eve, 1),
                Ok(())
            );
            // AssetId 1 is owned by Eve.
            assert_eq!(asseterc721.asset_get_owner(1), Some(accounts.eve));
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Bob transfers asset Id 2 from Alice to Eve.
            assert_eq!(
                asseterc721.transfer_from(accounts.alice, accounts.eve, 2),
                Ok(())
            );
            // Bob does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.bob), 0);
            // Eve owns 2 assets.
            assert_eq!(asseterc721.account_assets_number(accounts.eve), 2);
            // Get back to the parent execution context.
            ink_env::test::pop_execution_context();
            // Remove operator approval for Bob on behalf of Alice.
            assert_eq!(asseterc721.account_delegate_for_all_asset(accounts.bob, false), Ok(()));
            // Bob is not an approved operator for Alice.
            assert_eq!(
                asseterc721.check_proxy_for_all(accounts.alice, accounts.bob),
                false
            );
        }

        #[ink::test]
        fn not_approved_transfer_should_fail() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1.
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Bob does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.bob), 0);
            // Eve does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.eve), 0);
            // Get contract address.
            let callee = ink_env::account_id::<ink_env::DefaultEnvironment>()
                .unwrap_or([0x0; 32].into());
            // Create call
            let mut data =
                ink_env::test::CallData::new(ink_env::call::Selector::new([0x00; 4])); // account_assets_number
            data.push_arg(&accounts.bob);
            // Push the new execution context to set Eve as caller
            ink_env::test::push_execution_context::<ink_env::DefaultEnvironment>(
                accounts.eve,
                callee,
                1000000,
                1000000,
                data,
            );
            // Eve is not an approved operator by Alice.
            assert_eq!(
                asseterc721.transfer_from(accounts.alice, accounts.frank, 1),
                Err(Error::NotApproved)
            );
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Bob does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.bob), 0);
            // Eve does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.eve), 0);
        }

        #[ink::test]
        fn asset_delete_works() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1 for Alice
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Alice owns 1 asset.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 1);
            // Alice owns asset Id 1.
            assert_eq!(asseterc721.asset_get_owner(1), Some(accounts.alice));
            // Destroy asset Id 1.
            assert_eq!(asseterc721.asset_delete(1), Ok(()));
            // Alice does not owns assets.
            assert_eq!(asseterc721.account_assets_number(accounts.alice), 0);
            // Asset Id 1 does not exists
            assert_eq!(asseterc721.asset_get_owner(1), None);
        }

        #[ink::test]
        fn asset_delete_fails_asset_not_found() {
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Try asset_deleteing a non existent asset
            assert_eq!(asseterc721.asset_delete(1), Err(Error::AssetNotFound));
        }

        #[ink::test]
        fn asset_delete_fails_not_owner() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            // Create a new contract instance.
            let mut asseterc721 = AssetErc721::new();
            // Create asset Id 1 for Alice
            assert_eq!(asseterc721.asset_new(1), Ok(()));
            // Try asset_deleteing this asset with a different account
            set_sender(accounts.eve);
            assert_eq!(asseterc721.asset_delete(1), Err(Error::NotOwner));
        }

        fn set_sender(sender: AccountId) {
            let callee = ink_env::account_id::<ink_env::DefaultEnvironment>()
                .unwrap_or([0x0; 32].into());
            test::push_execution_context::<Environment>(
                sender,
                callee,
                1000000,
                1000000,
                test::CallData::new(call::Selector::new([0x00; 4])), // dummy
            );
        }
    }
}
