"""Typed tools the chat loop is allowed to call."""
from __future__ import annotations

from agent_tax.agent.extractor import extract_w2
from agent_tax.core.models import Answers, LineItems, Taxpayer, W2
from agent_tax.core.pdf_filler import fill_1040_pdf
from agent_tax.core.tax_engine import compute_1040


def extract_w2_tool(file_bytes: bytes) -> W2:
    return extract_w2(file_bytes)


def compute_1040_tool(w2: W2, answers: Answers) -> LineItems:
    return compute_1040(w2, answers)


def fill_1040_pdf_tool(lines: LineItems, taxpayer: Taxpayer) -> bytes:
    return fill_1040_pdf(lines, taxpayer)
