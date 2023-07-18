#![cfg_attr(not(feature = "std"), no_std)]

#[ink::contract]
mod delegator {
    use accumulator::AccumulatorRef;

    #[ink(storage)]
    pub struct Delegator {
        /// Says which of `adder` or `subber` is currently in use.
        // which: Which,
        /// The `accumulator` smart contract.
        accumulator: AccumulatorRef,
    }

    impl Delegator {
        /// Instantiate a `delegator` contract with the given sub-contract codes.
        #[ink(constructor)]
        pub fn new(init_value: i32, version: u32, accumulator_code_hash: Hash) -> Self {
            let total_balance = Self::env().balance();
            let salt = version.to_le_bytes();
            let accumulator = AccumulatorRef::new()
                .endowment(total_balance / 4)
                .code_hash(accumulator_code_hash)
                .salt_bytes(salt)
                .instantiate();

            Self {
                // which: Which::Adder,
                accumulator,
            }
        }

        /// Returns the `accumulator` value.
        #[ink(message)]
        pub fn get(&self) -> i32 {
            self.accumulator.get()
        }

        /// Returns the `accumulator` value.
        #[ink(message)]
        pub fn inc(&mut self, by: i32) {
            self.accumulator.inc(by);
        }
    }
}