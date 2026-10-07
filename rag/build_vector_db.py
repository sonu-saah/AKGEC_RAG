from pathlib import Path
import json
import chromadb
from sentence_transformers import SentenceTransformer

# Read the filtered chunks created by the chunking step.
INPUT_FILE = Path("data/rag_chunks.json")

# Store the ChromaDB database in this directory.
DB_DIR = "data/chroma_db"

# Use a lightweight local embedding model.
MODEL_NAME = "all-MiniLM-L6-v2"


# Build the vector database from the filtered chunks.
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    print("Total chunks:", len(chunks))
    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    # Create a persistent local ChromaDB client.
    client = chromadb.PersistentClient(path=DB_DIR)

    # Create the collection for AKGEC documents.
    collection = client.get_or_create_collection(
        name="akgec_documents"
    )

    texts = [chunk["text"] for chunk in chunks]

    print("Creating embeddings...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    ).tolist()

    # Store embeddings with source information for retrieval and citations.
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


# Run the vector database creation process.
if __name__ == "__main__":
    main()