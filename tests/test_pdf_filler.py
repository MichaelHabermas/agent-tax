"""Verify the filler produces a valid PDF with our values landing in the right fields.

We round-trip via pypdf — read the output, assert each mapped field's /V matches
what we wrote. This catches mapping regressions without needing visual inspection.
"""
from decimal import Decimal
import io

from pypdf import PdfReader

from agent_tax.core.models import Answers, LineItems, Taxpayer, W2
from agent_tax.core.pdf_filler import fill_1040_pdf
from agent_tax.core.tax_engine import compute_1040
from agent_tax.form_map.f1040_2025 import (
    FILING_STATUS_FIELDS,
    LINE_FIELDS,
)


def _sample_w2() -> W2:
    return W2(
        employee_first_name="Jordan A.",
        employee_last_name="Rivera",
        employee_ssn="111-11-1111",
        employee_address_line1="482 Birchwood Ln",
        employee_city="Asheville",
        employee_state="NC",
        employee_zip="28801",
        employer_name="Blue Ridge Coffee Roasters, LLC",
        employer_ein="12-3456789",
        box1_wages=Decimal("48000"),
        box2_fed_withholding=Decimal("4250"),
        box3_ss_wages=Decimal("48000"),
        box5_medicare_wages=Decimal("48000"),
    )


def test_fill_and_round_trip():
    w2 = _sample_w2()
    lines = compute_1040(w2, Answers(filing_status="single"))
    taxpayer = Taxpayer.from_w2(w2)
    pdf_bytes = fill_1040_pdf(lines, taxpayer)

    assert pdf_bytes.startswith(b"%PDF-"), "must produce a valid PDF header"

    out = PdfReader(io.BytesIO(pdf_bytes))
    assert len(out.pages) == 2

    fields = out.get_fields() or {}

    # Money lines — non-zero amounts must equal the rendered string; zeros are blank.
    expected = {
        "l1a_wages": "48000",
        "l1z_total_wages": "48000",
        "l9_total_income": "48000",
        "l11_agi": "48000",
        "l12_std_deduction": "15750",
        "l15_taxable_income": "32250",
        "l16_tax": "3635",
        "l22_total_before_credits": "3635",
        "l24_total_tax": "3635",
        "l25a_w2_withholding": "4250",
        "l25d_total_withholding": "4250",
        "l33_total_payments": "4250",
        "l34_overpayment": "615",
        "l35a_refund": "615",
        "l37_amount_owed": "",  # zero -> blank
    }
    for key, want in expected.items():
        field_name = LINE_FIELDS[key]
        actual = fields[field_name].get("/V", "")
        assert str(actual) == want, f"{key} ({field_name}): want {want!r}, got {actual!r}"

    # Identity
    assert "Rivera" in str(fields["topmostSubform[0].Page1[0].f1_15[0]"].get("/V", ""))

    # Filing-status radio — should be set to the "single" state value.
    fs_field, fs_state = FILING_STATUS_FIELDS["single"]
    assert str(fields[fs_field].get("/V", "")) == fs_state


def test_fill_handles_owed_path():
    """When withholding < tax, L37 should be populated and L34/L35a should be blank."""
    w2 = _sample_w2()
    w2.box2_fed_withholding = Decimal("1000")
    lines = compute_1040(w2, Answers(filing_status="single"))
    taxpayer = Taxpayer.from_w2(w2)
    pdf_bytes = fill_1040_pdf(lines, taxpayer)
    fields = PdfReader(io.BytesIO(pdf_bytes)).get_fields() or {}
    assert str(fields[LINE_FIELDS["l37_amount_owed"]].get("/V", "")) == "2635"
    assert str(fields[LINE_FIELDS["l35a_refund"]].get("/V", "")) == ""


def test_fill_mfj_changes_filing_status_radio():
    w2 = _sample_w2()
    lines = compute_1040(w2, Answers(filing_status="mfj"))
    taxpayer = Taxpayer.from_w2(w2)
    pdf_bytes = fill_1040_pdf(lines, taxpayer)
    fields = PdfReader(io.BytesIO(pdf_bytes)).get_fields() or {}
    fs_field, fs_state = FILING_STATUS_FIELDS["mfj"]
    assert str(fields[fs_field].get("/V", "")) == fs_state
    # MFJ doubles the std deduction
    assert str(fields[LINE_FIELDS["l12_std_deduction"]].get("/V", "")) == "31500"
