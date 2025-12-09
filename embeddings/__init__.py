# embeddings/__init__.py

"""
Embeddings Module for Graph-RAG System
=======================================
This module contains embedding-based retrieval components:
- feature_vector_builder.py: Build and store embeddings (Step 2.b)
- similarity_search.py: Search by semantic similarity (Step 1.c + 2.b)
"""

from .feature_vector_builder import FeatureVectorBuilder, load_config
from .similarity_search import SimilaritySearcher

__all__ = ["FeatureVectorBuilder", "SimilaritySearcher", "load_config"]
