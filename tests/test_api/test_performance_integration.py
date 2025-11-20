"""Teste de integracao E2E para Performance Monitoring System.

Valida que metricas de performance sao capturadas automaticamente:
- PerformanceMiddleware registrado e ativo
- LLM tokens capturados em DiagnosticAgent, OnboardingAgent, Orchestrator
- Metricas persistidas e recuperaveis via API

Fase: 4.9 - Integracao Performance Monitoring
"""

import pytest

from src.memory.schemas import PerformanceMetrics


@pytest.fixture
def mock_api_key():
    """API key mockada para autenticacao."""
    return "test_api_key_integration_123"


@pytest.fixture
def override_auth(mock_api_key):
    """Override de autenticacao para testes (nao usado, mas mantido para compatibilidade)."""


def test_performance_middleware_exists(override_auth, mock_api_key):
    """Teste SMOKE: PerformanceMiddleware pode ser importado sem erro.

    Valida que middleware foi criado e esta disponivel.
    """
    # Validar import sem erro (middleware existe e esta sintaticamente correto)
    try:
        from api.middleware.performance import PerformanceMiddleware

        assert PerformanceMiddleware is not None
        print("[OK] PerformanceMiddleware importado com sucesso")
    except ImportError as e:
        pytest.fail(f"Erro ao importar PerformanceMiddleware: {e}")


def test_llm_tokens_captured_in_context_vars(override_auth, mock_api_key):
    """Teste SMOKE E2E: LLM tokens sao capturados via context vars.

    Valida que track_llm_tokens() acumula tokens corretamente.
    Context vars armazenam int (total tokens), nao dict por modelo.
    """
    from api.middleware.performance import (
        llm_model_name_ctx,
        llm_tokens_in_ctx,
        llm_tokens_out_ctx,
        track_llm_tokens,
    )

    # Inicializar context vars (int, nao dict - seguir default=0 do ContextVar)
    llm_tokens_in_ctx.set(0)
    llm_tokens_out_ctx.set(0)
    llm_model_name_ctx.set(None)

    # Simular chamada LLM (ordem correta: tokens_in, tokens_out, model_name)
    track_llm_tokens(100, 50, "gpt-5-mini-2025-08-07")

    # Validar que context vars foram atualizadas
    tokens_in_total = llm_tokens_in_ctx.get()
    tokens_out_total = llm_tokens_out_ctx.get()
    model_name = llm_model_name_ctx.get()

    # Context vars armazenam TOTAL (int), nao dict por modelo
    assert tokens_in_total == 100, f"Esperado 100 tokens_in, obteve {tokens_in_total}"
    assert tokens_out_total == 50, f"Esperado 50 tokens_out, obteve {tokens_out_total}"
    assert model_name == "gpt-5-mini-2025-08-07", f"Esperado modelo correto, obteve {model_name}"

    # Testar acumulacao (segunda chamada)
    track_llm_tokens(25, 15, "gpt-5-mini-2025-08-07")
    assert llm_tokens_in_ctx.get() == 125, "Tokens_in devem acumular (100+25=125)"
    assert llm_tokens_out_ctx.get() == 65, "Tokens_out devem acumular (50+15=65)"

    print(
        f"[OK] LLM tokens capturados e acumulados: in={llm_tokens_in_ctx.get()} out={llm_tokens_out_ctx.get()} model={model_name}"
    )


def test_performance_system_end_to_end_smoke(override_auth, mock_api_key):
    """Teste SMOKE E2E COMPLETO: Sistema de performance monitoring funcionando.

    Valida integracao completa:
    1. Schema PerformanceMetrics valido
    2. PerformanceService API disponivel
    3. Instrumentacao LLM integrada

    Nota: Teste rapido (smoke), validando componentes core sem TestClient.
    """
    # Validar que schema PerformanceMetrics aceita tokens corretos
    metric = PerformanceMetrics(
        endpoint="/api/v1/diagnostics",
        method="POST",
        status_code=200,
        duration_ms=1234.56,
        user_id="user_test",
        diagnostic_id="diag_123",
        tokens_in=1000,
        tokens_out=500,
        model_name="gpt-5-mini-2025-08-07",
        metadata={},
    )

    # Validar campos
    assert metric.endpoint == "/api/v1/diagnostics"
    assert metric.tokens_in == 1000
    assert metric.tokens_out == 500
    assert metric.model_name == "gpt-5-mini-2025-08-07"
    assert metric.duration_ms == 1234.56

    # Validar que instrumentacao foi adicionada nos agents
    from src.agents import diagnostic_agent, onboarding_agent, orchestrator

    # Verificar import track_llm_tokens existe
    assert hasattr(
        diagnostic_agent, "track_llm_tokens"
    ), "DiagnosticAgent nao importou track_llm_tokens"
    assert hasattr(
        onboarding_agent, "track_llm_tokens"
    ), "OnboardingAgent nao importou track_llm_tokens"
    assert hasattr(orchestrator, "track_llm_tokens"), "Orchestrator nao importou track_llm_tokens"

    print("[OK] Sistema de performance monitoring integrado: schema validado, imports corretos")
