from typing import Tuple
import statistics


def infer_experience_level(final_score: float) -> str:
    if final_score >= 85:
        return "Senior"
    if final_score >= 65:
        return "Mid"
    return "Junior"


def compute_confidence(scores: Tuple[float, ...]) -> float:
    # lower variance => higher confidence; normalized to 0..1
    if len(scores) == 0:
        return 0.0
    try:
        var = statistics.pvariance(scores)
    except Exception:
        var = 0.0
    # simple mapping: cap variance
    conf = 1.0 - min(var / 2500.0, 1.0)
    return round(conf, 3)


def production_strength(production_score: float) -> str:
    if production_score >= 80:
        return "strong production engineering background"
    if production_score >= 50:
        return "solid production experience"
    return "limited production exposure"


def behavior_level(behavior_score: float) -> str:
    if behavior_score >= 75:
        return "high recruiter engagement"
    if behavior_score >= 45:
        return "moderate recruiter engagement"
    return "low recruiter engagement"


def trajectory_quality(trajectory_score: float) -> str:
    if trajectory_score >= 75:
        return "consistent career growth"
    if trajectory_score >= 45:
        return "somewhat variable career trajectory"
    return "unstable career progression"


def authenticity_risk(authenticity_score: float) -> str:
    if authenticity_score >= 80:
        return "low authenticity risk"
    if authenticity_score >= 50:
        return "minor authenticity risk"
    return "moderate authenticity risk"
