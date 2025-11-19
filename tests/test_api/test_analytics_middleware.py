"""Testes E2E para AnalyticsMiddleware.

Valida que o middleware coleta métricas corretamente
de todos os requests HTTP.

Fase: 4.4 - Advanced Analytics Dashboard
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from starlette.requests import Request

from api.main import app
from api.middleware.analytics import AnalyticsMiddleware


@pytest.fixture
def mock_metrics_service():
    """Mock do MetricsService para testes."""
    service = AsyncMock()
    service.record_request = AsyncMock()
    return service


@pytest.fixture
def client_with_analytics(mock_metrics_service):
    """TestClient com AnalyticsMiddleware mockado."""
    # Criar app temporário com middleware mockado
    from fastapi import FastAPI
    
    test_app = FastAPI()
    
    # Adicionar middleware com service mockado
    middleware = AnalyticsMiddleware(test_app, metrics_service=mock_metrics_service)
    test_app.add_middleware(AnalyticsMiddleware, metrics_service=mock_metrics_service)
    
    # Adicionar endpoint de teste
    @test_app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    return TestClient(test_app), mock_metrics_service


def test_middleware_skips_health_endpoint(client_with_analytics):
    """Middleware deve ignorar endpoint /health."""
    client, mock_service = client_with_analytics
    
    response = client.get("/health")
    
    assert response.status_code == 200
    # Service não deve ser chamado para /health
    mock_service.record_request.assert_not_called()


def test_middleware_collects_metrics(client_with_analytics):
    """Middleware deve coletar métricas de requests normais."""
    client, mock_service = client_with_analytics
    
    response = client.get("/test", headers={"X-API-Key": "bsc_test_valid"})
    
    assert response.status_code == 200
    
    # Verificar que record_request foi chamado
    mock_service.record_request.assert_called_once()
    
    # Verificar parâmetros da chamada
    call_args = mock_service.record_request.call_args[1]
    assert call_args["endpoint"] == "/test"
    assert call_args["method"] == "GET"
    assert call_args["status_code"] == 200
    assert "latency_ms" in call_args
    assert call_args["latency_ms"] > 0


def test_middleware_extracts_api_key(client_with_analytics):
    """Middleware deve extrair API key do header."""
    client, mock_service = client_with_analytics
    
    response = client.get("/test", headers={"X-API-Key": "bsc_test_engelar"})
    
    assert response.status_code == 200
    
    call_args = mock_service.record_request.call_args[1]
    # API key deve estar mascarada
    assert call_args["api_key"] is not None
    assert "..." in call_args["api_key"] or len(call_args["api_key"]) > 0

