from __future__ import annotations
from pathlib import Path

# ============================================================
# AUTO-DETECT PROJECT ROOT  (PricingSystem/)
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# === STANDARD PROJECT FOLDERS ===
DATA_DIR = BASE_DIR / "Data"
ASSETS_DIR = BASE_DIR / "Assets"
OUTPUT_DIR = BASE_DIR / "Output"

LOG_DIR = OUTPUT_DIR / "Quotes_Log"
PDF_DIR = OUTPUT_DIR / "Quotes_Client_PDF"

# === SPECIFIC FILES ===
MASTER_FILE = DATA_DIR / "Master_FullPricing.xlsx"
SOC_FILE = DATA_DIR / "PUC_SOC.xlsx"
COUNTER_FILE = DATA_DIR / "quote_counters.csv"
LOGO_FILE = ASSETS_DIR / "logo_pudong.png"
QRCODE_FILE = ASSETS_DIR / "wechat_qr.png"   # QR Wechat


# ============================================================
# IMPORTS
# ============================================================
import os
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    Image,
)

# ============================================================
# LOCAL CHARGES POL
# ============================================================

def get_local_charges_pol() -> List[dict]:
    """Local charges @ POL theo layout anh chốt."""
    return [
        {"name": "THC", "basis": "Per container", "amt20": 135, "amt40": 200},
        {"name": "SEAL", "basis": "Per piece", "amt20": 10, "amt40": 10},
        {"name": "AMS", "basis": "Per shipment", "amt20": 40, "amt40": 40},
        {"name": "Telex Release", "basis": "Per shipment", "amt20": 35, "amt40": 35},
        {"name": "Original B/L", "basis": "Per set", "amt20": 40, "amt40": 40},
    ]


# ============================================================
# GENERATE PDF (SINGLE DEST)
# ============================================================

def generate_quote_pdf(result: Dict[str, Any], logo_path: str) -> str:
    """
    Tạo file PDF báo giá từ result của generate_quote().
    - result: dict trả về từ engine
    - logo_path: đường dẫn file logo PNG
    Trả về: đường dẫn tuyệt đối PDF
    """

    os.makedirs(PDF_DIR, exist_ok=True)

    summary = result["summary"]
    options = result["options"]

    quote_ref = result["quote_ref_no"]
    quote_date = result["quote_date"]

    customer = summary.get("customer_name") or "Customer"
    email = summary.get("customer_email") or ""
    contact_person = summary.get("contact_person") or ""

    pol = summary.get("pol") or ""
    place = summary.get("place_of_delivery") or ""
    route_str = f"{pol} → {place}"

    incoterm = summary.get("incoterm") or ""
    commodity = summary.get("commodity_type") or ""
    is_soc = summary.get("is_soc")
    soc_display = "SOC" if is_soc else "COC"
    containers_summary = summary.get("containers_summary") or ""

    local_charges = get_local_charges_pol()

    # ===== Ready PDF path =====
    safe_customer = "".join(
        c for c in customer if c.isalnum() or c in " _-"
    ).strip() or "Customer"
    filename = f"{quote_ref} - {safe_customer}.pdf"
    pdf_path = PDF_DIR / filename

    # ===== PAGE SETUP =====
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    style_title_center = ParagraphStyle(
        "TitleCenter",
        parent=style_normal,
        fontName="Helvetica-Bold",
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor("#003366"),
    )

    style_subtitle_center = ParagraphStyle(
        "SubtitleCenter",
        parent=style_normal,
        fontName="Helvetica-Oblique",
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor("#777777"),
    )

    style_section = ParagraphStyle(
        "Section",
        parent=style_normal,
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#003366"),
        spaceBefore=6,
        spaceAfter=2,
    )

    style_small = ParagraphStyle(
        "Small",
        parent=style_normal,
        fontSize=9,
        textColor=colors.HexColor("#555555"),
    )

    story: List = []

    # ============================================================
    # 1. TITLE
    # ============================================================
    story.append(Paragraph("YOUR PERSONALIZED QUOTATION PUDONG PRIME", style_title_center))

    line_tbl = Table([[""]], colWidths=[170 * mm])
    line_tbl.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.HexColor("#003366")),
            ]
        )
    )
    story.append(line_tbl)

    story.append(Paragraph("<i>Delivering Value, Building Trust</i>", style_subtitle_center))
    story.append(Spacer(1, 4 * mm))

    # ============================================================
    # 2. VALUED CLIENT DETAILS + LOGO
    # ============================================================
    story.append(Paragraph("VALUED CLIENT DETAILS", style_section))

    # ---- Bảng thông tin khách (căn thẳng cột trái) ----
    cust_data = [
        [Paragraph("<b>Client Name:</b>", style_normal), Paragraph(customer, style_normal)],
        [Paragraph("<b>Contact Email:</b>", style_normal), Paragraph(email, style_normal)],
        [
            Paragraph("<b>Main Point of Contact:</b>", style_normal),
            Paragraph(contact_person, style_normal),
        ],
    ]

    # colWidths label = 50mm để thẳng với Route/Incoterm
    cust_table = Table(cust_data, colWidths=[50 * mm, 120 * mm])
    cust_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    left_cell = [cust_table]

    # ---- Logo + right-aligned text ----
    logo_flow = None
    if logo_path and os.path.exists(logo_path):
        logo_flow = Image(logo_path)
        logo_flow._restrictSize(70 * mm, 30 * mm)

    right_lines = [
        "JC TRANS ID: 155843",
        "FMC OTI License: 024060",
        f"Ref: {quote_ref}",
        f"Date: {quote_date}",
    ]

    right_para = Paragraph(
        "<br/>".join(right_lines),
        ParagraphStyle(
            "RightBlock",
            parent=style_small,
            alignment=2,  # RIGHT
            textColor=colors.HexColor("#444444"),
            leading=12,
        ),
    )

    right_cell: List = []
    if logo_flow:
        right_cell.append(logo_flow)
        right_cell.append(Spacer(1, 2 * mm))
    right_cell.append(right_para)

    header_table = Table(
        [[left_cell, right_cell]],
        colWidths=[100 * mm, 60 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),

                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),

                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 3 * mm))

    # ============================================================
    # 3. SHIPMENT DETAILS
    # ============================================================
    story.append(Paragraph("SHIPMENT DETAILS", style_section))

    ship_data = [
        [Paragraph("<b>Route:</b>", style_normal), Paragraph(route_str, style_normal)],
        [Paragraph("<b>Incoterm:</b>", style_normal), Paragraph(incoterm, style_normal)],
        [Paragraph("<b>Commodity:</b>", style_normal), Paragraph(commodity, style_normal)],
        [Paragraph("<b>SOC / COC:</b>", style_normal), Paragraph(soc_display, style_normal)],
        [
            Paragraph("<b>Containers:</b>", style_normal),
            Paragraph(containers_summary, style_normal),
        ],
    ]

    ship_table = Table(ship_data, colWidths=[50 * mm, 120 * mm])
    ship_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(ship_table)
    story.append(Spacer(1, 2 * mm))

    # ============================================================
    # 4. OCEAN FREIGHT OPTIONS
    # ============================================================
    story.append(Paragraph("OCEAN FREIGHT OPTIONS", style_section))

    ocean_header = ["Carrier", "Validity", "20GP", "40GP", "40HQ", "Total"]
    ocean_data = [ocean_header]

    for opt in options:
        rates = opt.get("container_rates", {})
        r20 = rates.get("20GP", "")
        r40 = rates.get("40GP", "")
        r40hq = rates.get("40HQ", "")
        total = opt.get("total_ocean_amount", "")
        currency = opt.get("currency", "")
        validity = f"{opt.get('valid_from', '')} → {opt.get('valid_to', '')}"

        ocean_data.append(
            [
                opt.get("carrier", ""),
                validity,
                r20,
                r40,
                r40hq,
                f"{total} {currency}",
            ]
        )

    ocean_table = Table(
        ocean_data,
        colWidths=[30 * mm, 55 * mm, 20 * mm, 20 * mm, 20 * mm, 25 * mm],
    )
    ocean_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(ocean_table)
    story.append(Spacer(1, 1.5 * mm))

    # ============================================================
    # 5. LOCAL CHARGES @ POL
    # ============================================================
    story.append(Paragraph(f"LOCAL CHARGES @ POL ({pol})", style_section))
    story.append(Paragraph("Not included in above ocean freight.", style_small))

    lc_header = ["Charge Name", "Basis", "20' (USD)", "40' (USD)"]
    lc_data = [lc_header]

    for lc in local_charges:
        lc_data.append([lc["name"], lc["basis"], lc["amt20"], lc["amt40"]])

    lc_table = Table(
        lc_data,
        colWidths=[60 * mm, 60 * mm, 25 * mm, 25 * mm],
    )
    lc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(lc_table)
    story.append(Spacer(1, 1.5 * mm))

    # ============================================================
    # 6. NOTES
    # ============================================================
    story.append(Paragraph("NOTES", style_section))

    recommended_opt = None
    for opt in options:
        if opt.get("is_recommended"):
            recommended_opt = opt
            break
    if recommended_opt is None and options:
        recommended_opt = options[0]

    if recommended_opt:
        note = recommended_opt.get("notes") or ""
        carrier = recommended_opt.get("carrier") or ""
        if note:
            text = f"• Recommended carrier: <b>{carrier}</b> – {note}"
        else:
            text = f"• Recommended carrier: <b>{carrier}</b>."
    else:
        text = "• No specific routing notes."

    story.append(Paragraph(text, style_normal))
    story.append(Spacer(1, 2 * mm))

    # ============================================================
    # 7. TERMS & CONDITIONS
    # ============================================================
    story.append(Paragraph("TERMS & CONDITIONS", style_section))

    terms = [
        "• This quote is all-in with no hidden charges — guaranteed.",
        "• For contract-level or high-volume shipments, we can secure significantly better pricing upon request.",
        "• If this is an urgent shipment, please inform us to avoid roll.",
        "• If ISF filing is required, please notify at booking time.",
    ]
    for t in terms:
        story.append(Paragraph(t, style_normal))

    story.append(Spacer(1, 3 * mm))

    # ============================================================
    # 8. PREPARED BY (horizontal) + QR WECHAT
    # ============================================================
    prepared_line = (
        "Prepared by: <b>Nelson Huynh</b> | "
        "Sales Team Leader | "
        "Wechat: NelsonPudong | "
        "Phone: +84 931.301.014"
    )

    prepared_para = Paragraph(
        prepared_line,
        ParagraphStyle(
            "Prepared",
            parent=style_normal,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#333333"),
        ),
    )

    qr_img = None
    if QRCODE_FILE.exists():
        qr_img = Image(str(QRCODE_FILE))
        qr_img._restrictSize(25 * mm, 25 * mm)

    if qr_img:
        footer_table = Table(
            [[prepared_para, qr_img]],
            colWidths=[145 * mm, 25 * mm],
        )
        footer_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(footer_table)
    else:
        story.append(prepared_para)

    # ============================================================
    # BUILD PDF
    # ============================================================
    doc.build(story)
    return str(pdf_path)


# ============================================================
# GENERATE PDF MULTI-DESTINATION
# ============================================================

def generate_quote_pdf_multi(results: List[Dict[str, Any]], logo_path: str) -> str:
    """
    Tạo file PDF báo giá từ N result của generate_quote() (multi Place of Delivery).
    - results: list các dict trả về từ engine (mỗi dict = 1 PODelivery)
    - logo_path: đường dẫn file logo PNG
    Trả về: đường dẫn tuyệt đối PDF
    """

    if not results:
        raise ValueError("results rỗng, không thể tạo PDF multi.")

    os.makedirs(PDF_DIR, exist_ok=True)

    first = results[0]
    summary0 = first["summary"]

    quote_ref0 = first["quote_ref_no"]
    quote_date = first["quote_date"]

    customer = summary0.get("customer_name") or "Customer"
    email = summary0.get("customer_email") or ""
    contact_person = summary0.get("contact_person") or ""

    pol = summary0.get("pol") or ""

    local_charges = get_local_charges_pol()

    # ===== Ready PDF path =====
    safe_customer = "".join(
        c for c in customer if c.isalnum() or c in " _-"
    ).strip() or "Customer"
    filename = f"{quote_ref0} - {safe_customer} - MULTI.pdf"
    pdf_path = PDF_DIR / filename

    # ===== PAGE SETUP =====
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]

    style_title_center = ParagraphStyle(
        "TitleCenter",
        parent=style_normal,
        fontName="Helvetica-Bold",
        fontSize=15,
        alignment=1,
        textColor=colors.HexColor("#003366"),
    )

    style_subtitle_center = ParagraphStyle(
        "SubtitleCenter",
        parent=style_normal,
        fontName="Helvetica-Oblique",
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor("#777777"),
    )

    style_section = ParagraphStyle(
        "Section",
        parent=style_normal,
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#003366"),
        spaceBefore=6,
        spaceAfter=2,
    )

    style_small = ParagraphStyle(
        "Small",
        parent=style_normal,
        fontSize=9,
        textColor=colors.HexColor("#555555"),
    )

    story: List = []

    # ============================================================
    # 1. TITLE
    # ============================================================
    story.append(Paragraph("YOUR PERSONALIZED QUOTATION PUDONG PRIME", style_title_center))

    line_tbl = Table([[""]], colWidths=[170 * mm])
    line_tbl.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.HexColor("#003366")),
            ]
        )
    )
    story.append(line_tbl)

    story.append(Paragraph("<i>Delivering Value, Building Trust</i>", style_subtitle_center))
    story.append(Spacer(1, 4 * mm))

    # ============================================================
    # 2. VALUED CLIENT DETAILS + LOGO
    # ============================================================
    story.append(Paragraph("VALUED CLIENT DETAILS", style_section))

    cust_data = [
        [Paragraph("<b>Client Name:</b>", style_normal), Paragraph(customer, style_normal)],
        [Paragraph("<b>Contact Email:</b>", style_normal), Paragraph(email, style_normal)],
        [
            Paragraph("<b>Main Point of Contact:</b>", style_normal),
            Paragraph(contact_person, style_normal),
        ],
    ]

    cust_table = Table(cust_data, colWidths=[50 * mm, 120 * mm])
    cust_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    left_cell = [cust_table]

    logo_flow = None
    if logo_path and os.path.exists(logo_path):
        logo_flow = Image(logo_path)
        logo_flow._restrictSize(70 * mm, 30 * mm)

    right_lines = [
        "JC TRANS ID: 155843",
        "FMC OTI License: 024060",
        f"Ref: {quote_ref0}",
        f"Date: {quote_date}",
    ]

    right_para = Paragraph(
        "<br/>".join(right_lines),
        ParagraphStyle(
            "RightBlock",
            parent=style_small,
            alignment=2,  # RIGHT
            textColor=colors.HexColor("#444444"),
            leading=12,
        ),
    )

    right_cell: List = []
    if logo_flow:
        right_cell.append(logo_flow)
        right_cell.append(Spacer(1, 2 * mm))
    right_cell.append(right_para)

    header_table = Table(
        [[left_cell, right_cell]],
        colWidths=[100 * mm, 60 * mm],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 3 * mm))

    # ============================================================
    # 3. LOOP MỖI SHIPMENT / PLACE OF DELIVERY
    # ============================================================
    for res in results:
        summary = res["summary"]
        options = res["options"]

        pol_i = summary.get("pol") or pol
        place_i = summary.get("place_of_delivery") or ""
        route_str = f"{pol_i} → {place_i}"

        incoterm_i = summary.get("incoterm") or ""
        commodity_i = summary.get("commodity_type") or ""
        is_soc_i = summary.get("is_soc")
        soc_display_i = "SOC" if is_soc_i else "COC"
        containers_summary_i = summary.get("containers_summary") or ""

        # === SHIPMENT DETAILS CHO ROUTE NÀY ===
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(f"SHIPMENT DETAILS – {place_i}", style_section))

        ship_data = [
            [Paragraph("<b>Route:</b>", style_normal), Paragraph(route_str, style_normal)],
            [Paragraph("<b>Incoterm:</b>", style_normal), Paragraph(incoterm_i, style_normal)],
            [Paragraph("<b>Commodity:</b>", style_normal), Paragraph(commodity_i, style_normal)],
            [Paragraph("<b>SOC / COC:</b>", style_normal), Paragraph(soc_display_i, style_normal)],
            [
                Paragraph("<b>Containers:</b>", style_normal),
                Paragraph(containers_summary_i, style_normal),
            ],
        ]

        ship_table = Table(ship_data, colWidths=[50 * mm, 120 * mm])
        ship_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(ship_table)
        story.append(Spacer(1, 2 * mm))

        # === OCEAN FREIGHT OPTIONS CHO ROUTE NÀY ===
        story.append(Paragraph(f"OCEAN FREIGHT OPTIONS – {place_i}", style_section))

        ocean_header = ["Carrier", "Validity", "20GP", "40GP", "40HQ", "Total"]
        ocean_data = [ocean_header]

        for opt in options:
            rates = opt.get("container_rates", {})
            r20 = rates.get("20GP", "")
            r40 = rates.get("40GP", "")
            r40hq = rates.get("40HQ", "")
            total = opt.get("total_ocean_amount", "")
            currency = opt.get("currency", "")
            validity = f"{opt.get('valid_from', '')} → {opt.get('valid_to', '')}"

            ocean_data.append(
                [
                    opt.get("carrier", ""),
                    validity,
                    r20,
                    r40,
                    r40hq,
                    f"{total} {currency}",
                ]
            )

        ocean_table = Table(
            ocean_data,
            colWidths=[30 * mm, 55 * mm, 20 * mm, 20 * mm, 20 * mm, 25 * mm],
        )
        ocean_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(ocean_table)
        story.append(Spacer(1, 2 * mm))

        # === NOTES NGẮN CHO ROUTE NÀY (OPTIONAL) ===
        recommended_opt = None
        for opt in options:
            if opt.get("is_recommended"):
                recommended_opt = opt
                break
        if recommended_opt is None and options:
            recommended_opt = options[0]

        if recommended_opt:
            note = recommended_opt.get("notes") or ""
            carrier = recommended_opt.get("carrier") or ""
            if note:
                text = f"• Recommended carrier for {place_i}: <b>{carrier}</b> – {note}"
            else:
                text = f"• Recommended carrier for {place_i}: <b>{carrier}</b>."
            story.append(Paragraph(text, style_normal))
            story.append(Spacer(1, 1.5 * mm))

    # ============================================================
    # 4. LOCAL CHARGES @ POL (IN CHUNG)
    # ============================================================
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(f"LOCAL CHARGES @ POL ({pol})", style_section))
    story.append(Paragraph("Not included in above ocean freight.", style_small))

    lc_header = ["Charge Name", "Basis", "20' (USD)", "40' (USD)"]
    lc_data = [lc_header]

    for lc in local_charges:
        lc_data.append([lc["name"], lc["basis"], lc["amt20"], lc["amt40"]])

    lc_table = Table(
        lc_data,
        colWidths=[60 * mm, 60 * mm, 25 * mm, 25 * mm],
    )
    lc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(lc_table)
    story.append(Spacer(1, 2 * mm))

    # ============================================================
    # 5. TERMS & CONDITIONS (IN CHUNG)
    # ============================================================
    story.append(Paragraph("TERMS & CONDITIONS", style_section))

    terms = [
        "• This quote is all-in with no hidden charges — guaranteed.",
        "• For contract-level or high-volume shipments, we can secure significantly better pricing upon request.",
        "• If this is an urgent shipment, please inform us to avoid roll.",
        "• If ISF filing is required, please notify at booking time.",
    ]
    for t in terms:
        story.append(Paragraph(t, style_normal))

    story.append(Spacer(1, 3 * mm))

    # ============================================================
    # 6. PREPARED BY (horizontal) + QR WECHAT
    # ============================================================
    prepared_line = (
        "Prepared by: <b>Nelson Huynh</b> | "
        "Sales Team Leader | "
        "Wechat: NelsonPudong | "
        "Phone: +84 931.301.014"
    )

    prepared_para = Paragraph(
        prepared_line,
        ParagraphStyle(
            "Prepared",
            parent=style_normal,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#333333"),
        ),
    )

    qr_img = None
    if QRCODE_FILE.exists():
        qr_img = Image(str(QRCODE_FILE))
        qr_img._restrictSize(25 * mm, 25 * mm)

    if qr_img:
        footer_table = Table(
            [[prepared_para, qr_img]],
            colWidths=[145 * mm, 25 * mm],
        )
        footer_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(footer_table)
    else:
        story.append(prepared_para)

    # ============================================================
    # BUILD PDF
    # ============================================================
    doc.build(story)
    return str(pdf_path)
