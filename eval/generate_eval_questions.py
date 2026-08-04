import json
import os
import re
import time

import ollama

MODEL = "gpt-oss:120b-cloud"
CATEGORIES = ["accounts", "cards", "loans", "insurance", "fundstransfer", "investments", "security"]
PER_CATEGORY = 250
GARBAGE_COUNT = 250
BATCH_SIZE = 25
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_questions.json")

GEN_PROMPT = """Generate {n} realistic questions a bank customer might type into a \
customer support chat about "{category}" banking topics (e.g. accounts, cards, \
loans, insurance, fund transfers, investments, or security depending on context).

Vary the style:
- Some short and direct ("How do I reset my card PIN?")
- Some with a bit of backstory/context ("I just moved to a new city and need to \
update my registered address, what's the process?")
- Some vague or informally worded, with typos or casual phrasing
- A couple of edge cases: multi-part questions, or questions mixing this topic \
with something unrelated

Return ONLY a JSON array of {n} strings, no markdown fences, no extra text.
"""

GARBAGE_PROMPT = """Generate {n} short chat messages that a bank's customer support \
chatbot might receive that are NOT relevant banking questions — things like small \
talk, general knowledge questions, jokes, nonsense/garbage text, or completely \
unrelated topics (weather, cooking, movies, etc). Keep them short and varied.

Return ONLY a JSON array of {n} strings, no markdown fences, no extra text.
"""


def extract_json_array(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def generate_batch(prompt: str, retries: int = 2):
    for attempt in range(retries + 1):
        try:
            response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
            return extract_json_array(response.message.content)
        except Exception as e:  # pylint: disable=broad-except
            if attempt == retries:
                print(f"    batch failed after {retries} retries: {e}")
                return []
            time.sleep(1)


def main():
    dataset = []
    start = time.time()

    for category in CATEGORIES:
        collected = []
        while len(collected) < PER_CATEGORY:
            n = min(BATCH_SIZE, PER_CATEGORY - len(collected))
            questions = generate_batch(GEN_PROMPT.format(n=n, category=category))
            collected.extend(str(q) for q in questions if isinstance(q, str) and q.strip())
            print(f"{category}: {len(collected)}/{PER_CATEGORY} ({time.time() - start:.0f}s elapsed)")
        for q in collected[:PER_CATEGORY]:
            dataset.append({"question": q, "expected_category": category})

    collected = []
    while len(collected) < GARBAGE_COUNT:
        n = min(BATCH_SIZE, GARBAGE_COUNT - len(collected))
        questions = generate_batch(GARBAGE_PROMPT.format(n=n))
        collected.extend(str(q) for q in questions if isinstance(q, str) and q.strip())
        print(f"garbage: {len(collected)}/{GARBAGE_COUNT} ({time.time() - start:.0f}s elapsed)")
    for q in collected[:GARBAGE_COUNT]:
        dataset.append({"question": q, "expected_category": "none"})

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Saved {len(dataset)} questions to {OUTPUT_PATH} in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
