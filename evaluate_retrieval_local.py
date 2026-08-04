import json
import os
import time

import numpy as np
import ollama

import faq_retrieval as fr
from evaluate_retrieval import EVAL_PATH, RESULTS_DIR, render_report

REPORT_PATH = os.path.join(RESULTS_DIR, "retrieval_report.md")
LOCAL_MODEL = "embeddinggemma"


def predict_category(question: str):
    # Local Ollama variant — same reasoning as recall_at_k_local.py: the
    # Ollama Cloud embed API isn't authorized on the current plan yet, so
    # this uses the local server directly instead of faq_retrieval.py's
    # cloud-configured client. Production (main.py) is untouched.
    embed_start = time.perf_counter()
    response = ollama.embed(model=LOCAL_MODEL, input=question)
    embed_seconds = time.perf_counter() - embed_start

    search_start = time.perf_counter()
    query_vector = np.array(response["embeddings"][0], dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)

    scores = fr._normed_matrix @ query_vector
    top_i = int(np.argmax(scores))

    predicted = fr.faqs[top_i]["Class"] if scores[top_i] >= 0.55 else "none"
    search_seconds = time.perf_counter() - search_start

    return predicted, {"embed_seconds": embed_seconds, "search_seconds": search_seconds}


def main():
    with open(EVAL_PATH, encoding="utf-8") as f:
        eval_set = json.load(f)

    y_true = []
    y_pred = []
    embed_latencies = []
    search_latencies = []

    for i, item in enumerate(eval_set):
        predicted, timing = predict_category(item["question"])
        y_true.append(item["expected_category"])
        y_pred.append(predicted)
        embed_latencies.append(timing["embed_seconds"])
        search_latencies.append(timing["search_seconds"])

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(eval_set)} evaluated...")

    report = render_report(y_true, y_pred, embed_latencies, search_latencies)
    print("\n" + report)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSaved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
