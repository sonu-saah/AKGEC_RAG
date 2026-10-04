from pathlib import Path
import json

# HTML pages aur extracted PDF JSON files ke folders define karta hai.
PAGE_DIR = Path("data/pages")
PDF_DIR = Path("data/pdf_data")
OUTPUT_FILE = Path("data/rag_documents.json")

# HTML page JSON files ko common document format mein convert karta hai.
def load_pages():
    documents = []

    for file in PAGE_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            text = data.get("text", "").strip()

            if text:
                documents.append({
                    "text": text,
                    "source": data.get("url", file.name),
                    "title": data.get("title", ""),
                    "type": "webpage"
                })

        except Exception as error:
            print("Page error:", file.name, error)

    return documents

# PDF page JSON files ko common document format mein convert karta hai.
def load_pdfs():
    documents = []

    for file in PDF_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for page in data.get("pages", []):
                text = page.get("text", "").strip()

                if text:
                    documents.append({
                        "text": text,
                        "source": data.get("source_file", file.name),
                        "page": page.get("page_number"),
                        "type": "pdf"
                    })

        except Exception as error:
            print("PDF error:", file.name, error)

    return documents

# Webpage aur PDF documents ko ek common JSON dataset mein combine karta hai.
def main():
    documents = load_pages() + load_pdfs()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            documents,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("RAG DATA PREPARATION COMPLETED")
    print("Total documents:", len(documents))
    print("Output:", OUTPUT_FILE)

# Program ko directly run karta hai.
if __name__ == "__main__":
    main()