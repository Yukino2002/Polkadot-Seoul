#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
pub mod dummy_risk_strategy {
    use logics::traits::risk_strategy::*;
    use openbrush::traits::Storage;

    #[ink(storage)]
    #[derive(Default, Storage)]
    pub struct DummyRiskStrategyContract {
        result: bool,
        collateral_amount: Balance,
    }

    impl RiskStrategy for DummyRiskStrategyContract {
        #[ink(message)]
        fn validate_borrow(
            &self,
            _account: AccountId,
            _asset: AccountId,
            _amount: Balance,
        ) -> Result<()> {
            if self.result {
                return Ok(())
            }
            Err(0)
        }

        #[ink(message)]
        fn validate_withdraw(
            &self,
            _account: AccountId,
            _asset: AccountId,
            _amount: Balance,
        ) -> Result<()> {
            if self.result {
                return Ok(())
            }
            Err(0)
        }

        #[ink(message)]
        fn validate_liquidation(
            &self,
            _liquidatee: AccountId,
            _collateral_asset: AccountId,
            _debt_asset: AccountId,
            _debt_amount: Balance,
        ) -> Result<Balance> {
            Ok(self.collateral_amount)
        }
    }

    impl DummyRiskStrategyContract {
        #[ink(constructor)]
        pub fn new() -> Self {
            Self::default()
        }

        #[ink(message)]
        pub fn set_result(&mut self, result: bool) {
            self.result = result;
        }

        #[ink(message)]
        pub fn set_collateral_amount(&mut self, collateral_amount: Balance) {
            self.collateral_amount = collateral_amount;
        }
    }
}
