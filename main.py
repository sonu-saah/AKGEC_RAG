
"""Main entry point for the AKGEC RAG chatbot."""

from rag.retriever import search, combine_results, rerank
from llm.gemini import generate_answer
from verifier.answer_verifier import verify_answer


# Map PDF filenames to their official AKGEC webpage URLs
PDF_SOURCE_URLS = {
    "B-Tech-Ist-Year-2026-27_0001.pdf":
        "https://www.akgec.ac.in/fee-structure-for-new-students2026-27",

    "BTech1Yr.pdf":
        "https://www.akgec.ac.in/fee-structure-for-new-students2026-27",

    "B-Tech-Ist-Year-FW-2026-27_0001.pdf":
        "https://www.akgec.ac.in/fee-structure-for-new-students2026-27",

    "HOSTEL-FEE-2026-27_0001-1.pdf":
        "https://www.akgec.ac.in/hostel/",
}


def build_context(results):
    """Prepare retrieved document content for Gemini answer generation."""
    context_parts = []

    for index, result in enumerate(results, start=1):
        source = result.get("source", "")
        page = result.get("page")
        source_type = result.get("type", "")

        official_url = PDF_SOURCE_URLS.get(source, source)

        context_parts.append(
            f"""
SOURCE {index}
SOURCE FILE: {source}
PAGE: {page}
TYPE: {source_type}
OFFICIAL URL: {official_url}

CONTENT:
{result["text"]}
"""
        )

    return "\n".join(context_parts)


def build_citations(results):
    """Select official source citations and avoid duplicate URLs."""
    citations = []
    seen_urls = set()

    # Prefer a PDF source linked to an official AKGEC webpage
    for result in results:
        source = result.get("source", "")
        page = result.get("page")
        source_type = result.get("type", "")

        if source.endswith("_ocr.json"):
            continue

        if source_type != "pdf":
            continue

        official_url = PDF_SOURCE_URLS.get(source, source)

        if not official_url.startswith("http"):
            continue

        if official_url in seen_urls:
            continue

        seen_urls.add(official_url)

        citations.append({
            "source": source,
            "page": page,
            "type": source_type,
            "url": official_url,
        })

        break

    # Use an official AKGEC webpage if no valid PDF citation exists
    if not citations:
        for result in results:
            source = result.get("source", "")
            source_type = result.get("type", "")

            if source_type != "webpage":
                continue

            if "akgec.ac.in" not in source:
                continue

            if source in seen_urls:
                continue

            seen_urls.add(source)

            citations.append({
                "source": source,
                "page": None,
                "type": source_type,
                "url": source,
            })

            break

    return citations


def print_citations(citations):
    """Display source filenames, PDF page numbers and official URLs."""
    print("\nSOURCES / CITATIONS")

    if not citations:
        print("No official citation found.")
        return

    for index, citation in enumerate(citations, start=1):
        print(f"\n[{index}]")
        print("Source:", citation["source"])

        if citation["page"] is not None:
            print("Page:", citation["page"])

        print("Type:", citation["type"])
        print("Official URL:", citation["url"])


def main():
    """Execute the complete AKGEC RAG question-answering pipeline."""

    # Accept a question from the terminal
    question = input("Ask your AKGEC question: ").strip()

    # Hybrid retrieval: Search using vector similarity and BM25
    (
        vector_results,
        keyword_results,
        original_query,
        normalized_query,
    ) = search(question)

    # Result fusion: Merge vector and keyword search results
    results = combine_results(vector_results, keyword_results)

    # Reranking: Prioritize the most relevant document chunks
    results = rerank(question, results)

    # Context building: Prepare retrieved evidence for Gemini
    context = build_context(results)

    # LLM inference: Generate an answer using Gemini API
    answer = generate_answer(question, context)

    # Answer verification: Check the answer against retrieved context
    verification = verify_answer(answer, context)

    # Source attribution: Collect official citation references
    citations = build_citations(results)

    # Display the original and normalized queries
    print("\nORIGINAL QUESTION")
    print(original_query)

    print("\nNORMALIZED QUERY")
    print(normalized_query)

    # Display the generated answer
    print("\nFINAL ANSWER")
    print(answer)

    # Display citations and verification result
    print_citations(citations)

    print("\nVERIFICATION")
    print(verification)

    if not verification["verified"]:
        print(
            "\nWARNING: Answer could not be fully verified "
            "from the retrieved AKGEC data."
        )


# Run main() only when this file is executed directly
if __name__ == "__main__":
    main()
