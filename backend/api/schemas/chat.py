"""
backend/api/schemas/chat.py

Pydantic request/response models for the /chat endpoint.
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question in Marathi or English")
    language: Literal["mr", "en"] = Field(
        default="mr",
        description="Response language: mr=Marathi, en=English (retrieves Marathi transcripts)",
    )


class SourceChunk(BaseModel):
    chunk_id: str
    video_name: str
    start_time: float
    end_time: float
    text: str
    score: float = Field(default=0.0, description="Cosine similarity score (0-1)")


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    follow_up_questions: List[str]
    language: str = Field(default="mr", description="Response language used")
