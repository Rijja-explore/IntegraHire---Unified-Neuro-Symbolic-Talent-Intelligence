"""Behavioral and recruitability scoring."""
from ..schemas import CandidateProfile, BehavioralSignals
from typing import Dict, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BehavioralEngine:
    """Evaluate candidate behavioral quality and recruitability."""

    @staticmethod
    def calculate_activity_recency(last_active_date: str, days_threshold: int = 180) -> Tuple[float, str]:
        """
        Calculate activity recency score.
        Returns: (score 0-100, status)
        """
        try:
            last_active = datetime.strptime(last_active_date, "%Y-%m-%d")
            days_since_active = (datetime.now() - last_active).days

            if days_since_active < 7:
                return 100.0, "very_active"
            elif days_since_active < 30:
                return 85.0, "active"
            elif days_since_active < 90:
                return 60.0, "moderately_active"
            elif days_since_active < 180:
                return 40.0, "inactive"
            else:
                return 20.0, "dormant"
        except:
            return 0.0, "unknown"

    @staticmethod
    def calculate_engagement_score(signals: BehavioralSignals) -> float:
        """
        Calculate engagement score based on recruiter interactions.
        Returns: score (0-100)
        """
        # Normalize components (0-1 scale)
        response_rate = signals.recruiter_response_rate  # Already 0-1
        open_to_work = 1.0 if signals.open_to_work_flag else 0.0

        # Interview completion rate (0-1)
        interview_rate = min(1.0, signals.interview_completion_rate)

        # Offer acceptance rate (0-1, -1 means unknown)
        offer_rate = max(0, signals.offer_acceptance_rate) if signals.offer_acceptance_rate >= 0 else 0.5

        # Application activity
        apps_last_30d = min(1.0, signals.applications_submitted_30d / 5)  # 5+ apps = max

        # Saved by recruiters (indicator of attractiveness)
        saved_score = min(1.0, signals.saved_by_recruiters_30d / 3)  # 3+ = max

        # Response time (lower is better, normalize)
        response_time_score = max(0, 1.0 - (signals.avg_response_time_hours / 168))  # 1 week = cutoff

        # Profile completeness
        profile_complete = signals.profile_completeness_score / 100

        # Combine
        engagement = (
            (response_rate * 0.25) +
            (open_to_work * 0.15) +
            (interview_rate * 0.15) +
            (offer_rate * 0.1) +
            (apps_last_30d * 0.1) +
            (saved_score * 0.1) +
            (response_time_score * 0.1) +
            (profile_complete * 0.05)
        ) * 100

        return min(100, max(0, engagement))

    @staticmethod
    def calculate_reliability_score(signals: BehavioralSignals) -> float:
        """
        Calculate reliability score based on verification and communication.
        Returns: score (0-100)
        """
        verified_email = 1.0 if signals.verified_email else 0.0
        verified_phone = 1.0 if signals.verified_phone else 0.0
        linkedin_connected = 1.0 if signals.linkedin_connected else 0.5

        # Connection network as proxy for legitimacy
        connection_score = min(1.0, signals.connection_count / 500)  # 500+ = max

        reliability = (
            (verified_email * 0.3) +
            (verified_phone * 0.2) +
            (linkedin_connected * 0.2) +
            (connection_score * 0.3)
        ) * 100

        return min(100, max(0, reliability))

    @staticmethod
    def calculate_availability_score(signals: BehavioralSignals) -> float:
        """
        Calculate availability based on notice period and job market signals.
        Returns: score (0-100)
        """
        # Notice period penalty (prefer short notice)
        if signals.notice_period_days <= 7:
            notice_score = 100.0
        elif signals.notice_period_days <= 30:
            notice_score = 80.0
        elif signals.notice_period_days <= 60:
            notice_score = 60.0
        elif signals.notice_period_days <= 90:
            notice_score = 40.0
        else:
            notice_score = 20.0

        # Activity level
        activity_score, _ = BehavioralEngine.calculate_activity_recency(
            signals.last_active_date
        )

        # Job market signals
        search_signal = min(1.0, signals.search_appearance_30d / 100)  # 100+ = max
        saved_signal = min(1.0, signals.saved_by_recruiters_30d / 5)

        availability = (
            (notice_score * 0.4) +
            (activity_score * 0.3) +
            (search_signal * 0.15) +
            (saved_signal * 0.15)
        )

        return min(100, max(0, availability))

    @staticmethod
    def calculate_technical_validation_score(signals: BehavioralSignals) -> float:
        """
        Calculate technical validation based on assessment scores and GitHub activity.
        Returns: score (0-100)
        """
        # Skill assessments
        if signals.skill_assessment_scores:
            avg_assessment = sum(signals.skill_assessment_scores.values()) / len(
                signals.skill_assessment_scores
            )
        else:
            avg_assessment = 50.0  # Neutral if no assessments

        # GitHub activity
        github_score = max(0, min(100, signals.github_activity_score * 10)) if signals.github_activity_score >= 0 else 0.0

        validation = (avg_assessment * 0.6) + (github_score * 0.4)
        return min(100, max(0, validation))

    def evaluate(self, candidate: CandidateProfile) -> Tuple[float, Dict]:
        """
        Evaluate behavioral quality.

        Returns:
            - behavior_score (0-100)
            - detailed_analysis (dict)
        """
        signals = candidate.redrob_signals

        analysis = {
            "candidate_id": candidate.candidate_id,
            "engagement_score": 0.0,
            "reliability_score": 0.0,
            "availability_score": 0.0,
            "technical_validation_score": 0.0,
            "activity_status": "unknown",
            "final_score": 0.0,
        }

        # Calculate component scores
        engagement = self.calculate_engagement_score(signals)
        reliability = self.calculate_reliability_score(signals)
        availability = self.calculate_availability_score(signals)
        technical_validation = self.calculate_technical_validation_score(signals)
        activity_recency, activity_status = self.calculate_activity_recency(
            signals.last_active_date
        )

        analysis["engagement_score"] = engagement
        analysis["reliability_score"] = reliability
        analysis["availability_score"] = availability
        analysis["technical_validation_score"] = technical_validation
        analysis["activity_recency_score"] = activity_recency
        analysis["activity_status"] = activity_status

        # Combine with weights
        behavior_score = (
            (engagement * 0.35) +
            (reliability * 0.2) +
            (availability * 0.25) +
            (technical_validation * 0.1) +
            (activity_recency * 0.1)
        )

        # Heavy penalty if dormant
        if activity_status == "dormant":
            behavior_score *= 0.5

        analysis["final_score"] = min(100, max(0, behavior_score))

        return analysis["final_score"], analysis
