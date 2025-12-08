from neo4j_connector import run_query
from embeddings.model_loader import embed_texts, MODEL_CONFIG

MODEL_KEY = "minilm"  # or "e5_base"


def fetch_journeys():
    """
    Pull all journeys with their main features to build text descriptions.
    Adjust property names if they differ.
    """
    query = """
    MATCH (j:Journey)-[:DEPARTS_FROM]->(dep:Airport)
    MATCH (j)-[:ARRIVES_AT]->(arr:Airport)
    OPTIONAL MATCH (p:Passenger)-[:TOOK]->(j)
    OPTIONAL MATCH (j)-[:ON]->(f:Flight)
    RETURN id(j) AS jid,
           dep.station_code AS dep_code,
           arr.station_code AS arr_code,
           j.arrival_delay_minutes AS delay,
           j.actual_flown_miles AS miles,
           j.number_of_legs AS legs,
           p.passenger_class AS passenger_class,
           p.generation AS generation,
           f.fleet_type_description AS fleet_type
    """
    return run_query(query)


def make_description(row: dict) -> str:
    """
    Turn a Journey row into a textual description.
    This is what we embed.
    """
    parts = []
    dep = row.get("dep_code") or "UNKNOWN"
    arr = row.get("arr_code") or "UNKNOWN"

    parts.append(f"Journey from {dep} to {arr}.")

    if row.get("passenger_class"):
        parts.append(f"Passenger class: {row['passenger_class']}.")

    if row.get("generation"):
        parts.append(f"Generation: {row['generation']}.")

    if row.get("fleet_type"):
        parts.append(f"Fleet type: {row['fleet_type']}.")

    delay = row.get("delay")
    if delay is not None:
        parts.append(f"Arrival delay: {delay} minutes.")

    miles = row.get("miles")
    if miles is not None:
        parts.append(f"Flown miles: {miles}.")

    legs = row.get("legs")
    if legs is not None:
        parts.append(f"Number of legs: {legs}.")

    return " ".join(parts)


def store_embeddings(rows, embeddings):
    """
    Write embeddings back to Journey nodes as a list<float> property.
    Also creates a vector index (if not exists).
    """
    dim = MODEL_CONFIG[MODEL_KEY]["dim"]

    # 1) create the vector index (idempotent)
    create_index = f"""
    CREATE VECTOR INDEX journey_embedding_{MODEL_KEY}_index IF NOT EXISTS
    FOR (j:Journey) ON (j.journey_embedding_{MODEL_KEY})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {dim},
        `vector.similarity_function`: "cosine"
      }}
    }}
    """
    run_query(create_index)

    # 2) set embeddings
    # We do it in batches to avoid sending giant parameters
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch_rows = rows[i : i + batch_size]
        batch_embs = embeddings[i : i + batch_size]

        query = """
        UNWIND $batch AS row
        MATCH (j:Journey)
        WHERE id(j) = row.jid
        SET j.journey_embedding_""" + MODEL_KEY + """ = row.embedding
        """
        params = {
            "batch": [
                {"jid": r["jid"], "embedding": e}
                for r, e in zip(batch_rows, batch_embs)
            ]
        }
        run_query(query, params)


def main():
    rows = fetch_journeys()
    print(f"Fetched {len(rows)} journeys")

    descriptions = [make_description(r) for r in rows]
    embeddings = embed_texts(descriptions, model_key=MODEL_KEY)

    print("Storing embeddings in Neo4j…")
    store_embeddings(rows, embeddings)
    print("Done.")


if __name__ == "__main__":
    main()