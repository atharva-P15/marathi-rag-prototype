"""
Query expansion for improved retrieval, especially for English queries
over Marathi transcript content.
"""
import json
import logging
import re
from typing import List

from groq import Groq

from backend.config import settings
from backend.services.llm.prompts import QUERY_EXPANSION_PROMPT

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _extract_json(text: str) -> dict:
    """Extract JSON object from LLM response."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    return {}


def expand_query(question: str, language: str = "mr") -> str:
    """
    Expand a user query for better retrieval.

    For English queries: generates Marathi keywords via LLM + English synonyms.
    For Marathi queries: adds keyword extraction from the question itself.

    Returns an enriched query string combining original + expansion terms.
    """
    if not settings.enable_query_expansion:
        return question

    parts = [question]

    if language == "en":
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": QUERY_EXPANSION_PROMPT},
                    {"role": "user", "content": question},
                ],
                temperature=0.0,
                max_tokens=512,
            )
            raw = response.choices[0].message.content or ""
            data = _extract_json(raw)

            marathi_kw = data.get("marathi_keywords", [])
            marathi_phrases = data.get("marathi_phrases", [])
            english_syn = data.get("english_synonyms", [])

            if marathi_kw:
                parts.extend(marathi_kw)
            if marathi_phrases:
                parts.extend(marathi_phrases)
            if english_syn:
                parts.extend(english_syn)

            logger.info(
                f"Query expansion (en→mr): +{len(marathi_kw)} Marathi keywords, "
                f"+{len(english_syn)} English synonyms."
            )
        except Exception as e:
            logger.warning(f"Query expansion failed, using original query: {e}")
    else:
        from backend.utils.marathi_text import extract_keywords
        keywords = extract_keywords(question, top_n=6)
        if keywords:
            parts.extend(keywords)
            logger.info(f"Query expansion (mr): +{len(keywords)} keywords.")

    return " ".join(parts)
