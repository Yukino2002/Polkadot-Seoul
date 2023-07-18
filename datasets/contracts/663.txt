#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]
#![allow(non_snake_case)]
#[openbrush::contract]
pub mod PositionDescriptor {
    use openbrush::contracts::psp34::Id;
    use openbrush::contracts::traits::psp22::extensions::metadata::PSP22MetadataRef;
    use crabswap::traits::periphery::position_descriptor::*;
    use crabswap::traits::periphery::position_manager::PositionManagerRef;
    use ink_prelude::string::String;
    use ink_storage::traits::SpreadAllocate;
    use primitives::{Address, U256, Int256, Int24};
    use crabswap::traits::periphery::periphery_immutable_state::PeripheryImmutableStateRef;
    use crabswap::traits::core::factory::FactoryRef;
    use libs::periphery::{TokenRatioSortOrder, NFTDescriptor};
    use crabswap::traits::core::pool_action::{PoolActionRef, Slot0};
    use ink_prelude::vec::Vec;
    use ink_prelude::vec;

    // TODO decode the hex to accountId
    static DAI:&'static str = "e4678b676433e1f6f3f6a77730f4ede1737ad4b828b229def437e3e2ab46eb01";
    static USDC:&'static str = "e4678b676433e1f6f3f6a77730f4ede1737ad4b828b229def437e3e2ab46eb01";
    static USDT:&'static str = "e4678b676433e1f6f3f6a77730f4ede1737ad4b828b229def437e3e2ab46eb01";
    static TBTC:&'static str = "e4678b676433e1f6f3f6a77730f4ede1737ad4b828b229def437e3e2ab46eb01";
    static WBTC:&'static str = "e4678b676433e1f6f3f6a77730f4ede1737ad4b828b229def437e3e2ab46eb01";
    static CHAIN_ID:u8 = 1;
    // address private constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    // address private constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    // address private constant TBTC = 0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa;
    // address private constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;

    #[ink(storage)]
    #[derive(SpreadAllocate)]
    pub struct PositionDescriptor {
        pub WETH9:Address,
        /// @dev A null-terminated string
        pub nativeCurrencyLabelBytes:Vec<u8>
    }

    impl Descriptor for PositionDescriptor {
        //positionManager is NonfungiblePositionManager address
        #[ink(message)]
        fn tokenURI(&self, positionManager: Address, tokenId: u128) -> String {
            // (, , address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, , , , , ) =
            //     positionManager.positions(tokenId);
            let (_, _, token0, token1, fee, tickLower, tickUpper, _, _, _, _, _) =
                PositionManagerRef::positions(&positionManager, Id::U128(tokenId));

            // IUniswapV3Pool pool =
            //     IUniswapV3Pool(
            //         PoolAddress.computeAddress(
            //             positionManager.factory(),
            //             PoolAddress.PoolKey({token0: token0, token1: token1, fee: fee})
            //         )
            //     );
            let factory_address = PeripheryImmutableStateRef::factory(&positionManager);
            let pool:Address = FactoryRef::get_pool(&factory_address,fee,token0,token1);

            // bool _flipRatio = flipRatio(token0, token1, ChainId.get());
            let _flipRatio:bool = self.flipRatio(token0, token1, CHAIN_ID);
            // address quoteTokenAddress = !_flipRatio ? token1 : token0;
            let quoteTokenAddress:Address = if !_flipRatio{
                token1
            }else{
                token0
            };
            // address baseTokenAddress = !_flipRatio ? token0 : token1;
            let baseTokenAddress:Address = if !_flipRatio {
                token0
            }else{
                token1
            };
            // (, int24 tick, , , , , ) = pool.slot0();
            let slot0:Slot0 = PoolActionRef::getSlot0(&pool);
            let tick:Int24 = slot0.tick;

            // return
            //     NFTDescriptor.constructTokenURI(
            //         NFTDescriptor.ConstructTokenURIParams({
            //             tokenId: tokenId,
            //             quoteTokenAddress: quoteTokenAddress,
            //             baseTokenAddress: baseTokenAddress,
            //             quoteTokenSymbol: quoteTokenAddress == WETH9
            //                 ? nativeCurrencyLabel()
            //                 : SafeERC20Namer.tokenSymbol(quoteTokenAddress),
            //             baseTokenSymbol: baseTokenAddress == WETH9
            //                 ? nativeCurrencyLabel()
            //                 : SafeERC20Namer.tokenSymbol(baseTokenAddress),
            //             quoteTokenDecimals: IERC20Metadata(quoteTokenAddress).decimals(),
            //             baseTokenDecimals: IERC20Metadata(baseTokenAddress).decimals(),
            //             flipRatio: _flipRatio,
            //             tickLower: tickLower,
            //             tickUpper: tickUpper,
            //             tickCurrent: tick,
            //             tickSpacing: pool.tickSpacing(),
            //             fee: fee,
            //             poolAddress: address(pool)
            //         })
            //     );
            return NFTDescriptor::constructTokenURI(
                    NFTDescriptor::ConstructTokenURIParams{
                        tokenId: U256::from(tokenId),
                        quoteTokenAddress: quoteTokenAddress,
                        baseTokenAddress: baseTokenAddress,
                        quoteTokenSymbol: if quoteTokenAddress == self.WETH9{
                            self.nativeCurrencyLabel()
                        }else{
                            PSP22MetadataRef::token_symbol(&quoteTokenAddress).expect("option errro!")
                        },
                        baseTokenSymbol: if baseTokenAddress == self.WETH9{
                            self.nativeCurrencyLabel()
                        }else{
                            PSP22MetadataRef::token_symbol(&baseTokenAddress).expect("option errro!")
                        },
                        quoteTokenDecimals: PSP22MetadataRef::token_decimals(&quoteTokenAddress),
                        baseTokenDecimals: PSP22MetadataRef::token_decimals(&baseTokenAddress),
                        flipRatio: _flipRatio,
                        tickLower: tickLower,
                        tickUpper: tickUpper,
                        tickCurrent: tick,
                        tickSpacing: PoolActionRef::get_tickspacing(&pool),
                        fee: fee,
                        poolAddress: pool
                    }
                );
        }
    }

    impl PositionDescriptor {
        #[ink(constructor)]
        // constructor(address _WETH9, bytes32 _nativeCurrencyLabelBytes) {
        pub fn new(_WETH9: AccountId, mut _nativeCurrencyLabelBytes: String) -> Self {
            ink_lang::codegen::initialize_contract(|instance: &mut PositionDescriptor| {
                instance.WETH9 = _WETH9;
                unsafe{
                instance.nativeCurrencyLabelBytes= _nativeCurrencyLabelBytes.as_mut_vec().clone();
            }
            })
        }

        fn flipRatio(&self,
             token0:Address,
             token1:Address,
             chainId:u8
        ) -> bool {
            return self.tokenRatioPriority(token0, chainId) > self.tokenRatioPriority(token1, chainId);
        }

        /// @notice Returns the native currency label as a string
        pub fn nativeCurrencyLabel(&self) ->String {
            let mut len = 0_usize;
            while len < 32 && self.nativeCurrencyLabelBytes[len] != 0 {
                len+=1;
            }
            let mut b:Vec<u8> = vec!(0;len);
            for i in 0..len {
                b[i] = self.nativeCurrencyLabelBytes[i];
            }
            return String::from_utf8(b).expect("error!");
        }

        pub fn tokenRatioPriority(&self,token:Address, chainId:u8) -> Int256 {
            if token == self.WETH9 {
                return TokenRatioSortOrder::DENOMINATOR;
            }
            if chainId == 1 {
                if token == TokenRatioSortOrder::trans_hex_2_account(USDC) {
                    return TokenRatioSortOrder::NUMERATOR_MOST;
                } else if token == TokenRatioSortOrder::trans_hex_2_account(USDT) {
                    return TokenRatioSortOrder::NUMERATOR_MORE;
                } else if token == TokenRatioSortOrder::trans_hex_2_account(DAI) {
                    return TokenRatioSortOrder::NUMERATOR;
                } else if token == TokenRatioSortOrder::trans_hex_2_account(TBTC) {
                    return TokenRatioSortOrder::DENOMINATOR_MORE;
                } else if token == TokenRatioSortOrder::trans_hex_2_account(WBTC) {
                    return TokenRatioSortOrder::DENOMINATOR_MOST;
                } else {
                    return 0;
                }
            }
            return 0;
        }
    }
}
