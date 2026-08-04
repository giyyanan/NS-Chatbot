import json

import numpy as np

import faq_retrieval as fr

EVAL_PATH = "eval_questions.json"
K_VALUES = [1, 3, 5, 10]
MIN_SCORE = 0.55


def ranked_categories(query: str):
    response = fr._ollama_client.embed(model=fr.EMBEDDING_MODEL, input=query)
    query_vector = np.array(response["embeddings"][0], dtype=np.float32)
    query_vector = query_vector / np.linalg.norm(query_vector)

    scores = fr._normed_matrix @ query_vector
    ranked = np.argsort(-scores)[: max(K_VALUES)]

    return [(fr.faqs[i]["Class"], float(scores[i])) for i in ranked]


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
