"""
BM25 lexical retrieval index.

Implements efficient full-text search using the BM25 algorithm
from the rank-bm25 library.
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

from rank_bm25 import BM25Okapi

from .config import get_config
from .schemas import CandidateRecord
from .utils import normalize_text, tokenize_text

logger = logging.getLogger(__name__)


class BM25Index:
    """
    BM25 full-text search index.

    Supports:
    - Efficient indexing of large candidate pools
    - Configurable parameters (k1, b)
    - Query expansion
    - Persistence
    """

    def __init__(self, k1: Optional[float] = None, b: Optional[float] = None):
        """
        Initialize BM25 index.

        Args:
            k1: BM25 k1 parameter. If None, uses config default.
            b: BM25 b parameter. If None, uses config default.
        """
        self.config = get_config().bm25
        self.k1 = k1 or self.config.k1
        self.b = b or self.config.b
        self.bm25: Optional[BM25Okapi] = None
        self.candidates: List[CandidateRecord] = []
        self.candidate_ids: List[str] = []

    def build_index(self, candidates: List[CandidateRecord]):
        """
        Build BM25 index from candidates.

        Args:
            candidates: List of candidate records
        """
        logger.info(f"Building BM25 index for {len(candidates)} candidates")
        start_time = time.time()

        self.candidates = candidates
        self.candidate_ids = [c.candidate_id for c in candidates]

        # Tokenize all profile texts
        corpus = []
        for candidate in candidates:
            tokens = tokenize_text(candidate.profile_text, remove_stopwords=True)
            corpus.append(tokens)

        # Build BM25 index
        self.bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b)

        elapsed = time.time() - start_time
        logger.info(f"BM25 index built in {elapsed:.2f}s")

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Retrieve top-k candidates for a query using BM25.

        Args:
            query: Search query
            top_k: Number of results to return. If None, uses config default.

        Returns:
            List of (candidate_id, score) tuples, sorted by score descending
        """
        if self.bm25 is None:
            raise ValueError("Index not built. Call build_index() first.")

        top_k = top_k or self.config.top_k

        # Tokenize query
        query_tokens = tokenize_text(query, remove_stopwords=True)

        if not query_tokens:
            logger.warning("Query produced no tokens after preprocessing")
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Sort and get top-k
        scored_results = [(self.candidate_ids[i], float(scores[i])) for i in range(len(scores))]
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results[:top_k]

    def retrieve_with_ranks(self, query: str, top_k: Optional[int] = None) -> List[dict]:
        """
        Retrieve candidates with rank information.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of dicts with candidate_id, score, and rank
        """
        results = self.retrieve(query, top_k)

        return [{"candidate_id": cid, "score": score, "rank": rank} for rank, (cid, score) in enumerate(results, 1)]

    def save_index(self, file_path: Path):
        """
        Save index to disk.

        Args:
            file_path: Path to save index
        """
        if self.bm25 is None:
            raise ValueError("No index to save. Call build_index() first.")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        # BM25Okapi doesn't have a built-in save method, so we save candidate IDs
        # and metadata. The index can be rebuilt from candidates.
        metadata = {
            "num_candidates": len(self.candidates),
            "k1": self.k1,
            "b": self.b,
            "candidate_ids": self.candidate_ids,
        }

        metadata_path = file_path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"BM25 index metadata saved to {metadata_path}")

    def load_index(self, file_path: Path, candidates: List[CandidateRecord]):
        """
        Load index from disk.

        Args:
            file_path: Path to index metadata
            candidates: List of candidate records (needed to rebuild index)
        """
        metadata_path = file_path.with_suffix(".json")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Index metadata not found: {metadata_path}")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Verify consistency
        if metadata["num_candidates"] != len(candidates):
            logger.warning(
                f"Candidate count mismatch: index has {metadata['num_candidates']}, "
                f"provided {len(candidates)}"
            )

        # Rebuild index
        self.build_index(candidates)
        logger.info(f"BM25 index loaded from {metadata_path}")

    def get_index_info(self) -> dict:
        """Get information about the index."""
        return {
            "num_candidates": len(self.candidates),
            "k1": self.k1,
            "b": self.b,
            "is_built": self.bm25 is not None,
        }
