#!/usr/bin/env python3
"""Generate the sample filled 2025 Form W-2 (employee Copy B).

It does NOT draw a form. It stamps sample values onto the **genuine IRS
Copy B page** (extracted from docs/w2_blank_2025.pdf) at the form's real field
coordinates, then flattens to one page. The result is byte-for-byte the official
IRS form with data typed in — so it looks exactly like a real W-2.

Fake/test data only; SSN 111-11-1111 is the placeholder that signals it is not real.

Deps: pypdf, reportlab.   Run:  python scripts/generate_sample_w2.py

NOTE (OMB number): the IRS's own W-2 PDF renders "OMB No. 1545-0029" in non-Adobe
viewers (Preview/poppler/pypdf) due to a font-encoding quirk in the IRS file. The
true W-2 OMB is 1545-0008. We leave the genuine form untouched (see SPECS §9).
"""
import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

REPO = Path(__file__).resolve().parents[1]
BLANK = REPO / "docs" / "w2_blank_2025.pdf"
OUT = REPO / "docs" / "w2_filled_sample_2025.pdf"
COPY_B_PAGE = 3  # index of "Copy B—To Be Filed With Employee's FEDERAL Tax Return"

# --- sample taxpayer (single source for this fixture; nothing app-facing) ---
SSN = "111-11-1111"
EMP_FIRST, EMP_LAST = "Jordan A.", "Rivera"
EMP_ADDR = ("482 Birchwood Ln", "Asheville, NC 28801")
EIN = "12-3456789"
EMPLOYER = ("Blue Ridge Coffee Roasters, LLC", "1200 Riverside Dr", "Asheville, NC 28801")
CONTROL = "00123"
BOX = dict(b1="48,000.00", b2="4,250.00", b3="48,000.00", b4="2,976.00",
           b5="48,000.00", b6="696.00", b12a_code="DD", b12a_amt="6,200.00",
           b15_state="NC", b15_id="0123456", b16="48,000.00", b17="2,040.00")


def build_overlay(w, h):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))

    def L(x, y, s, size=9.5):
        c.setFont("Helvetica", size); c.drawString(x, y, s)

    def R(xr, y, s, size=9.5):
        c.setFont("Helvetica", size); c.drawRightString(xr, y, s)

    # identity column (coords = the form's real field rectangles)
    L(156, 734, SSN, 10)
    L(41, 710, EIN)
    L(41, 683, EMPLOYER[0]); L(41, 671, EMPLOYER[1]); L(41, 659, EMPLOYER[2])
    L(41, 614, CONTROL)
    L(41, 590, EMP_FIRST); L(177, 590, EMP_LAST)
    L(41, 574, EMP_ADDR[0]); L(41, 562, EMP_ADDR[1])
    # money boxes (right-aligned in their fields)
    R(449, 710, BOX["b1"]); R(571, 710, BOX["b2"])
    R(450, 686, BOX["b3"]); R(571, 686, BOX["b4"])
    R(450, 662, BOX["b5"]); R(571, 662, BOX["b6"])
    L(466, 590, BOX["b12a_code"]); R(571, 590, BOX["b12a_amt"])
    # state row
    L(41, 482, BOX["b15_state"]); L(69, 482, BOX["b15_id"])
    R(277, 482, BOX["b16"]); R(356, 482, BOX["b17"])
    # No watermark: SSN 111-11-1111 (+ fake employer/EIN) is the test-data tell,
    # so the form reads exactly like a real W-2. (Fixture is fake data — SPECS §1.5/§9.)
    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]


def main():
    reader = PdfReader(str(BLANK))
    base = reader.pages[COPY_B_PAGE]
    mb = base.mediabox
    base.merge_page(build_overlay(float(mb.width), float(mb.height)))
    if "/Annots" in base:                 # drop empty interactive widgets -> clean flatten
        del base["/Annots"]
    out = PdfWriter(); out.add_page(base)
    with open(OUT, "wb") as f:
        out.write(f)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
