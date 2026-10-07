import json
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("data/relevant_documents.json")


# Show the document types and common sources in the filtered dataset.
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    types = Counter(document.get("type", "unknown") for document in documents)

    sources = Counter(
        Path(document.get("source", "unknown")).name
        for document in documents
    )

    print(f"Total relevant documents: {len(documents)}")

    print("\nDocument types:")
    for doc_type, count in types.items():
        print(f"{doc_type}: {count}")

    print("\nTop 30 sources:")
    for source, count in sources.most_common(30):
        print(f"{count:4}  {source}")


if __name__ == "__main__":
    main()