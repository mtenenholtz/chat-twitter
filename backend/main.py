import os
import threading
import queue

from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
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
import tiktoken
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

class Message(BaseModel):
    text: str
    sender: str
    
class Chat(BaseModel):
    messages: list[dict]

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

@app.post("/chat_stream/")
async def chat_stream(chat: List[Message]):
    model_name = 'gpt-3.5-turbo'
    encoding_name = 'cl100k_base'

    def llm_thread(g, prompt):
        try:
            llm = ChatOpenAI(
                model_name=model_name,
                verbose=True,
                streaming=True,
                callback_manager=CallbackManager([ChainStreamHandler(g)]),
                temperature=0.7,
                openai_api_key=os.environ['OPENAI_API_KEY']
            )

            # add historical messages iteratively until we reach our token limit
            # not a perfectly accurate method, but close enough
            encoding = tiktoken.get_encoding(encoding_name)
            token_limit, num_tokens = 1000, 0
            messages = [HumanMessage(content=chat[-1].text)]
            for message in reversed(chat[:-1]):
                num_tokens += 4
                num_tokens += len(encoding.encode(message.text))

                if num_tokens > token_limit:
                    break
                else:
                    new_message = HumanMessage(content=message.text) if message.sender == 'user' else AIMessage(content=message.text)
                    messages = [new_message] + messages
                    
            messages = [SystemMessage(content="You are a poetic assistant")] + messages
            llm(messages)

        finally:
            g.close()

    def chat_fn(prompt):
        g = ThreadedGenerator()
        threading.Thread(target=llm_thread, args=(g, prompt)).start()
        return g

    return StreamingResponse(chat_fn(chat), media_type='text/event-stream')
