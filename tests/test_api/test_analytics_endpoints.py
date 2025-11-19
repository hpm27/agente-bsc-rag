"""Testes E2E para endpoints de analytics.

Valida que os endpoints retornam dados corretos
e seguem contratos de API.

Fase: 4.4 - Advanced Analytics Dashboard
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """TestClient para API."""
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """API key válida para testes."""
    return "bsc_test_valid"


@pytest.fixture
def mock_metrics_service():
    """Mock do MetricsService para testes."""
    service = AsyncMock()
    
    # Mock métodos do service
    service.get_requests_by_endpoint = AsyncMock(return_value=[
        {"timestamp": "2025-11-19:10:00", "endpoint": "/api/v1/clients", "count": 10, "errors": 1, "4xx": 1, "5xx": 0}
    ])
    
    service.get_latency_percentiles = AsyncMock(return_value={
        "p50": 120.0,
        "p95": 250.0,
        "p99": 500.0,
        "mean": 135.0,
        "max": 1200.0,
        "samples": 45
    })
    
    service.get_errors_by_endpoint = AsyncMock(return_value=[
        {"endpoint": "/api/v1/clients", "total_requests": 100, "errors": 5, "error_rate": 0.05}
    ])
    
    service.get_top_consumers = AsyncMock(return_value=[
        {"api_key": "bsc_test_***", "requests": 150, "unique_endpoints": 5, "last_request": "2025-11-19T10:00:00"}
    ])
    
    service.get_top_endpoints = AsyncMock(return_value=[
        {"endpoint": "/api/v1/clients", "requests": 100, "errors": 5, "error_rate": 0.05}
    ])
    
    return service


def test_overview_endpoint_returns_kpis(client, mock_api_key, mock_metrics_service):
    """GET /analytics/overview deve retornar KPIs principais."""
    with patch("api.routers.analytics.get_metrics_service", return_value=mock_metrics_service):
        response = client.get(
            "/api/v1/analytics/overview",
            headers={"X-API-Key": mock_api_key},
            params={"period": "24h"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura da resposta
    assert "total_requests" in data
    assert "error_rate" in data
    assert "avg_latency_ms" in data
    assert "active_api_keys" in data
    assert "period" in data


def test_traffic_endpoint_returns_time_series(client, mock_api_key, mock_metrics_service):
    """GET /analytics/traffic deve retornar dados time-series."""
    with patch("api.routers.analytics.get_metrics_service", return_value=mock_metrics_service):
        response = client.get(
            "/api/v1/analytics/traffic",
            headers={"X-API-Key": mock_api_key},
            params={"period": "24h", "interval": "minute"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura
    assert "data" in data
    assert "period" in data
    assert "interval" in data
    assert isinstance(data["data"], list)
    
    # Verificar estrutura dos pontos de dados
    if data["data"]:
        point = data["data"][0]
        assert "timestamp" in point
        assert "endpoint" in point
        assert "count" in point
        assert "errors" in point


def test_performance_endpoint_returns_latency_metrics(client, mock_api_key, mock_metrics_service):
    """GET /analytics/performance deve retornar métricas de latência."""
    with patch("api.routers.analytics.get_metrics_service", return_value=mock_metrics_service):
        response = client.get(
            "/api/v1/analytics/performance",
            headers={"X-API-Key": mock_api_key},
            params={"endpoint": "/api/v1/clients", "period": "24h"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estrutura
    assert "endpoint" in data
    assert "p50" in data
    assert "p95" in data
    assert "p99" in data
    assert "mean" in data
    assert "max" in data
    assert "samples" in data


def test_errors_endpoint_returns_error_metrics(client, mock_api_key, mock_metrics_service):
    """GET /analytics/errors deve retornar métricas de erros."""
    with patch("api.routers.analytics.get_metrics_service", return_value=mock_metrics_service):
        response = client.get(
            "/api/v1/analytics/errors",
            headers={"X-API-Key": mock_api_key},
            params={"period": "24h"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que é lista
    assert isinstance(data, list)
    
    # Verificar estrutura dos itens
    if data:
        item = data[0]
        assert "endpoint" in item
        assert "total_requests" in item
        assert "errors" in item
        assert "error_rate" in item


def test_consumers_endpoint_returns_top_consumers(client, mock_api_key, mock_metrics_service):
    """GET /analytics/consumers deve retornar top API keys."""
    with patch("api.routers.analytics.get_metrics_service", return_value=mock_metrics_service):
        response = client.get(
            "/api/v1/analytics/consumers",
            headers={"X-API-Key": mock_api_key},
            params={"limit": 10, "period": "24h"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que é lista
    assert isinstance(data, list)
    
    # Verificar estrutura dos itens
    if data:
        item = data[0]
        assert "api_key" in item
        assert "requests" in item
        assert "unique_endpoints" in item
        assert "last_request" in item


def test_endpoints_endpoint_returns_endpoint_metrics(client, mock_api_key, mock_metrics_service):
    """GET /analytics/endpoints deve retornar métricas por endpoint."""
    with patch("api.routers.analytics.get_metrics_service", return_value=mock_metrics_service):
        response = client.get(
            "/api/v1/analytics/endpoints",
            headers={"X-API-Key": mock_api_key},
            params={"metric": "requests", "limit": 10, "period": "24h"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que é lista
    assert isinstance(data, list)
    
    # Verificar estrutura dos itens
    if data:
        item = data[0]
        assert "endpoint" in item
        assert "requests" in item
        assert "errors" in item
        assert "error_rate" in item


def test_analytics_endpoints_require_authentication(client):
    """Endpoints de analytics devem exigir autenticação."""
    endpoints = [
        "/api/v1/analytics/overview",
        "/api/v1/analytics/traffic",
        "/api/v1/analytics/performance",
        "/api/v1/analytics/errors",
        "/api/v1/analytics/consumers",
        "/api/v1/analytics/endpoints"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401  # Unauthorized


def test_performance_endpoint_validates_endpoint_parameter(client, mock_api_key):
    """GET /analytics/performance deve validar parâmetro endpoint obrigatório."""
    response = client.get(
        "/api/v1/analytics/performance",
        headers={"X-API-Key": mock_api_key},
        params={"period": "24h"}
        # endpoint não fornecido
    )
    
    # Deve retornar 422 (Validation Error) ou 400
    assert response.status_code in [400, 422]


def test_traffic_endpoint_validates_interval_parameter(client, mock_api_key):
    """GET /analytics/traffic deve validar parâmetro interval."""
    response = client.get(
        "/api/v1/analytics/traffic",
        headers={"X-API-Key": mock_api_key},
        params={"period": "24h", "interval": "invalid"}
    )
    
    # Deve retornar erro de validação
    assert response.status_code in [400, 422]

