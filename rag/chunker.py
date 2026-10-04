from pathlib import Path
import json

# Prepared RAG documents ko input ke roop mein use karta hai.
INPUT_FILE = Path("data/rag_documents.json")

# Chunked documents ko yahan save karta hai.
OUTPUT_FILE = Path("data/rag_chunks.json")

# Text ko fixed-size chunks mein divide karta hai.
def create_chunks(text, chunk_size=1000, overlap=150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

# Saare documents ko chunks mein convert karta hai.
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    chunks = []

    for document_index, document in enumerate(documents):
        text_chunks = create_chunks(document["text"])

        for chunk_index, text in enumerate(text_chunks):
            chunks.append({
                "chunk_id": f"{document_index}_{chunk_index}",
                "text": text,
                "source": document.get("source", ""),
                "page": document.get("page"),
                "type": document.get("type", "")
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("CHUNKING COMPLETED")
    print("Documents:", len(documents))
    print("Chunks:", len(chunks))
    print("Output:", OUTPUT_FILE)

# Program ko directly run karta hai.
if __name__ == "__main__":
    main()