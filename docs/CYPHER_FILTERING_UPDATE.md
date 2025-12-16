# Cypher Query Filtering Enhancement

## Summary

Updated ALL 10 Cypher queries to support **optional filtering** based on extracted entities. This makes the system much more flexible and allows combining filters (e.g., "shortest journeys from CAI airport" or "delayed business class flights").

---

## Changes Made

### 1. Updated All Cypher Queries ([cypher_queries.py](retrieval/cypher_queries.py))

**ALL 10 queries now support**:
- ✅ Optional `$from_airport` filter (departure airport)
- ✅ Optional `$to_airport` filter (arrival airport)
- ✅ Optional `$passenger_class` filter (economy, business, first)
- ✅ Optional `$generation` filter (Gen Z, Millennial, Boomer)
- ✅ Dynamic `$limit` parameter (from extracted entities or default 20)

**Query Pattern** (used by all queries):
```cypher
WHERE ($from_airport IS NULL OR dep.station_code = $from_airport)
  AND ($to_airport IS NULL OR arr.station_code = $to_airport)
  AND ($passenger_class IS NULL OR j.passenger_class = $passenger_class)
  AND ($generation IS NULL OR p.generation = $generation)
...
LIMIT $limit
```

**Queries Updated**:
1. ✅ `find_flights`
2. ✅ `delay_analysis`
3. ✅ `airport_info`
4. ✅ `passenger_experience`
5. ✅ `route_recommendation`
6. ✅ `general_query`
7. ✅ `most_delayed_flights`
8. ✅ `shortest_journeys`
9. ✅ `multi_leg_flights`
10. ✅ `loyalty_analysis`

---

### 2. Updated Parameter Mapping ([query_executor.py:96-130](retrieval/query_executor.py#L96-L130))

**Before**: Only `find_flights` and `airport_info` had parameter mapping.

**After**: ALL queries receive these parameters:
```python
params = {
    "from_airport": entities.get("departure_airport"),
    "to_airport": entities.get("arrival_airport"),
    "passenger_class": entities.get("passenger_class"),
    "generation": entities.get("generation"),
    "limit": entities.get("limit") or 20  # Dynamic or default
}
```

---

## Example Use Cases

### Example 1: "Show me the 5 shortest journeys from CAI airport"

**Flow**:
1. **Intent**: `shortest_journeys`
2. **Entities**:
   - `departure_airport`: "CAI" ✅
   - `sort_order`: "ASC"
   - `sort_attribute`: "miles"
   - `limit`: 5 ✅
3. **Cypher Query**: `shortest_journeys` with filters
4. **Parameters**:
   ```python
   {
       "from_airport": "CAI",
       "to_airport": None,
       "passenger_class": None,
       "generation": None,
       "limit": 5
   }
   ```
5. **Result**: Returns the 5 shortest flights departing from CAI ✅

---

### Example 2: "Economy class flights with longest delays"

**Flow**:
1. **Intent**: `most_delayed_flights`
2. **Entities**:
   - `passenger_class`: "economy" ✅
   - `sort_order`: "DESC"
   - `sort_attribute`: "delay"
   - `limit`: 10
3. **Cypher Query**: `most_delayed_flights` with class filter
4. **Parameters**:
   ```python
   {
       "from_airport": None,
       "to_airport": None,
       "passenger_class": "economy",
       "generation": None,
       "limit": 10
   }
   ```
5. **Result**: Returns top 10 delayed economy flights ✅

---

### Example 3: "Gen Z passengers from JFK to LAX"

**Flow**:
1. **Intent**: `find_flights`
2. **Entities**:
   - `departure_airport`: "JFK" ✅
   - `arrival_airport`: "LAX" ✅
   - `generation`: "gen z" ✅
3. **Parameters**:
   ```python
   {
       "from_airport": "JFK",
       "to_airport": "LAX",
       "passenger_class": None,
       "generation": "gen z",
       "limit": 20
   }
   ```
5. **Result**: Returns Gen Z passenger journeys on JFK→LAX route ✅

---

## Benefits

### 1. **Flexible Filtering**
Users can now combine multiple filters:
- "Business class flights from CAI"
- "Gen Z passengers with poor food satisfaction"
- "Economy delays on JFK to LAX route"

### 2. **Dynamic Limits**
Queries respect user-specified limits:
- "Top 5 flights" → `LIMIT 5`
- "Show me 3 journeys" → `LIMIT 3`
- No limit specified → `LIMIT 20` (default)

### 3. **Consistent Pattern**
All queries use the same WHERE clause pattern with NULL checks, making the codebase:
- ✅ Easy to maintain
- ✅ Easy to extend (add more filters later)
- ✅ Predictable behavior

### 4. **Backward Compatible**
If no entities are extracted (all params are NULL), queries return unfiltered results just like before.

---

## Testing

### Test Query 1:
```
Query: "Show me the 5 shortest journeys from CAI airport"
Expected: 5 flights departing from CAI, sorted by distance ASC
```

### Test Query 2:
```
Query: "Business class flights with longest delays"
Expected: Business class journeys sorted by delay DESC
```

### Test Query 3:
```
Query: "Flights from JFK"
Expected: All flights departing from JFK (any class, any destination)
```

### Test Query 4:
```
Query: "Gen Z passengers"
Expected: All Gen Z passenger journeys (no other filters)
```

---

## Next Steps

✅ **Cypher queries** now support flexible filtering
✅ **Entity extraction** detects airports, class, generation, limits
✅ **Query executor** maps all entities to parameters

**Remaining**: Post-process embedding results when superlatives detected (Issue #1 - deferred for now)

---

## Files Modified

1. **[retrieval/cypher_queries.py](retrieval/cypher_queries.py)** - All 10 queries updated with WHERE clauses and dynamic LIMIT
2. **[retrieval/query_executor.py](retrieval/query_executor.py#L96-L130)** - Updated `_map_entities_to_params()` to pass all entity parameters

**System is now ready for complex filtered queries!** 🎉
