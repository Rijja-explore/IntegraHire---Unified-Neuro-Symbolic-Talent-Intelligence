"""Detect honeypot / trap profiles used to catch inflated or fraudulent candidates."""

from __future__ import annotations

from typing import List, Tuple

from ..schemas import CandidateProfile

# Known trap skill combinations that should not appear without supporting experience.
_HONEYPOT_SKILL_MARKERS = {
    "honeypot_ml_stack",
    "trap_candidate_flag",
    "internal_audit_only",
}


class HoneypotDetector:
    """Lightweight honeypot checks (deterministic, no external calls)."""

    @staticmethod
    def evaluate(candidate: CandidateProfile) -> Tuple[float, List[str]]:
        """
        Returns:
            penalty (0-100): higher means more suspicious
            issues: human-readable flags
        """
        penalty = 0.0
        issues: List[str] = []

        skill_names = {s.name.lower() for s in candidate.skills}
        for marker in _HONEYPOT_SKILL_MARKERS:
            if marker in skill_names:
                penalty += 80.0
                issues.append(f"Honeypot skill marker detected: {marker}")

        years = candidate.profile.years_of_experience
        advanced_ai_skills = sum(
            1
            for s in candidate.skills
            if s.proficiency in {"advanced", "expert"}
            and any(k in s.name.lower() for k in ("llm", "fine-tuning", "lora", "rag", "vector"))
        )
        if years < 1.0 and advanced_ai_skills >= 4:
            penalty += 35.0
            issues.append("Advanced AI skill inflation relative to experience")

        if candidate.redrob_signals.github_activity_score < 0 and advanced_ai_skills >= 3:
            penalty += 20.0
            issues.append("Strong AI claims with invalid GitHub activity signal")

        return min(100.0, penalty), issues
