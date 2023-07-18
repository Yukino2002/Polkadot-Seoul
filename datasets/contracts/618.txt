#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[brush::contract]
pub mod psp22_token {
    use brush::contracts::psp22::extensions::metadata::*;
    use ink_prelude::string::String;
    use onsenswap_project::traits::psp22_token::*;

    #[ink(storage)]
    #[derive(Default, PSP22Storage, PSP22MetadataStorage)]
    pub struct PSP22TokenContract {
        #[PSP22StorageField]
        psp22: PSP22Data,
        #[PSP22MetadataStorageField]
        metadata: PSP22MetadataData,
    }

    impl PSP22 for PSP22TokenContract {}
    impl PSP22Metadata for PSP22TokenContract {}

    // trait defined in onsenswap_project::traits::psp22_token
    impl PSP22Token for PSP22TokenContract {}

    impl PSP22TokenContract {
        #[ink(constructor)]
        pub fn new(name: Option<String>, symbol: Option<String>) -> Self {
            let mut instance = Self::default();
            instance.metadata.name = name;
            instance.metadata.symbol = symbol;
            instance.metadata.decimals = 18;
            let total_supply = 1_000_000 * 10_u128.pow(18);
            assert!(instance._mint(instance.env().caller(), total_supply).is_ok());
            instance
        }
    }
}
