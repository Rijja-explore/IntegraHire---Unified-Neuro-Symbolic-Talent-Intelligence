# DEPENDENCY_AUDIT.md

Audit date: 2026-06-21 (final)

## Scope
- Consolidate repository to a single `requirements.txt`.
- Remove duplicate dependency manifests.
- Flag heavy packages and check if removable.

## Findings

### 1) Unused packages
Status: **PARTIAL**

Assessment:
- `python-docx`, `pypdf`, `plotly`, `streamlit` are used by the Streamlit frontend only.
- All other packages are used by retrieval, ranking, or tests.
- No unused core pipeline packages identified.

### 2) Duplicate packages
Status: **PASS**

Actions taken:
- Removed nested `retrieval/requirements.txt`.
- Single root `requirements.txt` is the only dependency manifest.

### 3) Conflicting versions
Status: **PASS**

- One authoritative requirements file.
- `pip install -r requirements.txt` succeeded in audit environment.

### 4) Heavy packages that can be removed
Status: **PARTIAL**

Heavy packages:
- `torch`, `transformers`, `sentence-transformers`, `faiss-cpu`

Assessment: Required for declared hybrid retrieval architecture. Do not remove without redesign.

## Final `requirements.txt`

Status: **PASS** — single file at repository root.

```
pydantic>=2.5,<3.0
numpy>=1.26,<2.0
pandas>=2.0,<3.0
sentence-transformers>=3.0,<4.0
torch>=2.6,<3.0
transformers>=4.41,<5.0
rank-bm25>=0.2,<1.0
faiss-cpu>=1.9,<2.0
tqdm>=4.65,<5.0
python-dotenv>=1.0,<2.0
scikit-learn>=1.3,<2.0
streamlit>=1.28,<2.0
plotly>=5.0,<6.0
python-docx>=1.1,<2.0
pypdf>=4.0,<6.0
pytest>=7.0,<9.0
```

## Verification

- `pip install -r requirements.txt` — PASS
- `pytest tests/ retrieval/tests/ ranking/tests/` — 68 passed
- Full pipeline — PASS (10.79s)
