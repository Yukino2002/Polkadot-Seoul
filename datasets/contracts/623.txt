#![cfg_attr(not(any(test, feature = "std")), no_std)]

use ink_core::{
    env::{self, AccountId, Balance},
    memory::format,
    storage,
};
use ink_lang::contract;
use parity_codec::{Decode, Encode};

/// Events deposited by the NFToken contract
#[derive(Encode, Decode)]
enum Event {
    /// Emits when the owner of the contract mints tokens
    Mint { owner: AccountId, value: u64 },
    /// Emits when a transfer has been made.
    Transfer {
        from: Option<AccountId>,
        to: Option<AccountId>,
        token_id: u64,
    },
    /// Emits when an approved address for an NFT is changed or re-affirmed.
    Approval {
        owner: AccountId,
        spender: AccountId,
        token_id: u64,
        approved: bool,
    },
}

/// Deposits an NFToken event.
fn deposit_event(event: Event) {
    env::deposit_raw_event(&event.encode()[..])
}

contract! {
    /// Storage values of the contract
    struct NFToken {
        /// Owner of contract
        owner: storage::Value<AccountId>,
        /// Total tokens minted
        total_minted: storage::Value<u64>,
        /// Mapping: token_id(u64) -> owner (AccountID)
        id_to_owner: storage::HashMap<u64, AccountId>,
        /// Mapping: owner(AccountID) -> tokenCount (u64)
        owner_to_token_count: storage::HashMap<AccountId, u64>,
        /// Mapping: token_id(u64) to account(AccountId)
        approvals: storage::HashMap<u64, AccountId>,
    }

    impl Deploy for NFToken {
        /// Initializes our state to `false` upon deploying our smart contract.
        fn deploy(&mut self, init_value: u64) {
            self.total_minted.set(0);
            self.owner.set(env.caller());
            if init_value > 0 {
                self.mint_impl(env.caller(), init_value);
            }
        }
    }

    /// Public methods
    impl NFToken {
        /// Return the total amount of tokens ever minted
        pub(external) fn total_minted(&self) -> u64 {
            let total_minted = *self.total_minted;
            total_minted
        }
    }

    /// Private Methods
    impl NFToken {

    }

}

#[cfg(all(test, feature = "test-env"))]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let mut contract = NFToken::deploy_mock();
        assert_eq!(contract.get(), false);
        contract.flip();
        assert_eq!(contract.get(), true);
    }
}
