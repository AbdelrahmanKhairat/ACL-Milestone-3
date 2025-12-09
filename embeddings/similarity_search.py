# embeddings/similarity_search.py

"""
Similarity Search Module - Step 2.b
====================================
This module implements semantic similarity search using the feature vector embeddings:
1. Embeds user queries using the same models
2. Performs vector similarity search in Neo4j
3. Returns relevant Journey nodes based on semantic similarity

This completes Step 1.c (Input Embedding) and Step 2.b (Embedding-based Retrieval).
"""

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List, Tuple
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SimilaritySearcher:
    """
    Performs semantic similarity search using feature vector embeddings.
    """

    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.models = {}

    def load_model(self, model_name: str) -> SentenceTransformer:
        """
        Load a sentence transformer model for embedding queries.

        Args:
            model_name: HuggingFace model name

        Returns:
            Loaded SentenceTransformer model
        """
        if model_name not in self.models:
            print(f"Loading model: {model_name}...")
            self.models[model_name] = SentenceTransformer(model_name)
        return self.models[model_name]

    def embed_query(self, query: str, model_name: str) -> List[float]:
        """
        Embed a user query using the specified model.

        This is Step 1.c: Input Embedding!

        Args:
            query: User's natural language query
            model_name: Name of the embedding model to use

        Returns:
            Embedding vector as a list of floats
        """
        model = self.load_model(model_name)
        embedding = model.encode(query)
        return embedding.tolist()

    def similarity_search(
        self,
        query_embedding: List[float],
        embedding_property: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search in Neo4j.

        Uses cosine similarity to find the most similar Journey nodes.

        Args:
            query_embedding: The embedded user query
            embedding_property: Name of the embedding property to search
                               (e.g., "embedding_minilm" or "embedding_mpnet")
            top_k: Number of top results to return

        Returns:
            List of Journey nodes with similarity scores
        """
        # Neo4j vector similarity search query
        cypher_query = f"""
        MATCH (j:Journey)
        WHERE j.{embedding_property} IS NOT NULL
        WITH j,
             vector.similarity.cosine(j.{embedding_property}, $query_vector) AS score
        ORDER BY score DESC
        LIMIT $top_k
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs,
               score
        """

        with self.driver.session() as session:
            result = session.run(cypher_query, {
                "query_vector": query_embedding,
                "top_k": top_k
            })
            records = [dict(record) for record in result]

        return records

    def search_by_query(
        self,
        user_query: str,
        model_name: str,
        embedding_property: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Complete pipeline: embed query and search for similar journeys.

        Args:
            user_query: User's natural language query
            model_name: Model to use for embedding
            embedding_property: Property name in Neo4j
            top_k: Number of results to return

        Returns:
            Dictionary with query, embeddings, and results
        """
        # Step 1.c: Embed the user query
        query_embedding = self.embed_query(user_query, model_name)

        # Step 2.b: Perform similarity search
        results = self.similarity_search(query_embedding, embedding_property, top_k)

        return {
            "query": user_query,
            "model": model_name,
            "embedding_property": embedding_property,
            "query_embedding": query_embedding[:5],  # Show first 5 dims
            "results": results,
            "count": len(results)
        }

    def format_results_for_llm(self, search_response: Dict[str, Any]) -> str:
        """
        Format similarity search results into readable text for LLM context.

        Args:
            search_response: Response from search_by_query()

        Returns:
            Formatted string for LLM context
        """
        results = search_response.get("results", [])
        count = search_response.get("count", 0)
        query = search_response.get("query", "")

        if count == 0:
            return "No similar journeys found in the knowledge graph."

        formatted = f"Found {count} similar journeys for query: '{query}'\n\n"

        for i, record in enumerate(results, 1):
            score = record.get("score", 0)
            feedback_id = record.get("feedback_ID", "unknown")
            passenger_class = record.get("passenger_class", "unknown")
            food_score = record.get("food_satisfaction_score", 0)
            delay = record.get("arrival_delay_minutes", 0)
            miles = record.get("actual_flown_miles", 0)
            legs = record.get("number_of_legs", 1)

            formatted += f"Result {i} (similarity: {score:.3f}):\n"
            formatted += f"  - Journey ID: {feedback_id}\n"
            formatted += f"  - Class: {passenger_class}\n"
            formatted += f"  - Food satisfaction: {food_score}/5\n"
            formatted += f"  - Arrival delay: {delay} minutes\n"
            formatted += f"  - Distance: {miles} miles\n"
            formatted += f"  - Legs: {legs}\n\n"

        return formatted.strip()

    def compare_models(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Compare results from both embedding models for the same query.

        Args:
            user_query: User's query
            top_k: Number of results per model

        Returns:
            Dictionary with results from both models
        """
        print(f"\nComparing models for query: '{user_query}'\n")

        # Search with MiniLM
        print("Searching with all-MiniLM-L6-v2...")
        minilm_results = self.search_by_query(
            user_query,
            "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_minilm",
            top_k
        )

        # Search with MPNet
        print("Searching with all-mpnet-base-v2...")
        mpnet_results = self.search_by_query(
            user_query,
            "sentence-transformers/all-mpnet-base-v2",
            "embedding_mpnet",
            top_k
        )

        return {
            "query": user_query,
            "minilm": minilm_results,
            "mpnet": mpnet_results
        }

    def close(self):
        """Close Neo4j driver connection."""
        self.driver.close()


# ==========================================
# Utility Functions
# ==========================================

def load_config(path="config.txt") -> Dict[str, str]:
    """Load Neo4j configuration from config.txt file."""
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
    Demo: Semantic similarity search using both embedding models.
    """

    print("\n" + "="*80)
    print("SIMILARITY SEARCH DEMO - Step 1.c & 2.b")
    print("="*80 + "\n")

    # Load config
    cfg = load_config()

    # Initialize searcher
    searcher = SimilaritySearcher(
        uri=cfg["URI"],
        username=cfg["USERNAME"],
        password=cfg["PASSWORD"]
    )

    # Test queries
    test_queries = [
        "Flights with long delays and poor food quality",
        "Short distance business class journeys",
        "Comfortable flights with good service",
        "Economy class with minimal delays",
        "Multi-leg journeys with satisfaction issues"
    ]

    try:
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"QUERY: {query}")
            print(f"{'='*80}\n")

            # Compare both models
            comparison = searcher.compare_models(query, top_k=3)

            # Display MiniLM results
            print("\n--- Results from all-MiniLM-L6-v2 (384 dim) ---")
            minilm_formatted = searcher.format_results_for_llm(comparison["minilm"])
            print(minilm_formatted)

            # Display MPNet results
            print("\n--- Results from all-mpnet-base-v2 (768 dim) ---")
            mpnet_formatted = searcher.format_results_for_llm(comparison["mpnet"])
            print(mpnet_formatted)

            print("\n" + "-"*80 + "\n")

        print("\n" + "="*80)
        print("✅ Similarity search demo completed!")
        print("="*80)
        print("\nYou can now:")
        print("1. Use these embeddings in your Graph-RAG pipeline")
        print("2. Combine with Cypher query results (Step 2.a)")
        print("3. Move to Step 3: LLM Layer")

    finally:
        searcher.close()
