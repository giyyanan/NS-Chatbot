import csv
import os

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


def retrieve(query: str, top_k: int = 3, min_score: float = 0.55):
    response = ollama.embed(model=EMBEDDING_MODEL, input=query)
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
    return results
