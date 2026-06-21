"""
Tests for BM25 and FAISS retrieval components.
"""

import unittest

import numpy as np

from retrieval.bm25_index import BM25Index
from retrieval.faiss_index import FAISSIndex
from retrieval.fusion import ReciprocalRankFusion
from retrieval.preprocessing import CandidatePreprocessor
from retrieval.schemas import CandidateProfile, CareerEntry, CandidateRawData


class TestBM25Index(unittest.TestCase):
    """Test BM25 indexing and retrieval."""

    def setUp(self):
        """Set up test fixtures."""
        self.bm25 = BM25Index()
        self.preprocessor = CandidatePreprocessor()

    def create_test_candidates(self, count=10):
        """Create test candidates."""
        candidates = []

        for i in range(count):
            profile = CandidateProfile(
                anonymized_name=f"Candidate {i}",
                headline=f"Role {i}",
                summary=f"Python developer with experience in machine learning and data science.",
                location="NYC",
                country="USA",
                years_of_experience=float(i + 1),
                current_title=f"Engineer {i}",
                current_company=f"Company {i}",
                current_company_size="501-1000",
                current_industry="Tech",
            )

            career = CareerEntry(
                company=f"Company {i}",
                title=f"Engineer {i}",
                start_date="2020-01-01",
                end_date=None,
                duration_months=24,
                is_current=True,
                industry="Tech",
                company_size="501-1000",
                description="Experience with Python, ML, and cloud platforms.",
            )

            candidate = CandidateRawData(
                candidate_id=f"CAND_{i:07d}",
                profile=profile,
                career_history=[career],
            )

            processed = self.preprocessor.preprocess_candidate(candidate)
            candidates.append(processed)

        return candidates

    def test_build_index(self):
        """Test BM25 index building."""
        candidates = self.create_test_candidates(10)
        self.bm25.build_index(candidates)

        self.assertEqual(len(self.bm25.candidates), 10)
        self.assertIsNotNone(self.bm25.bm25)

    def test_retrieve_query(self):
        """Test BM25 retrieval."""
        candidates = self.create_test_candidates(10)
        self.bm25.build_index(candidates)

        results = self.bm25.retrieve("Python machine learning", top_k=5)

        self.assertLessEqual(len(results), 5)
        self.assertTrue(all(isinstance(r, tuple) and len(r) == 2 for r in results))
        # Results should be sorted by score
        scores = [r[1] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieve_with_ranks(self):
        """Test BM25 retrieval with rank information."""
        candidates = self.create_test_candidates(10)
        self.bm25.build_index(candidates)

        results = self.bm25.retrieve_with_ranks("Python developer", top_k=5)

        self.assertLessEqual(len(results), 5)
        for rank, result in enumerate(results, 1):
            self.assertEqual(result["rank"], rank)


class TestFAISSIndex(unittest.TestCase):
    """Test FAISS indexing and retrieval."""

    def setUp(self):
        """Set up test fixtures."""
        self.embedding_dim = 384
        self.faiss = FAISSIndex(self.embedding_dim)

    def test_add_embeddings(self):
        """Test adding embeddings to index."""
        embeddings = np.random.randn(10, self.embedding_dim).astype(np.float32)
        candidate_ids = [f"CAND_{i:07d}" for i in range(10)]

        self.faiss.add_embeddings(embeddings, candidate_ids)

        self.assertEqual(len(self.faiss.candidate_ids), 10)
        self.assertEqual(self.faiss.index.ntotal, 10)

    def test_search(self):
        """Test FAISS search."""
        embeddings = np.random.randn(10, self.embedding_dim).astype(np.float32)
        candidate_ids = [f"CAND_{i:07d}" for i in range(10)]

        self.faiss.add_embeddings(embeddings, candidate_ids)

        query = np.random.randn(self.embedding_dim).astype(np.float32)
        results = self.faiss.search(query, top_k=5)

        self.assertLessEqual(len(results), 5)
        self.assertTrue(all(isinstance(r, tuple) and len(r) == 2 for r in results))

    def test_search_1d_query(self):
        """Test FAISS search with 1D query."""
        embeddings = np.random.randn(10, self.embedding_dim).astype(np.float32)
        candidate_ids = [f"CAND_{i:07d}" for i in range(10)]

        self.faiss.add_embeddings(embeddings, candidate_ids)

        # 1D query
        query = np.random.randn(self.embedding_dim).astype(np.float32)
        results = self.faiss.search(query, top_k=5)

        self.assertLessEqual(len(results), 5)


class TestReciprocalRankFusion(unittest.TestCase):
    """Test RRF fusion."""

    def setUp(self):
        """Set up test fixtures."""
        self.rrf = ReciprocalRankFusion(k=60)

    def test_fuse_rankings(self):
        """Test fusion of two rankings."""
        bm25_results = [
            ("CAND_0000001", 10.0),
            ("CAND_0000002", 8.0),
            ("CAND_0000003", 6.0),
        ]

        embedding_results = [
            ("CAND_0000002", 0.9),
            ("CAND_0000001", 0.85),
            ("CAND_0000004", 0.8),
        ]

        fused = self.rrf.fuse_rankings(bm25_results, embedding_results)

        self.assertGreaterEqual(len(fused), 3)
        # All candidates from both lists should be included
        candidate_ids = {c[0] for c in fused}
        self.assertIn("CAND_0000001", candidate_ids)
        self.assertIn("CAND_0000002", candidate_ids)

    def test_rrf_component(self):
        """Test RRF component calculation."""
        component = self.rrf.calculate_rrf_component(rank=1, k=60)

        self.assertEqual(component, 1.0 / 61)

    def test_normalize_scores(self):
        """Test score normalization."""
        results = [
            ("CAND_0000001", 0.5),
            ("CAND_0000002", 0.2),
            ("CAND_0000003", 0.9),
        ]

        normalized = self.rrf.normalize_scores(results)

        self.assertEqual(len(normalized), 3)
        # Check that scores are normalized to 0-1
        for _, score in normalized:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
