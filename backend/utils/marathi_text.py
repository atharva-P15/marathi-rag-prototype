"""
Marathi-specific text utilities for tokenization, normalization, and keyword extraction.
"""
import re
from collections import Counter
from typing import List

# Common Marathi ASR filler words / disfluencies
MARATHI_FILLERS = {
    "अं", "अ", "हं", "ह", "म्हणजे", "काय", "बरं", "ठीक", "ना", "नं",
    "uh", "um", "hmm", "aha",
}

# Devanagari block
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+")

# Sentence-ending markers in Marathi transcripts
SENTENCE_END_RE = re.compile(r"[।!?…]+")


def normalize_devanagari(text: str) -> str:
    """Normalize common Devanagari variants and remove zero-width characters."""
    text = text.replace("\u200c", "").replace("\u200d", "").replace("\u00a0", " ")
    # Normalize nukta variants occasionally seen in ASR output
    text = text.replace("क़", "क").replace("ख़", "ख").replace("ग़", "ग")
    return text


def tokenize_marathi(text: str) -> List[str]:
    """
    Tokenize Marathi/English mixed text for BM25.
    Keeps Devanagari words and Latin tokens; drops very short noise tokens.
    """
    text = normalize_devanagari(text.lower())
    # Split on whitespace and punctuation while keeping Devanagari words
    tokens = re.findall(r"[\u0900-\u097F]+|[a-z0-9]+", text)
    return [t for t in tokens if len(t) > 1]


def extract_keywords(text: str, top_n: int = 8) -> List[str]:
    """Simple frequency-based keyword extraction for chunk metadata."""
    tokens = tokenize_marathi(text)
    stop = MARATHI_FILLERS | {
        "आहे", "आहेत", "होते", "होता", "कर", "केले", "मी", "तो", "ती", "ते",
        "आणि", "पण", "किंवा", "जर", "म्हणून", "the", "and", "is", "are", "was", "for",
    }
    filtered = [t for t in tokens if t not in stop and len(t) > 2]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def restore_punctuation(text: str, is_sentence_end: bool = False) -> str:
    """Add Marathi sentence punctuation when missing at natural boundaries."""
    text = text.strip()
    if not text:
        return text
    if is_sentence_end and not SENTENCE_END_RE.search(text[-3:]):
        return text + "।"
    return text
