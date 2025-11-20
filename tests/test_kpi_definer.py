"""Testes unitarios para KPI Definer Tool.

Valida:
- Criacao e inicializacao de KPIDefinerTool
- Definicao de KPIs SMART com/sem RAG
- Validacao de schemas (KPIDefinition + KPIFramework)
- Balanceamento entre perspectivas BSC
- Tratamento de erros (LLM failures, validacao)

Created: 2025-10-19 (FASE 3.4)
Coverage target: 70%+
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.memory.schemas import (
    CompanyInfo,
    CompleteDiagnostic,
    DiagnosticResult,
    KPIDefinition,
    KPIFramework,
    Recommendation,
    StrategicContext,
)
from src.tools.kpi_definer import KPIDefinerTool

if TYPE_CHECKING:
    pass


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock LLM que retorna lista de KPIDefinition valida.

    Side effect detecta perspectiva no prompt e retorna KPIs correspondentes.
    """
    llm = MagicMock(spec=["invoke", "with_structured_output"])

    # Simula structured output que retorna lista de KPIs
    from pydantic import BaseModel

    class KPIListOutput(BaseModel):
        kpis: list[KPIDefinition]

    # Define KPIs mock para cada perspectiva
    kpis_by_perspective = {
        "Financeira": [
            KPIDefinition(
                name="Crescimento de Receita Recorrente (ARR)",
                description=(
                    "Mede o crescimento percentual da receita recorrente anual "
                    "(ARR) em relacao ao periodo anterior, indicando expansao sustentavel do negocio"
                ),
                perspective="Financeira",
                metric_type="quantidade",
                target_value="> 40%",
                measurement_frequency="mensal",
                data_source="ERP financeiro + CRM (contratos recorrentes)",
                calculation_formula="((ARR_atual - ARR_anterior) / ARR_anterior) * 100",
            ),
            KPIDefinition(
                name="EBITDA Margin",
                description=(
                    "Mede a margem de lucro operacional (EBITDA) em relacao a receita total, "
                    "indicando eficiencia operacional e rentabilidade antes de juros, impostos, "
                    "depreciacao e amortizacao"
                ),
                perspective="Financeira",
                metric_type="qualidade",
                target_value="> 25%",
                measurement_frequency="trimestral",
                data_source="Sistema contabil + balanco patrimonial",
                calculation_formula="(EBITDA / Receita_Total) * 100",
            ),
            KPIDefinition(
                name="Customer Acquisition Cost (CAC)",
                description=(
                    "Mede o custo medio para adquirir um novo cliente, incluindo marketing, "
                    "vendas e onboarding. Essencial para avaliar eficiencia de investimentos "
                    "em crescimento"
                ),
                perspective="Financeira",
                metric_type="custo",
                target_value="< R$ 5.000",
                measurement_frequency="mensal",
                data_source="CRM + plataforma marketing + financeiro",
                calculation_formula="Custos_Marketing_Vendas_Total / Numero_Novos_Clientes",
            ),
        ],
        "Clientes": [
            KPIDefinition(
                name="Net Promoter Score (NPS)",
                description=(
                    "Mede a satisfacao e lealdade dos clientes atraves da probabilidade "
                    "de recomendacao do produto a outros. Indicador chave de experiencia do cliente"
                ),
                perspective="Clientes",
                metric_type="qualidade",
                target_value="> 50",
                measurement_frequency="trimestral",
                data_source="Pesquisa NPS automatizada pos-interacao",
                calculation_formula="% Promotores (9-10) - % Detratores (0-6)",
            ),
            KPIDefinition(
                name="Customer Churn Rate",
                description=(
                    "Mede a taxa de cancelamento de clientes em um periodo. Metrica critica "
                    "para SaaS, indicando qualidade do produto e sucesso do cliente"
                ),
                perspective="Clientes",
                metric_type="quantidade",
                target_value="< 5%",
                measurement_frequency="mensal",
                data_source="CRM + sistema de billing",
                calculation_formula="(Clientes_Cancelados / Clientes_Inicio_Periodo) * 100",
            ),
            KPIDefinition(
                name="Customer Lifetime Value (CLV)",
                description=(
                    "Mede o valor total projetado que um cliente gerara durante todo "
                    "relacionamento com a empresa. Essencial para estrategias de retencao"
                ),
                perspective="Clientes",
                metric_type="quantidade",
                target_value="> R$ 50.000",
                measurement_frequency="trimestral",
                data_source="CRM + historico financeiro",
                calculation_formula="(Receita_Media_Mensal * Tempo_Vida_Cliente) - CAC",
            ),
        ],
        "Processos Internos": [
            KPIDefinition(
                name="Lead Time de Desenvolvimento",
                description=(
                    "Mede o tempo medio desde a concepcao de uma feature ate sua entrega "
                    "em producao. Indicador de agilidade e eficiencia operacional"
                ),
                perspective="Processos Internos",
                metric_type="tempo",
                target_value="< 15 dias",
                measurement_frequency="mensal",
                data_source="Jira + GitLab (pipeline CI/CD)",
                calculation_formula="Data_Deploy - Data_Inicio_Feature",
            ),
            KPIDefinition(
                name="Taxa de Automacao de Processos",
                description=(
                    "Mede o percentual de processos operacionais que foram automatizados "
                    "vs manuais. Indicador de eficiencia e escalabilidade"
                ),
                perspective="Processos Internos",
                metric_type="quantidade",
                target_value="> 70%",
                measurement_frequency="trimestral",
                data_source="Auditoria processos + sistema workflow",
                calculation_formula="(Processos_Automatizados / Total_Processos) * 100",
            ),
            KPIDefinition(
                name="Taxa de Incidentes Criticos",
                description=(
                    "Mede a quantidade de incidentes criticos (P1/P2) em producao por mes. "
                    "Indicador de qualidade do software e maturidade DevOps"
                ),
                perspective="Processos Internos",
                metric_type="quantidade",
                target_value="< 3 por mes",
                measurement_frequency="mensal",
                data_source="Sistema monitoring (Datadog, New Relic)",
                calculation_formula="Count(Incidentes_P1 + Incidentes_P2)",
            ),
        ],
        "Aprendizado e Crescimento": [
            KPIDefinition(
                name="Taxa de Retencao de Talentos",
                description=(
                    "Mede o percentual de colaboradores chave que permanecem na empresa "
                    "apos 12 meses. Indicador de clima e engajamento"
                ),
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value="> 90%",
                measurement_frequency="anual",
                data_source="Sistema RH (desligamentos)",
                calculation_formula="(Colaboradores_Permanentes / Total_Inicial) * 100",
            ),
            KPIDefinition(
                name="Horas de Treinamento por Colaborador",
                description=(
                    "Mede a media de horas investidas em capacitacao e desenvolvimento "
                    "por colaborador. Indicador de investimento em pessoas"
                ),
                perspective="Aprendizado e Crescimento",
                metric_type="tempo",
                target_value="> 40 horas/ano",
                measurement_frequency="anual",
                data_source="Plataforma LMS + registros treinamento",
                calculation_formula="Total_Horas_Treinamento / Numero_Colaboradores",
            ),
            KPIDefinition(
                name="Indice de Inovacao",
                description=(
                    "Mede o percentual da receita gerada por produtos/features lancadas "
                    "nos ultimos 12 meses. Indicador de capacidade de inovacao"
                ),
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value="> 20%",
                measurement_frequency="trimestral",
                data_source="Sistema financeiro + catalogo produtos",
                calculation_formula="(Receita_Novos_Produtos / Receita_Total) * 100",
            ),
        ],
    }

    # SOLUCAO: Usar contador de chamadas para retornar perspectiva correta sequencialmente
    # A tool chama 4x: Financeira -> Clientes -> Processos Internos -> Aprendizado
    from itertools import cycle

    perspective_order = [
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento",
    ]
    perspective_cycle = cycle(perspective_order)

    def mock_invoke_side_effect(prompt: str):
        """Retorna KPIs da proxima perspectiva na sequencia.

        Usa itertools.cycle para iterar pelas 4 perspectivas na ordem
        que a tool as chama (Financeira, Clientes, Processos, Aprendizado).
        """
        perspective = next(perspective_cycle)
        kpis = kpis_by_perspective[perspective]
        return KPIListOutput(kpis=kpis)

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.side_effect = mock_invoke_side_effect

    llm.with_structured_output.return_value = mock_structured_llm
    return llm


@pytest.fixture
def mock_financial_agent() -> MagicMock:
    """Mock Financial Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "KPIs financeiros BSC: Foco em rentabilidade, crescimento de receita, margem EBITDA e retorno sobre investimento (ROI)."
    }
    return agent


@pytest.fixture
def mock_customer_agent() -> MagicMock:
    """Mock Customer Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "KPIs clientes BSC: Satisfacao (CSAT), retencao (churn), net promoter score (NPS) e lifetime value (LTV)."
    }
    return agent


@pytest.fixture
def mock_process_agent() -> MagicMock:
    """Mock Process Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "KPIs processos BSC: Eficiencia operacional, lead time, taxa de defeitos e produtividade por colaborador."
    }
    return agent


@pytest.fixture
def mock_learning_agent() -> MagicMock:
    """Mock Learning Agent."""
    agent = MagicMock()
    agent.invoke.return_value = {
        "answer": "KPIs aprendizado BSC: Horas de treinamento por funcionario, taxa de promocao interna, indice de inovacao e engagement."
    }
    return agent


@pytest.fixture
def company_info() -> CompanyInfo:
    """Fixture de empresa valida para testes."""
    return CompanyInfo(
        name="TechInova Solutions",
        sector="Tecnologia",
        size="média",  # Corrigido: schema espera com acento
        industry="Desenvolvimento de Software B2B",
    )


@pytest.fixture
def strategic_context() -> StrategicContext:
    """Fixture de contexto estrategico valido."""
    return StrategicContext(
        mission="Democratizar tecnologia de gestao para PMEs brasileiras",
        vision="Ser referencia em software de gestao empresarial no Brasil ate 2027",
        core_values=["Inovacao continua", "Foco no cliente", "Excelencia tecnica"],
        strategic_objectives=[
            "Aumentar receita recorrente (ARR) em 40% em 2025",
            "Reduzir churn para <5% ao ano",
            "Lancar 3 novos produtos no portfolio",
        ],
        current_challenges=[
            "Competir com grandes players internacionais",
            "Escalar operacoes mantendo qualidade",
            "Reduzir churn de clientes",
        ],
    )


@pytest.fixture
def diagnostic_result() -> CompleteDiagnostic:
    """Fixture de diagnostico BSC completo valido."""
    return CompleteDiagnostic(
        financial=DiagnosticResult(
            perspective="Financeira",
            current_state="Empresa apresenta crescimento de receita mas margens em queda devido custos operacionais elevados",
            gaps=["Falta de controle rigoroso de custos", "Margens em declinio"],
            opportunities=[
                "Automacao para reduzir custos",
                "Renegociacao de contratos fornecedores",
            ],
            priority="HIGH",
        ),
        customer=DiagnosticResult(
            perspective="Clientes",
            current_state="Alta satisfacao inicial mas churn crescente apos 6 meses de uso do produto",
            gaps=["Onboarding insuficiente", "Suporte tecnico reativo"],
            opportunities=["Programa de sucesso do cliente", "Comunidade de usuarios"],
            priority="HIGH",
        ),
        process=DiagnosticResult(
            perspective="Processos Internos",
            current_state="Processos manuais geram gargalos e erros operacionais frequentes",
            gaps=["Automacao limitada", "Falta de padronizacao"],
            opportunities=["RPA para processos repetitivos", "Documentacao de workflows"],
            priority="MEDIUM",
        ),
        learning=DiagnosticResult(
            perspective="Aprendizado e Crescimento",
            current_state="Equipe tecnica qualificada mas com gaps em gestao de projetos ageis",
            gaps=["Falta de treinamento em metodologias ageis", "Cultura de feedback limitada"],
            opportunities=["Certificacoes Scrum/Kanban", "Programas de mentoria interna"],
            priority="MEDIUM",
        ),
        synergies=[
            "Automacao de processos internos pode reduzir custos operacionais (Processos + Financeira)",
            "Programa de sucesso do cliente pode melhorar retencao e receita (Clientes + Financeira)",
        ],
        executive_summary="TechInova Solutions apresenta crescimento solido mas enfrenta desafios de margens e churn. Priorizar automacao e sucesso do cliente.",
        recommendations=[
            Recommendation(
                title="Implementar programa de Customer Success",
                description="Criar equipe dedicada a acompanhar onboarding e adocao do produto para reduzir churn de 15% para <5%",
                impact="HIGH",
                effort="MEDIUM",
                priority="HIGH",
                timeframe="6 meses",
                next_steps=[
                    "Contratar lider de Customer Success",
                    "Definir jornada do cliente e milestones",
                    "Criar playbooks de onboarding",
                ],
            ),
            Recommendation(
                title="Automatizar processos operacionais repetitivos com RPA",
                description="Implementar Robotic Process Automation em processos manuais para reduzir custos operacionais em 20-30% e eliminar erros",
                impact="HIGH",
                effort="MEDIUM",
                priority="HIGH",
                timeframe="4 meses",
                next_steps=[
                    "Mapear processos repetitivos candidatos a RPA",
                    "Selecionar ferramenta RPA",
                    "Pilotar em 2-3 processos criticos",
                ],
            ),
            Recommendation(
                title="Implementar programa de capacitacao em metodologias ageis",
                description="Treinar equipe em Scrum e Kanban para melhorar gestao de projetos e velocidade de entrega de features",
                impact="MEDIUM",
                effort="LOW",
                priority="MEDIUM",
                timeframe="3 meses",
                next_steps=[
                    "Contratar consultoria especializada em Agile",
                    "Certificar 5 colaboradores em Scrum Master",
                    "Implementar sprints em 2 squads piloto",
                ],
            ),
        ],
    )


# ============================================================================
# TESTES: CRIACAO E INICIALIZACAO
# ============================================================================


def test_kpi_definer_tool_initialization(mock_llm, mock_financial_agent):
    """TESTE 1: Criacao basica de KPIDefinerTool."""
    tool = KPIDefinerTool(llm=mock_llm, financial_agent=mock_financial_agent)

    assert tool.llm == mock_llm
    assert tool.financial_agent == mock_financial_agent
    assert tool.customer_agent is None
    assert tool.process_agent is None
    assert tool.learning_agent is None


def test_kpi_definer_tool_initialization_with_all_agents(
    mock_llm, mock_financial_agent, mock_customer_agent, mock_process_agent, mock_learning_agent
):
    """TESTE 2: Criacao com todos 4 specialist agents."""
    tool = KPIDefinerTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent,
    )

    assert tool.llm == mock_llm
    assert tool.financial_agent == mock_financial_agent
    assert tool.customer_agent == mock_customer_agent
    assert tool.process_agent == mock_process_agent
    assert tool.learning_agent == mock_learning_agent


# ============================================================================
# TESTES: WORKFLOW COMPLETO
# ============================================================================


def test_define_kpis_without_rag(mock_llm, company_info, strategic_context, diagnostic_result):
    """TESTE 3: Definir KPIs sem RAG (use_rag=False)."""
    tool = KPIDefinerTool(llm=mock_llm)

    # Mock para retornar KPIs diferentes por perspectiva
    # (mesmo mock retorna KPIs 'Financeira' mas tool deve ajustar perspective)
    framework = tool.define_kpis(
        company_info=company_info,
        strategic_context=strategic_context,
        diagnostic_result=diagnostic_result,
        use_rag=False,
    )

    # Validar estrutura
    assert isinstance(framework, KPIFramework)
    assert framework.total_kpis() >= 8  # Minimo 2 por perspectiva
    assert framework.total_kpis() <= 32  # Maximo 8 por perspectiva

    # Validar cada perspectiva tem 2-8 KPIs
    assert 2 <= len(framework.financial_kpis) <= 8
    assert 2 <= len(framework.customer_kpis) <= 8
    assert 2 <= len(framework.process_kpis) <= 8
    assert 2 <= len(framework.learning_kpis) <= 8


def test_define_kpis_with_rag(
    mock_llm,
    mock_financial_agent,
    mock_customer_agent,
    mock_process_agent,
    mock_learning_agent,
    company_info,
    strategic_context,
    diagnostic_result,
):
    """TESTE 4: Definir KPIs com RAG (use_rag=True)."""
    tool = KPIDefinerTool(
        llm=mock_llm,
        financial_agent=mock_financial_agent,
        customer_agent=mock_customer_agent,
        process_agent=mock_process_agent,
        learning_agent=mock_learning_agent,
    )

    framework = tool.define_kpis(
        company_info=company_info,
        strategic_context=strategic_context,
        diagnostic_result=diagnostic_result,
        use_rag=True,
    )

    # Validar que RAG foi chamado (4 agents invoked)
    assert mock_financial_agent.invoke.called
    assert mock_customer_agent.invoke.called
    assert mock_process_agent.invoke.called
    assert mock_learning_agent.invoke.called

    # Validar estrutura framework
    assert isinstance(framework, KPIFramework)
    assert framework.total_kpis() >= 8


def test_define_kpis_missing_company_info(mock_llm, strategic_context, diagnostic_result):
    """TESTE 5: Erro se company_info None."""
    tool = KPIDefinerTool(llm=mock_llm)

    with pytest.raises(ValueError, match="company_info ausente"):
        tool.define_kpis(
            company_info=None,  # type: ignore
            strategic_context=strategic_context,
            diagnostic_result=diagnostic_result,
            use_rag=False,
        )


def test_define_kpis_missing_strategic_context(mock_llm, company_info, diagnostic_result):
    """TESTE 6: Erro se strategic_context None."""
    tool = KPIDefinerTool(llm=mock_llm)

    with pytest.raises(ValueError, match="strategic_context ausente"):
        tool.define_kpis(
            company_info=company_info,
            strategic_context=None,  # type: ignore
            diagnostic_result=diagnostic_result,
            use_rag=False,
        )


def test_define_kpis_missing_diagnostic_result(mock_llm, company_info, strategic_context):
    """TESTE 7: Erro se diagnostic_result None."""
    tool = KPIDefinerTool(llm=mock_llm)

    with pytest.raises(ValueError, match="diagnostic_result ausente"):
        tool.define_kpis(
            company_info=company_info,
            strategic_context=strategic_context,
            diagnostic_result=None,  # type: ignore
            use_rag=False,
        )


# ============================================================================
# TESTES: SCHEMA VALIDATION
# ============================================================================


def test_kpi_definition_valid():
    """TESTE 8: KPIDefinition valido com todos campos SMART."""
    kpi = KPIDefinition(
        name="Crescimento de Receita Recorrente",
        description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
        perspective="Financeira",
        metric_type="quantidade",
        target_value="> 30%",
        measurement_frequency="mensal",
        data_source="ERP financeiro",
        calculation_formula="((ARR_atual - ARR_anterior) / ARR_anterior) * 100",
    )

    assert kpi.name == "Crescimento de Receita Recorrente"
    assert kpi.perspective == "Financeira"
    assert kpi.metric_type == "quantidade"
    assert kpi.target_value == "> 30%"
    assert kpi.measurement_frequency == "mensal"


def test_kpi_definition_invalid_name_too_short():
    """TESTE 9: KPIDefinition invalido - nome muito curto (<10 chars)."""
    with pytest.raises(ValidationError, match="at least 10 characters"):
        KPIDefinition(
            name="ARR",  # Apenas 3 chars (minimo 10)
            description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
            perspective="Financeira",
            metric_type="quantidade",
            target_value="> 30%",
            measurement_frequency="mensal",
            data_source="ERP financeiro",
        )


def test_kpi_definition_invalid_name_empty():
    """TESTE 10: KPIDefinition invalido - nome vazio."""
    with pytest.raises(ValidationError, match="Nome do KPI nao pode ser vazio"):
        KPIDefinition(
            name="          ",  # Apenas espacos
            description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
            perspective="Financeira",
            metric_type="quantidade",
            target_value="> 30%",
            measurement_frequency="mensal",
            data_source="ERP financeiro",
        )


def test_kpi_definition_invalid_description_too_short():
    """TESTE 11: KPIDefinition invalido - descricao muito curta (<50 chars)."""
    with pytest.raises(ValidationError, match="at least 50 characters"):
        KPIDefinition(
            name="Crescimento ARR",
            description="Mede ARR",  # Apenas 9 chars (minimo 50)
            perspective="Financeira",
            metric_type="quantidade",
            target_value="> 30%",
            measurement_frequency="mensal",
            data_source="ERP financeiro",
        )


def test_kpi_definition_invalid_perspective():
    """TESTE 12: KPIDefinition invalido - perspectiva invalida."""
    with pytest.raises(ValidationError, match="Input should be"):
        KPIDefinition(
            name="Crescimento de Receita Recorrente",
            description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
            perspective="Marketing",  # type: ignore  # Invalida (permitidas: Financeira, Clientes, Processos Internos, Aprendizado e Crescimento)
            metric_type="quantidade",
            target_value="> 30%",
            measurement_frequency="mensal",
            data_source="ERP financeiro",
        )


def test_kpi_definition_invalid_metric_type():
    """TESTE 13: KPIDefinition invalido - metric_type invalido."""
    with pytest.raises(ValidationError, match="Input should be"):
        KPIDefinition(
            name="Crescimento de Receita Recorrente",
            description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
            perspective="Financeira",
            metric_type="percentual",  # type: ignore  # Invalido (permitidos: quantidade, qualidade, tempo, custo)
            target_value="> 30%",
            measurement_frequency="mensal",
            data_source="ERP financeiro",
        )


def test_kpi_definition_invalid_measurement_frequency():
    """TESTE 14: KPIDefinition invalido - frequencia invalida."""
    with pytest.raises(ValidationError, match="Input should be"):
        KPIDefinition(
            name="Crescimento de Receita Recorrente",
            description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
            perspective="Financeira",
            metric_type="quantidade",
            target_value="> 30%",
            measurement_frequency="bimestral",  # type: ignore  # Invalido (permitidos: diario, semanal, mensal, trimestral, anual)
            data_source="ERP financeiro",
        )


def test_kpi_framework_valid():
    """TESTE 15: KPIFramework valido com 2-8 KPIs por perspectiva."""
    kpi1 = KPIDefinition(
        name="Crescimento de Receita Recorrente ARR completo",
        description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
        perspective="Financeira",
        metric_type="quantidade",
        target_value="> 30%",
        measurement_frequency="mensal",
        data_source="ERP financeiro",
    )

    kpi2 = KPIDefinition(
        name="EBITDA Margin percentual de lucro operacional",
        description="Mede margem de lucro operacional em relacao a receita total",
        perspective="Financeira",
        metric_type="qualidade",
        target_value="> 25%",
        measurement_frequency="trimestral",
        data_source="Sistema contabil",
    )

    kpi3 = KPIDefinition(
        name="Customer Satisfaction Score CSAT pesquisa clientes",
        description="Mede nivel de satisfacao dos clientes atraves de pesquisas pos-atendimento",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 85%",
        measurement_frequency="mensal",
        data_source="Plataforma de pesquisas",
    )

    kpi4 = KPIDefinition(
        name="Net Promoter Score NPS indicador lealdade",
        description="Mede lealdade e propensao a recomendar a empresa para outros clientes",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 50",
        measurement_frequency="trimestral",
        data_source="Pesquisa NPS automatizada",
    )

    kpi5 = KPIDefinition(
        name="Lead Time medio de processos operacionais criticos",
        description="Mede tempo medio desde inicio ate conclusao dos processos operacionais",
        perspective="Processos Internos",
        metric_type="tempo",
        target_value="< 5 dias",
        measurement_frequency="semanal",
        data_source="Sistema de workflow",
    )

    kpi6 = KPIDefinition(
        name="Taxa de Defeitos em Processos percentual erros",
        description="Mede percentual de erros ou falhas em processos operacionais criticos",
        perspective="Processos Internos",
        metric_type="qualidade",
        target_value="< 2%",
        measurement_frequency="mensal",
        data_source="Sistema de qualidade",
    )

    kpi7 = KPIDefinition(
        name="Horas de Treinamento por Funcionario media anual",
        description="Mede numero medio de horas de capacitacao investidas por colaborador",
        perspective="Aprendizado e Crescimento",
        metric_type="quantidade",
        target_value="> 40 horas/ano",
        measurement_frequency="trimestral",
        data_source="Sistema de RH",
    )

    kpi8 = KPIDefinition(
        name="Employee Engagement Score indice engajamento equipes",
        description="Mede nivel de engajamento e satisfacao dos colaboradores com a empresa",
        perspective="Aprendizado e Crescimento",
        metric_type="qualidade",
        target_value="> 80%",
        measurement_frequency="trimestral",  # Corrigido: semestral nao existe no schema
        data_source="Pesquisa de clima organizacional",
    )

    framework = KPIFramework(
        financial_kpis=[kpi1, kpi2],
        customer_kpis=[kpi3, kpi4],
        process_kpis=[kpi5, kpi6],
        learning_kpis=[kpi7, kpi8],
    )

    assert framework.total_kpis() == 8
    assert len(framework.financial_kpis) == 2
    assert len(framework.customer_kpis) == 2
    assert len(framework.process_kpis) == 2
    assert len(framework.learning_kpis) == 2


def test_kpi_framework_invalid_too_few_kpis_per_perspective():
    """TESTE 16: KPIFramework invalido - perspectiva com <2 KPIs."""
    kpi1 = KPIDefinition(
        name="Crescimento de Receita Recorrente ARR completo",
        description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
        perspective="Financeira",
        metric_type="quantidade",
        target_value="> 30%",
        measurement_frequency="mensal",
        data_source="ERP financeiro",
    )

    kpi2 = KPIDefinition(
        name="Customer Satisfaction Score CSAT pesquisa clientes",
        description="Mede nivel de satisfacao dos clientes atraves de pesquisas pos-atendimento",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 85%",
        measurement_frequency="mensal",
        data_source="Plataforma de pesquisas",
    )

    kpi3 = KPIDefinition(
        name="Net Promoter Score NPS indicador lealdade",
        description="Mede lealdade e propensao a recomendar a empresa para outros clientes",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 50",
        measurement_frequency="trimestral",
        data_source="Pesquisa NPS automatizada",
    )

    kpi4 = KPIDefinition(
        name="Lead Time medio de processos operacionais criticos",
        description="Mede tempo medio desde inicio ate conclusao dos processos operacionais",
        perspective="Processos Internos",
        metric_type="tempo",
        target_value="< 5 dias",
        measurement_frequency="semanal",
        data_source="Sistema de workflow",
    )

    kpi5 = KPIDefinition(
        name="Taxa de Defeitos em Processos percentual erros",
        description="Mede percentual de erros ou falhas em processos operacionais criticos",
        perspective="Processos Internos",
        metric_type="qualidade",
        target_value="< 2%",
        measurement_frequency="mensal",
        data_source="Sistema de qualidade",
    )

    kpi6 = KPIDefinition(
        name="Horas de Treinamento por Funcionario media anual",
        description="Mede numero medio de horas de capacitacao investidas por colaborador",
        perspective="Aprendizado e Crescimento",
        metric_type="quantidade",
        target_value="> 40 horas/ano",
        measurement_frequency="trimestral",
        data_source="Sistema de RH",
    )

    kpi7 = KPIDefinition(
        name="Employee Engagement Score indice engajamento equipes",
        description="Mede nivel de engajamento e satisfacao dos colaboradores com a empresa",
        perspective="Aprendizado e Crescimento",
        metric_type="qualidade",
        target_value="> 80%",
        measurement_frequency="trimestral",  # Corrigido: semestral nao existe no schema
        data_source="Pesquisa de clima organizacional",
    )

    with pytest.raises(ValidationError, match="at least 2 items"):
        KPIFramework(
            financial_kpis=[kpi1],  # Apenas 1 KPI (minimo 2)
            customer_kpis=[kpi2, kpi3],
            process_kpis=[kpi4, kpi5],
            learning_kpis=[kpi6, kpi7],
        )


def test_kpi_framework_invalid_wrong_perspective():
    """TESTE 17: KPIFramework invalido - KPI em perspectiva errada."""
    kpi_financeira = KPIDefinition(
        name="Crescimento de Receita Recorrente ARR completo",
        description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
        perspective="Financeira",
        metric_type="quantidade",
        target_value="> 30%",
        measurement_frequency="mensal",
        data_source="ERP financeiro",
    )

    kpi_financeira2 = KPIDefinition(
        name="EBITDA Margin percentual de lucro operacional",
        description="Mede margem de lucro operacional em relacao a receita total",
        perspective="Financeira",
        metric_type="qualidade",
        target_value="> 25%",
        measurement_frequency="trimestral",
        data_source="Sistema contabil",
    )

    kpi_clientes = KPIDefinition(
        name="Customer Satisfaction Score CSAT pesquisa clientes",
        description="Mede nivel de satisfacao dos clientes atraves de pesquisas pos-atendimento",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 85%",
        measurement_frequency="mensal",
        data_source="Plataforma de pesquisas",
    )

    kpi_clientes2 = KPIDefinition(
        name="Net Promoter Score NPS indicador lealdade",
        description="Mede lealdade e propensao a recomendar a empresa para outros clientes",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 50",
        measurement_frequency="trimestral",
        data_source="Pesquisa NPS automatizada",
    )

    kpi_processos = KPIDefinition(
        name="Lead Time medio de processos operacionais criticos",
        description="Mede tempo medio desde inicio ate conclusao dos processos operacionais",
        perspective="Processos Internos",
        metric_type="tempo",
        target_value="< 5 dias",
        measurement_frequency="semanal",
        data_source="Sistema de workflow",
    )

    kpi_processos2 = KPIDefinition(
        name="Taxa de Defeitos em Processos percentual erros",
        description="Mede percentual de erros ou falhas em processos operacionais criticos",
        perspective="Processos Internos",
        metric_type="qualidade",
        target_value="< 2%",
        measurement_frequency="mensal",
        data_source="Sistema de qualidade",
    )

    kpi_aprendizado = KPIDefinition(
        name="Horas de Treinamento por Funcionario media anual",
        description="Mede numero medio de horas de capacitacao investidas por colaborador",
        perspective="Aprendizado e Crescimento",
        metric_type="quantidade",
        target_value="> 40 horas/ano",
        measurement_frequency="trimestral",
        data_source="Sistema de RH",
    )

    kpi_aprendizado2 = KPIDefinition(
        name="Employee Engagement Score indice engajamento equipes",
        description="Mede nivel de engajamento e satisfacao dos colaboradores com a empresa",
        perspective="Aprendizado e Crescimento",
        metric_type="qualidade",
        target_value="> 80%",
        measurement_frequency="trimestral",  # Corrigido: semestral nao existe no schema
        data_source="Pesquisa de clima organizacional",
    )

    with pytest.raises(
        ValidationError, match="financial_kpis deve conter apenas KPIs da perspectiva 'Financeira'"
    ):
        KPIFramework(
            financial_kpis=[kpi_financeira, kpi_clientes],  # kpi_clientes em lista errada!
            customer_kpis=[kpi_clientes2, kpi_financeira2],  # Tambem invertido
            process_kpis=[kpi_processos, kpi_processos2],
            learning_kpis=[kpi_aprendizado, kpi_aprendizado2],
        )


def test_kpi_framework_by_perspective_method():
    """TESTE 18: KPIFramework.by_perspective() retorna KPIs corretos."""
    kpi1 = KPIDefinition(
        name="Crescimento de Receita Recorrente ARR completo",
        description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
        perspective="Financeira",
        metric_type="quantidade",
        target_value="> 30%",
        measurement_frequency="mensal",
        data_source="ERP financeiro",
    )

    kpi2 = KPIDefinition(
        name="EBITDA Margin percentual de lucro operacional",
        description="Mede margem de lucro operacional em relacao a receita total",
        perspective="Financeira",
        metric_type="qualidade",
        target_value="> 25%",
        measurement_frequency="trimestral",
        data_source="Sistema contabil",
    )

    kpi3 = KPIDefinition(
        name="Customer Satisfaction Score CSAT pesquisa clientes",
        description="Mede nivel de satisfacao dos clientes atraves de pesquisas pos-atendimento",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 85%",
        measurement_frequency="mensal",
        data_source="Plataforma de pesquisas",
    )

    kpi4 = KPIDefinition(
        name="Net Promoter Score NPS indicador lealdade",
        description="Mede lealdade e propensao a recomendar a empresa para outros clientes",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 50",
        measurement_frequency="trimestral",
        data_source="Pesquisa NPS automatizada",
    )

    kpi5 = KPIDefinition(
        name="Lead Time medio de processos operacionais criticos",
        description="Mede tempo medio desde inicio ate conclusao dos processos operacionais",
        perspective="Processos Internos",
        metric_type="tempo",
        target_value="< 5 dias",
        measurement_frequency="semanal",
        data_source="Sistema de workflow",
    )

    kpi6 = KPIDefinition(
        name="Taxa de Defeitos em Processos percentual erros",
        description="Mede percentual de erros ou falhas em processos operacionais criticos",
        perspective="Processos Internos",
        metric_type="qualidade",
        target_value="< 2%",
        measurement_frequency="mensal",
        data_source="Sistema de qualidade",
    )

    kpi7 = KPIDefinition(
        name="Horas de Treinamento por Funcionario media anual",
        description="Mede numero medio de horas de capacitacao investidas por colaborador",
        perspective="Aprendizado e Crescimento",
        metric_type="quantidade",
        target_value="> 40 horas/ano",
        measurement_frequency="trimestral",
        data_source="Sistema de RH",
    )

    kpi8 = KPIDefinition(
        name="Employee Engagement Score indice engajamento equipes",
        description="Mede nivel de engajamento e satisfacao dos colaboradores com a empresa",
        perspective="Aprendizado e Crescimento",
        metric_type="qualidade",
        target_value="> 80%",
        measurement_frequency="trimestral",  # Corrigido: semestral nao existe no schema
        data_source="Pesquisa de clima organizacional",
    )

    framework = KPIFramework(
        financial_kpis=[kpi1, kpi2],
        customer_kpis=[kpi3, kpi4],
        process_kpis=[kpi5, kpi6],
        learning_kpis=[kpi7, kpi8],
    )

    # Testar by_perspective para cada perspectiva
    financial_kpis = framework.by_perspective("Financeira")
    assert len(financial_kpis) == 2
    assert all(kpi.perspective == "Financeira" for kpi in financial_kpis)

    customer_kpis = framework.by_perspective("Clientes")
    assert len(customer_kpis) == 2
    assert all(kpi.perspective == "Clientes" for kpi in customer_kpis)

    process_kpis = framework.by_perspective("Processos Internos")
    assert len(process_kpis) == 2
    assert all(kpi.perspective == "Processos Internos" for kpi in process_kpis)

    learning_kpis = framework.by_perspective("Aprendizado e Crescimento")
    assert len(learning_kpis) == 2
    assert all(kpi.perspective == "Aprendizado e Crescimento" for kpi in learning_kpis)


def test_kpi_framework_summary_method():
    """TESTE 19: KPIFramework.summary() retorna texto formatado correto."""
    kpi1 = KPIDefinition(
        name="Crescimento de Receita Recorrente ARR completo",
        description="Mede crescimento percentual da receita recorrente em relacao ao periodo anterior",
        perspective="Financeira",
        metric_type="quantidade",
        target_value="> 30%",
        measurement_frequency="mensal",
        data_source="ERP financeiro",
    )

    kpi2 = KPIDefinition(
        name="EBITDA Margin percentual de lucro operacional",
        description="Mede margem de lucro operacional em relacao a receita total",
        perspective="Financeira",
        metric_type="qualidade",
        target_value="> 25%",
        measurement_frequency="trimestral",
        data_source="Sistema contabil",
    )

    kpi3 = KPIDefinition(
        name="Customer Satisfaction Score CSAT pesquisa clientes",
        description="Mede nivel de satisfacao dos clientes atraves de pesquisas pos-atendimento",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 85%",
        measurement_frequency="mensal",
        data_source="Plataforma de pesquisas",
    )

    kpi4 = KPIDefinition(
        name="Net Promoter Score NPS indicador lealdade",
        description="Mede lealdade e propensao a recomendar a empresa para outros clientes",
        perspective="Clientes",
        metric_type="qualidade",
        target_value="> 50",
        measurement_frequency="trimestral",
        data_source="Pesquisa NPS automatizada",
    )

    kpi5 = KPIDefinition(
        name="Lead Time medio de processos operacionais criticos",
        description="Mede tempo medio desde inicio ate conclusao dos processos operacionais",
        perspective="Processos Internos",
        metric_type="tempo",
        target_value="< 5 dias",
        measurement_frequency="semanal",
        data_source="Sistema de workflow",
    )

    kpi6 = KPIDefinition(
        name="Taxa de Defeitos em Processos percentual erros",
        description="Mede percentual de erros ou falhas em processos operacionais criticos",
        perspective="Processos Internos",
        metric_type="qualidade",
        target_value="< 2%",
        measurement_frequency="mensal",
        data_source="Sistema de qualidade",
    )

    kpi7 = KPIDefinition(
        name="Horas de Treinamento por Funcionario media anual",
        description="Mede numero medio de horas de capacitacao investidas por colaborador",
        perspective="Aprendizado e Crescimento",
        metric_type="quantidade",
        target_value="> 40 horas/ano",
        measurement_frequency="trimestral",
        data_source="Sistema de RH",
    )

    kpi8 = KPIDefinition(
        name="Employee Engagement Score indice engajamento equipes",
        description="Mede nivel de engajamento e satisfacao dos colaboradores com a empresa",
        perspective="Aprendizado e Crescimento",
        metric_type="qualidade",
        target_value="> 80%",
        measurement_frequency="trimestral",  # Corrigido: semestral nao existe no schema
        data_source="Pesquisa de clima organizacional",
    )

    framework = KPIFramework(
        financial_kpis=[kpi1, kpi2],
        customer_kpis=[kpi3, kpi4],
        process_kpis=[kpi5, kpi6],
        learning_kpis=[kpi7, kpi8],
    )

    summary = framework.summary()

    # Validar que summary contem informacoes chave
    assert "8 KPIs" in summary
    assert "Financeira: 2" in summary
    assert "Clientes: 2" in summary
    assert "Processos Internos: 2" in summary
    assert "Aprendizado e Crescimento: 2" in summary
