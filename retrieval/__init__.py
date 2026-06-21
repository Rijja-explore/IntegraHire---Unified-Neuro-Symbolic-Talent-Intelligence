"""
Retrieval and Semantic Intelligence Subsystem.

A production-grade hybrid retrieval engine combining BM25 lexical search,
dense embeddings, and Reciprocal Rank Fusion for intelligent candidate ranking.

Key components:
- CandidatePreprocessor: Normalizes and enriches candidate profiles
- EmbeddingGenerator: Generates dense vector representations
- BM25Index: Efficient full-text search
- FAISSIndex: Fast similarity search
- ReciprocalRankFusion: Fuses multiple rankings
- RetrievalEngine: Main orchestration and API

Usage:
    from retrieval.retrieval_engine import RetrievalEngine
    from pathlib import Path

    engine = RetrievalEngine()
    engine.build_indexes(Path("candidates.jsonl"))
    response = engine.retrieve_by_text("Software Engineer with ML experience", top_k=100)
"""

from .retrieval_engine import RetrievalEngine
from .schemas import CandidateRecord, RetrievalRequest, RetrievalResponse, RetrievalResult

__version__ = "1.0.0"
__all__ = [
    "RetrievalEngine",
    "CandidateRecord",
    "RetrievalRequest",
    "RetrievalResponse",
    "RetrievalResult",
]
