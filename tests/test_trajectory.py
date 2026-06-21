"""Dedicated unit tests for the trajectory engine."""

from ranking.trajectory.trajectory_engine import (
    LearningVelocityCalculator,
    ProgressionAnalyzer,
    SpecializationDetector,
    TrajectoryEngine,
)


class TestTrajectoryEngine:
    def test_progression_analysis(self, sample_candidate):
        score, _issues = ProgressionAnalyzer.analyze_progression(sample_candidate.career_history)
        assert 0 <= score <= 100

    def test_specialization_detection(self, sample_candidate):
        spec, focus = SpecializationDetector.detect_specialization(sample_candidate.career_history)
        assert spec in ["ml", "data", "backend", "unknown"]
        assert 0 <= focus <= 100

    def test_learning_velocity(self, sample_candidate):
        velocity = LearningVelocityCalculator.calculate_learning_velocity(sample_candidate)
        assert 0 <= velocity <= 100

    def test_trajectory_evaluation(self, sample_candidate):
        engine = TrajectoryEngine()
        score, learning_velocity, _analysis = engine.evaluate(sample_candidate)
        assert 0 <= score <= 100
        assert 0 <= learning_velocity <= 100
