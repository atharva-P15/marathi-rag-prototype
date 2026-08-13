"""
backend/api/schemas/video.py

Pydantic request/response models for video and chunk endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class IndexRequest(BaseModel):
    video_path: str = Field(..., description="Path to video file inside media/videos/")


class IndexResponse(BaseModel):
    video_id: str
    video_name: str
    chunks_indexed: int
    status: str


class VideoResponse(BaseModel):
    id: str
    name: str
    filename: str
    duration: Optional[float]
    language: str
    status: str
    indexed_at: Optional[str]


class ChunkResponse(BaseModel):
    id: str
    video_id: str
    chunk_index: int
    start_time: float
    end_time: float
    text: str
    char_count: int
