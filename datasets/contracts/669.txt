#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]
#![allow(non_snake_case)]

#[openbrush::contract]
pub mod position_manager {
    use openbrush::contracts::psp34::PSP34Data;
    // use crabswap::impls::periphery::position_manager::*;
    use openbrush::contracts::psp34::extensions::burnable::*;
    use openbrush::contracts::psp34::extensions::mintable::*;
    use openbrush::modifiers;
    use crabswap::impls::erc721_permit::*;
    use crabswap::impls::periphery::PeripheryPayments::*;
    use crabswap::impls::pool_initialize::*;
    use crabswap::impls::psp34_base::*;
    use crabswap::traits::core::pool_action::PoolActionRef;
    use crabswap::traits::periphery::position_manager::*;
    use crabswap::traits::periphery::LiquidityManagement::*;
    use crabswap::traits::periphery::periphery_immutable_state::*;

    use ink_lang::codegen::EmitEvent;
    use ink_lang::codegen::Env;
    use ink_prelude::string::String;
    use ink_storage::Mapping;
    use libs::core::FixedPoint128;
    use libs::core::Position::Info;
    use libs::periphery::PoolAddress;
    use libs::swap::FullMath;
    use primitives::{Int24, Uint128, Uint24, Uint256, Uint80, Uint96, ADDRESS0};

    use ink_storage::traits::PackedLayout;

    #[cfg(feature = "std")]
    use ink_storage::traits::StorageLayout;

    use crabswap::traits::core::factory::*;
    use crabswap::traits::periphery::position_descriptor::*;
    use ink_env::DefaultEnvironment;
    use ink_prelude::vec::Vec;
    use ink_storage::traits::{SpreadAllocate, SpreadLayout};
    use libs::core::TickMath;
    use libs::periphery::LiquidityAmounts;
    use libs::PoolKey;
    use primitives::{Address, U256};
    use scale::{Decode, Encode};

    use crabswap::impls::periphery_immutable_state::{ImmutableStateStorage,ImmutableStateData};
    use crabswap::traits::core::pool_action::*;
    use ink_env::CallFlags;

    #[derive(Default, Debug, Encode, Decode, SpreadAllocate, SpreadLayout, PackedLayout)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo, StorageLayout))]
    pub struct Position {
        // the nonce for permits
        nonce: Uint96,
        // the address that is approved for spending this token
        operator: Address,
        // the ID of the pool with which this token is connected
        poolId: Uint80,
        // the tick range of the position
        tickLower: Int24,
        tickUpper: Int24,
        // the liquidity of the position
        liquidity: Uint128,
        // the fee growth of the aggregate position as of the last action on the individual position
        feeGrowthInside0LastX128: Uint256,
        feeGrowthInside1LastX128: Uint256,
        // how many uncollected tokens are owed to the position, as of the last computation
        tokensOwed0: Uint128,
        tokensOwed1: Uint128,
    }

    #[derive(Default, Decode, Encode, Debug, SpreadAllocate, SpreadLayout)]
    struct MintCallbackData {
        poolKey: PoolKey,
        payer: Address,
    }
    #[ink(storage)]
    #[derive(
        Default,
        SpreadAllocate,
        ImmutableStateStorage,
        PSP34Storage,
        ERC721PermitStorage,
        PSP34BaseStorage,
    )]
    pub struct PositionMangerContract {
        #[ImmutableStateField]
        immutable_state: ImmutableStateData,
        #[PSP34StorageField]
        psp34: PSP34Data,
        #[ERC721PermitStorageField]
        erc721_permit: ERC721PermitData,
        #[PSP34BaseStorageField]
        psp34_base: PSP34BaseData,

        // /// @dev IDs of pools assigned by this contract
        // mapping(address => uint80) private _poolIds;
        _poolIds: Mapping<Address, u128>,

        // /// @dev Pool keys by pool ID, to save on SSTOREs for position data
        // mapping(uint80 => PoolAddress.PoolKey) private _poolIdToPoolKey;
        _poolIdToPoolKey: Mapping<u128, PoolAddress::PoolKey>,

        // /// @dev The token ID position data
        // mapping(uint256 => Position) private _positions;
        _positions: Mapping<Id, Position>,

        // /// @dev The ID of the next token that will be minted. Skips 0
        // uint176 private _nextId = 1;
        _nextId: u128,
        // /// @dev The ID of the next pool that is used for the first time. Skips 0
        // uint80 private _nextPoolId = 1;
        _nextPoolId: u128,

        /// @dev The address of the token descriptor contract, which handles generating token URIs for position tokens
        _tokenDescriptor: Address,
    }

    impl Initializer for PositionMangerContract {}
    impl PSP34 for PositionMangerContract {}
    impl PSP34Mintable for PositionMangerContract {}
    impl PSP34Burnable for PositionMangerContract {}
    impl PSP34Base for PositionMangerContract {}
    impl PeripheryImmutableState for PositionMangerContract {}
        
    impl IERC721Permit for PositionMangerContract {
        #[ink(message)]
        fn _getAndIncrementNonce(&mut self, _tokenId: Id) -> u128{
            let mut position: Position = self
                ._positions
                .get(&_tokenId)
                .expect("token not in _positions!");
            position.nonce +=1;
            self._positions.insert(_tokenId,&position);
            position.nonce
        }
    }
    
    impl LiquidityManagementTrait for PositionMangerContract {
        // returns (uint128 liquidity,uint256 amount0,uint256 amount1,IUniswapV3Pool pool)
        #[ink(message)]
        fn addLiquidity(&mut self, params: AddLiquidityParams) -> (u128, U256, U256, Address) {
            // PoolAddress.PoolKey memory poolKey =
            //         PoolAddress.PoolKey({token0: params.token0, token1: params.token1, fee: params.fee});
            let poolKey: PoolKey = PoolKey {
                token0: params.token0,
                token1: params.token1,
                fee: params.fee,
            };

            // pool = IUniswapV3Pool(PoolAddress.computeAddress(factory, poolKey));
            let factory = self.immutable_state.factory;
            // let poolAddress = PoolAddress::computeAddress(factory, poolKey.clone());
            let poolAddress =
                FactoryRef::get_pool(&factory, params.fee, params.token0, params.token1);

            //         // compute the liquidity amount
            //         {
            //             // (uint160 sqrtPriceX96, , , , , , ) = poolRef::slot0(poolAddress);
            let slot0: Slot0 = PoolActionRef::getSlot0(&poolAddress);
            let sqrtPriceX96 = slot0.sqrtPriceX96.value;
            //             // uint160 sqrtRatioAX96 = TickMath.getSqrtRatioAtTick(params.tickLower);
            let sqrtRatioAX96 = TickMath::getSqrtRatioAtTick(params.tickLower);
            //             // uint160 sqrtRatioBX96 = TickMath.getSqrtRatioAtTick(params.tickUpper);
            let sqrtRatioBX96 = TickMath::getSqrtRatioAtTick(params.tickUpper);

            //             liquidity = LiquidityAmounts::getLiquidityForAmounts(
            //                 sqrtPriceX96,
            //                 sqrtRatioAX96,
            //                 sqrtRatioBX96,
            //                 params.amount0Desired,
            //                 params.amount1Desired
            //             );
            //         }
            ink_env::debug_println!(
                "sqrtPriceX96 is:{},sqrtRatioAX96 is:{},sqrtRatioBX96 is:{}",
                sqrtPriceX96,
                sqrtRatioAX96,
                sqrtRatioBX96
            );
            let liquidity = LiquidityAmounts::getLiquidityForAmounts(
                sqrtPriceX96,
                sqrtRatioAX96,
                sqrtRatioBX96,
                params.amount0Desired.value,
                params.amount1Desired.value,
            );

            //         (amount0, amount1) = pool.mint(
            //             params.recipient,
            //             params.tickLower,
            //             params.tickUpper,
            //             liquidity,
            //             abi.encode(MintCallbackData({poolKey: poolKey, payer: msg.sender}))
            //         );
            let msg_sender = ink_env::caller::<DefaultEnvironment>();
            let mint_callback_data = MintCallbackData {
                poolKey: poolKey,
                payer: msg_sender,
            };

            let callback_data = scale::Encode::encode(&mint_callback_data);
            let (amount0, amount1) = PoolActionRef::mint_builder(
                &poolAddress,
                params.recipient,
                params.tickLower,
                params.tickUpper,
                liquidity,
                callback_data.clone(),
            )
            .call_flags(CallFlags::default().set_allow_reentry(true))
            .fire()
            .unwrap();
            // self.uniswapV3MintCallback(amount0, amount1, callback_data);
            //         require(amount0 >= params.amount0Min && amount1 >= params.amount1Min, 'Price slippage check');
            assert!(
                amount0 >= params.amount0Min.value && amount1 >= params.amount1Min.value,
                "Price slippage check"
            );
            return (liquidity, amount0, amount1, poolAddress);
        }

        #[ink(message)]
        fn uniswapV3MintCallback(&mut self, amount0Owed: U256, amount1Owed: U256, data: Vec<u8>) {
            let manager_address: openbrush::traits::AccountId =
                ink_env::account_id::<DefaultEnvironment>();
            let msg_sender = ink_env::caller::<DefaultEnvironment>();
            // MintCallbackData memory deceoded = abi.decode(data, (MintCallbackData));
            let decoded: MintCallbackData =
                scale::Decode::decode(&mut data.as_ref()).expect("call back data parse error!");
            // TODO add callback validation
            // CallbackValidation.verifyCallback(factory, decoded.poolKey);

            // if (amount0Owed > 0) pay(decoded.poolKey.token0, decoded.payer, msg.sender, amount0Owed);
            if amount0Owed > U256::from(0) {
                PeripheryPaymentsTraitRef::pay_builder(
                    &manager_address,
                    decoded.poolKey.token0,
                    decoded.payer,
                    msg_sender,
                    amount0Owed,
                )
                .call_flags(CallFlags::default().set_allow_reentry(true))
                .fire()
                .unwrap();
            }
            // if (amount1Owed > 0) pay(decoded.poolKey.token1, decoded.payer, msg.sender, amount1Owed);
            if amount1Owed > U256::from(0) {
                PeripheryPaymentsTraitRef::pay_builder(
                    &manager_address,
                    decoded.poolKey.token1,
                    decoded.payer,
                    msg_sender,
                    amount1Owed,
                )
                .call_flags(CallFlags::default().set_allow_reentry(true))
                .fire()
                .unwrap();
            }
        }
    }

    impl PeripheryPaymentsTrait for PositionMangerContract {}

    // modifier isAuthorizedForToken(uint256 tokenId) {
    //     require(_isApprovedOrOwner(msg.sender, tokenId), 'Not approved');
    //     _;
    // }

    /// Throws if called by any account other than the owner.
    // #[modifier_definition]
    // pub fn only_owner<T, F, R, E>(instance: &mut T, body: F) -> Result<R, E>
    // where
    //     T: OwnableStorage,
    //     F: FnOnce(&mut T) -> Result<R, E>,
    //     E: From<OwnableError>,
    // {
    //     if instance.get().owner != T::env().caller() {
    //         return Err(From::from(OwnableError::CallerIsNotOwner))
    //     }
    //     body(instance)
    // }

    impl PositionMangerContract {
        #[ink(constructor, payable)]
        pub fn new(factory: AccountId, weth9: AccountId, _tokenDescriptor: AccountId) -> Self {
            // let initializer = PoolInitializeData {
            //     factory,
            //     WETH9: weth9,
            // };
            // let name = "Crabswap V3 Positions NFT-V1";
            // let symbol = "Crab-V3-POS";
            // let psp34_base = PSP34BaseData {
            //     name: String::from(name),
            //     symbol: String::from(symbol),
            // };
            // let erc721_permit = ERC721PermitData {
            //     nameHash: ink_lang::blake2x256!("Crabswap V3 Positions NFT-V1"),
            //     versionHash: ink_lang::blake2x256!("1"),
            // };
            // let psp34 = PSP34Data::default();
            // let instance: PositionMangerContract = PositionMangerContract {
            //     initializer,
            //     erc721_permit,
            //     psp34_base,
            //     _tokenDescriptor,
            //     psp34,
            //     _nextPoolId: 1,
            //     _nextId: 1,
            //     _positions: Default::default(),
            //     _poolIdToPoolKey: Default::default(),
            //     _poolIds: Default::default(),
            // };
            // instance
            ink_lang::codegen::initialize_contract(|instance: &mut PositionMangerContract| {
                instance.immutable_state.factory = factory;
                instance.immutable_state.WETH9 = weth9;
                let name = "Crabswap V3 Positions NFT-V1";
                let symbol = "Crab-V3-POS";
                // let version = "1";
                instance.erc721_permit.nameHash =
                    ink_lang::blake2x256!("Crabswap V3 Positions NFT-V1");
                instance.erc721_permit.versionHash = ink_lang::blake2x256!("1");
                instance.psp34_base.name = String::from(name);
                instance.psp34_base.symbol = String::from(symbol);
                instance._tokenDescriptor = _tokenDescriptor;
                instance._nextPoolId = 0;
                instance._nextId = 0;
                instance._positions = Default::default();
                instance._poolIdToPoolKey = Default::default();
                instance._poolIds = Default::default();
            })
        }

        /// @dev Caches a pool key
        fn cachePoolKey(&mut self, pool: Address, poolKey: PoolAddress::PoolKey) -> u128 {
            let mut poolId = match self._poolIds.get(&pool) {
                Some(id) => id,
                None => 0,
            };
            if poolId == 0 {
                self._nextPoolId = self._nextPoolId + 1;
                poolId = self._nextPoolId;
                self._poolIds.insert(pool, &poolId);
                self._poolIdToPoolKey.insert(poolId, &poolKey);
            }
            poolId
        }

        // #[ink(message)]
        // pub fn testEvent(&mut self) -> u128 {
        //     self.env().emit_event(TestEvent { tokenId: 1 });
        //     0
        // }
    }

    // impl PositionManager for PositionMangerContract{}
    impl PositionManager for PositionMangerContract {
        #[ink(message, payable)]
        #[modifiers(checkDeadline(deadline))]
        fn increaseLiquidity(
            &mut self,
            tokenId: Id,
            amount0Desired: U256,
            amount1Desired: U256,
            amount0Min: U256,
            amount1Min: U256,
            deadline: u64,
        ) -> (
            u128, //liquidity
            U256, //amount0
            U256, //amount1
        ) {
            // Position storage position = _positions[params.tokenId];
            let params = IncreaseLiquidityParams {
                tokenId,
                amount0Desired,
                amount1Desired,
                amount0Min,
                amount1Min,
                deadline,
            };
            let mut position: Position = self
                ._positions
                .get(params.tokenId.clone())
                .expect("token not in _positions!");
            // PoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];
            let poolKey: PoolAddress::PoolKey = self
                ._poolIdToPoolKey
                .get(position.poolId)
                .expect("token not in _poolIdToPoolKey!");
            // IUniswapV3Pool pool;

            // (liquidity, amount0, amount1, pool) = addLiquidity(
            //     AddLiquidityParams({
            //         token0: poolKey.token0,
            //         token1: poolKey.token1,
            //         fee: poolKey.fee,
            //         tickLower: position.tickLower,
            //         tickUpper: position.tickUpper,
            //         amount0Desired: params.amount0Desired,
            //         amount1Desired: params.amount1Desired,
            //         amount0Min: params.amount0Min,
            //         amount1Min: params.amount1Min,
            //         recipient: address(this)
            //     })
            // );
            let address_this = ink_env::account_id::<DefaultEnvironment>();
            let (liquidity, amount0, amount1, pool) = self.addLiquidity(AddLiquidityParams {
                token0: poolKey.token0,
                token1: poolKey.token1,
                fee: poolKey.fee,
                tickLower: position.tickLower,
                tickUpper: position.tickUpper,
                amount0Desired: Uint256::new_with_u256(params.amount0Desired),
                amount1Desired: Uint256::new_with_u256(params.amount1Desired),
                amount0Min: Uint256::new_with_u256(params.amount0Min),
                amount1Min: Uint256::new_with_u256(params.amount1Min),
                recipient: address_this,
            });

            // bytes32 positionKey = PositionKey.compute(address(this), position.tickLower, position.tickUpper);
            // let positionKey = PositionKey::compute(address_this, position.tickLower, position.tickUpper);

            // // this is now updated to the current transaction
            // (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) = pool.positions(positionKey);
            let positionInfo: Info = PoolActionRef::positions(
                &pool,
                address_this,
                position.tickLower,
                position.tickUpper,
            );
            let feeGrowthInside0LastX128 = positionInfo.feeGrowthInside0LastX128;
            let feeGrowthInside1LastX128 = positionInfo.feeGrowthInside1LastX128;
            // position.tokensOwed0 += uint128(
            //     FullMath.mulDiv(
            //         feeGrowthInside0LastX128 - position.feeGrowthInside0LastX128,
            //         position.liquidity,
            //         FixedPoint128.Q128
            //     )
            // );
            position.tokensOwed0 = position.tokensOwed0
                + FullMath::mulDiv(
                    feeGrowthInside0LastX128.value - position.feeGrowthInside0LastX128.value,
                    U256::from(position.liquidity),
                    U256::from(FixedPoint128::Q128),
                )
                .as_u128();
            // position.tokensOwed1 += uint128(
            //     FullMath.mulDiv(
            //         feeGrowthInside1LastX128 - position.feeGrowthInside1LastX128,
            //         position.liquidity,
            //         FixedPoint128.Q128
            //     )
            // );
            position.tokensOwed1 = position.tokensOwed1
                + FullMath::mulDiv(
                    feeGrowthInside1LastX128.value - position.feeGrowthInside1LastX128.value,
                    U256::from(position.liquidity),
                    U256::from(FixedPoint128::Q128),
                )
                .as_u128();
            // position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
            position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
            // position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
            position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
            // position.liquidity += liquidity;
            position.liquidity += liquidity;
            self._positions.insert(params.tokenId.clone(), &position);
            // emit IncreaseLiquidity(params.tokenId, liquidity, amount0, amount1);
            self.env().emit_event(IncreaseLiquidity {
                tokenId: params.tokenId.clone(),
                liquidity,
                amount0,
                amount1,
            });
            (liquidity, amount0, amount1)
        }

        // #[ink(message)]
        // fn setFactory(&mut self, factory: Address) {
        //     self.factory = Some(factory);
        // }

        // isAuthorizedForToken(params.tokenId)
        // checkDeadline(params.deadline)
        #[ink(message, payable)]
        #[modifiers(checkDeadline(deadline))]
        #[modifiers(isAuthorizedForToken(tokenId))]
        fn decreaseLiquidity(
            &mut self,
            tokenId: Id,
            liquidity: u128,
            amount0Min: U256,
            amount1Min: U256,
            deadline: u64,
        ) -> (U256, U256) {
            let params = DecreaseLiquidityParams {
                tokenId:tokenId.clone(),
                liquidity,
                amount0Min,
                amount1Min,
                deadline,
            };
            // require(params.liquidity > 0);
            assert!(liquidity > 0, "liquidity must big than 0!");

            // Position storage position = _positions[params.tokenId];
            let mut position: Position = self
                ._positions
                .get(tokenId.clone())
                .expect("tokenId not in _positions!");
            // uint128 positionLiquidity = position.liquidity;
            let positionLiquidity: u128 = position.liquidity;
            // require(positionLiquidity >= params.liquidity);
            assert!(
                U256::from(positionLiquidity) >= U256::from(params.liquidity),
                "positionLiquidity must bt params.liquidity"
            );
            // PoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];
            let poolKey: PoolAddress::PoolKey = self
                ._poolIdToPoolKey
                .get(position.poolId)
                .expect("poolId not in _poolIdToPoolKey!");
            // IUniswapV3Pool pool = IUniswapV3Pool(PoolAddress.computeAddress(factory, poolKey));
            let factoryAddress = self.immutable_state.factory;
            let pool: Address =
                FactoryRef::get_pool(&factoryAddress, poolKey.fee, poolKey.token0, poolKey.token1);

            // (amount0, amount1) = pool.burn(position.tickLower, position.tickUpper, params.liquidity);
            let (amount0, amount1) = PoolActionRef::burn(
                &pool,
                position.tickLower,
                position.tickUpper,
                params.liquidity,
            );
            // require(amount0 >= params.amount0Min && amount1 >= params.amount1Min, 'Price slippage check');
            assert!(
                amount0 >= params.amount0Min && amount1 >= params.amount1Min,
                "Price slippage check"
            );
            // bytes32 positionKey = PositionKey.compute(address(this), position.tickLower, position.tickUpper);
            let address_this = ink_env::account_id::<DefaultEnvironment>();
            // let positionKey = PositionKey::compute(address_this, position.tickLower, position.tickUpper);
            // // this is now updated to the current transaction
            // (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) = pool.positions(positionKey);
            let pool_info = PoolActionRef::positions(
                &pool,
                address_this,
                position.tickLower,
                position.tickUpper,
            );
            let feeGrowthInside0LastX128 = pool_info.feeGrowthInside0LastX128;
            let feeGrowthInside1LastX128 = pool_info.feeGrowthInside1LastX128;
            // position.tokensOwed0 +=
            //     uint128(amount0) +
            //     uint128(
            //         FullMath.mulDiv(
            //             feeGrowthInside0LastX128 - position.feeGrowthInside0LastX128,
            //             positionLiquidity,
            //             FixedPoint128.Q128
            //         )
            //     );
            position.tokensOwed0 += amount0.as_u128()
                + FullMath::mulDiv(
                    feeGrowthInside0LastX128.value - position.feeGrowthInside0LastX128.value,
                    U256::from(positionLiquidity),
                    U256::from(FixedPoint128::Q128),
                )
                .as_u128();
            // position.tokensOwed1 +=
            //     uint128(amount1) +
            //     uint128(
            //         FullMath.mulDiv(
            //             feeGrowthInside1LastX128 - position.feeGrowthInside1LastX128,
            //             positionLiquidity,
            //             FixedPoint128.Q128
            //         )
            //     );
            position.tokensOwed1 += amount1.as_u128()
                + FullMath::mulDiv(
                    feeGrowthInside1LastX128.value - position.feeGrowthInside1LastX128.value,
                    U256::from(positionLiquidity),
                    U256::from(FixedPoint128::Q128),
                )
                .as_u128();
            // position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
            position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
            // position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
            position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
            // // subtraction is safe because we checked positionLiquidity is gte params.liquidity
            // position.liquidity = positionLiquidity - params.liquidity;
            position.liquidity = positionLiquidity - params.liquidity;
            self._positions.insert(tokenId.clone(), &position);
            // emit DecreaseLiquidity(params.tokenId, params.liquidity, amount0, amount1);
            self.env().emit_event(DecreaseLiquidity {
                tokenId: params.tokenId,
                liquidity,
                amount0,
                amount1,
            });
            (amount0, amount1)
        }

        #[ink(message)]
        fn tokenURI(&self, tokenId: u128) -> String {
            assert!(self._check_token_exists(&Id::U128(tokenId)).is_ok());
            let manager_address = ink_env::account_id::<DefaultEnvironment>();
            return DescriptorRef::tokenURI(&self._tokenDescriptor, manager_address, tokenId);
        }

        /**
         * @dev Returns whether `spender` is allowed to manage `tokenId`.
         *
         * Requirements:
         *
         * - `tokenId` must exist.
         */
        fn _isApprovedOrOwner(&self, spender: Address, tokenId: Id) -> bool {
            // require(_exists(tokenId), "ERC721: operator query for nonexistent token");
            // address owner = ERC721.ownerOf(tokenId);
            // return (spender == owner || getApproved(tokenId) == spender || ERC721.isApprovedForAll(owner, spender));
            // let tokenId: Id = Id::U128(tokenId);
            assert!(
                self._check_token_exists(&tokenId).is_ok(),
                "ERC721: operator query for nonexistent token"
            );
            let owner: Address = self.owner_of(tokenId.clone()).unwrap();
            spender == owner || self._allowance(&owner, &spender, &Some(&tokenId))
        }

        #[ink(message)]
        fn positions(
            &self,
            tokenId: Id,
        ) -> (
            Uint96,
            Address,
            Address,
            Address,
            Uint24,
            Int24,
            Int24,
            u128,
            U256,
            U256,
            u128,
            u128,
        ) {
            //Position memory position = _positions[tokenId];
            // require(position.poolId != 0, 'Invalid token ID');
            // PoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];
            let position: Position = self._positions.get(tokenId).unwrap_or(Default::default());
            assert!(position.poolId != 0, "Invalid token ID");
            let poolKey: PoolAddress::PoolKey = self._poolIdToPoolKey.get(position.poolId).unwrap();
            return (
                position.nonce,
                position.operator,
                poolKey.token0,
                poolKey.token1,
                poolKey.fee,
                position.tickLower,
                position.tickUpper,
                position.liquidity,
                position.feeGrowthInside0LastX128.value,
                position.feeGrowthInside1LastX128.value,
                position.tokensOwed0,
                position.tokensOwed1,
            );
        }

        // pub token0: Address,
        // pub token1: Address,
        // pub fee: Uint24,
        // pub tickLower: Int24,
        // pub tickUpper: Int24,
        // pub amount0Desired: Uint256,
        // pub amount1Desired: Uint256,
        // pub amount0Min: Uint256,
        // pub amount1Min: Uint256,
        // pub recipient: Address,
        // pub deadline: Uint256,
        #[ink(message, payable)]
        fn mint(
            &mut self,
            token0: Address,
            token1: Address,
            fee: Uint24,
            tickLower: Int24,
            tickUpper: Int24,
            amount0Desired: U256,
            amount1Desired: U256,
            amount0Min: U256,
            amount1Min: U256,
            recipient: Address,
            deadline: U256,
        ) -> (
            Id, //tokenId
            u128, //liquidity
            U256, //amount0
            U256, //amount1
        ) {
            // IUniswapV3Pool pool;
            // (liquidity, amount0, amount1, pool) = addLiquidity(
            //     AddLiquidityParams({
            //         token0: params.token0,
            //         token1: params.token1,
            //         fee: params.fee,
            //         recipient: address(this),
            //         tickLower: params.tickLower,
            //         tickUpper: params.tickUpper,
            //         amount0Desired: params.amount0Desired,
            //         amount1Desired: params.amount1Desired,
            //         amount0Min: params.amount0Min,
            //         amount1Min: params.amount1Min
            //     })
            // );
            let position_manager_address = ink_env::account_id::<DefaultEnvironment>();
            let addLiquidityParams = AddLiquidityParams {
                token0: token0,
                token1: token1,
                fee: fee,
                recipient: position_manager_address,
                tickLower: tickLower,
                tickUpper: tickUpper,
                amount0Desired: Uint256::new_with_u256(amount0Desired),
                amount1Desired: Uint256::new_with_u256(amount1Desired),
                amount0Min: Uint256::new_with_u256(amount0Min),
                amount1Min: Uint256::new_with_u256(amount1Min),
            };
            // uint128 liquidity,uint256 amount0,uint256 amount1,IUniswapV3Pool pool
            // let liquidity: u128;
            // let amount0: U256;
            // let amount1: U256;

            let (liquidity, amount0, amount1, pool) = self.addLiquidity(addLiquidityParams);
            ink_env::debug_println!(
                "liquidity:{:?}, amount0:{:?}, amount1:{:?}",
                liquidity,
                amount0,
                amount1
            );
            self._nextId = self._nextId + 1;
            let tokenId = Id::U128(self._nextId);
            self._mint_to(recipient, tokenId.clone()).expect("mint error!");
            // _mint(params.recipient, (tokenId = _nextId++));
            // bytes32 positionKey = PositionKey.compute(address(this), params.tickLower, params.tickUpper);
            // let positionKey = PositionKey::compute(address_of_this,params.tickLower, params.tickUpper);
            // (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) = pool.positions(positionKey);
            let position_info =
                PoolActionRef::positions(&pool, position_manager_address, tickLower, tickUpper);
            let feeGrowthInside0LastX128 = position_info.feeGrowthInside0LastX128;
            let feeGrowthInside1LastX128 = position_info.feeGrowthInside1LastX128;

            // // idempotent set
            // uint80 poolId =
            //     cachePoolKey(
            //         address(pool),
            //         PoolAddress.PoolKey({token0: params.token0, token1: params.token1, fee: params.fee})
            //     );
            let pool_key = PoolAddress::PoolKey {
                token0: token0,
                token1: token1,
                fee: fee,
            };
            let poolId = self.cachePoolKey(position_manager_address, pool_key);

            // _positions[tokenId] = Position({
            //     nonce: 0,
            //     operator: address(0),
            //     poolId: poolId,
            //     tickLower: params.tickLower,
            //     tickUpper: params.tickUpper,
            //     liquidity: liquidity,
            //     feeGrowthInside0LastX128: feeGrowthInside0LastX128,
            //     feeGrowthInside1LastX128: feeGrowthInside1LastX128,
            //     tokensOwed0: 0,
            //     tokensOwed1: 0
            // });
            let position = Position {
                nonce: 0,
                operator: ADDRESS0.into(),
                poolId: poolId,
                tickLower: tickLower,
                tickUpper: tickUpper,
                liquidity: liquidity,
                feeGrowthInside0LastX128: feeGrowthInside0LastX128,
                feeGrowthInside1LastX128: feeGrowthInside1LastX128,
                tokensOwed0: 0,
                tokensOwed1: 0,
            };
            self._positions.insert(tokenId.clone(), &position);
            self.env().emit_event(IncreaseLiquidity {
                tokenId:tokenId.clone(),
                liquidity,
                amount0,
                amount1,
            });
            // ink_lang::codegen::EmitEvent::<PositionMangerContract>::emit_event(self.env(), IncreaseLiquidity {
            //         tokenId,
            //         liquidity,
            //         amount0,
            //         amount1,
            //     });
            // emit IncreaseLiquidity(tokenId, liquidity, amount0, amount1);
            (tokenId.clone(), liquidity, amount0, amount1)
        }

        #[ink(message, payable)]
        #[modifiers(isAuthorizedForToken(tokenId))]
        fn collect(
            &mut self,
            tokenId: Id,
            recipient: Address,
            amount0Max: u128,
            amount1Max: u128,
        ) -> (U256, U256){
            let params = CollectParams{
                tokenId,
                recipient,
                amount0Max,
                amount1Max,
            };
            // require(params.amount0Max > 0 || params.amount1Max > 0);
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$1");
            assert!(params.amount0Max > 0 || params.amount1Max > 0,"input must be position!");
            // // allow collecting to the nft position manager address with address 0
            // address recipient = params.recipient == address(0) ? address(this) : params.recipient;
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$2");
            let recipient:Address = if params.recipient == ADDRESS0.into(){
                ink_env::account_id::<DefaultEnvironment>()
            }else{
                params.recipient
            };
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$3");
            // Position storage position = _positions[params.tokenId];
            let mut position:Position = self._positions.get(params.tokenId.clone()).expect("tokenId not exist!");
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$4");
            // PoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];
            let poolKey:PoolAddress::PoolKey = self._poolIdToPoolKey.get(position.poolId).expect("pooId not exist!");
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$5");
            // IUniswapV3Pool pool = IUniswapV3Pool(PoolAddress.computeAddress(factory, poolKey));
            let factoryAddress = self.immutable_state.factory;
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$6");
            let pool: Address =
                FactoryRef::get_pool(&factoryAddress, poolKey.fee, poolKey.token0, poolKey.token1);
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$7");
            // (uint128 tokensOwed0, uint128 tokensOwed1) = (position.tokensOwed0, position.tokensOwed1);
            let (mut tokensOwed0,mut tokensOwed1) = (position.tokensOwed0, position.tokensOwed1);
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$8");
            // // trigger an update of the position fees owed and fee growth snapshots if it has any liquidity
            // if (position.liquidity > 0) {
            //     pool.burn(position.tickLower, position.tickUpper, 0);
            //     (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) =
            //         pool.positions(PositionKey.compute(address(this), position.tickLower, position.tickUpper));
            let address_of_this = ink_env::account_id::<DefaultEnvironment>();
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$9");
            if position.liquidity > 0 {
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$10");
                PoolActionRef::burn(&pool,position.tickLower, position.tickUpper, 0);
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$11");
                let position_info =
                    PoolActionRef::positions(&pool,address_of_this, position.tickLower, position.tickUpper);
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$11");
                let feeGrowthInside0LastX128 = position_info.feeGrowthInside0LastX128;
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$12");
                let feeGrowthInside1LastX128 = position_info.feeGrowthInside1LastX128;
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$13");
                //     tokensOwed0 += uint128(
                //         FullMath.mulDiv(
                //             feeGrowthInside0LastX128 - position.feeGrowthInside0LastX128,
                //             position.liquidity,
                //             FixedPoint128.Q128
                //         )
                //     );
                tokensOwed0+=FullMath::mulDiv(
                                feeGrowthInside0LastX128.value - position.feeGrowthInside0LastX128.value,
                                U256::from(position.liquidity),
                                U256::from(FixedPoint128::Q128)
                            ).as_u128();
                            ink_env::debug_println!("$$$$$$$$$$$$$$$$$14");
                //     tokensOwed1 += uint128(
                //         FullMath.mulDiv(
                //             feeGrowthInside1LastX128 - position.feeGrowthInside1LastX128,
                //             position.liquidity,
                //             FixedPoint128.Q128
                //         )
                //     );
                tokensOwed1+=FullMath::mulDiv(
                    feeGrowthInside1LastX128.value - position.feeGrowthInside1LastX128.value,
                    U256::from(position.liquidity),
                    U256::from(FixedPoint128::Q128)
                ).as_u128();
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$15");
                //     position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
                //     position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
                position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
                position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$16");
            }

            // // compute the arguments to give to the pool#collect method
            // (uint128 amount0Collect, uint128 amount1Collect) =
            //     (
            //         params.amount0Max > tokensOwed0 ? tokensOwed0 : params.amount0Max,
            //         params.amount1Max > tokensOwed1 ? tokensOwed1 : params.amount1Max
            //     );
            let (amount0Collect, amount1Collect) = (
                    if params.amount0Max > tokensOwed0{
                        tokensOwed0
                    }else{
                        params.amount0Max
                    },
                    if params.amount1Max > tokensOwed1 {
                        tokensOwed1
                    }else{
                        params.amount1Max
                    }
                );
                ink_env::debug_println!("$$$$$$$$$$$$$$$$$17");
            // // the actual amounts collected are returned
            // (amount0, amount1) = pool.collect(
            //     recipient,
            //     position.tickLower,
            //     position.tickUpper,
            //     amount0Collect,
            //     amount1Collect
            // );
            let (amount0, amount1) = PoolActionRef::collect(&pool,recipient,
                    position.tickLower,
                    position.tickUpper,
                    amount0Collect,
                    amount1Collect);
                    ink_env::debug_println!("$$$$$$$$$$$$$$$$$18");
            let amount0 = U256::from(amount0);
            let amount1 = U256::from(amount1);
            // // sometimes there will be a few less wei than expected due to rounding down in core, but we just subtract the full amount expected
            // // instead of the actual amount so we can burn the token
            // (position.tokensOwed0, position.tokensOwed1) = (tokensOwed0 - amount0Collect, tokensOwed1 - amount1Collect);
            position.tokensOwed0 = tokensOwed0 - amount0Collect;
            position.tokensOwed1 = tokensOwed1 - amount1Collect;
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$19");
            self._positions.insert(params.tokenId.clone(),&position);
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$20");
            // emit Collect(params.tokenId, recipient, amount0Collect, amount1Collect);
            self.env().emit_event(Collect {
                tokenId:params.tokenId.clone(),
                recipient,
                amount0,
                amount1,
            });
            // ink_lang::codegen::EmitEvent::<PositionMangerContract>::emit_event(self.env(), Collect {
            //     tokenId:params.tokenId,
            //     recipient,
            //     amount0,
            //     amount1,
            // });
            ink_env::debug_println!("$$$$$$$$$$$$$$$$$21");
            (amount0,amount1)
        }

        #[ink(message, payable)]
        #[modifiers(isAuthorizedForToken(tokenId))]
        fn burn(&mut self,tokenId:Id){
            // Position storage position = _positions[tokenId];
            let position:Position = self._positions.get(tokenId.clone()).expect("tokenId not exist!");
            // require(position.liquidity == 0 && position.tokensOwed0 == 0 && position.tokensOwed1 == 0, 'Not cleared');
            ink_env::debug_println!("position.liquidity is:{:?} && position.tokensOwed0 is:{:?} && position.tokensOwed1 is:{:?}",position.liquidity , position.tokensOwed0 , position.tokensOwed1);
            assert!(position.liquidity == 0 && position.tokensOwed0 == 0 && position.tokensOwed1 == 0, "Not cleared");
            // delete _positions[tokenId];
            self._positions.remove(tokenId.clone());
            // _burn(tokenId);
            let caller = ink_env::caller::<DefaultEnvironment>();
            self._burn_from(caller,tokenId.clone()).expect("burn token failed");
        }

        #[ink(message)]
        fn getApproved(&self,tokenId:Id)->Address{
            //require(_exists(tokenId), 'ERC721: approved query for nonexistent token');
            assert!(self._check_token_exists(&tokenId).is_ok(), "ERC721: approved query for nonexistent token");
            //return _positions[tokenId].operator;
            let position:Position = self._positions.get(tokenId.clone()).expect("tokenId not exist!");
            position.operator
        }
        
    }

    /// Event emitted when a token transfer occurs.
    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        from: Option<AccountId>,
        #[ink(topic)]
        to: Option<AccountId>,
        #[ink(topic)]
        id: Id,
    }

    /// @notice Emitted when tokens are collected for a position NFT
    /// @dev The amounts reported may not be exactly equivalent to the amounts transferred, due to rounding behavior
    /// @param tokenId The ID of the token for which underlying tokens were collected
    /// @param recipient The address of the account that received the collected tokens
    /// @param amount0 The amount of token0 owed to the position that was collected
    /// @param amount1 The amount of token1 owed to the position that was collected
    // event Collect(uint256 indexed tokenId, address recipient, uint256 amount0, uint256 amount1);
    #[ink(event)]
    pub struct Collect{
        #[ink(topic)]
        tokenId:Id,
        recipient:AccountId,
        amount0:U256,
        amount1:U256,
    }
    /// Event emitted when a token approve occurs.
    #[ink(event)]
    pub struct Approval {
        #[ink(topic)]
        from: AccountId,
        #[ink(topic)]
        to: AccountId,
        #[ink(topic)]
        id: Option<Id>,
        approved: bool,
    }

    /// @notice Emitted when liquidity is increased for a position NFT
    /// @dev Also emitted when a token is minted
    /// @param tokenId The ID of the token for which liquidity was increased
    /// @param liquidity The amount by which liquidity for the NFT position was increased
    /// @param amount0 The amount of token0 that was paid for the increase in liquidity
    /// @param amount1 The amount of token1 that was paid for the increase in liquidity
    // event IncreaseLiquidity(uint256 indexed tokenId, uint128 liquidity, uint256 amount0, uint256 amount1);
    #[ink(event)]
    pub struct IncreaseLiquidity {
        #[ink(topic)]
        tokenId: Id,
        liquidity: u128,
        amount0: U256,
        amount1: U256,
    }

    /// @notice Emitted when liquidity is decreased for a position NFT
    /// @param tokenId The ID of the token for which liquidity was decreased
    /// @param liquidity The amount by which liquidity for the NFT position was decreased
    /// @param amount0 The amount of token0 that was accounted for the decrease in liquidity
    /// @param amount1 The amount of token1 that was accounted for the decrease in liquidity
    #[ink(event)]
    pub struct DecreaseLiquidity {
        #[ink(topic)]
        tokenId: Id,
        liquidity: u128,
        amount0: U256,
        amount1: U256,
    }

    #[ink(event)]
    pub struct TestEvent {
        #[ink(topic)]
        tokenId: Id,
    }

    impl PSP34Internal for PositionMangerContract {

        fn _approve_for(&mut self, to: AccountId, id: Option<Id>, approved: bool) -> Result<(), PSP34Error> {
            let mut caller = ink_env::caller::<DefaultEnvironment>();
            if id.is_some() {
                let id = id.unwrap();
                let maybe_owner = self.owner_of(id.clone());

                if maybe_owner.is_none() {
                    return Err(PSP34Error::TokenNotExists)
                }
                let owner = maybe_owner.unwrap();

                if approved && owner == to {
                    return Err(PSP34Error::SelfApprove)
                }

                if owner != caller && !self._allowance(&owner, &caller, &None) {
                    return Err(PSP34Error::NotApproved)
                };
                caller = owner;

                // get position and change the operator.
                let mut position:Position = self._positions.get(id.clone()).expect("tokenId not exist!");
                if approved {
                    position.operator = to;
                    self._positions.insert(id.clone(),&position);
                } else {
                    position.operator = ADDRESS0.into();
                    self._positions.insert(id.clone(),&position);
                }
                self._emit_approval_event(caller, to, Some(id.clone()), approved);
            }
            
            Ok(())
        }

        fn _emit_transfer_event(&self, from: Option<AccountId>, to: Option<AccountId>, id: Id) {
            self.env().emit_event(Transfer { from, to, id });
        }

        fn _emit_approval_event(
            &self,
            from: AccountId,
            to: AccountId,
            id: Option<Id>,
            approved: bool,
        ) {
            self.env().emit_event(Approval {
                from,
                to,
                id,
                approved,
            });
        }
    }
}
