"""Dedicated unit tests for the behavioral engine."""

from ranking.behavior.behavioral_engine import BehavioralEngine


class TestBehavioralEngine:
    def test_engagement_score(self, sample_candidate):
        engine = BehavioralEngine()
        score = engine.calculate_engagement_score(sample_candidate.redrob_signals)
        assert 0 <= score <= 100
        assert score > 70

    def test_reliability_score(self, sample_candidate):
        engine = BehavioralEngine()
        score = engine.calculate_reliability_score(sample_candidate.redrob_signals)
        assert 0 <= score <= 100

    def test_availability_score(self, sample_candidate):
        engine = BehavioralEngine()
        score = engine.calculate_availability_score(sample_candidate.redrob_signals)
        assert 0 <= score <= 100

    def test_behavioral_evaluation(self, sample_candidate):
        engine = BehavioralEngine()
        score, analysis = engine.evaluate(sample_candidate)
        assert 0 <= score <= 100
        assert score > 60
        assert "final_score" in analysis
