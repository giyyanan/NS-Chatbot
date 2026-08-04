"""
Discovers FAQ entries from any CSV/JSON file in data/ and maintains an
embedding cache over them, auto-rebuilt whenever data/ contents change.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import csv
import hashlib
import json
import os

import numpy as np
import ollama

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
EMBEDDING_MODEL = "embeddinggemma"
OLLAMA_HOST = os.getenv("OLLAMA_EMBED_HOST", "http://127.0.0.1:11434")
CACHE_PREFIX = f"faq_embeddings_{EMBEDDING_MODEL}"
CACHE_PATH = os.path.join(DATA_DIR, f"{CACHE_PREFIX}.npy")
META_PATH = os.path.join(DATA_DIR, f"{CACHE_PREFIX}.meta.json")

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


def _data_manifest_hash() -> str:
    fingerprints = []
    for name in sorted(os.listdir(DATA_DIR)):
        if name.startswith(CACHE_PREFIX):
            continue
        if not (name.lower().endswith(".csv") or name.lower().endswith(".json")):
            continue
        path = os.path.join(DATA_DIR, name)
        stat = os.stat(path)
        fingerprints.append(f"{name}:{stat.st_mtime_ns}:{stat.st_size}")

    digest_input = EMBEDDING_MODEL + "|" + "|".join(fingerprints)
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def _embed_entries(entries: List[Dict[str, str]]) -> np.ndarray:
    vectors = []
    for entry in entries:
        text = f"{entry['question']}\n{entry['answer']}"
        response = _client.embed(model=EMBEDDING_MODEL, input=text)
        vectors.append(response["embeddings"][0])
    return np.array(vectors, dtype=np.float32)


def _load_cache_meta() -> Optional[Dict[str, Any]]:
    if not os.path.exists(META_PATH):
        return None
    with open(META_PATH, encoding="utf-8") as f:
        return json.load(f)


def ensure_embeddings() -> Tuple[List[Dict[str, str]], np.ndarray]:
    """
    Returns (entries, normalized_embedding_matrix) for whatever FAQ files are
    currently in data/, rebuilding the embedding cache if data/ has changed
    (or the cache doesn't exist yet) since the cache was last built.
    """
    entries = discover_entries()
    if not entries:
        return entries, np.zeros((0, 0), dtype=np.float32)

    manifest_hash = _data_manifest_hash()

    meta = _load_cache_meta()
    cache_valid = (
        meta is not None
        and meta.get("manifest_hash") == manifest_hash
        and meta.get("count") == len(entries)
        and os.path.exists(CACHE_PATH)
    )

    if cache_valid:
        matrix = np.load(CACHE_PATH)
    else:
        matrix = _embed_entries(entries)
        np.save(CACHE_PATH, matrix)
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump({"manifest_hash": manifest_hash, "count": len(entries), "model": EMBEDDING_MODEL}, f)

    normed_matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
    return entries, normed_matrix
