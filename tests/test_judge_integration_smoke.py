"""
Teste Smoke: Integracao Judge no Workflow de Diagnostico

Valida que Judge Agent avalia diagnostico e adiciona metadata corretamente.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from unittest.mock import AsyncMock, patch


def test_judge_integration_smoke():
    """Teste smoke: Judge avalia diagnostico e adiciona metadata."""
    from src.agents.diagnostic_agent import CompleteDiagnostic, PerspectiveInsights, Recommendation
    from src.agents.judge_agent import JudgmentResult
    from src.graph.consulting_orchestrator import ConsultingOrchestrator
    from src.graph.states import BSCState
    from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

    # Mock ClientProfile valido
    mock_profile = ClientProfile(
        company=CompanyInfo(name="TechCorp", sector="Tecnologia", size="Medio"),
        context=StrategicContext(
            current_challenges=["Desafio 1", "Desafio 2"],
            strategic_goals=["Objetivo 1", "Objetivo 2"],
            industry_context="Contexto da industria",
            competitive_landscape="Cenario competitivo",
        ),
    )

    # Mock CompleteDiagnostic valido
    mock_diagnostic = CompleteDiagnostic(
        executive_summary="Diagnostico BSC completo para TechCorp",
        financial_perspective=PerspectiveInsights(
            insights=["Insight financeiro 1", "Insight financeiro 2"],
            current_state="Estado atual financeiro",
            gaps_identified=["Gap 1", "Gap 2"],
        ),
        customer_perspective=PerspectiveInsights(
            insights=["Insight cliente 1"],
            current_state="Estado atual cliente",
            gaps_identified=["Gap cliente"],
        ),
        process_perspective=PerspectiveInsights(
            insights=["Insight processo 1"],
            current_state="Estado atual processo",
            gaps_identified=["Gap processo"],
        ),
        learning_perspective=PerspectiveInsights(
            insights=["Insight aprendizado 1"],
            current_state="Estado atual aprendizado",
            gaps_identified=["Gap aprendizado"],
        ),
        recommendations=[
            Recommendation(
                title="Recomendacao 1",
                description="Descricao da recomendacao 1",
                priority="HIGH",
                impact="HIGH",
                perspective="financial",
                timeframe="short_term",
            )
        ],
    )

    # Mock JudgmentResult valido
    mock_judgment = JudgmentResult(
        quality_score=0.85,
        verdict="approved",
        is_grounded=True,
        is_complete=True,
        has_sources=False,  # Diagnostico nao tem fontes (esperado)
        reasoning="Diagnostico de alta qualidade baseado em perfil cliente",
        suggestions=[],
    )

    # Mock State
    mock_state = BSCState(
        client_profile=mock_profile, original_query="Realizar diagnostico BSC", messages=[]
    )

    # Criar orchestrator
    orchestrator = ConsultingOrchestrator()

    # Mock DiagnosticAgent.run_diagnostic
    with patch.object(
        orchestrator.diagnostic_agent,
        "run_diagnostic",
        new_callable=AsyncMock,
        return_value=mock_diagnostic,
    ):
        # Mock JudgeAgent.evaluate
        with patch.object(orchestrator.judge_agent, "evaluate", return_value=mock_judgment):
            # Executar coordinate_discovery (async)
            result = asyncio.run(orchestrator.coordinate_discovery(mock_state))

            # VALIDACOES:

            # 1. Result deve ter diagnostic
            assert "diagnostic" in result
            assert result["diagnostic"] is not None

            # 2. Diagnostic deve ter metadata
            diagnostic_dict = result["diagnostic"]
            assert "metadata" in diagnostic_dict

            # 3. Metadata deve ter judge_evaluation
            assert "judge_evaluation" in diagnostic_dict["metadata"]
            judge_eval = diagnostic_dict["metadata"]["judge_evaluation"]

            # 4. Judge_evaluation deve ter campos obrigatorios
            assert "quality_score" in judge_eval
            assert "verdict" in judge_eval
            assert "is_grounded" in judge_eval
            assert "is_complete" in judge_eval
            assert "has_sources" in judge_eval
            assert "reasoning" in judge_eval
            assert "suggestions" in judge_eval
            assert "evaluated_at" in judge_eval

            # 5. Valores devem ser corretos
            assert judge_eval["quality_score"] == 0.85
            assert judge_eval["verdict"] == "approved"
            assert judge_eval["is_grounded"] is True
            assert judge_eval["is_complete"] is True
            assert judge_eval["has_sources"] is False

            print("[OK] Teste smoke: Judge integration validada!")
            print(f"Score: {judge_eval['quality_score']}")
            print(f"Verdict: {judge_eval['verdict']}")
            print(f"Reasoning: {judge_eval['reasoning']}")


def test_judge_integration_low_score_warning():
    """Teste: Judge com score baixo adiciona warning mas permite prosseguir."""
    from src.agents.diagnostic_agent import CompleteDiagnostic, PerspectiveInsights
    from src.agents.judge_agent import JudgmentResult
    from src.graph.consulting_orchestrator import ConsultingOrchestrator
    from src.graph.states import BSCState
    from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

    # Mock ClientProfile
    mock_profile = ClientProfile(
        company=CompanyInfo(name="TechCorp", sector="Tecnologia", size="Medio"),
        context=StrategicContext(
            current_challenges=["Desafio 1"],
            strategic_goals=["Objetivo 1"],
            industry_context="Contexto",
            competitive_landscape="Cenario",
        ),
    )

    # Mock CompleteDiagnostic
    mock_diagnostic = CompleteDiagnostic(
        executive_summary="Diagnostico basico",
        financial_perspective=PerspectiveInsights(
            insights=["Insight 1"], current_state="Estado", gaps_identified=["Gap"]
        ),
        customer_perspective=PerspectiveInsights(
            insights=["Insight 1"], current_state="Estado", gaps_identified=["Gap"]
        ),
        process_perspective=PerspectiveInsights(
            insights=["Insight 1"], current_state="Estado", gaps_identified=["Gap"]
        ),
        learning_perspective=PerspectiveInsights(
            insights=["Insight 1"], current_state="Estado", gaps_identified=["Gap"]
        ),
        recommendations=[],
    )

    # Mock JudgmentResult com SCORE BAIXO
    mock_judgment = JudgmentResult(
        quality_score=0.55,  # Abaixo de 0.7 (threshold)
        verdict="needs_improvement",
        is_grounded=False,
        is_complete=True,
        has_sources=False,
        reasoning="Diagnostico precisa de mais profundidade",
        suggestions=["Adicionar mais insights por perspectiva"],
    )

    mock_state = BSCState(
        client_profile=mock_profile, original_query="Diagnostico BSC", messages=[]
    )

    orchestrator = ConsultingOrchestrator()

    # Mock agents
    with (
        patch.object(
            orchestrator.diagnostic_agent,
            "run_diagnostic",
            new_callable=AsyncMock,
            return_value=mock_diagnostic,
        ),
        patch.object(orchestrator.judge_agent, "evaluate", return_value=mock_judgment),
    ):
        # Executar
        result = asyncio.run(orchestrator.coordinate_discovery(mock_state))

        # VALIDACOES:

        # 1. Diagnostic deve ser retornado (PERMITIR PROSSEGUIR mesmo com score baixo)
        assert "diagnostic" in result

        # 2. Judge_evaluation deve estar presente
        judge_eval = result["diagnostic"]["metadata"]["judge_evaluation"]

        # 3. Score deve ser 0.55 (baixo)
        assert judge_eval["quality_score"] == 0.55
        assert judge_eval["verdict"] == "needs_improvement"

        # 4. Suggestions deve estar presente (para humano revisar)
        assert len(judge_eval["suggestions"]) > 0

        print("[OK] Teste low score: Warning adicionado mas workflow prosseguiu!")
        print(f"Score: {judge_eval['quality_score']} (abaixo de 0.7)")
        print(f"Suggestions: {judge_eval['suggestions']}")


if __name__ == "__main__":
    print("\n[TEST 1] Judge Integration Smoke Test")
    print("=" * 70)
    test_judge_integration_smoke()

    print("\n[TEST 2] Low Score Warning Test")
    print("=" * 70)
    test_judge_integration_low_score_warning()

    print("\n[OK] Todos os testes smoke passaram!")
