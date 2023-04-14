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
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

import pinecone
import openai
import tiktoken
import os

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "https://chat-twitter.fly.dev",
    "https://chat-twitter.fly.dev:8000"
    "https://chat-twitter.fly.dev:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pinecone.init(
    api_key=os.environ['PINECONE_API_KEY'],
    environment='us-east1-gcp'
)

class Message(BaseModel):
    text: str
    sender: str

class ContextSystemMessage(BaseModel):
    system_message: str
    
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

def format_context(docs):
    context = '\n\n'.join([f'From file {d.metadata["document_id"]}:\n' + str(d.page_content) for d in docs])
    return context

@app.get("/heath")
def health():
    return "OK"

@app.post("/system_message", response_model=ContextSystemMessage)
def system_message(query: Message):
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.environ['OPENAI_API_KEY'],
        openai_organization=os.environ['OPENAI_ORG_ID'],
    )
    db = Pinecone(
        index=pinecone.Index('pinecone-index'),
        embedding_function=embeddings.embed_query,
        text_key='text',
        namespace='twitter-algorithm'
    )

    docs = db.similarity_search(query.text, k=10)
    context = format_context(docs)

    prompt = """Given the following context and code, answer the following question. Do not use outside context, and do not assume the user can see the provided context. Try to be as detailed as possible and reference the components that you are looking at.
    If you are going to write code, make sure to specify the language of the code. For example, if you were writing Python, you would write the following:

    ```python
    <python code goes here>
    ```
    
    Now, here is the relevant context: 

    Context: {context}
    """

    return {'system_message': prompt.format(context=context)}

@app.post("/chat_stream")
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
                openai_api_key=os.environ['OPENAI_API_KEY'],
                openai_organization=os.environ['OPENAI_ORG_ID']
            )

            encoding = tiktoken.get_encoding(encoding_name)
            token_limit, num_tokens = 1000, 0
            messages = [SystemMessage(content=chat[0].text), HumanMessage(content=chat[-1].text)]
            for message in reversed(chat[1:-1]):
                num_tokens += 4
                num_tokens += len(encoding.encode(message.text))

                if num_tokens > token_limit:
                    break
                else:
                    new_message = HumanMessage(content=message.text) if message.sender == 'user' else AIMessage(content=message.text)
                    messages = [new_message] + messages

            print(f'Num tokens in call: {num_tokens + len(encoding.encode(messages[0].content))  + len(encoding.encode(messages[-1].content))}')
            llm(messages)

        finally:
            g.close()

    def chat_fn(prompt):
        g = ThreadedGenerator()
        threading.Thread(target=llm_thread, args=(g, prompt)).start()
        return g

    return StreamingResponse(chat_fn(chat), media_type='text/event-stream')
