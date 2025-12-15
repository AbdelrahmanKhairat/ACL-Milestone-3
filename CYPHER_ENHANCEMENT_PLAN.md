# Cypher Query Enhancement Plan

## Problem Analysis: "Which flights had the longest delays?"

### Current Flow Issues:

1. **Intent Classification**: Works (returns "delay_analysis")
2. **Entity Extraction**: Returns empty (no entities found) - This is OK
3. **Query Selection**: Selects "delay_analysis" query
4. **Query Execution**: Should work but query structure may not be optimal

### Root Problems:

#### Problem 1: Query Structure Not Optimal
Current `delay_analysis` query:
```cypher
MATCH (f:Flight)-[:ARRIVES_AT]->(a:Airport)
OPTIONAL MATCH (j:Journey)-[:ON]->(f)
RETURN f, j, a
ORDER BY j.arrival_delay_minutes DESC
LIMIT 20
```

**Issues:**
- Returns Flight and Airport, but delay is on Journey
- Question asks "which flights" but we need to show Journey details
- Missing departure airport and passenger info

#### Problem 2: Too Generic Intent
"delay_analysis" is too broad - need more specific intents:
- `most_delayed_flights` - for "longest/worst delays"
- `least_delayed_flights` - for "best on-time performance"
- `delay_by_airport` - for "delays from JFK"
- `delay_by_class` - for "business class delays"

#### Problem 3: Missing Superlative Detection
Entity extractor doesn't detect:
- "longest", "worst", "most" → should trigger TOP ordering
- "shortest", "best", "least" → should trigger BOTTOM ordering
- "average", "typical" → should trigger AVERAGE calculation

## Enhancement Strategy:

### 1. Add Superlative Entity Extraction
Extract ordering hints: "longest", "shortest", "most", "least", "best", "worst"

### 2. Improve Intent Classification
Add more specific delay-related intents

### 3. Enhance Cypher Queries
Make queries return complete Journey context with all relationships

### 4. Add Query Parameters
Support filtering by entities even for aggregation queries

## Implementation Plan:

1. Update `entity-extractions.py` - add superlative detection
2. Update `intent-classifier.py` - add specific delay intents
3. Update `cypher_queries.py` - improve query structures
4. Update `query_executor.py` - handle new parameters
