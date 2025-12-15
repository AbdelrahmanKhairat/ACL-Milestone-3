# preprocessing/entity_extractor.py

import re
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import Optional, Dict, Any, Tuple, List

# ----------------------------
# Static vocab (tune as needed)
# ----------------------------

AIRPORT_CODES = ["CAI", "DXB", "JFK", "LHR", "FRA", "AMS", "CDG"]

PASSENGER_CLASS_KEYWORDS = {
    "economy": ["economy", "eco"],
    "business": ["business", "biz"],
    "first": ["first class", "first"],
}

GENERATIONS_MAP = {
    "gen z": "Gen Z",
    "millennial": "Millennial",
    "boomer": "Boomer",
    "gen x": "Gen X",
    "silent": "Silent"
}

FLEET_TYPES = ["A320", "A321", "A330", "A350", "A380", "B737", "B747", "B757", "B767", "B777", "B787"]


# ----------------------------
# Data class for entities
# ----------------------------

@dataclass
class AirlineEntities:
    flight_no: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    route: Optional[str] = None
    passenger_class: Optional[str] = None
    generation: Optional[str] = None
    fleet_type: Optional[str] = None
    date: Optional[str] = None
    # New: Superlatives and comparatives
    sort_order: Optional[str] = None  # "DESC" or "ASC"
    sort_attribute: Optional[str] = None  # "delay", "miles", "food_score", etc.
    limit: Optional[int] = None  # Top N results
    number_of_legs: Optional[int] = None


# ----------------------------
# Low-level extractors
# ----------------------------

# MS985, LH777, BA250, etc.
FLIGHT_RE = re.compile(r"\b([A-Z]{2}\d{2,4})\b", re.IGNORECASE)

# CAI-DXB style route
ROUTE_RE = re.compile(r"\b([A-Z]{3})-([A-Z]{3})\b")

# Any 3-letter uppercase code (airport code pattern)
AIRPORT_CODE_RE = re.compile(r"\b([A-Z]{3})\b")


def extract_flight_number(text: str) -> Optional[str]:
    m = FLIGHT_RE.search(text.upper())
    return m.group(1) if m else None


def extract_airports_and_route(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    ENHANCED: Now detects ANY 3-letter airport code, not just hardcoded list.

    - Detect 'CAI-DXB' style pattern
    - Or detect any 3-letter codes with 'from ... to ...' keywords
    """
    upper = text.upper()
    lower = text.lower()

    # 1) CAI-DXB pattern
    m = ROUTE_RE.search(upper)
    if m:
        dep, arr = m.group(1), m.group(2)
        return dep, arr, f"{dep}-{arr}"

    # 2) Find ALL 3-letter uppercase codes in the text
    all_matches = AIRPORT_CODE_RE.findall(upper)

    # Filter out common words that aren't airports (optional - can expand this list)
    excluded_words = {
        "THE", "AND", "FOR", "ARE", "YOU", "CAN", "ANY", "ALL", "TOP", "ASC", "DESC",
        "GEN", "NEW", "OLD", "BAD", "BIG", "ONE", "TWO", "GET", "GOT", "HAS", "HAD",
        "NOT", "BUT", "YET", "NOW", "HOW", "WHY", "WHO", "WAS", "WEE", "WAY", "LEG"
    }
    codes_found = [code for code in all_matches if code not in excluded_words]

    dep = arr = None

    # Case 1: "from XXX to YYY" - both airports present
    if "from" in lower and "to" in lower and len(codes_found) >= 2:
        dep, arr = codes_found[0], codes_found[1]
    # Case 2: Just two airport codes mentioned (no from/to)
    elif len(codes_found) == 2:
        dep, arr = codes_found[0], codes_found[1]
    # Case 3: "from XXX" only (departure airport)
    elif "from" in lower and len(codes_found) >= 1:
        dep = codes_found[0]
    # Case 4: "to XXX" only (arrival airport)
    elif "to" in lower and len(codes_found) >= 1:
        arr = codes_found[0]

    route = f"{dep}-{arr}" if dep and arr else None
    return dep, arr, route


def extract_passenger_class(text: str) -> Optional[str]:
    lower = text.lower()
    # direct keywords (economy, business, first)
    for norm, kws in PASSENGER_CLASS_KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                return norm
    return None


def extract_generation(text: str) -> Optional[str]:
    lower = text.lower()
    for key, val in GENERATIONS_MAP.items():
        if key in lower:
            return val
    return None


def extract_fleet_type(text: str) -> Optional[str]:
    upper = text.upper()
    for f in FLEET_TYPES:
        if f in upper:
            return f
    return None


def extract_date(text: str) -> Optional[str]:
    lower = text.lower()
    today = date.today()

    if "today" in lower:
        return today.isoformat()
    if "tomorrow" in lower:
        return (today + timedelta(days=1)).isoformat()
    if "next week" in lower:
        return (today + timedelta(days=7)).isoformat()

    # YYYY-MM-DD
    m = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
    if m:
        return m.group(0)

    return None


def extract_number_of_legs(text: str) -> Optional[int]:
    """
    Extract specific number of legs requirements.
    """
    lower = text.lower()
    
    # Direct keywords
    if "non-stop" in lower or "direct" in lower:
        return 1
    
    # "one leg" pattern
    if "one leg" in lower or "1 leg" in lower:
        return 1
    
    # Numeric patterns for legs
    # "2 legs", "3 legs"
    m = re.search(r"\b(\d+)\s+legs?\b", lower)
    if m:
        return int(m.group(1))
        
    return None


def extract_superlatives(text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Extract superlative/comparative keywords to determine sorting and limits.

    Returns:
        Tuple of (sort_order, sort_attribute, limit)
        - sort_order: "DESC" for highest/worst/longest, "ASC" for lowest/best/shortest
        - sort_attribute: "delay", "miles", "food_score", "legs"
        - limit: number of results (e.g., "top 5" → 5)
    """
    lower = text.lower()

    sort_order = None
    sort_attribute = None
    limit = None

    # Superlatives indicating DESC order (highest/worst/longest)
    desc_keywords = [
        "longest", "worst", "most", "highest", "maximum", "max",
        "slowest", "largest", "biggest", "top", "greatest"
    ]

    # Superlatives indicating ASC order (shortest/best/lowest)
    asc_keywords = [
        "shortest", "best", "least", "lowest", "minimum", "min",
        "fastest", "smallest", "bottom", "fewest"
    ]

    # Determine sort order
    if any(word in lower for word in desc_keywords):
        sort_order = "DESC"
    elif any(word in lower for word in asc_keywords):
        sort_order = "ASC"

    # Determine sort attribute based on context
    if any(word in lower for word in ["delay", "late", "punctual", "on time", "arrival"]):
        sort_attribute = "delay"
    elif any(word in lower for word in ["distance", "miles", "far", "long haul", "short haul"]):
        sort_attribute = "miles"
    elif any(word in lower for word in ["food", "meal", "service quality", "satisfaction"]):
        sort_attribute = "food_score"
    elif any(word in lower for word in ["connection", "stop", "leg"]):
        sort_attribute = "legs"

    # Extract numeric limit (e.g., "top 5", "10 flights", "first 3", "the 5 shortest")
    limit_patterns = [
        r"\btop\s+(\d+)\b",
        r"\bfirst\s+(\d+)\b",
        r"\bthe\s+(\d+)\b",  # NEW: handles "the 5 shortest"
        r"\b(\d+)\s+(?:flight|journey|result)",
        r"\blimit\s+(\d+)\b",
    ]

    for pattern in limit_patterns:
        m = re.search(pattern, lower)
        if m:
            limit = int(m.group(1))
            break

    # Default limit if superlative found but no number specified
    if sort_order and not limit:
        limit = 10  # Default top 10

    return sort_order, sort_attribute, limit


# ----------------------------
# Public wrapper
# ----------------------------

def extract_entities(user_input: str) -> Dict[str, Any]:
    flight_no = extract_flight_number(user_input)
    dep, arr, route = extract_airports_and_route(user_input)
    sort_order, sort_attribute, limit = extract_superlatives(user_input)
    legs = extract_number_of_legs(user_input)

    entities = AirlineEntities(
        flight_no=flight_no,
        departure_airport=dep,
        arrival_airport=arr,
        route=route,
        passenger_class=extract_passenger_class(user_input),
        generation=extract_generation(user_input),
        fleet_type=extract_fleet_type(user_input),
        date=extract_date(user_input),
        sort_order=sort_order,
        sort_attribute=sort_attribute,
        limit=limit,
        number_of_legs=legs,
    )

    return asdict(entities)


# ----------------------------
# Manual test
# ----------------------------

if __name__ == "__main__":
    queries = [
        "Show me flights from CAI to DXB tomorrow in economy.",
        "Compare delays for Gen Z passengers flying CAI to JFK.",
        "Which fleet type has the worst delays on the CAI-DXB route?",
        "Complaints from business class passengers on MS985.",
    ]
    for q in queries:
        print("Q:", q)
        print("Entities:", extract_entities(q))
        print("-" * 50)
