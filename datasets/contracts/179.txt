#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[brush::contract]
mod psp34 {
    use brush::contracts::psp34::*;
    use brush::contracts::psp34::extensions::metadata::*;
    use brush::contracts::psp34::extensions::mintable::*;
    use brush::contracts::psp34::extensions::burnable::*;
    use ink_storage::traits::SpreadAllocate;

    #[ink(storage)]
    #[derive(Default, SpreadAllocate, PSP34Storage, PSP34MetadataStorage)]
    pub struct MyPSP34 {
        #[PSP34StorageField]
        psp34: PSP34Data,
        #[PSP34MetadataStorageField]
        metadata: PSP34MetadataData,
    }

    impl PSP34 for MyPSP34 {}
    impl PSP34Metadata for MyPSP34 {}
    impl PSP34Internal for MyPSP34 {}
    impl PSP34MetadataInternal for MyPSP34 {}
    impl PSP34Mintable for MyPSP34 {}
    impl PSP34Burnable for MyPSP34 {}

    impl MyPSP34 {
        #[ink(constructor)]
        pub fn new(id: Id, name: String, symbol: String) -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut Self| {
                instance._set_attribute(id.clone(), String::from("name").into_bytes(), name.into_bytes());
                instance._set_attribute(id, String::from("symbol").into_bytes(), symbol.into_bytes());
            })
        }
    }
}
