"""Dedicated unit tests for the authenticity engine."""

from ranking.authenticity.authenticity_engine import AuthenticityEngine
from ranking.authenticity.skill_consistency import SkillConsistency
from ranking.authenticity.timeline_validator import TimelineValidator
from ranking.schemas import Experience


class TestAuthenticityEngine:
    def test_timeline_validation_success(self, sample_candidate):
        validator = TimelineValidator()
        penalty, issues = validator.validate_timeline(sample_candidate.career_history)
        assert penalty == 0
        assert len(issues) == 0

    def test_timeline_validation_overlap(self):
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
        assert penalty > 0
        assert len(issues) > 0

    def test_skill_consistency(self, sample_candidate):
        score = SkillConsistency.calculate_skill_consistency_score(
            sample_candidate.skills,
            sample_candidate.career_history,
        )
        assert 0 <= score <= 100
        assert score > 70

    def test_authenticity_evaluation(self, sample_candidate):
        engine = AuthenticityEngine()
        engine.fit([sample_candidate])
        auth_score, anomaly_score, _analysis = engine.evaluate(sample_candidate)
        assert 0 <= auth_score <= 100
        assert 0 <= anomaly_score <= 100
        assert auth_score > 60
