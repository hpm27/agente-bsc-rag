"""Testes para DiagnosticAgent.

Suite completa de testes para validação do agente de diagnóstico BSC
multi-perspectiva.

Cobertura:
- analyze_perspective() para cada uma das 4 perspectivas
- run_parallel_analysis() (execução AsyncIO)
- consolidate_diagnostic() (cross-perspective synergies)
- generate_recommendations() (priorização)
- run_diagnostic() (orquestrador E2E)
- Validações de erro (dados ausentes, output inválido)
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from src.agents.diagnostic_agent import DiagnosticAgent
from src.graph.states import BSCState
from src.memory.schemas import (
    ClientProfile,
    CompanyInfo,
    CompleteDiagnostic,
    DiagnosticResult,
    Recommendation,
    StrategicContext,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_llm():
    """LLM mockado para testes."""
    llm = MagicMock()
    return llm


@pytest.fixture
def diagnostic_agent(mock_llm):
    """DiagnosticAgent instanciado com LLM mockado."""
    return DiagnosticAgent(llm=mock_llm)


@pytest.fixture
def sample_client_profile():
    """ClientProfile de exemplo para testes."""
    company = CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média",
        industry="Software as a Service",
    )

    context = StrategicContext(
        mission="Transformar a indústria através da inovação",
        vision="Ser líder global até 2030",
        current_challenges=[
            "Alta rotatividade de talentos",
            "Processos manuais ineficientes",
            "Falta de visibilidade financeira",
        ],
        strategic_objectives=[
            "Crescer receita recorrente em 30% ao ano",
            "Reduzir churn de clientes para 5%",
            "Automatizar 50% dos processos em 6 meses",
        ],
    )

    profile = ClientProfile(company=company, context=context)
    return profile


@pytest.fixture
def sample_bsc_state(sample_client_profile):
    """BSCState de exemplo com ClientProfile."""
    state = BSCState(
        query="Como implementar BSC?",  # Campo obrigatório
        conversation_history=[],
        client_profile=sample_client_profile,
    )
    return state


@pytest.fixture
def sample_diagnostic_result():
    """DiagnosticResult de exemplo (perspectiva Financeira)."""
    return DiagnosticResult(
        perspective="Financeira",
        current_state="Empresa possui EBITDA de 22% mas falta visibilidade de custos por projeto",
        gaps=[
            "Ausência de ABC costing",
            "KPIs financeiros não conectados a processos",
            "Falta de análise de rentabilidade por cliente",
        ],
        opportunities=[
            "Implementar ABC costing",
            "Conectar KPIs financeiros a processos",
            "Dashboard financeiro executivo",
        ],
        priority="HIGH",
        key_insights=["Kaplan & Norton: 60% empresas falham em conectar finanças a processos"],
    )


@pytest.fixture
def sample_perspective_results(sample_diagnostic_result):
    """Resultados das 4 perspectivas para testes."""
    return {
        "Financeira": sample_diagnostic_result,
        "Clientes": DiagnosticResult(
            perspective="Clientes",
            current_state="Churn rate de 18%/ano, NPS não medido",
            gaps=["Ausência de métricas de satisfação", "Churn analysis superficial"],
            opportunities=["Implementar programa Voice of Customer", "Segmentar clientes"],
            priority="MEDIUM",
            key_insights=["Kaplan: reter cliente é 5-10x mais barato que adquirir"],
        ),
        "Processos Internos": DiagnosticResult(
            perspective="Processos Internos",
            current_state="60% processos manuais, lead time 45 dias",
            gaps=["Processos não documentados", "Lead time 80% acima do benchmark"],
            opportunities=["Value Stream Mapping", "Automatizar processos gargalo"],
            priority="HIGH",
            key_insights=["Execution Premium: excelência operacional requer medição contínua"],
        ),
        "Aprendizado e Crescimento": DiagnosticResult(
            perspective="Aprendizado e Crescimento",
            current_state="Turnover 35%/ano, sistemas legados de 15 anos",
            gaps=["Turnover 75% acima da média", "Sistemas legados impedem decisões data-driven"],
            opportunities=["Programa de retenção de talentos", "Modernizar stack tecnológico"],
            priority="HIGH",
            key_insights=["Kaplan: Aprendizado é a base da pirâmide BSC"],
        ),
    }


# ============================================================================
# TESTES: analyze_perspective()
# ============================================================================


def test_analyze_perspective_financial(diagnostic_agent, sample_bsc_state):
    """Testa análise da perspectiva Financeira."""
    # Mock structured output do LLM
    mock_result = DiagnosticResult(
        perspective="Financeira",
        current_state="Teste análise financeira com pelo menos 20 caracteres",
        gaps=["Gap 1", "Gap 2", "Gap 3"],
        opportunities=["Opp 1", "Opp 2"],
        priority="HIGH",
        key_insights=["Insight 1"],
    )

    diagnostic_agent.llm.with_structured_output = Mock(
        return_value=Mock(invoke=Mock(return_value=mock_result))
    )

    # Mock specialist agent (método correto: invoke, não process_query)
    with patch.object(
        diagnostic_agent.financial_agent, "invoke", return_value={"answer": "Contexto BSC"}
    ):
        result = diagnostic_agent.analyze_perspective(
            "Financeira",
            sample_bsc_state.client_profile,
            sample_bsc_state,
        )

    assert result.perspective == "Financeira"
    assert result.priority == "HIGH"
    assert len(result.gaps) == 3
    assert len(result.opportunities) == 2


def test_analyze_perspective_customer(diagnostic_agent, sample_bsc_state):
    """Testa análise da perspectiva Clientes."""
    mock_result = DiagnosticResult(
        perspective="Clientes",
        current_state="Teste análise clientes com 20+ caracteres",
        gaps=["Gap A"],
        opportunities=["Opp A"],
        priority="MEDIUM",
        key_insights=["Insight A"],
    )

    diagnostic_agent.llm.with_structured_output = Mock(
        return_value=Mock(invoke=Mock(return_value=mock_result))
    )

    with patch.object(
        diagnostic_agent.customer_agent, "invoke", return_value={"answer": "Contexto BSC"}
    ):
        result = diagnostic_agent.analyze_perspective(
            "Clientes",
            sample_bsc_state.client_profile,
            sample_bsc_state,
        )

    assert result.perspective == "Clientes"
    assert result.priority == "MEDIUM"


def test_analyze_perspective_invalid_perspective(diagnostic_agent, sample_bsc_state):
    """Testa que perspectiva inválida lança ValueError."""
    with pytest.raises(ValueError, match="Perspectiva inválida"):
        diagnostic_agent.analyze_perspective(
            "InvalidPerspective",  # type: ignore
            sample_bsc_state.client_profile,
            sample_bsc_state,
        )


# ============================================================================
# TESTES: run_parallel_analysis()
# ============================================================================


@pytest.mark.asyncio
async def test_run_parallel_analysis_success(diagnostic_agent, sample_bsc_state):
    """Testa análise paralela das 4 perspectivas com sucesso."""
    # Mock analyze_perspective para retornar resultados distintos
    mock_results = {
        "Financeira": DiagnosticResult(
            perspective="Financeira",
            current_state="Financial state analysis with sufficient characters",
            gaps=["Gap 1"],
            opportunities=["Opp 1"],
            priority="HIGH",
            key_insights=["Insight 1"],
        ),
        "Clientes": DiagnosticResult(
            perspective="Clientes",
            current_state="Customer state analysis with sufficient characters",
            gaps=["Gap 2"],
            opportunities=["Opp 2"],
            priority="MEDIUM",
            key_insights=["Insight 2"],
        ),
        "Processos Internos": DiagnosticResult(
            perspective="Processos Internos",
            current_state="Process state analysis with sufficient characters",
            gaps=["Gap 3"],
            opportunities=["Opp 3"],
            priority="HIGH",
            key_insights=["Insight 3"],
        ),
        "Aprendizado e Crescimento": DiagnosticResult(
            perspective="Aprendizado e Crescimento",
            current_state="Learning state analysis with sufficient characters",
            gaps=["Gap 4"],
            opportunities=["Opp 4"],
            priority="LOW",
            key_insights=["Insight 4"],
        ),
    }

    def mock_analyze(perspective, profile, state):
        return mock_results[perspective]

    with patch.object(diagnostic_agent, "analyze_perspective", side_effect=mock_analyze):
        results = await diagnostic_agent.run_parallel_analysis(
            sample_bsc_state.client_profile,
            sample_bsc_state,
        )

    # Validar que retornou 4 resultados
    assert len(results) == 4
    assert "Financeira" in results
    assert "Clientes" in results
    assert "Processos Internos" in results
    assert "Aprendizado e Crescimento" in results

    # Validar que cada resultado é correto
    assert results["Financeira"].priority == "HIGH"
    assert results["Clientes"].priority == "MEDIUM"
    assert results["Processos Internos"].priority == "HIGH"
    assert results["Aprendizado e Crescimento"].priority == "LOW"


# ============================================================================
# TESTES: consolidate_diagnostic()
# ============================================================================


def test_consolidate_diagnostic_success(diagnostic_agent, sample_perspective_results):
    """Testa consolidação cross-perspective com sucesso."""
    # Mock LLM response com JSON válido
    mock_response = Mock()
    mock_response.content = """{
        "cross_perspective_synergies": [
            "Processos manuais -> custos altos",
            "Turnover alto -> qualidade inconsistente"
        ],
        "executive_summary": "Empresa possui desafios estruturais em 3 perspectivas. Principais gaps: custos opacos, processos manuais, turnover alto. Recomenda-se iniciar pela perspectiva Aprendizado.",
        "next_phase": "APPROVAL_PENDING"
    }"""

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    consolidated = diagnostic_agent.consolidate_diagnostic(sample_perspective_results)

    assert "cross_perspective_synergies" in consolidated
    assert "executive_summary" in consolidated
    assert "next_phase" in consolidated
    assert len(consolidated["cross_perspective_synergies"]) == 2
    assert consolidated["next_phase"] == "APPROVAL_PENDING"


def test_consolidate_diagnostic_invalid_json(diagnostic_agent, sample_perspective_results):
    """Testa que JSON inválido lança ValueError."""
    mock_response = Mock()
    mock_response.content = "Not a valid JSON"

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    with pytest.raises(ValueError, match="JSON inválido"):
        diagnostic_agent.consolidate_diagnostic(sample_perspective_results)


def test_consolidate_diagnostic_missing_field(diagnostic_agent, sample_perspective_results):
    """Testa que campo obrigatório ausente lança ValueError."""
    mock_response = Mock()
    mock_response.content = """{
        "cross_perspective_synergies": ["Synergy 1"],
        "executive_summary": "Summary text"
    }"""

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    with pytest.raises(ValueError, match="Campo obrigatório ausente"):
        diagnostic_agent.consolidate_diagnostic(sample_perspective_results)


# ============================================================================
# TESTES: generate_recommendations()
# ============================================================================


def test_generate_recommendations_success(diagnostic_agent, sample_perspective_results):
    """Testa geração de recomendações com sucesso."""
    mock_consolidated = {
        "cross_perspective_synergies": ["Synergy 1", "Synergy 2"],
        "executive_summary": "Executive summary text",
        "next_phase": "APPROVAL_PENDING",
    }

    # Mock LLM response com lista de recomendações
    mock_response = Mock()
    mock_response.content = """[
        {
            "title": "Implementar Dashboard Financeiro",
            "description": "Criar dashboard executivo com top 10 KPIs financeiros conectados a processos operacionais",
            "impact": "HIGH",
            "effort": "LOW",
            "priority": "HIGH",
            "timeframe": "quick win (1-3 meses)",
            "next_steps": ["Definir KPIs", "Prototipar dashboard"]
        },
        {
            "title": "Criar Programa de Retenção",
            "description": "Programa estruturado de desenvolvimento e retenção de talentos com planos de carreira e mentoria",
            "impact": "HIGH",
            "effort": "MEDIUM",
            "priority": "HIGH",
            "timeframe": "médio prazo (3-6 meses)",
            "next_steps": ["Mapear competências críticas", "Criar trilhas de carreira"]
        },
        {
            "title": "Implementar NPS Trimestral",
            "description": "Programa Voice of Customer com surveys trimestrais para medir NPS e CSAT",
            "impact": "MEDIUM",
            "effort": "LOW",
            "priority": "MEDIUM",
            "timeframe": "quick win (1-3 meses)",
            "next_steps": ["Definir survey questions", "Escolher ferramenta"]
        }
    ]"""

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    recommendations = diagnostic_agent.generate_recommendations(
        sample_perspective_results,
        mock_consolidated,
    )

    # Validar quantidade e ordenação
    assert len(recommendations) == 3
    assert recommendations[0].priority == "HIGH"
    assert recommendations[1].priority == "HIGH"
    assert recommendations[2].priority == "MEDIUM"

    # Validar conteúdo
    assert "Dashboard Financeiro" in recommendations[0].title
    assert recommendations[0].impact == "HIGH"
    assert recommendations[0].effort == "LOW"


def test_generate_recommendations_invalid_list(diagnostic_agent, sample_perspective_results):
    """Testa que output não-lista lança ValueError."""
    mock_consolidated = {
        "cross_perspective_synergies": [],
        "executive_summary": "Summary",
        "next_phase": "APPROVAL_PENDING",
    }

    mock_response = Mock()
    mock_response.content = """{"not": "a list"}"""

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    with pytest.raises(ValueError, match="lista de recomendações"):
        diagnostic_agent.generate_recommendations(
            sample_perspective_results,
            mock_consolidated,
        )


# ============================================================================
# TESTES: run_diagnostic() - ORQUESTRADOR E2E
# ============================================================================


@pytest.mark.asyncio
async def test_run_diagnostic_success(
    diagnostic_agent, sample_bsc_state, sample_perspective_results
):
    """Testa execução completa do diagnóstico E2E."""

    # Mock run_parallel_analysis para retornar sample_perspective_results
    async def mock_parallel(*args, **kwargs):
        return sample_perspective_results

    with patch.object(diagnostic_agent, "run_parallel_analysis", side_effect=mock_parallel):
        # Mock consolidate_diagnostic
        mock_consolidated = {
            "cross_perspective_synergies": ["Synergy 1"],
            "executive_summary": "Executive summary com 250 caracteres mínimo para validar constraint Pydantic do campo executive_summary que requer entre 200 e 2000 caracteres. Este texto possui conteúdo suficiente para passar na validação do schema CompleteDiagnostic.",
            "next_phase": "APPROVAL_PENDING",
        }

        with patch.object(
            diagnostic_agent, "consolidate_diagnostic", return_value=mock_consolidated
        ):
            # Mock generate_recommendations
            mock_recommendations = [
                Recommendation(
                    title="Recomendação Teste 1",
                    description="Descrição detalhada com mais de 50 caracteres conforme requerido",
                    impact="HIGH",
                    effort="LOW",
                    priority="HIGH",
                    timeframe="quick win (1-3 meses)",
                    next_steps=["Step 1", "Step 2"],
                ),
                Recommendation(
                    title="Recomendação Teste 2",
                    description="Outra descrição detalhada com mais de 50 caracteres para validação",
                    impact="MEDIUM",
                    effort="MEDIUM",
                    priority="MEDIUM",
                    timeframe="médio prazo (3-6 meses)",
                    next_steps=["Step A"],
                ),
                Recommendation(
                    title="Recomendação Teste 3",
                    description="Terceira descrição detalhada cumprindo requisito de 50+ caracteres",
                    impact="LOW",
                    effort="LOW",
                    priority="LOW",
                    timeframe="longo prazo (6-12 meses)",
                    next_steps=["Step X"],
                ),
            ]

            with patch.object(
                diagnostic_agent, "generate_recommendations", return_value=mock_recommendations
            ):
                diagnostic = await diagnostic_agent.run_diagnostic(sample_bsc_state)

    # Validar CompleteDiagnostic
    assert isinstance(diagnostic, CompleteDiagnostic)
    assert diagnostic.financial.perspective == "Financeira"
    assert diagnostic.customer.perspective == "Clientes"
    assert diagnostic.process.perspective == "Processos Internos"
    assert diagnostic.learning.perspective == "Aprendizado e Crescimento"
    assert len(diagnostic.recommendations) == 3
    assert len(diagnostic.cross_perspective_synergies) == 1
    assert len(diagnostic.executive_summary) >= 200
    assert diagnostic.next_phase == "APPROVAL_PENDING"


@pytest.mark.asyncio
async def test_run_diagnostic_missing_client_profile(diagnostic_agent):
    """Testa que client_profile ausente lança ValueError."""
    state = BSCState(
        query="Como implementar BSC?",
        conversation_history=[],
        # client_profile=None  # Propositalmente ausente
    )

    with pytest.raises(ValueError, match="client_profile ausente"):
        await diagnostic_agent.run_diagnostic(state)


# ============================================================================
# TESTES: VALIDAÇÃO DE SCHEMAS PYDANTIC
# ============================================================================


def test_diagnostic_result_validation():
    """Testa validações do schema DiagnosticResult."""
    # Valid result
    result = DiagnosticResult(
        perspective="Financeira",
        current_state="State with more than 20 chars",
        gaps=["Gap 1"],
        opportunities=["Opp 1"],
        priority="HIGH",
        key_insights=["Insight 1"],
    )
    assert result.perspective == "Financeira"

    # Invalid: current_state too short
    with pytest.raises(ValidationError):
        DiagnosticResult(
            perspective="Financeira",
            current_state="Short",  # < 20 chars
            gaps=[],
            opportunities=[],
            priority="HIGH",
            key_insights=[],
        )


@pytest.fixture
def sample_complete_diagnostic(sample_perspective_results):
    """CompleteDiagnostic de exemplo para testes de refinement."""
    return CompleteDiagnostic(
        financial=sample_perspective_results["Financeira"],
        customer=sample_perspective_results["Clientes"],
        process=sample_perspective_results["Processos Internos"],
        learning=sample_perspective_results["Aprendizado e Crescimento"],
        recommendations=[
            Recommendation(
                title="Implementar ABC Costing",
                description="Descrição detalhada com mais de 50 caracteres conforme requerido pelo schema Pydantic",
                impact="HIGH",
                effort="MEDIUM",
                priority="HIGH",
                timeframe="médio prazo (3-6 meses)",
                next_steps=["Mapear processos", "Identificar cost drivers"],
            ),
            Recommendation(
                title="Programa Voice of Customer",
                description="Outra descrição detalhada com mais de 50 caracteres para validação do schema",
                impact="MEDIUM",
                effort="LOW",
                priority="MEDIUM",
                timeframe="quick win (1-3 meses)",
                next_steps=["Criar surveys", "Analisar feedback"],
            ),
            Recommendation(
                title="Automatização de Processos Críticos",
                description="Terceira recomendação detalhada com mais de 50 caracteres para atender ao requisito mínimo de 3 recomendações do schema CompleteDiagnostic",
                impact="HIGH",
                effort="HIGH",
                priority="HIGH",
                timeframe="longo prazo (6-12 meses)",
                next_steps=[
                    "Mapear processos manuais",
                    "Identificar oportunidades de automação",
                    "Implementar RPA",
                ],
            ),
        ],
        cross_perspective_synergies=[
            "Processos manuais (Processos) -> custos altos (Financeira) + erros frequentes (Clientes)"
        ],
        executive_summary=(
            "Executive summary com 250 caracteres mínimo para validar constraint Pydantic do campo "
            "executive_summary que requer entre 200 e 2000 caracteres. Este texto possui conteúdo "
            "suficiente para passar na validação do schema CompleteDiagnostic."
        ),
        next_phase="APPROVAL_PENDING",
    )


def test_recommendation_validation():
    """Testa validações do schema Recommendation."""
    # Valid recommendation
    rec = Recommendation(
        title="Valid Title Here",
        description="Description with more than 50 characters required by schema",
        impact="HIGH",
        effort="LOW",
        priority="HIGH",
        timeframe="quick win (1-3 meses)",
        next_steps=["Step 1"],
    )
    assert rec.priority == "HIGH"

    # Invalid: title too short
    with pytest.raises(ValidationError):
        Recommendation(
            title="Short",  # < 10 chars
            description="Description with more than 50 characters required",
            perspective="Financeira",
            impact="HIGH",
            effort="LOW",
            priority="HIGH",
            timeframe="quick win",
            next_steps=[],
        )

    # Priority logic auto-correction (LOW impact + HIGH effort -> priority ajustado para LOW)
    rec_auto = Recommendation(
        title="Auto Priority Correction Test",
        description="This tests automatic priority correction based on impact vs effort logic that we have",
        impact="LOW",
        effort="HIGH",
        priority="HIGH",  # Will be auto-corrected to LOW
        timeframe="test",
        next_steps=["Step 1"],
    )
    assert rec_auto.priority == "LOW"  # Auto-corrected!


# ============================================================================
# TESTES: @retry DECORATOR BEHAVIOR (Memória [[memory:9969868]])
# ============================================================================


def test_analyze_perspective_retry_on_validation_error(diagnostic_agent, sample_bsc_state):
    """Testa que ValidationError após 3 tentativas é re-lançada (reraise=True).

    Com @retry(reraise=True), a exceção original é re-lançada após tentativas esgotadas.
    """
    # Mock que sempre lança ValidationError
    mock_result = Mock()
    mock_result.errors.return_value = [
        {"type": "value_error", "loc": ("test",), "msg": "Test error"}
    ]

    def mock_invoke_with_error(*args, **kwargs):
        # Criar ValidationError simples
        from pydantic import BaseModel, field_validator

        class TestModel(BaseModel):
            test_field: int

            @field_validator("test_field")
            @classmethod
            def validate_field(cls, v):
                raise ValueError("Test error")

        try:
            TestModel(test_field="invalid")  # Dispara ValidationError
        except ValidationError as e:
            raise e  # Re-lança para teste

    diagnostic_agent.llm.with_structured_output = Mock(
        return_value=Mock(invoke=mock_invoke_with_error)
    )

    with patch.object(
        diagnostic_agent.financial_agent, "invoke", return_value={"answer": "Context"}
    ):
        # Com reraise=True, lança ValidationError original (não RetryError)
        with pytest.raises(ValidationError):
            diagnostic_agent.analyze_perspective(
                "Financeira",
                sample_bsc_state.client_profile,
                sample_bsc_state,
            )


def test_consolidate_diagnostic_retry_on_value_error(diagnostic_agent, sample_perspective_results):
    """Testa que ValueError após 3 tentativas é re-lançada (reraise=True)."""
    # Mock que sempre retorna JSON inválido
    mock_response = Mock()
    mock_response.content = "Invalid JSON causing ValueError"

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    # Com reraise=True, lança ValueError original
    with pytest.raises(ValueError):
        diagnostic_agent.consolidate_diagnostic(sample_perspective_results)


def test_generate_recommendations_retry_behavior(diagnostic_agent, sample_perspective_results):
    """Testa que ValueError após 3 tentativas é re-lançada (reraise=True)."""
    mock_consolidated = {
        "cross_perspective_synergies": [],
        "executive_summary": "Summary",
        "next_phase": "APPROVAL_PENDING",
    }

    # Mock que sempre retorna JSON inválido
    mock_response = Mock()
    mock_response.content = "Not valid JSON"

    diagnostic_agent.llm.invoke = Mock(return_value=mock_response)

    # Com reraise=True, lança ValueError original
    with pytest.raises(ValueError):
        diagnostic_agent.generate_recommendations(
            sample_perspective_results,
            mock_consolidated,
        )


# ============================================================================
# TESTES: REFINEMENT LOGIC (FASE 4.6)
# ============================================================================


@pytest.mark.asyncio
async def test_refine_diagnostic_validates_feedback_empty(
    diagnostic_agent, sample_complete_diagnostic, sample_bsc_state
):
    """refine_diagnostic deve validar que feedback não é vazio."""
    with pytest.raises(ValueError, match="Feedback não pode ser vazio"):
        await diagnostic_agent.refine_diagnostic(
            existing_diagnostic=sample_complete_diagnostic,
            feedback="",  # Feedback vazio
            state=sample_bsc_state,
        )


@pytest.mark.asyncio
async def test_refine_diagnostic_validates_diagnostic_none(diagnostic_agent, sample_bsc_state):
    """refine_diagnostic deve validar que diagnóstico não é None."""
    with pytest.raises(ValueError, match="Diagnóstico existente não pode ser None"):
        await diagnostic_agent.refine_diagnostic(
            existing_diagnostic=None,  # Diagnóstico None
            feedback="SWOT precisa mais Opportunities",
            state=sample_bsc_state,
        )


@pytest.mark.asyncio
async def test_refine_diagnostic_validates_client_profile(
    diagnostic_agent, sample_complete_diagnostic
):
    """refine_diagnostic deve validar que state tem client_profile."""
    state = BSCState(
        query="Como implementar BSC?",
        conversation_history=[],
        # client_profile ausente propositalmente
    )

    with pytest.raises(ValueError, match="client_profile ausente"):
        await diagnostic_agent.refine_diagnostic(
            existing_diagnostic=sample_complete_diagnostic,
            feedback="SWOT precisa mais Opportunities",
            state=state,
        )


@pytest.mark.asyncio
async def test_refine_diagnostic_returns_refined_diagnostic(
    diagnostic_agent, sample_complete_diagnostic, sample_bsc_state
):
    """refine_diagnostic deve retornar CompleteDiagnostic refinado."""
    # Mock LLM structured output
    refined_diagnostic_mock = CompleteDiagnostic(
        financial=sample_complete_diagnostic.financial,
        customer=sample_complete_diagnostic.customer,
        process=sample_complete_diagnostic.process,
        learning=sample_complete_diagnostic.learning,
        recommendations=[
            Recommendation(
                title="Nova Recomendação Refinada",
                description="Descrição detalhada com mais de 50 caracteres conforme requerido pelo schema Pydantic para validação",
                impact="HIGH",
                effort="LOW",
                priority="HIGH",
                timeframe="quick win (1-3 meses)",
                next_steps=["Step refinado 1", "Step refinado 2"],
            ),
        ]
        + sample_complete_diagnostic.recommendations,
        cross_perspective_synergies=sample_complete_diagnostic.cross_perspective_synergies,
        executive_summary="Executive summary refinado com melhorias aplicadas baseadas no feedback do usuário. "
        * 10,
        next_phase="APPROVAL_PENDING",
    )

    # Mock structured LLM (usar AsyncMock para ainvoke)
    mock_structured_llm = Mock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=refined_diagnostic_mock)
    diagnostic_agent.llm.with_structured_output = Mock(return_value=mock_structured_llm)

    # Executar refinement
    refined = await diagnostic_agent.refine_diagnostic(
        existing_diagnostic=sample_complete_diagnostic,
        feedback="SWOT precisa mais Opportunities relacionadas ao mercado enterprise",
        state=sample_bsc_state,
    )

    # Validar resultado
    assert isinstance(refined, CompleteDiagnostic)
    assert len(refined.recommendations) >= len(sample_complete_diagnostic.recommendations)
    assert refined.executive_summary != sample_complete_diagnostic.executive_summary


@pytest.mark.asyncio
async def test_refine_diagnostic_fallback_on_timeout(
    diagnostic_agent, sample_complete_diagnostic, sample_bsc_state
):
    """refine_diagnostic deve retornar diagnóstico original se timeout."""
    import asyncio

    # Mock LLM que demora muito (timeout)
    async def slow_llm(*args, **kwargs):
        await asyncio.sleep(400)  # Mais que timeout de 300s
        return sample_complete_diagnostic

    mock_structured_llm = Mock()
    mock_structured_llm.ainvoke = slow_llm
    diagnostic_agent.llm.with_structured_output = Mock(return_value=mock_structured_llm)

    # Executar refinement (deve timeout e retornar original)
    refined = await diagnostic_agent.refine_diagnostic(
        existing_diagnostic=sample_complete_diagnostic,
        feedback="SWOT precisa mais Opportunities",
        state=sample_bsc_state,
    )

    # Deve retornar diagnóstico original (fallback)
    assert refined == sample_complete_diagnostic


@pytest.mark.asyncio
async def test_refine_diagnostic_fallback_on_error(
    diagnostic_agent, sample_complete_diagnostic, sample_bsc_state
):
    """refine_diagnostic deve retornar diagnóstico original se erro."""
    # Mock LLM que lança exceção
    mock_structured_llm = Mock()
    mock_structured_llm.ainvoke = Mock(side_effect=Exception("LLM error"))
    diagnostic_agent.llm.with_structured_output = Mock(return_value=mock_structured_llm)

    # Executar refinement (deve capturar erro e retornar original)
    refined = await diagnostic_agent.refine_diagnostic(
        existing_diagnostic=sample_complete_diagnostic,
        feedback="SWOT precisa mais Opportunities",
        state=sample_bsc_state,
    )

    # Deve retornar diagnóstico original (fallback)
    assert refined == sample_complete_diagnostic


@pytest.mark.asyncio
async def test_refine_diagnostic_preserves_valid_insights(
    diagnostic_agent, sample_complete_diagnostic, sample_bsc_state
):
    """refine_diagnostic deve preservar insights válidos do diagnóstico original."""
    # Mock LLM que retorna diagnóstico refinado mantendo perspectivas
    refined_diagnostic_mock = CompleteDiagnostic(
        financial=sample_complete_diagnostic.financial,  # Mantém original
        customer=sample_complete_diagnostic.customer,  # Mantém original
        process=sample_complete_diagnostic.process,  # Mantém original
        learning=sample_complete_diagnostic.learning,  # Mantém original
        recommendations=sample_complete_diagnostic.recommendations
        + [
            Recommendation(
                title="Nova Recomendação Adicionada",
                description="Descrição detalhada com mais de 50 caracteres conforme requerido pelo schema Pydantic para validação completa",
                impact="MEDIUM",
                effort="LOW",
                priority="MEDIUM",
                timeframe="quick win (1-3 meses)",
                next_steps=["Novo step"],
            ),
        ],
        cross_perspective_synergies=sample_complete_diagnostic.cross_perspective_synergies,
        executive_summary="Executive summary atualizado refletindo melhorias aplicadas. " * 10,
        next_phase="APPROVAL_PENDING",
    )

    # Mock structured LLM (usar AsyncMock para ainvoke)
    mock_structured_llm = Mock()
    mock_structured_llm.ainvoke = AsyncMock(return_value=refined_diagnostic_mock)
    diagnostic_agent.llm.with_structured_output = Mock(return_value=mock_structured_llm)

    # Executar refinement
    refined = await diagnostic_agent.refine_diagnostic(
        existing_diagnostic=sample_complete_diagnostic,
        feedback="Adicionar mais recomendações práticas",
        state=sample_bsc_state,
    )

    # Validar que perspectivas foram preservadas
    assert refined.financial == sample_complete_diagnostic.financial
    assert refined.customer == sample_complete_diagnostic.customer
    assert refined.process == sample_complete_diagnostic.process
    assert refined.learning == sample_complete_diagnostic.learning
    # Recomendações devem ter aumentado
    assert len(refined.recommendations) > len(sample_complete_diagnostic.recommendations)


@pytest.mark.asyncio
async def test_refine_diagnostic_handles_llm_none_response(
    diagnostic_agent, sample_complete_diagnostic, sample_bsc_state
):
    """refine_diagnostic deve retornar diagnóstico original se LLM retorna None."""
    # Mock LLM que retorna None
    mock_structured_llm = Mock()
    mock_structured_llm.ainvoke = Mock(return_value=None)
    diagnostic_agent.llm.with_structured_output = Mock(return_value=mock_structured_llm)

    # Executar refinement
    refined = await diagnostic_agent.refine_diagnostic(
        existing_diagnostic=sample_complete_diagnostic,
        feedback="SWOT precisa mais Opportunities",
        state=sample_bsc_state,
    )

    # Deve retornar diagnóstico original (fallback)
    assert refined == sample_complete_diagnostic
