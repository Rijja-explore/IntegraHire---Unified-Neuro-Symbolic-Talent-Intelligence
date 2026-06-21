"""Dedicated unit tests for candidate DNA generation."""

from ranking.dna.dna_generator import CandidateDNAGenerator


class TestDNAGenerator:
    def test_dna_generation(self, sample_candidate):
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
        assert 0 <= dna.authenticity <= 100
        assert 0 <= dna.learning_velocity <= 100
