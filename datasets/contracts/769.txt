#![cfg_attr(not(feature = "std"), no_std)]
use ink_lang as ink;
#[ink::contract]
mod Pooling {
    use erc20::{ Erc20Ref };
    use ink_env;
    use ink_storage::{
        collections::HashMap as StorageHashMap,
        traits::{ PackedLayout, SpreadLayout },
    };
    use ink_prelude::{ vec::Vec, vec };
    #[ink(storage)]
    pub struct MyPool {
        token: Erc20Ref,
        locked: StorageHashMap<AccountId, Vec<Lock>>
    }
    #[derive( scale::{ Encode, Decode }, PackedLayout, SpreadLayout )]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct Lock {
        amount: Balance,
        at: u128,
    }

    impl MyPool {
        #[ink(constructor)]
        pub fn new(token_account_id: AccountId) -> Self {
            let erc20 = Erc20Ref::from_account_id(token_account_id);
            Self {
                locked: StorageHashMap::new(),
                token: erc20,
            }
        }
        // staking operation
        #[ink(message)]
        pub fn stake(&mut self, amount: Balance) {
            let staker = self.env().caller();
            let current_block_time = u128::from(self.env().block_timestamp());
            if self.token.balance_of(staker) < amount {
                ink_env::debug_println!("{}", "Not enough");
                return;
            } else if self.locked.contains_key(&staker) {
                let mut staked_amount = self.locked.get_mut(&staker).unwrap();
                staked_amount.push(
                    Lock {
                    at: current_block_time,
                    amount,
                });
            } else {
                self.locked.insert( 
                    staker,
                    vec![Lock {
                        at: current_block_time,
                        amount,
                    }],
                );
            }
            self.token.approve_from_to(staker, self.env().account_id(), amount);
            self.token.transfer_from(staker, self.env().account_id(), amount);
        }

        #[ink(message)]
        pub fn claim(&mut self, amount: Balance) {
            let staker = self.env().caller();
            let mut claim_amount: Balance = amount.clone();
            let mut claim_balance: Balance;
            let locking_length = self.locked.get(&staker).unwrap().len();
            (0..(locking_length - 1)).for_each(|i| {
                let locked_time: Balance = self.locked.get(&staker).unwrap()[i].at;
                let locked_amount: Balance = self.locked.get(&staker).unwrap()[i].amount;
                let offset_day = (u128::from(self.env().block_timestamp()) - locked_time) / 86400000;
                //calculate claimable percent when claim is required
                let claim_percent = match offset_day {
                    0..=5 => 0.5 + offset_day * 0.1,
                    // after 5
                    5.. => 1,

                    _ => 0 
                }
                //check if claim amount is exceeded
                claim_amount = claim_amount - locked_amount * claim_percent
                if claim_amount < 0 {
                    claim_balance = amount.clone()
                }
                if i == (locking_length - 1) & claim_amount > 0 {
                    ink_env::debug_println!("{}", "Hey, You have Not enough amount");
                    return;
                }
            });
            let mut amount = _amount.clone(), i = 0;
            // token transfer to staker
            self.token.approve_from_to(self.env().account_id(), staker, claim_balance);
            self.token.transfer_from(self.env().account_id(), staker, claim_balance);
        }
    }

    #[cfg(test)]
    mod tests {
        #[ink::test]
        fn default_works() {
            
        }
    }
}
