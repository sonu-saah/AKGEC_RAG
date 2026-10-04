import fitz
import pytesseract
from PIL import Image
from pathlib import Path
import json
import io


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

# Windows mein Tesseract executable ka exact location.
# Hum full path use kar rahe hain because Administrator
# PowerShell mein "tesseract" command PATH se recognize nahi ho rahi thi.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# INPUT PDF
# ============================================================

# Abhi OCR pipeline ko ek real AKGEC PDF par test karenge.
# Later isi logic ko automatic PDF pipeline mein integrate karenge.
PDF_PATH = Path("data/pdfs/Fee-Fixation-Letter.pdf")


# ============================================================
# OUTPUT JSON
# ============================================================

# OCR ke baad complete page-wise data yahan save hoga.
OUTPUT_PATH = Path("data/pdf_data/Fee-Fixation-Letter_ocr.json")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# OPEN PDF
# ============================================================

# PyMuPDF PDF ko read karega.
pdf = fitz.open(PDF_PATH)

print("=" * 60)
print("OCR PROCESS STARTED")
print("=" * 60)

print("PDF:", PDF_PATH)
print("Total pages:", len(pdf))


# ============================================================
# PROCESS EACH PAGE
# ============================================================

all_pages = []

for page_number, page in enumerate(pdf, start=1):

    print(f"\nProcessing Page {page_number}...")

    # --------------------------------------------------------
    # FIRST TRY NORMAL PDF TEXT EXTRACTION
    # --------------------------------------------------------

    # Agar PDF mein selectable text available hai,
    # to PyMuPDF directly text extract kar sakta hai.
    normal_text = page.get_text("text")

    # Extra spaces and line breaks clean karo.
    normal_text = " ".join(normal_text.split())

    # --------------------------------------------------------
    # DECIDE WHETHER OCR IS REQUIRED
    # --------------------------------------------------------

    # Agar extracted text bahut short hai,
    # to page scanned/image-based ho sakta hai.
    OCR_THRESHOLD = 100

    if len(normal_text) >= OCR_THRESHOLD:

        print(
            f"Normal text extraction successful "
            f"({len(normal_text)} characters)"
        )

        final_text = normal_text
        extraction_method = "pdf_text"

    else:

        print(
            f"Normal text insufficient "
            f"({len(normal_text)} characters)"
        )

        print("Running OCR...")

        # ----------------------------------------------------
        # CONVERT PDF PAGE INTO IMAGE
        # ----------------------------------------------------

        # 300 DPI ke approximately equivalent rendering.
        # Higher resolution generally OCR accuracy improve karta hai,
        # lekin processing aur memory cost bhi badhata hai.
        zoom = 300 / 72

        matrix = fitz.Matrix(zoom, zoom)

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        # ----------------------------------------------------
        # CONVERT IMAGE BYTES INTO PIL IMAGE
        # ----------------------------------------------------

        image = Image.open(
            io.BytesIO(pixmap.tobytes("png"))
        )

        # ----------------------------------------------------
        # RUN OCR
        # ----------------------------------------------------

        # eng = English
        # hin = Hindi
        #
        # "eng+hin" ka matlab Tesseract dono languages
        # ko recognize karne ki koshish karega.
        ocr_text = pytesseract.image_to_string(
            image,
            lang="eng+hin"
        )

        # OCR output clean karo.
        ocr_text = " ".join(ocr_text.split())

        final_text = ocr_text
        extraction_method = "ocr"

        print(
            "OCR extracted:",
            len(final_text),
            "characters"
        )

    # --------------------------------------------------------
    # SAVE PAGE DATA
    # --------------------------------------------------------

    all_pages.append({
        "page": page_number,
        "text": final_text,
        "extraction_method": extraction_method
    })


# ============================================================
# CLOSE PDF
# ============================================================

pdf.close()


# ============================================================
# SAVE FINAL JSON
# ============================================================

result = {
    "source_url": "https://www.akgec.ac.in/wp-content/uploads/2024/03/Fee-Fixation-Letter.pdf",
    "file_name": PDF_PATH.name,
    "total_pages": len(all_pages),
    "pages": all_pages
}


with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        result,
        file,
        ensure_ascii=False,
        indent=4
    )


# ============================================================
# FINAL REPORT
# ============================================================

ocr_pages = [
    page["page"]
    for page in all_pages
    if page["extraction_method"] == "ocr"
]

print("\n" + "=" * 60)
print("OCR PROCESS COMPLETED")
print("=" * 60)

print("Output:", OUTPUT_PATH)
print("Total pages:", len(all_pages))
print("Pages processed using OCR:", ocr_pages)
print("Number of OCR pages:", len(ocr_pages))
print("=" * 60)