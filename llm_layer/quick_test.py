# llm_layer/quick_test.py
"""
Quick Pipeline Test
===================
Tests a few questions quickly and shows the logs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_layer.graph_rag_pipeline import GraphRAGPipeline, load_config


def quick_test(model_name: str = "qwen"):
    """
    Quick test of the pipeline with detailed output.

    Args:
        model_name: LLM model to use (openai, qwen, llama)
    """
    # Load config
    cfg = load_config()

    # Initialize pipeline
    print(f"\n{'='*80}")
    print(f"QUICK PIPELINE TEST - MODEL: {model_name.upper()}")
    print(f"{'='*80}\n")

    pipeline = GraphRAGPipeline(
        neo4j_uri=cfg["URI"],
        neo4j_username=cfg["USERNAME"],
        neo4j_password=cfg["PASSWORD"],
        hf_token="your_token",
        default_model=model_name,
        embedding_model="mpnet"
    )

    # Test questions
    questions = [
        "Which flights have the longest delays?",
        "Show me flights from CAI to DXB",
        "Which flights have poor passenger experience?"
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"QUESTION {i}/{len(questions)}: {question}")
        print(f"{'='*80}\n")

        # Run pipeline
        result = pipeline.answer_question(question, model=model_name)

        # Display detailed results
        print(f"\n{'─'*80}")
        print("RETRIEVAL RESULTS:")
        print(f"{'─'*80}")

        cypher_count = result.get("cypher_results", {}).get("count", 0) if result.get("cypher_results") else 0
        embedding_count = result.get("embedding_results", {}).get("count", 0) if result.get("embedding_results") else 0

        print(f"  Cypher Query: {cypher_count} results")
        print(f"  Embeddings:   {embedding_count} results")

        print(f"\n{'─'*80}")
        print("CONTEXT SENT TO LLM:")
        print(f"{'─'*80}")
        context = result.get("combined_context", "")
        print(f"  Length: {len(context)} characters")
        print(f"\n  First 500 characters:")
        print(f"  {context[:500]}...")

        print(f"\n{'─'*80}")
        print("PROMPT SENT TO LLM:")
        print(f"{'─'*80}")
        prompt = result.get("prompt", "")
        print(f"  Length: {len(prompt)} characters")
        print(f"\n  First 800 characters:")
        print(f"  {prompt[:800]}...")

        print(f"\n{'─'*80}")
        print("LLM RESPONSE:")
        print(f"{'─'*80}")
        print(f"  Success: {result.get('success')}")
        print(f"  Response Time: {result.get('llm_response', {}).get('response_time', 0):.2f}s")
        print(f"\n  Answer:\n  {result.get('answer', 'No answer')}")

        print(f"\n{'='*80}\n")

    pipeline.close()

    print(f"\n[OK] Quick test complete!\n")


if __name__ == "__main__":
    import sys

    # Get model from command line or use default
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen"

    if model not in ["openai", "qwen", "llama"]:
        print(f"Unknown model: {model}")
        print("Available models: openai, qwen, llama")
        sys.exit(1)

    quick_test(model)
