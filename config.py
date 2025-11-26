import os
from dotenv import load_dotenv

# Lädt Variablen aus .env-Datei (falls vorhanden)
load_dotenv()

class Config:
    DATA_PATH = os.getenv("DATA_PATH", "data/")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma/")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "hr_documents")

    # Optional: OpenAI- oder API-Keys später hier speichern
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")