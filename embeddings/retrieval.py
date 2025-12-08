from typing import List, Dict, Any

from neo4j_connector import run_query
from embeddings.model_loader import embed_texts, MODEL_CONFIG

DEFAULT_MODEL_KEY = "minilm"


def embed_query(text: str, model_key: str = DEFAULT_MODEL_KEY) -> List[float]:
    """
    Input embedding: convert user text into a vector using the SAME model
    used to build Journey embeddings.
    """
    return embed_texts([text], model_key=model_key)[0]


def semantic_journey_search(
    query_text: str,
    k: int = 10,
    model_key: str = DEFAULT_MODEL_KEY,
) -> List[Dict[str, Any]]:
    """
    Use Neo4j vector index to retrieve top-k similar Journey nodes
    for a given user query.
    """
    query_embedding = embed_query(query_text, model_key=model_key)

    index_name = f"journey_embedding_{model_key}_index"

    cypher = f"""
    CALL db.index.vector.queryNodes(
        '{index_name}', $k, $embedding
    )
    YIELD node, score
    MATCH (node)-[:DEPARTS_FROM]->(dep:Airport)
    MATCH (node)-[:ARRIVES_AT]->(arr:Airport)
    OPTIONAL MATCH (node)-[:ON]->(f:Flight)
    RETURN id(node) AS journey_id,
           score,
           dep.station_code AS from_airport,
           arr.station_code AS to_airport,
           f.flight_number AS flight_number,
           node.arrival_delay_minutes AS delay,
           node.actual_flown_miles AS miles,
           node.number_of_legs AS legs
    ORDER BY score DESC
    LIMIT $k
    """

    params = {"k": k, "embedding": query_embedding}
    return run_query(cypher, params)