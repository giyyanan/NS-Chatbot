# NS Chatbot

Your FAQ assistant for banking, built to answer customer support questions
straight from a static FAQ dataset — no hallucinated policies, no made-up
numbers, just grounded answers with a warm, human tone and real multi-turn
conversation.

> 🚧 **Status:** This is a baseline implementation built **without Neuro-SAN**.
> Multi-turn history is currently handled with a plain in-memory message list
> replayed to the LLM on each call, not an agentic network. Neuro-SAN
> integration is the planned next step — the eval framework in this repo
> exists specifically to produce a before/after comparison once that
> happens. This README will be rewritten once Neuro-SAN is integrated.

## What is NS Chatbot?

NS Chatbot is a full-stack RAG chatbot: a FastAPI backend retrieves the most
relevant entries from a static FAQ dataset (`BankFAQs.csv`) using semantic
embeddings, hands that context to an LLM along with a warm, tightly-scoped
system prompt, and streams the answer back to a minimal chat UI. Guardrails
sit on both sides of the LLM call to block prompt injection and redact PII,
so it stays safe to expose to real customers even without a fine-tuned model.

## ✨ Key Features

- 🧠 **Semantic FAQ retrieval** — embeds every question with a local Ollama
  model (`embeddinggemma`) and ranks by cosine similarity, not keyword
  matching, so typos and paraphrased questions still find the right answer
- 💬 **Multi-turn chat** — full conversation history replayed to the LLM on
  every call, streamed back as NDJSON with a live typing indicator
- 🔒 **Guardrails** — regex-based prompt-injection blocking and PII
  redaction on input (and optionally output), fully configured via
  `guardrails-config.yaml`, no code changes needed to tune
- 🎭 **On-brand persona** — `agent_prompt.md` keeps the assistant warm and
  conversational while staying strictly scoped to the FAQ dataset; the
  security rules in it can't be overridden by anything a user types
- 🧪 **Built-in evaluation** — a 2000-question, LLM-generated test set
  (`eval_questions.json`) measures retrieval precision/recall per category
  plus a latency breakdown (embedding call vs local search), so retrieval
  quality is a number, not a guess
- 🐳 **Dockerized + CI/CD** — GitHub Actions runs the test suite on every
  push/PR and pushes a Docker image to DockerHub on `master`

## High-level Architecture

```
Browser (index.html)
    |  fetch() -> streamed NDJSON
    v
FastAPI backend (main.py)
    |
    |-- Input guardrails (guardrails.py) -- block prompt injection, redact PII
    |
    |-- FAQ retrieval (faq_retrieval.py) -- semantic search over BankFAQs.csv
    |       embeds the query with a local Ollama model (embeddinggemma),
    |       cosine-similarity against a precomputed embedding cache
    |
    |-- LLM call -- Ollama Cloud if OLLAMA_API_KEY is set, otherwise a local
    |       Ollama model (llama3.2:3b by default) -- agent_prompt.md as the
    |       system prompt + retrieved FAQ context + conversation history
    |
    |-- Output guardrails (guardrails.py) -- redact PII (currently disabled)
    v
Streamed response back to the browser
```

## Quick start

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Configure environment
FAQ retrieval always embeds locally (a local Ollama server with
`embeddinggemma` pulled). Chat generation has two modes, chosen automatically
by whether `OLLAMA_API_KEY` is set:

- **Cloud** (if you have an Ollama Cloud API key) — set `OLLAMA_API_KEY` and
  it'll be used for chat, going to `OLLAMA_HOST`/`OLLAMA_MODEL`.
- **Local** (no API key needed) — leave `OLLAMA_API_KEY` unset and chat falls
  back to a local Ollama model (`LOCAL_OLLAMA_MODEL`, default `llama3.2:3b`).
  Slower on CPU-only hardware, but works fully offline.

Create a `.env` file — cloud example:
```
OLLAMA_API_KEY=your_ollama_cloud_api_key
OLLAMA_HOST=https://ollama.com
OLLAMA_MODEL=gpt-oss:20b
RETRIEVAL_TOP_K=10
```
Local-only example (just omit `OLLAMA_API_KEY`):
```
LOCAL_OLLAMA_MODEL=llama3.2:3b
RETRIEVAL_TOP_K=10
```

### 3. Set up local embeddings
```
ollama pull embeddinggemma
```
If running chat locally too (no `OLLAMA_API_KEY`), also pull the chat model:
```
ollama pull llama3.2:3b
```
The FAQ embedding cache (`faq_embeddings_embeddinggemma.npy`) is already
committed. To rebuild it after changing `BankFAQs.csv`:
```
python3 scratch_build_embeddings.py
```

### 4. Run it
```
uvicorn main:app --reload
```
Open `http://localhost:8000`.

### Or run it with Docker
```
docker compose up --build
```
The image bundles Ollama itself and always pulls `embeddinggemma` on first
start, so FAQ retrieval works fully offline inside the container. For chat,
the entrypoint checks `OLLAMA_API_KEY` (from `.env`, passed through via
`env_file`): if it's set, chat goes to Ollama Cloud and no local chat model is
pulled; if it's absent, the entrypoint also pulls `LOCAL_OLLAMA_MODEL`
(default `llama3.2:3b`) and chat runs fully locally. A named volume
(`ollama_data`) caches pulled models so they aren't re-downloaded on restart.

## Testing

| Suite | What it checks | Speed |
|---|---|---|
| `pytest test_main.py -v` | API behavior — chat flow, guardrails, error handling, all mocked | Fast (~1s), safe for CI |
| `python3 evaluate_retrieval.py` | Retrieval quality — precision/recall per FAQ category + latency breakdown, against 2000 real questions | Slow (~15 min), run manually |

Install test dependencies first: `pip install -r requirements-dev.txt`

**Current baseline (pre-Neuro-SAN):** ~47.8% top-1 category accuracy, ~743ms
average retrieval latency (94% of which is the embedding API call itself,
6% local cosine search).

## CI/CD

`.github/workflows/ci.yml` runs the test suite on every push/PR to `master`,
then builds and pushes a Docker image to `<DOCKERHUB_USERNAME>/ns-chatbot` on pushes to
`master` — requires `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` secrets configured
on the repo; the push step skips gracefully if they're absent.

## Known limitations

- 🕸️ **No Neuro-SAN yet** — multi-turn history is a plain list replayed to
  the LLM, not an agentic network. Planned next.
- 🖼️ **No separate frontend Dockerfile** — the frontend is currently served
  as a static file by the backend container.
- 📉 **Uneven retrieval accuracy** — see `evaluate_retrieval.py` output for
  the full per-category breakdown (`accounts` and off-topic rejection are
  the weakest areas currently).
- 🐢 **Local chat mode is slow on CPU-only hardware** — with no
  `OLLAMA_API_KEY`, chat falls back to a local model (`llama3.2:3b` by
  default); expect ~15-40s per response without a GPU, versus much faster
  cloud responses.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | FastAPI backend, `/chat` endpoint, guardrail + retrieval wiring |
| `index.html` | Frontend chat UI |
| `faq_retrieval.py` | Semantic FAQ retrieval (embeddings + cosine similarity) |
| `agent_prompt.md` | System prompt: persona, scope, security rules |
| `guardrails.py` / `guardrails-config.yaml` | Prompt-injection and PII guardrails |
| `BankFAQs.csv` | FAQ dataset (question/answer/category) |
| `faq_embeddings_embeddinggemma.npy` | Precomputed FAQ embeddings cache |
| `test_main.py` | API test suite (pytest, mocked Ollama calls) |
| `evaluate_retrieval.py` / `eval_questions.json` | Retrieval quality eval framework |
| `scratch_generate_eval_questions.py` | Generates the eval question set |
| `scratch_build_embeddings.py` | Builds/rebuilds the embedding cache |
