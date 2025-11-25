"""
Configurações gerais da aplicação.
"""

import os
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Gemini é opcional - só importa se disponível
try:
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import-not-found]

    GEMINI_AVAILABLE = True
except ImportError:
    ChatGoogleGenerativeAI = None  # type: ignore[misc, assignment]
    GEMINI_AVAILABLE = False

from src.memory.factory import MemoryFactory  # Exposto no módulo para facilitar patch em testes


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
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Google (para Gemini)
    google_api_key: str | None = None

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
    redis_password: str | None = None
    redis_db: int = 0
    redis_index_name: str = "bsc_knowledge"

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 10
    top_k_perspective_search: int = 5  # Número de documentos por perspectiva BSC nos agents
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
    gpt5_max_completion_tokens: int = 128000
    gpt5_reasoning_effort: str = (
        "medium"  # GPT-5.1 Thinking: apenas "medium" | GPT-5.1 Instant: "none", "low", "medium", "high"
    )

    # Onboarding Agent Configuration (GPT-5 family)
    onboarding_llm_model: str = (
        "gpt-5-2025-08-07"  # Opções: "gpt-5-2025-08-07" (top performance, $1.25 in/$10.00 out) ou "gpt-5-mini-2025-08-07" (econômico, $0.25 in/$2.00 out, reasoning mantido)
    )

    # Translation Configuration (Query PT<->EN)
    translation_llm_model: str = "gpt-5-mini-2025-08-07"  # Tarefa simples, mini suficiente

    # Diagnostic Agent Configuration (Análise 4 perspectivas BSC)
    diagnostic_llm_model: str = "gpt-5-2025-08-07"  # Reasoning avançado necessário

    # ========================================================================
    # LLM POR TIPO DE AGENTE - SESSAO 45 (Qualidade Máxima)
    # Baseado em benchmarks Claude Opus 4.5 vs GPT-5.1 vs Gemini 3 Pro
    # ========================================================================

    # CONVERSAÇÃO/EMPATIA: GPT-5.1 (melhor em conversação natural, empatia)
    llm_conversational: str = "gpt-5.1-chat-latest"  # OnboardingAgent, CustomerAgent, LearningAgent

    # ANÁLISE COMPLEXA: Claude Opus 4.5 (80.9% SWE-bench, auto-correção, tarefas longas)
    llm_analysis: str = "claude-opus-4-5-20250924"  # DiagnosticAgent, JudgeAgent, ProcessAgent

    # SÍNTESE LONGA: Claude Opus 4.5 (Infinite Chat, contexto infinito)
    llm_synthesis: str = "claude-opus-4-5-20250924"  # Orchestrator (40-60K tokens input)

    # RACIOCÍNIO QUANTITATIVO: GPT-5.1 (fallback se Gemini não instalado)
    # Ideal: Gemini 3 Pro (92% GPQA Diamond) - requer: pip install langchain-google-genai
    llm_quantitative: str = "gpt-5.1-chat-latest"  # FinancialAgent, BenchmarkingTool

    # FERRAMENTAS CONSULTIVAS: Claude Opus 4.5 (structured output confiável, menos erros)
    llm_tools: str = (
        "claude-opus-4-5-20250924"  # SWOT, PrioritizationMatrix, ActionPlan, StrategyMap
    )

    # TAREFAS SIMPLES (econômico): GPT-5 mini (custo baixo, qualidade suficiente)
    llm_simple: str = "gpt-5-mini-2025-08-07"  # Translation, Query Decomposition, Router

    # Agent Configuration
    max_iterations: int = 10
    temperature: float = 0.0
    max_tokens: int = 128000
    agent_max_workers: int = 4

    # Workflow Refinement Configuration (SESSAO 44)
    # Controla quantas vezes o Judge pode solicitar refinamento dos agentes
    # 0 = sem refinamento (resposta única), 1 = 1 refinamento, 2 = 2 refinamentos (padrão)
    max_refinement_iterations: int = 2

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
    decomposition_llm: str = "gpt-5-mini-2025-08-07"

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
    router_llm_model: str = "gpt-5-mini-2025-08-07"  # Modelo para LLM fallback
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
    auto_metadata_model: str = "gpt-5-mini-2025-08-07"  # Modelo para extração (econômico e rápido)
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

    # Memory Configuration (Mem0 Platform)
    # FASE 1.6: Config Management - Configurações obrigatórias para Mem0
    mem0_api_key: str = Field(
        ..., description="Mem0 Platform API Key (obrigatório)", alias="MEM0_API_KEY"
    )
    mem0_org_name: str | None = Field(
        default=None, description="Mem0 Organization Name", alias="MEM0_ORG_NAME"
    )
    mem0_org_id: str | None = Field(
        default=None, description="Mem0 Organization ID", alias="MEM0_ORG_ID"
    )
    mem0_project_id: str | None = Field(
        default=None, description="Mem0 Project ID", alias="MEM0_PROJECT_ID"
    )
    mem0_project_name: str | None = Field(
        default=None, description="Mem0 Project Name", alias="MEM0_PROJECT_NAME"
    )
    memory_provider: str = Field(
        default="mem0", description="Memory provider type (default: mem0, future: supabase, redis)"
    )

    # (sem validadores de nível de modelo; validações específicas ficam por campo)

    @field_validator("mem0_api_key")
    @classmethod
    def validate_mem0_api_key(cls, v: str) -> str:
        """Valida que MEM0_API_KEY não está vazia e tem formato válido."""
        if not v or v.strip() == "":
            raise ValueError("MEM0_API_KEY não pode estar vazia")

        # Validação básica de formato (Mem0 keys começam com 'm0-')
        v_stripped = v.strip()
        if not v_stripped.startswith("m0-"):
            raise ValueError(
                "MEM0_API_KEY parece inválida. Deve começar com 'm0-'. "
                "Verifique suas credenciais em https://app.mem0.ai/dashboard/api-keys"
            )

        # Validação de tamanho mínimo
        if len(v_stripped) < 20:
            raise ValueError(
                f"MEM0_API_KEY parece inválida (muito curta: {len(v_stripped)} chars). "
                f"Keys válidas do Mem0 têm 40+ caracteres."
            )

        return v_stripped

    @field_validator("memory_provider")
    @classmethod
    def validate_memory_provider(cls, v: str) -> str:
        """Valida que MEMORY_PROVIDER é um valor conhecido."""
        v_lower = v.lower().strip()
        valid_providers = ["mem0", "supabase", "redis"]

        if v_lower not in valid_providers:
            raise ValueError(
                f"MEMORY_PROVIDER inválido: {v!r}. " f"Valores válidos: {valid_providers}"
            )

        return v_lower

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,  # Permite usar aliases (MEM0_API_KEY no .env)
    )


# Singleton instance (usa env_file do model_config)
settings = Settings()  # type: ignore[call-arg]


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **kwargs: Any,
):
    """
    Factory function que retorna ChatOpenAI ou ChatAnthropic baseado no modelo.

    Provider é detectado automaticamente pelo prefixo do modelo:
    - 'gpt-*' -> ChatOpenAI
    - 'claude-*' -> ChatAnthropic

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

    # SESSAO 46: Extrair timeout de kwargs para tratar por provider
    # - ChatAnthropic: usa 'timeout'
    # - ChatOpenAI: usa 'request_timeout' (NÃO 'timeout'!)
    # - ChatGoogleGenerativeAI: usa 'timeout'
    timeout_value = kwargs.pop("timeout", None)

    # Detecta provider pelo nome do modelo
    if model.startswith("claude-"):
        # Modelo Anthropic - limite de 64K tokens para Claude Opus 4.5
        # SESSAO 46: Verificar se max_tokens não é None antes de min()
        claude_max_tokens = min(max_tokens, 64000) if max_tokens is not None else 64000
        if not settings.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY nao configurada no .env. " "Necessaria para usar modelos Claude."
            )

        # Anthropic usa 'timeout' diretamente
        anthropic_kwargs = {**kwargs}
        if timeout_value is not None:
            anthropic_kwargs["timeout"] = timeout_value

        return ChatAnthropic(  # type: ignore[call-arg]
            model=model,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=claude_max_tokens,
            **anthropic_kwargs,
        )
    if model.startswith("gpt-"):
        # Modelo OpenAI
        # SESSAO 46: OpenAI usa 'request_timeout', NÃO 'timeout'!
        openai_kwargs = {**kwargs}
        if timeout_value is not None:
            openai_kwargs["request_timeout"] = timeout_value  # Converter timeout -> request_timeout

        # GPT-5 usa max_completion_tokens, modelos antigos usam max_tokens
        if model.startswith("gpt-5"):
            return ChatOpenAI(  # type: ignore[arg-type,call-arg]
                model=model,
                api_key=SecretStr(settings.openai_api_key),
                temperature=1.0,  # GPT-5 exige temperature=1.0
                max_completion_tokens=max_tokens,  # GPT-5 usa max_completion_tokens
                reasoning_effort=settings.gpt5_reasoning_effort,
                **openai_kwargs,
            )
        return ChatOpenAI(  # type: ignore[arg-type,call-arg]
            model=model,
            api_key=SecretStr(settings.openai_api_key),
            temperature=temperature,
            max_tokens=max_tokens,  # GPT-4/3.5 usam max_tokens
            **openai_kwargs,
        )
    if model.startswith("gemini-"):
        # Modelo Google Gemini
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "langchain_google_genai nao instalado. "
                "Execute: pip install langchain-google-genai"
            )
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY nao configurada no .env. " "Necessaria para usar modelos Gemini."
            )

        # Gemini usa 'timeout' diretamente
        gemini_kwargs = {**kwargs}
        if timeout_value is not None:
            gemini_kwargs["timeout"] = timeout_value

        return ChatGoogleGenerativeAI(  # type: ignore[call-arg]
            model=model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
            **gemini_kwargs,
        )
    raise ValueError(
        f"Modelo '{model}' nao reconhecido. "
        f"Deve comecar com 'gpt-' (OpenAI), 'claude-' (Anthropic) ou 'gemini-' (Google)."
    )


def get_llm_for_agent(
    agent_type: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    **kwargs: Any,
):
    """
    Factory function que retorna LLM otimizado para cada tipo de agente.

    SESSAO 45: Baseado em benchmarks Claude Opus 4.5 vs GPT-5.1 vs Gemini 3 Pro.
    Prioriza qualidade máxima sem restrição de custo.

    Args:
        agent_type: Tipo de agente/ferramenta. Valores válidos:
            - "conversational": OnboardingAgent, CustomerAgent, LearningAgent
            - "analysis": DiagnosticAgent, JudgeAgent, ProcessAgent
            - "synthesis": Orchestrator (síntese de grandes inputs)
            - "quantitative": FinancialAgent, BenchmarkingTool
            - "tools": SWOT, PrioritizationMatrix, ActionPlan, StrategyMap
            - "simple": Translation, QueryDecomposition, Router
        temperature: Override de temperatura (opcional)
        max_tokens: Override de max tokens (opcional)
        **kwargs: Argumentos adicionais para o LLM

    Returns:
        LLM configurado para o tipo de agente

    Example:
        >>> llm = get_llm_for_agent("analysis")  # Claude Opus 4.5
        >>> llm = get_llm_for_agent("conversational")  # GPT-5.1
        >>> llm = get_llm_for_agent("quantitative")  # Gemini 3 Pro

    Mapping:
        - conversational -> GPT-5.1 (empatia, conversação natural)
        - analysis -> Claude Opus 4.5 (auto-correção, tarefas longas)
        - synthesis -> Claude Opus 4.5 (Infinite Chat, contexto infinito)
        - quantitative -> Gemini 3 Pro (GPQA Diamond 92%)
        - tools -> Claude Opus 4.5 (structured output confiável)
        - simple -> GPT-5 mini (econômico, suficiente)
    """
    # Mapeamento tipo de agente -> configuração do modelo
    agent_llm_mapping = {
        "conversational": settings.llm_conversational,
        "analysis": settings.llm_analysis,
        "synthesis": settings.llm_synthesis,
        "quantitative": settings.llm_quantitative,
        "tools": settings.llm_tools,
        "simple": settings.llm_simple,
    }

    # Validar tipo de agente
    if agent_type not in agent_llm_mapping:
        raise ValueError(
            f"agent_type '{agent_type}' não reconhecido. "
            f"Valores válidos: {list(agent_llm_mapping.keys())}"
        )

    model = agent_llm_mapping[agent_type]

    # SESSAO 45: Fallback para Gemini se não estiver disponível
    # Quando Gemini não está instalado, usa GPT-5.1 mini como fallback para quantitative
    if not GEMINI_AVAILABLE and model and "gemini" in model.lower():
        import logging

        logging.getLogger(__name__).warning(
            f"[WARN] Gemini não disponível para agent_type='{agent_type}'. "
            f"Usando fallback: {settings.default_llm_model}"
        )
        model = settings.default_llm_model

    # Usar get_llm para criar o LLM apropriado
    return get_llm(model=model, temperature=temperature, max_tokens=max_tokens, **kwargs)


def validate_memory_config() -> None:
    """
    Valida configuração de memória em startup.

    FASE 1.6: Validação crítica de ambiente para garantir que:
    1. MEM0_API_KEY está configurada quando MEMORY_PROVIDER='mem0'
    2. Provider escolhido existe no MemoryFactory
    3. Configuração está funcional antes de iniciar workflow

    Raises:
        ValueError: Se configuração for inválida
        ImportError: Se MemoryFactory não puder ser importado
    """
    import logging

    logger = logging.getLogger(__name__)

    # Usa singleton settings global (respeita monkeypatch em testes)
    current_settings = settings

    # 1. Validar que provider escolhido é suportado
    try:
        # Usa MemoryFactory importado no escopo do módulo (facilita patching nos testes)
        available_providers = MemoryFactory.list_providers()
        if current_settings.memory_provider not in available_providers:
            raise ValueError(
                f"MEMORY_PROVIDER '{current_settings.memory_provider}' não está registrado. "
                f"Provedores disponíveis: {available_providers}"
            )

        logger.info(
            "[OK] MEMORY_PROVIDER validado: %r (disponíveis: %s)",
            current_settings.memory_provider,
            available_providers,
        )

    except ImportError as e:
        raise ImportError(
            f"Não foi possível importar MemoryFactory: {e}. "
            f"Verifique se src/memory/factory.py existe."
        ) from e

    # 2. Validação específica para Mem0
    if current_settings.memory_provider == "mem0":
        if not current_settings.mem0_api_key:
            raise ValueError(
                "MEM0_API_KEY é obrigatória quando MEMORY_PROVIDER='mem0'. "
                "Adicione MEM0_API_KEY=your-key no arquivo .env"
            )

        # API key já foi validada pelo field_validator, mas vamos garantir
        if not current_settings.mem0_api_key.startswith("m0-"):
            raise ValueError(
                "MEM0_API_KEY parece inválida (deve começar com 'm0-'). "
                "Verifique suas credenciais em https://app.mem0.ai/dashboard/api-keys"
            )

        logger.info(
            "[OK] Mem0 configurado: API key válida (%d chars), org=%r, project=%r",
            len(current_settings.mem0_api_key),
            current_settings.mem0_org_name,
            current_settings.mem0_project_name,
        )

    # 3. Validação futura para outros providers
    elif current_settings.memory_provider == "supabase":
        logger.warning(
            "[WARN] MEMORY_PROVIDER='supabase' ainda não implementado. " "Use 'mem0' por enquanto."
        )
    elif current_settings.memory_provider == "redis":
        logger.warning(
            "[WARN] MEMORY_PROVIDER='redis' ainda não implementado. " "Use 'mem0' por enquanto."
        )

    logger.info("[OK] Configuração de memória validada com sucesso")


# Ensure directories exist
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.literature_dir, exist_ok=True)
os.makedirs(settings.models_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)

# Validate memory configuration on import (FASE 1.6)
# Desabilitado por padrão para não quebrar testes que não precisam de Mem0
# Habilitar manualmente em main.py ou workflow startup
# validate_memory_config()
