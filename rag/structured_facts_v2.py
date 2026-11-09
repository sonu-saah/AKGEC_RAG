import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "akgec_master_v13.json"

STOPWORDS = {
    "what", "which", "where", "when", "who", "how",
    "is", "are", "was", "were", "the", "a", "an",
    "of", "for", "in", "at", "to", "and", "about",
    "does", "do", "can", "you", "me", "tell",
    "please"
}

INTENT_TERMS = {
    "located": {"address", "location", "ghaziabad"},
    "location": {"address", "institution"},
    "address": {"institution", "address"},
    "established": {"establishment", "year"},
    "founded": {"establishment", "year"},
    "full": {"name", "institution"},
    "form": {"name", "institution"},
    "stand": {"name", "program", "course"},
    "stands": {"name", "program", "course"}
}


# Convert text into searchable tokens.
def tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


# Expand query with generic intent-related vocabulary.
def expand_query(question):
    terms = tokenize(question)
    expanded = list(terms)

    for term in terms:
        expanded.extend(sorted(INTENT_TERMS.get(term, set())))

    return expanded


# Extract original table rows without modifying values.
def load_facts():
    master = json.loads(MASTER.read_text(encoding="utf-8-sig"))
    facts = []

    for section in master:
        for block_index, block in enumerate(section.get("blocks", [])):
            if block.get("type") != "table":
                continue

            rows = block.get("rows", [])

            for row_index, row in enumerate(rows):
                if not isinstance(row, list):
                    continue

                cells = [str(cell).strip() for cell in row]

                if not any(cells):
                    continue

                facts.append({
                    "section": section.get("title", ""),
                    "source_url": section.get("source_url", ""),
                    "source_page": block.get("source_page"),
                    "block_index": block_index,
                    "row_index": row_index,
                    "text": " | ".join(cell for cell in cells if cell),
                    "cells": cells
                })

    return facts


# Rank original table rows using keyword retrieval.
def search_facts(question, facts, bm25, top_k=5):
    query = expand_query(question)
    scores = bm25.get_scores(query)

    important = set(tokenize(question)) - STOPWORDS

    ranked = []

    for index, fact in enumerate(facts):
        text_terms = set(tokenize(fact["text"]))
        section_terms = set(tokenize(fact["section"]))

        coverage = (
            len(important & text_terms) / len(important)
            if important else 0
        )

        section_coverage = (
            len(important & section_terms) / len(important)
            if important else 0
        )

        score = (
            float(scores[index])
            + 3 * coverage
            + 2 * section_coverage
        )

        ranked.append((score, fact))

    ranked.sort(key=lambda item: item[0], reverse=True)

    return ranked[:top_k]


# Run a read-only structured fact retrieval test.
def main():
    facts = load_facts()

    documents = [
        tokenize(fact["section"] + " " + fact["text"])
        for fact in facts
    ]

    bm25 = BM25Okapi(documents)

    questions = [
        "What is the full form of AKGEC?",
        "Where is AKGEC located?",
        "What does CSIT stand for?",
        "When was AKGEC established?",
        "What is the NBA accreditation status of Information Technology?",
        "What is the B.Tech first year fee?"
    ]

    print("ORIGINAL TABLE ROWS:", len(facts))

    for question in questions:
        print("\n" + "=" * 65)
        print("QUESTION:", question)

        for rank, (score, fact) in enumerate(
            search_facts(question, facts, bm25), 1
        ):
            print(
                f"\nRANK: {rank}",
                "\nSCORE:", round(score, 3),
                "\nSECTION:", fact["section"],
                "\nTEXT:", fact["text"][:350],
                "\nSOURCE:", fact["source_url"]
            )

    print("\nSTATUS: STRUCTURED FACT RETRIEVAL TEST COMPLETE")


if __name__ == "__main__":
    main()
