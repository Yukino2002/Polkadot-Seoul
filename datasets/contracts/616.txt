#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

mod crypto {
    use twox_hash;

    /// Do a XX 128-bit hash and place result in `dest`.
    pub fn twox_128_into(data: &[u8], dest: &mut [u8; 16]) {
        use ::core::hash::Hasher;
        let mut h0 = twox_hash::XxHash::with_seed(0);
        let mut h1 = twox_hash::XxHash::with_seed(1);
        h0.write(data);
        h1.write(data);
        let r0 = h0.finish();
        let r1 = h1.finish();
        use byteorder::{
            ByteOrder,
            LittleEndian,
        };
        LittleEndian::write_u64(&mut dest[0..8], r0);
        LittleEndian::write_u64(&mut dest[8..16], r1);
    }

    /// Do a XX 128-bit hash and return result.
    pub fn twox_128(data: &[u8]) -> [u8; 16] {
        let mut r: [u8; 16] = [0; 16];
        twox_128_into(data, &mut r);
        r
    }

     /// Do a Blake2 256-bit hash and place result in `dest`.
    pub fn blake2_256_into(data: &[u8], dest: &mut [u8; 32]) {
        dest.copy_from_slice(blake2_rfc::blake2b::blake2b(32, &[], data).as_bytes());
    }

    /// Do a Blake2 256-bit hash and return result.
    pub fn blake2_256(data: &[u8]) -> [u8; 32] {
        let mut r = [0; 32];
        blake2_256_into(data, &mut r);
        r
    }
}

#[derive(scale::Encode, scale::Decode)]
pub struct H256Wrapper(btc_primitives::H256);

impl From<btc_primitives::H256> for H256Wrapper {
    fn from(h: btc_primitives::H256) -> Self {
        Self(h)
    }
}

#[cfg(feature = "std")]
impl type_metadata::HasTypeId for H256Wrapper {
    fn type_id() -> type_metadata::TypeId {
        type_metadata::TypeIdCustom::new(
            "H256",
            type_metadata::Namespace::from_module_path("bitcoin_primitives")
                .expect("non-empty Rust identifier namespaces cannot fail"),
            Vec::new(),
        )
        .into()
    }
}

#[cfg(feature = "std")]
impl type_metadata::HasTypeDef for H256Wrapper {
    fn type_def() -> type_metadata::TypeDef {
        use ink_prelude::vec;
        type_metadata::TypeDefTupleStruct::new(vec![type_metadata::UnnamedField::of::<
            [u8; 32],
        >()])
        .into()
    }
}

#[ink::contract(version = "0.1.0", env = DefaultXrmlTypes)]
mod btc_spv_oracle {

    use super::{
        crypto,
        H256Wrapper,
    };
    use scale::{
        Decode,
        Encode,
        KeyedVec,
    };
    use btc_primitives::H256;
    
    use ink_prelude::vec::Vec;
    use ink_prelude::collections::BTreeMap;

    use ink_core::{
        env::DefaultXrmlTypes, 
        storage
    };

    #[derive(Debug, PartialEq, PartialOrd, Ord, Eq, Clone, Copy, Encode, Decode)]
    #[cfg_attr(feature = "ink-generate-abi", derive(type_metadata::Metadata))]
    pub enum AssetType {
        Free,
        ReservedStaking,
        ReservedStakingRevocation,
        ReservedWithdrawal,
        ReservedDexSpot,
        ReservedDexFuture,
        ReservedCurrency,
        ReservedXRC20,
        GasPayment,
    }

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    struct BtcSpvOracle {
        // To check if the bet is set or not?
        isBetSet: storage::Value<bool>,
        // This is used to set a new bet.
        currentBet: storage::Value<u32>,
        value: storage::Value<u32>,
        owner: storage::Value<AccountId>,
    }


     #[ink(event)]
    struct NewBetSet {
        name: Hash,
        from: AccountId,
        old_address: Option<AccountId>,
        new_address: AccountId,
    }

    #[ink(event)]
    struct GameResult {
        name: Hash,
        #[ink(topic)]
        from: AccountId,
        #[ink(topic)]
        old_owner: Option<AccountId>,
        #[ink(topic)]
        new_owner: AccountId,
    } 

    impl BtcSpvOracle {
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        fn new(&mut self, init_value: bool) {
            self.value.set(0);
        }

        #[ink(message)]
        fn get_init_data(&self, height: u32) -> u32 {
            *self.value
        }

        // Returns the block Hash
        #[ink(message)]
        fn get_btc_block_hash(&self, height: u32) -> Vec<H256Wrapper> {
            let mut key =  b"XBridgeOfBTC BlockHashFor".to_vec();
            Encode::encode_to(&height, &mut key);
            let params = crypto::blake2_256(&key);
            let result = self.env().get_runtime_storage::<Vec<H256>>(&params[..]);
            result.unwrap().unwrap().into_iter().map(|x| x.into()).collect()
        }

         #[ink(message)]
        fn get_best_index(&self) -> H256Wrapper {
            const BEST_INDEX: &[u8] = b"XBridgeOfBTC BestIndex";
            let key = crypto::twox_128(BEST_INDEX);
            let result = self.env().get_runtime_storage::<H256>(&key[..]);
            result.unwrap().unwrap().into()
        }

    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        /// We test if the default constructor does its job.
        #[test]
        fn default_works() {
            // Note that even though we defined our `#[ink(constructor)]`
            // above as `&mut self` functions that return nothing we can call
            // them in test code as if they were normal Rust constructors
            // that take no `self` argument but return `Self`.
            let btc_spv_oracle = BtcPredictGame::new(true);
            let height: u32 = 628811;

            let mut key = b"XBridgeOfBTC BlockHashFor".to_vec();
            println!("parity_codec:{:?}", key);
            Encode::encode_to(&height, &mut key);

            let params = crypto::blake2_256(&key);

            println!("parity_codec:{:?}", key);

            println!("params:{:?}", params);
            let result: Vec<H256> = btc_spv_oracle.get_btc_block_hash(height);

            println!("hash:{:?}", result);

            // assert_eq!(btc_spv_oracle.get_btc_block_hash(height), true);
        }
    }
}
