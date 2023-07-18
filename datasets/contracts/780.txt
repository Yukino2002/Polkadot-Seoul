#![cfg_attr(not(feature = "std"), no_std)]

extern crate alloc;

use ink_lang as ink;

#[allow(unused_imports)]
#[allow(non_snake_case)]
#[allow(clippy::new_without_default)]
#[ink::contract]
mod mb_operatorstore {
    use alloc::string::String;
    use ink_prelude::vec::Vec;
    use ink_prelude::collections::BTreeMap;
    use ink_storage::{
        collections::HashMap as StorageHashMap,
        traits::{
            PackedLayout,
            SpreadLayout,
        },
    };

    /**
     _operator The address of the operator.
     _account The address of the account being operated.
  */
    #[ink(storage)]
    pub struct MBOperatorStore {
        permissionsOf:StorageHashMap<(AccountId, AccountId), u64>
    }

    impl MBOperatorStore {
        #[ink(constructor)]
        pub fn new(
        ) -> Self {
            Self {
                permissionsOf: Default::default(),
            }
        }
        /**
       @notice
       Whether or not an operator has the permission to take a certain action pertaining to the specified domain.
       @param _operator The operator to check.
       @param _account The account that has given out permissions to the operator.
       @param _permissionIndex The permission index to check for.
       @return A flag indicating whether the operator has the specified permission.
      */
        #[ink(message)]
        pub fn hasPermission(
            &self,
            _operator: AccountId,
            _account: AccountId,
            _permissionIndex: u64
        ) -> bool {
            assert!(_permissionIndex <= 255,"PERMISSION IS OUT");
            let permission = *self.permissionsOf.get(&(_operator,_account)).unwrap_or(&0);
            ((permission >> _permissionIndex) & 1) == 1
        }
        /**
          @notice
          Sets permissions for an operators.
          @param _operatorData The data that specifies the params for the operator being set.
        */
        #[ink(message)]
        pub fn setOperator(
            &mut self,
            _operator: AccountId,
            _permissionIndexes: Vec<u64>
        ) -> bool {
            let _packed:u64 = self._packedPermissions(_permissionIndexes);
            let caller = Self::env().caller();
            self.permissionsOf.insert((_operator, caller),_packed);
            true
        }

        fn _packedPermissions(&self, _indexes:Vec<u64>) -> u64{
            let mut packed = 0;
            for _i in _indexes.iter() {
                assert!(_i <= &255,"PERMISSION IS OUT");
                packed |= 1 << _i;
            }
            packed
        }
    }

    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;
        /// Imports `ink_lang` so we can use `#[ink::test]`.
        use ink_lang as ink;
        #[ink::test]
        fn MBOperatorStore_works() {
            let accounts =
                ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                    .expect("Cannot get accounts");
            let mut ms = MBOperatorStore::new();
            let mut vec = Vec::new();
            vec.push(1);
            ms.setOperator(AccountId::default(),vec);
            assert!(ms.hasPermission(AccountId::default(),accounts.alice,1) == true);
        }
    }
}
