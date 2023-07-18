#![cfg_attr(not(feature = "std"), no_std)]

#[openbrush::contract]
pub mod one {
    use one_two_project::traits::{one::*, two::*};

    #[ink(storage)]
    pub struct OneContract {
        strength: u16,
    }

    impl OneContract {
        #[ink(constructor)]
        pub fn new(s: u16) -> Self {
            OneContract { strength: s }
        }
    }

    impl One for OneContract {
        #[ink(message)]
        fn change(&mut self, l: u16) {
            self.strength = l;
        }

        #[ink(message)]
        fn show(&self) -> u16 {
            self.strength
        }

        #[ink(message)]
        fn change_two(&mut self, two: AccountId, l: u16) {
            let two_instance: &TwoRef = &two;
            two_instance.change(l);
        }
    }
}
