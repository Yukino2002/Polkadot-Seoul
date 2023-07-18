#![no_std]
#![allow(non_snake_case)]
#![feature(proc_macro_hygiene)]



use wasm_mid;
use wee_alloc;
#[global_allocator]
static ALLOC: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;


// 合约1
pub mod contract1{
    use wasm_std::types::{U256, Address};
    use wasm2ct::types::*;
    use wasm2ct_derive::gen_contract;
    use wasm_std::String;
    use wasm2ct::types::{Stream,Sink};    
    #[gen_contract(true)]
    pub trait Interface{
        fn constructor(&mut self,_list:String)->String;
        fn add_num(&mut self,a:u32,b:u32)->u32;
        fn add_str(&mut self,a:String,b:String)->String;
        fn ret_tuple(&mut self)->(String,u32);
        fn ret_list(&mut self)->[u8;3];
        fn save_str(&mut self,a:String)->bool;
        fn get_str(&mut self)->String;
    }
    
}

// 合约2
pub mod contract2{
    use wasm_std::types::{U256, Address};
    use wasm2ct::types::*;
    use wasm2ct_derive::gen_contract;
    use wasm_std::String;
    use wasm2ct::types::{Stream,Sink};
    use crate::contract1::Interface as Interface1;     
    #[gen_contract(false)]
    pub trait Interface{
        fn add_num(&mut self,a:u32,b:u32,c:Address)->u32;
        fn ret_addr(&mut self,a:Address)->Address;
    }
    pub struct Contract2;
    impl Interface for Contract2{
        fn add_num(&mut self,a:u32,b:u32,c:Address)->u32{
            let mut token = crate::contract1::Outer::new(c);
            let tar = token.add_num(a,b);
            tar
        }
        fn ret_addr(&mut self,a:Address)->Address{
            a
        }        
    }
}





use wasm2ct::ContractInterface;

#[no_mangle]
pub fn call() {
    let mut endpoint = contract2::Contract::new(contract2::Contract2{});
    // Read http://solidity.readthedocs.io/en/develop/abi-spec.html#formal-specification-of-the-encoding for details
    wasm_mid::ret(&endpoint.call(&wasm_mid::input()));
}

#[no_mangle]
pub fn deploy() {
    let mut endpoint = contract2::Contract::new(contract2::Contract2{});
    endpoint.deploy(&wasm_mid::input());
}