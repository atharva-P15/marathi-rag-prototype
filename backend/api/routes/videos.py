"""
backend/api/routes/videos.py

GET /videos — List all indexed videos from SQLite.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.schemas.video import VideoResponse
from backend.database.sqlite_client import get_db
from backend.database.models import Video

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/videos", response_model=List[VideoResponse], summary="List all indexed videos")
def list_videos(db: Session = Depends(get_db)) -> List[VideoResponse]:
    """Return all video records from the metadata database."""
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return [
        VideoResponse(
            id=v.id,
            name=v.name,
            filename=v.filename,
            duration=v.duration,
            language=v.language,
            status=v.status,
            indexed_at=v.indexed_at.isoformat() if v.indexed_at else None,
        )
        for v in videos
    ]
