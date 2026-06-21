import csv
import logging
from typing import List
from typing import Any

# CandidateRecord typing is deprecated in the current unified pipeline; keep runtime flexible.
CandidateRecord = Any



logger = logging.getLogger(__name__)


def write_submission_csv(records: List[CandidateRecord], path: str) -> None:
    """Write submission CSV with strict validation of format and constraints.
    
    - Expects records to be sorted by final_score DESC with deterministic tie-breaks
    - Validates exactly 100 rows
    - Scores must be non-increasing
    - No missing reasoning fields
    """
    if len(records) != 100:
        raise ValueError(f"Expected exactly 100 records, got {len(records)}")

    # Validate monotonic score
    for i in range(len(records) - 1):
        if records[i].final_score + 1e-9 < records[i + 1].final_score:
            raise ValueError(
                f"Scores must be non-increasing: rank {i+1} score {records[i].final_score} "
                f"< rank {i+2} score {records[i+1].final_score}"
            )

    def _get(obj, key: str):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key)

    # Validate reasoning non-empty
    for i, r in enumerate(records):
        reasoning = _get(r, "reasoning")
        cid = _get(r, "candidate_id")
        if not reasoning or not str(reasoning).strip():
            raise ValueError(f"Empty reasoning at rank {i+1} for {cid}")

    with open(path, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for idx, r in enumerate(records, start=1):
            cid = _get(r, "candidate_id")
            final_score = _get(r, "final_score")
            reasoning = _get(r, "reasoning")
            # Format score to 6 decimal places for consistency
            score_str = f"{float(final_score):.6f}"
            writer.writerow([cid, idx, score_str, str(reasoning).strip()])


    logger.info(f"Wrote {len(records)} rows to {path}")

