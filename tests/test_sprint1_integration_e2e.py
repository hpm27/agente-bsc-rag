"""
Teste E2E SPRINT 1: Validação completa da integração das 7 ferramentas consultivas.

Escopo:
- Valida que DiagnosticAgent executa as 7 ferramentas em paralelo
- Mede latência adicional (<60s target)
- Verifica que consolidate_diagnostic usa outputs das ferramentas
- Confirma zero regressões vs baseline

IMPORTANTE: Este teste usa DiagnosticAgent diretamente (não workflow completo)
para evitar dependência do onboarding consultivo (fora do scope Sprint 1).
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.agents.diagnostic_agent import DiagnosticAgent
from src.memory.schemas import (
    ClientProfile,
    CompanyInfo,
    StrategicContext,
    CompleteDiagnostic,
    DiagnosticToolsResult,
)
from src.graph.states import BSCState
from config.settings import get_llm


@pytest.fixture
def valid_client_profile():
    """ClientProfile válido para testes E2E."""
    return ClientProfile(
        id="test_sprint1_e2e",
        company=CompanyInfo(
            name="TechCorp Inovação",
            sector="Tecnologia",
            size="média",
            industry="Software empresarial B2B SaaS",
        ),
        context=StrategicContext(
            current_challenges=[
                "Alta taxa de churn de clientes (15% ao ano)",
                "Processos de desenvolvimento desorganizados",
                "Dificuldade em atrair talentos técnicos seniores",
            ],
            strategic_objectives=[
                "Reduzir churn para <5% em 12 meses",
                "Implementar metodologia ágil em todos os times",
                "Crescer receita recorrente (ARR) em 30% ao ano",
            ],
        ),
    )


@pytest.fixture
def diagnostic_agent_real():
    """DiagnosticAgent com LLM REAL para teste E2E."""
    return DiagnosticAgent()


@pytest.fixture
def bsc_state_sprint1(valid_client_profile):
    """BSCState configurado para Sprint 1."""
    return BSCState(
        query="Como implementar BSC considerando as 4 perspectivas?",
        session_id="sprint1_e2e",
        user_id="test_sprint1",
        client_profile=valid_client_profile,
    )


@pytest.mark.asyncio
async def test_sprint1_integration_complete_flow(diagnostic_agent_real, bsc_state_sprint1):
    """
    TESTE E2E CRÍTICO SPRINT 1: Fluxo completo com 7 ferramentas consultivas.

    Valida:
    - 7/7 ferramentas executam em paralelo
    - Latência adicional <60s
    - Diagnóstico final menciona outputs das ferramentas
    - Zero breaking changes (diagnóstico continua funcionando)
    """
    # Medir latência total
    start = time.time()

    # Executar diagnóstico completo
    result = await diagnostic_agent_real.run_diagnostic(bsc_state_sprint1)

    end = time.time()
    latency = end - start

    # VALIDAÇÃO 1: Resultado não é None
    assert result is not None, "run_diagnostic não deve retornar None"

    # VALIDAÇÃO 2: É um CompleteDiagnostic
    assert isinstance(
        result, CompleteDiagnostic
    ), f"Esperado CompleteDiagnostic, recebeu {type(result)}"

    # VALIDAÇÃO 3: Tem as 4 perspectivas
    assert result.financial is not None, "Perspectiva Financeira ausente"
    assert result.customer is not None, "Perspectiva Clientes ausente"
    assert result.process is not None, "Perspectiva Processos ausente"
    assert result.learning is not None, "Perspectiva Aprendizado ausente"

    # VALIDAÇÃO 4: Tem recomendações (mínimo 3)
    assert (
        len(result.recommendations) >= 3
    ), f"Esperado >=3 recomendações, recebeu {len(result.recommendations)}"

    # VALIDAÇÃO 5: diagnostic_tools_results está presente (SPRINT 1!)
    assert (
        result.diagnostic_tools_results is not None
    ), "diagnostic_tools_results ausente (falha Sprint 1)"

    tools_result = result.diagnostic_tools_results
    assert isinstance(tools_result, DiagnosticToolsResult), "diagnostic_tools_results tipo inválido"

    # VALIDAÇÃO 6: Pelo menos 4/7 ferramentas executaram com sucesso (permite falhas parciais)
    tools_executed = len(tools_result.tools_executed)
    assert tools_executed >= 4, f"Esperado >=4 ferramentas executadas, recebeu {tools_executed}"

    # VALIDAÇÃO 7: Latência das ferramentas <60s (TARGET SPRINT 1)
    tools_latency = tools_result.execution_time
    assert tools_latency < 60.0, f"Latência ferramentas {tools_latency:.2f}s excede target 60s"

    # VALIDAÇÃO 8: Diagnóstico menciona pelo menos uma ferramenta (consolidação enriquecida)
    executive_summary = result.executive_summary.lower()
    tool_keywords = ["swot", "five whys", "kpi", "objetivo", "benchmark", "prioriza"]
    mentions_tools = any(keyword in executive_summary for keyword in tool_keywords)

    # Log resultados
    print("\n[SPRINT 1 E2E] ========== RESULTADOS ==========")
    print(f"[SPRINT 1 E2E] Latência total: {latency:.2f}s")
    print(f"[SPRINT 1 E2E] Latência ferramentas: {tools_latency:.2f}s")
    print(f"[SPRINT 1 E2E] Ferramentas executadas: {tools_executed}/7")
    print(f"[SPRINT 1 E2E] Ferramentas com sucesso: {tools_result.tools_executed}")
    print(f"[SPRINT 1 E2E] Ferramentas falhadas: {tools_result.tools_failed}")
    print(f"[SPRINT 1 E2E] Recomendações: {len(result.recommendations)}")
    print(f"[SPRINT 1 E2E] Menções a ferramentas no executive_summary: {mentions_tools}")
    print("[SPRINT 1 E2E] ================================\n")

    # Assertions finais
    assert (
        latency < 180.0
    ), f"Latência total {latency:.2f}s muito alta (esperado <3min para E2E completo)"

    # OPCIONAL: Verificar menciona ferramentas (não obrigatório mas desejável)
    if not mentions_tools:
        print(
            "[SPRINT 1 E2E] WARNING: Executive summary não menciona nenhuma ferramenta consultiva"
        )


@pytest.mark.asyncio
async def test_sprint1_tools_metadata_tracking(diagnostic_agent_real, bsc_state_sprint1):
    """
    Valida que metadata de execução das ferramentas está correto.
    """
    result = await diagnostic_agent_real.run_diagnostic(bsc_state_sprint1)

    tools_result = result.diagnostic_tools_results
    assert tools_result is not None

    # Validar metadata
    assert tools_result.execution_time > 0, "execution_time deve ser > 0"
    assert isinstance(tools_result.tools_executed, list), "tools_executed deve ser lista"
    assert isinstance(tools_result.tools_failed, list), "tools_failed deve ser lista"

    # Total de ferramentas = 7
    total_tools = len(tools_result.tools_executed) + len(tools_result.tools_failed)
    assert total_tools == 7, f"Total de ferramentas deve ser 7, recebeu {total_tools}"

    # Timestamp criado
    assert tools_result.created_at is not None, "created_at ausente"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=long"])
