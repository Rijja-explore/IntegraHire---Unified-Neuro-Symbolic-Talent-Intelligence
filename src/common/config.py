"""
Unified configuration system for the entire ranking pipeline.

This is the single source of truth for all configuration including:
- Embedding model and parameters
- Retrieval engine settings (BM25, FAISS, fusion)
- Intelligence engine weights and thresholds
- Ranking engine parameters

All values are loadable from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


# =============================================================================
# RETRIEVAL CONFIGURATION
# =============================================================================

@dataclass
class EmbeddingConfig:
    """Configuration for embedding model."""
    model_name: str = None
    batch_size: int = None
    max_seq_length: int = None
    cache_dir: Path = None
    device: str = None
    normalize: bool = None

    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
        self.max_seq_length = int(os.getenv("EMBEDDING_MAX_SEQ_LENGTH", "512"))
        self.cache_dir = Path(os.getenv("EMBEDDING_CACHE_DIR", "./embeddings_cache"))
        self.device = os.getenv("EMBEDDING_DEVICE", "cpu")
        self.normalize = os.getenv("EMBEDDING_NORMALIZE", "true").lower() == "true"


@dataclass
class BM25Config:
    """Configuration for BM25 retrieval."""
    k1: float = None
    b: float = None
    top_k: int = None

    def __init__(self):
        self.k1 = float(os.getenv("BM25_K1", "1.5"))
        self.b = float(os.getenv("BM25_B", "0.75"))
        self.top_k = int(os.getenv("BM25_TOP_K", "100"))


@dataclass
class FAISSConfig:
    """Configuration for FAISS indexing."""
    index_type: str = None  # flat, ivf, hnsw
    metric: str = None
    nprobe: int = None
    top_k: int = None
    index_path: Path = None
    use_gpu: bool = None

    def __init__(self):
        self.index_type = os.getenv("FAISS_INDEX_TYPE", "flat")
        self.metric = os.getenv("FAISS_METRIC", "cosine")
        self.nprobe = int(os.getenv("FAISS_NPROBE", "10"))
        self.top_k = int(os.getenv("FAISS_TOP_K", "100"))
        self.index_path = Path(os.getenv("FAISS_INDEX_PATH", "./faiss_index"))
        self.use_gpu = os.getenv("FAISS_USE_GPU", "false").lower() == "true"


@dataclass
class RetrievalEngineConfig:
    """Configuration for retrieval fusion."""
    bm25_weight: float = None
    embedding_weight: float = None
    rrf_k: int = None
    top_k: int = None
    min_score: float = None

    def __init__(self):
        self.bm25_weight = float(os.getenv("RETRIEVAL_BM25_WEIGHT", "0.4"))
        self.embedding_weight = float(os.getenv("RETRIEVAL_EMBEDDING_WEIGHT", "0.6"))
        self.rrf_k = int(os.getenv("RETRIEVAL_RRF_K", "60"))
        self.top_k = int(os.getenv("RETRIEVAL_TOP_K", "100"))
        self.min_score = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.0"))


@dataclass
class PreprocessingConfig:
    """Configuration for candidate preprocessing."""
    max_summary_length: int = None
    max_experience_chars: int = None
    include_skills: bool = None
    include_education: bool = None
    normalize_text: bool = None

    def __init__(self):
        self.max_summary_length = int(os.getenv("PREPROCESSING_MAX_SUMMARY", "500"))
        self.max_experience_chars = int(os.getenv("PREPROCESSING_MAX_EXPERIENCE", "2000"))
        self.include_skills = os.getenv("PREPROCESSING_INCLUDE_SKILLS", "true").lower() == "true"
        self.include_education = os.getenv("PREPROCESSING_INCLUDE_EDUCATION", "true").lower() == "true"
        self.normalize_text = os.getenv("PREPROCESSING_NORMALIZE_TEXT", "true").lower() == "true"


# =============================================================================
# INTELLIGENCE ENGINE CONFIGURATION
# =============================================================================

@dataclass
class IntelligenceWeights:
    """Final score fusion weights."""
    semantic_score: float = None
    production_score: float = None
    authenticity_score: float = None
    trajectory_score: float = None
    behavior_score: float = None
    dna_score: float = None

    def __init__(self):
        self.semantic_score = float(os.getenv("INTELLIGENCE_SEMANTIC_WEIGHT", "0.25"))
        self.production_score = float(os.getenv("INTELLIGENCE_PRODUCTION_WEIGHT", "0.20"))
        self.authenticity_score = float(os.getenv("INTELLIGENCE_AUTHENTICITY_WEIGHT", "0.20"))
        self.trajectory_score = float(os.getenv("INTELLIGENCE_TRAJECTORY_WEIGHT", "0.15"))
        self.behavior_score = float(os.getenv("INTELLIGENCE_BEHAVIOR_WEIGHT", "0.15"))
        self.dna_score = float(os.getenv("INTELLIGENCE_DNA_WEIGHT", "0.05"))

    def validate(self) -> None:
        """Validate weights sum to ~1.0."""
        total = sum([
            self.semantic_score, self.production_score,
            self.authenticity_score, self.trajectory_score,
            self.behavior_score, self.dna_score
        ])
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Intelligence weights must sum to 1.0, got {total}")


@dataclass
class AuthenticityConfig:
    """Configuration for authenticity scoring."""
    min_experience_years: float = None
    timeline_gap_threshold_months: int = None
    skill_consistency_threshold: float = None
    authenticity_floor: float = None
    # Hardcoded penalties (from timeline_validator.py)
    gap_penalty: float = None
    overlap_penalty: float = None
    short_role_penalty: float = None
    extreme_duration_penalty: float = None
    career_gap_penalty: float = None
    # Hardcoded penalties (from skill_consistency.py)
    skill_not_in_experience_penalty: float = None
    unrelated_skill_combo_penalty: float = None
    suspicious_skill_combo_penalty: float = None
    # Anomaly detection contamination rate
    anomaly_contamination: float = None

    def __init__(self):
        self.min_experience_years = float(os.getenv("AUTHENTICITY_MIN_EXPERIENCE_YEARS", "4.0"))
        self.timeline_gap_threshold_months = int(os.getenv("AUTHENTICITY_TIMELINE_GAP_MONTHS", "3"))
        self.skill_consistency_threshold = float(os.getenv("AUTHENTICITY_SKILL_CONSISTENCY", "0.6"))
        self.authenticity_floor = float(os.getenv("AUTHENTICITY_FLOOR", "30.0"))
        self.gap_penalty = float(os.getenv("AUTHENTICITY_GAP_PENALTY", "10.0"))
        self.overlap_penalty = float(os.getenv("AUTHENTICITY_OVERLAP_PENALTY", "15.0"))
        self.short_role_penalty = float(os.getenv("AUTHENTICITY_SHORT_ROLE_PENALTY", "5.0"))
        self.extreme_duration_penalty = float(os.getenv("AUTHENTICITY_EXTREME_DURATION_PENALTY", "8.0"))
        self.career_gap_penalty = float(os.getenv("AUTHENTICITY_CAREER_GAP_PENALTY", "5.0"))
        self.skill_not_in_experience_penalty = float(os.getenv("AUTHENTICITY_SKILL_NOT_IN_EXP_PENALTY", "3.0"))
        self.unrelated_skill_combo_penalty = float(os.getenv("AUTHENTICITY_UNRELATED_COMBO_PENALTY", "2.0"))
        self.suspicious_skill_combo_penalty = float(os.getenv("AUTHENTICITY_SUSPICIOUS_COMBO_PENALTY", "2.0"))
        self.anomaly_contamination = float(os.getenv("AUTHENTICITY_ANOMALY_CONTAMINATION", "0.05"))


@dataclass
class TrajectoryWeights:
    """Configuration for trajectory scoring."""
    progression_weight: float = None
    specialization_weight: float = None
    learning_velocity_weight: float = None
    specialization_bonus: float = None
    specialization_minimal: float = None

    def __init__(self):
        self.progression_weight = float(os.getenv("TRAJECTORY_PROGRESSION_WEIGHT", "0.7"))
        self.specialization_weight = float(os.getenv("TRAJECTORY_SPECIALIZATION_WEIGHT", "0.3"))
        self.learning_velocity_weight = float(os.getenv("TRAJECTORY_LEARNING_VELOCITY_WEIGHT", "0.5"))
        self.specialization_bonus = float(os.getenv("TRAJECTORY_SPECIALIZATION_BONUS", "0.2"))
        self.specialization_minimal = float(os.getenv("TRAJECTORY_SPECIALIZATION_MINIMAL", "0.1"))


@dataclass
class BehaviorWeights:
    """Configuration for behavioral scoring."""
    # Engagement score components
    response_rate_weight: float = None
    open_to_work_weight: float = None
    interview_rate_weight: float = None
    offer_rate_weight: float = None
    apps_30d_weight: float = None
    saved_recruiters_weight: float = None
    response_time_weight: float = None
    profile_complete_weight: float = None
    # Reliability score components
    verified_email_weight: float = None
    verified_phone_weight: float = None
    linkedin_connected_weight: float = None
    # Normalization thresholds
    apps_max_for_normalization: int = None
    saved_max_for_normalization: int = None
    response_time_cutoff_hours: float = None

    def __init__(self):
        # Engagement weights (sum to 1.0)
        self.response_rate_weight = float(os.getenv("BEHAVIOR_RESPONSE_RATE_WEIGHT", "0.25"))
        self.open_to_work_weight = float(os.getenv("BEHAVIOR_OPEN_TO_WORK_WEIGHT", "0.15"))
        self.interview_rate_weight = float(os.getenv("BEHAVIOR_INTERVIEW_RATE_WEIGHT", "0.15"))
        self.offer_rate_weight = float(os.getenv("BEHAVIOR_OFFER_RATE_WEIGHT", "0.10"))
        self.apps_30d_weight = float(os.getenv("BEHAVIOR_APPS_30D_WEIGHT", "0.10"))
        self.saved_recruiters_weight = float(os.getenv("BEHAVIOR_SAVED_RECRUITERS_WEIGHT", "0.10"))
        self.response_time_weight = float(os.getenv("BEHAVIOR_RESPONSE_TIME_WEIGHT", "0.10"))
        self.profile_complete_weight = float(os.getenv("BEHAVIOR_PROFILE_COMPLETE_WEIGHT", "0.05"))
        # Reliability weights (sum to 1.0)
        self.verified_email_weight = float(os.getenv("BEHAVIOR_VERIFIED_EMAIL_WEIGHT", "0.30"))
        self.verified_phone_weight = float(os.getenv("BEHAVIOR_VERIFIED_PHONE_WEIGHT", "0.20"))
        self.linkedin_connected_weight = float(os.getenv("BEHAVIOR_LINKEDIN_CONNECTED_WEIGHT", "0.50"))
        # Normalization thresholds
        self.apps_max_for_normalization = int(os.getenv("BEHAVIOR_APPS_MAX_NORMALIZE", "5"))
        self.saved_max_for_normalization = int(os.getenv("BEHAVIOR_SAVED_MAX_NORMALIZE", "3"))
        self.response_time_cutoff_hours = float(os.getenv("BEHAVIOR_RESPONSE_TIME_CUTOFF", "168"))  # 1 week


@dataclass
class ProductionConfig:
    """Configuration for production signals."""
    skill_weight_basis: float = None
    proficiency_weight: float = None
    duration_weight: float = None
    endorsement_weight: float = None
    skill_duration_max_months: int = None
    endorsement_max_count: int = None
    recency_days: int = None
    high_value_skills: Dict[str, float] = field(default_factory=dict)
    medium_value_skills: Dict[str, float] = field(default_factory=dict)
    low_value_skills: Dict[str, float] = field(default_factory=dict)
    default_skill_weight: float = None

    def __init__(self):
        self.skill_weight_basis = float(os.getenv("PRODUCTION_SKILL_WEIGHT_BASIS", "0.5"))
        self.proficiency_weight = float(os.getenv("PRODUCTION_PROFICIENCY_WEIGHT", "0.3"))
        self.duration_weight = float(os.getenv("PRODUCTION_DURATION_WEIGHT", "0.1"))
        self.endorsement_weight = float(os.getenv("PRODUCTION_ENDORSEMENT_WEIGHT", "0.1"))
        self.skill_duration_max_months = int(os.getenv("PRODUCTION_SKILL_DURATION_MAX", "24"))
        self.endorsement_max_count = int(os.getenv("PRODUCTION_ENDORSEMENT_MAX", "20"))
        self.recency_days = int(os.getenv("PRODUCTION_RECENCY_DAYS", "180"))
        self.default_skill_weight = float(os.getenv("PRODUCTION_DEFAULT_SKILL_WEIGHT", "0.4"))

        # Initialize skill value mappings
        self.high_value_skills = {
            "FAISS": 1.0, "Milvus": 1.0, "Qdrant": 1.0, "Weaviate": 1.0,
            "Pinecone": 1.0, "OpenSearch": 1.0, "Elasticsearch": 1.0,
            "Vector Search": 1.0, "Embedding": 1.0, "Retrieval": 1.0,
            "Ranking": 1.0, "Learning-to-Rank": 1.0, "XGBoost": 0.9,
            "LightGBM": 0.9, "Spark": 1.0, "Airflow": 1.0, "Kafka": 1.0,
            "Flink": 0.9, "MLOps": 1.0, "A/B Testing": 1.0,
            "Evaluation Framework": 1.0, "NDCG": 1.0, "MRR": 1.0,
            "Information Retrieval": 1.0, "LoRA": 0.8, "QLoRA": 0.8,
            "Fine-tuning": 0.8, "PEFT": 0.8
        }

        self.medium_value_skills = {
            "NLP": 0.6, "Transformers": 0.6, "ML": 0.5, "Deep Learning": 0.5,
            "Python": 0.7, "PyTorch": 0.6, "TensorFlow": 0.5, "Scikit-learn": 0.5,
            "Redis": 0.5, "SQL": 0.5, "Docker": 0.5, "Kubernetes": 0.6
        }

        self.low_value_skills = {
            "Prompt Engineering": 0.2, "ChatGPT": 0.1, "LangChain": 0.2,
            "OpenAI": 0.1, "Generative AI": 0.3, "RAG": 0.3
        }

    @property
    def high_value(self) -> Dict[str, float]:
        return self.high_value_skills

    @property
    def medium_value(self) -> Dict[str, float]:
        return self.medium_value_skills

    @property
    def low_value(self) -> Dict[str, float]:
        return self.low_value_skills


@dataclass
class DNAWeights:
    """Configuration for DNA dimension calculations."""
    # Technical depth: (0.5 production, 0.3 trajectory, 0.2 learning_velocity)
    technical_depth_production: float = None
    technical_depth_trajectory: float = None
    technical_depth_learning: float = None
    # Production readiness: (0.6 production, 0.2 behavior, 0.2 trajectory)
    production_readiness_production: float = None
    production_readiness_behavior: float = None
    production_readiness_trajectory: float = None
    # Behavior reliability: (0.3 behavior, 0.4 learning_velocity, 0.3 trajectory)
    behavior_reliability_behavior: float = None
    behavior_reliability_learning: float = None
    behavior_reliability_trajectory: float = None
    # Research orientation: (inverse, penalize PhD/academic)
    research_penalty_multiplier: float = None
    # Startup fit: (0.3 behavior, 0.4 learning_velocity, 0.3 trajectory)
    startup_behavior: float = None
    startup_learning: float = None
    startup_trajectory: float = None

    def __init__(self):
        self.technical_depth_production = float(os.getenv("DNA_TECHNICAL_PRODUCTION", "0.5"))
        self.technical_depth_trajectory = float(os.getenv("DNA_TECHNICAL_TRAJECTORY", "0.3"))
        self.technical_depth_learning = float(os.getenv("DNA_TECHNICAL_LEARNING", "0.2"))

        self.production_readiness_production = float(os.getenv("DNA_PRODREADY_PRODUCTION", "0.6"))
        self.production_readiness_behavior = float(os.getenv("DNA_PRODREADY_BEHAVIOR", "0.2"))
        self.production_readiness_trajectory = float(os.getenv("DNA_PRODREADY_TRAJECTORY", "0.2"))

        self.behavior_reliability_behavior = float(os.getenv("DNA_BEHRELIABILITY_BEHAVIOR", "0.3"))
        self.behavior_reliability_learning = float(os.getenv("DNA_BEHRELIABILITY_LEARNING", "0.4"))
        self.behavior_reliability_trajectory = float(os.getenv("DNA_BEHRELIABILITY_TRAJECTORY", "0.3"))

        self.research_penalty_multiplier = float(os.getenv("DNA_RESEARCH_PENALTY", "0.8"))

        self.startup_behavior = float(os.getenv("DNA_STARTUP_BEHAVIOR", "0.3"))
        self.startup_learning = float(os.getenv("DNA_STARTUP_LEARNING", "0.4"))
        self.startup_trajectory = float(os.getenv("DNA_STARTUP_TRAJECTORY", "0.3"))


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = None
    format: str = None  # json or text
    log_file: Optional[Path] = None

    def __init__(self):
        self.level = os.getenv("LOG_LEVEL", "INFO")
        self.format = os.getenv("LOGGING_FORMAT", "text")  # text or json
        log_file_path = os.getenv("LOG_FILE")
        self.log_file = Path(log_file_path) if log_file_path else None


# =============================================================================
# MAIN SYSTEM CONFIGURATION
# =============================================================================

@dataclass
class SystemConfig:
    """Main system configuration aggregating all sub-configs."""

    embedding: EmbeddingConfig = None
    bm25: BM25Config = None
    faiss: FAISSConfig = None
    retrieval: RetrievalEngineConfig = None
    preprocessing: PreprocessingConfig = None
    intelligence_weights: IntelligenceWeights = None
    authenticity: AuthenticityConfig = None
    trajectory: TrajectoryWeights = None
    behavior: BehaviorWeights = None
    production: ProductionConfig = None
    dna: DNAWeights = None
    logging: LoggingConfig = None

    def __post_init__(self):
        """Initialize all sub-configs."""
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.bm25 is None:
            self.bm25 = BM25Config()
        if self.faiss is None:
            self.faiss = FAISSConfig()
        if self.retrieval is None:
            self.retrieval = RetrievalEngineConfig()
        if self.preprocessing is None:
            self.preprocessing = PreprocessingConfig()
        if self.intelligence_weights is None:
            self.intelligence_weights = IntelligenceWeights()
        if self.authenticity is None:
            self.authenticity = AuthenticityConfig()
        if self.trajectory is None:
            self.trajectory = TrajectoryWeights()
        if self.behavior is None:
            self.behavior = BehaviorWeights()
        if self.production is None:
            self.production = ProductionConfig()
        if self.dna is None:
            self.dna = DNAWeights()
        if self.logging is None:
            self.logging = LoggingConfig()

    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Load configuration from environment variables."""
        return cls()

    def validate(self) -> None:
        """Validate all configuration values."""
        # Retrieval weights
        if not (0.0 <= self.retrieval.bm25_weight <= 1.0):
            raise ValueError("BM25 weight must be between 0 and 1")
        if not (0.0 <= self.retrieval.embedding_weight <= 1.0):
            raise ValueError("Embedding weight must be between 0 and 1")
        if abs(self.retrieval.bm25_weight + self.retrieval.embedding_weight - 1.0) > 0.01:
            raise ValueError("BM25 and embedding weights must sum to ~1.0")

        # Intelligence weights
        self.intelligence_weights.validate()


# =============================================================================
# GLOBAL CONFIGURATION SINGLETON
# =============================================================================

_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get the global system configuration (singleton)."""
    global _config
    if _config is None:
        _config = SystemConfig.from_env()
        _config.validate()
    return _config


def set_config(config: SystemConfig) -> None:
    """Set the global system configuration."""
    global _config
    config.validate()
    _config = config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
