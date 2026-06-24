"""Pydantic contracts shared across layers. These ARE the guardrail (P3)."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from agent_tax.config.tax_year_2025 import FilingStatus

Money = Decimal


class W2(BaseModel):
    """Extracted from a single 2025 W-2. Only the boxes we use."""

    employee_first_name: str
    employee_last_name: str
    employee_ssn: str = Field(pattern=r"^\d{3}-?\d{2}-?\d{4}$")
    employee_address_line1: str
    employee_address_line2: str = ""
    employee_city: str
    employee_state: str = Field(min_length=2, max_length=2)
    employee_zip: str

    employer_name: str
    employer_ein: str = Field(pattern=r"^\d{2}-?\d{7}$")

    box1_wages: Money = Field(ge=0)
    box2_fed_withholding: Money = Field(ge=0)
    box3_ss_wages: Money = Field(ge=0, default=Decimal("0"))
    box5_medicare_wages: Money = Field(ge=0, default=Decimal("0"))

    @field_validator("employee_ssn", "employer_ein", mode="after")
    @classmethod
    def _strip_dashes_keep_format(cls, v: str) -> str:
        return v

    def plausibility_errors(self) -> list[str]:
        errs: list[str] = []
        if self.box2_fed_withholding > self.box1_wages:
            errs.append("federal withholding exceeds wages")
        if self.box3_ss_wages and abs(self.box3_ss_wages - self.box1_wages) > self.box1_wages * Decimal("0.5"):
            errs.append("box 3 (SS wages) deviates >50% from box 1 (wages)")
        return errs


class Answers(BaseModel):
    """Collected from the user across ≤5 questions."""

    filing_status: FilingStatus
    can_be_claimed_as_dependent: bool = False
    other_income_acknowledged: bool = True
    take_standard_deduction: bool = True


class LineItems(BaseModel):
    """The 1040 lines we fill. Money as Decimal; the PDF filler renders strings."""

    l1a_wages: Money
    l1z_total_wages: Money
    l9_total_income: Money
    l11_agi: Money
    l12_std_deduction: Money
    l15_taxable_income: Money
    l16_tax: Money
    l22_total_before_credits: Money
    l24_total_tax: Money
    l25a_w2_withholding: Money
    l25c_other_withholding: Money = Decimal("0")
    l25d_total_withholding: Money
    l33_total_payments: Money
    l34_overpayment: Money = Decimal("0")
    l35a_refund: Money = Decimal("0")
    l37_amount_owed: Money = Decimal("0")
    filing_status: FilingStatus


class Taxpayer(BaseModel):
    """Identity fields stamped onto the 1040 header. Mirrors W2 identity."""

    first_name: str
    last_name: str
    ssn: str
    address_line1: str
    address_line2: str = ""
    city: str
    state: str
    zip: str

    @classmethod
    def from_w2(cls, w2: W2) -> "Taxpayer":
        return cls(
            first_name=w2.employee_first_name,
            last_name=w2.employee_last_name,
            ssn=w2.employee_ssn,
            address_line1=w2.employee_address_line1,
            address_line2=w2.employee_address_line2,
            city=w2.employee_city,
            state=w2.employee_state,
            zip=w2.employee_zip,
        )
