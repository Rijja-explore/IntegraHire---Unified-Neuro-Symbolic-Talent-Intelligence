"""
FAISS dense vector index for efficient similarity search.

Provides efficient indexing and retrieval of embeddings using
the FAISS library with CPU-only operation.
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np

from .config import get_config

logger = logging.getLogger(__name__)


class FAISSIndex:
    """
    FAISS index for dense vector similarity search.

    Supports:
    - Multiple index types (flat, IVF)
    - Cosine and L2 similarity
    - Efficient top-k retrieval
    - Persistence to disk
    """

    def __init__(self, embedding_dim: int, index_type: Optional[str] = None):
        """
        Initialize FAISS index.

        Args:
            embedding_dim: Dimension of embeddings
            index_type: Type of index. If None, uses config default.
        """
        self.config = get_config().faiss
        self.embedding_dim = embedding_dim
        self.index_type = index_type or self.config.index_type
        self.index: Optional[faiss.Index] = None
        self.candidate_ids: List[str] = []
        self._initialize_index()

    def _initialize_index(self):
        """Initialize the FAISS index."""
        if self.index_type == "flat":
            self._create_flat_index()
        elif self.index_type == "ivf":
            self._create_ivf_index()
        else:
            logger.warning(f"Unknown index type {self.index_type}, using flat")
            self._create_flat_index()

    def _create_flat_index(self):
        """Create a flat (brute-force) index with cosine similarity."""
        # Use InnerProduct metric for normalized vectors (equivalent to cosine)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        logger.info(f"Created flat FAISS index for {self.embedding_dim}-d vectors")

    def _create_ivf_index(self):
        """Create an IVF (Inverted File) index."""
        # Quantizer for IVF
        quantizer = faiss.IndexFlatIP(self.embedding_dim)
        # IVF with 100 partitions as default
        nlist = max(100, min(1000, 100000 // self.embedding_dim))
        self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist, faiss.METRIC_INNER_PRODUCT)
        logger.info(f"Created IVF FAISS index with {nlist} partitions")

    def add_embeddings(self, embeddings: np.ndarray, candidate_ids: List[str]):
        """
        Add embeddings to the index.

        Args:
            embeddings: Array of shape (n_candidates, embedding_dim)
            candidate_ids: List of candidate IDs
        """
        if len(embeddings) != len(candidate_ids):
            raise ValueError(f"Embedding count ({len(embeddings)}) != candidate ID count ({len(candidate_ids)})")

        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        # Ensure embeddings are normalized (for cosine similarity)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms

        logger.info(f"Adding {len(embeddings)} embeddings to FAISS index")
        start_time = time.time()

        # For IVF, need to train first
        if isinstance(self.index, faiss.IndexIVFFlat):
            if not self.index.is_trained:
                logger.info("Training IVF index...")
                self.index.train(embeddings)

        self.index.add(embeddings)
        self.candidate_ids.extend(candidate_ids)

        elapsed = time.time() - start_time
        logger.info(f"Added embeddings in {elapsed:.2f}s. Total: {self.index.ntotal}")

    def search(self, query_embedding: np.ndarray, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: Query embedding of shape (embedding_dim,) or (1, embedding_dim)
            top_k: Number of results to return

        Returns:
            List of (candidate_id, similarity_score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            raise ValueError("Index is empty. Call add_embeddings() first.")

        top_k = top_k or self.config.top_k

        # Ensure query is 2D and float32
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)

        # Normalize query
        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm

        # Set IVF parameters if applicable
        if isinstance(self.index, faiss.IndexIVFFlat):
            self.index.nprobe = self.config.nprobe

        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:  # -1 means no result
                candidate_id = self.candidate_ids[idx]
                # Convert distance to similarity (already a similarity for IP metric)
                similarity = float(dist)
                results.append((candidate_id, similarity))

        return results

    def search_with_ranks(self, query_embedding: np.ndarray, top_k: Optional[int] = None) -> List[dict]:
        """
        Search with rank information.

        Args:
            query_embedding: Query embedding
            top_k: Number of results

        Returns:
            List of dicts with candidate_id, similarity, and rank
        """
        results = self.search(query_embedding, top_k)
        return [{"candidate_id": cid, "similarity": sim, "rank": rank} for rank, (cid, sim) in enumerate(results, 1)]

    def save_index(self, file_path: Path):
        """
        Save index to disk.

        Args:
            file_path: Path to save index
        """
        if self.index is None:
            raise ValueError("No index to save")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = file_path.with_suffix(".faiss")
        faiss.write_index(self.index, str(index_path))

        # Save metadata
        metadata = {
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "num_candidates": self.index.ntotal,
            "candidate_ids": self.candidate_ids,
        }

        metadata_path = file_path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"FAISS index saved to {index_path}")

    def load_index(self, file_path: Path):
        """
        Load index from disk.

        Args:
            file_path: Path to index file
        """
        index_path = file_path.with_suffix(".faiss")
        metadata_path = file_path.with_suffix(".json")

        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Load FAISS index
        self.index = faiss.read_index(str(index_path))
        self.candidate_ids = metadata["candidate_ids"]

        logger.info(f"FAISS index loaded. Candidates: {len(self.candidate_ids)}")

    def get_index_info(self) -> dict:
        """Get information about the index."""
        return {
            "num_candidates": len(self.candidate_ids),
            "embedding_dim": self.embedding_dim,
            "index_type": self.index_type,
            "is_trained": self.index.is_trained if hasattr(self.index, "is_trained") else True,
            "total_vectors": self.index.ntotal if self.index else 0,
        }
