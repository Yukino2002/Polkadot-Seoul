use anchor_lang::{
    prelude::*,
    solana_program::{pubkey, pubkey::Pubkey},
};
use std::mem;

use test_linker::{cpi::accounts::TestLink, program::TestLinker};

declare_id!("3XQdG1Zpk151xuGHSd6DUkNuh9m9i3M8ptxJEHNfZdJ2");
pub const OWNER_GUARD: Pubkey = pubkey!("CuK4CzZFFQaK2KaUYYyNodQ6ZG6PTv1jjYKvqHUx7P5Y");
pub const SPOTTER_SEED: &str = "spotter";
pub const KEEPER_SEED: &str = "keeper";
pub const CONTRACT_SEED: &str = "contract";
pub const OPERATION_SEED: &str = "operation";
pub const DESCRIMINATOR_LEN: usize = 8;

#[program]
pub mod aggregation_spotter {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, init_addr: [Pubkey; 2]) -> Result<()> {
        ctx.accounts.spotter.is_initialized = true;
        ctx.accounts.spotter.admin = init_addr[0];
        ctx.accounts.spotter.executor = init_addr[1];
        ctx.accounts.spotter.rate_decimals = 10000;
        ctx.accounts.spotter.number_of_keepers = 0;
        ctx.accounts.spotter.consensus_target_rate = 6500; // 65 %

        Ok(())
    }

    /// @notice Create and add keeper to whitelist
    /// @param keeper address of keeper to add
    pub fn create_keeper(ctx: Context<CreateKeeper>, keeper: Pubkey) -> Result<()> {
        if *ctx.accounts.keeper_acc.key != keeper {
            return Err(SpotterError::WrongKeeperAccount.into());
        }

        ctx.accounts.keeper_pda.key = keeper;
        ctx.accounts.keeper_pda.is_allowed = true;
        ctx.accounts.spotter.number_of_keepers += 1;

        Ok(())
    }

    /// @notice Reenable keeper in whitelist
    /// @param keeper address of keeper to remove
    pub fn enable_keeper(ctx: Context<RemoveKeeper>, keeper: Pubkey) -> Result<()> {
        if *ctx.accounts.keeper_acc.key != keeper {
            return Err(SpotterError::WrongKeeperAccount.into());
        }

        if ctx.accounts.keeper_pda.is_allowed {
            return Err(SpotterError::KeeperAlreadyEnabled.into());
        }

        ctx.accounts.keeper_pda.is_allowed = true;
        ctx.accounts.spotter.number_of_keepers += 1;

        Ok(())
    }

    /// @notice Disable keeper from whitelist
    /// @param keeper address of keeper to remove
    pub fn remove_keeper(ctx: Context<RemoveKeeper>, keeper: Pubkey) -> Result<()> {
        if *ctx.accounts.keeper_acc.key != keeper {
            return Err(SpotterError::WrongKeeperAccount.into());
        }

        ctx.accounts.keeper_pda.is_allowed = false;
        ctx.accounts.spotter.number_of_keepers -= 1;

        Ok(())
    }

    /// @notice Adding contract to whitelist
    /// @param _contract address of contract to add
    pub fn add_allowed_contract(ctx: Context<AddAllowedContract>, contract: Pubkey) -> Result<()> {
        if *ctx.accounts.contract_acc.key != contract {
            return Err(SpotterError::WrongContractAccount.into());
        }

        ctx.accounts.contract_pda.key = contract;
        ctx.accounts.contract_pda.is_allowed = true;

        Ok(())
    }

    /// @notice Removing contract from whitelist
    /// @param _contract address of contract to remove
    pub fn remove_allowed_contract(
        ctx: Context<RemoveAllowedContract>,
        contract: Pubkey,
    ) -> Result<()> {
        if *ctx.accounts.contract_acc.key != contract {
            return Err(SpotterError::WrongContractAccount.into());
        }

        ctx.accounts.contract_pda.is_allowed = false;

        Ok(())
    }

    /// @notice Setting of target rate
    /// @param rate target rate
    pub fn set_consensus_target_rate(
        ctx: Context<SetConsensusTargetRate>,
        rate: u64,
    ) -> Result<()> {
        ctx.accounts.spotter.consensus_target_rate = rate;

        Ok(())
    }

    pub fn create_operation(
        ctx: Context<CreateOperation>,
        operation_data: OperationData,
        gas_price: u64,
    ) -> Result<()> {
        check_keeper(&ctx.accounts.keeper_pda)?;

        let keeper_proof = KeeperProof {
            keeper: *ctx.accounts.keeper_acc.key,
            gas_price: gas_price,
        };

        let proof_info = ProofInfo {
            is_approved: false,
            is_executed: false,
            proofs_count: 1,
            proofed_keepers: vec![Some(keeper_proof)],
        };

        let operation = Operation {
            operation_data,
            proof_info,
        };

        *ctx.accounts.operation_pda = operation;

        msg!(
            "NewOperation({}; [{:?}])",
            ctx.accounts.operation_pda.key(),
            ctx.accounts.operation_pda.operation_data.accounts
        );

        Ok(())
    }

    pub fn propose_operation(ctx: Context<ProposeOperation>, gas_price: u64) -> Result<()> {
        if ctx.accounts.operation_pda.proof_info.is_approved {
            return Err(SpotterError::OperationAlreadyApproved.into());
        }

        check_keeper(&ctx.accounts.keeper_pda)?;

        // Iterate over the list of keepers that already voted for this operation.
        // If the current keeper is already in the list, return an error.
        for proofed_keeper_opt in ctx.accounts.operation_pda.proof_info.proofed_keepers.iter() {
            if let Some(proofed_keeper) = proofed_keeper_opt {
                if proofed_keeper.keeper == ctx.accounts.keeper_pda.key {
                    return Err(SpotterError::KeeperIsAlreadyApproved.into());
                }
            } else {
                break;
            }
        }

        // Add new proof
        let keeper_proof = KeeperProof {
            keeper: *ctx.accounts.keeper_acc.key,
            gas_price: gas_price,
        };

        let keeper_idx = ctx.accounts.operation_pda.proof_info.proofs_count as usize;

        ctx.accounts
            .operation_pda
            .proof_info
            .proofed_keepers
            .insert(keeper_idx, Some(keeper_proof));
        ctx.accounts.operation_pda.proof_info.proofs_count += 1;

        // Check if enough votes were submitted to approve operation.
        // If they are, approve operation
        let rate_decimals = ctx.accounts.spotter.rate_decimals;
        let num_allowed_keepers = ctx.accounts.spotter.number_of_keepers;

        if ctx.accounts.operation_pda.proof_info.proofs_count * (rate_decimals as u64)
            / num_allowed_keepers
            >= ctx.accounts.spotter.consensus_target_rate
        {
            ctx.accounts.operation_pda.proof_info.is_approved = true;
            msg!("ProposalApproved({})", ctx.accounts.operation_acc.key);
        }

        Ok(())
    }

    /// @notice execute approved operation
    pub fn execute_operation(ctx: Context<ExecuteOperation>) -> Result<()> {
        // If operation is already executed, return an error.
        if ctx.accounts.operation_pda.proof_info.is_executed {
            return Err(SpotterError::OperationAlreadyExecuted.into());
        }

        // If operation is not approved, return an error.
        if !ctx.accounts.operation_pda.proof_info.is_approved {
            return Err(SpotterError::OperationIsNotApproved.into());
        }

        // Check if accounts array has correct length.
        if ctx.accounts.operation_pda.operation_data.accounts.len() != 2 {
            msg!(
                "IncorrectAccountsLength(expected: {}, actual: {})",
                2,
                ctx.accounts.operation_pda.operation_data.accounts.len()
            );
            return Err(SpotterError::IncorrectAccountsLength.into());
        }

        // Check that each provided account corresponds to the correct account in operationData.
        if ctx.accounts.operation_pda.operation_data.accounts[0] != *ctx.accounts.test_program.key {
            return Err(SpotterError::WrongContractAccount.into());
        }

        if ctx.accounts.operation_pda.operation_data.accounts[1] != *ctx.accounts.executer.key {
            return Err(SpotterError::WrongContractAccount.into());
        }

        // If provided program id account differs from the one stored in operation, return an error.
        if ctx.accounts.operation_pda.operation_data.contr != *ctx.accounts.test_program.key {
            return Err(SpotterError::WrongContractAccount.into());
        }

        let cpi_ctx = ctx.accounts.get_cpi_ctx(
            ctx.accounts.test_program.to_account_info(),
            ctx.accounts.executer.to_account_info(),
        );

        test_linker::cpi::test_link(cpi_ctx)?;

        ctx.accounts.operation_pda.proof_info.is_executed = true;

        Ok(())
    }
}

pub fn check_keeper(keeper: &Keeper) -> Result<()> {
    if keeper.is_allowed {
        return Ok(());
    }

    Err(SpotterError::KeeperNotAllowed.into())
}

#[error_code]
pub enum SpotterError {
    KeeperNotAllowed,
    KeeperAlreadyEnabled,
    WrongKeeperAccount,
    WrongContractAccount,
    OperationAlreadyApproved,
    OperationAlreadyExecuted,
    OperationIsNotApproved,
    KeeperIsAlreadyApproved,
    IncorrectAccountsLength,
    IncorrectAccounts,
}

#[account]
pub struct Keeper {
    pub is_allowed: bool, // 1
    pub key: Pubkey,      // 32
}

impl Keeper {
    pub const MAXIMUM_SIZE: usize = DESCRIMINATOR_LEN + 1 + 32;
}

#[account]
pub struct AllowedContract {
    pub is_allowed: bool, // 1
    pub key: Pubkey,      // 32
}

impl AllowedContract {
    pub const MAXIMUM_SIZE: usize = DESCRIMINATOR_LEN + 1 + 32;
}

#[derive(AnchorSerialize, AnchorDeserialize, Debug, Clone, Copy)]
pub struct KeeperProof {
    pub keeper: Pubkey, // 32
    pub gas_price: u64, // 8
}

impl KeeperProof {
    pub const MAXIMUM_SIZE: usize = 32 + 8;
}

/// Calculates size of the vector with borsh serialization
pub const fn calculate_vec_allocating_size<T>(max_elements: usize, element_size: usize) -> usize {
    let metadata_size = mem::size_of::<Vec<T>>();
    // let metadata_size: usize = 24; // Usual metadata for Vec is 24 bytes

    metadata_size + (element_size * max_elements)
}

/// @notice struct for informations that hold knowledge of operation status
/// @param isApproved indicates operation approved and ready to execute
/// @param isExecuted indicates operation is executed
/// @param proofsCount number of proofs by uniq keepers
/// @param proofedKeepers keepers which made proof of operation
#[derive(AnchorSerialize, AnchorDeserialize, Debug, Clone)]
pub struct ProofInfo {
    pub is_approved: bool,                         // 1
    pub is_executed: bool,                         // 1
    pub proofs_count: u64,                         // 8
    pub proofed_keepers: Vec<Option<KeeperProof>>, // (n + 1) * 40
}

impl ProofInfo {
    pub const MAXIMUM_SIZE: usize = 1
        + 1
        + 8
        + calculate_vec_allocating_size::<KeeperProof>(100, KeeperProof::MAXIMUM_SIZE + 1);

    pub const fn maximum_size(num_elements: usize) -> usize {
        1 + 1
            + 8
            + calculate_vec_allocating_size::<KeeperProof>(
                num_elements,
                KeeperProof::MAXIMUM_SIZE + 1,
            )
    }
}

/// @notice struct for informations that hold knowledge of operation calling proccess
/// @param contr contract address
/// @param functionSelector function selector to execute
/// @param params parameters for func call
#[derive(AnchorSerialize, AnchorDeserialize, Debug, Clone)]
pub struct OperationData {
    pub contr: Pubkey, // 32
    pub accounts: Vec<Pubkey>, // (n + 1) * 32
                       // pub functionSelector: ,
                       // pub params: ,
}

impl OperationData {
    pub const MAXIMUM_SIZE: usize =
        32 + calculate_vec_allocating_size::<Option<Pubkey>>(100, 32 + 1);

    pub const fn maximum_size(num_accounts: usize) -> usize {
        32 + calculate_vec_allocating_size::<Option<Pubkey>>(num_accounts, 32 + 1)
    }
}

/// @notice main struct that keeps all information about one entity
/// @param proofInfo struct for informations that hold knowledge of operation status
/// @param oracleOpTxId tx id where operation was generated on entangle oracle blockchain spotter contract
/// @param operationData struct for informations that hold knowledge of operation calling proccess
#[account]
pub struct Operation {
    pub proof_info: ProofInfo,
    pub operation_data: OperationData,
}

impl Operation {
    pub const MAXIMUM_SIZE: usize =
        DESCRIMINATOR_LEN + ProofInfo::MAXIMUM_SIZE + OperationData::MAXIMUM_SIZE;

    pub const fn maximum_size(num_elements: usize, num_accounts: usize) -> usize {
        DESCRIMINATOR_LEN
            + ProofInfo::maximum_size(num_elements)
            + OperationData::maximum_size(num_accounts)
    }
}

#[account]
pub struct AggregationSpotter {
    pub is_initialized: bool,   // 1
    pub admin: Pubkey,          // 32
    pub executor: Pubkey,       // 32
    pub number_of_keepers: u64, // 8
    /// 10000 = 100%    
    pub rate_decimals: u64, // 8
    /// percentage of proofs div numberOfAllowedKeepers which should be reached to approve operation. Scaled with 10000 decimals, e.g. 6000 is 60%
    pub consensus_target_rate: u64, // 8
}

impl AggregationSpotter {
    pub const MAXIMUM_SIZE: usize = DESCRIMINATOR_LEN + 1 + 32 + 32 + 8 + 8 + 8;
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = admin, space = AggregationSpotter::MAXIMUM_SIZE, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(mut, constraint = admin.key() == OWNER_GUARD)]
    pub admin: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CreateKeeper<'info> {
    #[account(mut, has_one = admin, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(mut, constraint = admin.key() == spotter.admin)]
    pub admin: Signer<'info>,
    #[account(init, payer = admin, space = Keeper::MAXIMUM_SIZE, seeds=[KEEPER_SEED.as_ref(), keeper_acc.key.as_ref()], bump)]
    pub keeper_pda: Account<'info, Keeper>,
    /// CHECK: We need this account only to create the PDA
    pub keeper_acc: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct EnableKeeper<'info> {
    #[account(mut, has_one = admin, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(constraint = admin.key() == spotter.admin)]
    pub admin: Signer<'info>,
    #[account(mut, seeds=[KEEPER_SEED.as_ref(), keeper_acc.key.as_ref()], bump)]
    pub keeper_pda: Account<'info, Keeper>,
    /// CHECK: We need this account only to create the PDA
    pub keeper_acc: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RemoveKeeper<'info> {
    #[account(mut, has_one = admin, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(constraint = admin.key() == spotter.admin)]
    pub admin: Signer<'info>,
    #[account(mut, seeds=[KEEPER_SEED.as_ref(), keeper_acc.key.as_ref()], bump)]
    pub keeper_pda: Account<'info, Keeper>,
    /// CHECK: We need this account only to create the PDA
    pub keeper_acc: AccountInfo<'info>,
}

#[derive(Accounts)]
pub struct AddAllowedContract<'info> {
    #[account(mut, has_one = admin, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(mut, constraint = admin.key() == spotter.admin)]
    pub admin: Signer<'info>,
    #[account(init, payer = admin, space = AllowedContract::MAXIMUM_SIZE, seeds=[CONTRACT_SEED.as_ref(), contract_acc.key.as_ref()], bump)]
    pub contract_pda: Account<'info, AllowedContract>,
    /// CHECK: We need this account only to create the PDA
    pub contract_acc: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RemoveAllowedContract<'info> {
    #[account(mut, has_one = admin, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(constraint = admin.key() == spotter.admin)]
    pub admin: Signer<'info>,
    #[account(mut, seeds=[CONTRACT_SEED.as_ref(), contract_acc.key.as_ref()], bump)]
    pub contract_pda: Account<'info, AllowedContract>,
    /// CHECK: We need this account only to create the PDA
    pub contract_acc: AccountInfo<'info>,
}

#[derive(Accounts)]
pub struct SetConsensusTargetRate<'info> {
    #[account(mut, has_one = admin, seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(constraint = admin.key() == spotter.admin)]
    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct CreateOperation<'info> {
    #[account(seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(mut)]
    pub keeper_acc: Signer<'info>,
    #[account(mut, seeds=[KEEPER_SEED.as_ref(), keeper_acc.key.as_ref()], bump)]
    pub keeper_pda: Account<'info, Keeper>,
    #[account(init, payer = keeper_acc, space = Operation::maximum_size(spotter.number_of_keepers as usize, 10), seeds=[OPERATION_SEED.as_ref(), operation_acc.key.as_ref()], bump)]
    pub operation_pda: Account<'info, Operation>,
    /// CHECK: We need this account only to create the PDA
    pub operation_acc: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct ProposeOperation<'info> {
    #[account(seeds=[SPOTTER_SEED.as_ref()], bump)]
    pub spotter: Account<'info, AggregationSpotter>,
    #[account(mut)]
    pub keeper_acc: Signer<'info>,
    #[account(mut, seeds=[KEEPER_SEED.as_ref(), keeper_acc.key.as_ref()], bump)]
    pub keeper_pda: Account<'info, Keeper>,
    /// CHECK: We need this account only to create the PDA
    pub operation_acc: AccountInfo<'info>,
    #[account(mut, seeds=[OPERATION_SEED.as_ref(), operation_acc.key.as_ref()], bump)]
    pub operation_pda: Account<'info, Operation>,
}

#[derive(Accounts)]
pub struct ExecuteOperation<'info> {
    /// Callee program id
    pub test_program: Program<'info, TestLinker>,
    #[account(mut)]
    pub executer: Signer<'info>,
    /// CHECK: We need this account only to create the PDA
    pub operation_acc: AccountInfo<'info>,
    #[account(mut, seeds=[OPERATION_SEED.as_ref(), operation_acc.key.as_ref()], bump)]
    pub operation_pda: Account<'info, Operation>,
}

impl<'info> ExecuteOperation<'info> {
    pub fn get_cpi_ctx(
        &self,
        cpi_program: AccountInfo<'info>,
        executer: AccountInfo<'info>,
    ) -> CpiContext<'_, '_, '_, 'info, TestLink<'info>> {
        let cpi_accounts = TestLink { executer: executer };

        CpiContext::new(cpi_program, cpi_accounts)
    }
}
