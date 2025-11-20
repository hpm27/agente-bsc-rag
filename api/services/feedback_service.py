"""Serviço de feedback para coleta e análise de feedback de usuários.

Este serviço gerencia feedback sobre diagnósticos BSC gerados pelo sistema,
armazenando-os no Mem0 para análise histórica e melhoria contínua.

Features:
- Coleta de feedback estruturado (rating 1-5 + texto opcional)
- Armazenamento persistente no Mem0
- Busca e listagem com filtros
- Agregação de estatísticas (média, contagem, distribuição)

Fase: 4.5 - Feedback Collection System
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from mem0 import MemoryClient

from src.memory.schemas import Feedback

logger = logging.getLogger(__name__)


class FeedbackService:
    """Serviço para gerenciar feedback de usuários sobre diagnósticos BSC.

    Armazena feedback no Mem0 com estrutura:
    - Memory Type: "feedback"
    - Metadata: diagnostic_id, rating, phase, user_id, created_at
    - Content: comment (texto opcional) ou "Feedback rating: {rating}"

    Usage:
        service = FeedbackService()
        feedback_id = await service.collect_feedback(feedback)
        stats = await service.get_feedback_stats("diag_123")
    """

    def __init__(self, mem0_client: MemoryClient | None = None):
        """Inicializa FeedbackService.

        Args:
            mem0_client: MemoryClient do Mem0 (opcional, cria se None)
        """
        if mem0_client is None:
            api_key = os.getenv("MEM0_API_KEY")
            if not api_key:
                raise ValueError(
                    "MEM0_API_KEY não encontrada. Configure no .env ou passe mem0_client."
                )
            os.environ["MEM0_API_KEY"] = api_key
            self.client = MemoryClient()
        else:
            self.client = mem0_client

        logger.info("[FEEDBACK] FeedbackService inicializado")

    def collect_feedback(self, feedback: Feedback) -> str:
        """Coleta e armazena feedback no Mem0.

        Args:
            feedback: Instância de Feedback a ser armazenada

        Returns:
            feedback_id: ID único do feedback armazenado (UUID gerado)

        Raises:
            ValueError: Se feedback for inválido
            Exception: Erros de comunicação com Mem0

        Example:
            >>> feedback = Feedback(
            ...     rating=5,
            ...     comment="Excelente diagnóstico!",
            ...     diagnostic_id="diag_123",
            ...     user_id="user_456",
            ...     phase="discovery"
            ... )
            >>> service = FeedbackService()
            >>> feedback_id = service.collect_feedback(feedback)
            >>> feedback_id
            'a3b5c7d9-e1f2-4a5b-8c9d-0e1f2a3b4c5d'
        """
        try:
            # Gerar feedback_id único
            feedback_id = str(uuid4())

            # Preparar mensagem (comment ou rating)
            if feedback.comment:
                message_content = feedback.comment
            else:
                message_content = f"Feedback rating: {feedback.rating}/5"

            # Preparar metadata (sanitizado para < 2000 chars)
            metadata = {
                "feedback_id": feedback_id,
                "diagnostic_id": feedback.diagnostic_id,
                "rating": feedback.rating,
                "phase": feedback.phase,
                "user_id": feedback.user_id,
                "created_at": feedback.created_at.isoformat(),
                "memory_type": "feedback",
            }

            # Adicionar metadata customizado se fornecido
            if feedback.metadata:
                # Limitar tamanho do metadata customizado
                custom_metadata = {
                    k: str(v)[:200] if len(str(v)) > 200 else v
                    for k, v in feedback.metadata.items()
                }
                metadata.update(custom_metadata)

            # Sanitizar metadata para < 2000 chars (limite Mem0)
            metadata = self._sanitize_metadata(metadata)

            # Armazenar no Mem0
            # Usar user_id específico para feedback: "feedback_{user_id}"
            # Isso permite buscar todos feedbacks de um usuário
            feedback_user_id = f"feedback_{feedback.user_id}"

            self.client.add(messages=[message_content], user_id=feedback_user_id, metadata=metadata)

            # CRÍTICO: Aguardar add() completar (eventual consistency Mem0)
            # Sleep 2s para garantir disponibilidade para read subsequente
            time.sleep(2)

            logger.info(
                "[FEEDBACK] Feedback coletado: id=%s, rating=%d, diagnostic_id=%s, user_id=%s",
                feedback_id,
                feedback.rating,
                feedback.diagnostic_id,
                feedback.user_id,
            )

            return feedback_id

        except Exception as e:
            logger.error("[ERROR] [FEEDBACK] Erro ao coletar feedback: %s", str(e), exc_info=True)
            raise

    def get_feedback(self, feedback_id: str, user_id: str | None = None) -> Feedback | None:
        """Busca feedback específico por ID.

        Args:
            feedback_id: ID único do feedback
            user_id: ID do usuário (opcional, ajuda na busca)

        Returns:
            Feedback encontrado ou None se não existir

        Example:
            >>> service = FeedbackService()
            >>> feedback = service.get_feedback("feedback_123", user_id="user_456")
            >>> feedback.rating
            5
        """
        try:
            # Buscar no Mem0 usando search com filters
            # Mem0 v2 exige filters obrigatórios
            filters = {"AND": [{"feedback_id": feedback_id}]}

            if user_id:
                # Adicionar filtro de user_id se fornecido
                filters["AND"].append({"user_id": user_id})

            # Buscar memórias com feedback_id
            results = self.client.get_all(filters=filters, page=1, page_size=10)

            # Mem0 pode retornar dict com 'results' ou lista direta
            if isinstance(results, dict) and "results" in results:
                memories_list = results["results"]
            elif isinstance(results, list):
                memories_list = results
            else:
                memories_list = [results] if results else []

            if not memories_list or len(memories_list) == 0:
                logger.debug("[FEEDBACK] Feedback não encontrado: id=%s", feedback_id)
                return None

            # Converter primeira memória encontrada para Feedback
            memory = memories_list[0]
            return self._memory_to_feedback(memory)

        except Exception as e:
            logger.error("[ERROR] [FEEDBACK] Erro ao buscar feedback: %s", str(e), exc_info=True)
            return None

    def list_feedback(
        self,
        diagnostic_id: str | None = None,
        user_id: str | None = None,
        rating_min: int | None = None,
        rating_max: int | None = None,
        phase: str | None = None,
        limit: int = 100,
    ) -> list[Feedback]:
        """Lista feedbacks com filtros opcionais.

        Args:
            diagnostic_id: Filtrar por diagnóstico específico
            user_id: Filtrar por usuário específico
            rating_min: Rating mínimo (1-5)
            rating_max: Rating máximo (1-5)
            phase: Filtrar por fase do workflow
            limit: Limite de resultados (default: 100)

        Returns:
            Lista de Feedback encontrados

        Example:
            >>> service = FeedbackService()
            >>> feedbacks = service.list_feedback(
            ...     diagnostic_id="diag_123",
            ...     rating_min=4
            ... )
            >>> len(feedbacks)
            5
        """
        try:
            # Construir filters para Mem0 v2
            filters = {"AND": [{"memory_type": "feedback"}]}

            if diagnostic_id:
                filters["AND"].append({"diagnostic_id": diagnostic_id})

            if user_id:
                filters["AND"].append({"user_id": user_id})

            if phase:
                filters["AND"].append({"phase": phase})

            # Rating filters (Mem0 não suporta range direto, filtrar depois)
            # Buscar todos e filtrar em memória

            # Buscar no Mem0
            results = self.client.get_all(filters=filters, page=1, page_size=limit)

            # Mem0 pode retornar dict com 'results' ou lista direta
            if isinstance(results, dict) and "results" in results:
                memories_list = results["results"]
            elif isinstance(results, list):
                memories_list = results
            else:
                memories_list = [results] if results else []

            if not memories_list:
                return []

            # Converter memórias para Feedback
            feedbacks = []
            for memory in memories_list:
                try:
                    feedback = self._memory_to_feedback(memory)

                    # Aplicar filtros de rating em memória
                    if rating_min is not None and feedback.rating < rating_min:
                        continue
                    if rating_max is not None and feedback.rating > rating_max:
                        continue

                    feedbacks.append(feedback)
                except Exception as e:
                    logger.warning(
                        "[WARN] [FEEDBACK] Erro ao converter memória para Feedback: %s", str(e)
                    )
                    continue

            # Ordenar por created_at (mais recente primeiro)
            feedbacks.sort(key=lambda f: f.created_at, reverse=True)

            logger.debug(
                "[FEEDBACK] Listados %d feedbacks (filtros: diagnostic_id=%s, user_id=%s, rating_min=%s, rating_max=%s)",
                len(feedbacks),
                diagnostic_id,
                user_id,
                rating_min,
                rating_max,
            )

            return feedbacks

        except Exception as e:
            logger.error("[ERROR] [FEEDBACK] Erro ao listar feedbacks: %s", str(e), exc_info=True)
            return []

    def get_feedback_stats(
        self, diagnostic_id: str | None = None, user_id: str | None = None
    ) -> dict[str, Any]:
        """Calcula estatísticas agregadas de feedback.

        Args:
            diagnostic_id: Filtrar por diagnóstico específico (opcional)
            user_id: Filtrar por usuário específico (opcional)

        Returns:
            Dict com estatísticas:
            - total_count: Total de feedbacks
            - avg_rating: Média de ratings (float)
            - positive_count: Count de ratings >= 4
            - negative_count: Count de ratings <= 2
            - neutral_count: Count de ratings == 3
            - rating_distribution: Dict com count por rating (1-5)

        Example:
            >>> service = FeedbackService()
            >>> stats = service.get_feedback_stats(diagnostic_id="diag_123")
            >>> stats["avg_rating"]
            4.2
            >>> stats["total_count"]
            10
        """
        try:
            # Buscar todos feedbacks com filtros
            feedbacks = self.list_feedback(
                diagnostic_id=diagnostic_id,
                user_id=user_id,
                limit=1000,  # Limite alto para estatísticas
            )

            if not feedbacks:
                return {
                    "total_count": 0,
                    "avg_rating": 0.0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                }

            # Calcular estatísticas
            total_count = len(feedbacks)
            ratings = [f.rating for f in feedbacks]
            avg_rating = sum(ratings) / total_count if total_count > 0 else 0.0

            positive_count = sum(1 for f in feedbacks if f.is_positive())
            negative_count = sum(1 for f in feedbacks if f.is_negative())
            neutral_count = sum(1 for f in feedbacks if f.is_neutral())

            # Distribuição de ratings
            rating_distribution = dict.fromkeys(range(1, 6), 0)
            for f in feedbacks:
                rating_distribution[f.rating] += 1

            stats = {
                "total_count": total_count,
                "avg_rating": round(avg_rating, 2),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "rating_distribution": rating_distribution,
            }

            logger.debug(
                "[FEEDBACK] Estatísticas calculadas: total=%d, avg_rating=%.2f, positive=%d, negative=%d",
                total_count,
                avg_rating,
                positive_count,
                negative_count,
            )

            return stats

        except Exception as e:
            logger.error(
                "[ERROR] [FEEDBACK] Erro ao calcular estatísticas: %s", str(e), exc_info=True
            )
            return {
                "total_count": 0,
                "avg_rating": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            }

    def _memory_to_feedback(self, memory: dict[str, Any]) -> Feedback:
        """Converte memória do Mem0 para Feedback.

        Args:
            memory: Dict retornado pelo Mem0

        Returns:
            Instância de Feedback

        Raises:
            ValueError: Se memória não contém campos obrigatórios
        """
        try:
            metadata = memory.get("metadata", {})

            # Extrair comment do conteúdo da memória
            messages = memory.get("messages", [])
            comment = None
            if messages and len(messages) > 0:
                content = (
                    messages[0].get("content", "")
                    if isinstance(messages[0], dict)
                    else str(messages[0])
                )
                # Se não começar com "Feedback rating:", é um comment real
                if not content.startswith("Feedback rating:"):
                    comment = content

            # Extrair campos obrigatórios
            rating = metadata.get("rating")
            diagnostic_id = metadata.get("diagnostic_id")
            user_id = metadata.get("user_id")
            phase = metadata.get("phase")

            if not all([rating, diagnostic_id, user_id, phase]):
                raise ValueError(
                    f"Memória inválida: faltam campos obrigatórios. " f"Metadata: {metadata}"
                )

            # Extrair created_at
            created_at_str = metadata.get("created_at")
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            else:
                created_at = datetime.now(timezone.utc)

            # Extrair feedback_id do metadata
            feedback_id = metadata.get("feedback_id", "unknown")

            # Extrair metadata customizado (excluir campos padrão)
            custom_metadata = {
                k: v
                for k, v in metadata.items()
                if k
                not in [
                    "feedback_id",
                    "diagnostic_id",
                    "rating",
                    "phase",
                    "user_id",
                    "created_at",
                    "memory_type",
                ]
            }

            # Adicionar feedback_id ao metadata para acesso fácil
            custom_metadata["_feedback_id"] = feedback_id

            return Feedback(
                rating=int(rating),
                comment=comment,
                diagnostic_id=diagnostic_id,
                user_id=user_id,
                phase=phase,
                created_at=created_at,
                metadata=custom_metadata,
            )

        except Exception as e:
            logger.error(
                "[ERROR] [FEEDBACK] Erro ao converter memória para Feedback: %s. Memory: %s",
                str(e),
                memory,
            )
            raise

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Sanitiza metadata para garantir < 2000 chars (limite Mem0).

        Args:
            metadata: Dict de metadata original

        Returns:
            Dict sanitizado com tamanho < 2000 chars
        """
        import json

        def _calculate_size(d: dict[str, Any]) -> int:
            """Calcula tamanho do metadata JSON serializado."""
            return len(json.dumps(d, separators=(",", ":"), ensure_ascii=False))

        def _truncate(text: str, max_len: int) -> str:
            """Trunca texto garantindo que não ultrapasse max_len."""
            if not isinstance(text, str):
                text = str(text)
            return text if len(text) <= max_len else text[: max_len - 3] + "..."

        # Tentar metadata original
        size = _calculate_size(metadata)

        if size <= 2000:
            return metadata

        # Se > 2000, truncar campos de texto progressivamente
        logger.warning("[WARN] [FEEDBACK] Metadata > 2000 chars (%d). Truncando campos...", size)

        # Truncar campos de texto
        sanitized = metadata.copy()
        for key, value in sanitized.items():
            if isinstance(value, str) and len(value) > 100:
                sanitized[key] = _truncate(value, 100)

        size = _calculate_size(sanitized)

        if size > 2000:
            # Último recurso: remover metadata customizado
            logger.warning(
                "[WARN] [FEEDBACK] Metadata ainda > 2000 chars após truncamento. Removendo campos customizados."
            )
            sanitized = {
                k: v
                for k, v in sanitized.items()
                if k
                in [
                    "feedback_id",
                    "diagnostic_id",
                    "rating",
                    "phase",
                    "user_id",
                    "created_at",
                    "memory_type",
                ]
            }

        return sanitized
