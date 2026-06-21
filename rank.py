#!/usr/bin/env python3
"""Production entry point for the ranking pipeline."""

import argparse
import logging
import os
import sys
from pathlib import Path

from src.common import get_config
from src.pipeline.rank_pipeline import rank, rank_from_candidates


logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point for the ranking pipeline."""
    parser = argparse.ArgumentParser(
        description="Recruiter Cognitive Twin — Rank candidates deterministically.",
        epilog=(
            "Full pipeline:\n"
            "  python rank.py --candidates candidates.jsonl "
            "--job_description job_description.txt --output submission.csv\n\n"
            "Pre-scored mode:\n"
            "  python rank.py --retrieval retrieval.json --ranking ranking.json "
            "--output submission.csv --candidates candidates.jsonl --jd job_description.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--candidates",
        default=None,
        help="Path to candidates.jsonl (required for full pipeline).",
    )
    parser.add_argument(
        "--job_description",
        "--jd",
        dest="jd",
        default=None,
        help="Path to job description text file.",
    )
    parser.add_argument(
        "--retrieval",
        default=None,
        help="Path to retrieval JSON (pre-scored mode).",
    )
    parser.add_argument(
        "--ranking",
        default=None,
        help="Path to ranking JSON (pre-scored mode).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output CSV (will be overwritten).",
    )
    parser.add_argument(
        "--index-dir",
        default=None,
        help="Retrieval index directory (full pipeline; default: ./retrieval/retrieval_indices).",
    )
    parser.add_argument(
        "--pool-size",
        type=int,
        default=None,
        help="Retrieval pool size before intelligence scoring (default: 2000).",
    )
    parser.add_argument(
        "--rebuild-indexes",
        action="store_true",
        help="Force rebuild of BM25/FAISS indexes.",
    )
    args = parser.parse_args()

    config = get_config()
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(message)s")

    full_mode = args.candidates and args.jd
    prescored_mode = args.retrieval and args.ranking

    if full_mode and prescored_mode:
        logger.error("Use either full pipeline (--candidates + --job_description) OR pre-scored mode (--retrieval + --ranking).")
        sys.exit(1)
    if not full_mode and not prescored_mode:
        logger.error(
            "Provide either:\n"
            "  --candidates + --job_description  (full pipeline)\n"
            "  --retrieval + --ranking           (pre-scored mode)"
        )
        sys.exit(1)

    errors = []
    if args.candidates and not os.path.exists(args.candidates):
        errors.append(f"candidates file not found: {args.candidates}")
    if args.jd and not os.path.exists(args.jd):
        errors.append(f"JD file not found: {args.jd}")
    if args.retrieval and not os.path.exists(args.retrieval):
        errors.append(f"retrieval file not found: {args.retrieval}")
    if args.ranking and not os.path.exists(args.ranking):
        errors.append(f"ranking file not found: {args.ranking}")

    if errors:
        for err in errors:
            logger.error(err)
        sys.exit(1)

    jd_text = None
    if args.jd:
        with open(args.jd, "r", encoding="utf-8") as handle:
            jd_text = handle.read().strip()
        logger.info("Loaded JD from %s (%d chars)", args.jd, len(jd_text))

    try:
        if full_mode:
            logger.info("Running full pipeline (retrieval → intelligence → ranking → export)...")
            rank_from_candidates(
                args.candidates,
                jd_text,
                args.output,
                index_dir=args.index_dir,
                pool_size=args.pool_size,
                rebuild_indexes=args.rebuild_indexes,
            )
        else:
            logger.info("Running pre-scored ranking pipeline...")
            rank(
                args.retrieval,
                args.ranking,
                args.output,
                candidates_jsonl=args.candidates,
                jd_text=jd_text,
            )

        logger.info("Ranking complete. Output written to: %s", args.output)
        logger.info("  - CSV: %s", args.output)
        logger.info("  - Metadata: %s.metadata.json", args.output)
        logger.info("  - Debug: %s.top100.json", args.output)
    except Exception as exc:
        logger.error("Ranking failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
