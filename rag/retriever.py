import json
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

# Existing ChromaDB and embedding model settings.
DB_DIR = "data/chroma_db"
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_FILE = "data/rag_chunks.json"


# Add extra score for terms that strongly match the question intent.
def apply_keyword_boost(query, chunk_text, score):
    query = query.lower()
    text = chunk_text.lower()

    # Seat-related questions should prefer sanctioned intake information.
    if any(word in query for word in ["seat", "seats", "intake", "capacity"]):
        if "sanctioned intake" in text:
            score += 10
        if "courses offered" in text:
            score += 5

    # Fee-related questions should prefer fee information.
    if "fee" in query and "fee" in text:
        score += 5

    # Placement-related questions should prefer placement information.
    if "placement" in query and "placement" in text:
        score += 5

    return score


# Search using both vector search and BM25 keyword search.
def search(query, top_k=5):
    # Load chunks used by BM25.
    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    # Load the embedding model and ChromaDB.
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection("akgec_documents")

    # Convert the question into a vector.
    query_embedding = model.encode(query).tolist()

    # Retrieve semantically similar chunks.
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Prepare chunks for BM25.
    tokenized_chunks = [
        chunk.get("text", "").lower().split()
        for chunk in chunks
    ]

    # Create the BM25 keyword search index.
    bm25 = BM25Okapi(tokenized_chunks)

    # Search using the user's keywords.
    query_tokens = query.lower().split()
    bm25_scores = bm25.get_scores(query_tokens)

    keyword_results = []

    # Apply question-specific boosting to BM25 results.
    for score, chunk in zip(bm25_scores, chunks):
        text = chunk.get("text", "")

        final_score = apply_keyword_boost(
            query,
            text,
            float(score)
        )

        if final_score > 0:
            keyword_results.append((final_score, chunk))

    # Sort BM25 results by score.
    keyword_results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # Keep only the best keyword results.
    keyword_results = keyword_results[:top_k]

    return vector_results, keyword_results


# Combine vector and keyword results into one hybrid list.
def combine_results(vector_results, keyword_results, top_k=5):
    combined = {}

    # Add vector search results.
    documents = vector_results["documents"][0]
    metadatas = vector_results["metadatas"][0]
    distances = vector_results["distances"][0]

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        source = metadata.get("source", "")

        # Smaller distance means better vector similarity.
        vector_score = 1 / (1 + distance)

        combined[source] = {
            "text": document,
            "source": source,
            "score": vector_score
        }

    # Add or update results from BM25.
    for score, chunk in keyword_results:
        source = chunk.get("source", "")

        # Normalize BM25 score.
        keyword_score = score / (score + 10)

        if source in combined:
            # Combine vector and keyword scores.
            combined[source]["score"] += keyword_score
        else:
            combined[source] = {
                "text": chunk.get("text", ""),
                "source": source,
                "score": keyword_score
            }

    # Convert dictionary to list.
    final_results = list(combined.values())

    # Sort by combined hybrid score.
    final_results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return final_results[:top_k]


# Rerank hybrid results using the actual question intent.
def rerank(query, results):
    query = query.lower()

    for result in results:
        text = result["text"].lower()

        # Start with the hybrid retrieval score.
        score = result["score"]

        # Give extra weight to official course/intake information.
        if any(
            word in query
            for word in ["seat", "seats", "intake", "capacity"]
        ):
            if "sanctioned intake" in text:
                score += 0.5

            if "courses offered" in text:
                score += 0.3

        # Give extra weight to the exact course name.
        if "computer science and engineering" in query:
            if "computer science and engineering" in text:
                score += 0.5

        result["rerank_score"] = score

    # Sort according to the new reranking score.
    results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return results


# Test the complete retrieval and reranking pipeline.
def main():
    query = input("Enter your question: ").strip()

    # Step 1: Get vector and BM25 results.
    vector_results, keyword_results = search(query)

    # Step 2: Combine both retrieval methods.
    final_results = combine_results(
        vector_results,
        keyword_results
    )

    # Step 3: Rerank the combined results.
    final_results = rerank(
        query,
        final_results
    )

    print("\nRERANKED HYBRID RETRIEVAL RESULTS")

    for index, result in enumerate(
        final_results,
        start=1
    ):
        print(f"\n--- Result {index} ---")
        print("Rerank Score:", round(
            result["rerank_score"],
            4
        ))
        print("Source:", result["source"])
        print("Text:", result["text"][:700])


# Run the complete retrieval pipeline.
if __name__ == "__main__":
    main()