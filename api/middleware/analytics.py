"""Middleware de Analytics para coleta automática de métricas da API.

Este middleware intercepta todos os requests HTTP e coleta métricas:
- Endpoint acessado
- Método HTTP
- Status code da resposta
- Latência (tempo de processamento)
- API key do cliente (se presente)

As métricas são enviadas para MetricsService que armazena em Redis.

Fase: 4.4 - Advanced Analytics Dashboard
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware que coleta métricas de todos os requests HTTP.

    Intercepta requests antes e depois do processamento para coletar:
    - Endpoint (path)
    - Método HTTP (GET, POST, etc)
    - Status code da resposta
    - Latência em milissegundos
    - API key do cliente (extraída do header X-API-Key)

    As métricas são enviadas assincronamente para MetricsService
    para não impactar a performance da API.

    Usage:
        from api.middleware import AnalyticsMiddleware

        app.add_middleware(AnalyticsMiddleware)
    """

    def __init__(self, app, metrics_service=None):
        """Inicializa middleware de analytics.

        Args:
            app: FastAPI application instance
            metrics_service: Instância de MetricsService (opcional, cria se None)
        """
        super().__init__(app)
        self.metrics_service = metrics_service
        logger.info("[ANALYTICS] Middleware de analytics inicializado")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Intercepta request e coleta métricas.

        Args:
            request: Request HTTP
            call_next: Próximo handler na cadeia

        Returns:
            Response HTTP processada
        """
        # Ignorar endpoints de health e docs (não são métricas relevantes)
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Marcar início do processamento
        start_time = time.time()

        # Extrair informações do request
        endpoint = request.url.path
        method = request.method
        api_key = self._extract_api_key(request)

        # Executar request (próximo handler)
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            # Capturar exceções não tratadas (500 errors)
            status_code = 500
            error = str(e)
            logger.error(f"[ANALYTICS] Erro ao processar request: {e}", exc_info=True)
            raise

        # Calcular latência em milissegundos
        latency_ms = (time.time() - start_time) * 1000

        # Coletar métrica (assíncrono, não bloqueia response)
        try:
            await self._record_metric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                latency_ms=latency_ms,
                api_key=api_key,
                error=error,
            )
        except Exception as e:
            # Não falhar request se coleta de métricas falhar
            logger.warning(f"[ANALYTICS] Erro ao coletar métrica: {e}")

        return response

    def _should_skip(self, path: str) -> bool:
        """Verifica se endpoint deve ser ignorado na coleta de métricas.

        Args:
            path: Caminho do endpoint

        Returns:
            True se deve ignorar, False caso contrário
        """
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]

        return path in skip_paths or path.startswith("/docs/") or path.startswith("/static/")

    def _extract_api_key(self, request: Request) -> str | None:
        """Extrai API key do header X-API-Key.

        Args:
            request: Request HTTP

        Returns:
            API key se presente, None caso contrário
        """
        api_key = request.headers.get("X-API-Key")

        # Mascarar API key para logs (segurança)
        if api_key:
            if len(api_key) > 20:
                masked_key = f"{api_key[:10]}...{api_key[-6:]}"
            else:
                masked_key = f"{api_key[:6]}..."
            return masked_key

        return None

    async def _record_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        api_key: str | None = None,
        error: str | None = None,
    ) -> None:
        """Registra métrica no MetricsService.

        Args:
            endpoint: Caminho do endpoint (ex: /api/v1/clients)
            method: Método HTTP (GET, POST, etc)
            status_code: Status code da resposta (200, 404, 500, etc)
            latency_ms: Latência em milissegundos
            api_key: API key do cliente (opcional)
            error: Mensagem de erro se houver (opcional)
        """
        # Se MetricsService não foi injetado, criar instância lazy
        if self.metrics_service is None:
            # Importação lazy para evitar circular imports
            from api.services.metrics_service import MetricsService

            self.metrics_service = MetricsService()

        # Chamar método de registro (assíncrono)
        await self.metrics_service.record_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            api_key=api_key,
            error=error,
        )
