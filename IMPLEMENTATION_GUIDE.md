"""
Implementation Guide and Deployment Notes for Candidate Ranking System
"""

# IMPLEMENTATION GUIDE

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   Input Layer                                    │
│  - Candidate Profiles (JSONL) + Retrieval Scores (JSON)          │
└────────────────────────────────┬────────────────────────────────┘
                                  │
                   ┌──────────────────────────────┐
                   │  CandidateRankingPipeline     │
                   └──────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┬──────────┐
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
  ┌─────────┐┌────────┐┌───────┐┌──────┐┌────────┐
  │Authentic││Trajec- ││Prod.  ││Behav-││DNA     │
  │ity      ││tory    ││Signals││ioral ││Gener.  │
  │Engine   ││Engine  ││Engine ││Engine││        │
  └────┬────┘└────┬───┘└───┬───┘└──┬───┘└───┬────┘
       │          │        │       │        │
       └──────────┼────────┼───────┼────────┘
                  │
         ┌────────▼─────────┐
         │  Score Fusion    │
         │  & Ranking       │
         └────────┬─────────┘
                  │
       ┌──────────▼──────────┐
       │ Ranked Candidates   │
       │ + Explanations      │
       └─────────────────────┘
```

## Module Responsibilities

### 1. config.py
**Purpose**: Centralized configuration and constants

**Key Components**:
- `ScoringWeights`: Configurable score fusion weights (0.25, 0.20, 0.20, etc.)
- `SkillWeights`: Skill importance multipliers (FAISS=1.0, ChatGPT=0.1)
- `ThresholdConfig`: Decision thresholds and cutoffs
- `ProductionSignals`: High/medium/low value signal dictionaries
- `RankerConfig`: LightGBM configuration (for future use)

**Design Principles**:
- All weights are configurable (no hard-coded thresholds)
- Weights documented with rationale
- Easy to A/B test different configurations

### 2. schemas.py
**Purpose**: Data contracts using Pydantic

**Key Models**:
- `CandidateProfile`: Complete candidate data
- `CandidateScores`: All computed scores for a candidate
- `CandidateDNA`: 8-dimensional DNA profile
- `RankedCandidate`: Output format with explanation
- `FeatureVector`: Engineered features for ML

**Design Principles**:
- Type validation at boundaries
- Clear field documentation
- Compatible with JSON serialization

### 3. Authenticity Engine
**Files**: `authenticity/timeline_validator.py`, `skill_consistency.py`, `anomaly_detector.py`, `authenticity_engine.py`

**Responsibilities**:
1. **Timeline Validation** (timeline_validator.py)
   - Detects overlapping positions (B started before A ended)
   - Checks for negative durations
   - Validates dates are parseable and logical
   - Penalizes unrealistic claims (40-year tenure)

2. **Skill Consistency** (skill_consistency.py)
   - Groups skills into clusters (ML, DataEng, DevOps, etc.)
   - Detects advanced skills without supporting experience
   - Flags suspicious combinations (Expert ML + Beginner Python)
   - Calculates consistency score (100 - penalties)

3. **Anomaly Detection** (anomaly_detector.py)
   - Extracts 10 features per candidate
   - Trains Isolation Forest on candidate pool
   - Produces anomaly score (0-100)
   - Flags unusual profiles

4. **Main Engine** (authenticity_engine.py)
   - Orchestrates all three components
   - Combines penalties multiplicatively (score * factor)
   - Produces: (auth_score, anomaly_score, detailed_analysis)

**Output**:
- `authenticity_score`: 0-100 (higher = more trustworthy)
- `anomaly_score`: 0-100 (higher = more suspicious)
- `analysis`: Dict with issues found

### 4. Trajectory Engine
**File**: `trajectory/trajectory_engine.py`

**Responsibilities**:
1. **Progression Analysis**
   - Extracts seniority level from each job title
   - Rewards steady progression (L3→L4→L5)
   - Penalizes demotions
   - Scores 0-100 based on progression quality

2. **Specialization Detection**
   - Maps each role to specialization (ML, Data, Backend, etc.)
   - Calculates focus score = (roles in dominant specialization / total roles) * 100
   - Rewards deep focus, penalizes constant switching

3. **Learning Velocity**
   - Counts specialized skills acquired per year
   - Measures career growth pace
   - Produces 0-100 score

**Output**:
- `trajectory_score`: 0-100 (career progression quality)
- `learning_velocity_score`: 0-100 (skill acquisition rate)
- `analysis`: Specialization, progression issues

### 5. Production Engine
**File**: `production/production_engine.py`

**Responsibilities**:
1. **Skill Scoring**
   - Maps each skill to production value (0.1-1.0)
   - FAISS/Milvus/Qdrant = 1.0 (must-haves)
   - LightGBM = 0.9 (valuable)
   - ChatGPT = 0.1 (low value)
   - Combines skill weight + proficiency + endorsements

2. **Production Recency**
   - Checks current role is production-focused
   - Applies penalty if non-technical title
   - Scores availability (currently shipping vs not)

3. **System Detection**
   - Extracts specific systems from profile
   - Looks for: FAISS, Milvus, Ranking, Evaluation Framework
   - Penalties for missing critical signals

**Output**:
- `production_score`: 0-100 (production readiness)
- `analysis`: Top systems, missing signals, skill breakdown

### 6. Behavioral Engine
**File**: `behavior/behavioral_engine.py`

**Responsibilities**:
1. **Engagement Score**
   - Recruiter response rate (0-1)
   - Open to work flag
   - Interview completion rate
   - Application activity
   - Saved by recruiters count
   - Profile completeness
   - Combines with weights: response_rate*0.25 + interview*0.15 + ...

2. **Reliability Score**
   - Email verified: 0.3 weight
   - Phone verified: 0.2 weight
   - LinkedIn connected: 0.2 weight
   - Connection count (proxy for legitimacy): 0.3 weight

3. **Availability Score**
   - Notice period (14 days = 100, 150+ days = 20)
   - Recent activity
   - Job market signals (search appearance, saved count)

4. **Technical Validation**
   - Skill assessment scores
   - GitHub activity score

**Output**:
- `behavior_score`: 0-100 (recruiter interaction quality)
- `analysis`: Component scores, activity status

### 7. DNA Generator
**File**: `dna/dna_generator.py`

**Produces 8 Dimensions**:
1. **Technical Depth**: Production + Trajectory + Learning Velocity
   - Formula: 0.5*prod + 0.3*traj + 0.2*velocity
   
2. **Production Readiness**: Direct measure of shipping ability
   - Formula: 0.6*prod + 0.2*behav + 0.2*traj
   
3. **Research Orientation**: PhD degree, publications, academic language
   - Negatively correlated with this role
   - High score = more academic (penalized)
   
4. **Startup Fit**: Comfort with ambiguity and fast movement
   - Formula: 0.3*behav + 0.4*learning_vel + 0.3*traj
   
5. **Career Stability**: Average job tenure, job-hopping penalty
   - Rewards 3+ year tenures, penalizes frequent moves
   
6. **Behavior Reliability**: Direct copy of behavior score
   
7. **Authenticity**: Direct copy of authenticity score
   
8. **Learning Velocity**: Direct copy of learning velocity score

**Output**: `CandidateDNA` object with all 8 scores (0-100 each)

### 8. Ranking Engine
**File**: `ranking/ranking_engine.py`

**Responsibilities**:
1. **Score Fusion**
   - Weighted sum of 6 components:
     - Semantic (from retrieval): 25%
     - Production: 20%
     - Authenticity: 20%
     - Trajectory: 15%
     - Behavior: 15%
     - DNA: 5%
   - Produces final_score (0-100)

2. **Strength/Weakness Identification**
   - Strengths: Components > 70
   - Weaknesses: Components < 50
   - DNA-based insights

3. **Ranking**
   - Sort by final_score descending
   - Assign ranks
   - Prepare output

**Output**: `RankedCandidate` with all details

### 9. Feature Store
**File**: `feature_store.py`

**Responsibilities**:
1. **CandidateRankingPipeline**: Main orchestrator
   - Initializes all engines
   - Coordinates batch processing
   - Manages feature storage
   
2. **FeatureStore**: In-memory cache
   - Stores computed features
   - Stores scores
   - Enables explainability

**Key Methods**:
- `fit()`: Trains anomaly detector
- `process_candidate()`: Single candidate through pipeline
- `process_batch()`: Multiple candidates
- `rank()`: Produces final ranking
- `explain_score()`: Score breakdown

## Integration Points

### Input: Retrieval Scores
```python
semantic_scores = {
    "CAND_001": 85.0,  # BM25 or embedding similarity (0-100)
    "CAND_002": 72.0,
    ...
}
```

### Output: Ranked Results
```json
{
  "rank": 1,
  "candidate_id": "CAND_001",
  "final_score": 84.2,
  "semantic_score": 85.0,
  "authenticity_score": 90.0,
  ...
  "top_strengths": [...],
  "top_weaknesses": [...]
}
```

## Performance Tuning

### Batch Processing
```python
# Process in batches to manage memory
for batch in chunked(candidates, batch_size=1000):
    scores = pipeline.process_batch(batch, semantic_scores)
    save_to_disk(scores)
```

### Caching
- Anomaly detector fitted once, reused for all candidates
- Feature extraction vectorized where possible
- No redundant computation

### Parallelization
Current system is single-threaded. For 100k candidates:
```python
from multiprocessing import Pool

def process_chunk(chunk):
    return pipeline.process_batch(chunk, semantic_scores)

with Pool(8) as pool:
    all_scores = pool.map(process_chunk, chunked(candidates, 1000))
```

## Testing Strategy

### Unit Tests (tests/test_ranking.py)
- Timeline validation
- Skill consistency
- Authenticity engine
- Trajectory analysis
- Production scoring
- Behavioral evaluation
- DNA generation
- Final ranking

### Integration Tests
```python
# Load sample data
candidates = load_candidates(sample_jsonl)

# Run full pipeline
pipeline = CandidateRankingPipeline()
pipeline.fit(candidates)
scores = pipeline.process_batch(candidates, semantic_scores)
ranked = pipeline.rank(scores)

# Validate output
assert len(ranked) == len(candidates)
assert all(0 <= c.final_score <= 100 for c in ranked)
assert ranked[0].final_score >= ranked[-1].final_score
```

### Validation Tests
```python
# Check for edge cases
- Empty career history
- No skills
- Invalid dates
- Extreme values
- Null/None fields
```

## Deployment

### Single-Machine Deployment
1. Install dependencies: `pip install pydantic scikit-learn`
2. Copy ranking/ directory
3. Run: `python ranking/main.py`

### Distributed Deployment
```python
# Leader process
pipeline = CandidateRankingPipeline()
pipeline.fit(all_candidates)

# Distribute to workers
for chunk in chunks:
    queue.put(chunk)

# Worker process
while True:
    chunk = queue.get()
    scores = pipeline.process_batch(chunk, semantic_scores)
    save_results(scores)
```

### Monitoring
```python
# Log key metrics
- candidates_processed: counter
- avg_processing_time: histogram
- score_distribution: percentiles (10th, 50th, 90th, 99th)
- anomaly_detection_rate: ratio
- authentication_score_distribution: histogram
```

## Future Enhancements

1. **LightGBM Learning-to-Rank**
   - With labeled training data (hired/rejected)
   - Learn optimal feature weights
   - Online model updates

2. **Online Feedback Loop**
   - Track which ranked candidates convert (offer -> hire)
   - Measure offline-online correlation
   - Continuously retrain weights

3. **Hard Filters**
   - Minimum years of experience (5)
   - Minimum production score (threshold)
   - Exclude pure academic backgrounds

4. **Custom JD Weights**
   - Different roles get different weight configs
   - Senior IC role vs Manager role vs Researcher role
   - Learn per-JD weights from hiring data

5. **Real-time Updates**
   - Stream candidate profile changes
   - Incremental scoring
   - Trigger re-ranking on significant changes

6. **Explainability Dashboard**
   - Visualize score components
   - Show career timeline
   - Highlight production systems found
   - Compare candidate to cohort

## Code Quality

**Standards**:
- Type hints throughout (PEP 484)
- Docstrings for all public methods
- Logging for tracing
- No magic numbers (all in config.py)
- Pydantic models for all data contracts

**Dependencies**:
- pydantic: Type validation
- scikit-learn: Isolation Forest
- numpy: Vectorized operations
- Standard library only (no external APIs)

**Performance Guarantees**:
- O(n) time complexity (single pass per candidate)
- O(1) space per candidate (excluding feature store)
- Deterministic results (fixed seeds)
- CPU-only (no GPU required)

## Maintenance

**Regular Tasks**:
1. Monitor anomaly detection rate (should stay ~5-10%)
2. Check score distribution (should be roughly normal)
3. Validate against known good/bad candidates
4. Review false positives from authenticity engine
5. Track which candidates in top 100 actually get hired

**Periodic Reviews**:
- Refit anomaly detector monthly on new candidate pool
- A/B test different weight configurations
- Analyze candidate profiles that scored unexpectedly
- Update production signals list as new tools emerge

**Alerting**:
- Authenticity score below 30: likely fake profile
- Anomaly score above 80: investigate further
- Production score below 20: missing critical experience
- Behavior score below 40: candidate unlikely to respond
