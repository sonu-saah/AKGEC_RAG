from contextlib import asynccontextmanager
from pathlib import Path
import importlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.answer_generator import AnswerGenerator

generator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global generator

    # Configure the validated experimental RAG.
    module = importlib.import_module(AnswerGenerator.__init__.__globals__["HybridRetriever"].__module__)

    module.CHUNKS_FILE = Path("data/fresh/structured/rag_experiment_chunks_v3.json")
    module.DB_DIR = "data/fresh/chroma_db_experiment"
    module.COLLECTION_NAME = "akgec_experiment_documents"

    generator = AnswerGenerator()
    yield
    generator = None


app = FastAPI(
    title="AKGEC AI Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "rag_loaded": generator is not None}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if generator is None:
        raise HTTPException(status_code=503, detail="RAG is not ready")

    try:
        answer, sources = generator.answer(request.question)
        return ChatResponse(answer=answer, sources=sources)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer right now"
        )
