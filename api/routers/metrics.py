"""Endpoints REST para sistema de performance monitoring.

Este router fornece acesso programático às métricas de performance,
permitindo listar métricas individuais e visualizar estatísticas agregadas.

Endpoints:
- GET /api/v1/metrics - Listar métricas (filtros: endpoint, method, user_id, status_code, hours)
- GET /api/v1/metrics/stats - Estatísticas agregadas (P50, P95, Mean latency, tokens, custo)

Fase: 4.8 - Performance Monitoring
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.dependencies import verify_api_key
from api.schemas.responses import MetricsListResponse, MetricsStatsResponse
from api.services.performance_service import get_performance_service

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Rate limits por endpoint
LIMIT_READ = "100/minute"


def _get_performance_service():
    """Dependency para obter PerformanceService instance.

    Permite override via dependency_overrides para testes.
    """
    return get_performance_service()


@router.get(
    "/",
    response_model=MetricsListResponse,
    summary="Listar métricas de performance",
    description="Lista métricas de performance com filtros opcionais (endpoint, method, user_id, status_code, hours).",
)
@limiter.limit(LIMIT_READ)
async def list_metrics(
    request: Request,
    response: Response,
    endpoint: str | None = Query(None, description="Filtrar por endpoint específico"),
    method: str | None = Query(None, description="Filtrar por método HTTP (GET, POST, etc)"),
    user_id: str | None = Query(None, description="Filtrar por user_id"),
    status_code: int | None = Query(
        None, ge=100, le=599, description="Filtrar por status code (100-599)"
    ),
    hours: int = Query(
        24, ge=1, le=168, description="Buscar métricas das últimas N horas (1-168, default: 24)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados (1-1000)"),
    auth: dict = Depends(verify_api_key),
    service=Depends(_get_performance_service),
) -> MetricsListResponse:
    """Lista métricas de performance com filtros opcionais.

    Args:
        endpoint: Filtrar por endpoint específico (ex: /api/v1/diagnostics)
        method: Filtrar por método HTTP (GET, POST, PATCH, DELETE, PUT)
        user_id: Filtrar por user_id específico
        status_code: Filtrar por código HTTP (100-599)
        hours: Buscar métricas das últimas N horas (1-168, default: 24)
        limit: Limite de resultados (1-1000, default: 100)
        auth: Autenticação via API key

    Returns:
        MetricsListResponse com lista de métricas filtradas

    Raises:
        HTTPException 400: Filtros inválidos
        HTTPException 500: Erro ao listar métricas
    """
    try:
        logger.info(
            f"[METRICS] [LIST] Listando métricas | endpoint={endpoint} | "
            f"method={method} | user_id={user_id} | status={status_code} | "
            f"hours={hours} | limit={limit}"
        )

        # service já vem via Depends(_get_performance_service)

        # Buscar métricas com filtros
        metrics = service.get_metrics(
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            status_code=status_code,
            hours=hours,
            limit=limit,
        )

        # Serializar métricas para dicts
        metrics_dicts = [metric.to_dict() for metric in metrics]

        # Construir response
        filters_applied = {
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "status_code": status_code,
            "hours": hours,
            "limit": limit,
        }

        response_data = MetricsListResponse(
            metrics=metrics_dicts, total=len(metrics_dicts), filters_applied=filters_applied
        )

        logger.info(
            f"[METRICS] [LIST] Retornando {len(metrics_dicts)} métricas | "
            f"filters={filters_applied}"
        )

        return response_data

    except ValueError as e:
        logger.error(f"[METRICS] [LIST] Validação falhou: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[METRICS] [LIST] Erro ao listar métricas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao listar métricas")


@router.get(
    "/stats",
    response_model=MetricsStatsResponse,
    summary="Estatísticas agregadas de performance",
    description="Agrega estatísticas de performance: P50/P95/Mean latency, taxa de erro, throughput, tokens LLM, custo estimado.",
)
@limiter.limit(LIMIT_READ)
async def get_metrics_stats(
    request: Request,
    response: Response,
    endpoint: str | None = Query(
        None, description="Filtrar por endpoint específico (ou None para todos)"
    ),
    hours: int = Query(
        24, ge=1, le=168, description="Agregar métricas das últimas N horas (1-168, default: 24)"
    ),
    auth: dict = Depends(verify_api_key),
    service=Depends(_get_performance_service),
) -> MetricsStatsResponse:
    """Agrega estatísticas de performance das métricas.

    Calcula:
    - Latência P50, P95, Mean, Min, Max
    - Total de requests e taxa de erro
    - Throughput (requests/min)
    - Tokens consumidos (input/output por modelo LLM)
    - Custo estimado em USD (baseado em pricing LLM)

    Args:
        endpoint: Filtrar por endpoint específico (ou None para todos)
        hours: Agregar métricas das últimas N horas (1-168, default: 24)
        auth: Autenticação via API key

    Returns:
        MetricsStatsResponse com estatísticas agregadas

    Raises:
        HTTPException 400: Filtros inválidos
        HTTPException 500: Erro ao agregar estatísticas

    Example:
        >>> GET /api/v1/metrics/stats?hours=24&endpoint=/api/v1/diagnostics
        {
            "total_requests": 150,
            "error_requests": 5,
            "error_rate": 3.33,
            "throughput_per_min": 6.25,
            "latency": {
                "p50_ms": 12345.67,
                "p95_ms": 23456.78,
                "mean_ms": 14567.89,
                "min_ms": 5678.90,
                "max_ms": 34567.89
            },
            "tokens": {
                "gpt-5-mini-2025-08-07": {
                    "tokens_in": 123456,
                    "tokens_out": 56789,
                    "total_tokens": 180245
                }
            },
            "cost_usd": 24.56,
            "period_hours": 24,
            "endpoint": "/api/v1/diagnostics"
        }
    """
    try:
        logger.info(
            f"[METRICS] [STATS] Agregando estatísticas | "
            f"endpoint={endpoint or 'ALL'} | hours={hours}"
        )

        # service já vem via Depends(_get_performance_service)

        # Agregar estatísticas
        stats = service.aggregate_stats(endpoint=endpoint, hours=hours)

        # Construir response
        response_data = MetricsStatsResponse(**stats)

        logger.info(
            f"[METRICS] [STATS] Estatísticas agregadas | "
            f"total={stats['total_requests']} | error_rate={stats['error_rate']}% | "
            f"p95={stats['latency']['p95_ms']:.2f}ms | cost=${stats['cost_usd']:.4f}"
        )

        return response_data

    except ValueError as e:
        logger.error(f"[METRICS] [STATS] Validação falhou: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[METRICS] [STATS] Erro ao agregar estatísticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao agregar estatísticas")
