"""
COMPATIBILITY SHIM for Retrieval Config.
Re-exports from unified src/common/config.py location.
"""

from src.common.config import (
    EmbeddingConfig,
    BM25Config,
    FAISSConfig,
    RetrievalEngineConfig,
    PreprocessingConfig,
    LoggingConfig,
    SystemConfig,
    get_config,
    set_config,
    reset_config,
)

__all__ = [
    "EmbeddingConfig",
    "BM25Config",
    "FAISSConfig",
    "RetrievalEngineConfig",
    "PreprocessingConfig",
    "LoggingConfig",
    "SystemConfig",
    "get_config",
    "set_config",
    "reset_config",
]
