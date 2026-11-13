#!/usr/bin/env python3
"""Build a school-format Word document from a simple JSON spec.

Usage:
    python make_docx.py spec.json output.docx

Spec format (all keys optional except "blocks"):
{
  "title": "Годишно тематично разпределение",
  "subtitle": "Математика, X клас, 2026/2027",
  "landscape": true,                 # use for ГТР and wide tables (page is always A4)
  "line_spacing": 1.15,              # optional, e.g. when a template prescribes spacing
  "header_fields": [["Училище", "....."], ["Учител", "....."]],
  "blocks": [
    {"type": "heading", "text": "Цели", "level": 2},
    {"type": "paragraph", "text": "Текст. **удебелено** се поддържа."},
    {"type": "bullets", "items": ["едно", "две"]},
    {"type": "numbered", "items": ["първо", "второ"]},
    {"type": "table", "columns": ["№", "Тема"], "rows": [["1", "..."]],
     "widths_cm": [1, 8]},
    {"type": "page_break"},
    {"type": "signature", "lines": ["Изготвил: ............", "Утвърдил: ............"]}
  ]
}
"""
import json
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

FONT = "Times New Roman"


def set_base_style(doc):
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for name in ("Heading 1", "Heading 2", "Heading 3", "Title"):
        st = doc.styles[name]
        st.font.name = FONT
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT) if st.element.rPr is not None else None


def add_runs(par, text, size=None, bold_all=False):
    # Supports **bold** spans.
    parts = re.split(r"(\*\*[^*]+\*\*)", text or "")
    for part in parts:
        if not part:
            continue
        bold = part.startswith("**") and part.endswith("**")
        run = par.add_run(part[2:-2] if bold else part)
        run.bold = bold or bold_all
        run.font.name = FONT
        if size:
            run.font.size = Pt(size)


def shade(cell, hex_fill="D9E2F3"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def add_table(doc, block):
    cols = block["columns"]
    rows = block.get("rows", [])
    size = block.get("font_size", 10)
    table = doc.add_table(rows=1, cols=len(cols))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0]
    repeat_header(hdr)
    for i, c in enumerate(cols):
        cell = hdr.cells[i]
        cell.text = ""
        add_runs(cell.paragraphs[0], str(c), size=size, bold_all=True)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(cell)
    for r in rows:
        cells = table.add_row().cells
        for i in range(len(cols)):
            val = r[i] if i < len(r) else ""
            cells[i].text = ""
            lines = str(val).split("\n")
            add_runs(cells[i].paragraphs[0], lines[0], size=size)
            for extra in lines[1:]:
                add_runs(cells[i].add_paragraph(), extra, size=size)
    widths = block.get("widths_cm")
    if widths:
        # Fixed layout + explicit grid, otherwise LibreOffice/Word may render equal columns.
        table.autofit = False
        tblPr = table._tbl.tblPr
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tblPr.append(layout)
        for i, gc in enumerate(table._tbl.tblGrid.findall(qn("w:gridCol"))):
            if i < len(widths):
                gc.set(qn("w:w"), str(int(Cm(widths[i]).twips)))
        for row in table.rows:
            for i, w in enumerate(widths[: len(cols)]):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()


def build(spec, out):
    doc = Document()
    set_base_style(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)  # A4 – стандартът в българските училища
    if spec.get("line_spacing"):
        doc.styles["Normal"].paragraph_format.line_spacing = float(spec["line_spacing"])
    if spec.get("landscape"):
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(2))

    for label, value in spec.get("header_fields", []):
        p = doc.add_paragraph()
        add_runs(p, f"**{label}:** {value}")

    if spec.get("title"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, spec["title"].upper(), size=14, bold_all=True)
    if spec.get("subtitle"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_runs(p, spec["subtitle"], size=12, bold_all=True)

    for b in spec["blocks"]:
        t = b.get("type")
        if t == "heading":
            h = doc.add_heading(level=b.get("level", 2))
            add_runs(h, b["text"])
        elif t == "paragraph":
            p = doc.add_paragraph()
            add_runs(p, b["text"])
        elif t in ("bullets", "numbered"):
            style = "List Bullet" if t == "bullets" else "List Number"
            for item in b["items"]:
                add_runs(doc.add_paragraph(style=style), item)
        elif t == "table":
            add_table(doc, b)
        elif t == "page_break":
            doc.add_page_break()
        elif t == "signature":
            doc.add_paragraph()
            for line in b["lines"]:
                add_runs(doc.add_paragraph(), line)
        else:
            raise ValueError(f"Unknown block type: {t}")
    doc.save(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        build(json.load(f), sys.argv[2])
    print("saved", sys.argv[2])
