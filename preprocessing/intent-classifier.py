# preprocessing/intent_classifier.py

def classify_intent(text: str) -> str:
    """
    Rule-based intent classification for the Airline Graph-RAG system.
    Matches keywords to determine which retrieval strategy to use.
    """

    t = text.lower()

    # --- Delay / performance analysis ---
    delay_keywords = ["delay", "late", "on time", "punctual", "arrival time"]
    if any(word in t for word in delay_keywords):
        return "delay_analysis"

    # --- Flight search (origin → destination) ---
    flight_keywords = ["flight", "flights", "depart", "arrive"]
    if any(word in t for word in flight_keywords) and ("from" in t or "to" in t):
        return "find_flights"

    # --- Airport information ---
    airport_keywords = ["airport", "terminal", "gate", "station"]
    if any(word in t for word in airport_keywords):
        return "airport_info"

    # --- Passenger satisfaction / experience ---
    passenger_keywords = ["rating", "satisfaction", "feedback", "experience", "service quality"]
    if any(word in t for word in passenger_keywords):
        return "passenger_experience"

    # --- Route recommendation ---
    recommendation_keywords = ["recommend", "best route", "fastest", "cheapest", "optimal"]
    if any(word in t for word in recommendation_keywords):
        return "route_recommendation"

    # --- Default fallback ---
    return "general_query"
