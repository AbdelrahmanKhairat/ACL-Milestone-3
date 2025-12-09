# llm_layer/graph_rag_pipeline.py

"""
Complete Graph-RAG Pipeline
============================
Integrates all components:
- Step 1: Input Preprocessing (Intent + Entity + Embedding)
- Step 2: Graph Retrieval (Cypher + Embeddings)
- Step 3: LLM Layer (Combine + Prompt + Generate + Evaluate)

This is the main pipeline that answers user questions end-to-end.
"""

import sys
import os
import importlib.util

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from retrieval.query_executor import QueryExecutor, load_config
from embeddings.similarity_search import SimilaritySearcher
from llm_layer.result_combiner import ResultCombiner
from llm_layer.prompt_builder import PromptBuilder
try:
    from llm_layer.llm_integrations_v2 import LLMIntegration
except ImportError:
    from llm_layer.llm_integrations import LLMIntegration


class GraphRAGPipeline:
    """
    End-to-end Graph-RAG pipeline for airline insights.
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        hf_token: Optional[str] = None,
        default_model: str = "qwen",
        embedding_model: str = "mpnet"
    ):
        """
        Initialize the complete pipeline.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_username: Neo4j username
            neo4j_password: Neo4j password
            hf_token: HuggingFace API token (optional)
            default_model: Default LLM model (openai, qwen, llama)
            embedding_model: Embedding model to use (minilm or mpnet)
        """
        # Step 1: Load preprocessing modules
        self._load_preprocessing_modules()

        # Step 2: Initialize graph retrieval
        self.query_executor = QueryExecutor(neo4j_uri, neo4j_username, neo4j_password)
        self.similarity_searcher = SimilaritySearcher(neo4j_uri, neo4j_username, neo4j_password)

        # Step 3: Initialize LLM layer
        self.result_combiner = ResultCombiner()
        self.prompt_builder = PromptBuilder()
        self.llm = LLMIntegration(hf_token=hf_token)

        # Configuration
        self.default_model = default_model
        self.embedding_model = embedding_model
        self.embedding_property = f"embedding_{embedding_model}"

        # Model mapping for embedding models
        self.embedding_model_names = {
            "minilm": "sentence-transformers/all-MiniLM-L6-v2",
            "mpnet": "sentence-transformers/all-mpnet-base-v2"
        }

    def _load_preprocessing_modules(self):
        """Load intent classifier and entity extractor modules."""
        # Load intent_classifier
        spec = importlib.util.spec_from_file_location(
            "intent_classifier",
            "preprocessing/intent-classifier.py"
        )
        intent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(intent_module)
        self.classify_intent = intent_module.classify_intent

        # Load entity_extractions
        spec = importlib.util.spec_from_file_location(
            "entity_extractions",
            "preprocessing/entity-extractions.py"
        )
        entity_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entity_module)
        self.extract_entities = entity_module.extract_entities

    def answer_question(
        self,
        user_query: str,
        model: str = None,
        use_embeddings: bool = True,
        use_cypher: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a user question using the complete Graph-RAG pipeline.

        Args:
            user_query: User's natural language question
            model: LLM model to use (None = use default)
            use_embeddings: Whether to use embedding search
            use_cypher: Whether to use Cypher queries

        Returns:
            Dictionary with answer and all intermediate results
        """
        model = model or self.default_model

        print(f"\n{'='*80}")
        print(f"GRAPH-RAG PIPELINE: {user_query}")
        print(f"{'='*80}\n")

        # === STEP 1: PREPROCESSING ===
        print("[Step 1.a] Classifying intent...")
        intent = self.classify_intent(user_query)
        print(f"  Intent: {intent}")

        print("[Step 1.b] Extracting entities...")
        entities = self.extract_entities(user_query)
        print(f"  Entities: {entities}")

        # === STEP 2: GRAPH RETRIEVAL ===
        cypher_response = None
        embedding_response = None

        if use_cypher:
            print("\n[Step 2.a] Executing Cypher query...")
            cypher_response = self.query_executor.execute_query(intent, entities)
            print(f"  Found {cypher_response['count']} results from Cypher")

        if use_embeddings:
            print("[Step 2.b] Performing semantic similarity search...")
            embedding_model_name = self.embedding_model_names[self.embedding_model]
            embedding_response = self.similarity_searcher.search_by_query(
                user_query,
                embedding_model_name,
                self.embedding_property,
                top_k=5
            )
            print(f"  Found {embedding_response['count']} results from embeddings")

        # === STEP 3: LLM LAYER ===
        print("\n[Step 3.a] Combining results...")
        if cypher_response and embedding_response:
            combined = self.result_combiner.combine_results(cypher_response, embedding_response)
        elif cypher_response:
            combined = {"formatted_context": self.query_executor.format_results_for_llm(cypher_response)}
        elif embedding_response:
            combined = {"formatted_context": self.similarity_searcher.format_results_for_llm(embedding_response)}
        else:
            combined = {"formatted_context": "No data found."}

        print(f"  Combined {combined.get('total_count', 0)} unique results")

        print("[Step 3.b] Building prompt...")
        prompt = self.prompt_builder.build_prompt(
            user_query,
            combined["formatted_context"]
        )

        print(f"[Step 3.c] Querying LLM ({model})...")
        llm_response = self.llm.query_model(prompt, model_key=model)

        if llm_response["success"]:
            print(f"  Response generated in {llm_response['response_time']:.2f}s")
        else:
            print(f"  Error: {llm_response['error']}")

        # === RETURN COMPLETE RESULTS ===
        return {
            "user_query": user_query,
            "intent": intent,
            "entities": entities,
            "cypher_results": cypher_response,
            "embedding_results": embedding_response,
            "combined_context": combined["formatted_context"],
            "prompt": prompt,
            "llm_response": llm_response,
            "answer": llm_response["answer"],
            "success": llm_response["success"]
        }

    def compare_models(self, user_query: str) -> Dict[str, Any]:
        """
        Answer the same question with all 3 LLM models for comparison.

        Args:
            user_query: User's question

        Returns:
            Dictionary with results from all models
        """
        print(f"\n{'='*80}")
        print(f"COMPARING ALL MODELS: {user_query}")
        print(f"{'='*80}\n")

        # Get preprocessing and retrieval once
        intent = self.classify_intent(user_query)
        entities = self.extract_entities(user_query)

        cypher_response = self.query_executor.execute_query(intent, entities)
        embedding_model_name = self.embedding_model_names[self.embedding_model]
        embedding_response = self.similarity_searcher.search_by_query(
            user_query,
            embedding_model_name,
            self.embedding_property,
            top_k=5
        )

        combined = self.result_combiner.combine_results(cypher_response, embedding_response)
        prompt = self.prompt_builder.build_prompt(user_query, combined["formatted_context"])

        # Query all models
        print("Querying all LLM models...")
        all_responses = self.llm.query_all_models(prompt)

        # Format comparison
        comparison = {
            "user_query": user_query,
            "context": combined["formatted_context"],
            "models": all_responses
        }

        # Print comparison
        print("\n" + "="*80)
        print("MODEL COMPARISON RESULTS")
        print("="*80)

        for model_key, response in all_responses.items():
            print(f"\n{'-'*80}")
            print(f"MODEL: {model_key}")
            print(f"{'-'*80}")
            print(f"Response Time: {response['response_time']:.2f}s")
            print(f"Success: {response['success']}")

            if response['success']:
                print(f"\nAnswer:\n{response['answer']}")
            else:
                print(f"\nError: {response['error']}")

        return comparison

    def close(self):
        """Close all connections."""
        self.query_executor.close()
        self.similarity_searcher.close()


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo: Complete Graph-RAG pipeline.
    """
    print("\n" + "="*80)
    print("GRAPH-RAG PIPELINE DEMO - Complete System")
    print("="*80 + "\n")

    # Load configuration
    cfg = load_config()

    # Initialize pipeline
    print("Initializing Graph-RAG pipeline...")
    pipeline = GraphRAGPipeline(
        neo4j_uri=cfg["URI"],
        neo4j_username=cfg["USERNAME"],
        neo4j_password=cfg["PASSWORD"],
        hf_token="your_token",  # Add your token if needed
        default_model="qwen",
        embedding_model="mpnet"  # Use MPNet (better results)
    )

    print("Pipeline ready!\n")

    # Test questions
    test_questions = [
        "Which flights have the longest delays?",
        "Show me journeys with poor food quality",
        "What are the most comfortable flights?"
    ]

    try:
        # Test single question
        print("\n" + "="*80)
        print("TEST 1: Single Question with Default Model")
        print("="*80)

        result = pipeline.answer_question(test_questions[0])

        print("\n" + "-"*80)
        print("FINAL ANSWER:")
        print("-"*80)
        print(result["answer"])
        print()

        # Test model comparison
        print("\n" + "="*80)
        print("TEST 2: Compare All Models")
        print("="*80)

        comparison = pipeline.compare_models(test_questions[1])

        print("\n" + "="*80)
        print("Pipeline demo completed!")
        print("="*80)

    finally:
        pipeline.close()
        print("\nConnections closed.")
