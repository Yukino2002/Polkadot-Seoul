#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;
use rand::{self, Rng, thread_rng};

#[ink::contract]
mod chance {

    /// Defines the storage of your contract.
    /// Add new fields to the below struct in order
    /// to add new static storage fields to your contract.
    #[ink(storage)]
    pub struct Chance {
        players: Vec<AccountId>,
        player_count: u32,
        last_winner: AccountId,
        round_count: u32,
        max_players: u32,
    }

    impl Chance {
        #[ink(constructor)]
        pub fn new(max_players: u32) -> Self {
            Self {
                max_players,
                players: Vec::new(),
                player_count: 0,
                last_winner: AccountId::from([0x0; 32]),
                round_count: 0,
            }
        }

        /// A message that can be called on instantiated contracts.
        /// This one pushes the caller into the round players.
        #[ink(message, payable)]
        pub fn enter(&mut self) {
            self.players.push(self.env().caller());
            self.player_count += 1;
            if self.player_count == self.max_players {
                self.start_round();
            }
        }

        #[ink(message)]
        pub fn start_round(&mut self) {
            let winner = self.choose_winner();
            self.transfer(winner, self.env().balance());
            self.last_winner = winner;
            self.round_count += 1;
            self.player_count = 0;
            self.players = Vec::new();
        }

        /// Chooses a random winner from the round players.
        #[ink(message)]
        pub fn choose_winner(&self) -> AccountId {
            self.players[rand::thread_rng().gen_range(0..self.players.len())]
        }

        /// Transfers the given amount to the given account.
        #[ink(message)]
        pub fn transfer(&mut self, to: AccountId, amount: Balance) {
            self.env().transfer(to, amount).unwrap();
        }

        /// Getters

        /// Returns the current round players.
        #[ink(message)]
        pub fn get_players(&self) -> Vec<AccountId> {
            self.players
        }

        /// Returns the current round players count.
        #[ink(message)]
        pub fn get_player_count(&self) -> u32 {
            self.player_count
        }

        /// Returns the last winner.
        #[ink(message)]
        pub fn get_last_winner(&self) -> AccountId {
            self.last_winner
        }
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        /// Imports `ink_lang` so we can use `#[ink::test]`.
        use ink_lang as ink;

        /// We test if the default constructor does its job.
        #[ink::test]
        fn default_works() {
            let chance = Chance::default();
            assert_eq!(chance.get(), false);
        }

        /// We test a simple use case of our contract.
        #[ink::test]
        fn it_works() {
            let mut chance = Chance::new(false);
            assert_eq!(chance.get(), false);
            chance.flip();
            assert_eq!(chance.get(), true);
        }
    }
}
