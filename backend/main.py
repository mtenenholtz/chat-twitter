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

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

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
    environment=os.environ['PINECONE_ENVIRONMENT']
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

def format_query(query, context):
    return f"""Relevant context: {context}
    
    {query}"""

def embedding_search(query, k):
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.environ['OPENAI_API_KEY'],
        openai_organization=os.environ['OPENAI_ORG_ID'],
    )
    db = Pinecone(
        index=os.environ['PINECONE_INDEX'],
        embedding_function=embeddings.embed_query,
        text_key='text',
        namespace=os.environ['PINECONE_NAMESPACE']
    )

    return db.similarity_search(query, k=k)

@app.get("/health")
def health():
    return "OK"

@app.post("/system_message", response_model=ContextSystemMessage)
def system_message(query: Message):
    docs = embedding_search(query.text, k=os.environ['NUM_RELEVANT_DOCS'])
    context = format_context(docs)

    prompt = """Given the following context and code, answer the following question. Do not use outside context, and do not assume the user can see the provided context. Try to be as detailed as possible and reference the components that you are looking at. Keep in mind that these are only code snippets, and more snippets may be added during the conversation.
    Do not generate code, only reference the exact code snippets that you have been provided with. If you are going to write code, make sure to specify the language of the code. For example, if you were writing Python, you would write the following:

    ```python
    <python code goes here>
    ```
    
    Now, here is the relevant context: 

    Context: {context}
    """

    return {'system_message': prompt.format(context=context)}

@app.post("/chat_stream")
async def chat_stream(chat: List[Message]):
    model_name = os.environ['MODEL_NAME']
    encoding_name = os.environ['ENCODING_NAME']

    def llm_thread(g, prompt):
        try:
            llm = ChatOpenAI(
                model_name=model_name,
                verbose=True,
                streaming=True,
                callback_manager=CallbackManager([ChainStreamHandler(g)]),
                temperature=os.environ['TEMPERATURE'],
                openai_api_key=os.environ['OPENAI_API_KEY'],
                openai_organization=os.environ['OPENAI_ORG_ID']
            )

            encoding = tiktoken.get_encoding(encoding_name)

            # the system message gets NUM_RELEVANT_DOCS new docs. Only include NUM_RELEVANT_FOLLOWUP_DOCS more for new queries
            if len(chat) > os.environ['NUM_RELEVANT_FOLLOWUP_DOCS']:
                system_message, latest_query = [chat[0].text, chat[-1].text]
                keep_messages = [system_message, latest_query]
                new_messages = []

                token_count = sum([len(encoding.encode(m)) for m in keep_messages])
                # fit in as many of the previous human messages as possible
                for message in chat[1:-1:2]:
                    token_count += len(encoding.encode(message.text))

                    if token_count > os.environ['MAX_HUMAN_TOKENS']:
                        break

                    new_messages.append(message.text)
                    
                query_messages = [system_message] + new_messages + [latest_query]
                query_text = '\n'.join(query_messages)

                # add some more context
                docs = embedding_search(query_text, k=os.environ['NUM_RELEVANT_FOLLOWUP_DOCS'])
                context = format_context(docs)
                formatted_query = format_query(latest_query, context)
            else:
                formatted_query = chat[-1].text

            # always include the system message and the latest query in the prompt
            system_message = SystemMessage(content=chat[0].text)
            latest_query = HumanMessage(content=formatted_query)
            messages = [latest_query]

            # for all the rest of the messages, iterate over them in reverse and fit as many in as possible
            token_limit = os.environ['MAX_TOKENS']
            num_tokens = len(encoding.encode(chat[0].text)) + len(encoding.encode(formatted_query))
            for message in reversed(chat[1:-1]):
                # count the number of new tokens
                num_tokens += os.environ['TOKENS_PER_MESSAGE']
                num_tokens += len(encoding.encode(message.text))

                if num_tokens > token_limit:
                    # if we're over the token limit, stick with what we've got
                    break
                else:
                    # otherwise, add the new message in after the system prompt, but before the rest of the messages we've added
                    new_message = HumanMessage(content=message.text) if message.sender == 'user' else AIMessage(content=message.text)
                    messages = [new_message] + messages

            # add the system message to the beginning of the prompt
            messages = [system_message] + messages

            llm(messages)

        finally:
            g.close()

    def chat_fn(prompt):
        g = ThreadedGenerator()
        threading.Thread(target=llm_thread, args=(g, prompt)).start()
        return g

    return StreamingResponse(chat_fn(chat), media_type='text/event-stream')
