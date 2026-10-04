import os
import chromadb
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

# Load embedding model and ChromaDB
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
collection = chroma_client.get_collection("akgec_documents")

# Create Gemini client
gemini_client = genai.Client(api_key=api_key)

# Retrieve relevant chunks from ChromaDB
def retrieve_context(question, top_k=5):
    query_embedding = embedding_model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    return documents, metadatas

# Generate an answer using only retrieved AKGEC context
def generate_answer(question):
    documents, metadatas = retrieve_context(question)

    context_parts = []

    for i, (document, metadata) in enumerate(zip(documents, metadatas), 1):
        source = metadata.get("source", "Unknown")
        page = metadata.get("page", "")

        context_parts.append(
            f"[Source {i}] {source} {page}\n{document}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are an AI assistant for Ajay Kumar Garg Engineering College (AKGEC).

Answer the user's question using ONLY the provided context.

If the answer is not present in the context, say:
"I could not find this information in the available AKGEC data."

Do not make up information.

User Question:
{question}

Context:
{context}
"""

    response = gemini_client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt
    )

    return response.output_text

# Test the complete RAG pipeline
question = "How many seats are available in Computer Science and Engineering?"
answer = generate_answer(question)

print("\nAnswer:")
print(answer)