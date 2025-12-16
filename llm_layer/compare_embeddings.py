# llm_layer/compare_embeddings.py
"""
Embedding Model Comparison Script - Semantic Search Only
========================================================
Compares 'minilm' and 'mpnet' embedding models by running 8 test questions.
Measures similarity scores, execution time, and retrieved content relevance.
Does NOT use an LLM for generation.
"""

import os
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.query_executor import load_config
from embeddings.similarity_search import SimilaritySearcher

# Test Dataset: 8 Questions
TEST_QUESTIONS = [
    # Simple Retrieval
    "Which flights have the longest delays?",
    "Show me the 5 shortest journeys",
    "Find economy class flights from JFK to LAX",
    
    # Semantic Search
    "Flights with terrible food and poor service",
    "What are the most comfortable flights?",
    "Show me journeys with good food but long delays",
    
    # Complex/Multi-hop
    "Best business class routes with minimal delays",
    "Gold loyalty members on long-haul flights"
]

EMBEDDING_MODELS = {
    "minilm": {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "property": "embedding_minilm"
    },
    "mpnet": {
        "name": "sentence-transformers/all-mpnet-base-v2",
        "property": "embedding_mpnet"
    }
}

def run_comparison():
    """Run the embedding comparison suite."""
    print("\n" + "=" * 80)
    print("STARTING EMBEDDING MODEL COMPARISON SUITE")
    print("=" * 80)
    print(f"Models: {list(EMBEDDING_MODELS.keys())}")
    print(f"Questions: {len(TEST_QUESTIONS)}")
    print("-" * 80)

    # Load Config
    cfg = load_config()
    
    # Initialize Searcher
    print("Initializing Similarity Searcher...")
    try:
        searcher = SimilaritySearcher(
            uri=cfg["URI"],
            username=cfg["USERNAME"],
            password=cfg["PASSWORD"]
        )
    except Exception as e:
        print(f"Failed to initialize searcher: {e}")
        return

    results = {model: [] for model in EMBEDDING_MODELS}
    
    # Run Tests
    for q_idx, question in enumerate(TEST_QUESTIONS):
        print(f"\n[Question {q_idx+1}/{len(TEST_QUESTIONS)}] {question}")
        
        for model_key, model_config in EMBEDDING_MODELS.items():
            print(f"  Testing {model_key}...", end="", flush=True)
            try:
                start_t = time.time()
                
                # Perform search
                response = searcher.search_by_query(
                    question,
                    model_name=model_config["name"],
                    embedding_property=model_config["property"],
                    top_k=5
                )
                
                end_t = time.time()
                duration = end_t - start_t
                
                # Extract metrics
                items = response.get("results", [])
                count = len(items)
                
                if count > 0:
                    top_score = items[0].get("score", 0.0)
                    avg_score = sum(item.get("score", 0.0) for item in items) / count
                    
                    # Format the top result to get a readable string
                    top_result_formatted = searcher.format_results_for_llm({
                        "results": [items[0]], 
                        "count": 1, 
                        "query": question
                    })
                    # Extract just the result part, removing the header "Found 1 similar..."
                    if "Result 1" in top_result_formatted:
                        top_content = top_result_formatted.split("Result 1", 1)[1].strip()
                    else:
                        top_content = top_result_formatted
                else:
                    top_score = 0.0
                    avg_score = 0.0
                    top_content = "No results found."
                
                metrics = {
                    "question": question,
                    "duration": duration,
                    "count": count,
                    "top_score": top_score,
                    "avg_score": avg_score,
                    "top_content": top_content
                }
                results[model_key].append(metrics)
                print(f" Done ({duration:.2f}s, Top Score: {top_score:.4f})")
                
            except Exception as e:
                print(f" Error: {e}")
                results[model_key].append({
                    "question": question,
                    "duration": 0,
                    "count": 0,
                    "top_score": 0,
                    "avg_score": 0,
                    "top_content": f"ERROR: {str(e)}"
                })

    # Generate Report
    generate_report(results)
    searcher.close()

def generate_report(results: Dict[str, List[Dict]]):
    """Generate a detailed markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = []
    
    report.append(f"# Embedding Model Comparison Report\n")
    report.append(f"**Date:** {timestamp}\n")
    report.append(f"**Models:** {', '.join(EMBEDDING_MODELS.keys())}\n")
    report.append(f"**Questions:** {len(TEST_QUESTIONS)}\n")
    
    # 1. Quantitative Summary
    report.append("\n## 1. Quantitative Metrics Summary\n")
    report.append("| Model | Avg Time (s) | Avg Top Score | Avg Mean Score |")
    report.append("|-------|--------------|---------------|----------------|")
    
    for model in EMBEDDING_MODELS:
        data = results[model]
        avg_time = sum(r["duration"] for r in data) / len(data) if data else 0
        avg_top = sum(r["top_score"] for r in data) / len(data) if data else 0
        avg_mean = sum(r["avg_score"] for r in data) / len(data) if data else 0
        
        report.append(f"| {model} | {avg_time:.3f} | {avg_top:.4f} | {avg_mean:.4f} |")

    # 2. Detailed Comparison Table
    report.append("\n## 2. Detailed Comparison (Scores)\n")
    report.append("| Q# | Question | MinILM Score | MPNet Score | Winner |")
    report.append("|----|----------|--------------|-------------|--------|")
    
    for i, question in enumerate(TEST_QUESTIONS):
        minilm_res = results["minilm"][i]
        mpnet_res = results["mpnet"][i]
        
        m_score = minilm_res["top_score"]
        p_score = mpnet_res["top_score"]
        
        winner = "MPNet" if p_score > m_score else "MinILM"
        if abs(p_score - m_score) < 0.01: winner = "Tie"
        
        report.append(f"| Q{i+1} | {question[:40]}... | {m_score:.4f} | {p_score:.4f} | {winner} |")

    # 3. Qualitative Comparison (Top Retrieved Content)
    report.append("\n## 3. Qualitative Evaluation (Top Retrieved Result)\n")
    
    for i, question in enumerate(TEST_QUESTIONS):
        report.append(f"\n### Q{i+1}: {question}\n")
        
        minilm_content = results["minilm"][i]["top_content"]
        mpnet_content = results["mpnet"][i]["top_content"]
        
        report.append(f"**MinILM** (Score: {results['minilm'][i]['top_score']:.4f}):")
        report.append(f"> {minilm_content}\n")
        
        report.append(f"**MPNet** (Score: {results['mpnet'][i]['top_score']:.4f}):")
        report.append(f"> {mpnet_content}\n")
            
        report.append("---\n")

    # Save to file
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.join(output_dir, f"embedding_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"\nReport saved to: {filename}")
    print("\nSummary:")
    print("\n".join(report[:15])) # Print first few lines

if __name__ == "__main__":
    run_comparison()
