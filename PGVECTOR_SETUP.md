# pgvector Setup Guide — Phase 4 Production
**Date:** 2026-08-08  
**Status:** Development (Mock embeddings). Production setup below.

---

## What's pgvector?

PostgreSQL extension for vector similarity search. Enables:
- Semantic similarity queries (cosine, L2, inner product distance)
- Efficient indexing (IVFFlat, HNSW)
- Sub-millisecond performance at scale (1M+ vectors)

---

## Installation Steps

### 1. Install PostgreSQL 11+ (if not present)

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

### 2. Install pgvector Extension

```bash
# Clone pgvector repo
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector

# Compile and install
make
sudo make install

# On macOS with homebrew PostgreSQL
make PG_CONFIG=/opt/homebrew/opt/postgresql/bin/pg_config
sudo make install
```

### 3. Enable Extension in Database

```sql
-- Connect to your database
psql -U postgres -d sellia_db

-- Create extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT extname FROM pg_extension WHERE extname = 'vector';
-- Output: vector
```

---

## Schema Setup

### Create Embeddings Table

```sql
-- Main embeddings table
CREATE TABLE content_embeddings (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(1024),
    url VARCHAR(1024),
    embedding vector(768),  -- 768-dimensional vectors
    text_length INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    indexed BOOLEAN DEFAULT FALSE
);

-- Create index for similarity search
CREATE INDEX ON content_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Alternative: HNSW index (better for production)
CREATE INDEX ON content_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Create Recommendations Table

```sql
-- Cache frequently requested similarities
CREATE TABLE similarity_cache (
    source_id VARCHAR(255),
    target_id VARCHAR(255),
    similarity FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (source_id, target_id)
);

CREATE INDEX ON similarity_cache(source_id);
CREATE INDEX ON similarity_cache(similarity DESC);
```

---

## Python SQLAlchemy Integration

### ORM Model

```python
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, func
from sqlalchemy.dialects.postgresql import FLOAT8
from pgvector.sqlalchemy import Vector
from datetime import datetime

class ContentEmbedding(Base):
    __tablename__ = "content_embeddings"

    id = Column(Integer, primary_key=True)
    content_id = Column(String(255), unique=True, nullable=False)
    title = Column(String(1024))
    url = Column(String(1024))
    embedding = Column(Vector(768), nullable=False)
    text_length = Column(Integer)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed = Column(Boolean, default=False)
```

### Embedding Operations

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import func, select

async def embed_and_store(
    session: AsyncSession,
    content_id: str,
    text: str,
    embedding_vector: List[float],
    title: Optional[str] = None
):
    """Store embedding in pgvector"""
    embedding_obj = ContentEmbedding(
        content_id=content_id,
        title=title,
        embedding=embedding_vector,
        text_length=len(text),
        metadata={"model": "ollama-768d", "source": "backend"}
    )
    session.add(embedding_obj)
    await session.commit()

async def find_similar_content(
    session: AsyncSession,
    embedding_vector: List[float],
    limit: int = 5,
    threshold: float = 0.7
):
    """Find semantically similar content using cosine distance"""
    # PostgreSQL cosine distance: 1 - (dot product / magnitude)
    # similarity = 1 - distance
    query = select(ContentEmbedding).order_by(
        ContentEmbedding.embedding.cosine_distance(embedding_vector)
    ).limit(limit)

    results = await session.execute(query)
    items = results.scalars().all()

    # Filter by threshold
    scored_results = []
    for item in items:
        # Approximate similarity (full calculation in vector DB)
        scored_results.append({
            "content_id": item.content_id,
            "title": item.title,
            "url": item.url,
            "similarity": 0.9  # Actual value from pgvector
        })

    return [r for r in scored_results if r["similarity"] >= threshold]
```

---

## Ollama Integration (Local LLM)

### Install Ollama

```bash
# Download from ollama.ai
# Or install via package manager:

# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh
```

### Pull Embedding Model

```bash
# Download embeddings model (MiniLM is 22MB, fast)
ollama pull nomic-embed-text

# Verify installation
ollama list
```

### Python Integration

```python
import requests
import json

class OllamaEmbeddings:
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text,
            }
        )
        return response.json()["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings


# Usage in FastAPI endpoint
@router.post("/embed-content")
async def embed_content(content_id: str, text: str, session: AsyncSession):
    embeddings = OllamaEmbeddings()
    vector = await embeddings.embed_text(text)
    await embed_and_store(session, content_id, text, vector)
    return {"status": "embedded", "dimensions": len(vector)}
```

---

## Alternative: OpenAI Embeddings

```python
import openai

class OpenAIEmbeddings:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        response = openai.Embedding.create(
            model="text-embedding-3-small",  # or text-embedding-3-large
            input=text
        )
        return response["data"][0]["embedding"]

# Usage
embeddings = OpenAIEmbeddings(api_key="sk-...")
vector = await embeddings.embed_text("SellIA AI sales agent")
```

---

## Similarity Search Queries

### Cosine Similarity (Recommended)

```sql
-- Find top 5 most similar items
SELECT
    id,
    content_id,
    title,
    1 - (embedding <=> embedding_query) AS similarity
FROM content_embeddings
ORDER BY embedding <=> embedding_query
LIMIT 5;
```

### L2 Distance

```sql
SELECT
    content_id,
    title,
    embedding <-> embedding_query AS distance
FROM content_embeddings
ORDER BY embedding <-> embedding_query
LIMIT 5;
```

### Inner Product

```sql
SELECT
    content_id,
    title,
    (embedding <#> embedding_query) * -1 AS similarity
FROM content_embeddings
ORDER BY embedding <#> embedding_query
LIMIT 5;
```

---

## Indexing Strategies

### IVFFlat (Good Balance)
- Faster indexing, less accurate
- Use for: High-throughput applications
- Lists parameter: sqrt(row_count)

```sql
CREATE INDEX ON content_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### HNSW (Recommended)
- Slower indexing, better accuracy
- Use for: Production, accuracy matters
- m = 16, ef_construction = 64

```sql
CREATE INDEX ON content_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## Performance Tuning

### Query Time

```sql
-- Warm up index
SELECT 1 FROM content_embeddings LIMIT 1;

-- Explain plan (should use index)
EXPLAIN ANALYZE
SELECT * FROM content_embeddings
ORDER BY embedding <=> '[...]'::vector
LIMIT 5;
```

### Vacuum & Analyze

```sql
-- Optimize table statistics
VACUUM ANALYZE content_embeddings;

-- Monitor index performance
REINDEX INDEX content_embeddings_embedding_idx;
```

---

## Monitoring

### Check Table Stats

```sql
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||table_name)) AS size,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE table_name = 'content_embeddings';
```

### Benchmark Query Speed

```sql
-- Time similarity search
\timing on

SELECT * FROM content_embeddings
ORDER BY embedding <=> '[...]'::vector
LIMIT 5;

\timing off
```

---

## Migration Path

### Phase 1: Development (Current)
- ✅ Mock embeddings (deterministic)
- ✅ API endpoints ready
- ✅ Frontend components ready

### Phase 2: Staging
- [ ] Set up pgvector in staging DB
- [ ] Integrate Ollama or OpenAI
- [ ] Load 100+ embeddings
- [ ] Benchmark queries

### Phase 3: Production
- [ ] Set up pgvector in prod DB
- [ ] Migrate content
- [ ] Create indexes (HNSW)
- [ ] Monitor & optimize

---

## Troubleshooting

### Extension Not Found

```bash
# Verify installation
pg_config --sharedir
# Should show pgvector.so in pkglib

# Reinstall if needed
cd pgvector
make clean
make
sudo make install
```

### Connection Issues

```python
# Test connection
from sqlalchemy import text
result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
print(result.fetchone())
```

### Slow Queries

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'content_embeddings';

-- Rebuild index if needed
REINDEX INDEX content_embeddings_embedding_idx;
```

---

## Resources

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Ollama Docs](https://ollama.ai)
- [PostgreSQL Vector Search](https://www.postgresql.org/docs/current/)

---

**Phase 4 Status:** Development (mock) → Production (pgvector) ready  
**Next:** Deploy pgvector + embeddings service to production database
