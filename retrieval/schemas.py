"""
Pydantic schemas for the retrieval subsystem.

Defines data models with validation for candidates, job descriptions, and retrieval results.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Use a base model that disables protected namespace checks to avoid
# warnings about fields like "model_name" conflicting with protected prefixes.
class BaseModelWithConfig(BaseModel):
    model_config = {"protected_namespaces": ()}


class SkillRecord(BaseModelWithConfig):
    """Represents a single skill with proficiency information."""

    name: str
    proficiency: str  # basic, intermediate, advanced
    endorsements: int = 0
    duration_months: int = 0


class EducationRecord(BaseModelWithConfig):
    """Represents a single education entry."""

    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: Optional[str] = None


class CareerEntry(BaseModelWithConfig):
    """Represents a single career/work experience entry."""

    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str


class CandidateProfile(BaseModelWithConfig):
    """Represents the basic profile information of a candidate."""

    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str


class CandidateRawData(BaseModelWithConfig):
    """Raw candidate data as it comes from the JSONL file."""

    candidate_id: str
    profile: CandidateProfile
    career_history: List[CareerEntry]
    education: List[EducationRecord] = []
    skills: List[SkillRecord] = []

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        """Validate candidate ID format."""
        if not v.startswith("CAND_"):
            raise ValueError(f"Invalid candidate ID format: {v}")
        return v


class CandidateRecord(BaseModelWithConfig):
    """
    Processed candidate record ready for retrieval.

    Contains aggregated profile text optimized for semantic understanding.
    """

    candidate_id: str
    profile_text: str = Field(..., description="Rich text profile for semantic matching")
    raw_data: CandidateRawData = Field(..., description="Original candidate data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class RetrievalResult(BaseModelWithConfig):
    """Result of a single candidate retrieval."""

    candidate_id: str
    bm25_score: float = Field(..., description="BM25 lexical relevance score (0-1)")
    bm25_rank: int = Field(..., description="BM25 ranking position")
    embedding_score: float = Field(..., description="Dense embedding cosine similarity (0-1)")
    embedding_rank: int = Field(..., description="Dense retrieval ranking position")
    semantic_score: float = Field(..., description="Final RRF-fused semantic score (0-1)")
    retrieval_rank: int = Field(..., description="Final ranking position")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RetrievalRequest(BaseModelWithConfig):
    """Request to retrieve candidates for a job."""

    job_description: str
    job_description_embedding: Optional[List[float]] = None
    top_k: int = 100
    min_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModelWithConfig):
    """Response containing retrieved candidates."""

    job_description: str
    candidates: List[RetrievalResult]
    total_candidates_searched: int
    retrieval_latency_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobDescription(BaseModelWithConfig):
    """Processed job description for retrieval."""

    original_text: str
    cleaned_text: str
    embedding: Optional[List[float]] = None
    keywords: List[str] = Field(default_factory=list)
    key_responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexMetadata(BaseModelWithConfig):
    """Metadata about an index (BM25 or FAISS)."""

    num_candidates: int
    created_at: str
    model_name: Optional[str] = None
    index_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
