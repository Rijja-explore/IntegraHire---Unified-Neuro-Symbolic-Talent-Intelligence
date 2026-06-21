"""
COMPATIBILITY SHIM for Ranking Config.
Re-exports from unified src/common/config.py location.
"""

from src.common.config import (
    IntelligenceWeights,
    AuthenticityConfig,
    TrajectoryWeights,
    BehaviorWeights,
    ProductionConfig,
    DNAWeights,
)

ProductionSignals = ProductionConfig  # backward compat alias
ScoringWeights = IntelligenceWeights  # backward compat alias

# For backward compatibility, provide the default instances used by old code
class _DefaultInstances:
    """Helper to create default instances for backward compatibility."""

    @staticmethod
    def get_defaults():
        """Return default instances for old code patterns."""
        return {
            'DEFAULT_SCORING_WEIGHTS': IntelligenceWeights(),
            'DEFAULT_THRESHOLD_CONFIG': AuthenticityConfig(),
            'DEFAULT_PRODUCTION_SIGNALS': ProductionConfig(),
            'DEFAULT_SKILL_WEIGHTS': None,  # Not needed in new unified config
            'DEFAULT_RANKER_CONFIG': None,  # Not needed in new unified config
        }


# Create singleton-like defaults for backward compatibility
_defaults = _DefaultInstances.get_defaults()
DEFAULT_SCORING_WEIGHTS = _defaults['DEFAULT_SCORING_WEIGHTS']
DEFAULT_THRESHOLD_CONFIG = _defaults['DEFAULT_THRESHOLD_CONFIG']
DEFAULT_PRODUCTION_SIGNALS = _defaults['DEFAULT_PRODUCTION_SIGNALS']

__all__ = [
    "IntelligenceWeights",
    "AuthenticityConfig",
    "TrajectoryWeights",
    "BehaviorWeights",
    "ProductionConfig",
    "ProductionSignals",
    "ScoringWeights",
    "DNAWeights",
    "DEFAULT_SCORING_WEIGHTS",
    "DEFAULT_THRESHOLD_CONFIG",
    "DEFAULT_PRODUCTION_SIGNALS",
]
