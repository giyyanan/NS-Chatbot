import json
import os
from datetime import datetime, timezone

import numpy as np
import ollama

import faq_retrieval as fr

EVAL_PATH = "eval_questions.json"
RESULTS_DIR = "eval_results"
REPORT_PATH = os.path.join(RESULTS_DIR, "recall_at_k.md")
K_VALUES = [1, 3, 5, 10, 20, 30]
MIN_SCORE = 0.55
LOCAL_MODEL = "embeddinggemma"


def ranked_categories(query: str):
    # Uses the local Ollama server (default localhost:11434), NOT the Ollama
    # Cloud client faq_retrieval.py uses in production. This file exists only
    # to run this eval now, before the Ollama Cloud embed API is available on
    # the account's plan. faq_retrieval.py itself is untouched.
    response = ollama.embed(model=LOCAL_MODEL, input=query)
    query_vector = np.array(response["embeddings"][0], dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)

    scores = fr._normed_matrix @ query_vector
    ranked = np.argsort(-scores)[: max(K_VALUES)]

    return [(fr.faqs[i]["Class"], float(scores[i])) for i in ranked]


def render_report(hits: dict, total: int) -> str:
    lines = []
    lines.append("# Recall@k Evaluation Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Questions evaluated: {total}")
    lines.append(f"min_score: {MIN_SCORE}  |  embedding model: {LOCAL_MODEL} (local Ollama)")
    lines.append("")
    lines.append("Recall@k = fraction of questions where the correct category appears")
    lines.append("somewhere in the top-k retrieved results (above the similarity threshold).")
    lines.append("")
    lines.append("| k | Correct | Recall | Δ vs previous k |")
    lines.append("|---|---|---|---|")
    prev = None
    for k in K_VALUES:
        recall = hits[k] / total
        delta = f"+{(recall - prev) * 100:.1f}pp" if prev is not None else "—"
        lines.append(f"| {k} | {hits[k]}/{total} | {recall:.1%} | {delta} |")
        prev = recall
    lines.append("")

    return "\n".join(lines)


def main():
    with open(EVAL_PATH, encoding="utf-8") as f:
        eval_set = json.load(f)

    hits = {k: 0 for k in K_VALUES}
    total = len(eval_set)

    for i, item in enumerate(eval_set):
        expected = item["expected_category"]
        ranked = ranked_categories(item["question"])

        for k in K_VALUES:
            top_k_categories = [c for c, s in ranked[:k] if s >= MIN_SCORE]
            if expected == "none":
                correct = not top_k_categories
            else:
                correct = expected in top_k_categories
            if correct:
                hits[k] += 1

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{total} evaluated...")

    report = render_report(hits, total)
    print("\n" + report)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSaved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
