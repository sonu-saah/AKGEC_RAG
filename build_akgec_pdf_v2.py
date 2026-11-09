import json
from pathlib import Path
from xml.sax.saxutils import escape
from collections import Counter
import pymupdf

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, LongTable,
    TableStyle, PageBreak, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

DATA = Path("data")
MASTER = DATA / "akgec_master_v13.json"
BASE = DATA / "AKGEC_Master_Corrected_Base.pdf"
OUTPUT = DATA / "AKGEC_Complete_Master_Corrected_v2.pdf"
CAL_DIR = DATA / "official_calendar_pdfs"

pages = json.loads(MASTER.read_text(encoding="utf-8"))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="BookTitle2", parent=styles["Title"],
    fontSize=21, leading=28, spaceAfter=18,
    textColor=colors.HexColor("#17365D")
))
styles.add(ParagraphStyle(
    name="BookSection2", parent=styles["Heading1"],
    fontSize=15, leading=20, spaceAfter=10,
    textColor=colors.HexColor("#17365D")
))
styles.add(ParagraphStyle(
    name="BookBody2", parent=styles["BodyText"],
    fontSize=9, leading=13, spaceAfter=6
))
styles.add(ParagraphStyle(
    name="BookCell2", parent=styles["BodyText"],
    fontSize=7, leading=10, wordWrap="CJK"
))
styles.add(ParagraphStyle(
    name="BookNote2", parent=styles["BodyText"],
    fontSize=8, leading=11, spaceAfter=5,
    textColor=colors.HexColor("#8A4B08")
))

def P(value, style="BookBody2"):
    return Paragraph(
        escape(str(value if value is not None else "")).replace("\n", "<br/>"),
        styles[style]
    )

def table(rows, widths=None):
    if not rows:
        return None
    rows = [list(r) if isinstance(r, (list, tuple)) else [r] for r in rows]
    n = max(len(r) for r in rows)
    available = A4[0] - 36*mm
    if n > 12:
        return P(json.dumps(rows, ensure_ascii=False), "BookCell2")
    widths = widths or [available/n]*n
    data = [
        [P(x, "BookCell2") for x in (r + [""]*(n-len(r)))]
        for r in rows
    ]
    t = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E8EFF7")),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#B9C8D6")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(18*mm, 12*mm, "AKGEC | Compiled reference")
    canvas.drawRightString(A4[0]-18*mm, 12*mm, str(doc.page))
    canvas.restoreState()

def record_lines(record):
    for key, value in record.items():
        if value is None or value == "":
            continue
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        yield key.replace("_", " ").title() + ": " + str(value)

def fee_table_rows(records):
    rows = [[
        "Branch / Group", "Registration", "Tuition / Development",
        "PDP", "Books", "Medical", "Convocation", "Total (INR)"
    ]]
    for r in records:
        c = r.get("charges_inr", {})
        rows.append([
            r.get("branch_group", "All / Not specified"),
            c.get("registration_fee", "—"),
            c.get("tuition_and_development_fee", c.get("development_fee", "—")),
            c.get("pdp_fee", "—"),
            c.get("text_book_charges", "—"),
            c.get("medical_charges", "—"),
            c.get("convocation_charges", "—"),
            r.get("total_fee_inr", "—")
        ])
    return rows

story = [
    Spacer(1, 35*mm),
    P("AJAY KUMAR GARG ENGINEERING COLLEGE", "BookTitle2"),
    P("Complete Website Information Reference | 2026–27"),
    Spacer(1, 12*mm),
    P("Compiled from 72 selected official website sections."),
    P("Some source-derived records require final visual verification.", "BookNote2"),
    PageBreak(),
    P("Contents", "BookSection2")
]

for i, page in enumerate(pages, 1):
    story.append(P(f"{i}. {page.get('title', 'Untitled')}"))
story.append(PageBreak())

fee_written = 0
calendar_marker = "__AKGEC_CALENDAR_INSERT_HERE__"

for i, page in enumerate(pages, 1):
    title = page.get("title", f"Section {i}")
    story.append(P(f"{i}. {title}", "BookSection2"))
    if page.get("source_url"):
        story.append(P("Official source: " + page["source_url"], "BookCell2"))

    if title == "Academic Calendar":
        story.append(P(
            "The next two pages reproduce the original official calendar PDFs. "
            "They replace the incomplete OCR transcription.",
            "BookNote2"
        ))
        story.append(P(calendar_marker, "BookCell2"))
    else:
        for b in page.get("blocks", []):
            typ = b.get("type")
            if typ == "table" and b.get("rows"):
                story.append(table(b["rows"]))
                story.append(Spacer(1, 3*mm))
            elif b.get("text"):
                txt = b["text"]
                if typ == "heading":
                    story.append(P(txt, "Heading3"))
                elif typ == "list_item":
                    story.append(P("• " + txt))
                else:
                    story.append(P(txt))
            if any(s in str(b.get("verification_status", "")).lower()
                   for s in ("pending", "incomplete", "inferred")):
                story.append(P(
                    "Verification: " + str(b["verification_status"]),
                    "BookNote2"
                ))

    members = page.get("management_members", [])
    if members:
        story.append(P("Management Members", "Heading2"))
        for member in members:
            for line in record_lines(member):
                story.append(P(line, "BookCell2"))

    fees = page.get("structured_fee_records", [])
    if fees:
        btech = [r for r in fees if r.get("course") == "B.Tech"]
        others = [r for r in fees if r.get("course") != "B.Tech"]

        if btech:
            story.append(P("B.Tech Fee Structure 2026–27", "Heading2"))
            for year in ("1st Year", "2nd Year", "3rd Year", "4th Year"):
                for category in ("Regular", "Fee Waiver"):
                    group = [
                        r for r in btech
                        if r.get("year") == year and r.get("category") == category
                    ]
                    if not group:
                        continue
                    story.append(P(f"{year} — {category}", "Heading3"))
                    if year == "1st Year":
                        for r in group:
                            story.append(P(
                                f"Total fee: INR {r['total_fee_inr']:,}",
                                "BookBody2"
                            ))
                    else:
                        story.append(table(fee_table_rows(group)))
                    for r in group:
                        fee_written += 1
                        story.append(P(
                            "Source: " + r.get("source_url", ""),
                            "BookCell2"
                        ))
                        story.append(P(
                            "Verification: " + r.get("verification_status", ""),
                            "BookNote2"
                        ))
                        if r.get("notes"):
                            story.append(P("Note: " + r["notes"], "BookCell2"))

        if others:
            story.append(P("Other Fee Records", "Heading2"))
            for r in others:
                fee_written += 1
                for line in record_lines(r):
                    story.append(P(line, "BookCell2"))
                story.append(Spacer(1, 3*mm))

    if i < len(pages):
        story.append(PageBreak())

doc = SimpleDocTemplate(
    str(BASE), pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=18*mm, bottomMargin=20*mm
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)

# Replace calendar placeholder page with the original PDF pages.
calendars = [
    CAL_DIR / "Academic_Calendar_2026_27_Odd.pdf",
    CAL_DIR / "Academic_Calendar_2026_27_First_Year.pdf"
]
for f in calendars:
    if not f.exists():
        raise FileNotFoundError(f)

result = pymupdf.open()
inserted = False
with pymupdf.open(BASE) as base:
    for page in base:
        page_text = page.get_text()
        if calendar_marker in page_text:
            # Keep the section heading page, then insert both original pages.
            result.insert_pdf(base, from_page=page.number, to_page=page.number)
            for filename in calendars:
                with pymupdf.open(filename) as original:
                    result.insert_pdf(original)
            inserted = True
        else:
            result.insert_pdf(base, from_page=page.number, to_page=page.number)

if not inserted:
    result.close()
    raise RuntimeError("Calendar insertion marker not found.")

result.save(OUTPUT, garbage=4, deflate=True)
result.close()

with pymupdf.open(OUTPUT) as final:
    print("=== CORRECTED PDF v2 ===")
    print("PDF pages:", len(final))
    print("Sections:", len(pages))
    print("Fee records included:", fee_written)
    print("Original calendar pages inserted:", len(calendars))
    print("File size (MB):", round(OUTPUT.stat().st_size/1048576, 2))
    print("Saved:", OUTPUT)
