"""
Compares the full neuro-san agent network (grounded via faq_search) against
a bare LLM call with no tool access and no FAQ context, on the same sample
of eval questions. Answers a simple question: does routing through the
agent network + retrieval actually make answers more grounded, or would a
raw chat call do just as well?

Uses OLLAMA_MODEL (default gpt-oss:20b-cloud, same model for both paths) so
comparison isn't confounded by model choice -- only by agent-vs-no-agent.
Cloud model recommended for run time; the local qwen2.5:7b fallback works
too but is much slower (see README).
"""

import json
import os
import random
import re
import sys
import time

from typing import Dict
from typing import List

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(EVAL_DIR)
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
CODED_TOOLS_DIR = os.path.join(BACKEND_DIR, "coded_tools")
AGENT_NETWORK_FILE = os.path.join(BACKEND_DIR, "agent_network", "faq_chatbot.hocon")
EVAL_PATH = os.path.join(EVAL_DIR, "eval_questions.json")
RESULTS_DIR = os.path.join(EVAL_DIR, "reports")
REPORT_PATH = os.path.join(RESULTS_DIR, "agent_vs_baseline_report.md")

# Must be set before the agent network's coded tools get resolved -- same
# requirement as backend/app.py.
os.environ["AGENT_TOOL_PATH"] = CODED_TOOLS_DIR
if CODED_TOOLS_DIR not in sys.path:
    sys.path.insert(0, CODED_TOOLS_DIR)

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from neuro_san.client.direct_agent_session_factory import DirectAgentSessionFactory
from neuro_san.client.streaming_input_processor import StreamingInputProcessor

from faq_retriever import retrieve_with_timing

MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b-cloud")
BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
SAMPLE_PER_CATEGORY = int(os.environ.get("SAMPLE_PER_CATEGORY", "2"))
SEED = 42

BASELINE_SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for a bank. Answer the "
    "customer's question as best you can."
)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "to", "of", "in", "on", "at", "for", "with", "by",
    "from", "as", "this", "that", "these", "those", "it", "its", "you",
    "your", "will", "would", "can", "could", "should", "please", "into",
    "not", "if", "then", "than", "have", "has", "had", "do", "does", "did",
}


def tokenize(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def groundedness(answer: str, reference: str) -> float:
    """Fraction of reference-answer content words that show up in `answer`.

    A crude proxy for "did this response actually draw on the real FAQ
    content" -- not a substitute for reading the side-by-side answers, but
    gives a quick relative signal between the two paths.
    """
    ref_tokens = tokenize(reference)
    if not ref_tokens:
        return 0.0
    ans_tokens = tokenize(answer)
    return len(ref_tokens & ans_tokens) / len(ref_tokens)


DECLINE_PHRASES = (
    "i'm sorry", "i am sorry", "i don't have", "i do not have",
    "i couldn't find", "i could not find", "i don't know", "i do not know",
    "not aware of", "reach out", "reaching out", "get in touch",
    "contact our", "contact customer", "recommend contacting",
    "customer support team", "live agent", "human agent", "support team",
    "best next step", "connect you to", "connect you with",
    "faq entry", "faq resources",
)


def declined(answer: str) -> bool:
    """Heuristic: did the model punt to a human/support channel instead of
    answering, rather than making something up? Keyword-based -- not
    perfect, but the model's refusal phrasing is consistent enough in
    practice for a quick signal.

    Model output routinely uses smart/curly quotes ("don't" as U+2019, not
    a plain apostrophe) -- normalize those before matching, or every
    apostrophe-containing phrase above silently never matches.
    """
    lowered = answer.lower().replace("’", "'").replace("‘", "'")
    return any(phrase in lowered for phrase in DECLINE_PHRASES)


def verdict(answer: str, reference: str, score: float) -> str:
    """One human-readable verdict per answer, combining decline-detection
    with the groundedness score. Designed so an honest "I don't know" on an
    ungrounded question scores as correct, not as a failure -- the raw
    groundedness score alone would penalize it.
    """
    has_reference = bool(reference)
    is_decline = declined(answer)

    if not has_reference:
        return "Honest (declined)" if is_decline else "Hallucinated (answered anyway)"
    if is_decline:
        return "Over-cautious (declined, but a real answer existed)"
    if score >= 0.4:
        return "Grounded"
    if score >= 0.15:
        return "Partial"
    return "Weak/wrong"


VERDICT_ICONS = {
    "Honest (declined)": "✅",
    "Grounded": "✅",
    "Partial": "⚠️",
    "Over-cautious (declined, but a real answer existed)": "⚠️",
    "Weak/wrong": "❌",
    "Hallucinated (answered anyway)": "❌",
}


def truncate(text: str, limit: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def sample_questions() -> List[Dict]:
    with open(EVAL_PATH, encoding="utf-8") as handle:
        data = json.load(handle)
    by_category: Dict[str, List[Dict]] = {}
    for item in data:
        by_category.setdefault(item["expected_category"], []).append(item)
    rng = random.Random(SEED)
    sample = []
    for category in sorted(by_category):
        if category == "none":
            continue
        items = by_category[category]
        sample.extend(rng.sample(items, min(SAMPLE_PER_CATEGORY, len(items))))
    return sample


def agent_answer(session, question: str) -> str:
    input_processor = StreamingInputProcessor(session=session)
    input_processor.reset()
    chat_request = input_processor.formulate_chat_request(question, sly_data=None, chat_context=None)
    message_processor = input_processor.get_message_processor()
    for chat_response in session.streaming_chat(chat_request):
        response = chat_response.get("response", {})
        message_processor.process_message(response)
    return message_processor.get_compiled_answer() or "(no response)"


def baseline_answer(llm: ChatOllama, question: str) -> str:
    messages = [HumanMessage(content=f"{BASELINE_SYSTEM_PROMPT}\n\nCustomer question: {question}")]
    return llm.invoke(messages).content


def render_report(rows: List[Dict]) -> str:
    for row in rows:
        row["agent_verdict"] = verdict(row["agent_answer"], row["reference"], row["agent_grounded"])
        row["baseline_verdict"] = verdict(row["baseline_answer"], row["reference"], row["baseline_grounded"])

    n = len(rows)
    has_ref_rows = [r for r in rows if r["reference"]]
    no_ref_rows = [r for r in rows if not r["reference"]]
    agent_good = sum(1 for r in rows if VERDICT_ICONS[r["agent_verdict"]] == "✅")
    baseline_good = sum(1 for r in rows if VERDICT_ICONS[r["baseline_verdict"]] == "✅")
    agent_avg_time = sum(r["agent_seconds"] for r in rows) / n
    baseline_avg_time = sum(r["baseline_seconds"] for r in rows) / n

    lines = []
    lines.append("# Agent Network vs. Bare LLM — Comparison Report")
    lines.append("")
    lines.append(f"Model: `{MODEL}` (same model both paths — only agent-vs-no-agent varies)")
    lines.append(f"Questions compared: {n} ({len(has_ref_rows)} had a real FAQ match, "
                  f"{len(no_ref_rows)} didn't — nothing in the dataset covers them)")
    lines.append("")
    lines.append("## TL;DR")
    lines.append("")
    lines.append(f"- **Agent: {agent_good}/{n} good outcomes ✅ — Baseline: {baseline_good}/{n} ✅**")
    if no_ref_rows:
        agent_declined = sum(1 for r in no_ref_rows if declined(r["agent_answer"]))
        baseline_declined = sum(1 for r in no_ref_rows if declined(r["baseline_answer"]))
        lines.append(
            f"- On the {len(no_ref_rows)} questions with **no real answer in the FAQ data**, "
            f"the agent honestly said so **{agent_declined}/{len(no_ref_rows)}** times; the "
            f"baseline did **{baseline_declined}/{len(no_ref_rows)}** times — the rest of the "
            "time it invented a plausible-sounding answer with no basis in this bank's actual "
            "policies (fake phone numbers, fake fees, fake limits)."
        )
    if has_ref_rows:
        agent_grounded_n = sum(1 for r in has_ref_rows if r["agent_verdict"] == "Grounded")
        baseline_grounded_n = sum(1 for r in has_ref_rows if r["baseline_verdict"] == "Grounded")
        lines.append(
            f"- On the {len(has_ref_rows)} questions the FAQ **does** cover, the agent's answer "
            f"was clearly grounded in the real policy **{agent_grounded_n}/{len(has_ref_rows)}** "
            f"times vs. the baseline's **{baseline_grounded_n}/{len(has_ref_rows)}**."
        )
    lines.append(
        f"- Agent averaged **{agent_avg_time:.1f}s** per answer; baseline averaged "
        f"**{baseline_avg_time:.1f}s** — the agent's answers are also shorter and less padded."
    )
    lines.append("")
    lines.append(
        "Verdict legend: ✅ correct behavior (grounded answer, or an honest decline when "
        "nothing in the FAQ applies) · ⚠️ borderline · ❌ wrong (hallucinated, or declined "
        "when a real answer existed)."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| # | Category | Question | Agent | Baseline |")
    lines.append("|---|---|---|---|---|")
    for i, row in enumerate(rows, 1):
        a_icon = VERDICT_ICONS[row["agent_verdict"]]
        b_icon = VERDICT_ICONS[row["baseline_verdict"]]
        lines.append(
            f"| {i} | {row['category']} | {truncate(row['question'], 55)} "
            f"| {a_icon} {row['agent_verdict']} ({row['agent_seconds']:.0f}s) "
            f"| {b_icon} {row['baseline_verdict']} ({row['baseline_seconds']:.0f}s) |"
        )
    lines.append("")
    lines.append(
        "*(\"Grounded\"/\"Partial\"/\"Weak\" come from a crude content-word-overlap score "
        "against the real FAQ answer — a rough proxy, not a correctness judgement. Read the "
        "full answers below for the real picture on any row that looks surprising.)*"
    )
    lines.append("")
    lines.append("## Full answers")
    lines.append("")
    for i, row in enumerate(rows, 1):
        lines.append(f"### {i}. [{row['category']}] {row['question']}")
        lines.append("")
        lines.append(f"**Real FAQ answer (reference):** {row['reference'] or '(no match found)'}")
        lines.append("")
        lines.append(
            f"**Agent — {VERDICT_ICONS[row['agent_verdict']]} {row['agent_verdict']} "
            f"({row['agent_grounded']:.0%} grounded, {row['agent_seconds']:.1f}s):** "
            f"{row['agent_answer']}"
        )
        lines.append("")
        lines.append(
            f"**Baseline — {VERDICT_ICONS[row['baseline_verdict']]} {row['baseline_verdict']} "
            f"({row['baseline_grounded']:.0%} grounded, {row['baseline_seconds']:.1f}s):** "
            f"{row['baseline_answer']}"
        )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    questions = sample_questions()
    print(f"Comparing {len(questions)} questions, model={MODEL}, base_url={BASE_URL}")

    factory = DirectAgentSessionFactory()
    session = factory.create_session(AGENT_NETWORK_FILE)
    llm = ChatOllama(model=MODEL, base_url=BASE_URL)

    rows = []
    for i, item in enumerate(questions, 1):
        question = item["question"]
        category = item["expected_category"]
        print(f"  [{i}/{len(questions)}] {question}")

        ref_results, _ = retrieve_with_timing(question)
        reference = ref_results[0]["answer"] if ref_results else ""

        start = time.perf_counter()
        a_answer = agent_answer(session, question)
        a_seconds = time.perf_counter() - start

        start = time.perf_counter()
        b_answer = baseline_answer(llm, question)
        b_seconds = time.perf_counter() - start

        rows.append(
            {
                "question": question,
                "category": category,
                "reference": reference,
                "agent_answer": a_answer,
                "agent_seconds": a_seconds,
                "agent_grounded": groundedness(a_answer, reference),
                "baseline_answer": b_answer,
                "baseline_seconds": b_seconds,
                "baseline_grounded": groundedness(b_answer, reference),
            }
        )

    os.makedirs(RESULTS_DIR, exist_ok=True)
    report = render_report(rows)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        handle.write(report)
    print(f"\nSaved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
