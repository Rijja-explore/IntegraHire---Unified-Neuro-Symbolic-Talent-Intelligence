# MISSING_COMPONENTS.md

Audit date: 2026-06-21 (final)

## Status: No Critical Missing Components

All previously identified blockers have been resolved.

| Item | Priority | Resolution |
|---|---|---|
| Duplicate architecture (`src/` vs root) | High | Resolved — `src/*` re-exports root modules; schemas consolidated under `src/common/schemas.py` |
| Missing intelligence unit tests | High | Resolved — `tests/test_authenticity.py`, `test_trajectory.py`, `test_behavior.py`, `test_production.py`, `test_dna.py` |
| Reproducibility command | High | Resolved — `data/candidates.jsonl` + normalizer; pipeline runs end-to-end |
| Performance benchmark | Medium | Resolved — `tools/benchmark_pipeline.py`, `benchmark_report.json` (10.79s) |
| Schema normalization for mock JSONL | Medium | Resolved — `src/common/normalizer.py` |

## Optional Future Enhancements (Non-Blocking)

| File / Area | Priority | Reason | Suggestion |
|---|---|---|---|
| `demo/app.py` | Low | Legacy demo UI separate from production Streamlit app | Remove or document as optional demo |
| Memory telemetry on Windows | Low | `resource` module unavailable on Windows | Add optional `psutil` for precise RSS reporting |
| Full-schema production dataset | Low | Current `data/candidates.jsonl` uses simplified mock format | Ship full-schema JSONL for competition parity |

## Definition of Done

No critical missing components remain. Project meets completion criteria (see `PROJECT_AUDIT.md`).
