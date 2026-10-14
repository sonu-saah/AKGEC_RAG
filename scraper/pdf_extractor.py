# Extract text from AKGEC PDFs using PyMuPDF and OCR

import json
import re
import hashlib
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image


# Configuration
INPUT_REPORT = Path("data/fresh/download_report.json")
OUTPUT_DIR = Path("data/fresh/pdf_data")
EXTRACTION_REPORT = Path("data/fresh/pdf_extraction_report.json")

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR_DPI = 250
MIN_TEXT_LENGTH = 80

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# Clean text while preserving line breaks
def clean_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# Extract text from a normal PDF page
def extract_native_text(page):
    return clean_text(
        page.get_text("text", sort=True)
    )


# Extract text from a scanned PDF page
def extract_ocr_text(page):
    pix = page.get_pixmap(
        dpi=OCR_DPI,
        alpha=False
    )

    image = Image.frombytes(
        "RGB",
        (pix.width, pix.height),
        pix.samples
    )

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 3"
    )

    return clean_text(text)


# Extract tables from text-based PDF pages
def extract_native_tables(page):
    tables = []

    try:
        finder = page.find_tables()

        for table in finder.tables:
            rows = table.extract()

            cleaned_rows = []

            for row in rows:
                cleaned_row = [
                    clean_text(str(cell)) if cell is not None else ""
                    for cell in row
                ]

                if any(cleaned_row):
                    cleaned_rows.append(cleaned_row)

            if cleaned_rows:
                tables.append({
                    "rows": cleaned_rows
                })

    except Exception as error:
        print("Table detection warning:", error)

    return tables


# Create stable output filename
def make_output_filename(pdf_path):
    return f"{pdf_path.stem}.json"


# Process one PDF
def process_pdf(resource):
    pdf_path = Path(resource["local_path"])

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    document = pymupdf.open(pdf_path)

    pages = []

    try:
        for index, page in enumerate(document):
            native_text = extract_native_text(page)

            if len(native_text) >= MIN_TEXT_LENGTH:
                method = "native"
                text = native_text
                tables = extract_native_tables(page)

            else:
                method = "ocr"
                text = extract_ocr_text(page)
                tables = []

            pages.append({
                "page_number": index + 1,
                "method": method,
                "text": text,
                "character_count": len(text),
                "tables": tables,
                "needs_review": len(text) < MIN_TEXT_LENGTH
            })

            print(
                f"  Page {index + 1}: "
                f"{method} | {len(text)} characters | "
                f"{len(tables)} tables"
            )

    finally:
        document.close()

    result = {
        "title": resource.get("title", ""),
        "section": resource.get("section", ""),
        "source_url": resource.get("url", ""),
        "source_page": resource.get("source_page", ""),
        "local_file": str(pdf_path),
        "sha256": resource.get("sha256", ""),
        "total_pages": len(pages),
        "pages": pages
    }

    return result


# Main extraction
def main():
    if not INPUT_REPORT.exists():
        print("Download report not found:", INPUT_REPORT)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_REPORT, "r", encoding="utf-8") as file:
        report = json.load(file)

    resources = [
        item for item in report.get("results", [])
        if item.get("status") in {"downloaded", "existing"}
        and item.get("local_path")
    ]

    completed = []
    failed = []

    print("PDFs to process:", len(resources))

    for index, resource in enumerate(resources, start=1):
        print(
            f"\n[{index}/{len(resources)}] "
            f"{resource.get('title', '')}"
        )

        try:
            result = process_pdf(resource)

            output_file = OUTPUT_DIR / make_output_filename(
                Path(resource["local_path"])
            )

            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(
                    result,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

            completed.append({
                "title": result["title"],
                "section": result["section"],
                "output": str(output_file),
                "total_pages": result["total_pages"],
                "ocr_pages": sum(
                    p["method"] == "ocr" for p in result["pages"]
                ),
                "review_pages": sum(
                    p["needs_review"] for p in result["pages"]
                )
            })

            print("Saved:", output_file)

        except Exception as error:
            failed.append({
                "title": resource.get("title", ""),
                "url": resource.get("url", ""),
                "error": str(error)
            })

            print("Failed:", error)

    summary = {
        "processed": len(completed),
        "failed": len(failed),
        "completed": completed,
        "failures": failed
    }

    with open(EXTRACTION_REPORT, "w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 55)
    print("HYBRID PDF EXTRACTION COMPLETED")
    print("=" * 55)
    print("Processed:", len(completed))
    print("Failed:", len(failed))
    print("Report:", EXTRACTION_REPORT)


if __name__ == "__main__":
    main()