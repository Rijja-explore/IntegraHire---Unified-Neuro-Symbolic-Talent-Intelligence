"""Feature store and candidate processing pipeline."""
from .schemas import CandidateProfile, CandidateScores, FeatureVector, RankedCandidate
from .authenticity.authenticity_engine import AuthenticityEngine
from .trajectory.trajectory_engine import TrajectoryEngine
from .production.production_engine import ProductionEngine
from .behavior.behavioral_engine import BehavioralEngine
from .dna.dna_generator import CandidateDNAGenerator
from .ranking.ranking_engine import RankingEngine
from .config import DEFAULT_SCORING_WEIGHTS
from typing import List, Dict, Tuple, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FeatureStore:
    """Store and manage computed features for candidates."""

    def __init__(self):
        self.features: Dict[str, FeatureVector] = {}
        self.scores: Dict[str, CandidateScores] = {}

    def store_features(self, feature_vector: FeatureVector):
        """Store feature vector."""
        self.features[feature_vector.candidate_id] = feature_vector

    def store_scores(self, scores: CandidateScores):
        """Store computed scores."""
        self.scores[scores.candidate_id] = scores

    def get_features(self, candidate_id: str) -> Optional[FeatureVector]:
        """Retrieve feature vector."""
        return self.features.get(candidate_id)

    def get_scores(self, candidate_id: str) -> Optional[CandidateScores]:
        """Retrieve scores."""
        return self.scores.get(candidate_id)

    def to_dict(self) -> Dict:
        """Export to dictionary."""
        return {
            "num_features": len(self.features),
            "num_scores": len(self.scores),
            "candidates": list(self.scores.keys()),
        }


class CandidateRankingPipeline:
    """End-to-end candidate ranking pipeline."""

    def __init__(self, scoring_weights=None):
        self.authenticity_engine = AuthenticityEngine()
        self.trajectory_engine = TrajectoryEngine()
        self.production_engine = ProductionEngine()
        self.behavior_engine = BehavioralEngine()
        self.ranking_engine = RankingEngine(weights=scoring_weights or DEFAULT_SCORING_WEIGHTS)
        self.feature_store = FeatureStore()

    def fit(self, candidates: List[CandidateProfile]):
        """Fit engines on candidate pool."""
        logger.info(f"Fitting engines on {len(candidates)} candidates...")
        self.authenticity_engine.fit(candidates)
        logger.info("Authenticity engine fitted")

    def process_candidate(
        self,
        candidate: CandidateProfile,
        semantic_score: float,
    ) -> CandidateScores:
        """
        Process single candidate through all engines.

        Args:
            candidate: Candidate profile
            semantic_score: Semantic similarity score from retrieval (0-100)

        Returns:
            CandidateScores with all dimensions
        """
        candidate_id = candidate.candidate_id
        start_time = datetime.now()

        # 1. Authenticity
        auth_score, anomaly_score, auth_analysis = self.authenticity_engine.evaluate(candidate)

        # 2. Trajectory
        traj_score, learning_vel_score, traj_analysis = self.trajectory_engine.evaluate(candidate)

        # 3. Production
        prod_score, prod_analysis = self.production_engine.evaluate(candidate)

        # 4. Behavior
        behav_score, behav_analysis = self.behavior_engine.evaluate(candidate)

        # 5. DNA
        dna = CandidateDNAGenerator.generate_dna(
            candidate,
            authenticity_score=auth_score,
            trajectory_score=traj_score,
            learning_velocity_score=learning_vel_score,
            production_score=prod_score,
            behavior_score=behav_score,
        )

        # 6. Final score
        scores = self.ranking_engine.compute_final_score(
            candidate_id=candidate_id,
            semantic_score=semantic_score,
            authenticity_score=auth_score,
            anomaly_score=anomaly_score,
            trajectory_score=traj_score,
            learning_velocity_score=learning_vel_score,
            production_score=prod_score,
            behavior_score=behav_score,
            dna=dna,
        )

        # Store
        self.feature_store.store_scores(scores)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.debug(
            f"Processed {candidate_id} in {elapsed:.2f}s: "
            f"final_score={scores.final_score:.1f}"
        )

        return scores

    def process_batch(
        self,
        candidates: List[CandidateProfile],
        semantic_scores: Dict[str, float],
    ) -> List[CandidateScores]:
        """
        Process batch of candidates.

        Args:
            candidates: List of candidate profiles
            semantic_scores: Dict mapping candidate_id -> semantic_score

        Returns:
            List of CandidateScores for all candidates
        """
        logger.info(f"Processing batch of {len(candidates)} candidates...")
        start_time = datetime.now()

        all_scores = []
        for candidate in candidates:
            semantic_score = semantic_scores.get(candidate.candidate_id, 50.0)
            scores = self.process_candidate(candidate, semantic_score)
            all_scores.append(scores)

        elapsed = (datetime.now() - start_time).total_seconds()
        throughput = len(candidates) / elapsed if elapsed > 0 else 0
        logger.info(
            f"Processed batch in {elapsed:.2f}s ({throughput:.1f} candidates/sec)"
        )

        return all_scores

    def rank(self, candidate_scores: List[CandidateScores]) -> List[RankedCandidate]:
        """Rank candidates by final score."""
        return self.ranking_engine.rank_candidates(candidate_scores)

    def explain_score(
        self,
        candidate_id: str,
    ) -> Dict:
        """Explain a candidate's score."""
        scores = self.feature_store.get_scores(candidate_id)
        if not scores:
            return {"error": f"No scores found for {candidate_id}"}

        contributions = self.ranking_engine.score_fusion.explain_score(scores)

        return {
            "candidate_id": candidate_id,
            "final_score": scores.final_score,
            "score_components": {
                "semantic_score": scores.semantic_score,
                "authenticity_score": scores.authenticity_score,
                "trajectory_score": scores.trajectory_score,
                "production_score": scores.production_score,
                "behavior_score": scores.behavior_score,
                "dna_score": scores.dna_score,
            },
            "score_contributions": contributions,
            "dna_dimensions": {
                "technical_depth": scores.dna.technical_depth,
                "production_readiness": scores.dna.production_readiness,
                "research_orientation": scores.dna.research_orientation,
                "startup_fit": scores.dna.startup_fit,
                "career_stability": scores.dna.career_stability,
                "behavior_reliability": scores.dna.behavior_reliability,
                "authenticity": scores.dna.authenticity,
                "learning_velocity": scores.dna.learning_velocity,
            },
        }
