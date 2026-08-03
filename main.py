import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

messages = {}

class Message(BaseModel):
    text: str

@app.post("/messages")
async def add_message(msg: Message):
    timestamp = time.time()
    messages[timestamp] = msg.text
    return {"timestamp": timestamp, "text": msg.text}

@app.get("/messages")
async def get_messages():
    return messages

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
    <head><title>Chat</title></head>
    <body>
        <div id="chat" style="margin-bottom:10px;"></div>
        <input id="input" type="text" placeholder="Type a message">
        <button onclick="send()">Send</button>

        <script>
            async function send() {
                const input = document.getElementById("input");
                const text = input.value;
                if (!text) return;
                await fetch("/messages", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({text: text})
                });
                input.value = "";
                loadMessages();
            }

            async function loadMessages() {
                const res = await fetch("/messages");
                const data = await res.json();
                const chat = document.getElementById("chat");
                chat.innerHTML = Object.entries(data)
                    .sort((a, b) => a[0] - b[0])
                    .map(([ts, text]) => `<div>${text}</div>`)
                    .join("");
            }

            loadMessages();
        </script>
    </body>
    </html>
    """
