#![cfg_attr(not(feature = "std"), no_std)]
#![allow(clippy::new_without_default)]

use ink_lang as ink;

#[ink::contract]
pub mod plasm_faucet {
    use chrono::prelude::*;
    #[cfg(not(feature = "ink-as-dependency"))]
    use ink_storage::{collections::HashMap as StorageHashMap, lazy::Lazy};

    #[ink(storage)]
    pub struct PlasmFaucet {
        AMOUNT: u128,
        owner: AccountId,
        cooldownMap: StorageHashMap<AccountId, u32>,
        cooldown: u32,
    }

    //error types
    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        TransferFailed,
        InsufficientFunds,
        BelowSupsistenceThreshold,
    }

    impl PlasmFaucet {
        /// Create new instance of this contract.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                AMOUNT: 50,
                cooldownMap: StorageHashMap::new(),
                cooldown: 5,
                owner: Self::env().caller(),
            }
        }

        /// Transfers `self.AMOUNT` of PLD to caller.
        ///
        /// # Errors
        ///
        /// - Panics if requested transfer exceeds contract balance.
        /// - Panics if requested transfer brings the contract balance
        ///   below the subsistence threshold.
        /// - Panics if transfer fails for any other reason.
        #[ink(message)]
        pub fn drip(&mut self, to: AccountId) {
            //check cooldown
            let now = Utc::now().second();
            let elapsed = now - self.cooldownMap.get(&to).unwrap_or(&now);
            if elapsed < self.cooldown {
                panic!(
                    "You must wait {} more seconds before requesting PLD!",
                    self.cooldown - elapsed
                );
            }

            ink_env::debug_println(&ink_prelude::format!(
                "contract balance: {}",
                self.env().balance()
            ));

            assert!(self.AMOUNT <= self.env().balance(), "insufficient funds!");

            match self.env().transfer(to, self.AMOUNT) {
                Err(ink_env::Error::BelowSubsistenceThreshold) => {
                    panic!(
                        "requested transfer would have brought contract\
                    below subsistence threshold!"
                    )
                }

                Err(_) => panic!("transfer failed!"),
                Ok(_) => {
                    self.cooldownMap.insert(to, Utc::now().second());
                }
            }
        }

        /// Asserts that the token self.amount sent as payment with this call
        /// is exactly `self.AMOUNT`. This method will fail otherwise, and the
        /// transaction would then be reverted.
        ///
        /// # Note
        ///
        /// The method needs to be annotated with `payable`; only then it is
        /// allowed to receive value as part of the call.
        #[ink(message, payable, selector = "0xCAFEBABE")]
        pub fn was_it_amt(&self) {
            let msg =
                ink_prelude::format!("received payment: {}", self.env().transferred_balance());
            ink_env::debug_println(&msg);
            assert!(
                self.env().transferred_balance() == self.AMOUNT,
                "payment was not {}",
                self.AMOUNT
            );
        }

        fn check_owner(&self) {
            if self.env().caller() != self.owner {
                panic!(
                    "Only this owner can execute that function , {:?}",
                    self.owner
                );
            }
        }

        pub fn change_amount(&mut self, new_amount: u128) {
            self.check_owner();
            self.AMOUNT = new_amount;
        }

        pub fn change_owner(&mut self, new_owner: AccountId) {
            self.check_owner();
            self.owner = new_owner;
        }
    }
}
