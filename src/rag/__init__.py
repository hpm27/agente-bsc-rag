"""
Módulo RAG - Retrieval Augmented Generation.

Contém todas as implementações de vector stores, retrieval,
chunking, embeddings e re-ranking para o Agente BSC.
"""

# Base classes
from .base_vector_store import BaseVectorStore, SearchResult, VectorStoreStats

# Vector Store implementations
from .qdrant_vector_store import QdrantVectorStore, create_qdrant_vector_store
from .weaviate_vector_store import WeaviateVectorStore, create_weaviate_vector_store
from .redis_vector_store import RedisVectorStore, create_redis_vector_store

# Factory
from .vector_store_factory import (
    create_vector_store,
    get_recommended_vector_store,
    compare_vector_stores,
    print_vector_store_comparison
)

# Legacy compatibility (mantém import antigo funcionando)
from .redis_vector_store import RedisVectorStore as RedisVectorStore  # noqa

__all__ = [
    # Base
    'BaseVectorStore',
    'SearchResult',
    'VectorStoreStats',
    
    # Implementations
    'QdrantVectorStore',
    'WeaviateVectorStore',
    'RedisVectorStore',
    
    # Factory functions
    'create_qdrant_vector_store',
    'create_weaviate_vector_store',
    'create_redis_vector_store',
    'create_vector_store',
    'get_recommended_vector_store',
    'compare_vector_stores',
    'print_vector_store_comparison',
]

