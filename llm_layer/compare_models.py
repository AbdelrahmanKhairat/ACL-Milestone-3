# llm_layer/compare_models.py
"""
Model Comparison Script - Quantitative Evaluation
==================================================
Compares all 3 LLM models (Qwen, OpenAI, Llama) across 15 test questions.
Provides quantitative metrics for Step 3.d of the assignment.
"""

import os
import sys
import re
from typing import Dict, List, Any
from datetime import datetime
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_detailed_log(filepath: str) -> Dict[str, Any]:
    """
    Parse a detailed test log file to extract metrics.

    Args:
        filepath: Path to the detailed log file

    Returns:
        Dictionary with model name, questions, and metrics
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract model name from filename or content
    model_name = "unknown"
    if "qwen" in filepath.lower():
        model_name = "Qwen"
    elif "openai" in filepath.lower():
        model_name = "OpenAI"
    elif "llama" in filepath.lower():
        model_name = "Llama"
    else:
        # Try to extract from content
        model_match = re.search(r'Model: (\w+)', content)
        if model_match:
            model_name = model_match.group(1).title()

    # Extract question-by-question results
    questions = []

    # Find the question-by-question summary table
    table_match = re.search(
        r'QUESTION-BY-QUESTION SUMMARY:.*?-{50,}.*?-{50,}(.*?)={50,}',
        content,
        re.DOTALL
    )

    if table_match:
        table_content = table_match.group(1)

        # Skip header line and parse data lines
        lines = [line.strip() for line in table_content.split('\n') if line.strip()]

        for line in lines[1:]:  # Skip header
            # Parse line: #    Cypher   Embed    Time(s)    Success    Question
            parts = line.split()
            if len(parts) >= 5:
                try:
                    question_num = int(parts[0])
                    cypher_count = int(parts[1])
                    embed_count = int(parts[2])
                    response_time = float(parts[3])
                    success = parts[4].lower() == "yes"
                    question_text = ' '.join(parts[5:])

                    questions.append({
                        'number': question_num,
                        'question': question_text,
                        'cypher_count': cypher_count,
                        'embed_count': embed_count,
                        'response_time': response_time,
                        'success': success
                    })
                except (ValueError, IndexError):
                    continue

    # Extract summary statistics
    summary = {}

    # Total questions
    total_match = re.search(r'Total Questions: (\d+)', content)
    if total_match:
        summary['total_questions'] = int(total_match.group(1))

    # Success count
    success_match = re.search(r'Successful: (\d+)', content)
    if success_match:
        summary['successful'] = int(success_match.group(1))

    # Failed count
    failed_match = re.search(r'Failed: (\d+)', content)
    if failed_match:
        summary['failed'] = int(failed_match.group(1))

    # Success rate
    rate_match = re.search(r'Success Rate: ([\d.]+)%', content)
    if rate_match:
        summary['success_rate'] = float(rate_match.group(1))

    # Average metrics
    avg_cypher_match = re.search(r'Average Cypher Results: ([\d.]+)', content)
    if avg_cypher_match:
        summary['avg_cypher'] = float(avg_cypher_match.group(1))

    avg_embed_match = re.search(r'Average Embedding Results: ([\d.]+)', content)
    if avg_embed_match:
        summary['avg_embedding'] = float(avg_embed_match.group(1))

    avg_time_match = re.search(r'Average Response Time: ([\d.]+)s', content)
    if avg_time_match:
        summary['avg_response_time'] = float(avg_time_match.group(1))

    avg_prompt_match = re.search(r'Average Prompt Length: ([\d.]+) characters', content)
    if avg_prompt_match:
        summary['avg_prompt_length'] = float(avg_prompt_match.group(1))

    avg_response_match = re.search(r'Average Response Length: ([\d.]+) characters', content)
    if avg_response_match:
        summary['avg_response_length'] = float(avg_response_match.group(1))

    return {
        'model': model_name,
        'filepath': filepath,
        'questions': questions,
        'summary': summary
    }


def compare_models(model_data: List[Dict[str, Any]]) -> str:
    """
    Compare all models and generate a comprehensive report.

    Args:
        model_data: List of parsed model data dictionaries

    Returns:
        Formatted comparison report as string
    """
    report = []

    # Header
    report.append("=" * 120)
    report.append("MODEL COMPARISON - QUANTITATIVE EVALUATION (Step 3.d)")
    report.append("=" * 120)
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Models Compared: {len(model_data)}")
    report.append(f"Questions per Model: 15\n")

    # Overall Summary Table
    report.append("\n" + "=" * 120)
    report.append("OVERALL QUANTITATIVE METRICS")
    report.append("=" * 120)
    report.append("")

    # Create summary table
    header = f"{'Model':<15} {'Success':<10} {'Failed':<10} {'Success %':<12} {'Avg Time(s)':<15} {'Avg Prompt':<12} {'Avg Response':<12}"
    report.append(header)
    report.append("-" * 120)

    for data in model_data:
        model = data['model']
        s = data['summary']

        row = f"{model:<15} {s.get('successful', 0):<10} {s.get('failed', 0):<10} " \
              f"{s.get('success_rate', 0.0):<12.1f} {s.get('avg_response_time', 0.0):<15.2f} " \
              f"{int(s.get('avg_prompt_length', 0)):<12} {int(s.get('avg_response_length', 0)):<12}"
        report.append(row)

    report.append("")

    # Best performer analysis
    report.append("\n" + "=" * 120)
    report.append("BEST PERFORMER ANALYSIS")
    report.append("=" * 120)
    report.append("")

    # Find best in each category
    best_success_rate = max(model_data, key=lambda x: x['summary'].get('success_rate', 0))
    fastest_avg = min(model_data, key=lambda x: x['summary'].get('avg_response_time', float('inf')))

    report.append(f"Highest Success Rate: {best_success_rate['model']} ({best_success_rate['summary'].get('success_rate', 0):.1f}%)")
    report.append(f"Fastest Average Response: {fastest_avg['model']} ({fastest_avg['summary'].get('avg_response_time', 0):.2f}s)")

    # Find best response quality (longest responses usually = more detailed)
    best_response_length = max(model_data, key=lambda x: x['summary'].get('avg_response_length', 0))
    report.append(f"Most Detailed Responses: {best_response_length['model']} ({int(best_response_length['summary'].get('avg_response_length', 0))} chars avg)")

    report.append("")

    # Question-by-Question Comparison
    report.append("\n" + "=" * 120)
    report.append("QUESTION-BY-QUESTION COMPARISON")
    report.append("=" * 120)
    report.append("")

    # Assuming all models have same 15 questions
    if model_data[0]['questions']:
        for i in range(15):
            question_text = model_data[0]['questions'][i]['question'] if i < len(model_data[0]['questions']) else f"Question {i+1}"

            report.append(f"\nQuestion {i+1}: {question_text}")
            report.append("-" * 120)

            # Table header
            header = f"{'Model':<15} {'Cypher':<10} {'Embed':<10} {'Time(s)':<12} {'Success':<10}"
            report.append(header)
            report.append("-" * 60)

            # Compare each model's response to this question
            for data in model_data:
                if i < len(data['questions']):
                    q = data['questions'][i]
                    success_str = "Yes" if q['success'] else "No"
                    row = f"{data['model']:<15} {q['cypher_count']:<10} {q['embed_count']:<10} " \
                          f"{q['response_time']:<12.2f} {success_str:<10}"
                    report.append(row)

            # Identify winner for this question (fastest successful response)
            successful_models = []
            for data in model_data:
                if i < len(data['questions']) and data['questions'][i]['success']:
                    successful_models.append((data['model'], data['questions'][i]['response_time']))

            if successful_models:
                winner = min(successful_models, key=lambda x: x[1])
                report.append(f"\n  --> Fastest: {winner[0]} ({winner[1]:.2f}s)")

    # Retrieval Performance Comparison
    report.append("\n\n" + "=" * 120)
    report.append("RETRIEVAL PERFORMANCE")
    report.append("=" * 120)
    report.append("")

    header = f"{'Model':<15} {'Avg Cypher Results':<20} {'Avg Embedding Results':<22} {'Total Results':<15}"
    report.append(header)
    report.append("-" * 120)

    for data in model_data:
        s = data['summary']
        avg_cypher = s.get('avg_cypher', 0.0)
        avg_embed = s.get('avg_embedding', 0.0)
        total = avg_cypher + avg_embed

        row = f"{data['model']:<15} {avg_cypher:<20.1f} {avg_embed:<22.1f} {total:<15.1f}"
        report.append(row)

    # Performance Statistics
    report.append("\n\n" + "=" * 120)
    report.append("DETAILED PERFORMANCE STATISTICS")
    report.append("=" * 120)
    report.append("")

    for data in model_data:
        report.append(f"\n{data['model']}:")
        report.append("-" * 50)

        if data['questions']:
            response_times = [q['response_time'] for q in data['questions'] if q['success']]

            if response_times:
                report.append(f"  Fastest Response: {min(response_times):.2f}s")
                report.append(f"  Slowest Response: {max(response_times):.2f}s")
                report.append(f"  Median Response: {sorted(response_times)[len(response_times)//2]:.2f}s")
                report.append(f"  Average Response: {sum(response_times)/len(response_times):.2f}s")

    # Recommendations
    report.append("\n\n" + "=" * 120)
    report.append("RECOMMENDATIONS")
    report.append("=" * 120)
    report.append("")

    # Determine overall best model
    # Weight: 50% success rate, 30% speed, 20% response quality
    scores = []
    for data in model_data:
        s = data['summary']
        success_score = s.get('success_rate', 0) / 100.0
        speed_score = 1.0 / (s.get('avg_response_time', 1.0) + 0.1)  # Inverse of time
        quality_score = min(s.get('avg_response_length', 0) / 1000.0, 1.0)  # Normalize to max 1.0

        total_score = (success_score * 0.5) + (speed_score * 0.3) + (quality_score * 0.2)
        scores.append((data['model'], total_score, success_score, speed_score, quality_score))

    scores.sort(key=lambda x: x[1], reverse=True)

    report.append("Overall Ranking (weighted: 50% success, 30% speed, 20% detail):")
    report.append("")
    for rank, (model, total, success, speed, quality) in enumerate(scores, 1):
        report.append(f"{rank}. {model}")
        report.append(f"   - Total Score: {total:.3f}")
        report.append(f"   - Success: {success:.3f}, Speed: {speed:.3f}, Quality: {quality:.3f}")
        report.append("")

    report.append("Best Model for Production: " + scores[0][0])
    report.append(f"  Reason: Highest combined score across success rate, speed, and response quality.")

    # Footer
    report.append("\n" + "=" * 120)
    report.append("END OF COMPARISON REPORT")
    report.append("=" * 120)

    return '\n'.join(report)


def main():
    """
    Main function to run model comparison.
    """
    print("\n" + "=" * 120)
    print("MODEL COMPARISON TOOL - Step 3.d Quantitative Evaluation")
    print("=" * 120)
    print("\nSearching for test result files...\n")

    # Find all detailed test result files
    output_dir = "outputs"
    pattern = os.path.join(output_dir, "pipeline_test_detailed_*_*.txt")

    files = glob.glob(pattern)

    if not files:
        print(f"[ERROR] No test result files found in {output_dir}/")
        print("Expected pattern: pipeline_test_detailed_<model>_<timestamp>.txt")
        print("\nPlease run the tests first:")
        print("  venv\\Scripts\\python.exe llm_layer\\test_pipeline_detailed.py")
        return

    print(f"Found {len(files)} test result file(s):")
    for f in files:
        print(f"  - {os.path.basename(f)}")

    # Parse each file
    print("\nParsing test results...")
    model_data = []

    for filepath in files:
        try:
            data = parse_detailed_log(filepath)
            if data['questions']:  # Only include if we successfully parsed questions
                model_data.append(data)
                print(f"  [OK] Parsed {data['model']}: {len(data['questions'])} questions")
            else:
                print(f"  [WARNING] Could not parse questions from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  [ERROR] Failed to parse {os.path.basename(filepath)}: {e}")

    if len(model_data) < 2:
        print(f"\n[WARNING] Only found {len(model_data)} model(s) with valid data.")
        print("Need at least 2 models for comparison.")
        print("\nRun tests on more models:")
        print("  venv\\Scripts\\python.exe llm_layer\\test_pipeline_detailed.py")
        return

    # Generate comparison report
    print(f"\nGenerating comparison report for {len(model_data)} model(s)...")
    report = compare_models(model_data)

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"model_comparison_{timestamp}.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] Comparison report saved to: {output_file}")

    # Also print to console
    print("\n" + "=" * 120)
    print("COMPARISON REPORT PREVIEW")
    print("=" * 120)
    print(report)

    print(f"\n[OK] Full report saved to: {output_file}")
    print("\nComparison complete!")


if __name__ == "__main__":
    main()
