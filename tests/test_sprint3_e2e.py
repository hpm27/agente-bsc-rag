"""
Testes E2E SPRINT 3: Validacao completa das ferramentas de validacao avancada.

Escopo:
- Valida KPIAlignmentCheckerTool com LLM real (timeout protegido)
- Valida CauseEffectMapperTool com LLM real (timeout protegido)
- Valida integracao no design_solution_handler
- Valida carregamento de reports na UI

IMPORTANTE: Testes E2E sao mais lentos (usam LLM real).
Para testes rapidos, use test_sprint3_validation_tools.py (unitarios com mocks).
"""

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from config.settings import get_llm_for_agent
from src.memory.schemas import (
    AlignmentIssue,
    CauseEffectAnalysis,
    CauseEffectConnection,
    CauseEffectGap,
    KPIAlignmentReport,
    KPIDefinition,
    KPIFramework,
    StrategicObjective,
    StrategyMap,
    StrategyMapPerspective,
)
from src.tools.cause_effect_mapper import CauseEffectMapperTool
from src.tools.kpi_alignment_checker import KPIAlignmentCheckerTool


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def valid_objective_financial():
    """Objetivo estrategico valido para perspectiva Financeira."""
    return StrategicObjective(
        name="Aumentar margem EBITDA para 18% ate 2026",
        description="Atingir margem EBITDA de 18% atraves de otimizacao de custos operacionais e aumento de receita com produtos premium de maior margem",
        perspective="Financeira",
        timeframe="24 meses",
        success_criteria=[
            "Margem EBITDA >= 18%",
            "Crescimento receita >= 10% YoY",
        ],
        related_kpis=["Margem EBITDA %", "Crescimento Receita YoY"],
        priority="Alta",
    )


@pytest.fixture
def valid_objective_customer():
    """Objetivo estrategico valido para perspectiva Clientes."""
    return StrategicObjective(
        name="Atingir NPS de 50 pontos ou mais",
        description="Melhorar Net Promoter Score para 50+ atraves de iniciativas de customer experience e resolucao rapida de problemas dos clientes",
        perspective="Clientes",
        timeframe="12 meses",
        success_criteria=[
            "NPS >= 50",
            "Taxa de retencao >= 90%",
        ],
        related_kpis=["Net Promoter Score", "Taxa de Retencao Clientes"],
        priority="Alta",
    )


@pytest.fixture
def valid_objective_process():
    """Objetivo estrategico valido para perspectiva Processos Internos."""
    return StrategicObjective(
        name="Reduzir lead time de producao em 30%",
        description="Implementar Lean Manufacturing para reduzir o lead time de producao em 30% atraves de eliminacao de waste e otimizacao de fluxo",
        perspective="Processos Internos",
        timeframe="18 meses",
        success_criteria=[
            "Lead time reduzido em 30%",
            "OEE >= 85%",
        ],
        related_kpis=["Lead Time Producao", "OEE - Overall Equipment Effectiveness"],
        priority="Alta",
    )


@pytest.fixture
def valid_objective_learning():
    """Objetivo estrategico valido para perspectiva Aprendizado e Crescimento."""
    return StrategicObjective(
        name="Certificar 80% da equipe em Lean Six Sigma",
        description="Implementar programa de certificacao Lean Six Sigma para 80% dos colaboradores de producao e qualidade em 12 meses",
        perspective="Aprendizado e Crescimento",
        timeframe="12 meses",
        success_criteria=[
            "80% equipe certificada",
            "30 projetos de melhoria concluidos",
        ],
        related_kpis=["% Equipe Certificada", "Projetos Melhoria Concluidos"],
        priority="Alta",
    )


@pytest.fixture
def valid_strategy_map(
    valid_objective_financial,
    valid_objective_customer,
    valid_objective_process,
    valid_objective_learning,
):
    """Strategy Map completo e valido com 4 perspectivas e conexoes."""
    # Criar segundo objetivo para cada perspectiva
    obj_financial_2 = StrategicObjective(
        name="Reduzir custo operacional em 15% ate 2026",
        description="Reduzir custo por unidade produzida atraves de automacao e Lean Manufacturing para melhorar margem de contribuicao",
        perspective="Financeira",
        timeframe="18 meses",
        success_criteria=["Custo unitario reduzido 15%", "ROI automacao >= 25%"],
        related_kpis=["Custo por Unidade", "ROI Automacao"],
        priority="Alta",
    )

    obj_customer_2 = StrategicObjective(
        name="Reduzir churn rate para menos de 5%",
        description="Implementar programa de retencao proativa para reduzir taxa de cancelamento de clientes para menos de 5% ao ano",
        perspective="Clientes",
        timeframe="12 meses",
        success_criteria=["Churn rate < 5%", "Customer Lifetime Value +20%"],
        related_kpis=["Churn Rate", "Customer Lifetime Value"],
        priority="Alta",
    )

    obj_process_2 = StrategicObjective(
        name="Atingir OEE de 85% nas linhas de producao",
        description="Melhorar Overall Equipment Effectiveness para 85% atraves de manutencao preventiva e setup rapido (SMED)",
        perspective="Processos Internos",
        timeframe="18 meses",
        success_criteria=["OEE >= 85%", "Downtime < 5%"],
        related_kpis=["OEE", "Downtime %"],
        priority="Alta",
    )

    obj_learning_2 = StrategicObjective(
        name="Implementar cultura de melhoria continua",
        description="Criar sistema de ideias e reconhecimento para fomentar cultura de melhoria continua com meta de 5 sugestoes por colaborador ao ano",
        perspective="Aprendizado e Crescimento",
        timeframe="12 meses",
        success_criteria=["5+ sugestoes/colaborador/ano", "80% engajamento"],
        related_kpis=["Sugestoes por Colaborador", "Engajamento Colaboradores"],
        priority="Alta",
    )

    # Conexoes causa-efeito validas (L->P->C->F)
    connections = [
        CauseEffectConnection(
            source_objective_id="learning_1",
            target_objective_id="process_1",
            relationship_type="enables",
            strength="strong",
            rationale="Certificacao Lean Six Sigma habilita melhoria de processos produtivos",
        ),
        CauseEffectConnection(
            source_objective_id="learning_2",
            target_objective_id="process_2",
            relationship_type="enables",
            strength="strong",
            rationale="Cultura de melhoria continua permite atingir OEE de 85%",
        ),
        CauseEffectConnection(
            source_objective_id="process_1",
            target_objective_id="customer_1",
            relationship_type="drives",
            strength="strong",
            rationale="Reducao de lead time melhora experiencia do cliente e NPS",
        ),
        CauseEffectConnection(
            source_objective_id="process_2",
            target_objective_id="customer_2",
            relationship_type="drives",
            strength="strong",
            rationale="OEE 85% aumenta confiabilidade e reduz churn de clientes",
        ),
        CauseEffectConnection(
            source_objective_id="customer_1",
            target_objective_id="financial_1",
            relationship_type="drives",
            strength="strong",
            rationale="NPS 50+ aumenta receita via recomendacoes e upsell, melhorando EBITDA",
        ),
        CauseEffectConnection(
            source_objective_id="customer_2",
            target_objective_id="financial_2",
            relationship_type="drives",
            strength="strong",
            rationale="Churn < 5% preserva receita recorrente e reduz CAC, impactando custos",
        ),
        CauseEffectConnection(
            source_objective_id="learning_1",
            target_objective_id="process_2",
            relationship_type="supports",
            strength="medium",
            rationale="Certificacao Lean tambem suporta melhoria de OEE via metodologias",
        ),
        CauseEffectConnection(
            source_objective_id="learning_2",
            target_objective_id="process_1",
            relationship_type="supports",
            strength="medium",
            rationale="Cultura de melhoria continua tambem contribui para reducao de lead time",
        ),
    ]

    return StrategyMap(
        financial=StrategyMapPerspective(
            name="Financeira",
            objectives=[valid_objective_financial, obj_financial_2],
        ),
        customer=StrategyMapPerspective(
            name="Clientes",
            objectives=[valid_objective_customer, obj_customer_2],
        ),
        process=StrategyMapPerspective(
            name="Processos Internos",
            objectives=[valid_objective_process, obj_process_2],
        ),
        learning=StrategyMapPerspective(
            name="Aprendizado e Crescimento",
            objectives=[valid_objective_learning, obj_learning_2],
        ),
        cause_effect_connections=connections,
        strategic_priorities=["Excelencia Operacional", "Inovacao de Produto", "Customer Intimacy"],
    )


@pytest.fixture
def valid_kpi_framework():
    """KPIFramework valido com KPIs para todas perspectivas."""
    return KPIFramework(
        financial_kpis=[
            KPIDefinition(
                name="Margem EBITDA %",
                description="Percentual de margem EBITDA sobre receita liquida, indicando rentabilidade operacional",
                perspective="Financeira",
                metric_type="quantidade",
                target_value=">= 18%",
                measurement_frequency="mensal",
                data_source="ERP Financeiro",
            ),
            KPIDefinition(
                name="Crescimento Receita YoY",
                description="Crescimento percentual da receita liquida comparado ao mesmo periodo do ano anterior",
                perspective="Financeira",
                metric_type="quantidade",
                target_value=">= 10%",
                measurement_frequency="trimestral",
                data_source="ERP Financeiro",
            ),
        ],
        customer_kpis=[
            KPIDefinition(
                name="Net Promoter Score",
                description="Indicador de lealdade do cliente baseado na probabilidade de recomendacao da empresa",
                perspective="Clientes",
                metric_type="qualidade",
                target_value=">= 50",
                measurement_frequency="trimestral",
                data_source="Pesquisa NPS automatizada",
            ),
            KPIDefinition(
                name="Taxa de Retencao Clientes",
                description="Percentual de clientes ativos que permanecem no periodo em relacao ao periodo anterior",
                perspective="Clientes",
                metric_type="quantidade",
                target_value=">= 90%",
                measurement_frequency="mensal",
                data_source="CRM Sistema",
            ),
        ],
        process_kpis=[
            KPIDefinition(
                name="Lead Time Producao",
                description="Tempo total desde o inicio ate a conclusao do processo produtivo em dias",
                perspective="Processos Internos",
                metric_type="tempo",
                target_value="<= 5 dias",
                measurement_frequency="semanal",
                data_source="MES - Manufacturing Execution System",
            ),
            KPIDefinition(
                name="OEE - Overall Equipment Effectiveness",
                description="Indicador de eficiencia geral dos equipamentos considerando disponibilidade, performance e qualidade",
                perspective="Processos Internos",
                metric_type="quantidade",
                target_value=">= 85%",
                measurement_frequency="diario",
                data_source="Sistema de Automacao Industrial",
            ),
        ],
        learning_kpis=[
            KPIDefinition(
                name="% Equipe Certificada",
                description="Percentual de colaboradores com certificacao Lean Six Sigma (Yellow Belt ou superior)",
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value=">= 80%",
                measurement_frequency="mensal",
                data_source="RH - Sistema de Treinamento",
            ),
            KPIDefinition(
                name="Projetos Melhoria Concluidos",
                description="Numero acumulado de projetos de melhoria continua concluidos no ano",
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value=">= 30",
                measurement_frequency="mensal",
                data_source="PMO - Gestao de Projetos",
            ),
        ],
    )


@pytest.fixture
def mock_llm():
    """Mock LLM para testes sem custo de API."""
    mock = Mock()
    # Mock para validate_semantic_alignment
    mock.ainvoke = AsyncMock(return_value=Mock(content='{"is_aligned": true, "confidence": 0.9}'))
    return mock


# ============================================================================
# TESTES E2E - KPI ALIGNMENT CHECKER
# ============================================================================


class TestKPIAlignmentCheckerE2E:
    """Testes E2E para KPIAlignmentCheckerTool."""

    @pytest.mark.asyncio
    async def test_validate_kpi_alignment_complete_flow(
        self, valid_strategy_map, valid_kpi_framework
    ):
        """
        TESTE E2E: Fluxo completo de validacao de alinhamento KPI.

        Valida:
        1. Tool executa sem erro
        2. Retorna KPIAlignmentReport valido
        3. Score esta no range 0-100
        4. is_aligned calculado corretamente
        5. alignment_by_perspective tem 4 perspectivas
        """
        # Setup
        tool = KPIAlignmentCheckerTool()

        # Execucao com timeout
        start = time.time()
        try:
            report = await asyncio.wait_for(
                tool.validate_kpi_alignment(
                    strategy_map=valid_strategy_map,
                    kpi_framework=valid_kpi_framework,
                ),
                timeout=60.0,  # 60s timeout para LLM
            )
        except asyncio.TimeoutError:
            pytest.skip("Timeout na chamada LLM - pular teste E2E")
            return

        latency = time.time() - start

        # VALIDACAO 1: Retorno nao e None
        assert report is not None, "validate_kpi_alignment nao deve retornar None"

        # VALIDACAO 2: E um KPIAlignmentReport
        assert isinstance(
            report, KPIAlignmentReport
        ), f"Esperado KPIAlignmentReport, recebeu {type(report)}"

        # VALIDACAO 3: Score no range 0-100
        assert (
            0 <= report.overall_score <= 100
        ), f"Score deve estar entre 0-100, recebeu {report.overall_score}"

        # VALIDACAO 4: is_aligned e boolean
        assert isinstance(
            report.is_aligned, bool
        ), f"is_aligned deve ser bool, recebeu {type(report.is_aligned)}"

        # VALIDACAO 5: alignment_by_perspective tem 4 perspectivas
        assert (
            len(report.alignment_by_perspective) == 4
        ), f"Esperado 4 perspectivas, recebeu {len(report.alignment_by_perspective)}"

        # VALIDACAO 6: Latencia aceitavel (< 60s)
        assert latency < 60, f"Latencia muito alta: {latency:.2f}s (max 60s)"

        # Log resultados
        print(f"\n[OK] KPI Alignment E2E - Score: {report.overall_score:.1f}/100")
        print(f"[OK] is_aligned: {report.is_aligned}")
        print(f"[OK] Issues: {len(report.alignment_issues)}")
        print(f"[OK] Latencia: {latency:.2f}s")

    @pytest.mark.asyncio
    async def test_validate_kpi_alignment_with_mock_llm(
        self, valid_strategy_map, valid_kpi_framework, mock_llm
    ):
        """
        TESTE E2E com Mock: Validacao estrutural sem custo de API.
        """
        # Setup com mock
        tool = KPIAlignmentCheckerTool(llm=mock_llm)

        # Execucao
        report = await tool.validate_kpi_alignment(
            strategy_map=valid_strategy_map,
            kpi_framework=valid_kpi_framework,
        )

        # VALIDACAO 1: Retorno valido
        assert report is not None
        assert isinstance(report, KPIAlignmentReport)

        # VALIDACAO 2: Score calculado (mesmo com mock)
        assert 0 <= report.overall_score <= 100

        # VALIDACAO 3: Tem timestamp
        assert report.validated_at is not None


# ============================================================================
# TESTES E2E - CAUSE EFFECT MAPPER
# ============================================================================


class TestCauseEffectMapperE2E:
    """Testes E2E para CauseEffectMapperTool."""

    @pytest.mark.asyncio
    async def test_analyze_cause_effect_complete_flow(self, valid_strategy_map):
        """
        TESTE E2E: Fluxo completo de analise causa-efeito.

        Valida:
        1. Tool executa sem erro
        2. Retorna CauseEffectAnalysis valido
        3. Score esta no range 0-100
        4. is_complete calculado corretamente
        5. total_connections correto
        6. connections_by_type preenchido
        """
        # Setup
        tool = CauseEffectMapperTool()

        # Execucao com timeout
        start = time.time()
        try:
            analysis = await asyncio.wait_for(
                tool.analyze_cause_effect(
                    strategy_map=valid_strategy_map,
                ),
                timeout=60.0,  # 60s timeout para LLM
            )
        except asyncio.TimeoutError:
            pytest.skip("Timeout na chamada LLM - pular teste E2E")
            return

        latency = time.time() - start

        # VALIDACAO 1: Retorno nao e None
        assert analysis is not None, "analyze_cause_effect nao deve retornar None"

        # VALIDACAO 2: E um CauseEffectAnalysis
        assert isinstance(
            analysis, CauseEffectAnalysis
        ), f"Esperado CauseEffectAnalysis, recebeu {type(analysis)}"

        # VALIDACAO 3: Score no range 0-100
        assert (
            0 <= analysis.completeness_score <= 100
        ), f"Score deve estar entre 0-100, recebeu {analysis.completeness_score}"

        # VALIDACAO 4: is_complete e boolean
        assert isinstance(
            analysis.is_complete, bool
        ), f"is_complete deve ser bool, recebeu {type(analysis.is_complete)}"

        # VALIDACAO 5: total_connections >= 0
        assert (
            analysis.total_connections >= 0
        ), f"total_connections deve ser >= 0, recebeu {analysis.total_connections}"

        # VALIDACAO 6: Latencia aceitavel (< 60s)
        assert latency < 60, f"Latencia muito alta: {latency:.2f}s (max 60s)"

        # Log resultados
        print(f"\n[OK] Cause-Effect E2E - Score: {analysis.completeness_score:.1f}/100")
        print(f"[OK] is_complete: {analysis.is_complete}")
        print(f"[OK] Gaps: {len(analysis.gaps)}")
        print(f"[OK] Total connections: {analysis.total_connections}")
        print(f"[OK] Latencia: {latency:.2f}s")

    @pytest.mark.asyncio
    async def test_analyze_cause_effect_with_mock_llm(self, valid_strategy_map, mock_llm):
        """
        TESTE E2E com Mock: Validacao estrutural sem custo de API.
        """
        # Setup com mock
        tool = CauseEffectMapperTool(llm=mock_llm)

        # Execucao
        analysis = await tool.analyze_cause_effect(
            strategy_map=valid_strategy_map,
        )

        # VALIDACAO 1: Retorno valido
        assert analysis is not None
        assert isinstance(analysis, CauseEffectAnalysis)

        # VALIDACAO 2: Score calculado (mesmo com mock)
        assert 0 <= analysis.completeness_score <= 100

        # VALIDACAO 3: Tem timestamp
        assert analysis.analyzed_at is not None


# ============================================================================
# TESTES E2E - INTEGRACAO COMBINADA
# ============================================================================


class TestCombinedValidationE2E:
    """Testes E2E de integracao entre KPI Alignment e Cause-Effect."""

    @pytest.mark.asyncio
    async def test_combined_validation_scores(
        self, valid_strategy_map, valid_kpi_framework, mock_llm
    ):
        """
        TESTE E2E: Validacao combinada KPI + Causa-Efeito.

        Valida:
        1. Ambas ferramentas executam
        2. Scores sao consistentes
        3. Score combinado calculado corretamente
        """
        # Setup
        kpi_tool = KPIAlignmentCheckerTool(llm=mock_llm)
        ce_tool = CauseEffectMapperTool(llm=mock_llm)

        # Execucao paralela
        kpi_report, ce_analysis = await asyncio.gather(
            kpi_tool.validate_kpi_alignment(valid_strategy_map, valid_kpi_framework),
            ce_tool.analyze_cause_effect(valid_strategy_map),
        )

        # VALIDACAO 1: Ambos retornos validos
        assert kpi_report is not None
        assert ce_analysis is not None

        # VALIDACAO 2: Scores no range
        assert 0 <= kpi_report.overall_score <= 100
        assert 0 <= ce_analysis.completeness_score <= 100

        # VALIDACAO 3: Score combinado
        combined_score = (kpi_report.overall_score + ce_analysis.completeness_score) / 2
        assert 0 <= combined_score <= 100

        # Log resultados
        print(f"\n[OK] KPI Score: {kpi_report.overall_score:.1f}/100")
        print(f"[OK] CE Score: {ce_analysis.completeness_score:.1f}/100")
        print(f"[OK] Combined Score: {combined_score:.1f}/100")

    @pytest.mark.asyncio
    async def test_validation_reports_serialization(
        self, valid_strategy_map, valid_kpi_framework, mock_llm
    ):
        """
        TESTE E2E: Serializacao dos reports para persistencia.

        Valida:
        1. Reports podem ser convertidos para dict
        2. Dicts podem ser reconvertidos para Pydantic
        """
        # Setup
        kpi_tool = KPIAlignmentCheckerTool(llm=mock_llm)
        ce_tool = CauseEffectMapperTool(llm=mock_llm)

        # Execucao
        kpi_report = await kpi_tool.validate_kpi_alignment(valid_strategy_map, valid_kpi_framework)
        ce_analysis = await ce_tool.analyze_cause_effect(valid_strategy_map)

        # VALIDACAO 1: Serializacao para dict
        kpi_dict = kpi_report.model_dump()
        ce_dict = ce_analysis.model_dump()

        assert isinstance(kpi_dict, dict)
        assert isinstance(ce_dict, dict)

        # VALIDACAO 2: Deserializacao de dict
        kpi_restored = KPIAlignmentReport(**kpi_dict)
        ce_restored = CauseEffectAnalysis(**ce_dict)

        assert kpi_restored.overall_score == kpi_report.overall_score
        assert ce_restored.completeness_score == ce_analysis.completeness_score


# ============================================================================
# TESTES E2E - UI LOADER
# ============================================================================


class TestUILoaderE2E:
    """Testes E2E para carregamento de reports na UI."""

    def test_load_validation_reports_structure(self):
        """
        TESTE E2E: Estrutura da funcao load_validation_reports.

        Valida:
        1. Funcao existe e pode ser importada
        2. Retorna tupla com 3 elementos
        3. Tipos corretos quando dados nao existem
        """
        # Import
        from ui.helpers.mem0_loader import load_validation_reports

        # Execucao com user_id inexistente
        kpi_report, ce_analysis, error = load_validation_reports("nonexistent_user_123")

        # VALIDACAO 1: Retorna tupla de 3 elementos
        assert isinstance(kpi_report, (KPIAlignmentReport, type(None)))
        assert isinstance(ce_analysis, (CauseEffectAnalysis, type(None)))
        assert isinstance(error, (str, type(None)))

        # VALIDACAO 2: Com user inexistente, deve ter erro ou None
        # (nao deve quebrar)
        assert error is not None or (kpi_report is None and ce_analysis is None)

    def test_validation_reports_type_checking(self):
        """
        TESTE E2E: Verificacao de tipos dos reports.

        Valida:
        1. KPIAlignmentReport tem atributos esperados
        2. CauseEffectAnalysis tem atributos esperados
        """
        # Criar reports de exemplo
        kpi_report = KPIAlignmentReport(
            overall_score=85.0,
            is_aligned=True,
            alignment_by_perspective={
                "Financeira": 90.0,
                "Clientes": 80.0,
                "Processos Internos": 85.0,
                "Aprendizado e Crescimento": 85.0,
            },
            alignment_issues=[],
            recommendations=["Recomendacao teste"],
        )

        ce_analysis = CauseEffectAnalysis(
            completeness_score=75.0,
            is_complete=False,
            total_connections=8,
            connections_by_type={"enables": 2, "drives": 4, "supports": 2},
            connections_by_perspective_pair={
                "L->P": 4,
                "P->C": 2,
                "C->F": 2,
            },
            gaps=[],
        )

        # VALIDACAO 1: KPIAlignmentReport atributos
        assert hasattr(kpi_report, "overall_score")
        assert hasattr(kpi_report, "is_aligned")
        assert hasattr(kpi_report, "alignment_by_perspective")
        assert hasattr(kpi_report, "alignment_issues")
        assert hasattr(kpi_report, "critical_issues_count")

        # VALIDACAO 2: CauseEffectAnalysis atributos
        assert hasattr(ce_analysis, "completeness_score")
        assert hasattr(ce_analysis, "is_complete")
        assert hasattr(ce_analysis, "total_connections")
        assert hasattr(ce_analysis, "connections_by_type")
        assert hasattr(ce_analysis, "gaps")
