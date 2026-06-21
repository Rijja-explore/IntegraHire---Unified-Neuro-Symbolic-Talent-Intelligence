"""Tests for candidate record normalization."""

from src.common.normalizer import normalize_candidate_record


def test_normalize_simplified_mock_record():
    raw = {
        "candidate_id": "CAND_0000000",
        "profile": {
            "name": "Candidate 0",
            "years_experience": 6,
            "current_title": "Software Engineer",
            "current_company": "InnovateLabs",
            "location": "Bangalore",
        },
        "career_history": [{"company": "Tesla", "title": "Software Engineer", "duration_months": 37}],
        "skills": [{"name": "Python", "proficiency": "advanced"}],
        "education": [{"institution": "MIT", "degree": "Bachelor", "tier": "tier_2"}],
        "redrob_signals": {"engagement_score": 90.5, "response_rate": 0.58},
    }
    normalized = normalize_candidate_record(raw)
    assert normalized["profile"]["anonymized_name"] == "Candidate 0"
    assert normalized["profile"]["years_of_experience"] == 6.0
    assert normalized["career_history"][0]["start_date"]
    assert normalized["behavioral_signals"]["recruiter_response_rate"] == 0.58
