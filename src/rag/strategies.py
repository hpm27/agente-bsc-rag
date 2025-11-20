"""
Estratégias de Retrieval para Router Inteligente (RAG Avançado - Fase 2A.3).

Define estratégias de retrieval otimizadas por tipo de query BSC:
- DirectAnswerStrategy: Queries simples (cache + LLM direto)
- DecompositionStrategy: Queries complexas (usa Query Decomposition)
- HybridSearchStrategy: Queries conceituais (padrão MVP)
- MultiHopStrategy: Queries relacionais (placeholder Graph RAG)
"""

import asyncio
from abc import ABC, abstractmethod

from config.settings import get_llm, settings
from loguru import logger

from src.rag.base_vector_store import SearchResult


class RetrievalStrategy(ABC):
    """
    Estratégia abstrata de retrieval.

    Cada estratégia implementa uma abordagem diferente de retrieval
    otimizada para um tipo específico de query BSC.
    """

    def __init__(self, name: str):
        """
        Inicializa estratégia.

        Args:
            name: Nome descritivo da estratégia
        """
        self.name = name
        self.complexity = "unknown"  # low, medium, high

    @abstractmethod
    def execute(self, query: str, retriever, **kwargs) -> list[SearchResult]:
        """
        Executa estratégia de retrieval.

        Args:
            query: Query do usuário
            retriever: Instância de BSCRetriever
            **kwargs: Parâmetros adicionais (k, filters, etc)

        Returns:
            Lista de documentos relevantes (SearchResult)
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(complexity='{self.complexity}')"


class DirectAnswerStrategy(RetrievalStrategy):
    """
    Estratégia para queries simples e diretas.

    Workflow:
    1. Verificar cache (Redis ou dict em memória)
    2. Se cache miss -> LLM direto (GPT-4o-mini) sem retrieval pesado
    3. Se LLM falhar -> Fallback para retrieval leve (top_k=5)

    Benefícios:
    - Latência: 70s -> <5s (-85%)
    - Custo: Mínimo (LLM pequeno)
    - Uso: 30% das queries (simples e factuais)

    Quando usar:
    - Queries < 30 palavras
    - Perguntas diretas ("O que é BSC?", "Defina...")
    - SEM palavras de ligação ("e", "também")
    """

    def __init__(self):
        """Inicializa estratégia de resposta direta."""
        super().__init__(name="DirectAnswer")
        self.complexity = "low"
        self.cache: dict[str, str] = {}  # Simple dict cache (TODO: Redis)
        self.cache_enabled = (
            settings.enable_direct_answer_cache
            if hasattr(settings, "enable_direct_answer_cache")
            else True
        )
        self.llm = get_llm(model_name="gpt-4o-mini", temperature=0.2)

        logger.debug(
            f"[DirectAnswer] Estratégia inicializada (cache={'enabled' if self.cache_enabled else 'disabled'})"
        )

    def execute(self, query: str, retriever, k: int = 5, **kwargs) -> list[SearchResult]:
        """
        Executa resposta direta para query simples.

        Args:
            query: Query simples do usuário
            retriever: BSCRetriever instance
            k: Número de documentos (default: 5, mais leve)

        Returns:
            Lista de SearchResult (pode ser vazia se usar LLM direto)
        """
        # Prioridade 1: Cache
        if self.cache_enabled and query in self.cache:
            logger.info(f"[DirectAnswer] Cache HIT para query: '{query[:50]}...'")
            # Retornar resposta do cache como SearchResult
            cached_answer = self.cache[query]
            return [
                SearchResult(
                    content=cached_answer,
                    source="cache",
                    page=0,
                    score=1.0,
                    search_type="cached",
                    metadata={"strategy": "DirectAnswer", "from_cache": True},
                )
            ]

        # Prioridade 2: LLM direto (queries extremamente simples)
        if self._is_trivial_query(query):
            logger.info("[DirectAnswer] Query trivial detectada - usando LLM direto")
            try:
                prompt = f"""Responda de forma concisa e direta (máximo 2-3 parágrafos):

Pergunta: {query}

Resposta:"""
                llm_answer = self.llm.invoke(prompt).content

                # Salvar no cache
                if self.cache_enabled:
                    self.cache[query] = llm_answer

                return [
                    SearchResult(
                        content=llm_answer,
                        source="llm_direct",
                        page=0,
                        score=0.9,
                        search_type="direct_answer",
                        metadata={"strategy": "DirectAnswer", "from_llm": True},
                    )
                ]
            except Exception as e:
                logger.warning(f"[DirectAnswer] LLM direto falhou: {e} - fallback para retrieval")

        # Prioridade 3: Retrieval leve (fallback)
        logger.info(f"[DirectAnswer] Usando retrieval leve (k={k})")
        results = retriever.retrieve(
            query=query,
            k=k,
            use_hybrid=True,
            use_rerank=True,
            multilingual=False,  # Queries simples geralmente não precisam multilíngue
        )

        return results

    def _is_trivial_query(self, query: str) -> bool:
        """
        Verifica se query é trivial o suficiente para LLM direto.

        Heurísticas:
        - Começa com "O que é", "Defina", "Explique"
        - Comprimento < 15 palavras
        - Sem contexto complexo

        Args:
            query: Query a avaliar

        Returns:
            True se trivial, False caso contrário
        """
        query_lower = query.lower().strip()
        word_count = len(query_lower.split())

        # Padrões triviais
        trivial_patterns = [
            query_lower.startswith("o que é"),
            query_lower.startswith("defina"),
            query_lower.startswith("explique"),
            query_lower.startswith("qual é"),
            query_lower.startswith("quem é"),
            query_lower.startswith("quando é"),
        ]

        return any(trivial_patterns) and word_count < 15


class DecompositionStrategy(RetrievalStrategy):
    """
    Estratégia para queries complexas multi-parte.

    Usa Query Decomposition (TECH-001) implementada e validada:
    - Decompõe query em 2-4 sub-queries independentes
    - Retrieval paralelo (AsyncIO)
    - Reciprocal Rank Fusion (RRF) para combinar resultados

    Benefícios:
    - Recall: +30-40% (validado)
    - Answer Quality: +30-50% (validado)
    - Latência adicional: +4s (aceitável para queries complexas)

    Quando usar:
    - Queries > 30 palavras
    - Múltiplas partes ("e", "também", "considerando")
    - Múltiplas perspectivas BSC mencionadas
    - Padrão "4 perspectivas", "todas perspectivas"
    """

    def __init__(self, decomposer=None):
        """
        Inicializa estratégia de decomposição.

        Args:
            decomposer: Instância de QueryDecomposer (se None, criada lazy)
        """
        super().__init__(name="Decomposition")
        self.complexity = "medium-high"
        self._decomposer = decomposer

        logger.debug("[Decomposition] Estratégia inicializada")

    @property
    def decomposer(self):
        """Lazy loading de QueryDecomposer."""
        if self._decomposer is None:
            from src.rag.query_decomposer import QueryDecomposer

            llm = get_llm(model_name="gpt-4o-mini", temperature=0.3)
            self._decomposer = QueryDecomposer(llm=llm)
            logger.debug("[Decomposition] QueryDecomposer criado (lazy loading)")
        return self._decomposer

    def execute(self, query: str, retriever, k: int = 10, **kwargs) -> list[SearchResult]:
        """
        Executa decomposição de query complexa.

        Args:
            query: Query complexa do usuário
            retriever: BSCRetriever instance
            k: Número final de documentos

        Returns:
            Lista de SearchResult rankeados por RRF
        """
        logger.info(f"[Decomposition] Executando para query: '{query[:50]}...'")

        # Usar retrieve_with_decomposition() implementado em TECH-001
        # Este método já faz toda lógica: should_decompose, decompose, retrieve paralelo, RRF

        # Detectar se já está em event loop (ex: pytest-asyncio)
        try:
            asyncio.get_running_loop()
            # Já em loop -> criar novo loop em thread separada
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    retriever.retrieve_with_decomposition(
                        query=query,
                        k=k,
                        decomposer=self.decomposer,
                        use_hybrid=True,
                        use_rerank=True,
                    ),
                )
                results = future.result()
        except RuntimeError:
            # Não está em loop -> asyncio.run() normal
            results = asyncio.run(
                retriever.retrieve_with_decomposition(
                    query=query, k=k, decomposer=self.decomposer, use_hybrid=True, use_rerank=True
                )
            )

        logger.info(f"[Decomposition] Retornados {len(results)} documentos")
        return results


class HybridSearchStrategy(RetrievalStrategy):
    """
    Estratégia padrão de busca híbrida (MVP atual).

    Workflow:
    1. Hybrid search (semântico + BM25)
    2. Expansão multilíngue (PT-BR + EN)
    3. Reciprocal Rank Fusion (RRF)
    4. Cohere Re-ranking

    Benefícios:
    - Precision@5: 75% (validado MVP)
    - Recall: +106% com multilíngue (validado MVP)
    - Balanceado: Bom para maioria dos casos

    Quando usar:
    - Queries conceituais/abstratas
    - Queries sobre benefícios, vantagens, características
    - Fallback quando categoria não é clara
    - Padrão para queries que não se encaixam em outras categorias
    """

    def __init__(self):
        """Inicializa estratégia de busca híbrida."""
        super().__init__(name="HybridSearch")
        self.complexity = "medium"

        logger.debug("[HybridSearch] Estratégia inicializada (padrão MVP)")

    def execute(self, query: str, retriever, k: int = 10, **kwargs) -> list[SearchResult]:
        """
        Executa busca híbrida padrão.

        Args:
            query: Query conceitual do usuário
            retriever: BSCRetriever instance
            k: Número de documentos

        Returns:
            Lista de SearchResult
        """
        logger.info(f"[HybridSearch] Executando busca padrão para query: '{query[:50]}...'")

        # Usar retrieve() padrão do MVP (já validado e funcionando bem)
        results = retriever.retrieve(
            query=query,
            k=k,
            use_hybrid=True,  # Hybrid search (semantic + BM25)
            use_rerank=True,  # Cohere re-ranking
            multilingual=True,  # Expansão PT-BR + EN com RRF
            filters=kwargs.get("filters"),
        )

        logger.info(f"[HybridSearch] Retornados {len(results)} documentos")
        return results


class MultiHopStrategy(RetrievalStrategy):
    """
    Estratégia para queries relacionais (multi-hop reasoning).

    ESTADO ATUAL: Placeholder para futuro Graph RAG

    Queries relacionais exigem seguir relações entre entidades:
    - "Qual impacto de A em B?"
    - "Como X influencia Y?"
    - "Relação entre P1 e P2?"

    Graph RAG seria ideal, mas:
    - Dataset atual (literatura conceitual BSC) inadequado
    - Precisa dataset operacional com entidades e relações explícitas
    - Complexidade: Muito alta (3-4 semanas)
    - ROI: Alto SE dataset mudar, baixo AGORA

    POR ENQUANTO: Fallback para HybridSearchStrategy

    TODO (Fase 2C - Condicional):
    - Avaliar disponibilidade de dataset BSC operacional
    - SE disponível: Implementar Graph RAG
    - SENÃO: Manter fallback para Hybrid
    """

    def __init__(self):
        """Inicializa estratégia multi-hop (placeholder)."""
        super().__init__(name="MultiHop")
        self.complexity = "very-high"
        self.fallback_strategy = HybridSearchStrategy()

        logger.debug(
            "[MultiHop] Estratégia inicializada (PLACEHOLDER - fallback para HybridSearch)"
        )

    def execute(self, query: str, retriever, k: int = 10, **kwargs) -> list[SearchResult]:
        """
        Executa multi-hop reasoning (atualmente fallback para Hybrid).

        Args:
            query: Query relacional do usuário
            retriever: BSCRetriever instance
            k: Número de documentos

        Returns:
            Lista de SearchResult
        """
        logger.info(f"[MultiHop] Executando (fallback para Hybrid) para query: '{query[:50]}...'")
        logger.warning("[MultiHop] Graph RAG não implementado ainda - usando HybridSearch")

        # TODO: Implementar Graph RAG quando dataset estiver pronto
        # Por enquanto: fallback para HybridSearch
        return self.fallback_strategy.execute(query=query, retriever=retriever, k=k, **kwargs)
