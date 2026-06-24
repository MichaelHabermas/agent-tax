"""W-2 extraction tool.

The fast path uses PDF text extraction, which works for the supplied realistic
fixture and many text PDFs. OpenRouter vision can be added behind this interface
without changing the chat loop or tax tools.
"""
from __future__ import annotations

from decimal import Decimal
import io
import re

from pypdf import PdfReader

from agent_tax.core.models import W2


class ExtractionError(ValueError):
    pass


def _money(text: str) -> Decimal:
    return Decimal(text.replace(",", ""))


def _read_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_w2(file_bytes: bytes) -> W2:
    text = _read_pdf_text(file_bytes)
    compact = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    ssn = re.search(r"\b\d{3}-\d{2}-\d{4}\b", compact)
    ein = re.search(r"\b\d{2}-\d{7}\b", compact)
    amounts = re.findall(r"\b\d{1,3}(?:,\d{3})*\.\d{2}\b", compact)
    state_zip = re.findall(r"\b([A-Z]{2})\s+(\d{5})(?:-\d{4})?\b", compact)

    if not ssn or not ein or len(amounts) < 2 or len(state_zip) < 2:
        raise ExtractionError("I could not read the key W-2 fields from that PDF.")

    lines = compact.splitlines()
    ssn_idx = lines.index(ssn.group(0))
    employer_ein_idx = lines.index(ein.group(0))

    employer_name = lines[employer_ein_idx + 1] if len(lines) > employer_ein_idx + 1 else "Unknown employer"
    employee_first = lines[employer_ein_idx + 5] if len(lines) > employer_ein_idx + 5 else "Taxpayer"
    employee_last = lines[employer_ein_idx + 6] if len(lines) > employer_ein_idx + 6 else ""
    employee_address = lines[employer_ein_idx + 7] if len(lines) > employer_ein_idx + 7 else ""
    employee_city_state_zip = lines[employer_ein_idx + 8] if len(lines) > employer_ein_idx + 8 else ""

    city_match = re.match(r"(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", employee_city_state_zip)
    if not city_match:
        raise ExtractionError("I could not read the employee city/state/ZIP from that W-2.")

    return W2(
        employee_first_name=employee_first,
        employee_last_name=employee_last,
        employee_ssn=ssn.group(0),
        employee_address_line1=employee_address,
        employee_city=city_match.group(1),
        employee_state=city_match.group(2),
        employee_zip=city_match.group(3),
        employer_name=employer_name,
        employer_ein=ein.group(0),
        box1_wages=_money(amounts[0]),
        box2_fed_withholding=_money(amounts[1]),
        box3_ss_wages=_money(amounts[2]) if len(amounts) > 2 else _money(amounts[0]),
        box5_medicare_wages=_money(amounts[4]) if len(amounts) > 4 else _money(amounts[0]),
    )
