from typing import List, Dict
import logging

from src.common.schemas import RankedCandidate, CandidateRecord


logger = logging.getLogger(__name__)


def merge_records(retrieval: List[Dict], ranking: List[Dict]):

    """Merge retrieval and ranking records into CandidateRecord objects.
    
    Handles missing fields gracefully with defaults (0.0).
    Logs warnings for candidates present in retrieval but missing from ranking.
    """
    if not retrieval:
        raise ValueError("retrieval list is empty")
    if not ranking:
        raise ValueError("ranking list is empty")

    rank_map = {r.get("candidate_id"): r for r in ranking if r.get("candidate_id")}
    merged = []
    missing_count = 0

    for rec in retrieval:
        cid = rec.get("candidate_id")
        if not cid:
            logger.warning("Skipping retrieval record with missing candidate_id")
            continue

        r = rank_map.get(cid, {})
        if not r:
            missing_count += 1

        cr = CandidateRecord(
            candidate_id=cid,
            semantic_score=float(rec.get("semantic_score", 0.0)),
            authenticity_score=float(r.get("authenticity_score", 0.0)),
            trajectory_score=float(r.get("trajectory_score", 0.0)),
            behavior_score=float(r.get("behavior_score", 0.0)),
            production_score=float(r.get("production_score", 0.0)),
            final_score=float(r.get("final_score", 0.0)),
        )
        merged.append(cr)

    if missing_count > 0:
        logger.warning(f"{missing_count} candidates present in retrieval but not in ranking")

    logger.info(f"Merged {len(merged)} candidate records")
    return merged
