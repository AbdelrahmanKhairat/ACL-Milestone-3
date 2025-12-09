from llm_integration_v3 import LLMIntegration


llm = LLMIntegration(hf_token="your_token")

print(llm.query_model("Capital of Egypt?", model_key="gemma"))
# print(llm.query_model("Capital of France ?", model_key="llama"))
# print(llm.query_model("Explain quantum computing simply", model_key="qwen"))