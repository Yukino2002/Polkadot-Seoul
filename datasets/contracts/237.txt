#![cfg_attr(not(feature = "std"), no_std, no_main)]

#[ink::contract]
mod erc20 {

    use ink::storage::Mapping;

    #[ink(storage)]
    #[derive(Default)]
    pub struct Erc20 {
        total_supply: Balance,
        balances: Mapping<AccountId, Balance>,
        allowances: Mapping<(AccountId, AccountId), Balance>,
    }

    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        from: Option<AccountId>,
        #[ink(topic)]
        to: Option<AccountId>,
        value: Balance,
    }

    #[ink(event)]
    pub struct Approval {
        #[ink(topic)]
        owner: AccountId,
        #[ink(topic)]
        spender: AccountId,
        value: Balance,
    }

    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        InsufficientBalance,
        InsufficientAllowance,
    }

    type Result<T> = core::result::Result<T, Error>;

    impl Erc20 {
        #[ink(constructor)]
        pub fn new(total_supply: Balance) -> Self {
            let mut balances = Mapping::new();
            balances.insert(Self::env().caller(), &total_supply);

            Self::env().emit_event(Transfer {
                from: None,
                to: Some(Self::env().caller()),
                value: total_supply,
            });

            Self {
                total_supply,
                balances,
                ..Default::default()
            }
        }

        #[ink(message)]
        pub fn total_supply(&self) -> Balance {
            self.total_supply
        }

        #[ink(message)]
        pub fn balance_of(&self, owner: AccountId) -> Balance {
            self.balances.get(owner).unwrap_or_default()
        }
        
        #[ink(message)]
        pub fn allowance(&self, owner: AccountId, spender: AccountId) -> Balance {
            self.allowances.get((owner, spender)).unwrap_or_default()
        }

        #[ink(message)]
        pub fn transfer(&mut self, to: AccountId, value: Balance) -> Result<()> {
            self.transfer_helper(self.env().caller(), to, value)
        }

        #[ink(message)]
        // pub fn transfer_from(
        //     &mut self,
        //     from: AccountId,
        //     to: AccountId,
        //     value: Balance,
        // ) -> Result<()> {
        //     let caller = self.env().caller();
        //     let allowance = self.allowance(caller, from);
        //     if allowance < value {
        //         return Err(Error::InsufficientAllowance);
        //     }
        //     let from_balance = self.balance_of(from);
        //     if from_balance < value {
        //         return Err(Error::InsufficientBalance);
        //     }
        //     self.transfer_helper(from, to, value)?;
        //     self.allowances.insert((from, caller), &(allowance - value));
        //     Ok(())
        // }

        pub fn transfer_from(
            &mut self,
            from: AccountId,
            to: AccountId,
            value: Balance,
        ) -> Result<()> {
            let caller = self.env().caller();
            let allowance = self.allowance(caller, from);
            if allowance < value {
                return Err(Error::InsufficientAllowance);
            }

            self.transfer_helper(caller, to, value)?;
            self.allowances.insert((caller, from), &(allowance - value));
            Ok(())
        }

        #[ink(message)]
        pub fn approve(&mut self, spender: AccountId, value: Balance) -> Result<()> {
            let caller = self.env().caller();
            self.allowances.insert((caller, spender), &value);
            self.env().emit_event(Approval {
                owner: caller,
                spender,
                value,
            });
            Ok(())
        }

        #[ink(message)]
        pub fn increase_allowance(&mut self, spender: AccountId, value: Balance) -> Result<()> {
            let caller = self.env().caller();
            let allowance = self.allowance(caller, spender);
            self.allowances
                .insert((caller, spender), &(allowance + value));
            Ok(())
        }

        #[ink(message)]
        pub fn decrease_allowance(&mut self, spender: AccountId, value: Balance) -> Result<()> {
            let caller = self.env().caller();
            let allowance = self.allowance(caller, spender);
            if allowance < value {
                return Err(Error::InsufficientAllowance);
            }
            self.allowances
                .insert((caller, spender), &(allowance - value));
            Ok(())
        }

        #[ink(message)]
        pub fn burn(&mut self, value: Balance) -> Result<()> {
            let caller = self.env().caller();
            let balance = self.balance_of(caller);
            if balance < value {
                return Err(Error::InsufficientBalance);
            }
            self.balances.insert(caller, &(balance - value));
            self.total_supply -= value;

            self.env().emit_event(Transfer {
                from: Some(caller),
                to: None,
                value,
            });
            Ok(())
        }

        pub fn transfer_helper(
            &mut self,
            from: AccountId,
            to: AccountId,
            value: Balance,
        ) -> Result<()> {
            let from_balance = self.balance_of(from);
            if from_balance < value {
                return Err(Error::InsufficientBalance);
            }

            let to_balance = self.balance_of(to);

            self.balances.insert(from, &(from_balance - value));
            self.balances.insert(to, &(to_balance + value));

            self.env().emit_event(Transfer {
                from: Some(from),
                to: Some(to),
                value,
            });

            Ok(())
        }
    }

    #[cfg(test)]
    mod tests {

        use super::*;

        type Event = <Erc20 as ::ink::reflect::ContractEventBase>::Type;

        #[ink::test]
        fn constructor_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let erc20 = Erc20::new(1000);

            assert_eq!(erc20.total_supply(), 1000);
            assert_eq!(erc20.balance_of(accounts.alice), 1000);

            let emitted_events = ink::env::test::recorded_events().collect::<Vec<_>>();
            let event = emitted_events[0].clone();
            let decoded = <Event as scale::Decode>::decode(&mut &event.data[..]).unwrap();

            match decoded {
                Event::Transfer(Transfer { from, to, value }) => {
                    assert_eq!(from, None);
                    assert_eq!(to, Some(accounts.alice));
                    assert_eq!(value, 1000);
                }
                _ => panic!("wrong event"),
            }
        }

        #[ink::test]
        fn transfer_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let mut erc20 = Erc20::new(1000);

            assert_eq!(erc20.balance_of(accounts.bob), 0);
            assert_eq!(erc20.balance_of(accounts.charlie), 0);

            erc20.transfer(accounts.bob, 500).expect("transfer failed");

            assert_eq!(erc20.balance_of(accounts.alice), 500);
            assert_eq!(erc20.balance_of(accounts.bob), 500);

            let emitted_events = ink::env::test::recorded_events().collect::<Vec<_>>();
            let event = emitted_events[1].clone();
            let decoded = <Event as scale::Decode>::decode(&mut &event.data[..]).unwrap();

            match decoded {
                Event::Transfer(Transfer { from, to, value }) => {
                    assert_eq!(from, Some(accounts.alice));
                    assert_eq!(to, Some(accounts.bob));
                    assert_eq!(value, 500);
                }
                _ => panic!("wrong event"),
            }
        }

        #[ink::test]
        fn approve_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let mut erc20 = Erc20::new(1000);

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 0);

            erc20.approve(accounts.bob, 500).expect("approve failed");

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 500);

            let emitted_events = ink::env::test::recorded_events().collect::<Vec<_>>();
            let event = emitted_events[1].clone();
            let decoded = <Event as scale::Decode>::decode(&mut &event.data[..]).unwrap();

            match decoded {
                Event::Approval(Approval {
                    owner,
                    spender,
                    value,
                }) => {
                    assert_eq!(owner, accounts.alice);
                    assert_eq!(spender, accounts.bob);
                    assert_eq!(value, 500);
                }
                _ => panic!("wrong event"),
            }
        }

        #[ink::test]
        fn transfer_from_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let mut erc20 = Erc20::new(1000);

            erc20.approve(accounts.bob, 500).expect("approve failed");

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 500);

            erc20
                .transfer_from(accounts.bob, accounts.charlie, 300)
                .expect("transfer_from failed");

            assert_eq!(erc20.balance_of(accounts.alice), 700);
            assert_eq!(erc20.balance_of(accounts.charlie), 300);
            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 200);

            let emitted_events = ink::env::test::recorded_events().collect::<Vec<_>>();
            let event = emitted_events[2].clone();
            let decoded = <Event as scale::Decode>::decode(&mut &event.data[..]).unwrap();

            match decoded {
                Event::Transfer(Transfer { from, to, value }) => {
                    assert_eq!(from, Some(accounts.alice));
                    assert_eq!(to, Some(accounts.charlie));
                    assert_eq!(value, 300);
                }
                _ => panic!("wrong event"),
            }
        }

        #[ink::test]
        fn increase_allowance_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let mut erc20 = Erc20::new(1000);

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 0);

            erc20
                .increase_allowance(accounts.bob, 500)
                .expect("increase_allowance failed");

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 500);
        }

        #[ink::test]
        fn decrease_allowance_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let mut erc20 = Erc20::new(1000);

            erc20.approve(accounts.bob, 500).expect("approve failed");

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 500);

            erc20
                .decrease_allowance(accounts.bob, 200)
                .expect("decrease_allowance failed");

            assert_eq!(erc20.allowance(accounts.alice, accounts.bob), 300);
        }

        #[ink::test]
        fn burn_works() {
            let accounts = ink::env::test::default_accounts::<ink::env::DefaultEnvironment>();
            let mut erc20 = Erc20::new(1000);

            assert_eq!(erc20.balance_of(accounts.alice), 1000);
            assert_eq!(erc20.total_supply(), 1000);

            erc20.burn(300).expect("burn failed");

            assert_eq!(erc20.balance_of(accounts.alice), 700);
            assert_eq!(erc20.total_supply(), 700);

            let emitted_events = ink::env::test::recorded_events().collect::<Vec<_>>();
            let event = emitted_events[1].clone();
            let decoded = <Event as scale::Decode>::decode(&mut &event.data[..]).unwrap();

            match decoded {
                Event::Transfer(Transfer { from, to, value }) => {
                    assert_eq!(from, Some(accounts.alice));
                    assert_eq!(to, None);
                    assert_eq!(value, 300);
                }
                _ => panic!("wrong event"),
            }
        }
    }
}
