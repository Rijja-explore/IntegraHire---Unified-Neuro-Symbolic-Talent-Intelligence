"""
Comprehensive end-to-end example of the retrieval engine.

Demonstrates:
1. Building indexes from candidate data
2. Retrieving candidates for a job description
3. Processing and scoring results
"""

import json
import sys
import time
from pathlib import Path

from retrieval.retrieval_engine import RetrievalEngine
from retrieval.utils import get_logger

logger = get_logger(__name__)


def load_sample_job_description() -> str:
    """Load a sample job description."""
    return """
    Senior Machine Learning Engineer
    
    We are looking for an experienced ML Engineer to join our team.
    
    Required:
    - 5+ years of experience in ML/Data Science
    - Proficiency in Python, TensorFlow, PyTorch
    - Experience with NLP, computer vision, or retrieval systems
    - Strong understanding of distributed systems and Spark
    - Experience with cloud platforms (AWS, GCP, Azure)
    
    Nice to have:
    - Experience with FAISS or vector databases
    - Contributions to open-source ML projects
    - Experience with A/B testing and ML evaluation
    - Knowledge of LLMs or transformers
    - Publication track record in top-tier ML conferences
    
    Responsibilities:
    - Design and implement scalable ML systems
    - Build and optimize deep learning models
    - Collaborate with data engineers on feature pipelines
    - Evaluate model performance and iterate on improvements
    - Mentor junior engineers on ML best practices
    """


def main():
    """Run end-to-end example."""
    logger.info("=" * 80)
    logger.info("RETRIEVAL ENGINE END-TO-END EXAMPLE")
    logger.info("=" * 80)

    # Setup paths
    project_root = Path(__file__).parent.parent
    candidates_file = project_root / "candidates.jsonl"
    index_dir = project_root / "retrieval_indices"

    if not candidates_file.exists():
        logger.error(f"Candidates file not found: {candidates_file}")
        logger.error("Please ensure candidates.jsonl exists in the project root")
        return 1

    try:
        # Initialize engine
        logger.info("\n[1] Initializing retrieval engine...")
        engine = RetrievalEngine(index_dir=index_dir)
        system_info = engine.get_system_info()
        logger.info(f"System config: {json.dumps(system_info['config'], indent=2)}")

        # Check if indexes exist
        indexes_exist = (index_dir / "bm25_index.json").exists() and (index_dir / "faiss_index.faiss").exists()

        if indexes_exist:
            logger.info("\n[2] Loading existing indexes...")
            engine.load_indexes(candidates_file)
            logger.info(f"✓ Loaded {len(engine.candidates)} candidates")
        else:
            logger.info("\n[2] Building indexes from candidate data...")
            logger.info(f"Loading candidates from: {candidates_file}")

            build_start = time.time()
            stats = engine.build_indexes(candidates_file)

            build_time = time.time() - build_start
            logger.info(f"✓ Build completed in {build_time:.2f}s")
            logger.info(f"  - Total candidates: {stats['total_candidates']}")
            logger.info(f"  - Embeddings shape: {stats['embeddings_shape']}")
            logger.info(f"  - BM25 index: {stats['bm25_index_info']}")
            logger.info(f"  - FAISS index: {stats['faiss_index_info']}")

        # Display system info
        logger.info("\n[3] System information:")
        system_info = engine.get_system_info()
        logger.info(f"  - Candidates indexed: {system_info['state']['num_candidates']}")
        logger.info(f"  - Embeddings dimension: {system_info['state']['embeddings_shape'][1] if system_info['state']['embeddings_shape'] else 'N/A'}")

        # Retrieve candidates
        logger.info("\n[4] Retrieving candidates for job description...")
        job_description = load_sample_job_description()

        retrieval_start = time.time()
        response = engine.retrieve_by_text(job_description, top_k=20, min_score=0.0)
        retrieval_time = time.time() - retrieval_start

        logger.info(f"✓ Retrieval completed in {response.retrieval_latency_ms:.0f}ms")
        logger.info(f"  - Total candidates searched: {response.total_candidates_searched}")
        logger.info(f"  - Top candidates returned: {len(response.candidates)}")

        # Display results
        logger.info("\n[5] Top 10 Retrieved Candidates:")
        logger.info("-" * 120)
        logger.info(
            f"{'Rank':<6} {'Candidate ID':<15} {'BM25 Score':<12} {'Embedding Sim':<14} {'Final Score':<12} "
            f"{'BM25 Rank':<10} {'Emb Rank':<10}"
        )
        logger.info("-" * 120)

        for candidate in response.candidates[:10]:
            logger.info(
                f"{candidate.retrieval_rank:<6} {candidate.candidate_id:<15} "
                f"{candidate.bm25_score:<12.4f} {candidate.embedding_score:<14.4f} "
                f"{candidate.semantic_score:<12.4f} {candidate.bm25_rank:<10} {candidate.embedding_rank:<10}"
            )

        # Detailed view of top candidate
        if response.candidates:
            logger.info("\n[6] Detailed Profile of Top Candidate:")
            logger.info("-" * 80)

            top_candidate = response.candidates[0]
            profile = engine.get_candidate_profile(top_candidate.candidate_id)

            if profile:
                logger.info(f"Candidate ID: {profile['candidate_id']}")
                logger.info(f"Years of Experience: {profile['metadata'].get('years_of_experience', 'N/A')}")
                logger.info(f"Location: {profile['metadata'].get('location', 'N/A')}")
                logger.info(f"Current Company: {profile['metadata'].get('current_company', 'N/A')}")
                logger.info(f"Skills Count: {profile['metadata'].get('skills_count', 0)}")
                logger.info(f"\nProfile Text (first 500 chars):")
                logger.info(profile["profile_text"][:500])

        # Statistics
        logger.info("\n[7] Retrieval Statistics:")
        logger.info("-" * 80)

        bm25_scores = [c.bm25_score for c in response.candidates]
        embedding_scores = [c.embedding_score for c in response.candidates]
        final_scores = [c.semantic_score for c in response.candidates]

        logger.info(f"BM25 Scores - Min: {min(bm25_scores):.4f}, Max: {max(bm25_scores):.4f}, Mean: {sum(bm25_scores) / len(bm25_scores):.4f}")
        logger.info(
            f"Embedding Scores - Min: {min(embedding_scores):.4f}, Max: {max(embedding_scores):.4f}, Mean: {sum(embedding_scores) / len(embedding_scores):.4f}"
        )
        logger.info(f"Final Scores - Min: {min(final_scores):.4f}, Max: {max(final_scores):.4f}, Mean: {sum(final_scores) / len(final_scores):.4f}")

        # Save results to file
        output_file = project_root / "retrieval_results.json"
        results_data = {
            "job_description": job_description,
            "retrieval_time_ms": response.retrieval_latency_ms,
            "total_candidates_searched": response.total_candidates_searched,
            "candidates": [
                {
                    "rank": c.retrieval_rank,
                    "candidate_id": c.candidate_id,
                    "bm25_score": c.bm25_score,
                    "embedding_score": c.embedding_score,
                    "semantic_score": c.semantic_score,
                }
                for c in response.candidates[:50]
            ],
        }

        with open(output_file, "w") as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"\n[8] Results saved to: {output_file}")

        logger.info("\n" + "=" * 80)
        logger.info("✓ END-TO-END EXAMPLE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"\n✗ Error during execution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
