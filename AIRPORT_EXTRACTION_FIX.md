# Airport Code Extraction Fix

## Problem

The entity extractor was failing to extract airport codes from user queries like:
- "show me the 5 shortest journeys from IAX airport" → `departure_airport: None`
- "show me the 5 shortest journeys from CAI airport" → `departure_airport: None`

Additionally, numeric limits were not being extracted from patterns like "the 5 shortest".

## Root Causes

### Issue 1: Hardcoded Airport Whitelist
The `AIRPORT_CODES` list only contained 7 airports:
```python
AIRPORT_CODES = ["CAI", "DXB", "JFK", "LHR", "FRA", "AMS", "CDG"]
```

However, your database contains many other airports (IAX, MKX, SFX, ORX, SMX, RIX, etc.).

The extraction logic only checked for airports in this hardcoded list:
```python
codes_found: List[str] = []
for code in AIRPORT_CODES:
    if code in upper:
        codes_found.append(code)
```

### Issue 2: Missing Limit Pattern
The numeric limit extraction didn't support the pattern "the N":
```python
limit_patterns = [
    r"\btop\s+(\d+)\b",      # "top 5"
    r"\bfirst\s+(\d+)\b",    # "first 5"
    # Missing: "the 5"
    r"\b(\d+)\s+(?:flight|journey|result)",
    r"\blimit\s+(\d+)\b",
]
```

## Solutions Implemented

### Fix 1: Dynamic Airport Code Detection
**File**: [preprocessing/entity-extractions.py](preprocessing/entity-extractions.py#L56)

**Added regex pattern** to detect ANY 3-letter uppercase code:
```python
# Any 3-letter uppercase code (airport code pattern)
AIRPORT_CODE_RE = re.compile(r"\b([A-Z]{3})\b")
```

**Updated extraction logic** to find all 3-letter codes and filter out common words:
```python
# 2) Find ALL 3-letter uppercase codes in the text
all_matches = AIRPORT_CODE_RE.findall(upper)

# Filter out common words that aren't airports
excluded_words = {
    "THE", "AND", "FOR", "ARE", "YOU", "CAN", "ANY", "ALL", "TOP", "ASC", "DESC",
    "GEN", "NEW", "OLD", "BAD", "BIG", "ONE", "TWO", "GET", "GOT", "HAS", "HAD",
    "NOT", "BUT", "YET", "NOW", "HOW", "WHY", "WHO", "WAS", "WEE", "WAY"
}
codes_found = [code for code in all_matches if code not in excluded_words]
```

**Benefits**:
- ✅ Works with ANY airport in your database (IAX, MKX, SFX, etc.)
- ✅ No need to maintain a hardcoded list
- ✅ Automatically adapts to new airports added to the database
- ✅ Filters out common English words to avoid false positives

### Fix 2: Enhanced Limit Pattern
**File**: [preprocessing/entity-extractions.py](preprocessing/entity-extractions.py#L195-L202)

**Added "the N" pattern**:
```python
limit_patterns = [
    r"\btop\s+(\d+)\b",
    r"\bfirst\s+(\d+)\b",
    r"\bthe\s+(\d+)\b",  # NEW: handles "the 5 shortest"
    r"\b(\d+)\s+(?:flight|journey|result)",
    r"\blimit\s+(\d+)\b",
]
```

**Benefits**:
- ✅ Extracts limits from "the 5 shortest" → `limit: 5`
- ✅ Works with all existing patterns (top, first, etc.)

## Test Results

### Before Fix:
```python
Query: "show me the 5 shortest journeys from IAX airport"
Entities: {
    "departure_airport": None,  # ❌ Missing
    "limit": 10,                # ❌ Wrong (should be 5)
    "sort_order": "ASC"
}
```

### After Fix:
```python
Query: "show me the 5 shortest journeys from IAX airport"
Entities: {
    "departure_airport": "IAX",  # ✅ Correct
    "limit": 5,                  # ✅ Correct
    "sort_order": "ASC"
}
```

## Additional Test Cases

### Test 1: CAI Airport
```
Query: "show me the 5 shortest journeys from CAI airport"
✅ departure_airport: CAI
✅ limit: 5
✅ sort_order: ASC
```

### Test 2: Two Airports (JFK to LAX)
```
Query: "flights from JFK to LAX"
✅ departure_airport: JFK
✅ arrival_airport: LAX
```

### Test 3: MKX Airport with Class Filter
```
Query: "economy class flights from MKX"
✅ departure_airport: MKX
✅ passenger_class: economy
```

### Test 4: Gen Z Query (No False Airport Extraction)
```
Query: "Compare delays for Gen Z passengers flying CAI to JFK"
✅ departure_airport: CAI
✅ arrival_airport: JFK
✅ generation: gen z
❌ NO "GEN" extracted as airport (filtered out)
```

## Impact

With these fixes, the Cypher query filtering system now works correctly:

1. **Airport filtering** - Works with ANY airport in your database
2. **Numeric limits** - Correctly extracts from "the N" patterns
3. **Combined filters** - Supports complex queries like:
   - "the 5 shortest journeys from IAX airport"
   - "top 10 delayed economy flights from MKX to SFX"
   - "business class flights from JFK with longest delays"

## Files Modified

1. **[preprocessing/entity-extractions.py](preprocessing/entity-extractions.py)**
   - Added `AIRPORT_CODE_RE` regex pattern (line 56)
   - Updated `extract_airports_and_route()` function (lines 64-103)
   - Added "the N" pattern to limit extraction (line 199)

---

**System is now ready to handle airport filtering for ALL airports in your database!** ✅
