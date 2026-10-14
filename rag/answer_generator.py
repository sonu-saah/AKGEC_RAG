import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Import existing hybrid retriever.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hybrid_retriever import HybridRetriever

# Load API configuration.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MODEL_NAME = "gemini-3.5-flash-lite"


class AnswerGenerator:
    def __init__(self):
        self.retriever = HybridRetriever()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=api_key)

    # Retrieve context and generate a grounded answer.
    def answer(self, question):
        results = self.retriever.search(question, top_k=5)

        if not results:
            return "No relevant information found.", []

        # Keep only relevant placement documents
        placement_terms = ("placement", "recruitment", "recruiter", "placed", "job offers")

        if any(term in question.lower() for term in placement_terms):
            results = [
                item for item in results
                if any(term in (
                    item.get("title", "") + " " +
                    item.get("source_url", "")
                ).lower() for term in ("placement", "visitedcompany", "recruiter"))
            ]

            if not results:
                return "Placement information not found in retrieved documents.", []

        context_parts = []
        sources = []

        for index, item in enumerate(results, start=1):
            source_url = item.get("source_url", "")
            title = item.get("title", "Unknown")

            context_parts.append(
                f"[Source {index}]\n"
                f"Title: {title}\n"
                f"URL: {source_url}\n"
                f"Content: {item['text']}"
            )

            if source_url and source_url not in sources:
                sources.append(source_url)

        context = "\n\n".join(context_parts)

        prompt = f"""
You are an official-information assistant for Ajay Kumar Garg
Engineering College (AKGEC).

Answer the user's question using ONLY the provided context.

Rules:
1. Do not invent information or statistics.
2. If information is missing, clearly say it is not available
   in the provided documents.
3. Give clear, concise and helpful answers.
4. Cite supporting context using [Source 1], [Source 2], etc.
5. Do not confuse placement offers with unique students placed.
6. Do not treat OCR-corrupted numbers or dates as reliable facts.
7. If documents from different years are present, respect the
   year requested by the user.
8. Do not claim to represent the college officially.
9. For general placement-record questions, provide a concise
   placement summary instead of a company-wise table.
10. Never display suspicious salary values such as 08-Dec,
    03-May, date-formatted CTC values, or malformed table cells.
11. Do not guess, correct, or convert corrupted CTC values.
12. Report total offers only when explicitly supported by the
    retrieved document. Do not call offers unique students.
13. Provide company-wise figures only when the user specifically
    requests them and the extracted rows are unambiguous.
14. For general questions, answer concisely in 3-6 sentences.
15. For general placement-record questions, report the total
    offers and optionally mention 3-5 companies without listing
    every company or individual offer count.
16. Provide detailed lists or tables only when explicitly requested.
17. Do not mention corrupted OCR values unless the user asks
    about data quality.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        answer_text = response.text or "No answer generated."

        # Extract individual and grouped source citations.
        citation_groups = re.findall(
            r"\[Sources?\s+([\d,\s]*(?:Sources?\s+[\d,\s]*)*)\]",
            answer_text,
            flags=re.IGNORECASE
        )

        cited_numbers = set()

        for group in citation_groups:
            cited_numbers.update(
                int(number)
                for number in re.findall(r"\d+", group)
            )

        # Map citation numbers to retrieved source URLs.
        cited_sources = []

        for number in sorted(cited_numbers):
            if 1 <= number <= len(results):
                url = results[number - 1].get("source_url", "")

                if url and url not in cited_sources:
                    cited_sources.append(url)

        return answer_text, cited_sources


def main():
    generator = AnswerGenerator()

    question = "What courses are offered at AKGEC?"

    print("\nQUESTION:", question)

    try:
        answer, sources = generator.answer(question)

        print("\nANSWER:\n")
        print(answer)

        print("\nRETRIEVED SOURCES:")
        for source in sources:
            print("-", source)

        print("\nRAG ANSWER GENERATION TEST COMPLETED")

    except Exception as error:
        print("ANSWER GENERATION FAILED")
        print("ERROR TYPE:", type(error).__name__)
        print("ERROR:", str(error)[:500])


if __name__ == "__main__":
    main()
