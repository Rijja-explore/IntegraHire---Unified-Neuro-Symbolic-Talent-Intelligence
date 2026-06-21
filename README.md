# Recruiter Cognitive Twin (RCT) — Ranking Engine

Production-grade deterministic ranking system for the Intelligent Candidate Discovery & Ranking Challenge. Designed to run on CPU under 5 minutes with ≤16GB RAM, no external APIs, and zero hallucination in reasoning.

## Architecture

The system consists of modular components that work together to produce a ranked submission:

```
retrieval.json + ranking.json + candidates.jsonl + JD text
    ↓
[Orchestrator] → merge + stream top-k selection
    ↓
[Reasoning Engine] → profile-aware, JD-matched reasoning per candidate
    ↓
[Validator] → strict schema/monotonicity/existence checks
    ↓
[CSV Export] → deterministic, 100-row submission
```

### Components

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `orchestrator/pipeline.py` | Main entry point, coordinates workflow | Logging, error handling, metadata output |
| `orchestrator/topk.py` | Streaming top-K selection | Min-heap O(K) memory, deterministic tie-breaks |
| `reasoning/generator.py` | Profile-truthful reasoning generation | JD matching, no hallucination, confidence scores |
| `export/validator.py` | Strict submission validation | 100 rows, monotonic scores, existence checks |
| `export/csv_writer.py` | CSV serialization | UTF-8, proper escaping, format validation |
| `evaluation/ndcg.py` | NDCG@K computation | Batch evaluation, configurable K |
| `demo/app.py` | Streamlit web interface | Upload inputs, preview results, download CSV |

## Setup

### Requirements
- Python 3.11+
- ~100MB disk for dependencies
- No GPU required; CPU-only

### Installation

```bash
# Clone or download the repository
cd IntegraHire---Unified-Neuro-Symbolic-Talent-Intelligence

# Install Python dependencies
pip install -r requirements.txt
```

## Usage

### Full Pipeline (Recommended)

Runs retrieval → intelligence → ranking → reasoning → CSV in one command:

```bash
pip install -r requirements.txt

python rank.py \
    --candidates candidates.jsonl \
    --job_description job_description.txt \
    --output submission.csv
```

On first run, BM25/FAISS indexes are built under `./retrieval/retrieval_indices/`.
Subsequent runs reuse cached indexes. Pre-download the embedding model for offline use:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
```

Optional flags:
- `--pool-size 2000` — retrieval pool before intelligence scoring (default: 2000)
- `--rebuild-indexes` — force index rebuild
- `--index-dir ./retrieval/retrieval_indices` — custom index location

Validate output:
```bash
python validate_submission.py submission.csv
```

### Pre-Scored Mode

If you already have retrieval and ranking JSON files:

```bash
python rank.py \
    --retrieval retrieval.json \
    --ranking ranking.json \
    --output submission.csv \
    --candidates candidates.jsonl \
    --jd job_description.txt
```

**Arguments:**
- `--retrieval` (required): JSON file with retrieval results (list of candidates + semantic_score, etc.)
- `--ranking` (required): JSON file with ranking signals (list of candidates + authenticity_score, etc.)
- `--output` (required): Path to write the output CSV
- `--candidates` (optional): Path to `candidates.jsonl` for profile-aware reasoning and strict validation
- `--jd` (optional): Path to JD text file for skill matching in reasoning

**Example Output:**
```
Ranking complete. Output written to: submission.csv
Generated files:
  - submission.csv (100 rows, deterministically ranked)
  - submission.csv.metadata.json (pipeline timing, counts)
  - submission.csv.top100.json (debug info with reasoning)
```

### Streamlit Web Interface

```bash
streamlit run demo/app.py
```

Opens a browser UI where you can:
1. Paste or edit the Job Description
2. Upload retrieval and ranking JSON files
3. Optionally enable local `candidates.jsonl` for profile-aware reasoning
4. View top 10 candidates with reasoning
5. Download the submission CSV

## Data Contracts

### Input: retrieval.json
```json
[
  {
    "candidate_id": "CAND_0000001",
    "semantic_score": 0.85,
    "bm25_score": 0.72,
    "embedding_score": 0.88
  },
  ...
]
```

### Input: ranking.json
```json
[
  {
    "candidate_id": "CAND_0000001",
    "authenticity_score": 88.5,
    "trajectory_score": 76.2,
    "behavior_score": 82.1,
    "production_score": 90.3,
    "final_score": 87.25
  },
  ...
]
```

### Input: candidates.jsonl (per `candidate_schema.json`)
```jsonl
{"candidate_id": "CAND_0000001", "profile": {...}, "career_history": [...], "skills": [...], "redrob_signals": {...}}
```

### Output: submission.csv
```csv
candidate_id,rank,score,reasoning
CAND_0001234,1,0.987654,Senior AI Engineer with 7.2y experience at TechCorp (10001+). JD-relevant skills: Python, Kubernetes. Signals: production very strong, recruiter engagement strong, trajectory strong, authenticity strong. Strong fit with high confidence. Educated at IIT Bombay (tier 1).
CAND_0005678,2,0.976543,...
...
CAND_0009999,100,0.445432,...
```

## Key Features

### 1. Deterministic Ranking
- Primary sort: `final_score` descending
- Secondary tie-breaks: computed secondary signal, semantic_score, candidate_id ascending
- No randomness; identical inputs → identical outputs

### 2. Streaming Top-K Selection
- Memory efficient: O(K) = O(100) heap for candidates
- CPU efficient: O(N log K) where N = total candidates
- Handles 200k+ candidates under time/memory limits

### 3. Profile-Truthful Reasoning
- Only references skills, experience, companies, education actually in the profile
- Never hallucinating credentials or companies
- JD keyword matching to find relevant skills
- Rank-appropriate tone (strong fit vs. moderate fit vs. gaps)
- Confidence scores reflect signal consistency

### 4. Strict Validation
- **Exactly 100 rows**: fails if not 100 data rows
- **Unique ranks 1–100**: each rank appears exactly once
- **Non-increasing scores**: score[rank_i] ≥ score[rank_i+1]
- **Unique candidate_ids**: no duplicates
- **Existence check**: all candidates exist in candidates.jsonl
- **Non-empty reasoning**: every candidate has reasoning text

### 5. Reproducibility
- Fixed seeds/no randomness (deterministic by design)
- Metadata output includes timing and candidate counts
- Debug JSON includes all reasoning and confidence scores
- Full logging of pipeline stages

## Performance Characteristics

- **Runtime**: <5 seconds typical for 200k candidates → top 100
  - Merge: O(N)
  - Top-K selection: O(N log 100)
  - Reasoning generation: ~50ms per candidate × 100 = ~5s
  - CSV write + validation: ~100ms
- **Memory**: ~200MB active for 200k+ candidates (heap-based)
- **Network**: Zero API calls; fully offline
- **Disk**: ~1MB per run (CSV + metadata + debug JSON)

## Architecture Decisions

### Why Streaming Top-K?
Production-scale hiring systems cannot fit all candidates in memory. Using a min-heap of size K ensures the ranking engine scales to 200k+ candidates while staying under 16GB RAM.

### Why No LLM During Ranking?
LLM calls per candidate (even local) would exceed the 5-minute budget. Reasoning is generated deterministically from profile facts and signal scores, matching the "no external API" constraint.

### Why Deterministic Tie-Breaks?
Competition judges reproduce submissions in sandboxed environments. Randomized tie-breaks or time-based ordering would fail reproducibility checks. All tie-breaking uses deterministic, sortable fields.

### Why Profile-Based Reasoning?
Stage 4 manual review explicitly penalizes hallucination (claiming skills not in the profile). By extracting only facts from the structured profile, we guarantee every claim is verifiable.

## Testing

Run unit tests:
```bash
python tools/run_quick_checks.py
```

Run validation on existing CSV:
```bash
python validate_submission.py submission.csv
```

## Debugging

### Check pipeline logs
```bash
python rank.py ... 2>&1 | tee ranking.log
```

### Inspect debug JSON
```bash
python -m json.tool submission.csv.top100.json
```

### Inspect metadata
```bash
python -m json.tool submission.csv.metadata.json
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "retrieval file not found" | Path typo or file missing | Use absolute path or run from repo root |
| "Expected exactly 100 records" | Top-K returned fewer than 100 | Check retrieval + ranking files have ≥100 entries |
| "scores must be non-increasing" | Sorting logic failed | Verify secondary signal computation in topk.py |
| "candidate_ids not in candidates.jsonl" | Mismatch between datasets | Ensure all retrieval candidates are in candidates.jsonl |
| Empty reasoning | Profile extraction failed | Check candidate_schema.json structure |

## For Challenge Participants

### What We Optimize For
1. **Determinism**: Every ranking is reproducible
2. **Efficiency**: Fits 200k candidates in 5 minutes on CPU
3. **Truthfulness**: Reasoning never hallucinated; judges can verify every claim
4. **Rank consistency**: Reasoning tone matches the rank (confident for rank 1–10, honest about gaps for rank 90–100)

### What We Avoid
1. **External APIs**: No OpenAI, Anthropic, or hosted LLM calls
2. **GPU**: CPU-only, works in sandboxed Docker
3. **Randomness**: Identical inputs always produce identical outputs
4. **Templated reasoning**: Each reasoning is tailored to the candidate's actual profile

## Repository Structure

```
REDROB_PERSON3/
├── rank.py                       # CLI entry point
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── candidate_schema.json         # Schema of candidates.jsonl
├── validate_submission.py        # Standalone submission validator
├── common/
│   ├── schemas.py               # CandidateRecord dataclass
│   └── constants.py             # Constants (log format, top-K)
├── orchestrator/
│   ├── pipeline.py              # Main orchestrator
│   ├── loader.py                # JSON loading
│   ├── merger.py                # Record merging
│   └── topk.py                  # Streaming top-K selector
├── reasoning/
│   ├── generator.py             # Reasoning generation (core differentiator)
│   ├── fact_extractor.py        # Profile fact extraction
│   └── templates.py             # (deprecated; generator is self-contained)
├── export/
│   ├── csv_writer.py            # CSV serialization + validation
│   └── validator.py             # Strict schema/existence checks
├── evaluation/
│   ├── ndcg.py                  # NDCG@K computation
│   └── metrics.py               # Metrics aggregation
├── demo/
│   └── app.py                   # Streamlit UI
├── tools/
│   ├── profile_index.py         # Candidate profile loader
│   └── run_quick_checks.py      # Unit test runner
└── tests/
    ├── test_topk.py
    ├── test_ndcg.py
    ├── test_reasoning.py
    ├── test_validator.py
    └── test_merge.py
```

## License & Disclaimer

Built for the Redrob Intelligent Candidate Discovery & Ranking Challenge. The system is designed to be production-ready and reproducible, meeting all challenge constraints.

---

**Questions or issues?** Check the test suite and debug JSON outputs for detailed traces.
