"""Code guardrails: scope, validation, and the hard question cap."""
from __future__ import annotations

from agent_tax.core.models import W2

MAX_QUESTIONS = 5
SCOPE_REFUSAL = (
    "I can only prepare a simple educational 2025 federal Form 1040 from one W-2, "
    "using the standard deduction. This is not tax advice and it is not an e-filed return."
)


def enforce_question_budget(question_count: int) -> None:
    if question_count >= MAX_QUESTIONS:
        raise ValueError("The five-question limit has been reached.")


def validate_w2(w2: W2) -> list[str]:
    issues = w2.plausibility_errors()
    if not w2.employee_first_name or not w2.employee_last_name:
        issues.append("employee name is missing")
    if not w2.employee_address_line1 or not w2.employee_city:
        issues.append("employee address is incomplete")
    return issues


def is_yes(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {"y", "yes", "yeah", "yep", "true", "correct", "standard", "ok", "okay"}


def parse_filing_status(text: str) -> str | None:
    normalized = " ".join(text.strip().lower().replace("-", " ").split())
    choices = {
        "single": "single",
        "s": "single",
        "married filing jointly": "mfj",
        "mfj": "mfj",
        "jointly": "mfj",
        "married filing separately": "mfs",
        "mfs": "mfs",
        "separately": "mfs",
        "head of household": "hoh",
        "hoh": "hoh",
        "qualifying surviving spouse": "qss",
        "surviving spouse": "qss",
        "qss": "qss",
    }
    return choices.get(normalized)
