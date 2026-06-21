"""Comprehensive README for Candidate Intelligence & Ranking System."""

# Candidate Intelligence & Ranking System

## Overview

A production-grade candidate intelligence and ranking subsystem for AI-powered recruiting platforms. This system evaluates candidates across multiple dimensions:

- **Authenticity**: Detects fake/suspicious profiles
- **Career Trajectory**: Measures progression quality and specialization
- **Production Readiness**: Assesses hands-on engineering experience
- **Behavioral Quality**: Evaluates recruiter engagement and reliability
- **Candidate DNA**: Generates multi-dimensional candidate profiles

## Architecture

```
ranking/
├── config.py                      # Configuration and weights
├── schemas.py                     # Pydantic models
├── feature_store.py               # Feature storage and pipeline
├── authenticity/
│   ├── timeline_validator.py      # Career timeline validation
│   ├── skill_consistency.py       # Skill clustering and buzzword detection
│   ├── anomaly_detector.py        # Isolation Forest anomaly detection
│   └── authenticity_engine.py     # Main authenticity scorer
├── trajectory/
│   └── trajectory_engine.py       # Career progression & specialization
├── production/
│   └── production_engine.py       # Production signals & systems
├── behavior/
│   └── behavioral_engine.py       # Recruiter engagement signals
├── dna/
│   └── dna_generator.py           # Candidate DNA dimensions
├── ranking/
│   └── ranking_engine.py          # Final score fusion & ranking
├── tests/
│   └── test_ranking.py            # Unit tests
└── main.py                        # Entry point
```

## Key Features

### 1. Authenticity Engine
- **Timeline Validation**: Detects overlapping positions, impossible dates, unrealistic gaps
- **Skill Consistency**: Validates skills match career history, detects buzzword inflation
- **Anomaly Detection**: Uses Isolation Forest on engineered features
- **Skill Clustering**: Groups related skills (ML, DataEng, DevOps, etc.)

### 2. Trajectory Engine
- **Progression Analysis**: Tracks career growth (junior → senior → lead)
- **Specialization Detection**: Identifies primary focus area
- **Learning Velocity**: Estimates skill acquisition rate
- **Industry Consistency**: Rewards deep specialization

### 3. Production Engine
- **Skill Scoring**: Weights production systems (FAISS, Milvus, Ranking, etc.)
- **Recency Checking**: Ensures current role involves production work
- **System Detection**: Extracts specific production systems from profile
- **Critical Signals**: Checks for must-have technologies

### 4. Behavioral Engine
- **Engagement Score**: Recruiter response rates, interview completion
- **Reliability Score**: Verified email/phone, LinkedIn connections
- **Availability**: Notice period, job market signals
- **Technical Validation**: Skill assessments, GitHub activity

### 5. DNA Generator
Eight-dimensional candidate profile:
- Technical Depth
- Production Readiness
- Research Orientation (lower is better for this role)
- Startup Fit
- Career Stability
- Behavior Reliability
- Authenticity
- Learning Velocity

### 6. Ranking Engine
- **Score Fusion**: Configurable weighted scoring
- **Default Weights**:
  - Semantic: 25% (from retrieval)
  - Production: 20%
  - Authenticity: 20%
  - Trajectory: 15%
  - Behavior: 15%
  - DNA: 5%
- **Explainability**: Score breakdown and strength/weakness identification

## Usage

### Basic Pipeline

```python
from feature_store import CandidateRankingPipeline
from schemas import CandidateProfile
from config import DEFAULT_SCORING_WEIGHTS

# Initialize
pipeline = CandidateRankingPipeline(scoring_weights=DEFAULT_SCORING_WEIGHTS)

# Fit on candidate pool (trains anomaly detector)
pipeline.fit(candidates)

# Process candidates
all_scores = pipeline.process_batch(candidates, semantic_scores)

# Rank
ranked_candidates = pipeline.rank(all_scores)

# Explain individual score
explanation = pipeline.explain_score(candidate_id)
```

### Loading Candidates

```python
import json
from schemas import CandidateProfile

# Load from JSONL
with open('candidates.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        candidate = CandidateProfile(**data)
```

### Integration with Retrieval

```python
# Get semantic scores from your retrieval system
semantic_scores = {
    "CAND_001": 85.0,
    "CAND_002": 72.0,
    ...
}

# Process through ranking pipeline
scores = pipeline.process_batch(candidates, semantic_scores)
ranked = pipeline.rank(scores)
```

## Configuration

### Scoring Weights

Modify `config.py` to adjust scoring:

```python
from config import ScoringWeights

weights = ScoringWeights(
    semantic_score=0.25,      # Retrieval relevance
    production_score=0.20,    # Production engineering
    authenticity_score=0.20,  # Profile authenticity
    trajectory_score=0.15,    # Career progression
    behavior_score=0.15,      # Recruiter engagement
    dna_score=0.05,          # Candidate DNA
)
```

### Production Signals

High-value signals (1.0):
- FAISS, Milvus, Qdrant, Weaviate, Pinecone
- Vector Search, Embedding, Retrieval, Ranking
- Spark, Airflow, Kafka
- A/B Testing, NDCG, MRR

Medium-value (0.5-0.7):
- NLP, Transformers, Python
- ML, Deep Learning

Low-value (0.1-0.3):
- Prompt Engineering, ChatGPT, LangChain

## Performance

- **Throughput**: ~50-100 candidates/second (depends on career history length)
- **Memory**: <16GB for 100k candidates
- **CPU-only**: No external API calls or GPU required
- **Reproducible**: Deterministic scoring (seeds set for randomness)

## Explainability

Each ranked candidate includes:
- Final score breakdown by component
- DNA dimensions
- Top strengths
- Top weaknesses

Example explanation:
```json
{
  "candidate_id": "CAND_001",
  "final_score": 82.5,
  "score_components": {
    "semantic_score": 75.0,
    "authenticity_score": 90.0,
    "production_score": 85.0,
    "behavior_score": 80.0,
    ...
  },
  "dna_dimensions": {
    "technical_depth": 88.0,
    "production_readiness": 92.0,
    "startup_fit": 78.0,
    ...
  }
}
```

## Job-Specific Tuning (Senior AI Engineer @ Redrob)

The system emphasizes:

1. **Production experience** (20% weight)
   - Rewards: FAISS, Milvus, Qdrant, Ranking, Learning-to-Rank
   - Penalizes: Pure research, LangChain tutorials

2. **Technical depth** (via DNA)
   - Requires embeddings & retrieval experience
   - Requires vector DB experience
   - Evaluates evaluation framework knowledge

3. **Behavioral signals** (15% weight)
   - Active on platform
   - Responsive to recruiters
   - Short notice period preferred

4. **Career stability** (DNA dimension)
   - Penalizes job-hoppers
   - Rewards 3+ year tenures
   - Identifies "title-chasers"

5. **Authenticity** (20% weight)
   - Detects keyword stuffing
   - Validates timeline consistency
   - Flags anomalous profiles

## Disqualifiers (Hard Filters)

Could be applied pre-ranking:
- Pure research background without production (authenticity floor)
- Recent AI experience only (< 12 months)
- Hasn't written production code (18 months+)
- Title-chasing pattern (frequent job changes)
- Only consulting firm experience
- Closed-source proprietary work (5+ years)

## Testing

Run tests:
```bash
cd ranking
pytest tests/test_ranking.py -v
```

Tests cover:
- Timeline validation
- Skill consistency
- Authenticity evaluation
- Trajectory analysis
- Production scoring
- Behavioral evaluation
- DNA generation
- Final ranking

## Running the Demo

```bash
python ranking/main.py
```

Processes first 1000 candidates and outputs:
- Top 100 ranked candidates
- Score explanations
- Results saved to `ranking_results.jsonl`

## Output Format

```json
{
  "rank": 1,
  "candidate_id": "CAND_0000001",
  "final_score": 85.2,
  "semantic_score": 75.0,
  "authenticity_score": 90.0,
  "trajectory_score": 82.0,
  "production_score": 88.0,
  "behavior_score": 80.0,
  "dna": {
    "technical_depth": 85.0,
    "production_readiness": 90.0,
    "startup_fit": 78.0,
    "career_stability": 85.0
  },
  "top_strengths": [
    "Strong semantic match to job description",
    "Proven production engineering experience",
    "Excellent production readiness"
  ],
  "top_weaknesses": []
}
```

## Future Enhancements

1. **LightGBM Learning-to-Rank**: With labeled training data
2. **Online A/B Testing**: Track which scores correlate with hires
3. **Active Learning**: Identify high-uncertainty candidates
4. **Multi-language Support**: Handle international profiles
5. **Real-time Updates**: Streaming candidate profile changes
6. **Custom Filters**: Hard requirements per JD

## Design Philosophy

- **Explainable**: Every score has a clear breakdown
- **CPU-efficient**: No external APIs, vectorized operations
- **Scalable**: Designed for 100k+ candidates
- **Reproducible**: Deterministic with fixed seeds
- **Defensive**: Detects honeypot profiles and keyword stuffing
- **Production-focused**: Rewards shipping ability over keywords

## Authors

Candidate Intelligence Team
Redrob AI - Series A AI-native Recruiting Platform
