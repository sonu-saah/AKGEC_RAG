

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



def answer_question(question):
    """Execute the RAG pipeline and measure performance."""

    import time

    total_start = time.perf_counter()

    # 1. Hybrid retrieval
    start = time.perf_counter()

    (
        vector_results,
        keyword_results,
        original_query,
        normalized_query,
    ) = search(question)

    retrieval_time = time.perf_counter() - start

    # 2. Combine and rerank
    start = time.perf_counter()

    results = combine_results(
        vector_results,
        keyword_results
    )

    results = rerank(question, results)

    rerank_time = time.perf_counter() - start

    # 3. Build context
    context = build_context(results)

    # 4. Gemini answer generation
    start = time.perf_counter()

    answer = generate_answer(question, context)

    llm_time = time.perf_counter() - start

    # 5. Verification and citations
    start = time.perf_counter()

    verification = verify_answer(answer, context)
    citations = build_citations(results)

    verification_time = time.perf_counter() - start

    total_time = time.perf_counter() - total_start

    # Display output
    print("\nORIGINAL QUESTION")
    print(original_query)

    print("\nNORMALIZED QUERY")
    print(normalized_query)

    print("\nFINAL ANSWER")
    print(answer)

    print_citations(citations)

    print("\nVERIFICATION")
    print(verification)

    # Performance report
    print("\n===== PERFORMANCE REPORT =====")
    print(f"Retrieval Time: {retrieval_time:.3f} sec")
    print(f"Reranking Time: {rerank_time:.3f} sec")
    print(f"Gemini Time: {llm_time:.3f} sec")
    print(f"Verification Time: {verification_time:.3f} sec")
    print(f"Total Response Time: {total_time:.3f} sec")

    print(f"Vector Results: {len(vector_results)}")
    print(f"BM25 Results: {len(keyword_results)}")
    print(f"Final Retrieved Chunks: {len(results)}")

    if not verification["verified"]:
        print(
            "\nWARNING: Numeric claims could not be "
            "fully verified against retrieved context."
        )



def main():
    """Run the chatbot continuously until the user exits."""

    print("\n===== AKGEC RAG CHATBOT =====")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        question = input("\nAsk your AKGEC question: ").strip()

        if question.lower() in ("exit", "quit"):
            print("\nChatbot stopped. Goodbye!")
            break

        if not question:
            print("Please enter a valid question.")
            continue

        try:
            answer_question(question)

        except Exception as error:
            print(f"\nERROR: {error}")
            print("Please try another question.")


# Run main() only when this file is executed directly
if __name__ == "__main__":
    main()
