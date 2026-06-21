"""Timeline validation for career history authenticity."""
from datetime import datetime
from typing import List, Tuple
from ..schemas import Experience
import logging

logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

class TimelineValidator:
    """Validates career timeline for inconsistencies."""

    @staticmethod
    def validate_timeline(career_history: List[Experience]) -> Tuple[float, List[str]]:
        """
        Validate career timeline for:
        - Overlapping positions
        - Negative durations
        - Impossible dates
        - Unrealistic experience claims

        Returns: (penalty_score, issues_found)
        """
        penalty = 0.0
        issues = []

        # Sort by start date
        experiences = sorted(
            [e for e in career_history if e.start_date],
            key=lambda x: parse_date(x.start_date) or datetime.min
        )

        for i in range(len(experiences) - 1):
            curr = experiences[i]
            next_exp = experiences[i + 1]

            curr_start = parse_date(curr.start_date)
            curr_end = parse_date(curr.end_date) if curr.end_date else datetime.now()
            next_start = parse_date(next_exp.start_date)

            # Check for overlaps
            if curr_start and next_start and curr_end and curr_end > next_start:
                gap_days = (curr_end - next_start).days
                penalty += min(10, abs(gap_days) / 10)
                issues.append(
                    f"Overlapping positions: {curr.title} at {curr.company} "
                    f"({curr.end_date}) vs {next_exp.title} at {next_exp.company} ({next_start.date()})"
                )

        # Check for unrealistic durations
        for exp in experiences:
            if exp.duration_months < 0:
                penalty += 15
                issues.append(f"Negative duration: {exp.title} at {exp.company} "
                            f"({exp.duration_months} months)")
            elif exp.duration_months == 0 and not exp.is_current:
                penalty += 5
                issues.append(f"Zero duration non-current role: {exp.title}")
            elif exp.duration_months > 480:  # 40 years
                penalty += 8
                issues.append(f"Unrealistic duration: {exp.title} ({exp.duration_months} months)")

        return penalty, issues

    @staticmethod
    def check_career_consistency(experiences: List[Experience]) -> Tuple[float, List[str]]:
        """Check for sudden unrelated career jumps."""
        penalty = 0.0
        issues = []

        # Track industry changes
        industries = [e.industry for e in experiences]

        for i in range(len(industries) - 1):
            # If switching between completely unrelated industries
            related = TimelineValidator._are_industries_related(industries[i], industries[i + 1])
            if not related and i > 0:  # Allow first transition
                penalty += 5
                issues.append(f"Unrelated industry jump: {industries[i]} -> {industries[i + 1]}")

        return penalty, issues

    @staticmethod
    def _are_industries_related(ind1: str, ind2: str) -> bool:
        """Check if two industries are reasonably related."""
        tech_industries = {
            "IT Services", "Software", "Technology", "Financial Technology",
            "Telecommunications", "Data & Analytics", "AI/ML", "SaaS"
        }
        manufacturing_industries = {
            "Manufacturing", "Hardware", "Industrial", "Automotive"
        }
        business_industries = {
            "Consulting", "Accounting", "Finance", "Business Services"
        }

        ind1_tech = ind1 in tech_industries
        ind2_tech = ind2 in tech_industries
        ind1_mfg = ind1 in manufacturing_industries
        ind2_mfg = ind2 in manufacturing_industries
        ind1_biz = ind1 in business_industries
        ind2_biz = ind2 in business_industries

        # Same category
        if (ind1_tech and ind2_tech) or (ind1_mfg and ind2_mfg) or (ind1_biz and ind2_biz):
            return True

        # Allow transitions between tech and business
        if (ind1_tech and ind2_biz) or (ind1_biz and ind2_tech):
            return True

        return False
