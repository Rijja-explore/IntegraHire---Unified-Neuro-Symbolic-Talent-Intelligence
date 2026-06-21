"""
Candidate preprocessing pipeline.

Extracts and normalizes candidate data to generate rich profile text
optimized for semantic retrieval.
"""

import logging
from typing import Any, Dict, List, Optional

from .config import get_config
from .schemas import CandidateRawData, CandidateRecord
from .utils import normalize_text


logger = logging.getLogger(__name__)


class CandidatePreprocessor:
    """
    Preprocesses raw candidate data into retrieval-optimized profiles.

    Generates rich text that combines:
    - Current role and company
    - Work experience and achievements
    - Education and qualifications
    - Skills and expertise
    """

    def __init__(self):
        """Initialize preprocessor with config."""
        self.config = get_config().preprocessing

    def preprocess_candidate(self, raw_data: CandidateRawData) -> CandidateRecord:
        """
        Preprocess a single candidate.

        Args:
            raw_data: Raw candidate data from JSONL

        Returns:
            Processed candidate record with optimized profile text
        """
        profile_text = self._generate_profile_text(raw_data)

        metadata = {
            "years_of_experience": raw_data.profile.years_of_experience,
            "location": raw_data.profile.location,
            "country": raw_data.profile.country,
            "current_company": raw_data.profile.current_company,
            "current_industry": raw_data.profile.current_industry,
            "company_size": raw_data.profile.current_company_size,
            "education_count": len(raw_data.education),
            "skills_count": len(raw_data.skills),
            "career_entries": len(raw_data.career_history),
        }

        return CandidateRecord(
            candidate_id=raw_data.candidate_id,
            profile_text=profile_text,
            raw_data=raw_data,
            metadata=metadata,
        )

    def _generate_profile_text(self, raw_data: CandidateRawData) -> str:
        """
        Generate optimized profile text combining all candidate information.

        Args:
            raw_data: Raw candidate data

        Returns:
            Rich profile text for retrieval
        """
        sections = []

        # 1. Current Position Section
        current_section = self._build_current_position(raw_data.profile)
        if current_section:
            sections.append(current_section)

        # 2. Professional Summary
        if raw_data.profile.summary:
            summary = self._truncate_text(raw_data.profile.summary, self.config.max_summary_length)
            sections.append(f"Professional Summary:\n{summary}")

        # 3. Experience Section
        experience_section = self._build_experience_section(raw_data.career_history)
        if experience_section:
            sections.append(experience_section)

        # 4. Education Section
        if self.config.include_education and raw_data.education:
            education_section = self._build_education_section(raw_data.education)
            if education_section:
                sections.append(education_section)

        # 5. Skills Section
        if self.config.include_skills and raw_data.skills:
            skills_section = self._build_skills_section(raw_data.skills)
            if skills_section:
                sections.append(skills_section)

        # Combine all sections
        profile_text = "\n\n".join(sections)

        if self.config.normalize_text:
            profile_text = normalize_text(profile_text)

        return profile_text

    def _build_current_position(self, profile: Any) -> str:
        """Build current position section."""
        sections = []

        if profile.current_title:
            sections.append(f"Current Role: {profile.current_title}")

        if profile.current_company:
            sections.append(f"Current Company: {profile.current_company}")

        if profile.current_industry:
            sections.append(f"Industry: {profile.current_industry}")

        if profile.current_company_size:
            sections.append(f"Company Size: {profile.current_company_size}")

        if profile.years_of_experience:
            sections.append(f"Years of Experience: {profile.years_of_experience}")

        if profile.location:
            sections.append(f"Location: {profile.location}")

        if sections:
            return "CURRENT POSITION\n" + "\n".join(sections)

        return ""

    def _build_experience_section(self, career_history: List[Any]) -> str:
        """Build work experience section."""
        if not career_history:
            return ""

        sections = ["WORK EXPERIENCE"]

        for entry in career_history:
            exp_text = self._format_experience_entry(entry)
            sections.append(exp_text)

        return "\n".join(sections)

    def _format_experience_entry(self, entry: Any) -> str:
        """Format a single experience entry."""
        lines = []

        # Title and Company
        title_company = f"{entry.title} at {entry.company}"
        lines.append(title_company)

        # Duration
        if entry.start_date and entry.end_date:
            lines.append(f"  ({entry.start_date} - {entry.end_date}) [{entry.duration_months} months]")
        elif entry.start_date:
            lines.append(f"  ({entry.start_date} - Present) [{entry.duration_months} months]")

        # Industry and company size
        if entry.industry or entry.company_size:
            lines.append(f"  {entry.industry} | {entry.company_size}")

        # Description (truncated)
        if entry.description:
            description = self._truncate_text(entry.description, self.config.max_experience_chars)
            lines.append(f"  {description}")

        return "\n".join(lines)

    def _build_education_section(self, education_records: List[Any]) -> str:
        """Build education section."""
        if not education_records:
            return ""

        sections = ["EDUCATION"]

        for edu in education_records:
            edu_text = self._format_education_entry(edu)
            sections.append(edu_text)

        return "\n".join(sections)

    def _format_education_entry(self, edu: Any) -> str:
        """Format a single education entry."""
        lines = []

        # Degree and field
        degree_field = f"{edu.degree} in {edu.field_of_study}"
        lines.append(degree_field)

        # Institution
        lines.append(f"  {edu.institution}")

        # Years
        if edu.start_year and edu.end_year:
            lines.append(f"  ({edu.start_year} - {edu.end_year})")

        # Grade and tier
        if edu.grade:
            lines.append(f"  Grade: {edu.grade}")

        if edu.tier:
            lines.append(f"  Tier: {edu.tier}")

        return "\n".join(lines)

    def _build_skills_section(self, skills: List[Any]) -> str:
        """Build skills section."""
        if not skills:
            return ""

        sections = ["SKILLS & EXPERTISE"]

        # Group by proficiency level
        by_proficiency = {}
        for skill in skills:
            level = skill.proficiency if hasattr(skill, "proficiency") else "unknown"
            if level not in by_proficiency:
                by_proficiency[level] = []
            by_proficiency[level].append(skill)

        # Format by proficiency
        for level in ["advanced", "intermediate", "basic"]:
            if level in by_proficiency:
                skill_names = [s.name for s in by_proficiency[level]]
                level_title = level.title()
                sections.append(f"{level_title}: {', '.join(skill_names)}")

        return "\n".join(sections)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text

        truncated = text[: max_length - 3]
        # Try to truncate at word boundary
        last_space = truncated.rfind(" ")
        if last_space > max_length * 0.8:
            truncated = truncated[:last_space]

        return truncated + "..."

    def batch_preprocess(self, candidates: List[CandidateRawData]) -> List[CandidateRecord]:
        """
        Preprocess a batch of candidates.

        Args:
            candidates: List of raw candidate data

        Returns:
            List of processed candidates
        """
        logger.info(f"Preprocessing {len(candidates)} candidates")

        processed = []
        for candidate in candidates:
            try:
                record = self.preprocess_candidate(candidate)
                processed.append(record)
            except Exception as e:
                logger.warning(f"Error preprocessing candidate {candidate.candidate_id}: {e}")

        logger.info(f"Successfully preprocessed {len(processed)} candidates")
        return processed
