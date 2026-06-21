from reasoning.generator import generate_reasoning_for
from common.schemas import CandidateRecord


def test_generate_reasoning_basic():
    r = CandidateRecord(
        candidate_id="c1",
        semantic_score=80,
        authenticity_score=90,
        trajectory_score=80,
        behavior_score=85,
        production_score=88,
        final_score=90,
    )
    text, conf = generate_reasoning_for(r)
    assert isinstance(text, str) and text
    assert 0.0 <= conf <= 1.0
