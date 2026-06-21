import heapq
import re
from typing import Any, Iterable, List, Tuple


def _get(rec: Any, name: str, default: float = 0.0) -> float:
    """Attribute/dict accessor with numeric coercion."""
    if isinstance(rec, dict):
        return float(rec.get(name, default))
    return float(getattr(rec, name, default))


def _get_candidate_id(rec: Any) -> str:
    if isinstance(rec, dict):
        return str(rec.get("candidate_id", ""))
    return str(getattr(rec, "candidate_id", ""))


def _candidate_id_tiebreak(candidate_id: str) -> int:
    """Lower numeric candidate IDs rank higher when scores tie (hackathon rule)."""
    match = re.match(r"CAND_(\d+)", candidate_id)
    if not match:
        return 0
    return -int(match.group(1))


def compute_secondary_signal(record: Any) -> float:
    """Deterministic weighted sum used for diagnostics (not tie-breaking)."""
    return (
        0.5 * _get(record, "production_score")
        + 0.25 * _get(record, "behavior_score")
        + 0.15 * _get(record, "trajectory_score")
        + 0.10 * _get(record, "authenticity_score")
    )


def ranking_sort_key(record: Any) -> Tuple[float, str]:
    """Sort key: final_score DESC, candidate_id ASC for equal scores."""
    return (-_get(record, "final_score"), _get_candidate_id(record))


def heap_rank_key(record: Any) -> Tuple[float, int]:
    """Heap key where higher is better; equal scores break on candidate_id ASC."""
    final_score = _get(record, "final_score")
    cid = _get_candidate_id(record)
    return (final_score, _candidate_id_tiebreak(cid))


def top_k_stream(records: Iterable[Any], k: int = 100) -> List[Any]:
    """Return top-k records by final_score DESC, candidate_id ASC on ties.

    Memory: O(k). Deterministic per hackathon submission rules.
    """

    heap: List[Tuple[Tuple[float, int], Any]] = []

    for rec in records:
        key = heap_rank_key(rec)
        item = (key, rec)

        if len(heap) < k:
            heapq.heappush(heap, item)
        elif key > heap[0][0]:
            heapq.heapreplace(heap, item)

    sorted_items = sorted(heap, key=lambda x: x[0], reverse=True)
    return [item[1] for item in sorted_items]
