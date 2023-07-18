#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;
use pink_extension as pink;

use index_traits::SignedTransaction;
use index_traits::Signer as SignerTrait;

#[pink::contract(env=PinkEnvironment)]
mod subsigner {
    use super::*;
    use ink_prelude::{string::String, vec::Vec};
    use ink_storage::traits::{PackedLayout, SpreadAllocate, SpreadLayout};
    use paralib::ToArray;
    use pink::chain_extension::signing;
    use pink_extension::PinkEnvironment;
    use signing::SigType;

    #[ink(storage)]
    #[derive(SpreadAllocate)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct SubSigner {
        key: [u8; 32],
        admin: AccountId,
    }

    impl SubSigner {
        #[ink(constructor)]
        pub fn new() -> Self {
            let admin = Self::env().caller();
            SubSigner {
                key: Self::init_key(admin),
                admin,
            }
        }

        /// Initializes the contract key with a salt
        ///
        /// In the future we will use a bunch of predefined keys
        pub fn init_key(caller: AccountId) -> [u8; 32] {
            let salt: &[u8; 32] = caller.as_ref();
            signing::derive_sr25519_key(salt).to_array()
        }
    }

    /// Signs the unsigned_tx with an interior predefined key
    impl SignerTrait for SubSigner {
        #[ink(message)]
        fn sign_transaction(&self, unsigned_tx: Vec<u8>) -> SignedTransaction {
            let signature = signing::sign(&unsigned_tx, &self.key, SigType::Sr25519);
            SignedTransaction::SubSignedTX(signature)
        }
    }
}
