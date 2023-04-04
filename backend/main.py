import os
import threading
import queue

from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

import openai
import os

openai.organization = os.environ['OPENAI_ORG_ID']
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Chat(BaseModel):
    text: str

class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration: raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)

class ChainStreamHandler(StreamingStdOutCallbackHandler):
    def __init__(self, gen):
        super().__init__()
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)

@app.post("/chat/")
async def chat(chat: Chat):
    openai.api_key = chat.api_key
    openai.organization = chat.org_id
    llm = ChatOpenAI()
    resp = llm([HumanMessage(content=chat.text)])
    return {'message': resp.content}

@app.post("/chat_stream/")
async def chat_stream(chat: Chat):
    def llm_thread(g, prompt):
        try:
            llm = ChatOpenAI(
                model_name='gpt-3.5-turbo',
                verbose=True,
                streaming=True,
                callback_manager=CallbackManager([ChainStreamHandler(g)]),
                temperature=0.7,
                openai_api_key=os.environ['OPENAI_API_KEY']
            )
            llm([SystemMessage(content="You are a poetic assistant"), HumanMessage(content=prompt)])

        finally:
            g.close()

    def chat_fn(prompt):
        g = ThreadedGenerator()
        threading.Thread(target=llm_thread, args=(g, prompt)).start()
        return g

    return StreamingResponse(chat_fn(chat.text), media_type='text/event-stream')
