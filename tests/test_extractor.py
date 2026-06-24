from decimal import Decimal
from pathlib import Path

from agent_tax.agent.extractor import extract_w2


def test_extract_sample_w2_pdf():
    pdf = Path("assets/w2_filled_sample_2025.pdf").read_bytes()
    w2 = extract_w2(pdf)

    assert w2.employee_first_name == "Jordan A."
    assert w2.employee_last_name == "Rivera"
    assert w2.employee_ssn == "111-11-1111"
    assert w2.employer_ein == "12-3456789"
    assert w2.box1_wages == Decimal("48000.00")
    assert w2.box2_fed_withholding == Decimal("4250.00")
