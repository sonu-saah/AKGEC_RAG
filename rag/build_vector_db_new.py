from pathlib import Path
import json

import chromadb
from sentence_transformers import SentenceTransformer

# Input chunks from the fresh filtered dataset.
INPUT_FILE = Path("data/fresh/structured/rag_chunks.json")

# Keep the previous database untouched.
DB_DIR = "data/fresh/chroma_db"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "akgec_fresh_documents"
BATCH_SIZE = 64


# Build embeddings and store them in ChromaDB.
def main():
    chunks = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    print("Total chunks:", len(chunks))
    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    client = chromadb.PersistentClient(path=DB_DIR)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Creating embeddings and storing batches...")

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        texts = [item["text"] for item in batch]

        embeddings = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()

        metadatas = []

        for item in batch:
            metadatas.append({
                "title": item.get("title", ""),
                "source_url": item.get("source_url", ""),
                "source_type": item.get("source_type", ""),
                "section": item.get("section", ""),
                "page_number": item.get("page_number") or 0,
                "chunk_index": item.get("chunk_index", 0)
            })

        collection.upsert(
            ids=[item["chunk_id"] for item in batch],
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        print(
            f"Stored {min(start + BATCH_SIZE, len(chunks))}"
            f"/{len(chunks)} chunks"
        )

    print("\nVECTOR DATABASE CREATED")
    print("Collection:", collection.name)
    print("Total vectors:", collection.count())
    print("Database:", DB_DIR)


if __name__ == "__main__":
    main()
