import itertools

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

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
    chat["messages"].append({"role": "assistant", "text": "This is a placeholder response."})
    return chat["messages"]

@app.get("/")
async def index():
    return FileResponse("index.html")
