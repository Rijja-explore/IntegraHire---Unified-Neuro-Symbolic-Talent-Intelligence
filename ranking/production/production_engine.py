"""Production readiness and engineering signals."""
from ..schemas import CandidateProfile, Skill
from ..config import ProductionSignals, DEFAULT_PRODUCTION_SIGNALS
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProductionSignalDetector:
    """Detect production engineering signals from candidate profile."""

    def __init__(self, signals_config: ProductionSignals = None):
        self.signals = signals_config or DEFAULT_PRODUCTION_SIGNALS

    def score_skills(self, skills: List[Skill]) -> Tuple[float, Dict[str, float]]:
        """
        Score skills based on production value.
        Returns: (skill_production_score, skill_breakdown)
        """
        if not skills:
            return 0.0, {}

        skill_scores = {}
        total_score = 0.0
        total_weight = 0.0

        for skill in skills:
            skill_weight = self._get_skill_weight(skill.name)

            # Proficiency multiplier
            proficiency_multiplier = {
                "beginner": 0.3,
                "intermediate": 0.6,
                "advanced": 0.9,
                "expert": 1.0,
            }.get(skill.proficiency, 0.5)

            # Duration signal (more months = more real-world experience)
            duration_score = min(1.0, skill.duration_months / 24)  # 24 months = max

            # Endorsement signal
            endorsement_score = min(1.0, skill.endorsements / 20)  # 20+ endorsements = max

            # Combine signals
            skill_score = (
                (skill_weight * 0.5) +
                (proficiency_multiplier * 0.3) +
                (duration_score * 0.1) +
                (endorsement_score * 0.1)
            )

            skill_scores[skill.name] = skill_score
            total_score += skill_score
            total_weight += 1.0

        avg_skill_score = (total_score / total_weight * 100) if total_weight > 0 else 0.0

        return avg_skill_score, skill_scores

    def _get_skill_weight(self, skill_name: str) -> float:
        """Get weight for a skill based on production value."""
        skill_lower = skill_name.lower()

        for skill_pattern, weight in self.signals.high_value.items():
            if skill_pattern.lower() in skill_lower or skill_lower in skill_pattern.lower():
                return weight

        for skill_pattern, weight in self.signals.medium_value.items():
            if skill_pattern.lower() in skill_lower or skill_lower in skill_pattern.lower():
                return weight

        for skill_pattern, weight in self.signals.low_value.items():
            if skill_pattern.lower() in skill_lower or skill_lower in skill_pattern.lower():
                return weight

        return 0.4  # Default neutral weight

    def check_production_recency(self, candidate: CandidateProfile, days_threshold: int = 180) -> Tuple[float, str]:
        """
        Check if candidate has recent production experience.
        Returns: (recency_score 0-100, status)
        """
        if not candidate.career_history:
            return 0.0, "no_experience"

        # Check current role
        current_role = next((e for e in candidate.career_history if e.is_current), None)

        if not current_role:
            return 30.0, "not_currently_working"

        # Check if current role involves production work
        production_keywords = {
            "engineer", "developer", "architect", "lead", "senior", "staff",
            "principal", "data", "ml", "ai", "infrastructure", "platform"
        }

        current_title_lower = current_role.title.lower()
        has_production_title = any(kw in current_title_lower for kw in production_keywords)

        if not has_production_title:
            return 40.0, "current_non_production_role"

        # Calculate recency from career history
        from datetime import datetime
        try:
            current_start = datetime.strptime(current_role.start_date, "%Y-%m-%d")
            days_in_current = (datetime.now() - current_start).days
            recency_score = min(100, 50 + (days_in_current / days_threshold) * 50)
        except:
            recency_score = 50.0

        return recency_score, "currently_producing"

    def extract_production_systems(self, candidate: CandidateProfile) -> List[str]:
        """Extract specific production systems mentioned."""
        systems = []
        production_systems = set()

        for pattern_list in [self.signals.high_value, self.signals.medium_value]:
            production_systems.update(pattern_list.keys())

        candidate_text = f"{candidate.profile.summary} {candidate.profile.headline} ".lower()
        for exp in candidate.career_history:
            candidate_text += f"{exp.title} {exp.description} ".lower()

        for skill in candidate.skills:
            candidate_text += f"{skill.name} ".lower()

        for system in production_systems:
            if system.lower() in candidate_text:
                systems.append(system)

        return list(set(systems))


class ProductionEngine:
    """Evaluate production readiness."""

    def __init__(self, signals_config: ProductionSignals = None):
        self.detector = ProductionSignalDetector(signals_config)

    def evaluate(self, candidate: CandidateProfile) -> Tuple[float, Dict]:
        """
        Evaluate production readiness.

        Returns:
            - production_score (0-100)
            - detailed_analysis (dict)
        """
        analysis = {
            "candidate_id": candidate.candidate_id,
            "skill_production_score": 0.0,
            "production_systems_found": [],
            "recency_status": "unknown",
            "final_score": 0.0,
        }

        # 1. Score skills for production value
        skill_prod_score, skill_scores = self.detector.score_skills(candidate.skills)
        analysis["skill_production_score"] = skill_prod_score
        analysis["top_production_skills"] = sorted(
            skill_scores.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # 2. Check production recency
        recency_score, recency_status = self.detector.check_production_recency(candidate)
        analysis["production_recency_score"] = recency_score
        analysis["recency_status"] = recency_status

        # 3. Extract production systems
        systems = self.detector.extract_production_systems(candidate)
        analysis["production_systems_found"] = systems

        # Bonus for high-value systems
        high_value_systems = []
        for system in systems:
            if system in self.detector.signals.high_value:
                high_value_systems.append(system)

        system_bonus = min(20, len(high_value_systems) * 2)

        # 4. Check for critical missing signals
        critical_missing = []
        required_signals = [
            ("retrieval system", ["FAISS", "Milvus", "Qdrant", "Weaviate", "Pinecone"]),
            ("vector database", ["Milvus", "Qdrant", "Weaviate", "Pinecone", "Elasticsearch"]),
            ("ranking system", ["Ranking", "Learning-to-Rank", "XGBoost", "LightGBM"]),
            ("evaluation framework", ["NDCG", "MRR", "MAP", "Evaluation"]),
        ]

        for signal_name, keywords in required_signals:
            found = any(
                k in analysis["production_systems_found"]
                or any(k.lower() in s.name.lower() for s in candidate.skills)
                for k in keywords
            )
            if not found:
                critical_missing.append(signal_name)

        analysis["critical_missing_signals"] = critical_missing
        missing_penalty = len(critical_missing) * 15

        # Combine signals
        final_score = (
            (skill_prod_score * 0.4) +
            (recency_score * 0.4) +
            (system_bonus * 0.2)
        ) - missing_penalty

        final_score = max(0, min(100, final_score))
        analysis["final_score"] = final_score

        return final_score, analysis
