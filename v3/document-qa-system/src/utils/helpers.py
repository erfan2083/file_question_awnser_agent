"""Utility helper functions."""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List

from loguru import logger


def generate_id(text: str, prefix: str = "") -> str:
    """
    Generate a unique ID from text using SHA-256.

    Args:
        text: Input text to hash
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string
    """
    hash_object = hashlib.sha256(text.encode())
    hash_hex = hash_object.hexdigest()[:16]
    return f"{prefix}{hash_hex}" if prefix else hash_hex


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    Args:
        text: Input text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove special characters but keep punctuation
    text = re.sub(r"[^\w\s.,!?;:()\-\"\']+", "", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Rough estimation: 1 token ≈ 4 characters
    return len(text) // 4


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime as ISO string.

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def validate_language_code(code: str, supported: List[str]) -> bool:
    """
    Validate language code.

    Args:
        code: Language code to validate
        supported: List of supported language codes

    Returns:
        True if valid, False otherwise
    """
    return code.lower() in [lang.lower() for lang in supported]


def calculate_similarity_score(
    bm25_score: float, vector_score: float, bm25_weight: float = 0.5, vector_weight: float = 0.5
) -> float:
    """
    Calculate hybrid similarity score.

    Args:
        bm25_score: BM25 relevance score
        vector_score: Vector similarity score
        bm25_weight: Weight for BM25 score
        vector_weight: Weight for vector score

    Returns:
        Combined similarity score
    """
    return (bm25_score * bm25_weight) + (vector_score * vector_weight)


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """
    Extract keywords from text using simple frequency analysis.

    Args:
        text: Input text
        top_k: Number of top keywords to extract

    Returns:
        List of keywords
    """
    # Simple keyword extraction (can be improved with NLP libraries)
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    # Remove common stop words
    stop_words = {
        "the",
        "is",
        "at",
        "which",
        "on",
        "and",
        "or",
        "but",
        "for",
        "from",
        "with",
        "this",
        "that",
        "are",
        "was",
        "were",
        "been",
        "have",
        "has",
        "had",
    }
    keywords = [w for w in words if w not in stop_words]
    # Count frequencies
    word_freq: Dict[str, int] = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    # Sort by frequency
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_keywords[:top_k]]


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def safe_dict_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary.

    Args:
        dictionary: Input dictionary
        key: Key to retrieve
        default: Default value if key not found

    Returns:
        Value from dictionary or default
    """
    try:
        return dictionary.get(key, default)
    except Exception as e:
        logger.warning(f"Error getting key '{key}' from dictionary: {e}")
        return default


def merge_metadata(base: Dict[str, Any], additional: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two metadata dictionaries.

    Args:
        base: Base metadata
        additional: Additional metadata to merge

    Returns:
        Merged metadata dictionary
    """
    merged = base.copy()
    merged.update(additional)
    return merged
