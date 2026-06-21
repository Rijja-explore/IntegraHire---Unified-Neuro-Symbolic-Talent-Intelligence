"""
Utility functions for the retrieval subsystem.

Includes text processing, logging, and helper functions.
"""

import json
import logging
import logging.handlers
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np

from .config import get_config


def setup_logging(name: str = "retrieval") -> logging.Logger:
    """
    Set up structured logging for the subsystem.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    config = get_config()
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.logging.level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.logging.level))

    if config.logging.format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if configured
    if config.logging.log_file:
        config.logging.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            config.logging.log_file, maxBytes=100 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(getattr(logging, config.logging.level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def normalize_text(text: str) -> str:
    """
    Normalize text for processing.

    Applies:
    - Lowercasing
    - Whitespace normalization
    - Special character cleaning

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Remove extra punctuation but keep important ones
    text = re.sub(r"[^\w\s.,;:()\-/]", "", text)

    return text.strip()


def tokenize_text(text: str, remove_stopwords: bool = True) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Input text
        remove_stopwords: Whether to remove common stopwords

    Returns:
        List of tokens
    """
    if not text:
        return []

    text = normalize_text(text)
    tokens = text.split()

    if remove_stopwords:
        stopwords = get_stopwords()
        tokens = [t for t in tokens if t not in stopwords]

    return tokens


def get_stopwords() -> Set[str]:
    """Get common English stopwords."""
    return {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
    }


def extract_keywords(text: str, top_k: int = 20) -> List[str]:
    """
    Extract keywords from text using simple frequency analysis.

    Args:
        text: Input text
        top_k: Number of top keywords to extract

    Returns:
        List of keywords
    """
    tokens = tokenize_text(text, remove_stopwords=True)

    if not tokens:
        return []

    # Count frequency
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1

    # Sort by frequency
    sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    return [token for token, _ in sorted_tokens[:top_k]]


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def normalize_scores(scores: List[float], min_val: float = 0.0, max_val: float = 1.0) -> List[float]:
    """
    Normalize scores to a specified range.

    Args:
        scores: Input scores
        min_val: Minimum value for normalization
        max_val: Maximum value for normalization

    Returns:
        Normalized scores
    """
    if not scores:
        return []

    scores_array = np.array(scores)
    min_score = np.min(scores_array)
    max_score = np.max(scores_array)

    if min_score == max_score:
        return [min_val] * len(scores)

    normalized = (scores_array - min_score) / (max_score - min_score)
    return (normalized * (max_val - min_val) + min_val).tolist()


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load JSONL file.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of parsed JSON objects
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def save_jsonl(data: List[Dict[str, Any]], file_path: Path) -> None:
    """
    Save data to JSONL file.

    Args:
        data: List of dictionaries to save
        file_path: Path to save file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")


def batch_iterator(items: List[Any], batch_size: int):
    """
    Iterate over items in batches.

    Args:
        items: List of items
        batch_size: Batch size

    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with statistics
    """
    if not values:
        return {"count": 0}

    arr = np.array(values)
    return {
        "count": len(values),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = seconds / 60
        return f"{minutes:.1f}m"


def get_logger(name: str = "retrieval") -> logging.Logger:
    """Get or create a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger = setup_logging(name)
    return logger
