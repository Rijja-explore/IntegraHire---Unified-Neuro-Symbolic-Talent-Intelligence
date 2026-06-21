"""
Reciprocal Rank Fusion (RRF) for hybrid retrieval fusion.

Combines BM25 and dense embedding rankings using RRF to produce
a unified semantic relevance score.
"""

import logging
from typing import Dict, List, Optional, Tuple

from .config import get_config

logger = logging.getLogger(__name__)


class ReciprocalRankFusion:
    """
    Combines multiple ranking lists using Reciprocal Rank Fusion.

    Formula: RRF(d) = Σ 1/(k + rank(d))

    Where:
    - d is a document (candidate)
    - rank(d) is the rank of document in each ranking
    - k is a configurable constant (typically 60)
    """

    def __init__(self, k: Optional[int] = None):
        """
        Initialize RRF fusion.

        Args:
            k: RRF constant parameter. If None, uses config default.
        """
        self.config = get_config().retrieval
        self.k = k or self.config.rrf_k

    def fuse_rankings(
        self, bm25_results: List[Tuple[str, float]], embedding_results: List[Tuple[str, float]], weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[str, float]]:
        """
        Fuse two ranking lists using RRF.

        Args:
            bm25_results: List of (candidate_id, score) from BM25
            embedding_results: List of (candidate_id, score) from embeddings
            weights: Optional weights for each ranking. Dict with keys 'bm25' and 'embedding'.
                    If None, uses config defaults.

        Returns:
            List of (candidate_id, fused_score) sorted by score descending
        """
        if weights is None:
            weights = {"bm25": self.config.bm25_weight, "embedding": self.config.embedding_weight}

        # Build rank maps
        bm25_ranks: Dict[str, int] = {cid: rank for rank, (cid, _) in enumerate(bm25_results, 1)}
        embedding_ranks: Dict[str, int] = {cid: rank for rank, (cid, _) in enumerate(embedding_results, 1)}

        # Collect all candidate IDs
        all_candidates = set(bm25_ranks.keys()) | set(embedding_ranks.keys())

        # Calculate RRF scores
        fused_scores: Dict[str, float] = {}

        for candidate_id in all_candidates:
            score = 0.0

            # BM25 contribution
            if candidate_id in bm25_ranks:
                rank = bm25_ranks[candidate_id]
                rrf_component = 1.0 / (self.k + rank)
                score += weights["bm25"] * rrf_component

            # Embedding contribution
            if candidate_id in embedding_ranks:
                rank = embedding_ranks[candidate_id]
                rrf_component = 1.0 / (self.k + rank)
                score += weights["embedding"] * rrf_component

            fused_scores[candidate_id] = score

        # Sort by fused score
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_results

    def fuse_with_metadata(
        self,
        bm25_results: List[dict],
        embedding_results: List[dict],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[dict]:
        """
        Fuse rankings and return detailed metadata.

        Args:
            bm25_results: List of dicts with candidate_id, score, rank
            embedding_results: List of dicts with candidate_id, similarity, rank
            weights: Optional weights

        Returns:
            List of fused results with detailed information
        """
        # Extract (candidate_id, score) tuples
        bm25_tuples = [(r["candidate_id"], r["score"]) for r in bm25_results]
        embedding_tuples = [(r["candidate_id"], r["similarity"]) for r in embedding_results]

        # Fuse
        fused_tuples = self.fuse_rankings(bm25_tuples, embedding_tuples, weights)

        # Build result dicts
        bm25_lookup = {r["candidate_id"]: r for r in bm25_results}
        embedding_lookup = {r["candidate_id"]: r for r in embedding_results}

        fused_results = []
        for rank, (candidate_id, fused_score) in enumerate(fused_tuples, 1):
            result = {
                "candidate_id": candidate_id,
                "fused_score": fused_score,
                "final_rank": rank,
                "bm25_rank": bm25_lookup.get(candidate_id, {}).get("rank"),
                "bm25_score": bm25_lookup.get(candidate_id, {}).get("score"),
                "embedding_rank": embedding_lookup.get(candidate_id, {}).get("rank"),
                "embedding_similarity": embedding_lookup.get(candidate_id, {}).get("similarity"),
            }
            fused_results.append(result)

        return fused_results

    def normalize_scores(self, results: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """
        Normalize fused scores to 0-1 range.

        Args:
            results: List of (candidate_id, score) tuples

        Returns:
            List of results with normalized scores
        """
        if not results:
            return []

        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)

        if min_score == max_score:
            # All scores are the same
            return [(cid, 1.0) for cid, _ in results]

        normalized = []
        for candidate_id, score in results:
            normalized_score = (score - min_score) / (max_score - min_score)
            normalized.append((candidate_id, normalized_score))

        return normalized

    @staticmethod
    def calculate_rrf_component(rank: int, k: int = 60) -> float:
        """
        Calculate RRF component for a given rank.

        Args:
            rank: Ranking position (1-indexed)
            k: RRF constant

        Returns:
            RRF component value
        """
        return 1.0 / (k + rank)

    def get_fusion_config(self) -> dict:
        """Get current fusion configuration."""
        return {
            "k": self.k,
            "bm25_weight": self.config.bm25_weight,
            "embedding_weight": self.config.embedding_weight,
        }
