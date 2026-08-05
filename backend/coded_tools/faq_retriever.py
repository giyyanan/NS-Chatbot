"""
Semantic (embeddings-based) retrieval over whatever FAQ dataset(s) are
present in data/ (see faq_index.py for discovery/embedding).
"""

from typing import Any
from typing import Dict

import os
import time

import numpy as np

from neuro_san.interfaces.coded_tool import CodedTool

import faq_index

RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "10"))

faqs, _normed_matrix = faq_index.ensure_embeddings()

#serach method with timing calculations, basically used for evals
def retrieve_with_timing(query: str, top_k: int = RETRIEVAL_TOP_K, min_score: float = 0.55):

    if not faqs:
        return [], {"embed_seconds": 0.0, "search_seconds": 0.0}

    embed_start = time.perf_counter()
    response = faq_index._client.embed(model=faq_index.EMBEDDING_MODEL, input=query)
    embed_seconds = time.perf_counter() - embed_start

    search_start = time.perf_counter()
    query_vector = np.array(response["embeddings"][0], dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)

    # cosine mathing thorugh matrix multiplication
    scores = _normed_matrix @ query_vector
    ranked = np.argsort(-scores)[:top_k]

    results = []
    for i in ranked:
        if scores[i] < min_score:
            break
        results.append(
            {
                "question": faqs[i]["question"],
                "answer": faqs[i]["answer"],
                "category": faqs[i]["category"],
                "score": float(scores[i]),
            }
        )
    search_seconds = time.perf_counter() - search_start

    return results, {"embed_seconds": embed_seconds, "search_seconds": search_seconds}

#Default method for fetching the search results with a min score of .55 for cosine search
def retrieve(query: str, top_k: int = RETRIEVAL_TOP_K, min_score: float = 0.55):
    if not faqs:
        return []

    response = faq_index._client.embed(model=faq_index.EMBEDDING_MODEL, input=query)
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
                "question": faqs[i]["question"],
                "answer": faqs[i]["answer"],
                "category": faqs[i]["category"],
                "score": float(scores[i]),
            }
        )
    return results

#implementation class for exposing the retrieve method in coded tools
class FaqRetriever(CodedTool):
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        query = str(args.get("query", "")).strip()
        if not query:
            return "No search query was provided."

        matches = retrieve(query)
        if not matches:
            return (
                f"No FAQ entries matched the query '{query}'. "
                "Tell the customer this topic isn't covered by the FAQ dataset "
                "and suggest they contact human customer support."
            )

        blocks = []
        for match in matches:
            lines = []
            if match["category"]:
                lines.append(f"Category: {match['category']}")
            lines.append(f"Q: {match['question']}")
            lines.append(f"A: {match['answer']}")
            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        return self.invoke(args, sly_data)
