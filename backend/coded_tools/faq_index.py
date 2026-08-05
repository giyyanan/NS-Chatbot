"""
Discovers FAQ entries from any CSV/JSON file in data/ and loads the
pre-built embedding cache over them (see build_embeddings() /
eval/scratch_build_embeddings.py -- the cache is built offline, not
regenerated automatically at app startup).
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import csv
import json
import os

import numpy as np
import ollama

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
EMBEDDING_MODEL = "embeddinggemma"
OLLAMA_HOST = os.getenv("OLLAMA_EMBED_HOST", "http://127.0.0.1:11434")
CACHE_PREFIX = f"faq_embeddings_{EMBEDDING_MODEL}"
CACHE_PATH = os.path.join(DATA_DIR, f"{CACHE_PREFIX}.npy")

_client = ollama.Client(host=OLLAMA_HOST)

QUESTION_KEYS = ["question", "q", "query", "title", "prompt"]
ANSWER_KEYS = ["answer", "a", "response", "reply", "text", "content", "body"]
CATEGORY_KEYS = ["category", "categories", "class", "topic", "tag", "tags", "section", "type"]
LIST_KEYS = ["faqs", "data", "items", "entries", "records"]


def _match_key(available: List[str], candidates: List[str]) -> Optional[str]:
    lowered = {key.lower(): key for key in available}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _rows_from_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _rows_from_json(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        key = _match_key(list(payload.keys()), LIST_KEYS)
        if key and isinstance(payload[key], list):
            return payload[key]

    return []


def _extract_entries(rows: List[Dict[str, Any]], source: str) -> List[Dict[str, str]]:
    if not rows:
        return []

    if not isinstance(rows[0], dict):
        raise ValueError(f"{source}: expected a list of objects/rows, got {type(rows[0]).__name__} entries.")

    available = list(rows[0].keys())
    question_key = _match_key(available, QUESTION_KEYS)
    answer_key = _match_key(available, ANSWER_KEYS)
    category_key = _match_key(available, CATEGORY_KEYS)

    if not question_key or not answer_key:
        raise ValueError(
            f"{source}: could not find question/answer columns among {available}. "
            f"Expected one of {QUESTION_KEYS} and one of {ANSWER_KEYS}."
        )

    entries = []
    for row in rows:
        entries.append(
            {
                "question": str(row.get(question_key) or "").strip(),
                "answer": str(row.get(answer_key) or "").strip(),
                "category": str(row.get(category_key) or "").strip() if category_key else "",
            }
        )
    return entries


def discover_entries() -> List[Dict[str, str]]:
    """Scans data/ for .csv and .json FAQ files and returns their combined entries."""
    entries: List[Dict[str, str]] = []
    for name in sorted(os.listdir(DATA_DIR)):
        if name.startswith(CACHE_PREFIX):
            continue

        path = os.path.join(DATA_DIR, name)
        if name.lower().endswith(".csv"):
            entries.extend(_extract_entries(_rows_from_csv(path), name))
        elif name.lower().endswith(".json"):
            entries.extend(_extract_entries(_rows_from_json(path), name))

    return entries


def build_embeddings(entries: List[Dict[str, str]]) -> np.ndarray:
    """
    Embeds every FAQ entry via Ollama and writes the result to CACHE_PATH.
    Offline/manual step, not called at app startup -- see
    eval/scratch_build_embeddings.py. Re-run that script after changing
    data/'s contents.
    """
    vectors = []
    for entry in entries:
        text = f"{entry['question']}\n{entry['answer']}"
        response = _client.embed(model=EMBEDDING_MODEL, input=text)
        vectors.append(response["embeddings"][0])
    matrix = np.array(vectors, dtype=np.float32)
    np.save(CACHE_PATH, matrix)
    return matrix


def ensure_embeddings() -> Tuple[List[Dict[str, str]], np.ndarray]:
    """
    Returns (entries, normalized_embedding_matrix) for whatever FAQ files are
    currently in data/. Assumes the embedding cache at CACHE_PATH has
    already been built -- run `python eval/scratch_build_embeddings.py`
    after changing data/'s contents. Keeps app startup simple and fast,
    with no live Ollama call needed just to boot.
    """
    entries = discover_entries()
    if not entries:
        return entries, np.zeros((0, 0), dtype=np.float32)

    if not os.path.exists(CACHE_PATH):
        raise RuntimeError(
            f"No embedding cache at {CACHE_PATH}. Run "
            "`python eval/scratch_build_embeddings.py` first."
        )

    matrix = np.load(CACHE_PATH)
    if matrix.shape[0] != len(entries):
        raise RuntimeError(
            f"Embedding cache at {CACHE_PATH} has {matrix.shape[0]} vectors "
            f"but data/ currently has {len(entries)} FAQ entries -- rebuild "
            "with `python eval/scratch_build_embeddings.py`."
        )

    normed_matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
    return entries, normed_matrix
