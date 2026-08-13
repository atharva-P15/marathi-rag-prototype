"""
backend/database/models.py

SQLAlchemy ORM models for SQLite.
Production swap: Change engine URL to PostgreSQL — models stay identical.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Video(Base):
    """
    Represents a single indexed Marathi video.
    One video → many chunks.
    """
    __tablename__ = "videos"

    id = Column(String, primary_key=True)           # UUID
    name = Column(String, nullable=False)            # Display name
    filename = Column(String, nullable=False)        # Original file name
    duration = Column(Float, nullable=True)          # Total duration in seconds
    language = Column(String, default="mr")          # ISO 639-1 code
    status = Column(String, default="pending")       # pending | indexed | failed
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("Chunk", back_populates="video", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "filename": self.filename,
            "duration": self.duration,
            "language": self.language,
            "status": self.status,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Chunk(Base):
    """
    A single timestamped text chunk from a video transcript.
    Stored in both SQLite (metadata) and ChromaDB (vector).
    """
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)                            # UUID
    video_id = Column(String, ForeignKey("videos.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)                    # Order within video
    start_time = Column(Float, nullable=False)                       # seconds
    end_time = Column(Float, nullable=False)                         # seconds
    text = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="chunks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "video_id": self.video_id,
            "chunk_index": self.chunk_index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text,
            "char_count": self.char_count,
        }
