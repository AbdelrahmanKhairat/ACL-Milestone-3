# Graph-RAG System Test Questions

## Test Suite for Enhanced Cypher Queries + Semantic Embeddings

These 7 questions comprehensively test all enhancements made to the Graph-RAG system.

---

## 1. Superlative Detection - Most Delayed Flights
**Question:** `"Which flights had the longest delays?"`

**Tests:**
- ✅ Intent: `most_delayed_flights` (specific intent)
- ✅ Entity Extraction: `sort_order="DESC"`, `sort_attribute="delay"`, `limit=10`
- ✅ Cypher Query: Filters WHERE delay > 0, orders DESC by arrival_delay_minutes
- ✅ Returns: Complete Journey context with all 13 properties

**Expected Results:**
- Top 10 most delayed flights
- Each result shows: Route (JFK→LAX), Flight number, Delay minutes, Class, Food score, etc.
- Semantic embedding should also catch "long delays", "worst delays" if description rich

---

## 2. Numeric Limit + Superlative - Shortest Journeys
**Question:** `"Show me the 5 shortest journeys"`

**Tests:**
- ✅ Intent: `shortest_journeys` (specific intent)
- ✅ Entity Extraction: `sort_order="ASC"`, `sort_attribute="miles"`, `limit=5`
- ✅ Cypher Query: Orders ASC by actual_flown_miles
- ✅ Limit: Only 5 results returned

**Expected Results:**
- 5 shortest flights by distance
- Should show regional/short-haul flights
- Complete context: airports, passenger info, flight details

---

## 3. Multi-Entity Extraction - Route + Class
**Question:** `"Economy class flights from JFK to LAX"`

**Tests:**
- ✅ Intent: `find_flights` (route-based)
- ✅ Entity Extraction: `departure_airport="JFK"`, `arrival_airport="LAX"`, `passenger_class="economy"`
- ✅ Cypher Query: Filters by route AND class
- ✅ Parameter Binding: Uses $from_airport, $to_airport in query

**Expected Results:**
- All Economy flights on JFK→LAX route
- Should include delays, food scores, miles, legs
- Tests parameter passing in find_flights query

---

## 4. Semantic Search - Food Quality (Embedding Focus)
**Question:** `"Flights with terrible food and poor service"`

**Tests:**
- ✅ Intent: `passenger_experience`
- ✅ Semantic Matching: Embedding description should match "TERRIBLE FOOD quality, very poor service"
- ✅ Cypher Query: Orders by food_satisfaction_score ASC (worst first)
- ✅ Combination: Both Cypher + Embedding results merged

**Expected Results:**
- Flights with food_score = 1 or 2
- Embedding results should rank high for "terrible", "poor" descriptors
- Result combination shows de-duplication by feedback_ID

---

## 5. Multi-Leg Journeys - Connection Detection
**Question:** `"Flights with connections or layovers"`

**Tests:**
- ✅ Intent: `multi_leg_flights` (specific intent)
- ✅ Entity Extraction: No specific entities (relies on intent only)
- ✅ Cypher Query: Filters WHERE number_of_legs > 1
- ✅ Ordering: DESC by number_of_legs (most connections first)

**Expected Results:**
- Only multi-leg journeys (legs > 1)
- Sorted by number of connections
- Shows complete route, flight, passenger info

---

## 6. Loyalty Analysis - Passenger Tier
**Question:** `"Gold loyalty members on long-haul flights"`

**Tests:**
- ✅ Intent: `loyalty_analysis` (specific intent)
- ✅ Entity Extraction: May detect "long-haul" → `sort_attribute="miles"`
- ✅ Cypher Query: Orders by loyalty_program_level DESC
- ✅ Semantic Embedding: Should match "Gold loyalty" + "long distance"

**Expected Results:**
- Passengers with Gold/Platinum loyalty levels
- Preferably long-haul flights (high miles)
- Shows generation, loyalty_level, record_locator

---

## 7. Complex Multi-Factor Query - Best Routes
**Question:** `"Best business class routes with minimal delays and good food"`

**Tests:**
- ✅ Intent: `route_recommendation` (complex query)
- ✅ Entity Extraction: `passenger_class="business"`, `sort_order="ASC"` (best/minimal)
- ✅ Cypher Query: Multi-factor ordering (delay ASC, miles ASC, food DESC)
- ✅ Semantic Embedding: Should match "good food", "minimal delays", "best routes"

**Expected Results:**
- Business class flights
- Low delays + high food scores
- Efficient routes (lower miles preferred)
- Tests complex ORDER BY clause in route_recommendation

---

## Testing Instructions

### Run in Streamlit:
1. Start the app: `streamlit run app.py`
2. Enter each question in the text input
3. Observe results in both sections:
   - **Retrieved Knowledge Graph Context** (Cypher + Embeddings combined)
   - **Assistant Answer** (LLM generation)

### What to Validate:
- ✅ Correct intent classification (check logs or add debug output)
- ✅ Correct entities extracted (especially superlatives, limits)
- ✅ Cypher results match expected filters/ordering
- ✅ Embedding results semantically relevant
- ✅ No duplicate feedback_IDs in combined results
- ✅ Complete 13-property structure in all results
- ✅ LLM answer references the retrieved context

---

## Expected Coverage

| Feature | Question(s) Testing |
|---------|-------------------|
| Superlative Detection (DESC) | 1, 4 |
| Superlative Detection (ASC) | 2, 7 |
| Numeric Limit Extraction | 2 |
| Specific Intents | 1, 2, 5, 6 |
| Multi-Entity Extraction | 3, 7 |
| Airport Code Extraction | 3 |
| Passenger Class Extraction | 3, 7 |
| Semantic Food Matching | 4, 7 |
| Semantic Delay Matching | 7 |
| Multi-Leg Detection | 5 |
| Loyalty Level Matching | 6 |
| Complex Multi-Factor Ordering | 7 |
| Result Combination (Cypher + Embedding) | ALL |

---

## Success Criteria

**All tests pass if:**
1. Each query returns relevant results (no empty responses)
2. Superlatives correctly trigger DESC/ASC ordering
3. Numeric limits respected (e.g., only 5 results for question 2)
4. No duplicate feedback_IDs in combined results
5. All results have complete 13-property structure
6. Semantic embeddings contribute meaningful matches (especially for questions 4, 6, 7)
7. LLM generates coherent answers based on retrieved context

**System is production-ready when all 7 questions produce expected results!**
