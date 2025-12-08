# ==================== GENERATOR.PY (FINAL CLEAN VERSION) ====================

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

from .models import BASE_DIR, OUTPUT_DIR


PDF_DIR = OUTPUT_DIR / "Quotes_Client_PDF"
LOGO = BASE_DIR / "Assets" / "logo_pudong.png"


def generate_quote_pdf(result: Dict[str, Any]) -> str:

    os.makedirs(PDF_DIR, exist_ok=True)

    ref = result["quote_ref_no"]
    customer = result["summary"]["customer_name"]
    filename = f"{ref} - {customer}.pdf"
    pdf_path = PDF_DIR / filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=12*mm,
        bottomMargin=12*mm
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title = ParagraphStyle("title", parent=normal, fontSize=18, alignment=1)

    story = []

    story.append(Paragraph("QUOTATION SUMMARY", title))
    story.append(Spacer(1, 10))

    # HEADER
    story.append(Paragraph(f"<b>Customer:</b> {customer}", normal))
    story.append(Paragraph(f"<b>Date:</b> {result['quote_date']}", normal))
    story.append(Spacer(1, 8))

    # SUMMARY
    s = result["summary"]
    story.append(Paragraph(f"<b>Route:</b> {s['pol']} → {s['place_of_delivery']}", normal))
    story.append(Paragraph(f"<b>Commodity:</b> {s['commodity_type']}", normal))
    story.append(Paragraph(f"<b>Containers:</b> {s['containers_summary']}", normal))
    story.append(Spacer(1, 10))

    # OPTIONS TABLE
    head = ["Carrier", "POD", "20GP", "40GP", "40HQ", "Total"]
    data = [head]

    for opt in result["options"]:
        ct = opt["container_rates"]
        data.append([
            opt["carrier"],
            opt["pod"],
            ct.get("20GP", ""),
            ct.get("40GP", ""),
            ct.get("40HQ", ""),
            opt["total_ocean_amount"],
        ])

    tbl = Table(data, colWidths=[35*mm, 30*mm, 20*mm, 20*mm, 20*mm, 25*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey)
    ]))

    story.append(tbl)
    story.append(Spacer(1, 15))

    # FOOTER
    if LOGO.exists():
        img = Image(str(LOGO))
        img._restrictSize(60*mm, 20*mm)
        story.append(img)

    doc.build(story)
    return str(pdf_path)
