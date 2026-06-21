"""
Job description processing pipeline.

Extracts and normalizes job description text for retrieval.
"""

import logging
import re
from typing import List, Optional

from .embeddings import EmbeddingGenerator
from .schemas import JobDescription
from .utils import extract_keywords, normalize_text, tokenize_text

logger = logging.getLogger(__name__)


class JobDescriptionProcessor:
    """
    Processes job descriptions for candidate retrieval.

    Extracts:
    - Clean text
    - Key responsibilities
    - Required and nice-to-have skills
    - Keywords
    - Embedding vector
    """

    def __init__(self):
        """Initialize processor."""
        self.embedding_generator = EmbeddingGenerator()

    def process_job_description(self, job_text: str, generate_embedding: bool = True) -> JobDescription:
        """
        Process a job description.

        Args:
            job_text: Raw job description text
            generate_embedding: Whether to generate embedding

        Returns:
            Processed JobDescription object
        """
        logger.info("Processing job description")

        # Clean text
        cleaned_text = self._clean_text(job_text)

        # Extract components
        responsibilities = self._extract_responsibilities(cleaned_text)
        required_skills = self._extract_required_skills(cleaned_text)
        nice_to_have_skills = self._extract_nice_to_have_skills(cleaned_text)
        keywords = extract_keywords(cleaned_text, top_k=30)

        # Generate embedding
        embedding = None
        if generate_embedding:
            try:
                embedding_vec = self.embedding_generator.generate_single_embedding(cleaned_text)
                embedding = embedding_vec.tolist()
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")

        return JobDescription(
            original_text=job_text,
            cleaned_text=cleaned_text,
            embedding=embedding,
            keywords=keywords,
            key_responsibilities=responsibilities,
            required_skills=required_skills,
            nice_to_have_skills=nice_to_have_skills,
        )

    def _clean_text(self, text: str) -> str:
        """Clean job description text."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove markdown links but keep text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        # Normalize
        if len(text) > 5000:
            # Truncate very long descriptions
            text = text[:5000]

        return normalize_text(text)

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract key responsibilities from job description."""
        responsibilities = []

        # Look for bullet points or numbered items
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Match bullet points or numbered lists
            if re.match(r"^[-•*]\s+", line) or re.match(r"^\d+\.\s+", line):
                # Remove bullet/number prefix
                clean_line = re.sub(r"^[-•*]\s+|^\d+\.\s+", "", line).strip()

                if len(clean_line) > 10 and len(clean_line) < 200:
                    responsibilities.append(clean_line)

        # Limit to top 10
        return responsibilities[:10]

    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills."""
        skills = self._extract_skill_section(text, ["required", "must have", "must-have"])

        # Common tech skills to look for
        common_skills = [
            "python",
            "java",
            "javascript",
            "typescript",
            "c++",
            "go",
            "rust",
            "sql",
            "aws",
            "azure",
            "gcp",
            "kubernetes",
            "docker",
            "ml",
            "machine learning",
            "nlp",
            "deep learning",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
            "spark",
            "hadoop",
            "elasticsearch",
            "postgresql",
            "mongodb",
            "redis",
            "react",
            "vue",
            "angular",
            "node.js",
        ]

        found_skills = []
        text_lower = text.lower()

        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)

        # Add extracted skills
        found_skills.extend(skills)

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)

        return unique_skills[:20]

    def _extract_nice_to_have_skills(self, text: str) -> List[str]:
        """Extract nice-to-have skills."""
        return self._extract_skill_section(text, ["nice to have", "preferred", "bonus"])[:15]

    def _extract_skill_section(self, text: str, keywords: List[str]) -> List[str]:
        """Extract skills from sections matching keywords."""
        skills = []

        # Find sections with keywords
        for keyword in keywords:
            pattern = rf"{keyword}[^:]*:\s*(.+?)(?=\n\n|\n[A-Z]|$)"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

            if match:
                section = match.group(1)

                # Extract skill names (words, possibly with - or +)
                skill_pattern = r"([a-zA-Z0-9\-+\.\s]{2,50}?)(?:,|;|\n|$)"
                found = re.findall(skill_pattern, section)

                for skill in found:
                    skill = skill.strip()
                    if 2 < len(skill) < 50 and skill.count(" ") < 3:
                        skills.append(skill)

        return skills

    def get_jd_embedding(self, job_description: JobDescription) -> Optional[List[float]]:
        """
        Get embedding for job description.

        Args:
            job_description: JobDescription object

        Returns:
            Embedding vector or None
        """
        if job_description.embedding is None:
            embedding_vec = self.embedding_generator.generate_single_embedding(job_description.cleaned_text)
            return embedding_vec.tolist()

        return job_description.embedding
