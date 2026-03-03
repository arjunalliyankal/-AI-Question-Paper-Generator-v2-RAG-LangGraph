# ─── utils/pdf_generator.py ──────────────────────────────────────────────────
# Handles PDF creation using ReportLab

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


# ─── Style Definitions ────────────────────────────────────────────────────────

def _build_styles():
    """Return a dict of named ParagraphStyles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CustomTitle", parent=base["Normal"],
            fontSize=14, fontName="Times-Bold",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            fontSize=11, fontName="Times-Bold",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "center": ParagraphStyle(
            "NormalCenter", parent=base["Normal"],
            fontSize=10, fontName="Times-Roman",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Normal"],
            fontSize=11, fontName="Times-Bold",
            alignment=TA_CENTER, spaceBefore=12, spaceAfter=6,
        ),
        "instruction": ParagraphStyle(
            "Instruction", parent=base["Normal"],
            fontSize=9, fontName="Times-Italic",
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "question": ParagraphStyle(
            "Question", parent=base["Normal"],
            fontSize=10, fontName="Times-Roman",
            alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=4, leftIndent=20,
        ),
        "q_number": ParagraphStyle(
            "QNumber", parent=base["Normal"],
            fontSize=10, fontName="Times-Bold",
            spaceBefore=8, spaceAfter=2,
        ),
        "subpart": ParagraphStyle(
            "Subpart", parent=base["Normal"],
            fontSize=10, fontName="Times-Roman",
            alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=2, leftIndent=30,
        ),
        "base": base["Normal"],
    }


# ─── Section Builders ─────────────────────────────────────────────────────────

def _question_row(q_label, question_text, marks, styles):
    row = Table(
        [[
            Paragraph(q_label, styles["q_number"]),
            Paragraph(question_text, styles["question"]),
            Paragraph(f"[{marks}]", styles["q_number"]),
        ]],
        colWidths=[1.2 * cm, 14.8 * cm, 1.5 * cm],
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return row


def _subpart_row(part_label, text, marks, styles):
    row = Table(
        [[
            Paragraph("", styles["base"]),
            Paragraph(f"({part_label}) {text}", styles["subpart"]),
            Paragraph(f"[{marks}]", styles["base"]),
        ]],
        colWidths=[1.2 * cm, 14.8 * cm, 1.5 * cm],
    )
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return row


def _build_header(config, styles, story):
    story.append(Paragraph(config.get("university", "XYZ UNIVERSITY").upper(), styles["title"]))
    story.append(Paragraph(f"FACULTY OF {config.get('faculty', 'DEPARTMENT').upper()}", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))
    story.append(Spacer(1, 6))

    info_data = [
        [Paragraph(f"<b>Subject:</b> {config['subject']}", styles["base"]),
         Paragraph(f"<b>Subject Code:</b> {config['subject_code']}", styles["base"])],
        [Paragraph(f"<b>Semester:</b> {config['semester']}", styles["base"]),
         Paragraph(f"<b>Exam:</b> {config['exam_type']}", styles["base"])],
        [Paragraph(f"<b>Duration:</b> {config['duration']} Hours", styles["base"]),
         Paragraph(f"<b>Max Marks:</b> {config['total_marks']}", styles["base"])],
    ]
    info_table = Table(info_data, colWidths=[9 * cm, 9 * cm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>General Instructions:</b>", styles["base"]))
    for inst in [
        "1. All sections are compulsory unless otherwise specified.",
        "2. Figures to the right indicate full marks.",
        "3. Draw neat diagrams wherever necessary.",
        "4. Assume suitable data if necessary and state the same.",
        "5. Use of calculator is not permitted.",
    ]:
        story.append(Paragraph(inst, styles["instruction"]))
    story.append(Spacer(1, 10))


def _build_section_a(config, questions, styles, story):
    qs = questions.get("section_a", [])
    if not qs:
        return
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Paragraph("SECTION – A", styles["section"]))
    story.append(Paragraph(
        f"(Short Answer Questions – Attempt any {config['sec_a_attempt']} out of {config['sec_a_count']}) "
        f"[{config['sec_a_attempt']} × {config['sec_a_marks']} = "
        f"{config['sec_a_attempt'] * config['sec_a_marks']} Marks]",
        styles["instruction"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 6))
    for i, q in enumerate(qs):
        story.append(_question_row(f"Q.{i+1}", q["question"], q["marks"], styles))


def _build_section_b(config, questions, styles, story):
    qs = questions.get("section_b", [])
    if not qs:
        return
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Paragraph("SECTION – B", styles["section"]))
    story.append(Paragraph(
        f"(Medium Answer Questions – Attempt any {config['sec_b_attempt']} out of {config['sec_b_count']}) "
        f"[{config['sec_b_attempt']} × {config['sec_b_marks']} = "
        f"{config['sec_b_attempt'] * config['sec_b_marks']} Marks]",
        styles["instruction"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 6))
    for i, q in enumerate(qs):
        story.append(_question_row(f"Q.{i+1}", q["question"], q["marks"], styles))
        for sp in q.get("sub_parts", []):
            story.append(_subpart_row(sp["part"], sp["text"], sp.get("marks", ""), styles))


def _build_section_c(config, questions, styles, story):
    qs = questions.get("section_c", [])
    if not qs:
        return
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Paragraph("SECTION – C", styles["section"]))
    story.append(Paragraph(
        f"(Long Answer Questions – Attempt any {config['sec_c_attempt']} out of {config['sec_c_count']}) "
        f"[{config['sec_c_attempt']} × {config['sec_c_marks']} = "
        f"{config['sec_c_attempt'] * config['sec_c_marks']} Marks]",
        styles["instruction"],
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 6))
    for i, q in enumerate(qs):
        elements = [_question_row(f"Q.{i+1}", q["question"], q["marks"], styles)]
        for sp in q.get("sub_parts", []):
            elements.append(_subpart_row(sp["part"], sp["text"], sp.get("marks", ""), styles))
        story.append(KeepTogether(elements))


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_pdf(config: dict, questions: dict) -> bytes:
    """
    Build a university-style question paper PDF.

    Args:
        config:    Paper configuration dictionary.
        questions: Generated questions dict (section_a, section_b, section_c).

    Returns:
        PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story  = []

    _build_header(config, styles, story)
    _build_section_a(config, questions, styles, story)
    _build_section_b(config, questions, styles, story)
    _build_section_c(config, questions, styles, story)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Paragraph("*** End of Question Paper ***", styles["center"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
