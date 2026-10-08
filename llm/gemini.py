import os
from dotenv import load_dotenv
from google import genai

# Load the Gemini API key from the .env file.
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")


# Create the Gemini client.
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


# Generate an answer using only the retrieved AKGEC context.
def generate_answer(question, context):
    prompt = f"""
You are an AKGEC information assistant.

Answer the user's question using ONLY the provided AKGEC context.

Rules:
- Do not use outside knowledge.
- Do not invent or guess information.
- If the answer is not available in the context, say:
  "I could not find this information in the AKGEC data."
- Give a short and clear answer.
- Do not mention or generate any source URL.
- Do not add a "Sources" or "Source URL" section.
- The application will handle citations separately.

USER QUESTION:
{question}

AKGEC CONTEXT:
{context}

ANSWER:
"""

    # Send the question and retrieved context to Gemini.
    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=prompt
    )

    return interaction.output_text


# Test Gemini with a small example.
if __name__ == "__main__":
    question = "How many seats are available in Computer Science and Engineering?"

    context = """
    Courses Offered
    Courses Sanctioned Intake
    B.Tech Computer Science and Engineering 450
    Source: https://www.akgec.ac.in/admissions/courses-offered/
    """

    answer = generate_answer(question, context)

    print("\nGEMINI ANSWER")
    print(answer)