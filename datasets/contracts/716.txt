#![cfg_attr(not(feature = "std"), no_std)]

#[ink::contract]
mod voting {
    use ink::prelude::{
        string::String,
        vec::Vec,
    };
    
    #[ink(storage)]
    pub struct Voting {

        proposal: Vec<Proposal>,
        max_proposals: u32,
        registered_voters: Vec<AccountId>,
        max_votes: u32,
    }
    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode, Clone)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct Vote {
        voter: AccountId,
        vote: bool,
        proposal_id: u32,
        token_id: u32,
        // todo:  add token id for nft checking
    }

    #[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode, Clone)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub struct Proposal {
        proposer: AccountId,
        name: String,
        description: String,
        accepted: bool,
        votes: Vec<Vote>,
        base_uri: String,
    }

    impl Voting {
        /// Constructor that initializes the `bool` value to the given `init_value`.
        #[ink(constructor)]
        pub fn new(proposal: Proposal) -> Self {
            let mut proposal_vec = Vec::new();
            proposal_vec.push(proposal);
            let registered_voters = Vec::new();
            Self {
                proposal: proposal_vec,
                max_proposals: 10,
                max_votes: 3,
                registered_voters,
            }
        }
        /// submit a proposal
        #[ink(message)]
        pub fn add_proposal(&mut self, proposal: Proposal) {
            self.proposal.push(proposal);
        }
        /// votes for a proposal
        #[ink(message)]
        pub fn vote(&mut self, vote: Vote) {
            // check if voter is registered
            if self.registered_voters.iter().any(|i| *i == vote.voter) {
                let proposal = self.proposal.get_mut(vote.proposal_id as usize).unwrap();

                // I suspect the proposal_id might be stored as a hash instead of a uint
                proposal.votes.push(vote);
            }
        }
        /// registers a voter
        #[ink(message)]
        pub fn register_voter(&mut self, voter: AccountId) {
            self.registered_voters.push(voter);
        }

        /// checks the proposal if it has been accepted
        #[ink(message)]
        pub fn check_proposal(&mut self, proposal_id: u32) -> bool {
            let proposal = self.proposal.get_mut(proposal_id as usize).unwrap();

            //  check if the proposal isn't accepted and the max threshold hasn't been reached
            if proposal.accepted != true {
                let mut yes_votes = 0;
                let mut no_votes = 0;
                for vote in proposal.votes.iter() {
                    if yes_votes + no_votes < self.max_votes {
                        if vote.vote {
                            yes_votes += 1;
                        } else {
                            no_votes += 1;
                        }
                    }
                }
                if yes_votes > no_votes {
                    proposal.accepted = true;
                }
            }

            // println!("wtf {:?}", proposal.accepted);
            proposal.accepted
        }

        /// Simply returns the current value of our `bool`.
        #[ink(message)]
        pub fn get(&self) -> Vec<Proposal> {
            self.proposal.clone()
        }

        #[ink(message)]
        pub fn get_registered_voters(&self) -> Vec<AccountId> {
            self.registered_voters.clone()
        }
    }

    /// Unit tests in Rust are normally defined within such a `#[cfg(test)]`
    /// module and test functions are marked with a `#[test]` attribute.
    /// The below code is technically just normal Rust code.
    #[cfg(test)]
    mod tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        /// We test if the default constructor does its job.
        #[ink::test]
        fn default_works() {
            let new_proposal = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test"),
                description: String::from("test"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };
            let voting = Voting::new(new_proposal);
            println!("voting: {:?}", voting);
            // assert_eq!(voting.get(), false);
        }

        /// tests for proposal creation successful
        #[ink::test]
        fn create_proposal_works() {
            let new_proposal_one = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test"),
                description: String::from("test"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };
            let mut voting = Voting::new(new_proposal_one.clone());
            let new_proposal_two = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test2"),
                description: String::from("test2"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };
            voting.add_proposal(new_proposal_two.clone());
            assert_eq!(voting.get(), vec![new_proposal_one, new_proposal_two]);
        }

        /// This checks if the voting works
        #[ink::test]
        fn vote_works() {
            // First proposal
            let new_proposal_one = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test"),
                description: String::from("test"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };
            let mut voting = Voting::new(new_proposal_one.clone());

            // Second proposal
            let mut new_proposal_two = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test2"),
                description: String::from("test2"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };
            // vote for second proposal
            voting.add_proposal(new_proposal_two.clone());
            let vote = Vote {
                voter: AccountId::from([0x1; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };

            // voting.vote(vote.clone());

            //  push votes
            new_proposal_two.votes.push(vote.clone());
            voting.vote(vote.clone());
            println!("voting: {:?}", new_proposal_two.votes.get(0));
            assert_eq!(new_proposal_two.votes.get(0), Some(&vote));
            // println!("voting: {:?}", voting.get());
            // assert_eq!(proposal_two.get_votes(), vec![vote]);
        }

        #[ink::test]
        fn check_invalid_voter_cant_vote() {}

        #[ink::test]
        fn check_register_voter_works() {}
        /// this checks for the results after the threshold has been met
        #[ink::test]
        fn check_proposal_works() {
            let new_proposal_one = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test"),
                description: String::from("test"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };
            let mut voting = Voting::new(new_proposal_one.clone());
            let new_proposal_two = Proposal {
                proposer: AccountId::from([0x1; 32]),
                name: String::from("test2"),
                description: String::from("test2"),
                accepted: false,
                votes: Vec::new(),
                base_uri: String::from("test"),
            };

            voting.add_proposal(new_proposal_two.clone());

            let vote_1 = Vote {
                voter: AccountId::from([0x1; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };

            voting.register_voter(vote_1.clone().voter);

            let vote_2 = Vote {
                voter: AccountId::from([0x2; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_2.clone().voter);
            let vote_3 = Vote {
                voter: AccountId::from([0x3; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_3.clone().voter);

            let vote_4 = Vote {
                voter: AccountId::from([0x4; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_4.clone().voter);

            let vote_5 = Vote {
                voter: AccountId::from([0x5; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_5.clone().voter);

            let vote_6 = Vote {
                voter: AccountId::from([0x6; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_6.clone().voter);

            let vote_7 = Vote {
                voter: AccountId::from([0x7; 32]),
                vote: true,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_7.clone().voter);

            let vote_8 = Vote {
                voter: AccountId::from([0x8; 32]),
                vote: false,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_8.clone().voter);

            let vote_9 = Vote {
                voter: AccountId::from([0x9; 32]),
                vote: false,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_9.clone().voter);

            let vote_10 = Vote {
                voter: AccountId::from([0x10; 32]),
                vote: false,
                proposal_id: 1,
                token_id: 1,
            };
            voting.register_voter(vote_10.clone().voter);

            voting.vote(vote_1.clone());
            voting.vote(vote_2);
            voting.vote(vote_3);
            voting.vote(vote_4);
            voting.vote(vote_5);
            voting.vote(vote_6);
            voting.vote(vote_7);
            voting.vote(vote_8);
            voting.vote(vote_9);
            voting.vote(vote_10);

            // println!("voting: {:?}", voting.check_proposal(1));
            voting.check_proposal(1);
            // println!("wtf 2 {:?}", voting);

            assert_eq!(voting.check_proposal(1), true);
        }
    }

    /// This is how you'd write end-to-end (E2E) or integration tests for ink! contracts.
    ///
    /// When running these you need to make sure that you:
    /// - Compile the tests with the `e2e-tests` feature flag enabled (`--features e2e-tests`)
    /// - Are running a Substrate node which contains `pallet-contracts` in the background
    #[cfg(all(test, feature = "e2e-tests"))]
    mod e2e_tests {
        /// Imports all the definitions from the outer scope so we can use them here.
        use super::*;

        /// A helper function used for calling contract messages.
        use ink_e2e::build_message;

        /// The End-to-End test `Result` type.
        type E2EResult<T> = std::result::Result<T, Box<dyn std::error::Error>>;

        /// We test that we can upload and instantiate the contract using its default constructor.
        #[ink_e2e::test]
        async fn default_works(mut client: ink_e2e::Client<C, E>) -> E2EResult<()> {
            // Given
            let constructor = VotingRef::default();

            // When
            let contract_account_id = client
                .instantiate("voting", &ink_e2e::alice(), constructor, 0, None)
                .await
                .expect("instantiate failed")
                .account_id;

            // Then
            let get =
                build_message::<VotingRef>(contract_account_id.clone()).call(|voting| voting.get());
            let get_result = client.call_dry_run(&ink_e2e::alice(), &get, 0, None).await;
            assert!(matches!(get_result.return_value(), false));

            Ok(())
        }

        /// We test that we can read and write a value from the on-chain contract contract.
        #[ink_e2e::test]
        async fn it_works(mut client: ink_e2e::Client<C, E>) -> E2EResult<()> {
            // Given
            let constructor = VotingRef::new(false);
            let contract_account_id = client
                .instantiate("voting", &ink_e2e::bob(), constructor, 0, None)
                .await
                .expect("instantiate failed")
                .account_id;

            let get =
                build_message::<VotingRef>(contract_account_id.clone()).call(|voting| voting.get());
            let get_result = client.call_dry_run(&ink_e2e::bob(), &get, 0, None).await;
            assert!(matches!(get_result.return_value(), false));

            // When
            let flip = build_message::<VotingRef>(contract_account_id.clone())
                .call(|voting| voting.flip());
            let _flip_result = client
                .call(&ink_e2e::bob(), flip, 0, None)
                .await
                .expect("flip failed");

            // Then
            let get =
                build_message::<VotingRef>(contract_account_id.clone()).call(|voting| voting.get());
            let get_result = client.call_dry_run(&ink_e2e::bob(), &get, 0, None).await;
            assert!(matches!(get_result.return_value(), true));

            Ok(())
        }
    }
}
