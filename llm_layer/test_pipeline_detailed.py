# llm_layer/test_pipeline_detailed.py
"""
Detailed Pipeline Testing Script
=================================
Tests 15 different questions on a single LLM model and logs:
1. Number of results from Cypher query
2. Number of results from embeddings
3. Number of results sent to LLM (combined)
4. The full prompt sent to LLM
5. The LLM's response
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any
import json
from datetime import datetime

from llm_layer.graph_rag_pipeline import GraphRAGPipeline, load_config


class DetailedPipelineTester:
    """
    Tests the Graph-RAG pipeline with detailed logging.
    """

    def __init__(self, model_name: str = "qwen", output_file: str = None):
        """
        Initialize the tester.

        Args:
            model_name: LLM model to use (openai, qwen, llama)
            output_file: Path to save results (default: outputs/pipeline_test_detailed_{timestamp}.txt)
        """
        self.model_name = model_name

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/pipeline_test_detailed_{model_name}_{timestamp}.txt"

        self.output_file = output_file

        # Load config and initialize pipeline
        cfg = load_config()
        self.pipeline = GraphRAGPipeline(
            neo4j_uri=cfg["URI"],
            neo4j_username=cfg["USERNAME"],
            neo4j_password=cfg["PASSWORD"],
            hf_token="hf_token",
            default_model=model_name,
            embedding_model="mpnet"
        )

        # Test questions (15 diverse questions)
        self.test_questions = [
            # Delay Questions (3)
            "Which flights have the longest delays?",
            "Show me flights with delays from ORD",
            "Flights delayed more than 1 hour",

            # Flight Search (3)
            "Show me flights from CAI to DXB",
            "What flights go from JFK to FRA?",
            "Find economy class flights",

            # Airport Questions (2)
            "Tell me about ORD airport",
            "Information on Cairo airport",

            # Passenger Experience (3)
            "Which flights have poor passenger experience?",
            "Show me flights with bad food quality",
            "Flights with low satisfaction scores",

            # Recommendations (2)
            "Recommend a good flight route",
            "Best business class flights",

            # Complex Questions (2)
            "Business class flights from ORD with delays",
            "Economy passengers on long distance routes with poor food"
        ]

    def test_single_question(self, question: str, question_number: int) -> Dict[str, Any]:
        """
        Test a single question and collect detailed metrics.

        Args:
            question: The question to test
            question_number: Question number (for logging)

        Returns:
            Dictionary with all metrics and results
        """
        print(f"\n[{question_number}/15] Testing: {question}")

        # Run the pipeline
        result = self.pipeline.answer_question(question, model=self.model_name)

        # Extract metrics
        metrics = {
            "question_number": question_number,
            "question": question,
            "intent": result.get("intent"),
            "entities": result.get("entities"),
            "cypher_count": result.get("cypher_results", {}).get("count", 0) if result.get("cypher_results") else 0,
            "embedding_count": result.get("embedding_results", {}).get("count", 0) if result.get("embedding_results") else 0,
            "combined_count": len(result.get("combined_context", "")),  # We'll extract this better
            "prompt": result.get("prompt", ""),
            "prompt_length": len(result.get("prompt", "")),
            "llm_response": result.get("answer", ""),
            "llm_response_length": len(result.get("answer", "")),
            "response_time": result.get("llm_response", {}).get("response_time", 0),
            "success": result.get("success", False)
        }

        print(f"  [OK] Cypher: {metrics['cypher_count']} results")
        print(f"  [OK] Embeddings: {metrics['embedding_count']} results")
        print(f"  [OK] Prompt: {metrics['prompt_length']} chars")
        print(f"  [OK] Response: {metrics['llm_response_length']} chars in {metrics['response_time']:.2f}s")

        return metrics

    def format_result_for_log(self, metrics: Dict[str, Any]) -> str:
        """
        Format a single result for the log file.

        Args:
            metrics: Metrics dictionary

        Returns:
            Formatted string
        """
        separator = "=" * 100
        subseparator = "-" * 100

        output = f"\n{separator}\n"
        output += f"QUESTION {metrics['question_number']}/15: {metrics['question']}\n"
        output += f"{separator}\n\n"

        # Step 1: Intent & Entities
        output += f"[STEP 1] PREPROCESSING\n{subseparator}\n"
        output += f"Intent: {metrics['intent']}\n"
        output += f"Entities Extracted:\n"
        for key, value in metrics['entities'].items():
            if value is not None:
                output += f"  - {key}: {value}\n"
        if not any(metrics['entities'].values()):
            output += "  (No entities extracted)\n"
        output += "\n"

        # Step 2: Retrieval Results
        output += f"[STEP 2] GRAPH RETRIEVAL\n{subseparator}\n"
        output += f"Cypher Query Results: {metrics['cypher_count']} journeys\n"
        output += f"Embedding Search Results: {metrics['embedding_count']} journeys\n"
        output += f"Total Context Length: {metrics['prompt_length']} characters\n"
        output += "\n"

        # Step 3: LLM Prompt
        output += f"[STEP 3] PROMPT SENT TO LLM\n{subseparator}\n"
        output += f"Prompt Length: {metrics['prompt_length']} characters\n"
        output += f"Model: {self.model_name}\n\n"
        output += "FULL PROMPT:\n"
        output += metrics['prompt']
        output += "\n\n"

        # Step 4: LLM Response
        output += f"[STEP 4] LLM RESPONSE\n{subseparator}\n"
        output += f"Response Time: {metrics['response_time']:.2f} seconds\n"
        output += f"Response Length: {metrics['llm_response_length']} characters\n"
        output += f"Success: {metrics['success']}\n\n"
        output += "FULL RESPONSE:\n"
        output += metrics['llm_response']
        output += "\n\n"

        return output

    def run_all_tests(self):
        """
        Run all 15 test questions and save detailed logs.
        """
        print(f"\n{'='*100}")
        print(f"DETAILED PIPELINE TESTING - MODEL: {self.model_name.upper()}")
        print(f"{'='*100}")
        print(f"Testing {len(self.test_questions)} questions...")
        print(f"Results will be saved to: {self.output_file}\n")

        # Open output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"{'='*100}\n")
            f.write(f"GRAPH-RAG PIPELINE - DETAILED TEST RESULTS\n")
            f.write(f"{'='*100}\n\n")
            f.write(f"Model: {self.model_name}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Questions: {len(self.test_questions)}\n")
            f.write(f"\n{'='*100}\n\n")

            # Test each question
            all_metrics = []
            for i, question in enumerate(self.test_questions, 1):
                try:
                    metrics = self.test_single_question(question, i)
                    all_metrics.append(metrics)

                    # Write to file immediately
                    f.write(self.format_result_for_log(metrics))
                    f.flush()  # Ensure it's written

                except Exception as e:
                    print(f"  [ERROR] Error: {e}")
                    error_log = f"\n{'='*100}\n"
                    error_log += f"QUESTION {i}/15: {question}\n"
                    error_log += f"{'='*100}\n"
                    error_log += f"ERROR: {str(e)}\n\n"
                    f.write(error_log)
                    f.flush()

            # Write summary
            f.write(f"\n\n{'='*100}\n")
            f.write(f"SUMMARY STATISTICS\n")
            f.write(f"{'='*100}\n\n")

            successful = [m for m in all_metrics if m['success']]

            f.write(f"Total Questions: {len(self.test_questions)}\n")
            f.write(f"Successful: {len(successful)}\n")
            f.write(f"Failed: {len(all_metrics) - len(successful)}\n")
            f.write(f"Success Rate: {len(successful)/len(all_metrics)*100:.1f}%\n\n")

            if successful:
                avg_cypher = sum(m['cypher_count'] for m in successful) / len(successful)
                avg_embedding = sum(m['embedding_count'] for m in successful) / len(successful)
                avg_response_time = sum(m['response_time'] for m in successful) / len(successful)
                avg_prompt_len = sum(m['prompt_length'] for m in successful) / len(successful)
                avg_response_len = sum(m['llm_response_length'] for m in successful) / len(successful)

                f.write(f"Average Cypher Results: {avg_cypher:.1f}\n")
                f.write(f"Average Embedding Results: {avg_embedding:.1f}\n")
                f.write(f"Average Response Time: {avg_response_time:.2f}s\n")
                f.write(f"Average Prompt Length: {avg_prompt_len:.0f} characters\n")
                f.write(f"Average Response Length: {avg_response_len:.0f} characters\n\n")

            # Question-by-question summary
            f.write(f"\nQUESTION-BY-QUESTION SUMMARY:\n")
            f.write(f"{'-'*100}\n")
            f.write(f"{'#':<4} {'Cypher':<8} {'Embed':<8} {'Time(s)':<10} {'Success':<10} Question\n")
            f.write(f"{'-'*100}\n")

            for m in all_metrics:
                status = "Yes" if m['success'] else "No"
                f.write(f"{m['question_number']:<4} {m['cypher_count']:<8} {m['embedding_count']:<8} "
                       f"{m['response_time']:<10.2f} {status:<10} {m['question'][:50]}...\n")

            f.write(f"\n{'='*100}\n")
            f.write(f"END OF REPORT\n")
            f.write(f"{'='*100}\n")

        print(f"\n{'='*100}")
        print(f"[OK] Testing complete!")
        print(f"[OK] Results saved to: {self.output_file}")
        print(f"{'='*100}\n")

        # Close pipeline
        self.pipeline.close()

        return all_metrics


def main():
    """
    Main function to run the detailed pipeline test.
    """
    print("\nWelcome to the Detailed Pipeline Tester!")
    print("This will test 15 questions and log everything in detail.\n")

    # Choose model
    print("Available models:")
    print("  1. qwen (Qwen2.5-7B-Instruct) - Default, best quality")
    print("  2. openai (gpt-oss-120b)")
    print("  3. llama (Llama-3.1-8B-Instruct)")

    model_choice = input("\nChoose model (1-3) or press Enter for default (qwen): ").strip()

    model_map = {
        "1": "qwen",
        "2": "openai",
        "3": "llama",
        "": "qwen"
    }

    model_name = model_map.get(model_choice, "qwen")

    print(f"\n[OK] Using model: {model_name}")
    print("Starting tests...\n")

    # Run tests
    tester = DetailedPipelineTester(model_name=model_name)
    metrics = tester.run_all_tests()

    # Print summary to console
    print("\nQUICK SUMMARY:")
    print(f"  Total Questions: {len(metrics)}")
    print(f"  Successful: {sum(1 for m in metrics if m['success'])}")
    print(f"  Average Response Time: {sum(m['response_time'] for m in metrics)/len(metrics):.2f}s")
    print(f"\nCheck the output file for full details!")


if __name__ == "__main__":
    main()
