"""Skill consistency and buzzword inflation detection."""
from typing import List, Dict, Tuple, Set
from ..schemas import Skill, Experience
import logging

logger = logging.getLogger(__name__)

class SkillCluster:
    """Define skill clusters for consistency checking."""

    CLUSTERS = {
        "ai_ml": {
            "core": {"NLP", "Deep Learning", "Machine Learning", "ML", "AI", "Artificial Intelligence"},
            "frameworks": {"PyTorch", "TensorFlow", "Scikit-learn", "Keras", "JAX"},
            "specialized": {"Computer Vision", "Object Detection", "Image Classification", "Speech Recognition", "Fine-tuning LLMs", "GANs"},
        },
        "data_engineering": {
            "core": {"Data Engineering", "ETL", "Data Pipeline", "Data Warehousing", "SQL"},
            "tools": {"Spark", "Airflow", "Kafka", "Flink", "Beam", "dbt", "Presto"},
            "databases": {"Snowflake", "BigQuery", "Redshift", "PostgreSQL", "MySQL", "Oracle"},
        },
        "retrieval_search": {
            "core": {"Retrieval", "Search", "Ranking", "Information Retrieval", "Vector Search", "Embedding"},
            "systems": {"FAISS", "Milvus", "Qdrant", "Weaviate", "Pinecone", "Elasticsearch", "OpenSearch"},
            "frameworks": {"LangChain", "RAG"},
        },
        "devops_infrastructure": {
            "core": {"DevOps", "Infrastructure", "Cloud", "Deployment"},
            "platforms": {"AWS", "GCP", "Azure", "Kubernetes", "Docker"},
            "tools": {"Terraform", "Ansible", "Jenkins", "GitLab"},
        },
        "distributed_systems": {
            "core": {"Distributed Systems", "Microservices", "Scalability", "Performance"},
            "messaging": {"Kafka", "RabbitMQ", "Pub/Sub"},
            "coordination": {"Zookeeper", "Consul", "etcd"},
        },
        "evaluation_testing": {
            "core": {"A/B Testing", "Evaluation", "Metrics", "Benchmarking", "NDCG", "MRR", "MAP"},
            "testing": {"Unit Testing", "Integration Testing", "Load Testing"},
        },
        "frontend": {
            "core": {"JavaScript", "TypeScript", "React", "Vue", "Angular"},
            "styling": {"Tailwind", "CSS", "HTML"},
        },
        "low_value": {
            "marketing": {"Marketing", "Content Writing", "SEO", "Social Media"},
            "generic": {"Prompt Engineering", "ChatGPT", "Excel", "PowerPoint"},
            "design": {"Photoshop", "Figma", "Design"},
        },
    }

    @classmethod
    def get_cluster(cls, skill_name: str) -> str:
        """Find which cluster a skill belongs to."""
        skill_lower = skill_name.lower()
        for cluster_name, categories in cls.CLUSTERS.items():
            for category, skills in categories.items():
                if any(s.lower() in skill_lower or skill_lower in s.lower() for s in skills):
                    return cluster_name
        return "uncategorized"

class SkillConsistency:
    """Check skill-experience consistency."""

    @staticmethod
    def validate_skill_consistency(skills: List[Skill], career_history: List[Experience]) -> Tuple[float, List[str]]:
        """
        Check for:
        - Advanced/Expert skills without supporting experience
        - Skill clusters present across career
        - Buzzword inflation
        """
        penalty = 0.0
        issues = []

        # Extract skills by proficiency
        advanced_expert_skills = {
            s.name for s in skills if s.proficiency in ["advanced", "expert"]
        }
        intermediate_skills = {
            s.name for s in skills if s.proficiency == "intermediate"
        }
        beginner_skills = {
            s.name for s in skills if s.proficiency == "beginner"
        }

        # Build experience text
        experience_text = " ".join([
            f"{e.title} {e.company} {e.description}" for e in career_history
        ]).lower()

        # Check advanced skills have supporting experience
        for skill in advanced_expert_skills:
            skill_lower = skill.lower()
            if skill_lower not in experience_text:
                penalty += 3
                issues.append(f"Advanced skill '{skill}' not mentioned in experience")

        # Detect skill clusters
        skill_clusters_found = {}
        for skill in [s.name for s in skills]:
            cluster = SkillCluster.get_cluster(skill)
            if cluster not in skill_clusters_found:
                skill_clusters_found[cluster] = []
            skill_clusters_found[cluster].append(skill)

        # Penalize having many unrelated clusters (buzzword inflation)
        unrelated_clusters = {
            "ai_ml", "devops_infrastructure", "frontend", "low_value"
        }
        found_unrelated = len([c for c in skill_clusters_found.keys() if c in unrelated_clusters])

        if found_unrelated >= 3:
            penalty += min(10, found_unrelated * 2)
            issues.append(
                f"Possible buzzword inflation: {found_unrelated} unrelated skill clusters "
                f"({', '.join([c for c in skill_clusters_found.keys() if c in unrelated_clusters])})"
            )

        # Check for suspicious skill combinations
        suspicious_combos = SkillConsistency._check_suspicious_combinations(
            advanced_expert_skills, intermediate_skills, beginner_skills
        )
        penalty += len(suspicious_combos) * 2
        issues.extend(suspicious_combos)

        return penalty, issues

    @staticmethod
    def _check_suspicious_combinations(
        advanced: Set[str], intermediate: Set[str], beginner: Set[str]
    ) -> List[str]:
        """Check for suspicious skill combinations."""
        issues = []

        # Example: Expert in deep learning but beginner in Python
        if any(s.lower() in "deep learning neural network transformer" for s in advanced):
            if any(s.lower() == "python" for s in beginner):
                issues.append("Advanced ML skills but only beginner Python")

        # Too many advanced skills (more than 5)
        if len(advanced) > 8:
            issues.append(f"Suspiciously many advanced skills ({len(advanced)})")

        # Expert in unrelated fields (e.g., Photoshop + Kubernetes)
        if any(s.lower() in "photoshop figma design" for s in advanced):
            if any(s.lower() in "kubernetes docker devops" for s in advanced):
                issues.append("Unrelated skill expertise: Design + DevOps")

        return issues

    @staticmethod
    def calculate_skill_consistency_score(skills: List[Skill], career_history: List[Experience]) -> float:
        """
        Calculate skill consistency score (0-100).
        Higher is better.
        """
        base_score = 100.0
        penalty, _ = SkillConsistency.validate_skill_consistency(skills, career_history)
        return max(0, base_score - penalty)
