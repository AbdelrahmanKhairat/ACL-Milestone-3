# llm_layer/llm_integrations_v2.py

import time
from typing import Dict, Any, Optional


class LLMIntegration:
    """
    Works with real FREE HuggingFace models:
      - OpenAI/gpt-oss-120b          (chat)
      - Meta-Llama/Llama-3.1-8B-Instruct (chat)
      - Qwen/Qwen2.5-7B-Instruct          (chat)
    """

    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token
        self.client = None

        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=hf_token)
            self.available = True
        except ImportError:
            print("Missing library: pip install huggingface-hub")
            self.available = False

        # Only models that work 100% free
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

    def query_model(self, prompt, model_key="phi", max_tokens=512, temperature=0.7):
        if not self.available:
            return {"success": False, "error": "HuggingFace client not available"}

        if model_key not in self.models:
            raise ValueError(f"Unknown model: {list(self.models.keys())}")

        cfg = self.models[model_key]
        model = cfg["name"]
        start = time.time()

        try:
            # TEXT MODEL (Phi-3)
            if cfg["type"] == "text":
                result = self.client.text_generation(
                    model=model,
                    prompt=prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                )
                answer = result

            # CHAT MODEL (Qwen)
            else:
                result = self.client.chat_completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                answer = result.choices[0].message["content"]

            return {
                "success": True,
                "model": model,
                "answer": answer,
                "response_time": time.time() - start,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "model": model,
                "answer": None,
                "response_time": time.time() - start,
                "error": str(e),
            }
