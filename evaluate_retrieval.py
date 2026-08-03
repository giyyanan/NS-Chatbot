import json

from sklearn.metrics import classification_report

from faq_retrieval import retrieve_with_timing

EVAL_PATH = "eval_questions.json"


def predict_category(question: str):
    results, timing = retrieve_with_timing(question)
    predicted = results[0]["class"] if results else "none"
    return predicted, timing


def percentiles(values: list[float]):
    values = sorted(values)
    avg = sum(values) / len(values)
    p50 = values[len(values) // 2]
    p95 = values[int(len(values) * 0.95)]
    return avg, p50, p95


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

    print("\n" + "=" * 70)
    print(f"Evaluated {len(eval_set)} questions\n")
    print(classification_report(y_true, y_pred, zero_division=0))

    e_avg, e_p50, e_p95 = percentiles(embed_latencies)
    s_avg, s_p50, s_p95 = percentiles(search_latencies)
    total_avg = e_avg + s_avg

    print("Latency breakdown:")
    print(f"  Ollama embedding call : avg={e_avg * 1000:.1f}ms  p50={e_p50 * 1000:.1f}ms  p95={e_p95 * 1000:.1f}ms")
    print(f"  Local cosine search   : avg={s_avg * 1000:.2f}ms  p50={s_p50 * 1000:.2f}ms  p95={s_p95 * 1000:.2f}ms")
    print(f"  Total retrieval       : avg={total_avg * 1000:.1f}ms  ({e_avg / total_avg:.1%} embedding / {s_avg / total_avg:.1%} search)")

    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    print(f"\nOverall accuracy: {accuracy:.1%}")


if __name__ == "__main__":
    main()
