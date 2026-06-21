"""Main authenticity engine."""
from ..schemas import CandidateProfile
from .timeline_validator import TimelineValidator
from .skill_consistency import SkillConsistency
from .anomaly_detector import AnomalyDetector
from .honeypot_detector import HoneypotDetector
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)

class AuthenticityEngine:
    """Evaluate candidate authenticity and detect suspicious profiles."""

    def __init__(self, anomaly_contamination: float = 0.05):
        """Initialize authenticity engine."""
        self.timeline_validator = TimelineValidator()
        self.skill_consistency = SkillConsistency()
        self.anomaly_detector = AnomalyDetector(contamination=anomaly_contamination)
        self.honeypot_detector = HoneypotDetector()

    def fit(self, candidates: List[CandidateProfile]):
        """Fit anomaly detector on candidate pool."""
        self.anomaly_detector.fit(candidates)

    def evaluate(self, candidate: CandidateProfile) -> Tuple[float, float, Dict[str, any]]:
        """
        Evaluate candidate authenticity.

        Returns:
            - authenticity_score (0-100)
            - anomaly_score (0-100)
            - detailed_analysis (dict with breakdown)
        """
        analysis = {
            "candidate_id": candidate.candidate_id,
            "timeline_issues": [],
            "skill_issues": [],
            "anomaly_signals": [],
        }

        score = 100.0

        # 1. Timeline validation
        timeline_penalty, timeline_issues = self.timeline_validator.validate_timeline(
            candidate.career_history
        )
        consistency_penalty, consistency_issues = self.timeline_validator.check_career_consistency(
            candidate.career_history
        )
        timeline_penalty += consistency_penalty
        analysis["timeline_issues"] = timeline_issues + consistency_issues
        score -= timeline_penalty

        # 2. Skill consistency
        skill_consistency_score = self.skill_consistency.calculate_skill_consistency_score(
            candidate.skills, candidate.career_history
        )
        skill_penalty = 100 - skill_consistency_score
        score = score * (skill_consistency_score / 100)
        analysis["skill_consistency_score"] = skill_consistency_score

        # 3. Anomaly detection
        anomaly_score, is_anomaly = self.anomaly_detector.predict(candidate)

        if is_anomaly:
            analysis["anomaly_signals"].append(f"Detected as anomaly (score: {anomaly_score:.1f})")
            score *= (100 - anomaly_score) / 100

        # 4. Honeypot / trap profile detection
        honeypot_penalty, honeypot_issues = self.honeypot_detector.evaluate(candidate)
        if honeypot_issues:
            analysis["honeypot_issues"] = honeypot_issues
            score = max(0.0, score - honeypot_penalty)

        # Floor score
        final_authenticity_score = max(0, min(100, score))

        analysis["timeline_penalty"] = timeline_penalty
        analysis["skill_penalty"] = skill_penalty
        analysis["anomaly_score"] = anomaly_score
        analysis["is_anomaly"] = is_anomaly
        analysis["final_score"] = final_authenticity_score

        return final_authenticity_score, anomaly_score, analysis
