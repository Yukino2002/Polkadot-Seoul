#![feature(proc_macro_hygiene)]
#![cfg_attr(not(feature = "std"), no_std)]

use ink_core::storage;
use ink_lang2 as ink;
use ink_types_node_runtime::{calls, AccountIndex, NodeRuntimeTypes, AccountId as AccountIdExt};
use scale::KeyedVec as _;

#[ink::contract(version = "0.1.0")]
mod dead_man_switch {
    /// Defines the storage of the contract.
    #[ink(storage)]
    struct DeadManSwitch {
        /// Every benefactor should send a heartbeat every `heartbeat_frequency` milliseconds.
        heartbeat_frequency: storage::Value<u64>,
        // TODO: Can't figure out how to store struct as hashmap value. Come back to it later.
        /*/// Store a mapping from benefactors AccountId to a Benefactor
        benefactors: storage::HashMap<AccountId, Benefactor>,*/
        /// Following 3 maps will have 1 entry each benefactor. This is ugly and should be replaced
        /// by one hashmap per benefactor where value is a struct.

        /// The amount of inheritance that it to be given to heir
        benefactor_balances: storage::HashMap<AccountId, Balance>,
        /// Heir's AccountId where inheritance will be transferred
        benefactor_heirs: storage::HashMap<AccountId, AccountId>,
        /// Last block number when the heartbeat was sent.
        /// XXX: Using Block number for now since can't find a way to access current time.
        benefactor_heartbeats: storage::HashMap<AccountId, Moment>
    }

    // TODO: Can't figure out how to store struct as hashmap value. Come back to it later.
    /*struct Benefactor {
        /// The amount of inheritance that it to be given to heir
        my_balance: storage::Value<Balance>,
        /// Heir's AccountId where inheritance will be transferred
        heir_account: storage::Value<AccountId>,
        /// Last time when the heartbeat was sent
        last_hearbeat_at: storage::Value<Moment>
    }*/

    impl DeadManSwitch {
        /// Constructor that initializes the `heartbeat_frequency` value to the given `heartbeat_frequency`.
        #[ink(constructor)]
        fn new(&mut self, heartbeat_frequency: u64) {
            self.heartbeat_frequency.set(heartbeat_frequency);
        }

        /// Return the current heartbeat frequency. A benefactor should ping at least once in this
        /// duration to be considered alive.
        #[ink(message)]
        fn get_heartbeat_frequency(&self) -> u64 {
            *self.heartbeat_frequency
        }

        /// Register a new benefactor based on the caller's AccountId. Only register if the caller
        /// is not already registered and return true. Return false if already registered.
        #[ink(message)]
        fn register_benefactor(&mut self, heir_id: storage::Value<AccountId>, inheritance: storage::Value<Balance>) -> bool {
            let caller = self.env().caller();
            // Any of the 3 structs can be checked here
            match self.benefactor_heartbeats.get(&caller) {
                None => {
                    // Can't find heartbeat, caller not registered already, so register
                    let caller_balance = self.env().transferred_balance();
                    if caller_balance < *inheritance {
                        // Caller doesn't have enough balance as he intends to leave in inheritance
                        self.env()
                            .emit_event(
                                BenefactorRegistrationFailed {
                                    benefactor: caller,
                                });
                        false
                    } else {
                        // Caller can register now
                        self.benefactor_balances.insert(caller, *inheritance);
                        self.benefactor_heirs.insert(caller, *heir_id);
                        self.update_heartbeat(caller);
                        self.env()
                            .emit_event(
                                NewBenefactor {
                                    benefactor: caller,
                                    heir: *heir_id,
                                    inheritance: *inheritance,
                                });
                        true
                    }
                }
                Some(_) => false        // caller already registered as a benefactor
            }
        }

        /// A heartbeat sent by a benefactor
        /// Process the heartbeat if the benefactor is registered and return true. Return false otherwise.
        #[ink(message)]
        fn ping(&mut self) -> bool {
            let caller = self.env().caller();
            match self.benefactor_heartbeats.get(&caller) {
                Some(_) => {
                    // Benefactor exists
                    self.update_heartbeat(caller);
                    true
                }
                None => false       // Benefactor does not exist
            }
        }

        /// Check if benefactor is alive. Proxies to `_is_alive`
        #[ink(message)]
        fn is_alive(&self, benefactor_id: storage::Value<AccountId>) -> bool {
            self._is_alive(&benefactor_id)
        }

        /// Call to claim inheritance of the benefactor. If the benefactor is dead, the inheritance
        /// is transferred to the heir, an event is logged and true is returned. If the benefactor
        /// is alive or non-existant, false is returned.
        #[ink(message)]
        fn claim_inheritance(&mut self, benefactor_id: storage::Value<AccountId>) -> bool {
            if self._is_alive(&benefactor_id) {
                false
            } else {
                // Cloning since need to pass them to even
                let heir_id = self.benefactor_heirs.get(&benefactor_id).unwrap().clone();
                let inheritance = self.benefactor_balances.get(&benefactor_id).unwrap().clone();

                // XXX: Following fails to compile with error "error: cannot find macro `vec` in this scope", probably an Ink! issue
                // let heir_bytes = heir_id.to_keyed_vec(&vec![]);
                // Convert an AccountId to AccountIdExt
                const EMPTY_PREFIX: &[u8] = b"";
                let heir_bytes = heir_id.to_keyed_vec(EMPTY_PREFIX);
                let mut heir_byte_array: [u8; 32] = [0u8; 32];
                heir_byte_array.clone_from_slice(&heir_bytes);
                let heir_addr = calls::Address::Id(AccountIdExt::from(heir_byte_array));

                // Prepare the transfer call.
                let transfer_call = calls::Balances::<NodeRuntimeTypes, AccountIndex>::transfer(heir_addr, inheritance);
                // TODO: Find a way to transfer balance, the following do not work
                // self.env().dispatch_call(&ransfer_call);
                // self.env().ext_dispatch_call(transfer_call);
                // self.ext_dispatch_call(transfer_call);
                // self.env().invoke_runtime(&transfer_call);

                self.env()
                    .emit_event(
                        InheritanceClaimed {
                            benefactor: *benefactor_id,
                            heir: heir_id,
                            inheritance,
                        });
                true
            }
        }

        /// Update last received heartbeat of the caller to the current block time
        fn update_heartbeat(&mut self, caller: AccountId) {
            let current_block_time = self.env().now_in_ms();
            self.benefactor_heartbeats.insert(caller, current_block_time);
        }

        /// A private helper.
        /// Checks if the benefactor is alive by comparing its last send heartbeat't block time to
        /// current block time and comparing against `self.heartbeat_frequency`. Returns false if
        /// the benefactor is not registered.
        fn _is_alive(&self, benefactor_id: &storage::Value<AccountId>) -> bool {
            match self.benefactor_heartbeats.get(benefactor_id) {
                Some(last_heartbeat) => {
                    let current_block_time = self.env().now_in_ms();
                    (current_block_time - last_heartbeat) <= *self.heartbeat_frequency
                }
                None => false
            }
        }
    }

    #[ink(event)]
    struct NewBenefactor {
        #[ink(topic)]
        benefactor: AccountId,
        #[ink(topic)]
        heir: AccountId,
        inheritance: Balance,
    }

    #[ink(event)]
    struct BenefactorRegistrationFailed {
        #[ink(topic)]
        benefactor: AccountId,
    }

    #[ink(event)]
    struct InheritanceClaimed {
        #[ink(topic)]
        benefactor: AccountId,
        #[ink(topic)]
        heir: AccountId,
        inheritance: Balance,
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        #[test]
        fn check_heartbeat_frequency_after_init() {
            let mut dead_man_switch = DeadManSwitch::new(100000);
            assert_eq!(dead_man_switch.get_heartbeat_frequency(), 100000);
        }

        #[test]
        fn check_benefactor_registration_fails_for_already_registered() {
            // TODO:
        }

        #[test]
        fn check_benefactor_registration_fails_when_insufficient_balance() {
            let mut dead_man_switch = DeadManSwitch::new(10u64);
            /*let heir: AccountId = [0u8; 32].into();
            dead_man_switch.register_benefactor()*/
            // TODO: Check event as well
        }

        #[test]
        fn check_benefactor_registration_works_for_unregistered() {
            // TODO: Check event as well
        }

        #[test]
        fn check_ping_fails_for_unregistered() {
            // TODO:
        }

        #[test]
        fn check_ping_works_for_registered() {
            // TODO:
        }
    }
}
