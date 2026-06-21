"""
Compatibility shim for retrieval schemas.

Canonical models live in ``src.common.schemas``. This module re-exports them
with retrieval-specific aliases and request/response types.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from src.common.schemas import (
    BaseModelWithConfig,
    CandidateBasicProfile,
    CandidateRawData,
    Education,
    Experience,
    IndexMetadata,
    JobDescription,
    PreprocessedCandidate,
    RetrievalResult,
    Skill,
)

# Backward-compatible aliases used by retrieval modules
SkillRecord = Skill
EducationRecord = Education
CareerEntry = Experience
CandidateProfile = CandidateBasicProfile
CandidateRecord = PreprocessedCandidate

__all__ = [
    "SkillRecord",
    "EducationRecord",
    "CareerEntry",
    "CandidateProfile",
    "CandidateRawData",
    "CandidateRecord",
    "RetrievalResult",
    "JobDescription",
    "IndexMetadata",
    "RetrievalRequest",
    "RetrievalResponse",
]


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
