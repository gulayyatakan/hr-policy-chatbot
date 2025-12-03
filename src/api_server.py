from fastapi.responses import StreamingResponse
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
    "http://localhost:5173",      # Vite dev
    "http://127.0.0.1:5173",
]

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
    path: str
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
        include=["documents", "metadatas"],
    )

    docs_list = results.get("documents", [])
    metas_list = results.get("metadatas", [])

    if not docs_list or not docs_list[0]:
        return []

    docs = docs_list[0]
    metas = metas_list[0] if metas_list else [{}] * len(docs)

    chunks = []
    for doc, meta in zip(docs, metas):
        full_path = meta.get("source", "")
        # nice shorter path for frontend
        rel_name = Path(full_path).name if full_path else full_path
        chunks.append(
            {
                "content": doc,
                "path": rel_name,
                "chunk_index": meta.get("chunk_index", -1),
            }
        )
    return chunks


def build_context(chunks):
    lines = []
    for i, ch in enumerate(chunks, start=1):
        lines.append(
            f"### Chunk {i}\n"
            f"Source: {ch['path']} (chunk {ch['chunk_index']})\n\n"
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


def stream_answer_with_ollama(question: str, context: str):
    """
    Generator that yields the answer text chunk by chunk from Ollama,
    wrapped as proper SSE events.
    """
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

    stream = ollama.chat(
        model="phi3:mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in stream:
        part = chunk["message"]["content"]
        if not part:
            continue
        # SSE format: each "event" is prefixed by 'data: ' and ends with double newline
        yield f"data: {part}\n\n"


# ---------- plain JSON endpoint ----------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    collection = get_collection()
    chunks = retrieve_chunks(collection, req.question, top_k=3)

    if not chunks:
        return ChatResponse(
            answer="No HR policies are indexed yet. Please contact the administrator.",
            sources=[],
        )

    context = build_context(chunks)
    answer = generate_answer_with_ollama(req.question, context)

    sources = [
        SourceInfo(path=c["path"], chunk_index=c["chunk_index"]) for c in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)


# ---------- streaming endpoint for Vite frontend ----------
@app.post("/chat-stream")
def chat_stream(req: ChatRequest):
    """
    Streaming endpoint: sends the answer as SSE text chunks.
    Frontend will use parseSSEStream(stream) to consume this.
    """
    collection = get_collection()
    chunks = retrieve_chunks(collection, req.question, top_k=3)

    if not chunks:
        def fallback():
            # still SSE format
            yield "data: No HR policies are indexed yet. Please contact the administrator.\n\n"
        return StreamingResponse(fallback(), media_type="text/event-stream")

    context = build_context(chunks)

    return StreamingResponse(
        stream_answer_with_ollama(req.question, context),
        media_type="text/event-stream",
    )