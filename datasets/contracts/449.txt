#![recursion_limit = "128"]

mod contract;

use anyhow::Error;
#[macro_use]
extern crate serde_derive;
#[macro_use]
extern crate serde_json;
extern crate hex;
mod markdown;

use yew::format::Json;
use sha3::{Digest, Sha3_256};
use yew::services::storage::Area;
use serde_derive::{Deserialize, Serialize};
use serde_json::{json};
use yew::services::{ DialogService, StorageService };
use yew::services::fetch::{ FetchService, FetchTask, Request, Response };
use yew::{html, Component, ComponentLink, Html, InputData, Renderable, ShouldRender};

type AsBinary = bool;

#[derive(Debug)]
pub enum Format {
    Json,
    Toml,
}

const KEY: &'static str = "yew.crm.database";

#[derive(Serialize, Deserialize)]
struct Database {
    clients: Vec<Client>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Client {
    key: String,
    contract: String,
}

impl Client {
    fn empty() -> Self {
        Client {
            key: "".into(),
            contract: "".into(),
        }
    }
}

#[derive(Debug)]
pub enum Scene {
    ClientsList,
    NewClientForm(Client),
    Settings,
}

pub struct Model {
    fetch_service: FetchService,
    link: ComponentLink<Self>,
    storage: StorageService,
    dialog: DialogService,
    database: Database,
    scene: Scene,
}

#[derive(Debug)]
pub enum Msg {
    SwitchTo(Scene),
    AddNew,
    UpdateFirstName(String),
    UpdateLastName(String),
    UpdateContract(String),
    Clear,
    Noop,
    Error,
    FetchData(Format, AsBinary),
    FetchReady(Result<DataFromFile, Error>),
}

/// This type is used to parse data from `./static/data.json` file and
/// have to correspond the data layout from that file.
#[derive(Deserialize, Debug)]
pub struct DataFromFile {
    value: u32,
}

/// This type is used as a request which sent to websocket connection.
#[derive(Serialize, Debug)]
struct WsRequest {
    value: u32,
}

/// This type is an expected response from a websocket connection.
#[derive(Deserialize, Debug)]
pub struct WsResponse {
    value: u32,
}

impl Component for Model {
    type Message = Msg;
    type Properties = ();

    async fn add_new(key: String, contract: String) {
    }

    fn create(_: Self::Properties, link: ComponentLink<Self>) -> Self {
        let storage = StorageService::new(Area::Local);
        let Json(database) = storage.restore(KEY);
        let database = database.unwrap_or_else(|_| Database {
            clients: Vec::new(),
        });
        Model {
            fetch_service: FetchService::new(),
            link,
            storage,
            dialog: DialogService::new(),
            database,
            scene: Scene::ClientsList,
        }
    }

    fn update(&mut self, msg: Self::Message) -> ShouldRender {
        let mut new_scene = None;
        match self.scene {
            Scene::ClientsList => match msg {
                Msg::SwitchTo(Scene::NewClientForm(client)) => {
                    new_scene = Some(Scene::NewClientForm(client));
                }
                Msg::SwitchTo(Scene::Settings) => {
                    new_scene = Some(Scene::Settings);
                }
                unexpected => {
                    panic!(
                        "Unexpected message when clients list shown: {:?}",
                        unexpected
                    );
                }
            },
            Scene::NewClientForm(ref mut client) => match msg {
                Msg::UpdateFirstName(val) => {
                    println!("Input: {}", val);
                    client.key = val;
                }
                Msg::UpdateContract(val) => {
                    println!("Input: {}", val);
                    client.contract = val.clone();
                    let mut hasher = Sha3_256::new();
                    hasher.input(val.clone().as_bytes());
                    client.key = hex::encode(hasher.result());
                }
                Msg::AddNew =>  {
                    let mut new_client = Client::empty();
                    ::std::mem::swap(client, &mut new_client);
                    
                    self.database.clients.push(new_client);
                    self.storage.store(KEY.clone(), Json(&self.database));
                    
                    let CONTRACT = new_client.contract;
        
                    let future = async {
                        match post_contract(KEY, CONTRACT).await {
                            Ok(v) => println!("Okay"),
                            Err(e) => println!("error")
                        }
                    };

                    
                }
                Msg::SwitchTo(Scene::ClientsList) => {
                    new_scene = Some(Scene::ClientsList);
                }
                unexpected => {
                    panic!(
                        "Unexpected message during new client editing: {:?}",
                        unexpected
                    );
                }
            },
            Scene::Settings => match msg {
                Msg::Clear => {
                    let ok = { self.dialog.confirm("Do you really want to clear the data?") };
                    if ok {
                        self.database.clients.clear();
                        self.storage.remove(KEY);
                    }
                }
                Msg::SwitchTo(Scene::ClientsList) => {
                    new_scene = Some(Scene::ClientsList);
                }
                unexpected => {
                    panic!("Unexpected message for settings scene: {:?}", unexpected);
                }
            },
        }
        if let Some(new_scene) = new_scene.take() {
            self.scene = new_scene;
        }
        true
    }

    fn view(&self) -> Html {
        match self.scene {
            Scene::NewClientForm(ref client) => html! {
                <div class="crm">
                    <h1>{"Document Storage demo with Markdown renderer"}</h1>
                    <button disabled=client.key.is_empty()
                            onclick=self.link.callback(|_| Msg::AddNew)>{ "Add New" }</button>
                    <button onclick=self.link.callback(|_| Msg::SwitchTo(Scene::ClientsList))>{ "Go Back" }</button>
                    <div class="documents">
                        { client.view_contract_input(&self.link) }
                    </div>
                </div>
            },
            Scene::Settings => html! {
                <div>
                    <h1>{"Document Storage demo with Markdown renderer"}</h1>
                    <button onclick=self.link.callback(|_| Msg::Clear)>{ "Clear Database" }</button>
                    <button onclick=self.link.callback(|_| Msg::SwitchTo(Scene::ClientsList))>{ "Go Back" }</button>
                </div>
            },
            Scene::ClientsList => html! {
                <div class="crm">
                    <h1>{"Document Storage demo with Markdown renderer"}</h1>
                    <button onclick=self.link.callback(|_| Msg::SwitchTo(Scene::NewClientForm(Client::empty())))>{ "Add New" }</button>
                    <button onclick=self.link.callback(|_| Msg::SwitchTo(Scene::Settings))>{ "Settings" }</button>
                    <div class="clients">
                        { for self.database.clients.iter().map(Renderable::render) }
                    </div>
                </div>
            }
        }
    }
}

impl Renderable for Client {
    fn render(&self) -> Html {
        html! {
            <div class="client">
                <p>{ format!("Key: {}", self.key) }</p>
                <p>{ "Contract:" }</p>
                { markdown::render_markdown(&self.contract) }
            </div>
        }
    }
}

impl Client {
    fn view_contract_input(&self, link: &ComponentLink<Model>) -> Html {
        html! {
            <div class="new-client">
            <input invalid=true
                   id="key"
                   class="key"
                   placeholder="Key"
                   value=&self.key />
            <textarea
               value={contract::contract.to_string()} 
               id="contract"   
               class="contract"
               placeholder="Contract(in markdown)"

               oninput=link.callback(|e: InputData| Msg::UpdateContract(e.value)) />
            </div>
        }
    }

    fn view_verify_contract(&self, link: &ComponentLink<Model>) -> Html {
        html! {
            <div class="new-client">
            <input invalid=true
                   id="key"
                   class="key"
                   placeholder="Key"
                   value=&self.key />
            <textarea
               value={contract::contract.to_string()} 
               id="contract"   
               class="contract"
               placeholder="Contract(in markdown)"

               oninput=link.callback(|e: InputData| Msg::UpdateContract(e.value)) />
            </div>
        }
    }
}