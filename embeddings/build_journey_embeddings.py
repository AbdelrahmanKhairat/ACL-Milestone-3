import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from neo4j_connector import run_query
from embeddings.model_loader import embed_texts, MODEL_CONFIG


def fetch_journeys():
    """
    Pull all journeys with ALL their properties and related entities.
    Includes: Journey properties, Flight details, Airport codes, Passenger info.
    """
    query = """
    MATCH (p:Passenger)-[:TOOK]->(j:Journey)-[:ON]->(f:Flight)
    MATCH (f)-[:DEPARTS_FROM]->(dep:Airport)
    MATCH (f)-[:ARRIVES_AT]->(arr:Airport)
    RETURN id(j) AS jid,
           j.feedback_ID AS feedback_id,
           j.passenger_class AS passenger_class,
           j.food_satisfaction_score AS food_score,
           j.arrival_delay_minutes AS delay,
           j.actual_flown_miles AS miles,
           j.number_of_legs AS legs,
           dep.station_code AS dep_code,
           arr.station_code AS arr_code,
           f.fleet_type_description AS fleet_type,
           f.flight_number AS flight_number,
           p.generation AS generation,
           p.loyalty_program_level AS loyalty_level,
           p.record_locator AS record_locator
    """
    return run_query(query)


def make_description(row: dict) -> str:
    """
    Turn a Journey row into a comprehensive, semantically-rich textual description.
    Includes ALL Journey properties, related entities, AND descriptive keywords
    for better semantic matching with natural language queries.
    """
    parts = []

    # Route information with descriptive context
    dep = row.get("dep_code") or "UNKNOWN"
    arr = row.get("arr_code") or "UNKNOWN"
    parts.append(f"Flight journey from {dep} airport to {arr} airport.")

    # Passenger class with emphasis
    passenger_class = row.get("passenger_class", "Economy")
    parts.append(f"{passenger_class.upper()} CLASS passenger.")

    # Flight details
    if row.get("flight_number"):
        parts.append(f"Flight {row['flight_number']}.")
    if row.get("fleet_type"):
        parts.append(f"Aircraft type: {row['fleet_type']}.")

    # Passenger demographics
    if row.get("generation"):
        parts.append(f"{row['generation']} generation passenger.")
    if row.get("loyalty_level"):
        parts.append(f"Loyalty program: {row['loyalty_level']} member.")

    # Distance with descriptive categories
    miles = row.get("miles")
    if miles is not None:
        if miles < 500:
            dist_desc = "SHORT DISTANCE regional"
        elif miles < 1500:
            dist_desc = "MEDIUM DISTANCE"
        elif miles < 3000:
            dist_desc = "LONG DISTANCE"
        else:
            dist_desc = "VERY LONG DISTANCE international"
        parts.append(f"{dist_desc} flight ({miles} miles).")

    # Number of legs with descriptive terms
    legs = row.get("legs")
    if legs is not None:
        if legs == 1:
            parts.append("DIRECT FLIGHT with no connections.")
        elif legs == 2:
            parts.append("ONE-STOP flight with one connection.")
        else:
            parts.append(f"MULTI-LEG journey with {legs} connections.")

    # Food satisfaction with descriptive quality indicators
    food = row.get("food_score")
    if food is not None:
        if food == 1:
            food_desc = "TERRIBLE FOOD quality, very poor service, major complaints"
        elif food == 2:
            food_desc = "POOR FOOD quality, low satisfaction, dissatisfied passengers"
        elif food == 3:
            food_desc = "AVERAGE FOOD quality, acceptable service"
        elif food == 4:
            food_desc = "GOOD FOOD quality, high satisfaction, pleased passengers"
        else:  # 5
            food_desc = "EXCELLENT FOOD quality, outstanding service, very satisfied passengers"
        parts.append(f"{food_desc} (score: {food}/5).")

    # Arrival delay with descriptive severity
    delay = row.get("delay")
    if delay is not None:
        if delay > 60:
            delay_desc = "VERY LONG DELAY, extremely late arrival, significant disruption"
        elif delay > 30:
            delay_desc = "LONG DELAY, substantial lateness, frustrated passengers"
        elif delay > 15:
            delay_desc = "MODERATE DELAY, minor lateness"
        elif delay > -15:
            delay_desc = "ON-TIME arrival, punctual flight"
        elif delay > -30:
            delay_desc = "EARLY arrival, ahead of schedule"
        else:
            delay_desc = "VERY EARLY arrival, well ahead of schedule"
        parts.append(f"{delay_desc} ({delay} minutes).")

    # Overall experience summary based on metrics
    if food is not None and delay is not None:
        # Calculate overall sentiment
        experience_score = food - (abs(delay) / 20)
        if legs and legs > 1:
            experience_score -= 0.5

        if experience_score < 1.5:
            parts.append("Overall: UNCOMFORTABLE experience, POOR SERVICE, dissatisfied passenger with complaints.")
        elif experience_score < 2.5:
            parts.append("Overall: BELOW AVERAGE experience, some service issues and dissatisfaction.")
        elif experience_score < 3.5:
            parts.append("Overall: AVERAGE experience, acceptable journey with standard service.")
        elif experience_score < 4.5:
            parts.append("Overall: COMFORTABLE experience, GOOD SERVICE, satisfied passenger.")
        else:
            parts.append("Overall: EXCELLENT experience, OUTSTANDING SERVICE, very satisfied and comfortable passenger.")

    return " ".join(parts)


def store_embeddings(rows, embeddings, model_key):
    """
    Write embeddings back to Journey nodes as a list<float> property.
    Also creates a vector index (if not exists).

    Args:
        rows: List of journey data dictionaries
        embeddings: List of embedding vectors
        model_key: Model identifier (e.g., "minilm", "mpnet")
    """
    dim = MODEL_CONFIG[model_key]["dim"]

    # Property name should match what similarity_search.py expects: "embedding_minilm" or "embedding_mpnet"
    property_name = f"embedding_{model_key}"

    # 1) create the vector index (idempotent)
    create_index = f"""
    CREATE VECTOR INDEX {property_name}_index IF NOT EXISTS
    FOR (j:Journey) ON (j.{property_name})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {dim},
        `vector.similarity_function`: "cosine"
      }}
    }}
    """
    run_query(create_index)
    print(f"✓ Created vector index: {property_name}_index (dimension: {dim})")

    # 2) set embeddings
    # We do it in batches to avoid sending giant parameters
    batch_size = 500
    total = len(rows)
    for i in range(0, total, batch_size):
        batch_rows = rows[i : i + batch_size]
        batch_embs = embeddings[i : i + batch_size]

        query = f"""
        UNWIND $batch AS row
        MATCH (j:Journey)
        WHERE id(j) = row.jid
        SET j.{property_name} = row.embedding
        """
        params = {
            "batch": [
                {"jid": r["jid"], "embedding": e}
                for r, e in zip(batch_rows, batch_embs)
            ]
        }
        run_query(query, params)
        print(f"  Stored {min(i + batch_size, total)}/{total} embeddings...", end="\r")

    print(f"\n✓ Stored {len(embeddings)} embeddings as '{property_name}' property")


def build_for_model(rows, descriptions, model_key):
    """
    Build and store embeddings for a specific model.

    Args:
        rows: Journey data rows
        descriptions: Text descriptions for each journey
        model_key: Model identifier ("minilm" or "mpnet")
    """
    print(f"\n{'='*80}")
    print(f"Building embeddings with {model_key.upper()} model")
    print(f"Model: {MODEL_CONFIG[model_key]['hf_name']}")
    print(f"Dimension: {MODEL_CONFIG[model_key]['dim']}")
    print(f"{'='*80}\n")

    print(f"Generating embeddings for {len(descriptions)} journeys...")
    embeddings = embed_texts(descriptions, model_key=model_key)
    print(f"✓ Generated {len(embeddings)} embeddings\n")

    print("Storing embeddings in Neo4j...")
    store_embeddings(rows, embeddings, model_key)

    print(f"\n✅ Completed building embeddings for {model_key}")


def main():
    """
    Build comprehensive Journey embeddings for both MiniLM and MPNet models.
    Embeddings include ALL Journey properties and related entities (Flight, Airport, Passenger).
    """
    print("\n" + "="*80)
    print("JOURNEY EMBEDDINGS BUILDER - Enhanced with Complete Context")
    print("="*80 + "\n")

    print("Step 1: Fetching journeys with ALL properties and relationships...")
    rows = fetch_journeys()
    print(f"✓ Fetched {len(rows)} journeys\n")

    print("Step 2: Creating comprehensive text descriptions...")
    descriptions = [make_description(r) for r in rows]
    print(f"✓ Created {len(descriptions)} descriptions")
    print(f"\nExample description:")
    print(f"  {descriptions[0]}\n")

    # Build embeddings for both models
    build_for_model(rows, descriptions, "minilm")
    build_for_model(rows, descriptions, "mpnet")

    print("\n" + "="*80)
    print("✅ COMPLETE: Built embeddings for both models!")
    print("="*80)
    print("\nEmbeddings now include:")
    print("  • ALL Journey properties (delay, miles, legs, food score, class)")
    print("  • Airport codes (departure/arrival)")
    print("  • Flight details (number, fleet type)")
    print("  • Passenger info (generation, loyalty level, record locator)")
    print("\nThis enables better semantic matching for queries like:")
    print("  - 'flights from JFK with delays'")
    print("  - 'Gen Z economy flights with poor service'")
    print("  - 'business class Boeing 787 long-haul flights'")
    print()


if __name__ == "__main__":
    main()