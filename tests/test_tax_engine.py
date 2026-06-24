"""Golden test (no LLM): the sample W-2 ($48k single) must produce the
hand-verified 1040 lines. If this test goes red, the engine is wrong — not the test.

Sample target lines (from SPECS §3, hand-verified against the 2025 IRS Tax Table):
    L15 (taxable)   = 32,250
    L16 (tax)       = 3,635
    L34 (refund)    = 615
"""
from decimal import Decimal

import pytest

from agent_tax.core.models import Answers, W2
from agent_tax.core.tax_engine import compute_1040, standard_deduction
from agent_tax.core.tax_tables import tax_from_table


def _sample_w2(wages: Decimal = Decimal("48000"), wh: Decimal = Decimal("4250")) -> W2:
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
        box1_wages=wages,
        box2_fed_withholding=wh,
        box3_ss_wages=wages,
        box5_medicare_wages=wages,
    )


def test_golden_single_48k():
    w2 = _sample_w2()
    lines = compute_1040(w2, Answers(filing_status="single"))
    assert lines.l1a_wages == Decimal("48000")
    assert lines.l12_std_deduction == Decimal("15750")
    assert lines.l15_taxable_income == Decimal("32250")
    assert lines.l16_tax == Decimal("3635")
    assert lines.l24_total_tax == Decimal("3635")
    assert lines.l33_total_payments == Decimal("4250")
    assert lines.l34_overpayment == Decimal("615")
    assert lines.l35a_refund == Decimal("615")
    assert lines.l37_amount_owed == Decimal("0")


def test_python_round_trap_documented():
    """Documents the bug we avoided: Python's round() is banker's rounding."""
    # raw bracket on the midpoint of $32,250's range ($32,225) is $3,634.50
    # half-up -> 3635 (correct, IRS Tax Table)
    # banker's round -> 3634 (wrong — rounds half-to-even)
    assert tax_from_table(Decimal("32250"), "single") == Decimal("3635")
    assert round(3634.50) == 3634  # banker's — would have been a bug


def test_owed_path_single():
    """Withholding < tax → amount owed on L37, refund 0."""
    w2 = _sample_w2(wages=Decimal("48000"), wh=Decimal("1000"))
    lines = compute_1040(w2, Answers(filing_status="single"))
    assert lines.l34_overpayment == Decimal("0")
    assert lines.l35a_refund == Decimal("0")
    assert lines.l37_amount_owed == Decimal("2635")


def test_mfj_std_deduction_doubles():
    w2 = _sample_w2()
    lines = compute_1040(w2, Answers(filing_status="mfj"))
    assert lines.l12_std_deduction == Decimal("31500")
    assert lines.l15_taxable_income == Decimal("16500")


def test_hoh_std_deduction():
    w2 = _sample_w2()
    lines = compute_1040(w2, Answers(filing_status="hoh"))
    assert lines.l12_std_deduction == Decimal("23625")


def test_dependent_of_another_reduces_std_deduction():
    # earned income $48k → cap = min(normal 15750, max(1350, 48000+450)) = 15750 (normal binds)
    sd = standard_deduction("single", Decimal("48000"), claimed_as_dependent=True)
    assert sd == Decimal("15750")
    # tiny earned income → floor binds: min(15750, max(1350, 500+450)) = 1350
    sd_low = standard_deduction("single", Decimal("500"), claimed_as_dependent=True)
    assert sd_low == Decimal("1350")


def test_zero_taxable_income_does_not_explode():
    w2 = _sample_w2(wages=Decimal("10000"), wh=Decimal("0"))
    lines = compute_1040(w2, Answers(filing_status="single"))
    assert lines.l15_taxable_income == Decimal("0")
    assert lines.l16_tax == Decimal("0")
