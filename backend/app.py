"""
FastAPI backend for the FAQ chatbot.

The agent network is loaded once at startup as an in-process (library)
neuro-san DirectAgentSession -- no separate neuro-san server process needed.
"""

from typing import Any
from typing import Dict
from typing import Generator
from typing import Optional

import json
import logging
import os
import sys
import time

#setting up path for all components in the Folder System
BACKEND_DIR: str = os.path.dirname(os.path.abspath(__file__))
AGENT_NETWORK_FILE: str = os.path.join(BACKEND_DIR, "agent_network", "faq_chatbot.hocon")
CODED_TOOLS_DIR: str = os.path.join(BACKEND_DIR, "coded_tools")
FRONTEND_DIR: str = os.path.join(os.path.dirname(BACKEND_DIR), "frontend")

#must be set before the coded tools get resolved
os.environ["AGENT_TOOL_PATH"] = CODED_TOOLS_DIR
if CODED_TOOLS_DIR not in sys.path:
    sys.path.insert(0, CODED_TOOLS_DIR)

from dotenv import load_dotenv  
from fastapi import FastAPI, HTTPException  
from fastapi.responses import FileResponse, StreamingResponse  
from pydantic import BaseModel  

from neuro_san.client.direct_agent_session_factory import DirectAgentSessionFactory
from neuro_san.client.streaming_input_processor import StreamingInputProcessor
from neuro_san.interfaces.agent_session import AgentSession

from backend.guardrails import apply_input_guards, apply_output_guards

import faq_index

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("faq_chatbot")

app = FastAPI(title="FAQ Chatbot Backend")

#neuro-san swallows agent errors and returns them as normal text starting with "Error from ", used to detect it as an error
NEURO_SAN_ERROR_PREFIXES = ("Error from ",)

#single shared agent session and conversation for all callers, not per visitor sessions
_session: AgentSession = None
_chat_context: Optional[Dict[str, Any]] = None
_sly_data: Optional[Dict[str, Any]] = None

#timestamp -> role and text for each message
messages: Dict[float, Dict[str, str]] = {}


#builds the faq embedding index and the single agent session used for the lifetime of the process, runs once on startup
@app.on_event("startup")
def load_agent_network() -> None:
    global _session
    logger.info("Building FAQ embedding index...")
    entries, _ = faq_index.ensure_embeddings()
    logger.info("FAQ embedding index ready (%d entries)", len(entries))
    factory = DirectAgentSessionFactory()
    _session = factory.create_session(AGENT_NETWORK_FILE)
    logger.info("Loaded faq_chatbot agent network from %s", AGENT_NETWORK_FILE)


#request payload for post /chat
class Message(BaseModel):
    text: str


#returns the full message log for the single shared conversation
@app.get("/chat/messages")
async def get_messages() -> Dict[float, Dict[str, str]]:
    return messages


#sends a message through guardrails into the agent network and streams the reply back as ndjson
@app.post("/chat")
async def chat(msg: Message) -> StreamingResponse:
    global _chat_context, _sly_data

    user_timestamp = time.time()
    input_allowed, processed_text, block_reason = apply_input_guards(msg.text)
    messages[user_timestamp] = {"role": "user", "text": processed_text}

    #generator that streams the ndjson response chunks back to the client
    def stream_reply() -> Generator[str, None, None]:
        global _chat_context, _sly_data

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
            input_processor = StreamingInputProcessor(session=_session)
            input_processor.reset()
            chat_request = input_processor.formulate_chat_request(
                processed_text, sly_data=_sly_data, chat_context=_chat_context
            )
            message_processor = input_processor.get_message_processor()

            prev_compiled = ""
            for chat_response in _session.streaming_chat(chat_request):
                response = chat_response.get("response", {})
                message_processor.process_message(response)

                compiled = message_processor.get_compiled_answer() or ""
                if role != "error" and compiled.startswith(NEURO_SAN_ERROR_PREFIXES):
                    role = "error"
                if compiled != prev_compiled and compiled.startswith(prev_compiled):
                    delta = compiled[len(prev_compiled):]
                    prev_compiled = compiled
                    if delta:
                        full_text += delta
                        yield json.dumps({"type": "chunk", "role": role, "text": delta}) + "\n"
                elif compiled != prev_compiled:
                    # Compiled answer was rewritten rather than extended (rare);
                    # fall back to sending the new text as a fresh chunk.
                    prev_compiled = compiled
                    full_text = compiled
                    yield json.dumps({"type": "chunk", "role": role, "text": compiled}) + "\n"

            _chat_context = message_processor.get_chat_context()
            returned_sly_data = message_processor.get_sly_data()
            if returned_sly_data:
                _sly_data = {**(_sly_data or {}), **returned_sly_data}

            if not full_text:
                full_text = "(The agent did not return a response.)"
                yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"

            full_text = apply_output_guards(full_text)
        except Exception as exc:
            logger.exception("Agent network call failed")
            role = "error"
            full_text = f"Agent network error: {exc}"
            yield json.dumps({"type": "chunk", "role": role, "text": full_text}) + "\n"

        reply_timestamp = time.time()
        messages[reply_timestamp] = {"role": role, "text": full_text}
        yield json.dumps({"type": "done", "role": role, "timestamp": reply_timestamp}) + "\n"

    return StreamingResponse(stream_reply(), media_type="application/x-ndjson")


#basic liveness check
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

#serves the static HTML file for the chatbot
@app.get("/")
async def index() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
