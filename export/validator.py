from typing import List, Set, Any

# CandidateRecord typing is deprecated in the current unified pipeline; keep runtime flexible.
CandidateRecord = Any

from tools.profile_index import load_profiles_for_ids



class ValidationError(Exception):
    pass


def validate_submission_records(records: List[CandidateRecord], candidates_jsonl_path: str) -> None:
    # Enforce exactly 100 rows
    if len(records) != 100:
        raise ValidationError(f"submission must contain exactly 100 rows, got {len(records)}")

    # unique ids
    def _get(obj, key: str):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key)

    ids = [_get(r, "candidate_id") for r in records]

    if len(ids) != len(set(ids)):
        raise ValidationError("duplicate candidate IDs detected in submission")

    # monotonic non-increasing scores
    for i in range(len(records) - 1):
        a = _get(records[i], "final_score")
        b = _get(records[i + 1], "final_score")
        if a + 1e-9 < b:
            raise ValidationError(
                f"scores must be non-increasing: rank {i+1} score {a} < rank {i+2} score {b}"
            )

    # reasoning presence
    for r in records:
        reasoning = _get(r, "reasoning")
        cid = _get(r, "candidate_id")
        if not reasoning or not str(reasoning).strip():
            raise ValidationError(f"empty reasoning for {cid}")


    # existence check in candidates.jsonl for top-100
    needed = set(ids)
    found = load_profiles_for_ids(candidates_jsonl_path, needed)
    missing = needed - set(found.keys())
    if missing:
        raise ValidationError(f"the following candidate_ids are not present in candidates.jsonl: {sorted(list(missing))}")


def validate_records(records: List[Any]) -> None:
    """Legacy validation function for checking basic constraints (e.g. reasoning presence)."""
    def _get(obj, key: str):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key)

    ids = [_get(r, "candidate_id") for r in records]
    if len(ids) != len(set(ids)):
        raise ValidationError("duplicate candidate IDs detected")

    # reasoning presence
    for r in records:
        reasoning = _get(r, "reasoning")
        cid = _get(r, "candidate_id")
        if not reasoning or not str(reasoning).strip():
            raise ValidationError(f"empty reasoning for {cid}")


