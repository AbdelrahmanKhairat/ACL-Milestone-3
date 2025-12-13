# Code Architecture - File-by-File Summary

## Overview
This document provides a comprehensive summary of all Python files in the Graph-RAG pipeline, organized by directory.

---

## 📁 Directory: `preprocessing/`
**Purpose:** Step 1 - Input Preprocessing (Intent Classification + Entity Extraction)

### 1. `intent-classifier.py`
**Purpose:** Classifies user questions into intent categories

**What it does:**
- Uses rule-based keyword matching
- Analyzes the user's question text
- Returns one of 6 intents:
  - `delay_analysis` - Questions about flight delays
  - `find_flights` - Search for specific flights/routes
  - `airport_info` - Airport information queries
  - `passenger_experience` - Passenger satisfaction queries
  - `route_recommendation` - Route suggestions
  - `general_query` - Fallback for other questions

**Key Function:**
- `classify_intent(text: str) -> str` - Main classification function

**Example:**
```python
classify_intent("Which flights have the longest delays?")
# Returns: "delay_analysis"
```

---

### 2. `entity-extractions.py`
**Purpose:** Extracts airline-specific entities from user questions

**What it does:**
- Uses regex patterns to extract entities
- Identifies airports, routes, passenger classes, etc.
- Returns structured entity dictionary

**Entities Extracted:**
- `flight_no` - Flight numbers (e.g., "AA123")
- `departure_airport` - Airport codes (e.g., "ORD", "JFK")
- `arrival_airport` - Destination codes
- `route` - Full routes (e.g., "ORD-LAX")
- `passenger_class` - Economy, Business, First
- `generation` - Gen Z, Millennial, Boomer
- `fleet_type` - Aircraft types (A320, B737, etc.)
- `date` - Travel dates (future enhancement)

**Key Class:**
- `AirlineEntities` - Data class holding all entities

**Key Function:**
- `extract_entities(text: str) -> Dict[str, Any]` - Main extraction function

**Example:**
```python
extract_entities("Show me economy flights from ORD to LAX")
# Returns: {
#   "departure_airport": "ORD",
#   "arrival_airport": "LAX",
#   "route": "ORD-LAX",
#   "passenger_class": "economy"
# }
```

---

## 📁 Directory: `retrieval/`
**Purpose:** Step 2.a - Baseline Retrieval using Cypher Queries

### 3. `cypher_queries.py`
**Purpose:** Library of Cypher query templates

**What it does:**
- Stores 10+ pre-written Cypher queries
- Each query targets a specific intent
- Uses parameterized queries for flexibility

**Query Templates:**
1. **find_flights** - Search flights by departure/arrival airports
2. **delay_analysis** - Top 20 flights with longest delays
3. **airport_info** - Airport-specific flight data
4. **passenger_experience** - Bottom 30 flights by food/entertainment scores
5. **route_recommendation** - Top 20 routes by passenger satisfaction
6. **general_query** - Fallback query returning sample data
7. **class_specific_query** - Filter by passenger class
8. Additional specialized queries

**Key Variable:**
- `QUERIES` - Dictionary mapping intent → Cypher query string

**Example Query:**
```cypher
# delay_analysis template:
MATCH (f:Flight)-[:ARRIVES_AT]->(a:Airport)
OPTIONAL MATCH (j:Journey)-[:ON]->(f)
RETURN f, j, a
ORDER BY j.arrival_delay_minutes DESC
LIMIT 20
```

---

### 4. `query_executor.py`
**Purpose:** Executes Cypher queries against Neo4j

**What it does:**
- Takes classified intent and extracted entities
- Selects appropriate Cypher query template
- Fills in parameters with extracted entities
- Executes query against Neo4j
- Formats and returns results

**Key Class:**
- `QueryExecutor` - Main query execution class

**Key Methods:**
- `execute_query(intent, entities)` - Main execution function
- `_build_parameters(intent, entities)` - Maps entities to query params
- `_format_results(records)` - Converts Neo4j records to structured JSON

**Result Format:**
```python
{
    "count": 15,  # Number of results
    "query": "MATCH ...",  # Executed Cypher query
    "results": [
        {
            "journey_id": "12345",
            "flight_no": "AA100",
            "delay_minutes": 120,
            # ... more properties
        }
    ]
}
```

**Critical Fix Applied:**
- Filters out `embedding_*` properties to prevent context bloat (514KB → 5KB)

---

## 📁 Directory: `embeddings/`
**Purpose:** Step 2.b - Embedding-based Retrieval (Semantic Similarity)

### 5. `feature_vector_builder.py`
**Purpose:** Creates embeddings for Journey nodes

**What it does:**
- Converts Journey properties into text descriptions
- Generates embeddings using sentence transformers
- Stores embeddings in Neo4j vector index
- Supports multiple embedding models

**Key Class:**
- `FeatureVectorBuilder` - Main embedding builder

**Key Methods:**
- `load_model(model_name)` - Load sentence transformer
- `create_text_description(journey_properties)` - Convert properties to text
- `build_embeddings_batch()` - Process all journeys
- `create_vector_index()` - Create Neo4j vector index

**Text Description Format:**
```
"Journey: Business class, 45 min delay, food score 3,
entertainment score 4, 1200 miles, 2 legs"
```

**Embedding Models Supported:**
- `all-MiniLM-L6-v2` (384 dim, fast)
- `all-mpnet-base-v2` (768 dim, better quality)

---

### 6. `similarity_search.py`
**Purpose:** Performs semantic similarity search

**What it does:**
- Embeds user queries using same models
- Performs vector similarity search in Neo4j
- Returns top-k most similar Journey nodes
- Implements cosine similarity ranking

**Key Class:**
- `SimilaritySearcher` - Main search class

**Key Methods:**
- `load_model(model_name)` - Load embedding model
- `search(query_text, top_k, model)` - Main search function
- `embed_query(query_text)` - Convert query to vector

**Search Process:**
1. User query → Embed using sentence transformer
2. Neo4j vector search → Find similar journeys
3. Return top 5 results with similarity scores

**Example:**
```python
searcher.search("flights with bad food", top_k=5, model="mpnet")
# Returns 5 journeys with lowest food satisfaction scores
```

---

### 7. `build_journey_embeddings.py`
**Purpose:** Script to build and store all embeddings

**What it does:**
- Fetches all Journey nodes from Neo4j
- Converts each to text description
- Generates embeddings using models
- Stores in Neo4j with vector indices

**Key Functions:**
- `fetch_journeys()` - Get all journeys from Neo4j
- `make_description(row)` - Convert journey to text
- `build_and_store()` - Main build function

**Usage:**
```bash
python embeddings/build_journey_embeddings.py
```

---

### 8. `model_loader.py`
**Purpose:** Centralized model loading and caching

**What it does:**
- Lazy-loads sentence transformer models
- Caches loaded models to avoid reloading
- Provides consistent interface for all embedding models

**Key Configuration:**
```python
MODEL_CONFIG = {
    "minilm": {
        "hf_name": "sentence-transformers/all-MiniLM-L6-v2",
        "dim": 384
    },
    "e5_base": {
        "hf_name": "intfloat/multilingual-e5-base",
        "dim": 768
    }
}
```

**Key Function:**
- `get_model(model_key)` - Load and cache model

---

### 9. `retrieval.py`
**Purpose:** Legacy/alternative retrieval interface (not actively used)

---

## 📁 Directory: `llm_layer/`
**Purpose:** Step 3 - LLM Layer (Combine + Prompt + Generate + Evaluate)

### 10. `graph_rag_pipeline.py` ⭐ **MAIN PIPELINE**
**Purpose:** End-to-end Graph-RAG orchestrator

**What it does:**
- Integrates ALL components from Steps 1-3
- Orchestrates the complete pipeline flow
- Main entry point for answering questions

**Pipeline Flow:**
```
User Question
    ↓
Step 1: Preprocessing
    - Classify intent
    - Extract entities
    ↓
Step 2: Retrieval
    - Execute Cypher query (baseline)
    - Perform embedding search (semantic)
    ↓
Step 3: LLM Layer
    - Combine results
    - Build structured prompt
    - Query LLM
    - Return answer
```

**Key Class:**
- `GraphRAGPipeline` - Main pipeline class

**Key Method:**
- `answer_question(question, model, use_cypher, use_embeddings)` - Main function

**Returns:**
```python
{
    "question": "...",
    "intent": "delay_analysis",
    "entities": {...},
    "cypher_results": {...},
    "embedding_results": {...},
    "combined_context": "...",
    "prompt": "...",
    "answer": "...",
    "success": True,
    "llm_response": {
        "response_time": 1.82,
        "model": "qwen"
    }
}
```

---

### 11. `result_combiner.py`
**Purpose:** Combines Cypher and embedding results (Step 3.a)

**What it does:**
- Merges results from baseline and embeddings
- Removes duplicates (by journey_id)
- Ranks/prioritizes results
- Creates unified context for LLM

**Key Class:**
- `ResultCombiner` - Result merger

**Key Method:**
- `combine_results(cypher_response, embedding_response, max_results)`

**Deduplication Strategy:**
- Uses journey_id as unique identifier
- Keeps first occurrence (Cypher results prioritized)

---

### 12. `prompt_builder.py`
**Purpose:** Creates structured prompts (Step 3.b)

**What it does:**
- Builds prompts with Persona + Context + Task structure
- Reduces hallucinations by grounding in KG data
- Provides clear instructions to LLM

**Prompt Structure:**
```
PERSONA:
You are an airline company insights assistant...

CONTEXT (Knowledge Graph Data):
[Retrieved journey data with properties]

TASK:
Answer the following question based ONLY on the CONTEXT provided above.

INSTRUCTIONS:
1. Use ONLY the information provided in the CONTEXT
2. If insufficient data, say so
3. Provide specific examples from the data
...

USER QUESTION: [question]

YOUR ANSWER:
```

**Key Class:**
- `PromptBuilder` - Prompt construction class

**Key Method:**
- `build_prompt(context, question)` - Main prompt builder

---

### 13. `llm_integrations_v2.py`
**Purpose:** LLM interface supporting 3 models

**What it does:**
- Manages connections to HuggingFace models
- Supports 3 free LLMs for comparison
- Handles API calls and error handling

**Supported Models:**
1. **Qwen** - Qwen/Qwen2.5-7B-Instruct (via HuggingFace)
2. **OpenAI** - gpt-oss-120b (via Groq)
3. **Llama** - meta-llama/Llama-3.1-8B-Instruct (via Novita AI)

**Key Class:**
- `LLMIntegration` - Main LLM interface

**Key Method:**
- `query_model(model_name, prompt, max_tokens, temperature)` - Query LLM

**Error Handling:**
- Timeout errors
- API rate limits (402 errors)
- Authentication failures (401 errors)

---

### 14. `evaluator.py`
**Purpose:** Evaluates and compares LLM models (Step 3.d)

**What it does:**
- Tracks quantitative metrics (time, tokens, success rate)
- Supports qualitative evaluation (relevance, accuracy, naturalness)
- Creates comparison reports

**Quantitative Metrics:**
- Response time (seconds)
- Token count
- Success rate (0.0 to 1.0)
- Average response length

**Qualitative Metrics:**
- Relevance (1-5)
- Factual accuracy (1-5)
- Naturalness (1-5)
- Completeness (1-5)

**Key Classes:**
- `QuantitativeMetrics` - Dataclass for quantitative data
- `QualitativeMetrics` - Dataclass for qualitative data
- `ModelEvaluator` - Main evaluator

---

### 15. `compare_models.py`
**Purpose:** Automated model comparison script

**What it does:**
- Parses detailed test log files
- Extracts metrics for all 3 models
- Creates comprehensive comparison report
- Ranks models using weighted scoring

**Key Functions:**
- `parse_detailed_log(filepath)` - Extract metrics from logs
- `compare_models(model_data)` - Generate comparison report

**Comparison Report Includes:**
- Overall metrics table
- Best performer analysis
- Question-by-question comparison
- Retrieval performance
- Detailed statistics
- Weighted rankings

**Weighted Scoring:**
```python
score = (success_rate * 0.5) +
        (speed_score * 0.3) +
        (quality_score * 0.2)
```

**Usage:**
```bash
python llm_layer/compare_models.py
```

---

### 16. `test_pipeline_detailed.py`
**Purpose:** Comprehensive testing script (15 questions)

**What it does:**
- Tests pipeline with 15 diverse questions
- Logs all metrics and results
- Saves detailed output to files
- Supports all 3 models

**Test Questions Cover:**
- Delay analysis (3 questions)
- Flight search (2 questions)
- Economy/business class (3 questions)
- Airport info (2 questions)
- Passenger experience (3 questions)
- Route recommendations (2 questions)

**Logged Metrics:**
- Cypher result count
- Embedding result count
- Prompt length
- Response length
- Response time
- Success/failure status

**Usage:**
```bash
python llm_layer/test_pipeline_detailed.py
# Select model: 1 (Qwen), 2 (OpenAI), or 3 (Llama)
```

**Output:**
- Console: Real-time progress
- File: `outputs/pipeline_test_detailed_{model}_{timestamp}.txt`

---

### 17. `quick_test.py`
**Purpose:** Quick 3-question test

**What it does:**
- Fast testing with 3 representative questions
- Same metrics as detailed test
- Useful for rapid validation

**Test Questions:**
1. "Which flights have the longest delays?"
2. "Find economy class flights"
3. "Which flights have poor passenger experience?"

**Usage:**
```bash
python llm_layer/quick_test.py
```

---

### 18. `llm_integrations.py` & `llm_integration_v3.py`
**Purpose:** Legacy LLM integration versions

**Status:** Replaced by `llm_integrations_v2.py`
**Note:** Kept for backward compatibility

---

### 19. `test.py`
**Purpose:** Early testing/prototype script

**Status:** Superseded by `quick_test.py` and `test_pipeline_detailed.py`

---

## 📁 Root Files

### 20. `app.py` ⭐ **STREAMLIT UI**
**Purpose:** Step 4 - Web-based UI for Graph-RAG system

**What it does:**
- Provides interactive web interface
- Displays KG context and LLM answers
- Allows model and retrieval method selection
- Shows detailed metrics and statistics

**Features:**
- ✅ Model selection dropdown (Qwen/OpenAI/Llama)
- ✅ Retrieval method toggles (Cypher/Embeddings/Both)
- ✅ Example questions
- ✅ KG context viewer (dark theme)
- ✅ LLM answer display (light blue theme)
- ✅ Metrics dashboard
- ✅ Intent & entity display
- ✅ Optional Cypher query display

**UI Components:**
1. **Sidebar** - Configuration and settings
2. **Main Area** - Question input and results
3. **Metrics Cards** - Response time, counts
4. **Context Box** - Raw KG data (dark background, light text)
5. **Answer Box** - LLM response (light blue background, black text)

**Usage:**
```bash
streamlit run app.py
# Opens at http://localhost:8501
```

---

## 📊 File Relationships

### Pipeline Flow (file dependencies):
```
app.py
  └─> graph_rag_pipeline.py
       ├─> intent-classifier.py (Step 1.a)
       ├─> entity-extractions.py (Step 1.b)
       ├─> query_executor.py (Step 2.a)
       │    └─> cypher_queries.py
       ├─> similarity_search.py (Step 2.b)
       │    └─> model_loader.py
       ├─> result_combiner.py (Step 3.a)
       ├─> prompt_builder.py (Step 3.b)
       └─> llm_integrations_v2.py (Step 3.c)
```

### Testing Flow:
```
test_pipeline_detailed.py
  └─> graph_rag_pipeline.py
       └─> [all components]

compare_models.py
  └─> parses output files from test_pipeline_detailed.py
```

---

## 🎯 File Usage Guide

### For Testing:
- **Quick test (3 questions):** `llm_layer/quick_test.py`
- **Full test (15 questions):** `llm_layer/test_pipeline_detailed.py`
- **Model comparison:** `llm_layer/compare_models.py`

### For Demo:
- **Interactive UI:** `app.py` (Streamlit)
- **Direct pipeline:** `llm_layer/graph_rag_pipeline.py`

### For Development:
- **Add new intents:** `preprocessing/intent-classifier.py`
- **Add new entities:** `preprocessing/entity-extractions.py`
- **Add new queries:** `retrieval/cypher_queries.py`
- **Modify prompt:** `llm_layer/prompt_builder.py`

### For Setup:
- **Build embeddings:** `embeddings/build_journey_embeddings.py`
- **Test connections:** `neo4j_connector.py`, `test_fixed_pipeline.py`

---

## 📈 File Statistics

| Directory | Files | Purpose |
|-----------|-------|---------|
| `preprocessing/` | 3 | Step 1: Input preprocessing |
| `retrieval/` | 3 | Step 2.a: Cypher queries |
| `embeddings/` | 6 | Step 2.b: Semantic search |
| `llm_layer/` | 10 | Step 3: LLM layer |
| Root | 1 | Step 4: UI |
| **Total** | **23** | **Complete pipeline** |

---

## 🔑 Key Entry Points

1. **Web UI:** `app.py`
2. **Python API:** `llm_layer/graph_rag_pipeline.py`
3. **Testing:** `llm_layer/test_pipeline_detailed.py`
4. **Comparison:** `llm_layer/compare_models.py`
5. **Setup:** `embeddings/build_journey_embeddings.py`

---

## 💡 Quick Reference

### To answer a question programmatically:
```python
from llm_layer.graph_rag_pipeline import GraphRAGPipeline, load_config

cfg = load_config()
pipeline = GraphRAGPipeline(
    neo4j_uri=cfg["URI"],
    neo4j_username=cfg["USERNAME"],
    neo4j_password=cfg["PASSWORD"],
    hf_token="your_token",
    default_model="qwen"
)

result = pipeline.answer_question(
    "Which flights have the longest delays?",
    model="qwen",
    use_cypher=True,
    use_embeddings=True
)

print(result["answer"])
```

### To launch the UI:
```bash
streamlit run app.py
```

### To run tests:
```bash
# Quick test
python llm_layer/quick_test.py

# Full test
python llm_layer/test_pipeline_detailed.py

# Compare models
python llm_layer/compare_models.py
```

---

**This covers all major Python files in your Graph-RAG implementation!** 🚀
