"""SSOT — mapping from semantic 1040 keys to AcroForm field names.

Discovered once via scripts/discover_fields.py (overlay-render → visual inspection
of /tmp/f1040_disc_p{1,2}.png). Locked here; the rest of the codebase imports.

Field-name conventions in assets/f1040.pdf:
  * Text fields:  topmostSubform[0].Page{1,2}[0].f{1,2}_NN[0]
  * Buttons:      topmostSubform[0].Page{1,2}[0].c{1,2}_NN[0]
  * Filing-status radio group is split across two parent subforms so each option
    has a distinct full path AND a distinct "checked" state value (/1 .. /5).
"""
from __future__ import annotations

from agent_tax.config.tax_year_2025 import FilingStatus

P1 = "topmostSubform[0].Page1[0]"
P1_ADDR = f"{P1}.Address_ReadOrder[0]"
P1_FS = f"{P1}.Checkbox_ReadOrder[0]"
P2 = "topmostSubform[0].Page2[0]"


TAXPAYER_FIELDS: dict[str, str] = {
    "first_name_mi": f"{P1}.f1_14[0]",
    "last_name":     f"{P1}.f1_15[0]",
    "ssn":           f"{P1}.f1_16[0]",
    "address_line1": f"{P1_ADDR}.f1_20[0]",
    "apt_no":        f"{P1_ADDR}.f1_21[0]",
    "city":          f"{P1_ADDR}.f1_22[0]",
    "state":         f"{P1_ADDR}.f1_23[0]",
    "zip":           f"{P1_ADDR}.f1_24[0]",
}


LINE_FIELDS: dict[str, str] = {
    "l1a_wages":              f"{P1}.f1_47[0]",
    "l1z_total_wages":        f"{P1}.f1_57[0]",
    "l9_total_income":        f"{P1}.f1_73[0]",
    "l11_agi":                f"{P1}.f1_75[0]",
    "l12_std_deduction":      f"{P2}.f2_02[0]",
    "l15_taxable_income":     f"{P2}.f2_06[0]",
    "l16_tax":                f"{P2}.f2_08[0]",
    "l22_total_before_credits": f"{P2}.f2_14[0]",
    "l24_total_tax":          f"{P2}.f2_16[0]",
    "l25a_w2_withholding":    f"{P2}.f2_17[0]",
    "l25d_total_withholding": f"{P2}.f2_20[0]",
    "l33_total_payments":     f"{P2}.f2_29[0]",
    "l34_overpayment":        f"{P2}.f2_30[0]",
    "l35a_refund":            f"{P2}.f2_31[0]",
    "l37_amount_owed":        f"{P2}.f2_35[0]",
}


# Each filing-status entry: (full field name, "checked" state value).
# pypdf's update_page_form_field_values writes the value as the field's V;
# for a /Btn radio, the value must equal the field's "on" state (per _States_).
FILING_STATUS_FIELDS: dict[FilingStatus, tuple[str, str]] = {
    "single": (f"{P1_FS}.c1_8[0]", "/1"),
    "mfj":    (f"{P1_FS}.c1_8[1]", "/2"),
    "mfs":    (f"{P1_FS}.c1_8[2]", "/3"),
    "hoh":    (f"{P1}.c1_8[0]",    "/4"),
    "qss":    (f"{P1}.c1_8[1]",    "/5"),
}


# Page index hints for filling routines that need to know which page to update.
PAGE_INDEX: dict[str, int] = {
    **{k: 0 for k in TAXPAYER_FIELDS},
    **{k: 0 for k in FILING_STATUS_FIELDS},
    "l1a_wages": 0, "l1z_total_wages": 0, "l9_total_income": 0, "l11_agi": 0,
    "l12_std_deduction": 1, "l15_taxable_income": 1, "l16_tax": 1,
    "l22_total_before_credits": 1, "l24_total_tax": 1, "l25a_w2_withholding": 1,
    "l25d_total_withholding": 1, "l33_total_payments": 1, "l34_overpayment": 1,
    "l35a_refund": 1, "l37_amount_owed": 1,
}
