/* 
    Using the standard library if we run the tests module, 
    or if we use a std feature flag within our code. 
    Otherwise the contract will always compile with no_std.
*/
#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract(version = "0.1.0")]
#[derive(
    Debug,
    Copy,
    Clone,
)]

mod roleContract {
    #[cfg(not(feature = "ink-as-dependency"))]
    use ink_core::{
        env::println,
        storage,
    };
    use  ink_prelude::string::String;

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    struct RoleContract {
        /// Stores a single `bool` value on the storage.
        // value: storage::Value<bool>,

        // Stores address -> roleType
        // roleType = 1 (System)
        // roleType = 2 (GWAL)
        registered_roles: storage::HashMap<AccountId, u32>,
        account_parent_map: storage::HashMap<AccountId, AccountId>,
        role_permission_map: storage::HashMap<AccountId, (u128, u32)>,
        multi_sig_approvers: storage::HashMap<(AccountId, u128, u32), u32>,
    }

    #[ink(event)]
    struct AddrEvent {
        #[ink(topic)]
        addr: AccountId,
    }

    #[ink(event)]
    struct U32Event {
        #[ink(topic)]
        id: u32,
    }

    #[ink(event)]
    struct U128Event {
        #[ink(topic)]
        id: u128,
    }

    #[ink(event)]
    struct BoolEvent {
        #[ink(topic)]
        data: bool,
    }

    impl RoleContract {
        /// Constructor that initializes the caller as roleType = 1 (System)
        #[ink(constructor)]
        fn new(&mut self){
            let caller = self.env().caller();
            self.addRoleType(caller, 1);
        }

        /// A message that can be called on instantiated contracts.
        /// add role type for an address in map
        #[ink(message)]
        fn addRoleType(&mut self, addr: AccountId, value: u32) {
            match self.registered_roles.get(&addr) {
                Some(_) => {
                    *self.registered_roles.get_mut(&addr).unwrap() = value
                    // &oldVal = value
                    // self.registered_roles.mutate_with(&addr, |value| oldVal = value);
                }
                None => {
                    self.registered_roles.insert(addr, value);
                }
            };

            self.env()
                .emit_event(
                    AddrEvent {
                        addr: addr,
                    }
                );

            self.env()
                .emit_event(
                    U32Event {
                        id: value,
                    }
                );
        }

        /// Simply returns caller
        #[ink(message)]
        fn getCaller(&self) -> AccountId {
            let caller = self.env().caller();

            self.env()
                .emit_event(
                    AddrEvent {
                        addr: caller,
                    }
                );
            caller
        }

        /// Get role type by address
        #[ink(message)]
        fn getRoleType(&self, of: AccountId) -> u32 {
            let role_type = *self.registered_roles.get(&of).unwrap_or(&0);

            self.env()
                .emit_event(
                    U32Event {
                        id: role_type,
                    }
                );
            
            role_type
        }

        /// Add role permission
        #[ink(message)]
        fn addRole(&mut self, addr: AccountId, func_name: u128, permission: u32) {
            // let name = func_name.clone();
            let roleMap = self.role_permission_map.get(&addr);

            match roleMap {
                Some(_) => {
                    *self.role_permission_map.get_mut(&addr).unwrap() = (func_name, permission)
                }
                None => {
                    self.role_permission_map.insert(addr, (func_name, permission));
                }
            };

            self.env()
                .emit_event(
                    U128Event {
                        id: func_name,
                    }
                );

            self.env()
                .emit_event(
                    U32Event {
                        id: permission,
                    }
                );
        }

        /// Get role permission
        #[ink(message)]
        fn getRole(&self, addr: AccountId) -> (u128, u32) {
            let mut func_name;
            let mut permissioned = 0u32;
            let roleMap = self.role_permission_map.get(&addr);
            match roleMap {
                Some(_) => {
                    let (ref name, ref p) = roleMap.unwrap();
                    func_name = *name;
                    permissioned = *p;
                }
                None => {
                    // let empty_str = String::from("");
                    func_name = 0u128;
                    permissioned = 0u32;
                    println("Didn't find match!");
                }
            };

            self.env()
                .emit_event(
                    U128Event {
                        id: func_name,
                    }
                );

            self.env()
                .emit_event(
                    U32Event {
                        id: permissioned,
                    }
                );

            (func_name, permissioned)
        }

        /// Remove role permission
        #[ink(message)]
        fn removeRole(&mut self, addr: AccountId) -> u128 {
            let mut func_name;
            let removedValue = self.role_permission_map.remove(&addr);
            match removedValue {
                Some(_) => {
                    let (ref name, ref p) = removedValue.unwrap();
                    func_name = *name;
                }
                None => {
                    // let empty_str = String::from("");
                    func_name = 0u128;
                    println("Didn't find match!");
                }
            };

            self.env()
                .emit_event(
                    U128Event {
                        id: func_name,
                    }
                );

            func_name
        }

        /// Check if account already has a role permission
        #[ink(message)]
        fn hasRole(&self, addr: AccountId) -> bool {
            let permission = self.role_permission_map.contains_key(&addr);
            self.env()
                .emit_event(
                    BoolEvent {
                        data: permission,
                    }
                );
            permission
        }

        /// Add approver for multi-sig approval process (ex. use for approveTransferToOther())
        #[ink(message)]
        fn addApprover(&mut self, addr: AccountId, func_name: u128, _stage: u32) {
            // let name = func_name.clone();
            let k = (addr, func_name, _stage);
            let approverMap = self.multi_sig_approvers.get(&k);

            match approverMap {
                Some(_) => {
                    *self.multi_sig_approvers.get_mut(&k).unwrap() = 1
                }
                None => {
                    self.multi_sig_approvers.insert(k, 1);
                }
            };

            self.env()
                .emit_event(
                    U128Event {
                        id: func_name,
                    }
                );

            self.env()
                .emit_event(
                    U32Event {
                        id: _stage,
                    }
                );
        }

        /// Check if account is already registered as an approver
        #[ink(message)]
        fn isApprover(&self, addr: AccountId, func_name: u128, _stage: u32) -> bool {
            // let name = func_name.clone();
            let k = (addr, func_name, _stage);
            // if self.multi_sig_approvers.contains_key(&k) {
            //     println("No key is found!");
            //     return false;
            // }

            let permissioned = *self.multi_sig_approvers.get(&k).unwrap_or(&0);
            // permissioned == 1
            if permissioned == 1 {
                self.env()
                    .emit_event(
                        BoolEvent {
                            data: true,
                        }
                    );
                return true;
            } else {
                self.env()
                    .emit_event(
                        BoolEvent {
                            data: false,
                        }
                    );
                return false;
            };
        }

        /// Add parent account
        #[ink(message)]
        fn addParent(&mut self, of: AccountId, parentAddr: AccountId) {
            match self.account_parent_map.get(&of) {
                Some(_) => {
                    *self.account_parent_map.get_mut(&of).unwrap() = parentAddr
                }
                None => {
                    self.account_parent_map.insert(of, parentAddr);
                }
            };

            self.env()
                .emit_event(
                    AddrEvent {
                        addr: parentAddr,
                    }
                );
        }

        /// Get granter by address
        #[ink(message)]
        fn getParent(&self, of: AccountId) -> AccountId {
            let parentAddr;
            let someOrNone = self.account_parent_map.get(&of);

            if someOrNone.is_some() {
                parentAddr = *someOrNone.unwrap();

                self.env()
                .emit_event(
                    AddrEvent {
                        addr: parentAddr,
                    }
                );
            
                parentAddr
            } else {
                let bytes: [u8; 32] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                let empty_account = AccountId::from(bytes);
                println("Didn't find match!");

                empty_account
            }
        }

        /// For test api, set role
        #[ink(message)]
        fn testSetRole(&mut self) {
            let caller = self.env().caller();
            self.addRole(caller, 1001, 1);
        }

        /// Get total balance
        #[ink(message)]
        fn getBalance(&self) -> u128 {
            let total_balance = self.env().balance();
            self.env()
                .emit_event(
                    U128Event {
                        id: total_balance,
                    }
                );
            total_balance
        }
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        // We test if the default constructor does its job.
        #[test]
        fn test_parent_map() {
            // Note that even though we defined our `#[ink(constructor)]`
            // above as `&mut self` functions that return nothing we can call
            // them in test code as if they were normal Rust constructors
            // that take no `self` argument but return `Self`.
            let mut roleContract = RoleContract::new();
            let bytes: [u8; 32] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            let bytes2: [u8; 32] = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            let acc = AccountId::from(bytes);
            let p_acc = AccountId::from(bytes2);
            roleContract.addParent(acc, p_acc);
            let res = roleContract.getParent(acc);

            println!("Parent address is: {:?}", res);
        }

        // // We test a simple use case of our role permission map management
        // #[test]
        // fn test_role_permission_map() {
        //     let mut roleContract = RoleContract::new();
        //     let bytes: [u8; 32] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        //     let acc = AccountId::from(bytes);
        //     println!("--------- Start test ---------");
        //     println!("Contains key? {:?}", roleContract.hasRole(acc));

        //     println!("--------- Add role permission ----------");
        //     // roleContract.addRole(acc, "settlement".to_string(), 1);
        //     roleContract.addRole(acc, 2005, 1);
        //     let (func, permission) = roleContract.getRole(acc);

        //     println!("Function name: {:?}", func);
        //     println!("isPermissioned: {:?}", permission == 1);
        //     println!("Contains key? {:?}", roleContract.hasRole(acc));

        //     println!("--------- Remove role permission ----------");
        //     let removed_func = roleContract.removeRole(acc);
        //     println!("Removed function name: {:?}", removed_func);
        //     // println!("isPermissioned: {:?}", removed_permission == 1);
        //     println!("Contains key? {:?}", roleContract.hasRole(acc));
        //     // assert_eq!(accContract.get(), true);
        // }

        // We test a simple use case of our approver management
        #[test]
        fn test_multi_sig_approvers() {
            let mut roleContract = RoleContract::new();
            let bytes: [u8; 32] = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            let acc = AccountId::from(bytes);
            println!("--------- Start test ---------");
            println!("Function name: approveTransferToOther");
            println!("Stage: 1");
            println!("Contains key? {:?}", roleContract.isApprover(acc, 2008, 1));

            println!("--------- Add approver ----------");
            // roleContract.addApprover(acc, "approveTransferToOther".to_string(), 1);
            roleContract.addApprover(acc, 2008, 1);
            let permissioned = roleContract.isApprover(acc, 2008, 1);

            println!("isApprover: {:?}", permissioned);
        }
    }
}

// pub use crate::roleContract::RoleContract;