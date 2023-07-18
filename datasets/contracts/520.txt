#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

#[openbrush::contract]
pub mod staking {
    use openbrush::traits::{DefaultEnv, Storage};
    use staking_dapp::traits::reputation::ReputationRef;
    use staking_dapp::{
        impls::{reputation, staking},
        traits::staking::*,
    };

    const HALVING_PERIOD: Timestamp = 60 * 60 * 24 * 365;
    const INITIAL_REWARD_RATE: u128 = 50;
    const REPUTATION_PERIOD: Timestamp = 60 * 60 * 24;

    #[ink(storage)]
    #[derive(Storage)]
    pub struct StakingContract {
        #[storage_field]
        staking: staking::data::Data,
        #[storage_field]
        reputation: reputation::data::Data,
    }

    impl Internal for StakingContract {
        fn reward_per_token(&self) -> Result<Balance, StakingError> {
            if self.staking.total_staked == 0 {
                return Ok(self.staking.reward_per_token_stored);
            }

            let time_since_last_update = self
                .last_time_reward_applicable()?
                .checked_sub(self.staking.last_update_time)
                .ok_or(StakingError::OverflowError)?;

            let halving_duration = time_since_last_update
                .checked_div(HALVING_PERIOD)
                .ok_or(StakingError::DivideByZero)?;

            let current_reward_rate = self
                .staking
                .reward_rate
                .checked_div(
                    2u128
                        .checked_pow(
                            halving_duration
                                .try_into()
                                .map_err(|_| StakingError::OverflowError)?,
                        )
                        .ok_or(StakingError::OverflowError)?,
                )
                .ok_or(StakingError::DivideByZero)?;

            self.staking
                .reward_per_token_stored
                .checked_add(
                    (time_since_last_update as u128)
                        .checked_mul(current_reward_rate)
                        .ok_or(StakingError::OverflowError)?
                        .checked_mul(10u128.pow(18))
                        .ok_or(StakingError::OverflowError)?
                        .checked_div(self.staking.total_staked)
                        .ok_or(StakingError::DivideByZero)?,
                )
                .ok_or(StakingError::OverflowError)
        }

        fn update_reward(&mut self, staker: AccountId) -> Result<(), StakingError> {
            self.staking.reward_per_token_stored = self.reward_per_token()?;
            self.staking.last_update_time = self.last_time_reward_applicable()?;
            self.staking.rewards.insert(&staker, &self.earned(staker)?);
            self.staking
                .user_reward_per_token_paid
                .insert(&staker, &self.staking.reward_per_token_stored);
            Ok(())
        }

        fn earned(&self, staker: AccountId) -> Result<Balance, StakingError> {
            let staked_amount = self.staking.balances.get(&staker).unwrap_or(0);

            staked_amount
                .checked_mul(
                    self.reward_per_token()?
                        .checked_sub(
                            self.staking
                                .user_reward_per_token_paid
                                .get(&staker)
                                .unwrap_or(0),
                        )
                        .ok_or(StakingError::OverflowError)?,
                )
                .ok_or(StakingError::OverflowError)?
                .checked_add(self.staking.rewards.get(&staker).unwrap_or(0))
                .ok_or(StakingError::OverflowError)
        }

        fn last_time_reward_applicable(&self) -> Result<Timestamp, StakingError> {
            let now = Self::env().block_timestamp();

            if now
                < self
                    .staking
                    .last_update_time
                    .checked_add(HALVING_PERIOD)
                    .ok_or(StakingError::OverflowError)?
            {
                Ok(now)
            } else {
                self.staking
                    .last_update_time
                    .checked_add(HALVING_PERIOD)
                    .ok_or(StakingError::OverflowError)
            }
        }

        fn update_reputation(&mut self, staker: AccountId) -> Result<(), StakingError> {
            let now = Self::env().block_timestamp();
            let last_time_update = self
                .reputation
                .reputation_last_update
                .get(&staker)
                .unwrap_or(0);

            let time_elapsed = now
                .checked_sub(last_time_update)
                .ok_or(StakingError::OverflowError)?;

            let rate = time_elapsed
                .checked_div(REPUTATION_PERIOD)
                .ok_or(StakingError::DivideByZero)?;

            let balance = self.staking.balances.get(&staker).unwrap_or(0);

            let new_reputation = balance
                .checked_mul(rate as u128)
                .ok_or(StakingError::OverflowError)?
                .checked_div(10u128.pow(18))
                .ok_or(StakingError::DivideByZero)?;

            self.reputation.reputation_last_update.insert(&staker, &now);

            ReputationRef::update_reputation(
                &self.reputation.reputation_token,
                staker,
                new_reputation,
            )?;
            Ok(())
        }
    }

    impl Staking for StakingContract {}

    impl StakingContract {
        #[ink(constructor)]
        pub fn new(staking_token: AccountId, reputation_token: AccountId) -> Self {
            let mut instance = StakingContract {
                staking: Default::default(),
                reputation: Default::default(),
            };

            instance.staking.staking_token = staking_token;
            instance.staking.reward_rate = INITIAL_REWARD_RATE;
            instance.staking.last_update_time = instance.env().block_timestamp();
            instance.reputation.reputation_token = reputation_token;
            instance
        }

        #[ink(message)]
        pub fn claim_reputation(&mut self) -> Result<(), StakingError> {
            self.update_reputation(self.env().caller())?;
            Ok(())
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use ink::codegen::Env;
        use staking_token::token::StakingTokenContract;

        const INITIAL_SUPPLY: Balance = 1_000_000_000 * 10u128.pow(18);

        #[ink::test]
        fn instantiation() {
            let name = Some(openbrush::traits::String::from("My Staking Token"));
            let symbol = Some(openbrush::traits::String::from("MST"));
            let staking_token =
                StakingTokenContract::new(name.clone(), symbol.clone(), 18, INITIAL_SUPPLY);

            let reputation_token = AccountId::from([0x1; 32]);

            let staking_contract =
                StakingContract::new(staking_token.env().account_id(), reputation_token);
            assert_eq!(staking_contract.staking.total_staked, 0);
            assert_eq!(staking_contract.staking.reward_rate, 50);
            assert_eq!(staking_contract.staking.reward_per_token_stored, 0);
            assert_eq!(staking_contract.staking.last_update_time, 0);
            assert_eq!(
                staking_contract.staking.staking_token,
                staking_token.env().account_id()
            );
        }

    }

    #[cfg(all(test, feature = "e2e-tests"))]
    mod e2e_tests {

        use super::*;
        /// A helper function used for calling contract messages.
        use ink_e2e::build_message;
        use openbrush::contracts::psp22::psp22_external::PSP22;
        use reputation_token::token::ReputationTokenContractRef;
        use staking_dapp::traits::staking::staking_external::Staking;
        use staking_token::token::StakingTokenContractRef;

        const INITIAL_SUPPLY: Balance = 1_000_000_000 * 10u128.pow(18);
        const STAKING_ALLOCATION: u128 = 70;

        /// The End-to-End test `Result` type.
        type E2EResult<T> = std::result::Result<T, Box<dyn std::error::Error>>;

        /// We test that we can upload and instantiate the contract using its constructor.
        #[ink_e2e::test(
            additional_contracts = "../staking_token/Cargo.toml ../reputation_token/Cargo.toml"
        )]
        async fn instantiation_works(mut client: ink_e2e::Client<C, E>) -> E2EResult<()> {
            // Instantiate the staking token contract
            let staking_token = client
                .instantiate(
                    "staking_token",
                    &ink_e2e::alice(),
                    StakingTokenContractRef::new(
                        Some(openbrush::traits::String::from("My Staking Token")),
                        Some(openbrush::traits::String::from("MST")),
                        18,
                        INITIAL_SUPPLY,
                    ),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            let reputation_token = client
                .instantiate(
                    "reputation_token",
                    &ink_e2e::alice(),
                    ReputationTokenContractRef::new(),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            let staking_contract = client
                .instantiate(
                    "staking_contract",
                    &ink_e2e::alice(),
                    StakingContractRef::new(staking_token, reputation_token),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Check total staked amount at the beginning is 0
            let token_name = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.total_staked());
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &token_name, 0, None)
                    .await
                    .return_value(),
                0
            );

            // Check staked amount of the user at the beginning is 0
            let bob_account = ink_e2e::account_id(ink_e2e::AccountKeyring::Bob);
            let bob_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.balance_of(bob_account));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &bob_staked_amount, 0, None)
                    .await
                    .return_value(),
                0
            );

            Ok(())
        }

        // test that we can stake tokens
        #[ink_e2e::test]
        async fn stake_works(mut client: Client<C, E>) -> E2EResult<()> {
            // Instantiate the staking token contract
            let staking_token = client
                .instantiate(
                    "staking_token",
                    &ink_e2e::alice(),
                    StakingTokenContractRef::new(
                        Some(openbrush::traits::String::from("My Staking Token")),
                        Some(openbrush::traits::String::from("MST")),
                        18,
                        INITIAL_SUPPLY,
                    ),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Instantiate the reputation token contract
            let reputation_token = client
                .instantiate(
                    "reputation_token",
                    &ink_e2e::alice(),
                    ReputationTokenContractRef::new(),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Instantiate the staking contract
            let staking_contract = client
                .instantiate(
                    "staking_contract",
                    &ink_e2e::alice(),
                    StakingContractRef::new(staking_token, reputation_token),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Grant Staking contract Minter role in the reputation token contract
            let grant_minter_role =
                build_message::<ReputationTokenContractRef>(reputation_token.clone())
                    .call(|contract| contract.set_minter(staking_contract.clone()));

            client
                .call(&ink_e2e::alice(), grant_minter_role, 0, None)
                .await
                .expect("grant_minter_role failed");

            // Transfer 70% of the staking tokens to the staking contract
            let transfer =
                build_message::<StakingTokenContractRef>(staking_token.clone()).call(|contract| {
                    contract.transfer(
                        staking_contract.clone(),
                        INITIAL_SUPPLY * STAKING_ALLOCATION / 100,
                        vec![],
                    )
                });

            client
                .call(&ink_e2e::alice(), transfer, 0, None)
                .await
                .expect("transfer failed");

            // Alice stakes 1_000_000 tokens again without allowing the staking contract to spend tokens on her behalf
            let alice_stake = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.stake(1_000_000));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &alice_stake, 0, None)
                    .await
                    .return_value(),
                Err(StakingError::InsufficientAllowance)
            );

            // Alice allows the staking contract to spend 1_000_000 tokens on her behalf
            let approve = build_message::<StakingTokenContractRef>(staking_token.clone())
                .call(|contract| contract.approve(staking_contract.clone(), 1_000_000));
            client
                .call(&ink_e2e::alice(), approve, 0, None)
                .await
                .expect("approve failed");

            // Alice stakes 1_000_000 tokens
            let alice_stake = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.stake(1_000_000));
            client
                .call(&ink_e2e::alice(), alice_stake, 0, None)
                .await
                .expect("stake failed");

            // Check total staked amount
            let total_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.total_staked());
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &total_staked_amount, 0, None)
                    .await
                    .return_value(),
                1_000_000
            );

            // Check staked amount of alice
            let alice_account = ink_e2e::account_id(ink_e2e::AccountKeyring::Alice);
            let alice_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.balance_of(alice_account));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &alice_staked_amount, 0, None)
                    .await
                    .return_value(),
                1_000_000
            );

            // Bob stakes 500_000 tokens
            // Alic transfers 500_000 tokens to Bob
            let transfer =
                build_message::<StakingTokenContractRef>(staking_token.clone()).call(|contract| {
                    contract.transfer(
                        ink_e2e::account_id(ink_e2e::AccountKeyring::Bob),
                        500_000,
                        vec![],
                    )
                });
            client
                .call(&ink_e2e::alice(), transfer, 0, None)
                .await
                .expect("transfer failed");

            // Bob allows the staking contract to spend 500_000 tokens on his behalf
            let approve = build_message::<StakingTokenContractRef>(staking_token.clone())
                .call(|contract| contract.approve(staking_contract.clone(), 500_000));
            client
                .call(&ink_e2e::bob(), approve, 0, None)
                .await
                .expect("approve failed");

            // Bob stakes 500_000 tokens
            let bob_stake = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.stake(500_000));
            client
                .call(&ink_e2e::bob(), bob_stake, 0, None)
                .await
                .expect("stake failed");

            // Check total staked amount
            let total_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.total_staked());
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &total_staked_amount, 0, None)
                    .await
                    .return_value(),
                1_500_000
            );

            // Check staked amount of bob
            let bob_account = ink_e2e::account_id(ink_e2e::AccountKeyring::Bob);
            let bob_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.balance_of(bob_account));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &bob_staked_amount, 0, None)
                    .await
                    .return_value(),
                500_000
            );

            Ok(())
        }

        // test that we can unstake tokens
        #[ink_e2e::test]
        async fn withdraw_works(mut client: Client<C, E>) -> E2EResult<()> {
            // Instantiate the staking token contract
            let staking_token = client
                .instantiate(
                    "staking_token",
                    &ink_e2e::alice(),
                    StakingTokenContractRef::new(
                        Some(openbrush::traits::String::from("My Staking Token")),
                        Some(openbrush::traits::String::from("MST")),
                        18,
                        INITIAL_SUPPLY,
                    ),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Instantiate the reputation token contract
            let reputation_token = client
                .instantiate(
                    "reputation_token",
                    &ink_e2e::alice(),
                    ReputationTokenContractRef::new(),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Instantiate the staking contract
            let staking_contract = client
                .instantiate(
                    "staking_contract",
                    &ink_e2e::alice(),
                    StakingContractRef::new(staking_token, reputation_token),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Grant Staking contract Minter role in the reputation token contract
            let grant_minter_role =
                build_message::<ReputationTokenContractRef>(reputation_token.clone())
                    .call(|contract| contract.set_minter(staking_contract.clone()));

            client
                .call(&ink_e2e::alice(), grant_minter_role, 0, None)
                .await
                .expect("grant_minter_role failed");

            // Transfer 70% of the staking tokens to the staking contract
            let transfer =
                build_message::<StakingTokenContractRef>(staking_token.clone()).call(|contract| {
                    contract.transfer(
                        staking_contract.clone(),
                        INITIAL_SUPPLY * STAKING_ALLOCATION / 100,
                        vec![],
                    )
                });

            client
                .call(&ink_e2e::alice(), transfer, 0, None)
                .await
                .expect("transfer failed");

            // Alice tries to withdraw 1_000_000 tokens from the staking contract
            let alice_withdraw = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.withdraw(1_000_000));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &alice_withdraw, 0, None)
                    .await
                    .return_value(),
                Err(StakingError::InsufficientBalance),
            );

            // Alice allows the staking contract to spend 1_000_000 tokens on her behalf
            let approve = build_message::<StakingTokenContractRef>(staking_token.clone())
                .call(|contract| contract.approve(staking_contract.clone(), 1_000_000));
            client
                .call(&ink_e2e::alice(), approve, 0, None)
                .await
                .expect("approve failed");

            // Alice stakes 1_000_000 tokens
            let alice_stake = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.stake(1_000_000));
            client
                .call(&ink_e2e::alice(), alice_stake, 0, None)
                .await
                .expect("stake failed");

            // Check total staked amount
            let total_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.total_staked());
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &total_staked_amount, 0, None)
                    .await
                    .return_value(),
                1_000_000
            );

            // Check staked amount of alice
            let alice_account = ink_e2e::account_id(ink_e2e::AccountKeyring::Alice);
            let alice_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.balance_of(alice_account));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &alice_staked_amount, 0, None)
                    .await
                    .return_value(),
                1_000_000
            );

            // Alice withdraws 500_000 tokens
            let alice_withdraw = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.withdraw(500_000));
            client
                .call(&ink_e2e::alice(), alice_withdraw, 0, None)
                .await
                .expect("withdraw failed");

            // Check total staked amount
            let total_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.total_staked());
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &total_staked_amount, 0, None)
                    .await
                    .return_value(),
                500_000
            );

            // Check staked amount of alice
            let alice_staked_amount = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.balance_of(alice_account));
            assert_eq!(
                client
                    .call_dry_run(&ink_e2e::alice(), &alice_staked_amount, 0, None)
                    .await
                    .return_value(),
                500_000
            );

            Ok(())
        }

        // Test reward distribution
        #[ink_e2e::test]
        async fn rewards_distribution_works(mut client: Client<C, E>) -> E2EResult<()> {
            // Instantiate the staking token contract
            let staking_token = client
                .instantiate(
                    "staking_token",
                    &ink_e2e::alice(),
                    StakingTokenContractRef::new(
                        Some(openbrush::traits::String::from("My Staking Token")),
                        Some(openbrush::traits::String::from("MST")),
                        18,
                        INITIAL_SUPPLY,
                    ),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Instantiate the reputation token contract
            let reputation_token = client
                .instantiate(
                    "reputation_token",
                    &ink_e2e::alice(),
                    ReputationTokenContractRef::new(),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Instantiate the staking contract
            let staking_contract = client
                .instantiate(
                    "staking_contract",
                    &ink_e2e::alice(),
                    StakingContractRef::new(staking_token, reputation_token),
                    0,
                    None,
                )
                .await
                .expect("instantiate failed")
                .account_id;

            // Grant Staking contract Minter role in the reputation token contract
            let grant_minter_role =
                build_message::<ReputationTokenContractRef>(reputation_token.clone())
                    .call(|contract| contract.set_minter(staking_contract.clone()));

            client
                .call(&ink_e2e::alice(), grant_minter_role, 0, None)
                .await
                .expect("grant_minter_role failed");

            // Transfer 70% of the staking tokens to the staking contract
            let transfer =
                build_message::<StakingTokenContractRef>(staking_token.clone()).call(|contract| {
                    contract.transfer(
                        staking_contract.clone(),
                        INITIAL_SUPPLY * STAKING_ALLOCATION / 100,
                        vec![],
                    )
                });

            client
                .call(&ink_e2e::alice(), transfer, 0, None)
                .await
                .expect("transfer failed");

            // Alice allows the staking contract to spend 100_000_000^18 tokens on her behalf
            let approve =
                build_message::<StakingTokenContractRef>(staking_token.clone()).call(|contract| {
                    contract.approve(staking_contract.clone(), 100_000_000 * 10u128.pow(18))
                });
            client
                .call(&ink_e2e::alice(), approve, 0, None)
                .await
                .expect("approve failed");

            // Alice stakes 100_000_000^18 tokens
            let alice_stake = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.stake(100_000_000 * 10u128.pow(18)));
            client
                .call(&ink_e2e::alice(), alice_stake, 0, None)
                .await
                .expect("stake failed");

            // TODO How to simulate elapsed time here ? Does this work ?
            ink::env::test::set_block_timestamp::<ink::env::DefaultEnvironment>(HALVING_PERIOD);
            ink::env::test::advance_block::<ink::env::DefaultEnvironment>();

            // Get Reward for Alice
            let alice_reward = build_message::<StakingContractRef>(staking_contract.clone())
                .call(|contract| contract.get_reward());
            client
                .call(&ink_e2e::alice(), alice_reward, 0, None)
                .await
                .expect("get_reward failed");

            // Check the balance of Alice
            let alice_account = ink_e2e::account_id(ink_e2e::AccountKeyring::Alice);
            let _alice_balance = build_message::<StakingTokenContractRef>(staking_token.clone())
                .call(|contract| contract.balance_of(alice_account));
            // assert_eq!(
            //     client
            //         .call_dry_run(&ink_e2e::alice(), &alice_balance, 0, None)
            //         .await
            //         .return_value(),
            //     0
            // );

            Ok(())
        }
    }
}
