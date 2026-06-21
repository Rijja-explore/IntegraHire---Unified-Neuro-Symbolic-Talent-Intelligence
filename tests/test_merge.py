from orchestrator.merger import merge_records


def test_merge_basic():
    retrieval = [{"candidate_id": "a", "semantic_score": 1.0}]
    ranking = [{"candidate_id": "a", "final_score": 2.0}]
    merged = merge_records(retrieval, ranking)
    assert len(merged) == 1
    assert merged[0].final_score == 2.0
