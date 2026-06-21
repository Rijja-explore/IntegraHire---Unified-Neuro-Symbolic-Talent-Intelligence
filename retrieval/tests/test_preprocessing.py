"""
Tests for preprocessing module.
"""

import unittest

from retrieval.preprocessing import CandidatePreprocessor
from retrieval.schemas import CandidateRawData, CandidateProfile, CareerEntry, EducationRecord, SkillRecord


class TestCandidatePreprocessor(unittest.TestCase):
    """Test candidate preprocessing."""

    def setUp(self):
        """Set up test fixtures."""
        self.preprocessor = CandidatePreprocessor()

    def create_sample_candidate(self):
        """Create a sample candidate for testing."""
        profile = CandidateProfile(
            anonymized_name="Test User",
            headline="Senior Engineer",
            summary="Experienced professional with 5 years in software development.",
            location="New York",
            country="USA",
            years_of_experience=5.0,
            current_title="Senior Engineer",
            current_company="Tech Corp",
            current_company_size="501-1000",
            current_industry="Technology",
        )

        career = CareerEntry(
            company="Tech Corp",
            title="Senior Engineer",
            start_date="2022-01-01",
            end_date=None,
            duration_months=24,
            is_current=True,
            industry="Technology",
            company_size="501-1000",
            description="Led development of microservices architecture.",
        )

        education = EducationRecord(
            institution="State University",
            degree="B.S.",
            field_of_study="Computer Science",
            start_year=2015,
            end_year=2019,
            grade="3.8 GPA",
        )

        skill = SkillRecord(name="Python", proficiency="advanced", endorsements=50)

        return CandidateRawData(
            candidate_id="CAND_0000001",
            profile=profile,
            career_history=[career],
            education=[education],
            skills=[skill],
        )

    def test_preprocess_candidate(self):
        """Test preprocessing a single candidate."""
        candidate = self.create_sample_candidate()
        result = self.preprocessor.preprocess_candidate(candidate)

        self.assertEqual(result.candidate_id, "CAND_0000001")
        self.assertIsNotNone(result.profile_text)
        self.assertGreater(len(result.profile_text), 0)
        self.assertIn("Senior Engineer".lower(), result.profile_text.lower())

    def test_profile_text_contains_sections(self):
        """Test that profile text contains all expected sections."""
        candidate = self.create_sample_candidate()
        result = self.preprocessor.preprocess_candidate(candidate)

        profile_text = result.profile_text.lower()

        # Check for key sections
        self.assertIn("current role", profile_text)
        self.assertIn("work experience", profile_text)
        self.assertIn("education", profile_text)
        self.assertIn("skills", profile_text)

    def test_metadata_extraction(self):
        """Test that metadata is properly extracted."""
        candidate = self.create_sample_candidate()
        result = self.preprocessor.preprocess_candidate(candidate)

        self.assertEqual(result.metadata["years_of_experience"], 5.0)
        self.assertEqual(result.metadata["location"], "New York")
        self.assertEqual(result.metadata["career_entries"], 1)
        self.assertEqual(result.metadata["education_count"], 1)
        self.assertEqual(result.metadata["skills_count"], 1)

    def test_batch_preprocess(self):
        """Test batch preprocessing."""
        candidates = [self.create_sample_candidate() for _ in range(5)]
        results = self.preprocessor.batch_preprocess(candidates)

        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsNotNone(result.profile_text)

    def test_truncation(self):
        """Test that long texts are truncated."""
        candidate = self.create_sample_candidate()
        # Create a very long description
        candidate.career_history[0].description = "x" * 10000

        result = self.preprocessor.preprocess_candidate(candidate)

        # Should still be processable
        self.assertIsNotNone(result.profile_text)


class TestTextProcessing(unittest.TestCase):
    """Test text processing utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.preprocessor = CandidatePreprocessor()

    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "A" * 1000
        truncated = self.preprocessor._truncate_text(long_text, 100)

        self.assertLessEqual(len(truncated), 103)  # 100 + "..."
        self.assertTrue(truncated.endswith("..."))

    def test_format_experience_entry(self):
        """Test formatting of experience entries."""
        career = CareerEntry(
            company="Tech Corp",
            title="Senior Engineer",
            start_date="2022-01-01",
            end_date="2024-01-01",
            duration_months=24,
            is_current=False,
            industry="Technology",
            company_size="501-1000",
            description="Led development of microservices.",
        )

        formatted = self.preprocessor._format_experience_entry(career)

        self.assertIn("Senior Engineer", formatted)
        self.assertIn("Tech Corp", formatted)
        self.assertIn("Technology", formatted)


if __name__ == "__main__":
    unittest.main()
