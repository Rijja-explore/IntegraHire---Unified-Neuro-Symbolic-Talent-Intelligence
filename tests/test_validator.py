from common.schemas import CandidateRecord
from export.validator import validate_records, ValidationError


def test_validator_rejects_empty_reasoning():
    r = CandidateRecord(
        candidate_id="c1",
        semantic_score=1,
        authenticity_score=1,
        trajectory_score=1,
        behavior_score=1,
        production_score=1,
        final_score=1,
        reasoning="",
    )
    try:
        validate_records([r])
        assert False, "should have raised"
    except ValidationError:
        assert True
