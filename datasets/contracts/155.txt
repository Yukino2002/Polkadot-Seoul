#![cfg_attr(not(feature = "std"), no_std)]
use ink_lang as ink;
#[ink::contract]
mod erc20 {
    use ink_storage::traits::SpreadAllocate;
    use ink_storage::Mapping;

    #[ink(storage)]
    #[derive(SpreadAllocate)]
    pub struct MyContract {
        balances: Mapping<AccountId, u128>,
        allowances: Mapping<(AccountId, AccountId), u128>,
        total_supply: u128,
        decimal: u8,
        owner: AccountId,
    }

    #[ink(event)]
    pub struct Transfer {
        from: AccountId,
        to: AccountId,
        value: Balance,
    }

    #[ink(event)]
    pub struct TransferFrom {
        from: AccountId,
        to: AccountId,
        amount: Balance,
    }

    #[ink(event)]
    pub struct Approval {
        caller: AccountId,
        spender: AccountId,
        value: u128,
    }

    #[ink(event)]
    pub struct DepoisetAllow {
        caller: AccountId,
        take_from: AccountId,
    }

    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        InsufficientBalance,
        InsufficientAllowance,
    }
    pub type Result<T> = core::result::Result<T, Error>;
    impl MyContract {
        #[ink(constructor)]
        pub fn new(total_supply: u128, decimal: u8) -> Self {
            ink_lang::utils::initialize_contract(|contract: &mut Self| {
                let caller = Self::env().caller();
                contract.balances.insert(&caller, &total_supply);
                contract.total_supply = total_supply;
                contract.owner = contract.env().caller();
                contract.decimal = decimal;
            })
        }

        #[ink(message)]
        pub fn total_supply(&mut self) -> u128 {
            self.total_supply
        }

        #[ink(message)]
        pub fn owner(&mut self) -> AccountId {
            self.owner
        }

        #[ink(message)]
        pub fn decimal(&mut self) -> u8 {
            self.decimal
        }

        #[ink(message)]
        pub fn balance_of(&mut self, address: AccountId) -> u128 {
            self.balances.get(&address).unwrap()
        }

        #[ink(message)]
        pub fn tranfer(&mut self, to: AccountId, amount: u128) -> Result<()> {
            let caller = self.env().caller();
            let caller_amount = self.balances.get(&caller).unwrap();
            let receiver = self.balances.get(&to).unwrap();
            assert!(amount <= caller_amount, "ander price");
            self.balances.insert(&caller, &(caller_amount - amount));
            self.balances.insert(&to, &(receiver + amount));
            self.env().emit_event(Transfer {
                from: caller,
                to,
                value: amount,
            });
            Ok(())
        }

        #[ink(message)]
        pub fn tranfer_from(&mut self, from: AccountId, to: AccountId, amount: u128) -> Result<()> {
            let caller = self.env().caller();
            let sender_amount = self.balances.get(&from).unwrap();
            let receiver = self.balances.get(&to).unwrap();
            let allow_amount = self.allowances.get(&(from, caller)).unwrap();

            assert!(
                amount <= allow_amount && amount <= sender_amount,
                "ander price"
            );
            self.allowances
                .insert(&(from, caller), &(allow_amount - amount));
            self.balances.insert(&from, &(sender_amount - amount));
            self.balances.insert(&to, &(receiver + amount));
            self.env().emit_event(TransferFrom { from, to, amount });
            Ok(())
        }

        #[ink(message)]
        pub fn approve(&mut self, spender: AccountId, value: u128) -> Result<()> {
            let caller = self.env().caller();
            let sender_amount = self.balances.get(&caller).unwrap();
            assert!(value <= sender_amount, "ander price");
            self.allowances.insert((&caller, &spender), &value);
            self.env().emit_event(Approval {
                caller,
                spender,
                value,
            });
            Ok(())
        }

        #[ink(message)]
        pub fn get_allow(&mut self, sender: AccountId, spender: AccountId) -> u128 {
            self.allowances.get((sender, spender)).unwrap()
        }

        #[ink(message)]
        pub fn depoiset_allow(&mut self, take_from: AccountId) -> Result<()> {
            let caller = self.env().caller();
            let is_true = self.allowances.contains(&(caller, take_from));
            assert!(is_true, "allownance not find");
            self.allowances.remove(&(caller, take_from));
            self.env().emit_event(DepoisetAllow { caller, take_from });
            Ok(())
        }
    }
}
