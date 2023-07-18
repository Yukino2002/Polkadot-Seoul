#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
mod counter {
    #[ink(storage)]
    pub struct Counter {
        count: u32,
    }

    impl Counter {
        #[ink(constructor)]
        pub fn new(init_value: u32) -> Self {
            Self { count: init_value }
        }

        #[ink(message)]
        pub fn get(&self) -> u32 {
            self.count
        }

        #[ink(message)]
        pub fn inc(&mut self) {
            self.count = self.count.saturating_add(1);
        }

        #[ink(message)]
        pub fn dec(&mut self) {
            self.count = self.count.saturating_sub(1);
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        use ink_lang as ink;

        #[ink::test]
        fn new_works() {
            let counter = Counter::new(10);
            assert_eq!(counter.get(), 10);
        }

        #[ink::test]
        fn it_works() {
            let mut counter = Counter::new(0);
            counter.inc();
            assert_eq!(counter.get(), 1);
            counter.dec();
            assert_eq!(counter.get(), 0);
            counter.dec();
            assert_eq!(counter.get(), 0);
        }
    }
}
