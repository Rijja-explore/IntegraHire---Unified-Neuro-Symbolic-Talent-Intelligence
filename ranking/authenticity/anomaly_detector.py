"""Anomaly detection for suspicious candidate profiles."""
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Tuple, List, Dict
from ..schemas import CandidateProfile
import logging

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Detect anomalous candidate profiles using Isolation Forest."""

    def __init__(self, contamination: float = 0.1):
        """Initialize anomaly detector."""
        self.contamination = contamination
        self.model = None
        self.feature_names = [
            "years_of_experience",
            "num_jobs",
            "avg_job_duration_months",
            "skill_endorsement_ratio",
            "skill_duration_consistency",
            "profile_completeness",
            "education_year_gap",
            "recent_activity_score",
            "total_endorsements",
            "connection_count_log",
        ]

    def extract_features(self, candidate: CandidateProfile) -> np.ndarray:
        """Extract features for anomaly detection."""
        features = []

        # 1. Years of experience
        years_exp = candidate.profile.years_of_experience
        features.append(years_exp)

        # 2. Number of jobs
        num_jobs = len(candidate.career_history)
        features.append(num_jobs)

        # 3. Average job duration
        if num_jobs > 0:
            avg_duration = np.mean([e.duration_months for e in candidate.career_history])
        else:
            avg_duration = 0
        features.append(avg_duration)

        # 4. Skill endorsement ratio (endorsements per skill)
        num_skills = len(candidate.skills)
        if num_skills > 0:
            total_endorsements = sum(s.endorsements for s in candidate.skills)
            endorsement_ratio = total_endorsements / num_skills
        else:
            endorsement_ratio = 0
        features.append(endorsement_ratio)

        # 5. Skill duration consistency (std dev of skill durations)
        if num_skills > 1:
            skill_durations = [s.duration_months for s in candidate.skills]
            duration_consistency = np.std(skill_durations)
        else:
            duration_consistency = 0
        features.append(duration_consistency)

        # 6. Profile completeness
        completeness = candidate.redrob_signals.profile_completeness_score
        features.append(completeness)

        # 7. Education year gap (inconsistency between education and experience start)
        if candidate.education:
            latest_edu_year = max(e.end_year for e in candidate.education)
            earliest_job_date = None
            if candidate.career_history:
                from datetime import datetime
                dates = []
                for e in candidate.career_history:
                    try:
                        d = datetime.strptime(e.start_date, "%Y-%m-%d")
                        dates.append(d.year)
                    except:
                        pass
                earliest_job_date = min(dates) if dates else None

            if earliest_job_date:
                edu_job_gap = earliest_job_date - latest_edu_year
            else:
                edu_job_gap = 0
        else:
            edu_job_gap = 0
        features.append(edu_job_gap)

        # 8. Recent activity score (recency of last login)
        from datetime import datetime
        try:
            last_active = datetime.strptime(candidate.redrob_signals.last_active_date, "%Y-%m-%d")
            days_since_active = (datetime.now() - last_active).days
            recent_activity = max(0, 100 - (days_since_active / 3))  # 0-100 scale, decays every 3 days
        except:
            recent_activity = 0
        features.append(recent_activity)

        # 9. Total endorsements
        total_endorsements = sum(s.endorsements for s in candidate.skills)
        features.append(total_endorsements)

        # 10. Connection count (log scale)
        conn_count = max(1, candidate.redrob_signals.connection_count)
        features.append(np.log1p(conn_count))

        return np.array(features, dtype=np.float32)

    def fit(self, candidates: List[CandidateProfile]):
        """Fit the anomaly detector on a batch of candidates."""
        X = np.array([self.extract_features(c) for c in candidates], dtype=np.float32)

        # Standardize features
        self.X_mean = np.mean(X, axis=0)
        self.X_std = np.std(X, axis=0)
        self.X_std[self.X_std == 0] = 1  # Avoid division by zero

        X_normalized = (X - self.X_mean) / self.X_std

        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_normalized)
        logger.info(f"Anomaly detector fitted on {len(candidates)} candidates")

    def predict(self, candidate: CandidateProfile) -> Tuple[float, bool]:
        """
        Predict anomaly score for a candidate.

        Returns: (anomaly_score (0-100), is_anomaly (bool))
        """
        if self.model is None:
            logger.warning("Model not fitted, returning neutral score")
            return 50.0, False

        features = self.extract_features(candidate)
        X_normalized = (features - self.X_mean) / self.X_std

        # Get anomaly score from Isolation Forest
        # predict() returns -1 for anomalies, 1 for normal
        # anomaly_score() returns raw score
        raw_score = self.model.score_samples(X_normalized.reshape(1, -1))[0]

        # Normalize to 0-100 scale (higher = more anomalous)
        # Raw scores are typically in range [-1, 1] or wider
        anomaly_score = 50 + (raw_score * 25)  # Map to ~0-100 range
        anomaly_score = max(0, min(100, anomaly_score))

        is_anomaly = anomaly_score > 70

        return float(anomaly_score), is_anomaly
