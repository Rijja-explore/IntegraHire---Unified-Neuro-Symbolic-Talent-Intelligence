"""Single runtime entrypoint for ranking."""

from __future__ import annotations

from typing import Optional

from orchestrator.full_pipeline import run_full_pipeline
from orchestrator.pipeline import run_pipeline


def rank(
    retrieval_path: str,
    ranking_path: str,
    output_path: str,
    *,
    candidates_jsonl: Optional[str] = None,
    jd_text: Optional[str] = None,
) -> None:
    """Run the pre-scored pipeline and write the submission CSV."""
    run_pipeline(
        retrieval_path,
        ranking_path,
        output_path,
        candidates_jsonl=candidates_jsonl,
        jd_text=jd_text,
    )


def rank_from_candidates(
    candidates_jsonl: str,
    jd_text: str,
    output_path: str,
    *,
    index_dir: Optional[str] = None,
    pool_size: Optional[int] = None,
    rebuild_indexes: bool = False,
) -> None:
    """Run the full end-to-end pipeline from raw candidates + JD."""
    kwargs = {
        "index_dir": index_dir,
        "rebuild_indexes": rebuild_indexes,
    }
    if pool_size is not None:
        kwargs["pool_size"] = pool_size
    run_full_pipeline(candidates_jsonl, jd_text, output_path, **kwargs)
