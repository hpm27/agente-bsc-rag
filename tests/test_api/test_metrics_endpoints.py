"""Testes E2E para endpoints de métricas de performance.

Valida API REST de performance monitoring:
- GET /api/v1/metrics - Listar métricas
- GET /api/v1/metrics/stats - Estatísticas agregadas

Fase: 4.8 - Performance Monitoring
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import verify_api_key
from api.routers.metrics import _get_performance_service
from src.memory.schemas import PerformanceMetrics


@pytest.fixture
def client():
    """Cliente de teste da API."""
    # Limpar overrides anteriores
    app.dependency_overrides = {}
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """API key mockada para autenticação."""
    return "test_api_key_metrics_123"


@pytest.fixture
def override_auth(mock_api_key):
    """Override de autenticação para testes."""
    def mock_verify_api_key():
        return {"api_key_id": "test_key", "user_id": "test_user"}
    
    app.dependency_overrides[verify_api_key] = mock_verify_api_key
    
    yield
    
    # Cleanup
    app.dependency_overrides = {}


@pytest.fixture
def sample_metrics():
    """Métricas de exemplo para testes."""
    return [
        PerformanceMetrics(
            endpoint="/api/v1/diagnostics",
            method="POST",
            duration_ms=12345.67,
            status_code=200,
            user_id="user_xyz789",
            tokens_in=5678,
            tokens_out=2345,
            model_name="gpt-5-mini-2025-08-07"
        ),
        PerformanceMetrics(
            endpoint="/api/v1/clients",
            method="GET",
            duration_ms=5678.90,
            status_code=200,
            user_id="user_xyz789"
        )
    ]


def test_list_metrics_returns_200(client, override_auth, mock_api_key, sample_metrics):
    """GET /api/v1/metrics deve retornar 200 com lista de métricas."""
    # Mock performance service
    mock_service = Mock()
    mock_service.get_metrics = Mock(return_value=sample_metrics)
    
    def mock_get_service():
        return mock_service
    
    try:
        app.dependency_overrides[_get_performance_service] = mock_get_service
        
        response = client.get(
            "/api/v1/metrics",
            headers={"X-API-Key": mock_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "total" in data
        assert data["total"] == 2
        assert "filters_applied" in data
    finally:
        # Cleanup
        app.dependency_overrides.pop(_get_performance_service, None)


def test_list_metrics_filters_by_endpoint(client, override_auth, mock_api_key, sample_metrics):
    """GET /api/v1/metrics deve filtrar por endpoint."""
    # Mock performance service
    filtered_metrics = [m for m in sample_metrics if m.endpoint == "/api/v1/diagnostics"]
    mock_service = Mock()
    mock_service.get_metrics = Mock(return_value=filtered_metrics)
    
    def mock_get_service():
        return mock_service
    
    try:
        app.dependency_overrides[_get_performance_service] = mock_get_service
        
        response = client.get(
            "/api/v1/metrics",
            headers={"X-API-Key": mock_api_key},
            params={"endpoint": "/api/v1/diagnostics"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["filters_applied"]["endpoint"] == "/api/v1/diagnostics"
    finally:
        # Cleanup
        app.dependency_overrides.pop(_get_performance_service, None)


def test_list_metrics_validates_limit(client, override_auth, mock_api_key):
    """GET /api/v1/metrics deve validar limit (1-1000)."""
    # Mock service para não tentar criar Mem0 real
    mock_service = Mock()
    
    def mock_get_service():
        return mock_service
    
    try:
        app.dependency_overrides[_get_performance_service] = mock_get_service
        
        response = client.get(
            "/api/v1/metrics",
            headers={"X-API-Key": mock_api_key},
            params={"limit": 0}  # Inválido
        )
        
        assert response.status_code == 422  # Validation error
    finally:
        app.dependency_overrides.pop(_get_performance_service, None)


def test_list_metrics_validates_hours(client, override_auth, mock_api_key):
    """GET /api/v1/metrics deve validar hours (1-168)."""
    # Mock service para não tentar criar Mem0 real
    mock_service = Mock()
    
    def mock_get_service():
        return mock_service
    
    try:
        app.dependency_overrides[_get_performance_service] = mock_get_service
        
        response = client.get(
            "/api/v1/metrics",
            headers={"X-API-Key": mock_api_key},
            params={"hours": 200}  # > 168 (7 dias)
        )
        
        assert response.status_code == 422  # Validation error
    finally:
        app.dependency_overrides.pop(_get_performance_service, None)


def test_get_stats_returns_200(client, override_auth, mock_api_key):
    """GET /api/v1/metrics/stats deve retornar 200 com estatísticas."""
    # Mock performance service
    mock_service = Mock()
    mock_service.aggregate_stats = Mock(return_value={
        "total_requests": 100,
        "error_requests": 5,
        "error_rate": 5.0,
        "throughput_per_min": 4.17,
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
        "endpoint": "ALL"
    })
    
    def mock_get_service():
        return mock_service
    
    try:
        app.dependency_overrides[_get_performance_service] = mock_get_service
        
        response = client.get(
            "/api/v1/metrics/stats",
            headers={"X-API-Key": mock_api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 100
        assert data["error_rate"] == 5.0
        assert "latency" in data
        assert "p50_ms" in data["latency"]
        assert "p95_ms" in data["latency"]
        assert "tokens" in data
        assert data["cost_usd"] == 24.56
    finally:
        # Cleanup
        app.dependency_overrides.pop(_get_performance_service, None)


def test_get_stats_filters_by_endpoint(client, override_auth, mock_api_key):
    """GET /api/v1/metrics/stats deve filtrar por endpoint."""
    # Mock performance service
    mock_service = Mock()
    mock_service.aggregate_stats = Mock(return_value={
        "total_requests": 50,
        "error_requests": 2,
        "error_rate": 4.0,
        "throughput_per_min": 2.08,
        "latency": {"p50_ms": 10000.0, "p95_ms": 20000.0, "mean_ms": 12000.0, "min_ms": 5000.0, "max_ms": 25000.0},
        "tokens": {},
        "cost_usd": 0.0,
        "period_hours": 24,
        "endpoint": "/api/v1/diagnostics"
    })
    
    def mock_get_service():
        return mock_service
    
    try:
        app.dependency_overrides[_get_performance_service] = mock_get_service
        
        response = client.get(
            "/api/v1/metrics/stats",
            headers={"X-API-Key": mock_api_key},
            params={"endpoint": "/api/v1/diagnostics"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/api/v1/diagnostics"
    finally:
        # Cleanup
        app.dependency_overrides.pop(_get_performance_service, None)


def test_list_metrics_requires_authentication(client):
    """GET /api/v1/metrics deve retornar 401 sem autenticação."""
    response = client.get("/api/v1/metrics")
    
    assert response.status_code == 401


def test_get_stats_requires_authentication(client):
    """GET /api/v1/metrics/stats deve retornar 401 sem autenticação."""
    response = client.get("/api/v1/metrics/stats")
    
    assert response.status_code == 401

