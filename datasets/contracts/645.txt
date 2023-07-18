#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
pub mod zk_vote_dao_governance_token {
    // imports from ink!
    use ink_prelude::string::String;
    use ink_storage::traits::SpreadAllocate;
    use openbrush::contracts::ownable::*;

    // imports from openbrush

    use openbrush::contracts::psp22::extensions::metadata::*;
    use openbrush::contracts::psp22::extensions::mintable::*;
    use openbrush::traits::Storage;

    #[ink(storage)]
    #[derive(Default, SpreadAllocate, Storage)]
    pub struct AlephVote {
        #[storage_field]
        psp22: psp22::Data,
        #[storage_field]
        ownable: ownable::Data,
        #[storage_field]
        metadata: metadata::Data,
    }

    // Section contains default implementation without any modifications
    impl PSP22 for AlephVote {}
    impl Ownable for AlephVote {}
    impl PSP22Mintable for AlephVote {
        #[ink(message)]
        #[openbrush::modifiers(only_owner)]
        fn mint(&mut self, account: AccountId, amount: Balance) -> Result<(), PSP22Error> {
            self._mint(account, amount)
        }
    }
    impl PSP22Metadata for AlephVote {}

    impl AlephVote {
        #[ink(constructor)]
        pub fn new(
            initial_supply: Balance,
            name: Option<String>,
            symbol: Option<String>,
            decimals: u8,
        ) -> Self {
            ink_lang::codegen::initialize_contract(|_instance: &mut AlephVote| {
                _instance
                    ._mint(_instance.env().caller(), initial_supply)
                    .expect("Should mint");
                _instance._init_with_owner(_instance.env().caller());
                _instance.metadata.name = name;
                _instance.metadata.symbol = symbol;
                _instance.metadata.decimals = decimals;
            })
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use ink_lang as ink;

    #[ink::test]
    fn total_supply_works() {
        let test_token = zk_vote_dao_governance_token::AlephVote::new(
            1000,
            Some("Test Vote Token".to_string()),
            Some("TVT".to_string()),
            18,
        );
        assert_eq!(test_token.total_supply(), 1000);
    }
}
