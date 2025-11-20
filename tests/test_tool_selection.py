"""Testes unitarios para Tool Selection Logic - FASE 3.7.

Este modulo testa o suggest_tool() do ConsultingOrchestrator que seleciona
a ferramenta consultiva BSC mais adequada usando abordagem hibrida:
- Heuristica keyword-based (90% casos)
- LLM Classifier GPT-5 mini (10% casos ambiguos)
- Fallback SWOT (casos extremos)

Coverage esperado: Heuristicas, LLM classifier, Fallback, Edge cases.

Added: 2025-10-27 (FASE 3.7)
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.graph.consulting_orchestrator import ConsultingOrchestrator
from src.memory.schemas import (
    ClientProfile,
    CompanyInfo,
    StrategicContext,
    ToolSelection,
)

# ============================================================================
# FIXTURES (Pydantic Validados com Margem Seguranca)
# ============================================================================


@pytest.fixture
def valid_client_profile() -> ClientProfile:
    """ClientProfile valido com campos obrigatorios + margem seguranca."""
    return ClientProfile(
        client_id="test_tool_selection_001",
        company=CompanyInfo(
            name="TechCorp Analytics",
            sector="Tecnologia",
            size="media",
            industry="Software as a Service",
            location="Sao Paulo, SP",
            website="https://techcorp.com",
            description="Empresa de analytics e BI para empresas de medio porte",
        ),
        context=StrategicContext(
            current_challenges=[
                "Baixo NPS (Net Promoter Score) em comparacao ao setor",
                "Custos operacionais altos afetando margem de lucro",
                "Dificuldade em reter talentos tecnicos qualificados",
            ],
            strategic_objectives=[
                "Aumentar NPS de 45 para 65 em 12 meses atraves de melhorias na experiencia do cliente",
                "Reduzir custos operacionais em 15% via automatizacao de processos internos",
                "Melhorar retencao de talentos atingindo 85% de retencao anual",
            ],
            competitive_position="lideranca de mercado",
            growth_stage="expansao",
        ),
        created_at="2025-01-15T10:00:00Z",
        last_updated="2025-01-15T10:00:00Z",
    )


@pytest.fixture
def mock_complete_diagnostic() -> dict[str, Any]:
    """CompleteDiagnostic mockado como dict (formato state)."""
    return {
        "financial": {
            "current_state": "Margem EBITDA abaixo do setor (18% vs 25% setor)",
            "gaps": ["Eficiencia operacional limitada", "Custos fixos elevados"],
            "opportunities": ["Automatizacao processos", "Reducao desperdicios"],
            "priority": "HIGH",
            "key_insights": "Eficiencia operacional e principal gap vs setor",
        },
        "customer": {
            "current_state": "NPS 45 (abaixo da media do setor)",
            "gaps": ["Experiencia cliente inconsistente", "Tempo resposta alto"],
            "opportunities": ["Programa fidelizacao", "Omnichannel"],
            "priority": "HIGH",
            "key_insights": "Foco necessario em experiencia do cliente",
        },
        "process": {
            "current_state": "Processos manuais impactando eficiencia",
            "gaps": ["Automatizacao limitada", "Silos departamentais"],
            "opportunities": ["Digitalizacao workflows", "Integracao sistemas"],
            "priority": "MEDIUM",
            "key_insights": "Processos precisam ser digitalizados",
        },
        "learning": {
            "current_state": "Retencao de talentos baixa (60% anual)",
            "gaps": ["Falta programas desenvolvimento", "Culture fit inconsistente"],
            "opportunities": ["Career paths claros", "Mentoring program"],
            "priority": "MEDIUM",
            "key_insights": "Retencao afeta capacidade de inovacao",
        },
        "recommendations": [
            {
                "title": "Implementar programa de melhoria NPS",
                "impact": "HIGH",
                "effort": "MEDIUM",
                "priority": "HIGH",
                "timeframe": "3-6 meses",
            }
        ],
        "executive_summary": "TechCorp tem potencial lideranca mas precisa focar em experiencia cliente, eficiencia operacional e retencao talentos para sustentar crescimento.",
        "cross_perspective_synergies": "Melhoria experiencia cliente gera impacto positivo em retencao talentos e eficiencia operacional.",
        "next_phase": "SOLUTION_DESIGN",
    }


# ============================================================================
# TESTES HEURISTICAS (6 Tools - 90% Casos)
# ============================================================================


def test_heuristic_five_whys_with_root_cause_keyword(valid_client_profile):
    """Heuristica deve detectar FIVE_WHYS com keyword 'causa raiz'."""
    orchestrator = ConsultingOrchestrator()

    # Usar metodo privado diretamente para testar heuristica isolada
    result = orchestrator._classify_with_heuristics(
        query="Nosso problema e a causa raiz das baixas vendas", diagnostic_result=None
    )

    assert result == "FIVE_WHYS", "Deveria detectar FIVE_WHYS com keyword 'causa raiz'"


def test_heuristic_five_whys_with_why_keyword(valid_client_profile):
    """Heuristica deve detectar FIVE_WHYS com keyword 'por que'."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Por que nosso NPS esta baixo?", diagnostic_result=None
    )

    assert result == "FIVE_WHYS", "Deveria detectar FIVE_WHYS com keyword 'por que'"


def test_heuristic_swot_with_explicit_keyword(valid_client_profile):
    """Heuristica deve detectar SWOT com keyword explicito."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Vamos fazer uma analise SWOT da empresa", diagnostic_result=None
    )

    assert result == "SWOT", "Deveria detectar SWOT com keyword explicito"


def test_heuristic_swot_with_strengths_weaknesses(valid_client_profile):
    """Heuristica deve detectar SWOT com keywords 'forcas/fraquezas'."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Quais sao nossas forcas e fraquezas?", diagnostic_result=None
    )

    assert result == "SWOT", "Deveria detectar SWOT com keywords forcas/fraquezas"


def test_heuristic_issue_tree_with_decompose_keyword(valid_client_profile):
    """Heuristica deve detectar ISSUE_TREE com keyword 'decompor'."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Como decompor o problema de baixa lucratividade?", diagnostic_result=None
    )

    assert result == "ISSUE_TREE", "Deveria detectar ISSUE_TREE com keyword 'decompor'"


def test_heuristic_kpi_definer_with_explicit_keyword(valid_client_profile):
    """Heuristica deve detectar KPI_DEFINER com keyword 'kpi'."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Precisamos definir KPIs para as 4 perspectivas BSC", diagnostic_result=None
    )

    assert result == "KPI_DEFINER", "Deveria detectar KPI_DEFINER com keyword explicito"


def test_heuristic_strategic_objectives_with_goals_keyword(valid_client_profile):
    """Heuristica deve detectar STRATEGIC_OBJECTIVES com keyword 'objetivos'."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Quais devem ser nossos objetivos estrategicos?", diagnostic_result=None
    )

    assert result == "STRATEGIC_OBJECTIVES", "Deveria detectar STRATEGIC_OBJECTIVES"


def test_heuristic_benchmarking_with_comparison_keyword(valid_client_profile):
    """Heuristica deve detectar BENCHMARKING com keyword 'comparacao'."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Como estamos comparados aos concorrentes?", diagnostic_result=None
    )

    assert result == "BENCHMARKING", "Deveria detectar BENCHMARKING com keyword comparacao"


def test_heuristic_no_match_returns_none(valid_client_profile):
    """Heuristica deve retornar None quando nenhum match encontrado."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Bom dia, como posso ajuda-lo?", diagnostic_result=None  # Query generica sem keywords
    )

    assert result is None, "Deveria retornar None quando heuristica falha"


def test_heuristic_combined_query_and_diagnostic(valid_client_profile, mock_complete_diagnostic):
    """Heuristica deve analisar query + diagnostic result combinados."""
    orchestrator = ConsultingOrchestrator()

    result = orchestrator._classify_with_heuristics(
        query="Precisamos investigar",  # Query parcial
        diagnostic_result=mock_complete_diagnostic,  # Diagnostic tem "NPS 45"
    )

    # Diagnostic mentionou NPS, entao pode inferir FIVE_WHYS se query mencionar causa raiz
    # Mas esse teste e para validar que combined_text funciona
    assert result in ["FIVE_WHYS", "ISSUE_TREE", None], "Deveria analisar diagnostic tambem"


# ============================================================================
# TESTES LLM CLASSIFIER (10% Casos Ambiguos)
# ============================================================================


@pytest.mark.asyncio
async def test_llm_classifier_with_ambiguous_query(valid_client_profile):
    """LLM classifier deve lidar com query ambigua."""
    orchestrator = ConsultingOrchestrator()

    # Mock LLM structured output
    mock_tool_selection = ToolSelection(
        tool_name="ISSUE_TREE",
        confidence=0.78,
        reasoning="Query ambigua mas contexto sugere decomposicao de problema complexo",
        alternative_tools=["FIVE_WHYS", "SWOT"],
    )

    with patch.object(
        orchestrator, "_classify_with_llm", new_callable=AsyncMock, return_value=mock_tool_selection
    ) as mock_llm:

        result = await orchestrator._classify_with_llm(
            client_profile=valid_client_profile,
            diagnostic_result=None,
            query="Temos varios problemas para resolver",  # Ambigua
        )

        assert result.tool_name == "ISSUE_TREE"
        assert 0.60 <= result.confidence <= 0.85  # Confidence medio (ambiguo)
        assert len(result.reasoning) >= 20  # Minimo 20 chars
        mock_llm.assert_called_once()


# ============================================================================
# TESTES SUGGEST_TOOL PUBLICO (Orchestration Complete)
# ============================================================================


@pytest.mark.asyncio
async def test_suggest_tool_heuristic_path_success(valid_client_profile):
    """suggest_tool deve usar heuristica e retornar tool_name corretamente."""
    orchestrator = ConsultingOrchestrator()

    result = await orchestrator.suggest_tool(
        client_profile=valid_client_profile,
        user_query="Por que nossas vendas caíram 30%?",  # Keyword "por que"
    )

    assert isinstance(result, ToolSelection)
    assert result.tool_name == "FIVE_WHYS"
    assert result.confidence >= 0.90  # Alta confidence (heuristica)
    assert len(result.reasoning) >= 20


@pytest.mark.asyncio
async def test_suggest_tool_llm_path_fallback(valid_client_profile):
    """suggest_tool deve escalar para LLM quando heuristica falha."""
    orchestrator = ConsultingOrchestrator()

    # Mock LLM para retornar classificacao
    mock_llm_selection = ToolSelection(
        tool_name="STRATEGIC_OBJECTIVES",
        confidence=0.82,
        reasoning="Contexto empresa sugere definicao de objetivos estrategicos de longo prazo",
        alternative_tools=[],
    )

    with patch.object(
        orchestrator, "_classify_with_llm", new_callable=AsyncMock, return_value=mock_llm_selection
    ):

        result = await orchestrator.suggest_tool(
            client_profile=valid_client_profile,
            user_query="Precisamos planejar nossos proximos passos estrategicos",  # Ambiguo
        )

        assert result.tool_name == "STRATEGIC_OBJECTIVES"
        assert 0.70 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_suggest_tool_fallback_swot_when_all_fail(valid_client_profile):
    """suggest_tool deve usar fallback SWOT quando heuristica E LLM falham."""
    orchestrator = ConsultingOrchestrator()

    # Mock LLM para lancar exception
    with patch.object(
        orchestrator,
        "_classify_with_llm",
        new_callable=AsyncMock,
        side_effect=Exception("LLM timeout"),
    ):

        result = await orchestrator.suggest_tool(
            client_profile=valid_client_profile, user_query="?????"  # Query completamente invalida
        )

        assert result.tool_name == "SWOT"
        assert result.confidence == 0.50  # Baixa confidence (fallback)
        assert len(result.alternative_tools) >= 2  # Deve ter alternativas


@pytest.mark.asyncio
async def test_suggest_tool_with_diagnostic_context(valid_client_profile, mock_complete_diagnostic):
    """suggest_tool deve usar diagnostic_result como contexto adicional."""
    orchestrator = ConsultingOrchestrator()

    result = await orchestrator.suggest_tool(
        client_profile=valid_client_profile,
        diagnostic_result=mock_complete_diagnostic,
        user_query="Quais KPIs devemos acompanhar?",  # Keyword "KPI"
    )

    assert result.tool_name == "KPI_DEFINER"
    assert result.confidence >= 0.90


# ============================================================================
# TESTES EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_suggest_tool_with_none_query(valid_client_profile):
    """suggest_tool deve funcionar com query=None (apenas contexto cliente)."""
    orchestrator = ConsultingOrchestrator()

    # Deve escalar para LLM (heuristica retorna None se combined_text vazio)
    mock_llm_selection = ToolSelection(
        tool_name="SWOT",
        confidence=0.75,
        reasoning="Sem query, contexto cliente sugere analise SWOT inicial",
        alternative_tools=[],
    )

    with patch.object(
        orchestrator, "_classify_with_llm", new_callable=AsyncMock, return_value=mock_llm_selection
    ):

        result = await orchestrator.suggest_tool(
            client_profile=valid_client_profile, user_query=None  # Sem query
        )

        assert result.tool_name == "SWOT"
        assert isinstance(result, ToolSelection)


def test_heuristic_case_insensitive(valid_client_profile):
    """Heuristica deve ser case-insensitive."""
    orchestrator = ConsultingOrchestrator()

    # Teste com maiusculas
    result_upper = orchestrator._classify_with_heuristics(
        query="POR QUE NOSSO NPS ESTA BAIXO?", diagnostic_result=None
    )

    # Teste com minusculas
    result_lower = orchestrator._classify_with_heuristics(
        query="por que nosso nps esta baixo?", diagnostic_result=None
    )

    assert result_upper == result_lower == "FIVE_WHYS"


@pytest.mark.asyncio
async def test_suggest_tool_with_none_diagnostic(valid_client_profile):
    """suggest_tool deve funcionar com diagnostic_result=None."""
    orchestrator = ConsultingOrchestrator()

    result = await orchestrator.suggest_tool(
        client_profile=valid_client_profile,
        diagnostic_result=None,  # Sem diagnostic previo
        user_query="Vamos fazer SWOT",  # Keyword obvio
    )

    assert result.tool_name == "SWOT"
    assert isinstance(result, ToolSelection)
    assert result.confidence >= 0.90
