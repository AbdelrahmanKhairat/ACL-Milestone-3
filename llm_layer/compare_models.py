# llm_layer/compare_models.py
"""
Model Comparison Script - Active Evaluation
===========================================
Runs a 10-question test suite against all 3 LLM models (Qwen, OpenAI, Llama).
Generates a comprehensive report with Quantitative and Qualitative metrics.
"""

import os
import sys
import time
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_layer.graph_rag_pipeline import GraphRAGPipeline, load_config

# Test Dataset: 8 Questions (Simple -> Complex)
TEST_QUESTIONS = [
    # Simple Retrieval (1-3)
    "Which flights have the longest delays?",
    "Show me the 5 shortest journeys",
    "Find economy class flights from JFK to LAX",
    
    # Semantic Search (4-6)
    "Flights with terrible food and poor service",
    "What are the most comfortable flights?",
    "Show me journeys with good food but long delays",
    
    # Complex/Multi-hop (7-8)
    "Best business class routes with minimal delays",
    "Gold loyalty members on long-haul flights"
]

MODELS_TO_TEST = ["qwen", "openai", "llama"]

def estimate_tokens(text: str) -> int:
    """Estimate token count (approx 4 chars per token)."""
    if not text:
        return 0
    return len(text) // 4

def run_comparison():
    """Run the comparison suite."""
    print("\n" + "=" * 80)
    print("STARTING MODEL COMPARISON SUITE")
    print("=" * 80)
    print(f"Models: {MODELS_TO_TEST}")
    print(f"Questions: {len(TEST_QUESTIONS)}")
    print("-" * 80)

    # Load Config
    cfg = load_config()
    
    # Initialize Pipeline (using one instance, we'll swap models in the call or init multiple if needed)
    # The pipeline supports passing 'model' to answer_question, so one instance is enough.
    # We need a token for the LLM integration.
    hf_token = "hf_token" # Placeholder, user should have set this or we rely on env/input
    # Ideally we get this from env or config, but for now we'll assume it's set or handled by the class
    # If the user has a token in app.py, we might need it here. 
    # For this script, we'll try to load from a local file or env if possible, 
    # or just rely on the user having set it in the code or environment.
    # Let's check if we can find a token in a config file or just ask the user to ensure it's set.
    # For now, we will initialize with a placeholder and hope the user has set it in the class or env.
    # Actually, let's try to read it from a file if it exists, otherwise warn.

    print("Initializing Pipeline...")
    try:
        pipeline = GraphRAGPipeline(
            neo4j_uri=cfg["URI"],
            neo4j_username=cfg["USERNAME"],
            neo4j_password=cfg["PASSWORD"],
            hf_token=hf_token,
            default_model="qwen", # Default, will override per call
            embedding_model="mpnet"
        )
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        return

    results = {model: [] for model in MODELS_TO_TEST}
    
    # Run Tests
    for q_idx, question in enumerate(TEST_QUESTIONS):
        print(f"\n[Question {q_idx+1}/{len(TEST_QUESTIONS)}] {question}")
        
        # We run the retrieval ONCE per question to be fair (or should we? 
        # The pipeline does retrieval inside answer_question. 
        # To strictly compare LLMs, we should ideally use the SAME context.
        # However, answer_question does it all. 
        # Let's stick to answer_question for simplicity as it simulates real usage.)
        
        for model in MODELS_TO_TEST:
            print(f"  Testing {model}...", end="", flush=True)
            try:
                # Run pipeline
                start_t = time.time()
                response = pipeline.answer_question(
                    question, 
                    model=model, 
                    use_cypher=True, 
                    use_embeddings=True
                )
                # Note: answer_question prints a lot, might clutter output. 
                # We might want to suppress stdout if we want a clean progress bar, 
                # but for now let's let it print debug info as it's helpful.
                
                # Collect metrics
                ans = response.get("answer", "")
                prompt = response.get("prompt", "")
                success = response.get("success", False)
                resp_time = response.get("llm_response", {}).get("response_time", 0)
                
                metrics = {
                    "question": question,
                    "answer": ans,
                    "response_time": resp_time,
                    "success": success,
                    "prompt_tokens": estimate_tokens(prompt),
                    "response_tokens": estimate_tokens(ans),
                    "context_length": len(response.get("combined_context", ""))
                }
                results[model].append(metrics)
                print(f" Done ({resp_time:.2f}s)")
                
            except Exception as e:
                print(f" Error: {e}")
                results[model].append({
                    "question": question,
                    "answer": f"ERROR: {str(e)}",
                    "response_time": 0,
                    "success": False,
                    "prompt_tokens": 0,
                    "response_tokens": 0,
                    "context_length": 0
                })

    # Generate Report
    generate_report(results)
    pipeline.close()

def generate_report(results: Dict[str, List[Dict]]):
    """Generate a detailed markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = []
    
    report.append(f"# Model Comparison Report\n")
    report.append(f"**Date:** {timestamp}\n")
    report.append(f"**Models:** {', '.join(MODELS_TO_TEST)}\n")
    report.append(f"**Questions:** {len(TEST_QUESTIONS)}\n")
    
    # 1. Quantitative Summary
    report.append("\n## 1. Quantitative Metrics Summary\n")
    report.append("| Model | Success Rate | Avg Time (s) | Avg Prompt Tok | Avg Resp Tok |")
    report.append("|-------|--------------|--------------|----------------|--------------|")
    
    for model in MODELS_TO_TEST:
        data = results[model]
        success_count = sum(1 for r in data if r["success"])
        avg_time = sum(r["response_time"] for r in data) / len(data) if data else 0
        avg_prompt = sum(r["prompt_tokens"] for r in data) / len(data) if data else 0
        avg_resp = sum(r["response_tokens"] for r in data) / len(data) if data else 0
        success_rate = (success_count / len(data)) * 100 if data else 0
        
        report.append(f"| {model.title()} | {success_rate:.1f}% | {avg_time:.2f} | {int(avg_prompt)} | {int(avg_resp)} |")

    # 2. Detailed Evaluation Table (For Human Grading)
    report.append("\n## 2. Detailed Evaluation Table (Human Grading)\n")
    report.append("Please rate Relevance, Naturalness, and Correctness on a scale of 1-5.\n")
    report.append("| Q# | Model | Time (s) | Tokens | Relevance | Naturalness | Correctness |")
    report.append("|----|-------|----------|--------|-----------|-------------|-------------|")
    
    for i in range(len(TEST_QUESTIONS)):
        for model in MODELS_TO_TEST:
            res = results[model][i]
            report.append(f"| Q{i+1} | {model.title()} | {res['response_time']:.2f} | {res['response_tokens']} | | | |")
        # Add a separator row for readability
        report.append("| | | | | | | |")

    # 3. Qualitative Comparison (Question by Question)
    report.append("\n## 3. Qualitative Evaluation (Answers)\n")
    
    for i, question in enumerate(TEST_QUESTIONS):
        report.append(f"\n### Q{i+1}: {question}\n")
        
        for model in MODELS_TO_TEST:
            res = results[model][i]
            status = "✅" if res["success"] else "❌"
            report.append(f"**{model.title()}** ({status}, {res['response_time']:.2f}s):")
            report.append(f"> {res['answer'].replace(chr(10), '  '+chr(10))}\n") # Indent newlines
            
        report.append("---\n")

    # Save to file
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.join(output_dir, f"model_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"\nReport saved to: {filename}")
    print("\nSummary:")
    print("\n".join(report[:15])) # Print first few lines (summary table)

if __name__ == "__main__":
    run_comparison()
