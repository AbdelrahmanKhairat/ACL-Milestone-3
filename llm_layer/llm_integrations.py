# llm_layer/llm_integrations.py

"""
LLM Integrations - Step 3.c
============================
Integrates multiple LLM models for comparison:
1. Gemma-2-2b-it (HuggingFace)
2. Llama-3.2-3b-instruct (HuggingFace)
3. Qwen2.5-3b-instruct (HuggingFace)

All using FREE HuggingFace Inference API.
"""

import time
import requests
from typing import Dict, Any, Optional


class LLMIntegration:
    """
    Manages connections to multiple LLM models via HuggingFace Inference API.
    """

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize LLM integration.

        Args:
            hf_token: HuggingFace API token (optional for public models)
        """
        self.hf_token = hf_token
        self.base_url = "https://api-inference.huggingface.co/models/"  # Updated endpoint

        # Model configurations
        self.models = {
            "gemma": {
                "name": "google/gemma-2-2b-it",
                "max_tokens": 512,
                "temperature": 0.7
            },
            "llama": {
                "name": "meta-llama/Llama-3.2-3B-Instruct",
                "max_tokens": 512,
                "temperature": 0.7
            },
            "qwen": {
                "name": "Qwen/Qwen2.5-3B-Instruct",
                "max_tokens": 512,
                "temperature": 0.7
            }
        }

    def query_model(
        self,
        prompt: str,
        model_key: str = "gemma",
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
        if model_key not in self.models:
            raise ValueError(f"Unknown model: {model_key}. Choose from: {list(self.models.keys())}")

        model_config = self.models[model_key]
        model_name = model_config["name"]

        start_time = time.time()

        try:
            response = self._call_huggingface_api(
                model_name,
                prompt,
                max_tokens,
                temperature
            )

            end_time = time.time()

            return {
                "model": model_key,
                "model_full_name": model_name,
                "answer": response["generated_text"],
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

    def _call_huggingface_api(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Call HuggingFace Inference API.

        Args:
            model_name: Full model name on HuggingFace
            prompt: Prompt text
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            API response dictionary
        """
        url = f"{self.base_url}{model_name}"

        headers = {}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            # HuggingFace returns a list, take first result
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")

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
# Fallback: Local Model (if API fails)
# ==========================================

class LocalLLM:
    """
    Fallback to local transformer model if API is unavailable.
    Uses sentence-transformers for simple question answering.
    """

    def __init__(self):
        self.available = False
        try:
            from transformers import pipeline
            self.generator = pipeline("text-generation", model="gpt2")
            self.available = True
        except ImportError:
            print("Warning: transformers not installed. Local LLM unavailable.")

    def generate(self, prompt: str, max_length: int = 200) -> str:
        """
        Generate text using local model.

        Args:
            prompt: Input prompt
            max_length: Maximum generation length

        Returns:
            Generated text
        """
        if not self.available:
            return "Local LLM not available. Please install transformers."

        result = self.generator(prompt, max_length=max_length, num_return_sequences=1)
        return result[0]['generated_text']


# ==========================================
# Demo / Test
# ==========================================

if __name__ == "__main__":
    """
    Demo: Query LLM models with sample prompt.
    """
    print("\n" + "="*80)
    print("LLM INTEGRATION DEMO - Step 3.c")
    print("="*80 + "\n")

    # Sample prompt
    sample_prompt = """You are an airline insights assistant.

Based on this data:
- Journey J_123: Economy class, 104 min delay, food 2/5
- Journey J_456: Business class, 45 min delay, food 3/5
- Journey J_789: Economy class, 109 min delay, food 1/5

Answer: Which flights have the worst passenger experience?

Answer:"""

    # Initialize LLM integration
    llm = LLMIntegration()

    print("Testing LLM models...")
    print("Note: First run may be slow as models load on HuggingFace servers\n")

    # Test single model
    print("TEST 1: Single Model Query (Gemma)")
    print("-" * 80)
    result = llm.query_model(sample_prompt, model_key="gemma")

    if result["success"]:
        print(f"Model: {result['model_full_name']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        print(f"\nAnswer:\n{result['answer']}")
    else:
        print(f"Error: {result['error']}")

    print("\n\n")

    # Test all models
    print("TEST 2: Compare All Models")
    print("-" * 80)
    print("Querying all 3 models (this may take 30-60 seconds)...\n")

    comparison = llm.compare_models(sample_prompt)
    print(comparison)

    print("\n" + "="*80)
    print("LLM Integration demo completed!")
    print("="*80)
    print("\nNOTE: If you see errors, you may need a HuggingFace token.")
    print("Get one at: https://huggingface.co/settings/tokens")
    print("Then pass it: LLMIntegration(hf_token='your_token_here')")
