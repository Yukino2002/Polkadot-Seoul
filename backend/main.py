import uvicorn
from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Annotated
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import firestore, credentials
import os
import openai

load_dotenv()

cred = credentials.Certificate(
    './polka-4b03b-firebase-adminsdk-8i5ut-01290f6951.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()


@app.get("/")
async def root():
    # doc_ref = db.collection("users").document("alovelace")
    # doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})

    # doc_ref = db.collection("users").document("aturing")
    # doc_ref.set({
    #     "first": "Alan",
    #     "middle": "Mathison",
    #     "last": "Turing",
    #     "born": 1912
    # })

    users_ref = db.collection("users")
    docs = users_ref.stream()

    users_data = []
    for doc in docs:
        print(f"{doc.id} => {doc.to_dict()}")
        users_data.append(doc.to_dict())

    print(users_data)

    return {"message": users_data}


class Message(BaseModel):
    message: str


@app.post("/openai")
async def openai_endpoint(message: Message,
                          open_ai_key: Annotated[str | None,
                                                 Header()] = None):

    openai.api_key = "sk-" + open_ai_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": message.message
        }],
        max_tokens=100,
    )

    return {"response": response.choices[0].message.content}


# At the bottom of the file/module
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
