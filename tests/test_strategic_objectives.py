"""Testes unitarios para Strategic Objectives Tool.

Valida:
- Criacao e inicializacao de StrategicObjectivesTool
- Definicao de objetivos SMART com/sem RAG
- Vinculacao com KPIs existentes
- Validacao de schemas (StrategicObjective + StrategicObjectivesFramework)
- Balanceamento entre perspectivas BSC
- Tratamento de erros (LLM failures, validacao)

Created: 2025-10-19 (FASE 3.5)
Coverage target: 70%+
"""

from __future__ import annotations

from itertools import cycle
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
    StrategicObjective,
    StrategicObjectivesFramework,
)
from src.tools.strategic_objectives import StrategicObjectivesTool

if TYPE_CHECKING:
    pass


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock LLM que retorna lista de StrategicObjective valida usando itertools.cycle.

    Usa itertools.cycle para retornar objetivos com perspectiva correta sequencialmente:
    Financeira -> Clientes -> Processos Internos -> Aprendizado e Crescimento

    Pattern validado Sessao 19 (KPI Definer mock).
    """
    llm = MagicMock(spec=["invoke", "with_structured_output"])

    # Simula structured output que retorna lista de objetivos
    from pydantic import BaseModel

    class ObjectivesListOutput(BaseModel):
        objectives: list[dict]

    # Define objetivos mock para cada perspectiva (2 objetivos por perspectiva)
    objectives_by_perspective = {
        "Financeira": [
            {
                "name": "Aumentar rentabilidade sustentavel de longo prazo",
                "description": (
                    "Aumentar margem EBITDA de 15% para 20% em 12 meses atraves de "
                    "otimizacao de custos operacionais e crescimento de receita recorrente, "
                    "mantendo qualidade e satisfacao dos clientes"
                ),
                "perspective": "Financeira",
                "timeframe": "12 meses",
                "success_criteria": [
                    "Margem EBITDA atingir 20% ou superior ao final de 12 meses",
                    "Crescimento de receita recorrente (ARR) >= 15% year-over-year",
                ],
                "related_kpis": ["Margem EBITDA", "Crescimento ARR"],
                "priority": "Alta",
                "dependencies": [],
            },
            {
                "name": "Reduzir custos operacionais mantendo qualidade",
                "description": (
                    "Reduzir custos operacionais em 10% nos proximos 18 meses atraves "
                    "de automacao de processos manuais e renegociacao de contratos com "
                    "fornecedores, sem impactar qualidade de produtos/servicos"
                ),
                "perspective": "Financeira",
                "timeframe": "18 meses",
                "success_criteria": [
                    "Reducao de custos operacionais >= 10% vs baseline atual",
                    "Manutencao de indicadores de qualidade (NPS >= 70, churn < 5%)",
                ],
                "related_kpis": ["Custos Operacionais", "NPS"],
                "priority": "Media",
                "dependencies": [],
            },
        ],
        "Clientes": [
            {
                "name": "Atingir excelencia em experiencia do cliente",
                "description": (
                    "Elevar Net Promoter Score (NPS) de 60 para 75 pontos em 18 meses "
                    "atraves de melhorias continuas na jornada do cliente, treinamento "
                    "de equipe de atendimento e personalizacao de servicos"
                ),
                "perspective": "Clientes",
                "timeframe": "18 meses",
                "success_criteria": [
                    "NPS (Net Promoter Score) atingir 75 pontos ou superior",
                    "Taxa de resolucao no primeiro contato >= 80%",
                ],
                "related_kpis": ["NPS", "Taxa Resolucao Primeiro Contato"],
                "priority": "Alta",
                "dependencies": [],
            },
            {
                "name": "Aumentar retencao e fidelizacao de clientes",
                "description": (
                    "Reduzir taxa de churn de 8% para 4% em 12 meses atraves de "
                    "programa de sucesso do cliente, melhorias no onboarding e "
                    "implementacao de programa de fidelidade customizado"
                ),
                "perspective": "Clientes",
                "timeframe": "12 meses",
                "success_criteria": [
                    "Taxa de churn mensal <= 4% (target final)",
                    "Customer Lifetime Value (LTV) aumentar em 25%",
                ],
                "related_kpis": ["Taxa Churn", "Customer Lifetime Value"],
                "priority": "Alta",
                "dependencies": [],
            },
        ],
        "Processos Internos": [
            {
                "name": "Otimizar eficiencia operacional end-to-end",
                "description": (
                    "Reduzir lead time de desenvolvimento de 6 para 3 semanas em 12 meses "
                    "atraves de implementacao de metodologias ageis (Scrum/Kanban), "
                    "automacao de testes e CI/CD pipeline robusto"
                ),
                "perspective": "Processos Internos",
                "timeframe": "12 meses",
                "success_criteria": [
                    "Lead time medio de desenvolvimento <= 3 semanas",
                    "Taxa de automacao de testes >= 80% da cobertura",
                ],
                "related_kpis": ["Lead Time Desenvolvimento", "Cobertura Testes"],
                "priority": "Alta",
                "dependencies": [],
            },
            {
                "name": "Implementar cultura de melhoria continua",
                "description": (
                    "Estabelecer programa estruturado de kaizen com 100% das areas "
                    "operacionais participando ativamente nos proximos 18 meses, "
                    "gerando minimo de 50 melhorias implementadas por trimestre"
                ),
                "perspective": "Processos Internos",
                "timeframe": "18 meses",
                "success_criteria": [
                    "100% das areas operacionais participam de ciclos kaizen trimestrais",
                    "Minimo de 50 melhorias implementadas por trimestre (target médio)",
                ],
                "related_kpis": ["Taxa Participacao Kaizen", "Melhorias Implementadas"],
                "priority": "Media",
                "dependencies": [],
            },
        ],
        "Aprendizado e Crescimento": [
            {
                "name": "Atingir taxa de retencao de talentos sustentavel",
                "description": (
                    "Elevar taxa de retencao de funcionarios de 80% para 90% em 18 meses "
                    "atraves de programa de desenvolvimento de carreiras, plano de "
                    "remuneracao competitivo e cultura organizacional focada em bem-estar"
                ),
                "perspective": "Aprendizado e Crescimento",
                "timeframe": "18 meses",
                "success_criteria": [
                    "Taxa de retencao de funcionarios >= 90% anualmente",
                    "Employee Net Promoter Score (eNPS) >= 60 pontos",
                ],
                "related_kpis": ["Taxa Retencao Funcionarios", "eNPS"],
                "priority": "Alta",
                "dependencies": [],
            },
            {
                "name": "Desenvolver competencias criticas para crescimento",
                "description": (
                    "Capacitar 100% dos funcionarios em competencias estrategicas "
                    "(digital, lideranca, inovacao) atraves de programa de treinamento "
                    "estruturado de 40 horas/ano por colaborador nos proximos 12 meses"
                ),
                "perspective": "Aprendizado e Crescimento",
                "timeframe": "12 meses",
                "success_criteria": [
                    "100% dos funcionarios completam minimo 40 horas de treinamento/ano",
                    "Avaliacao de competencias estrategicas media >= 4.0 (escala 1-5)",
                ],
                "related_kpis": ["Horas Treinamento por Funcionario", "Avaliacao Competencias"],
                "priority": "Media",
                "dependencies": [],
            },
        ],
    }

    # SOLUCAO: itertools.cycle para retornar perspectivas corretas sequencialmente
    # Tool chama: Financeira -> Clientes -> Processos -> Aprendizado
    perspective_order = [
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento",
    ]
    perspective_cycle = cycle(perspective_order)

    def mock_invoke_side_effect(prompt: str):
        """Retorna objetivos da proxima perspectiva na sequencia."""
        perspective = next(perspective_cycle)
        objectives = objectives_by_perspective[perspective]
        return ObjectivesListOutput(objectives=objectives)

    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.side_effect = mock_invoke_side_effect
    llm.with_structured_output.return_value = mock_structured_llm
    return llm


@pytest.fixture
def valid_company_info() -> CompanyInfo:
    """Fixture com CompanyInfo valido."""
    return CompanyInfo(
        name="TechCorp Solutions",
        sector="Tecnologia",
        industry="Software as a Service",
        size="média",
        founded_year=2018,
    )


@pytest.fixture
def valid_strategic_context() -> str:
    """Fixture com contexto estrategico valido (50+ chars)."""
    return (
        "Escalar operacoes mantendo qualidade de servico e satisfacao dos clientes "
        "em mercado competitivo de tecnologia B2B SaaS"
    )


@pytest.fixture
def valid_diagnostic_result() -> CompleteDiagnostic:
    """Fixture com CompleteDiagnostic valido (4 perspectivas BSC)."""
    financial_diag = DiagnosticResult(
        perspective="Financeira",
        current_state=(
            "Receita em crescimento acelerado de 40% YoY mas margens EBITDA comprimidas "
            "em 15% devido a custos operacionais elevados e falta de visibilidade detalhada "
            "de rentabilidade por produto e cliente, limitando decisoes estrategicas precisas"
        ),
        gaps=[
            "Margens EBITDA baixas (15% vs target 20%)",
            "Falta visibilidade de custos por produto",
            "CAC (Customer Acquisition Cost) alto",
        ],
        opportunities=[
            "Implementar Activity-Based Costing para visibilidade custos",
            "Otimizar investimentos marketing focando canais com ROI > 3x",
        ],
        priority="HIGH",
    )

    customer_diag = DiagnosticResult(
        perspective="Clientes",
        current_state=(
            "NPS (Net Promoter Score) em nivel bom de 60 pontos mas taxa de churn elevada "
            "de 8% mensal especialmente em segmento SMB, indicando problemas de retencao "
            "e onboarding que impactam crescimento sustentavel e LTV (Lifetime Value) clientes"
        ),
        gaps=[
            "Taxa churn mensal de 8% vs target 4%",
            "NPS 60 pontos vs target 75 pontos",
            "Customer Lifetime Value (LTV) baixo R$ 80K vs target R$ 100K",
        ],
        opportunities=[
            "Implementar programa Customer Success dedicado para SMB",
            "Melhorar processo onboarding com automacao e personalizacao",
        ],
        priority="HIGH",
    )

    process_diag = DiagnosticResult(
        perspective="Processos Internos",
        current_state=(
            "Processos de desenvolvimento de software e operacoes predominantemente manuais "
            "gerando lead time elevado de 6 semanas e retrabalho frequente, limitando agilidade "
            "de time-to-market e aumentando custos operacionais desnecessariamente"
        ),
        gaps=[
            "Lead time desenvolvimento 6 semanas vs target 3 semanas",
            "Taxa automacao de testes baixa 40% vs target 80%",
            "Retrabalho frequente por falta QA automatizado",
        ],
        opportunities=[
            "Implementar metodologias ageis (Scrum/Kanban) e CI/CD",
            "Automacao de testes unitarios e integracao (target 80% cobertura)",
        ],
        priority="MEDIUM",
    )

    learning_diag = DiagnosticResult(
        perspective="Aprendizado e Crescimento",
        current_state=(
            "Turnover de funcionarios elevado em 20% anual especialmente em equipes tecnicas "
            "e comerciais devido a falta de programa estruturado de desenvolvimento de carreira "
            "e remuneracao nao competitiva vs mercado, impactando produtividade e continuidade"
        ),
        gaps=[
            "Turnover anual 20% vs target 10%",
            "Falta programa estruturado de desenvolvimento carreira",
            "Remuneracao 10-15% abaixo da media de mercado",
        ],
        opportunities=[
            "Criar academia interna de treinamento e certificacoes",
            "Revisar politica remuneracao alinhando com mercado",
        ],
        priority="MEDIUM",
    )

    return CompleteDiagnostic(
        financial=financial_diag,
        customer=customer_diag,
        process=process_diag,
        learning=learning_diag,
        recommendations=[
            Recommendation(
                title="Implementar metodologias ageis e automacao de processos",
                description=(
                    "Reduzir lead time de desenvolvimento e melhorar time-to-market "
                    "atraves de Scrum, Kanban, CI/CD e automacao de testes unitarios, "
                    "aumentando produtividade da equipe e qualidade do software"
                ),
                impact="HIGH",
                effort="MEDIUM",
                priority="HIGH",
                timeframe="6-12 meses",
                next_steps=[
                    "Contratar Scrum Master experiente",
                    "Treinar equipe em metodologias ageis",
                    "Implementar CI/CD pipeline robusto",
                ],
            ),
            Recommendation(
                title="Criar programa estruturado de retencao de talentos",
                description=(
                    "Reduzir rotatividade atraves de plano de carreira claro, remuneracao "
                    "competitiva e cultura organizacional focada em bem-estar e desenvolvimento "
                    "continuo dos funcionarios, aumentando engajamento e produtividade"
                ),
                impact="HIGH",
                effort="MEDIUM",
                priority="HIGH",
                timeframe="12-18 meses",
                next_steps=[
                    "Mapear competencias e expectativas de carreira",
                    "Revisar politica de remuneracao vs mercado",
                    "Implementar programa de desenvolvimento continuo",
                ],
            ),
            Recommendation(
                title="Implementar Activity-Based Costing para visibilidade custos",
                description=(
                    "Substituir sistema tradicional de custos por ABC para aumentar visibilidade "
                    "de rentabilidade por produto, cliente e canal, permitindo decisoes estrategicas "
                    "baseadas em dados precisos de margem e lucratividade real"
                ),
                impact="HIGH",
                effort="MEDIUM",
                priority="HIGH",
                timeframe="6-9 meses",
                next_steps=[
                    "Contratar consultor especializado em ABC Costing",
                    "Mapear processos e atividades atuais (2 meses)",
                    "Pilotar ABC em 1 linha de produto (3 meses)",
                ],
            ),
        ],
        executive_summary=(
            "TechCorp Solutions esta em fase de crescimento acelerado com receita crescendo "
            "40% YoY mas enfrenta desafios criticos de escalabilidade operacional, retencao "
            "de clientes (churn 8%) e talentos (turnover 20%) que podem limitar crescimento "
            "futuro se nao endereçados estrategicamente atraves de automacao de processos, "
            "melhorias em customer success e programa estruturado de retencao de talentos"
        ),
        next_phase="APPROVAL_PENDING",
    )


@pytest.fixture
def valid_kpi_framework() -> KPIFramework:
    """Fixture com KPIFramework valido (3 KPIs por perspectiva para testes vinculacao)."""
    return KPIFramework(
        financial_kpis=[
            KPIDefinition(
                name="Margem EBITDA",
                description=(
                    "Mede a margem de lucro operacional (EBITDA) em relacao a receita total, "
                    "indicando eficiencia operacional e rentabilidade antes de juros, impostos, "
                    "depreciacao e amortizacao"
                ),
                perspective="Financeira",
                metric_type="qualidade",
                target_value="> 20%",
                measurement_frequency="trimestral",
                data_source="Sistema contabil + balanco patrimonial",
                calculation_formula="(EBITDA / Receita_Total) * 100",
            ),
            KPIDefinition(
                name="Crescimento ARR",
                description=(
                    "Mede o crescimento percentual da receita recorrente anual "
                    "(ARR) em relacao ao periodo anterior, indicando expansao sustentavel do negocio"
                ),
                perspective="Financeira",
                metric_type="quantidade",
                target_value="> 15%",
                measurement_frequency="mensal",
                data_source="ERP financeiro + CRM (contratos recorrentes)",
                calculation_formula="((ARR_atual - ARR_anterior) / ARR_anterior) * 100",
            ),
            KPIDefinition(
                name="Custos Operacionais",
                description=(
                    "Mede os custos operacionais totais mensais incluindo pessoal, "
                    "infraestrutura, marketing e vendas, excluindo depreciacao e amortizacao"
                ),
                perspective="Financeira",
                metric_type="custo",
                target_value="< R$ 3 milhoes/mes",
                measurement_frequency="mensal",
                data_source="Sistema contabil + centro de custos",
                calculation_formula="Soma(Pessoal + Infra + Marketing + Vendas)",
            ),
        ],
        customer_kpis=[
            KPIDefinition(
                name="NPS Score (Net Promoter Score)",
                description=(
                    "Net Promoter Score mede a probabilidade de clientes recomendarem "
                    "a empresa, variando de -100 (todos detratores) a +100 (todos promotores)"
                ),
                perspective="Clientes",
                metric_type="qualidade",
                target_value=">= 75 pontos",
                measurement_frequency="trimestral",
                data_source="Pesquisa NPS automatizada (email + in-app)",
                calculation_formula="% Promotores (9-10) - % Detratores (0-6)",
            ),
            KPIDefinition(
                name="Taxa Churn",
                description=(
                    "Taxa de cancelamento de clientes (churn rate) mensal, indicando "
                    "eficacia de retencao e satisfacao geral com produtos/servicos"
                ),
                perspective="Clientes",
                metric_type="quantidade",
                target_value="<= 4%",
                measurement_frequency="mensal",
                data_source="CRM + plataforma de cobranca",
                calculation_formula="(Clientes_Cancelados / Clientes_Ativos_Inicio_Mes) * 100",
            ),
            KPIDefinition(
                name="Customer Lifetime Value",
                description=(
                    "Valor total de receita que um cliente gera durante todo relacionamento "
                    "com a empresa, indicando lucratividade de longo prazo por cliente"
                ),
                perspective="Clientes",
                metric_type="quantidade",
                target_value="> R$ 100.000",
                measurement_frequency="trimestral",
                data_source="CRM + financeiro (receita recorrente + upsells)",
                calculation_formula="Receita_Media_Mensal / Taxa_Churn_Mensal",
            ),
        ],
        process_kpis=[
            KPIDefinition(
                name="Lead Time Desenvolvimento",
                description=(
                    "Tempo medio entre inicio de desenvolvimento de uma feature e deploy "
                    "em producao, indicando agilidade e eficiencia do processo de desenvolvimento"
                ),
                perspective="Processos Internos",
                metric_type="quantidade",
                target_value="<= 3 semanas",
                measurement_frequency="semanal",
                data_source="Jira + GitHub + sistema CI/CD",
                calculation_formula="Soma(Deploy_Date - Start_Date) / Total_Features",
            ),
            KPIDefinition(
                name="Cobertura Testes",
                description=(
                    "Percentual de cobertura de testes automatizados (unitarios + integracao) "
                    "no codigo base, indicando qualidade e confiabilidade do software"
                ),
                perspective="Processos Internos",
                metric_type="qualidade",
                target_value=">= 80%",
                measurement_frequency="semanal",
                data_source="SonarQube + CI/CD pipeline",
                calculation_formula="(Linhas_Cobertas / Total_Linhas_Codigo) * 100",
            ),
            KPIDefinition(
                name="Taxa Participacao Kaizen",
                description=(
                    "Percentual de areas operacionais que participaram ativamente de ciclos "
                    "de kaizen (melhoria continua) no trimestre, indicando engajamento "
                    "e cultura de excelencia operacional"
                ),
                perspective="Processos Internos",
                metric_type="qualidade",
                target_value="100%",
                measurement_frequency="trimestral",
                data_source="Sistema de gestao de melhorias + planilha tracking",
                calculation_formula="(Areas_Participantes / Total_Areas_Operacionais) * 100",
            ),
        ],
        learning_kpis=[
            KPIDefinition(
                name="Taxa Retencao Funcionarios",
                description=(
                    "Percentual de funcionarios que permanecem na empresa ao longo de 12 meses, "
                    "indicando satisfacao, engajamento e eficacia de programas de retencao"
                ),
                perspective="Aprendizado e Crescimento",
                metric_type="qualidade",
                target_value=">= 90%",
                measurement_frequency="mensal",
                data_source="Sistema RH + folha de pagamento",
                calculation_formula="((Total_Funcionarios - Saidas_12_Meses) / Total_Funcionarios) * 100",
            ),
            KPIDefinition(
                name="eNPS Score (Employee Net Promoter Score)",
                description=(
                    "Employee Net Promoter Score mede a probabilidade de funcionarios "
                    "recomendarem a empresa como local de trabalho, indicando engajamento "
                    "e satisfacao da equipe"
                ),
                perspective="Aprendizado e Crescimento",
                metric_type="qualidade",
                target_value=">= 60 pontos",
                measurement_frequency="trimestral",
                data_source="Pesquisa eNPS interna anonima",
                calculation_formula="% Promotores (9-10) - % Detratores (0-6)",
            ),
            KPIDefinition(
                name="Horas Treinamento por Funcionario",
                description=(
                    "Media de horas de treinamento e desenvolvimento por funcionario anualmente, "
                    "indicando investimento em capacitacao e desenvolvimento de competencias"
                ),
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value=">= 40 horas/ano",
                measurement_frequency="trimestral",
                data_source="Plataforma LMS + planilha tracking treinamentos",
                calculation_formula="Soma(Horas_Treinamento_Total) / Total_Funcionarios",
            ),
        ],
    )


# ============================================================================
# TESTES - TOOL CREATION
# ============================================================================


def test_create_tool_without_rag(mock_llm):
    """Deve criar StrategicObjectivesTool sem RAG."""
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=False)

    assert tool.llm == mock_llm
    assert tool.use_rag is False
    assert tool.rag_agents is None


def test_create_tool_with_rag_but_no_agents(mock_llm):
    """Deve falhar ao criar tool com use_rag=True mas sem rag_agents."""
    with pytest.raises(ValueError, match="rag_agents obrigatorio quando use_rag=True"):
        StrategicObjectivesTool(llm=mock_llm, use_rag=True, rag_agents=None)


def test_create_tool_with_rag_and_agents(mock_llm):
    """Deve criar StrategicObjectivesTool com RAG e agents."""
    rag_agents = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=True, rag_agents=rag_agents)

    assert tool.llm == mock_llm
    assert tool.use_rag is True
    assert tool.rag_agents == rag_agents


# ============================================================================
# TESTES - DEFINE OBJECTIVES WORKFLOW
# ============================================================================


def test_define_objectives_without_rag(
    mock_llm, valid_company_info, valid_strategic_context, valid_diagnostic_result
):
    """Deve definir objetivos estrategicos sem RAG agents."""
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=False)

    framework = tool.define_objectives(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        diagnostic_result=valid_diagnostic_result,
    )

    # Validar retorno
    assert isinstance(framework, StrategicObjectivesFramework)
    assert framework.total_objectives() > 0

    # Validar perspectivas (2 objetivos por perspectiva = 8 total)
    assert len(framework.financial_objectives) == 2
    assert len(framework.customer_objectives) == 2
    assert len(framework.process_objectives) == 2
    assert len(framework.learning_objectives) == 2

    # Validar perspectivas corretas
    for obj in framework.financial_objectives:
        assert obj.perspective == "Financeira"
    for obj in framework.customer_objectives:
        assert obj.perspective == "Clientes"
    for obj in framework.process_objectives:
        assert obj.perspective == "Processos Internos"
    for obj in framework.learning_objectives:
        assert obj.perspective == "Aprendizado e Crescimento"


def test_define_objectives_with_rag(
    mock_llm, valid_company_info, valid_strategic_context, valid_diagnostic_result
):
    """Deve definir objetivos estrategicos com RAG agents (mocked)."""
    # Mock RAG agents
    mock_financial = MagicMock()
    mock_financial.invoke.return_value = {"output": "Conhecimento BSC financeiro..."}
    mock_customer = MagicMock()
    mock_customer.invoke.return_value = {"output": "Conhecimento BSC clientes..."}
    mock_process = MagicMock()
    mock_process.invoke.return_value = {"output": "Conhecimento BSC processos..."}
    mock_learning = MagicMock()
    mock_learning.invoke.return_value = {"output": "Conhecimento BSC aprendizado..."}

    rag_agents = (mock_financial, mock_customer, mock_process, mock_learning)

    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=True, rag_agents=rag_agents)

    framework = tool.define_objectives(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        diagnostic_result=valid_diagnostic_result,
    )

    # Validar retorno
    assert isinstance(framework, StrategicObjectivesFramework)
    assert framework.total_objectives() == 8  # 2 objetivos por perspectiva

    # Validar RAG agents foram chamados (1x cada)
    assert mock_financial.invoke.called
    assert mock_customer.invoke.called
    assert mock_process.invoke.called
    assert mock_learning.invoke.called


def test_define_objectives_with_existing_kpis_linkage(
    mock_llm,
    valid_company_info,
    valid_strategic_context,
    valid_diagnostic_result,
    valid_kpi_framework,
):
    """Deve definir objetivos e vincular com KPIs existentes."""
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=False)

    framework = tool.define_objectives(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        diagnostic_result=valid_diagnostic_result,
        existing_kpis=valid_kpi_framework,
    )

    # Validar retorno
    assert isinstance(framework, StrategicObjectivesFramework)
    assert framework.total_objectives() == 8

    # Validar vinculacao: todos objetivos devem ter related_kpis (mock configurado assim)
    objectives_with_kpis = framework.with_related_kpis()
    assert len(objectives_with_kpis) >= 4  # Pelo menos metade tem KPIs vinculados


def test_validates_company_info_required(
    mock_llm, valid_strategic_context, valid_diagnostic_result
):
    """Deve falhar se company_info nao fornecido."""
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=False)

    with pytest.raises(ValueError, match="company_info obrigatorio"):
        tool.define_objectives(
            company_info=None,
            strategic_context=valid_strategic_context,
            diagnostic_result=valid_diagnostic_result,
        )


def test_validates_strategic_context_required(
    mock_llm, valid_company_info, valid_diagnostic_result
):
    """Deve falhar se strategic_context nao fornecido ou vazio."""
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=False)

    with pytest.raises(ValueError, match="strategic_context obrigatorio"):
        tool.define_objectives(
            company_info=valid_company_info,
            strategic_context="   ",  # Apenas espacos
            diagnostic_result=valid_diagnostic_result,
        )


def test_validates_diagnostic_result_required(
    mock_llm, valid_company_info, valid_strategic_context
):
    """Deve falhar se diagnostic_result nao fornecido."""
    tool = StrategicObjectivesTool(llm=mock_llm, use_rag=False)

    with pytest.raises(ValueError, match="diagnostic_result obrigatorio"):
        tool.define_objectives(
            company_info=valid_company_info,
            strategic_context=valid_strategic_context,
            diagnostic_result=None,
        )


# ============================================================================
# TESTES - SCHEMA VALIDATION
# ============================================================================


def test_strategic_objective_validators():
    """Deve validar campos de StrategicObjective corretamente."""
    # Objetivo valido
    obj = StrategicObjective(
        name="Aumentar rentabilidade sustentavel",
        description=(
            "Aumentar margem EBITDA de 15% para 20% em 12 meses atraves de "
            "otimizacao de custos e crescimento de receita recorrente"
        ),
        perspective="Financeira",
        timeframe="12 meses",
        success_criteria=[
            "Margem EBITDA >= 20% ao final de 12 meses",
            "Crescimento receita recorrente >= 15% year-over-year",
        ],
        priority="Alta",
    )

    assert obj.name == "Aumentar rentabilidade sustentavel"
    assert obj.perspective == "Financeira"
    assert len(obj.success_criteria) == 2

    # name vazio deve falhar
    with pytest.raises(ValidationError):
        StrategicObjective(
            name="",
            description="Descricao valida com mais de 50 caracteres para passar validacao min_length",
            perspective="Financeira",
            timeframe="12 meses",
            success_criteria=["Criterio 1 com 20 caracteres", "Criterio 2 com 20 chars"],
        )

    # success_criteria com menos de 2 items deve falhar
    with pytest.raises(ValidationError):
        StrategicObjective(
            name="Objetivo valido",
            description="Descricao valida com mais de 50 caracteres para passar validacao min_length",
            perspective="Financeira",
            timeframe="12 meses",
            success_criteria=["Apenas um criterio com 20 caracteres"],  # Menos de 2
        )

    # success_criteria com criterio muito curto deve falhar
    with pytest.raises(ValidationError):
        StrategicObjective(
            name="Objetivo valido",
            description="Descricao valida com mais de 50 caracteres para passar validacao min_length",
            perspective="Financeira",
            timeframe="12 meses",
            success_criteria=[
                "Criterio 1 valido com mais de 20 caracteres",
                "Curto",  # Menos de 20 caracteres
            ],
        )


def test_strategic_objectives_framework_cross_perspective_validation():
    """Deve validar que objetivos estao nas perspectivas corretas."""
    obj_financeira = StrategicObjective(
        name="Objetivo financeiro valido",
        description="Descricao completa com mais de 50 caracteres para validacao Pydantic min_length",
        perspective="Financeira",
        timeframe="12 meses",
        success_criteria=[
            "Criterio 1 valido com 20 caracteres minimos",
            "Criterio 2 valido com 20 caracteres tambem",
        ],
    )

    obj_clientes = StrategicObjective(
        name="Objetivo clientes valido",
        description="Descricao completa com mais de 50 caracteres para validacao Pydantic min_length",
        perspective="Clientes",
        timeframe="12 meses",
        success_criteria=[
            "Criterio 1 valido com 20 caracteres minimos",
            "Criterio 2 valido com 20 caracteres tambem",
        ],
    )

    # Framework valido (objetivos nas perspectivas corretas)
    framework = StrategicObjectivesFramework(
        financial_objectives=[obj_financeira], customer_objectives=[obj_clientes]
    )

    assert len(framework.financial_objectives) == 1
    assert len(framework.customer_objectives) == 1

    # Framework invalido (objetivo perspectiva errada)
    with pytest.raises(
        ValidationError,
        match="customer_objectives deve conter apenas objetivos da perspectiva 'Clientes'",
    ):
        StrategicObjectivesFramework(
            financial_objectives=[],
            customer_objectives=[obj_financeira],  # Financeira em customer_objectives!
        )


def test_strategic_objectives_framework_methods():
    """Deve validar metodos uteis do StrategicObjectivesFramework."""
    obj1_fin = StrategicObjective(
        name="Obj financeiro 1",
        description="Descricao com 50+ caracteres para validacao Pydantic min_length obrigatoria",
        perspective="Financeira",
        timeframe="12 meses",
        success_criteria=["Criterio 1 com 20 chars", "Criterio 2 com 20 chars"],
        related_kpis=["EBITDA"],
        priority="Alta",
    )

    obj2_fin = StrategicObjective(
        name="Obj financeiro 2",
        description="Descricao com 50+ caracteres para validacao Pydantic min_length obrigatoria",
        perspective="Financeira",
        timeframe="18 meses",
        success_criteria=["Criterio A com 20 chars", "Criterio B com 20 chars"],
        priority="Média",
    )

    obj1_cust = StrategicObjective(
        name="Obj clientes 1",
        description="Descricao com 50+ caracteres para validacao Pydantic min_length obrigatoria",
        perspective="Clientes",
        timeframe="12 meses",
        success_criteria=["Criterio X com 20 chars", "Criterio Y com 20 chars"],
        related_kpis=["NPS", "Churn"],
        priority="Alta",
    )

    framework = StrategicObjectivesFramework(
        financial_objectives=[obj1_fin, obj2_fin], customer_objectives=[obj1_cust]
    )

    # total_objectives()
    assert framework.total_objectives() == 3

    # by_perspective()
    assert len(framework.by_perspective("Financeira")) == 2
    assert len(framework.by_perspective("Clientes")) == 1
    assert len(framework.by_perspective("Processos Internos")) == 0

    # by_priority()
    assert len(framework.by_priority("Alta")) == 2
    assert len(framework.by_priority("Media")) == 1
    assert len(framework.by_priority("Baixa")) == 0

    # with_related_kpis()
    assert len(framework.with_related_kpis()) == 2  # obj1_fin e obj1_cust tem KPIs

    # summary()
    summary = framework.summary()
    assert "3 objetivos estrategicos" in summary
    assert "Financeira: 2 objetivos" in summary
    assert "Clientes: 1 objetivos" in summary
    assert "Alta: 2 objetivos" in summary
    assert "Media: 1 objetivos" in summary
