"""
In-memory BM25 index for lexical retrieval over Marathi transcripts.

Built lazily from SQLite chunk records. Complements semantic search for
hybrid retrieval — especially useful for named entities and exact terms.
"""
import logging
import threading
from typing import Dict, List, Optional, Tuple

from rank_bm25 import BM25Okapi

from sqlalchemy.orm import joinedload

from backend.database.sqlite_client import SessionLocal
from backend.database.models import Chunk
from backend.utils.marathi_text import tokenize_marathi

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_index: Optional[BM25Okapi] = None
_chunk_ids: List[str] = []
_chunk_map: Dict[str, dict] = {}


def _build_chunk_record(chunk: Chunk) -> dict:
    return {
        "chunk_id": chunk.id,
        "video_id": chunk.video_id,
        "video_name": chunk.video.name if chunk.video else "",
        "start_time": chunk.start_time,
        "end_time": chunk.end_time,
        "chunk_index": chunk.chunk_index,
        "text": chunk.text,
    }


def rebuild_index() -> None:
    """Rebuild BM25 index from all chunks in SQLite."""
    global _index, _chunk_ids, _chunk_map

    with _lock:
        db = SessionLocal()
        try:
            chunks = db.query(Chunk).options(joinedload(Chunk.video)).all()
            if not chunks:
                _index = None
                _chunk_ids = []
                _chunk_map = {}
                logger.info("BM25 index: no chunks found.")
                return

            _chunk_ids = []
            _chunk_map = {}
            tokenized_corpus: List[List[str]] = []

            for chunk in chunks:
                record = _build_chunk_record(chunk)
                _chunk_ids.append(chunk.id)
                _chunk_map[chunk.id] = record
                tokenized_corpus.append(tokenize_marathi(chunk.text))

            _index = BM25Okapi(tokenized_corpus)
            logger.info(f"BM25 index rebuilt: {len(_chunk_ids)} documents.")
        finally:
            db.close()


def invalidate_index() -> None:
    """Mark index as stale — will rebuild on next query."""
    global _index
    with _lock:
        _index = None


def _ensure_index() -> bool:
    global _index
    if _index is None:
        rebuild_index()
    return _index is not None


def search(query: str, top_k: int = 20) -> List[dict]:
    """
    BM25 lexical search over indexed chunks.

    Returns chunk dicts with bm25_score added, sorted by relevance.
    """
    if not _ensure_index():
        return []

    tokens = tokenize_marathi(query)
    if not tokens:
        return []

    scores = _index.get_scores(tokens)

    ranked: List[Tuple[int, float]] = sorted(
        enumerate(scores), key=lambda x: x[1], reverse=True
    )[:top_k]

    results = []
    for idx, score in ranked:
        if score <= 0:
            continue
        chunk_id = _chunk_ids[idx]
        record = dict(_chunk_map[chunk_id])
        record["bm25_score"] = round(float(score), 4)
        results.append(record)

    return results
