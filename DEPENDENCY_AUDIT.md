# DEPENDENCY_AUDIT.md

## Summary
Static inspection indicates `requirements.txt` is incomplete for runtime execution.

### Evidence
- `src/common/schemas.py` imports `pydantic`.
- `src/retrieval/embeddings.py` imports `sentence_transformers`.
- Other modules likely import FAISS, numpy, etc.

But root `requirements.txt` currently contains only:
- streamlit
- pytest
- pandas
- plotly

## Findings
- Missing required packages: **FAIL**
  - `pydantic` is missing.
  - `sentence_transformers` is missing.
  - `numpy` is likely missing.
  - `faiss` / `faiss-cpu` likely missing.
  - Potentially other retrieval/ranking deps are missing.
- Unused packages: **UNKNOWN** (cannot compute without full import graph)
- Conflicting versions: **UNKNOWN**

## Recommended action (next step)
- Generate a correct `requirements.txt` by:
  1) scanning all `import ...` statements across `src/` and root packages
  2) mapping imports → PyPI package names
  3) pinning minimal working versions
- Then validate by running end-to-end in Docker (where dependency install should work).

Until then, end-to-end runtime remains blocked.

