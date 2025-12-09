# llm_layer/prompt_builder.py

"""
Prompt Builder - Step 3.b
==========================
Creates structured prompts with:
- PERSONA: Assistant's role
- CONTEXT: Retrieved KG information
- TASK: Instructions for the LLM

This structured approach reduces hallucinations and improves answer quality.
"""

from typing import Dict, Any


class PromptBuilder:
    """
    Builds structured prompts for LLM queries using Context + Persona + Task format.
    """

    def __init__(self, persona: str = None):
        """
        Initialize prompt builder with optional custom persona.

        Args:
            persona: Custom persona description (uses default if None)
        """
        self.persona = persona or self._default_persona()

    def _default_persona(self) -> str:
        """
        Default persona for airline insights assistant.

        Returns:
            Persona description string
        """
        return """You are an airline company insights assistant. Your role is to analyze
flight performance data and passenger satisfaction metrics to help the airline
improve service quality. You provide factual, data-driven insights based on
actual flight records and passenger feedback."""

    def build_prompt(
        self,
        user_query: str,
        context: str,
        include_instructions: bool = True
    ) -> str:
        """
        Build complete structured prompt with Persona + Context + Task.

        Args:
            user_query: The user's natural language question
            context: Retrieved KG information (formatted)
            include_instructions: Whether to include safety instructions

        Returns:
            Complete prompt string ready for LLM
        """
        prompt_parts = []

        # === PERSONA SECTION ===
        prompt_parts.append("=" * 80)
        prompt_parts.append("PERSONA:")
        prompt_parts.append("=" * 80)
        prompt_parts.append(self.persona.strip())
        prompt_parts.append("")

        # === CONTEXT SECTION ===
        prompt_parts.append("=" * 80)
        prompt_parts.append("CONTEXT (Knowledge Graph Data):")
        prompt_parts.append("=" * 80)
        prompt_parts.append(context.strip())
        prompt_parts.append("")

        # === TASK SECTION ===
        prompt_parts.append("=" * 80)
        prompt_parts.append("TASK:")
        prompt_parts.append("=" * 80)
        prompt_parts.append(f"Answer the following question based ONLY on the CONTEXT provided above.")
        prompt_parts.append("")

        # Safety instructions (prevent hallucination)
        if include_instructions:
            prompt_parts.append("IMPORTANT INSTRUCTIONS:")
            prompt_parts.append("1. Use ONLY the information provided in the CONTEXT section")
            prompt_parts.append("2. If the CONTEXT doesn't contain enough information, say: 'I don't have sufficient data to answer this question'")
            prompt_parts.append("3. Provide specific examples from the data (journey IDs, metrics, numbers)")
            prompt_parts.append("4. Be concise and factual - avoid speculation")
            prompt_parts.append("5. Do NOT make up or hallucinate any flight numbers, delays, or statistics")
            prompt_parts.append("6. If you see conflicting data, mention both sources")
            prompt_parts.append("")

        # === USER QUESTION ===
        prompt_parts.append("-" * 80)
        prompt_parts.append("USER QUESTION:")
        prompt_parts.append(user_query.strip())
        prompt_parts.append("-" * 80)
        prompt_parts.append("")

        # === ANSWER SECTION ===
        prompt_parts.append("YOUR ANSWER:")
        prompt_parts.append("(Provide a clear, factual answer based on the CONTEXT above)")
        prompt_parts.append("")

        return "\n".join(prompt_parts)

    def build_simple_prompt(self, user_query: str, context: str) -> str:
        """
        Build a simpler prompt format (for models that prefer less structure).

        Args:
            user_query: User's question
            context: Retrieved KG data

        Returns:
            Simple prompt string
        """
        return f"""You are an airline insights assistant.

Based on this data:
{context}

Answer this question: {user_query}

Use only the data provided. Be specific and factual."""

    def build_few_shot_prompt(
        self,
        user_query: str,
        context: str,
        examples: list = None
    ) -> str:
        """
        Build prompt with few-shot examples to guide the model.

        Args:
            user_query: User's question
            context: Retrieved KG data
            examples: List of example Q&A pairs

        Returns:
            Few-shot prompt string
        """
        examples = examples or self._default_examples()

        prompt_parts = []
        prompt_parts.append(self.persona)
        prompt_parts.append("")
        prompt_parts.append("Here are some example questions and answers:")
        prompt_parts.append("")

        # Add examples
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"Example {i}:")
            prompt_parts.append(f"Q: {example['question']}")
            prompt_parts.append(f"A: {example['answer']}")
            prompt_parts.append("")

        # Add actual query
        prompt_parts.append("Now answer this question based on the provided data:")
        prompt_parts.append("")
        prompt_parts.append("DATA:")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append(f"QUESTION: {user_query}")
        prompt_parts.append("")
        prompt_parts.append("ANSWER:")

        return "\n".join(prompt_parts)

    def _default_examples(self) -> list:
        """
        Default few-shot examples for airline queries.

        Returns:
            List of example Q&A dictionaries
        """
        return [
            {
                "question": "Which flights have the longest delays?",
                "answer": "Based on the data, Journey J_123 has the longest delay at 104 minutes, followed by Journey J_456 with 87 minutes delay. Both are Economy class flights."
            },
            {
                "question": "What is the average food satisfaction score?",
                "answer": "The average food satisfaction across the provided journeys is 2.3 out of 5, indicating below-average food quality."
            }
        ]

    def set_persona(self, persona: str):
        """
        Update the persona description.

        Args:
            persona: New persona string
        """
        self.persona = persona

    def get_persona_variants(self) -> Dict[str, str]:
        """
        Get different persona variants for different tasks.

        Returns:
            Dictionary of persona variants
        """
        return {
            "default": self._default_persona(),

            "detailed": """You are an expert airline operations analyst with deep knowledge of
passenger satisfaction metrics, flight performance indicators, and service quality
assessment. You provide comprehensive, data-driven insights with specific
recommendations for operational improvements.""",

            "concise": """You are an airline data assistant. Provide brief, factual answers
based on flight data.""",

            "executive": """You are an executive airline insights advisor. Provide high-level
strategic insights focusing on business impact, customer satisfaction trends,
and actionable recommendations for senior management.""",

            "technical": """You are a technical airline data analyst. Provide precise statistical
analysis of flight operations data, including exact metrics, percentages, and
data-driven observations."""
        }


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo: Build different types of prompts.
    """
    print("\n" + "="*80)
    print("PROMPT BUILDER DEMO - Step 3.b")
    print("="*80 + "\n")

    # Sample context
    sample_context = """
KNOWLEDGE GRAPH DATA (Intent: delay_analysis):
================================================================================

1. EXACT MATCHES from database query (2 results):
--------------------------------------------------------------------------------

Result 1:
  Journey ID: J_123
  Passenger Class: Economy
  Food Satisfaction: 2/5
  Arrival Delay: 104 minutes
  Distance: 1400 miles
  Number of Legs: 1

2. SEMANTIC MATCHES from AI similarity search (1 results):
--------------------------------------------------------------------------------

Result 1:
  Journey ID: J_789
  Passenger Class: Economy
  Food Satisfaction: 1/5
  Arrival Delay: 109 minutes
  Distance: 719 miles
  Number of Legs: 3
  Similarity Score: 0.831

3. SUMMARY:
--------------------------------------------------------------------------------
Total unique journeys found: 3
Average arrival delay: 106.5 minutes
Average food satisfaction: 1.7/5
"""

    sample_query = "Which flights have the worst delays and passenger experience?"

    # Test 1: Standard structured prompt
    print("TEST 1: Standard Structured Prompt")
    print("=" * 80)
    builder = PromptBuilder()
    standard_prompt = builder.build_prompt(sample_query, sample_context)
    print(standard_prompt)
    print("\n\n")

    # Test 2: Simple prompt
    print("TEST 2: Simple Prompt")
    print("=" * 80)
    simple_prompt = builder.build_simple_prompt(sample_query, sample_context)
    print(simple_prompt)
    print("\n\n")

    # Test 3: Different personas
    print("TEST 3: Persona Variants")
    print("=" * 80)
    personas = builder.get_persona_variants()
    for name, persona in personas.items():
        print(f"\n{name.upper()} PERSONA:")
        print("-" * 40)
        print(persona.strip())
        print()

    print("\n" + "="*80)
    print("Prompt Builder demo completed!")
    print("="*80)
