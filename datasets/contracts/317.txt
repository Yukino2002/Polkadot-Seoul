// implementation ERC721 according to https://eips.ethereum.org/EIPS/eip-721
// #![cfg_attr(not(any(test, feature = "test-env")), no_std)]
#![feature(proc_macro_hygiene)]
#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract(version = "0.1.0", env = DefaultXrmlTypes)]
mod erc721 {
    use ink_core::{
        env::{
            DefaultXrmlTypes
        },
        storage,
    };

    /// Event emitted when a token transfer occurs
    #[ink(event)]
    struct Transfer {
        from: Option<AccountId>,
        to: AccountId,
        id: Hash,
    }

    /// Event emited when a token approve occurs
    #[ink(event)]
    struct Approval {
        from: AccountId,
        to: AccountId,
        id: Hash,
    }

    /// Event emitted when an operator is enabled or disabled for an owner.
    /// The operator can manage all NFTs of the owner.
    #[ink(event)]
    struct ApprovalForAll {
        owner: AccountId,
        operator: AccountId,
        approved: bool
    }


    #[ink(storage)]
    struct Erc721 {
        /// Mapping from token to owner.
        token_owner: storage::HashMap<Hash, AccountId>,
        /// Mapping from token to approvals users.
        token_approvals: storage::HashMap<Hash, AccountId>,
        /// Mapping from owner to number of owned token.
        owned_tokens_count: storage::HashMap<AccountId, u128>,
        /// Mapping from owner to operator approvals
        operator_approvals: storage::HashMap<AccountId, storage::HashMap<AccountId, bool>>,
        default_account: storage::Value<AccountId>,
    }

    impl Erc721 {

        #[ink(constructor)]
        fn new(&mut self) {
            self.default_account.set(AccountId::from([0x0; 32]));
        }

        #[ink(message)]
        fn mint(&mut self, id: Hash) -> bool {
            let caller = self.env().caller();
            let owner = self.owner_of_or_none(&id);
            if owner != *self.default_account {
                env.println(&format!("Erc721::mint::token is exist"));
                return false;
            }
            self.token_owner.insert(id, caller);
            let balance = self.balance_of_or_zero(&caller);
            self.owned_tokens_count.insert(caller, balance + 1);
            self.env.emit_event(Transfer {
                from: None,
                to: caller,
                id: id,
            });
            true
        }

        /// Get token balance of specific account.
        #[ink(message)]
        fn balance_of(&self, owner: AccountId) -> Balance {
            let balance = self.balance_of_or_zero(&owner);
            self.env().println(&format!("Erc721::balance_of(owner = {:?}) = {:?}", owner, balance));
            balance
        }

        /// Get owner for specific token.
        #[ink(message)]
        fn owner_of(&self, id: Hash) -> AccountId {
            let owner = self.owner_of_or_none(&id);
            self.env().println(&format!("Erc721::owner_of(token = {:?}) = {:?}", id, owner));
            owner
        }

        /// The approved address for this token, or the none address if there is none
        #[ink(message)]
        fn get_approved(&self, id: Hash) -> AccountId {
            let account = self.approved_of_or_none(&id);
            account
        }

        #[ink(message)]
        fn set_approval_for_all(&mut self, to: AccountId, approved: bool) -> bool {
            let caller = self.env().caller();
            let hashmap = self.operator_approvals.get_mut(&caller);
            match hashmap {
                Some(hashmap) => {
                    hashmap.insert(to, approved);
                },
                None => {
                    unsafe {
                        use ink_core::storage::alloc::AllocateUsing;
                        use ink_core::storage::alloc::Initialize;
                        let mut default_hashmap: storage::HashMap<AccountId, bool> = storage::HashMap::allocate_using(&mut env.dyn_alloc).initialize_into(());
                        default_hashmap.insert(to, approved);
                        self.operator_approvals.insert(caller, default_hashmap);
                    }
                },
           }
           self.env().emit_event(ApprovalForAll {
                owner: caller,
                operator: to,
                approved: approved,
            });
            true
        }

        #[ink(message)]
        fn is_approved_for_all(&self, owner: AccountId, operator: AccountId) -> bool {
            self.is_approved_for_all_impl(owner, operator)
        }

        #[ink(message)]
        fn transfer_from(&mut self, from: AccountId, to: AccountId, id: Hash) -> bool {
            let owner = self.owner_of_or_none(&id);
            env.println(&format!("Erc721::transfer_from::(owner={:?}, from={:?}, to={:?}", owner, from , to));
            if owner == *self.default_account {
                self.env().println(&format!("Erc721::transfer_from::owner is None"));
                return false;
            }
            if owner != from {
                self.env().println(&format!("Erc721::transfer_from::from is not owner"));
                return false;
            }
            if to == *self.default_account {
                self.env().println(&format!("Erc721::transfer_from::spender is None"));
                return false;
            }
            if self.is_approved_or_owner(env.caller(), id) {
                return self.transfer_from_impl(&from, &to, &id);
            }
            false
        }

        /// Approve another account to operate the given token
        #[ink(message)]
        fn approve(&mut self, to: AccountId, id: Hash) -> bool {
            let caller = self.env().caller();
            let owner = self.owner_of_or_none(&id);
            if caller != owner {
                env.println(&format!("Erc721::approve::caller is not owner"));
                return false;
            }
            if owner == to {
                self.env().println(&format!("Erc721::approve::approve to current owner"));
                return false;
            }
            self.token_approvals.insert(id, to);
            self.env().emit(Approval {
                from: owner,
                to: to,
                id: id,
            });
            true
        }

         /// Returns the balance of the AccountId or 0 if there is no balance.
        fn balance_of_or_zero(&self, of: &AccountId) -> u128 {
            *self.owned_tokens_count.get(of).unwrap_or(&0)
        }

        fn owner_of_or_none(&self, id: &Hash) -> AccountId {
            let owner = self.token_owner.get(id).unwrap_or(&self.default_account);
            *owner
        }

        fn approved_of_or_none(&self, id: &Hash) -> AccountId {
            let owner = self.token_approvals.get(id).unwrap_or(&self.default_account);
            *owner
        }

        fn is_approved_or_owner(&self, spender: AccountId, id: Hash) -> bool {
            let owner = self.owner_of_or_none(&id);
            if owner == spender {
                // env.println(&format!("Erc721::is_approved_or_owner::spender is owner"));
                return true;
            }
            if spender == self.approved_of_or_none(&id) {
                // env.println(&format!("Erc721::is_approved_or_owner::spender is not approved"));
                return true;
            }
            if self.is_approved_for_all_impl(owner, spender) {
                // env.println(&format!("Erc721::is_approved_or_owner::spender is not approved for all"));
                return true;
            }
            false
        }

        fn is_approved_for_all_impl(&self, owner: AccountId, operator: AccountId) -> bool {
            let hashmap = self.operator_approvals.get(&owner);
            match hashmap {
                Some(hashmap) => return *hashmap.get(&operator).unwrap_or(&false),
                None => return false
            }
        }

        fn transfer_from_impl(&mut self, from: &AccountId, to: &AccountId, id: &Hash) -> bool {

            self.clear_approval(id);

            let from_balance = self.balance_of_or_zero(from);
            let to_balance = self.balance_of_or_zero(to);

            self.owned_tokens_count.insert(*from, from_balance - 1);
            self.owned_tokens_count.insert(*to, to_balance + 1);
            self.token_owner.insert(*id, *to);

            true
        }

        fn clear_approval(&mut self, id: &Hash) {
            if *self.default_account != self.approved_of_or_none(&id) {
                self.token_approvals.insert(*id, *self.default_account);
            }
        }
    }

    #[cfg(all(test, feature = "test-env"))]
    mod tests {
        use super::*;
        use ink_core::env;
        type Types = ink_core::env::DefaultSrmlTypes;

        #[test]
        fn deployment_works() {
            let alice = AccountId::from([0x01; 32]);
            let bob = AccountId::from([0x02; 32]);
            let carol = AccountId::from([0x03; 32]);
            let default_account = AccountId::from([0x0; 32]);
            let token1 = Hash::from([0x11; 32]);
            let token2 = Hash::from([0x12; 32]);

            env::test::set_caller::<Types>(alice);

            // Test initial state
            let mut contract = Erc721::deploy_mock();
            assert_eq!(contract.balance_of(alice), 0);
            assert_eq!(contract.owner_of(token1), default_account);

            // Test mint function
            assert_eq!(contract.mint(token1), true);
            assert_eq!(contract.balance_of(alice), 1);
            assert_eq!(contract.mint(token2), true);
            assert_eq!(contract.balance_of(alice), 2);
            assert_eq!(contract.owner_of(token1), alice);
            assert_eq!(contract.mint(token1), false);

            // Test get_approved
            assert_eq!(contract.get_approved(token1), default_account);

            // Test approve
            assert_eq!(contract.approve(bob, token1), true);
            assert_eq!(contract.get_approved(token1), bob);

            // Test transfer_from
            assert_eq!(contract.owner_of(token1), alice);
            assert_eq!(contract.owner_of(token2), alice);
            assert_eq!(contract.transfer_from(alice, bob, token1), true);
            assert_eq!(contract.owner_of(token1), bob);

            // Test set_approval_for_all
            assert_eq!(contract.is_approved_for_all(alice, bob), false);
            assert_eq!(contract.set_approval_for_all(bob, true), true);
            assert_eq!(contract.is_approved_for_all(alice, bob), true);

            assert_eq!(contract.transfer_from(bob, carol, token2), false);
            assert_eq!(contract.owner_of(token2), alice);
            assert_eq!(contract.transfer_from(alice, carol, token2), true);
            assert_eq!(contract.balance_of(alice), 0);
            assert_eq!(contract.balance_of(bob), 1);
            assert_eq!(contract.balance_of(carol), 1);
            assert_eq!(contract.owner_of(token2), carol);

            assert_eq!(contract.set_approval_for_all(bob, false), true);
            assert_eq!(contract.is_approved_for_all(alice, bob), false);
        }
    }
}
