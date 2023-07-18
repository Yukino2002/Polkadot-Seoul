use std::collections::HashMap;
use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::collections::{LazyOption, LookupMap, UnorderedMap, UnorderedSet, Vector};
use near_sdk::json_types::{Base64VecU8, U128};
use near_sdk::serde::{Deserialize, Serialize};
use near_sdk::{
    env, near_bindgen, AccountId, Balance, CryptoHash, PanicOnDefault, Promise, PromiseOrValue,
};
use std::convert::TryInto;

use crate::internal::*;
pub use crate::metadata::*;
pub use crate::mint::*;
pub use crate::nft_core::*;
pub use crate::approval::*;
pub use crate::royalty::*;
pub use crate::events::*;

mod internal;
mod approval; 
mod enumeration; 
mod metadata; 
mod mint; 
mod nft_core; 
mod royalty; 
mod events;

/// This spec can be treated like a version of the standard.
pub const NFT_METADATA_SPEC: &str = "nft-1.0.0";
/// This is the name of the NFT standard we're using
pub const NFT_STANDARD_NAME: &str = "nep171";

#[near_bindgen]
#[derive(BorshDeserialize, BorshSerialize, PanicOnDefault)]
pub struct Contract {
    //contract owner
    pub owner_id: AccountId,

    //keeps track of all the token IDs for a given account
    pub tokens_per_owner: LookupMap<AccountId, UnorderedSet<TokenId>>,

    //keeps track of the token struct for a given token ID
    pub tokens_by_id: LookupMap<TokenId, Token>,

    //keeps track of the token metadata for a given token ID
    pub token_metadata_by_id: UnorderedMap<TokenId, TokenMetadata>,

    pub remain_ids: Vector<String>,

    //keeps track of the metadata for the contract
    pub metadata: LazyOption<NFTContractMetadata>,
    pub contributor_0: Vector<AccountId>,
    pub contributor_4: Vector<AccountId>,
    pub contributor_7: Vector<AccountId>,
}

/// Helper structure for keys of the persistent collections.
#[derive(BorshSerialize)]
pub enum StorageKey {
    TokensPerOwner,
    TokenPerOwnerInner { account_id_hash: CryptoHash },
    TokensById,
    TokenMetadataById,
    NFTContractMetadata,
    TokensPerType,
    TokensPerTypeInner { token_type_hash: CryptoHash },
    TokenTypesLocked,
    Contributor0,
    Contributor4,
    Contributor7,
    RemainIds,
}

#[near_bindgen]
impl Contract {
    /*
        initialization function (can only be called once).
        this initializes the contract with metadata that was passed in and
        the owner_id. 
    */
    #[init]
    pub fn new(owner_id: AccountId) -> Self {
        //create a variable of type Self with all the fields initialized. 
        let mut this = Self {
            //Storage keys are simply the prefixes used for the collections. This helps avoid data collision
            tokens_per_owner: LookupMap::new(StorageKey::TokensPerOwner.try_to_vec().unwrap()),
            tokens_by_id: LookupMap::new(StorageKey::TokensById.try_to_vec().unwrap()),
            token_metadata_by_id: UnorderedMap::new(
                StorageKey::TokenMetadataById.try_to_vec().unwrap(),
            ),
            //set the owner_id field equal to the passed in owner_id. 
            owner_id,
            metadata: LazyOption::new(
                StorageKey::NFTContractMetadata.try_to_vec().unwrap(),
                Some(&&NFTContractMetadata {
                    spec: "nft-1.0.0".to_string(),
                    name: "TerraSpaces".to_string(),
                    symbol: "TS".to_string(),
                    icon: Some("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAApXUlEQVR4nIW7aZgkV3Xn/bv3xpKRa2VVZe1V3dX7Ur1pl1o7i4RlgS2QATGYwcaIzZjNYNmMwQxgwAyGwTC8tsEDw2YEg5BABiQEEtKAlpbU6m71vnd17VvumRFxz3yI6pYEzPNmPfVkRGbkjTj3nPM/u1JanwWyACIWAKU1yUvx3EuSc6Mgluc+tgKuBt9AJYS0g7gGlhpc0nUpL+6+gU8c/Bg256DcFNQjcAwISKOFHu5B+S72zAKqMwNaQzMGpZJ/UZBxk+OGhayHbYXQqHL99pczPz/JnvGnobeEtCJspcwVG69mbmGOg7MHcXt7kWaIRDHKdbDtEKyQXjNCOLdUVUrr51EDSsCKRRnNb78UaMA+b080ycNpBaFFjAUFWzLbGMuOoSx8c+obqMAH0dC2IAKugyl1I3GENFvJWmkfWhG0LLgGlE7W9Z3kRrEgxJh8Ecc4rE31c7I2QTWuonCx1hIUOunzOpiqTtNybPJMsYBSiLU4mQwAOpchrtTQQAVArEXE8vqhNzIcjCDW/jb9CMS/ce4ub1QrSjYjFAqqwNvW/wVPze/im+NfR2WChKv1FkiMhC2UZ3BWDSHzZez8Eqo7C7UWUmmAshBFYOPkuNJMfqtipFxDtdo4fb3sOfQI5fo8TleReGoWv6MDUypybN+vaaTAyeWw5RpEMcQWaYU4hSymkKV5+CRxu1lRSuuyWJsD+MiFn2LX1KM8Mv0Qs+EsSqvf2oIXqsXzpECDtGOKqzfQO7yR4w/dS8sNIZ+CmTpKG9AKiSLcdatR2QztJ59BpVOQT8NcHbRJOI9K1ARQEajBAtKMsROLZK68mHByhvbRE7jb1mIXqsSTc2Quu5BwZo728dOYkR5oxUgrRnkO0g4T7e3KYytNEFAZH2lHFYPIHZ09w35v10oGbDf3TtzDXGs2UQH5bXp/azNUcpFEMYWRtfjZAouTJ6gtzoCn8fBR7RiLRVmL7i6ifB+7VIGwCZ4L9TbENhF3keSeIgm+GJXschSjAg9isPU64iZYJUs1nM4OAOLFJVTgJvjSChOuRxEmm0YHPnGlvkyXgFgQ2tqgKK3aTKZ/iC8c+ixzzdkEBM8hg/xu0p/7UiFxohfpCy6hXW+wdOooynOgEdPf7uLWgddiRCEKnPVrsLNzxGfOogdLieo0msvgEycPZmNohcmxATs+i1QaqHxA+/ARoqUFTG+R6OBJlFI4fSWazzyLDVvoYg67UIV2CFqQsI3JBJhiDinXAQtasAtVlKNRhct3ltsHD+fai/PEEqHUb4Kf+h1SsLwrKuG8KRbx1q+nsftpaDUh40OlxWhuNa8dfh1ff/Z/ML4mQBXyxLsPgOegCgEyuZQAqKMTYHV1cr9GiBroQCKLTC+Quvhi7MIS7SNH0EM9SGiRqXlSF+3A1hu0nz2Is3UdxEJ8ZjZRq9giVtClHHaxAQLO6h7i8UWk0cJft4rm1FRFeStWlKOZmZyt159n/v5fhD9/DwRZFmmdL0CjRTQxAY5CGcPL+m9CtyzTjSkeyxxGu2lUtUk8vwCBD1qh6hGYZaQ/p25KoTwXWTa3ynMw2SK23cC2G6jQImhMLo8p5IjLZQSLCoLE3FWbiNbobIAKUsSLZZTvgjYoLISCLuQJ2xW6w0xFt0+e5LeIV/8/xJNYDbRCdxexi4tEExOoVAoiIaOzvHjNzZxsn+KxxcdwR1bBfI14dh6VzUPUgGYdggx4Pjhe8q5cVCqAQgaqMeCgOvKEp04TL1WTe5Ub6EwWM9hL69kjiFHowV7iiUWk2oKUD7FF5zPofBrqITrlotMu8eQSujOPdjWcOEFPqgOllCqjVO4815/PefU7dkFpJGxhukv427dSv/9nyeWuh4RtcqUB1m24gqd+9QNswUNnO5Czi6hcgPU9mD7LW9a+k363mw8d+xD43Wi1jDm+AaWw83W81UNgNO2DJzGrSkitjT07T2r7Bmy7TfvwCUxvidg2oN7EpLoQZZE4xh3uxi7ViRdqmMECdroC7Qh/2xoa+/ai5uq8+5L38qMzP64opXQZRe4cV5U2aG0QpZGwvazxgnI8MAZp1TG9PehcHsI20fgEWAvGRXfl8cXHjRRLtUnI5lHKQCtElALV5rL0GGPBevbXD/FI81kwaUChjEaWza5yXZTrIq0QOedrRBbCEKe7MwHOKCKSFiukhw6TYbc9BTqF9h1AIeGyH2FUcn1gkGad/sIwBTeFM73IpK5VnESdLQpF1snStG3AII5G5TtR9QhxNLZWQ2FRro+7ehVSq9HafQQT5LBxjHY96C9RX6jBUg0zMApti0QWenxUGDPsFrmg+zq+OXsPi6lpnI6NiLKJpHkGIlCuQWVS2HIDldeoQhpZaqJSDqa3QHxyCluZxXoupAJ29F3PJc4oz5a/S5zO4Hg+dqGW+CaORipNdN5HBS7xwUNkh0dJh/DkrvthpA+llC6L2Byu4R2X/BV37/kWp8rH0Dh0/uvnyL74RpwWzH3yv7Hwb1/C37yB1t5nX6AVxs2QWreK2r499Pztf6HrdW8gDkNA0FrTimNWpTJ0OR6PNKdJGZ+MyaCIUahziofSGoWAgF52hLCC67q06g3cumX2/p9w5EtfRnWUePV/uQN35yYerVfpM1liiRK31yyDqlboYpbYxhT9HGd+/At2v+42aFUwawaR6cWKAso3Db08l3M72FXbxWJ5noatclH7lRRfcjOHfnoL7VqI8gyVL/0r8//8eZROgU0e2KQ9tOdRNgtcOv+HbEtdzrOf2sL41b2kn7dJRSBuQUOBpxOCDaAMROq8M/kc/Cyfe0AdWLML5j//HR5o3MnQn7yFdddeRd54LGmoa/CfD1PL7w2guVRmMJUnbLR54Pbbqdz7Q1TGQ6kYjFtRQZAr39Z/W64tIf/r+FfodYd48HU/plHL8+07H+TpD23kzFvGkPFpKqkGutEmWtOLOArdjpCci27GXKxLDGYUx2swf6BKbmoRrINoRSGlKW8s0uxwCHjOyMQaoqqQfmYBFcfgmAR3tcJpxXjdKcJtWQaAOYFdjWk63DQr3CxZYBHQAp4CicGdYdmDhLhfMfhQm6EPPMu+9Cm+WvlHGuOHMdkMUqlgp6ZxVq+oODde9sd854lvU6nMkXEKTIXj3LX/Pj5w67s48+QFND9xGHvjWmYjgzfn4Jo0/j8dpdHhQNolmqyjUwaTL5M2PWwZylO6v8bafz1DsyvNnFmkfHiBw+9YT+WSAl7LIgo87dOd6aLoK0Y/NYMebxJ3uCilaTYbVBtLzIxk2PfmbmaCkAWJ6DcBw5kc2eYScRRR8hWCwlhFToTm+g7ilCIyMFCBt/y0zOSw8Le7PkSjMo471Ed0egrKVfzLLyDcsx/V3TVcbrVquUp1HgCXAI3Pr1/zc0ZKG/mXz9/LoTcPcfiTF1M8GFLt0Ox8zyNc/ECbxkA32raxAku2wbHJs2ztSbNpRx/tvEdLWlxc2soTh+sc2HeSbsfBmiQsnWwushDMcMP6YSh62JgkdKVNT98QPc4gP3zqBI35JZpEBI5Db7aDuB3TsDHiKbRxqJsWzWMnGb9+iKP/fYygrqAHdn/th5z58MeoBU2qrQrGuETTs6AUuiuLVKrYSi3BACAHilXZ1TSjkLPNk9zQ9wf8+Pbv8f2fPsojvzrC6YdfwcLKPENWWKdDLvrP96JFI6UsKhRSKY9PP/oZ7jlyN8XcEBWnShfdfOXSL5DrSVOpVljOt5DKptg1s4u/PvxxUpUMTgPwNCqEhlfhms0v4309b6JtWxjXYNpgfUXkxdiKRTsK5RqisElGCd0yykc+tBKzLkOHwMHpBR545atg9iTUY/ysh41bxGfn0UNdSKtFfGYCPdJXQSlVBmQkvULuvvInssasFI0WRvrku7f8UOR9Ip/Xd8u7rn9Ydiy05aInJmV0akbSf/Vu0SCuUxBXZcRXaUmhJFsalsyObQLIn61+m3x862cEHHF1VjydFxcjweqVktq8VrK6S1LpkgTZHgkIJLd1TPJbt0maDnGz3eIXe8TFFX/LZgku2CYuGfFHhsVbOSKpjhXCgJaPrnyPfP1LIjeJyNtnRV4jIn2f+5JQHBFveIO4mzaKyXaKcTLi77xQdDoQQPS6YdHpVFkB5ct6r8qt7djA02d/zb5gnEK2h4XTh9jiXczTb3mI3fun+em9e9hz5zaeuCiLmWvSWOMwd9MtNB55COMViNoNgi0biOdniafm6Ru7gL5KwPzMGQ5XThCIm5il9f3E1ToyV0XHCgnbiLWYVX3QDlGVJlKPicMaTlcXprcbO78EVpBmAx0EuLjMt2bYkdnIV3f+gE9+updsVjBZxUNPPcveV70Sxwhoi11YQnkaFTjY+cUkwixkkIUKqh1VdDHfi+d6LMaL7KnswekrEbUadIY59tQe5dO//AI7dgwxsDbPuk8ep+ilyFRqxK9+B41jxxDlEYtFpVPYlEuowWJx01l2V/dyuHyAQDtYE2E7PSQwxJPzxPUqoW0QuRabM9hiQLiwSGtplkiaSCYglojYhXB+iXBuDutq4qUG7WYLqPN3+bfx6Ct6qfRY0hXF0SYc+tTH4OxZMIKNmki1hhAjSrDlapJ8CSOoNaGYgxe94l1lx08JIN7YenGzWfFA8k6PeGjpzqyU4x+elCO3Tshn+aG8+79NyFizIT3XvyoRJSctJt8lwSUXCyAmlxdv65bkWBkxyhEN4q1ZIf72jaJBNEaMMqJA3O0bxLtosygQjRatjGiQ9NVXSmpL8rnbURC31C0eGcnl+gUfubXrBnn6zxryspOR3H5U5LamSO+Xvy2QFmfjBtHdfaJMWvRwnyid3MtsGhGlVXK8fkRUNl0mk+sq+z09Qm9BdJASgxJX+eLjSGnFBqGUlT/d8FaRD8Ty5bUPyJ9n/1227R+XYmtOVh86LSu+d7doLxCdSktqxw4xxU5RQSDKmGSDQJwNo2K6i6KzGdFKiwJRWouzcZXogZKodOr8gykQM9ArTk9JtOuJdh1xfF9cLy2pbFHcVIekMxn52djd8s57RK5qWrltSuTis01h83Yh0yGm2CdmcEDM2hWiPE9UyhfdVxTlOaIHusSsGxYV+KKgrGvNeVphDR1ZpNFEUFgJkcCh3eFSiDv42oF/48HTD/Oi6zeyUD2J//4HKM7FZFYOkb/lZjre8EZss07ciog9hTSSBIRSCvJJqltabWy1dj7BpEpFMBqZmEXqzSQPkMmgOjtAK6LpGSRso5RG2gKicLRH2F7kre4rmL/xxdx9XUR6EWZ64NAXPg37nsZ0FpBGPXEjW01otyHrn0+zq5SPNENotJZzkJduK6uUL4AopRKuea54K4fFA+mkQ+hPy3UDN4n8jcgjN5+Wd+l/k/dnviov/sYRWXVmTlbtekaCLQnydwUl6cz2J+sU82LWr0jWRonSCff1QEn0muHzHD93X3fDOvG2jSXXpz3RxbQYjDhOIIHpEPBkVXFIdl++V277cSw3n4zktpMia3+2R0hnRaVyor28mE2joruLydqdGVFqWbLGVooKvORzxwhQNrKwdAdR7CtrEcAZHkB3dRAfP4PuzGMDj3TV5cDCQfp0P3+47VpuvGA7M0fr7O1tU1/h0i4VmJ04zR89aRjt386Bmd3EK7qTLPCpySTNJpL8dwTQjmBq7nleO+jBXuzsHHY6yUarWKAVo5RBi8ZJBYSZCp9N30Hjtlu4/zrL6HHDdAme+Ms3Yg/uw+noQlwLC1Wk1UwyzNUWFHOojixydg5a7eS5YstwbkVbU28mqAiolA/5DHG5hhiVoG7UxjbaFMnx1ofeztV33cD+2n66ezLEm3vwO3vJnG6w+fa3Uth6BY+cvI9aVqOCdBKH23MVJZ3UB0IL1cby50lgoLo7k82p1JIiCSTVpxgUGs9JUQtnuNZsY+1Nb+aTfw4MGaaug91f/Rei++4FIJqdSPKIzei5rLKjk7pAGEOzvVwgETJBnnX923FQChEBx+COrSN6Yi+CoPs7sJNLIBCaNMQVvI48xwqLHDt7gvHpgA1fPMsjF3czEPSwdTDNP/1RkdaueUxxCHvg9HLI50AcoYZ7USkPOXz6fDQkIjgb1qJ9j/bufUlobJIKE1qjlEaJxgYG3YRXZd7Kt6dniT56gItrW3jY/TfO1h6m6447kHw3jnaZ/4dPEzszEDlQrqNW92FPTyJlUI5GIotBsfNFb+DRX34HgLKzcZU42zcmiJl2RRUCUQrRWic6CJLfukm8/l7ZGGyUs++YlP1/OiHv5SvyZ3+zRy6PY1l/dkmGa2XJXfVSIYnGBZ0S5QWiuvOi8hlRSok6ZwWUEnfrRjG9JVHGJN9pLUpr0dqINq44xhfPzwsg79n+Pon/qC6/6L5Pjjr3yXt5o/TlLpXumWdkpYjsEJGVv9glKp1OMCSVEvoKAsigNyQltzsx9evXS/biyyWdLQq+Lhvdkb+DtO9TqSUlKsck4tOOk8wvgs5lUSmfjE1zqnmYpUqTP7n0VspLlolfTNB8YBeFrz8Om0vUXnUt+Z3XkL7mRmoP/gwkTGoEtWZS/DiX+S11ojwfe/I0IvKCpKxCL0uAA2LQaYf1zhDz77mCxb9YzYm3r+CuHVX6929jwy81F/3PGovf+3ee+dyfQLmBDlKIY9GOYUD1UnK6sa6m3OVjfJ+4Uac5Pw6ZTBtv+4ay9t1k1xz9W8isjBF/60ZxQLKdPdKx83JRKHn8lU+IfFzk2EuX5KlLnpL38im5/qIvy/BsTTZNW1lXt1J4+18IBlHKJJxPCrGiuztED5SWrQPnOf8C7ruBBF6noFxBIcOvfJ8wcUTYf0RGpS1P3i9Subwp1Rsq8veZz0hwzodw06JX9Qh+cn77FR+QVZmVAkjqyp2iU8uxwIYhUa4pK4MpY1ROxCYJSGGZ82BWDwOK+OgpUps3wmIZf3yW5nCRtWoNO4P1dAx084kNd/CPr/H5rlvFy3Ugcw0m3vsmjpZ3YU9OA+3EHiPotaNIrYacneY8/kBSO4RlHHAwoSLMalaOruA90bt54P97E7WVQhRa1OkTbPyzvyOV7iLOab599FtMTEzgpvLEgWAXKgwGQ1wzcgO/OHE3S90BYU+R9tPPoIs5xFHI9BKms1hxtNaICMJyHk3sslPiI0tV0BrdkSecnsFoQ7szSy5Os7+6h71nHoaTUPv1AFtbr6X3yyUK+4STW3Is7lxP/N+/g8oUE9PjOpBJQaOJzC8lDpEIGTeLr1MstOcTc6k1KgaVSiOZed7fuo2Rt72J72+BlScUM2sM9/75O/nZ4Xufy4G5ASk3T2hCpB6SzndTKAxwfOEQZ80CuqOIU60DSalMaR/T34+EIfiFbNl1fXFwxCz74dpzRA92nRdR/+rLBBAnm5P8NddICi0m5cmWzVfJ3lc/Kd+46mF5D9+RV/7Tcdm5aOWyfQsycGZcvE07kjXctKhSl6jezvNrngPK20ffLm9e+dYkdjCeGJMSzxSEHl9+32yRX151Qi7dH8uLD4Ry85zI8Dd/LID4flG8TFE8PysGV0wuLco1olBS2rFTnK7k+f0LLxBTWla3XBLzmHRG0i+6TlQqVSZt0mVfp8TFEQPij60Vd8Oq5AelvKhiLkHPLVvEW70qCWyyWcllukWh5V+v/l8iHxX5St/P5QMb7pcLji3J+sfOythUQ/r+5WvJOj0lUdls4g0uxwh9Tkm+ccV35erS9ZI2adHaFYMRzxREreoTCka+8crvy0fvFLnuTCSv3y1y6emG6LHlQCvdKcYJxDie6CCVeJiFnDhjG5J79veKd8E2QellLEve3U3rxb9we4ID+UzZ+Ph3IJGPY9A9RYDEGgQBqtVGmi10sRNpt6DVQuI2KtboELCKh049zOvW3srY9g2M/+gInq85cUMv5tkp1GWbaT2zj3DPbpSfhihCbEyuNMBg3zra1Sr3Tf8H9aiGEYOf76TJIlQrXPzP3yD+r7dy0FhGziiqqxSPffEfaHz3W5h0EQmbQIxIDDZGZTPgukitBq6DipMmC2nWk2OlML0llNLE8wvoYh4ltLVWGo3gZNM4g33YY6dRS3Xc4UGk1kRpl9SObdjpWaLpadRAJ9JqEkYtMibHnJzlg/f/PZ1Fn+LGAr2fP8noyZCoO08q8uj8mw+AcqFeTwqhQG5ghKWSy5ePfolau4rBxVEuUV+KUk8/N8Tv5Pq91zG3O0I1Yqp9mv1nzrL4xX9AaQeRCJEkxpc4RmLQI4NIHGNnF9B93SAx0elxSLuIm5TezMgQ0fhZ4skp3E3rkUYLOkiVC+vXSn7tKglA0j29kl63RjRIsGOrpLaOJSaqvyi6MysaxChHXHxJk5VculsMGfnRTT+SyXcuysf4trz5938pF0625cKfn5HVE/OSf+NbEp1XRtbdeJv0rt4ixjjCslPkBmlxx1ZKt9ste27dK41LYvngjgflhn0Nec1jVm6cEkn/abKGzhRFuSlRTmK6neFhCa65OhHzYlb06sHEqXq+KS9mxYwOJNevHRV326ZzmFA2mZ7eO6Te9KXaTJwgpaHZxPSUwAr29DjSaqGNXq7JJdUclIKMR0p51MMFTs7M8I4r/pgWEXP3H8Ku7mRxQw96oYzdMkrjhz8BRxOn09QnT9GulVEodC5AZzKE8zOs7NvBlX1jOEbxlQ+vhbRHyjcc2PMoE3/9NpQJEuy0EUQhurOAymaSACrlkXSGtBOrs2zZnJGh5Lhaw/T1oGKLVKpIvY7yvbbWHRn0YhNTbuP0lmB+AR0rvJER4kNHkEoFJ0jDUgPVaCXFTix4CklpWrUGnaaXRxbv4yt3fZ4d77+QUz94Ga0VGTwt5CYU6Z6VFD/wl0irxcLjD1KfnURpF7CY3m5iV5NZUjwbH+BXTz/Endu7WVidoXtWM52BY5/9IEQW5aeSgmcUJu0E3R3E01NE4+M4G9ejHA+ZW0pqggBGo1cMItUGUqljVq8gnpkjPjuFSnuwVIce8uXuvmHp6huSImnpGBiS3NCQZNCSCfJCJhE1X/viKEcclJhCRpxCRlyMpFVWep1hAWSjvkH+x8598rYbfibvGbtTXv2lQ7JpOpYdB5dk9cS0eBu2nk+jaccXd1NibbIqLWsuuUFenrtKfv6Sw3LF/lB+/3AkL18UGfja/05QP9MpOpVL0L6jQ1LXX5t4l8aIu22zKNc571UC4qwcEvfCxGKojC96Re9yjOCIKiXrqJRXNvn+oTtUre1Tb6KKHYloL1XRyqFuG4zkV5NOZVmqz+EoJyk8qiTEVBFYhKZt8Mnr/oHXXfk6VtS7uFF30HhiDnuwwsTbR6mIxuvKYwaHqNz5LfB8dDGDrdZwMwUyqzaxdGovH+/5ax781HUcukjTndKcMMKRN9+GmpzEhg0kWi7Xa4USwcYhKpuGcg2p1hKnSASVy6B8F1mqorJB4nHUGiglSSOmFQhccExbm5FOdKWFDsEZ6EJXWphahORSeKGhyymyfdVVBCZNTAzaQdVD1HI3pwZM4HDP2fv5+uOf5+9P/jnBaoffe/1L6TjYZvMnDuO4Gu/xSVLXXkvm2t9DmlVUPoudXSQ7upZZdYZXVnaQuez1/ERNMfaA4OyPOPWhv0WeehrcgGDjVrzNFxC85HpSY9sIDx9F5dNIFBLPzi03cyTtdaojix2fIp6YxqwchDBGqg3IB9AIodqEbCoJ0IYolIfWbZHBrTukl6z0BL3Sle4WF+SaC26Ryza8VFwcKQSdEqSz4uOLr1Pi4YoLklo1JIXhlc+FwCD/afgNIn8v8p3tu+R93C03PbAgFz1dlk27z8rQA78QcEThSOH668VkCrIi6JPd1+yTr2aekM/wA/lnfiDX6TeeX6/ng38tQyIyIqFsikWKb3qnoDmfYjuP9mlf9Mq+5DjwRA0ve4BGicr5ybX5lKjO9Lmgr2yK/SvuwHd8ObWQ1KrbFlyHjjXrqVcXmJ05RTtuEdsYEy4nOm0IqRSqKw+NFnGtgdc2pMmQSXXwqD7EzmAHN2zfycFfHUAaISf+0yjOqSqycRSaDdpPP4GKXdrTE9zSezM3//5tpF7hsvXFa/nBhUf5zjMfxm/FXOK9luJ1b4QTM2x+Wjjz+I+Y/NzfoVphktRcDtnNikFwHWRuEZ1ywXeh0kBF8XNi7yU9yrSi5dBctRkdu6g84o/IMH0ymB+RftMjfZ2jsvKqF0nR75IsnnSle5KYAE9yOidp7Uu61C3BhpXiYySFK4HKSAZPSqMbhM0r5MrsNSLvF/n1DYflE3xfbv3BhKybqMnYU7OydmJe0qvXn+fwhuJlsmnXLlnfnJWtUpXBIwdEd2blZy+5R06/QuTOzbvk/pHd8ge8XsgjqqdDFPq55IrninPRmKhcJgHZ/k5Rnpt85y4nW1CiCv4LpEZpVTad084dGO0r30C1hlrZA2lD++nDOG6aOIpZChf45Ng/0mw1ONw8SLBuBTTayKkplA5AQqCNXruSeLFK7mSVg+2D9DvDvOKSF/PsvlOovWXOvHYA22xjXYWzcjXVC4Z56Z4Mfa/9CNOvupjgmRZOtsChW17G6iPz3LTpj5nrOEmxs8Yz/v/hH+ufgXmVYJRebgoIPFR3gfjgiST11tcJE/PnOJzkFp0kJ0k9XM64qHOZl7Zam15bjuvNnHQEyFAROz6DbUdIM6IZV/FyBfpXbWR4KsOzS/sYV5N4XgqpNomjGEsd1dmN7ushnppBVdv4LUOZGgOplTx5+4NMjEfc+90nOfTFrTz8B0WcZycZ39LBH959lL/836v424/1YEwMA4aHvvstpt56G4WeURbsIswuQCYLvsWPXOJKm1haSeP6SC+2UodqHVXMIbGFSi3pMv3NDrfljtvzx1pBTEVrqzCFDDqMMZ6DthpdaydJUuORzRbJdpb4ydR/cKp5nGw6h1psoSLQjovJZNCFHCrwkLkk7RyamE5V5FTzAJ949AuMrRpgYE2Roc+dYHjCkst2032myvbDab59hbDYKeQahhOTC0x+8oMI0OhK4fd24wD+cC9eKk9cXkKIUJrlPiBBuTpphg78JJX3u4jnecQ//1yDKUX5O9T6Xp+uNPbpYygxKM+j1Zyk/+JryQwOsv/n3yI3uhLfDZCZOsp1k9Y428DZsgHKNeKDB9E6g0KjrEX1BZjQ5bGT/4ebxn6PjaOrePKnT5FLZZm4oY/OUw0WLl3FoVUeA2dhYbXmiX/6CM2f3IM7NER87CRSrePs2Ei85zC2UgHlIhIiRqNKeez4LNSaqHwKphaTas/vIv53vZJBj7YpDY3coSZrPtUQJSapEYQRztqVhGGL+qkziKtRbYFKRNIZHqKCFHr1AHJmBuotVJggrPIMpF2otci6eRZKLaZPzvDm7a9lsrLE0R/ux75qiP4NfczWLI4r2GGPg5OnOPNXt6OMgyyWUZ15VFeO+Ox0ErWhEWJUdyHJLM2V0f1dia432udlW9S5ZvPlVNv/Sxo8A1baWuukO1MvNJPgJOWhBjpw0xnCw2doTU/hpXKYJYtug9EGkw/QgYfp7kBVQ3SthTYuyjEoo9FaI7HQympKwSB3HbuTHx74Cb93zcV0CWz/4nGW+hRLnYLt8JkZgmNf/CjMzKEzGcSQ1PCNJl4oJ6ZCSUJcPoMyBgmTrDUpL9kEeAHxaTfNQHZ4md7fkP9zfXkWtJkOMVajUi662cZcPIoz1I3dfRAnF+D1FVGTDbQxaKPRYYQz2o/JBdhH9iaYoVPoGHR3GhXZxJVeXcK2mugjEwjwkZ/9Vwpiec0fvYTWN05jvzlBwXHJWRi/62GaP/4eGh9ZrGK2rMEeO0N85DRKqYQAJxH7+NhZZLGKXj+MPTuHzJfPi/3zOb9+YAc3jb06Of9N/YdkLEcE0xf030FofRyFGs7BbB05No9KB7SiJrbaxvVT0I4Qo1C9aeRsBZoxKlqOCxyFDhxYrKFT51RjHtWMEavJ4HKkWGFszZVct2ozx56cQZ6Yp33LCuY82PcXryE+cBhnZBAcQcanILaoZWL0aH/S8T1XSWoMjoGlGiqMXiDi54h/25p3UW7Oc//Je2nHreVN/I3+7+SkrRUKrTQq8NCOQc3Wk+805MiQ8wpIHKPSHqaYSkCuYVG1EOO4GDTKaJQotDLoQhqTS6NqbdTyppExFLp6+NhTn2XhxARX3rwW7/AJSk/AM898n9ajv8LL5JOARpOUy8/VDl2T2HClkpkCBdJsIbXmCwDvHPGljiFSXsBCbZZyY+EF9Mqy1/j8lxmIuu9Qm3p9VQxgzxSqI0BSiqn549y++d2UvBKPzv6C3I61yXTMyXmU750fPVFGJYFRWMVctAElEO85hDLpxFGxTcxwL+74IkdPPU6tZXjDpbeg5gvc9fDX2XvvHfjzDfTaEezUHCyWQbsoiVGBj17Rixweh1odhrphsQqRoEhUQ6nEHAJ0dw1z6caX8rUnP89Ua+p3Sge8ABjb6sKVl5SlpXJSD7G+JV5sEiOsvOwK2gfHOTt3nHB1FplpoJoRNrYkJRSLaCFuNKE7hwznsacXkGozcaRsE1XsRK8aoLLrKbJOgdgKNdvgxFuO8/jCMW7+90vxAW9oBe2pGUSBDduIRKiuPJJOIeOzEHjgmoTr8XKZfVmmzxFWuO5GzMQ01WP7abcbLyBURMiR4UObP86/nPwSB6v7z31XcbTV2Formc5wFTqdQvkO2vc5wwStTiHjBJTnp/G1l7SjS4xFQSgY30M600gzRmbLoByM0ljfh+4s1gj9xRVk4zSzrUUqfpM//sGfcNo/iZf3yfp9tFoNVBgvt+U7SRXXcRJ0d00y+RUvl7jPzTMkMo1yXXRXF+3aEu3pk8TtRlLYeR7XOzr7KXpFFptzuMp9gQpoPWfRzrIJm63jbB3GGeni0H3fwx0q4BfyTO7bzctWv5xirkQraqKVwUSgoxizbQRVbsH+cYyfRYsC28Ab20hjfpbwscfZcdnN2MAw1zpJz8gafjrxI46fOEjXivUszo9TnZnGMT4Ki44tuq+EmlpATS9iBrpgoQblRlIuf75YA87wMP7YFhqP/Yp4fu45fX8ekelcF9mVo3z06EfYW3nmBWuoy3ouL0s1zFlXI5u6kIOzxFgYDGgensS3KXaufQlH5/ZzfPFYAiLNGOlLI8MZ7IFZpBYirsK2Gkghi1rTy+JTTzA2spPR0ibuf+bbmFKRto5RpxbQxRztjGXxzFnWpzeAUhyvHcEtdWDjCLtQgWwKcTRSrp+f/LTLI6tJHRPc1atRKZ/w6FFotp6TjmXua+D1V7ybB/bdxeny8RcAIkljfkXrCFTgoNMGvdROpmA1CdBkMhRLg9g44sD8s4hYXO2gUyaZu5lv0qyUUY5GxwqdS2F68qh6Cy9fJO5Ic7p6nFpUoaVCnFijXEVTtXDF5ZLCJVxW2snG7AbaboQyJqkLqmTwStWjRDWXJ9k0+rzYm3yB2IZE42eSrpLzc06CiOB39lBcPcbR6hEc47Ituw2DQYl6gXRo1QTV5UOnj3p2GtXloYezqP2T5NeMUlmR4p4D3yTv5vGdFBILZjBHs7aEPTrHpYNXJ20pURPngrUoDXb/PgpbLuDE9BGe3v9jCqvW4s20kfF59IoeyvMzFCcd/nT923h44gHunrqLQv8gTJZRSw10kE4CrlaEVm7ioaLPI787OEhw4YXY46ewi+Vk5ug3+OuOjKJGV/HwM/ewwV3Lywdv4VwFXJ2XAVA7N1wvzLaRMCYe9uFsAysWO5zGni4j7WQ6zEYx4oHNaCrTc3Rme7hp3S08dujnHIyO4a7qQQ6cRUZKkE8RP3kEm09DX4AcWcRmNZJxKU+c5sKxm+hId/Hg43cS5hWek0IvtLAFFwvIQvO86yvn/mxMTEjq0suozo7D0dP8zcYP82xlH98/c2fi7CyDXnDZZTSO7iU9E/GhbR/n/qn7uG/yP85bBpFEpRDBMW0mrKuziKArcTJzpxRSizBWY60gRqPd5anytpDtLJG1WWqNCgcah3B685hKSOx5qMkygkY5PsZR2HZir3SssLWIINtJmSqNSp2m0yKnu5PZIgs6UhDFJAk/zuv8OcAzfopocZ583TCU3cjupaco28oyRwWdSqEyGaLTpzF45NNZ9lb28vj8r19gFhNNEcTo6v8FPDqvr/6iGocAAAAASUVORK5CYII=".to_string()),
                    base_uri: Some("https://gateway.pinata.cloud/ipfs/QmbfjrT9C5y7JLwrB5NMXRuMKGy9GfyeKVgT8Sap1GN9qc".to_owned()),
                    reference: None,
                    reference_hash: None,
                })),
            contributor_0: Vector::new(StorageKey::Contributor0.try_to_vec().unwrap()),
            contributor_4: Vector::new(StorageKey::Contributor4.try_to_vec().unwrap()),
            contributor_7: Vector::new(StorageKey::Contributor7.try_to_vec().unwrap()),
            remain_ids: Vector::new(StorageKey::RemainIds.try_to_vec().unwrap()),
        };

        //return the Contract object
        for i in 1..777{
            this.remain_ids.push(&i.to_string());
        }
        this
    }

    #[payable]
    pub fn update_nftmetadata(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.metadata.set(&NFTContractMetadata {
            spec: "nft-1.0.0".to_string(),
            name: "TerraSpaces".to_string(),
            symbol: "TS".to_string(),
            icon: Some("data:image/png;base64,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".to_string()),
            base_uri: Some("https://terraspaces_nft_1.mypinata.cloud/ipfs/QmeP2Gn7fjycGerqTiKZnexyYXvu5qvDVKq4WHdfzwL8bi".to_owned()),
            reference: None,
            reference_hash: None,
        });
    }

    pub fn get_contributor_0(&self) -> Vec<AccountId> {
        self.contributor_0.to_vec()
    }

    pub fn get_remain_ids(&self) -> Vec<String> {
        self.remain_ids.to_vec()
    }

    pub fn get_contributor_4(&self) -> Vec<AccountId> {
        self.contributor_4.to_vec()
    }

    pub fn get_contributor_7(&self) -> Vec<AccountId> {
        self.contributor_7.to_vec()
    }

    #[payable]
    pub fn init_whitelist_1(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.contributor_0.push(&"zerotime.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"s0urce.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"babywinsch.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"unsophisticated.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"resolute168.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"hungcoiiii1.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"franksky.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"killuaaaa.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"normalget.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"milosog.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"isecho.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"bats4mint.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"mumnag.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"lordyacko.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"happymikey.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"auraatom.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"sometimeart.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"hoayen.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"sabermint.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"saygege.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"kbneoburner3.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"drimyselena.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"mikeyburner.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"velaburn.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"aidarkunn.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"nefaca.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"legendkiller.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"e34c8f6a484cafe3bededa08dbc2444c4e0f6aff8d628894471bea04959dc004".to_string().try_into().unwrap());
        self.contributor_0.push(&"bakar88.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"victorokezie.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"goudvisburner.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"hommemmtw.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"2e644f27d9dd296993a3833b3e504b92ae298eab130b276c8c5a808f10bb8be9".to_string().try_into().unwrap());
        self.contributor_0.push(&"markoeth.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"sidrickmingo348.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"xtyalsa.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"dabbie3229.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"d4a5eb8a0c066cdcc005ff16bd0efb8793f080385eec4d8afe29d38ba84a2e87".to_string().try_into().unwrap());
        self.contributor_0.push(&"sr1234.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"harunguyen.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"ahmetmetin.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"zig_zag.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"07ede979a89ea47dea4cdfee4a986775b8d6a415a73415b30fc42dde622df8d7".to_string().try_into().unwrap());
        self.contributor_0.push(&"25ecf0a543bfa184d583c96ee5dec12463f3b3d6a902c554e83be39d9078f949".to_string().try_into().unwrap());
        self.contributor_0.push(&"0e474338679d1aeb6b1df8707daab00d501ffb8b6f6150631b37596cf5b7d06b".to_string().try_into().unwrap());
        self.contributor_0.push(&"asacwyafam.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"2a4d9bb6eadd2cf31e57927bbe1cea5b1759f0fa41544540cc57ebab91319c24".to_string().try_into().unwrap());
        self.contributor_0.push(&"nhelskie_nft.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"mubashir.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"meowboka.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"buibuitui.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"fabrianable.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"ar1stoay.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"mkelvin26.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"jamjadam.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"borabenz.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"pharaohtan7.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"kalpesh7.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"mikeuponly.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"whalehunter.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"707c42b5f064fbe2393f712ff8144395998a7107c5e240e6e436c2907c16a92c".to_string().try_into().unwrap());
        self.contributor_0.push(&"saadventurous.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"9870084d92245d52db36dada511ac415398ecb1f0df53dde43d7688b17fc3b54".to_string().try_into().unwrap());
        self.contributor_0.push(&"dongudo.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"5816370d9f2ca0db9739e153985f2202a3256d62b99a03343c7cb332837ec51e".to_string().try_into().unwrap());
        self.contributor_0.push(&"saygege.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"bigdollamami.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"notmyburner.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"nobody_83.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"assassinss.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"j4son.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"eb529b450434e2cf36a29272d9bbc95d14cbbbb9f40390befbe4bbe1e09f61e1".to_string().try_into().unwrap());
        self.contributor_0.push(&"gurkans.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"thechewy.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"fde020cff5a7db46597f0cc87918ed9bd3798571253d47a07603986e4e8feea1".to_string().try_into().unwrap());
        self.contributor_0.push(&"4cc0c7fdacb1b89515e763b64f519bcf4f39a34895be2cad44cf1cd9f5a5a7db".to_string().try_into().unwrap());
        self.contributor_0.push(&"9870084d92245d52db36dada511ac415398ecb1f0df53dde43d7688b17fc3b54".to_string().try_into().unwrap());
        self.contributor_0.push(&"luciddream.near".to_string().try_into().unwrap());
        self.contributor_0.push(&"xuguangxia.near".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_2(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.contributor_4.push(&"adambennett.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"edgepqrs.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"meivan13.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"nanth.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"fda582061f92b503ae588418dedf170880469baa905b4252723a45aa16bb546c".to_string().try_into().unwrap());
        self.contributor_4.push(&"jamjadam.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"dkumar69.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"5816370d9f2ca0db9739e153985f2202a3256d62b99a03343c7cb332837ec51e".to_string().try_into().unwrap());
        self.contributor_4.push(&"2cea9d141e791617b0bb0b0f39c62740625441df3f177771e6e177a18bc1d45e".to_string().try_into().unwrap());
        self.contributor_4.push(&"bensteckel.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"sr1234.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"534d108ee26ebbd944ace1c3f25b662208ff288ac159a2c2d79141a1bdf6f422".to_string().try_into().unwrap());
        self.contributor_4.push(&"dj_fbm.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"mcspaceman.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"syxhung94.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"cowboymode.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"crypto_groggs.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"mujer_bruja.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"johnybravo.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"asacwyafam.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"f53a0bc5469cca22c28fec593c775dbc2ca7fa840ed8d13c9b45587a022bcf60".to_string().try_into().unwrap());
        self.contributor_4.push(&"69fc316844be2318073f58cc903e0acb2d11f06b7052805a07a5055de9756fdd".to_string().try_into().unwrap());
        self.contributor_4.push(&"a042e58b29ab5506ac1437369a5c8a349045fc2cd3115f79c8a3aef38bd75c3f".to_string().try_into().unwrap());
        self.contributor_4.push(&"gurkans.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jemailkarami.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"miraclechinaka.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"18bad2af160c4fb53e714eaf3d7fd69d2cb40c539a0a279e716786aa22a1d9d5".to_string().try_into().unwrap());
        self.contributor_4.push(&"zennie.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"thangdt.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"rickdeluxe.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"imshafiiqbal.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"himanshu97.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"artronaut.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"nobody_83.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"supah.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"prolificrug.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"nearnftwatch.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"misfiress.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"comfyrelax.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"memoire.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"0xknth.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"8xpavell.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"notaajaib.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"omarbibz.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"davidmanfredini.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"iamburner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"ev3reth.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"lollipapi.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"0xc6eburner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"drgnstone.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"harshit18.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"33a8884b03582efffc43220c058b3a474f315cc4a89df1c827bd0891870ec38e".to_string().try_into().unwrap());
        self.contributor_4.push(&"nearlynoob2.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"hopiumm.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"ewtd.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"didderd.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"dab1787a371600b5bfd3b62d7759bc4497f8e2af64b6668bce56c3bc2b5a331f".to_string().try_into().unwrap());
        self.contributor_4.push(&"backup.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"thithikute.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"minttwo.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"stephenwolf.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"nftsniper.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"m0on.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"0b62fa9a4b7350cacb590d6e1e09d587de6c2f3446e17d90e328e5ab61803b9b".to_string().try_into().unwrap());
        self.contributor_4.push(&"pruthvi.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"boorner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jsdrburner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"quocduy1901.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"phoenix100.near".to_string().try_into().unwrap());
        // self.contributor_4.push(&"HcuFWb9aNXtXiYWi1d1xpPBDYpSL7KUUX769SxFHQNKf".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_3(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );

        self.contributor_4.push(&"nearbots.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"caeseumoxide".to_string().try_into().unwrap());
        self.contributor_4.push(&"f5b7a7f27ed4d5b4d456cb23b05170e9920c79c07009d1cb9669a6114024f86e".to_string().try_into().unwrap());
        self.contributor_4.push(&"plutocrat.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"codedforum.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"alpharebel.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jayjirayu.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jughead03.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"nagatoshi.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"lfg420.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"kinvin.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"yeayy.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"f92b439464b901e83058ef8d8cdbcdd3ed7a8390f39173b536a66915e908c40e".to_string().try_into().unwrap());
        self.contributor_4.push(&"blaze.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jen.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"natnatasha.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"spearmint.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"srms.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"rurena.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"markeymark.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"burnergangs.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"metazhou.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jagermeierr.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"aod_satoshi.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"bf9f9ee1c2d2232b9ece930a10b763bb51e3f3738e318fc8e28d08265c26f31b".to_string().try_into().unwrap());
        self.contributor_4.push(&"kenny0001.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"atharav25.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"minibb.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"bbzkarim.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"keeroz.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"lim2481284.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"rektdegen.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"opshenry.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"2d2f0b934e665edb3753e73fa4de476b25cbb694cc941a27cb602c3cdeec7266".to_string().try_into().unwrap());
        self.contributor_4.push(&"serhio420.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"iamdk1.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"balaburner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"somdot.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"0xknth.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"8xpavelburner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"burnergang.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"jardel.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"linkify.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"boomint.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"beforesunset.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"fudge.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"rickbakas.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"apeburner.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"minterino.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"dryollo.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"mintooor.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"howl33333.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"sellnft.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"burner_mint.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"yupig.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"hommemmtw.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"thecryptoasian.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"drwho31.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"zebu.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"mokkan.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"c-k-s.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"ltlollipop.near".to_string().try_into().unwrap());
        self.contributor_4.push(&"modsiw.near".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_4(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.contributor_7.push(&"hardcockcafe.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pro100skill.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jayrness.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rahulgoel.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"hykinho.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"swifty0.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"amoxid.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"aleph888.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"marcane.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"9kurama.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"zackupup.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"makil.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rastamano1.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"sevenzen.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nearsg.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"parasr.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"est_predict.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"5816370d9f2ca0db9739e153985f2202a3256d62b99a03343c7cb332837ec51e".to_string().try_into().unwrap());
        self.contributor_7.push(&"istiyakkhan.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"originalvu.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"frankpst.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tuturuu.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"aadilk4.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"cyuen.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"cremefraiche.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"boorner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ledoanh.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nneminter.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"candy69.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"cybrog.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ffbda417cf06556f008d13e1b3da736fd0aec18f02a0e72c9cb3237749e16f17".to_string().try_into().unwrap());
        self.contributor_7.push(&"tutoni.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"41e11c8244a581c1f3cce3150ef1f8a9cf063c6bb45b126c2928afdb735f82c4".to_string().try_into().unwrap());
        self.contributor_7.push(&"mehighlow.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pilot29.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"itax.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"zujka.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"beckers.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mintr.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"alterschwede.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"994f66a2ae97ae828ab7131b4ca0d864f8cb5d77a2dfce5c80ecc1a0de5831a8".to_string().try_into().unwrap());
        self.contributor_7.push(&"novaskburn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"coahero.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tony2401.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mimieuro5.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rolandsilva.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"milolow.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ivango60.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"evky.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nootno0t.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"predragns.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"boiler4444.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tmmynft.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"atharav25.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"17041997.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"clinomaciac28.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"swhx7758521.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jtburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"dyepburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"choby.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"senay.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"eqx66.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mageme.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"colindtn2.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"beeris.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"comfyrelax.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"topshow20.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nlphuong19.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"backpack.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jin02.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nearwork.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"themicrowave.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"97eb8f5698074c1c551e8bacfdf10a556e5c9d58921de6fcb61237a64020f9ed".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_5(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.contributor_7.push(&"finnard.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"suip-noomefas.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pkmnmaster.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pwwm.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rosenin.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"wineyang.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"occulus.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nikajoy.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"majinmint.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ola_uriel.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"domtoretto.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"g-rant_p.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"gavro.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"cortezs.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"khanhdn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"susukute.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"giya.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"chisiledjoe.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"logan08.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"artronaut.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"minterino.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"inri.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nth122.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"theburningduck.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"frankthetanker.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mangomax.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"hansolo1.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"wormsama.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"49860fa82138c8aa911c56f642ee30dbe23971bb2613de4561fe43b7a89858e2".to_string().try_into().unwrap());
        self.contributor_7.push(&"stayhydrated.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"0c1204ea6871b174593342a4cac8f5909e997e1c2e38e4630e12cf9b965a645c".to_string().try_into().unwrap());
        self.contributor_7.push(&"nearassassin.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"hailmary.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"8nakburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"vvronnn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"thenightracer.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mstanojevic.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lamlamli.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nearnftsquad2.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"taexyz.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lfmint.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"burner01.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"xanaaa.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ilyadreamer.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"y_breezy.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"kminter.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"zekeoghanabi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"planett.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"labanj.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"trepidnobody.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mohanv.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"f0611470aa1e8321ccd00715a04e6d8e206d49fc8761278854f3c2a0b4169e1c".to_string().try_into().unwrap());
        self.contributor_7.push(&"slasherica.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"alucard666.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"aa507b381dd41a01fd96fc0349807cf8d096483808e27c81e48d599c34e38eb5".to_string().try_into().unwrap());
        self.contributor_7.push(&"gohan.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nftmints.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mello00.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"heeyitsaria.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"glenn_hodl.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"astrals.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"strawhat.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"cryptobiker.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"iamempty.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"11dec324f2436c8a8e43abf71f69ced91c29dcd4b781faf28ac778ea1467645f".to_string().try_into().unwrap());
        self.contributor_7.push(&"makdibabu.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"warreningente.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"chiquin.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"npthebulltrading.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"xvhere.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"miyukisan.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"wubzmint.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jabberbkk.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"whiteflame1997.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mjnftburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nearparas.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"bloodytoad.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"259e931b0ff73508db3330ea880335ec0b9dda4f7adc6e0541c1a657ca4a972b".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_6(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.contributor_7.push(&"bendito2.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"4d3810d733f832d2ef3abb2db5e630d8dfde16aafbe72c1577b419249e80ffc4".to_string().try_into().unwrap());
        self.contributor_7.push(&"ruengdet.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"9b621f56ae70c14f54328c965eae94b06c17490a1496be2d70f2b37a20c3a666".to_string().try_into().unwrap());
        self.contributor_7.push(&"gujjubhatt.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"beforesunset.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"bauglir.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"5b20775573dfe056ecaf8d03a8cad06e3e1e1aa17aa5bbe0fd510485325c4f93".to_string().try_into().unwrap());
        self.contributor_7.push(&"miburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"d59c573e4344ab3798eee5d89920a1feee6c0efcee27839d93f7a35a1f823ff1".to_string().try_into().unwrap());
        self.contributor_7.push(&"temtem124.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"2e0c3bb76878a5ec13668fb678ae2a3ff656b50c737b38a8755a5671781acdc2".to_string().try_into().unwrap());
        self.contributor_7.push(&"thetug.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ladykiller.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"burniesanders.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"adityavidyarthi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mintone.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"heycome.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"godl69.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"172b5e9dd62550811f9044a3896a887b013593923f7eeb0342eb4091d8cc942b".to_string().try_into().unwrap());
        self.contributor_7.push(&"ymymym.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"niqo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"henryis.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"2d2f0b934e665edb3753e73fa4de476b25cbb694cc941a27cb602c3cdeec7266".to_string().try_into().unwrap());
        self.contributor_7.push(&"b38eb8c7232ad225c8d962991287f6e2b6c0977da541460a0499a2b490eb7051".to_string().try_into().unwrap());
        self.contributor_7.push(&"jouzy.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"opo7777.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"boomint.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ugozy.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"kallia.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"b1mple.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"shomi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mextlibrn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"solunagg.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"quinn4815.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"avalavex.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mint-tauro.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"0xnuii.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lalitsingla01.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"3a012e85e7c1c67c93b1a1aae2fd96fc5c32453ae0da473b5430b1a8aa3d6752".to_string().try_into().unwrap());
        self.contributor_7.push(&"jaywalker.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jen.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"0b00efd27e39ecd8807be0236f373ed1148c02f5a7ce4975768df3bb20145319".to_string().try_into().unwrap());
        self.contributor_7.push(&"mear.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jecika.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tucken.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"42a6aa8b50d9800f6eb600cf954deb8fcc41b5cfc73d7b20e7657d6afb94b2e2".to_string().try_into().unwrap());
        self.contributor_7.push(&"mikica.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"eineklein.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"0xfminn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"codedforum.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"dontscamme.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"burnaboi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"danielbennettmd.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"vizard.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"fbm_b.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"f29c6a6b79f538ce6007023cd8e58ebe23ae9c1dac163bc1393b423af3560135".to_string().try_into().unwrap());
        self.contributor_7.push(&"samurai.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"luziax.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"louii.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"timmitis.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tdskub.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"larala.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"markmklsn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"wachiizz.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"dzonika.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"being_ujjwal.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"bas_c.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"hellpanda_nft.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rejinderi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"1132.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"1n1.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"suria.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"yoochan.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"kneelock.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"shakiev.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jingyang.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pradau.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"0f6fa1e8058123cb2ca6c3503beb23dde7f38fabed0652f8479d5704f7cd8a83".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_7(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );

        self.contributor_7.push(&"deg3n.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"08b0efccc7b7149ea3422ab6b5c25b5e20125c0d785ca421086a82834749f62d".to_string().try_into().unwrap());
        self.contributor_7.push(&"aburnerwallet.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"toxicburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lxvrnft.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"d35899dee93ad1f87aa6b839a90277f2d6132d88f6074b73c6a5cb23e8dae347".to_string().try_into().unwrap());
        self.contributor_7.push(&"thethriftlord.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mofeoluwa.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"odinr.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mikes.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lrlhx7758521.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"xiao712.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"smqhx7758521.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"zebraman.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mintthree.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"saboshin.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nftsniper.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"1kendell12.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rayscooker.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"kanzyani.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"helix55boi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"fat-unicorn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tpro.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"topjirayu.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"phoenix100.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"yashwin.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"f5b7a7f27ed4d5b4d456cb23b05170e9920c79c07009d1cb9669a6114024f86e".to_string().try_into().unwrap());
        self.contributor_7.push(&"8f1cff415cfddf57ed715ce451452a4f3c57f20e8aaf9788bd6be20ac51338c4".to_string().try_into().unwrap());
        self.contributor_7.push(&"elliotb.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"howaboutthat.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"dylzie.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"dc6a73cb075f08bab8ce7cdf809bd27e8baebbc84ad73e198c8ae224e3d7e325".to_string().try_into().unwrap());
        self.contributor_7.push(&"ballanle.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"card4card.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"xmoose1.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"a1ri.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"plutocrat.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"azorahai.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ivn_ivn.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"touya.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"burnergangs.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"neffertiti85.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"335732524486aae88cc7e3bbd9ca1ef5ce77e597726b4db5457b512578bb913d".to_string().try_into().unwrap());
        self.contributor_7.push(&"caeseumoxide.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mynameisginny.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"rizan.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"alpharebel.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"omoko.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pgoo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"originals.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nearty.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"samburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nagatoshi.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pribiden.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"e083714d4ee2816b33d57347430c1d6d3a1ba3df3048b812984aafcd45225893".to_string().try_into().unwrap());
        self.contributor_7.push(&"c421a8f197eb5b5442b9fecdd3c60aba73f15f28a6acdd0f81ab735e0782b2ec".to_string().try_into().unwrap());
        self.contributor_7.push(&"morseburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"kuroyami.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"srms.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"498dc846e0505cecf7fea0f19c97e3470ea422d0d3d23168c7ca05129109d1a0".to_string().try_into().unwrap());
        self.contributor_7.push(&"topcypher.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"halalowo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"subhodoy.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"smileii.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"af0cd7faf2bf5d5d605e0ddf9e1c0d78ea5768aa7009211aba04c4149f3425c3".to_string().try_into().unwrap());
        self.contributor_7.push(&"modsiw.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"crypto_m.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"aa094f49c4c3aaa37a70a6ffa04ecd6c8be13e0d78fc56091c33c80f28fe0e0f".to_string().try_into().unwrap());
        self.contributor_7.push(&"kuceng7z.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"cxcminting.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"skellies.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tuanyeupk123.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"1dc1ebc1ca95e3bf7d7f30e1fabfb3387d0f48c18a6a6a6c5df91523517afb92".to_string().try_into().unwrap());
    }

    #[payable]
    pub fn init_whitelist_8(
        &mut self,
    ) {
        assert_eq!(
            &env::predecessor_account_id(),
            &self.owner_id,
            "Owner's method"
        );
        self.contributor_7.push(&"nftwme.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ponzinft.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"queef-vault.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"johnanthony.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"yohanesleonardo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"gilbank.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"iaiw.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"3b8a46a61d85c46c9e140a413e3fa9354b7a1f558d369ce548a969a9b86eb69f".to_string().try_into().unwrap());
        self.contributor_7.push(&"nicecolours.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"autoyetimints.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lalit15.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"samurai.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"migos4r.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"bd_dream1.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"guesswhos.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"snipburner.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"gio13.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"mykola_gavrysh.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"pinkman6_6.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"gdizzytre.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jesse13.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"lushmeadow.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"arvalo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"dbuki.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"hanna01.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"trenomint.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"939a33ce828fa754653dafcfa3152f11a8f3cf074a443dddf97f3e506898fd28".to_string().try_into().unwrap());
        self.contributor_7.push(&"trololol.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"xcyon.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"amritdoll.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"solewindd.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"tuyenvd3.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"magician19.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"uruz.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"returds.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nikpie.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"yidarmy.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"ciossu.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"jiale.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"derymars.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"sourdeeezle.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"scarbo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"treno.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"web3hedge.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"atasnamatogo.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"bordin14789.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"shabeer.near".to_string().try_into().unwrap());
        self.contributor_7.push(&"nfteng.near".to_string().try_into().unwrap());
    }
}