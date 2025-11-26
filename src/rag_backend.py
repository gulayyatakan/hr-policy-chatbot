import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# === Paths / constants ===
BASE_DIR = Path(__file__).resolve().parent.parent  # .../hr_rag_chatbot
CHROMA_PATH = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "hr-policies"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def _get_chroma_collection():
    """
    Load the existing Chroma collection created by ingest_md.py.
    We do NOT set an embedding_function here because we stored
    embeddings manually during ingestion.
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(allow_reset=False),
    )
    return client.get_collection(COLLECTION_NAME)


_collection = _get_chroma_collection()


def embed_query(text: str) -> list[float]:
    """
    Turn a user query into a single embedding vector.
    """
    vec = _embedding_model.encode([text])[0]  # shape (384,)
    return vec.tolist()


def retrieve_chunks(query: str, top_k: int = 3):
    """
    Given a user query, return the top_k most similar chunks from Chroma.

    Returns a list of dicts:
    [
      {
        "id": "gitlab_vacation_policy.md::chunk-0",
        "content": "...",
        "metadata": {...}
      },
      ...
    ]
    """
    query_embedding = embed_query(query)

    result = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    # Chroma returns lists-of-lists
    docs = result["documents"][0]
    ids = result["ids"][0]
    metadatas = result["metadatas"][0]

    hits = []
    for i in range(len(ids)):
        hits.append(
            {
                "id": ids[i],
                "content": docs[i],
                "metadata": metadatas[i],
            }
        )
    return hits


if __name__ == "__main__":
    # Simple CLI test
    print("Loaded collection:", COLLECTION_NAME)
    while True:
        q = input("\nAsk an HR question (or 'exit'): ").strip()
        if q.lower() in ("exit", "quit"):
            break
        results = retrieve_chunks(q, top_k=3)
        if not results:
            print("No results.")
            continue
        print("\nTop chunks:")
        for idx, hit in enumerate(results, start=1):
            print(f"\n--- Result {idx} ---")
            print("ID:", hit["id"])
            print("Source:", hit["metadata"].get("source"))
            print(hit["content"][:500], "...")