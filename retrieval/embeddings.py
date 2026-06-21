"""
Embedding pipeline for generating dense vector representations.

Uses sentence-transformers with BAAI/bge-small-en-v1.5 model.
Implements efficient batch processing, caching, and persistence.
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import get_config
from .utils import batch_iterator

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings for text using sentence-transformers.

    Features:
    - Lazy model loading
    - Batch processing
    - Optional caching
    - Persistence to disk
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding generator.

        Args:
            model_name: Model name to use. If None, uses config default.
        """
        self.config = get_config().embedding
        self.model_name = model_name or self.config.model_name
        self.model: Optional[SentenceTransformer] = None
        self.cache_dir = self.config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.config.device)
            logger.info(f"Model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")

    def generate_embeddings(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            show_progress: Whether to show progress bar

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        self._load_model()

        logger.info(f"Generating embeddings for {len(texts)} texts")
        start_time = time.time()

        embeddings_list = []

        # Process in batches
        for batch in batch_iterator(texts, self.config.batch_size):
            batch_embeddings = self.model.encode(
                batch, convert_to_numpy=True, show_progress_bar=show_progress, batch_size=len(batch)
            )

            if self.config.normalize:
                batch_embeddings = self._normalize_embeddings(batch_embeddings)

            embeddings_list.append(batch_embeddings)

        # Concatenate all batches
        embeddings = np.vstack(embeddings_list) if embeddings_list else np.array([])

        elapsed = time.time() - start_time
        logger.info(f"Embedding generation completed in {elapsed:.2f}s. Shape: {embeddings.shape}")

        return embeddings

    def generate_embeddings_to_disk(self, texts: List[str], file_path: Path, show_progress: bool = True) -> Tuple[Path, dict]:
        """
        Generate embeddings and write them incrementally to disk using a memory-mapped .npy file.

        This avoids holding the full embedding matrix in memory for large corpora.

        Args:
            texts: List of text strings
            file_path: Path to write the .npy memmap
            show_progress: Whether to show progress bars

        Returns:
            Tuple of (file_path, metadata)
        """
        if not texts:
            raise ValueError("No texts provided")

        self._load_model()

        n = len(texts)
        dim = self.model.get_sentence_embedding_dimension()

        # Create a .npy memmap for incremental writes
        file_path.parent.mkdir(parents=True, exist_ok=True)
        memmap = np.lib.format.open_memmap(str(file_path), mode="w+", dtype="float32", shape=(n, dim))

        idx = 0
        for batch in batch_iterator(texts, self.config.batch_size):
            batch_embeddings = self.model.encode(
                batch, convert_to_numpy=True, show_progress_bar=show_progress, batch_size=len(batch)
            )

            if self.config.normalize:
                batch_embeddings = self._normalize_embeddings(batch_embeddings)

            if batch_embeddings.dtype != np.float32:
                batch_embeddings = batch_embeddings.astype(np.float32)

            memmap[idx : idx + len(batch_embeddings), :] = batch_embeddings
            idx += len(batch_embeddings)

        # Save metadata
        metadata = {
            "shape": (n, dim),
            "dtype": "float32",
            "model": self.model_name,
            "normalized": self.config.normalize,
        }
        metadata_path = file_path.with_suffix(".meta.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Wrote embeddings memmap to {file_path} (shape={n},{dim})")
        return file_path, metadata

    def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            1D numpy array of shape (embedding_dim,)
        """
        self._load_model()
        embedding = self.model.encode([text], convert_to_numpy=True)[0]

        if self.config.normalize:
            embedding = self._normalize_embedding(embedding)

        return embedding

    @staticmethod
    def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        """Normalize a single embedding to unit length."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding

    @staticmethod
    def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        return embeddings / norms

    def save_embeddings(self, embeddings: np.ndarray, file_path: Path, metadata: Optional[dict] = None):
        """
        Save embeddings to disk.

        Args:
            embeddings: Embeddings array
            file_path: Path to save file
            metadata: Optional metadata to save with embeddings
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save embeddings
        np.save(file_path, embeddings)

        # Save metadata
        metadata_path = file_path.with_suffix(".meta.json")
        meta = {
            "shape": embeddings.shape,
            "dtype": str(embeddings.dtype),
            "model": self.model_name,
            "normalized": self.config.normalize,
        }
        if metadata:
            meta.update(metadata)

        with open(metadata_path, "w") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"Saved embeddings to {file_path}")

    def load_embeddings(self, file_path: Path) -> Tuple[np.ndarray, dict]:
        """
        Load embeddings from disk.

        Args:
            file_path: Path to embeddings file

        Returns:
            Tuple of (embeddings array, metadata dictionary)
        """
        # Use memory-mapped load to avoid allocating the full array in memory
        embeddings = np.load(file_path, mmap_mode="r")

        metadata_path = file_path.with_suffix(".meta.json")
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

        logger.info(f"Loaded embeddings from {file_path}. Shape: {embeddings.shape}")
        return embeddings, metadata

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        self._load_model()
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "device": self.config.device,
            "normalized": self.config.normalize,
        }


class EmbeddingCache:
    """Manages caching of embeddings to avoid recomputation."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache. If None, uses config default.
        """
        self.cache_dir = cache_dir or get_config().embedding.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        import hashlib

        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Get cached embedding for text.

        Args:
            text: Text to look up

        Returns:
            Embedding if cached, None otherwise
        """
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.npy"

        if cache_file.exists():
            logger.debug(f"Cache hit for: {text[:50]}...")
            return np.load(cache_file)

        return None

    def put(self, text: str, embedding: np.ndarray):
        """
        Cache embedding for text.

        Args:
            text: Text to cache
            embedding: Embedding vector
        """
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.npy"
        np.save(cache_file, embedding)

    def clear(self):
        """Clear all cached embeddings."""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Embedding cache cleared")
