# NS-Chatbot

A bank FAQ chatbot: a plain HTML/JS chat UI talking to a FastAPI backend,
which in turn drives a [neuro-san](https://github.com/cognizant-ai-lab/neuro-san)
agent network to answer questions grounded in a real FAQ dataset
(`data/BankFAQ.csv`, sourced from the [Kaggle BankFAQs
dataset](https://www.kaggle.com/datasets/somanathkshirasagar/bankfaqs)).
Answers come from retrieval over that dataset, not the model's memory, and
the whole conversation is wrapped in guardrails against prompt injection
and PII leakage.

## Deliverables

- **GitHub repo**: [github.com/giyyanan/NS-Chatbot](https://github.com/giyyanan/NS-Chatbot),
  branch `faqChatBot`.
- **Dockerfile(s)**: just one, [`Dockerfile`](Dockerfile), plus
  [`docker-compose.yml`](docker-compose.yml) for a one-command offline run
  with its own Ollama daemon. The backend serves the frontend directly
  (`GET /` in `app.py`), so splitting into a second container for a single
  static HTML file would only add a CORS setup and a parameterized
  frontend URL for no real benefit — see [Running with
  Docker](#running-with-docker).
- **GitHub Actions**: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
  — runs the test suite on every push/PR, builds the image, and pushes to
  Docker Hub on `main` once the right secrets are set.
- **README**: this file.
- **Docker Hub image**:
  [giyyananv/ns-chatbot](https://hub.docker.com/repository/docker/giyyananv/ns-chatbot/general).

## Features

- **Multi-turn conversation** through neuro-san itself — `chat_context`
  gets threaded between turns by the session layer, nothing hand-rolled in
  the backend.
- **Semantic retrieval without a vector DB** — embeddings-based search over
  whatever `.csv`/`.json` FAQ file lands in `data/`, columns detected
  automatically, backed by a pre-built embedding cache checked into the
  repo.
- **Guardrails** on both ends — prompt-injection blocking and PII
  redaction on the way in, PII redaction on the way out, all sitting in
  the FastAPI layer around the agent call.
- **A streaming UI** — replies come back as NDJSON and render
  incrementally with a typing indicator; blocked or failed requests get
  their own error-bubble styling.
- **A retrieval eval harness** (`eval/`) for recall@k and per-category
  precision/recall against a synthetic labeled question set.

## Agent Network Architecture

The full path a message takes, end to end — the network itself,
the LLM behind it, how it reaches the FAQ data, and how the backend
bridges the two.

### Network Structure

The agent network lives in `backend/agent_network/faq_chatbot.hocon`. It's
deliberately small: one front-man agent, `faq_bot`, wired to a single tool,
`faq_search`. `faq_bot`'s instructions hold everything about how it should
behave the tone, what it's allowed to talk about, and a set of security
rules around prompt injection and reproducing its own system prompt.
`faq_search` is the only way it's allowed to get facts.

Multi-turn conversation isn't something the backend implements. It's
neuro-san's own session state. `app.py` never stores or replays prior
messages by hand. Each `/chat` call builds a request through
`StreamingInputProcessor`, passing along whatever `chat_context`/`sly_data`
came back from the *previous* turn. Once `faq_bot` responds,
`message_processor.get_chat_context()` hands back an updated context,
which gets stored and fed into the next call. That round-trip is what
lets someone ask "what about the fee?" after asking about a lost card,
and have `faq_bot` correctly resolve "the fee" against what was said a
turn earlier — the backend is just the courier, not the memory.

### LLM Configuration

The network runs on Ollama — local daemon or Ollama Cloud, picked via two
config files:

- `faq_chatbot.hocon`'s `llm_config` sets `model_name` and `base_url`,
  each written twice: a hardcoded default, followed by `${?OLLAMA_MODEL}`
  / `${?OLLAMA_BASE_URL}`. HOCON's optional-substitution syntax silently
  drops that second line if the env var isn't set (rather than resolving
  it to null), so this reads as "use the default unless an env var says
  otherwise" in two lines, no conditionals needed.
- `faq_llm_info.hocon` registers the actual model entries
  (`gpt-oss:20b-cloud`, `gpt-oss:120b-cloud`, `qwen2.5:7b`) that
  `model_name` can point at. This file exists because Ollama isn't in
  neuro-san's built-in model catalog. Anything referenced in
  `llm_config` needs a matching entry here (provider class, context
  window, capabilities) or the network refuses to load.

### FAQ Data Retrieval

`faq_search` is a neuro-san `CodedTool` — plain Python the agent calls for
something an LLM shouldn't try to do on its own, here a deterministic
embeddings search. It's implemented as `FaqRetriever` in
`backend/coded_tools/faq_retriever.py`, declared in `faq_chatbot.hocon`'s
`tools` list, and resolved at startup through the `AGENT_TOOL_PATH`
environment variable, which `app.py` points at `backend/coded_tools/`
before the network loads.

There's no vector database involved. Retrieval is a pre-built embedding
cache (`data/faq_embeddings_embeddinggemma.npy`) plus a plain numpy
cosine-similarity search. `backend/coded_tools/faq_index.py` auto-discovers
every `.csv`/`.json` file in `data/`, detects the question/answer/category
columns by header name, and loads the cache alongside them. When `faq_bot`
calls `faq_search` with a query, `FaqRetriever` embeds it, ranks every FAQ
entry by cosine similarity, and returns the top, score-thresholded matches
as plain text — `faq_bot`'s instructions then require it to answer only
from what that tool call returned, never from its own training data.

### Backend Integration — `POST /chat`

`app.py` never talks to an LLM directly; its job is guardrails plus wiring
the frontend to neuro-san. Per request:

1. Guardrails run first — prompt-injection blocking and PII redaction —
   before the agent network is touched at all.
2. If the message passes, the in-process `DirectAgentSession` (built once
   at startup, no separate neuro-san server) turns it into a chat request
   via `StreamingInputProcessor`, carrying forward `chat_context`/
   `sly_data` from the previous turn.
3. `session.streaming_chat(...)` yields responses incrementally;
   `message_processor.get_compiled_answer()` is polled on each one, and
   just the new text is streamed to the frontend as an NDJSON chunk — so
   the UI renders the reply as it's generated instead of waiting for the
   whole thing.
4. Once the agent's done, `apply_output_guards` redacts any PII in the
   final text, and the turn's `chat_context`/`sly_data` are saved for the
   next call.

That's the whole loop: the frontend only ever sees `/chat`'s NDJSON
stream. Everything about how the answer got grounded — the multi-turn
memory, the LLM call, the retrieval tool call — happens inside neuro-san,
orchestrated entirely by `faq_chatbot.hocon`.

## Setup

### Prerequisites

- Python 3.10+
- Ollama, installed and running locally

The backend expects Ollama to already be installed, running, and signed
in before it starts — it won't do any of that for you. (Docker Compose is
the one exception: it spins up and provisions its own Ollama daemon, so
none of this section applies there.)

#### Installing Ollama

It's a native install, not something pip handles:

- **macOS / Windows**: grab the installer from https://ollama.com/download.
- **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`.

On macOS/Windows this also gives you a background app that keeps the
daemon running; on Linux it registers `ollama.service` with systemd
instead. Once it's in, `ollama --version` should just work.

#### Authenticating with Ollama Cloud

The chat model here (`gpt-oss:*-cloud`) runs through Ollama Cloud, so the
daemon needs to be signed in — the local `embeddinggemma`/`qwen2.5:7b`
models don't need this at all. Run:

```bash
ollama signin
```

It prints a short code and a URL — open that in a browser, log into (or
create) an Ollama account, and enter the code. It's a one-time thing per
machine; nothing gets stored in this repo, the session just lives with
the local daemon. `ollama auth status` will confirm it worked. None of
this applies inside Docker Compose — see [Running with
Docker](#running-with-docker) for the headless equivalent
(`OLLAMA_API_KEY`).

### Running Locally

```bash
ollama pull embeddinggemma     # needed for FAQ retrieval
ollama serve                   # if it's not already running as a service
ollama signin                  # once, for the cloud model above
```

Then:

```bash
# from the repo root
pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/** and start chatting. The embedding cache
for `data/BankFAQ.csv` is already committed, so startup just loads it. 
No Ollama call needed to boot, and it's fast. If you change what's in
`data/` (add or edit a FAQ file), rebuild the cache with `python
eval/scratch_build_embeddings.py` — the backend won't do this for you
automatically, and it'll raise a clear error at startup if the cache and
the data are out of sync.

Everything in `backend/agent_network/faq_chatbot.hocon` and the coded
tools resolves paths relative to the repo root or the file's own
location, so this works from a fresh clone no matter where it lives on
disk . Just run `uvicorn` from the repo root.

### Running with Docker

```bash
docker compose up
```

No install, no `ollama pull`, no credentials — the stack brings up its
own `ollama` container, pulls `embeddinggemma` for retrieval and
`qwen2.5:7b` for chat (a local, no-signup fallback), and starts the app at
**http://localhost:8000/**. Fully offline.

If you'd rather use the cloud model (`gpt-oss:120b-cloud`, the actual
default in `faq_chatbot.hocon`), copy `.env.example` to `.env` and set
`OLLAMA_API_KEY` (get one from https://ollama.com → Settings → API keys)
and `OLLAMA_MODEL=gpt-oss:120b-cloud`. This is how the containerized
daemon authenticates without the usual `ollama signin` flow, which can't
run headless. `.env` is gitignored — don't commit real keys.

## Project Structure

- **`backend/`** — the FastAPI service.
  - `app.py` — the API itself (`POST /chat`, `GET /chat/messages`,
    `GET /health`, `GET /`). Loads the agent network once at startup as an
    in-process neuro-san `DirectAgentSession`.
  - `guardrails.py` + `guardrails-config.yaml` — regex-based
    prompt-injection blocking and PII redaction around the agent call.
  - `agent_network/faq_chatbot.hocon` — the agent network itself: one
    front-man agent (`faq_bot`) wired to the `faq_search` tool.
  - `agent_network/faq_llm_info.hocon` — registers the Ollama models
    neuro-san can route to (cloud default, local fallback).
  - `coded_tools/faq_index.py` — finds every FAQ file in `data/` and loads
    the pre-built embedding cache next to them (built offline by
    `eval/scratch_build_embeddings.py`, never regenerated at startup).
  - `coded_tools/faq_retriever.py` — the `faq_search` tool: embeddings-based
    search over that cache.
- **`frontend/index.html`** — the whole UI. No build step, no framework,
  just one file.
- **`data/`** — the FAQ dataset(s) plus the embedding cache `faq_index.py`
  keeps alongside them.
- **`eval/`** — the retrieval eval harness, independent of the running
  backend. More on this in [Evaluation](#evaluation).
- **`tests/`** — the pytest suite: mocked app/guardrail tests plus one
  live sanity check against the real agent network. More on this in
  [Testing](#testing).
- **`Dockerfile`, `docker-compose.yml`, `.dockerignore`** — the
  containerized backend plus a self-contained Ollama daemon.
- **`.github/workflows/ci.yml`** — runs the tests on every push/PR, builds
  the image, and pushes to Docker Hub on `main` if the right secrets are
  configured (skips the push otherwise, doesn't fail).

## Testing

- `tests/test_app.py` — the FastAPI app against a fake agent session, so
  no live Ollama needed: normal streamed replies, the empty-response
  fallback, prompt injection getting blocked before the agent's even
  called, PII getting redacted before the call, agent-network exceptions
  and neuro-san's swallowed-error responses turning into error bubbles,
  and `chat_context` carrying across turns. One test is the exception —
  `test_llm_responds_to_a_real_question` makes a real call through the
  actual agent network and Ollama, and just skips (doesn't fail) if
  nothing's reachable.
- `tests/test_guardrails.py` — PII redaction and injection detection
  tested directly against the real `guardrails-config.yaml`. Also mocked,
  no live Ollama needed.

```bash
pip install -r backend/requirements.txt -r tests/requirements.txt
pytest tests/
```

## Evaluation

`eval/` is a retrieval eval harness that runs independently of the
backend:

- `generate_eval_questions.py` uses an LLM to build a labeled question set
  (`eval_questions.json`) across the FAQ categories, plus some off-topic
  "none" cases.
- `evaluate_retrieval.py` reports precision/recall/F1 per category, plus
  embedding and search latency percentiles.
- `recall_at_k.py` reports recall@k (1/3/5/10) — whether the right
  category shows up anywhere in the top-k, not just at #1.
- `compare_agent_vs_baseline.py` runs a sample of questions through both
  the full agent (grounded via `faq_search`) and a bare LLM call with no
  tools, same model both times, to see what the agent wrapper actually
  buys over a raw chat call.

```bash
pip install -r eval/requirements.txt
python eval/evaluate_retrieval.py
python eval/recall_at_k.py
python eval/compare_agent_vs_baseline.py
```

Reports land in `eval/reports/`.

### Planned Improvements

`compare_agent_vs_baseline.py` currently scores "groundedness" with a
fairly crude content-word-overlap heuristic and dumps the full answer
text for every question — accurate, but a lot to read, and it actually
undersells the agent path (an honest "I don't know, contact support"
scores low on overlap despite being exactly the right answer to an
ungrounded question). A small LLM-as-judge pass per question — one line
of verdict (`grounded` / `hallucinated` / `honest-decline`) plus a short
reason — would turn this into something scannable instead of a wall of
text.

## Future Work

- **Per-client session isolation.** Right now `_chat_context`,
  `_sly_data`, and `messages` are process-global — everyone shares one
  conversation, which was the point given the spec asked for a single
  chat interface, not per-visitor sessions. If that ever needs to change:
  thread a `session_id` through `POST /chat`, key those three off it, and
  move them out of an in-process dict (Redis, a DB) if the backend needs
  to survive restarts or scale past one process.
- **Formats beyond CSV/JSON.** `faq_index.py` auto-detects any
  `.csv`/`.json` file in `data/`, but that's hardcoded to those two
  formats and to a question/answer/category shape. Supporting other
  sources (PDF, plain text, a database) means generalizing
  `_rows_from_*`/`_extract_entries` into something closer to a per-format
  parser interface.
- **Auto-rebuilding the embedding cache** when `data/` changes, instead of
  the current manual `python eval/scratch_build_embeddings.py` step. Kept
  simple on purpose — no hashing or invalidation logic to reason about —
  since nothing here calls for a hot-swappable dataset, and this keeps
  startup fast with no live Ollama call needed just to boot.
- **Rejecting empty `text`** in `POST /chat`. An empty string satisfies
  Pydantic's `str` type and sails straight through the guardrails
  (neither regex matches an empty string) and into the agent.
- **Splitting `faq_bot`** into a router plus topic specialists (accounts,
  cards, loans, ...) instead of one front-man agent and one retrieval tool
  — worth doing once the dataset or the guardrail surface grows enough
  that a single prompt starts feeling unwieldy.
- **Surfacing which FAQ entry or category grounded an answer** in the UI —
  a lightweight "sources" affordance, using data `faq_search` already
  returns but the agent currently just discards after answering.
- **Actually using `sly_data`.** It's already threaded end-to-end —
  `app.py` carries `_sly_data` across turns and passes it into every
  `faq_search` call, `FaqRetriever.invoke` accepts it — but nothing
  writes anything into it yet, so it's a placeholder channel right now.
  `sly_data` is neuro-san's mechanism for passing information to tools
  without it ever entering the LLM's context, which makes it the right
  place for anything genuinely confidential (an authenticated customer's
  account ID, say) that `faq_search` might need but that should never be
  visible to the model itself.
- **A per-user chat history sidebar** — it's scaffolded but commented out
  in `frontend/index.html`, waiting on the session-isolation decision
  above.
