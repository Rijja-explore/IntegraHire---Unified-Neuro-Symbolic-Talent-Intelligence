"""Shared pytest fixtures for intelligence engine tests."""

from datetime import datetime

import pytest

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


@pytest.fixture
def sample_candidate():
    """Create a representative candidate profile for engine tests."""
    profile = Profile(
        anonymized_name="Test Engineer",
        headline="Senior ML Engineer",
        summary="Experienced in ML systems and production engineering",
        location="San Francisco",
        country="USA",
        years_of_experience=6.0,
        current_title="Senior Engineer",
        current_company="TechCorp",
        current_company_size="10001+",
        current_industry="Software",
    )

    career_history = [
        Experience(
            company="TechCorp",
            title="Senior Engineer",
            start_date="2023-01-15",
            end_date=None,
            duration_months=18,
            is_current=True,
            industry="Software",
            company_size="10001+",
            description="Led ML ranking system development with FAISS and LightGBM",
        ),
        Experience(
            company="StartupXYZ",
            title="ML Engineer",
            start_date="2020-06-01",
            end_date="2022-12-31",
            duration_months=31,
            is_current=False,
            industry="Technology",
            company_size="51-200",
            description="Built recommendation system using embeddings and Kafka",
        ),
    ]

    education = [
        Education(
            institution="Top University",
            degree="B.S.",
            field_of_study="Computer Science",
            start_year=2016,
            end_year=2020,
            grade="3.8",
            tier="tier_1",
        )
    ]

    skills = [
        Skill(name="Python", proficiency="advanced", endorsements=50, duration_months=60),
        Skill(name="FAISS", proficiency="advanced", endorsements=15, duration_months=24),
        Skill(name="LightGBM", proficiency="advanced", endorsements=20, duration_months=18),
        Skill(name="Kafka", proficiency="intermediate", endorsements=10, duration_months=24),
        Skill(name="PyTorch", proficiency="advanced", endorsements=25, duration_months=36),
    ]

    signals = BehavioralSignals(
        profile_completeness_score=95.0,
        signup_date="2020-01-15",
        last_active_date=datetime.now().strftime("%Y-%m-%d"),
        open_to_work_flag=True,
        profile_views_received_30d=50,
        applications_submitted_30d=3,
        recruiter_response_rate=0.8,
        avg_response_time_hours=4.0,
        skill_assessment_scores={"FAISS": 85.0, "LightGBM": 80.0},
        connection_count=500,
        endorsements_received=100,
        notice_period_days=14,
        expected_salary_range_inr_lpa={"min": 50.0, "max": 80.0},
        preferred_work_mode="hybrid",
        willing_to_relocate=True,
        github_activity_score=8.5,
        search_appearance_30d=200,
        saved_by_recruiters_30d=15,
        interview_completion_rate=0.9,
        offer_acceptance_rate=0.8,
        verified_email=True,
        verified_phone=True,
        linkedin_connected=True,
    )

    return CandidateProfile(
        candidate_id="CAND_TEST_001",
        profile=profile,
        career_history=career_history,
        education=education,
        skills=skills,
        certifications=[],
        languages=[Language(language="English", proficiency="professional")],
        redrob_signals=signals,
    )
