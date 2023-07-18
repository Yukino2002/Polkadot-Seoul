#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
pub mod governor {
    use ink_storage::{
        traits::*,
        Mapping,
    };
    use ink_prelude::string::String;
    use openbrush::contracts::traits::psp22::*;
    use scale::{
        Decode,
        Encode,
    };

    pub const ONE_MINUTE: u64 = 60 * 1000;

    #[derive(Encode, Decode)]
    #[cfg_attr(feature = "std", derive(Debug, PartialEq, Eq, scale_info::TypeInfo))]
    pub enum VoteType {
        Against,
        For,
    }

    #[derive(Copy, Clone, Debug, PartialEq, Eq, Encode, Decode)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum GovernorError {
        AmountShouldNotBeZero,
        DurationError,
        ProposalNotFound,
        ProposalAlreadyExecuted,
        VotePeriodEnded,
        VotePeriodNotEnded,
        TransferError,
        ProposalNotAccepted,
    }

    #[derive(Encode, Decode, SpreadLayout, PackedLayout, SpreadAllocate, Default)]
    #[cfg_attr(feature = "std", derive(Debug, PartialEq, Eq, scale_info::TypeInfo, StorageLayout))]
    pub struct Proposal {
        for_address: AccountId,
        against_address: AccountId,
        to: AccountId,
        title: String,
        description: String,
        amount: Balance,
        vote_start: Timestamp,
        vote_end: Timestamp,
        executed: bool,
    }

    #[derive(Encode, Decode, SpreadLayout, PackedLayout, SpreadAllocate, Default)]
    #[cfg_attr(feature = "std", derive(Debug, PartialEq, Eq, scale_info::TypeInfo, StorageLayout))]
    pub struct ProposalVote {
        against_votes: u8,
        for_votes: u8,
    }

    pub type ProposalId = u32;

    #[ink(storage)]
    #[derive(SpreadAllocate)]
    pub struct Governor {
        proposal_votes: Mapping<ProposalId, ProposalVote>,
        proposals: Mapping<ProposalId, Proposal>,
        next_proposal_id: u32,
        governance_token: AccountId,
    }

    impl Governor {
        #[ink(constructor, payable)]
        pub fn new(governance_token: AccountId) -> Self {
            ink_lang::utils::initialize_contract(|instance: &mut Self| {
                instance.governance_token = governance_token;
            })
        }

        #[ink(message)]
        pub fn propose(&mut self, for_address: AccountId, against_address: AccountId, to: AccountId, title: String, description: String, amount: Balance, duration: u64) -> Result<(), GovernorError> {
            if amount == 0 {
                return Err(GovernorError::AmountShouldNotBeZero)
            }
            if duration == 0 || duration > 60 * ONE_MINUTE {
                return Err(GovernorError::DurationError)
            }

            let now = self.env().block_timestamp();
            let proposal = Proposal {
                for_address,
                against_address,
                to,
                title,
                description,
                amount,
                vote_start: now,
                vote_end: now + duration * ONE_MINUTE,
                executed: false,
            };

            let id = self.next_proposal_id();
            self.proposals.insert(id, &proposal);

            Ok(())
        }

        #[ink(message)]
        pub fn execute(&mut self, proposal_id: ProposalId) -> Result<(), GovernorError> {
            let mut proposal = self
                .proposals
                .get(&proposal_id)
                .ok_or(GovernorError::ProposalNotFound)?;
            if proposal.executed {
                return Err(GovernorError::ProposalAlreadyExecuted)
            }
            let weight_for = self.account_weight(proposal.for_address);
            let weight_against = self.account_weight(proposal.against_address);
            let mut proposal_current_vote = self.proposal_votes.get(proposal_id).unwrap_or_default();
            proposal_current_vote.for_votes = weight_for;
            proposal_current_vote.against_votes = weight_against;

            if proposal_current_vote.against_votes >= proposal_current_vote.for_votes {
                return Err(GovernorError::ProposalNotAccepted)
            }

            proposal.executed = true;
            self.env()
                .transfer(proposal.to, proposal.amount)
                .map_err(|_| GovernorError::TransferError)?;

            Ok(())
        }

        #[ink(message)]
        pub fn get_proposal_vote(&self, proposal_id: ProposalId) -> Option<ProposalVote> {
            let proposal = self
                .proposals
                .get(&proposal_id)
                .ok_or(GovernorError::ProposalNotFound).ok()?;
            let weight_for = self.account_weight(proposal.for_address);
            let weight_against = self.account_weight(proposal.against_address);
            let mut proposal_current_vote = self.proposal_votes.get(proposal_id).unwrap_or_default();
            proposal_current_vote.for_votes = weight_for;
            proposal_current_vote.against_votes = weight_against;
           
            Some(proposal_current_vote)
        }

        #[ink(message)]
        pub fn get_proposal(&self, proposal_id: u32) -> Option<Proposal> {
            self.proposals.get(proposal_id)
        }

        #[ink(message)]
        pub fn get_proposals_size(&self) -> ProposalId {
            self.next_proposal_id
        }

        fn account_weight(&self, caller: AccountId) -> u8 {
            let balance = PSP22Ref::balance_of(&self.governance_token, caller);
            balance as u8
        }

        fn next_proposal_id(&mut self) -> ProposalId {
            let id = self.next_proposal_id;
            self.next_proposal_id += 1;
            id
        }
    }
}
