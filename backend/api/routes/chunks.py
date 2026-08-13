"""
backend/api/routes/chunks.py

GET /chunks — List chunks for a specific video, for inspection/debugging.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.api.schemas.video import ChunkResponse
from backend.database.sqlite_client import get_db
from backend.database.models import Chunk

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/chunks", response_model=List[ChunkResponse], summary="List chunks for a video")
def list_chunks(
    video_id: Optional[str] = Query(default=None, description="Filter by video UUID"),
    db: Session = Depends(get_db),
) -> List[ChunkResponse]:
    """
    Return all chunks for a specific video_id, ordered by chunk_index.
    If no video_id provided, returns chunks for all videos.
    """
    query = db.query(Chunk)
    if video_id:
        query = query.filter(Chunk.video_id == video_id)
    chunks = query.order_by(Chunk.chunk_index).all()

    return [
        ChunkResponse(
            id=c.id,
            video_id=c.video_id,
            chunk_index=c.chunk_index,
            start_time=c.start_time,
            end_time=c.end_time,
            text=c.text,
            char_count=c.char_count,
        )
        for c in chunks
    ]
