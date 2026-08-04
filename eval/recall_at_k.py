import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "coded_tools"))

import faq_retriever as fr  # noqa: E402  pylint: disable=wrong-import-position

EVAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_questions.json")
K_VALUES = [1, 3, 5, 10]
MIN_SCORE = 0.55


def ranked_categories(query: str):
    results, _ = fr.retrieve_with_timing(query, top_k=max(K_VALUES), min_score=0.0)
    return [(r["category"], r["score"]) for r in results]


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

    print("\nRecall@k (correct category appears somewhere in top-k above threshold):")
    for k in K_VALUES:
        print(f"  k={k:>2}: {hits[k]}/{total} = {hits[k] / total:.1%}")


if __name__ == "__main__":
    main()
