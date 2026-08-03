import re

import yaml

with open("guardrails-config.yaml", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone": r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "api_key": r"\b(sk-[a-zA-Z0-9]{32,}|AKIA[0-9A-Z]{16})\b",
}

INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|prompts|rules)",
    r"you are now",
    r"new (instructions|rules|persona|role)\s*:",
    r"system prompt\s*:",
    r"disregard (everything|all|your)",
    r"pretend (you are|to be|you're)",
    r"act as (a |an )?(?!customer|user)",
    r"reveal (your|the) (system|initial|original) (prompt|instructions)",
    r"output (your|the) (system|initial) (prompt|message)",
    r"repeat (your|the) (instructions|system prompt|rules)",
    r"forget (your|all) (previous )?instructions",
]


def redact_pii(text: str, enabled_types: list[str]) -> tuple[str, list[str]]:
    found = []
    for pii_type in enabled_types:
        pattern = PII_PATTERNS.get(pii_type)
        if not pattern:
            continue
        if re.search(pattern, text):
            found.append(pii_type)
            text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text, found


def detect_injection(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in INJECTION_PATTERNS)


def apply_input_guards(text: str) -> tuple[bool, str, str | None]:
    """Returns (allowed, processed_text, block_reason)."""
    guards = CONFIG["input_guards"]

    injection_guard = guards.get("injection_detector", {})
    if injection_guard.get("enabled") and detect_injection(text):
        if injection_guard.get("action") == "block":
            return False, text, (
                "This message looks like it's trying to override my "
                "instructions, so I can't process it. Please rephrase your "
                "question about our banking FAQs."
            )

    pii_guard = guards.get("pii_scanner", {})
    if pii_guard.get("enabled"):
        text, found = redact_pii(text, pii_guard.get("patterns", []))
        if found and pii_guard.get("action") == "block":
            return False, text, (
                "Your message appears to contain sensitive personal "
                "information (" + ", ".join(found) + "). Please remove it "
                "and try again."
            )

    return True, text, None


def apply_output_guards(text: str) -> str:
    guards = CONFIG["output_guards"]
    pii_guard = guards.get("pii_scanner", {})
    if pii_guard.get("enabled"):
        text, _ = redact_pii(text, list(PII_PATTERNS.keys()))
    return text
