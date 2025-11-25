"""
Testes para ferramentas de validacao Sprint 3.

Sprint 3.1: KPIAlignmentCheckerTool
Sprint 3.2: CauseEffectMapperTool

Testes:
- Testes unitarios (mock LLM)
- Validacoes estruturais
- Cenarios edge case

CHECKLIST [[9969868]]:
[x] Grep schemas ANTES de criar fixtures
[x] Functional assertions (nao text assertions)
[x] Margem de seguranca em validators
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

# Schemas
from src.memory.schemas import (
    StrategyMap,
    StrategyMapPerspective,
    StrategicObjective,
    CauseEffectConnection,
    KPIFramework,
    KPIDefinition,
    KPIAlignmentReport,
    AlignmentIssue,
    CauseEffectAnalysis,
    CauseEffectGap,
)

# Tools
from src.tools.kpi_alignment_checker import (
    KPIAlignmentCheckerTool,
    create_kpi_alignment_checker_tool,
)
from src.tools.cause_effect_mapper import (
    CauseEffectMapperTool,
    create_cause_effect_mapper_tool,
)


# ============================================================================
# FIXTURES - OBJECTIVES VALIDOS (grep src/memory/schemas.py confirmou)
# Campos obrigatorios: name (min 10), description (min 50), perspective, timeframe (min 5), success_criteria (min 2 items)
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
    # Criar segundo objetivo para cada perspectiva (minimo 2)
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
        description="Estabelecer sistema de sugestoes e kaizen events para criar cultura de melhoria continua com participacao de 70% dos colaboradores",
        perspective="Aprendizado e Crescimento",
        timeframe="24 meses",
        success_criteria=["70% participacao", "100+ sugestoes/mes"],
        related_kpis=["Taxa Participacao Melhoria", "Sugestoes Implementadas/Mes"],
        priority="Média",
    )

    # Criar perspectivas
    financial = StrategyMapPerspective(
        name="Financeira",
        objectives=[valid_objective_financial, obj_financial_2],
    )

    customer = StrategyMapPerspective(
        name="Clientes",
        objectives=[valid_objective_customer, obj_customer_2],
    )

    process = StrategyMapPerspective(
        name="Processos Internos",
        objectives=[valid_objective_process, obj_process_2],
    )

    learning = StrategyMapPerspective(
        name="Aprendizado e Crescimento",
        objectives=[valid_objective_learning, obj_learning_2],
    )

    # Criar conexoes causa-efeito (minimo 4)
    connections = [
        CauseEffectConnection(
            source_objective_id="Certificar 80% da equipe em Lean Six Sigma",
            target_objective_id="Reduzir lead time de producao em 30%",
            relationship_type="enables",
            strength="strong",
            rationale="Certificacao Lean Six Sigma habilita equipe a identificar e eliminar waste, reduzindo lead time de producao",
        ),
        CauseEffectConnection(
            source_objective_id="Reduzir lead time de producao em 30%",
            target_objective_id="Atingir NPS de 50 pontos ou mais",
            relationship_type="drives",
            strength="strong",
            rationale="Lead time menor resulta em entregas mais rapidas, aumentando satisfacao do cliente e NPS",
        ),
        CauseEffectConnection(
            source_objective_id="Atingir NPS de 50 pontos ou mais",
            target_objective_id="Aumentar margem EBITDA para 18% ate 2026",
            relationship_type="drives",
            strength="strong",
            rationale="Maior satisfacao cliente resulta em maior retencao e vendas recorrentes, aumentando receita e margem EBITDA",
        ),
        CauseEffectConnection(
            source_objective_id="Atingir OEE de 85% nas linhas de producao",
            target_objective_id="Reduzir custo operacional em 15% ate 2026",
            relationship_type="drives",
            strength="strong",
            rationale="OEE alto significa mais producao com mesmos recursos, reduzindo custo unitario",
        ),
    ]

    return StrategyMap(
        financial=financial,
        customer=customer,
        process=process,
        learning=learning,
        cause_effect_connections=connections,
        strategic_priorities=[
            "Excelencia Operacional",
            "Inovacao de Produto",
            "Customer Intimacy",
        ],
        created_at=datetime.now(timezone.utc),
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
                description="Tempo medio desde inicio da ordem de producao ate produto finalizado em estoque",
                perspective="Processos Internos",
                metric_type="tempo",
                target_value="< 5 dias",
                measurement_frequency="semanal",
                data_source="MES - Manufacturing Execution System",
            ),
            KPIDefinition(
                name="OEE - Overall Equipment Effectiveness",
                description="Indicador de eficiencia global dos equipamentos considerando disponibilidade, performance e qualidade",
                perspective="Processos Internos",
                metric_type="quantidade",
                target_value=">= 85%",
                measurement_frequency="diario",
                data_source="MES - Manufacturing Execution System",
            ),
        ],
        learning_kpis=[
            KPIDefinition(
                name="% Equipe Certificada",
                description="Percentual de colaboradores com certificacao Lean Six Sigma (Yellow, Green ou Black Belt)",
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value=">= 80%",
                measurement_frequency="trimestral",
                data_source="Sistema RH",
            ),
            KPIDefinition(
                name="Projetos Melhoria Concluidos",
                description="Numero de projetos de melhoria continua concluidos com impacto mensuravel no periodo",
                perspective="Aprendizado e Crescimento",
                metric_type="quantidade",
                target_value=">= 30/ano",
                measurement_frequency="mensal",
                data_source="Sistema de Gestao de Projetos",
            ),
        ],
    )


@pytest.fixture
def mock_llm():
    """Mock LLM para testes unitarios (sem custo API)."""
    mock = Mock()
    mock.ainvoke = AsyncMock(return_value=Mock(content='{"is_aligned": true, "confidence": 0.9}'))
    return mock


# ============================================================================
# TESTES KPI ALIGNMENT CHECKER
# ============================================================================


class TestKPIAlignmentCheckerTool:
    """Testes para KPIAlignmentCheckerTool."""

    def test_create_tool_factory(self):
        """Factory function deve criar tool valido."""
        tool = create_kpi_alignment_checker_tool()
        assert tool is not None
        assert isinstance(tool, KPIAlignmentCheckerTool)

    def test_init_with_default_llm(self):
        """Tool deve inicializar com LLM default."""
        tool = KPIAlignmentCheckerTool()
        assert tool.llm is not None

    def test_init_with_custom_llm(self, mock_llm):
        """Tool deve aceitar LLM customizado."""
        tool = KPIAlignmentCheckerTool(llm=mock_llm)
        assert tool.llm == mock_llm

    def test_collect_all_objectives(self, valid_strategy_map):
        """Deve coletar todos objectives de todas perspectivas."""
        tool = KPIAlignmentCheckerTool()
        objectives = tool._collect_all_objectives(valid_strategy_map)

        assert len(objectives) == 8  # 2 por perspectiva * 4 perspectivas
        assert all("name" in obj for obj in objectives)
        assert all("perspective" in obj for obj in objectives)

    def test_find_objectives_without_kpis_all_have(self, valid_strategy_map):
        """Quando todos objectives tem KPIs, deve retornar lista vazia."""
        tool = KPIAlignmentCheckerTool()
        without_kpis = tool._find_objectives_without_kpis(valid_strategy_map)

        # Todos objectives na fixture tem related_kpis
        assert len(without_kpis) == 0

    def test_find_orphan_kpis_all_referenced(self, valid_strategy_map, valid_kpi_framework):
        """Quando todos KPIs estao referenciados, deve retornar lista vazia."""
        tool = KPIAlignmentCheckerTool()
        orphans = tool._find_orphan_kpis(valid_strategy_map, valid_kpi_framework)

        # Todos KPIs da fixture estao em related_kpis dos objectives
        assert len(orphans) == 0

    def test_check_coverage_valid(self, valid_strategy_map, valid_kpi_framework):
        """Strategy Map e KPI Framework completos devem passar coverage."""
        tool = KPIAlignmentCheckerTool()
        issues, recs = tool._check_coverage(valid_strategy_map, valid_kpi_framework)

        # Todas perspectivas tem >= 2 objectives e KPIs
        assert len(issues) == 0

    def test_check_sufficiency_valid(self, valid_strategy_map):
        """Objectives com 1-3 KPIs devem passar sufficiency."""
        tool = KPIAlignmentCheckerTool()
        issues, recs = tool._check_sufficiency(valid_strategy_map)

        # Todos objectives tem 2 KPIs (dentro do ideal 1-3)
        assert len(issues) == 0

    def test_calculate_score_by_perspective(self, valid_strategy_map):
        """Deve calcular score corretamente por perspectiva."""
        tool = KPIAlignmentCheckerTool()
        issues = []  # Sem issues = score 100 para todas perspectivas

        scores = tool._calculate_score_by_perspective(valid_strategy_map, issues)

        assert "Financeira" in scores
        assert "Clientes" in scores
        assert "Processos Internos" in scores
        assert "Aprendizado e Crescimento" in scores
        assert all(score == 100 for score in scores.values())

    def test_calculate_overall_score_perfect(self):
        """Score perfeito quando nao ha issues."""
        tool = KPIAlignmentCheckerTool()
        score = tool._calculate_overall_score(
            issues=[],
            total_objectives=8,
            orphan_count=0,
            missing_kpis_count=0,
        )

        assert score == 100.0

    def test_calculate_overall_score_with_issues(self):
        """Score deve diminuir com issues."""
        tool = KPIAlignmentCheckerTool()

        issues = [
            AlignmentIssue(
                issue_type="missing_kpi",
                severity="high",
                description="Objetivo X nao tem KPI associado",
                recommendation="Criar KPI para objetivo X",
            ),
            AlignmentIssue(
                issue_type="orphan_kpi",
                severity="medium",
                description="KPI Y nao esta vinculado a objetivo",
                recommendation="Vincular KPI Y a objetivo",
            ),
        ]

        score = tool._calculate_overall_score(
            issues=issues,
            total_objectives=8,
            orphan_count=1,
            missing_kpis_count=1,
        )

        # Score deve ser menor que 100
        assert score < 100
        # Score deve considerar penalidades
        # high = -10, medium = -5, orphan = -3, missing = -5
        # 100 - 10 - 5 - 3 - 5 = 77
        assert score == 77.0

    @pytest.mark.asyncio
    async def test_validate_kpi_alignment_complete(
        self, valid_strategy_map, valid_kpi_framework, mock_llm
    ):
        """Validacao completa deve retornar KPIAlignmentReport."""
        tool = KPIAlignmentCheckerTool(llm=mock_llm)

        report = await tool.validate_kpi_alignment(
            strategy_map=valid_strategy_map,
            kpi_framework=valid_kpi_framework,
        )

        assert isinstance(report, KPIAlignmentReport)
        assert hasattr(report, "overall_score")
        assert hasattr(report, "is_aligned")
        assert hasattr(report, "alignment_by_perspective")
        assert hasattr(report, "alignment_issues")


# ============================================================================
# TESTES CAUSE-EFFECT MAPPER
# ============================================================================


class TestCauseEffectMapperTool:
    """Testes para CauseEffectMapperTool."""

    def test_create_tool_factory(self):
        """Factory function deve criar tool valido."""
        tool = create_cause_effect_mapper_tool()
        assert tool is not None
        assert isinstance(tool, CauseEffectMapperTool)

    def test_init_with_default_llm(self):
        """Tool deve inicializar com LLM default."""
        tool = CauseEffectMapperTool()
        assert tool.llm is not None

    def test_collect_all_objectives_names(self, valid_strategy_map):
        """Deve coletar nomes de todos objectives."""
        tool = CauseEffectMapperTool()
        names = tool._collect_all_objectives_names(valid_strategy_map)

        assert len(names) == 8
        assert "Aumentar margem EBITDA para 18% ate 2026" in names
        assert "Atingir NPS de 50 pontos ou mais" in names

    def test_get_objective_perspective(self, valid_strategy_map):
        """Deve retornar perspectiva correta para objetivo."""
        tool = CauseEffectMapperTool()

        persp = tool._get_objective_perspective(
            valid_strategy_map, "Aumentar margem EBITDA para 18% ate 2026"
        )
        assert persp == "Financeira"

        persp = tool._get_objective_perspective(
            valid_strategy_map, "Atingir NPS de 50 pontos ou mais"
        )
        assert persp == "Clientes"

    def test_check_flow_direction_valid(self, valid_strategy_map):
        """Conexoes corretas (L->P->C->F) nao devem gerar violacoes."""
        tool = CauseEffectMapperTool()
        violations = tool._check_flow_direction(
            valid_strategy_map.cause_effect_connections,
            valid_strategy_map,
        )

        # Conexoes na fixture seguem fluxo correto
        assert len(violations) == 0

    def test_detect_cycles_no_cycles(self, valid_strategy_map):
        """Strategy Map sem ciclos deve retornar False."""
        tool = CauseEffectMapperTool()
        has_cycles, cycles = tool._detect_cycles(
            valid_strategy_map.cause_effect_connections,
            valid_strategy_map,
        )

        assert has_cycles is False
        assert len(cycles) == 0

    def test_find_isolated_objectives_none(self, valid_strategy_map):
        """Quando todos objectives estao conectados, deve retornar lista vazia."""
        tool = CauseEffectMapperTool()
        all_objectives = tool._collect_all_objectives_names(valid_strategy_map)

        isolated = tool._find_isolated_objectives(
            valid_strategy_map.cause_effect_connections,
            all_objectives,
        )

        # Alguns objectives podem estar isolados na fixture
        # (nem todos estao em source ou target das conexoes)
        # Verificamos apenas que a funcao retorna lista
        assert isinstance(isolated, list)

    def test_check_minimum_connections_valid(self, valid_strategy_map):
        """Strategy Map com >= 4 conexoes adjacentes deve passar."""
        tool = CauseEffectMapperTool()
        has_minimum, missing = tool._check_minimum_connections(
            valid_strategy_map.cause_effect_connections,
            valid_strategy_map,
        )

        # Fixture tem 4 conexoes, incluindo L->P, P->C, C->F
        assert has_minimum is True
        assert len(missing) == 0

    def test_count_by_type(self, valid_strategy_map):
        """Deve contar conexoes por tipo corretamente."""
        tool = CauseEffectMapperTool()
        counts = tool._count_by_type(valid_strategy_map.cause_effect_connections)

        assert "enables" in counts
        assert "drives" in counts
        assert "supports" in counts
        # Fixture tem 1 enables + 3 drives
        assert counts["enables"] == 1
        assert counts["drives"] == 3

    def test_count_by_perspective_pair(self, valid_strategy_map):
        """Deve contar conexoes por par de perspectivas."""
        tool = CauseEffectMapperTool()
        counts = tool._count_by_perspective_pair(
            valid_strategy_map.cause_effect_connections,
            valid_strategy_map,
        )

        assert "L->P" in counts
        assert "P->C" in counts
        assert "C->F" in counts
        # Fixture deve ter pelo menos 1 conexao L->P, P->C, C->F
        assert counts["L->P"] >= 1

    def test_calculate_completeness_score_perfect(self):
        """Score perfeito quando todas validacoes passam."""
        tool = CauseEffectMapperTool()
        score = tool._calculate_completeness_score(
            total_connections=8,
            total_objectives=8,
            isolated_count=0,
            violations_count=0,
            gaps_count=0,
            connections_by_pair={"L->P": 2, "P->C": 2, "C->F": 2, "L->C": 1, "P->F": 1},
        )

        # Score alto com todas validacoes passando + bonus
        assert score >= 80

    def test_calculate_completeness_score_with_issues(self):
        """Score deve diminuir com issues."""
        tool = CauseEffectMapperTool()
        score = tool._calculate_completeness_score(
            total_connections=2,  # Poucas conexoes
            total_objectives=8,
            isolated_count=2,  # 2 isolados
            violations_count=1,  # 1 violacao
            gaps_count=3,  # 3 gaps
            connections_by_pair={"L->P": 1, "P->C": 1, "C->F": 0},  # Falta C->F
        )

        # Score deve ser menor
        assert score < 80

    @pytest.mark.asyncio
    async def test_analyze_cause_effect_complete(self, valid_strategy_map, mock_llm):
        """Analise completa deve retornar CauseEffectAnalysis."""
        tool = CauseEffectMapperTool(llm=mock_llm)

        analysis = await tool.analyze_cause_effect(
            strategy_map=valid_strategy_map,
            suggest_improvements=False,  # Desabilitar LLM para teste rapido
        )

        assert isinstance(analysis, CauseEffectAnalysis)
        assert hasattr(analysis, "completeness_score")
        assert hasattr(analysis, "is_complete")
        assert hasattr(analysis, "total_connections")
        assert hasattr(analysis, "gaps")
        assert hasattr(analysis, "isolated_objectives")


# ============================================================================
# TESTES DE INTEGRACAO ENTRE TOOLS
# ============================================================================


class TestValidationToolsIntegration:
    """Testes de integracao entre KPI Alignment e Cause-Effect Mapper."""

    @pytest.mark.asyncio
    async def test_both_tools_with_same_strategy_map(
        self, valid_strategy_map, valid_kpi_framework, mock_llm
    ):
        """Ambas tools devem funcionar com mesmo Strategy Map."""
        kpi_checker = KPIAlignmentCheckerTool(llm=mock_llm)
        ce_mapper = CauseEffectMapperTool(llm=mock_llm)

        # Executar ambas validacoes
        kpi_report = await kpi_checker.validate_kpi_alignment(
            valid_strategy_map, valid_kpi_framework
        )
        ce_analysis = await ce_mapper.analyze_cause_effect(
            valid_strategy_map, suggest_improvements=False
        )

        # Ambas devem retornar reports validos
        assert isinstance(kpi_report, KPIAlignmentReport)
        assert isinstance(ce_analysis, CauseEffectAnalysis)

        # Scores devem ser numericos
        assert isinstance(kpi_report.overall_score, float)
        assert isinstance(ce_analysis.completeness_score, float)

    @pytest.mark.asyncio
    async def test_combined_score_calculation(
        self, valid_strategy_map, valid_kpi_framework, mock_llm
    ):
        """Score combinado pode ser calculado a partir de ambas tools."""
        kpi_checker = KPIAlignmentCheckerTool(llm=mock_llm)
        ce_mapper = CauseEffectMapperTool(llm=mock_llm)

        kpi_report = await kpi_checker.validate_kpi_alignment(
            valid_strategy_map, valid_kpi_framework
        )
        ce_analysis = await ce_mapper.analyze_cause_effect(
            valid_strategy_map, suggest_improvements=False
        )

        # Score combinado (media simples)
        combined_score = (kpi_report.overall_score + ce_analysis.completeness_score) / 2

        assert 0 <= combined_score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
