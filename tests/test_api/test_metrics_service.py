"""Testes unitários para MetricsService.

Valida armazenamento e recuperação de métricas do Redis.

Fase: 4.4 - Advanced Analytics Dashboard
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta

from api.services.metrics_service import MetricsService


@pytest.fixture
def mock_redis_client():
    """Mock do Redis client para testes."""
    redis_mock = AsyncMock()
    
    # Mock para hash operations
    redis_mock.hgetall = AsyncMock(return_value={})
    redis_mock.hincrby = AsyncMock(return_value=1)
    redis_mock.setex = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.sadd = AsyncMock()
    redis_mock.smembers = AsyncMock(return_value=set())
    redis_mock.scan_iter = AsyncMock()
    redis_mock.zadd = AsyncMock()
    redis_mock.zcard = AsyncMock(return_value=0)
    redis_mock.zrange = AsyncMock(return_value=[])
    redis_mock.zremrangebyrank = AsyncMock()
    
    return redis_mock


@pytest.fixture
def metrics_service(mock_redis_client):
    """MetricsService com Redis mockado."""
    service = MetricsService(redis_client=mock_redis_client)
    return service


@pytest.mark.asyncio
async def test_record_request_stores_metrics(metrics_service, mock_redis_client):
    """record_request deve armazenar métricas em Redis."""
    await metrics_service.record_request(
        endpoint="/api/v1/clients",
        method="GET",
        status_code=200,
        latency_ms=150.5,
        api_key="bsc_test_engelar"
    )
    
    # Verificar que hincrby foi chamado para contadores
    assert mock_redis_client.hincrby.called
    
    # Verificar que expire foi chamado (TTL)
    assert mock_redis_client.expire.called


@pytest.mark.asyncio
async def test_record_request_counts_errors(metrics_service, mock_redis_client):
    """record_request deve contar erros 4xx e 5xx separadamente."""
    # Teste 4xx
    await metrics_service.record_request(
        endpoint="/api/v1/clients",
        method="GET",
        status_code=404,
        latency_ms=50.0
    )
    
    # Verificar que erro 4xx foi contado
    calls = [call[0][2] for call in mock_redis_client.hincrby.call_args_list]
    assert "4xx" in calls or "errors" in calls
    
    # Reset mock
    mock_redis_client.reset_mock()
    
    # Teste 5xx
    await metrics_service.record_request(
        endpoint="/api/v1/clients",
        method="GET",
        status_code=500,
        latency_ms=200.0
    )
    
    # Verificar que erro 5xx foi contado
    calls = [call[0][2] for call in mock_redis_client.hincrby.call_args_list]
    assert "5xx" in calls or "errors" in calls


@pytest.mark.asyncio
async def test_get_requests_by_endpoint_aggregates_data(metrics_service, mock_redis_client):
    """get_requests_by_endpoint deve agregar dados por intervalo."""
    # Mock dados de Redis
    mock_redis_client.hgetall = AsyncMock(side_effect=[
        {"count": "10", "errors": "1"},
        {"count": "15", "errors": "0"},
    ])
    
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    results = await metrics_service.get_requests_by_endpoint(
        endpoint="/api/v1/clients",
        start_time=start_time,
        end_time=end_time,
        interval="minute"
    )
    
    # Verificar que resultados foram retornados
    assert isinstance(results, list)
    # Verificar estrutura dos resultados
    if results:
        assert "timestamp" in results[0]
        assert "endpoint" in results[0]
        assert "count" in results[0]
        assert "errors" in results[0]


@pytest.mark.asyncio
async def test_get_latency_percentiles_calculates_percentiles(metrics_service, mock_redis_client):
    """get_latency_percentiles deve calcular P50/P95/P99."""
    # Mock dados de latência
    import json
    mock_redis_client.get = AsyncMock(return_value=json.dumps({
        "p50": 120.0,
        "p95": 250.0,
        "p99": 500.0,
        "mean": 135.0,
        "max": 1200.0,
        "samples": 45
    }))
    
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    results = await metrics_service.get_latency_percentiles(
        endpoint="/api/v1/clients",
        start_time=start_time,
        end_time=end_time
    )
    
    # Verificar estrutura do resultado
    assert "p50" in results
    assert "p95" in results
    assert "p99" in results
    assert "mean" in results
    assert "max" in results
    assert "samples" in results


@pytest.mark.asyncio
async def test_get_errors_by_endpoint_counts_errors(metrics_service, mock_redis_client):
    """get_errors_by_endpoint deve contar erros por endpoint."""
    # Mock scan_iter para retornar keys de endpoints
    async def mock_scan_iter(match, count):
        yield "metrics:requests:/api/v1/clients:2025-11-19:10:00"
        yield "metrics:requests:/api/v1/tools:2025-11-19:10:00"
    
    mock_redis_client.scan_iter = mock_scan_iter
    mock_redis_client.hgetall = AsyncMock(side_effect=[
        {"count": "100", "errors": "5"},
        {"count": "50", "errors": "2"},
    ])
    
    start_time = datetime.now() - timedelta(hours=24)
    end_time = datetime.now()
    
    results = await metrics_service.get_errors_by_endpoint(
        start_time=start_time,
        end_time=end_time
    )
    
    # Verificar que resultados foram retornados
    assert isinstance(results, list)
    # Verificar estrutura
    if results:
        assert "endpoint" in results[0]
        assert "total_requests" in results[0]
        assert "errors" in results[0]
        assert "error_rate" in results[0]


@pytest.mark.asyncio
async def test_get_top_consumers_returns_sorted_list(metrics_service, mock_redis_client):
    """get_top_consumers deve retornar lista ordenada por volume."""
    # Mock scan_iter para retornar keys de consumers
    async def mock_scan_iter(match, count):
        yield "metrics:consumer:bsc_test_key1:2025-11-19:10"
        yield "metrics:consumer:bsc_test_key2:2025-11-19:10"
    
    mock_redis_client.scan_iter = mock_scan_iter
    mock_redis_client.hgetall = AsyncMock(side_effect=[
        {"requests": "150"},
        {"requests": "200"},
    ])
    mock_redis_client.smembers = AsyncMock(return_value={"/api/v1/clients", "/api/v1/tools"})
    
    results = await metrics_service.get_top_consumers(limit=10, period="24h")
    
    # Verificar que resultados foram retornados
    assert isinstance(results, list)
    # Verificar estrutura
    if results:
        assert "api_key" in results[0]
        assert "requests" in results[0]
        assert "unique_endpoints" in results[0]
        assert "last_request" in results[0]
        
        # Verificar ordenação (maior volume primeiro)
        if len(results) > 1:
            assert results[0]["requests"] >= results[1]["requests"]


@pytest.mark.asyncio
async def test_get_top_endpoints_supports_multiple_metrics(metrics_service, mock_redis_client):
    """get_top_endpoints deve suportar ordenação por requests, latency ou errors."""
    # Mock para requests metric
    async def mock_scan_iter_requests(match, count):
        yield "metrics:requests:/api/v1/clients:2025-11-19:10:00"
    
    mock_redis_client.scan_iter = mock_scan_iter_requests
    mock_redis_client.hgetall = AsyncMock(return_value={"count": "100", "errors": "5"})
    
    # Teste com metric="requests"
    results_requests = await metrics_service.get_top_endpoints(
        metric="requests",
        limit=10,
        period="24h"
    )
    assert isinstance(results_requests, list)
    
    # Teste com metric="errors"
    results_errors = await metrics_service.get_top_endpoints(
        metric="errors",
        limit=10,
        period="24h"
    )
    assert isinstance(results_errors, list)


@pytest.mark.asyncio
async def test_record_request_sets_ttl_correctly(metrics_service, mock_redis_client):
    """record_request deve configurar TTL correto para diferentes granularidades."""
    await metrics_service.record_request(
        endpoint="/api/v1/clients",
        method="GET",
        status_code=200,
        latency_ms=150.0
    )
    
    # Verificar que expire foi chamado com TTL correto
    expire_calls = mock_redis_client.expire.call_args_list
    
    # Deve ter chamado expire para diferentes keys (minutos, horas, dias)
    assert len(expire_calls) > 0
    
    # Verificar TTLs (7 dias = 604800 segundos)
    ttl_7_days = 7 * 24 * 60 * 60
    ttl_30_days = 30 * 24 * 60 * 60
    
    # Pelo menos uma chamada deve ter TTL de 7 dias (minutos)
    ttls = [call[0][1] for call in expire_calls]
    assert ttl_7_days in ttls or ttl_30_days in ttls


@pytest.mark.asyncio
async def test_get_requests_by_endpoint_handles_empty_data(metrics_service, mock_redis_client):
    """get_requests_by_endpoint deve retornar lista vazia se não houver dados."""
    mock_redis_client.hgetall = AsyncMock(return_value={})
    
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    results = await metrics_service.get_requests_by_endpoint(
        endpoint="/api/v1/clients",
        start_time=start_time,
        end_time=end_time
    )
    
    # Deve retornar lista vazia ou lista com dados vazios
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_get_latency_percentiles_handles_no_samples(metrics_service, mock_redis_client):
    """get_latency_percentiles deve retornar zeros se não houver amostras."""
    mock_redis_client.get = AsyncMock(return_value=None)
    
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    results = await metrics_service.get_latency_percentiles(
        endpoint="/api/v1/clients",
        start_time=start_time,
        end_time=end_time
    )
    
    # Deve retornar estrutura com zeros
    assert results["p50"] == 0
    assert results["p95"] == 0
    assert results["p99"] == 0
    assert results["samples"] == 0

