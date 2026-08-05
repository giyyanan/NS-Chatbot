import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "coded_tools"))

import faq_retriever as fr  # noqa: E402  pylint: disable=wrong-import-position

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_PATH = os.path.join(EVAL_DIR, "eval_questions.json")
RESULTS_DIR = os.path.join(EVAL_DIR, "reports")
REPORT_PATH = os.path.join(RESULTS_DIR, "recall_at_k_report.md")
K_VALUES = [1, 3, 5, 10]
MIN_SCORE = 0.55


def ranked_categories(query: str):
    results, _ = fr.retrieve_with_timing(query, top_k=max(K_VALUES), min_score=0.0)
    return [(r["category"], r["score"]) for r in results]


def render_report(hits: dict, total: int) -> str:
    lines = []
    lines.append("# FAQ Retrieval — Recall@k Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Questions evaluated: {total}  |  min_score: {MIN_SCORE}")
    lines.append("")
    lines.append("## TL;DR")
    lines.append("")
    lines.append(
        f"- Top-1 result is correct **{hits[1] / total:.0%}** of the time. Widening the "
        f"search to the top-{max(K_VALUES)} results (instead of just the best match) gets "
        f"the right category in the results **{hits[max(K_VALUES)] / total:.0%}** of the time."
    )
    gap = hits[max(K_VALUES)] / total - hits[1] / total
    if gap > 0.1:
        lines.append(
            f"- That's a **{gap:.0%}** gap between top-1 and top-{max(K_VALUES)} — the right "
            "answer is often *in there somewhere*, just not ranked first. Worth revisiting "
            "the ranking/scoring, not just the search itself."
        )
    else:
        lines.append(
            "- Top-1 and top-k recall are close together, so when retrieval finds the right "
            "category at all, it usually ranks it first."
        )
    lines.append("")
    lines.append("## Recall@k")
    lines.append("")
    lines.append("(Does the correct category show up anywhere in the top-k results?)")
    lines.append("")
    lines.append("| k | Correct / Total | Recall |")
    lines.append("|---|---|---|")
    for k in K_VALUES:
        lines.append(f"| {k} | {hits[k]}/{total} | {hits[k] / total:.1%} |")
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
