import json

# OCR output JSON file load karo.
# Is file mein har PDF page ka extracted text stored hai.
with open(
    "data/pdf_data/Fee-Fixation-Letter_ocr.json",
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)


# ============================================================
# OCR QUALITY REPORT
# ============================================================

print("=" * 70)
print("OCR QUALITY CHECK")
print("=" * 70)

for page in data["pages"]:

    page_number = page["page"]
    method = page["extraction_method"]
    text = page["text"]

    print(
        f"\nPage {page_number}"
        f" | Method: {method}"
        f" | Characters: {len(text)}"
    )

    # First 300 characters show karenge
    # taaki OCR output manually inspect kar sakein.
    print("Text:", text[:300])


print("\n" + "=" * 70)
print("QUALITY CHECK COMPLETED")
print("=" * 70)