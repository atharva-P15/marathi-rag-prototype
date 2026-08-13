"""
Cross-encoder reranking for retrieved chunks.

Uses BAAI/bge-reranker-v2-m3 (multilingual) to re-score
candidate chunks after hybrid retrieval.
"""
import logging
from typing import List

from sentence_transformers import CrossEncoder

from backend.config import settings

logger = logging.getLogger(__name__)

_reranker: CrossEncoder | None = None


def _load_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info(f"Loading reranker: {settings.reranker_model} ...")
        _reranker = CrossEncoder(
            settings.reranker_model,
            device=settings.embedding_device,
        )
        logger.info("Reranker loaded.")
    return _reranker


def rerank_chunks(query: str, chunks: List[dict], top_k: int | None = None) -> List[dict]:
    """
    Re-score chunks using cross-encoder and return top-K.

    Adds rerank_score to each chunk dict.
    """
    if not chunks or not settings.enable_reranking:
        return chunks[: (top_k or settings.top_k_chunks)]

    k = top_k or settings.top_k_chunks
    model = _load_reranker()

    pairs = [(query, c["text"]) for c in chunks]
    scores = model.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = round(float(score), 4)

    reranked = sorted(chunks, key=lambda c: c.get("rerank_score", 0), reverse=True)
    logger.info(f"Reranked {len(chunks)} candidates → top {k}.")
    return reranked[:k]
