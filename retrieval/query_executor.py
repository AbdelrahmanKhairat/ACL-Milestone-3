# retrieval/query_executor.py

"""
Query Executor Module - Step 2.a Point 3
==========================================
This module completes the baseline retrieval by:
1. Taking the classified intent from intent_classifier.py
2. Taking the extracted entities from entity_extractor.py
3. Selecting the appropriate Cypher query from cypher_queries.py
4. Filling in parameters with extracted entities
5. Executing the query against Neo4j
6. Returning structured results
"""

from neo4j import GraphDatabase
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.cypher_queries import QUERIES


class QueryExecutor:
    """
    Executes Cypher queries against Neo4j using classified intents and extracted entities.
    """

    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.uri = uri

    def execute_query(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution function for Step 2.a Point 3.

        This function:
        1. Selects the Cypher query based on intent
        2. Maps entities to query parameters
        3. Executes the query against Neo4j
        4. Returns structured results

        Args:
            intent: The classified intent (e.g., "find_flights", "delay_analysis")
            entities: Dictionary of extracted entities from user input

        Returns:
            Dictionary containing:
                - "intent": The intent used
                - "query": The Cypher query executed
                - "params": The parameters passed to the query
                - "results": List of result records
                - "count": Number of results returned
        """
        # Step 1: Get the appropriate Cypher query template
        query_template = QUERIES.get(intent, QUERIES["general_query"])

        # Step 2: Map entities to parameters required by the query
        params = self._map_entities_to_params(intent, entities)

        # Step 3: Execute the query
        try:
            with self.driver.session() as session:
                result = session.run(query_template, params)
                records = self._process_results(result)

            # Step 4: Return structured response
            return {
                "intent": intent,
                "query": query_template.strip(),
                "params": params,
                "results": records,
                "count": len(records)
            }

        except Exception as e:
            return {
                "intent": intent,
                "query": query_template.strip(),
                "params": params,
                "error": str(e),
                "results": [],
                "count": 0
            }

    def _map_entities_to_params(self, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps extracted entities to the parameters expected by each Cypher query.

        ALL queries now support optional filtering based on extracted entities:
        - from_airport, to_airport: Filter by departure/arrival airports
        - passenger_class: Filter by passenger class (economy, business, first)
        - generation: Filter by passenger generation
        - limit: Dynamic limit from extracted entities (or default 20)

        Args:
            intent: The classified intent
            entities: Dictionary of extracted entities

        Returns:
            Dictionary of parameters for the Cypher query
        """
        # Build common parameters for all queries
        params = {
            "from_airport": entities.get("departure_airport"),
            "to_airport": entities.get("arrival_airport"),
            "passenger_class": entities.get("passenger_class"),
            "generation": entities.get("generation"),
            "number_of_legs": entities.get("number_of_legs"),
            "limit": entities.get("limit") or 20  # Use extracted limit or default to 20
        }

        # For airport_info intent, set station_code parameter
        if intent == "airport_info":
            # Use departure airport if available, otherwise arrival airport
            params["station_code"] = (
                entities.get("departure_airport") or
                entities.get("arrival_airport")
            )

        return params

    def _process_results(self, result) -> List[Dict[str, Any]]:
        """
        Processes Neo4j result records into serializable dictionaries.

        Converts Neo4j node/relationship objects into plain dictionaries
        for easier use in the LLM layer.

        Args:
            result: Neo4j result object

        Returns:
            List of dictionaries containing node properties
        """
        records = []

        for record in result:
            record_dict = {}

            # Extract each key-value pair from the record
            for key, value in record.items():
                # If value is a Neo4j Node, extract its properties
                if hasattr(value, 'items'):  # Node or dict-like object
                    record_dict[key] = dict(value)
                elif hasattr(value, '__iter__') and not isinstance(value, str):
                    # Handle lists of nodes
                    record_dict[key] = [dict(item) if hasattr(item, 'items') else item for item in value]
                else:
                    record_dict[key] = value

            records.append(record_dict)

        return records

    def format_results_for_llm(self, query_response: Dict[str, Any]) -> str:
        """
        Formats query results into a readable text format for the LLM context.

        NOW UPDATED: Handles the new flat property format from enhanced Cypher queries.
        All queries now return 13 standard properties instead of Node objects.

        Args:
            query_response: The response from execute_query()

        Returns:
            Formatted string suitable for LLM context
        """
        if query_response.get("error"):
            return f"Error executing query: {query_response['error']}"

        results = query_response.get("results", [])
        count = query_response.get("count", 0)
        intent = query_response.get("intent", "unknown")

        if count == 0:
            return "No results found in the knowledge graph for this query."

        # Special handling for statistical queries
        if intent == "calculate_statistic":
            record = results[0]
            total = record.get("total_journeys", 0)
            avg_delay = record.get("avg_delay", 0)
            avg_food = record.get("avg_food_score", 0)
            avg_dist = record.get("avg_distance", 0)
            min_delay = record.get("min_delay", 0)
            max_delay = record.get("max_delay", 0)

            return (
                f"Statistical Analysis:\n"
                f"Total Journeys: {total}\n"
                f"Average Delay: {avg_delay:.2f} minutes\n"
                f"Average Food Satisfaction: {avg_food:.2f}/5\n"
                f"Average Distance: {avg_dist:.2f} miles\n"
                f"Delay Range: {min_delay} to {max_delay} minutes\n"
            )

        formatted = f"Found {count} result(s) for {intent}:\n\n"

        for i, record in enumerate(results, 1):
            # Extract all properties (now flat, not nested in nodes)
            feedback_id = record.get("feedback_ID", "unknown")
            passenger_class = record.get("passenger_class", "Unknown")
            food_score = record.get("food_satisfaction_score", "N/A")
            delay = record.get("arrival_delay_minutes", "N/A")
            miles = record.get("actual_flown_miles", "N/A")
            legs = record.get("number_of_legs", "N/A")

            # Flight information
            flight_number = record.get("flight_number", "N/A")
            fleet_type = record.get("fleet_type", "N/A")

            # Airport information
            dep_airport = record.get("departure_airport", "N/A")
            arr_airport = record.get("arrival_airport", "N/A")

            # Passenger information
            generation = record.get("generation", "N/A")
            loyalty = record.get("loyalty_level", "N/A")
            record_locator = record.get("record_locator", "N/A")

            formatted += f"Result {i}:\n"
            formatted += f"Journey ID: {feedback_id}\n"
            formatted += f"Passenger Class: {passenger_class}\n"
            formatted += f"Food Satisfaction: {food_score}/5\n"
            formatted += f"Arrival Delay: {delay} minutes\n"
            formatted += f"Distance: {miles} miles\n"
            formatted += f"Number of Legs: {legs}\n"
            formatted += f"Flight: {flight_number} ({fleet_type})\n"
            formatted += f"Route: {dep_airport} → {arr_airport}\n"
            formatted += f"Passenger: {generation}, {loyalty} loyalty (Locator: {record_locator})\n"
            formatted += "\n"

        return formatted.strip()

    def _format_node(self, node_props: Dict[str, Any]) -> str:
        """
        Formats a single node's properties into a readable string.

        Args:
            node_props: Dictionary of node properties

        Returns:
            Formatted string of key-value pairs
        """
        # Filter out None values AND embedding properties (they're too large for LLM context!)
        props = {k: v for k, v in node_props.items()
                 if v is not None and not k.startswith('embedding_')}
        return ", ".join([f"{k}={v}" for k, v in props.items()])

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()


# ==========================================
# Utility Functions
# ==========================================

def load_config(path="config.txt") -> Dict[str, str]:
    """
    Load Neo4j configuration from config.txt file.

    Args:
        path: Path to config file

    Returns:
        Dictionary of configuration values
    """
    config = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo showing how to use QueryExecutor with intent classification and entity extraction.
    """

    # Import preprocessing modules
    import importlib.util

    # Load intent_classifier
    spec = importlib.util.spec_from_file_location("intent_classifier", "preprocessing/intent-classifier.py")
    intent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intent_module)
    classify_intent = intent_module.classify_intent

    # Load entity_extractions
    spec = importlib.util.spec_from_file_location("entity_extractions", "preprocessing/entity-extractions.py")
    entity_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entity_module)
    extract_entities = entity_module.extract_entities

    # Load Neo4j config
    cfg = load_config()

    # Initialize executor
    executor = QueryExecutor(
        uri=cfg["URI"],
        username=cfg["USERNAME"],
        password=cfg["PASSWORD"]
    )

    # Test queries
    test_queries = [
        "Show me flights from CAI to DXB",
        "Which flights have the longest delays?",
        "Tell me about passenger satisfaction on business class",
        "What are the shortest journeys?",
        "Show me information about airport ORD",
    ]

    print("=" * 80)
    print("QUERY EXECUTOR DEMO - Step 2.a Point 3")
    print("=" * 80)

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"USER QUERY: {query}")
        print(f"{'='*80}")

        # Step 1.a: Classify intent
        intent = classify_intent(query)
        print(f"\n[1.a] CLASSIFIED INTENT: {intent}")

        # Step 1.b: Extract entities
        entities = extract_entities(query)
        print(f"\n[1.b] EXTRACTED ENTITIES: {entities}")

        # Step 2.a Point 3: Execute query (THIS IS THE NEW PART!)
        response = executor.execute_query(intent, entities)
        print(f"\n[2.a.3] QUERY EXECUTED:")
        print(f"  - Results found: {response['count']}")
        print(f"  - Parameters used: {response['params']}")

        # Format for LLM
        llm_context = executor.format_results_for_llm(response)
        print(f"\n[FOR LLM CONTEXT]:\n{llm_context[:500]}...")  # Show first 500 chars

        print("\n")

    # Clean up
    executor.close()
    print("\n" + "=" * 80)
    print("Demo completed!")
    print("=" * 80)
