# test_fixed_pipeline.py
"""
Quick test to see if the Cypher query formatting fix works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_layer.graph_rag_pipeline import GraphRAGPipeline, load_config

# Load config
cfg = load_config()

# Initialize pipeline
print("Initializing Graph-RAG pipeline...")
pipeline = GraphRAGPipeline(
    neo4j_uri=cfg["URI"],
    neo4j_username=cfg["USERNAME"],
    neo4j_password=cfg["PASSWORD"],
    hf_token=os.getenv("HF_TOKEN"),
    default_model="qwen",
    embedding_model="mpnet"
)

print("Pipeline ready!\n")

# Test question
question = "Which flights have the longest delays?"

print(f"Testing with question: '{question}'\n")
print("="*80)

# Answer the question (use only Cypher, no embeddings for this test)
result = pipeline.answer_question(
    question,
    use_embeddings=False,  # Just test Cypher formatting
    use_cypher=True
)

print("\n" + "="*80)
print("FORMATTED CONTEXT (what the LLM sees):")
print("="*80)
print(result["combined_context"][:1000])  # First 1000 chars
print("\n... [showing first 1000 characters]")
print(f"\nTotal context length: {len(result['combined_context'])} characters")

print("\n" + "="*80)
print("FINAL ANSWER:")
print("="*80)
print(result["answer"])

print("\n" + "="*80)
print(f"Success: {result['success']}")
print("="*80)

pipeline.close()
