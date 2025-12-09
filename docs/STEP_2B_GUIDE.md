# Step 2.b Complete Guide - Feature Vector Embeddings

## Overview

You've now implemented **Step 2.b - Embedding-based Retrieval** using **Feature Vector Embeddings** with TWO models for comparison!

---

## 📁 Files Created

### 1. `embeddings/feature_vector_builder.py`
**Purpose:** Build and store feature vector embeddings in Neo4j

**What it does:**
- Fetches Journey nodes from Neo4j
- Converts numerical properties to text descriptions
- Generates embeddings using two models:
  - `all-MiniLM-L6-v2` (384 dimensions, fast)
  - `all-mpnet-base-v2` (768 dimensions, better quality)
- Stores embeddings in Neo4j as node properties
- Creates vector indexes for fast similarity search

### 2. `embeddings/similarity_search.py`
**Purpose:** Perform semantic similarity search

**What it does:**
- Embeds user queries (Step 1.c - Input Embedding)
- Searches Neo4j vector index for similar journeys
- Returns top-K most similar results with scores
- Compares results from both models

### 3. `embeddings/__init__.py`
Module initialization file

---

## 🔄 How Feature Vector Embeddings Work

### Step-by-Step Process:

#### 1️⃣ **Convert Journey to Text**
```python
Journey properties:
{
    "feedback_ID": "123",
    "passenger_class": "business",
    "food_satisfaction_score": 3,
    "arrival_delay_minutes": 45,
    "actual_flown_miles": 1200,
    "number_of_legs": 2
}

↓ Converts to ↓

"Journey feedback_123: Business class passenger traveled 1200 miles
 on 2 legs with food satisfaction 3 out of 5 and arrival delay of 45 minutes"
```

#### 2️⃣ **Generate Embeddings**
```python
Text → Sentence Transformer Model → Embedding Vector

"Journey feedback_123: Business class..." → [0.123, -0.456, 0.789, ...]

Model 1 (MiniLM): 384-dimensional vector
Model 2 (MPNet): 768-dimensional vector
```

#### 3️⃣ **Store in Neo4j**
```cypher
MATCH (j:Journey {feedback_ID: "123"})
SET j.embedding_minilm = [0.123, -0.456, 0.789, ...]
SET j.embedding_mpnet = [0.234, -0.567, 0.890, ...]
```

#### 4️⃣ **Create Vector Index**
```cypher
CREATE VECTOR INDEX embedding_minilm
FOR (j:Journey) ON j.embedding_minilm
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }
}
```

#### 5️⃣ **Search by Similarity**
```python
User query: "Flights with long delays and poor food"
↓
Embed query → [0.111, -0.222, 0.333, ...]
↓
Find similar vectors in Neo4j using cosine similarity
↓
Return top journeys with high similarity scores
```

---

## 🚀 Usage Instructions

### Step 1: Install Dependencies

```bash
cd c:\Users\LOQ\Desktop\ACL-Milestone-3
venv\Scripts\python.exe -m pip install sentence-transformers torch
```

### Step 2: Build Embeddings (Run Once)

```bash
venv\Scripts\python.exe embeddings\feature_vector_builder.py
```

**This will:**
1. Fetch all Journey nodes from Neo4j
2. Convert each to a text description
3. Generate embeddings using both models
4. Store embeddings in Neo4j
5. Create vector indexes

**Expected output:**
```
================================================================================
Building Feature Vector Embeddings: sentence-transformers/all-MiniLM-L6-v2
================================================================================

Step 1: Fetching Journey nodes from Neo4j...
✓ Fetched 500 Journey nodes

Step 2: Converting Journey properties to text descriptions...
✓ Created 500 text descriptions

Step 3: Generating embeddings...
✓ Generated 500 embeddings (dimension: 384)

Step 4: Creating vector index in Neo4j...
✓ Created vector index: embedding_minilm (dimension: 384)

Step 5: Storing embeddings in Neo4j...
✓ Stored 500 embeddings as 'embedding_minilm' property

[Same process repeats for all-mpnet-base-v2]
```

### Step 3: Test Similarity Search

```bash
venv\Scripts\python.exe embeddings\similarity_search.py
```

**This will:**
1. Test various queries
2. Search using both models
3. Compare results
4. Display similarity scores

---

## 💻 Code Examples

### Example 1: Build Embeddings

```python
from embeddings.feature_vector_builder import FeatureVectorBuilder, load_config

# Load config
cfg = load_config("config.txt")

# Initialize builder
builder = FeatureVectorBuilder(cfg["URI"], cfg["USERNAME"], cfg["PASSWORD"])

# Build embeddings for MiniLM model
builder.build_embeddings_for_model(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    property_name="embedding_minilm"
)

# Build embeddings for MPNet model
builder.build_embeddings_for_model(
    model_name="sentence-transformers/all-mpnet-base-v2",
    property_name="embedding_mpnet"
)

builder.close()
```

### Example 2: Search by Similarity

```python
from embeddings.similarity_search import SimilaritySearcher, load_config

# Load config
cfg = load_config("config.txt")

# Initialize searcher
searcher = SimilaritySearcher(cfg["URI"], cfg["USERNAME"], cfg["PASSWORD"])

# Search with MiniLM model
results = searcher.search_by_query(
    user_query="Flights with long delays and poor service",
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    embedding_property="embedding_minilm",
    top_k=5
)

# Format for LLM
llm_context = searcher.format_results_for_llm(results)
print(llm_context)

searcher.close()
```

### Example 3: Compare Both Models

```python
# Compare results from both models
comparison = searcher.compare_models(
    user_query="Comfortable business class flights",
    top_k=5
)

print("MiniLM results:", comparison["minilm"]["count"])
print("MPNet results:", comparison["mpnet"]["count"])
```

---

## 🔍 Understanding the Results

### Similarity Scores

- Range: 0.0 to 1.0
- Higher = More similar
- **0.9-1.0**: Very similar
- **0.7-0.9**: Moderately similar
- **<0.7**: Less similar

### Example Output

```
Found 5 similar journeys for query: 'Flights with long delays'

Result 1 (similarity: 0.892):
  - Journey ID: feedback_456
  - Class: economy
  - Food satisfaction: 2/5
  - Arrival delay: 67 minutes
  - Distance: 890 miles
  - Legs: 1

Result 2 (similarity: 0.878):
  - Journey ID: feedback_789
  - Class: business
  - Food satisfaction: 3/5
  - Arrival delay: 54 minutes
  - Distance: 1200 miles
  - Legs: 2
```

---

## 📊 Model Comparison

### all-MiniLM-L6-v2
- **Dimensions:** 384
- **Size:** ~80 MB
- **Speed:** Fast
- **Quality:** Good
- **Best for:** Quick searches, prototyping

### all-mpnet-base-v2
- **Dimensions:** 768
- **Size:** ~420 MB
- **Speed:** Slower
- **Quality:** Better
- **Best for:** High-quality results, production

### When to Use Which?

| Use Case | Recommended Model |
|----------|-------------------|
| Real-time user queries | MiniLM |
| Offline analysis | MPNet |
| Limited resources | MiniLM |
| Best accuracy | MPNet |
| Quick prototyping | MiniLM |
| Final production system | Compare both, pick winner |

---

## 🎯 What Step 2.b Achieves

### Without Embeddings (Cypher only):
```
User: "Uncomfortable flights"
System: No exact match for "uncomfortable"
Result: ❌ No results
```

### With Embeddings:
```
User: "Uncomfortable flights"
System: Embeds query → Finds similar journeys with:
  - Low food satisfaction scores
  - Long delays
  - Multiple legs
Result: ✅ 10 relevant journeys found!
```

---

## ✅ Completion Checklist

- [x] Feature Vector Builder created
- [x] Text conversion function (`journey_to_text()`)
- [x] Embedding generation for Model 1 (MiniLM)
- [x] Embedding generation for Model 2 (MPNet)
- [x] Neo4j vector index creation
- [x] Similarity search implementation
- [x] Input embedding (Step 1.c)
- [x] Model comparison function

---

## 🐛 Troubleshooting

### Issue: "Unable to retrieve routing information"
**Solution:** Make sure Neo4j is running and config.txt has correct credentials. Try changing `neo4j://` to `bolt://`.

### Issue: "No module named 'sentence_transformers'"
**Solution:**
```bash
venv\Scripts\python.exe -m pip install sentence-transformers torch
```

### Issue: "Vector index not found"
**Solution:** Run `feature_vector_builder.py` first to create the indexes.

### Issue: Models downloading slowly
**Solution:** First time running will download models (~80MB and ~420MB). Be patient!

### Issue: Out of memory
**Solution:** Process journeys in batches. Modify `fetch_all_journeys()` to add LIMIT.

---

## 🔜 Next Steps

Now you have completed:
- ✅ Step 1.a: Intent Classification
- ✅ Step 1.b: Entity Extraction
- ✅ Step 1.c: Input Embedding
- ✅ Step 2.a: Baseline (Cypher queries)
- ✅ Step 2.b: Embeddings (Feature Vector)

**Next: Step 3 - LLM Layer**

You need to:
1. **Combine results** from Cypher queries (2.a) and embeddings (2.b)
2. **Structure prompts** with Context + Persona + Task
3. **Compare 3+ LLMs** (e.g., Gemma, Llama, Mistral)
4. **Evaluate** quantitatively and qualitatively

---

## 📚 Key Concepts Summary

### Feature Vector Embeddings
Converting structured data → text → vectors for semantic search

### Semantic Similarity
Finding similar items based on meaning, not exact keywords

### Cosine Similarity
Measuring angle between vectors (0=different, 1=identical)

### Vector Index
Database index for fast similarity search

### Two Models
Comparing different embedding models to find best performance

---

## 🎓 Understanding Why This Matters

Traditional keyword search:
- Query: "bad food" → Matches: "bad", "food"
- Miss: "poor service", "unsatisfied", "disappointed"

Semantic search with embeddings:
- Query: "bad food" → Embedding: [0.1, -0.2, ...]
- Finds: Similar embeddings for:
  - "poor service"
  - "unsatisfied passengers"
  - "low satisfaction scores"

**Result:** More relevant results, better user experience!

---

## 📖 Further Reading

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Understanding Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

**Great work! Step 2.b is complete. Ready for Step 3?**
