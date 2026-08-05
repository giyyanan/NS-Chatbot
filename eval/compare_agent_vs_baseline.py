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

from langchain_core.messages import HumanMessage  # noqa: E402  pylint: disable=wrong-import-position
from langchain_ollama import ChatOllama  # noqa: E402  pylint: disable=wrong-import-position

from neuro_san.client.direct_agent_session_factory import DirectAgentSessionFactory  # noqa: E402  pylint: disable=wrong-import-position
from neuro_san.client.streaming_input_processor import StreamingInputProcessor  # noqa: E402  pylint: disable=wrong-import-position

from faq_retriever import retrieve_with_timing  # noqa: E402  pylint: disable=wrong-import-position

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
    agent_scores = [row["agent_grounded"] for row in rows]
    baseline_scores = [row["baseline_grounded"] for row in rows]
    lines = []
    lines.append("# Agent Network vs. Bare LLM — Comparison Report")
    lines.append("")
    lines.append(f"Model: `{MODEL}` (same model both paths, only agent-vs-no-agent varies)")
    lines.append(f"Questions compared: {len(rows)}")
    lines.append("")
    lines.append(
        f"**Avg groundedness — agent: {sum(agent_scores) / len(agent_scores):.1%}"
        f"  |  baseline: {sum(baseline_scores) / len(baseline_scores):.1%}**"
    )
    lines.append("")
    lines.append(
        "(\"Groundedness\" = fraction of the real FAQ answer's content words "
        "that show up in the model's response -- a rough proxy, not a "
        "correctness judgement. Read the side-by-side answers below for the "
        "real picture.)"
    )
    lines.append("")
    for i, row in enumerate(rows, 1):
        lines.append(f"## {i}. [{row['category']}] {row['question']}")
        lines.append("")
        lines.append(f"**Real FAQ answer (reference):** {row['reference'] or '(no match found)'}")
        lines.append("")
        lines.append(
            f"**Agent (grounded {row['agent_grounded']:.0%}, "
            f"{row['agent_seconds']:.1f}s):** {row['agent_answer']}"
        )
        lines.append("")
        lines.append(
            f"**Baseline (grounded {row['baseline_grounded']:.0%}, "
            f"{row['baseline_seconds']:.1f}s):** {row['baseline_answer']}"
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
