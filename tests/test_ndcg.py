from evaluation.ndcg import dcg_at_k, ndcg_at_k


def test_dcg_simple():
    vals = [3, 2, 3, 0, 1]
    assert dcg_at_k(vals, 3) > 0


def test_ndcg_identity():
    gold = {"a": 3.0, "b": 2.0, "c": 1.0}
    predicted = ["a", "b", "c"]
    assert abs(ndcg_at_k(gold, predicted, 3) - 1.0) < 1e-6
