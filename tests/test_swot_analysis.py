"""Testes unitários para SWOT Analysis Tool.

Valida:
- Criação e inicialização de SWOTAnalysisTool
- Geração de análise SWOT com/sem RAG
- Refinamento com resultados diagnósticos
- Validações de qualidade e completude
- Tratamento de erros (LLM failures, validação)

Created: 2025-10-19 (FASE 3.1)
Coverage target: 90%+
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.tools.swot_analysis import SWOTAnalysisTool
from src.memory.schemas import (
    SWOTAnalysis,
    CompanyInfo,
    StrategicContext,
)

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLLM


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock LLM que retorna SWOT estruturado válido."""
    llm = MagicMock(spec=["invoke", "with_structured_output"])
    
    # Simula structured output que retorna SWOTAnalysis direto
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = SWOTAnalysis(
        strengths=[
            "Equipe técnica altamente qualificada",
            "Marca consolidada no mercado",
            "Portfólio diversificado de produtos",
            "Cultura organizacional forte"
        ],
        weaknesses=[
            "Processos operacionais manuais",
            "Falta de ferramentas de BI",
            "Dependência de poucos clientes",
            "Turnover elevado em áreas operacionais"
        ],
        opportunities=[
            "Expansão para mercado digital",
            "Demanda por transformação digital",
            "Parcerias estratégicas com players",
            "Adoção de IA como diferencial"
        ],
        threats=[
            "Concorrência internacional",
            "Obsolescência tecnológica",
            "Instabilidade econômica brasileira",
            "Regulamentações LGPD aumentam compliance"
        ]
    )
    
    llm.with_structured_output.return_value = mock_structured_llm
    return llm


@pytest.fixture
def mock_financial_agent() -> MagicMock:
    """Mock Financial Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "Contexto financeiro BSC: Foco em indicadores de rentabilidade, ROI, crescimento de receita e lucratividade sustentável."
    }
    return agent


@pytest.fixture
def mock_customer_agent() -> MagicMock:
    """Mock Customer Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "Contexto clientes BSC: Satisfação, retenção, net promoter score (NPS) e valor do cliente ao longo do tempo."
    }
    return agent


@pytest.fixture
def mock_process_agent() -> MagicMock:
    """Mock Process Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "Contexto processos BSC: Eficiência operacional, qualidade, lead time e produtividade."
    }
    return agent


@pytest.fixture
def mock_learning_agent() -> MagicMock:
    """Mock Learning Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "Contexto aprendizado BSC: Capacitação de equipes, inovação, clima organizacional e cultura de aprendizado contínuo."
    }
    return agent


@pytest.fixture
def company_info() -> CompanyInfo:
    """Fixture de empresa válida para testes."""
    return CompanyInfo(
        name="TechInova Solutions",
        sector="Tecnologia",
        size="média",
        industry="Desenvolvimento de Software B2B"
    )


@pytest.fixture
def strategic_context() -> StrategicContext:
    """Fixture de contexto estratégico válido."""
    return StrategicContext(
        mission="Democratizar tecnologia de gestão para PMEs brasileiras",
        vision="Ser referência em software de gestão empresarial no Brasil até 2027",
        core_values=["Inovação contínua", "Foco no cliente", "Excelência técnica"],
        strategic_objectives=[
            "Aumentar receita recorrente (ARR) em 40% em 2025",
            "Reduzir churn para <5% ao ano",
            "Lançar 3 novos produtos no portfólio"
        ],
        current_challenges=[
            "Competir com grandes players internacionais",
            "Escalar operações mantendo qualidade",
            "Reduzir churn de clientes"
        ]
    )


# ============================================================================
# TESTES: CRIAÇÃO E INICIALIZAÇÃO
# ============================================================================


def test_swot_tool_creation(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock
):
    """Testa criação básica da SWOTAnalysisTool."""
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    assert tool is not None
    assert tool.llm == mock_llm
    assert tool.financial_agent == mock_financial_agent
    assert tool.customer_agent == mock_customer_agent
    assert tool.process_agent == mock_process_agent
    assert tool.learning_agent == mock_learning_agent


# ============================================================================
# TESTES: GERAÇÃO SWOT BÁSICO (SEM RAG)
# ============================================================================


def test_facilitate_swot_without_rag(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock,
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    """Testa facilitação SWOT básica sem RAG (apenas LLM)."""
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    result = tool.facilitate_swot(
        company_info=company_info,
        strategic_context=strategic_context,
        use_rag=False
    )
    
    # Valida tipo de retorno
    assert isinstance(result, SWOTAnalysis)
    
    # Valida completude (mock retorna 4 itens por quadrante)
    assert result.is_complete()
    assert len(result.strengths) >= 2
    assert len(result.weaknesses) >= 2
    assert len(result.opportunities) >= 2
    assert len(result.threats) >= 2


def test_facilitate_swot_quality_score(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock,
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    """Testa quality_score do SWOT facilitado."""
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    result = tool.facilitate_swot(
        company_info=company_info,
        strategic_context=strategic_context,
        use_rag=False
    )
    
    # Quality score deve ser alto (mock retorna 4 itens/quadrante)
    score = result.quality_score()
    assert 0.0 <= score <= 1.0
    assert score >= 0.8  # Esperado: 1.0 (4 itens cada)


def test_facilitate_swot_summary(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock,
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    """Testa método summary() do SWOT facilitado."""
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    result = tool.facilitate_swot(
        company_info=company_info,
        strategic_context=strategic_context,
        use_rag=False
    )
    
    summary = result.summary()
    
    # Valida formato do summary (aceita formato "Strengths (Forças):")
    assert "Strengths" in summary and "Forças" in summary
    assert "Weaknesses" in summary and "Fraquezas" in summary
    assert "Opportunities" in summary and "Oportunidades" in summary
    assert "Threats" in summary and "Ameaças" in summary


# ============================================================================
# TESTES: GERAÇÃO SWOT COM RAG
# ============================================================================


def test_facilitate_swot_with_rag(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock,
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    """Testa facilitação SWOT com RAG (specialist agents)."""
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    result = tool.facilitate_swot(
        company_info=company_info,
        strategic_context=strategic_context,
        use_rag=True
    )
    
    # Valida que specialist agents foram chamados
    assert mock_financial_agent.invoke.called
    assert mock_customer_agent.invoke.called
    assert mock_process_agent.invoke.called
    assert mock_learning_agent.invoke.called
    
    # Valida resultado completo
    assert isinstance(result, SWOTAnalysis)
    assert result.is_complete()


# ============================================================================
# TESTES: TRATAMENTO DE ERROS
# ============================================================================


def test_facilitate_swot_llm_failure_raises_error(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock,
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    """Testa que falha do LLM lança ValueError com mensagem clara."""
    # Configura LLM structured para falhar
    mock_structured = MagicMock()
    mock_structured.invoke.side_effect = Exception("LLM API timeout")
    mock_llm.with_structured_output.return_value = mock_structured
    
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    # Deve lançar ValueError com mensagem clara
    with pytest.raises(ValueError, match="Falha ao facilitar SWOT"):
        tool.facilitate_swot(
            company_info=company_info,
            strategic_context=strategic_context,
            use_rag=False
        )


# ============================================================================
# TESTES: MÉTODOS DE VALIDAÇÃO DO SCHEMA
# ============================================================================


def test_swot_is_complete_true():
    """Testa is_complete() retorna True com dados suficientes."""
    swot = SWOTAnalysis(
        strengths=["Força 1", "Força 2", "Força 3"],
        weaknesses=["Fraqueza 1", "Fraqueza 2"],
        opportunities=["Oportunidade 1", "Oportunidade 2", "Oportunidade 3"],
        threats=["Ameaça 1", "Ameaça 2"]
    )
    
    assert swot.is_complete() is True


def test_swot_is_complete_false_missing_items():
    """Testa is_complete() retorna False quando falta conteúdo."""
    swot = SWOTAnalysis(
        strengths=["Força 1"],  # Apenas 1 item
        weaknesses=["Fraqueza 1"],
        opportunities=[],  # Vazio
        threats=["Ameaça 1"]
    )
    
    assert swot.is_complete() is False


def test_swot_quality_score_perfect():
    """Testa quality_score() com SWOT perfeito (4 itens cada)."""
    swot = SWOTAnalysis(
        strengths=["S1", "S2", "S3", "S4"],
        weaknesses=["W1", "W2", "W3", "W4"],
        opportunities=["O1", "O2", "O3", "O4"],
        threats=["T1", "T2", "T3", "T4"]
    )
    
    score = swot.quality_score()
    assert score == 1.0  # Perfeito


def test_swot_quality_score_empty():
    """Testa quality_score() com SWOT vazio."""
    swot = SWOTAnalysis()  # Vazio (default)
    
    score = swot.quality_score()
    assert score == 0.0  # Zero


def test_swot_quality_score_partial():
    """Testa quality_score() com SWOT parcialmente preenchido."""
    swot = SWOTAnalysis(
        strengths=["S1", "S2"],  # 2/4
        weaknesses=["W1"],       # 1/4
        opportunities=["O1", "O2", "O3"],  # 3/4
        threats=[]  # 0/4
    )
    
    score = swot.quality_score()
    
    # Esperado: (2 + 1 + 3 + 0) / 16 = 6/16 = 0.375
    assert 0.35 <= score <= 0.40


def test_swot_summary_format():
    """Testa formato do summary()."""
    swot = SWOTAnalysis(
        strengths=["Força A"],
        weaknesses=["Fraqueza B"],
        opportunities=["Oportunidade C"],
        threats=["Ameaça D"]
    )
    
    summary = swot.summary()
    
    assert "Strengths" in summary or "Forças" in summary
    assert "Força A" in summary
    assert "Fraqueza B" in summary
    assert "Oportunidade C" in summary
    assert "Ameaça D" in summary


# ============================================================================
# TESTES: INTEGRAÇÃO COMPLETA (SMOKE TESTS)
# ============================================================================


def test_swot_tool_complete_workflow(
    mock_llm: MagicMock,
    mock_financial_agent: MagicMock,
    mock_customer_agent: MagicMock,
    mock_process_agent: MagicMock,
    mock_learning_agent: MagicMock,
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    """Smoke test: workflow completo com RAG."""
    tool = SWOTAnalysisTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent
    )
    
    # Facilitar SWOT com RAG
    swot = tool.facilitate_swot(
        company_info=company_info,
        strategic_context=strategic_context,
        use_rag=True
    )
    
    # Validações end-to-end
    assert swot.is_complete()
    assert swot.quality_score() >= 0.8
    
    summary = swot.summary()
    assert len(summary) > 100  # Summary substancial
    
    # Verificar que specialists foram chamados
    assert mock_financial_agent.invoke.called
    assert mock_customer_agent.invoke.called
    assert mock_process_agent.invoke.called
    assert mock_learning_agent.invoke.called
