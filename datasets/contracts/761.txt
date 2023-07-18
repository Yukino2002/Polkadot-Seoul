#![cfg_attr(not(feature = "std"), no_std)]

pub use self::redeemables::Redeemables;
use ink_lang as ink;

// The ERC-1155 error types.

// pub type Result<T, E = Error> = Result<T, E>;
/// Holds a simple `i32` value that can be incremented and decremented.

#[ink::contract]
pub mod redeemables {
    use ink_storage::traits::{PackedLayout, SpreadLayout};
    use ink_prelude::collections::BTreeMap;

    #[derive(Debug, PartialEq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        /// The sender of the transaction is not the ERC1155 contract
        NotERC1155Contract,
        /// The sender of the transaction is not the owner
        NotOwner,
        /// The ERC1155 Contract has already been set
        ContractAlreadySet,
    }

    pub type Result<T> = core::result::Result<T, Error>;
    pub type TokenId = u128;
    // type Balance = <ink_env::DefaultEnvironment as ink_env::Environment>::Balance;

    #[derive(
        Debug, PartialEq, Eq, scale::Encode, scale::Decode, PackedLayout, SpreadLayout,
    )]
    #[cfg_attr(feature = "std", derive(::scale_info::TypeInfo))]
    pub struct Staking {
        pub id: TokenId,
        pub balance: Balance,
        pub staker: AccountId,
        pub setid: u32,
        pub releaseDate: u64,
        pub tickets: BTreeMap<AccountId,bool>,
        }

    #[ink(storage)]
    pub struct Redeemables {
        contract_owner: AccountId,
        erc1155_address: AccountId,
        staked_tokens: BTreeMap<(AccountId,TokenId),Staking>,
        end_date: BTreeMap<AccountId, u64>,

    }

    impl Redeemables {
        /// Initializes the value to the initial value.
        // todo: remove release date from here, serves no purpose 
        #[ink(constructor)]
        pub fn new() -> Self {
            let contract_owner = Self::env().caller();
            Self {
                contract_owner,
                erc1155_address: Default::default(),
                staked_tokens: Default::default(),
                end_date: Default::default(),
                
            }
        }

        #[ink(message)]
        pub fn get_contract_address(&mut self) -> AccountId {
            self.env().account_id()
        }

        // #[ink(message)]
        // pub fn get_staked_nft(&mut self, account_id: AccountId, token_id: TokenId) -> Option<Staking> {
        //     *self.staked_tokens.get(&(account_id,token_id))
        // }

        #[ink(message)]
        pub fn get_erc1155_address(&mut self) -> AccountId {
            self.erc1155_address
        }


        #[ink(message)]
        pub fn get_staked_nft(
            &self,
            account_id: AccountId,
            token_id: TokenId,
        ) -> (
            Option<Balance>,
            Option<u32>,
            Option<u64>,
        ) {
            let balance = self.staked_tokens.get(&(account_id,token_id)).map(|v| v.balance.clone());
            let setid = self.staked_tokens.get(&(account_id,token_id)).map(|v| v.setid.clone());
            let releaseDate = self.staked_tokens.get(&(account_id,token_id)).map(|v| v.releaseDate.clone());
            return (balance, setid, releaseDate);
        }

        #[ink(message)]
        pub fn get_release_date(&mut self, account_id: AccountId, token_id: TokenId) -> u64 {
            self.staked_tokens.get(&(account_id,token_id)).map(|v| v.releaseDate.clone()).unwrap_or(0)
        }

        #[ink(message)]
        pub fn get_balance(&mut self, account_id: AccountId, token_id: TokenId) -> Balance {
            self.staked_tokens.get(&(account_id,token_id)).map(|v| v.balance.clone()).unwrap_or(0)
        }

        #[ink(message)]
        pub fn get_end_date(&self, address: AccountId) -> u64 {
            self.end_date[&address]
        }

        #[ink(message)]
        pub fn set_end_date(&mut self, end_date: u64) -> Result<()> {
            //todo: only let smart contracts do this 
            let caller = self.env().caller();
            self.end_date.insert(caller, end_date);
            Ok(())
        }

        // todo: get the release date here and store the ticket class
        #[ink(message)]
        pub fn stake_nft(&mut self,owner:AccountId,id:TokenId,balance:Balance,setid:u32,ticket_id:AccountId,releaseDate:u64) -> Result<()> {
            if self.env().caller() != self.erc1155_address {
                return Err(Error::NotERC1155Contract);
            }
            //* Test if it actually exists
            if self.staked_tokens.contains_key(&(owner,id)) {
                if(balance>0){
                    self.staked_tokens.get_mut(&(owner,id)).unwrap().balance += balance;
                }
                // let newbalance = self.staked_tokens.get(&(owner,id)).unwrap().balance+balance;
                if releaseDate > self.staked_tokens.get(&(owner,id)).unwrap().releaseDate {
                    self.staked_tokens.get_mut(&(owner,id)).unwrap().releaseDate = releaseDate;
                }

                self.staked_tokens.get_mut(&(owner,id)).unwrap().tickets.insert(ticket_id,true);
            }else{
                let mut tickets = BTreeMap::new();
                tickets.insert(ticket_id,true);
                self.staked_tokens.insert((owner,id),Staking{
                    id,
                    balance,
                    staker: owner,
                    setid,
                    releaseDate,
                    tickets
                });
            }

            Ok(())
        }

        #[ink(message)]
        pub fn redeem_nft(&mut self,owner:AccountId,id:TokenId) -> Result<()> {
            if self.env().caller() != self.erc1155_address {
                return Err(Error::NotERC1155Contract);
            }
            self.staked_tokens.remove(&(owner,id));
            Ok(())
        }

        #[ink(message)]
        pub fn set_erc1155_contract(&mut self, address: AccountId) -> Result<()> {
            if self.env().caller() != self.contract_owner {
                return Err(Error::NotOwner);
            }
            self.erc1155_address = address;
            Ok(())
        }

        

    }
}
// #![cfg_attr(not(feature = "std"), no_std)]

// pub use self::redeemables::Redeemables;
// use ink_lang as ink;

// #[ink::contract]
// pub mod redeemables {
//     /// Holds a simple `i32` value that can be incremented and decremented.
//     #[ink(storage)]
//     pub struct redeemables {
//         value: i32,
//     }

//     impl Redeemables {
//         /// Initializes the value to the initial value.
//         #[ink(constructor)]
//         pub fn new(init_value: i32) -> Self {
//             Self { value: init_value }
//         }

//         /// Mutates the internal value.
//         #[ink(message)]
//         pub fn inc(&mut self, by: i32) {
//             self.value += by;
//         }

//         /// Returns the current state.
//         #[ink(message)]
//         pub fn get(&self) -> i32 {
//             self.value
//         }
//     }
// }
