from pathlib import Path
import json
import re
import shutil

INPUT_FILE = Path("data/fresh/structured/rag_ready_candidates.json")
OUTPUT_FILE = Path("data/fresh/structured/rag_chunks.json")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


# Split text near sentence or word boundaries.
def create_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            boundary = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
                text.rfind(" ", start, end)
            )

            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = max(start + 1, end - overlap)

    return chunks


# Convert verified candidates into chunks.
def main():
    documents = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    chunks = []

    for document_index, document in enumerate(documents):
        text_chunks = create_chunks(document.get("text", ""))

        for chunk_index, chunk_text in enumerate(text_chunks):
            chunks.append({
                "chunk_id": f"fresh_{document_index}_{chunk_index}",
                "text": chunk_text,
                "title": document.get("title", ""),
                "source_url": document.get("source_url", ""),
                "source_type": document.get("source_type", ""),
                "section": document.get("section", ""),
                "page_number": document.get("page_number"),
                "chunk_index": chunk_index
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("CHUNKING COMPLETED")
    print("Documents:", len(documents))
    print("Chunks:", len(chunks))
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
