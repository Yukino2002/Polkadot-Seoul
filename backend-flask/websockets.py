from flask import Flask
from flask_socketio import SocketIO, emit
import time
import json
from datetime import datetime, timedelta
import pytz
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType
import os
from getpass import getpass
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import DeepLake
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import re
import requests
import ast
import subprocess
from langchain.schema import (AIMessage, HumanMessage, SystemMessage)
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.contracts import ContractCode, ContractInstance
from substrateinterface.exceptions import SubstrateRequestException
from tools.custom_pola_tools import (GetAccountBalanceTool,
                                        GenerateInkPolkadotContractTool,
                                        SendSubstrateBalanceTool,
                                        ListAllTransactionsTool,
                                        GetTransferDetailsTool,
                                        GetERC20TotalSupplyTool,
                                        GetERC20OfUserTool,
                                        TransferERC20ToUserTool)
from dotenv import load_dotenv

load_dotenv()
embeddings = OpenAIEmbeddings()
db = DeepLake(
    dataset_path=f"hub://commanderastern/polka-code-3",
    read_only=True,
    embedding_function=embeddings,
)

retriever = db.as_retriever()
retriever.search_kwargs["distance_metric"] = "cos"
retriever.search_kwargs["fetch_k"] = 20
retriever.search_kwargs["maximal_marginal_relevance"] = True
retriever.search_kwargs["k"] = 20

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('query')
def handle_query(data):
    print(data)
    weather_data = {"type": "weather", "content": "It's sunny today!"}
    emit('response', weather_data)
    time.sleep(10)

    news_data = {"type": "news", "content": "Latest news update here!"}
    emit('response', news_data)
    time.sleep(10)

    other_data = {"type": "other", "content": "Other type of data!"}
    emit('response', other_data)


@socketio.on('print')
def handle_query(data):
    # reinitialize agent everytime a query is made
    llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)
    tools = [
        GetAccountBalanceTool(),
        # GenerateInkPolkadotContractTool(),
        # SendSubstrateBalanceTool(),
        # ListAllTransactionsTool(),
        # GetTransferDetailsTool(),
        # GetERC20TotalSupplyTool(),
        # GetERC20OfUserTool(),
        # TransferERC20ToUserTool()
    ]
    agent = initialize_agent(tools,
                             llm,
                             agent=AgentType.OPENAI_FUNCTIONS,
                             verbose=True)

    model = ChatOpenAI(
        model_name="gpt-3.5-turbo-16k")  # 'ada' 'gpt-3.5-turbo' 'gpt-4',
    qa = ConversationalRetrievalChain.from_llm(model, retriever=retriever)

    # check if data is a json
    try:
        data = json.loads(data)
    except:
        return
    print(data)

    # check if it open ai key is not null
    if data['openAIKey'] is None or data['openAIKey'] == "":
        print("no open ai key")
        return
    if data['mnenonic'] is None or data['mnenonic'] == "":
        print("no memonic")
        return

    payload = dict()
    # payload['prompt'] = data['prompt'] + "nisoo"
    mnemonic = data['mnenonic']
    openai = data['openAIKey']
    session = {
        'user': {
            'name': 'Sybil AI',
            'email': data['session']['user']['email'],
            'image': 'https://i.imgur.com/usI3OTw.png'
        }
    }
    payload['session'] = session
    payload['chatId'] = data['chatId']

    payload['prompt'] =agent.run(data['prompt'])

    now_utc = datetime.now(pytz.timezone('UTC')) + timedelta(seconds=2)
    payload['createdAt'] = now_utc.isoformat()
    emit('response', payload)


if __name__ == '__main__':
    socketio.run(app)
