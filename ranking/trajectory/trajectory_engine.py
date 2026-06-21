"""Career trajectory analysis."""
from ..schemas import CandidateProfile, Experience
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)

class ProgressionAnalyzer:
    """Analyze career progression quality."""

    SENIORITY_LEVELS = {
        "intern": 1, "associate": 2, "junior": 2, "analyst": 2,
        "engineer": 3, "developer": 3, "manager": 3, "specialist": 3,
        "senior": 4, "principal": 5, "lead": 4, "director": 5,
        "head": 5, "vp": 6, "chief": 6, "c-level": 6,
    }

    @staticmethod
    def extract_seniority(title: str) -> int:
        """Extract seniority level from job title."""
        title_lower = title.lower()
        max_level = 0
        for keyword, level in ProgressionAnalyzer.SENIORITY_LEVELS.items():
            if keyword in title_lower:
                max_level = max(max_level, level)
        return max_level if max_level > 0 else 3  # Default to mid-level

    @staticmethod
    def analyze_progression(career_history: List[Experience]) -> Tuple[float, List[str]]:
        """
        Analyze career progression.
        Reward: junior -> engineer -> senior -> lead
        Penalize: random unrelated jumps
        """
        if not career_history:
            return 50.0, ["No career history"]

        # Sort by date
        from datetime import datetime
        sorted_history = sorted(
            career_history,
            key=lambda x: datetime.strptime(x.start_date, "%Y-%m-%d") if x.start_date else datetime.min
        )

        seniority_levels = [ProgressionAnalyzer.extract_seniority(e.title) for e in sorted_history]
        industries = [e.industry for e in sorted_history]

        score = 0.0
        issues = []

        # Check progression
        progression_quality = 0
        for i in range(len(seniority_levels) - 1):
            current = seniority_levels[i]
            next_level = seniority_levels[i + 1]

            if next_level > current:
                progression_quality += (next_level - current) * 10
            elif next_level == current:
                progression_quality += 5  # Lateral move is neutral-positive
            else:
                # Demotion is concerning
                progression_quality -= (current - next_level) * 15
                issues.append(
                    f"Career demotion: {sorted_history[i].title} -> {sorted_history[i+1].title}"
                )

        score = min(100, 50 + progression_quality / len(seniority_levels))

        # Check industry consistency
        if len(industries) > 1:
            same_industry = sum(1 for i in range(len(industries)-1) if industries[i] == industries[i+1])
            industry_stability = (same_industry / (len(industries) - 1)) * 100
            score = (score + industry_stability) / 2

        return max(0, min(100, score)), issues


class SpecializationDetector:
    """Detect career specialization and focus."""

    TECH_SPECIALIZATIONS = {
        "ml": {"ML", "Machine Learning", "AI", "Deep Learning", "NLP", "Computer Vision"},
        "data": {"Data Engineering", "Data Science", "Analytics", "Data", "Spark", "Hadoop"},
        "backend": {"Backend", "Server", "API", "Microservice", "Distributed"},
        "frontend": {"Frontend", "React", "Angular", "Vue", "JavaScript", "UI"},
        "devops": {"DevOps", "Infrastructure", "Cloud", "Kubernetes", "Docker"},
        "retrieval": {"Retrieval", "Search", "Ranking", "Information", "Vector"},
    }

    @staticmethod
    def detect_specialization(career_history: List[Experience]) -> Tuple[str, float]:
        """
        Detect primary specialization.
        Returns: (specialization, focus_score 0-100)
        """
        if not career_history:
            return "unknown", 0.0

        # Count specializations across all roles
        spec_counts = {spec: 0 for spec in SpecializationDetector.TECH_SPECIALIZATIONS}

        for exp in career_history:
            description_lower = f"{exp.title} {exp.description}".lower()
            for spec, keywords in SpecializationDetector.TECH_SPECIALIZATIONS.items():
                if any(kw.lower() in description_lower for kw in keywords):
                    spec_counts[spec] += 1

        # Find dominant specialization
        if max(spec_counts.values()) == 0:
            return "unspecialized", 0.0

        primary_spec = max(spec_counts, key=spec_counts.get)
        total_roles = len(career_history)
        focus_score = (spec_counts[primary_spec] / total_roles) * 100

        return primary_spec, focus_score


class LearningVelocityCalculator:
    """Estimate learning velocity from career progression."""

    @staticmethod
    def calculate_learning_velocity(candidate: CandidateProfile) -> float:
        """
        Estimate learning velocity (0-100).
        Based on:
        - New skills acquired per year
        - Technology evolution in roles
        - Career growth pace
        """
        if not candidate.career_history or not candidate.skills:
            return 50.0  # Neutral

        # Estimate years of actual experience
        years_exp = candidate.profile.years_of_experience
        if years_exp <= 0:
            years_exp = 1

        # Count unique skills in major categories
        ml_skills = sum(1 for s in candidate.skills if any(
            kw in s.name.lower() for kw in ["ml", "deep", "nlp", "ai", "learning", "neural"]
        ))
        data_skills = sum(1 for s in candidate.skills if any(
            kw in s.name.lower() for kw in ["data", "spark", "airflow", "kafka", "sql"]
        ))
        system_skills = sum(1 for s in candidate.skills if any(
            kw in s.name.lower() for kw in ["kubernetes", "docker", "aws", "gcp", "cloud"]
        ))

        total_specialized_skills = ml_skills + data_skills + system_skills
        skill_acquisition_rate = (total_specialized_skills / years_exp) * 10

        # Measure career growth
        titles = [e.title for e in candidate.career_history]
        progression_score = ProgressionAnalyzer.analyze_progression(candidate.career_history)[0]

        # Combine signals
        velocity = (skill_acquisition_rate * 0.5) + (progression_score * 0.3) + 20
        velocity = max(0, min(100, velocity))

        return velocity


class TrajectoryEngine:
    """Analyze overall career trajectory."""

    def __init__(self):
        self.progression_analyzer = ProgressionAnalyzer()
        self.specialization_detector = SpecializationDetector()
        self.learning_velocity_calculator = LearningVelocityCalculator()

    def evaluate(self, candidate: CandidateProfile) -> Tuple[float, float, Dict]:
        """
        Evaluate career trajectory.

        Returns:
            - trajectory_score (0-100)
            - learning_velocity_score (0-100)
            - detailed_analysis (dict)
        """
        analysis = {
            "candidate_id": candidate.candidate_id,
            "progression_issues": [],
            "primary_specialization": "unknown",
            "specialization_focus": 0.0,
        }

        # 1. Progression analysis
        progression_score, progression_issues = self.progression_analyzer.analyze_progression(
            candidate.career_history
        )
        analysis["progression_issues"] = progression_issues
        analysis["progression_score"] = progression_score

        # 2. Specialization detection
        primary_spec, focus_score = self.specialization_detector.detect_specialization(
            candidate.career_history
        )
        analysis["primary_specialization"] = primary_spec
        analysis["specialization_focus"] = focus_score

        # Reward deep specialization in relevant areas
        if primary_spec in ["ml", "data", "retrieval", "backend"]:
            spec_bonus = focus_score * 0.2
        elif primary_spec == "devops":
            spec_bonus = focus_score * 0.1
        else:
            spec_bonus = -10

        trajectory_score = progression_score * 0.7 + (focus_score * 0.3)
        trajectory_score = max(0, min(100, trajectory_score + spec_bonus))

        # 3. Learning velocity
        learning_velocity_score = self.learning_velocity_calculator.calculate_learning_velocity(
            candidate
        )
        analysis["learning_velocity_score"] = learning_velocity_score

        analysis["final_trajectory_score"] = trajectory_score

        return trajectory_score, learning_velocity_score, analysis
