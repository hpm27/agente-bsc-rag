"""Middleware de Performance Monitoring para observability do sistema.

Este middleware intercepta todos os requests HTTP e captura métricas de performance:
- Latência de cada endpoint (milissegundos)
- Status code da resposta
- User ID (se autenticado)
- Diagnostic ID (se presente no state/response)
- Tokens LLM consumidos (capturado via context vars)
- Metadata adicional (query_length, response_size, etc)

As métricas são enviadas para PerformanceService que armazena em Mem0.

Fase: 4.8 - Performance Monitoring
"""

import json
import logging
import time
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.services.performance_service import get_performance_service
from src.memory.schemas import PerformanceMetrics

logger = logging.getLogger(__name__)


# Context variables para capturar tokens LLM (acessível entre middleware e handlers)
llm_tokens_in_ctx: ContextVar[int] = ContextVar("llm_tokens_in", default=0)
llm_tokens_out_ctx: ContextVar[int] = ContextVar("llm_tokens_out", default=0)
llm_model_name_ctx: ContextVar[str | None] = ContextVar("llm_model_name", default=None)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware que captura métricas de performance de todos os requests HTTP.

    Intercepta requests antes e depois do processamento para coletar:
    - Latência em milissegundos (tempo total de processamento)
    - Status code da resposta
    - User ID (extraído do header X-API-Key ou state)
    - Diagnostic ID (extraído da response se presente)
    - Tokens LLM (input/output via context vars)
    - Metadata adicional (query_length, response_size, cache_hit)

    As métricas são enviadas assincronamente para PerformanceService
    para não impactar a performance da API.

    Usage:
        from api.middleware import PerformanceMiddleware

        app.add_middleware(PerformanceMiddleware)

        # Em handlers LLM, registrar tokens:
        from api.middleware.performance import llm_tokens_in_ctx, llm_tokens_out_ctx

        llm_tokens_in_ctx.set(1234)
        llm_tokens_out_ctx.set(567)
        llm_model_name_ctx.set("gpt-5-mini-2025-08-07")
    """

    def __init__(self, app, performance_service=None):
        """Inicializa middleware de performance monitoring.

        Args:
            app: FastAPI application instance
            performance_service: Instância de PerformanceService (opcional, lazy-loaded no dispatch)
        """
        super().__init__(app)
        self.performance_service = (
            performance_service  # Lazy loading (inicializado no dispatch se None)
        )
        logger.info("[PERFORMANCE] Middleware de performance monitoring inicializado")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Intercepta request e captura métricas de performance.

        Args:
            request: Request HTTP
            call_next: Próximo handler na cadeia

        Returns:
            Response HTTP processada
        """
        # Ignorar endpoints de health, docs, e metrics (evitar recursão)
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Resetar context vars para este request
        llm_tokens_in_ctx.set(0)
        llm_tokens_out_ctx.set(0)
        llm_model_name_ctx.set(None)

        # Marcar início do processamento
        start_time = time.time()

        # Extrair informações do request
        endpoint = request.url.path
        method = request.method
        user_id = self._extract_user_id(request)

        # Executar request (próximo handler)
        response = None
        error_message = None
        diagnostic_id = None

        try:
            response = await call_next(request)

            # Tentar extrair diagnostic_id da response (se JSON)
            if response.headers.get("content-type", "").startswith("application/json"):
                diagnostic_id = await self._extract_diagnostic_id(response)

        except Exception as e:
            # Capturar erro para registrar na métrica
            error_message = str(e)[:1000]  # Truncar para não explodir storage
            logger.error(
                f"[PERFORMANCE] Erro no endpoint {endpoint}: {error_message}", exc_info=True
            )
            # Re-lançar erro (não consumir exceção)
            raise

        finally:
            # Calcular latência
            duration_ms = (time.time() - start_time) * 1000

            # Capturar tokens LLM do context
            tokens_in = llm_tokens_in_ctx.get()
            tokens_out = llm_tokens_out_ctx.get()
            model_name = llm_model_name_ctx.get()

            # Construir metadata adicional
            metadata = {
                "query_length": len(await request.body()) if request.method == "POST" else 0,
                "user_agent": request.headers.get("user-agent", "unknown"),
                "remote_addr": request.client.host if request.client else "unknown",
            }

            # Adicionar response_size se response disponível
            if response:
                metadata["response_size"] = int(response.headers.get("content-length", 0))

            # Criar métrica
            try:
                metric = PerformanceMetrics(
                    endpoint=endpoint,
                    method=method,
                    duration_ms=duration_ms,
                    status_code=response.status_code if response else 500,
                    user_id=user_id,
                    diagnostic_id=diagnostic_id,
                    tokens_in=tokens_in if tokens_in > 0 else None,
                    tokens_out=tokens_out if tokens_out > 0 else None,
                    model_name=model_name,
                    error_message=error_message,
                    metadata=metadata,
                )

                # Lazy loading de PerformanceService (evitar erro em testes sem .env)
                if self.performance_service is None:
                    self.performance_service = get_performance_service()

                # Enviar métrica para PerformanceService (assíncrono, não bloquear)
                # TODO: Implementar queue async para não bloquear response
                self.performance_service.create_metric(metric)

                logger.debug(
                    f"[PERFORMANCE] Métrica capturada | "
                    f"endpoint={endpoint} | duration_ms={duration_ms:.2f} | "
                    f"status={metric.status_code} | tokens_in={tokens_in} | tokens_out={tokens_out}"
                )

            except Exception as e:
                # Não deixar erro de métrica impactar response
                logger.error(f"[PERFORMANCE] Erro ao criar métrica: {e}", exc_info=True)

        return response

    def _should_skip(self, path: str) -> bool:
        """Verifica se endpoint deve ser ignorado (não coletar métricas).

        Args:
            path: Path do endpoint

        Returns:
            True se deve ignorar, False se deve coletar métricas
        """
        skip_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/metrics",  # Evitar recursão (endpoint de métricas)
            "/api/v1/metrics/stats",
        }

        return path in skip_paths or path.startswith("/static")

    def _extract_user_id(self, request: Request) -> str | None:
        """Extrai user_id do request (header X-API-Key ou state).

        Args:
            request: Request HTTP

        Returns:
            user_id ou None
        """
        # Tentar extrair do header X-API-Key
        api_key = request.headers.get("x-api-key")
        if api_key:
            # API key format: bsc_live_xxxx ou bsc_test_xxxx
            # Usar api_key como user_id (simplificado para MVP)
            return api_key[:20]  # Truncar para não expor key completa

        # Tentar extrair do state (se request passou por auth)
        if hasattr(request.state, "user_id"):
            return request.state.user_id

        return None

    async def _extract_diagnostic_id(self, response: Response) -> str | None:
        """Extrai diagnostic_id da response JSON (se presente).

        Args:
            response: Response HTTP

        Returns:
            diagnostic_id ou None
        """
        try:
            # Tentar parsear body como JSON
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Recriar body_iterator como async generator para response não ficar corrompida
            async def async_body_iterator():
                yield body

            response.body_iterator = async_body_iterator()

            # Parsear JSON
            data = json.loads(body.decode())

            # Buscar diagnostic_id em campos comuns
            diagnostic_id = (
                data.get("diagnostic_id")
                or data.get("id")
                or data.get("result", {}).get("diagnostic_id")
            )

            return diagnostic_id

        except Exception:
            # Não é JSON ou erro ao parsear (ignorar silenciosamente)
            return None


def track_llm_tokens(tokens_in: int, tokens_out: int, model_name: str):
    """Helper function para registrar tokens LLM consumidos.

    Deve ser chamada em handlers que fazem LLM calls para capturar tokens.

    Args:
        tokens_in: Tokens de input
        tokens_out: Tokens de output
        model_name: Nome do modelo LLM (ex: gpt-5-mini-2025-08-07)

    Example:
        >>> from api.middleware.performance import track_llm_tokens
        >>>
        >>> # Em handler de diagnostic
        >>> response = llm.invoke(messages)
        >>> tokens_in = response.response_metadata["token_usage"]["prompt_tokens"]
        >>> tokens_out = response.response_metadata["token_usage"]["completion_tokens"]
        >>> track_llm_tokens(tokens_in, tokens_out, "gpt-5-mini-2025-08-07")
    """
    # Acumular tokens (pode haver múltiplas chamadas LLM no mesmo request)
    current_in = llm_tokens_in_ctx.get() or 0
    current_out = llm_tokens_out_ctx.get() or 0

    llm_tokens_in_ctx.set(current_in + tokens_in)
    llm_tokens_out_ctx.set(current_out + tokens_out)
    llm_model_name_ctx.set(model_name)  # Último modelo usado
