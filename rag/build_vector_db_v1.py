import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# Configure the new dataset and separate vector database.
ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "akgec_rag_chunks_v1.json"
DB_DIR = ROOT / "data" / "chroma_db_v1"
COLLECTION = "akgec_documents_v1"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64

# Validate input chunks before generating embeddings.
def load_chunks():
    chunks = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    assert isinstance(chunks, list) and chunks, "Empty or invalid dataset"

    ids = [str(c["id"]) for c in chunks]
    assert len(ids) == len(set(ids)), "Duplicate chunk IDs"

    for chunk in chunks:
        assert chunk.get("text", "").strip(), "Empty chunk text"

    return chunks

# Generate embeddings and save them in ChromaDB.
def main():
    chunks = load_chunks()
    print("Chunks:", len(chunks))
    print("Loading embedding model...")

    model = SentenceTransformer(MODEL)
    client = chromadb.PersistentClient(path=str(DB_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        vectors = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()

        metadata = [
            {
                "section": str(c.get("section", "")),
                "title": str(c.get("title") or c.get("section", "")),
                "source_url": str(c.get("source_url", "")),
                "content_type": str(c.get("content_type", "")),
                "verification_status": str(
                    c.get("verification_status", "unknown")
                ),
                "chunk_index": int(c.get("chunk_index") or 0)
            }
            for c in batch
        ]

        collection.upsert(
            ids=[str(c["id"]) for c in batch],
            documents=texts,
            embeddings=vectors,
            metadatas=metadata
        )

        print(f"Stored: {min(start + BATCH_SIZE, len(chunks))}/{len(chunks)}")

    print("\n=== EMBEDDING RESULT ===")
    print("Collection:", COLLECTION)
    print("Vectors:", collection.count())
    print("Database:", DB_DIR)

    assert collection.count() == len(chunks), "Vector count mismatch"
    print("SUCCESS: All chunks stored")

if __name__ == "__main__":
    main()
