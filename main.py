import itertools
import json
import os
import time

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from ollama import Client, RequestError, ResponseError
from pydantic import BaseModel

from faq_retrieval import retrieve
from guardrails import apply_input_guards, apply_output_guards

with open("agent_prompt.md", encoding="utf-8") as f:
    AGENT_PROMPT = f.read()

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

ollama_client = Client(
    host=OLLAMA_HOST,
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
)

# --- Multi-chat support (commented out: spec only calls for a single chat interface) ---
# chats = {}
# chat_id_counter = itertools.count(1)
#
# @app.post("/chats")
# async def create_chat():
#     chat_id = next(chat_id_counter)
#     chats[chat_id] = {"title": "New Chat", "messages": {}}
#     return {"id": chat_id, "title": chats[chat_id]["title"]}
#
# @app.get("/chats")
# async def list_chats():
#     return [{"id": chat_id, "title": chat["title"]} for chat_id, chat in chats.items()]
#
# @app.get("/chats/{chat_id}/messages")
# async def get_messages(chat_id: int):
#     if chat_id not in chats:
#         raise HTTPException(status_code=404, detail="Chat not found")
#     return chats[chat_id]["messages"]
#
# @app.post("/chats/{chat_id}/messages")
# async def add_message(chat_id: int, msg: Message):
#     if chat_id not in chats:
#         raise HTTPException(status_code=404, detail="Chat not found")
#
#     chat = chats[chat_id]
#     if not chat["messages"]:
#         chat["title"] = msg.text[:30]
#
#     user_timestamp = time.time()
#     chat["messages"][user_timestamp] = {"role": "user", "text": msg.text}
#
#     def stream_reply():
#         yield json.dumps({"type": "user_timestamp", "timestamp": user_timestamp}) + "\n"
#
#         role = "assistant"
#         full_text = ""
#         try:
#             stream = ollama_client.chat(
#                 model=OLLAMA_MODEL,
#                 messages=[
#                     {"role": m["role"], "content": m["text"]}
#                     for m in chat["messages"].values()
#                     if m["role"] != "error"
#                 ],
#                 stream=True,
#             )
#             for part in stream:
#                 delta = part.message.content
#                 if delta:
#                     full_text += delta
#                     yield json.dumps({"type": "chunk", "role": role, "text": delta}) + "\n"
#         except ResponseError as exc:
#             role = "error"
#             if exc.status_code == 401:
#                 full_text = "Ollama rejected the request: invalid or missing API key. Check OLLAMA_API_KEY in .env."
#             elif exc.status_code == 404:
#                 full_text = f"Model '{OLLAMA_MODEL}' was not found on your Ollama Cloud account."
#             else:
#                 full_text = f"Ollama returned an error ({exc.status_code}): {exc.error}"
#             yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"
#         except (RequestError, httpx.ConnectError, httpx.TimeoutException):
#             role = "error"
#             full_text = f"Could not reach Ollama at {OLLAMA_HOST}. Is the host reachable?"
#             yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"
#         except Exception as exc:
#             role = "error"
#             full_text = f"Unexpected error while contacting Ollama: {exc}"
#             yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"
#
#         reply_timestamp = time.time()
#         chat["messages"][reply_timestamp] = {"role": role, "text": full_text}
#         yield json.dumps({"type": "done", "role": role, "timestamp": reply_timestamp}) + "\n"
#
#     return StreamingResponse(stream_reply(), media_type="application/x-ndjson")


# --- Single chat interface (current spec: POST /chat) ---
messages = {}

class Message(BaseModel):
    text: str

@app.get("/chat/messages")
async def get_messages():
    return messages

@app.post("/chat")
async def chat(msg: Message):
    user_timestamp = time.time()
    input_allowed, processed_text, block_reason = apply_input_guards(msg.text)
    messages[user_timestamp] = {"role": "user", "text": processed_text}

    def stream_reply():
        yield json.dumps({"type": "user_timestamp", "timestamp": user_timestamp}) + "\n"

        role = "assistant"
        full_text = ""

        if not input_allowed:
            role = "error"
            full_text = block_reason
            yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"
            reply_timestamp = time.time()
            messages[reply_timestamp] = {"role": role, "text": full_text}
            yield json.dumps({"type": "done", "role": role, "timestamp": reply_timestamp}) + "\n"
            return

        try:
            faq_matches = retrieve(processed_text)
            if faq_matches:
                context = "\n\n".join(
                    f"Q: {m['question']}\nA: {m['answer']}" for m in faq_matches
                )
            else:
                context = "(No matching FAQ entry was found for this question.)"

            system_prompt = AGENT_PROMPT + "\n\nFAQ context:\n" + context

            stream = ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "system", "content": system_prompt}]
                + [
                    {"role": m["role"], "content": m["text"]}
                    for m in messages.values()
                    if m["role"] != "error"
                ],
                stream=True,
            )
            for part in stream:
                delta = part.message.content
                if delta:
                    full_text += delta
                    yield json.dumps({"type": "chunk", "role": role, "text": delta}) + "\n"
            full_text = apply_output_guards(full_text)
        except ResponseError as exc:
            role = "error"
            if exc.status_code == 401:
                full_text = "Ollama rejected the request: invalid or missing API key. Check OLLAMA_API_KEY in .env."
            elif exc.status_code == 404:
                full_text = f"Model '{OLLAMA_MODEL}' was not found on your Ollama Cloud account."
            else:
                full_text = f"Ollama returned an error ({exc.status_code}): {exc.error}"
            yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"
        except (RequestError, httpx.ConnectError, httpx.TimeoutException):
            role = "error"
            full_text = f"Could not reach Ollama at {OLLAMA_HOST}. Is the host reachable?"
            yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"
        except Exception as exc:
            role = "error"
            full_text = f"Unexpected error while contacting Ollama: {exc}"
            yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"

        reply_timestamp = time.time()
        messages[reply_timestamp] = {"role": role, "text": full_text}
        yield json.dumps({"type": "done", "role": role, "timestamp": reply_timestamp}) + "\n"

    return StreamingResponse(stream_reply(), media_type="application/x-ndjson")

@app.get("/")
async def index():
    return FileResponse("index.html")
