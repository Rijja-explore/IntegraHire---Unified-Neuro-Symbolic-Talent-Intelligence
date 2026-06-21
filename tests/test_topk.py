from orchestrator.topk import top_k_stream, compute_secondary_signal, ranking_sort_key
from common.schemas import CandidateRecord


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


def test_topk_tiebreaks():
    recs = [
        make_rec("CAND_0000002", 90, 80, 80, 70, 90),
        make_rec("CAND_0000001", 90, 70, 90, 70, 90),
        make_rec("CAND_0000003", 85, 90, 50, 60, 80),
    ]
    top = top_k_stream(recs, k=2)
    # Equal final scores: lower candidate_id ranks higher (hackathon rule)
    assert top[0].candidate_id == "CAND_0000001"
    assert top[1].candidate_id == "CAND_0000002"


def test_ranking_sort_key():
    recs = [
        make_rec("CAND_0000005", 1.0, 80, 80, 70, 90),
        make_rec("CAND_0000002", 1.0, 70, 90, 70, 90),
    ]
    sorted_recs = sorted(recs, key=ranking_sort_key)
    assert sorted_recs[0].candidate_id == "CAND_0000002"
    assert sorted_recs[1].candidate_id == "CAND_0000005"
