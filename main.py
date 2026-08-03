import itertools
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from ollama import Client, RequestError, ResponseError
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

ollama_client = Client(
    host=OLLAMA_HOST,
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
)

chats = {}
chat_id_counter = itertools.count(1)

class Message(BaseModel):
    text: str

@app.post("/chats")
async def create_chat():
    chat_id = next(chat_id_counter)
    chats[chat_id] = {"title": "New Chat", "messages": []}
    return {"id": chat_id, "title": chats[chat_id]["title"]}

@app.get("/chats")
async def list_chats():
    return [{"id": chat_id, "title": chat["title"]} for chat_id, chat in chats.items()]

@app.get("/chats/{chat_id}/messages")
async def get_messages(chat_id: int):
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chats[chat_id]["messages"]

@app.post("/chats/{chat_id}/messages")
async def add_message(chat_id: int, msg: Message):
    if chat_id not in chats:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = chats[chat_id]
    if not chat["messages"]:
        chat["title"] = msg.text[:30]

    chat["messages"].append({"role": "user", "text": msg.text})

    role = "assistant"
    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": m["role"], "content": m["text"]}
                for m in chat["messages"]
                if m["role"] != "error"
            ],
        )
        reply = response.message.content
    except ResponseError as exc:
        role = "error"
        if exc.status_code == 401:
            reply = "Ollama rejected the request: invalid or missing API key. Check OLLAMA_API_KEY in .env."
        elif exc.status_code == 404:
            reply = f"Model '{OLLAMA_MODEL}' was not found on your Ollama Cloud account."
        else:
            reply = f"Ollama returned an error ({exc.status_code}): {exc.error}"
    except (RequestError, httpx.ConnectError, httpx.TimeoutException):
        role = "error"
        reply = f"Could not reach Ollama at {OLLAMA_HOST}. Is the host reachable?"
    except Exception as exc:
        role = "error"
        reply = f"Unexpected error while contacting Ollama: {exc}"

    chat["messages"].append({"role": role, "text": reply})
    return chat["messages"]

@app.get("/")
async def index():
    return FileResponse("index.html")
