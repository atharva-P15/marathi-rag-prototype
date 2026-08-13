"""
backend/services/embedder/embedder_service.py

BAAI/bge-m3 embedding service using sentence-transformers.
bge-m3 is multilingual and handles Marathi well without fine-tuning.

Production swap: Wrap this in a dedicated embedding microservice
(e.g., Text Embeddings Inference server) — only the HTTP call changes.
"""
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from backend.config import settings

logger = logging.getLogger(__name__)

# Singleton model instance — expensive to load, reused for every call
_model: SentenceTransformer | None = None


def _load_model() -> SentenceTransformer:
    """Load bge-m3 (lazy, cached). Downloads ~2GB on first call."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model} ...")
        _model = SentenceTransformer(
            settings.embedding_model,
            device=settings.embedding_device,
        )
        logger.info("Embedding model loaded.")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each is a float list of dim ~1024 for bge-m3).
    """
    model = _load_model()
    logger.info(f"Embedding {len(texts)} text(s)...")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,  # Required for cosine similarity
        show_progress_bar=len(texts) > 10,
        batch_size=16,
    )
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.
    bge-m3 recommends wrapping query in 'Represent this sentence: ...'
    for retrieval tasks.

    Args:
        query: The user's question string.

    Returns:
        Embedding vector as a float list.
    """
    # bge-m3 query instruction prefix for retrieval tasks
    prefixed_query = f"Represent this sentence: {query}"
    return embed_texts([prefixed_query])[0]
