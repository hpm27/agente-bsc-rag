"""Endpoints REST para sistema de notificações.

Este router fornece acesso programático ao sistema de notificações,
permitindo criar, buscar, marcar como lidas e listar notificações de eventos do workflow BSC.

Endpoints:
- POST /api/v1/notifications - Criar nova notificação
- GET /api/v1/notifications/{notification_id} - Buscar notificação específica
- PATCH /api/v1/notifications/{notification_id}/read - Marcar notificação como lida
- GET /api/v1/notifications - Listar notificações (filtros: user_id, type, status, priority)
- GET /api/v1/notifications/stats - Estatísticas agregadas de notificações

Fase: 4.7 - Notification System
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, Response, Query, Depends, HTTPException, Path
from starlette.responses import JSONResponse

from api.dependencies import verify_api_key
from api.schemas.responses import (
    NotificationRequest,
    NotificationResponse,
    NotificationListResponse,
    NotificationStatsResponse
)
from api.services.notification_service import get_notification_service, NotificationService
from api.utils.rate_limit import LIMIT_WRITE, LIMIT_READ, limiter
from src.memory.schemas import Notification

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=201,
    summary="Criar nova notificação",
    description="Cria notificação sobre evento do workflow BSC (diagnostic_completed, refinement_completed, etc)."
)
@limiter.limit(LIMIT_WRITE)
async def create_notification(
    request: Request,
    response: Response,
    body: NotificationRequest,
    auth: dict = Depends(verify_api_key)
) -> NotificationResponse:
    """Cria nova notificação sobre evento do workflow BSC.
    
    Args:
        body: Dados da notificação (type, user_id, title, message, priority)
        auth: Autenticação via API key
        
    Returns:
        NotificationResponse com notificação criada
        
    Raises:
        HTTPException 400: Se dados inválidos
        HTTPException 500: Se erro ao salvar
    """
    try:
        service = get_notification_service()
        
        # Criar instância Notification
        notification = Notification(
            type=body.type,
            user_id=body.user_id,
            diagnostic_id=body.diagnostic_id,
            title=body.title,
            message=body.message,
            priority=body.priority,
            metadata=body.metadata or {}
        )
        
        # Criar notificação
        notification_id = service.create_notification(notification)
        
        # Retornar response
        return NotificationResponse(
            id=notification_id,
            type=notification.type,
            user_id=notification.user_id,
            diagnostic_id=notification.diagnostic_id,
            title=notification.title,
            message=notification.message,
            status=notification.status,
            priority=notification.priority,
            metadata=notification.metadata,
            created_at=notification.created_at.isoformat(),
            read_at=None
        )
        
    except ValueError as e:
        logger.warning(f"[NOTIFICATION] [API] [CREATE] Dados inválidos: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[NOTIFICATION] [API] [CREATE] Erro ao criar notificação: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao criar notificação")


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Buscar notificação",
    description="Busca notificação específica por ID."
)
@limiter.limit(LIMIT_READ)
async def get_notification(
    request: Request,
    response: Response,
    notification_id: str = Path(..., description="ID da notificação"),
    auth: dict = Depends(verify_api_key)
) -> NotificationResponse:
    """Busca notificação específica por ID.
    
    Args:
        notification_id: ID da notificação
        auth: Autenticação via API key
        
    Returns:
        NotificationResponse com notificação encontrada
        
    Raises:
        HTTPException 404: Se notificação não encontrada
        HTTPException 500: Se erro ao buscar
    """
    try:
        service = get_notification_service()
        
        notification = service.get_notification(notification_id)
        
        if not notification:
            raise HTTPException(
                status_code=404,
                detail=f"Notificação {notification_id} não encontrada"
            )
        
        return NotificationResponse(
            id=notification.id,
            type=notification.type,
            user_id=notification.user_id,
            diagnostic_id=notification.diagnostic_id,
            title=notification.title,
            message=notification.message,
            status=notification.status,
            priority=notification.priority,
            metadata=notification.metadata,
            created_at=notification.created_at.isoformat(),
            read_at=notification.read_at.isoformat() if notification.read_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NOTIFICATION] [API] [GET] Erro ao buscar notificação: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar notificação")


@router.patch(
    "/{notification_id}/read",
    status_code=200,
    summary="Marcar notificação como lida",
    description="Marca notificação como lida e registra timestamp de leitura."
)
@limiter.limit(LIMIT_WRITE)
async def mark_notification_as_read(
    request: Request,
    response: Response,
    notification_id: str = Path(..., description="ID da notificação"),
    auth: dict = Depends(verify_api_key)
) -> dict:
    """Marca notificação como lida.
    
    Args:
        notification_id: ID da notificação
        auth: Autenticação via API key
        
    Returns:
        Dict com mensagem de sucesso
        
    Raises:
        HTTPException 404: Se notificação não encontrada
        HTTPException 500: Se erro ao marcar como lida
    """
    try:
        service = get_notification_service()
        
        success = service.mark_as_read(notification_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Notificação {notification_id} não encontrada"
            )
        
        return {
            "message": "Notificação marcada como lida",
            "notification_id": notification_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NOTIFICATION] [API] [READ] Erro ao marcar como lida: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao marcar notificação como lida")


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Listar notificações",
    description="Lista notificações com filtros opcionais (user_id, type, status, priority)."
)
@limiter.limit(LIMIT_READ)
async def list_notifications(
    request: Request,
    response: Response,
    user_id: Optional[str] = Query(None, description="Filtrar por usuário"),
    type_filter: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    status_filter: Optional[str] = Query(None, description="Filtrar por status (unread, read)"),
    priority_filter: Optional[str] = Query(None, description="Filtrar por prioridade (high, medium, low)"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    auth: dict = Depends(verify_api_key)
) -> NotificationListResponse:
    """Lista notificações com filtros opcionais.
    
    Args:
        user_id: Filtrar por usuário específico
        type_filter: Filtrar por tipo de evento
        status_filter: Filtrar por status (unread/read)
        priority_filter: Filtrar por prioridade
        limit: Limite de resultados (1-1000)
        auth: Autenticação via API key
        
    Returns:
        NotificationListResponse com lista de notificações
        
    Raises:
        HTTPException 500: Se erro ao listar
    """
    try:
        service = get_notification_service()
        
        notifications = service.list_notifications(
            user_id=user_id,
            type_filter=type_filter,
            status_filter=status_filter,
            priority_filter=priority_filter,
            limit=limit
        )
        
        # Converter para NotificationResponse
        notification_responses = [
            NotificationResponse(
                id=notif.id,
                type=notif.type,
                user_id=notif.user_id,
                diagnostic_id=notif.diagnostic_id,
                title=notif.title,
                message=notif.message,
                status=notif.status,
                priority=notif.priority,
                metadata=notif.metadata,
                created_at=notif.created_at.isoformat(),
                read_at=notif.read_at.isoformat() if notif.read_at else None
            )
            for notif in notifications
        ]
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=len(notification_responses)
        )
        
    except Exception as e:
        logger.error(f"[NOTIFICATION] [API] [LIST] Erro ao listar notificações: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao listar notificações")


@router.get(
    "/stats",
    response_model=NotificationStatsResponse,
    summary="Estatísticas de notificações",
    description="Retorna estatísticas agregadas de notificações (total, não lidas, por prioridade/tipo)."
)
@limiter.limit(LIMIT_READ)
async def get_notification_stats(
    request: Request,
    response: Response,
    user_id: str = Query(..., description="ID do usuário"),
    auth: dict = Depends(verify_api_key)
) -> NotificationStatsResponse:
    """Retorna estatísticas de notificações de um usuário.
    
    Args:
        user_id: ID do usuário
        auth: Autenticação via API key
        
    Returns:
        NotificationStatsResponse com estatísticas
        
    Raises:
        HTTPException 500: Se erro ao calcular estatísticas
    """
    try:
        service = get_notification_service()
        
        # Listar todas notificações do usuário
        all_notifications = service.list_notifications(user_id=user_id, limit=1000)
        
        # Calcular estatísticas
        total_count = len(all_notifications)
        unread_count = service.get_unread_count(user_id)
        by_priority = service.get_stats_by_priority(user_id)
        
        # Contagem por tipo
        by_type = {}
        for notif in all_notifications:
            by_type[notif.type] = by_type.get(notif.type, 0) + 1
        
        return NotificationStatsResponse(
            total_count=total_count,
            unread_count=unread_count,
            by_priority=by_priority,
            by_type=by_type
        )
        
    except Exception as e:
        logger.error(f"[NOTIFICATION] [API] [STATS] Erro ao calcular estatísticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao calcular estatísticas")

