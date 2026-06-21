import logging
import time
import json
from typing import List, Iterator, Dict

# Use unified config and schemas from src/common
from src.common.config import get_config
from src.common.schemas import RankedCandidate, CandidateRecord

# Import local modules (these will be migrated)
from orchestrator.loader import load_json
from orchestrator.merger import merge_records
from orchestrator.topk import top_k_stream, ranking_sort_key
from validate_submission import validate_submission
from reasoning.generator import generate_reasoning_for
from export.csv_writer import write_submission_csv
from export.validator import validate_submission_records, ValidationError
from tools.profile_index import load_profiles_for_ids

logger = logging.getLogger(__name__)


def _merged_records_iter(retrieval_iter: Iterator[dict], ranking_map: Dict[str, dict]) -> Iterator[CandidateRecord]:
    """Merge retrieval and ranking results into unified records."""
    for rec in retrieval_iter:
        cid = rec.get("candidate_id")
        r = ranking_map.get(cid, {})
        merged = CandidateRecord(
            candidate_id=cid,
            semantic_score=float(rec.get("semantic_score", 0.0)),
            authenticity_score=float(r.get("authenticity_score", 0.0)),
            trajectory_score=float(r.get("trajectory_score", 0.0)),
            behavior_score=float(r.get("behavior_score", 0.0)),
            production_score=float(r.get("production_score", 0.0)),
            final_score=float(r.get("final_score", 0.0)),
            dna_score=float(r.get("dna_score", 0.0)),
            reasoning=None,
            confidence=None,
        )
        yield merged


def run_pipeline(retrieval_path: str, ranking_path: str, output_path: str, candidates_jsonl: str = None, jd_text: str = None) -> None:
    # Use a safe default log format (LOG_FORMAT may not exist in this module)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    logger.info("Pipeline start")
    start = time.time()

    retrieval = load_json(retrieval_path)
    ranking = load_json(ranking_path)
    ranking_map = {r["candidate_id"]: r for r in ranking}

    merged_iter = _merged_records_iter(iter(retrieval), ranking_map)

    # streaming top-k selection
    top_records = top_k_stream(merged_iter, k=100)
    logger.info("Selected top %d candidates", len(top_records))

    # fetch profiles for top candidates if candidates_jsonl provided
    profiles = {}
    if candidates_jsonl:
        ids = set([r["candidate_id"] for r in top_records])
        profiles = load_profiles_for_ids(candidates_jsonl, ids)

    # generate reasoning using profile and optional JD
    t0 = time.time()
    for r in top_records:
        cid = r["candidate_id"]
        profile = profiles.get(cid)
        reasoning, confidence = generate_reasoning_for(r, profile=profile, jd_text=jd_text)
        r["reasoning"] = reasoning
        r["confidence"] = confidence
    gen_time = time.time() - t0
    logger.info("Reasoning generation time: %.3fs", gen_time)


    # Final deterministic sorting: score DESC, candidate_id ASC on ties (hackathon rule)
    top_records.sort(key=ranking_sort_key)

    # validate
    try:
        if candidates_jsonl:
            validate_submission_records(top_records, candidates_jsonl)
        else:
            # if no candidates_jsonl provided, still ensure 100 rows and monotonicity
            if len(top_records) != 100:
                logger.warning("Top records count !=100; skipping strict existence validation")
    except ValidationError as e:
        logger.error("Validation failed: %s", e)
        raise

    # write CSV
    write_submission_csv(top_records, output_path)

    submission_errors = validate_submission(output_path)
    if submission_errors:
        raise ValidationError(
            "Submission failed hackathon validation: " + "; ".join(submission_errors[:5])
        )

    # write run metadata and debug top-100 JSON
    meta = {
        "pipeline_time_s": time.time() - start,
        "num_selected": len(top_records),
        "reasoning_time_s": gen_time,
    }
    with open(output_path + ".metadata.json", "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)

    debug_rows = [
        {
            "candidate_id": r["candidate_id"],
            "final_score": r["final_score"],
            "confidence": r["confidence"],
            "reasoning": r["reasoning"],
        }
        for r in top_records
    ]

    with open(output_path + ".top100.json", "w", encoding="utf-8") as df:
        json.dump(debug_rows, df, indent=2)

    logger.info("Exported CSV to %s", output_path)
    logger.info("Pipeline end (%.3fs)", time.time() - start)
