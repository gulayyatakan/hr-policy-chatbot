import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent  # e.g., /ws25_26_apip_do1_grp02
DOCS_PATH = BASE_DIR / "data" / "hr_policies"     # folder where your .md files are
CHROMA_PATH = BASE_DIR / "data" / "chroma"        # persistent vector storage

# === Embedding Model (local, no OpenAI) ===
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def load_markdown_files(docs_path: Path):
    """
    Load all .md files from the given directory.
    Returns a list of (doc_id, text, metadata) tuples.
    """
    documents = []

    if not docs_path.exists():
        raise FileNotFoundError(f"Docs folder not found: {docs_path}")

    print("Files in docs_path:", list(docs_path.iterdir()))
    for path in docs_path.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            continue

        # ID relative to the docs folder, e.g. "gitlab_vacation_policy.md"
        doc_id = str(path.relative_to(docs_path))

        # Use a project-relative path so the frontend does not see full absolute paths
        rel_path = path.relative_to(BASE_DIR)  # e.g. "hr_rag_chatbot/data/hr_policies/..."
        metadata = {"source": path.name}
        documents.append((doc_id, text, metadata))

    return documents


def simple_markdown_split(text: str, max_chars: int = 800):
    """
    Simple chunking logic:
    - Splits by headings or blank lines
    - Groups lines up to max_chars per chunk
    This is lightweight and works well for handbooks.
    """
    lines = text.splitlines()
    chunks = []
    buffer = []

    def flush_buffer():
        chunk_text = "\n".join(buffer).strip()
        if chunk_text:
            chunks.append(chunk_text)

    for line in lines:
        # Split on headings
        if line.startswith("#"):
            if buffer:
                flush_buffer()
                buffer.clear()
            buffer.append(line)
        else:
            buffer.append(line)

        # Limit chunk size
        if sum(len(l) for l in buffer) > max_chars:
            flush_buffer()
            buffer.clear()

    if buffer:
        flush_buffer()

    return chunks


def get_chroma_collection():
    """
    Creates or loads a persistent ChromaDB collection for HR policies.
    """
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(allow_reset=True)
    )

    collection = client.get_or_create_collection(
        name="hr-policies",
        metadata={"description": "GitLab Handbook HR section (markdown chunks)"}
    )

    return collection


def ingest():
    """
    Load markdown files, split into chunks, compute embeddings,
    and store them in ChromaDB.
    """
    collection = get_chroma_collection()
    docs = load_markdown_files(DOCS_PATH)

    if not docs:
        print(f"No .md files found in {DOCS_PATH}")
        return

    ids, contents, metadatas = [], [], []
    print(f"Found {len(docs)} markdown document(s). Chunking and embedding...")

    counter = 0
    for doc_id, text, base_meta in docs:
        chunks = simple_markdown_split(text)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}::chunk-{i}"
            ids.append(chunk_id)
            contents.append(chunk)
            metadatas.append({**base_meta, "chunk_index": i})
            counter += 1

    print(f"Total chunks created: {counter}")

    if not contents:
        print("No chunks generated. Nothing to ingest.")
        return

    print("Computing embeddings...")
    embeddings = embedding_model.encode(contents, show_progress_bar=True).tolist()

    print("Upserting data into Chroma...")
    collection.upsert(ids=ids, documents=contents, embeddings=embeddings, metadatas=metadatas)

    print("Ingestion completed successfully.")


if __name__ == "__main__":
    collection = get_chroma_collection()
    print(f"Looking for markdown files in: {DOCS_PATH.resolve()}")
    ingest()
