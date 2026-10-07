import chromadb
import json
from sentence_transformers import SentenceTransformer

# Existing ChromaDB and embedding model settings.
DB_DIR = "data/chroma_db"
MODEL_NAME = "all-MiniLM-L6-v2"

# Load the chunked data for keyword-based retrieval.
CHUNKS_FILE = "data/rag_chunks.json"

# Common words that do not help keyword search.
STOP_WORDS = {
    "how", "many", "what", "is", "are", "the",
    "in", "of", "to", "for", "a", "an", "and",
    "on", "at", "with", "can", "do"
}


# Retrieve relevant chunks using vector and keyword search.
def search(query, top_k=5):
    # Load chunks for keyword-based retrieval.
    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection("akgec_documents")

    # Convert the user query into an embedding.
    query_embedding = model.encode(query).tolist()

    # Retrieve results using vector similarity.
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Remove common words from the query.
    query_words = set(query.lower().split()) - STOP_WORDS

    # Create the cleaned query phrase.
    query_phrase = " ".join(query_words)

    keyword_results = []

    # Calculate keyword and phrase matches for every chunk.
    for chunk in chunks:
        text = chunk.get("text", "").lower()
        score = 0

        # Give a higher score when the complete phrase appears.
        if query_phrase in text:
            score += 10

        # Add points for individual important keywords.
        score += sum(word in text for word in query_words)

        if score > 0:
            keyword_results.append((score, chunk))

    # Keep the chunks with the highest keyword score.
    keyword_results.sort(key=lambda item: item[0], reverse=True)
    keyword_results = keyword_results[:top_k]

    return vector_results, keyword_results


# Display vector and keyword retrieval results.
def main():
    query = input("Enter your question: ").strip()

    vector_results, keyword_results = search(query)

    print("\nVECTOR SEARCH RESULTS")

    documents = vector_results["documents"][0]
    metadatas = vector_results["metadatas"][0]
    distances = vector_results["distances"][0]

    for index, (document, metadata, distance) in enumerate(
        zip(documents, metadatas, distances),
        start=1
    ):
        print(f"\n--- Vector Result {index} ---")
        print("Distance:", round(distance, 4))
        print("Source:", metadata.get("source", ""))
        print("Text:", document[:500])

    print("\nKEYWORD SEARCH RESULTS")

    for index, (score, chunk) in enumerate(keyword_results, start=1):
        print(f"\n--- Keyword Result {index} ---")
        print("Keyword Score:", score)
        print("Source:", chunk.get("source", ""))
        print("Text:", chunk.get("text", "")[:500])


# Run the retrieval test.
if __name__ == "__main__":
    main()