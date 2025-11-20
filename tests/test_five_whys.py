"""Testes unitarios para Five Whys Tool.

Este modulo testa a ferramenta de analise de causa raiz (5 Porques)
com mocks completos de LLM e specialist agents.

Pattern: Implementation-First Testing (Lesson Sessao 16)
- API real lida ANTES de escrever testes
- Fixtures Pydantic validadas com margem de seguranca
- Mocks LLM structured output completos

Created: 2025-10-19 (FASE 3.2)
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from src.memory.schemas import (
    CompanyInfo,
    FiveWhysAnalysis,
    StrategicContext,
    WhyIteration,
)
from src.tools.five_whys import FiveWhysTool, IterationOutput, RootCauseOutput

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_llm():
    """Mock LLM para structured output."""
    llm = Mock()
    llm.with_structured_output = Mock(side_effect=lambda schema: Mock())
    return llm


@pytest.fixture
def mock_specialist_agents():
    """Mock 4 specialist agents para RAG."""
    financial = Mock()
    financial.invoke = Mock(return_value={"context": "Conhecimento financeiro BSC relevante" * 5})

    customer = Mock()
    customer.invoke = Mock(return_value={"context": "Conhecimento clientes BSC relevante" * 5})

    process = Mock()
    process.invoke = Mock(return_value={"context": "Conhecimento processos BSC relevante" * 5})

    learning = Mock()
    learning.invoke = Mock(return_value={"context": "Conhecimento aprendizado BSC relevante" * 5})

    return {
        "financial": financial,
        "customer": customer,
        "process": process,
        "learning": learning,
    }


@pytest.fixture
def valid_company_info():
    """CompanyInfo valido para testes."""
    return CompanyInfo(
        name="TechCorp Ltda",
        sector="Tecnologia",
        size="média",  # Validacao Pydantic: 'micro', 'pequena', 'media', 'grande'
        industry="Software",
    )


@pytest.fixture
def valid_strategic_context():
    """StrategicContext valido para testes."""
    return StrategicContext(
        mission="Fornecer solucoes tecnologicas inovadoras" * 3,  # >= 50 chars
        vision="Ser lider em transformacao digital" * 3,  # >= 50 chars
        core_values=["Inovacao", "Excelencia", "Colaboracao"],
        current_challenges=[
            "Vendas baixas no ultimo trimestre devido a perda de clientes chave",
            "Processos internos ineficientes causando retrabalho",
            "Falta de treinamento da equipe em novas tecnologias",
        ],
        strategic_objectives=[
            "Aumentar taxa de retencao de clientes em 30% nos proximos 12 meses",
            "Automatizar 50% dos processos manuais ate o final do ano",
            "Implementar programa de capacitacao continua para equipe tecnica",
        ],
    )


@pytest.fixture
def valid_problem_statement():
    """Problem statement valido (>= 10 chars)."""
    return "Vendas baixas no ultimo trimestre devido a perda de clientes chave"


@pytest.fixture
def mock_iteration_output():
    """Mock IterationOutput structured do LLM."""
    return IterationOutput(
        question="Por que as vendas estao baixas no ultimo trimestre?",
        answer="Porque houve perda de clientes chave para concorrentes",
        confidence=0.85,
        is_root_cause=False,
        reasoning="Cliente menciona perda de clientes no contexto. Alta confianca.",
    )


@pytest.fixture
def mock_root_cause_output():
    """Mock RootCauseOutput structured do LLM."""
    return RootCauseOutput(
        root_cause=(
            "Falta de programa estruturado de customer success e relacionamento "
            "pos-venda resultou em baixo engajamento e posterior churn de clientes chave"
        ),
        confidence_score=85.0,
        reasoning=(
            "Analise das 5 iteracoes revela que a causa fundamental e organizacional: "
            "ausencia de estrutura dedicada a retencao. Investimentos em aquisicao sem "
            "foco proporcional em retencao levaram ao churn."
        ),
        recommended_actions=[
            "Implementar area de Customer Success com 2-3 profissionais dedicados",
            "Criar playbook de onboarding e check-ins mensais com clientes chave",
            "Estabelecer metricas de saude do cliente (NPS, usage, engagement)",
        ],
    )


# ============================================================================
# TESTES: FiveWhysTool Initialization
# ============================================================================


def test_five_whys_tool_creation_with_all_agents(mock_llm, mock_specialist_agents):
    """Test: Criar FiveWhysTool com todos os agents configurados."""
    tool = FiveWhysTool(
        llm=mock_llm,
        financial_agent=mock_specialist_agents["financial"],
        customer_agent=mock_specialist_agents["customer"],
        process_agent=mock_specialist_agents["process"],
        learning_agent=mock_specialist_agents["learning"],
        max_iterations=7,
    )

    assert tool.llm == mock_llm
    assert tool.financial_agent == mock_specialist_agents["financial"]
    assert tool.max_iterations == 7
    assert tool.llm_iteration is not None
    assert tool.llm_synthesis is not None


def test_five_whys_tool_creation_without_rag_agents(mock_llm):
    """Test: Criar FiveWhysTool sem RAG agents (opciona)."""
    tool = FiveWhysTool(
        llm=mock_llm,
        financial_agent=None,
        customer_agent=None,
        process_agent=None,
        learning_agent=None,
        max_iterations=5,
    )

    assert tool.llm == mock_llm
    assert tool.financial_agent is None
    assert tool.max_iterations == 5
    assert not tool._rag_available()


# ============================================================================
# TESTES: facilitate_five_whys (metodo principal)
# ============================================================================


def test_facilitate_five_whys_without_rag(
    mock_llm,
    valid_company_info,
    valid_strategic_context,
    valid_problem_statement,
    mock_iteration_output,
    mock_root_cause_output,
):
    """Test: Facilitar 5 Whys SEM RAG (use_rag=False)."""
    tool = FiveWhysTool(
        llm=mock_llm,
        financial_agent=None,  # RAG desabilitado
        max_iterations=3,
    )

    # Mock LLM structured output (3 iteracoes)
    mock_llm_iteration = Mock()
    mock_llm_synthesis = Mock()

    # Configurar retornos
    iteration_outputs = [
        IterationOutput(
            question=f"Por que iteracao {i}?",
            answer=f"Resposta iteracao {i} com contexto suficiente",
            confidence=0.8 + i * 0.05,
            is_root_cause=(i == 3),
            reasoning=f"Reasoning iteracao {i} com detalhes suficientes para validacao",
        )
        for i in range(1, 4)
    ]
    mock_llm_iteration.invoke = Mock(side_effect=iteration_outputs)
    mock_llm_synthesis.invoke = Mock(return_value=mock_root_cause_output)

    tool.llm_iteration = mock_llm_iteration
    tool.llm_synthesis = mock_llm_synthesis

    # Execute
    analysis = tool.facilitate_five_whys(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        problem_statement=valid_problem_statement,
        use_rag=False,
    )

    # Validar
    assert isinstance(analysis, FiveWhysAnalysis)
    assert len(analysis.iterations) == 3
    assert analysis.depth_reached() == 3
    assert analysis.is_complete()
    assert analysis.root_cause == mock_root_cause_output.root_cause
    assert analysis.confidence_score == 85.0
    assert len(analysis.recommended_actions) >= 2


def test_facilitate_five_whys_with_rag(
    mock_llm,
    mock_specialist_agents,
    valid_company_info,
    valid_strategic_context,
    valid_problem_statement,
    mock_root_cause_output,
):
    """Test: Facilitar 5 Whys COM RAG (use_rag=True)."""
    tool = FiveWhysTool(
        llm=mock_llm,
        financial_agent=mock_specialist_agents["financial"],
        customer_agent=mock_specialist_agents["customer"],
        process_agent=mock_specialist_agents["process"],
        learning_agent=mock_specialist_agents["learning"],
        max_iterations=4,
    )

    # Mock LLM structured output (4 iteracoes)
    mock_llm_iteration = Mock()
    mock_llm_synthesis = Mock()

    iteration_outputs = [
        IterationOutput(
            question=f"Por que iteracao {i}?",
            answer=f"Resposta iteracao {i} enriquecida com conhecimento BSC do RAG",
            confidence=0.70 + i * 0.03,  # 0.73, 0.76, 0.79, 0.82 (todos < 0.85 threshold)
            is_root_cause=False,
            reasoning=f"Reasoning iteracao {i} baseado em literatura BSC recuperada",
        )
        for i in range(1, 5)
    ]
    mock_llm_iteration.invoke = Mock(side_effect=iteration_outputs)
    mock_llm_synthesis.invoke = Mock(return_value=mock_root_cause_output)

    tool.llm_iteration = mock_llm_iteration
    tool.llm_synthesis = mock_llm_synthesis

    # Execute
    analysis = tool.facilitate_five_whys(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        problem_statement=valid_problem_statement,
        use_rag=True,
    )

    # Validar
    assert isinstance(analysis, FiveWhysAnalysis)
    assert len(analysis.iterations) == 4
    assert analysis.is_complete()

    # Validar que RAG foi invocado (4 specialist agents)
    mock_specialist_agents["financial"].invoke.assert_called_once()
    mock_specialist_agents["customer"].invoke.assert_called_once()
    mock_specialist_agents["process"].invoke.assert_called_once()
    mock_specialist_agents["learning"].invoke.assert_called_once()

    # Validar contexto RAG no resultado
    assert len(analysis.context_from_rag) > 0


def test_facilitate_five_whys_stops_early_if_root_cause_reached(
    mock_llm,
    valid_company_info,
    valid_strategic_context,
    valid_problem_statement,
    mock_root_cause_output,
):
    """Test: 5 Whys para ANTES de max_iterations se root cause atingida."""
    tool = FiveWhysTool(
        llm=mock_llm,
        max_iterations=7,  # Maximo 7 mas deve parar em 3
    )

    # Mock LLM: 3 iteracoes, ultima indica root_cause=True
    mock_llm_iteration = Mock()
    mock_llm_synthesis = Mock()

    iteration_outputs = [
        IterationOutput(
            question="Por que iteracao 1?",
            answer="Resposta iteracao 1 ainda nao e root cause suficiente",
            confidence=0.8,
            is_root_cause=False,
            reasoning="Ainda ha camadas causais mais profundas a explorar",
        ),
        IterationOutput(
            question="Por que iteracao 2?",
            answer="Resposta iteracao 2 chegando mais perto da causa fundamental",
            confidence=0.85,
            is_root_cause=False,
            reasoning="Causa e especifica mas ainda pode ir mais fundo",
        ),
        IterationOutput(
            question="Por que iteracao 3?",
            answer="Falta de budget alocado para area de customer success (constraint real)",
            confidence=0.9,
            is_root_cause=True,  # ROOT CAUSE ATINGIDA!
            reasoning="Identificada constraint de recurso que e a causa fundamental",
        ),
    ]
    mock_llm_iteration.invoke = Mock(side_effect=iteration_outputs)
    mock_llm_synthesis.invoke = Mock(return_value=mock_root_cause_output)

    tool.llm_iteration = mock_llm_iteration
    tool.llm_synthesis = mock_llm_synthesis

    # Execute
    analysis = tool.facilitate_five_whys(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        problem_statement=valid_problem_statement,
        use_rag=False,
    )

    # Validar: Apenas 3 iteracoes (nao 7)
    assert len(analysis.iterations) == 3
    assert analysis.depth_reached() == 3
    assert mock_llm_iteration.invoke.call_count == 3  # Parou apos 3


def test_facilitate_five_whys_raises_error_if_problem_too_short(
    mock_llm,
    valid_company_info,
    valid_strategic_context,
):
    """Test: Raise ValueError se problem_statement muito curto (< 10 chars)."""
    tool = FiveWhysTool(llm=mock_llm)

    with pytest.raises(ValueError, match="problem_statement deve ter >= 10 chars"):
        tool.facilitate_five_whys(
            company_info=valid_company_info,
            strategic_context=valid_strategic_context,
            problem_statement="Vendas",  # Apenas 6 chars (invalido!)
            use_rag=False,
        )


def test_facilitate_five_whys_raises_error_if_less_than_3_iterations(
    mock_llm,
    valid_company_info,
    valid_strategic_context,
    valid_problem_statement,
):
    """Test: Raise ValueError se menos de 3 iteracoes coletadas."""
    tool = FiveWhysTool(llm=mock_llm, max_iterations=3)

    # Mock LLM que falha apos 2 iteracoes
    mock_llm_iteration = Mock()

    iteration_outputs = [
        IterationOutput(
            question="Por que 1?",
            answer="Resposta 1 suficientemente detalhada",
            confidence=0.8,
            is_root_cause=False,
            reasoning="Reasoning 1 com detalhes suficientes para validacao",
        ),
        IterationOutput(
            question="Por que 2?",
            answer="Resposta 2 suficientemente detalhada",
            confidence=0.8,
            is_root_cause=False,
            reasoning="Reasoning 2 com detalhes suficientes para validacao",
        ),
        Exception("LLM falhou na iteracao 3 - simulando erro"),
    ]
    mock_llm_iteration.invoke = Mock(side_effect=iteration_outputs)

    tool.llm_iteration = mock_llm_iteration

    with pytest.raises(ValueError, match="Falha ao facilitar iteracao 3"):
        tool.facilitate_five_whys(
            company_info=valid_company_info,
            strategic_context=valid_strategic_context,
            problem_statement=valid_problem_statement,
            use_rag=False,
        )


# ============================================================================
# TESTES: FiveWhysAnalysis Schema
# ============================================================================


def test_five_whys_analysis_is_complete_true():
    """Test: FiveWhysAnalysis.is_complete() retorna True se valido."""
    iterations = [
        WhyIteration(
            iteration_number=i,
            question=f"Por que iteracao {i}?",
            answer=f"Resposta da iteracao {i} com detalhes suficientes para validacao",
            confidence=0.8,
        )
        for i in range(1, 4)
    ]

    analysis = FiveWhysAnalysis(
        problem_statement="Problema inicial com descricao suficiente",
        iterations=iterations,
        root_cause="Causa raiz fundamental identificada com detalhes suficientes para acao",
        confidence_score=85.0,
        recommended_actions=[
            "Acao recomendada 1 concreta e acionavel",
            "Acao recomendada 2 concreta e acionavel",
        ],
    )

    assert analysis.is_complete() is True


def test_five_whys_analysis_is_complete_false_insufficient_iterations():
    """Test: FiveWhysAnalysis.is_complete() retorna False se < 3 iteracoes."""
    iterations = [
        WhyIteration(
            iteration_number=1,
            question="Por que iteracao 1?",
            answer="Resposta da iteracao 1 com detalhes suficientes",
            confidence=0.8,
        ),
        WhyIteration(
            iteration_number=2,
            question="Por que iteracao 2?",
            answer="Resposta da iteracao 2 com detalhes suficientes",
            confidence=0.8,
        ),
    ]

    with pytest.raises(ValidationError):
        # Schema valida min_length=3 para iterations
        FiveWhysAnalysis(
            problem_statement="Problema inicial suficiente",
            iterations=iterations,  # Apenas 2 (invalido!)
            root_cause="Causa raiz fundamental com detalhes",
            confidence_score=85.0,
            recommended_actions=["Acao 1", "Acao 2"],
        )


def test_five_whys_analysis_depth_reached():
    """Test: FiveWhysAnalysis.depth_reached() retorna numero correto."""
    iterations = [
        WhyIteration(
            iteration_number=i,
            question=f"Por que {i}?",
            answer=f"Resposta {i} com detalhes suficientes",
            confidence=0.8,
        )
        for i in range(1, 6)  # 5 iteracoes
    ]

    analysis = FiveWhysAnalysis(
        problem_statement="Problema inicial suficiente",
        iterations=iterations,
        root_cause="Causa raiz fundamental com detalhes suficientes",
        confidence_score=85.0,
        recommended_actions=["Acao 1 suficiente", "Acao 2 suficiente"],
    )

    assert analysis.depth_reached() == 5


def test_five_whys_analysis_root_cause_confidence():
    """Test: FiveWhysAnalysis.root_cause_confidence() retorna score correto."""
    iterations = [
        WhyIteration(
            iteration_number=i,
            question=f"Por que {i}?",
            answer=f"Resposta {i} suficiente",
            confidence=0.8,
        )
        for i in range(1, 4)
    ]

    analysis = FiveWhysAnalysis(
        problem_statement="Problema inicial suficiente",
        iterations=iterations,
        root_cause="Causa raiz fundamental suficiente",
        confidence_score=92.5,
        recommended_actions=["Acao 1 suficiente", "Acao 2 suficiente"],
    )

    assert analysis.root_cause_confidence() == 92.5


def test_five_whys_analysis_average_confidence():
    """Test: FiveWhysAnalysis.average_confidence() calcula media correta."""
    iterations = [
        WhyIteration(
            iteration_number=1,
            question="Por que 1?",
            answer="Resposta 1 suficiente",
            confidence=0.8,
        ),
        WhyIteration(
            iteration_number=2,
            question="Por que 2?",
            answer="Resposta 2 suficiente",
            confidence=0.9,
        ),
        WhyIteration(
            iteration_number=3,
            question="Por que 3?",
            answer="Resposta 3 suficiente",
            confidence=0.7,
        ),
    ]

    analysis = FiveWhysAnalysis(
        problem_statement="Problema inicial suficiente",
        iterations=iterations,
        root_cause="Causa raiz fundamental suficiente",
        confidence_score=85.0,
        recommended_actions=["Acao 1 suficiente", "Acao 2 suficiente"],
    )

    expected_avg = (0.8 + 0.9 + 0.7) / 3
    assert analysis.average_confidence() == pytest.approx(expected_avg)


def test_five_whys_analysis_summary_format():
    """Test: FiveWhysAnalysis.summary() retorna formato correto."""
    iterations = [
        WhyIteration(
            iteration_number=i,
            question=f"Por que iteracao {i}?",
            answer=f"Resposta da iteracao {i}",
            confidence=0.8,
        )
        for i in range(1, 4)
    ]

    analysis = FiveWhysAnalysis(
        problem_statement="Vendas baixas no ultimo trimestre",
        iterations=iterations,
        root_cause="Falta de programa de customer success estruturado",
        confidence_score=85.0,
        recommended_actions=[
            "Implementar area de Customer Success",
            "Criar playbook de onboarding",
        ],
    )

    summary = analysis.summary()

    assert "Problema: Vendas baixas no ultimo trimestre" in summary
    assert "Iteracoes (3):" in summary
    assert "1. Por que iteracao 1? -> Resposta da iteracao 1" in summary
    assert "Causa Raiz: Falta de programa de customer success estruturado" in summary
    assert "Confianca: 85.0%" in summary
    assert "Acoes Recomendadas (2):" in summary
    assert "1. Implementar area de Customer Success" in summary


# ============================================================================
# TESTES: Validacoes Pydantic
# ============================================================================


def test_five_whys_analysis_validates_iteration_sequence():
    """Test: FiveWhysAnalysis valida que iteration_number esta em sequencia."""
    iterations = [
        WhyIteration(
            iteration_number=1,
            question="Por que 1?",
            answer="Resposta 1 suficiente",
            confidence=0.8,
        ),
        WhyIteration(
            iteration_number=3,  # Pulou 2! (invalido)
            question="Por que 3?",
            answer="Resposta 3 suficiente",
            confidence=0.8,
        ),
        WhyIteration(
            iteration_number=4,
            question="Por que 4?",
            answer="Resposta 4 suficiente",
            confidence=0.8,
        ),
    ]

    with pytest.raises(ValidationError, match="Iteration numbers devem estar em sequencia"):
        FiveWhysAnalysis(
            problem_statement="Problema inicial suficiente",
            iterations=iterations,
            root_cause="Causa raiz fundamental suficiente",
            confidence_score=85.0,
            recommended_actions=["Acao 1 suficiente", "Acao 2 suficiente"],
        )


def test_five_whys_analysis_validates_actions_not_empty():
    """Test: FiveWhysAnalysis valida que cada acao tem >= 10 chars."""
    iterations = [
        WhyIteration(
            iteration_number=i,
            question=f"Por que {i}?",
            answer=f"Resposta {i} suficiente",
            confidence=0.8,
        )
        for i in range(1, 4)
    ]

    with pytest.raises(ValidationError, match="Action 2 deve ter pelo menos 10 caracteres"):
        FiveWhysAnalysis(
            problem_statement="Problema inicial suficiente",
            iterations=iterations,
            root_cause="Causa raiz fundamental suficiente",
            confidence_score=85.0,
            recommended_actions=[
                "Acao 1 concreta e acionavel com detalhes",
                "Curta",  # Apenas 5 chars (invalido!)
            ],
        )
