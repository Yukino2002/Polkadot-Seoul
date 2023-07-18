#![cfg_attr(not(feature = "std"), no_std, no_main)]

#[ink::contract]
mod markets {

    use trait_erc20::{TERC20};
    use erc721::{Erc721Ref, TokenId};


    #[ink(storage)]
    pub struct Markets {
        // solidity: erc20 TERC20(address)
        acceptable_erc20: ink::contract_ref!(TERC20),
        erc721: Erc721Ref,
        price: Balance,
        minted_count: u32,
    }

    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        Erc20TransferFail,
        Erc721MintFail,
        Erc721TransferFail,
    }

    pub type Result<T> = core::result::Result<T, Error>;

    impl Markets {
        #[ink(constructor)]
        pub fn new (erc721: Erc721Ref, erc20: AccountId) -> Self {
            Self {
                acceptable_erc20: erc20.into(),
                erc721,
                price: 11,
                minted_count: 0,
            }
        }

        #[ink(message)]
        pub fn buy_nft(&mut self) -> Result<()> {
            let caller = self.env().caller();
            let res = self.acceptable_erc20.transfer_from(caller.into(), self.env().account_id().into(), self.price.into());
            if res.is_err() {
                return Err(Error::Erc20TransferFail);
            }
            
            self.minted_count += 1;
            let mint_res = self.erc721.mint(self.minted_count);
            if mint_res.is_err() {
                return Err(Error::Erc721MintFail);
            }

            let transfer_res = self.erc721.transfer(caller, self.minted_count);
            if transfer_res.is_err() {
                return Err(Error::Erc721TransferFail);
            }

            Ok(())
        }
    }
}
