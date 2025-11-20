"""Endpoints REST para coleta e análise de feedback.

Este router fornece acesso programático ao sistema de feedback,
permitindo coletar, buscar e analisar feedback de usuários sobre diagnósticos BSC.

Endpoints:
- POST /api/v1/feedback - Criar novo feedback
- GET /api/v1/feedback/{feedback_id} - Buscar feedback específico
- GET /api/v1/feedback - Listar feedbacks (filtros: diagnostic_id, user_id, rating, phase)
- GET /api/v1/feedback/stats - Estatísticas agregadas de feedback

Fase: 4.5 - Feedback Collection System
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response

from api.dependencies import verify_api_key
from api.schemas.responses import (
    FeedbackListResponse,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackStatsResponse,
)
from api.services.feedback_service import FeedbackService
from api.utils.rate_limit import LIMIT_READ, LIMIT_WRITE, limiter
from src.memory.schemas import Feedback

logger = logging.getLogger(__name__)

router = APIRouter()

# Instância global do FeedbackService
_feedback_service = None


def get_feedback_service() -> FeedbackService:
    """Retorna instância singleton do FeedbackService."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service


@router.post(
    "/",
    response_model=FeedbackResponse,
    status_code=201,
    summary="Criar novo feedback",
    description="Coleta feedback de usuário sobre um diagnóstico BSC (rating 1-5 + texto opcional).",
)
@limiter.limit(LIMIT_WRITE)
async def create_feedback(
    request: Request,
    response: Response,
    body: FeedbackRequest,
    auth: dict = Depends(verify_api_key),
) -> FeedbackResponse:
    """Cria novo feedback sobre diagnóstico BSC.

    Args:
        body: Dados do feedback (rating, comment, diagnostic_id, phase)
        auth: Autenticação via API key (extrai user_id)

    Returns:
        FeedbackResponse com feedback criado

    Raises:
        HTTPException 400: Se dados inválidos
        HTTPException 500: Se erro ao salvar
    """
    try:
        service = get_feedback_service()

        # Extrair user_id do auth (API key metadata)
        user_id = auth.get("user_id") or auth.get("api_key_id", "unknown")

        # Criar instância Feedback
        feedback = Feedback(
            rating=body.rating,
            comment=body.comment,
            diagnostic_id=body.diagnostic_id,
            user_id=user_id,
            phase=body.phase,
            metadata=body.metadata or {},
        )

        # Coletar feedback
        feedback_id = service.collect_feedback(feedback)

        # Retornar response
        return FeedbackResponse(
            feedback_id=feedback_id,
            rating=feedback.rating,
            comment=feedback.comment,
            diagnostic_id=feedback.diagnostic_id,
            user_id=feedback.user_id,
            phase=feedback.phase,
            created_at=feedback.created_at.isoformat(),
            metadata=feedback.metadata,
        )

    except ValueError as e:
        logger.error(f"[FEEDBACK] Erro de validação: {e}")
        raise HTTPException(status_code=400, detail=f"Dados inválidos: {e!s}")
    except Exception as e:
        logger.error(f"[FEEDBACK] Erro ao criar feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar feedback: {e!s}")


@router.get(
    "/{feedback_id}",
    response_model=FeedbackResponse,
    summary="Buscar feedback específico",
    description="Retorna feedback específico por ID.",
)
@limiter.limit(LIMIT_READ)
async def get_feedback(
    request: Request,
    response: Response,
    feedback_id: str = Path(..., description="ID único do feedback"),
    user_id: str | None = Query(None, description="ID do usuário (opcional, ajuda na busca)"),
    auth: dict = Depends(verify_api_key),
) -> FeedbackResponse:
    """Busca feedback específico por ID.

    Args:
        feedback_id: ID único do feedback
        user_id: ID do usuário (opcional)
        auth: Autenticação via API key

    Returns:
        FeedbackResponse com feedback encontrado

    Raises:
        HTTPException 404: Se feedback não encontrado
        HTTPException 500: Se erro ao buscar
    """
    try:
        service = get_feedback_service()

        # Buscar feedback
        feedback = service.get_feedback(feedback_id, user_id=user_id)

        if not feedback:
            raise HTTPException(status_code=404, detail=f"Feedback não encontrado: {feedback_id}")

        # Retornar response
        return FeedbackResponse(
            feedback_id=feedback_id,
            rating=feedback.rating,
            comment=feedback.comment,
            diagnostic_id=feedback.diagnostic_id,
            user_id=feedback.user_id,
            phase=feedback.phase,
            created_at=feedback.created_at.isoformat(),
            metadata=feedback.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FEEDBACK] Erro ao buscar feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar feedback: {e!s}")


@router.get(
    "/",
    response_model=FeedbackListResponse,
    summary="Listar feedbacks",
    description="Lista feedbacks com filtros opcionais (diagnostic_id, user_id, rating, phase).",
)
@limiter.limit(LIMIT_READ)
async def list_feedback(
    request: Request,
    response: Response,
    diagnostic_id: str | None = Query(None, description="Filtrar por diagnóstico"),
    user_id: str | None = Query(None, description="Filtrar por usuário"),
    rating_min: int | None = Query(None, ge=1, le=5, description="Rating mínimo (1-5)"),
    rating_max: int | None = Query(None, ge=1, le=5, description="Rating máximo (1-5)"),
    phase: str | None = Query(None, description="Filtrar por fase do workflow"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    auth: dict = Depends(verify_api_key),
) -> FeedbackListResponse:
    """Lista feedbacks com filtros opcionais.

    Args:
        diagnostic_id: Filtrar por diagnóstico específico
        user_id: Filtrar por usuário específico
        rating_min: Rating mínimo (1-5)
        rating_max: Rating máximo (1-5)
        phase: Filtrar por fase do workflow
        limit: Limite de resultados (1-1000)
        auth: Autenticação via API key

    Returns:
        FeedbackListResponse com lista de feedbacks

    Raises:
        HTTPException 400: Se filtros inválidos
        HTTPException 500: Se erro ao listar
    """
    # Validar rating_min <= rating_max ANTES de chamar serviço
    if rating_min is not None and rating_max is not None:
        if rating_min > rating_max:
            raise HTTPException(
                status_code=400, detail="rating_min não pode ser maior que rating_max"
            )

    try:
        service = get_feedback_service()

        # Listar feedbacks
        feedbacks = service.list_feedback(
            diagnostic_id=diagnostic_id,
            user_id=user_id,
            rating_min=rating_min,
            rating_max=rating_max,
            phase=phase,
            limit=limit,
        )

        # Converter para FeedbackResponse
        feedback_responses = []
        for f in feedbacks:
            # Extrair feedback_id do metadata (adicionado pelo service)
            feedback_id = f.metadata.get("_feedback_id", "unknown")
            # Remover _feedback_id do metadata antes de retornar
            clean_metadata = {k: v for k, v in f.metadata.items() if k != "_feedback_id"}

            feedback_responses.append(
                FeedbackResponse(
                    feedback_id=feedback_id,
                    rating=f.rating,
                    comment=f.comment,
                    diagnostic_id=f.diagnostic_id,
                    user_id=f.user_id,
                    phase=f.phase,
                    created_at=f.created_at.isoformat(),
                    metadata=clean_metadata,
                )
            )

        return FeedbackListResponse(feedbacks=feedback_responses, total=len(feedback_responses))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FEEDBACK] Erro ao listar feedbacks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar feedbacks: {e!s}")


@router.get(
    "/stats/summary",
    response_model=FeedbackStatsResponse,
    summary="Estatísticas de feedback",
    description="Retorna estatísticas agregadas de feedback (média, distribuição, etc).",
)
@limiter.limit(LIMIT_READ)
async def get_feedback_stats(
    request: Request,
    response: Response,
    diagnostic_id: str | None = Query(None, description="Filtrar por diagnóstico"),
    user_id: str | None = Query(None, description="Filtrar por usuário"),
    auth: dict = Depends(verify_api_key),
) -> FeedbackStatsResponse:
    """Retorna estatísticas agregadas de feedback.

    Args:
        diagnostic_id: Filtrar por diagnóstico específico (opcional)
        user_id: Filtrar por usuário específico (opcional)
        auth: Autenticação via API key

    Returns:
        FeedbackStatsResponse com estatísticas agregadas

    Raises:
        HTTPException 500: Se erro ao calcular estatísticas
    """
    try:
        service = get_feedback_service()

        # Calcular estatísticas
        stats = service.get_feedback_stats(diagnostic_id=diagnostic_id, user_id=user_id)

        return FeedbackStatsResponse(**stats)

    except Exception as e:
        logger.error(f"[FEEDBACK] Erro ao calcular estatísticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular estatísticas: {e!s}")
