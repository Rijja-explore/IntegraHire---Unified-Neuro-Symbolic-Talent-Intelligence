"""Retrieval subsystem — canonical entry via root ``retrieval`` package."""

from retrieval.retrieval_engine import RetrievalEngine
from retrieval.preprocessing import CandidatePreprocessor
from retrieval.fusion import ReciprocalRankFusion
from retrieval.embeddings import EmbeddingGenerator
from retrieval.bm25_index import BM25Index
from retrieval.faiss_index import FAISSIndex

__all__ = [
    "RetrievalEngine",
    "CandidatePreprocessor",
    "ReciprocalRankFusion",
    "EmbeddingGenerator",
    "BM25Index",
    "FAISSIndex",
]
