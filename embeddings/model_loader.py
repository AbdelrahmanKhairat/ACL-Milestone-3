from sentence_transformers import SentenceTransformer

# Register the models you want to compare
MODEL_CONFIG = {
    "minilm": {
        "hf_name": "sentence-transformers/all-MiniLM-L6-v2",
        "dim": 384,
    },
    "e5_base": {
        "hf_name": "intfloat/multilingual-e5-base",
        "dim": 768,
    },
}

_loaded_models = {}


def get_model(model_key: str) -> SentenceTransformer:
    """
    Lazy-load and cache models by key: 'minilm', 'e5_base', ...
    """
    if model_key not in MODEL_CONFIG:
        raise ValueError(f"Unknown model_key: {model_key}")
    if model_key not in _loaded_models:
        print(f"Loading embedding model: {model_key}")
        _loaded_models[model_key] = SentenceTransformer(
            MODEL_CONFIG[model_key]["hf_name"]
        )
    return _loaded_models[model_key]


def embed_texts(texts, model_key="minilm"):
    """
    Encode a list of strings into a list of vectors (list[float]).
    """
    model = get_model(model_key)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()  # convert numpy array -> python list