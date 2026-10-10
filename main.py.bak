from rag.retriever import search, combine_results, rerank
from llm.gemini import generate_answer
from verifier.answer_verifier import verify_answer


# Map important PDF files to their official AKGEC webpage.
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


# Build the context that will be sent to Gemini.
def build_context(results):
    context_parts = []

    for index, result in enumerate(results, start=1):
        source = result.get("source", "")
        page = result.get("page")
        source_type = result.get("type", "")

        official_url = PDF_SOURCE_URLS.get(
            source,
            source
        )

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


# Build the strongest available citation without duplicates.
def build_citations(results):
    citations = []
    seen_urls = set()

    # Prefer a relevant PDF source.
    for result in results:
        source = result.get("source", "")
        page = result.get("page")
        source_type = result.get("type", "")

        # Skip OCR JSON files.
        if source.endswith("_ocr.json"):
            continue

        if source_type != "pdf":
            continue

        official_url = PDF_SOURCE_URLS.get(
            source,
            source
        )

        # Do not use local PDF filename as an official URL.
        if not official_url.startswith("http"):
            continue

        if official_url in seen_urls:
            continue

        seen_urls.add(official_url)

        citations.append({
            "source": source,
            "page": page,
            "type": source_type,
            "url": official_url
        })

        break

    # If no mapped PDF is available, use the official AKGEC webpage.
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
                "url": source
            })

            break

    return citations


# Print source file, page and official URL.
def print_citations(citations):
    print("\nSOURCES / CITATIONS")

    if not citations:
        print("No official citation found.")

        return

    for index, citation in enumerate(
        citations,
        start=1
    ):
        print(f"\n[{index}]")

        print(
            "Source:",
            citation["source"]
        )

        if citation["page"] is not None:
            print(
                "Page:",
                citation["page"]
            )

        print(
            "Type:",
            citation["type"]
        )

        print(
            "Official URL:",
            citation["url"]
        )


# Run the complete AKGEC RAG pipeline.
def main():
    question = input(
        "Ask your AKGEC question: "
    ).strip()

    # Step 1: Retrieve relevant documents.
    (
        vector_results,
        keyword_results,
        original_query,
        normalized_query
    ) = search(question)

    # Step 2: Combine vector and keyword results.
    results = combine_results(
        vector_results,
        keyword_results
    )

    # Step 3: Rerank the retrieved results.
    results = rerank(
        question,
        results
    )

    # Step 4: Build context for Gemini.
    context = build_context(results)

    # Step 5: Generate the answer.
    answer = generate_answer(
        question,
        context
    )

    # 🔴 NIC Q&A IMPORTANT
    # Verify the generated answer against retrieved evidence.
    verification = verify_answer(
        answer,
        context
    )

    # Step 6: Build citations.
    citations = build_citations(
        results
    )

    print("\nORIGINAL QUESTION")
    print(original_query)

    print("\nNORMALIZED QUERY")
    print(normalized_query)

    print("\nFINAL ANSWER")
    print(answer)

    # Step 7: Display structured citations.
    print_citations(
        citations
    )

    print("\nVERIFICATION")
    print(verification)

    # Warn when the answer is not fully supported.
    if not verification["verified"]:
        print(
            "\nWARNING: Answer could not be fully verified "
            "from the retrieved AKGEC data."
        )


# Start the AKGEC RAG application.
if __name__ == "__main__":
    main()