import uvicorn
from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Annotated
from dotenv import load_dotenv
import os
import openai

load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


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
