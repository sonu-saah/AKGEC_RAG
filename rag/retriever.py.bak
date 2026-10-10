
import json
import re
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_FILE = BASE_DIR / "data" / "rag_chunks.json"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

COLLECTION_NAME = "akgec_documents"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_collection = None
_chunks = None
_bm25 = None
_chunk_texts = None


def normalize_query(query):
    query = query.lower().strip()

    replacements = {
        "b.tech": "btech",
        "b-tech": "btech",
        "b tech": "btech",
        "how much": "fee",
        "fees": "fee",
        "kitni hai": "fee",
        "kitna hai": "fee",
        "kitne hai": "fee",
    }

    for old, new in replacements.items():
        query = query.replace(old, new)

    return re.sub(r"\s+", " ", query).strip()


def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", str(text).lower())


def get_text(item):
    return str(
        item.get("text")
        or item.get("content")
        or item.get("page_content")
        or ""
    )


def get_source(item):
    return (
        item.get("source")
        or item.get("source_url")
        or item.get("url")
        or item.get("filename")
        or ""
    )


def get_metadata(item):
    metadata = item.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "source": str(
            metadata.get("source")
            or item.get("source")
            or item.get("source_url")
            or item.get("url")
            or item.get("filename")
            or ""
        ),
        "page": metadata.get("page", item.get("page")),
        "type": str(
            metadata.get("type")
            or item.get("type")
            or "webpage"
        ),
    }


def load_resources():
    global _model, _collection, _chunks, _bm25, _chunk_texts

    if _collection is not None:
        return

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {CHUNKS_FILE}"
        )

    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        _chunks = json.load(file)

    if isinstance(_chunks, dict):
        _chunks = _chunks.get("chunks", [])

    if not _chunks:
        raise ValueError("rag_chunks.json contains no chunks.")

    _chunk_texts = [get_text(chunk) for chunk in _chunks]

    if not any(text.strip() for text in _chunk_texts):
        raise ValueError("No readable text found in the chunks.")

    _model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    _collection = client.get_collection(
        name=COLLECTION_NAME
    )

    _bm25 = BM25Okapi([
        tokenize(text) or ["empty"]
        for text in _chunk_texts
    ])


def make_result(text, metadata, score):
    return {
        "text": text,
        "source": metadata.get("source", ""),
        "page": metadata.get("page"),
        "type": metadata.get("type", "webpage"),
        "score": float(score),
    }


def apply_keyword_boost(query, result):
    text = result["text"].lower()
    query = normalize_query(query)

    score = result.get("score", 0.0)

    if "placement" in query:
        if "steps to follow" in text and "our placement" not in text:
            return -1000.0

        placement_terms = [
            "our placement",
            "placement cell",
            "placement statistics",
            "placement & higher studies",
            "placement and higher studies",
            "students placed",
            "highest package",
            "average package",
            "companies visited",
            "placement record",
        ]

        if "our placement" in text:
            score += 10.0

        if "placement cell" in text:
            score += 5.0

        if any(term in text for term in placement_terms):
            score += 3.0

        if (
            "career planning & placement (one time)" in text
            and "our placement" not in text
        ):
            score -= 5.0

    if any(term in query for term in ["fee", "fees"]):
        if "fee" in text or "tuition" in text:
            score += 2.0

    if any(term in query for term in ["seat", "intake"]):
        if "sanctioned intake" in text or "courses offered" in text:
            score += 3.0

    return score


def search(query, top_k=5):
    load_resources()

    original_query = query
    normalized_query = normalize_query(query)

    query_embedding = _model.encode(
        normalized_query
    ).tolist()

    vector_data = _collection.query(
        query_embeddings=[query_embedding],
        n_results=min(20, _collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    vector_results = []

    documents = vector_data.get("documents", [[]])[0]
    metadatas = vector_data.get("metadatas", [[]])[0]
    distances = vector_data.get("distances", [[]])[0]

    for text, metadata, distance in zip(
        documents, metadatas, distances
    ):
        metadata = metadata or {}
        result = make_result(
            text,
            metadata,
            1.0 / (1.0 + max(float(distance), 0.0)),
        )
        result["score"] = apply_keyword_boost(query, result)
        vector_results.append(result)

    keyword_scores = _bm25.get_scores(
        tokenize(normalized_query)
    )

    best_score = max(keyword_scores) if len(keyword_scores) else 0.0
    keyword_results = []

    ranked_indices = sorted(
        range(len(keyword_scores)),
        key=lambda index: keyword_scores[index],
        reverse=True,
    )[:20]

    for index in ranked_indices:
        chunk = _chunks[index]
        text = _chunk_texts[index]

        if not text.strip():
            continue

        metadata = get_metadata(chunk)

        raw_score = float(keyword_scores[index])
        normalized_score = (
            raw_score / best_score if best_score > 0 else 0.0
        )

        result = make_result(
            text,
            metadata,
            normalized_score,
        )
        result["score"] = apply_keyword_boost(query, result)
        keyword_results.append(result)

    return (
        vector_results,
        keyword_results,
        original_query,
        normalized_query,
    )


def combine_results(vector_results, keyword_results, top_k=8):
    combined = {}

    for result in vector_results + keyword_results:
        key = (
            result.get("source", ""),
            result.get("page"),
            result.get("text", ""),
        )

        if key not in combined:
            combined[key] = result.copy()
        elif result.get("score", 0.0) > combined[key].get("score", 0.0):
            combined[key]["score"] = result["score"]

    return list(combined.values())


def rerank(query, results):
    normalized_query = normalize_query(query)

    for result in results:
        text = result.get("text", "").lower()
        score = result.get("score", 0.0)

        # Strongly demote admission registration instructions.
        if (
            "placement" in normalized_query
            and "steps to follow" in text
            and "our placement" not in text
        ):
            result["rerank_score"] = -1000.0
            continue

        if "placement" in normalized_query:
            if "our placement" in text:
                score += 10.0

            if "placement cell" in text:
                score += 5.0

            terms = [
                "placement statistics",
                "placement & higher studies",
                "placement and higher studies",
                "students placed",
                "highest package",
                "average package",
                "companies visited",
                "placement record",
            ]

            if any(term in text for term in terms):
                score += 3.0

        result["rerank_score"] = score

    results.sort(
        key=lambda item: item.get("rerank_score", -1000.0),
        reverse=True,
    )

    return results[:8]


if __name__ == "__main__":
    try:
        query = input("Enter your question: ").strip()

        if not query:
            print("Please enter a question.")
            raise SystemExit(0)

        (
            vector_results,
            keyword_results,
            original_query,
            normalized_query,
        ) = search(query)

        results = combine_results(
            vector_results,
            keyword_results,
        )

        results = rerank(query, results)

        print("\nORIGINAL QUERY")
        print(original_query)

        print("\nNORMALIZED QUERY")
        print(normalized_query)

        print("\nRERANKED HYBRID RETRIEVAL RESULTS")

        for index, result in enumerate(results, start=1):
            print(f"\n--- Result {index} ---")
            print(
                "Rerank Score:",
                round(result.get("rerank_score", 0.0), 4),
            )
            print("Source:", result.get("source", ""))
            print("Page:", result.get("page"))
            print("Type:", result.get("type", "webpage"))
            print("Text:", result.get("text", "")[:1200])

    except Exception as error:
        print(f"\nRetriever error: {error}")
