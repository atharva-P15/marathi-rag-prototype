"""
Contextual compression — extract query-relevant sentences from retrieved chunks.

Reduces noise before LLM synthesis while preserving Marathi source text.
Uses keyword overlap + sentence boundaries (।) — no extra LLM call needed.
"""
import logging
import re
from typing import List, Set

from backend.utils.marathi_text import tokenize_marathi, normalize_devanagari

logger = logging.getLogger(__name__)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[।!?…])\s+")


def _query_terms(query: str) -> Set[str]:
    return set(tokenize_marathi(query))


def _score_sentence(sentence: str, terms: Set[str]) -> float:
    """Score a sentence by keyword overlap with query terms."""
    sent_tokens = set(tokenize_marathi(sentence))
    if not sent_tokens or not terms:
        return 0.0
    overlap = len(sent_tokens & terms)
    return overlap / max(len(terms), 1)


def compress_chunk(text: str, query: str, max_sentences: int = 4) -> str:
    """
    Extract the most query-relevant sentences from a chunk.

    Falls back to full text if compression yields too little content.
    """
    text = normalize_devanagari(text.strip())
    if not text:
        return text

    terms = _query_terms(query)
    sentences = SENTENCE_SPLIT_RE.split(text)

    if len(sentences) <= max_sentences:
        return text

    scored = [(s, _score_sentence(s, terms)) for s in sentences if s.strip()]

    # Always keep at least the first sentence for context
    if scored and scored[0][1] == 0:
        scored[0] = (scored[0][0], 0.1)

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:max_sentences]

    # Restore original order for readability
    top_set = {s for s, _ in top}
    ordered = [s for s in sentences if s in top_set]

    compressed = " ".join(ordered).strip()
    if len(compressed) < 40:
        return text

    return compressed


def compress_chunks(chunks: List[dict], query: str) -> List[dict]:
    """Apply contextual compression to all retrieved chunks."""
    compressed = []
    for chunk in chunks:
        c = dict(chunk)
        c["original_text"] = chunk["text"]
        c["text"] = compress_chunk(chunk["text"], query)
        compressed.append(c)

    logger.info(f"Contextual compression applied to {len(chunks)} chunks.")
    return compressed
