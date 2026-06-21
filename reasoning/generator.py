from typing import Tuple, Optional, Set
from reasoning.fact_extractor import compute_confidence
from typing import Any

# CandidateRecord was part of an older schema; current pipeline passes simple objects/dicts.
CandidateRecord = Any
import re


def _tokenize(text: str) -> Set[str]:
    """Extract lowercase alphanumeric tokens for JD/skill matching."""
    if not text:
        return set()
    toks = re.findall(r"[a-zA-Z0-9#+\-_]+", text.lower())
    return set(toks)


def _extract_profile_facts(profile: dict) -> dict:
    """Extract key facts from profile, ensuring no hallucination."""
    facts = {
        "years": None,
        "title": None,
        "company": None,
        "skills": [],
        "headline": None,
        "education": [],
        "current_company_size": None,
    }
    if not profile:
        return facts

    prof = profile.get("profile") if isinstance(profile.get("profile"), dict) else profile
    facts["years"] = prof.get("years_of_experience")
    facts["title"] = prof.get("current_title")
    facts["company"] = prof.get("current_company")
    facts["headline"] = prof.get("headline")
    facts["current_company_size"] = prof.get("current_company_size")

    # Extract skills (list of objects with 'name', 'proficiency', 'endorsements')
    skills_obj_list = profile.get("skills") or prof.get("skills") or []
    for s in skills_obj_list:
        if isinstance(s, dict):
            name = s.get("name")
            proficiency = s.get("proficiency")
            if name:
                facts["skills"].append({"name": name, "proficiency": proficiency})
        elif isinstance(s, str):
            facts["skills"].append({"name": s, "proficiency": None})

    # Extract education (tier if available)
    edu_list = profile.get("education") or prof.get("education") or []
    for e in edu_list:
        if isinstance(e, dict):
            inst = e.get("institution")
            tier = e.get("tier")
            if inst:
                facts["education"].append({"institution": inst, "tier": tier})

    return facts


def _match_jd_skills(facts: dict, jd_text: str) -> list:
    """Find skills in profile that are mentioned in JD. No hallucination."""
    if not jd_text or not facts.get("skills"):
        return []
    jd_tokens = _tokenize(jd_text)
    matched = []
    for s_obj in facts["skills"]:
        name = s_obj.get("name", "")
        if name and name.lower() in jd_tokens:
            matched.append(name)
    return matched[:5]  # limit to top 5 matched skills


def _score_interpretation(score: float, min_val: float = 0.0, max_val: float = 100.0) -> str:
    """Interpret a signal score into a short phrase."""
    if score < 0:
        return "no signal"
    pct = (score - min_val) / (max_val - min_val) if max_val > min_val else 0
    if pct >= 0.85:
        return "very strong"
    if pct >= 0.70:
        return "strong"
    if pct >= 0.50:
        return "moderate"
    if pct >= 0.30:
        return "limited"
    return "weak"


def generate_reasoning_for(record: CandidateRecord, profile: Optional[dict] = None, jd_text: Optional[str] = None) -> Tuple[str, float]:
    """Generate specific, honest, profile-truthful reasoning.

    Returns (reasoning_text, confidence)
    Only reference facts actually present in the profile. Never hallucinate skills, employers, or experience.
    """
    scores = (
        record.semantic_score,
        record.authenticity_score,
        record.trajectory_score,
        record.behavior_score,
        record.production_score,
        record.final_score,
    )
    confidence = compute_confidence(scores)

    # Extract only truthful facts from profile
    facts = _extract_profile_facts(profile)

    # Build reasoning sentences
    sentences = []

    # 1. Experience and current role
    if facts["years"] is not None:
        sentences.append(f"{facts['years']:.1f}y experience, current: {facts['title'] or 'Professional'}")
        if facts["company"]:
            sentences.append(f"at {facts['company']} ({facts.get('current_company_size', 'n/a')})")
    elif facts["title"]:
        sentences.append(f"Current role: {facts['title']}")

    # 2. JD alignment (only if we can match skills)
    if jd_text:
        matched_skills = _match_jd_skills(facts, jd_text)
        if matched_skills:
            sentences.append(f"JD-relevant skills: {', '.join(matched_skills)}")
        else:
            sentences.append("Skills do not explicitly match JD keywords")

    # 3. Score interpretation (specific numeric facts)
    sig_parts = []
    if record.production_score > 0:
        sig_parts.append(f"production {_score_interpretation(record.production_score)}")
    if record.behavior_score > 0:
        sig_parts.append(f"recruiter engagement {_score_interpretation(record.behavior_score)}")
    if record.trajectory_score > 0:
        sig_parts.append(f"trajectory {_score_interpretation(record.trajectory_score)}")
    if record.authenticity_score > 0:
        sig_parts.append(f"authenticity {_score_interpretation(record.authenticity_score)}")

    if sig_parts:
        sentences.append(f"Signals: {', '.join(sig_parts)}")

    # 4. Rank-appropriate tone (be honest about rank)
    final_norm = record.final_score / 100.0 if record.final_score > 0 else 0
    if final_norm >= 0.85:
        sentences.append("Strong fit with high confidence.")
    elif final_norm >= 0.65:
        sentences.append("Solid candidate with reasonable alignment.")
    elif final_norm >= 0.40:
        sentences.append("Moderate fit; relevant experience present but gaps noted.")
    else:
        sentences.append("Limited alignment; significant ramp-up required.")

    # 5. Education if tier_1 or tier_2
    for edu in facts.get("education", []):
        tier = edu.get("tier")
        if tier in ["tier_1", "tier_2"]:
            sentences.append(f"Educated at {edu['institution']} (tier {tier[5:]}).")
            break

    reasoning = " ".join(sentences)
    return reasoning, confidence
