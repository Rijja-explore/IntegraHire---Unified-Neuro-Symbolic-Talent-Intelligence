"""Pydantic schemas for candidate profiles and scores."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Skill(BaseModel):
    name: str
    proficiency: str  # beginner, intermediate, advanced, expert
    endorsements: int = 0
    duration_months: int = 0

class Experience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: str  # tier_1, tier_2, tier_3, tier_4, tier_5

class Certification(BaseModel):
    name: str
    issuer: str
    year: int

class Language(BaseModel):
    language: str
    proficiency: str

class BehavioralSignals(BaseModel):
    profile_completeness_score: float
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool
    profile_views_received_30d: int
    applications_submitted_30d: int
    recruiter_response_rate: float
    avg_response_time_hours: float
    skill_assessment_scores: Dict[str, float]
    connection_count: int
    endorsements_received: int
    notice_period_days: int
    expected_salary_range_inr_lpa: Optional[Dict[str, float]]
    preferred_work_mode: str
    willing_to_relocate: bool
    github_activity_score: float
    search_appearance_30d: int
    saved_by_recruiters_30d: int
    interview_completion_rate: float
    offer_acceptance_rate: float
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool

class Profile(BaseModel):
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str

class CandidateProfile(BaseModel):
    """Complete candidate profile."""
    candidate_id: str
    profile: Profile
    career_history: List[Experience]
    education: List[Education]
    skills: List[Skill]
    certifications: List[Certification]
    languages: List[Language]
    redrob_signals: BehavioralSignals

class CandidateDNA(BaseModel):
    """Candidate DNA dimensions (0-100 scale)."""
    technical_depth: float
    production_readiness: float
    research_orientation: float
    startup_fit: float
    career_stability: float
    behavior_reliability: float
    authenticity: float
    learning_velocity: float

class CandidateScores(BaseModel):
    """All scoring dimensions for a candidate."""
    candidate_id: str
    semantic_score: float  # Input from retrieval
    authenticity_score: float
    anomaly_score: float
    trajectory_score: float
    learning_velocity_score: float
    production_score: float
    behavior_score: float
    dna_score: float
    final_score: float
    dna: CandidateDNA

class RankedCandidate(BaseModel):
    """Final ranked candidate for output."""
    candidate_id: str
    rank: int
    semantic_score: float
    authenticity_score: float
    trajectory_score: float
    production_score: float
    behavior_score: float
    dna_score: float
    final_score: float
    dna_dimensions: CandidateDNA
    top_strengths: List[str] = Field(default_factory=list)
    top_weaknesses: List[str] = Field(default_factory=list)

class FeatureVector(BaseModel):
    """Feature vector for a candidate."""
    candidate_id: str
    features: List[float]  # Flattened feature vector
    feature_names: List[str]
