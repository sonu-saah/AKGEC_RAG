import chromadb
from sentence_transformers import SentenceTransformer

# Existing ChromaDB aur embedding model ko load karta hai.
DB_DIR = "data/chroma_db"
MODEL_NAME = "all-MiniLM-L6-v2"

# User query ke liye relevant chunks retrieve karta hai.
def search(query, top_k=5):
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection("akgec_documents")

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results

# Retrieved chunks ko readable format mein display karta hai.
def main():
    query = input("Enter your question: ").strip()

    results = search(query)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print("\nRETRIEVED RESULTS")

    for index, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances),
        start=1
    ):
        print(f"\n--- Result {index} ---")
        print("Distance:", round(distance, 4))
        print("Source:", metadata.get("source", ""))
        print("Page:", metadata.get("page", ""))
        print("Type:", metadata.get("type", ""))
        print("Text:", document[:1000])

# Program ko directly run karta hai.
if __name__ == "__main__":
    main()