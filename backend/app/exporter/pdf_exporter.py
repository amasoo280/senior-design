from typing import List, Dict, Any
from reportlab.platypus import (
    SimpleDocTemplate, Table, Paragraph, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib import colors

def generate_pdf(
    rows: List[Dict[str, Any]],
    file_path: str,
    title: str = "Query Results"
) -> str:
    if not rows:
        raise ValueError("No data to export")

    # Landscape gives us breathing room
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(LETTER),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"]

    elements = []
    elements.append(Paragraph(title, styles["Title"]))

    headers = list(rows[0].keys())

    if len(headers) > 12:
        raise ValueError(
            f"Too many columns ({len(headers)}) to export cleanly to PDF. "
            "Please export as CSV instead."
        )

    # Wrap ALL cells using Paragraph
    table_data = [
        [Paragraph(str(h), styles["Heading4"]) for h in headers]
    ]

    for row in rows:
        table_data.append([
            Paragraph(str(row[h]), cell_style) for h in headers
        ])

    table = Table(table_data, repeatRows=1, hAlign="LEFT")

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    doc.build(elements)

    return file_path
