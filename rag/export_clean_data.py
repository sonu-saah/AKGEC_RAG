import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


INPUT_FILE = Path("data/rag_documents.json")
OUTPUT_DIR = Path("data/final")

TXT_FILE = OUTPUT_DIR / "AKGEC_Clean_Data.txt"
PDF_FILE = OUTPUT_DIR / "AKGEC_Clean_Data.pdf"


# Clean unnecessary whitespace from scraped text.
def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


# Create readable sections from each scraped document.
def build_sections(documents):
    sections = []

    for doc in documents:
        text = clean_text(doc.get("text", ""))

        if not text:
            continue

        source = doc.get("source", "Unknown")
        title = doc.get("title", "")
        page = doc.get("page", "")

        heading = title or Path(source).stem

        if page:
            heading += f" — Page {page}"

        sections.append({
            "heading": heading,
            "source": source,
            "text": text
        })

    return sections


# Save all cleaned data as a TXT file.
def save_txt(sections):
    with open(TXT_FILE, "w", encoding="utf-8") as file:
        for section in sections:
            file.write(f"{section['heading']}\n")
            file.write(f"Source: {section['source']}\n\n")
            file.write(f"{section['text']}\n")
            file.write("\n" + "=" * 80 + "\n\n")


# Save the same cleaned data as a readable PDF.
def save_pdf(sections):
    doc = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    for section in sections:
        story.append(
            Paragraph(
                escape(section["heading"]),
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                escape(f"Source: {section['source']}"),
                styles["Normal"]
            )
        )

        story.append(Spacer(1, 8))

        for paragraph_text in section["text"].split("\n"):
            paragraph_text = paragraph_text.strip()

            if paragraph_text:
                # Escape HTML/XML characters so scraped text is treated as plain text.
                safe_text = escape(paragraph_text)

                story.append(
                    Paragraph(
                        safe_text,
                        styles["BodyText"]
                    )
                )

                story.append(Spacer(1, 5))

        story.append(Spacer(1, 12))

    doc.build(story)


# Run the complete export process.
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    sections = build_sections(documents)

    save_txt(sections)
    save_pdf(sections)

    print(f"Documents processed: {len(documents)}")
    print(f"Clean sections created: {len(sections)}")
    print(f"TXT created: {TXT_FILE}")
    print(f"PDF created: {PDF_FILE}")


if __name__ == "__main__":
    main()