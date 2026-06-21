# API Documentation

## Main API: RetrievalEngine

The `RetrievalEngine` is the primary interface for all retrieval operations.

### Initialization

```python
from retrieval import RetrievalEngine
from pathlib import Path

engine = RetrievalEngine(index_dir=Path("./retrieval_indices"))
```

**Parameters**:
- `index_dir` (Path, optional): Directory to store/load indexes. Default: `./retrieval_indices`

---

## Index Building

### `build_indexes(candidates_jsonl_path: Path) -> dict`

Build all indexes from a candidates JSONL file. This is the initialization step.

**Parameters**:
- `candidates_jsonl_path` (Path): Path to candidates.jsonl file

**Returns**: Dictionary with build statistics
```python
{
    "total_candidates": 50000,
    "embeddings_shape": (50000, 384),
    "bm25_index_info": {...},
    "faiss_index_info": {...},
    "build_time_seconds": 123.45
}
```

**Example**:
```python
stats = engine.build_indexes(Path("candidates.jsonl"))
print(f"Built indexes for {stats['total_candidates']} candidates")
```

**Time Complexity**: O(n * m) where n=candidates, m=avg text length

**Note**: This operation takes 1-2 minutes for 100k candidates

---

### `load_indexes(candidates_jsonl_path: Path) -> None`

Load previously built indexes from disk.

**Parameters**:
- `candidates_jsonl_path` (Path): Path to candidates JSONL (for reference)

**Example**:
```python
engine.load_indexes(Path("candidates.jsonl"))
```

---

## Retrieval

### `retrieve_candidates(request: RetrievalRequest) -> RetrievalResponse`

Retrieve candidates for a job using a detailed request object.

**Parameters**:
- `request` (RetrievalRequest): Detailed request object

**Returns**: RetrievalResponse with ranked candidates

**RetrievalRequest Fields**:
```python
class RetrievalRequest(BaseModel):
    job_description: str           # Job description text
    job_description_embedding: Optional[List[float]] = None
    top_k: int = 100              # Number of results
    min_score: float = 0.0        # Minimum score threshold
    metadata: Dict[str, Any] = {}
```

**RetrievalResponse Fields**:
```python
class RetrievalResponse(BaseModel):
    job_description: str
    candidates: List[RetrievalResult]
    total_candidates_searched: int
    retrieval_latency_ms: float
    metadata: Dict[str, Any]
```

**RetrievalResult Fields**:
```python
class RetrievalResult(BaseModel):
    candidate_id: str              # Candidate ID
    bm25_score: float             # BM25 lexical score (0-1)
    bm25_rank: int                # BM25 ranking position
    embedding_score: float        # Dense embedding similarity (0-1)
    embedding_rank: int           # Embedding ranking position
    semantic_score: float         # Final RRF-fused score (0-1)
    retrieval_rank: int           # Final ranking position
    metadata: Dict[str, Any]
```

**Example**:
```python
from retrieval import RetrievalRequest

request = RetrievalRequest(
    job_description="Senior ML Engineer with Python",
    top_k=500,
    min_score=0.0
)

response = engine.retrieve_candidates(request)
print(f"Retrieved {len(response.candidates)} candidates")
print(f"Latency: {response.retrieval_latency_ms:.0f}ms")
```

---

### `retrieve_by_text(job_description: str, top_k: int = 100, min_score: float = 0.0) -> RetrievalResponse`

Convenience method for quick retrieval with text input.

**Parameters**:
- `job_description` (str): Job description text
- `top_k` (int): Number of candidates to retrieve (default: 100)
- `min_score` (float): Minimum score threshold (default: 0.0)

**Returns**: RetrievalResponse

**Example**:
```python
response = engine.retrieve_by_text(
    "Machine Learning Engineer with Spark and SQL",
    top_k=1000
)

for candidate in response.candidates[:10]:
    print(f"{candidate.candidate_id}: {candidate.semantic_score:.4f}")
```

---

## Candidate Information

### `get_candidate_profile(candidate_id: str) -> Optional[dict]`

Get the full profile of a candidate.

**Parameters**:
- `candidate_id` (str): Candidate ID (e.g., "CAND_0000001")

**Returns**: Dictionary with profile information or None if not found

**Response Structure**:
```python
{
    "candidate_id": "CAND_0000001",
    "profile_text": "...",  # Preprocessed profile text
    "metadata": {           # Extracted metadata
        "years_of_experience": 5.0,
        "location": "NYC",
        "current_company": "Tech Corp",
        ...
    },
    "raw_data": {...}       # Original candidate data
}
```

**Example**:
```python
profile = engine.get_candidate_profile("CAND_0000001")
if profile:
    print(f"Experience: {profile['metadata']['years_of_experience']} years")
    print(f"Location: {profile['metadata']['location']}")
```

---

## System Information

### `get_system_info() -> dict`

Get information about the retrieval system configuration and state.

**Returns**: Dictionary with system information

**Structure**:
```python
{
    "config": {
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "bm25_k1": 1.5,
        "bm25_b": 0.75,
        "rrf_k": 60,
        "bm25_weight": 0.4,
        "embedding_weight": 0.6
    },
    "indexes": {
        "bm25": {
            "num_candidates": 50000,
            "k1": 1.5,
            "b": 0.75,
            "is_built": true
        },
        "faiss": {
            "num_candidates": 50000,
            "embedding_dim": 384,
            "index_type": "flat",
            "total_vectors": 50000
        }
    },
    "state": {
        "num_candidates": 50000,
        "embeddings_shape": [50000, 384]
    }
}
```

**Example**:
```python
info = engine.get_system_info()
print(f"Using model: {info['config']['embedding_model']}")
print(f"Indexed candidates: {info['state']['num_candidates']}")
```

---

## Component APIs

### EmbeddingGenerator

```python
from retrieval.embeddings import EmbeddingGenerator
import numpy as np

generator = EmbeddingGenerator()

# Generate embeddings for multiple texts
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = generator.generate_embeddings(texts)  # (3, 384)

# Generate embedding for single text
embedding = generator.generate_single_embedding("Text")  # (384,)

# Save embeddings
generator.save_embeddings(embeddings, Path("embeddings.npy"))

# Load embeddings
embeddings, metadata = generator.load_embeddings(Path("embeddings.npy"))

# Get model info
info = generator.get_model_info()
```

---

### BM25Index

```python
from retrieval.bm25_index import BM25Index
from retrieval.schemas import CandidateRecord

index = BM25Index()

# Build index
index.build_index(candidates)  # candidates: List[CandidateRecord]

# Retrieve candidates
results = index.retrieve("query text", top_k=100)
# Returns: List[(candidate_id, score)]

# Retrieve with rank metadata
results = index.retrieve_with_ranks("query text", top_k=100)
# Returns: List[{"candidate_id": ..., "score": ..., "rank": ...}]

# Get index info
info = index.get_index_info()
```

---

### FAISSIndex

```python
from retrieval.faiss_index import FAISSIndex
import numpy as np

index = FAISSIndex(embedding_dim=384)

# Add embeddings
embeddings = np.random.randn(1000, 384).astype(np.float32)
candidate_ids = ["CAND_0000001", ...]
index.add_embeddings(embeddings, candidate_ids)

# Search
query_embedding = np.random.randn(384).astype(np.float32)
results = index.search(query_embedding, top_k=100)
# Returns: List[(candidate_id, similarity)]

# Search with rank metadata
results = index.search_with_ranks(query_embedding, top_k=100)
# Returns: List[{"candidate_id": ..., "similarity": ..., "rank": ...}]

# Persist and load
index.save_index(Path("faiss_index"))
index.load_index(Path("faiss_index"))
```

---

### ReciprocalRankFusion

```python
from retrieval.fusion import ReciprocalRankFusion

rrf = ReciprocalRankFusion(k=60)

# Fuse two rankings
bm25_results = [("CAND_001", 0.9), ("CAND_002", 0.7)]
embedding_results = [("CAND_002", 0.95), ("CAND_001", 0.85)]

fused = rrf.fuse_rankings(bm25_results, embedding_results)
# Returns: List[("candidate_id", fused_score)]

# Fuse with detailed metadata
bm25_results = [
    {"candidate_id": "CAND_001", "score": 0.9, "rank": 1},
    ...
]
embedding_results = [
    {"candidate_id": "CAND_001", "similarity": 0.85, "rank": 1},
    ...
]

fused = rrf.fuse_with_metadata(bm25_results, embedding_results)
```

---

## Configuration API

```python
from retrieval.config import get_config, set_config, SystemConfig

# Get current config
config = get_config()

# Access sub-configs
config.embedding.model_name      # "BAAI/bge-small-en-v1.5"
config.embedding.batch_size      # 32
config.bm25.k1                  # 1.5
config.retrieval.bm25_weight    # 0.4

# Create custom config
custom_config = SystemConfig()
custom_config.retrieval.bm25_weight = 0.3
custom_config.retrieval.embedding_weight = 0.7
custom_config.validate()
set_config(custom_config)
```

---

## Utility Functions

```python
from retrieval.utils import (
    normalize_text,
    tokenize_text,
    extract_keywords,
    cosine_similarity,
    normalize_scores,
    load_jsonl,
    save_jsonl,
    batch_iterator,
    calculate_statistics,
    format_duration,
    get_logger,
    setup_logging
)

# Text processing
text = normalize_text("  Hello   WORLD  ")
tokens = tokenize_text(text, remove_stopwords=True)
keywords = extract_keywords(text, top_k=20)

# Vector operations
import numpy as np
vec1 = np.array([1, 0, 0])
vec2 = np.array([0.5, 0.5, 0])
similarity = cosine_similarity(vec1, vec2)

# Score normalization
scores = [1.0, 5.0, 10.0]
normalized = normalize_scores(scores)  # [0.0, 0.45, 1.0]

# File I/O
data = load_jsonl(Path("data.jsonl"))
save_jsonl(data, Path("output.jsonl"))

# Batching
for batch in batch_iterator(items, batch_size=32):
    process(batch)

# Statistics
stats = calculate_statistics([1, 2, 3, 4, 5])
# {"count": 5, "mean": 3.0, "median": 3.0, ...}

# Logging
logger = setup_logging("my_app")
logger.info("Message", extra={"field": "value"})
```

---

## Error Handling

All APIs use proper exception handling:

```python
try:
    response = engine.retrieve_by_text(job_description)
except ValueError as e:
    # Indexes not built
    print(f"Error: {e}")
except Exception as e:
    # Other errors
    print(f"Unexpected error: {e}")
```

---

## Performance Tips

1. **Batch Processing**: Process multiple queries in parallel
2. **Caching**: Reuse embeddings when possible
3. **Index Tuning**: Adjust k1, b for BM25; use IVF for large datasets
4. **Memory**: Pre-allocate buffers for batch operations
5. **Monitoring**: Log retrieval latencies for optimization

---

## Examples

See `retrieval/examples/` directory for complete examples:
- `demo.py`: Comprehensive end-to-end example
- `quickstart.py`: Quick start guide

---

**API Version**: 1.0  
**Last Updated**: 2024-06-12
