# MongoDB Vector Search — Complete In-Depth Guide

> **Audience:** Anyone — from beginners to production engineers.
> **Goal:** Understand MongoDB Vector Search from zero to production-ready code.

---

## Table of Contents

1. [MongoDB Vector Search Overview](#1-mongodb-vector-search-overview)
2. [Automated Embedding Overview](#2-automated-embedding-overview)
   - 2.1 [Enable and Use Automated Embedding](#21-enable-and-use-automated-embedding)
   - 2.2 [Embeddings Storage](#22-embeddings-storage)
   - 2.3 [Available Models](#23-available-models)
   - 2.4 [Key Concepts](#24-key-concepts)
3. [How to Index Fields for Vector Search](#3-how-to-index-fields-for-vector-search)
   - 3.1 [Syntax](#31-syntax)
   - 3.2 [MongoDB Vector Search Index Fields](#32-mongodb-vector-search-index-fields)
   - 3.3 [Supported Clients](#33-supported-clients)
   - 3.4 [Create a MongoDB Vector Search Index](#34-create-a-mongodb-vector-search-index)
   - 3.5 [View, Edit & Delete a Vector Search Index](#35-view-edit--delete-a-vector-search-index)
4. [Run Vector Search Queries](#4-run-vector-search-queries)
5. [Vector Search Types](#5-vector-search-types)
   - 5.1 [ANN Search](#51-ann-search-approximate-nearest-neighbor)
   - 5.2 [ENN Search](#52-enn-search-exact-nearest-neighbor)
6. [Considerations](#6-considerations)
7. [Keywords Reference](#7-keywords-reference)
8. [Use Cases and Design Patterns](#8-use-cases-and-design-patterns)
9. [Hybrid Search](#9-hybrid-search)
10. [Combined Vector Search + Full Text Search](#10-combined-vector-search--full-text-search)
11. [Production-Ready Code (Class-Based, Modular)](#11-production-ready-code-class-based-modular)

---

## 1. MongoDB Vector Search Overview

### What Is It?

MongoDB Vector Search is a built-in capability of **MongoDB Atlas** (and MongoDB 7.0+ self-managed) that lets you store, index, and search **vector embeddings** directly inside your MongoDB collections — no separate vector database needed.

A **vector embedding** is a list of numbers (e.g., `[0.12, -0.45, 0.78, ...]`) that represents the *meaning* of text, images, audio, or any data. Two pieces of content with similar meaning have vectors that are *close* to each other in high-dimensional space.

### Why Does It Matter?

Traditional databases search by **exact keyword match** (`WHERE name = 'laptop'`). They fail when a user types "portable computer" hoping to find "laptop". Vector search finds results by **semantic similarity** — meaning, not just words.

### Importance

- Powers **AI-native applications**: chatbots, recommendation engines, semantic search, RAG pipelines.
- Eliminates the need for a separate vector store (Pinecone, Weaviate, etc.) alongside your operational database.
- Combines transactional data + vector data in a single system — simpler architecture, less cost.

### Real-World Example

> **E-Commerce:** A user searches "comfortable shoes for walking all day". A keyword search finds nothing because no product is named that. MongoDB Vector Search finds "ergonomic sneakers", "orthopedic walking shoes", and "cushioned loafers" — because their descriptions are semantically close.

### Use Cases

- Semantic search on documents, knowledge bases, or product catalogs
- RAG (Retrieval-Augmented Generation) pipelines for LLM applications
- Recommendation systems (find items similar to what the user liked)
- Duplicate/near-duplicate content detection
- Image similarity search
- Customer support — find the most relevant FAQ answers

### Best Practices

- Always normalize vectors to unit length before storing if using cosine similarity.
- Choose embedding model dimensions based on accuracy vs. cost trade-off.
- Use `numCandidates` thoughtfully (higher = more accurate, slower).
- Pre-filter data with `$match` before vector search to reduce the search space.
- Monitor index build status before running queries.

---

## 2. Automated Embedding Overview

### What Is It?

Normally, you must call an external embedding API yourself, get back a vector, and store it in MongoDB. **Automated Embedding** removes this step. MongoDB integrates with **Voyage AI** (an Anthropic company) so that MongoDB automatically generates and stores embeddings when you insert or update documents.

Think of it like: you insert plain text → MongoDB calls the embedding model → stores the vector → ready for search. All automatically.

### Why It Matters

- Zero glue code for embedding generation.
- Embeddings stay in sync — when you update a document, the embedding auto-updates.
- Reduces architectural complexity significantly in production.

---

### 2.1 Enable and Use Automated Embedding

**Steps (Atlas UI or Driver):**

1. Create an Atlas cluster (M10 or higher for Vector Search).
2. In your Vector Search index definition, specify the `embeddingGenerator` field.
3. Point it to a Voyage AI model and your source text field.
4. MongoDB calls Voyage AI at index-time and at query-time automatically.

**Python Driver Example:**

```python
# When inserting — just store the raw text; MongoDB handles embedding
collection.insert_one({
    "title": "Ergonomic office chair",
    "description": "Lumbar support, adjustable arms, breathable mesh"
})
# The embedding for 'description' is auto-generated and stored internally
```

**At Query Time:**
```python
# Pass plain text query — MongoDB embeds it automatically
results = collection.aggregate([
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "description_embedding",
            "queryVector": None,          # Not needed with auto-embedding
            "query": "comfortable work chair with back support",  # Plain text!
            "numCandidates": 100,
            "limit": 5
        }
    }
])
```

---

### 2.2 Embeddings Storage

- Embeddings are stored as a **BSON array of doubles** in the document itself, in a designated field (e.g., `plot_embedding`, `description_embedding`).
- With Automated Embedding, this field is **auto-populated and managed** by MongoDB.
- Embedding field values look like: `[0.034, -0.217, 0.891, ..., 0.002]` (hundreds to thousands of dimensions).
- Storage overhead: 1536-dimension float32 = ~6KB per document. Plan your storage budget accordingly.

---

### 2.3 Available Models

MongoDB Automated Embedding uses **Voyage AI** models:

| Model | Dimensions | Best For |
|-------|-----------|----------|
| `voyage-3-large` | 1024 | Highest accuracy, general purpose |
| `voyage-3` | 1024 | Balanced accuracy and cost |
| `voyage-3-lite` | 512 | Speed-optimized, lower cost |
| `voyage-code-3` | 1024 | Code search and retrieval |
| `voyage-finance-2` | 1024 | Financial documents |
| `voyage-law-2` | 1024 | Legal documents |
| `voyage-multilingual-2` | 1024 | Multi-language support |

> **Note:** Model availability may change. Always check [MongoDB Docs](https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/) for the latest list.

---

### 2.4 Key Concepts

| Concept | Simple Explanation |
|---------|-------------------|
| **Embedding** | A list of numbers that captures the "meaning" of your data |
| **Dimension** | How many numbers are in the vector (e.g., 1536) |
| **Distance Metric** | How we measure similarity (cosine, euclidean, dotProduct) |
| **Index** | A special data structure built on your vectors to enable fast search |
| **numCandidates** | How many vectors to scan before picking top results |
| **Similarity Score** | A number (0–1) showing how close two vectors are |

---

## 3. How to Index Fields for Vector Search

### What Is Indexing?

Before you can search vectors, MongoDB must build a **vector search index** — a specialized structure (using HNSW algorithm internally) that organizes vectors for fast similarity lookup. Without an index, vector search is not possible.

---

### 3.1 Syntax

**Index definition (JSON format):**

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "plot_embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    }
  ]
}
```

**With a pre-filter field:**

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "plot_embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "genre"
    }
  ]
}
```

---

### 3.2 MongoDB Vector Search Index Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Must be `"vector"` |
| `path` | Yes | The document field that holds the embedding array |
| `numDimensions` | Yes | Number of dimensions; must match your embedding model's output |
| `similarity` | Yes | `"cosine"`, `"euclidean"`, or `"dotProduct"` |
| `quantization` | No | `"scalar"` or `"binary"` — compresses index for lower memory/disk usage |

**Similarity functions:**

- **cosine** — measures angle between vectors; best for text (direction matters, magnitude doesn't)
- **euclidean** — measures straight-line distance; best for spatial data
- **dotProduct** — measures projection; fastest but requires unit-normalized vectors

---

### 3.3 Supported Clients

You can create and manage Vector Search indexes using:

- **MongoDB Atlas UI** — visual interface, easiest for beginners
- **MongoDB Atlas CLI** — command-line management
- **mongosh** — MongoDB shell
- **MongoDB Compass** — desktop GUI tool
- **Python Driver** (`pymongo`) — programmatic creation
- **Node.js Driver** (`mongodb`) — programmatic creation
- **Atlas Search API** — REST API

---

### 3.4 Create a MongoDB Vector Search Index

#### Index Limitations

- Requires **MongoDB Atlas M10+** cluster (or MongoDB 7.0+ self-managed with Atlas Vector Search).
- Maximum **2048 dimensions** per vector field.
- One vector search index per collection is the recommended pattern (multiple indexes are supported but increase storage costs).
- Indexed vectors must be arrays of **float32/float64** values.
- Index build is **asynchronous** — query only after status is `READY`.

#### Prerequisites

- Atlas cluster M10 or higher (or compatible self-managed deployment).
- Collection with a field containing vector arrays.
- Network access configured on Atlas.

#### Required Access

- You need `Project Data Access Admin` or higher role on Atlas.
- For driver-based index creation: the database user needs `createIndex` privilege on the target collection.

#### Procedure — Single Index (Python)

```python
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

client = MongoClient("mongodb+srv://<user>:<pass>@cluster.mongodb.net/")
db = client["sample_mflix"]
collection = db["movies"]

# Define the vector search index
search_index_model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "plot_embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            }
        ]
    },
    name="vector_index",
    type="vectorSearch"
)

# Create the index
result = collection.create_search_index(model=search_index_model)
print(f"Index created: {result}")

# Wait for index to be READY before querying
import time
while True:
    indexes = list(collection.list_search_indexes("vector_index"))
    if indexes and indexes[0].get("status") == "READY":
        print("Index is ready!")
        break
    time.sleep(5)
```

#### Procedure — Multi Index (Multiple Fields)

```python
# Index with both vector field and filter field
search_index_model = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "plot_embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            },
            {
                "type": "filter",
                "path": "year"        # Enables pre-filtering by year
            },
            {
                "type": "filter",
                "path": "genre"       # Enables pre-filtering by genre
            }
        ]
    },
    name="vector_index_with_filters",
    type="vectorSearch"
)
```

---

### 3.5 View, Edit & Delete a Vector Search Index

**View:**
```python
# List all vector search indexes on a collection
indexes = list(collection.list_search_indexes())
for idx in indexes:
    print(idx["name"], idx["status"])
```

**Edit (Update):**
```python
# Update an existing index (change numCandidates behavior or add filter fields)
new_definition = {
    "fields": [
        {
            "type": "vector",
            "path": "plot_embedding",
            "numDimensions": 1536,
            "similarity": "dotProduct"     # Changed similarity
        },
        {
            "type": "filter",
            "path": "genre"
        }
    ]
}
collection.update_search_index("vector_index", new_definition)
```

**Delete:**
```python
collection.drop_search_index("vector_index")
print("Index deleted successfully.")
```

---

## 4. Run Vector Search Queries

Vector search queries are run using the **aggregation pipeline** with the `$vectorSearch` stage.

### Basic Query Pattern

```python
def run_vector_search(collection, query_vector, limit=5, num_candidates=100):
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "plot_embedding",
                "queryVector": query_vector,   # Your embedded query
                "numCandidates": num_candidates,
                "limit": limit
            }
        },
        {
            "$project": {
                "title": 1,
                "plot": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    return list(collection.aggregate(pipeline))
```

### Query with Pre-Filter

```python
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index_with_filters",
            "path": "plot_embedding",
            "queryVector": query_vector,
            "numCandidates": 200,
            "limit": 10,
            "filter": {                      # Pre-filter: only search within 2000s movies
                "year": {"$gte": 2000}
            }
        }
    },
    {"$project": {"title": 1, "year": 1, "score": {"$meta": "vectorSearchScore"}}}
]
```

---

## 5. Vector Search Types

### 5.1 ANN Search (Approximate Nearest Neighbor)

**What:** Finds the *approximately* closest vectors to your query vector. It doesn't scan every vector — it uses the HNSW index to narrow down candidates quickly.

**Why use it:** Extremely fast (milliseconds) even on millions of vectors. The approximation is so accurate (>95% recall) that for most applications it's indistinguishable from exact results.

**When to use:** Production workloads, real-time search, large datasets (100K+ documents).

**How it works (simplified):**
1. Query vector arrives.
2. HNSW index narrows search to `numCandidates` most promising vectors.
3. These candidates are re-ranked by exact distance.
4. Top `limit` results returned.

```python
# ANN Search — default behavior when using $vectorSearch
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "plot_embedding",
            "queryVector": query_vector,
            "numCandidates": 150,    # Scan 150 candidates, return top 10
            "limit": 10
            # No "exact": true — this is ANN (default)
        }
    }
]
```

**Best Practice:** Set `numCandidates` to 10–20x your `limit`. More candidates = better recall, more latency. Start at 10x and tune.

---

### 5.2 ENN Search (Exact Nearest Neighbor)

**What:** Finds the *exactly* closest vectors by computing distance to every vector in the collection (or filtered subset). Also called **KNN (K-Nearest Neighbor)** or brute-force search.

**Why use it:** 100% accuracy / perfect recall. Useful when correctness is critical or when your dataset is small.

**When to use:** Small collections (<10K documents), offline evaluation, correctness benchmarking, cases where no index exists.

**Trade-off:** Significantly slower than ANN on large datasets. O(N) complexity.

```python
# ENN Search — use "exact": true
pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "plot_embedding",
            "queryVector": query_vector,
            "numCandidates": 1000,
            "limit": 10,
            "exact": True              # Forces exact (brute-force) search
        }
    }
]
```

| | ANN | ENN |
|--|-----|-----|
| Speed | Very Fast | Slow on large data |
| Accuracy | ~95-99% | 100% |
| Index Required | Yes | No |
| Use Case | Production | Small datasets, evaluation |

---

## 6. Considerations

### 6.1 Limitations

- **Atlas M10+ required** for vector search indexes.
- **Max 2048 dimensions** per vector field.
- Vector fields must contain arrays of numbers — no null values, no mixed types.
- A single `$vectorSearch` stage must be the **first stage** in the aggregation pipeline.
- Cannot use `$vectorSearch` inside `$lookup`, `$facet`, or `$unionWith`.
- Atlas Search and Vector Search indexes are separate — you need both for hybrid search.
- Vectors stored as `float64` in BSON — be aware of storage costs at scale.

### 6.2 MongoDB Vector Search Indexing

- Index type: **HNSW (Hierarchical Navigable Small World)** — a graph-based ANN algorithm.
- Index build is asynchronous. New documents are indexed with a small lag.
- **Quantization** options reduce memory footprint:
  - `"scalar"` — reduces from float32 to int8. ~4x memory savings, slight accuracy loss.
  - `"binary"` — reduces to 1 bit per dimension. ~32x memory savings, larger accuracy loss.
- Use quantization when you have millions of vectors and memory is a concern.

### 6.3 MongoDB Vector Search Scoring

- The **vectorSearchScore** is a similarity value between 0 and 1.
- For **cosine** similarity: `score = (1 + cosine_similarity) / 2` — normalized to [0, 1].
- For **dotProduct**: `score = (1 + dot_product) / 2` (assumes unit vectors).
- For **euclidean**: `score = 1 / (1 + euclidean_distance)`.
- Access the score in your pipeline: `{"$meta": "vectorSearchScore"}`.
- Higher score = more similar.

### 6.4 MongoDB Vector Search Pre-Filtering

Pre-filtering lets you **restrict the vector search scope** to a subset of documents before the ANN algorithm runs.

**Why:** Searching 10,000 relevant documents is faster and more accurate than searching 10 million total documents.

**How:**
- Add `"type": "filter"` fields to your index definition.
- Use the `"filter"` parameter in `$vectorSearch`.
- Only indexed filter fields can be used — non-indexed filters are ignored.

```python
# Pre-filter: only search horror movies from the 1990s
"filter": {
    "$and": [
        {"genre": "horror"},
        {"year": {"$gte": 1990, "$lte": 1999}}
    ]
}
```

**Important:** Pre-filtering reduces the candidate pool. If you filter too aggressively and `numCandidates` is too low, you may get fewer results than `limit`. Increase `numCandidates` when applying narrow filters.

---

## 7. Keywords Reference

### `$vectorSearch`

The primary aggregation stage that triggers vector similarity search.

```python
{
    "$vectorSearch": {
        "index": "vector_index",          # Name of your vector search index
        "path": "plot_embedding",          # Field containing the vectors
        "queryVector": [0.1, -0.3, ...],   # Your query as a vector
        "numCandidates": 100,              # Candidate pool size for ANN
        "limit": 10,                       # Number of results to return
        "filter": {"year": {"$gte": 2000}},# Optional pre-filter
        "exact": False                     # True = ENN, False/omit = ANN
    }
}
```

**Key parameters:**
- `index` — Name of the vector search index to use (required)
- `path` — Field in the collection that stores the vector embeddings (required)
- `queryVector` — The embedded representation of your search query (required unless using auto-embedding)
- `numCandidates` — How many candidates the HNSW graph explores before ranking (required for ANN)
- `limit` — Final number of results returned (required)
- `filter` — Pre-filter expression (optional, must match indexed filter fields)
- `exact` — Boolean; `true` forces ENN/brute-force search (optional)

---

### `$search`

Used for **full-text search** (Atlas Search), not vector search. Part of the Lucene-based Atlas Search engine.

```python
{
    "$search": {
        "index": "default",
        "text": {
            "query": "laptop computer",
            "path": "description"
        }
    }
}
```

Used alongside `$vectorSearch` in hybrid search pipelines via `$rankFusion` or `$scoreFusion`.

---

### `$rankFusion`

Combines results from multiple search pipelines by **ranking** — without using raw scores. Uses **Reciprocal Rank Fusion (RRF)** internally.

```python
{
    "$rankFusion": {
        "input": {
            "pipelines": {
                "vector": [
                    {"$vectorSearch": { ... }},
                    {"$limit": 20}
                ],
                "fulltext": [
                    {"$search": { ... }},
                    {"$limit": 20}
                ]
            }
        }
    }
}
```

**Why use it:** Merges semantic + keyword results without needing to normalize their scores. More robust than score-based fusion. The `$rankFusion` stage is the recommended approach for hybrid search in MongoDB.

---

### `$scoreFusion`

Combines results from multiple pipelines by **blending their raw scores** using weighted arithmetic or geometric combination.

```python
{
    "$scoreFusion": {
        "input": {
            "pipelines": {
                "vector": [{"$vectorSearch": { ... }}, {"$limit": 20}],
                "fulltext": [{"$search": { ... }}, {"$limit": 20}]
            }
        },
        "combination": {
            "weights": {
                "vector": 0.7,
                "fulltext": 0.3
            }
        }
    }
}
```

**When to use:** When you want explicit weight control over how much semantic vs. keyword results contribute.

---

### `$limit`

Standard aggregation stage. Restricts the number of documents passed to the next stage.

```python
{"$limit": 10}   # Pass only top 10 documents forward
```

In vector search pipelines, always place `$limit` **after** `$vectorSearch` (or it's set inside `$vectorSearch` itself). Using `$limit` before `$vectorSearch` is not valid.

---

### `$match`

Standard aggregation filtering stage. Used **after** `$vectorSearch` for post-filtering results.

```python
# Post-filter: only return results with score above 0.8
{"$match": {"score": {"$gte": 0.8}}}
```

> **Note:** For performance, use `filter` inside `$vectorSearch` for pre-filtering. Use `$match` after for additional filtering that doesn't need to be indexed.

---

### `$sort`

Sorts documents in the pipeline. After `$vectorSearch`, results are already sorted by similarity score descending. You might re-sort for secondary ordering.

```python
# Sort by score descending, then by year descending
{"$sort": {"score": -1, "year": -1}}
```

---

### `$project`

Controls which fields appear in the output. Always use it to include `vectorSearchScore` and exclude large embedding arrays from the response.

```python
{
    "$project": {
        "_id": 0,
        "title": 1,
        "plot": 1,
        "year": 1,
        "score": {"$meta": "vectorSearchScore"},  # Expose similarity score
        "plot_embedding": 0                        # Exclude large vector field
    }
}
```

> **Best Practice:** Always exclude embedding fields from output — they're large arrays that bloat your response payload.

---

### `$geoNear`

Not specific to vector search, but can be **combined** with it. `$geoNear` performs geospatial proximity search.

```python
# Example: Find semantically similar items near a location
[
    {
        "$geoNear": {
            "near": {"type": "Point", "coordinates": [77.5946, 12.9716]},
            "distanceField": "dist",
            "maxDistance": 5000,
            "spherical": True
        }
    },
    {
        "$vectorSearch": { ... }   # Then semantic search within those results
    }
]
```

---

## 8. Use Cases and Design Patterns

### 8.1 Semantic Search

**What:** Find documents that are *meaningfully similar* to a query, regardless of exact word matches.

**Pattern:**
```
User Query → Embed Query → $vectorSearch → Return Top-K Results
```

**Real-World Example:** Legal tech platform — user searches "breach of contract in employment disputes". Semantic search returns relevant case summaries even if they use different legal terminology.

**Design Pattern:**
```
[User Input]
    ↓ embed via embedding model
[Query Vector]
    ↓ $vectorSearch (ANN)
[Top-K Candidate Documents]
    ↓ $project (title, content, score)
[Final Results]
```

---

### 8.2 Hybrid Search

**What:** Combines semantic (vector) search with keyword (full-text) search to get the best of both worlds. Use when you need both *meaning* and *exact term* matching.

**Real-World Example:** Medical records search — "insulin dosage for type 2 diabetes". Exact terms like "insulin" and "type 2" matter (keyword), but understanding context also matters (semantic).

---

### 8.3 How to Perform Semantic Search with MongoDB Vector Search (Full Example)

```python
import os
from pymongo import MongoClient
from openai import OpenAI

# Setup
mongo_client = MongoClient(os.environ["MONGODB_URI"])
db = mongo_client["sample_mflix"]
collection = db["movies"]

openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def get_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI text-embedding-3-small."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # 1536 dimensions
    )
    return response.data[0].embedding

def semantic_search(query: str, limit: int = 5) -> list[dict]:
    """Run semantic search on movies collection."""
    query_vector = get_embedding(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "plot_embedding",
                "queryVector": query_vector,
                "numCandidates": 150,
                "limit": limit
            }
        },
        {
            "$project": {
                "title": 1,
                "plot": 1,
                "year": 1,
                "score": {"$meta": "vectorSearchScore"},
                "plot_embedding": 0
            }
        }
    ]
    return list(collection.aggregate(pipeline))

# Usage
results = semantic_search("time travel adventure with a scientist")
for r in results:
    print(f"{r['title']} ({r['year']}) — Score: {r['score']:.4f}")
    print(f"  Plot: {r['plot'][:100]}...")
```

---

## 9. Hybrid Search

### 9.1 Hybrid Search Overview

Hybrid search combines two fundamentally different retrieval signals:

| Signal | Method | Strength |
|--------|--------|----------|
| **Semantic** | `$vectorSearch` (HNSW, cosine) | Understands meaning, handles paraphrasing |
| **Keyword** | `$search` (BM25, Lucene) | Exact term matching, proper nouns, codes |

**Why combine?** Neither alone is perfect. Semantic search may miss rare terms; keyword search misses paraphrases. Together, they cover each other's blind spots.

---

### 9.2 What is Reciprocal Rank Fusion (RRF)?

**The Problem:** Vector search gives similarity scores (0–1). Full-text search gives BM25 relevance scores (arbitrary range). You cannot directly add or compare them — they're on different scales.

**The Solution — RRF:** Instead of using raw scores, use *ranks* (position in the result list). Each document's RRF score is:

```
RRF_score(doc) = Σ  1 / (k + rank_in_pipeline_i)
```

Where:
- `k` = a smoothing constant (typically 60)
- `rank_in_pipeline_i` = the document's rank (1-indexed) in pipeline `i`

**Intuition with Example:**

| Movie | Vector Rank | Text Rank | RRF Score |
|-------|------------|-----------|-----------|
| Movie A | 1 | 3 | 1/(60+1) + 1/(60+3) = 0.0164 + 0.0156 = **0.0320** |
| Movie B | 2 | 1 | 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = **0.0325** |
| Movie C | 5 | 2 | 1/(60+5) + 1/(60+2) = 0.0154 + 0.0161 = **0.0315** |

Movie B wins because it appears near the top in BOTH result sets. A document that ranks #1 in one but doesn't appear at all in the other may lose to one that ranks moderately in both.

**Key properties:**
- Scale-invariant (no normalization needed)
- Rewards consistency across pipelines
- Penalizes documents absent from one pipeline
- Robust to outliers in individual scores

---

### 9.3 Hybrid Search Use Cases

| Use Case | Why Hybrid? |
|----------|-------------|
| **E-commerce product search** | Brand names need exact match; product descriptions need semantic |
| **Medical/legal search** | Specific codes/IDs need exact match; clinical context needs semantic |
| **Customer support** | Ticket IDs need exact; issue descriptions need semantic |
| **Code search** | Function names need exact; behavior descriptions need semantic |
| **News search** | Named entities need exact; topic understanding needs semantic |

---

### 9.4 Limitations of Hybrid Search

- Requires **two separate indexes** — a Vector Search index and an Atlas Search index.
- Higher query latency due to running two pipelines.
- `$rankFusion` and `$scoreFusion` are available only in certain Atlas tiers.
- Tuning weights in `$scoreFusion` requires experimentation per domain.
- ENN search inside hybrid pipelines is not recommended due to latency.

---

## 10. Combined Vector Search + Full Text Search

### 10.1 Create the Required Indexes

**Step 1: Vector Search Index (for semantic)**

```python
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

client = MongoClient(os.environ["MONGODB_URI"])
collection = client["sample_mflix"]["movies"]

# Vector Search Index
vector_index = SearchIndexModel(
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "plot_embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            },
            {"type": "filter", "path": "year"},
            {"type": "filter", "path": "genres"}
        ]
    },
    name="vector_index",
    type="vectorSearch"
)

# Atlas Search Index (for keyword / full-text)
text_index = SearchIndexModel(
    definition={
        "mappings": {
            "dynamic": False,
            "fields": {
                "title": {"type": "string"},
                "plot": {"type": "string"},
                "genres": {"type": "string"}
            }
        }
    },
    name="default",
    type="search"
)

collection.create_search_index(vector_index)
collection.create_search_index(text_index)
print("Both indexes created. Wait for READY status before querying.")
```

---

### 10.2 Run a Combined Query (Hybrid Search with $rankFusion)

```python
def hybrid_search(
    collection,
    query_text: str,
    query_vector: list[float],
    limit: int = 10,
    num_candidates: int = 150
) -> list[dict]:
    """
    Perform hybrid search combining vector similarity + full-text search
    using Reciprocal Rank Fusion via $rankFusion.
    """
    pipeline = [
        {
            "$rankFusion": {
                "input": {
                    "pipelines": {
                        "vector_pipeline": [
                            {
                                "$vectorSearch": {
                                    "index": "vector_index",
                                    "path": "plot_embedding",
                                    "queryVector": query_vector,
                                    "numCandidates": num_candidates,
                                    "limit": limit * 2   # Retrieve more for better fusion
                                }
                            }
                        ],
                        "text_pipeline": [
                            {
                                "$search": {
                                    "index": "default",
                                    "text": {
                                        "query": query_text,
                                        "path": ["title", "plot"]
                                    }
                                }
                            },
                            {"$limit": limit * 2}
                        ]
                    }
                },
                "rankConstant": 60    # RRF k parameter
            }
        },
        {"$limit": limit},
        {
            "$project": {
                "title": 1,
                "plot": 1,
                "year": 1,
                "score": {"$meta": "rankFusionScore"},
                "plot_embedding": 0
            }
        }
    ]
    return list(collection.aggregate(pipeline))

# Usage
query = "time traveler fixing historical mistakes"
query_vector = get_embedding(query)
results = hybrid_search(collection, query, query_vector)
for r in results:
    print(f"{r['title']} ({r['year']}) — Fusion Score: {r['score']:.6f}")
```

---

## 11. Production-Ready Code (Class-Based, Modular)

### 11.1 Data Loader

```python
# data_loader.py
import os
import json
from pathlib import Path
from pymongo import MongoClient
from typing import Any


class DataLoader:
    """
    Handles loading documents from various sources into MongoDB.
    Supports JSON files, JSONL files, and Python dicts.
    """

    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.client = MongoClient(mongo_uri)
        self.collection = self.client[db_name][collection_name]

    def load_from_json(self, file_path: str, batch_size: int = 500) -> int:
        """Load documents from a JSON or JSONL file."""
        path = Path(file_path)
        documents = []

        if path.suffix == ".jsonl":
            with open(path, "r") as f:
                documents = [json.loads(line) for line in f if line.strip()]
        elif path.suffix == ".json":
            with open(path, "r") as f:
                data = json.load(f)
                documents = data if isinstance(data, list) else [data]

        return self._bulk_insert(documents, batch_size)

    def load_from_dicts(self, documents: list[dict], batch_size: int = 500) -> int:
        """Load documents from a list of Python dicts."""
        return self._bulk_insert(documents, batch_size)

    def _bulk_insert(self, documents: list[dict], batch_size: int) -> int:
        """Insert documents in batches for efficiency."""
        total_inserted = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = self.collection.insert_many(batch, ordered=False)
            total_inserted += len(result.inserted_ids)
            print(f"Inserted batch {i // batch_size + 1}: {len(result.inserted_ids)} docs")
        print(f"Total inserted: {total_inserted}")
        return total_inserted

    def clear_collection(self):
        """Remove all documents from the collection."""
        result = self.collection.delete_many({})
        print(f"Cleared {result.deleted_count} documents.")

    def close(self):
        self.client.close()
```

---

### 11.2 Recursive Character Splitter (Custom)

```python
# text_splitter.py
from typing import Optional


class RecursiveCharacterSplitter:
    """
    Splits long text into overlapping chunks for embedding.

    Strategy: Try splitting by paragraph → sentence → word → character.
    Ensures no chunk exceeds max_chunk_size while maintaining semantic coherence.

    Args:
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Characters to overlap between consecutive chunks.
        separators: Ordered list of separators to try.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[list[str]] = None
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks using recursive separator strategy."""
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split using progressively finer separators."""
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        separator = self._pick_separator(text, separators)
        parts = text.split(separator)

        chunks = []
        current_chunk = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            test_chunk = f"{current_chunk}{separator}{part}".strip() if current_chunk else part

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Apply overlap: carry over the tail of current chunk
                    overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                    current_chunk = f"{overlap_text} {part}".strip() if overlap_text else part
                else:
                    # Part itself exceeds chunk_size — recurse with finer separator
                    next_separators = separators[separators.index(separator) + 1:] if separator in separators else [""]
                    sub_chunks = self._recursive_split(part, next_separators)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _pick_separator(self, text: str, separators: list[str]) -> str:
        """Pick the first separator that actually exists in the text."""
        for sep in separators:
            if sep and sep in text:
                return sep
        return separators[-1]  # Fallback to empty string (character split)

    def split_documents(self, documents: list[dict], text_field: str) -> list[dict]:
        """
        Split a list of documents by their text field.
        Returns new documents with chunk metadata.
        """
        result = []
        for doc in documents:
            text = doc.get(text_field, "")
            chunks = self.split_text(text)
            for idx, chunk in enumerate(chunks):
                chunk_doc = {**doc, text_field: chunk, "chunk_index": idx, "total_chunks": len(chunks)}
                chunk_doc.pop("_id", None)   # Remove _id to allow re-insertion
                result.append(chunk_doc)
        return result
```

---

### 11.3 Vector Store

```python
# vector_store.py
import os
import time
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from openai import OpenAI
from typing import Optional


class MongoDBVectorStore:
    """
    Production-ready MongoDB Vector Store.

    Handles:
    - Embedding generation (via OpenAI or any provider)
    - Vector index creation and management
    - Semantic search (ANN)
    - Hybrid search (ANN + Full-Text via $rankFusion)
    - Batch upsert of embeddings
    """

    def __init__(
        self,
        mongo_uri: str,
        db_name: str,
        collection_name: str,
        embedding_field: str = "embedding",
        vector_index_name: str = "vector_index",
        text_index_name: str = "default",
        num_dimensions: int = 1536,
        similarity: str = "cosine",
        openai_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.embedding_field = embedding_field
        self.vector_index_name = vector_index_name
        self.text_index_name = text_index_name
        self.num_dimensions = num_dimensions
        self.similarity = similarity
        self.embedding_model = embedding_model

        self.openai_client = OpenAI(api_key=openai_api_key or os.environ["OPENAI_API_KEY"])

    # ─── Embedding ────────────────────────────────────────────────

    def embed_text(self, text: str) -> list[float]:
        """Generate a single embedding."""
        response = self.openai_client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in one API call."""
        response = self.openai_client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        return [item.embedding for item in response.data]

    # ─── Index Management ─────────────────────────────────────────

    def create_vector_index(self, filter_fields: Optional[list[str]] = None, wait_for_ready: bool = True):
        """Create a vector search index, optionally with filter fields."""
        fields = [
            {
                "type": "vector",
                "path": self.embedding_field,
                "numDimensions": self.num_dimensions,
                "similarity": self.similarity
            }
        ]
        if filter_fields:
            for field in filter_fields:
                fields.append({"type": "filter", "path": field})

        index_model = SearchIndexModel(
            definition={"fields": fields},
            name=self.vector_index_name,
            type="vectorSearch"
        )
        self.collection.create_search_index(index_model)
        print(f"Vector search index '{self.vector_index_name}' creation initiated.")

        if wait_for_ready:
            self._wait_for_index_ready(self.vector_index_name)

    def create_text_index(self, text_fields: list[str], wait_for_ready: bool = True):
        """Create an Atlas Search (full-text) index."""
        field_mappings = {f: {"type": "string"} for f in text_fields}
        index_model = SearchIndexModel(
            definition={"mappings": {"dynamic": False, "fields": field_mappings}},
            name=self.text_index_name,
            type="search"
        )
        self.collection.create_search_index(index_model)
        print(f"Text search index '{self.text_index_name}' creation initiated.")

        if wait_for_ready:
            self._wait_for_index_ready(self.text_index_name)

    def _wait_for_index_ready(self, index_name: str, timeout_sec: int = 300):
        """Poll until the index status is READY."""
        start = time.time()
        while time.time() - start < timeout_sec:
            indexes = list(self.collection.list_search_indexes(index_name))
            if indexes and indexes[0].get("status") == "READY":
                print(f"Index '{index_name}' is READY.")
                return
            print(f"Waiting for index '{index_name}'... current status: {indexes[0].get('status') if indexes else 'not found'}")
            time.sleep(10)
        raise TimeoutError(f"Index '{index_name}' did not become READY within {timeout_sec}s.")

    def list_indexes(self) -> list[dict]:
        return list(self.collection.list_search_indexes())

    def delete_vector_index(self):
        self.collection.drop_search_index(self.vector_index_name)
        print(f"Index '{self.vector_index_name}' deleted.")

    # ─── Document Ingestion ───────────────────────────────────────

    def add_documents(
        self,
        documents: list[dict],
        text_field: str,
        batch_size: int = 100
    ) -> int:
        """
        Embed and insert documents into MongoDB.
        Adds the embedding vector to each document before insertion.
        """
        total = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc.get(text_field, "") for doc in batch]
            embeddings = self.embed_batch(texts)

            enriched = []
            for doc, emb in zip(batch, embeddings):
                doc_copy = {**doc, self.embedding_field: emb}
                doc_copy.pop("_id", None)
                enriched.append(doc_copy)

            result = self.collection.insert_many(enriched, ordered=False)
            total += len(result.inserted_ids)
            print(f"Batch {i // batch_size + 1}: inserted {len(result.inserted_ids)} docs")

        print(f"Total documents inserted with embeddings: {total}")
        return total

    # ─── Semantic Search ──────────────────────────────────────────

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        num_candidates: int = 150,
        filter_expr: Optional[dict] = None,
        project_fields: Optional[list[str]] = None
    ) -> list[dict]:
        """ANN semantic search using $vectorSearch."""
        query_vector = self.embed_text(query)

        vector_search_stage = {
            "$vectorSearch": {
                "index": self.vector_index_name,
                "path": self.embedding_field,
                "queryVector": query_vector,
                "numCandidates": num_candidates,
                "limit": limit
            }
        }
        if filter_expr:
            vector_search_stage["$vectorSearch"]["filter"] = filter_expr

        projection = {self.embedding_field: 0, "score": {"$meta": "vectorSearchScore"}}
        if project_fields:
            for f in project_fields:
                projection[f] = 1

        pipeline = [
            vector_search_stage,
            {"$project": projection}
        ]
        return list(self.collection.aggregate(pipeline))

    # ─── Hybrid Search ────────────────────────────────────────────

    def hybrid_search(
        self,
        query: str,
        text_search_fields: list[str],
        limit: int = 5,
        num_candidates: int = 150,
        rank_constant: int = 60,
        project_fields: Optional[list[str]] = None
    ) -> list[dict]:
        """Hybrid search combining $vectorSearch and $search via $rankFusion."""
        query_vector = self.embed_text(query)

        projection = {self.embedding_field: 0, "score": {"$meta": "rankFusionScore"}}
        if project_fields:
            for f in project_fields:
                projection[f] = 1

        pipeline = [
            {
                "$rankFusion": {
                    "input": {
                        "pipelines": {
                            "vector_pipeline": [
                                {
                                    "$vectorSearch": {
                                        "index": self.vector_index_name,
                                        "path": self.embedding_field,
                                        "queryVector": query_vector,
                                        "numCandidates": num_candidates,
                                        "limit": limit * 2
                                    }
                                }
                            ],
                            "text_pipeline": [
                                {
                                    "$search": {
                                        "index": self.text_index_name,
                                        "text": {
                                            "query": query,
                                            "path": text_search_fields
                                        }
                                    }
                                },
                                {"$limit": limit * 2}
                            ]
                        }
                    },
                    "rankConstant": rank_constant
                }
            },
            {"$limit": limit},
            {"$project": projection}
        ]
        return list(self.collection.aggregate(pipeline))

    def close(self):
        self.client.close()
```

---

### Usage Example — Full Pipeline

```python
# main.py
import os
from data_loader import DataLoader
from text_splitter import RecursiveCharacterSplitter
from vector_store import MongoDBVectorStore

MONGO_URI = os.environ["MONGODB_URI"]
DB = "my_knowledge_base"
COLLECTION = "documents"

# Step 1: Load raw documents
loader = DataLoader(MONGO_URI, DB, COLLECTION)
loader.load_from_json("data/knowledge_base.json")
loader.close()

# Step 2: Split long documents into chunks
from pymongo import MongoClient
client = MongoClient(MONGO_URI)
raw_docs = list(client[DB][COLLECTION].find({}, {"_id": 0}))

splitter = RecursiveCharacterSplitter(chunk_size=800, chunk_overlap=150)
chunked_docs = splitter.split_documents(raw_docs, text_field="content")
print(f"Split {len(raw_docs)} docs → {len(chunked_docs)} chunks")

# Step 3: Initialize VectorStore and create indexes
vs = MongoDBVectorStore(
    mongo_uri=MONGO_URI,
    db_name=DB,
    collection_name=f"{COLLECTION}_chunks",
    embedding_field="content_embedding",
    num_dimensions=1536,
    similarity="cosine"
)

# Create indexes (only needed once)
vs.create_vector_index(filter_fields=["source", "doc_type"])
vs.create_text_index(text_fields=["content", "title"])

# Step 4: Add documents with embeddings
vs.add_documents(chunked_docs, text_field="content", batch_size=50)

# Step 5: Semantic Search
print("\n--- Semantic Search ---")
results = vs.semantic_search(
    query="How do transformers handle long-range dependencies?",
    limit=3,
    num_candidates=100,
    project_fields=["title", "content", "source"]
)
for r in results:
    print(f"Score: {r['score']:.4f} | {r['title']}")
    print(f"  {r['content'][:150]}...\n")

# Step 6: Hybrid Search
print("\n--- Hybrid Search ---")
results = vs.hybrid_search(
    query="attention mechanism transformer architecture",
    text_search_fields=["content", "title"],
    limit=3,
    project_fields=["title", "content"]
)
for r in results:
    print(f"Fusion Score: {r['score']:.6f} | {r['title']}")

vs.close()
```

---

## Quick Reference Summary

| Topic | Key Points |
|-------|-----------|
| **Vector Search** | Similarity-based search using embeddings stored in MongoDB |
| **Embedding** | Array of floats representing semantic meaning of content |
| **Index** | HNSW-based; must be created before querying; async build |
| **ANN** | Approximate, fast, uses `numCandidates` for accuracy control |
| **ENN** | Exact/brute-force, use `"exact": true`, slow on large data |
| **Pre-filter** | Add `"filter"` in `$vectorSearch`; requires indexed filter fields |
| **Hybrid Search** | `$vectorSearch` + `$search` combined via `$rankFusion` |
| **RRF** | Rank-based score fusion; scale-invariant; k=60 is standard |
| **$rankFusion** | MongoDB operator for RRF-based hybrid search |
| **$scoreFusion** | Weighted score blending for hybrid search |
| **Quantization** | Scalar or binary compression; reduces index size |
| **Best Practice** | Exclude embedding fields from `$project`; monitor index status |

---

*References:*
- *https://www.mongodb.com/docs/vector-search/*
- *https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/*
- *https://www.mongodb.com/docs/vector-search/hybrid-search/hybrid-search/*
- *https://www.mongodb.com/docs/vector-search/hybrid-search/vector-search-with-full-text-search/*