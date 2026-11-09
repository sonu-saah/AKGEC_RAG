
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.answer_generator_v2_table_test import AnswerGenerator
from varifier.claim_verifier import get_nli_model

generator = None


# Initialize the V2 answer generator and verification model.
@asynccontextmanager
async def lifespan(app: FastAPI):
    global generator

    print("Loading V2 answer generator...")
    generator = AnswerGenerator()

    print("Loading semantic verification model...")
    get_nli_model()
    print("Semantic verification model ready.")

    yield

    generator = None


app = FastAPI(
    title="AKGEC AI Assistant API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


# Check whether the backend is running.
@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}


# Generate an answer using the V2 RAG pipeline.
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if generator is None:
        raise HTTPException(
            status_code=503,
            detail="Answer generator is not ready."
        )

    try:
        answer, sources = generator.answer(request.question)

        return ChatResponse(
            answer=answer,
            sources=sources
        )

    except Exception as error:
        print(f"Chat error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer."
        )
