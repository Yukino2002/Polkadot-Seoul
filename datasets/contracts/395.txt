#![cfg_attr(not(feature = "std"), no_std)]
extern crate alloc;
pub use self::role_manage::{
    RoleManage,
    // RoleManageRef,
};
use ink_lang as ink;

#[ink::contract]
mod role_manage {
    use alloc::string::String;
    use ink_prelude::vec::Vec;
    use ink_prelude::collections::BTreeMap;
    use ink_storage::{collections::HashMap as StorageHashMap, };



    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct RoleManage {
        owner:AccountId,
        index:u64,
        role_map:StorageHashMap<u64,String>,
        role_authority:StorageHashMap<String,Vec<String>>,
        user_role:StorageHashMap<AccountId,Vec<String>>,
    }

    impl RoleManage {
        #[ink(constructor)]
        pub fn new() -> Self {
           Self {
                owner:Self::env().caller(),
                index: 0,
                role_map : StorageHashMap::new(),
                role_authority: StorageHashMap::new(),
                user_role: StorageHashMap::new()
            }
        }

        fn only_core(&self,sender:AccountId) {
            assert_eq!(self.owner, sender);
        }

        #[ink(message)]
        pub fn add_role(&mut self, name: String) -> bool {
            self.only_core(Self::env().caller());
            self.role_map.insert(self.index, name);
            self.index += 1;
            true
        }

        #[ink(message)]
        pub fn list_roles(&self) -> Vec<String> {
            let mut role_vec = Vec::new();
            let mut iter = self.role_map.values();
            let mut role = iter.next();
            while role.is_some() {
                role_vec.push(role.unwrap().clone());
                role = iter.next();
            }
            role_vec
        }

        #[ink(message)]
        pub fn get_role_by_index(&self, index: u64) -> String {
            self.role_map.get(&index).unwrap().clone()
        }


        #[ink(message)]
        pub fn add_insert_authority(&mut self ,name:String,authority:String) -> bool {
            self.only_core(Self::env().caller());
            let role_authority_list = self.role_authority.entry(name.clone()).or_insert(Vec::new());
            role_authority_list.push(authority);

            true
        }

        #[ink(message)]
        pub fn list_role_authority(&self,name:String) -> Vec<String> {
            self.role_authority.get(&name).unwrap().clone()
        }

        #[ink(message)]
        pub fn add_user_role(&mut self,user:AccountId,role:String) -> bool {
            self.only_core(Self::env().caller());
            let user_role_list = self.user_role.entry(user.clone()).or_insert(Vec::new());
            user_role_list.push(role);
            true
        }
        #[ink(message)]
        pub fn check_user_role(&self,user:AccountId,role:String) -> bool {
            let list =  self.get_user_roles(user);
            for i in  list{
                if i == role {
                    return true
                }
            }
            false
        }
        #[ink(message)]
        pub fn get_user_roles(&self,user:AccountId) -> Vec<String> {
         self.user_role.get(&user).unwrap().clone()
        }
        //Query whether the user has the permission
        #[ink(message)]
        pub fn check_user_authority(&self,user:AccountId,authority:String) -> bool {
            let list =  self.get_user_authority(user);
            for i in  list{
                if i == authority {
                    return true
                }
            }
            false
        }
        //You can query a role set by user ID and traverse the role set to query the corresponding permission  
        #[ink(message)]
        pub fn get_user_authority(&self,user:AccountId) -> Vec<String> {
            let mut authority_vec = Vec::new();
            let list =  self.user_role.get(&user).unwrap().clone();
            for i in list {
               let mut authority =  self.role_authority.get(&i).unwrap().clone();
               authority_vec.append(&mut authority);
            }
            authority_vec
        }
    }
}
