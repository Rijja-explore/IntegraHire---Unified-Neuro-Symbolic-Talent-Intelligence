"""End-to-end pipeline: candidates.jsonl + JD → ranked submission CSV."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import List, Optional

from ranking.feature_store import CandidateRankingPipeline
from ranking.config import DEFAULT_SCORING_WEIGHTS
from retrieval.retrieval_engine import RetrievalEngine

from orchestrator.candidate_loader import load_ranking_profiles
from orchestrator.pipeline import run_pipeline

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = Path(os.getenv("RETRIEVAL_INDEX_DIR", "./retrieval/retrieval_indices"))
DEFAULT_POOL_SIZE = int(os.getenv("RETRIEVAL_POOL_SIZE", "2000"))


def _indexes_exist(index_dir: Path) -> bool:
    return (index_dir / "bm25_index.json").exists() and (index_dir / "faiss_index.faiss").exists()


def _build_retrieval_json(retrieval_results) -> List[dict]:
    records = []
    for result in retrieval_results:
        records.append(
            {
                "candidate_id": result.candidate_id,
                "semantic_score": float(result.semantic_score),
                "bm25_score": float(result.bm25_score),
                "embedding_score": float(result.embedding_score),
            }
        )
    return records


def _build_ranking_json(candidate_scores) -> List[dict]:
    records = []
    for scores in candidate_scores:
        records.append(
            {
                "candidate_id": scores.candidate_id,
                "authenticity_score": float(scores.authenticity_score),
                "trajectory_score": float(scores.trajectory_score),
                "behavior_score": float(scores.behavior_score),
                "production_score": float(scores.production_score),
                "dna_score": float(scores.dna_score),
                "final_score": float(scores.final_score) / 100.0,
            }
        )
    return records


def run_full_pipeline(
    candidates_jsonl: str,
    jd_text: str,
    output_path: str,
    *,
    index_dir: Optional[str] = None,
    pool_size: int = DEFAULT_POOL_SIZE,
    rebuild_indexes: bool = False,
) -> None:
    """
    Run retrieval → intelligence → ranking → reasoning → CSV export.

    Args:
        candidates_jsonl: Path to candidates.jsonl
        jd_text: Job description text
        output_path: Path for submission CSV
        index_dir: Directory for retrieval indices (built on first run)
        pool_size: Number of retrieval candidates to score with intelligence engines
        rebuild_indexes: Force rebuild of BM25/FAISS indexes
    """
    start = time.time()
    candidates_path = Path(candidates_jsonl)
    if not candidates_path.exists():
        raise FileNotFoundError(f"candidates file not found: {candidates_jsonl}")

    idx_dir = Path(index_dir or DEFAULT_INDEX_DIR)
    idx_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Stage 1/4: Retrieval (BM25 + FAISS + RRF)")
    engine = RetrievalEngine(index_dir=idx_dir)

    if rebuild_indexes or not _indexes_exist(idx_dir):
        logger.info("Building retrieval indexes from %s", candidates_path)
        engine.build_indexes(candidates_path)
    else:
        logger.info("Loading existing retrieval indexes from %s", idx_dir)
        engine.load_indexes(candidates_path)

    retrieval_response = engine.retrieve_by_text(jd_text, top_k=pool_size, min_score=0.0)
    if not retrieval_response.candidates:
        raise RuntimeError("Retrieval returned zero candidates; cannot produce submission.")

    logger.info(
        "Retrieved %d candidates in %.2fs",
        len(retrieval_response.candidates),
        retrieval_response.retrieval_latency_ms / 1000.0,
    )

    retrieved_ids = {r.candidate_id for r in retrieval_response.candidates}
    logger.info("Stage 2/4: Loading profiles for intelligence scoring")
    profiles = load_ranking_profiles(str(candidates_path), retrieved_ids)
    if not profiles:
        raise RuntimeError("No candidate profiles loaded for retrieved IDs.")

    profile_by_id = {p.candidate_id: p for p in profiles}
    semantic_scores = {
        r.candidate_id: float(r.semantic_score) * 100.0 for r in retrieval_response.candidates
    }

    logger.info("Stage 3/4: Intelligence engines (%d candidates)", len(profiles))
    ranking_pipeline = CandidateRankingPipeline(scoring_weights=DEFAULT_SCORING_WEIGHTS)
    ranking_pipeline.fit(profiles)
    ordered_profiles = [profile_by_id[cid] for cid in semantic_scores if cid in profile_by_id]
    candidate_scores = ranking_pipeline.process_batch(ordered_profiles, semantic_scores)

    retrieval_records = _build_retrieval_json(retrieval_response.candidates)
    ranking_records = _build_ranking_json(candidate_scores)

    logger.info("Stage 4/4: Orchestrator (top-100, reasoning, export)")
    with tempfile.TemporaryDirectory() as tmp:
        ret_path = os.path.join(tmp, "retrieval.json")
        rank_path = os.path.join(tmp, "ranking.json")
        with open(ret_path, "w", encoding="utf-8") as handle:
            json.dump(retrieval_records, handle)
        with open(rank_path, "w", encoding="utf-8") as handle:
            json.dump(ranking_records, handle)

        run_pipeline(
            ret_path,
            rank_path,
            output_path,
            candidates_jsonl=str(candidates_path),
            jd_text=jd_text,
        )

    logger.info("Full pipeline completed in %.2fs", time.time() - start)
