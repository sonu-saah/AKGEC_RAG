
import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Create Gemini client
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


def generate_answer(question, context):
    prompt = f"""
You are a helpful AI assistant for AKGEC
(Ajay Kumar Garg Engineering College).

Answer the user's question according to these rules:

1. For AKGEC-specific questions:
   - First use the provided AKGEC context.
   - Never invent official college information.
   - If the context does not contain a specific official fact,
     clearly say that the fact could not be verified from
     the available AKGEC data.

2. For general questions:
   - Use your general knowledge to answer.
   - Explain concepts clearly with useful examples when needed.
   - Do not refuse just because the answer is missing from
     the AKGEC context.

3. For mixed questions:
   - Use the AKGEC context for college-specific facts.
   - Use general knowledge for explanations.
   - Clearly distinguish verified college information from
     general explanations.

4. Never invent fees, placement statistics, admission dates,
   seat counts, or other official college details.

5. Give a clear, relevant answer in simple English.
   Use a short answer by default, but explain more when needed.

6. Do not generate a separate Sources section or source URLs.
   The application handles citations separately.

USER QUESTION:
{question}

RETRIEVED AKGEC CONTEXT:
{context if context and context.strip() else "No relevant AKGEC information was retrieved."}

ANSWER:
"""

    # Generate answer using Gemini
    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt
    )

    return interaction.output_text


# Test Gemini
if __name__ == "__main__":
    test_questions = [
        "What is the difference between B.Tech and M.Tech?",
        "What is the sanctioned intake for B.Tech CSE at AKGEC?",
        "What is Python programming?"
    ]

    sample_context = """
    Courses Offered:
    B.Tech Computer Science and Engineering
    Sanctioned Intake: 450
    Source: https://www.akgec.ac.in/admissions/courses-offered/
    """

    for question in test_questions:
        print("\n" + "=" * 60)
        print("QUESTION:", question)

        try:
            answer = generate_answer(question, sample_context)
            print("ANSWER:", answer)
        except Exception as error:
            print("ERROR:", error)
