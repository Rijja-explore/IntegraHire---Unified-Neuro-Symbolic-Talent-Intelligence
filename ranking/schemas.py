"""
Compatibility shim for intelligence/ranking schemas.

Canonical base models live in ``src.common.schemas``. Ranking-specific
containers (``CandidateProfile``, ``CandidateScores``) remain here because
they use the legacy ``redrob_signals`` field name and 0-100 score scales.
"""

from typing import Dict, List, Optional

from pydantic import Field, model_validator

from src.common.schemas import (
    BaseModelWithConfig,
    BehavioralSignals,
    CandidateBasicProfile,
    CandidateDNA,
    Certification,
    Education,
    Experience,
    Language,
    RankedCandidate,
    Skill,
)

Profile = CandidateBasicProfile


class CandidateProfile(BaseModelWithConfig):
    """Complete candidate profile for intelligence engines."""

    candidate_id: str
    profile: Profile
    career_history: List[Experience]
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    behavioral_signals: BehavioralSignals = Field(..., alias="redrob_signals")

    model_config = {"protected_namespaces": (), "populate_by_name": True}

    @property
    def redrob_signals(self) -> BehavioralSignals:
        """Legacy alias for behavioral signals."""
        return self.behavioral_signals

    @model_validator(mode="before")
    @classmethod
    def _normalize_signal_field(cls, data):
        if isinstance(data, dict) and "redrob_signals" in data and "behavioral_signals" not in data:
            data = dict(data)
            data["behavioral_signals"] = data.pop("redrob_signals")
        return data


class CandidateScores(BaseModelWithConfig):
    """All scoring dimensions for a candidate (intelligence engine output)."""

    candidate_id: str
    semantic_score: float
    authenticity_score: float
    anomaly_score: float
    trajectory_score: float
    learning_velocity_score: float
    production_score: float
    behavior_score: float
    dna_score: float
    final_score: float
    dna: CandidateDNA


class FeatureVector(BaseModelWithConfig):
    """Feature vector for a candidate."""

    candidate_id: str
    features: List[float]
    feature_names: List[str]


__all__ = [
    "Skill",
    "Experience",
    "Education",
    "Certification",
    "Language",
    "BehavioralSignals",
    "Profile",
    "CandidateProfile",
    "CandidateDNA",
    "CandidateScores",
    "RankedCandidate",
    "FeatureVector",
]
