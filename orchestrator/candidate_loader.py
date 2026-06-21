"""Load and convert candidate records from JSONL for the intelligence pipeline."""

from __future__ import annotations

import json
import logging
from typing import Dict, Iterable, List, Set

from ranking.schemas import (
    BehavioralSignals,
    CandidateProfile,
    Certification,
    Education,
    Experience,
    Language,
    Profile,
    Skill,
)
from src.common.normalizer import normalize_candidate_record

logger = logging.getLogger(__name__)

_DEFAULT_SIGNALS = {
    "profile_completeness_score": 50.0,
    "signup_date": "2020-01-01",
    "last_active_date": "2020-01-01",
    "open_to_work_flag": False,
    "profile_views_received_30d": 0,
    "applications_submitted_30d": 0,
    "recruiter_response_rate": 0.0,
    "avg_response_time_hours": 168.0,
    "skill_assessment_scores": {},
    "connection_count": 0,
    "endorsements_received": 0,
    "notice_period_days": 90,
    "expected_salary_range_inr_lpa": None,
    "preferred_work_mode": "",
    "willing_to_relocate": False,
    "github_activity_score": 0.0,
    "search_appearance_30d": 0,
    "saved_by_recruiters_30d": 0,
    "interview_completion_rate": 0.0,
    "offer_acceptance_rate": 0.0,
    "verified_email": False,
    "verified_phone": False,
    "linkedin_connected": False,
}


def _build_behavioral_signals(raw: dict) -> BehavioralSignals:
    signals = raw.get("redrob_signals") or raw.get("behavioral_signals") or {}
    merged = {**_DEFAULT_SIGNALS, **signals}
    return BehavioralSignals(**merged)


def raw_dict_to_profile(raw: dict) -> CandidateProfile:
    """Convert a parsed JSONL object into a ranking CandidateProfile."""
    raw = normalize_candidate_record(raw)
    profile_data = raw["profile"]
    return CandidateProfile(
        candidate_id=raw["candidate_id"],
        profile=Profile(**profile_data),
        career_history=[Experience(**e) for e in raw.get("career_history", [])],
        education=[Education(**e) for e in raw.get("education", [])],
        skills=[Skill(**s) for s in raw.get("skills", [])],
        certifications=[Certification(**c) for c in raw.get("certifications", [])],
        languages=[Language(**lang) for lang in raw.get("languages", [])],
        redrob_signals=_build_behavioral_signals(raw),
    )


def load_ranking_profiles(candidates_jsonl: str, ids: Set[str]) -> List[CandidateProfile]:
    """Stream JSONL and return CandidateProfile objects for the requested IDs."""
    if not ids:
        return []

    needed = set(ids)
    profiles: List[CandidateProfile] = []

    with open(candidates_jsonl, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            cid = raw.get("candidate_id")
            if cid not in needed:
                continue

            try:
                profiles.append(raw_dict_to_profile(raw))
            except Exception as exc:
                logger.warning("Skipping malformed candidate %s: %s", cid, exc)
                continue

            needed.discard(cid)
            if not needed:
                break

    if needed:
        logger.warning("Missing %d candidate profiles from JSONL", len(needed))

    return profiles


def iter_jsonl_records(candidates_jsonl: str) -> Iterable[dict]:
    """Yield parsed JSONL records."""
    with open(candidates_jsonl, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue
