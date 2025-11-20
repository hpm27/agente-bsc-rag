"""Router de webhooks - /api/v1/webhooks/*.

5 endpoints para gerenciamento de webhooks:
- POST /webhooks - Registrar novo webhook
- GET /webhooks - Listar webhooks ativos
- GET /webhooks/{id} - Obter webhook por ID
- DELETE /webhooks/{id} - Desativar webhook
- POST /webhooks/{id}/test - Testar webhook (ping)

Fase: 4.3 - Integration APIs
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status

from api.dependencies import verify_api_key
from api.schemas.requests import RegisterWebhookRequest
from api.schemas.responses import WebhookListResponse, WebhookResponse, WebhookTestResponse
from api.services.webhook_dispatcher import WebhookDispatcher
from api.utils.rate_limit import LIMIT_READ, LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)

router = APIRouter()

# Storage temporário de webhooks (em produção, usar Redis/DB)
_webhooks_storage: dict[str, dict] = {}

# Instância global do dispatcher
_dispatcher = WebhookDispatcher()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_webhook(webhook_id: str) -> dict:
    """Busca webhook por ID."""
    webhook = _webhooks_storage.get(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook com ID '{webhook_id}' não encontrado.",
        )

    return webhook


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo webhook",
    description="Registra um novo webhook para receber notificações de eventos BSC.",
)
@limiter.limit(LIMIT_WRITE)
async def register_webhook(
    request: Request,
    response: Response,
    body: RegisterWebhookRequest,
    auth: dict = Depends(verify_api_key),
):
    """Registra um novo webhook."""
    logger.info(
        f"[API] register_webhook | url={body.url} | "
        f"events={len(body.events)} | client_id={auth.get('client_id')}"
    )

    try:
        # Validar URL
        dispatcher = WebhookDispatcher()
        if not dispatcher._validate_url(body.url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"URL inválida ou insegura: {body.url}",
            )

        # Criar webhook
        webhook_id = f"whk_{uuid.uuid4().hex[:12]}"
        webhook_data = {
            "webhook_id": webhook_id,
            "url": body.url,
            "events": body.events,
            "secret": body.secret,  # Armazenar secret para signature
            "secret_provided": body.secret is not None,
            "is_active": body.is_active,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "total_deliveries": 0,
            "failed_deliveries": 0,
            "client_id": auth.get("client_id"),  # Associar ao cliente da API key
        }

        _webhooks_storage[webhook_id] = webhook_data

        logger.info(f"[API] Webhook registrado: {webhook_id}")

        # Construir response (não incluir secret)
        return WebhookResponse(
            webhook_id=webhook_id,
            url=body.url,
            events=body.events,
            secret_provided=body.secret is not None,
            is_active=body.is_active,
            created_at=webhook_data["created_at"],
            last_triggered=None,
            total_deliveries=0,
            failed_deliveries=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao registrar webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar webhook: {e!s}",
        )


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="Listar webhooks",
    description="Lista todos os webhooks registrados (filtrado por cliente da API key).",
)
@limiter.limit(LIMIT_READ)
async def list_webhooks(request: Request, response: Response, auth: dict = Depends(verify_api_key)):
    """Lista webhooks do cliente."""
    logger.info(f"[API] list_webhooks | client_id={auth.get('client_id')}")

    try:
        # Filtrar webhooks do cliente (ou todos se admin)
        client_id = auth.get("client_id")
        permissions = auth.get("permissions", [])

        webhooks_list = []
        for webhook_id, webhook_data in _webhooks_storage.items():
            # Admin pode ver todos, outros só os próprios
            if "admin" in permissions or webhook_data.get("client_id") == client_id:
                webhooks_list.append(
                    WebhookResponse(
                        webhook_id=webhook_id,
                        url=webhook_data["url"],
                        events=webhook_data["events"],
                        secret_provided=webhook_data["secret_provided"],
                        is_active=webhook_data["is_active"],
                        created_at=webhook_data["created_at"],
                        last_triggered=webhook_data["last_triggered"],
                        total_deliveries=webhook_data["total_deliveries"],
                        failed_deliveries=webhook_data["failed_deliveries"],
                    )
                )

        return WebhookListResponse(
            webhooks=webhooks_list,
            total=len(webhooks_list),
        )

    except Exception as e:
        logger.error(f"[API] Erro ao listar webhooks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar webhooks: {e!s}",
        )


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Obter webhook por ID",
    description="Retorna detalhes de um webhook específico.",
)
@limiter.limit(LIMIT_READ)
async def get_webhook(
    request: Request, response: Response, webhook_id: str, auth: dict = Depends(verify_api_key)
):
    """Obtém webhook por ID."""
    logger.info(f"[API] get_webhook | webhook_id={webhook_id}")

    try:
        webhook_data = _get_webhook(webhook_id)

        # Verificar permissão (cliente só pode ver próprios webhooks, exceto admin)
        client_id = auth.get("client_id")
        permissions = auth.get("permissions", [])

        if "admin" not in permissions and webhook_data.get("client_id") != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este webhook.",
            )

        return WebhookResponse(
            webhook_id=webhook_id,
            url=webhook_data["url"],
            events=webhook_data["events"],
            secret_provided=webhook_data["secret_provided"],
            is_active=webhook_data["is_active"],
            created_at=webhook_data["created_at"],
            last_triggered=webhook_data["last_triggered"],
            total_deliveries=webhook_data["total_deliveries"],
            failed_deliveries=webhook_data["failed_deliveries"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao obter webhook {webhook_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter webhook: {e!s}",
        )


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar webhook",
    description="Desativa um webhook (soft delete - não remove, apenas marca como inativo).",
)
@limiter.limit(LIMIT_WRITE)
async def deactivate_webhook(
    request: Request, response: Response, webhook_id: str, auth: dict = Depends(verify_api_key)
):
    """Desativa webhook por ID."""
    logger.info(f"[API] deactivate_webhook | webhook_id={webhook_id}")

    try:
        webhook_data = _get_webhook(webhook_id)

        # Verificar permissão
        client_id = auth.get("client_id")
        permissions = auth.get("permissions", [])

        if "admin" not in permissions and webhook_data.get("client_id") != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para desativar este webhook.",
            )

        # Soft delete (marcar como inativo)
        webhook_data["is_active"] = False

        logger.info(f"[API] Webhook desativado: {webhook_id}")

        return  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao desativar webhook {webhook_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao desativar webhook: {e!s}",
        )


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookTestResponse,
    summary="Testar webhook",
    description="Envia evento de teste (ping) para validar webhook.",
)
@limiter.limit(LIMIT_WRITE)
async def test_webhook(
    request: Request,
    response: Response,
    webhook_id: str,
    background_tasks: BackgroundTasks,
    auth: dict = Depends(verify_api_key),
):
    """Testa webhook enviando evento de ping."""
    logger.info(f"[API] test_webhook | webhook_id={webhook_id}")

    try:
        webhook_data = _get_webhook(webhook_id)

        # Verificar permissão
        client_id = auth.get("client_id")
        permissions = auth.get("permissions", [])

        if "admin" not in permissions and webhook_data.get("client_id") != client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para testar este webhook.",
            )

        # Verificar se webhook está ativo
        if not webhook_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook está desativado. Ative antes de testar.",
            )

        # Enviar teste assíncrono
        dispatcher = WebhookDispatcher()
        test_result = await dispatcher.test_webhook(
            webhook_url=webhook_data["url"],
            secret=webhook_data.get("secret"),
        )

        # Atualizar estatísticas
        webhook_data["last_triggered"] = datetime.now().isoformat()
        if test_result.get("success"):
            webhook_data["total_deliveries"] += 1
        else:
            webhook_data["failed_deliveries"] += 1

        # Construir response
        return WebhookTestResponse(
            webhook_id=webhook_id,
            test_event_sent=True,
            response_status=test_result.get("status_code"),
            response_time_ms=test_result.get("response_time_ms"),
            error=test_result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao testar webhook {webhook_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao testar webhook: {e!s}",
        )
