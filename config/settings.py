"""
Configurações gerais da aplicação.
"""
from pydantic_settings import BaseSettings
from typing import Optional, Any, Dict
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Application
    app_name: str = "Agente BSC"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # OpenAI
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-large"
    
    # Default LLM Model (provider-agnostico: pode ser gpt-* ou claude-*)
    default_llm_model: str = "claude-sonnet-4-5-20250929"
    
    # Cohere
    cohere_api_key: str
    
    # Anthropic (para Contextual Retrieval)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    
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
    
    # Contextual Retrieval (Anthropic ou OpenAI)
    enable_contextual_retrieval: bool = True
    contextual_model: str = "claude-sonnet-4-5-20250929"
    contextual_cache_enabled: bool = True
    contextual_provider: str = "openai"  # "openai" ou "anthropic"
    
    # GPT-5 Configuration (para Contextual Retrieval)
    gpt5_model: str = "gpt-5-2025-08-07"
    gpt5_max_completion_tokens: int = 2048
    gpt5_reasoning_effort: str = "minimal"  # "minimal", "low", "medium", "high"
    
    # Agent Configuration
    max_iterations: int = 10
    temperature: float = 0.0
    max_tokens: int = 2000
    agent_max_workers: int = 4
    
    # Embedding Fine-tuning
    use_finetuned_embeddings: bool = False
    finetuned_model_path: str = "./models/bsc-embeddings"
    
    # Embedding Cache Configuration
    embedding_cache_enabled: bool = True
    embedding_cache_dir: str = ".cache/embeddings"
    embedding_cache_ttl_days: int = 30
    embedding_cache_max_size_gb: int = 5
    
    # Query Decomposition (RAG Avancado - Fase 2A.1)
    enable_query_decomposition: bool = True
    decomposition_min_query_length: int = 30
    decomposition_score_threshold: int = 1
    decomposition_llm: str = "gpt-4o-mini"
    
    # Diversity Re-ranking (RAG Avançado - Fase 2A.2)
    enable_diversity_reranking: bool = True
    diversity_lambda: float = 0.5  # Balanceamento: 0.5 = equilibrado relevância/diversidade
    diversity_threshold: float = 0.8  # Similaridade máxima permitida entre docs
    metadata_boost_enabled: bool = True
    metadata_source_boost: float = 0.2  # Boost 20% para sources diferentes
    metadata_perspective_boost: float = 0.15  # Boost 15% para perspectives BSC diferentes
    adaptive_topn_enabled: bool = True  # Ajustar top_n baseado em complexidade da query
    
    # Router Inteligente (RAG Avançado - Fase 2A.3)
    enable_query_router: bool = True
    router_use_llm_fallback: bool = True  # Usar LLM para queries ambíguas (20% casos)
    router_llm_model: str = "gpt-4o-mini"  # Modelo para LLM fallback
    router_confidence_threshold: float = 0.8  # Threshold para confiar na heurística
    router_log_decisions: bool = True  # Logar todas decisões de routing
    router_log_file: str = "logs/routing_decisions.jsonl"
    simple_query_max_words: int = 30  # Threshold para queries simples
    complex_query_min_words: int = 30  # Threshold para queries complexas
    relational_keywords: str = "relação,impacto,causa,efeito,depende,influencia,deriva"
    enable_direct_answer_cache: bool = True  # Cache para DirectAnswerStrategy
    direct_answer_cache_ttl: int = 3600  # TTL do cache (1 hora)
    
    # Auto-Geração de Metadados (Fase 2 - Organização)
    enable_auto_metadata_generation: bool = True  # Gerar metadados com LLM para docs novos
    save_auto_metadata: bool = True  # Salvar metadados gerados no index.json
    auto_metadata_model: str = "gpt-4o-mini"  # Modelo para extração (barato e rápido)
    auto_metadata_content_limit: int = 3000  # Palavras do documento para análise LLM
    
    # Filtros por Perspectiva (Fase 2 - Integração)
    enable_perspective_filters: bool = True  # Filtrar retrieval por perspectiva BSC do agent
    
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
    
    # mem0.ai (opcional - para memória de longo prazo)
    mem0_api_key: Optional[str] = None
    mem0_org_name: Optional[str] = None
    mem0_org_id: Optional[str] = None
    mem0_project_id: Optional[str] = None
    mem0_project_name: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs: Any
):
    """
    Factory function que retorna ChatOpenAI ou ChatAnthropic baseado no modelo.
    
    Provider é detectado automaticamente pelo prefixo do modelo:
    - 'gpt-*' → ChatOpenAI
    - 'claude-*' → ChatAnthropic
    
    Args:
        model: Nome do modelo (usa settings.default_llm_model se None)
        temperature: Temperatura do modelo (usa settings.temperature se None)
        max_tokens: Max tokens de output (usa settings.max_tokens se None)
        **kwargs: Argumentos adicionais para o LLM
        
    Returns:
        ChatOpenAI ou ChatAnthropic configurado
    """
    model = model or settings.default_llm_model
    temperature = temperature if temperature is not None else settings.temperature
    max_tokens = max_tokens or settings.max_tokens
    
    # Detecta provider pelo nome do modelo
    if model.startswith("claude-"):
        # Modelo Anthropic
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY nao configurada no .env. "
                "Necessaria para usar modelos Claude."
            )
        
        return ChatAnthropic(
            model=model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    elif model.startswith("gpt-"):
        # Modelo OpenAI
        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    else:
        raise ValueError(
            f"Modelo '{model}' nao reconhecido. "
            f"Deve comecar com 'gpt-' (OpenAI) ou 'claude-' (Anthropic)."
        )


# Ensure directories exist
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.literature_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)
