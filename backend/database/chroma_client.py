"""
backend/database/chroma_client.py

ChromaDB client — local persistent vector store.
Production swap: Replace this file with a Qdrant client implementing
the same get_collection() interface. No other files change.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from backend.config import settings

_client: chromadb.PersistentClient | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Return a singleton ChromaDB persistent client."""
    global _client
    if _client is None:
        persist_dir = Path(settings.chroma_persist_dir).resolve()
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    """
    Return (or create) the main chunks collection.

    Collection schema:
      id       : chunk UUID (string)
      embedding: float[1024] from BAAI/bge-m3
      document : chunk text
      metadata : { video_id, video_name, start_time, end_time, chunk_index }
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},  # cosine similarity for bge-m3
    )
