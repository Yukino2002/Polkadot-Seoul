#![cfg_attr(not(feature = "mock"), no_std)]
#![feature(proc_macro_hygiene)]
extern crate alloc;
extern crate common;
extern crate ontio_std as ostd;
use common::CONTRACT_COMMON;
use ostd::abi::{Sink, Source};
use ostd::contract::wasm;
use ostd::database;
use ostd::prelude::*;
use ostd::runtime;
use ostd::runtime::check_witness;
use ostd::types::{Address, U128};

const MP_CONTRACT_ADDRESS: Address = ostd::macros::base58!("AdD2eNZihgt1QSy6WcxaZrxGUQi6mmx793");
const DTOKEN_CONTRACT_ADDRESS: Address =
    ostd::macros::base58!("AQJzHbcT9pti1zzV2cRZ92B1i1z8QNN2n6");

const KEY_MP_CONTRACT: &[u8] = b"01";
const KEY_DTOKEN_CONTRACT: &[u8] = b"02";

fn get_mp_contract_addr() -> Address {
    database::get::<_, Address>(KEY_MP_CONTRACT).unwrap_or(MP_CONTRACT_ADDRESS)
}

fn set_mp_contract_addr(mp: &Address) -> bool {
    assert!(check_witness(CONTRACT_COMMON.admin()));
    database::put(KEY_MP_CONTRACT, mp);
    true
}

fn get_dtoken_contract_addr() -> Address {
    database::get::<_, Address>(KEY_DTOKEN_CONTRACT).unwrap_or(DTOKEN_CONTRACT_ADDRESS)
}

fn set_dtoken_contract_addr(dtoken: &Address) -> bool {
    assert!(check_witness(CONTRACT_COMMON.admin()));
    database::put(KEY_DTOKEN_CONTRACT, dtoken);
    true
}

fn init(mp: &Address, dtoken: &Address) -> bool {
    assert!(check_witness(CONTRACT_COMMON.admin()));
    database::put(KEY_MP_CONTRACT, mp);
    database::put(KEY_DTOKEN_CONTRACT, dtoken);
    true
}

pub fn buy_use_token(
    resource_id: &[u8],
    n: U128,
    buyer_account: &Address,
    payer: &Address,
) -> bool {
    //call market place
    let mp = get_mp_contract_addr();
    if let Some(res) =
        wasm::call_contract(&mp, ("buyDToken", (resource_id, n, buyer_account, payer)))
    {
        let mut source = Source::new(res.as_slice());
        let token_ids: Vec<Vec<u8>> = source.read().unwrap();
        //call dtoken
        let dtoken = get_dtoken_contract_addr();
        for token_id in token_ids.iter() {
            verify_result(wasm::call_contract(
                &dtoken,
                ("useToken", (buyer_account, token_id, n)),
            ));
        }
        return true;
    }
    panic!("buy_use_token failed")
}

pub fn buy_reward_and_use_token(
    resource_id: &[u8],
    n: U128,
    buyer_account: &Address,
    payer: &Address,
    reward_uint_price: U128,
) -> bool {
    //call market place
    let mp = get_mp_contract_addr();
    if let Some(res) = wasm::call_contract(
        &mp,
        (
            "buyDTokenReward",
            (resource_id, n, buyer_account, payer, reward_uint_price),
        ),
    ) {
        let mut source = Source::new(res.as_slice());
        let token_ids: Vec<Vec<u8>> = source.read().unwrap();
        //call dtoken
        let dtoken = get_dtoken_contract_addr();
        for token_id in token_ids.iter() {
            verify_result(wasm::call_contract(
                &dtoken,
                ("useToken", (buyer_account, token_id, n)),
            ));
        }
        return true;
    }
    false
}

fn verify_result(res: Option<Vec<u8>>) {
    if let Some(r) = res {
        let mut source = Source::new(r.as_slice());
        let r: bool = source.read().unwrap();
        assert!(r);
    } else {
        panic!("call contract failed")
    }
}

#[no_mangle]
fn invoke() {
    let input = runtime::input();
    let mut source = Source::new(&input);
    let action: &[u8] = source.read().unwrap();
    let mut sink = Sink::new(12);
    match action {
        b"migrate" => {
            let (code, vm_type, name, version, author, email, desc) = source.read().unwrap();
            sink.write(CONTRACT_COMMON.migrate(code, vm_type, name, version, author, email, desc));
        }
        b"setDTokenContractAddr" => {
            let dtoken = source.read().unwrap();
            sink.write(set_dtoken_contract_addr(dtoken));
        }
        b"setMpContractAddr" => {
            let mp = source.read().unwrap();
            sink.write(set_mp_contract_addr(mp));
        }
        b"getDToken" => {
            sink.write(get_dtoken_contract_addr());
        }
        b"getMP" => {
            sink.write(get_mp_contract_addr());
        }
        b"init" => {
            let (mp, dtoken) = source.read().unwrap();
            sink.write(init(mp, dtoken));
        }
        b"buyAndUseToken" => {
            let (resource_id, n, buyer_account, payer) = source.read().unwrap();
            sink.write(buy_use_token(resource_id, n, buyer_account, payer));
        }
        b"buyRewardAndUseToken" => {
            let (resource_id, n, buyer_account, payer, unit_price) = source.read().unwrap();
            sink.write(buy_reward_and_use_token(
                resource_id,
                n,
                buyer_account,
                payer,
                unit_price,
            ));
        }
        _ => {
            let method = str::from_utf8(action).ok().unwrap();
            panic!("openkg contract, not support method:{}", method)
        }
    }
    runtime::ret(sink.bytes());
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
