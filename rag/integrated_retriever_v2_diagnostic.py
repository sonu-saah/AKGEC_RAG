import json
import re
from pathlib import Path

import chromadb
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


# Tokenize text for keyword retrieval.
def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


# Load the merged V2 retrieval data.
class IntegratedRetrieverV2:
    def __init__(self):
        path = Path("data/akgec_rag_chunks_v2_merged.json")
        self.chunks = json.loads(path.read_text(encoding="utf-8-sig"))
        self.by_id = {str(c["id"]): c for c in self.chunks}

        self.tokens = [
            tokenize(c.get("text", "") + " " + c.get("title", ""))
            for c in self.chunks
        ]
        self.bm25 = BM25Okapi(self.tokens)

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.client = chromadb.PersistentClient(
            path="data/chroma_db_v2_fees"
        )
        self.collection = self.client.get_collection(
            "akgec_documents_v2_fees"
        )

        master = json.loads(
            Path("data/akgec_master_v13.json").read_text(
                encoding="utf-8-sig"
            )
        )
        self.facts = []

        for section in master:
            for block in section.get("blocks", []):
                if block.get("type") != "table":
                    continue

                for row in block.get("rows", []):
                    cells = [
                        str(cell).strip()
                        for cell in row
                        if str(cell).strip()
                    ]

                    if len(cells) < 2:
                        continue

                    self.facts.append({
                        "id": f"fact_v2_{len(self.facts)}",
                        "text": " | ".join(cells),
                        "section": section.get("title", ""),
                        "title": section.get("title", ""),
                        "source_url": section.get("source_url", ""),
                        "content_type": "structured_fact"
                    })

        self.fact_bm25 = BM25Okapi([
            tokenize(f["text"] + " " + f["section"])
            for f in self.facts
        ])

    # Expand only source-supported abbreviations and intents.
    def expand_query(self, question):
        query = question.lower()

        if re.search(r"\bcsit\b", query):
            query += " computer science and information technology"


        if any(word in query for word in ("located", "location", "address")):
            query += " institution address"

        if any(word in query for word in ("established", "founded")):
            query += " year of establishment"

        return query

    # Match structured fee records using question constraints.
    def fee_results(self, question):
        q = question.lower()
        results = []

        years = re.findall(
            r"\b(?:1st|2nd|3rd|4th|first|second|third|fourth)\s*year\b",
            q
        )
        year_map = {
            "first year": "1st year",
            "second year": "2nd year",
            "third year": "3rd year",
            "fourth year": "4th year"
        }
        year = year_map.get(years[0], years[0]) if years else ""

        waiver = bool(re.search(r"fee\s*waiver|\bfw\b", q))
        lateral = "lateral" in q

        for chunk in self.chunks:
            if chunk.get("content_type") != "structured_fee":
                continue

            text = chunk["text"].lower()

            if "b.tech" in q or "btech" in q:
                if "course: b.tech" not in text:
                    continue

            if year and f"year: {year}" not in text:
                continue

            if waiver and not re.search(
                r"category:\s*fee\s*waiver", text
            ):
                continue

            if not waiver and "category: regular" not in text:
                continue

            if lateral and "lateral" not in text:
                continue

            score = 10.0

            branch_match = re.search(
                r"\b(csit|cse|ece|civil|mechanical|it|aiml)\b",
                q
            )

            if branch_match:
                branch = branch_match.group(1)
                branch_line = next(
                    (
                        line.lower()
                        for line in chunk["text"].splitlines()
                        if line.lower().startswith("branch / group:")
                    ),
                    ""
                )

                if not re.search(
                    rf"(?<![a-z]){re.escape(branch)}(?![a-z])",
                    branch_line
                ):
                    continue

                score += 5

            results.append((score, chunk))

        return sorted(results, key=lambda x: -x[0])

    # Retrieve verified structured facts before hybrid fallback.
    def search(self, question, top_k=5):
        q = question.lower()
        expanded = self.expand_query(question)

        def finish(items):
            return [
                {**item, "retrieval_score": round(score, 5)}
                for score, item in items[:top_k]
            ]

        # Match fee records using exact course, year, category and branch.
        if re.search(r"\b(fee|fees|tuition|charges|cost)\b", q):
            year_match = re.search(
                r"\b(1st|2nd|3rd|4th|first|second|third|fourth)\s*year\b",
                q
            )
            year_aliases = {
                "first": "1st", "second": "2nd",
                "third": "3rd", "fourth": "4th"
            }
            year = ""
            if year_match:
                year = year_aliases.get(
                    year_match.group(1), year_match.group(1)
                ) + " year"

            waiver = bool(re.search(r"fee\s*waiver|\bfw\b", q))
            category = "fee waiver" if waiver else "regular"

            course = ""
            if re.search(r"b\.?\s*tech", q):
                course = "b.tech"
            elif re.search(r"\bmca\b", q):
                course = "mca"
            elif re.search(r"m\.?\s*tech", q):
                course = "m.tech"

            branch_match = re.search(
                r"\b(csit|cse|ece|civil|mechanical|it|aiml|en)\b",
                q
            )
            branch = branch_match.group(1) if branch_match else ""

            matches = []

            for item in self.chunks:
                if item.get("content_type") != "structured_fee":
                    continue

                text = item["text"].lower()
                field_names = (
                    "Course", "Year", "Category", "Branch / Group",
                    "Registration Fee", "Tuition And Development Fee",
                    "Pdp Fee", "Text Book Charges", "Medical Charges",
                    "Total Fee", "Academic Session", "Notes"
                )

                pattern = (
                    r"(?i)(?<!\w)("
                    + "|".join(re.escape(name) for name in field_names)
                    + r"):\s*"
                )

                parts = list(re.finditer(pattern, text))
                fields = {}

                for index, match in enumerate(parts):
                    end = (
                        parts[index + 1].start()
                        if index + 1 < len(parts)
                        else len(text)
                    )
                    fields[match.group(1).lower()] = (
                        text[match.end():end].strip()
                    )

                if course and fields.get("course", "") != course:
                    continue
                if year and fields.get("year", "") != year:
                    continue
                if fields.get("category", "").replace(" ", "") != category.replace(" ", ""):
                    continue

                group = fields.get("branch / group", "")

                if branch:
                    if not re.search(
                        rf"(?<![a-z]){re.escape(branch)}(?![a-z])",
                        group
                    ):
                        continue

                score = 10.0
                if course:
                    score += 5
                if year:
                    score += 5
                if branch:
                    score += 5

                matches.append((score, item))

            if matches:
                return finish(matches)



        # Use grouped table records for targeted staging questions.
        if re.search(r"\bscholarships?\b", q) or re.search(
            r"\bcourses?\s+offered\b|\bwhat\s+(?:courses|programs)\b", q
        ):
            import json
            from pathlib import Path

            staging_path = Path(
                "data/akgec_rag_chunks_v2_table_staging.json"
            )

            staged = json.loads(
                staging_path.read_text(encoding="utf-8-sig")
            )

            if re.search(r"\bscholarships?\b", q):
                ids = [
                    "staging_scholarship_policy",
                    "staging_scholarship_jee",
                    "staging_scholarship_cuet",
                    "staging_scholarship_conditions"
                ]
            else:
                ids = [
                    "staging_courses_btech",
                    "staging_courses_mca",
                    "staging_courses_mtech"
                ]

            by_id = {item["id"]: item for item in staged}
            selected = [
                by_id[item_id] for item_id in ids
                if item_id in by_id
            ]

            if len(selected) != len(ids):
                raise RuntimeError("Missing grouped staging chunks")

            print("\nMODE: GROUPED TABLE DIRECT RETRIEVAL")
            print("Selected:", [x["id"] for x in selected[:top_k]])
            return selected[:top_k]

        # SCHOLARSHIP_SECTION_PRIORITY_V1
        # Prioritize official scholarship records for scholarship questions.
        if re.search(r"\bscholarships?\b", q):
            scholarship_chunks = [
                item for item in self.chunks
                if item.get("section", "").strip().lower() == "scholarship"
            ]

            if scholarship_chunks:
                ranked_scholarships = []

                for item in scholarship_chunks:
                    text = item.get("text", "").lower()
                    score = 10.0

                    if "jee" in text:
                        score += 2.0

                    if "cuet" in text:
                        score += 2.0

                    if "tuition" in text:
                        score += 1.0

                    ranked_scholarships.append((score, item))

                ranked_scholarships.sort(
                    key=lambda pair: -pair[0]
                )

                return finish(ranked_scholarships)

        # Select official fact rows for direct factual questions.
        fact_patterns = [
            (
                r"full form of akgec|what does akgec stand for",
                "name of the institution"
            ),
            (
                r"\b(located|location|address)\b",
                "institution address"
            ),
            (
                r"\b(established|founded|establishment)\b",
                "year of establishment"
            ),
            (
                r"\bcsit\b.*\b(stand|stands|full form)\b|"
                r"\b(full form)\b.*\bcsit\b",
                "computer science and information technology"
            )
        ]

        for pattern, phrase in fact_patterns:
            if re.search(pattern, q):
                matches = [
                    (10.0, item)
                    for item in self.facts
                    if phrase in item["text"].lower().replace(
                        "computerscience", "computer science"
                    )
                ]
                if matches:
                    return finish(matches)

        # Use hybrid retrieval for remaining questions.
        scores = {}

        def add(item, value):
            key = item["id"]
            if key not in scores:
                scores[key] = [0.0, item]
            scores[key][0] += value

        print("\n===== RETRIEVAL MODE =====")
        print("MODE: HYBRID BM25 + VECTOR")
        print("Question:", question)

        query_tokens = tokenize(expanded)
        bm_scores = self.bm25.get_scores(query_tokens)

        print("\n===== BM25 CANDIDATES =====")
        for rank, idx in enumerate(np.argsort(bm_scores)[::-1][:10], 1):
            item = self.chunks[int(idx)]
            print(
                f"{rank}. ID={item['id']} | "
                f"BM25={float(bm_scores[idx]):.4f} | "
                f"Title={item.get('title', '')}"
            )

        for rank, idx in enumerate(
            np.argsort(bm_scores)[::-1][:80]
        ):
            if bm_scores[idx] > 0:
                add(self.chunks[int(idx)], 2.0 / (60 + rank))

        embedding = self.model.encode(
            [expanded],
            normalize_embeddings=True
        ).tolist()

        vector = self.collection.query(
            query_embeddings=embedding,
            n_results=80
        )

        print("\n===== VECTOR CANDIDATES =====")
        distances = vector.get("distances", [[]])[0]
        for rank, chunk_id in enumerate(vector["ids"][0][:10], 1):
            item = self.by_id.get(str(chunk_id), {})
            distance = distances[rank - 1] if rank - 1 < len(distances) else None
            print(
                f"{rank}. ID={chunk_id} | "
                f"Distance={distance} | "
                f"Title={item.get('title', '')}"
            )

        for rank, chunk_id in enumerate(vector["ids"][0]):
            item = self.by_id.get(str(chunk_id))
            if item:
                add(item, 1.0 / (60 + rank))

        hod_intent = bool(re.search(
            r"\bhod\b|head of (the )?department", q
        ))

        for pair in scores.values():
            item = pair[1]
            text = item["text"].lower()
            section = item.get("section", "").lower()

            if hod_intent:
                if "hod" in text or "heading: hod" in text:
                    pair[0] += 0.10
                if "information technology" in q:
                    if section == "information technology":
                        pair[0] += 0.10
                    else:
                        pair[0] -= 0.10

        ranked = sorted(
            scores.values(),
            key=lambda pair: -pair[0]
        )

        print("\n===== FINAL HYBRID RANKING =====")
        for rank, (score, item) in enumerate(ranked[:10], 1):
            print(
                f"{rank}. ID={item['id']} | "
                f"FusionScore={score:.5f} | "
                f"Title={item.get('title', '')}"
            )

        return finish(ranked)


# Run retrieval checks without changing production.
if __name__ == "__main__":
    retriever = IntegratedRetrieverV2()

    questions = [
        "What is the full form of AKGEC?",
        "Where is AKGEC located?",
        "What does CSIT stand for?",
        "When was AKGEC established?",
        "What is the B.Tech first year fee?",
        "What is the B.Tech 3rd year IT fee?",
        "What is the NBA accreditation status of Information Technology?",
        "Who is the HOD of Information Technology?"
    ]

    for question in questions:
        print("\n" + "=" * 65)
        print("QUESTION:", question)

        for rank, item in enumerate(
            retriever.search(question, top_k=3),
            1
        ):
            print(f"\nRANK {rank}: {item['content_type']}")
            print("SECTION:", item["section"])
            print("TEXT:", item["text"][:400])
            print("SOURCE:", item["source_url"])

    print("\nSTATUS: INTEGRATED V2 RETRIEVAL TEST COMPLETE")
