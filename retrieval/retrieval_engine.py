"""
Main retrieval and semantic intelligence engine.

Orchestrates the complete retrieval pipeline:
1. Job description processing
2. Candidate preprocessing
3. BM25 lexical retrieval
4. Dense embedding retrieval
5. Reciprocal Rank Fusion
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

import numpy as np

from .bm25_index import BM25Index
from .config import get_config
from .embeddings import EmbeddingGenerator
from .faiss_index import FAISSIndex
from .fusion import ReciprocalRankFusion
from .job_processor import JobDescriptionProcessor
from .preprocessing import CandidatePreprocessor
from .schemas import (
    CandidateRawData,
    CandidateRecord,
    JobDescription,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
)
from .utils import get_logger, load_jsonl

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """
    Production-grade retrieval engine for candidate ranking.

    Combines:
    - BM25 lexical retrieval
    - Dense embedding retrieval
    - Reciprocal Rank Fusion
    - Efficient indexing
    """

    def __init__(self, index_dir: Optional[Path] = None):
        """
        Initialize retrieval engine.

        Args:
            index_dir: Directory to store/load indices
        """
        self.config = get_config()
        self.index_dir = Path(index_dir or "./retrieval_indices")
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.preprocessor = CandidatePreprocessor()
        self.embedding_generator = EmbeddingGenerator()
        self.jd_processor = JobDescriptionProcessor()
        self.bm25_index: Optional[BM25Index] = None
        self.faiss_index: Optional[FAISSIndex] = None
        self.fusion = ReciprocalRankFusion()

        # State
        self.candidates: List[CandidateRecord] = []
        self.embeddings: Optional[np.ndarray] = None

        logger.info("RetrievalEngine initialized")

    def build_indexes(self, candidates_jsonl_path: Path) -> dict:
        """
        Build all indexes from candidate JSONL file.

        This is the initialization step for the system.

        Args:
            candidates_jsonl_path: Path to candidates.jsonl file

        Returns:
            Dictionary with build statistics
        """
        logger.info(f"Loading candidates from {candidates_jsonl_path}")
        build_start = time.time()

        # Count records first so we can size the embedding memmap without loading
        # the entire JSONL into memory.
        total_candidates = 0
        with open(candidates_jsonl_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    total_candidates += 1

        logger.info(f"Detected {total_candidates} candidate records")

        # Prepare streamed embedding generation.
        self.embedding_generator._load_model()
        embedding_dim = self.embedding_generator.model.get_sentence_embedding_dimension()
        embeddings_path = self.index_dir / "embeddings.npy"
        embeddings_memmap = np.lib.format.open_memmap(
            str(embeddings_path), mode="w+", dtype="float32", shape=(total_candidates, embedding_dim)
        )

        self.candidates = []
        candidate_ids: List[str] = []
        write_index = 0
        batch_records: List[CandidateRecord] = []
        batch_texts: List[str] = []
        batch_ids: List[str] = []
        parse_errors = 0

        # Stream JSONL line by line and process in bounded batches.
        with open(candidates_jsonl_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue

                try:
                    parsed = json.loads(line)
                    from src.common.normalizer import normalize_candidate_record

                    raw_candidate = CandidateRawData(**normalize_candidate_record(parsed))
                    candidate = self.preprocessor.preprocess_candidate(raw_candidate)
                except Exception as e:
                    parse_errors += 1
                    logger.warning(f"Failed to parse candidate: {e}")
                    continue

                batch_records.append(candidate)
                batch_texts.append(candidate.profile_text)
                batch_ids.append(candidate.candidate_id)

                if len(batch_texts) >= self.config.embedding.batch_size:
                    batch_embeddings = self.embedding_generator.model.encode(
                        batch_texts, convert_to_numpy=True, show_progress_bar=False, batch_size=len(batch_texts)
                    )

                    if self.embedding_generator.config.normalize:
                        batch_embeddings = self.embedding_generator._normalize_embeddings(batch_embeddings)

                    if batch_embeddings.dtype != np.float32:
                        batch_embeddings = batch_embeddings.astype(np.float32)

                    embeddings_memmap[write_index : write_index + len(batch_embeddings), :] = batch_embeddings
                    write_index += len(batch_embeddings)

                    self.candidates.extend(batch_records)
                    candidate_ids.extend(batch_ids)

                    batch_records = []
                    batch_texts = []
                    batch_ids = []

        if batch_texts:
            batch_embeddings = self.embedding_generator.model.encode(
                batch_texts, convert_to_numpy=True, show_progress_bar=False, batch_size=len(batch_texts)
            )

            if self.embedding_generator.config.normalize:
                batch_embeddings = self.embedding_generator._normalize_embeddings(batch_embeddings)

            if batch_embeddings.dtype != np.float32:
                batch_embeddings = batch_embeddings.astype(np.float32)

            embeddings_memmap[write_index : write_index + len(batch_embeddings), :] = batch_embeddings
            write_index += len(batch_embeddings)

            self.candidates.extend(batch_records)
            candidate_ids.extend(batch_ids)

        embeddings_memmap.flush()

        if parse_errors:
            logger.warning(f"Skipped {parse_errors} malformed candidate records")

        logger.info(f"Preprocessed {len(self.candidates)} candidates")

        # Keep a memory-mapped view for downstream use.
        self.embeddings = np.load(embeddings_path, mmap_mode="r")[:write_index]

        # Build BM25 index
        self.bm25_index = BM25Index()
        self.bm25_index.build_index(self.candidates)

        # Build FAISS index
        self.faiss_index = FAISSIndex(embedding_dim, self.config.faiss.index_type)

        # Add embeddings in bounded batches so the FAISS build never copies the
        # full corpus into memory at once.
        faiss_batch_size = max(256, self.config.embedding.batch_size)
        for start in range(0, write_index, faiss_batch_size):
            end = min(start + faiss_batch_size, write_index)
            self.faiss_index.add_embeddings(self.embeddings[start:end], candidate_ids[start:end])

        # Save indexes
        self._save_indexes()

        elapsed = time.time() - build_start
        logger.info(f"Index building completed in {elapsed:.2f}s")

        stats = {
            "total_candidates": len(self.candidates),
            "embeddings_shape": self.embeddings.shape,
            "bm25_index_info": self.bm25_index.get_index_info(),
            "faiss_index_info": self.faiss_index.get_index_info(),
            "build_time_seconds": elapsed,
        }

        return stats

    def retrieve_candidates(self, request: RetrievalRequest) -> RetrievalResponse:
        """
        Retrieve candidates matching a job description.

        Args:
            request: RetrievalRequest with job description and parameters

        Returns:
            RetrievalResponse with ranked candidates
        """
        if not self.bm25_index or not self.faiss_index:
            raise ValueError("Indexes not built. Call build_indexes() first.")

        retrieval_start = time.time()
        logger.info(f"Retrieving candidates for job (top_k={request.top_k})")

        # Process job description
        jd = self.jd_processor.process_job_description(request.job_description, generate_embedding=True)

        # Get JD embedding
        if jd.embedding is None:
            jd_embedding = self.embedding_generator.generate_single_embedding(jd.cleaned_text)
        else:
            jd_embedding = np.array(jd.embedding)

        # BM25 retrieval
        bm25_results = self.bm25_index.retrieve_with_ranks(jd.cleaned_text, top_k=request.top_k * 2)

        # FAISS retrieval
        faiss_results = self.faiss_index.search_with_ranks(jd_embedding, top_k=request.top_k * 2)

        # RRF fusion
        fused_results = self.fusion.fuse_with_metadata(bm25_results, faiss_results)

        # Filter by minimum score and limit to top_k
        filtered_results = [r for r in fused_results if r["fused_score"] >= request.min_score][: request.top_k]

        max_bm25 = max((r.get("bm25_score") or 0.0 for r in filtered_results), default=1.0) or 1.0
        max_fused = max((r.get("fused_score") or 0.0 for r in filtered_results), default=1.0) or 1.0

        # Convert to RetrievalResult objects
        retrieval_results = []
        for result in filtered_results:
            bm25_raw = result["bm25_score"] or 0.0
            fused_raw = result["fused_score"] or 0.0
            retrieval_result = RetrievalResult(
                candidate_id=result["candidate_id"],
                bm25_score=min(1.0, bm25_raw / max_bm25),
                bm25_rank=result["bm25_rank"] or 9999,
                embedding_score=min(1.0, max(0.0, result["embedding_similarity"] or 0.0)),
                embedding_rank=result["embedding_rank"] or 9999,
                semantic_score=min(1.0, fused_raw / max_fused),
                retrieval_rank=result["final_rank"],
            )
            retrieval_results.append(retrieval_result)

        elapsed = time.time() - retrieval_start

        logger.info(
            f"Retrieved {len(retrieval_results)} candidates in {elapsed:.2f}s "
            f"(searched {len(self.candidates)} total)"
        )

        response = RetrievalResponse(
            job_description=request.job_description,
            candidates=retrieval_results,
            total_candidates_searched=len(self.candidates),
            retrieval_latency_ms=elapsed * 1000,
            metadata={"jd_keywords": jd.keywords[:10], "jd_required_skills": jd.required_skills[:5]},
        )

        return response

    def retrieve_by_text(
        self, job_description: str, top_k: int = 100, min_score: float = 0.0
    ) -> RetrievalResponse:
        """
        Convenience method to retrieve candidates by job description text.

        Args:
            job_description: Job description text
            top_k: Number of candidates to retrieve
            min_score: Minimum retrieval score

        Returns:
            RetrievalResponse
        """
        request = RetrievalRequest(job_description=job_description, top_k=top_k, min_score=min_score)

        return self.retrieve_candidates(request)

    def get_candidate_profile(self, candidate_id: str) -> Optional[dict]:
        """
        Get full profile of a candidate.

        Args:
            candidate_id: Candidate ID

        Returns:
            Candidate record or None if not found
        """
        for candidate in self.candidates:
            if candidate.candidate_id == candidate_id:
                return {
                    "candidate_id": candidate.candidate_id,
                    "profile_text": candidate.profile_text,
                    "metadata": candidate.metadata,
                    "raw_data": candidate.raw_data.dict(),
                }

        return None

    def _save_indexes(self):
        """Save all indexes to disk."""
        embeddings_path = self.index_dir / "embeddings.npy"
        if self.embeddings is not None and not embeddings_path.exists():
            self.embedding_generator.save_embeddings(
                self.embeddings, embeddings_path, metadata={"num_candidates": len(self.candidates)}
            )

        if self.bm25_index:
            bm25_path = self.index_dir / "bm25_index"
            self.bm25_index.save_index(bm25_path)

        if self.faiss_index:
            faiss_path = self.index_dir / "faiss_index"
            self.faiss_index.save_index(faiss_path)

        logger.info(f"All indexes saved to {self.index_dir}")

    def load_indexes(self, candidates_jsonl_path: Path):
        """
        Load all indexes from disk.

        Args:
            candidates_jsonl_path: Path to candidates JSONL for reference
        """
        # Load candidates and preprocess
        from src.common.normalizer import normalize_candidate_record

        raw_data = load_jsonl(candidates_jsonl_path)
        raw_candidates = [CandidateRawData(**normalize_candidate_record(item)) for item in raw_data]
        self.candidates = self.preprocessor.batch_preprocess(raw_candidates)

        # Load embeddings
        embeddings_path = self.index_dir / "embeddings.npy"
        if embeddings_path.exists():
            self.embeddings, _ = self.embedding_generator.load_embeddings(embeddings_path)

        # Load BM25 index
        bm25_path = self.index_dir / "bm25_index"
        if bm25_path.with_suffix(".json").exists():
            self.bm25_index = BM25Index()
            self.bm25_index.load_index(bm25_path, self.candidates)

        # Load FAISS index
        faiss_path = self.index_dir / "faiss_index"
        if faiss_path.with_suffix(".faiss").exists():
            embedding_dim = self.embeddings.shape[1] if self.embeddings is not None else 384
            self.faiss_index = FAISSIndex(embedding_dim)
            self.faiss_index.load_index(faiss_path)

        logger.info(f"Indexes loaded from {self.index_dir}")

    def get_system_info(self) -> dict:
        """Get system information and statistics."""
        return {
            "config": {
                "embedding_model": self.config.embedding.model_name,
                "bm25_k1": self.config.bm25.k1,
                "bm25_b": self.config.bm25.b,
                "rrf_k": self.fusion.k,
                "bm25_weight": self.config.retrieval.bm25_weight,
                "embedding_weight": self.config.retrieval.embedding_weight,
            },
            "indexes": {
                "bm25": self.bm25_index.get_index_info() if self.bm25_index else None,
                "faiss": self.faiss_index.get_index_info() if self.faiss_index else None,
            },
            "state": {
                "num_candidates": len(self.candidates),
                "embeddings_shape": self.embeddings.shape if self.embeddings is not None else None,
            },
        }
