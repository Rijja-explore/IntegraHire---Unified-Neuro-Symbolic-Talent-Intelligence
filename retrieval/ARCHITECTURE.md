# ARCHITECTURE.md - Technical Design Document

## System Overview

The Retrieval & Semantic Intelligence Subsystem is a modular, production-grade hybrid retrieval engine designed for intelligent candidate ranking in hiring platforms.

## Design Principles

1. **Modularity**: Each component can be used independently
2. **Efficiency**: CPU-only, scales to 100k+ candidates
3. **Type Safety**: Full type hints throughout
4. **Observability**: Structured logging for monitoring
5. **Configurability**: Environment-driven design
6. **Testability**: Comprehensive test coverage

## Core Components

### 1. Configuration Layer (`config.py`)

**Responsibility**: Centralized configuration management

**Key Classes**:
- `EmbeddingConfig`: Embedding model and processing parameters
- `BM25Config`: BM25 algorithm parameters
- `FAISSConfig`: FAISS index configuration
- `RetrievalConfig`: Retrieval fusion parameters
- `SystemConfig`: Aggregates all sub-configs

**Pattern**: Singleton with environment-driven initialization

```python
config = get_config()  # Thread-safe singleton
config.embedding.model_name  # "BAAI/bge-small-en-v1.5"
config.retrieval.bm25_weight  # 0.4
```

### 2. Data Models (`schemas.py`)

**Responsibility**: Type-safe data models with validation

**Key Classes**:
- `CandidateRawData`: Raw input from JSONL
- `CandidateRecord`: Processed candidate with profile text
- `RetrievalRequest`: Retrieval API input
- `RetrievalResponse`: Retrieval API output
- `RetrievalResult`: Individual candidate result
- `JobDescription`: Processed job description

**Pattern**: Pydantic models with validation and serialization

### 3. Utilities (`utils.py`)

**Responsibility**: Text processing and helper functions

**Key Functions**:
- `normalize_text()`: Text cleaning and normalization
- `tokenize_text()`: Word tokenization with stopword removal
- `extract_keywords()`: Frequency-based keyword extraction
- `cosine_similarity()`: Vector similarity calculation
- `setup_logging()`: Structured logging configuration

**Pattern**: Functional utilities with no state

### 4. Preprocessing (`preprocessing.py`)

**Responsibility**: Transform raw candidate data into retrieval text

**Key Class**: `CandidatePreprocessor`

**Process**:
1. Extract profile information
2. Aggregate career history
3. Include education details
4. Combine skills and expertise
5. Normalize and format

**Output**: Rich, semantically meaningful text for retrieval

```
CURRENT POSITION
Current Role: Senior ML Engineer
Current Company: Tech Corp
...

WORK EXPERIENCE
Senior ML Engineer at Tech Corp
  (2022-01-01 - Present) [24 months]
  Technology | 501-1000
  Led development of vector search platform...

EDUCATION
M.S. in Computer Science
  State University
  (2017 - 2019)

SKILLS & EXPERTISE
Advanced: Python, NLP, FAISS, Machine Learning
```

### 5. Embedding Pipeline (`embeddings.py`)

**Responsibility**: Generate dense vector representations

**Key Classes**:
- `EmbeddingGenerator`: Model wrapper with batch processing
- `EmbeddingCache`: Optional caching layer

**Features**:
- Lazy model loading
- Batch processing for efficiency
- Normalization for cosine similarity
- Disk persistence
- Caching to avoid recomputation

**Model**: `BAAI/bge-small-en-v1.5` (384-dimensional)

**Performance**:
- ~50 texts/sec on CPU
- Batch processing: 32-64 texts per batch
- Caching: 100x speedup on cached texts

### 6. BM25 Index (`bm25_index.py`)

**Responsibility**: Fast lexical retrieval

**Key Class**: `BM25Index`

**Algorithm**: BM25 (Best Matching 25)
- Probabilistic ranking function
- Parameter tuning: k1 (term frequency saturation), b (field length normalization)

**Features**:
- Tokenization with stopword removal
- Configurable parameters
- Top-k retrieval
- Rank metadata

**Complexity**: O(n) for retrieval, O(1) for query

### 7. FAISS Index (`faiss_index.py`)

**Responsibility**: Fast similarity search on embeddings

**Key Class**: `FAISSIndex`

**Index Types**:
- `flat`: Brute-force (good for <100k vectors)
- `ivf`: Inverted File (good for >100k vectors)

**Similarity Metric**: Cosine (via normalized inner product)

**Features**:
- Efficient top-k search
- Multi-type index support
- CPU-only operation
- Disk persistence

**Complexity**: O(k) for flat, O(n/nlist * k) for IVF

### 8. Fusion Layer (`fusion.py`)

**Responsibility**: Combine multiple rankings using RRF

**Key Class**: `ReciprocalRankFusion`

**Algorithm**: Reciprocal Rank Fusion (RRF)

Formula: `RRF(d) = Σ weights[i] * 1/(k + rank_i(d))`

**Features**:
- Weighted fusion of BM25 and embedding rankings
- Configurable k parameter (impact of rank position)
- Score normalization

**Insight**: RRF effectively combines signals from different modalities

### 9. Job Processor (`job_processor.py`)

**Responsibility**: Process job descriptions for retrieval

**Key Class**: `JobDescriptionProcessor`

**Extracts**:
- Clean text
- Key responsibilities (bullet points)
- Required skills
- Nice-to-have skills
- Keywords
- Embedding vector

**Features**:
- Section identification
- Skill matching
- Keyword extraction

### 10. Retrieval Engine (`retrieval_engine.py`)

**Responsibility**: Main orchestration point

**Key Class**: `RetrievalEngine`

**Pipeline**:
```
build_indexes(candidates.jsonl)
  ├─ Load raw candidates
  ├─ Preprocess profiles
  ├─ Generate embeddings
  ├─ Build BM25 index
  ├─ Build FAISS index
  └─ Save to disk

retrieve_candidates(job_description)
  ├─ Process job description
  ├─ Generate JD embedding
  ├─ BM25 retrieval (top-k*2)
  ├─ FAISS retrieval (top-k*2)
  ├─ RRF fusion
  ├─ Filter & rank
  └─ Return results
```

**State Management**:
- Candidates in memory (searchable)
- Embeddings in NumPy array
- BM25 index (rebuilds from candidates)
- FAISS index (persistent)

## Data Flow

### Indexing Phase

```
candidates.jsonl (raw data)
    ↓
CandidatePreprocessor
    ├─ Parse JSON schema
    ├─ Validate candidate data
    ├─ Extract and normalize fields
    └─ Generate profile text
    ↓
CandidateRecord[] (enriched candidates)
    ├─ Store in memory
    └─ Extract profile_text
    ↓
EmbeddingGenerator
    ├─ Tokenize and batch
    ├─ Load model (once)
    ├─ Generate embeddings
    └─ Normalize for cosine similarity
    ↓
Embeddings (NumPy array, float32)
    ├─ Persist to disk
    ├─ Load into FAISS
    └─ Also used by BM25
    ↓
BM25Index
    ├─ Tokenize profile texts
    ├─ Build BM25 ranking function
    └─ Ready for keyword queries
    ↓
FAISSIndex
    ├─ Add normalized embeddings
    ├─ Train (if IVF)
    └─ Ready for similarity search
    ↓
Indexes Persisted
```

### Retrieval Phase

```
Job Description (text)
    ↓
JobDescriptionProcessor
    ├─ Clean and normalize
    ├─ Extract keywords
    ├─ Identify skills
    └─ Generate embedding
    ↓
JD Query (text + embedding)
    ├─ To BM25Index ────────┐
    │   ├─ Tokenize       │
    │   ├─ Score candidates
    │   └─ Top-k results
    │                      ├─ ReciprocalRankFusion
    │                      │  ├─ Combine rankings
    └─ To FAISSIndex ──────┤  ├─ Apply weights
        ├─ Normalize      │  ├─ Calculate RRF scores
        ├─ Search         │  └─ Rank candidates
        └─ Top-k results  │
                          ↓
                     Fused Results
                          ↓
                    Filter & Rank
                          ↓
                   RetrievalResponse
                     (top-k candidates)
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Preprocessing | O(n * m) | n=candidates, m=avg profile length |
| Embedding Gen. | O(n * m) | Batch processing, cached |
| BM25 Build | O(n * m) | Tokenization, index building |
| FAISS Build | O(n * d) | n=vectors, d=dimension |
| BM25 Query | O(m) | m=query length (tokenized) |
| FAISS Query | O(log n) flat, O(n/nlist) IVF | Sub-linear with IVF |
| RRF Fusion | O(k) | k=number of results |

### Space Complexity

| Component | Space | Example (100k) |
|-----------|-------|----------------|
| Raw data | O(n) | ~2-5GB |
| Embeddings | O(n * d) | ~160MB (384-dim) |
| BM25 Index | O(n * v) | ~500MB-1GB |
| FAISS Index | O(n * d) | ~160MB (flat) |
| **Total** | | ~2.5-3GB |

## Design Patterns

### 1. Singleton Pattern
Configuration is a singleton to ensure consistency:
```python
config = get_config()  # Always returns same instance
```

### 2. Factory Pattern
Engine creates components on demand:
```python
preprocessor = CandidatePreprocessor()
embedder = EmbeddingGenerator()
```

### 3. Strategy Pattern
RRF fusion uses configurable strategies:
```python
fusion = ReciprocalRankFusion(k=60)
results = fusion.fuse_rankings(bm25_results, embedding_results)
```

### 4. Decorator Pattern
Logging wraps all operations:
```python
@log_operation
def build_indexes(...):
    ...
```

## Error Handling

1. **Validation**: Pydantic models validate all inputs
2. **Graceful Degradation**: Missing data handled with defaults
3. **Logging**: All errors logged with context
4. **Type Safety**: Type hints catch errors early

## Scalability Considerations

### For 100k+ Candidates

1. **Memory**: Use sparse embeddings or IVF indexing
2. **CPU**: Parallel batch processing with threading
3. **I/O**: Stream processing for very large files
4. **Latency**: FAISS IVF for sub-linear search

### Optimization Strategies

1. **Batch Size**: Tune embedding batch size
2. **Index Type**: Use IVF for 1M+ candidates
3. **Quantization**: Use int8 embeddings if needed
4. **Caching**: Cache embeddings and results
5. **Parallel**: Multi-threaded preprocessing

## Security Considerations

1. **Input Validation**: All inputs validated with Pydantic
2. **Resource Limits**: Batch sizes prevent memory overload
3. **Path Safety**: All paths validated before use
4. **No External APIs**: No external service dependencies

## Testing Strategy

1. **Unit Tests**: Component-level testing
2. **Integration Tests**: Pipeline testing
3. **Performance Tests**: Latency benchmarks
4. **Regression Tests**: Consistency checks

---

**Document Version**: 1.0  
**Last Updated**: 2024-06-12
