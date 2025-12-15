# preprocessing/intent_classifier.py

def classify_intent(text: str) -> str:
    """
    Enhanced rule-based intent classification for the Airline Graph-RAG system.
    Matches keywords to determine which retrieval strategy to use.
    Now includes specific sub-intents for better query handling.
    """

    t = text.lower()

    # --- Statistical / Aggregation queries ---
    if any(word in t for word in ["average", "mean", "count", "how many", "total", "percentage", "statistics", "stats"]):
        return "calculate_statistic"

    # --- Most delayed flights (superlative: longest/worst delays) ---
    if any(word in t for word in ["longest", "worst", "most delayed", "maximum delay"]):
        if any(word in t for word in ["delay", "late"]):
            return "most_delayed_flights"
        
        # Handle "longest flights" (distance)
        if "longest" in t and any(word in t for word in ["journey", "flight", "route", "distance"]):
            return "longest_journeys"

    # --- Shortest/best flights (distance or time) ---
    if any(word in t for word in ["shortest", "fastest", "quickest", "nearest"]):
        if any(word in t for word in ["journey", "flight", "route", "distance"]):
            return "shortest_journeys"

    # --- Multi-leg journeys ---
    if any(word in t for word in ["multi-leg", "connection", "stop", "layover", "indirect"]):
        return "multi_leg_flights"

    # --- Loyalty/passenger-based analysis ---
    if any(word in t for word in ["loyalty", "frequent flyer", "member", "tier"]):
        return "loyalty_analysis"

    # --- General delay analysis ---
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
    passenger_keywords = ["rating", "satisfaction", "feedback", "experience", "service quality", "food", "meal"]
    if any(word in t for word in passenger_keywords):
        return "passenger_experience"

    # --- Route recommendation ---
    recommendation_keywords = ["recommend", "best route", "optimal"]
    if any(word in t for word in recommendation_keywords):
        return "route_recommendation"

    # --- General flight query (catch-all for "flights", "journeys") ---
    if any(word in t for word in ["flight", "flights", "journey", "journeys"]):
        return "general_query"

    # --- Default fallback ---
    return "general_query"
