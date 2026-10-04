import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Create Gemini client
client = genai.Client(api_key=api_key)

# Send a simple test request
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input="Say only: Gemini connection successful."
)

print(interaction.output_text)