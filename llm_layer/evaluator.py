# llm_layer/evaluator.py

"""
Model Evaluator - Step 3.d
===========================
Evaluates LLM models using:
- Quantitative metrics: response time, token count, accuracy
- Qualitative metrics: relevance, factual accuracy, naturalness, completeness

Creates comparison reports for model selection.
"""

import time
import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class QuantitativeMetrics:
    """Quantitative evaluation metrics."""
    model_name: str
    response_time: float  # seconds
    token_count: int  # approximate
    success_rate: float  # 0.0 to 1.0
    avg_response_length: int  # characters


@dataclass
class QualitativeMetrics:
    """Qualitative evaluation metrics (human rated 1-5)."""
    model_name: str
    question: str
    relevance: int  # 1-5: How relevant is the answer?
    factual_accuracy: int  # 1-5: Did it use only KG data?
    naturalness: int  # 1-5: How natural is the language?
    completeness: int  # 1-5: Did it answer fully?
    notes: str = ""


class ModelEvaluator:
    """
    Evaluates and compares multiple LLM models.
    """

    def __init__(self):
        self.test_cases = []
        self.results = []

    def add_test_case(
        self,
        question: str,
        expected_elements: List[str],
        context: str
    ):
        """
        Add a test case for evaluation.

        Args:
            question: Test question
            expected_elements: List of elements that should appear in answer
            context: KG context for this question
        """
        self.test_cases.append({
            "question": question,
            "expected_elements": expected_elements,
            "context": context
        })

    def evaluate_quantitative(
        self,
        model_results: List[Dict[str, Any]]
    ) -> Dict[str, QuantitativeMetrics]:
        """
        Calculate quantitative metrics for each model.

        Args:
            model_results: List of results from all models

        Returns:
            Dictionary mapping model_name -> QuantitativeMetrics
        """
        metrics_by_model = {}

        # Group by model
        model_groups = {}
        for result in model_results:
            model = result["model"]
            if model not in model_groups:
                model_groups[model] = []
            model_groups[model].append(result)

        # Calculate metrics for each model
        for model, results in model_groups.items():
            times = [r["response_time"] for r in results]
            successes = [r["success"] for r in results]
            lengths = [len(r.get("answer", "")) for r in results]

            metrics = QuantitativeMetrics(
                model_name=model,
                response_time=sum(times) / len(times),
                token_count=sum(lengths) // 4,  # Rough estimate: 4 chars/token
                success_rate=sum(successes) / len(successes),
                avg_response_length=sum(lengths) // len(lengths)
            )

            metrics_by_model[model] = metrics

        return metrics_by_model

    def evaluate_qualitative_interactive(
        self,
        model_results: List[Dict[str, Any]]
    ) -> List[QualitativeMetrics]:
        """
        Interactive qualitative evaluation (asks user to rate answers).

        Args:
            model_results: Results from models

        Returns:
            List of QualitativeMetrics
        """
        qualitative_results = []

        print("\n" + "="*80)
        print("QUALITATIVE EVALUATION - Please rate each answer (1-5)")
        print("="*80 + "\n")

        for result in model_results:
            print(f"\n{'-'*80}")
            print(f"MODEL: {result['model']}")
            print(f"QUESTION: {result.get('question', 'N/A')}")
            print(f"{'-'*80}")
            print(f"\nANSWER:\n{result.get('answer', 'No answer')}\n")

            # Ask user for ratings
            print("Rate this answer (1=poor, 5=excellent):")

            try:
                relevance = int(input("  Relevance (1-5): "))
                factual_accuracy = int(input("  Factual Accuracy (1-5): "))
                naturalness = int(input("  Naturalness (1-5): "))
                completeness = int(input("  Completeness (1-5): "))
                notes = input("  Notes (optional): ")

                metrics = QualitativeMetrics(
                    model_name=result['model'],
                    question=result.get('question', ''),
                    relevance=relevance,
                    factual_accuracy=factual_accuracy,
                    naturalness=naturalness,
                    completeness=completeness,
                    notes=notes
                )

                qualitative_results.append(metrics)

            except (ValueError, KeyboardInterrupt):
                print("Skipping this evaluation...")
                continue

        return qualitative_results

    def evaluate_qualitative_auto(
        self,
        model_results: List[Dict[str, Any]]
    ) -> List[QualitativeMetrics]:
        """
        Automatic qualitative evaluation using simple heuristics.

        Args:
            model_results: Results from models

        Returns:
            List of QualitativeMetrics
        """
        qualitative_results = []

        for result in model_results:
            answer = result.get("answer", "").lower()
            question = result.get("question", "")

            # Simple heuristics for scoring
            # Relevance: Check if answer addresses the question
            relevance = 3  # Default
            if len(answer) > 50 and any(keyword in answer for keyword in ["delay", "flight", "journey", "passenger"]):
                relevance = 4

            # Factual accuracy: Check for specific data points
            factual_accuracy = 3
            if any(marker in answer for marker in ["j_", "journey", "flight", "minutes", "/5"]):
                factual_accuracy = 4

            # Naturalness: Check sentence structure
            naturalness = 3
            if answer.count(".") >= 2 and not answer.startswith("error"):
                naturalness = 4

            # Completeness: Check answer length
            completeness = 3
            if len(answer) > 100:
                completeness = 4

            metrics = QualitativeMetrics(
                model_name=result['model'],
                question=question,
                relevance=relevance,
                factual_accuracy=factual_accuracy,
                naturalness=naturalness,
                completeness=completeness,
                notes="Auto-evaluated"
            )

            qualitative_results.append(metrics)

        return qualitative_results

    def generate_comparison_report(
        self,
        quantitative: Dict[str, QuantitativeMetrics],
        qualitative: List[QualitativeMetrics]
    ) -> str:
        """
        Generate comprehensive comparison report.

        Args:
            quantitative: Quantitative metrics by model
            qualitative: List of qualitative metrics

        Returns:
            Formatted report string
        """
        report = []

        report.append("="*80)
        report.append("MODEL EVALUATION REPORT - Step 3.d")
        report.append("="*80)
        report.append("")

        # === QUANTITATIVE METRICS ===
        report.append("QUANTITATIVE METRICS:")
        report.append("-"*80)
        report.append(f"{'Model':<20} {'Resp Time (s)':<15} {'Success Rate':<15} {'Avg Length':<15}")
        report.append("-"*80)

        for model, metrics in quantitative.items():
            report.append(
                f"{model:<20} "
                f"{metrics.response_time:<15.2f} "
                f"{metrics.success_rate:<15.1%} "
                f"{metrics.avg_response_length:<15}"
            )

        report.append("")

        # === QUALITATIVE METRICS ===
        report.append("QUALITATIVE METRICS (Average Scores 1-5):")
        report.append("-"*80)

        # Group by model
        qual_by_model = {}
        for q in qualitative:
            if q.model_name not in qual_by_model:
                qual_by_model[q.model_name] = []
            qual_by_model[q.model_name].append(q)

        report.append(f"{'Model':<20} {'Relevance':<12} {'Factual':<12} {'Natural':<12} {'Complete':<12} {'Overall':<12}")
        report.append("-"*80)

        for model, metrics_list in qual_by_model.items():
            avg_rel = sum(m.relevance for m in metrics_list) / len(metrics_list)
            avg_fact = sum(m.factual_accuracy for m in metrics_list) / len(metrics_list)
            avg_nat = sum(m.naturalness for m in metrics_list) / len(metrics_list)
            avg_comp = sum(m.completeness for m in metrics_list) / len(metrics_list)
            overall = (avg_rel + avg_fact + avg_nat + avg_comp) / 4

            report.append(
                f"{model:<20} "
                f"{avg_rel:<12.2f} "
                f"{avg_fact:<12.2f} "
                f"{avg_nat:<12.2f} "
                f"{avg_comp:<12.2f} "
                f"{overall:<12.2f}"
            )

        report.append("")

        # === RECOMMENDATION ===
        report.append("RECOMMENDATION:")
        report.append("-"*80)

        # Find best model based on overall score
        best_model = None
        best_score = 0

        for model, metrics_list in qual_by_model.items():
            overall = sum(m.relevance + m.factual_accuracy + m.naturalness + m.completeness
                         for m in metrics_list) / (len(metrics_list) * 4)

            if overall > best_score:
                best_score = overall
                best_model = model

        report.append(f"Best performing model: {best_model} (Overall score: {best_score:.2f}/5)")

        # Consider response time
        fastest_model = min(quantitative.items(), key=lambda x: x[1].response_time)
        report.append(f"Fastest model: {fastest_model[0]} ({fastest_model[1].response_time:.2f}s)")

        report.append("")
        report.append("="*80)

        return "\n".join(report)

    def save_results(self, filepath: str, quantitative, qualitative):
        """
        Save evaluation results to JSON file.

        Args:
            filepath: Output file path
            quantitative: Quantitative metrics
            qualitative: Qualitative metrics
        """
        data = {
            "quantitative": {k: asdict(v) for k, v in quantitative.items()},
            "qualitative": [asdict(q) for q in qualitative]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results saved to: {filepath}")


# ==========================================
# Default Test Cases
# ==========================================

def get_default_test_cases() -> List[Dict[str, Any]]:
    """
    Get default test cases for airline queries.

    Returns:
        List of test case dictionaries
    """
    return [
        {
            "question": "Which flights have the longest delays?",
            "expected_elements": ["delay", "minutes", "journey"],
            "context": "Journey J_123: 104 min delay, Journey J_456: 87 min delay"
        },
        {
            "question": "What is the average food satisfaction score?",
            "expected_elements": ["food", "satisfaction", "average", "/5"],
            "context": "Journey J_123: food 2/5, Journey J_456: food 3/5"
        },
        {
            "question": "Show me business class journeys with poor experience",
            "expected_elements": ["business", "poor", "experience"],
            "context": "Journey J_789: Business class, food 2/5, delay 45 min"
        }
    ]


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo: Evaluate model results.
    """
    print("\n" + "="*80)
    print("MODEL EVALUATOR DEMO - Step 3.d")
    print("="*80 + "\n")

    # Mock results from 3 models
    mock_results = [
        # Gemma results
        {"model": "gemma", "question": "Which flights have longest delays?",
         "answer": "Based on the data, Journey J_123 has the longest delay at 104 minutes.",
         "response_time": 2.3, "success": True},
        {"model": "gemma", "question": "Average food score?",
         "answer": "The average food satisfaction is 2.5 out of 5.",
         "response_time": 1.8, "success": True},

        # Llama results
        {"model": "llama", "question": "Which flights have longest delays?",
         "answer": "Journey J_123 shows a delay of 104 minutes, which is the highest.",
         "response_time": 3.1, "success": True},
        {"model": "llama", "question": "Average food score?",
         "answer": "Food satisfaction averages 2.5/5 across journeys.",
         "response_time": 2.9, "success": True},

        # Qwen results
        {"model": "qwen", "question": "Which flights have longest delays?",
         "answer": "The data shows J_123 with 104 minute delay.",
         "response_time": 2.0, "success": True},
        {"model": "qwen", "question": "Average food score?",
         "answer": "Average is 2.5 out of 5.",
         "response_time": 1.7, "success": True},
    ]

    # Evaluate
    evaluator = ModelEvaluator()

    print("Calculating quantitative metrics...")
    quant_metrics = evaluator.evaluate_quantitative(mock_results)

    print("\nRunning automatic qualitative evaluation...")
    qual_metrics = evaluator.evaluate_qualitative_auto(mock_results)

    print("\nGenerating comparison report...\n")
    report = evaluator.generate_comparison_report(quant_metrics, qual_metrics)
    print(report)

    # Save results
    print("\nSaving results...")
    evaluator.save_results("evaluation_results.json", quant_metrics, qual_metrics)

    print("\n" + "="*80)
    print("Evaluator demo completed!")
    print("="*80)
