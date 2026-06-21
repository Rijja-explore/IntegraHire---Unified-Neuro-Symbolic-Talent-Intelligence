"""Dedicated unit tests for production readiness scoring."""

from ranking.production.production_engine import ProductionEngine, ProductionSignalDetector


class TestProductionEngine:
    def test_skill_scoring(self, sample_candidate):
        detector = ProductionSignalDetector()
        score, breakdown = detector.score_skills(sample_candidate.skills)
        assert 0 <= score <= 100
        assert score > 70
        assert isinstance(breakdown, dict)

    def test_production_evaluation(self, sample_candidate):
        engine = ProductionEngine()
        score, analysis = engine.evaluate(sample_candidate)
        assert 0 <= score <= 100
        assert "final_score" in analysis
