"""Webhook Dispatcher: Serviço para envio assíncrono de webhooks.

Implementa:
- Delivery assíncrono de webhooks
- Retry logic (3 tentativas com exponential backoff)
- HMAC-SHA256 signature verification
- Logging estruturado de deliveries

Fase: 4.3 - Integration APIs
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Dispatcher para envio assíncrono de webhooks com retry e signature.
    
    Attributes:
        timeout_seconds: Timeout para requisições HTTP (default: 10s)
        max_retries: Número máximo de tentativas (default: 3)
        retry_delays: Delays entre tentativas em segundos (exponential backoff)
    
    Example:
        >>> dispatcher = WebhookDispatcher()
        >>> await dispatcher.deliver(
        ...     event_type="diagnostic.completed",
        ...     payload={"diagnostic_id": "diag_123"},
        ...     webhook_url="https://cliente.com/webhooks",
        ...     secret="whsec_abc123"
        ... )
    """
    
    def __init__(
        self,
        timeout_seconds: int = 10,
        max_retries: int = 3,
    ):
        """Inicializa dispatcher com configurações."""
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delays = [1, 2, 5]  # Exponential backoff: 1s, 2s, 5s
        
        logger.info(
            f"[WEBHOOK_DISPATCHER] Inicializado | "
            f"timeout={timeout_seconds}s | max_retries={max_retries}"
        )
    
    def _generate_signature(
        self,
        payload: str,
        secret: str
    ) -> str:
        """Gera assinatura HMAC-SHA256 para payload.
        
        Formato: sha256={hex_signature}
        
        Args:
            payload: JSON string do payload
            secret: Secret para assinatura
        
        Returns:
            str: Assinatura no formato "sha256={hex}"
        """
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _validate_url(self, url: str) -> bool:
        """Valida se URL é válida e segura (HTTPS em produção)."""
        try:
            parsed = urlparse(url)
            
            # Validar scheme
            if parsed.scheme not in ["http", "https"]:
                return False
            
            # Em produção, forçar HTTPS
            if not settings.debug and parsed.scheme != "https":
                logger.warning(
                    f"[WEBHOOK_DISPATCHER] URL não-HTTPS em produção: {url}"
                )
                return False
            
            # Validar hostname
            if not parsed.hostname:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"[WEBHOOK_DISPATCHER] Erro ao validar URL: {e}")
            return False
    
    async def deliver(
        self,
        event_type: str,
        payload: Dict[str, Any],
        webhook_url: str,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Envia webhook com retry logic e signature.
        
        Args:
            event_type: Tipo de evento (ex: "diagnostic.completed")
            payload: Dados do evento
            webhook_url: URL do endpoint webhook
            secret: Secret para HMAC signature (opcional)
        
        Returns:
            dict: Resultado do delivery com status, attempts, response_time_ms
        
        Raises:
            ValueError: Se URL inválida
            httpx.HTTPError: Se todas tentativas falharam
        """
        # Validar URL
        if not self._validate_url(webhook_url):
            raise ValueError(f"URL inválida ou insegura: {webhook_url}")
        
        # Construir payload completo
        full_payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": payload,
        }
        
        payload_json = json.dumps(full_payload, ensure_ascii=False)
        
        # Gerar signature se secret fornecido
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"BSC-RAG-API/{settings.app_version}",
        }
        
        if secret:
            signature = self._generate_signature(payload_json, secret)
            headers["X-Webhook-Signature"] = signature
        
        # Tentativas de delivery
        last_error = None
        attempts = []
        
        for attempt_num in range(1, self.max_retries + 1):
            try:
                start_time = datetime.now()
                
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        webhook_url,
                        content=payload_json,
                        headers=headers,
                    )
                
                response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                # Sucesso (2xx)
                if 200 <= response.status_code < 300:
                    logger.info(
                        f"[WEBHOOK_DISPATCHER] Delivery bem-sucedido | "
                        f"event={event_type} | url={webhook_url} | "
                        f"attempt={attempt_num} | status={response.status_code} | "
                        f"time={response_time_ms:.0f}ms"
                    )
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "attempts": attempt_num,
                        "response_time_ms": round(response_time_ms, 2),
                        "delivered_at": datetime.now().isoformat(),
                    }
                
                # Erro retryable (5xx, timeout)
                if response.status_code >= 500 or response.status_code == 429:
                    error_msg = f"HTTP {response.status_code}"
                    last_error = httpx.HTTPStatusError(
                        f"Status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    
                    attempts.append({
                        "attempt": attempt_num,
                        "status_code": response.status_code,
                        "error": error_msg,
                        "response_time_ms": round(response_time_ms, 2),
                    })
                    
                    # Aguardar antes de retry (exceto última tentativa)
                    if attempt_num < self.max_retries:
                        delay = self.retry_delays[attempt_num - 1]
                        logger.warning(
                            f"[WEBHOOK_DISPATCHER] Retry em {delay}s | "
                            f"event={event_type} | attempt={attempt_num}/{self.max_retries} | "
                            f"status={response.status_code}"
                        )
                        await asyncio.sleep(delay)
                    
                    continue
                
                # Erro não-retryable (4xx exceto 429)
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(
                    f"[WEBHOOK_DISPATCHER] Erro não-retryable | "
                    f"event={event_type} | url={webhook_url} | "
                    f"status={response.status_code}"
                )
                
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "attempts": attempt_num,
                    "error": error_msg,
                    "response_time_ms": round(response_time_ms, 2),
                }
                
            except httpx.TimeoutException as e:
                last_error = e
                attempts.append({
                    "attempt": attempt_num,
                    "error": "Timeout",
                    "response_time_ms": None,
                })
                
                if attempt_num < self.max_retries:
                    delay = self.retry_delays[attempt_num - 1]
                    logger.warning(
                        f"[WEBHOOK_DISPATCHER] Timeout, retry em {delay}s | "
                        f"event={event_type} | attempt={attempt_num}/{self.max_retries}"
                    )
                    await asyncio.sleep(delay)
                
            except Exception as e:
                last_error = e
                attempts.append({
                    "attempt": attempt_num,
                    "error": str(e),
                    "response_time_ms": None,
                })
                
                if attempt_num < self.max_retries:
                    delay = self.retry_delays[attempt_num - 1]
                    await asyncio.sleep(delay)
        
        # Todas tentativas falharam
        logger.error(
            f"[WEBHOOK_DISPATCHER] Todas tentativas falharam | "
            f"event={event_type} | url={webhook_url} | "
            f"attempts={len(attempts)}"
        )
        
        return {
            "success": False,
            "attempts": attempts,
            "error": f"Todas {self.max_retries} tentativas falharam: {str(last_error)}",
            "last_error": str(last_error) if last_error else None,
        }
    
    async def test_webhook(
        self,
        webhook_url: str,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Envia evento de teste (ping) para validar webhook.
        
        Args:
            webhook_url: URL do webhook
            secret: Secret para signature
        
        Returns:
            dict: Resultado do teste
        """
        test_payload = {
            "test": True,
            "message": "Webhook test event from BSC RAG API",
        }
        
        return await self.deliver(
            event_type="webhook.test",
            payload=test_payload,
            webhook_url=webhook_url,
            secret=secret,
        )

