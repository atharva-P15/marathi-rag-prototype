"""
backend/api/routes/chat.py

POST /chat — Main RAG query endpoint.

Flow:
  1. Query expansion (Marathi keywords for English mode)
  2. Hybrid retrieval (semantic + BM25 + rerank + compression)
  3. Synthesized answer generation via Groq
  4. Return answer + sources + follow-up questions
"""
import logging
from fastapi import APIRouter, HTTPException
from backend.api.schemas.chat import ChatRequest, ChatResponse, SourceChunk
from backend.services.retriever.retriever_service import retrieve_chunks
from backend.services.llm.groq_service import generate_answer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Ask a question about indexed videos")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Submit a question and get a grounded, synthesized answer
    with source citations and suggested follow-up questions.

    language=mr: Questions and answers in Marathi.
    language=en: Questions in English, answers in English over Marathi transcripts.
    """
    try:
        chunks = retrieve_chunks(
            question=request.question,
            language=request.language,
        )

        result = generate_answer(
            question=request.question,
            chunks=chunks,
            language=request.language,
        )

        sources = [
            SourceChunk(
                chunk_id=s["chunk_id"],
                video_name=s["video_name"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                text=s["text"],
                score=s.get("score", 0.0),
            )
            for s in result["sources"]
        ]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            follow_up_questions=result["follow_up_questions"],
            language=request.language,
        )

    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=str(e))
