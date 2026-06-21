"""Unit tests for candidate ranking system."""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

from ranking.schemas import (
    CandidateProfile, Profile, Experience, Education, Skill,
    BehavioralSignals, Language, Certification
)
from ranking.authenticity.authenticity_engine import AuthenticityEngine
from ranking.authenticity.timeline_validator import TimelineValidator
from ranking.authenticity.skill_consistency import SkillConsistency
from ranking.trajectory.trajectory_engine import TrajectoryEngine
from ranking.production.production_engine import ProductionEngine
from ranking.behavior.behavioral_engine import BehavioralEngine
from ranking.dna.dna_generator import CandidateDNAGenerator
from ranking.ranking.ranking_engine import RankingEngine

# Test fixtures
@pytest.fixture
def sample_candidate():
    """Create sample candidate for testing."""
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

    languages = [Language(language="English", proficiency="professional")]

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
        languages=languages,
        redrob_signals=signals,
    )

class TestAuthenticityEngine:
    """Test authenticity evaluation."""

    def test_timeline_validation_success(self, sample_candidate):
        """Test timeline validation for valid candidate."""
        validator = TimelineValidator()
        penalty, issues = validator.validate_timeline(sample_candidate.career_history)
        assert penalty == 0, "No penalty for valid timeline"
        assert len(issues) == 0, "No issues in valid timeline"

    def test_timeline_validation_overlap(self):
        """Test timeline validation with overlapping positions."""
        exp1 = Experience(
            company="Company A",
            title="Engineer",
            start_date="2020-01-01",
            end_date="2022-06-30",
            duration_months=30,
            is_current=False,
            industry="Tech",
            company_size="1001-5000",
            description="Work",
        )
        exp2 = Experience(
            company="Company B",
            title="Senior Engineer",
            start_date="2022-03-01",
            end_date="2024-01-01",
            duration_months=22,
            is_current=False,
            industry="Tech",
            company_size="1001-5000",
            description="Work",
        )

        validator = TimelineValidator()
        penalty, issues = validator.validate_timeline([exp1, exp2])
        assert penalty > 0, "Penalty applied for overlapping positions"
        assert len(issues) > 0, "Issues detected"

    def test_skill_consistency(self, sample_candidate):
        """Test skill consistency scoring."""
        score = SkillConsistency.calculate_skill_consistency_score(
            sample_candidate.skills,
            sample_candidate.career_history
        )
        assert 0 <= score <= 100, "Score in valid range"
        assert score > 70, "Good consistency score for valid profile"

    def test_authenticity_evaluation(self, sample_candidate):
        """Test full authenticity evaluation."""
        engine = AuthenticityEngine()
        engine.fit([sample_candidate])
        auth_score, anomaly_score, analysis = engine.evaluate(sample_candidate)

        assert 0 <= auth_score <= 100, "Auth score in range"
        assert 0 <= anomaly_score <= 100, "Anomaly score in range"
        assert auth_score > 60, "Good authenticity for valid candidate"

class TestTrajectoryEngine:
    """Test trajectory evaluation."""

    def test_progression_analysis(self, sample_candidate):
        """Test career progression analysis."""
        from ranking.trajectory.trajectory_engine import ProgressionAnalyzer
        score, issues = ProgressionAnalyzer.analyze_progression(
            sample_candidate.career_history
        )
        assert 0 <= score <= 100, "Score in range"

    def test_specialization_detection(self, sample_candidate):
        """Test specialization detection."""
        from ranking.trajectory.trajectory_engine import SpecializationDetector
        spec, focus = SpecializationDetector.detect_specialization(
            sample_candidate.career_history
        )
        assert spec in ["ml", "data", "backend", "unknown"], f"Valid specialization: {spec}"
        assert 0 <= focus <= 100, "Focus score in range"

    def test_learning_velocity(self, sample_candidate):
        """Test learning velocity calculation."""
        from ranking.trajectory.trajectory_engine import LearningVelocityCalculator
        velocity = LearningVelocityCalculator.calculate_learning_velocity(
            sample_candidate
        )
        assert 0 <= velocity <= 100, "Velocity in range"

class TestProductionEngine:
    """Test production readiness evaluation."""

    def test_skill_scoring(self, sample_candidate):
        """Test production skill scoring."""
        from ranking.production.production_engine import ProductionSignalDetector
        detector = ProductionSignalDetector()
        score, breakdown = detector.score_skills(sample_candidate.skills)
        assert 0 <= score <= 100, "Score in range"
        assert score > 70, "High production score for skilled candidate"

    def test_production_evaluation(self, sample_candidate):
        """Test full production evaluation."""
        engine = ProductionEngine()
        score, analysis = engine.evaluate(sample_candidate)
        assert 0 <= score <= 100, "Score in range"
        assert "final_score" in analysis

class TestBehavioralEngine:
    """Test behavioral evaluation."""

    def test_engagement_score(self, sample_candidate):
        """Test engagement scoring."""
        engine = BehavioralEngine()
        score = engine.calculate_engagement_score(sample_candidate.redrob_signals)
        assert 0 <= score <= 100, "Score in range"
        assert score > 70, "High engagement for active candidate"

    def test_reliability_score(self, sample_candidate):
        """Test reliability scoring."""
        engine = BehavioralEngine()
        score = engine.calculate_reliability_score(sample_candidate.redrob_signals)
        assert 0 <= score <= 100, "Score in range"

    def test_availability_score(self, sample_candidate):
        """Test availability scoring."""
        engine = BehavioralEngine()
        score = engine.calculate_availability_score(sample_candidate.redrob_signals)
        assert 0 <= score <= 100, "Score in range"

    def test_behavioral_evaluation(self, sample_candidate):
        """Test full behavioral evaluation."""
        engine = BehavioralEngine()
        score, analysis = engine.evaluate(sample_candidate)
        assert 0 <= score <= 100, "Score in range"
        assert score > 60, "Good behavior score for active candidate"

class TestDNAGenerator:
    """Test DNA generation."""

    def test_dna_generation(self, sample_candidate):
        """Test candidate DNA generation."""
        dna = CandidateDNAGenerator.generate_dna(
            sample_candidate,
            authenticity_score=85.0,
            trajectory_score=80.0,
            learning_velocity_score=75.0,
            production_score=90.0,
            behavior_score=85.0,
        )

        assert dna.technical_depth > 0
        assert dna.production_readiness > 0
        assert 0 <= dna.research_orientation <= 100
        assert dna.startup_fit > 0

class TestRankingEngine:
    """Test ranking engine."""

    def test_final_ranking(self, sample_candidate):
        """Test final ranking score computation."""
        dna = CandidateDNAGenerator.generate_dna(
            sample_candidate,
            authenticity_score=85.0,
            trajectory_score=80.0,
            learning_velocity_score=75.0,
            production_score=90.0,
            behavior_score=85.0,
        )

        engine = RankingEngine()
        scores = engine.compute_final_score(
            candidate_id="TEST_001",
            semantic_score=75.0,
            authenticity_score=85.0,
            anomaly_score=20.0,
            trajectory_score=80.0,
            learning_velocity_score=75.0,
            production_score=90.0,
            behavior_score=85.0,
            dna=dna,
        )

        assert 0 <= scores.final_score <= 100, "Final score in range"
        assert scores.final_score > 70, "High score for qualified candidate"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
