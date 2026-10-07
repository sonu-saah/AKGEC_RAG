import json
from pathlib import Path

INPUT_FILE = Path("data/rag_documents.json")
OUTPUT_FILE = Path("data/relevant_documents.json")

# Documents useful for the main AKGEC chatbot knowledge base.
KEEP_KEYWORDS = [
    "admission",
    "course",
    "branch",
    "fee",
    "hostel",
    "placement",
    "department",
    "facility",
    "facilities",
    "campus",
    "scholarship",
    "training",
    "internship",
    "notice",
    "announcement",
    "contact",
    "about",
    "vision",
    "mission",
    "mandatory disclosure",
    "nirf",
    "aicte approval",
    "placement brochure",
    "admission brochure",
    "fee-fixation",
]

# Documents that are mainly magazines, newsletters, old records or unrelated files.
EXCLUDE_KEYWORDS = [
    "magazine",
    "newsletter",
    "session_",
    "year-",
    "year_",
    "user-manual",
    "syllabus",
    "non-credit",
    "hsmc",
    "engineering-science",
    "manual",
]


# Decide whether a document belongs to the chatbot knowledge base.
def is_relevant(document):
    source = str(document.get("source", "")).lower()
    title = str(document.get("title", "")).lower()

    name = f"{source} {title}"

    if any(keyword in name for keyword in EXCLUDE_KEYWORDS):
        return False

    return any(keyword in name for keyword in KEEP_KEYWORDS)


# Filter the original documents without modifying the original file.
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    relevant_documents = [
        document for document in documents
        if is_relevant(document)
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(relevant_documents, file, ensure_ascii=False, indent=2)

    print(f"Original documents: {len(documents)}")
    print(f"Relevant documents: {len(relevant_documents)}")
    print(f"Filtered documents: {len(documents) - len(relevant_documents)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()