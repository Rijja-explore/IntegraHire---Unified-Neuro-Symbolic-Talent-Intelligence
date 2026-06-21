#!/usr/bin/env python3
"""Benchmark the full ranking pipeline for hackathon compliance."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - Windows
    resource = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline.rank_pipeline import rank_from_candidates  # noqa: E402


def _peak_memory_mb() -> float:
    if resource is None:
        try:
            import psutil

            return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "win32":
        return usage / (1024 * 1024)
    return usage / 1024


def run_benchmark(
    candidates: str,
    job_description: str,
    output: str,
    *,
    index_dir: str | None = None,
    rebuild_indexes: bool = False,
) -> dict:
    start = time.perf_counter()
    rank_from_candidates(
        candidates,
        Path(job_description).read_text(encoding="utf-8").strip(),
        output,
        index_dir=index_dir,
        rebuild_indexes=rebuild_indexes,
    )
    elapsed = time.perf_counter() - start
    return {
        "elapsed_seconds": round(elapsed, 2),
        "peak_memory_mb": round(_peak_memory_mb(), 2),
        "output_csv": output,
        "output_exists": Path(output).exists(),
        "metadata_exists": Path(f"{output}.metadata.json").exists(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark IntegraHire full pipeline.")
    parser.add_argument("--candidates", default="data/candidates.jsonl")
    parser.add_argument("--job_description", default="data/job_description.txt")
    parser.add_argument("--output", default="submission.csv")
    parser.add_argument("--index-dir", default=None)
    parser.add_argument("--rebuild-indexes", action="store_true")
    parser.add_argument("--report", default="benchmark_report.json")
    args = parser.parse_args()

    report = run_benchmark(
        args.candidates,
        args.job_description,
        args.output,
        index_dir=args.index_dir,
        rebuild_indexes=args.rebuild_indexes,
    )
    report["runtime_pass"] = report["elapsed_seconds"] <= 300
    report["memory_pass"] = report["peak_memory_mb"] <= 16384

    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
