# debug_cypher_output.py
"""
Debug script to see what Cypher queries are actually returning
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import importlib.util

# Load preprocessing modules
spec = importlib.util.spec_from_file_location("intent_classifier", "preprocessing/intent-classifier.py")
intent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent_module)
classify_intent = intent_module.classify_intent

spec = importlib.util.spec_from_file_location("entity_extractions", "preprocessing/entity-extractions.py")
entity_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entity_module)
extract_entities = entity_module.extract_entities

from retrieval.query_executor import QueryExecutor, load_config

# Load config
cfg = load_config()

# Initialize query executor
executor = QueryExecutor(cfg["URI"], cfg["USERNAME"], cfg["PASSWORD"])

# Test question
question = "Which flights have the longest delays?"

print("="*80)
print(f"DEBUGGING CYPHER OUTPUT FOR: {question}")
print("="*80)

# Step 1: Classify intent
intent = classify_intent(question)
print(f"\n1. Intent: {intent}")

# Step 2: Extract entities
entities = extract_entities(question)
print(f"\n2. Entities: {entities}")

# Step 3: Execute query
response = executor.execute_query(intent, entities)

print(f"\n3. Cypher Response:")
print(f"   - Intent: {response.get('intent')}")
print(f"   - Count: {response.get('count')}")
print(f"   - Has error: {'error' in response}")

if 'error' in response:
    print(f"   - Error: {response['error']}")

print(f"\n4. Query Used:")
print(response.get('query', 'NO QUERY'))

print(f"\n5. Parameters:")
print(response.get('params', 'NO PARAMS'))

print(f"\n6. First 3 Results (raw):")
results = response.get('results', [])
for i, record in enumerate(results[:3]):
    print(f"\n   Result {i+1}:")
    print(f"   {record}")

print(f"\n7. Formatted for LLM:")
if hasattr(executor, 'format_results_for_llm'):
    formatted = executor.format_results_for_llm(response)
    print(formatted[:500])  # First 500 chars
    print(f"\n   Total formatted length: {len(formatted)} characters")
else:
    print("   ERROR: format_results_for_llm method not found!")

print("\n" + "="*80)

executor.close()
