# llm_layer/llm_integrations_v2.py

"""
LLM Integrations V2 - Fixed for HuggingFace API Changes
========================================================
Uses huggingface_hub library instead of direct API calls.
Supports 3 free LLM models for comparison.
"""

import time
from typing import Dict, Any, Optional


class LLMIntegration:
    """
    Manages connections to multiple LLM models via HuggingFace Hub.
    """

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize LLM integration.

        Args:
            hf_token: HuggingFace API token (optional but recommended)
        """
        self.hf_token = hf_token
        self.client = None

        # Try to import huggingface_hub
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=hf_token)
            self.available = True
        except ImportError:
            print("Warning: huggingface_hub not installed. Please install:")
            print("  pip install huggingface-hub")
            self.available = False

        # Model configurations (TESTED AND WORKING - from v3)
        self.models = {
            "openai": {
                "name": "openai/gpt-oss-120b",
                "type": "chat",
                "max_tokens": 512,
                "temperature": 0.7
            },
            "qwen": {
                "name": "Qwen/Qwen2.5-7B-Instruct",
                "type": "chat",
                "max_tokens": 512,
                "temperature": 0.7
            },
            "llama": {
                "name": "meta-llama/Llama-3.1-8B-Instruct",
                "type": "chat",
                "max_tokens": 512,
                "temperature": 0.7
            }
        }

    def query_model(
        self,
        prompt: str,
        model_key: str = "llama",
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Query a specific LLM model.

        Args:
            prompt: The prompt to send
            model_key: Model identifier (gemma, llama, qwen)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dictionary with response and metadata
        """
        if not self.available:
            return {
                "model": model_key,
                "model_full_name": "N/A",
                "answer": "Error: huggingface_hub not installed. Run: pip install huggingface-hub",
                "response_time": 0,
                "success": False,
                "error": "Module not installed"
            }

        if model_key not in self.models:
            raise ValueError(f"Unknown model: {model_key}. Choose from: {list(self.models.keys())}")

        model_config = self.models[model_key]
        model_name = model_config["name"]

        start_time = time.time()

        try:
            # Use the correct API based on model type (same as v3)
            model_type = model_config.get("type", "chat")

            if model_type == "text":
                # Text generation models (like Phi-3)
                result = self.client.text_generation(
                    model=model_name,
                    prompt=prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                )
                answer = result
            else:
                # Chat models (OpenAI, Qwen, Llama)
                result = self.client.chat_completion(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                answer = result.choices[0].message["content"]

            end_time = time.time()

            return {
                "model": model_key,
                "model_full_name": model_name,
                "answer": answer,
                "response_time": end_time - start_time,
                "success": True,
                "error": None
            }

        except Exception as e:
            end_time = time.time()
            return {
                "model": model_key,
                "model_full_name": model_name,
                "answer": f"Error: {str(e)}",
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }

    def query_all_models(self, prompt: str) -> Dict[str, Dict[str, Any]]:
        """
        Query all configured models with the same prompt.

        Args:
            prompt: Prompt to send to all models

        Returns:
            Dictionary mapping model_key -> response
        """
        results = {}

        for model_key in self.models.keys():
            print(f"Querying {model_key}...")
            results[model_key] = self.query_model(prompt, model_key)

        return results

    def compare_models(self, prompt: str) -> str:
        """
        Query all models and create comparison summary.

        Args:
            prompt: Prompt to send to all models

        Returns:
            Formatted comparison string
        """
        results = self.query_all_models(prompt)

        comparison = []
        comparison.append("=" * 80)
        comparison.append("MODEL COMPARISON RESULTS")
        comparison.append("=" * 80)

        for model_key, result in results.items():
            comparison.append(f"\n{'-'*80}")
            comparison.append(f"MODEL: {result['model_full_name']}")
            comparison.append(f"{'-'*80}")
            comparison.append(f"Response Time: {result['response_time']:.2f} seconds")
            comparison.append(f"Success: {result['success']}")

            if result['success']:
                comparison.append(f"\nAnswer:\n{result['answer']}")
            else:
                comparison.append(f"\nError: {result['error']}")

        return "\n".join(comparison)


# ==========================================
# Simple Fallback (No API needed)
# ==========================================

class SimpleLLM:
    """
    Simple rule-based fallback when APIs are unavailable.
    Provides basic question answering from KG context.
    """

    def __init__(self):
        self.available = True

    def query_model(self, prompt: str, model_key: str = "simple") -> Dict[str, Any]:
        """
        Generate a simple answer by extracting key information from prompt.

        Args:
            prompt: The full prompt (includes context)
            model_key: Ignored (kept for compatibility)

        Returns:
            Dictionary with simple answer
        """
        start_time = time.time()

        try:
            # Extract context section
            if "CONTEXT" in prompt:
                context_start = prompt.find("CONTEXT:")
                context_end = prompt.find("TASK:")
                if context_start != -1 and context_end != -1:
                    context = prompt[context_start:context_end]
                else:
                    context = prompt

                # Simple extraction of key info
                answer = self._extract_key_info(context)
            else:
                answer = "I found information in the data, but need better context parsing."

            end_time = time.time()

            return {
                "model": "simple_fallback",
                "model_full_name": "Simple Rule-Based Fallback",
                "answer": answer,
                "response_time": end_time - start_time,
                "success": True,
                "error": None
            }

        except Exception as e:
            end_time = time.time()
            return {
                "model": "simple_fallback",
                "model_full_name": "Simple Rule-Based Fallback",
                "answer": f"Error: {str(e)}",
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e)
            }

    def _extract_key_info(self, context: str) -> str:
        """Extract key information from context."""
        lines = context.split('\n')

        answer_parts = ["Based on the available data:\n"]

        # Find result entries
        for i, line in enumerate(lines):
            if "Result" in line and ":" in line:
                # Extract next few lines
                result_info = []
                for j in range(i, min(i+7, len(lines))):
                    if lines[j].strip():
                        result_info.append(lines[j].strip())

                if result_info:
                    answer_parts.append("- " + ", ".join(result_info[:3]))

        if len(answer_parts) == 1:
            answer_parts.append("Data was retrieved from the knowledge graph.")

        return "\n".join(answer_parts)


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo: Test LLM integration with new API.
    """
    print("\n" + "="*80)
    print("LLM INTEGRATION V2 DEMO")
    print("="*80 + "\n")

    # Sample prompt
    sample_prompt = """You are an airline insights assistant.

Based on this data:
- Journey J_123: Economy class, 104 min delay, food 2/5
- Journey J_456: Business class, 45 min delay, food 3/5

Answer: Which flights have the worst passenger experience?

Answer:"""

    print("Testing with HuggingFace Hub library...")
    print("Note: You may need to install: pip install huggingface-hub\n")

    # Try HuggingFace Hub
    llm = LLMIntegration()

    if llm.available:
        print("HuggingFace Hub available! Testing model...\n")
        result = llm.query_model(sample_prompt, model_key="qwen")

        if result["success"]:
            print(f"Model: {result['model_full_name']}")
            print(f"Response Time: {result['response_time']:.2f}s")
            print(f"\nAnswer:\n{result['answer']}")
        else:
            print(f"Error: {result['error']}")
            print("\nTrying simple fallback...")
    else:
        print("HuggingFace Hub not available. Using simple fallback...\n")

    # Fallback
    print("\n" + "-"*80)
    print("FALLBACK: Simple Rule-Based System")
    print("-"*80 + "\n")

    simple = SimpleLLM()
    result = simple.query_model(sample_prompt)
    print(f"Answer:\n{result['answer']}")

    print("\n" + "="*80)
    print("Demo completed!")
    print("="*80)
