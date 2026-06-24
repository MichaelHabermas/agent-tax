"""Pure tax computation — NO LLM, NO I/O. The deterministic spine."""
from __future__ import annotations

from decimal import Decimal

from agent_tax.config.tax_year_2025 import (
    DEPENDENT_OF_ANOTHER_EARNED_BUMP,
    DEPENDENT_OF_ANOTHER_FLOOR,
    STANDARD_DEDUCTION,
    FilingStatus,
)
from agent_tax.core.models import Answers, LineItems, W2
from agent_tax.core.tax_tables import tax_from_table


def standard_deduction(status: FilingStatus, earned_income: Decimal, claimed_as_dependent: bool) -> Decimal:
    """Std deduction, with the dependent-of-another reduction.

    If someone else can claim you, your std deduction is capped at the larger of
    $1,350 or (earned income + $450), but never more than the normal std deduction.
    """
    normal = STANDARD_DEDUCTION[status]
    if not claimed_as_dependent:
        return normal
    floor_or_earned = max(DEPENDENT_OF_ANOTHER_FLOOR, earned_income + DEPENDENT_OF_ANOTHER_EARNED_BUMP)
    return min(normal, floor_or_earned)


def compute_1040(w2: W2, answers: Answers) -> LineItems:
    """Produces the line items for our supported scope: single W-2 + standard deduction."""
    wages = w2.box1_wages
    l1a = wages
    l1z = wages
    l9 = l1z  # no other income lines in scope
    l11 = l9  # no adjustments
    l12 = standard_deduction(answers.filing_status, wages, answers.can_be_claimed_as_dependent)
    l15 = max(l11 - l12, Decimal("0"))
    l16 = tax_from_table(l15, answers.filing_status)
    l22 = l16  # no Schedule 2 additions
    l24 = l22  # no other taxes
    l25a = w2.box2_fed_withholding
    l25d = l25a  # no 1099 withholding in scope
    l33 = l25d  # no other payments

    overpayment = max(l33 - l24, Decimal("0"))
    owed = max(l24 - l33, Decimal("0"))

    return LineItems(
        l1a_wages=l1a,
        l1z_total_wages=l1z,
        l9_total_income=l9,
        l11_agi=l11,
        l12_std_deduction=l12,
        l15_taxable_income=l15,
        l16_tax=l16,
        l22_total_before_credits=l22,
        l24_total_tax=l24,
        l25a_w2_withholding=l25a,
        l25d_total_withholding=l25d,
        l33_total_payments=l33,
        l34_overpayment=overpayment,
        l35a_refund=overpayment,
        l37_amount_owed=owed,
        filing_status=answers.filing_status,
    )
