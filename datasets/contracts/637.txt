#![cfg_attr(not(feature = "std"), no_std)]

#[ink::contract]
mod cross_contract_flipper {
    use flipper::Flipper;

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct CrossContractFlipper {
        /// The other contract
        flipper: Flipper,
    }

    impl CrossContractFlipper {
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        pub fn new() -> Self {
            Self {
                flipper: Flipper::default()
            }
        }

        // #[ink(constructor)]
        // pub fn new(
        //     other_contract_code_hash: Hash,
        // ) -> Self {
        //     let other_contract = Flipper::new(false)
        //         .endowment(total_balance / 4)
        //         .code_hash(other_contract_code_hash)
        //         .instantiate()
        //         .expect("failed at instantiating the `OtherContract` contract");
        //     Self {
        //         other_contract
        //     }
        // }

        /// Calls the other contract.
        #[ink(message)]
        pub fn call_other_contract(&self) -> bool {
            self.flipper.get()
        }

        /// Calls the other contract to flip.
        #[ink(message)]
        pub fn call_other_contract_to_flip(&mut self) {
            self.flipper.flip()
        }
    }

}
