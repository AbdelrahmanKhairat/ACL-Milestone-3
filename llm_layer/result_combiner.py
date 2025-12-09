# llm_layer/result_combiner.py

"""
Result Combiner - Step 3.a
===========================
Combines results from:
- Step 2.a: Cypher query results (baseline)
- Step 2.b: Embedding similarity search results

Creates unified context for LLM consumption.
"""

from typing import Dict, Any, List


class ResultCombiner:
    """
    Combines Cypher query results and embedding search results into unified context.
    """

    def __init__(self):
        pass

    def combine_results(
        self,
        cypher_response: Dict[str, Any],
        embedding_response: Dict[str, Any],
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Merge Cypher and embedding results into unified context.

        Args:
            cypher_response: Response from QueryExecutor.execute_query()
            embedding_response: Response from SimilaritySearcher.search_by_query()
            max_results: Maximum number of results to include

        Returns:
            Dictionary with combined results and formatted context
        """
        # Extract results
        cypher_results = cypher_response.get("results", [])[:max_results]
        embedding_results = embedding_response.get("results", [])[:max_results]

        # Remove duplicates (if journey appears in both)
        unique_results = self._merge_and_deduplicate(cypher_results, embedding_results)

        # Format for LLM
        formatted_context = self._format_for_llm(
            cypher_results,
            embedding_results,
            unique_results,
            cypher_response.get("intent", "unknown")
        )

        return {
            "cypher_results": cypher_results,
            "embedding_results": embedding_results,
            "unique_results": unique_results,
            "formatted_context": formatted_context,
            "total_count": len(unique_results)
        }

    def _merge_and_deduplicate(
        self,
        cypher_results: List[Dict],
        embedding_results: List[Dict]
    ) -> List[Dict]:
        """
        Merge results and remove duplicates based on feedback_ID.

        Args:
            cypher_results: Results from Cypher query
            embedding_results: Results from embedding search

        Returns:
            List of unique results
        """
        seen_ids = set()
        unique = []

        # Add cypher results first (they're exact matches, higher priority)
        for result in cypher_results:
            feedback_id = self._extract_id(result)
            if feedback_id and feedback_id not in seen_ids:
                result["source"] = "cypher"
                unique.append(result)
                seen_ids.add(feedback_id)

        # Add embedding results (semantic matches)
        for result in embedding_results:
            feedback_id = result.get("feedback_ID")
            if feedback_id and feedback_id not in seen_ids:
                result["source"] = "embedding"
                unique.append(result)
                seen_ids.add(feedback_id)

        return unique

    def _extract_id(self, result: Dict) -> str:
        """
        Extract feedback_ID from a result (handles nested structures).

        Args:
            result: Result dictionary

        Returns:
            feedback_ID string or None
        """
        # Direct access
        if "feedback_ID" in result:
            return result["feedback_ID"]

        # Check nested journey object
        if "j" in result and isinstance(result["j"], dict):
            return result["j"].get("feedback_ID")

        return None

    def _format_for_llm(
        self,
        cypher_results: List[Dict],
        embedding_results: List[Dict],
        unique_results: List[Dict],
        intent: str
    ) -> str:
        """
        Format combined results into natural language context for LLM.

        Args:
            cypher_results: Cypher query results
            embedding_results: Embedding search results
            unique_results: Merged unique results
            intent: User's classified intent

        Returns:
            Formatted context string
        """
        context_parts = []

        # Header
        context_parts.append(f"KNOWLEDGE GRAPH DATA (Intent: {intent}):")
        context_parts.append("=" * 80)

        # Section 1: Exact matches from Cypher
        if cypher_results:
            context_parts.append(f"\n1. EXACT MATCHES from database query ({len(cypher_results)} results):")
            context_parts.append("-" * 80)
            for i, result in enumerate(cypher_results[:5], 1):  # Top 5
                formatted = self._format_single_result(result, i)
                context_parts.append(formatted)
        else:
            context_parts.append("\n1. EXACT MATCHES: No exact matches found.")

        # Section 2: Semantic matches from embeddings
        if embedding_results:
            context_parts.append(f"\n2. SEMANTIC MATCHES from AI similarity search ({len(embedding_results)} results):")
            context_parts.append("-" * 80)
            for i, result in enumerate(embedding_results[:5], 1):  # Top 5
                formatted = self._format_single_result(result, i, include_score=True)
                context_parts.append(formatted)
        else:
            context_parts.append("\n2. SEMANTIC MATCHES: No similar journeys found.")

        # Section 3: Summary statistics
        context_parts.append(f"\n3. SUMMARY:")
        context_parts.append("-" * 80)
        context_parts.append(f"Total unique journeys found: {len(unique_results)}")
        context_parts.append(f"From exact database queries: {len(cypher_results)}")
        context_parts.append(f"From semantic similarity: {len(embedding_results)}")

        # Calculate statistics if we have results
        if unique_results:
            avg_delay = self._calculate_avg(unique_results, "arrival_delay_minutes")
            avg_food = self._calculate_avg(unique_results, "food_satisfaction_score")

            if avg_delay is not None:
                context_parts.append(f"Average arrival delay: {avg_delay:.1f} minutes")
            if avg_food is not None:
                context_parts.append(f"Average food satisfaction: {avg_food:.1f}/5")

        context_parts.append("=" * 80)

        return "\n".join(context_parts)

    def _format_single_result(
        self,
        result: Dict,
        index: int,
        include_score: bool = False
    ) -> str:
        """
        Format a single result into readable text.

        Args:
            result: Result dictionary
            index: Result number
            include_score: Whether to include similarity score

        Returns:
            Formatted result string
        """
        lines = [f"\nResult {index}:"]

        # Extract fields (handle nested structures)
        feedback_id = result.get("feedback_ID") or self._extract_id(result)
        passenger_class = result.get("passenger_class", "Unknown")
        food_score = result.get("food_satisfaction_score", "N/A")
        delay = result.get("arrival_delay_minutes", "N/A")
        miles = result.get("actual_flown_miles", "N/A")
        legs = result.get("number_of_legs", "N/A")
        score = result.get("score")

        # Format details
        if feedback_id:
            lines.append(f"  Journey ID: {feedback_id}")
        lines.append(f"  Passenger Class: {passenger_class}")
        lines.append(f"  Food Satisfaction: {food_score}/5")
        lines.append(f"  Arrival Delay: {delay} minutes")
        lines.append(f"  Distance: {miles} miles")
        lines.append(f"  Number of Legs: {legs}")

        if include_score and score is not None:
            lines.append(f"  Similarity Score: {score:.3f}")

        return "\n".join(lines)

    def _calculate_avg(self, results: List[Dict], field: str) -> float:
        """
        Calculate average of a numeric field across results.

        Args:
            results: List of result dictionaries
            field: Field name to average

        Returns:
            Average value or None if no valid values
        """
        values = []
        for result in results:
            value = result.get(field)
            if value is not None and isinstance(value, (int, float)):
                values.append(value)

        return sum(values) / len(values) if values else None


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo: Combine Cypher and embedding results.
    """
    print("\n" + "="*80)
    print("RESULT COMBINER DEMO - Step 3.a")
    print("="*80 + "\n")

    # Mock Cypher results
    cypher_response = {
        "intent": "delay_analysis",
        "results": [
            {
                "feedback_ID": "J_123",
                "passenger_class": "Economy",
                "food_satisfaction_score": 2,
                "arrival_delay_minutes": 104,
                "actual_flown_miles": 1400,
                "number_of_legs": 1
            },
            {
                "feedback_ID": "J_456",
                "passenger_class": "Business",
                "food_satisfaction_score": 3,
                "arrival_delay_minutes": 45,
                "actual_flown_miles": 800,
                "number_of_legs": 1
            }
        ],
        "count": 2
    }

    # Mock embedding results
    embedding_response = {
        "query": "long delays and poor food",
        "results": [
            {
                "feedback_ID": "J_789",
                "passenger_class": "Economy",
                "food_satisfaction_score": 1,
                "arrival_delay_minutes": 109,
                "actual_flown_miles": 719,
                "number_of_legs": 3,
                "score": 0.831
            },
            {
                "feedback_ID": "J_123",  # Duplicate with cypher
                "passenger_class": "Economy",
                "food_satisfaction_score": 2,
                "arrival_delay_minutes": 104,
                "actual_flown_miles": 1400,
                "number_of_legs": 1,
                "score": 0.825
            }
        ],
        "count": 2
    }

    # Combine results
    combiner = ResultCombiner()
    combined = combiner.combine_results(cypher_response, embedding_response)

    print("COMBINED RESULTS:")
    print(f"Total unique journeys: {combined['total_count']}")
    print(f"\nFormatted Context for LLM:\n")
    print(combined['formatted_context'])

    print("\n" + "="*80)
    print("Result Combiner demo completed!")
    print("="*80)
