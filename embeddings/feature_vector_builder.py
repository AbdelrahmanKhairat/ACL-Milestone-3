# embeddings/feature_vector_builder.py

"""
Feature Vector Embeddings Builder - Step 2.b
=============================================
This module implements Feature Vector Embeddings for the airline theme:
1. Converts Journey node properties into text descriptions
2. Generates embeddings using sentence transformer models
3. Stores embeddings in Neo4j vector index
4. Enables semantic similarity search

For airline theme (numerical data):
- Construct text descriptions from Journey properties
- Example: "Journey: Business class, 45 min delay, food score 3, 1200 miles, 2 legs"
- Embed using two models for comparison:
  * all-MiniLM-L6-v2 (384 dim, fast)
  * all-mpnet-base-v2 (768 dim, better quality)
"""

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List, Tuple
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FeatureVectorBuilder:
    """
    Builds feature vector embeddings for Journey nodes.
    """

    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j connection and embedding models.

        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.models = {}

    def load_model(self, model_name: str) -> SentenceTransformer:
        """
        Load a sentence transformer model.

        Args:
            model_name: HuggingFace model name

        Returns:
            Loaded SentenceTransformer model
        """
        if model_name not in self.models:
            print(f"Loading model: {model_name}...")
            self.models[model_name] = SentenceTransformer(model_name)
            print(f"✓ Model loaded: {model_name}")
        return self.models[model_name]

    def journey_to_text(self, journey: Dict[str, Any]) -> str:
        """
        Convert a Journey node's properties into a natural language description.
        ENHANCED VERSION with descriptive words for better semantic matching.

        This is the key function for Feature Vector Embeddings!
        We convert numerical properties into readable, descriptive text.

        Args:
            journey: Dictionary of Journey node properties

        Returns:
            Enhanced text description with descriptive adjectives

        Example:
            Input: {
                "feedback_ID": "123",
                "passenger_class": "Business",
                "food_satisfaction_score": 2,
                "arrival_delay_minutes": 45,
                "actual_flown_miles": 400,
                "number_of_legs": 1
            }
            Output: "BUSINESS CLASS flight: SHORT DISTANCE journey (400 miles, single leg).
                     POOR FOOD quality (2/5). LONG DELAY (45 minutes late arrival).
                     Overall: uncomfortable experience with service issues."
        """
        feedback_id = journey.get("feedback_ID", "unknown")
        passenger_class = journey.get("passenger_class", "Economy")
        food_score = journey.get("food_satisfaction_score", 3)
        delay = journey.get("arrival_delay_minutes", 0)
        miles = journey.get("actual_flown_miles", 0)
        legs = journey.get("number_of_legs", 1)

        # === ENHANCED DESCRIPTIVE MAPPINGS ===

        # 1. Food quality descriptors
        food_descriptors = {
            1: "TERRIBLE FOOD (very poor quality, major complaints)",
            2: "POOR FOOD (low quality, dissatisfied)",
            3: "AVERAGE FOOD (acceptable quality)",
            4: "GOOD FOOD (high quality, satisfied)",
            5: "EXCELLENT FOOD (outstanding quality, very satisfied)"
        }
        food_desc = food_descriptors.get(food_score, "AVERAGE FOOD")

        # 2. Delay descriptors (considering magnitude)
        if delay > 60:
            delay_desc = f"VERY LONG DELAY (extremely late, {delay} minutes delayed)"
            delay_sentiment = "unacceptable delay"
        elif delay > 30:
            delay_desc = f"LONG DELAY (significantly late, {delay} minutes delayed)"
            delay_sentiment = "substantial delay"
        elif delay > 15:
            delay_desc = f"MODERATE DELAY ({delay} minutes late)"
            delay_sentiment = "minor delay"
        elif delay > -15:
            delay_desc = f"ON-TIME arrival ({delay} minutes)"
            delay_sentiment = "punctual"
        elif delay > -30:
            delay_desc = f"EARLY arrival ({abs(delay)} minutes early)"
            delay_sentiment = "ahead of schedule"
        else:
            delay_desc = f"VERY EARLY arrival ({abs(delay)} minutes early)"
            delay_sentiment = "well ahead of schedule"

        # 3. Distance descriptors
        if miles < 500:
            distance_desc = "SHORT DISTANCE"
            distance_type = "short flight"
        elif miles < 1500:
            distance_desc = "MEDIUM DISTANCE"
            distance_type = "regional flight"
        elif miles < 3000:
            distance_desc = "LONG DISTANCE"
            distance_type = "long-haul flight"
        else:
            distance_desc = "VERY LONG DISTANCE"
            distance_type = "international long-haul flight"

        # 4. Leg descriptors
        if legs == 1:
            leg_desc = "DIRECT flight (single leg, no connections)"
            leg_type = "direct"
        elif legs == 2:
            leg_desc = "ONE CONNECTION (2-leg journey)"
            leg_type = "one-stop"
        else:
            leg_desc = f"MULTI-LEG journey ({legs} legs, multiple connections)"
            leg_type = "multi-stop"

        # 5. Class emphasis (uppercase for better matching)
        class_desc = passenger_class.upper() + " CLASS"

        # 6. Overall experience assessment
        # Calculate experience score (lower is worse)
        experience_score = food_score - (abs(delay) / 20) - (legs * 0.5)

        if experience_score < 1.5:
            experience = "UNCOMFORTABLE experience with POOR SERVICE and ISSUES"
        elif experience_score < 2.5:
            experience = "BELOW AVERAGE experience with some dissatisfaction"
        elif experience_score < 3.5:
            experience = "AVERAGE experience, acceptable service"
        elif experience_score < 4.5:
            experience = "COMFORTABLE experience with GOOD SERVICE"
        else:
            experience = "EXCELLENT experience, COMFORTABLE flight, HIGH SATISFACTION"

        # === CONSTRUCT ENHANCED DESCRIPTION ===
        # Format: [CLASS] [DISTANCE] [DETAILS] [FOOD] [DELAY] [OVERALL]

        text = (
            f"{class_desc} flight: {distance_desc} {distance_type} "
            f"({miles} miles, {leg_desc}). "
            f"{food_desc}. {delay_desc}. "
            f"Overall journey: {experience}. "
            f"Journey characteristics: {delay_sentiment}, {leg_type}, "
            f"passenger class {passenger_class.lower()}."
        )

        return text

    def fetch_all_journeys(self) -> List[Dict[str, Any]]:
        """
        Fetch all Journey nodes from Neo4j.

        Returns:
            List of Journey node dictionaries
        """
        query = """
        MATCH (j:Journey)
        RETURN j.feedback_ID as feedback_ID,
               j.passenger_class as passenger_class,
               j.food_satisfaction_score as food_satisfaction_score,
               j.arrival_delay_minutes as arrival_delay_minutes,
               j.actual_flown_miles as actual_flown_miles,
               j.number_of_legs as number_of_legs
        """

        with self.driver.session() as session:
            result = session.run(query)
            journeys = [dict(record) for record in result]

        return journeys

    def generate_embeddings(
        self,
        model_name: str,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using the specified model.

        Args:
            model_name: Name of the model to use
            texts: List of text descriptions

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        model = self.load_model(model_name)
        print(f"Generating embeddings for {len(texts)} texts using {model_name}...")

        # Generate embeddings (returns numpy arrays)
        embeddings = model.encode(texts, show_progress_bar=True)

        # Convert to lists for Neo4j storage
        embeddings_list = [emb.tolist() for emb in embeddings]

        return embeddings_list

    def create_vector_index(self, index_name: str, dimension: int):
        """
        Create a vector index in Neo4j for similarity search.

        Args:
            index_name: Name for the vector index
            dimension: Dimension of the embeddings (384 or 768)
        """
        # Drop existing index if it exists
        drop_query = f"DROP INDEX {index_name} IF EXISTS"

        # Create new vector index
        create_query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (j:Journey)
        ON j.{index_name}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimension},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """

        with self.driver.session() as session:
            session.run(drop_query)
            session.run(create_query)

        print(f"✓ Created vector index: {index_name} (dimension: {dimension})")

    def store_embeddings(
        self,
        journeys: List[Dict[str, Any]],
        embeddings: List[List[float]],
        property_name: str
    ):
        """
        Store embeddings as properties on Journey nodes in Neo4j.
        Uses BATCH updates for much faster performance!

        Args:
            journeys: List of Journey node dictionaries
            embeddings: List of embedding vectors
            property_name: Name of the property to store embeddings under
                          (e.g., "embedding_minilm" or "embedding_mpnet")
        """
        # OPTIMIZED: Use UNWIND for batch updates (100x faster!)
        query = f"""
        UNWIND $batch as row
        MATCH (j:Journey {{feedback_ID: row.feedback_id}})
        SET j.{property_name} = row.embedding
        """

        # Prepare batch data
        batch_data = [
            {
                "feedback_id": journey["feedback_ID"],
                "embedding": embedding
            }
            for journey, embedding in zip(journeys, embeddings)
        ]

        # Process in batches of 500 for optimal performance
        batch_size = 500
        total = len(batch_data)

        with self.driver.session() as session:
            for i in range(0, total, batch_size):
                batch = batch_data[i:i + batch_size]
                session.run(query, {"batch": batch})
                print(f"  Stored {min(i + batch_size, total)}/{total} embeddings...", end="\r")

        print(f"\n✓ Stored {len(embeddings)} embeddings as '{property_name}' property")

    def build_embeddings_for_model(self, model_name: str, property_name: str):
        """
        Complete pipeline to build and store embeddings for one model.

        Args:
            model_name: HuggingFace model name (e.g., "sentence-transformers/all-MiniLM-L6-v2")
            property_name: Property name to store in Neo4j (e.g., "embedding_minilm")
        """
        print(f"\n{'='*80}")
        print(f"Building Feature Vector Embeddings: {model_name}")
        print(f"{'='*80}\n")

        # Step 1: Fetch all journeys
        print("Step 1: Fetching Journey nodes from Neo4j...")
        journeys = self.fetch_all_journeys()
        print(f"✓ Fetched {len(journeys)} Journey nodes\n")

        # Step 2: Convert to text descriptions
        print("Step 2: Converting Journey properties to text descriptions...")
        texts = [self.journey_to_text(journey) for journey in journeys]
        print(f"✓ Created {len(texts)} text descriptions")
        print(f"Example: {texts[0][:100]}...\n")

        # Step 3: Generate embeddings
        print("Step 3: Generating embeddings...")
        embeddings = self.generate_embeddings(model_name, texts)
        embedding_dim = len(embeddings[0])
        print(f"✓ Generated {len(embeddings)} embeddings (dimension: {embedding_dim})\n")

        # Step 4: Create vector index
        print("Step 4: Creating vector index in Neo4j...")
        index_name = property_name
        self.create_vector_index(index_name, embedding_dim)
        print()

        # Step 5: Store embeddings
        print("Step 5: Storing embeddings in Neo4j...")
        self.store_embeddings(journeys, embeddings, property_name)
        print()

        print(f"✓ Successfully built embeddings using {model_name}")
        print(f"  - Stored as property: '{property_name}'")
        print(f"  - Vector index: '{index_name}'")
        print(f"  - Dimension: {embedding_dim}")
        print()

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
# Main Execution
# ==========================================

if __name__ == "__main__":
    """
    Build Feature Vector Embeddings for both models:
    1. all-MiniLM-L6-v2 (384 dimensions)
    2. all-mpnet-base-v2 (768 dimensions)
    """

    print("\n" + "="*80)
    print("FEATURE VECTOR EMBEDDINGS BUILDER - Step 2.b")
    print("="*80 + "\n")

    # Load config
    cfg = load_config()

    # Initialize builder
    builder = FeatureVectorBuilder(
        uri=cfg["URI"],
        username=cfg["USERNAME"],
        password=cfg["PASSWORD"]
    )

    try:
        # Model 1: all-MiniLM-L6-v2 (fast, 384 dim)
        builder.build_embeddings_for_model(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            property_name="embedding_minilm"
        )

        # Model 2: all-mpnet-base-v2 (better quality, 768 dim)
        builder.build_embeddings_for_model(
            model_name="sentence-transformers/all-mpnet-base-v2",
            property_name="embedding_mpnet"
        )

        print("\n" + "="*80)
        print("✅ COMPLETE: Feature Vector Embeddings built for both models!")
        print("="*80)
        print("\nNext steps:")
        print("1. Use embeddings/similarity_search.py to search by similarity")
        print("2. Implement Step 1.c: Input embedding for user queries")
        print("3. Move to Step 3: LLM Layer")
        print()

    finally:
        builder.close()
