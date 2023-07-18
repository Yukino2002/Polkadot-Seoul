#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]
#[openbrush::contract]
pub mod token {
    use openbrush::contracts::access_control::*;
    use openbrush::{contracts::psp37::*, modifiers, storage::Mapping, traits::Storage};
    use staking_dapp::traits::reputation::{Internal, Reputation, *};

    #[ink(storage)]
    #[derive(Default, Storage)]
    pub struct ReputationTokenContract {
        #[storage_field]
        psp37: psp37::Data,
        #[storage_field]
        access: access_control::Data,
        reputation: Mapping<AccountId, u128>,
    }

    const MANAGER: RoleType = ink::selector_id!("MANAGER");
    const MINTER: RoleType = ink::selector_id!("MINTER");

    impl PSP37 for ReputationTokenContract {}

    impl Reputation for ReputationTokenContract {
        #[ink(message)]
        #[modifiers(only_role(MINTER))]
        fn update_reputation(
            &mut self,
            account: AccountId,
            new_reputation: u128,
        ) -> Result<(), PSP37Error> {
            let level = Self::get_level(self.reputation.get(&account).unwrap_or(0)) as u32;
            let new_level = Self::get_level(new_reputation);

            for i in level..new_level {
                assert!(self
                    ._mint_to(account, [(Id::U32(i + 1), 1u128)].to_vec())
                    .is_ok());
            }
            self.reputation.insert(&account, &new_reputation);
            Ok(())
        }
    }

    impl Internal for ReputationTokenContract {
        fn get_level(reputation: u128) -> u32 {
            let mut level = 0;
            let mut threshold = 1_000_000_000;

            while reputation >= threshold {
                level += 1;
                threshold *= 10;
            }

            level
        }
    }

    impl ReputationTokenContract {
        #[ink(constructor)]
        pub fn new() -> Self {
            let mut _instance = Self::default();
            _instance._init_with_admin(_instance.env().caller());
            _instance
                .grant_role(MANAGER, _instance.env().caller())
                .expect("Should grant MANAGER role");

            _instance
        }

        #[ink(message)]
        #[modifiers(only_role(MANAGER))]
        pub fn set_minter(&mut self, account: AccountId) -> Result<(), PSP37Error> {
            self.grant_role(MINTER, account)?;
            Ok(())
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use openbrush::contracts::psp37::Id;

        #[ink::test]
        fn test_reputation() {
            let mut contract = ReputationTokenContract::new();
            let alice = AccountId::from([0x1; 32]);
            let bob = AccountId::from([0x2; 32]);
            let charlie = AccountId::from([0x3; 32]);

            contract.set_minter(alice).unwrap();
            contract.update_reputation(bob, 1_000_000_000).unwrap();
            contract.update_reputation(charlie, 10_000_000_000).unwrap();

            assert_eq!(contract.balance_of(bob, Some(Id::U32(1))), 1);
            assert_eq!(contract.balance_of(charlie, Some(Id::U32(1))), 1);
            assert_eq!(contract.balance_of(charlie, Some(Id::U32(2))), 1);
        }

        #[ink::test]
        fn unauthorized() {
            let mut contract = ReputationTokenContract::new();
            let alice = AccountId::from([0x1; 32]);
            let bob = AccountId::from([0x2; 32]);

            contract.set_minter(alice).unwrap();
            contract.update_reputation(bob, 1_000_000_000).unwrap();

            assert_eq!(contract.balance_of(bob, Some(Id::U32(1))), 1);

            ink::env::test::set_caller::<ink::env::DefaultEnvironment>(bob);
            let result = contract.update_reputation(bob, 10_000_000_000);
            assert!(result.is_err());
        }
    }
}
