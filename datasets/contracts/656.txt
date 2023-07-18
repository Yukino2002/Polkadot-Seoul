#![cfg_attr(not(feature = "std"), no_std)]

#[ink::contract]
mod logic {
    use ink::storage::traits::StorageKey;
    use ink::storage::Lazy;

    #[ink(storage)]
    pub struct Logic {
        /// Note that we make use of the `Lazy` data structure here to ensure that the `admin`
        /// field gets stored in its own storage cell.
        ///
        /// If we don't do this it ends up getting stored at the `0x00000000` storage key where all
        /// the other `Packed` fields get stored.
        ///
        /// This is problematic because our `Proxy` contract is also writing its `Packed` fields
        /// to `0x00000000`. When we return control to the `Proxy` at the end of the call it'll end
        /// up overwriting our fields at `0x00000000` with its own!
        admin: Lazy<AccountId>,
        value: Lazy<u32>,
    }

    impl Logic {
        /// Creates a new instance of the `Logic` contract.
        ///
        /// # Note
        ///
        /// In theory we shouldn't need this since the contract should be initialized from the
        /// `Proxy`. However, we don't have the ability to do this yet so we still a) require that
        /// all contracts have a constructor, and b) we don't have a way to initialize storage
        /// otherwise.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                admin: Lazy::default(),
                value: Default::default(),
            }
        }

        #[ink(message)]
        pub fn get(&self) -> u32 {
            let key = self.value.key();
            ink::env::debug_println!("Logic::get: Key {:?}", &key);

            let value = self.value.get().unwrap();
            ink::env::debug_println!("Logic::get: {:?}", &value);
            value
        }

        #[ink(message)]
        pub fn set(&mut self, value: u32) {
            let key = self.value.key();
            ink::env::debug_println!("Logic::set: Key {:?}", &key);

            self.value.set(&value);
            ink::env::debug_println!("Logic::set: {:?}", &self.value.get());
        }

        #[ink(message)]
        pub fn inc(&mut self) {
            let key = self.value.key();
            ink::env::debug_println!("Logic::inc: Key {:?}", &key);

            let value = self.value.get().unwrap();
            self.value.set(&(value + 1));
            ink::env::debug_println!("Logic::inc: {:?}", &self.value.get());
        }

        #[ink(message)]
        pub fn get_admin(&self) -> AccountId {
            let key = self.admin.key();
            ink::env::debug_println!("Logic::get_admin: Key {:?}", &key);

            let value = self.admin.get().unwrap();
            ink::env::debug_println!("Logic::get_admin: {:?}", &value);
            value
        }

        #[ink(message)]
        pub fn set_admin(&mut self, new_admin: AccountId) {
            let key = self.admin.key();
            ink::env::debug_println!("Logic::set_admin: Key {:?}", &key);

            self.admin.set(&new_admin);
            ink::env::debug_println!("Logic::set_admin: {:?}", &self.admin.get());
        }
    }
}
