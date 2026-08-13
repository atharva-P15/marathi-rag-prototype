"""
backend/services/retriever/retriever_service.py

Hybrid retrieval pipeline:
  1. Query expansion (Marathi keywords for English queries)
  2. Semantic search (ChromaDB + bge-m3)
  3. BM25 lexical search
  4. Reciprocal Rank Fusion (RRF) to merge results
  5. Cross-encoder reranking
  6. Contextual compression
"""
import logging
from typing import Dict, List

from backend.database.chroma_client import get_collection
from backend.services.embedder.embedder_service import embed_query
from backend.services.retriever.bm25_index import search as bm25_search
from backend.services.retriever.reranker_service import rerank_chunks
from backend.services.retriever.query_expansion import expand_query
from backend.services.retriever.context_compressor import compress_chunks
from backend.config import settings

logger = logging.getLogger(__name__)

RRF_K = 60  # Reciprocal Rank Fusion constant


def _reciprocal_rank_fusion(
    ranked_lists: List[List[dict]],
    id_key: str = "chunk_id",
) -> List[dict]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion."""
    scores: Dict[str, float] = {}
    records: Dict[str, dict] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            cid = item[id_key]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
            if cid not in records:
                records[cid] = dict(item)

    merged = sorted(scores.keys(), key=lambda c: scores[c], reverse=True)
    result = []
    for cid in merged:
        record = records[cid]
        record["hybrid_score"] = round(scores[cid], 6)
        result.append(record)
    return result


def _semantic_search(query: str, top_k: int) -> List[dict]:
    """Retrieve chunks via ChromaDB cosine similarity."""
    query_embedding = embed_query(query)
    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if not results["ids"] or not results["ids"][0]:
        return []

    for idx, (chunk_id, doc, meta, dist) in enumerate(zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        chunks.append({
            "chunk_id": chunk_id,
            "video_id": meta.get("video_id", ""),
            "video_name": meta.get("video_name", ""),
            "start_time": meta.get("start_time", 0.0),
            "end_time": meta.get("end_time", 0.0),
            "chunk_index": meta.get("chunk_index", idx),
            "text": doc,
            "keywords": [
                k.strip() for k in meta.get("keywords", "").split(",") if k.strip()
            ],
            "semantic_score": round(1.0 - dist, 4),
        })

    return chunks


def retrieve_chunks(
    question: str,
    language: str = "mr",
    top_k: int | None = None,
) -> List[dict]:
    """
    Full hybrid retrieval pipeline.

    Args:
        question:  User's query.
        language:  Response language mode — "mr" or "en".
        top_k:     Final number of chunks. Defaults to settings.top_k_chunks.

    Returns:
        List of chunk dicts ordered by relevance, with compressed text.
    """
    k = top_k or settings.top_k_chunks
    candidates_k = settings.retrieval_candidates

    logger.info(f"Retrieving (lang={language}) for: {question[:80]}...")

    # Stage 1: Query expansion
    expanded_query = expand_query(question, language=language)

    # Stage 2: Semantic + BM25 retrieval in parallel conceptually
    semantic_results = _semantic_search(expanded_query, top_k=candidates_k)
    bm25_results = bm25_search(expanded_query, top_k=candidates_k)

    if not semantic_results and not bm25_results:
        logger.warning("No chunks found. Have you indexed a video?")
        return []

    # Stage 3: Hybrid fusion via RRF
    if semantic_results and bm25_results:
        fused = _reciprocal_rank_fusion([semantic_results, bm25_results])
    else:
        fused = semantic_results or bm25_results

    # Stage 4: Reranking
    reranked = rerank_chunks(question, fused, top_k=k)

    # Normalize final score field for API compatibility
    for chunk in reranked:
        chunk["score"] = chunk.get(
            "rerank_score",
            chunk.get("hybrid_score", chunk.get("semantic_score", 0.0)),
        )

    # Stage 5: Contextual compression
    if settings.enable_contextual_compression:
        reranked = compress_chunks(reranked, question)

    logger.info(f"Retrieved {len(reranked)} chunks after full pipeline.")
    return reranked
