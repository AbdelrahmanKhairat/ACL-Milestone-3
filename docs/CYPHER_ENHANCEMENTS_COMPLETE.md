# Cypher Query System - Complete Enhancements

## Summary of Changes

We've comprehensively enhanced the entire Cypher query retrieval system with three major improvements:

### 1. Enhanced Entity Extraction
### 2. Enhanced Intent Classification
### 3. Enhanced Cypher Queries

---

## 1. Enhanced Entity Extraction

**File:** `preprocessing/entity-extractions.py`

### New Entities Added:

```python
@dataclass
class AirlineEntities:
    # ... existing fields ...
    sort_order: Optional[str]      # "DESC" or "ASC"
    sort_attribute: Optional[str]  # "delay", "miles", "food_score", "legs"
    limit: Optional[int]            # Top N results
```

### New Function: `extract_superlatives()`

**Detects:**
- **Superlatives for DESC order**: "longest", "worst", "most", "highest", "maximum", "biggest", "top"
- **Superlatives for ASC order**: "shortest", "best", "least", "lowest", "minimum", "smallest", "bottom"
- **Numeric limits**: "top 5", "first 10", "3 flights"

**Examples:**
| Query | sort_order | sort_attribute | limit |
|-------|------------|----------------|-------|
| "Which flights had the longest delays?" | DESC | delay | 10 |
| "Show me the 5 shortest journeys" | ASC | miles | 5 |
| "Top 3 flights with worst food" | DESC | food_score | 3 |
| "Best on-time performance" | ASC | delay | 10 |

---

## 2. Enhanced Intent Classification

**File:** `preprocessing/intent-classifier.py`

### New Specific Intents:

1. **`most_delayed_flights`** - Triggers on: "longest delays", "worst delays", "most delayed"
2. **`shortest_journeys`** - Triggers on: "shortest", "fastest", "quickest"
3. **`multi_leg_flights`** - Triggers on: "multi-leg", "connection", "stop", "layover"
4. **`loyalty_analysis`** - Triggers on: "loyalty", "frequent flyer", "member"

### Improved Keywords:

- Added "food", "meal" to `passenger_experience` intent
- Better prioritization: specific intents checked BEFORE general ones

### Intent Hierarchy (Priority Order):

```
1. most_delayed_flights (most specific)
2. shortest_journeys
3. multi_leg_flights
4. loyalty_analysis
5. delay_analysis (general)
6. find_flights
7. airport_info
8. passenger_experience
9. route_recommendation
10. general_query (fallback)
```

---

## 3. Enhanced Cypher Queries

**File:** `retrieval/cypher_queries.py`

### Major Change: ALL queries now return complete Journey context

**Old structure** (returned Node objects):
```cypher
RETURN f, j, a  # Returns nodes - hard to work with
```

**New structure** (returns flat properties):
```cypher
RETURN j.feedback_ID as feedback_ID,
       j.passenger_class as passenger_class,
       j.food_satisfaction_score as food_satisfaction_score,
       j.arrival_delay_minutes as arrival_delay_minutes,
       j.actual_flown_miles as actual_flown_miles,
       j.number_of_legs as number_of_legs,
       f.flight_number as flight_number,
       f.fleet_type_description as fleet_type,
       dep.station_code as departure_airport,
       arr.station_code as arrival_airport,
       p.generation as generation,
       p.loyalty_program_level as loyalty_level,
       p.record_locator as record_locator
```

### Benefits:

1. **Consistent format** - Matches embedding search results
2. **Complete context** - All relationships included
3. **Easy to combine** - Cypher + Embedding results merge seamlessly
4. **LLM-ready** - Direct properties instead of nested objects

### All 10 Queries Enhanced:

✅ `find_flights` - Now returns complete Journey context
✅ `delay_analysis` - Now returns complete Journey context
✅ `airport_info` - Now returns flights from/to airport with Journey context
✅ `passenger_experience` - Now returns complete Journey context
✅ `route_recommendation` - Now returns complete Journey context
✅ `general_query` - Now returns sample journeys with complete context
✅ `most_delayed_flights` - NEW! Filters for delays > 0
✅ `shortest_journeys` - Enhanced with complete context
✅ `multi_leg_flights` - Enhanced with complete context
✅ `loyalty_analysis` - Enhanced with complete context

---

## Example Flow: "Which flights had the longest delays?"

### Before Enhancement:
```
User: "Which flights had the longest delays?"
↓
[Intent] delay_analysis
[Entities] All None (nothing extracted)
[Query] Returns Node objects: f, j, a
[Result] Hard to parse, missing context
```

### After Enhancement:
```
User: "Which flights had the longest delays?"
↓
[Intent] most_delayed_flights ✅ (more specific!)
[Entities]
  - sort_order: "DESC" ✅
  - sort_attribute: "delay" ✅
  - limit: 10 ✅
[Query] Returns flat properties with complete context ✅
[Result] Ready for LLM:
  - Journey ID: F_434
  - Route: JFK → LAX
  - Flight: AA1234 (Boeing 787)
  - Class: Economy
  - Passenger: Gen Z, Gold loyalty
  - Food: 1/5
  - Delay: 104 minutes ✅
  - Distance: 7853 miles
  - Legs: 3
```

---

## Testing Examples

### Test Query 1: "Which flights had the longest delays?"
- ✅ Intent: `most_delayed_flights`
- ✅ Entities: sort_order="DESC", sort_attribute="delay", limit=10
- ✅ Returns: Top 10 most delayed flights with complete context

### Test Query 2: "Show me the 5 shortest journeys"
- ✅ Intent: `shortest_journeys`
- ✅ Entities: sort_order="ASC", sort_attribute="miles", limit=5
- ✅ Returns: 5 shortest flights by distance with complete context

### Test Query 3: "Flights with connections"
- ✅ Intent: `multi_leg_flights`
- ✅ Entities: No specific sort/limit
- ✅ Returns: All multi-leg journeys with complete context

### Test Query 4: "Economy flights from JFK to LAX"
- ✅ Intent: `find_flights`
- ✅ Entities: departure_airport="JFK", arrival_airport="LAX", passenger_class="economy"
- ✅ Returns: Flights on that route with complete context

---

## Result Format (Consistent Across All Queries)

Every query now returns the same structure:

```python
{
    "feedback_ID": "F_434",
    "passenger_class": "Economy",
    "food_satisfaction_score": 1,
    "arrival_delay_minutes": 104,
    "actual_flown_miles": 7853,
    "number_of_legs": 3,
    "flight_number": "AA1234",
    "fleet_type": "Boeing 787",
    "departure_airport": "JFK",
    "arrival_airport": "LAX",
    "generation": "Gen Z",
    "loyalty_level": "Gold",
    "record_locator": "ABC123"
}
```

This matches the embedding search results format, making combination in `result_combiner.py` seamless!

---

## Next Steps

The Cypher query system is now fully enhanced and ready to work with:

1. ✅ Enhanced entity extraction with superlatives
2. ✅ Enhanced intent classification with specific intents
3. ✅ Enhanced Cypher queries returning complete context
4. ✅ Consistent format matching embedding search results

**Ready for integration with the full Graph-RAG pipeline!**
