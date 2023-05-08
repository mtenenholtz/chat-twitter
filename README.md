# Chat With the Algorithm

Ask questions about the open-sourced [Twitter algorithm](https://github.com/twitter/the-algorithm).

The app is publicly hosted here: https://chat-twitter.vercel.app/. Instructions for hosting it yourself are below.

## Basic architecture

The app is a NextJS/Tailwind CSS frontend with a FastAPI backend. The frontend is hosted on Vercel and the backend is hosted on a small node on [fly.io](https://fly.io/). The backend uses a Pinecone vector DB on the free tier. There is a Dockerfile provided.

Right now, I'm footing the OpenAI bill on the public instance. But I may require users to bring their own key in the future.

## Running locally

1. Clone the repo

```
git clone https://github.com/mtenenholtz/chat-twitter.git
cd chat-twitter
```

2. Install Node dependencies

```
npm i
```

3. Run the Node server

```
npm run dev
```

4. In another terminal, install the Python dependencies

```
# switch to the the backend/ directory and install the required libraries
cd backend 
pip install -r requirements.txt
```

5. Set up environment variables

Copy the .env-template file to create a .env file using the following command:
```bash
cp .env-template .env
```

Update the .env file with your values:
Replace the placeholder values with your actual API keys, organization ID, and other configuration values as needed. Save the file when you're done.


6. Set up a Pinecone index. Give it a vector dimension of 1536, use cosine for the similarity metric and name it `pinecone-index`. You can change the index name in the `.env` file if you want.


7. Embed the Twitter codebase

```
# still in the backend/ directory
python create_vector_db.py
```

8. Run the backend server

```
uvicorn main:app --reload
```

9. The URL for the backend is currently hard coded to the live server URL. You will have to change this to localhost or your other server name. This can be done in the `.env.local` file in the root directory of your project.

## Potential improvements

I will continue development on this project as demand exists. But, if I abandon it, here are some ideas:

- The dependency on Pinecone could be removed and replaced with a simple NumPy array. I just wanted to try Pinecone.
- Replace the `chat_stream` endpoint with a websocket implementation.
- Ask the model not to generatively reference its sources. Instead, simply copy the code snippet directly.
- The splitter could be improved. Right now, it's a character splitter that favors newlines, but OpenAI has implemented a similar one that splits on tokens instead.
- The embeddings and retrieval mechanisms could account for the hierarchy of the Algorithm's code structure, like Replit's Ghostwriter does.
- The UI could be improved **a lot**. I suck at JS.