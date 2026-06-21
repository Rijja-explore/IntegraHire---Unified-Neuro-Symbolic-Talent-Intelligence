"""
Quick start guide for the retrieval engine.

Run this to get started with minimal setup.
"""

import json
from pathlib import Path

from retrieval.retrieval_engine import RetrievalEngine
from retrieval.utils import get_logger

logger = get_logger(__name__)


def quickstart():
    """Quick start example."""
    logger.info("RETRIEVAL ENGINE QUICK START")
    logger.info("-" * 50)

    # Setup
    project_root = Path(__file__).parent.parent.parent
    candidates_file = project_root / "candidates.jsonl"
    index_dir = project_root / "retrieval_indices_quickstart"

    # Initialize engine
    logger.info("1. Initializing engine...")
    engine = RetrievalEngine(index_dir=index_dir)

    # Build or load indexes
    if not (index_dir / "bm25_index.json").exists():
        logger.info("2. Building indexes (this may take a minute)...")
        stats = engine.build_indexes(candidates_file)
        logger.info(f"   Built indexes for {stats['total_candidates']} candidates")
    else:
        logger.info("2. Loading existing indexes...")
        engine.load_indexes(candidates_file)

    # Retrieve candidates
    logger.info("3. Retrieving candidates...")
    job_description = "Machine Learning Engineer with Python and Spark experience"

    response = engine.retrieve_by_text(job_description, top_k=10)

    # Display results
    logger.info(f"\n4. Top {len(response.candidates)} Results:")
    for i, candidate in enumerate(response.candidates, 1):
        logger.info(
            f"   {i}. {candidate.candidate_id}: " f"Score={candidate.semantic_score:.4f} "
            f"(BM25: {candidate.bm25_score:.4f}, Embedding: {candidate.embedding_score:.4f})"
        )

    logger.info("\n✓ Quick start completed!")


if __name__ == "__main__":
    quickstart()
