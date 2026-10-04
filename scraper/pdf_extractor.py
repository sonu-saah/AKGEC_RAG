from pathlib import Path
import json
import fitz
import pytesseract
from PIL import Image

# Input PDF folder aur output folder define karta hai.
PDF_DIR = Path("data/resources")
OUTPUT_DIR = Path("data/pdf_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tesseract OCR engine ka Windows path set karta hai.
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Normal PDF text bahut kam ho to OCR use karega.
OCR_THRESHOLD = 100

# PDF page ko image mein convert karke OCR karta hai.
def extract_with_ocr(page):
    pixmap = page.get_pixmap(dpi=300)
    image = Image.frombytes(
        "RGB",
        [pixmap.width, pixmap.height],
        pixmap.samples
    )

    return pytesseract.image_to_string(
        image,
        lang="eng+hin"
    ).strip()

# Ek PDF ke har page se text extract karta hai.
def extract_pdf(pdf_path):
    document = fitz.open(pdf_path)
    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text").strip()

        if len(text) >= OCR_THRESHOLD:
            method = "pdf_text"
        else:
            text = extract_with_ocr(page)
            method = "ocr"

        pages.append({
            "page_number": page_number,
            "method": method,
            "text": text,
            "character_count": len(text)
        })

        print(
            f"  Page {page_number}/{len(document)} "
            f"-> {method} -> {len(text)} chars"
        )

    document.close()

    return pages

# PDF extraction result ko JSON file mein save karta hai.
def save_result(pdf_path, pages):
    output_file = OUTPUT_DIR / f"{pdf_path.stem}.json"

    result = {
        "source_file": pdf_path.name,
        "source_path": str(pdf_path),
        "total_pages": len(pages),
        "pages": pages
    }

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2
        )

# Saare downloaded PDF files ko process karta hai.
def main():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    print("Total PDF files:", len(pdf_files))

    successful = 0
    failed = 0

    for index, pdf_path in enumerate(pdf_files, start=1):
        print(f"\n[{index}/{len(pdf_files)}] {pdf_path.name}")

        try:
            pages = extract_pdf(pdf_path)
            save_result(pdf_path, pages)
            successful += 1

        except Exception as error:
            failed += 1
            print("Extraction failed:", error)

    print("\nPDF EXTRACTION COMPLETED")
    print("Successful:", successful)
    print("Failed:", failed)
    print("Output folder:", OUTPUT_DIR)

# Program ko directly run karta hai.
if __name__ == "__main__":
    main()