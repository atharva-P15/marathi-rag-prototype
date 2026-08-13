"""Shared helpers for indexing pipeline — metadata and embedding text."""

from backend.services.chunker.chunker_service import TranscriptChunk


def build_embedding_text(chunk: TranscriptChunk) -> str:
    """
    Build enriched text for embedding — prepends keywords for better retrieval.
    The stored document in ChromaDB remains the original chunk text.
    """
    if chunk.keywords:
        kw = ", ".join(chunk.keywords)
        return f"Keywords: {kw}. {chunk.text}"
    return chunk.text


def build_chroma_metadata(chunk: TranscriptChunk) -> dict:
    """Build ChromaDB metadata dict from a TranscriptChunk."""
    return {
        "video_id": chunk.video_id,
        "video_name": chunk.video_name,
        "start_time": chunk.start_time,
        "end_time": chunk.end_time,
        "chunk_index": chunk.chunk_index,
        "keywords": ", ".join(chunk.keywords) if chunk.keywords else "",
    }
