"""
Configurações gerais da aplicação.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Application
    app_name: str = "Agente BSC"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    
    # Cohere
    cohere_api_key: str
    
    # Anthropic (para Contextual Retrieval)
    anthropic_api_key: Optional[str] = None
    
    # Vector Store Configuration
    vector_store_type: str = "qdrant"  # 'qdrant', 'weaviate', ou 'redis'
    vector_store_index: str = "bsc_documents"
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Weaviate
    weaviate_host: str = "localhost"
    weaviate_port: int = 8080
    
    # Redis (mantido para compatibilidade)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_index_name: str = "bsc_knowledge"
    
    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 10
    top_n_rerank: int = 5
    hybrid_search_weight_semantic: float = 0.7
    hybrid_search_weight_bm25: float = 0.3
    
    # Contextual Retrieval (Anthropic)
    enable_contextual_retrieval: bool = True
    contextual_model: str = "claude-3-5-sonnet-20241022"
    contextual_cache_enabled: bool = True
    
    # Agent Configuration
    max_iterations: int = 10
    temperature: float = 0.0
    max_tokens: int = 2000
    
    # Embedding Fine-tuning
    use_finetuned_embeddings: bool = False
    finetuned_model_path: str = "./models/bsc-embeddings"
    
    # Human-in-the-loop
    require_approval_for_critical: bool = True
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Paths
    data_dir: str = "./data"
    literature_dir: str = "./data/bsc_literature"
    models_dir: str = "./models"
    logs_dir: str = "./logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()


# Ensure directories exist
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.literature_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)
