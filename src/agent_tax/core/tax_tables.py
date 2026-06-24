"""IRS Tax Table reproduction.

For taxable income <$100k the IRS requires the Tax Table, not bracket math.
The table is computed at the midpoint of each $50 range, then **half-up** rounded
to whole dollars. Python's built-in round() is banker's (round-half-to-even) and
gives wrong answers — we use Decimal+ROUND_HALF_UP everywhere.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from agent_tax.config.tax_year_2025 import (
    BRACKETS,
    TAX_TABLE_CEILING,
    TAX_TABLE_MIDPOINT_OFFSET,
    TAX_TABLE_RANGE,
    FilingStatus,
)


def _half_up(x: Decimal) -> Decimal:
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _bracket_tax(taxable: Decimal, status: FilingStatus) -> Decimal:
    """Raw bracketed tax — used internally by the table lookup."""
    brackets = BRACKETS[status]
    tax = Decimal("0")
    for i, (lo, rate) in enumerate(brackets):
        hi = brackets[i + 1][0] if i + 1 < len(brackets) else None
        if hi is not None and taxable > hi:
            tax += (hi - lo) * rate
        elif taxable > lo:
            tax += (taxable - lo) * rate
            break
        else:
            break
    return tax


def tax_from_table(taxable: Decimal, status: FilingStatus) -> Decimal:
    """Public: looks up tax for <$100k via the $50-range midpoint, half-up.

    For >=$100k, falls back to the Tax Computation Worksheet (continuous bracket math).
    """
    taxable = max(taxable, Decimal("0"))
    if taxable == 0:
        return Decimal("0")
    if taxable >= TAX_TABLE_CEILING:
        return _half_up(_bracket_tax(taxable, status))
    range_floor = (taxable // TAX_TABLE_RANGE) * TAX_TABLE_RANGE
    midpoint = range_floor + TAX_TABLE_MIDPOINT_OFFSET
    return _half_up(_bracket_tax(midpoint, status))
