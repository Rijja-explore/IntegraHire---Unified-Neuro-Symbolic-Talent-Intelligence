"""
Canonical unified schemas for the entire pipeline.

This is the single source of truth for all data models used across retrieval,
intelligence, ranking, orchestration, reasoning, and export modules.

Data flow:
  JSONL → CandidateRawData
  → PreprocessedCandidate (retrieval preprocessing)
  → RetrievalResult (retrieval engine output)
  → CandidateFeatures (after intelligence engines)
  → RankedCandidate (final submission output)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BaseModelWithConfig(BaseModel):
    """Base model that disables protected namespace warnings."""
    model_config = {"protected_namespaces": ()}


# =============================================================================
# CORE ENTITIES
# =============================================================================

class Skill(BaseModelWithConfig):
    """A single skill with proficiency and endorsement information."""
    name: str
    proficiency: str = Field(
        default="intermediate",
        description="beginner, intermediate, advanced, expert"
    )
    endorsements: int = Field(default=0, ge=0)
    duration_months: int = Field(default=0, ge=0)


class Education(BaseModelWithConfig):
    """A single education entry."""
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: Optional[str] = Field(
        default=None,
        description="tier_1, tier_2, tier_3, tier_4, tier_5"
    )


class Experience(BaseModelWithConfig):
    """A single work experience entry."""
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    duration_months: int = Field(ge=0)
    is_current: bool
    industry: str
    company_size: str
    description: str


class Certification(BaseModelWithConfig):
    """A single certification."""
    name: str
    issuer: str
    year: int


class Language(BaseModelWithConfig):
    """A language proficiency."""
    language: str
    proficiency: str


class CandidateBasicProfile(BaseModelWithConfig):
    """Immutable basic profile information (from JSONL)."""
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float = Field(ge=0)
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str


class BehavioralSignals(BaseModelWithConfig):
    """All behavioral and engagement signals for a candidate."""
    profile_completeness_score: float = Field(ge=0, le=100)
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool
    profile_views_received_30d: int = Field(ge=0)
    applications_submitted_30d: int = Field(ge=0)
    recruiter_response_rate: float = Field(ge=0, le=1)
    avg_response_time_hours: float = Field(ge=0)
    skill_assessment_scores: Dict[str, float] = Field(default_factory=dict)
    connection_count: int = Field(ge=0)
    endorsements_received: int = Field(ge=0)
    notice_period_days: int = Field(ge=0)
    expected_salary_range_inr_lpa: Optional[Dict[str, float]] = None
    preferred_work_mode: str = ""
    willing_to_relocate: bool = False
    github_activity_score: float = Field(ge=0, le=100)
    search_appearance_30d: int = Field(ge=0)
    saved_by_recruiters_30d: int = Field(ge=0)
    interview_completion_rate: float = Field(ge=0, le=1)
    offer_acceptance_rate: float = Field(ge=0, le=1)
    verified_email: bool = False
    verified_phone: bool = False
    linkedin_connected: bool = False


# =============================================================================
# PIPELINE INPUT
# =============================================================================

class CandidateRawData(BaseModelWithConfig):
    """Raw candidate data as loaded from JSONL."""
    candidate_id: str
    profile: CandidateBasicProfile
    career_history: List[Experience]
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    behavioral_signals: Optional[BehavioralSignals] = None

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        """Validate candidate ID format."""
        if not v or not v.startswith("CAND_"):
            raise ValueError(f"Invalid candidate ID format: {v}")
        return v


# =============================================================================
# JOB DESCRIPTION
# =============================================================================

class JobDescription(BaseModelWithConfig):
    """Processed job description for retrieval and reasoning."""
    original_text: str
    cleaned_text: str
    embedding: Optional[List[float]] = None
    keywords: List[str] = Field(default_factory=list)
    key_responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# RETRIEVAL SUBSYSTEM
# =============================================================================

class PreprocessedCandidate(BaseModelWithConfig):
    """Candidate preprocessed and ready for retrieval."""
    candidate_id: str
    profile_text: str = Field(description="Rich text profile for semantic matching")
    raw_data: CandidateRawData
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModelWithConfig):
    """Output of retrieval engine for a single candidate."""
    candidate_id: str
    bm25_score: float = Field(ge=0, le=1, description="BM25 lexical score")
    bm25_rank: int = Field(ge=0, description="BM25 ranking position")
    embedding_score: float = Field(ge=0, le=1, description="Dense embedding score")
    embedding_rank: int = Field(ge=0, description="Dense retrieval ranking position")
    semantic_score: float = Field(ge=0, le=1, description="Final RRF-fused score")
    retrieval_rank: int = Field(ge=0, description="Final ranking position")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexMetadata(BaseModelWithConfig):
    """Metadata about a search index."""
    num_candidates: int
    created_at: str
    model_name: Optional[str] = None
    index_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# INTELLIGENCE SUBSYSTEM
# =============================================================================

class CandidateDNA(BaseModelWithConfig):
    """Candidate DNA dimensions (0-100 scale)."""
    technical_depth: float = Field(ge=0, le=100)
    production_readiness: float = Field(ge=0, le=100)
    research_orientation: float = Field(ge=0, le=100)
    startup_fit: float = Field(ge=0, le=100)
    career_stability: float = Field(ge=0, le=100)
    behavior_reliability: float = Field(ge=0, le=100)
    authenticity: float = Field(ge=0, le=100)
    learning_velocity: float = Field(ge=0, le=100)


class CandidateFeatures(BaseModelWithConfig):
    """All computed features for a candidate (output of intelligence engines)."""
    candidate_id: str

    # Retrieval features
    semantic_score: float = Field(ge=0, le=1)

    # Intelligence engine outputs
    authenticity_score: float = Field(ge=0, le=100)
    anomaly_score: float = Field(ge=0, le=100)
    trajectory_score: float = Field(ge=0, le=100)
    learning_velocity_score: float = Field(ge=0, le=100)
    production_score: float = Field(ge=0, le=100)
    behavior_score: float = Field(ge=0, le=100)

    # DNA dimensions
    dna: CandidateDNA
    dna_score: float = Field(ge=0, le=100)

    # Final combined score
    final_score: float = Field(ge=0, le=1)

    # Interpretability
    top_strengths: List[str] = Field(default_factory=list)
    top_weaknesses: List[str] = Field(default_factory=list)


# =============================================================================
# FINAL SUBMISSION
# =============================================================================

class RankedCandidate(BaseModelWithConfig):
    """Final ranked candidate for submission."""
    candidate_id: str
    rank: int = Field(ge=1, le=100)

    # All scores for transparency
    semantic_score: float = Field(ge=0, le=1)
    authenticity_score: float = Field(ge=0, le=100)
    trajectory_score: float = Field(ge=0, le=100)
    production_score: float = Field(ge=0, le=100)
    behavior_score: float = Field(ge=0, le=100)
    dna_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=1)

    # DNA for transparency
    dna_dimensions: CandidateDNA

    # Reasoning
    reasoning: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)

    # Interpretability
    top_strengths: List[str] = Field(default_factory=list)
    top_weaknesses: List[str] = Field(default_factory=list)


class CandidateRecord(BaseModelWithConfig):
    """
    CandidateRecord represents a merged candidate record during orchestrator pipeline processing.
    It supports both attribute access (.field) and subscript item access (["field"])
    to maintain backward compatibility with old tests and pipeline parts.
    """
    candidate_id: str
    semantic_score: float = Field(default=0.0)
    authenticity_score: float = Field(default=0.0)
    trajectory_score: float = Field(default=0.0)
    behavior_score: float = Field(default=0.0)
    production_score: float = Field(default=0.0)
    final_score: float = Field(default=0.0)
    dna_score: float = Field(default=0.0)
    reasoning: Optional[str] = Field(default=None)
    confidence: Optional[float] = Field(default=None)

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


# Audit aliases for canonical model names used in documentation
CandidateScore = CandidateFeatures
FinalCandidate = RankedCandidate

