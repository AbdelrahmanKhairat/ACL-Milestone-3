# test_entity_query_integration.py

"""
Test Entity Extraction and Query Integration
==============================================
Tests how well the system handles different types of questions.
"""

import sys
import importlib.util

# Load modules
spec = importlib.util.spec_from_file_location("intent_classifier", "preprocessing/intent-classifier.py")
intent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent_module)
classify_intent = intent_module.classify_intent

spec = importlib.util.spec_from_file_location("entity_extractions", "preprocessing/entity-extractions.py")
entity_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entity_module)
extract_entities = entity_module.extract_entities

from retrieval.cypher_queries import QUERIES


def test_question(question: str):
    """Test a single question through the preprocessing pipeline."""
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}")

    # Step 1: Intent Classification
    intent = classify_intent(question)
    print(f"\n[OK] Intent: {intent}")

    # Step 2: Entity Extraction
    entities = extract_entities(question)
    print(f"\n[OK] Entities Extracted:")
    for key, value in entities.items():
        if value is not None:
            print(f"  - {key}: {value}")

    # Step 3: Check if query exists
    if intent in QUERIES:
        print(f"\n[OK] Cypher Query Available: YES")
        query = QUERIES[intent]

        # Check if query uses the extracted entities
        query_lower = query.lower()
        uses_entities = []

        if "$from_airport" in query or "$to_airport" in query:
            uses_entities.append("airports")
        if "$station_code" in query:
            uses_entities.append("station_code")

        if uses_entities:
            print(f"  Query expects: {', '.join(uses_entities)}")

            # Check if we extracted what the query needs
            if "airports" in uses_entities:
                if entities["departure_airport"] or entities["arrival_airport"]:
                    print(f"  [OK] Required entities FOUND")
                else:
                    print(f"  [WARNING] Query needs airports but none extracted!")
        else:
            print(f"  Query doesn't require specific entities (uses ORDER BY/LIMIT)")
    else:
        print(f"\n[WARNING] No Cypher Query for intent: {intent}")

    # Step 4: Assessment
    print(f"\n[ASSESSMENT]:")

    issues = []

    # Check intent accuracy
    if "delay" in question.lower() and intent != "delay_analysis":
        issues.append("Intent mismatch: Question about delays but intent is " + intent)
    if ("flight" in question.lower() or "route" in question.lower()) and ("from" in question.lower() or "to" in question.lower()) and intent != "find_flights":
        issues.append("Intent mismatch: Question about specific flights but intent is " + intent)
    if "airport" in question.lower() and intent != "airport_info":
        issues.append("Intent mismatch: Question about airports but intent is " + intent)
    if ("satisfaction" in question.lower() or "experience" in question.lower() or "service" in question.lower()) and intent != "passenger_experience":
        issues.append("Intent mismatch: Question about experience but intent is " + intent)

    # Check entity extraction
    if ("from" in question.lower() or "to" in question.lower()) and not (entities["departure_airport"] or entities["arrival_airport"]):
        issues.append("Entity extraction issue: Question mentions from/to but no airports extracted")

    if issues:
        print(f"  [ISSUES FOUND]:")
        for issue in issues:
            print(f"    - {issue}")
        return "NEEDS IMPROVEMENT"
    else:
        print(f"  [OK] Working well!")
        return "GOOD"


# ==========================================
# Test Cases
# ==========================================

print("\n" + "="*80)
print("ENTITY EXTRACTION & QUERY INTEGRATION TEST")
print("="*80)

test_cases = [
    # Category 1: Delay Questions
    ("Category: Delay Questions", [
        "Which flights have the longest delays?",
        "Show me flights with delays from ORD",
        "What flights are late from Cairo to Dubai?",
        "Flights delayed more than 1 hour",
    ]),

    # Category 2: Route/Flight Search
    ("Category: Flight Search", [
        "Show me flights from CAI to DXB",
        "Find flights from London to Paris",
        "What flights go from JFK to FRA?",
        "Flights between New York and Frankfurt",
    ]),

    # Category 3: Airport Information
    ("Category: Airport Questions", [
        "Tell me about ORD airport",
        "Information on Cairo airport",
        "What do you know about JFK?",
        "Details on CAI airport",
    ]),

    # Category 4: Passenger Experience
    ("Category: Passenger Experience", [
        "Which flights have poor passenger experience?",
        "Show me flights with bad service",
        "Flights with low satisfaction scores",
        "Which routes have unhappy passengers?",
    ]),

    # Category 5: Recommendations
    ("Category: Recommendations", [
        "Recommend a good flight route",
        "Best flights from Cairo?",
        "Fastest route to London",
        "Which flights should I take?",
    ]),

    # Category 6: Complex/Multi-entity
    ("Category: Complex Questions", [
        "Business class flights from ORD with delays",
        "Economy passengers on CAI-DXB route with poor food",
        "Gen Z travelers experiencing delays",
        "A320 flights with long delays",
    ]),

    # Category 7: Vague/General
    ("Category: General Questions", [
        "Tell me about flights",
        "What data do you have?",
        "Show me airline information",
        "Help me find a flight",
    ]),
]

results = {"GOOD": 0, "NEEDS IMPROVEMENT": 0}

for category, questions in test_cases:
    print(f"\n\n{'#'*80}")
    print(f"# {category}")
    print(f"{'#'*80}")

    for question in questions:
        result = test_question(question)
        results[result] += 1

# Summary
print(f"\n\n{'='*80}")
print("FINAL SUMMARY")
print(f"{'='*80}")
print(f"\nTotal questions tested: {results['GOOD'] + results['NEEDS IMPROVEMENT']}")
print(f"[OK] Working well: {results['GOOD']}")
print(f"[WARNING] Needs improvement: {results['NEEDS IMPROVEMENT']}")

percentage = (results['GOOD'] / (results['GOOD'] + results['NEEDS IMPROVEMENT'])) * 100
print(f"\nSuccess Rate: {percentage:.1f}%")

if percentage >= 80:
    print("\n[SUCCESS] OVERALL: GOOD - System handles most question types well!")
elif percentage >= 60:
    print("\n[WARNING] OVERALL: FAIR - System works but has some gaps")
else:
    print("\n[ERROR] OVERALL: NEEDS WORK - Significant improvements needed")

print("\n" + "="*80)
