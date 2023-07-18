//! Rubeus - encrypted credentials storage

#![cfg_attr(not(feature = "std"), no_std)]

#[ink::contract]
mod rubeus {
    use ink::storage::Mapping;
    use scale_info::prelude::{string::String, vec::Vec};

    #[ink(storage)]
    pub struct Rubeus {
        // A contract publisher is the smart-contract owner by default
        pub owner: AccountId,
        // Accounts with password groups
        pub credentials: Mapping<AccountId, Vec<Credential>>,
        // Accounts with notes
        pub notes: Mapping<AccountId, Vec<Note>>,
    }

    /// Credential struct
    #[derive(Debug, Default, Clone, Eq, PartialEq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct Credential {
        pub payload: String,
        pub group: String,
        pub id: String,
    }

    impl From<scale::Error> for Credential {
        fn from(_: scale::Error) -> Self {
            panic!("encountered unexpected invalid SCALE encoding")
        }
    }

    /// Note struct
    #[derive(Debug, Default, Clone, Eq, PartialEq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct Note {
        pub payload: String,
        pub id: String,
    }

    impl From<scale::Error> for Note {
        fn from(_: scale::Error) -> Self {
            panic!("encountered unexpected invalid SCALE encoding")
        }
    }

    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    /// Error types
    pub enum Error {
        /// Caller is not the owner of the contract
        AccessOwner,
        /// Credential(s) not found
        NotFound,
        /// Transfer Errors
        TransferFailed,
        // Credential must have unique id
        UniqueIdRequired,
    }

    impl Rubeus {
        /// You can set a contract owner while deploying the contract
        #[ink(constructor)]
        pub fn new(owner: AccountId) -> Self {
            Self {
                credentials: Mapping::new(),
                notes: Mapping::new(),
                owner,
            }
        }

        /// A contract publisher is the owner by default
        #[ink(constructor)]
        pub fn default() -> Self {
            Self {
                owner: Self::env().caller(),
                credentials: Mapping::new(),
                notes: Mapping::new(),
            }
        }

        /// Method for add new credential, with common payload. Note: a unique id is also required as a parameter, taking into runtime specifics.
        #[ink(message)]
        pub fn add_credential(
            &mut self,
            payload: String,
            group: String,
            id: String,
        ) -> Result<bool, Error> {
            let caller = Self::env().caller();

            let credential = Credential {
                payload,
                group,
                id: id.clone(),
            };

            let mut credentials = self.credentials.get(caller).unwrap_or_default();
            let not_exist = !credentials.iter().any(|c| c.id == id);

            not_exist
                .then(|| {
                    credentials.push(credential);
                    self.credentials.insert(caller, &credentials);
                    true
                })
                .ok_or(Error::UniqueIdRequired)
        }

        /// Method for update for credential, you can update the payload or the group, or both.  
        #[ink(message)]
        pub fn update_credential(
            &mut self,
            id: String,
            payload: Option<String>,
            group: Option<String>,
        ) -> Result<bool, Error> {
            let caller = Self::env().caller();

            if !self.credentials.contains(Self::env().caller()) {
                Err(Error::NotFound)
            } else {
                let mut credentials = self.credentials.get(caller).ok_or(Error::NotFound)?;

                let index = credentials
                    .iter()
                    .position(|c| c.id == id)
                    .ok_or(Error::NotFound)?;

                let credential = credentials.get_mut(index).ok_or(Error::NotFound)?;

                if let Some(_payload) = payload {
                    credential.payload = _payload;
                }

                if let Some(_group) = group {
                    credential.group = _group;
                }

                self.credentials.insert(caller, &credentials);
                Ok(true)
            }
        }

        /// Method for delete saved credential by id
        #[ink(message)]
        pub fn delete_credential(&mut self, id: String) -> Result<bool, Error> {
            let caller = Self::env().caller();

            if !self.credentials.contains(Self::env().caller()) {
                Err(Error::NotFound)
            } else {
                let mut credentials = self.credentials.get(caller).ok_or(Error::NotFound)?;

                let index = credentials
                    .iter()
                    .position(|c| c.id == id)
                    .ok_or(Error::NotFound)?;

                credentials.remove(index);

                self.credentials.insert(caller, &credentials);
                Ok(true)
            }
        }

        /// List of all saved credentials by caller
        #[ink(message)]
        pub fn get_credentials(&self) -> Vec<Credential> {
            self.credentials.get(Self::env().caller()).unwrap_or_default()
        }

        /// List of all saved credentials by group and caller
        #[ink(message)]
        pub fn get_credentials_by_group(&self, group: String) -> Vec<Credential> {
            let credentials = self.credentials.get(Self::env().caller()).unwrap_or_default();

            credentials
                .into_iter()
                .filter(|credential| credential.group.contains(&*group))
                .collect::<Vec<Credential>>()
        }

        /// Method for add new note, with common payload. Note: a unique id is also required as a parameter, taking into runtime specifics.
        #[ink(message)]
        pub fn add_note(
            &mut self,
            payload: String,
            id: String,
        ) -> Result<bool, Error> {
            let caller = Self::env().caller();

            let note = Note {
                id: id.clone(),
                payload,
            };

            let mut notes = self.notes.get(caller).unwrap_or_default();
            let not_exist = !notes.iter().any(|c| c.id == id);

            not_exist
                .then(|| {
                    notes.push(note);
                    self.notes.insert(caller, &notes);
                    true
                })
                .ok_or(Error::UniqueIdRequired)
        }

        /// Method for update for note, you can update the payload or the group, or both.  
        #[ink(message)]
        pub fn update_note(
            &mut self,
            id: String,
            payload: Option<String>,
        ) -> Result<bool, Error> {
            let caller = Self::env().caller();

            if !self.notes.contains(Self::env().caller()) {
                Err(Error::NotFound)
            } else {
                let mut notes = self.notes.get(caller).ok_or(Error::NotFound)?;

                let index = notes
                    .iter()
                    .position(|c| c.id == id)
                    .ok_or(Error::NotFound)?;

                let note = notes.get_mut(index).ok_or(Error::NotFound)?;

                if let Some(_payload) = payload {
                    note.payload = _payload;
                }

                self.notes.insert(caller, &notes);
                Ok(true)
            }
        }

        /// Method for delete saved note by id
        #[ink(message)]
        pub fn delete_note(&mut self, id: String) -> Result<bool, Error> {
            let caller = Self::env().caller();

            if !self.notes.contains(Self::env().caller()) {
                Err(Error::NotFound)
            } else {
                let mut notes = self.notes.get(caller).ok_or(Error::NotFound)?;

                let index = notes
                    .iter()
                    .position(|c| c.id == id)
                    .ok_or(Error::NotFound)?;

                notes.remove(index);

                self.notes.insert(caller, &notes);
                Ok(true)
            }
        }

        /// List of all saved notes by caller
        #[ink(message)]
        pub fn get_notes(&self) -> Vec<Note> {
            self.notes.get(Self::env().caller()).unwrap_or_default()
        }

        /// Transfer contract ownership to another user
        #[ink(message)]
        pub fn transfer_ownership(&mut self, account: AccountId) -> Result<bool, Error> {
            (Self::env().caller() == self.owner)
                .then(|| {
                    self.owner = account;
                    true
                })
                .ok_or(Error::AccessOwner)
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[ink::test]
        fn create_credential() {
            let accounts = default_accounts();

            // setup contract
            let mut contract = create_contract(1000);

            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);

            let credential = Credential {
                group: "group".into(),
                payload: "payload".into(),
                id: "1".into(),
            };

            // add new credential
            assert_eq!(
                contract.add_credential(
                    credential.payload.clone(),
                    credential.group.clone(),
                    credential.id.clone()
                ),
                Ok(true)
            );

            // error checking - you can add only with unique id
            assert_eq!(
                contract.add_credential(
                    credential.payload.clone(),
                    credential.group.clone(),
                    credential.id.clone()
                ),
                Err(Error::UniqueIdRequired)
            );

            // check for success adding credential
            assert_eq!(contract.get_credentials()[0], credential);
        }

        #[ink::test]
        fn update_credential() {
            let accounts = default_accounts();

            // setup contract
            let mut contract = create_contract(1000);

            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);

            contract
                .add_credential("payload".to_string(), "group".to_string(), "1".to_string())
                .unwrap();

            // params to update credential & compares later
            let credential = Credential {
                payload: "another_payload".into(),
                group: "another_group".into(),
                id: "1".into(),
            };

            // update existing credential
            assert_eq!(
                contract.update_credential(
                    credential.id.clone(),
                    Some(credential.payload.clone()),
                    Some(credential.group.clone()),
                ),
                Ok(true)
            );

            // error checking - you can update only for existing id
            assert_eq!(
                contract.update_credential(
                    "non_existent_id".into(),
                    Some(credential.payload.clone()),
                    Some(credential.group.clone()),
                ),
                Err(Error::NotFound)
            );

            // check for success updating credential
            assert_eq!(contract.get_credentials()[0], credential);
        }

        #[ink::test]
        fn delete_credential() {
            let accounts = default_accounts();

            // setup contract
            let mut contract = create_contract(1000);

            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);

            contract
                .add_credential("payload".to_string(), "group".to_string(), "1".to_string())
                .unwrap();

            // error checking - trying to delete non-existing credential
            assert_eq!(
                contract.delete_credential("100".into()),
                Err(Error::NotFound)
            );

            // delete existing credential
            assert_eq!(contract.delete_credential("1".into()), Ok(true));
            // check for success deleting credential
            assert_eq!(contract.credentials.get(accounts.alice).unwrap(), vec![]);
        }

        #[ink::test]
        fn list_of_credentials() {
            let accounts = default_accounts();

            // setup contract
            let mut contract = create_contract(1000);

            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);

            let first_credential = Credential {
                payload: "first_payload".into(),
                group: "first_group".into(),
                id: "1".into(),
            };

            let second_credential = Credential {
                payload: "second_payload".into(),
                group: "second_group".into(),
                id: "2".into(),
            };

            contract
                .add_credential(
                    first_credential.payload.clone(),
                    first_credential.group.clone(),
                    first_credential.id.clone(),
                )
                .unwrap();

            contract
                .add_credential(
                    second_credential.payload.clone(),
                    second_credential.group.clone(),
                    second_credential.id.clone(),
                )
                .unwrap();

            let all_credentials = contract.get_credentials();
            // check list by size
            assert_eq!(all_credentials.len(), 2);
            // compare for existing
            assert_eq!(all_credentials, vec![first_credential.clone(), second_credential.clone()]);

            let credentials_by_first_group = contract.get_credentials_by_group(first_credential.group.clone());
            // check list by size
            assert_eq!(credentials_by_first_group.len(), 1);
            // compare for existing
            assert_eq!(credentials_by_first_group, vec![first_credential.clone()]);

            let credentials_by_second_group = contract.get_credentials_by_group(second_credential.group.clone());
            // check list by size
            assert_eq!(credentials_by_second_group.len(), 1);
            // compare for existing
            assert_eq!(credentials_by_second_group, vec![second_credential.clone()]);
        }

        #[ink::test]
        fn create_note() {
            let accounts = default_accounts();
        
            // setup contract
            let mut contract = create_contract(1000);
        
            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);
        
            let note = Note {
                payload: "payload".into(),
                id: "1".into(),
            };
        
            // add new note
            assert_eq!(
                contract.add_note(
                    note.payload.clone(),
                    note.id.clone()
                ),
                Ok(true)
            );
        
            // error checking - you can add only with unique id
            assert_eq!(
                contract.add_note(
                    note.payload.clone(),
                    note.id.clone()
                ),
                Err(Error::UniqueIdRequired)
            );
        
            // check for success adding note
            assert_eq!(contract.get_notes()[0], note);
        }
        
        #[ink::test]
        fn update_note() {
            let accounts = default_accounts();
        
            // setup contract
            let mut contract = create_contract(1000);
        
            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);
        
            contract
                .add_note("payload".to_string(), "1".to_string())
                .unwrap();
        
            // params to update note & compares later
            let note = Note {
                payload: "another_payload".into(),
                id: "1".into(),
            };
        
            // update existing note
            assert_eq!(
                contract.update_note(
                    note.id.clone(),
                    Some(note.payload.clone()),
                ),
                Ok(true)
            );
        
            // error checking - you can update only for existing id
            assert_eq!(
                contract.update_note(
                    "non_existent_id".into(),
                    Some(note.payload.clone()),
                ),
                Err(Error::NotFound)
            );
        
            // check for success updating note
            assert_eq!(contract.get_notes()[0], note);
        }
        
        #[ink::test]
        fn delete_note() {
            let accounts = default_accounts();
        
            // setup contract
            let mut contract = create_contract(1000);
        
            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);
        
            contract
                .add_note("payload".to_string(), "1".to_string())
                .unwrap();
        
            // error checking - trying to delete non-existing note
            assert_eq!(
                contract.delete_note("100".into()),
                Err(Error::NotFound)
            );
        
            // delete existing note
            assert_eq!(contract.delete_note("1".into()), Ok(true));
            // check for success deleting note
            assert_eq!(contract.notes.get(accounts.alice).unwrap(), vec![]);
        }
        
        #[ink::test]
        fn list_of_notes() {
            let accounts = default_accounts();
        
            // setup contract
            let mut contract = create_contract(1000);
        
            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);
        
            let first_note = Note {
                payload: "first_payload".into(),
                id: "1".into(),
            };
        
            let second_note = Note {
                payload: "second_payload".into(),
                id: "2".into(),
            };
        
            contract
                .add_note(
                    first_note.payload.clone(),
                    first_note.id.clone(),
                )
                .unwrap();
        
            contract
                .add_note(
                    second_note.payload.clone(),
                    second_note.id.clone(),
                )
                .unwrap();
        
            let all_notes = contract.get_notes();
            // check list by size
            assert_eq!(all_notes.len(), 2);
            // compare for existing
            assert_eq!(all_notes, vec![first_note.clone(), second_note.clone()]);
        }

        #[ink::test]
        fn transfer_ownership() {
            let accounts = default_accounts();

            // setup contract
            let mut contract = create_contract(1000);

            set_sender(accounts.alice);
            assert_eq!(contract.owner, accounts.alice);

            // transfer ownership to bob
            assert_eq!(contract.transfer_ownership(accounts.bob), Ok(true));
            // check for new owner of the contract
            assert_eq!(contract.owner, accounts.bob);
        }

        fn create_contract(initial_balance: Balance) -> Rubeus {
            let accounts = default_accounts();

            set_sender(accounts.alice);
            set_balance(contract_id(), initial_balance);

            // Alice is the publisher and owner by default
            Rubeus::default()
        }

        fn contract_id() -> AccountId {
            ink::env::test::callee::<ink::env::DefaultEnvironment>()
        }

        fn set_sender(sender: AccountId) {
            ink::env::test::set_caller::<ink::env::DefaultEnvironment>(sender);
        }

        fn default_accounts() -> ink::env::test::DefaultAccounts<ink::env::DefaultEnvironment> {
            ink::env::test::default_accounts::<ink::env::DefaultEnvironment>()
        }

        fn set_balance(account_id: AccountId, balance: Balance) {
            ink::env::test::set_account_balance::<ink::env::DefaultEnvironment>(account_id, balance)
        }
    }
}
