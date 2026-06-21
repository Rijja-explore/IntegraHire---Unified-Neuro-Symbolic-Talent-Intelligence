# IntegraHire--Unified-Neuro-Symbolic-Talent-Intelligence

IntegraHire is an AI-powered hiring intelligence platform that combines hybrid retrieval with neuro-symbolic evaluation to produce deterministic top-100 candidate rankings.

## Capabilities
- Semantic Retrieval (BM25 + FAISS + RRF)
- Authenticity Detection
- Career Trajectory Analysis
- Production Readiness Scoring
- Behavioral Intelligence
- Candidate DNA Profiling
- Recruiter-centric Ranking and Reasoning
- Deterministic CSV Export and Validation

## Repository Structure
- `rank.py`: CLI entrypoint for full pipeline or pre-scored mode
- `orchestrator/`: orchestration, merge, top-k, full pipeline
- `retrieval/`: preprocessing, embeddings, BM25, FAISS, fusion
- `ranking/`: authenticity/trajectory/behavior/production/dna/ranking engines
- `reasoning/`: deterministic reasoning generation
- `export/`: CSV writing and validation helpers
- `tests/`, `retrieval/tests/`, `ranking/tests/`: test suites
- `app.py`, `pages/`, `components/`, `utils/`: production Streamlit frontend

## Installation
```bash
pip install -r requirements.txt
```

## Run Ranking Pipeline
```bash
python rank.py \
  --candidates data/candidates.jsonl \
  --job_description data/job_description.txt \
  --output submission.csv
```

If your files are at repository root, use:
```bash
python rank.py \
  --candidates test_candidates.jsonl \
  --job_description job_description.txt \
  --output submission.csv
```

## Run Streamlit Frontend
```bash
streamlit run app.py
```

## Deliverables and Audits
- `PROJECT_AUDIT.md`: final completeness and compliance audit
- `DEPENDENCY_AUDIT.md`: dependency consolidation audit
- `MISSING_COMPONENTS.md`: remaining blocking/non-blocking items
- `submission_metadata.yaml`: metadata file for submission workflows

## Notes
- Runtime is designed for CPU-only execution.
- Ranking is deterministic and validated before final export.
- No hosted LLM or external API call is required for ranking execution.
