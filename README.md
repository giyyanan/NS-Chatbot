# NS-Chatbot

An FAQ chatbot built on [neuro-san](https://github.com/cognizant-ai-lab/neuro-san),
Cognizant's data-driven multi-agent framework. A static HTML/JS chat UI talks
to a FastAPI backend, which drives a neuro-san agent network to answer
questions grounded in whatever FAQ dataset(s) are dropped into `data/`
(ships with `data/BankFAQ.csv`, a bank customer-support dataset, as an
example).

## Motivation

Point a single LLM call at "does the FAQ actually say that?" and it will
answer fluently whether or not it's right — a bank customer asking about
card-replacement fees or loan eligibility needs an answer grounded in an
actual policy entry, not a plausible-sounding guess. The system also has to
hold that line under adversarial pressure: users trying to talk the bot into
ignoring its instructions, or pasting sensitive data into the chat where it
shouldn't be logged or forwarded.

## Solution

Ground every answer in retrieval over the real FAQ dataset instead of model
memory, drive that retrieval + LLM loop through a neuro-san agent network
rather than hand-rolled chat logic, and put input/output guardrails between
the untrusted user and the agent. The frontend never talks to neuro-san
directly — only the FastAPI backend does, and it's the only thing that calls
into the agent network.

## Features

- **Multi-turn conversation** via a neuro-san agent network — state threaded
  through neuro-san's `chat_context` between turns, not reimplemented in the
  backend.
- **Semantic retrieval, no vector DB** — embeddings-based search over any
  `.csv`/`.json` FAQ file dropped into `data/`, columns auto-detected by
  header/key name, cached and rebuilt automatically when `data/` changes.
- **Guardrails** — input-side prompt-injection blocking and PII redaction,
  output-side PII redaction, applied at the FastAPI layer around the agent
  call.
- **Streaming UI** — NDJSON response stream rendered incrementally in the
  browser with a typing indicator, distinct error-bubble styling for
  blocked/failed requests.
- **Retrieval evaluation harness** (`eval/`) — measures recall@k and
  per-category precision/recall against a synthetic labeled question set.

## Quick Start

### Prerequisites

- Python 3.10+
- A local Ollama daemon

### Prep

```bash
ollama pull embeddinggemma     # used for FAQ retrieval
ollama serve                   # if not already running as a service
ollama signin                  # once, to authorize the cloud LLM below
```

### Install & run

```bash
# From the repo root
pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/** in a browser and start chatting. The first
request builds the embedding cache for whatever's in `data/` (slow, one
time); to pre-warm it ahead of time instead, run
`python eval/scratch_build_embeddings.py` before starting the backend.

All paths in `backend/agent_network/faq_chatbot.hocon` and the coded tools
are relative to the repo root / their own file location, so this works from
a fresh clone regardless of where the repo lives on disk — just launch
`uvicorn` from the repo root as shown above.

### Run with Docker instead

```bash
docker compose up
```

No Ollama install, `ollama pull`, or credentials needed — the stack brings
up its own `ollama` daemon, pulls `embeddinggemma` (retrieval) and
`qwen2.5:7b` (chat, a local fallback for the cloud model below) into it, and
then starts the app on **http://localhost:8000/**. Everything runs offline.

To use the cloud model (`gpt-oss:20b-cloud`, the default in
`faq_chatbot.hocon`) instead of the local fallback, copy `.env.example` to
`.env` and set `OLLAMA_API_KEY` (from https://ollama.com → Settings → API
keys) and `OLLAMA_MODEL=gpt-oss:20b-cloud` — this authenticates the
containerized Ollama daemon non-interactively, since the usual
`ollama signin` device-code flow can't run headless. `.env` is gitignored;
never commit real keys.

## How it works

- **Dataset**: any `.csv` or `.json` file in `data/` with question/answer
  (and optionally category) columns — auto-detected by header/key name
  (e.g. `question`/`q`/`query`, `answer`/`a`/`response`, `category`/`class`/
  `topic`). Ships with `data/BankFAQ.csv` (bank customer-support Q&A) as an
  example; drop in another CSV/JSON and it's picked up automatically.
- **Retrieval**: `backend/coded_tools/faq_index.py` discovers and embeds
  every FAQ file in `data/`, caching the result and rebuilding automatically
  whenever `data/` changes (a SHA-256 fingerprint over file name/size/mtime
  decides cache validity). `backend/coded_tools/faq_retriever.py` is the
  neuro-san `CodedTool` (`FaqRetriever`) that does the embeddings-based
  semantic search against that cache, exposed to the agent as `faq_search`.
- **Agent network**: `backend/agent_network/faq_chatbot.hocon` defines a
  single front-man agent (`faq_bot`) that calls `faq_search` for every
  customer question and answers only from what the tool returns.
- **Guardrails**: `backend/guardrails.py` + `backend/guardrails-config.yaml`
  apply input-side prompt-injection blocking and PII redaction, and
  output-side PII redaction, at the FastAPI layer.
- **LLM**: `gpt-oss:20b-cloud`, run through the local Ollama daemon (signed
  in via `ollama signin`), configured via
  `backend/agent_network/faq_llm_info.hocon`. No API key needed.

## Advanced concepts

### Coded Tools

`FaqRetriever` (`backend/coded_tools/faq_retriever.py`) is a neuro-san
`CodedTool` — Python code the agent network can call for things an LLM can't
do reliably on its own, here a deterministic embeddings search. It's
declared in `faq_chatbot.hocon` and resolved at startup via the
`AGENT_TOOL_PATH` environment variable, which `backend/app.py` points at
`backend/coded_tools/` before the agent network loads.

### Conversation state and sly_data

Multi-turn state is threaded via neuro-san's `chat_context`, returned by the
agent network after each turn and passed back in on the next one —
`backend/app.py` keeps it server-side between requests rather than the
frontend managing history itself. neuro-san also offers a parallel `sly_data`
channel for private data that should never enter the chat stream (tokens,
session ids, etc.); this backend threads it through end-to-end, though the
current `faq_search` tool doesn't read or write it — the channel is wired up
and ready for a future coded tool that needs it.

This backend runs a single shared conversation rather than per-visitor
sessions (`_chat_context`/`_sly_data`/`messages` are process-global in
`app.py`) — a deliberate scope decision for this project, not an oversight.

## Testing

`tests/test_app.py` — a pytest suite against the FastAPI app using a fake
agent session, covering: a normal streamed reply, the empty-response
fallback, prompt-injection blocked before the agent is ever called, PII
redacted before the agent call, agent-network exceptions surfaced as an
error bubble, and `chat_context` threading across turns.

```bash
pip install pytest
pytest tests/
```

## Evaluation

`eval/` — a retrieval evaluation harness, independent of the running
backend:

- `generate_eval_questions.py` uses an LLM to synthesize a labeled question
  set (`eval_questions.json`) across the FAQ categories plus off-topic
  "none" cases.
- `evaluate_retrieval.py` reports precision/recall/F1 per category plus
  embedding/search latency percentiles.
- `recall_at_k.py` reports recall@k (1/3/5/10) — whether the correct
  category shows up anywhere in the top-k results, not just the top-1.

```bash
pip install -r eval/requirements.txt
python eval/evaluate_retrieval.py
python eval/recall_at_k.py
```
