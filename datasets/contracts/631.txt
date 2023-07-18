#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

use ink_lang as ink;

#[openbrush::contract]
mod psp34_contract {
    use openbrush::contracts::psp34::extensions::metadata::*;
    use openbrush::contracts::psp34::extensions::burnable::*;
    use openbrush::contracts::psp34::extensions::enumerable::*;
    use openbrush::contracts::psp34::*;
    use ink_prelude::string::String;
    use ink_prelude::vec::Vec;
    use ink_storage::Mapping;
    use ink_storage::traits::SpreadAllocate;


    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    #[derive(Default, SpreadAllocate, PSP34Storage, PSP34MetadataStorage)]
    pub struct Psp34Contract {
        #[PSP34StorageField]
        psp34: PSP34Data<EnumerableBalances>,
        last_token_id: u8,
        cid_list: Mapping<String, Vec<String>>,
        #[PSP34MetadataStorageField]
        metadata: PSP34MetadataData,
    }

    impl PSP34 for Psp34Contract {}
    impl PSP34Metadata for Psp34Contract {}
    // Optionally you can add more default implementations
    impl PSP34Internal for Psp34Contract {}
    impl PSP34MetadataInternal for Psp34Contract {}
    impl PSP34Burnable for Psp34Contract {}
    impl PSP34Enumerable for Psp34Contract {}

    impl Psp34Contract {
        #[ink(constructor)]
        pub fn new(id: Id, name: String, symbol: String) -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut Self| {
                instance._set_attribute(id.clone(), String::from("name").into_bytes(), name.into_bytes());
                instance._set_attribute(id, String::from("symbol").into_bytes(), symbol.into_bytes());
            })
        }

        #[ink(message)]
        pub fn mint_token(&mut self) -> Result<(), PSP34Error> {
            self._mint_to(Self::env().caller(), Id::U8(self.last_token_id))?;
            self.last_token_id += 1;
            Ok(())
        }

        #[ink(message)]
        pub fn mint_with_attribute(&mut self, title: String, author: String, date: String, cid: String) -> Result<(), PSP34Error> {
            self._mint_to(Self::env().caller(), Id::U8(self.last_token_id))?;
            self.last_token_id += 1;
            let mut attributes = Vec::new();
            attributes.push(title);
            attributes.push(author);
            attributes.push(date);
            self.cid_list.insert(cid, &attributes);
            Ok(())
        }
    }
}