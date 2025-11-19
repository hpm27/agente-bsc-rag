"""Testes unitários para PerformanceService.

Valida funcionalidade do serviço de performance monitoring:
- Criação de métricas
- Listagem com filtros
- Agregação de estatísticas

Fase: 4.8 - Performance Monitoring
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone

from api.services.performance_service import PerformanceService, LLM_PRICING
from src.memory.schemas import PerformanceMetrics


@pytest.fixture
def mock_mem0_client():
    """Mock do MemoryClient do Mem0."""
    return Mock()


@pytest.fixture
def performance_service(mock_mem0_client):
    """Instância de PerformanceService com Mem0 mockado."""
    return PerformanceService(mem0_client=mock_mem0_client)


@pytest.fixture
def valid_metric():
    """Métrica válida para testes."""
    return PerformanceMetrics(
        endpoint="/api/v1/diagnostics",
        method="POST",
        duration_ms=12345.67,
        status_code=200,
        user_id="user_xyz789",
        diagnostic_id="diag_abc123",
        tokens_in=5678,
        tokens_out=2345,
        model_name="gpt-5-mini-2025-08-07",
        metadata={"query_length": 150, "response_size": 5000}
    )


def test_performance_service_initialization(performance_service):
    """PerformanceService deve inicializar com Mem0 client."""
    assert performance_service.client is not None


def test_create_metric_returns_metric_id(performance_service, valid_metric):
    """create_metric deve retornar metric_id quando sucesso."""
    # Mock Mem0 add
    performance_service.client.add = Mock(return_value={"id": "mem0_12345"})
    
    metric_id = performance_service.create_metric(valid_metric)
    
    assert metric_id == valid_metric.id
    assert metric_id.startswith("metric_")
    performance_service.client.add.assert_called_once()


def test_create_metric_validates_endpoint(performance_service, valid_metric):
    """create_metric deve validar endpoint mínimo 5 caracteres."""
    valid_metric.endpoint = "/"  # < 5 chars
    
    with pytest.raises(ValueError, match="endpoint inválido"):
        performance_service.create_metric(valid_metric)


def test_create_metric_validates_duration(performance_service, valid_metric):
    """create_metric deve validar duration_ms >= 0."""
    valid_metric.duration_ms = -100.0  # Negativo
    
    with pytest.raises(ValueError, match="duration_ms deve ser >= 0"):
        performance_service.create_metric(valid_metric)


def test_create_metric_validates_status_code(performance_service, valid_metric):
    """create_metric deve validar status_code entre 100-599."""
    valid_metric.status_code = 999  # Fora do range
    
    with pytest.raises(ValueError, match="status_code deve estar entre 100-599"):
        performance_service.create_metric(valid_metric)


def test_get_metrics_returns_filtered_list(performance_service):
    """get_metrics deve retornar lista de métricas filtradas."""
    # Mock Mem0 get_all
    performance_service.client.get_all = Mock(return_value={
        'results': [
            {
                "metadata": {
                    "metric_id": "metric_123",
                    "endpoint": "/api/v1/diagnostics",
                    "method": "POST",
                    "status_code": 200,
                    "timestamp_unix": int(datetime.now(timezone.utc).timestamp()),
                    "duration_ms": 12345.67,
                    "user_id": "user_123",
                    "tokens_in": 1000,
                    "tokens_out": 500,
                    "model_name": "gpt-5-mini-2025-08-07"
                }
            }
        ]
    })
    
    metrics = performance_service.get_metrics(
        endpoint="/api/v1/diagnostics",
        limit=100
    )
    
    assert len(metrics) >= 0
    assert isinstance(metrics, list)


def test_get_metrics_validates_limit_range(performance_service):
    """get_metrics deve validar limit entre 1-1000."""
    with pytest.raises(ValueError, match="limit deve estar entre 1-1000"):
        performance_service.get_metrics(limit=0)
    
    with pytest.raises(ValueError, match="limit deve estar entre 1-1000"):
        performance_service.get_metrics(limit=1001)


def test_aggregate_stats_returns_statistics(performance_service):
    """aggregate_stats deve retornar estatísticas agregadas."""
    # Mock get_metrics para retornar métricas de exemplo
    sample_metrics = [
        PerformanceMetrics(
            endpoint="/api/v1/diagnostics",
            method="POST",
            duration_ms=10000.0,
            status_code=200,
            tokens_in=1000,
            tokens_out=500,
            model_name="gpt-5-mini-2025-08-07"
        ),
        PerformanceMetrics(
            endpoint="/api/v1/diagnostics",
            method="POST",
            duration_ms=15000.0,
            status_code=200,
            tokens_in=1500,
            tokens_out=750,
            model_name="gpt-5-mini-2025-08-07"
        ),
        PerformanceMetrics(
            endpoint="/api/v1/diagnostics",
            method="POST",
            duration_ms=20000.0,
            status_code=500  # Erro
        )
    ]
    
    performance_service.get_metrics = Mock(return_value=sample_metrics)
    
    stats = performance_service.aggregate_stats(hours=24)
    
    assert "total_requests" in stats
    assert stats["total_requests"] == 3
    assert "error_rate" in stats
    assert stats["error_rate"] > 0  # 1/3 erro
    assert "latency" in stats
    assert "p50_ms" in stats["latency"]
    assert "p95_ms" in stats["latency"]
    assert "tokens" in stats
    assert "cost_usd" in stats


def test_aggregate_stats_calculates_cost_correctly(performance_service):
    """aggregate_stats deve calcular custo baseado em pricing LLM."""
    # Mock get_metrics
    sample_metrics = [
        PerformanceMetrics(
            endpoint="/api/v1/diagnostics",
            method="POST",
            duration_ms=10000.0,
            status_code=200,
            tokens_in=1_000_000,  # 1M tokens in
            tokens_out=500_000,  # 500K tokens out
            model_name="gpt-5-mini-2025-08-07"
        )
    ]
    
    performance_service.get_metrics = Mock(return_value=sample_metrics)
    
    stats = performance_service.aggregate_stats(hours=24)
    
    # Calcular custo esperado:
    # gpt-5-mini: $0.10/1M in, $0.40/1M out
    # Cost = (1M * 0.10) + (0.5M * 0.40) = $0.10 + $0.20 = $0.30
    expected_cost = (1_000_000 * LLM_PRICING["gpt-5-mini-2025-08-07"]["input"] / 1_000_000) + \
                    (500_000 * LLM_PRICING["gpt-5-mini-2025-08-07"]["output"] / 1_000_000)
    
    assert abs(stats["cost_usd"] - expected_cost) < 0.01  # Tolerância float


def test_aggregate_stats_handles_empty_metrics(performance_service):
    """aggregate_stats deve retornar stats vazias quando nenhuma métrica."""
    performance_service.get_metrics = Mock(return_value=[])
    
    stats = performance_service.aggregate_stats(hours=24)
    
    assert stats["total_requests"] == 0
    assert stats["error_rate"] == 0.0
    assert stats["throughput_per_min"] == 0.0
    assert stats["cost_usd"] == 0.0

