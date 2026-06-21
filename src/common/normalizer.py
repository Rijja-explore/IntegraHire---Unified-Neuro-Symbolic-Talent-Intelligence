"""Normalize candidate JSONL records into the canonical schema."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

_LOCATION_COUNTRY = {
    "san francisco": "USA",
    "new york": "USA",
    "london": "United Kingdom",
    "bangalore": "India",
    "toronto": "Canada",
}


def _country_from_location(location: str) -> str:
    if not location:
        return "Unknown"
    return _LOCATION_COUNTRY.get(location.lower().strip(), "Unknown")


def _synthetic_dates(duration_months: int, index: int) -> Dict[str, Any]:
    end = datetime.now() - timedelta(days=30 * index * 6)
    start = end - timedelta(days=30 * max(duration_months, 1))
    return {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": None if index == 0 else end.strftime("%Y-%m-%d"),
        "is_current": index == 0,
    }


def _normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    if profile.get("anonymized_name"):
        return profile

    name = profile.get("name") or profile.get("anonymized_name") or "Candidate"
    title = profile.get("current_title") or "Software Engineer"
    company = profile.get("current_company") or "Unknown Company"
    location = profile.get("location") or "Unknown"
    years = profile.get("years_of_experience", profile.get("years_experience", 0))

    return {
        "anonymized_name": name,
        "headline": profile.get("headline") or f"{title} at {company}",
        "summary": profile.get("summary")
        or f"{title} with {years} years of experience at {company}.",
        "location": location,
        "country": profile.get("country") or _country_from_location(location),
        "years_of_experience": float(years),
        "current_title": title,
        "current_company": company,
        "current_company_size": profile.get("current_company_size") or "1001-5000",
        "current_industry": profile.get("current_industry") or "Technology",
    }


def _normalize_career_history(career_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, entry in enumerate(career_history or []):
        item = dict(entry)
        if not item.get("start_date"):
            item.update(_synthetic_dates(int(item.get("duration_months") or 12), index))
        item.setdefault("end_date", None if item.get("is_current") else item.get("end_date"))
        item.setdefault("is_current", index == 0 and item.get("end_date") in (None, ""))
        item.setdefault("industry", "Technology")
        item.setdefault("company_size", "1001-5000")
        item.setdefault("description", f"{item.get('title', 'Engineer')} at {item.get('company', 'company')}.")
        item.setdefault("duration_months", 12)
        normalized.append(item)
    return normalized or [
        {
            "company": "Unknown",
            "title": "Engineer",
            "start_date": "2020-01-01",
            "end_date": None,
            "duration_months": 12,
            "is_current": True,
            "industry": "Technology",
            "company_size": "1001-5000",
            "description": "General engineering experience.",
        }
    ]


def _normalize_education(education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for entry in education or []:
        item = dict(entry)
        item.setdefault("field_of_study", item.get("field_of_study") or "Computer Science")
        item.setdefault("start_year", int(item.get("start_year") or 2014))
        item.setdefault("end_year", int(item.get("end_year") or item["start_year"] + 4))
        normalized.append(item)
    return normalized


def _normalize_skills(skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for skill in skills or []:
        item = dict(skill)
        item.setdefault("endorsements", 0)
        item.setdefault("duration_months", 12)
        normalized.append(item)
    return normalized


def _normalize_behavioral_signals(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    signals = raw.get("redrob_signals") or raw.get("behavioral_signals")
    if signals is None:
        return None

    merged = {
        "profile_completeness_score": float(signals.get("profile_completeness_score", 75.0)),
        "signup_date": signals.get("signup_date", "2020-01-01"),
        "last_active_date": signals.get("last_active_date", datetime.now().strftime("%Y-%m-%d")),
        "open_to_work_flag": bool(signals.get("open_to_work_flag", True)),
        "profile_views_received_30d": int(signals.get("profile_views_received_30d", 10)),
        "applications_submitted_30d": int(signals.get("applications_submitted_30d", 1)),
        "recruiter_response_rate": float(
            signals.get("recruiter_response_rate", signals.get("response_rate", 0.5))
        ),
        "avg_response_time_hours": float(signals.get("avg_response_time_hours", 24.0)),
        "skill_assessment_scores": signals.get("skill_assessment_scores") or {},
        "connection_count": int(signals.get("connection_count", 100)),
        "endorsements_received": int(signals.get("endorsements_received", 10)),
        "notice_period_days": int(signals.get("notice_period_days", 30)),
        "expected_salary_range_inr_lpa": signals.get("expected_salary_range_inr_lpa"),
        "preferred_work_mode": signals.get("preferred_work_mode", "hybrid"),
        "willing_to_relocate": bool(signals.get("willing_to_relocate", False)),
        "github_activity_score": float(
            signals.get("github_activity_score", signals.get("engagement_score", 5.0))
        ),
        "search_appearance_30d": int(signals.get("search_appearance_30d", 20)),
        "saved_by_recruiters_30d": int(signals.get("saved_by_recruiters_30d", 2)),
        "interview_completion_rate": float(signals.get("interview_completion_rate", 0.7)),
        "offer_acceptance_rate": float(signals.get("offer_acceptance_rate", 0.7)),
        "verified_email": bool(signals.get("verified_email", True)),
        "verified_phone": bool(signals.get("verified_phone", False)),
        "linkedin_connected": bool(signals.get("linkedin_connected", True)),
    }
    return merged


def normalize_candidate_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return a canonical candidate dict compatible with ``CandidateRawData``."""
    record = deepcopy(raw)
    record["profile"] = _normalize_profile(record.get("profile") or {})
    record["career_history"] = _normalize_career_history(record.get("career_history") or [])
    record["education"] = _normalize_education(record.get("education") or [])
    record["skills"] = _normalize_skills(record.get("skills") or [])
    record.setdefault("certifications", record.get("certifications") or [])
    record.setdefault("languages", record.get("languages") or [])

    behavioral = _normalize_behavioral_signals(record)
    if behavioral is not None:
        record["behavioral_signals"] = behavioral
        record["redrob_signals"] = behavioral

    return record
