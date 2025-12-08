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

GENERATIONS = ["gen z", "millennial", "boomer"]

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


# ----------------------------
# Low-level extractors
# ----------------------------

# MS985, LH777, BA250, etc.
FLIGHT_RE = re.compile(r"\b([A-Z]{2}\d{2,4})\b", re.IGNORECASE)

# CAI-DXB style route
ROUTE_RE = re.compile(r"\b([A-Z]{3})-([A-Z]{3})\b")


def extract_flight_number(text: str) -> Optional[str]:
    m = FLIGHT_RE.search(text.upper())
    return m.group(1) if m else None


def extract_airports_and_route(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    - Detect 'CAI-DXB' style pattern
    - Or detect CAI / DXB from AIRPORT_CODES and use 'from ... to ...' if present
    """
    upper = text.upper()
    lower = text.lower()

    # 1) CAI-DXB pattern
    m = ROUTE_RE.search(upper)
    if m:
        dep, arr = m.group(1), m.group(2)
        return dep, arr, f"{dep}-{arr}"

    # 2) From AIRPORT_CODES
    codes_found: List[str] = []
    for code in AIRPORT_CODES:
        if code in upper:
            codes_found.append(code)

    dep = arr = None
    if "from" in lower and "to" in lower and len(codes_found) >= 2:
        dep, arr = codes_found[0], codes_found[1]
    elif len(codes_found) == 2:
        dep, arr = codes_found[0], codes_found[1]

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
    for g in GENERATIONS:
        if g in lower:
            return g
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


# ----------------------------
# Public wrapper
# ----------------------------

def extract_entities(user_input: str) -> Dict[str, Any]:
    flight_no = extract_flight_number(user_input)
    dep, arr, route = extract_airports_and_route(user_input)

    entities = AirlineEntities(
        flight_no=flight_no,
        departure_airport=dep,
        arrival_airport=arr,
        route=route,
        passenger_class=extract_passenger_class(user_input),
        generation=extract_generation(user_input),
        fleet_type=extract_fleet_type(user_input),
        date=extract_date(user_input),
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
