"""
Tests for utility functions.
"""

import unittest

import numpy as np

from retrieval.utils import (
    cosine_similarity,
    extract_keywords,
    normalize_scores,
    normalize_text,
    tokenize_text,
    get_stopwords,
)


class TestTextProcessingUtils(unittest.TestCase):
    """Test text processing utilities."""

    def test_normalize_text(self):
        """Test text normalization."""
        text = "  Hello   WORLD  !  "
        normalized = normalize_text(text)

        self.assertEqual(normalized, "hello world")

    def test_normalize_text_special_chars(self):
        """Test normalization with special characters."""
        text = "Python@#$%^Developer"
        normalized = normalize_text(text)

        self.assertNotIn("@", normalized)
        self.assertIn("python", normalized)

    def test_tokenize_text(self):
        """Test text tokenization."""
        text = "Python developer with machine learning experience"
        tokens = tokenize_text(text, remove_stopwords=True)

        self.assertIn("python", tokens)
        self.assertIn("developer", tokens)
        self.assertNotIn("with", tokens)  # stopword

    def test_tokenize_without_stopword_removal(self):
        """Test tokenization without stopword removal."""
        text = "Hello world"
        tokens = tokenize_text(text, remove_stopwords=False)

        self.assertGreaterEqual(len(tokens), 2)

    def test_get_stopwords(self):
        """Test stopwords retrieval."""
        stopwords = get_stopwords()

        self.assertIsInstance(stopwords, set)
        self.assertIn("the", stopwords)
        self.assertIn("is", stopwords)
        self.assertGreater(len(stopwords), 10)

    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "Python is great. Python is powerful. Developer develops with Python."
        keywords = extract_keywords(text, top_k=5)

        self.assertLessEqual(len(keywords), 5)
        self.assertIn("python", keywords)


class TestVectorUtils(unittest.TestCase):
    """Test vector utilities."""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])

        similarity = cosine_similarity(vec1, vec2)

        self.assertAlmostEqual(similarity, 1.0, places=5)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity for orthogonal vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])

        similarity = cosine_similarity(vec1, vec2)

        self.assertAlmostEqual(similarity, 0.0, places=5)

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity for opposite vectors."""
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([-1, 0, 0])

        similarity = cosine_similarity(vec1, vec2)

        self.assertAlmostEqual(similarity, -1.0, places=5)

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector."""
        vec1 = np.array([0, 0, 0])
        vec2 = np.array([1, 1, 1])

        similarity = cosine_similarity(vec1, vec2)

        self.assertEqual(similarity, 0.0)

    def test_normalize_scores(self):
        """Test score normalization."""
        scores = [1.0, 5.0, 10.0]
        normalized = normalize_scores(scores)

        self.assertEqual(len(normalized), 3)
        self.assertAlmostEqual(normalized[0], 0.0, places=5)
        self.assertAlmostEqual(normalized[2], 1.0, places=5)

    def test_normalize_scores_same_values(self):
        """Test normalization with identical scores."""
        scores = [5.0, 5.0, 5.0]
        normalized = normalize_scores(scores)

        self.assertEqual(len(normalized), 3)
        self.assertTrue(all(s == 0.0 for s in normalized))

    def test_normalize_scores_range(self):
        """Test normalization to custom range."""
        scores = [1.0, 5.0, 10.0]
        normalized = normalize_scores(scores, min_val=0.5, max_val=1.5)

        self.assertGreaterEqual(min(normalized), 0.5)
        self.assertLessEqual(max(normalized), 1.5)


if __name__ == "__main__":
    unittest.main()
