"""
backend/services/llm/groq_service.py

Groq API integration for grounded RAG answers with cross-chunk synthesis.

Supports Marathi and English response modes while always reasoning
over original Marathi transcript chunks.
"""
import logging
import re
from typing import List, Literal

from groq import Groq

from backend.config import settings
from backend.services.llm.prompts import (
    SYSTEM_PROMPT_MARATHI,
    SYSTEM_PROMPT_ENGLISH,
    NOT_FOUND_MARATHI,
    NOT_FOUND_ENGLISH,
    NO_INDEX_MARATHI,
    NO_INDEX_ENGLISH,
)

logger = logging.getLogger(__name__)

Language = Literal["mr", "en"]

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _build_context_block(chunks: List[dict], language: Language) -> str:
    """Build the context section of the prompt from retrieved chunks."""
    lang_note = (
        "Note: Source text is in Marathi (Devanagari). Read and reason over it directly."
        if language == "en"
        else "Note: स्रोत मजकूर मराठीत आहे."
    )
    lines = [lang_note, ""]
    for i, chunk in enumerate(chunks, 1):
        ts_start = _format_timestamp(chunk["start_time"])
        ts_end = _format_timestamp(chunk["end_time"])
        keywords = chunk.get("keywords", [])
        kw_str = f" | Keywords: {', '.join(keywords)}" if keywords else ""
        lines.append(
            f"[CHUNK {i}]\n"
            f"Video: {chunk['video_name']} | Time: {ts_start} - {ts_end}{kw_str}\n"
            f"{chunk['text']}\n"
        )
    return "\n".join(lines)


def _system_prompt(language: Language) -> str:
    return SYSTEM_PROMPT_ENGLISH if language == "en" else SYSTEM_PROMPT_MARATHI


def generate_answer(
    question: str,
    chunks: List[dict],
    language: Language = "mr",
) -> dict:
    """
    Build prompt with retrieved context and call Groq for a synthesized answer.

    Args:
        question: User's query.
        chunks:   Retrieved chunks (Marathi text).
        language: Response language — "mr" for Marathi, "en" for English.

    Returns:
        { answer, sources, follow_up_questions }
    """
    if not chunks:
        return {
            "answer": NO_INDEX_ENGLISH if language == "en" else NO_INDEX_MARATHI,
            "sources": [],
            "follow_up_questions": [],
        }

    context_block = _build_context_block(chunks, language)

    synthesis_hint = (
        "Synthesize information across ALL relevant chunks into one coherent answer. "
        "Do not summarize chunks one by one."
        if language == "en"
        else "सर्व संबंधित खंडांमधील माहिती एकत्रित करून एक संश्लेषित उत्तर द्या. "
        "प्रत्येक खंड स्वतंत्रपणे सारांशित करू नका."
    )

    user_message = (
        f"Context Chunks:\n\n{context_block}\n\n"
        f"User Question: {question}\n\n"
        f"Important: {synthesis_hint}"
    )

    logger.info(f"Calling Groq ({settings.groq_model}, lang={language}) ...")

    client = _get_client()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _system_prompt(language)},
            {"role": "user", "content": user_message},
        ],
        temperature=settings.groq_temperature,
        max_tokens=settings.groq_max_tokens,
    )

    raw_text = response.choices[0].message.content or ""
    logger.info("Groq response received.")

    answer = _extract_tag(raw_text, "answer")
    follow_up_raw = _extract_tag(raw_text, "follow_up")

    # Use original (pre-compression) text in sources when available
    sources = [
        {
            "chunk_id": c["chunk_id"],
            "video_name": c["video_name"],
            "start_time": c["start_time"],
            "end_time": c["end_time"],
            "text": c.get("original_text", c["text"]),
            "score": c.get("score", 0.0),
        }
        for c in chunks
    ]

    follow_ups = _parse_follow_ups(follow_up_raw, language)

    fallback = NOT_FOUND_ENGLISH if language == "en" else NOT_FOUND_MARATHI
    return {
        "answer": answer or raw_text or fallback,
        "sources": sources,
        "follow_up_questions": follow_ups,
    }


def _extract_tag(text: str, tag: str) -> str:
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_follow_ups(text: str, language: Language) -> List[str]:
    lines = text.strip().split("\n")
    questions = []
    for line in lines:
        cleaned = re.sub(r"^\d+\.\s*", "", line.strip())
        if cleaned:
            questions.append(cleaned)
    return questions[:3]
