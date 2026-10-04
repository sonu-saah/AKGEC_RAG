from pathlib import Path
import json
import chromadb
from sentence_transformers import SentenceTransformer

# Chunked RAG data ko input ke roop mein use karta hai.
INPUT_FILE = Path("data/rag_chunks.json")

# ChromaDB ka local storage folder define karta hai.
DB_DIR = "data/chroma_db"

# Local embedding model load karta hai.
MODEL_NAME = "all-MiniLM-L6-v2"

# Chunks ko embeddings ke saath ChromaDB mein store karta hai.
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    print("Total chunks:", len(chunks))
    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    # Local persistent ChromaDB database create/open karta hai.
    client = chromadb.PersistentClient(path=DB_DIR)

    collection = client.get_or_create_collection(
        name="akgec_documents"
    )

    texts = [chunk["text"] for chunk in chunks]

    print("Creating embeddings...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    ).tolist()

    # Chunks ko vectors aur source metadata ke saath database mein store karta hai.
    collection.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "source": chunk.get("source", ""),
                "page": str(chunk.get("page") or ""),
                "type": chunk.get("type", "")
            }
            for chunk in chunks
        ]
    )

    print("\nVECTOR DATABASE CREATED")
    print("Collection:", collection.name)
    print("Total vectors:", collection.count())
    print("Database:", DB_DIR)


# Program ko directly run karta hai.
if __name__ == "__main__":
    main()