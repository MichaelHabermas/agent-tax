"""Fills the 2025 Form 1040 PDF. Pure I/O over pypdf + the form_map SSOT.

Renders money as whole-dollar strings (the IRS form uses whole dollars on these
lines). The W-2 input may carry cents (Decimal); we round half-up via the engine
already, so values arriving here are integral.

Returns PDF bytes — never writes to disk. The web layer streams them to the user.
"""
from __future__ import annotations

import io
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject, NumberObject, TextStringObject

from agent_tax.core.models import LineItems, Taxpayer
from agent_tax.form_map.f1040_2025 import (
    FILING_STATUS_FIELDS,
    LINE_FIELDS,
    PAGE_INDEX,
    TAXPAYER_FIELDS,
)

ASSET_PATH = Path(__file__).resolve().parents[3] / "assets" / "f1040.pdf"


def _money(d: Decimal) -> str:
    """IRS whole-dollar string. Zeros render as blank (cleaner form)."""
    if d == 0:
        return ""
    return f"{int(d):d}"


def _name_value(t: Taxpayer) -> str:
    return f"{t.first_name} {t.last_name}".strip()


def _fill_page(writer: PdfWriter, page_idx: int, values: dict[str, str]) -> None:
    if not values:
        return
    writer.update_page_form_field_values(writer.pages[page_idx], values)


def fill_1040_pdf(lines: LineItems, taxpayer: Taxpayer) -> bytes:
    """Stamp identity + filing status + line items onto the 2025 1040."""
    reader = PdfReader(str(ASSET_PATH))
    writer = PdfWriter(clone_from=reader)

    # Force the viewer to regenerate appearance streams so our values render.
    root = writer._root_object
    if "/AcroForm" in root:
        root["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    # Group by page so update_page_form_field_values can resolve hierarchies.
    page_values: dict[int, dict[str, str]] = {0: {}, 1: {}}

    # Identity
    page_values[0][TAXPAYER_FIELDS["first_name_mi"]] = f"{taxpayer.first_name}".strip()
    page_values[0][TAXPAYER_FIELDS["last_name"]] = taxpayer.last_name
    page_values[0][TAXPAYER_FIELDS["ssn"]] = taxpayer.ssn.replace("-", "")
    page_values[0][TAXPAYER_FIELDS["address_line1"]] = taxpayer.address_line1
    page_values[0][TAXPAYER_FIELDS["city"]] = taxpayer.city
    page_values[0][TAXPAYER_FIELDS["state"]] = taxpayer.state
    page_values[0][TAXPAYER_FIELDS["zip"]] = taxpayer.zip

    # Filing status — set the radio's "on" state value.
    fs_field, fs_state = FILING_STATUS_FIELDS[lines.filing_status]
    page_values[0][fs_field] = fs_state

    # Money lines (engine pre-rounded to whole dollars; render zeros as blank).
    for key, field_name in LINE_FIELDS.items():
        page_idx = PAGE_INDEX[key]
        value = getattr(lines, key)
        page_values[page_idx][field_name] = _money(value)

    _fill_page(writer, 0, page_values[0])
    _fill_page(writer, 1, page_values[1])

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
