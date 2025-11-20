"""Endpoints REST para analytics e métricas da API.

Este router fornece acesso programático às métricas coletadas pelo
AnalyticsMiddleware, permitindo integração com dashboards externos.

Endpoints:
- GET /analytics/overview - KPIs principais
- GET /analytics/traffic - Requests/min (time-series)
- GET /analytics/performance - Latência por endpoint
- GET /analytics/errors - Taxa de erros
- GET /analytics/consumers - Uso por API key
- GET /analytics/endpoints - Métricas por endpoint

Fase: 4.4 - Advanced Analytics Dashboard
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from api.dependencies import verify_api_key
from api.schemas.responses import (
    ConsumerMetricsResponse,
    EndpointMetricsResponse,
    ErrorMetricsResponse,
    LatencyMetricsResponse,
    OverviewMetricsResponse,
    TrafficDataPoint,
    TrafficResponse,
)
from api.services.metrics_service import MetricsService
from api.utils.rate_limit import LIMIT_READ, limiter

logger = logging.getLogger(__name__)

router = APIRouter()

# Instância global do MetricsService
_metrics_service = None


def get_metrics_service() -> MetricsService:
    """Retorna instância singleton do MetricsService."""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service


@router.get(
    "/overview",
    response_model=OverviewMetricsResponse,
    summary="KPIs principais do dashboard",
    description="Retorna métricas agregadas principais: total requests, taxa de erros, latência média, API keys ativas.",
)
@limiter.limit(LIMIT_READ)
async def get_overview(
    request: Request,
    response: Response,
    period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
    auth: dict = Depends(verify_api_key),
):
    """Retorna KPIs principais do dashboard analytics."""
    try:
        service = get_metrics_service()

        # Calcular start_time baseado no período
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(hours=24)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_time = datetime.now() - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Período inválido. Use: 1h, 24h, 7d, 30d")

        # Buscar dados agregados
        requests_data = await service.get_requests_by_endpoint(
            start_time=start_time, end_time=datetime.now()
        )

        total_requests = sum(r["count"] for r in requests_data)
        total_errors = sum(r["errors"] for r in requests_data)
        error_rate = total_errors / total_requests if total_requests > 0 else 0.0

        # Buscar latência média (aproximação via top endpoints)
        top_endpoints = await service.get_top_endpoints(metric="latency", limit=10, period=period)
        if top_endpoints:
            avg_latency = sum(e.get("mean", 0) for e in top_endpoints) / len(top_endpoints)
        else:
            avg_latency = 0.0

        # Buscar API keys ativas
        consumers = await service.get_top_consumers(limit=100, period=period)
        active_api_keys = len(consumers)

        return OverviewMetricsResponse(
            total_requests=total_requests,
            error_rate=error_rate,
            avg_latency_ms=avg_latency,
            active_api_keys=active_api_keys,
            period=period,
        )
    except Exception as e:
        logger.error(f"[ANALYTICS] Erro ao buscar overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar métricas: {e!s}")


@router.get(
    "/traffic",
    response_model=TrafficResponse,
    summary="Dados de tráfego (time-series)",
    description="Retorna requests/min ao longo do tempo para análise de tráfego.",
)
@limiter.limit(LIMIT_READ)
async def get_traffic(
    request: Request,
    response: Response,
    endpoint: str | None = Query(None, description="Endpoint específico (opcional)"),
    period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
    interval: str = Query("minute", description="Intervalo: minute, hour, day"),
    auth: dict = Depends(verify_api_key),
):
    """Retorna dados de tráfego em formato time-series."""
    try:
        service = get_metrics_service()

        # Calcular start_time
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(hours=24)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_time = datetime.now() - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Período inválido")

        if interval not in ["minute", "hour", "day"]:
            raise HTTPException(
                status_code=400, detail="Intervalo inválido. Use: minute, hour, day"
            )

        # Buscar dados
        requests_data = await service.get_requests_by_endpoint(
            endpoint=endpoint, start_time=start_time, end_time=datetime.now(), interval=interval
        )

        # Converter para TrafficDataPoint
        data_points = [
            TrafficDataPoint(
                timestamp=r["timestamp"],
                endpoint=r["endpoint"],
                count=r["count"],
                errors=r["errors"],
                error_4xx=r.get("4xx", 0),
                error_5xx=r.get("5xx", 0),
            )
            for r in requests_data
        ]

        return TrafficResponse(data=data_points, period=period, interval=interval)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYTICS] Erro ao buscar traffic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar tráfego: {e!s}")


@router.get(
    "/performance",
    response_model=LatencyMetricsResponse,
    summary="Métricas de latência por endpoint",
    description="Retorna percentis de latência (P50, P95, P99) para um endpoint específico.",
)
@limiter.limit(LIMIT_READ)
async def get_performance(
    request: Request,
    response: Response,
    endpoint: str = Query(..., description="Endpoint a analisar"),
    period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
    auth: dict = Depends(verify_api_key),
):
    """Retorna métricas de latência para um endpoint."""
    try:
        service = get_metrics_service()

        # Calcular start_time
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(hours=24)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_time = datetime.now() - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Período inválido")

        # Buscar percentis
        latency_data = await service.get_latency_percentiles(
            endpoint=endpoint, start_time=start_time, end_time=datetime.now()
        )

        return LatencyMetricsResponse(
            endpoint=endpoint,
            p50=latency_data["p50"],
            p95=latency_data["p95"],
            p99=latency_data["p99"],
            mean=latency_data["mean"],
            max=latency_data["max"],
            samples=latency_data["samples"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYTICS] Erro ao buscar performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar latência: {e!s}")


@router.get(
    "/errors",
    response_model=list[ErrorMetricsResponse],
    summary="Taxa de erros por endpoint",
    description="Retorna taxa de erros (4xx, 5xx) para todos os endpoints.",
)
@limiter.limit(LIMIT_READ)
async def get_errors(
    request: Request,
    response: Response,
    period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
    auth: dict = Depends(verify_api_key),
):
    """Retorna taxa de erros por endpoint."""
    try:
        service = get_metrics_service()

        # Calcular start_time
        if period == "1h":
            start_time = datetime.now() - timedelta(hours=1)
        elif period == "24h":
            start_time = datetime.now() - timedelta(hours=24)
        elif period == "7d":
            start_time = datetime.now() - timedelta(days=7)
        elif period == "30d":
            start_time = datetime.now() - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Período inválido")

        # Buscar erros
        errors_data = await service.get_errors_by_endpoint(
            start_time=start_time, end_time=datetime.now()
        )

        return [
            ErrorMetricsResponse(
                endpoint=e["endpoint"],
                total_requests=e["total_requests"],
                errors=e["errors"],
                error_rate=e["error_rate"],
            )
            for e in errors_data
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYTICS] Erro ao buscar errors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar erros: {e!s}")


@router.get(
    "/consumers",
    response_model=list[ConsumerMetricsResponse],
    summary="Uso por cliente (API key)",
    description="Retorna top API keys por volume de requests.",
)
@limiter.limit(LIMIT_READ)
async def get_consumers(
    request: Request,
    response: Response,
    limit: int = Query(10, ge=1, le=100, description="Número de consumers a retornar"),
    period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
    auth: dict = Depends(verify_api_key),
):
    """Retorna top consumers por volume de requests."""
    try:
        service = get_metrics_service()

        # Buscar top consumers
        consumers = await service.get_top_consumers(limit=limit, period=period)

        return [
            ConsumerMetricsResponse(
                api_key=c["api_key"],
                requests=c["requests"],
                unique_endpoints=c["unique_endpoints"],
                last_request=c["last_request"],
            )
            for c in consumers
        ]
    except Exception as e:
        logger.error(f"[ANALYTICS] Erro ao buscar consumers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar consumers: {e!s}")


@router.get(
    "/endpoints",
    response_model=list[EndpointMetricsResponse],
    summary="Métricas por endpoint",
    description="Retorna métricas detalhadas (requests, erros, latência) para todos os endpoints.",
)
@limiter.limit(LIMIT_READ)
async def get_endpoints(
    request: Request,
    response: Response,
    metric: str = Query(
        "requests", description="Métrica para ordenação: requests, latency, errors"
    ),
    limit: int = Query(10, ge=1, le=100, description="Número de endpoints a retornar"),
    period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
    auth: dict = Depends(verify_api_key),
):
    """Retorna métricas detalhadas por endpoint."""
    try:
        service = get_metrics_service()

        if metric not in ["requests", "latency", "errors"]:
            raise HTTPException(
                status_code=400, detail="Métrica inválida. Use: requests, latency, errors"
            )

        # Buscar top endpoints
        endpoints = await service.get_top_endpoints(metric=metric, limit=limit, period=period)

        # Buscar latência para cada endpoint (se não já incluída)
        results = []
        for ep in endpoints:
            endpoint_name = ep["endpoint"]

            # Se métrica é latency, já temos os dados
            if metric == "latency":
                results.append(
                    EndpointMetricsResponse(
                        endpoint=endpoint_name,
                        requests=0,  # Não disponível em latency metric
                        errors=0,
                        error_rate=0.0,
                        latency_p50=ep.get("p50"),
                        latency_p95=ep.get("p95"),
                        latency_p99=ep.get("p99"),
                    )
                )
            else:
                # Buscar latência separadamente
                latency_data = await service.get_latency_percentiles(
                    endpoint=endpoint_name,
                    start_time=datetime.now() - timedelta(hours=24),
                    end_time=datetime.now(),
                )

                results.append(
                    EndpointMetricsResponse(
                        endpoint=endpoint_name,
                        requests=ep.get("requests", 0),
                        errors=ep.get("errors", 0),
                        error_rate=ep.get("error_rate", 0.0),
                        latency_p50=latency_data["p50"] if latency_data["samples"] > 0 else None,
                        latency_p95=latency_data["p95"] if latency_data["samples"] > 0 else None,
                        latency_p99=latency_data["p99"] if latency_data["samples"] > 0 else None,
                    )
                )

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ANALYTICS] Erro ao buscar endpoints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar endpoints: {e!s}")
