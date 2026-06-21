"""Compatibility shim — canonical constants live in ``src.common.constants``."""

from src.common.constants import DEFAULT_TOP_K, FINAL_SUBMISSION_ROWS, LOG_FORMAT

__all__ = ["LOG_FORMAT", "DEFAULT_TOP_K", "FINAL_SUBMISSION_ROWS"]
