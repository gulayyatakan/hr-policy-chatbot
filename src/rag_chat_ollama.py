import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import ollama

# ----- Config -----
BASE_DIR = Path(__file__).resolve().parent.parent   # .../hr_rag_chatbot
CHROMA_PATH = BASE_DIR / "data" / "chroma"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL_NAME = "phi3:mini"   # your Ollama model


# ----- Embedding model (same as ingest) -----
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def get_chroma_collection():
    """
    Load the existing Chroma collection with the embedded HR chunks.
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(allow_reset=True),
    )

    collection = client.get_or_create_collection(
        name="hr-policies",
        metadata={"description": "GitLab Handbook HR section (markdown chunks)"}
    )

    return collection


def retrieve_chunks(collection, question: str, top_k: int = 3):
    """
    Turn the question into an embedding and retrieve the top_k most similar chunks.
    Returns a list of dicts with id, source, chunk_index, content.
    """
    # 1) Embed question
    query_embedding = embedding_model.encode([question]).tolist()

    # 2) Query Chroma using embeddings
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas"],  # <- IMPORTANT: no "ids" here
    )

    # If nothing found
    if not results.get("documents") or not results["documents"]:
        return []

    docs = results["documents"][0]      # list of texts
    metas = results["metadatas"][0]     # list of metadata dicts
    ids = results["ids"][0]             # ids are always returned, no need to "include" them

    chunks = []
    for doc_id, doc_text, meta in zip(ids, docs, metas):
        chunks.append({
            "id": doc_id,
            "source": meta.get("source", ""),
            "chunk_index": meta.get("chunk_index"),
            "content": doc_text,
        })

    return chunks


def build_context_text(chunks) -> str:
    """
    Build a readable context string for the LLM from retrieved chunks.
    """
    parts = []
    for i, ch in enumerate(chunks, start=1):
        parts.append(
            f"### Chunk {i}\n"
            f"Source: {ch['source']}\n\n"
            f"{ch['content']}\n"
        )
    return "\n---\n".join(parts)


def generate_answer_with_ollama(question: str, chunks) -> str:
    """
    Call the local Ollama model with question + retrieved context.
    """
    if not chunks:
        return "I couldn't find any relevant information in the HR policies for this question."

    context_text = build_context_text(chunks)

    system_prompt = (
        "You are an HR assistant for an internal company chatbot. "
        "You must answer ONLY based on the provided context from HR policies. "
        "If the answer is not clearly in the context, say that you don't know "
        "and suggest contacting HR. "
        "Keep the answer concise (max 4–5 sentences)."
    )

    user_content = (
        f"Question:\n{question}\n\n"
        f"Context from HR policies:\n{context_text}"
    )

    response = ollama.chat(
        model=LLM_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    return response["message"]["content"]


def main():
    collection = get_chroma_collection()
    print("HR RAG chat with Ollama (local LLM). Type 'exit' or 'quit' to stop.\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue

        if question.lower() in ("exit", "quit"):
            print("Bot: Goodbye.")
            break

        # 1) Retrieve chunks from Chroma
        chunks = retrieve_chunks(collection, question, top_k=3)

        # 2) Generate answer with local LLM
        answer = generate_answer_with_ollama(question, chunks)

        print(f"\nBot: {answer}\n")

        # Optional: show which sources were used
        if chunks:
            print("Sources used:")
            for ch in chunks:
                print(f"- {ch['source']} (chunk {ch['chunk_index']})")
        print("-" * 60)


if __name__ == "__main__":
    main()