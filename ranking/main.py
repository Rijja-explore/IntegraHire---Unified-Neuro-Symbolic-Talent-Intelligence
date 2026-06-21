"""Main script to demonstrate the candidate ranking system."""
import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import sys

# Add ranking module to path
sys.path.insert(0, str(Path(__file__).parent))

from .schemas import CandidateProfile
from .feature_store import CandidateRankingPipeline
from .config import DEFAULT_SCORING_WEIGHTS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_candidates_batch(jsonl_path: str, batch_size: int = 100, max_batches: int = None) -> List[CandidateProfile]:
    """Load candidates from JSONL file in batches."""
    candidates = []
    batch_count = 0

    with open(jsonl_path, 'r') as f:
        for i, line in enumerate(f):
            if max_batches and batch_count >= max_batches:
                break

            try:
                data = json.loads(line.strip())
                # Merge profile and metadata
                profile_data = {**data['profile'], **data}
                profile_data.pop('profile', None)

                candidate = CandidateProfile(**profile_data)
                candidates.append(candidate)

                if (i + 1) % batch_size == 0:
                    batch_count += 1
                    logger.info(f"Loaded {i + 1} candidates ({batch_count} batches)")

            except Exception as e:
                logger.warning(f"Failed to parse candidate {i}: {e}")
                continue

    logger.info(f"Total candidates loaded: {len(candidates)}")
    return candidates

def load_retrieval_results(jsonl_path: str) -> Dict[str, Dict]:
    """Load retrieval scores from JSON."""
    results = {}
    with open(jsonl_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            results[data['candidate_id']] = {
                'semantic_score': data.get('semantic_score', 50.0),
                'bm25_score': data.get('bm25_score', 50.0),
                'embedding_score': data.get('embedding_score', 50.0),
            }
    return results

def main():
    """Main ranking pipeline."""
    logger.info("=" * 80)
    logger.info("Candidate Intelligence & Ranking System")
    logger.info("=" * 80)

    # Configuration
    candidates_path = "d:/Projects/Resume/candidates.jsonl"
    output_path = "d:/Projects/Resume/ranking_results.jsonl"
    top_k = 100

    # Load small sample for demo (first 1000 candidates)
    logger.info("Loading candidates...")
    candidates = load_candidates_batch(candidates_path, batch_size=100, max_batches=10)

    if not candidates:
        logger.error("No candidates loaded!")
        return

    logger.info(f"Loaded {len(candidates)} candidates for ranking")

    # Initialize pipeline
    logger.info("Initializing ranking pipeline...")
    pipeline = CandidateRankingPipeline(scoring_weights=DEFAULT_SCORING_WEIGHTS)

    # Fit on candidate pool
    logger.info("Fitting anomaly detector on candidate pool...")
    pipeline.fit(candidates)

    # Create mock retrieval scores (BM25 baseline)
    logger.info("Computing baseline retrieval scores...")
    semantic_scores = {}
    for candidate in candidates:
        # Simple heuristic: experience and skills as proxy for relevance
        base_score = candidate.profile.years_of_experience * 5
        skill_bonus = min(30, len(candidate.skills))
        semantic_scores[candidate.candidate_id] = min(100, base_score + skill_bonus)

    # Process all candidates
    logger.info("Processing candidates through all engines...")
    start_time = datetime.now()

    all_scores = pipeline.process_batch(candidates, semantic_scores)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Processed {len(all_scores)} candidates in {elapsed:.2f}s "
        f"({len(all_scores)/elapsed:.1f} candidates/sec)"
    )

    # Rank candidates
    logger.info("Ranking candidates...")
    ranked_candidates = pipeline.rank(all_scores)

    # Output top candidates
    logger.info("=" * 80)
    logger.info(f"TOP {min(top_k, len(ranked_candidates))} CANDIDATES")
    logger.info("=" * 80)

    for ranked in ranked_candidates[:top_k]:
        logger.info(
            f"Rank {ranked.rank}: {ranked.candidate_id} "
            f"(score: {ranked.final_score:.1f}) "
            f"[Auth:{ranked.authenticity_score:.0f} Prod:{ranked.production_score:.0f} "
            f"Behav:{ranked.behavior_score:.0f}]"
        )

        if ranked.top_strengths:
            logger.info(f"  Strengths: {', '.join(ranked.top_strengths[:2])}")
        if ranked.top_weaknesses:
            logger.info(f"  Weaknesses: {', '.join(ranked.top_weaknesses[:2])}")

    # Save results
    logger.info(f"Saving results to {output_path}...")
    with open(output_path, 'w') as f:
        for ranked in ranked_candidates[:top_k]:
            result = {
                "rank": ranked.rank,
                "candidate_id": ranked.candidate_id,
                "final_score": round(ranked.final_score, 2),
                "semantic_score": round(ranked.semantic_score, 2),
                "authenticity_score": round(ranked.authenticity_score, 2),
                "trajectory_score": round(ranked.trajectory_score, 2),
                "production_score": round(ranked.production_score, 2),
                "behavior_score": round(ranked.behavior_score, 2),
                "dna": {
                    "technical_depth": round(ranked.dna_dimensions.technical_depth, 1),
                    "production_readiness": round(ranked.dna_dimensions.production_readiness, 1),
                    "startup_fit": round(ranked.dna_dimensions.startup_fit, 1),
                    "career_stability": round(ranked.dna_dimensions.career_stability, 1),
                },
                "top_strengths": ranked.top_strengths,
                "top_weaknesses": ranked.top_weaknesses,
            }
            f.write(json.dumps(result) + "\n")

    # Example explanation
    logger.info("=" * 80)
    logger.info("EXAMPLE SCORE EXPLANATION")
    logger.info("=" * 80)

    if ranked_candidates:
        top_candidate = ranked_candidates[0]
        explanation = pipeline.explain_score(top_candidate.candidate_id)
        logger.info(json.dumps(explanation, indent=2))

    logger.info("=" * 80)
    logger.info("Pipeline execution complete!")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
