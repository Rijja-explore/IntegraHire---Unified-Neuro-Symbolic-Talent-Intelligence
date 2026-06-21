"""Score fusion and final ranking."""
from ..schemas import CandidateScores, RankedCandidate, CandidateDNA
from ..config import ScoringWeights, DEFAULT_SCORING_WEIGHTS
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class ScoreFusion:
    """Fuse multiple ranking signals into final score."""

    def __init__(self, weights: ScoringWeights = None):
        self.weights = weights or DEFAULT_SCORING_WEIGHTS
        self._validate_weights()

    def _validate_weights(self):
        """Ensure weights sum to 1.0."""
        total = sum([
            self.weights.semantic_score,
            self.weights.production_score,
            self.weights.authenticity_score,
            self.weights.trajectory_score,
            self.weights.behavior_score,
            self.weights.dna_score,
        ])
        assert abs(total - 1.0) < 0.001, f"Weights must sum to 1.0, got {total}"

    def fuse_scores(self, scores: CandidateScores) -> float:
        """
        Fuse individual scores into final ranking score (0-100).
        """
        final = (
            (scores.semantic_score * self.weights.semantic_score) +
            (scores.production_score * self.weights.production_score) +
            (scores.authenticity_score * self.weights.authenticity_score) +
            (scores.trajectory_score * self.weights.trajectory_score) +
            (scores.behavior_score * self.weights.behavior_score) +
            (scores.dna_score * self.weights.dna_score)
        )

        return min(100, max(0, final))

    def explain_score(self, scores: CandidateScores) -> Dict[str, float]:
        """Break down score contributions."""
        contributions = {
            "semantic": scores.semantic_score * self.weights.semantic_score,
            "production": scores.production_score * self.weights.production_score,
            "authenticity": scores.authenticity_score * self.weights.authenticity_score,
            "trajectory": scores.trajectory_score * self.weights.trajectory_score,
            "behavior": scores.behavior_score * self.weights.behavior_score,
            "dna": scores.dna_score * self.weights.dna_score,
        }
        return contributions


class RankingEngine:
    """Main ranking engine for candidate scoring."""

    def __init__(self, weights: ScoringWeights = None):
        self.score_fusion = ScoreFusion(weights)

    def compute_final_score(
        self,
        candidate_id: str,
        semantic_score: float,
        authenticity_score: float,
        anomaly_score: float,
        trajectory_score: float,
        learning_velocity_score: float,
        production_score: float,
        behavior_score: float,
        dna: CandidateDNA,
    ) -> CandidateScores:
        """
        Compute final candidate scores.
        """
        # DNA score is average of all dimensions
        dna_score = sum([
            dna.technical_depth,
            dna.production_readiness,
            dna.startup_fit,
            dna.career_stability,
            dna.behavior_reliability,
            dna.authenticity,
            dna.learning_velocity,
        ]) / 7

        scores = CandidateScores(
            candidate_id=candidate_id,
            semantic_score=semantic_score,
            authenticity_score=authenticity_score,
            anomaly_score=anomaly_score,
            trajectory_score=trajectory_score,
            learning_velocity_score=learning_velocity_score,
            production_score=production_score,
            behavior_score=behavior_score,
            dna_score=dna_score,
            dna=dna,
            final_score=self.score_fusion.fuse_scores(CandidateScores(
                candidate_id=candidate_id,
                semantic_score=semantic_score,
                authenticity_score=authenticity_score,
                anomaly_score=anomaly_score,
                trajectory_score=trajectory_score,
                learning_velocity_score=learning_velocity_score,
                production_score=production_score,
                behavior_score=behavior_score,
                dna_score=dna_score,
                dna=dna,
                final_score=0.0,
            ))
        )

        return scores

    def rank_candidates(
        self,
        candidate_scores: List[CandidateScores],
    ) -> List[RankedCandidate]:
        """
        Rank candidates by final score.
        Returns sorted list with rank, strengths, and weaknesses.
        """
        # Sort by final score descending
        sorted_scores = sorted(candidate_scores, key=lambda x: x.final_score, reverse=True)

        ranked = []
        for rank, scores in enumerate(sorted_scores, start=1):
            # Extract strengths and weaknesses
            strengths = self._identify_strengths(scores)
            weaknesses = self._identify_weaknesses(scores)

            ranked_candidate = RankedCandidate(
                candidate_id=scores.candidate_id,
                rank=rank,
                semantic_score=scores.semantic_score,
                authenticity_score=scores.authenticity_score,
                trajectory_score=scores.trajectory_score,
                production_score=scores.production_score,
                behavior_score=scores.behavior_score,
                dna_score=scores.dna_score,
                final_score=scores.final_score,
                dna_dimensions=scores.dna,
                top_strengths=strengths,
                top_weaknesses=weaknesses,
            )

            ranked.append(ranked_candidate)

        return ranked

    @staticmethod
    def _identify_strengths(scores: CandidateScores) -> List[str]:
        """Identify top strengths."""
        strengths = []

        threshold = 70.0

        if scores.semantic_score >= threshold:
            strengths.append("Strong semantic match to job description")
        if scores.production_score >= threshold:
            strengths.append("Proven production engineering experience")
        if scores.trajectory_score >= threshold:
            strengths.append("Excellent career progression")
        if scores.behavior_score >= threshold:
            strengths.append("High engagement and availability")
        if scores.dna.technical_depth >= threshold:
            strengths.append("Strong technical depth")

        # DNA strengths
        dna = scores.dna
        if dna.production_readiness >= 75:
            strengths.append("Excellent production readiness")
        if dna.startup_fit >= 75:
            strengths.append("Great fit for fast-moving startup")
        if dna.career_stability >= 75:
            strengths.append("Demonstrates career stability")

        return strengths

    @staticmethod
    def _identify_weaknesses(scores: CandidateScores) -> List[str]:
        """Identify top weaknesses."""
        weaknesses = []

        threshold = 50.0

        if scores.authenticity_score < 50:
            weaknesses.append("Profile authenticity concerns")
        if scores.anomaly_score > 60:
            weaknesses.append("Anomalous profile signals detected")
        if scores.production_score < threshold:
            weaknesses.append("Limited production systems experience")
        if scores.trajectory_score < threshold:
            weaknesses.append("Inconsistent career trajectory")
        if scores.behavior_score < threshold:
            weaknesses.append("Low recruiter engagement signals")

        # DNA weaknesses
        dna = scores.dna
        if dna.research_orientation > 60:
            weaknesses.append("More research-oriented than product-focused")
        if dna.career_stability < 50:
            weaknesses.append("Pattern of frequent job changes")

        return weaknesses
