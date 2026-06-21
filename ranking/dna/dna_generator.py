"""Candidate DNA generation and dimension scoring."""
from ..schemas import CandidateProfile, CandidateDNA
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class CandidateDNAGenerator:
    """Generate candidate DNA dimensions based on overall profile."""

    @staticmethod
    def calculate_technical_depth(
        production_score: float,
        trajectory_score: float,
        learning_velocity_score: float,
    ) -> float:
        """
        Calculate technical depth dimension.
        High = deep ML systems expertise
        """
        depth = (
            (production_score * 0.5) +
            (trajectory_score * 0.3) +
            (learning_velocity_score * 0.2)
        )
        return min(100, max(0, depth))

    @staticmethod
    def calculate_production_readiness(
        production_score: float,
        behavior_score: float,
        trajectory_score: float,
    ) -> float:
        """
        Calculate production readiness dimension.
        High = ships working systems, not just research
        """
        readiness = (
            (production_score * 0.6) +
            (behavior_score * 0.2) +
            (trajectory_score * 0.2)
        )
        return min(100, max(0, readiness))

    @staticmethod
    def calculate_research_orientation(
        candidate: CandidateProfile,
    ) -> float:
        """
        Calculate research orientation dimension.
        High = academic/research background
        Lower = better for shipper roles
        """
        # Look for research indicators
        research_keywords = {"research", "phd", "publication", "paper", "academic", "lab"}
        research_penalty = 0.0

        summary_lower = candidate.profile.summary.lower()
        for keyword in research_keywords:
            if keyword in summary_lower:
                research_penalty += 15

        # Check for pure academic background
        for edu in candidate.education:
            if "phd" in edu.degree.lower():
                research_penalty += 20
            if edu.tier in ["tier_4", "tier_5"]:  # Tier 4-5 less likely to have strong production
                research_penalty += 5

        # Check for production signals (reduce research score)
        production_signals = {"deployed", "shipped", "production", "scale", "users", "real"}
        for signal in production_signals:
            if signal in summary_lower:
                research_penalty -= 10

        research_score = min(100, max(0, 50 + research_penalty))
        return 100 - research_score  # Invert: lower research = higher score for this role

    @staticmethod
    def calculate_startup_fit(
        behavior_score: float,
        learning_velocity_score: float,
        trajectory_score: float,
    ) -> float:
        """
        Calculate startup fit dimension.
        High = comfortable with ambiguity, learning, fast-moving environments
        """
        startup_fit = (
            (behavior_score * 0.3) +
            (learning_velocity_score * 0.4) +
            (trajectory_score * 0.3)
        )
        return min(100, max(0, startup_fit))

    @staticmethod
    def calculate_career_stability(
        candidate: CandidateProfile,
    ) -> float:
        """
        Calculate career stability dimension.
        High = stays at companies, doesn't job-hop
        """
        if not candidate.career_history:
            return 50.0

        # Calculate average tenure
        total_months = sum(e.duration_months for e in candidate.career_history if e.duration_months > 0)
        num_jobs = len(candidate.career_history)

        if num_jobs == 0:
            return 50.0

        avg_tenure = total_months / num_jobs

        # Score based on average tenure
        if avg_tenure >= 36:  # 3+ years average
            stability = 100.0
        elif avg_tenure >= 24:  # 2+ years
            stability = 85.0
        elif avg_tenure >= 12:  # 1+ years
            stability = 70.0
        elif avg_tenure >= 6:  # 6+ months
            stability = 50.0
        else:
            stability = 30.0

        # Penalty for job-hopping pattern
        short_stints = sum(1 for e in candidate.career_history if e.duration_months < 6)
        if short_stints >= 2:
            stability -= (short_stints * 10)

        return min(100, max(0, stability))

    @staticmethod
    def calculate_behavior_reliability(
        behavior_score: float,
    ) -> float:
        """
        Calculate behavior reliability dimension.
        Direct measure of recruiter interaction quality
        """
        return behavior_score

    @staticmethod
    def calculate_authenticity(
        authenticity_score: float,
    ) -> float:
        """
        Calculate authenticity dimension.
        Direct measure of profile authenticity
        """
        return authenticity_score

    @staticmethod
    def calculate_learning_velocity(
        learning_velocity_score: float,
    ) -> float:
        """
        Calculate learning velocity dimension.
        Direct measure of ability to acquire new skills
        """
        return learning_velocity_score

    @staticmethod
    def generate_dna(
        candidate: CandidateProfile,
        authenticity_score: float,
        trajectory_score: float,
        learning_velocity_score: float,
        production_score: float,
        behavior_score: float,
    ) -> CandidateDNA:
        """
        Generate complete candidate DNA profile.
        """
        dna = CandidateDNA(
            technical_depth=CandidateDNAGenerator.calculate_technical_depth(
                production_score, trajectory_score, learning_velocity_score
            ),
            production_readiness=CandidateDNAGenerator.calculate_production_readiness(
                production_score, behavior_score, trajectory_score
            ),
            research_orientation=CandidateDNAGenerator.calculate_research_orientation(candidate),
            startup_fit=CandidateDNAGenerator.calculate_startup_fit(
                behavior_score, learning_velocity_score, trajectory_score
            ),
            career_stability=CandidateDNAGenerator.calculate_career_stability(candidate),
            behavior_reliability=CandidateDNAGenerator.calculate_behavior_reliability(behavior_score),
            authenticity=CandidateDNAGenerator.calculate_authenticity(authenticity_score),
            learning_velocity=CandidateDNAGenerator.calculate_learning_velocity(learning_velocity_score),
        )
        return dna
