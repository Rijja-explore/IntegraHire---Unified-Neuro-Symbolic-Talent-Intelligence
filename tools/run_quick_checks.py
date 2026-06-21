import sys
import pathlib
# ensure workspace root is on sys.path for imports
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from orchestrator.topk import top_k_stream, compute_secondary_signal
from common.schemas import CandidateRecord
from evaluation.ndcg import ndcg_at_k
from reasoning.generator import generate_reasoning_for
from orchestrator.merger import merge_records


def make_rec(cid, final, prod, beh, traj, auth, sem=0.0):
    return CandidateRecord(
        candidate_id=cid,
        semantic_score=sem,
        authenticity_score=auth,
        trajectory_score=traj,
        behavior_score=beh,
        production_score=prod,
        final_score=final,
    )


def test_topk():
    recs = [
        make_rec("CAND_0000001", 90, 80, 80, 70, 90),
        make_rec("CAND_0000002", 90, 70, 90, 70, 90),
        make_rec("CAND_0000003", 85, 90, 50, 60, 80),
    ]
    top = top_k_stream(recs, k=2)
    assert len(top) == 2


def test_ndcg():
    gold = {"a": 3.0, "b": 2.0, "c": 1.0}
    pred = ["a", "b", "c"]
    val = ndcg_at_k(gold, pred, 3)
    assert abs(val - 1.0) < 1e-6


def test_reasoning():
    r = make_rec("CAND_0000001", 88, 88, 80, 77, 86)
    text, conf = generate_reasoning_for(r, profile=None, jd_text="python kubernetes")
    assert isinstance(text, str) and text
    assert 0.0 <= conf <= 1.0


def run_all():
    tests = [test_topk, test_ndcg, test_reasoning]
    for t in tests:
        try:
            t()
            print(f"{t.__name__}: OK")
        except AssertionError:
            print(f"{t.__name__}: FAIL")
            raise


if __name__ == "__main__":
    try:
        run_all()
        print("All quick checks passed.")
    except Exception as e:
        print("Quick checks failed:", e)
        sys.exit(1)
