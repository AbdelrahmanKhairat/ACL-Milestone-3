# LLM Layer Testing Scripts

This directory contains comprehensive testing scripts for the Graph-RAG pipeline.

## Test Scripts Overview

### 1. **test_pipeline_detailed.py** - Full Detailed Test (15 Questions)

The most comprehensive test that logs everything in detail.

**What it tests:**
- 15 diverse questions covering all intent types
- Logs for each question:
  - Number of Cypher results
  - Number of embedding results
  - Full prompt sent to LLM (with character count)
  - Full LLM response
  - Response time
  - Success/failure status

**How to run:**
```bash
cd c:\Users\LOQ\Desktop\ACL-Milestone-3
venv\Scripts\python.exe llm_layer\test_pipeline_detailed.py
```

**Interactive prompts:**
- Choose model: 1 (qwen), 2 (openai), or 3 (llama)
- Or just press Enter for default (qwen)

**Output:**
- Saves to: `outputs/pipeline_test_detailed_{model}_{timestamp}.txt`
- File includes:
  - Full prompt for each question
  - Full response from LLM
  - Summary statistics
  - Question-by-question comparison table

**Example output file structure:**
```
================================================================================
QUESTION 1/15: Which flights have the longest delays?
================================================================================

[STEP 1] PREPROCESSING
Intent: delay_analysis
Entities Extracted:
  (No entities extracted)

[STEP 2] GRAPH RETRIEVAL
Cypher Query Results: 20 journeys
Embedding Search Results: 5 journeys
Total Context Length: 4734 characters

[STEP 3] PROMPT SENT TO LLM
Prompt Length: 5892 characters
Model: qwen

FULL PROMPT:
PERSONA:
You are an airline company insights assistant...
[full prompt here]

[STEP 4] LLM RESPONSE
Response Time: 1.79 seconds
Response Length: 247 characters
Success: True

FULL RESPONSE:
Based on the provided context, the flight with the longest delay is...
```

---

### 2. **quick_test.py** - Quick Test (3 Questions)

Fast test for quick validation.

**What it tests:**
- 3 representative questions
- Shows retrieval counts, context preview, prompt preview, and LLM response
- Runs in ~10-20 seconds

**How to run:**
```bash
# Default (qwen model)
venv\Scripts\python.exe llm_layer\quick_test.py

# Specific model
venv\Scripts\python.exe llm_layer\quick_test.py qwen
venv\Scripts\python.exe llm_layer\quick_test.py openai
venv\Scripts\python.exe llm_layer\quick_test.py llama
```

**Output:**
- Prints directly to console
- Shows first 500 chars of context
- Shows first 800 chars of prompt
- Shows full LLM response

---

### 3. **graph_rag_pipeline.py** - Main Pipeline

The core pipeline implementation.

**How to run standalone:**
```bash
venv\Scripts\python.exe llm_layer\graph_rag_pipeline.py
```

**What it does:**
- Tests 2 sample questions
- Demonstrates model comparison feature
- Shows basic functionality

---

## Test Question Categories

The detailed test (`test_pipeline_detailed.py`) covers these question types:

### Delay Questions (3)
- "Which flights have the longest delays?"
- "Show me flights with delays from ORD"
- "Flights delayed more than 1 hour"

### Flight Search (3)
- "Show me flights from CAI to DXB"
- "What flights go from JFK to FRA?"
- "Find economy class flights"

### Airport Questions (2)
- "Tell me about ORD airport"
- "Information on Cairo airport"

### Passenger Experience (3)
- "Which flights have poor passenger experience?"
- "Show me flights with bad food quality"
- "Flights with low satisfaction scores"

### Recommendations (2)
- "Recommend a good flight route"
- "Best business class flights"

### Complex Questions (2)
- "Business class flights from ORD with delays"
- "Economy passengers on long distance routes with poor food"

---

## Understanding the Output

### Cypher Results Count
- Number of Journey nodes returned by the Cypher query
- Based on intent classification
- Example: `delay_analysis` intent returns top 20 delayed flights

### Embedding Results Count
- Number of Journey nodes returned by semantic similarity search
- Uses vector embeddings (MPNet by default)
- Typically returns top 5 most similar journeys

### Context Sent to LLM
- **Before fix:** Was 500KB+ (included embedding vectors)
- **After fix:** ~5KB (embedding vectors filtered out)
- Contains formatted journey data: delays, food scores, passenger class, etc.

### Prompt Structure
```
PERSONA:
You are an airline company insights assistant...

CONTEXT (Knowledge Graph Data):
Found 20 result(s) for delay_analysis:
Result 1:
  f: flight_number=757, fleet_type_description=A320-200
  j: passenger_class=Economy, arrival_delay_minutes=880, food_satisfaction_score=2
  a: station_code=JAX
...

TASK:
Answer the following question based ONLY on the CONTEXT provided above.

INSTRUCTIONS:
1. Use ONLY the information provided in the CONTEXT section
2. If the CONTEXT doesn't contain enough information, say: 'I don't have sufficient data'
3. Provide specific examples from the data (journey IDs, metrics, numbers)
...

USER QUESTION: Which flights have the longest delays?

YOUR ANSWER:
```

### Response Metrics
- **Response Time:** How long LLM took to generate answer (seconds)
- **Response Length:** Number of characters in LLM's answer
- **Success:** Whether LLM call succeeded (True/False)

---

## Common Issues

### Issue 1: "embedding vectors too large"
✅ **Fixed!** We filter out `embedding_minilm` and `embedding_mpnet` properties when formatting results for LLM.

### Issue 2: "UnicodeEncodeError"
✅ **Fixed!** Removed all Unicode checkmarks (✓, ✗) and replaced with [OK], [ERROR].

### Issue 3: "Model not available"
- HuggingFace models can be busy
- Wait 30-60 seconds and try again
- Or use a different model (qwen, openai, llama)

### Issue 4: "No results from Cypher"
- Check if intent classification is correct
- Check if entities were extracted correctly
- Run `test_entity_query_integration.py` to diagnose

---

## Model Comparison

All 3 models are chat-based and tested:

| Model | Full Name | Speed | Quality | Notes |
|-------|-----------|-------|---------|-------|
| **qwen** | Qwen/Qwen2.5-7B-Instruct | Medium | Excellent | **Default, recommended** |
| **openai** | openai/gpt-oss-120b | Medium | Good | Good alternative |
| **llama** | meta-llama/Llama-3.1-8B-Instruct | Slower | Very Good | More detailed responses |

---

## Interpreting Results

### Good Result Example:
```
Question: "Which flights have the longest delays?"
Cypher: 20 results
Embeddings: 5 results
Response Time: 1.79s
Success: True

Answer: "Based on the provided context, the flight with the longest delay is
Flight number 757, with an arrival delay of 880 minutes. The next longest
is flight number 2 with 620 minutes delay..."
```
✅ LLM correctly identified the flights with longest delays
✅ Provided specific data (flight numbers, delay times)
✅ Stayed grounded in the provided context

### Poor Result Example:
```
Question: "Find flights from London to Paris"
Cypher: 0 results
Embeddings: 5 results (unrelated)
Response Time: 1.45s
Success: True

Answer: "I don't have sufficient data to answer this question."
```
⚠️ Entity extraction failed (city names not recognized)
⚠️ Only airport codes (LHR, CDG) work, not city names
📝 Known limitation - see test_entity_query_integration.py results

---

## Next Steps

After running tests:

1. **Review the output file** - Check if LLM responses are accurate
2. **Check success rate** - Should be 80%+
3. **Identify failures** - Look for patterns in failed questions
4. **Improve if needed:**
   - Entity extraction (city name → airport code mapping)
   - Intent classification (for compound questions)
   - Query templates (add more specific queries)

---

## Quick Reference

```bash
# Full detailed test (15 questions, ~5 minutes)
venv\Scripts\python.exe llm_layer\test_pipeline_detailed.py

# Quick test (3 questions, ~20 seconds)
venv\Scripts\python.exe llm_layer\quick_test.py

# Test with specific model
venv\Scripts\python.exe llm_layer\quick_test.py llama

# Run pipeline demo
venv\Scripts\python.exe llm_layer\graph_rag_pipeline.py
```

---

**All tests fixed and ready to use!** 🚀
