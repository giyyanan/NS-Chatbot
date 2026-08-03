import csv
import os
import time

import numpy as np
import ollama

CSV_PATH = "BankFAQs.csv"
CACHE_PATH = "faq_embeddings_embeddinggemma.npy"
EMBEDDING_MODEL = "embeddinggemma"

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    faqs = list(csv.DictReader(f))

if not os.path.exists(CACHE_PATH):
    raise FileNotFoundError(
        f"{CACHE_PATH} not found. Run scratch_build_embeddings.py first to build "
        "the FAQ embedding cache (requires a local Ollama server with the "
        f"'{EMBEDDING_MODEL}' model pulled)."
    )

_matrix = np.load(CACHE_PATH)
_normed_matrix = _matrix / np.linalg.norm(_matrix, axis=1, keepdims=True)


def retrieve_with_timing(query: str, top_k: int = 3, min_score: float = 0.55):
    """Same as retrieve(), but also returns a timing breakdown:
    {"embed_seconds": ..., "search_seconds": ...} — embed_seconds is the
    Ollama embedding API call, search_seconds is the local numpy cosine
    similarity search against the cached FAQ matrix.
    """
    embed_start = time.perf_counter()
    response = ollama.embed(model=EMBEDDING_MODEL, input=query)
    embed_seconds = time.perf_counter() - embed_start

    search_start = time.perf_counter()
    query_vector = np.array(response["embeddings"][0], dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)

    scores = _normed_matrix @ query_vector
    ranked = np.argsort(-scores)[:top_k]

    results = []
    for i in ranked:
        if scores[i] < min_score:
            break
        results.append(
            {
                "question": faqs[i]["Question"],
                "answer": faqs[i]["Answer"],
                "class": faqs[i]["Class"],
                "score": float(scores[i]),
            }
        )
    search_seconds = time.perf_counter() - search_start

    return results, {"embed_seconds": embed_seconds, "search_seconds": search_seconds}


def retrieve(query: str, top_k: int = 3, min_score: float = 0.55):
    results, _ = retrieve_with_timing(query, top_k=top_k, min_score=min_score)
    return results
