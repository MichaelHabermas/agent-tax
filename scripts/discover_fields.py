"""One-shot field discovery for assets/f1040.pdf.

Overlays each text field's short name onto the form at its rectangle position,
then renders to PNG. Reading the PNG lets a human (or vision model) map every
short name (e.g. "f1_47") to its line number — the SSOT for form_map.

Usage:  uv run python scripts/discover_fields.py
Output: /tmp/f1040_disc_p1.png, /tmp/f1040_disc_p2.png
"""
from __future__ import annotations

import io
from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "assets" / "f1040.pdf"


def _short(fullname: str) -> str:
    return fullname.split(".")[-1].replace("[0]", "")


def _widgets_by_page(reader: PdfReader) -> list[list[tuple[str, str, list[float]]]]:
    """For each page: list of (short_name, ft, rect)."""
    out: list[list[tuple[str, str, list[float]]]] = []
    for page in reader.pages:
        rows: list[tuple[str, str, list[float]]] = []
        annots = page.get("/Annots") or []
        for a in annots:
            o = a.get_object()
            if o.get("/Subtype") != "/Widget":
                continue
            parts: list[str] = []
            cur = o
            while cur is not None:
                t = cur.get("/T")
                if t:
                    parts.append(str(t))
                cur = cur.get("/Parent")
                cur = cur.get_object() if cur is not None else None
            full = ".".join(reversed(parts))
            rect = [float(x) for x in o.get("/Rect", [0, 0, 0, 0])]
            rows.append((_short(full), str(o.get("/FT")), rect))
        out.append(rows)
    return out


def _label_overlay(rows, width: float, height: float) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    for short, ft, (x0, y0, x1, y1) in rows:
        c.setFont("Helvetica-Bold", 5.5)
        c.setFillColorRGB(0.85, 0.0, 0.0)
        # text fields get name inside the box; checkboxes get name to the right
        if ft == "/Tx":
            c.drawString(x0 + 1, y0 + 2, short)
        else:
            c.drawString(x1 + 2, y0 + 1, short)
    c.save()
    buf.seek(0)
    return buf.getvalue()


def main() -> None:
    reader = PdfReader(str(SRC))
    widgets = _widgets_by_page(reader)
    writer = PdfWriter(clone_from=reader)
    for i, page in enumerate(writer.pages):
        mb = page.mediabox
        ovl_bytes = _label_overlay(widgets[i], float(mb.width), float(mb.height))
        ovl_page = PdfReader(io.BytesIO(ovl_bytes)).pages[0]
        page.merge_page(ovl_page)

    merged = Path("/tmp/f1040_disc.pdf")
    with open(merged, "wb") as f:
        writer.write(f)

    pdf = pdfium.PdfDocument(str(merged))
    for i, page in enumerate(pdf):
        img = page.render(scale=2.5).to_pil()
        out = f"/tmp/f1040_disc_p{i+1}.png"
        img.save(out)
        print("wrote", out, img.size)


if __name__ == "__main__":
    main()
