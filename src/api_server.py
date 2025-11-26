import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import ollama
from pathlib import Path

# ---------- config ----------
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_PATH = BASE_DIR / "data" / "chroma"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# ---------- FastAPI setup ----------
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow frontend (localhost:3000 etc.) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class ChatRequest(BaseModel):
    question: str

class SourceInfo(BaseModel):
    source: str
    chunk_index: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]


# ---------- helpers ----------
def get_collection():
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(allow_reset=True),
    )
    return client.get_or_create_collection(name="hr-policies")


def embed_text(text: str) -> list[float]:
    return embedding_model.encode([text])[0].tolist()


def retrieve_chunks(collection, question: str, top_k: int = 3):
    query_emb = embed_text(question)
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["documents", "metadatas"],  # IDs not needed, we have metadata
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    chunks = []
    for doc, meta in zip(docs, metas):
        chunks.append(
            {
                "content": doc,
                "source": meta.get("source", ""),
                "chunk_index": meta.get("chunk_index", -1),
            }
        )
    return chunks


def build_context(chunks):
    lines = []
    for i, ch in enumerate(chunks, start=1):
        lines.append(
            f"### Chunk {i}\n"
            f"Source: {ch['source']} (chunk {ch['chunk_index']})\n\n"
            f"{ch['content']}\n"
        )
    return "\n\n".join(lines)


def generate_answer_with_ollama(question: str, context: str) -> str:
    system_prompt = (
        "You are an HR assistant. Answer the question strictly based on the "
        "provided policy context. If the answer is not in the context, say "
        "'I cannot answer that based on the available HR policies.'\n\n"
        "Always be concise and clear."
    )

    prompt = (
        f"{system_prompt}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    resp = ollama.chat(
        model="phi3:mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp["message"]["content"]


# ---------- endpoint ----------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    collection = get_collection()
    chunks = retrieve_chunks(collection, req.question, top_k=3)
    context = build_context(chunks)
    answer = generate_answer_with_ollama(req.question, context)

    sources = [
        SourceInfo(source=c["source"], chunk_index=c["chunk_index"]) for c in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)