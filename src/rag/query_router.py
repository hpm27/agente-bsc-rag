"""
Query Router Inteligente para RAG Avançado (Fase 2A.3).

Classifica queries BSC e escolhe estratégia de retrieval otimizada:
- SIMPLE_FACTUAL -> DirectAnswerStrategy
- COMPLEX_MULTI_PART -> DecompositionStrategy
- CONCEPTUAL_BROAD -> HybridSearchStrategy
- RELATIONAL -> MultiHopStrategy (placeholder)

Accuracy esperada: 85%+
Latência: <50ms (heurísticas), ~500ms (LLM fallback)
"""

import json
import re
from datetime import datetime
from enum import Enum
from typing import Any

from config.settings import get_llm, settings
from loguru import logger
from pydantic import BaseModel, Field

from src.rag.strategies import (
    DecompositionStrategy,
    DirectAnswerStrategy,
    HybridSearchStrategy,
    MultiHopStrategy,
    RetrievalStrategy,
)


class QueryCategory(Enum):
    """
    Categorias de queries BSC para routing.

    Cada categoria tem estratégia de retrieval otimizada.
    """

    SIMPLE_FACTUAL = "simple_factual"  # Queries simples e diretas
    COMPLEX_MULTI_PART = "complex_multi_part"  # Queries com múltiplas partes
    CONCEPTUAL_BROAD = "conceptual_broad"  # Queries abstratas/conceituais
    RELATIONAL = "relational"  # Queries sobre relações/impactos


class RoutingDecision(BaseModel):
    """
    Decisão de routing para uma query.

    Contém categoria identificada, estratégia escolhida,
    confidence score e metadata para analytics.
    """

    query: str = Field(description="Query original do usuário")
    category: QueryCategory = Field(description="Categoria identificada")
    strategy: str = Field(description="Nome da estratégia escolhida")
    confidence: float = Field(description="Confiança na classificação (0-1)", ge=0.0, le=1.0)
    heuristic_match: bool = Field(
        description="Se foi classificada por heurística (True) ou LLM (False)"
    )
    complexity_score: int = Field(description="Score de complexidade da query", ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")

    def to_dict(self) -> dict[str, Any]:
        """Converte para dict para logging."""
        return {
            "query": self.query,
            "category": self.category.value,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "heuristic_match": self.heuristic_match,
            "complexity_score": self.complexity_score,
            "metadata": self.metadata,
        }


class QueryClassifier:
    """
    Classificador de queries BSC.

    Usa heurísticas rápidas (80% casos) + LLM fallback (20% casos ambíguos).

    Heurísticas baseadas em:
    - Comprimento da query (palavras)
    - Palavras-chave específicas (relação, impacto, causa, etc)
    - Palavras de ligação (e, também, considerando)
    - Padrões BSC (4 perspectivas, todas perspectivas)
    """

    def __init__(self, llm=None, use_llm_fallback: bool = True):
        """
        Inicializa classificador.

        Args:
            llm: Modelo LLM para fallback (se None, usa settings)
            use_llm_fallback: Se deve usar LLM para queries ambíguas
        """
        self.use_llm_fallback = use_llm_fallback
        self.llm = llm or get_llm(model_name="gpt-4o-mini", temperature=0.2)

        # Configurações
        self.simple_query_max_words = (
            settings.simple_query_max_words if hasattr(settings, "simple_query_max_words") else 30
        )
        self.complex_query_min_words = (
            settings.complex_query_min_words if hasattr(settings, "complex_query_min_words") else 30
        )
        self.confidence_threshold = (
            settings.router_confidence_threshold
            if hasattr(settings, "router_confidence_threshold")
            else 0.8
        )

        # Palavras-chave relacionais
        relational_keywords_str = (
            settings.relational_keywords
            if hasattr(settings, "relational_keywords")
            else "relação,impacto,causa,efeito,depende,influencia,deriva"
        )
        self.relational_keywords = [kw.strip() for kw in relational_keywords_str.split(",")]

        logger.info(
            f"[QueryClassifier] Inicializado "
            f"(simple_max={self.simple_query_max_words}, "
            f"complex_min={self.complex_query_min_words}, "
            f"llm_fallback={'enabled' if use_llm_fallback else 'disabled'})"
        )

    def classify(self, query: str) -> tuple[QueryCategory, float, int]:
        """
        Classifica query em categoria BSC.

        Args:
            query: Query do usuário

        Returns:
            Tupla (categoria, confidence, complexity_score)
        """
        query_lower = query.lower().strip()
        word_count = len(query_lower.split())

        # Calcular complexity score (para analytics)
        complexity_score = self._calculate_complexity_score(query_lower, word_count)

        # PRIORIDADE 1: Queries RELACIONAIS (maior especificidade)
        if self._is_relational(query_lower):
            logger.debug("[Classifier] RELATIONAL detectado (keywords)")
            return QueryCategory.RELATIONAL, 0.9, complexity_score

        # PRIORIDADE 2: Queries COMPLEXAS multi-parte
        if self._is_complex_multi_part(query_lower, word_count):
            logger.debug("[Classifier] COMPLEX_MULTI_PART detectado (ligação/perspectivas)")
            return QueryCategory.COMPLEX_MULTI_PART, 0.85, complexity_score

        # PRIORIDADE 3: Queries SIMPLES factuais
        if self._is_simple_factual(query_lower, word_count):
            logger.debug("[Classifier] SIMPLE_FACTUAL detectado (curta/direta)")
            return QueryCategory.SIMPLE_FACTUAL, 0.9, complexity_score

        # PRIORIDADE 4: Ambíguo -> LLM fallback OU CONCEPTUAL_BROAD
        if self.use_llm_fallback and complexity_score >= 3:
            logger.debug(f"[Classifier] Query ambígua (score={complexity_score}) - usando LLM")
            try:
                category, confidence = self._classify_with_llm(query)
                return category, confidence, complexity_score
            except Exception as e:
                logger.warning(f"[Classifier] LLM fallback falhou: {e} - usando CONCEPTUAL_BROAD")

        # FALLBACK: CONCEPTUAL_BROAD (padrão)
        logger.debug("[Classifier] CONCEPTUAL_BROAD (fallback)")
        return QueryCategory.CONCEPTUAL_BROAD, 0.7, complexity_score

    def _is_relational(self, query_lower: str) -> bool:
        """
        Verifica se query é sobre relações/impactos entre elementos BSC.

        Heurísticas:
        - Contém palavras-chave: relação, impacto, causa, efeito, depende, etc
        - Padrões "A -> B", "A impacta B"

        Args:
            query_lower: Query em lowercase

        Returns:
            True se relacional
        """
        # Word boundaries para evitar falsos positivos
        for keyword in self.relational_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, query_lower):
                return True

        return False

    def _is_complex_multi_part(self, query_lower: str, word_count: int) -> bool:
        """
        Verifica se query tem múltiplas partes/perspectivas.

        Heurísticas:
        - Comprimento > complex_query_min_words (default: 30)
        - Contém 2+ palavras de ligação ("e", "também", "considerando", "além de")
        - Menciona múltiplas perspectivas BSC explicitamente
        - Padrão "4 perspectivas", "todas perspectivas"

        Args:
            query_lower: Query em lowercase
            word_count: Número de palavras

        Returns:
            True se complexa multi-parte
        """
        # Comprimento
        if word_count > self.complex_query_min_words:
            return True

        # Palavras de ligação (com word boundaries)
        linking_words = ["e", "também", "considerando", "além de", "além disso", "adicionalmente"]
        linking_count = 0
        for word in linking_words:
            pattern = r"\b" + re.escape(word) + r"\b"
            linking_count += len(re.findall(pattern, query_lower))

        if linking_count >= 2:
            return True

        # Padrão "4 perspectivas", "todas perspectivas"
        perspective_patterns = [
            r"\b(4|quatro|todas|múltiplas)\s+(as\s+)?perspectivas?\b",
            r"\bperspectivas?\s+(financeira|cliente|processo|aprendizado)\s+e\s+",
        ]
        for pattern in perspective_patterns:
            if re.search(pattern, query_lower):
                return True

        # Múltiplas perspectivas mencionadas explicitamente
        bsc_perspectives = ["financeira", "cliente", "processo", "aprendizado"]
        mentioned_count = sum(1 for p in bsc_perspectives if p in query_lower)
        if mentioned_count >= 2:
            return True

        return False

    def _is_simple_factual(self, query_lower: str, word_count: int) -> bool:
        """
        Verifica se query é simples e factual.

        Heurísticas:
        - Comprimento < simple_query_max_words (default: 30)
        - Contém "?" OU padrões de pergunta direta
        - Começa com "O que é", "Defina", "Qual é"
        - NÃO contém palavras de ligação
        - NÃO contém palavras relacionais

        Args:
            query_lower: Query em lowercase
            word_count: Número de palavras

        Returns:
            True se simples e factual
        """
        # Comprimento
        if word_count > self.simple_query_max_words:
            return False

        # Padrões de pergunta direta
        simple_patterns = [
            query_lower.startswith("o que é"),
            query_lower.startswith("defina"),
            query_lower.startswith("explique"),
            query_lower.startswith("qual é"),
            query_lower.startswith("quem é"),
            query_lower.startswith("quando é"),
            query_lower.startswith("onde é"),
            "?" in query_lower,
        ]

        if not any(simple_patterns):
            return False

        # NÃO contém palavras de ligação (com word boundaries)
        linking_words = ["e", "também", "considerando", "além"]
        for word in linking_words:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, query_lower):
                return False  # Tem ligação -> não é simples

        # NÃO contém palavras relacionais
        if self._is_relational(query_lower):
            return False  # É relacional -> não é simples factual

        return True

    def _calculate_complexity_score(self, query_lower: str, word_count: int) -> int:
        """
        Calcula score de complexidade da query (0-10).

        Fatores:
        - Comprimento (palavras)
        - Palavras de ligação
        - Perspectivas BSC mencionadas
        - Palavras relacionais

        Args:
            query_lower: Query em lowercase
            word_count: Número de palavras

        Returns:
            Score 0-10 (0=simples, 10=muito complexa)
        """
        score = 0

        # Fator 1: Comprimento (+0-3)
        if word_count < 15:
            score += 0
        elif word_count < 30:
            score += 1
        elif word_count < 60:
            score += 2
        else:
            score += 3

        # Fator 2: Palavras de ligação (+1 por palavra, max +3)
        linking_count = 0
        linking_words = ["e", "também", "considerando", "além de", "adicionalmente"]
        for word in linking_words:
            pattern = r"\b" + re.escape(word) + r"\b"
            linking_count += len(re.findall(pattern, query_lower))
        score += min(3, linking_count)

        # Fator 3: Perspectivas BSC (+1 por perspectiva, max +2)
        bsc_perspectives = ["financeira", "cliente", "processo", "aprendizado"]
        mentioned = sum(1 for p in bsc_perspectives if p in query_lower)
        score += min(2, mentioned)

        # Fator 4: Palavras relacionais (+2)
        if self._is_relational(query_lower):
            score += 2

        return min(10, score)  # Cap at 10

    def _classify_with_llm(self, query: str) -> tuple[QueryCategory, float]:
        """
        Classifica query usando LLM (fallback para queries ambíguas).

        Args:
            query: Query original

        Returns:
            Tupla (categoria, confidence)
        """
        prompt = f"""Classifique esta query sobre Balanced Scorecard em UMA das categorias:

CATEGORIAS:
1. SIMPLE_FACTUAL: Perguntas simples e diretas ("O que é BSC?", "Defina...")
2. COMPLEX_MULTI_PART: Queries com múltiplas partes ou perspectivas ("Como implementar BSC considerando A e B?")
3. CONCEPTUAL_BROAD: Queries abstratas/conceituais ("Benefícios do BSC", "Vantagens...")
4. RELATIONAL: Queries sobre relações/impactos ("Impacto de A em B", "Relação entre X e Y")

Query: "{query}"

Responda APENAS com o nome da categoria (ex: SIMPLE_FACTUAL)."""

        try:
            response = self.llm.invoke(prompt).content.strip().upper()

            # Parse resposta
            if "SIMPLE_FACTUAL" in response:
                return QueryCategory.SIMPLE_FACTUAL, 0.75
            if "COMPLEX_MULTI_PART" in response:
                return QueryCategory.COMPLEX_MULTI_PART, 0.75
            if "RELATIONAL" in response:
                return QueryCategory.RELATIONAL, 0.75
            if "CONCEPTUAL_BROAD" in response:
                return QueryCategory.CONCEPTUAL_BROAD, 0.75
            logger.warning(f"[LLM Classifier] Resposta inesperada: {response}")
            return QueryCategory.CONCEPTUAL_BROAD, 0.6

        except Exception as e:
            logger.error(f"[LLM Classifier] Erro: {e}")
            raise


class QueryRouter:
    """
    Router inteligente que classifica queries e escolhe estratégia de retrieval.

    Integra QueryClassifier + Retrieval Strategies para otimizar performance.

    Workflow:
    1. Classificar query (QueryClassifier)
    2. Escolher estratégia baseado em categoria
    3. Logar decisão (analytics)
    4. Retornar RoutingDecision

    Accuracy esperada: 85%+
    Latência overhead: <50ms (heurísticas), ~500ms (LLM fallback)
    """

    def __init__(self, classifier: QueryClassifier | None = None, enable_logging: bool = True):
        """
        Inicializa router.

        Args:
            classifier: QueryClassifier instance (se None, cria novo)
            enable_logging: Se deve logar decisões para analytics
        """
        self.classifier = classifier or QueryClassifier()
        self.enable_logging = enable_logging

        # Mapeamento categoria -> estratégia
        self.strategies: dict[QueryCategory, RetrievalStrategy] = {
            QueryCategory.SIMPLE_FACTUAL: DirectAnswerStrategy(),
            QueryCategory.COMPLEX_MULTI_PART: DecompositionStrategy(),
            QueryCategory.CONCEPTUAL_BROAD: HybridSearchStrategy(),
            QueryCategory.RELATIONAL: MultiHopStrategy(),
        }

        # Logging
        self.log_file = (
            settings.router_log_file
            if hasattr(settings, "router_log_file")
            else "logs/routing_decisions.jsonl"
        )

        logger.info(
            f"[QueryRouter] Inicializado com {len(self.strategies)} estratégias "
            f"(logging={'enabled' if enable_logging else 'disabled'})"
        )

    def route(self, query: str, **kwargs) -> RoutingDecision:
        """
        Roteia query para estratégia apropriada.

        Args:
            query: Query do usuário
            **kwargs: Parâmetros adicionais (metadata, etc)

        Returns:
            RoutingDecision com categoria, estratégia, confidence, metadata
        """
        # Classificar query
        category, confidence, complexity_score = self.classifier.classify(query)

        # Escolher estratégia
        strategy = self.strategies[category]

        # Criar decisão
        decision = RoutingDecision(
            query=query,
            category=category,
            strategy=strategy.name,
            confidence=confidence,
            heuristic_match=(confidence >= 0.8),  # Heurística se confidence alta
            complexity_score=complexity_score,
            metadata={
                "strategy_complexity": strategy.complexity,
                "query_length": len(query.split()),
                **kwargs,
            },
        )

        # Logar decisão
        if self.enable_logging:
            self._log_decision(decision)

        logger.info(
            f"[Router] Query routed: category={category.value}, "
            f"strategy={strategy.name}, confidence={confidence:.2f}, "
            f"complexity={complexity_score}"
        )

        return decision

    def get_strategy(self, category: QueryCategory) -> RetrievalStrategy:
        """
        Retorna estratégia para categoria.

        Args:
            category: Categoria da query

        Returns:
            Estratégia de retrieval correspondente
        """
        return self.strategies[category]

    def _log_decision(self, decision: RoutingDecision):
        """
        Loga decisão de routing para analytics.

        Formato: JSON Lines (1 linha = 1 decisão)

        Args:
            decision: RoutingDecision a logar
        """
        try:
            log_entry = {"timestamp": datetime.now().isoformat(), **decision.to_dict()}

            # Append to log file (JSON Lines format)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.error(f"[Router] Erro ao logar decisão: {e}")
