# MISSING_COMPONENTS.md

## P0 (blocking)
1. Canonical single clean architecture under `project/src/` matching the blueprint.
2. Remove duplicate root-level packages or rewire everything to only `src/`.
3. Single canonical schema usage across all modules.
4. End-to-end runtime pipeline from:
   - `job_description.txt`
   - `candidates.jsonl`
   to:
   - ranked deterministic CSV (exactly 100 rows)
5. Dependency correctness: `requirements.txt` must include all runtime dependencies.
6. Hackathon compliance: deterministic ranking + strict validator must be executed before export.

## P1
- Docker-based end-to-end validation.
- Performance profiling to ensure <5 minutes and <16GB.

## P2
- Provide `submission_metadata.yaml` (not just a template) if required by judge.

