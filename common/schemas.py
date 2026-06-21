"""
COMPATIBILITY SHIM: Re-exports from unified locations.
This file allows old imports (from common, retrieval, ranking config) to work
while the actual implementations have been consolidated into src/common/.

Gradual migration: New code uses src.common.*, old code can still use common.*
"""

# Re-export schemas from unified location
from src.common.schemas import (
    Skill,
    Education,
    Experience,
    Certification,
    Language,
    CandidateBasicProfile,
    BehavioralSignals,
    CandidateRawData,
    JobDescription,
    PreprocessedCandidate,
    RetrievalResult,
    IndexMetadata,
    CandidateDNA,
    CandidateFeatures,
    RankedCandidate,
    CandidateRecord,
)

__all__ = [
    "Skill",
    "Education",
    "Experience",
    "Certification",
    "Language",
    "CandidateBasicProfile",
    "BehavioralSignals",
    "CandidateRawData",
    "JobDescription",
    "PreprocessedCandidate",
    "RetrievalResult",
    "IndexMetadata",
    "CandidateDNA",
    "CandidateFeatures",
    "RankedCandidate",
    "CandidateRecord",
]
