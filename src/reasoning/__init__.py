"""Reasoning subsystem — canonical entry via root ``reasoning`` package."""

from reasoning.generator import generate_reasoning_for
from reasoning.fact_extractor import compute_confidence, infer_experience_level
from reasoning.templates import TEMPLATE

__all__ = ["generate_reasoning_for", "compute_confidence", "infer_experience_level", "TEMPLATE"]
