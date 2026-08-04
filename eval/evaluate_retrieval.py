import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "coded_tools"))

from sklearn.metrics import classification_report

from faq_retriever import RETRIEVAL_TOP_K, retrieve_with_timing  # noqa: E402  pylint: disable=wrong-import-position

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_PATH = os.path.join(EVAL_DIR, "eval_questions.json")
RESULTS_DIR = os.path.join(EVAL_DIR, "eval_results")
REPORT_PATH = os.path.join(RESULTS_DIR, "retrieval_report.md")


def predict_category(question: str):
    results, timing = retrieve_with_timing(question)
    predicted = results[0]["category"] if results else "none"
    return predicted, timing


def percentiles(values: list[float]):
    values = sorted(values)
    avg = sum(values) / len(values)
    p50 = values[len(values) // 2]
    p95 = values[int(len(values) * 0.95)]
    return avg, p50, p95


def render_report(y_true, y_pred, embed_latencies, search_latencies) -> str:
    report_dict = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    e_avg, e_p50, e_p95 = percentiles(embed_latencies)
    s_avg, s_p50, s_p95 = percentiles(search_latencies)
    total_avg = e_avg + s_avg
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)

    lines = []
    lines.append("# FAQ Retrieval Evaluation Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Questions evaluated: {len(y_true)}")
    lines.append(f"top_k: {RETRIEVAL_TOP_K}  |  min_score: 0.55")
    lines.append("")
    lines.append(f"**Overall accuracy: {accuracy:.1%}**")
    lines.append("")
    lines.append("## Precision / Recall by category")
    lines.append("")
    lines.append("| Category | Precision | Recall | F1 | Support |")
    lines.append("|---|---|---|---|---|")
    for category, metrics in sorted(report_dict.items()):
        if category in ("accuracy", "macro avg", "weighted avg"):
            continue
        lines.append(
            f"| {category} | {metrics['precision']:.2f} | {metrics['recall']:.2f} "
            f"| {metrics['f1-score']:.2f} | {int(metrics['support'])} |"
        )
    macro = report_dict["macro avg"]
    weighted = report_dict["weighted avg"]
    lines.append(
        f"| **macro avg** | {macro['precision']:.2f} | {macro['recall']:.2f} "
        f"| {macro['f1-score']:.2f} | {int(macro['support'])} |"
    )
    lines.append(
        f"| **weighted avg** | {weighted['precision']:.2f} | {weighted['recall']:.2f} "
        f"| {weighted['f1-score']:.2f} | {int(weighted['support'])} |"
    )
    lines.append("")
    lines.append("## Latency breakdown")
    lines.append("")
    lines.append("| Stage | avg | p50 | p95 |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Ollama embedding call | {e_avg * 1000:.1f}ms | {e_p50 * 1000:.1f}ms | {e_p95 * 1000:.1f}ms |")
    lines.append(f"| Local cosine search | {s_avg * 1000:.2f}ms | {s_p50 * 1000:.2f}ms | {s_p95 * 1000:.2f}ms |")
    lines.append(f"| **Total retrieval** | **{total_avg * 1000:.1f}ms** | — | — |")
    lines.append("")
    lines.append(
        f"Embedding call is {e_avg / total_avg:.1%} of total latency; "
        f"local search is {s_avg / total_avg:.1%}."
    )
    lines.append("")

    return "\n".join(lines)


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
