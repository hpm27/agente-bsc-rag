"""
Testes Sprint 4.2: MilestoneTrackerTool

Valida geracao de milestones a partir de Action Plans e calculo de metricas.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.memory.schemas import (
    ActionItem,
    ActionPlan,
    Milestone,
    MilestoneTrackerReport,
)
from src.tools.milestone_tracker import MilestoneTrackerTool, create_milestone_tracker_tool


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def valid_action_item_1():
    """ActionItem valido de alta prioridade."""
    return ActionItem(
        action_title="Implementar sistema CRM para coleta de feedback de clientes",
        description="Configurar plataforma CRM com integracao de dados de clientes e automacao de coleta de feedback sistematico para medir NPS e satisfacao",
        perspective="Clientes",
        priority="HIGH",
        effort="MEDIUM",
        responsible="Equipe de Marketing e TI",
        start_date="2025-11-01",
        due_date="2025-12-15",
        resources_needed=["Plataforma CRM", "Treinamento equipe", "Integracao APIs"],
        success_criteria="80% dos clientes respondendo surveys mensais",
        dependencies=["Definir metricas de satisfacao"],
    )


@pytest.fixture
def valid_action_item_2():
    """ActionItem valido de media prioridade."""
    return ActionItem(
        action_title="Criar dashboard executivo com top 10 KPIs financeiros",
        description="Desenvolver dashboard consolidando top 10 KPIs financeiros das 4 perspectivas BSC com atualizacao em tempo real e drill-down por area",
        perspective="Financeira",
        priority="MEDIUM",
        effort="HIGH",
        responsible="BI / Financeiro",
        start_date="2025-12-01",
        due_date="2025-12-30",
        resources_needed=["Power BI / Tableau", "Acesso ERP", "Definicao KPIs"],
        success_criteria="Dashboard operacional com 100% dos KPIs atualizados diariamente",
        dependencies=["Implementar sistema CRM para coleta de feedback de clientes"],
    )


@pytest.fixture
def valid_action_item_3():
    """ActionItem valido de baixa prioridade."""
    return ActionItem(
        action_title="Implementar programa de capacitacao em Lean Six Sigma",
        description="Desenvolver programa de capacitacao Lean Six Sigma para 80% da equipe de operacoes com certificacao Yellow Belt e projetos praticos",
        perspective="Aprendizado e Crescimento",
        priority="MEDIUM",
        effort="MEDIUM",
        responsible="RH / Operacoes",
        start_date="2025-11-15",
        due_date="2026-02-28",
        resources_needed=["Instrutor certificado", "Material didatico", "Projetos piloto"],
        success_criteria="80% da equipe certificada Yellow Belt",
        dependencies=[],
    )


@pytest.fixture
def valid_action_plan(valid_action_item_1, valid_action_item_2, valid_action_item_3):
    """ActionPlan valido com 3 action items."""
    action_items = [valid_action_item_1, valid_action_item_2, valid_action_item_3]

    # Calcular campos obrigatorios
    total = len(action_items)
    high_priority = sum(1 for a in action_items if a.priority == "HIGH")

    # Agrupar por perspectiva
    by_perspective = {}
    for item in action_items:
        persp = item.perspective
        if persp not in by_perspective:
            by_perspective[persp] = []
        by_perspective[persp].append(item.action_title)

    return ActionPlan(
        action_items=action_items,
        total_actions=total,
        high_priority_count=high_priority,
        by_perspective=by_perspective,
        summary="Plano de acao com 3 iniciativas estrategicas cobrindo Clientes, Financeiro e Aprendizado e Crescimento para implementacao BSC completa",
        timeline_summary="Execucao em 4 meses: Nov/2025 a Fev/2026",
    )


@pytest.fixture
def mock_llm():
    """Mock LLM para testes sem custo de API."""
    mock = Mock()
    mock.ainvoke = AsyncMock(return_value=Mock(content="{}"))
    return mock


# ============================================================================
# TESTES UNITARIOS - MILESTONE SCHEMA
# ============================================================================


class TestMilestoneSchema:
    """Testes para schema Milestone."""

    def test_create_valid_milestone(self):
        """Milestone valido deve ser criado sem erros."""
        milestone = Milestone(
            name="Sistema CRM configurado",
            description="CRM operacional com integracao de dados de clientes e dashboard",
            action_item_ref="Implementar sistema CRM",
            status="IN_PROGRESS",
            progress_percent=65.0,
            target_date="2025-12-15",
            responsible="TI / Marketing",
            dependencies=["Definicao de requisitos"],
            blockers=[],
        )

        assert milestone.name == "Sistema CRM configurado"
        assert milestone.status == "IN_PROGRESS"
        assert milestone.progress_percent == 65.0
        assert milestone.is_on_track() is True
        assert milestone.is_completed() is False

    def test_milestone_status_literals(self):
        """Milestone deve aceitar apenas status validos."""
        valid_statuses = ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "BLOCKED", "AT_RISK"]

        for status in valid_statuses:
            milestone = Milestone(
                name="Test Milestone Status",
                description="Testing status validation for milestone schema",
                action_item_ref="Test Action",
                status=status,
                target_date="2025-12-31",
                responsible="Test Team",
            )
            assert milestone.status == status

    def test_milestone_is_on_track(self):
        """Metodo is_on_track deve retornar corretamente."""
        # Milestone on track
        on_track = Milestone(
            name="On Track Milestone Test",
            description="Milestone que esta no prazo e sem impedimentos identificados",
            action_item_ref="Test Action",
            status="IN_PROGRESS",
            target_date="2025-12-31",
            responsible="Test Team",
        )
        assert on_track.is_on_track() is True

        # Milestone at risk
        at_risk = Milestone(
            name="At Risk Milestone Test",
            description="Milestone que esta em risco devido a atrasos ou impedimentos",
            action_item_ref="Test Action",
            status="AT_RISK",
            target_date="2025-12-31",
            responsible="Test Team",
        )
        assert at_risk.is_on_track() is False

        # Milestone blocked
        blocked = Milestone(
            name="Blocked Milestone Test",
            description="Milestone bloqueado por dependencia ou impedimento externo",
            action_item_ref="Test Action",
            status="BLOCKED",
            target_date="2025-12-31",
            responsible="Test Team",
        )
        assert blocked.is_on_track() is False


# ============================================================================
# TESTES UNITARIOS - MILESTONE TRACKER REPORT SCHEMA
# ============================================================================


class TestMilestoneTrackerReportSchema:
    """Testes para schema MilestoneTrackerReport."""

    def test_create_valid_report(self):
        """Report valido deve ser criado sem erros."""
        milestones = [
            Milestone(
                name="Milestone 1 - Sistema CRM",
                description="Configuracao completa do sistema CRM com integracao de dados",
                action_item_ref="Implementar CRM",
                status="COMPLETED",
                progress_percent=100.0,
                target_date="2025-12-15",
                responsible="Equipe TI",
            ),
            Milestone(
                name="Milestone 2 - Dashboard KPIs",
                description="Dashboard executivo com top 10 KPIs das 4 perspectivas BSC",
                action_item_ref="Criar Dashboard",
                status="IN_PROGRESS",
                progress_percent=50.0,
                target_date="2025-12-30",
                responsible="Equipe BI",
            ),
        ]

        report = MilestoneTrackerReport(
            milestones=milestones,
            total_milestones=2,
            completed_count=1,
            in_progress_count=1,
            at_risk_count=0,
            overall_progress=75.0,
            critical_path=["Milestone 2 - Dashboard KPIs"],
            next_due_milestones=["Milestone 2 - Dashboard KPIs"],
            summary="Plano de acao 75% completo. 1/2 milestones finalizados, 1 em andamento.",
            recommendations=["Priorizar conclusao do Dashboard KPIs"],
        )

        assert report.total_milestones == 2
        assert report.completed_count == 1
        assert report.overall_progress == 75.0
        assert len(report.milestones) == 2

    def test_report_helper_methods(self):
        """Metodos auxiliares do report devem funcionar."""
        milestones = [
            Milestone(
                name="Completed Milestone Test",
                description="Milestone completado para teste de metodos auxiliares",
                action_item_ref="Test Action 1",
                status="COMPLETED",
                progress_percent=100.0,
                target_date="2025-12-15",
                responsible="Team Alpha",
            ),
            Milestone(
                name="At Risk Milestone Test",
                description="Milestone em risco para teste de metodos auxiliares",
                action_item_ref="Test Action 2",
                status="AT_RISK",
                progress_percent=30.0,
                target_date="2025-12-30",
                responsible="Team Beta",
            ),
        ]

        report = MilestoneTrackerReport(
            milestones=milestones,
            total_milestones=2,
            completed_count=1,
            in_progress_count=0,
            at_risk_count=1,
            overall_progress=65.0,
            summary="Plano 65% completo com 1 milestone em risco requerendo atencao imediata.",
        )

        # Test get_milestones_by_status
        completed = report.get_milestones_by_status("COMPLETED")
        assert len(completed) == 1
        assert completed[0].name == "Completed Milestone Test"

        # Test get_blocked_milestones
        at_risk = report.get_blocked_milestones()
        assert len(at_risk) == 1
        assert at_risk[0].status == "AT_RISK"


# ============================================================================
# TESTES UNITARIOS - MILESTONE TRACKER TOOL
# ============================================================================


class TestMilestoneTrackerTool:
    """Testes para MilestoneTrackerTool."""

    def test_create_tool_factory(self):
        """Factory function deve criar tool valido."""
        tool = create_milestone_tracker_tool()
        assert tool is not None
        assert isinstance(tool, MilestoneTrackerTool)

    def test_init_with_default_llm(self):
        """Tool deve inicializar com LLM default."""
        tool = MilestoneTrackerTool()
        assert tool.llm is not None

    def test_init_with_custom_llm(self, mock_llm):
        """Tool deve aceitar LLM customizado."""
        tool = MilestoneTrackerTool(llm=mock_llm)
        assert tool.llm == mock_llm

    @pytest.mark.asyncio
    async def test_generate_milestones_from_action_plan(self, valid_action_plan, mock_llm):
        """Deve gerar milestones a partir de action plan."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-20",
        )

        # Validacoes basicas
        assert report is not None
        assert isinstance(report, MilestoneTrackerReport)
        assert report.total_milestones == 3
        assert len(report.milestones) == 3

        # Validar que milestones foram criados corretamente
        milestone_names = [m.name for m in report.milestones]
        assert any("CRM" in name for name in milestone_names)
        assert any("dashboard" in name.lower() or "KPI" in name for name in milestone_names)

    @pytest.mark.asyncio
    async def test_milestone_status_determination(self, valid_action_plan, mock_llm):
        """Deve determinar status corretamente baseado em datas."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        # Testar com data no meio do periodo
        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-12-01",
        )

        # Pelo menos um milestone deve estar IN_PROGRESS
        statuses = [m.status for m in report.milestones]
        assert "IN_PROGRESS" in statuses or "AT_RISK" in statuses

    @pytest.mark.asyncio
    async def test_overall_progress_calculation(self, valid_action_plan, mock_llm):
        """Deve calcular progresso geral corretamente."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-25",
        )

        # Progresso deve estar no range 0-100
        assert 0 <= report.overall_progress <= 100

        # Progresso deve ser media dos milestones
        expected_avg = sum(m.progress_percent for m in report.milestones) / len(report.milestones)
        assert abs(report.overall_progress - expected_avg) < 1.0

    @pytest.mark.asyncio
    async def test_critical_path_identification(self, valid_action_plan, mock_llm):
        """Deve identificar caminho critico."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        # Usar data que coloca alguns milestones em risco
        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-12-20",  # Proximo do prazo
        )

        # Critical path deve ser lista
        assert isinstance(report.critical_path, list)

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, valid_action_plan, mock_llm):
        """Deve gerar recomendacoes."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-25",
        )

        # Deve ter pelo menos uma recomendacao
        assert len(report.recommendations) >= 1
        assert all(isinstance(r, str) for r in report.recommendations)

    @pytest.mark.asyncio
    async def test_summary_generation(self, valid_action_plan, mock_llm):
        """Deve gerar summary executivo."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-25",
        )

        # Summary deve conter informacoes chave
        assert report.summary is not None
        assert len(report.summary) >= 20
        assert "%" in report.summary or "completo" in report.summary.lower()


# ============================================================================
# TESTES DE INTEGRACAO
# ============================================================================


class TestMilestoneTrackerIntegration:
    """Testes de integracao para MilestoneTrackerTool."""

    @pytest.mark.asyncio
    async def test_end_to_end_milestone_tracking(self, valid_action_plan, mock_llm):
        """Teste E2E de geracao de milestones."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        # Gerar report
        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-25",
        )

        # Validar estrutura completa
        assert report.total_milestones == len(report.milestones)
        assert (
            report.completed_count + report.in_progress_count + report.at_risk_count
            <= report.total_milestones
        )
        assert 0 <= report.overall_progress <= 100
        assert report.tracked_at is not None

        # Validar cada milestone
        for milestone in report.milestones:
            assert milestone.name is not None
            assert milestone.description is not None
            assert milestone.action_item_ref is not None
            assert milestone.status in [
                "NOT_STARTED",
                "IN_PROGRESS",
                "COMPLETED",
                "BLOCKED",
                "AT_RISK",
            ]
            assert 0 <= milestone.progress_percent <= 100
            assert milestone.target_date is not None
            assert milestone.responsible is not None

    @pytest.mark.asyncio
    async def test_serialization_roundtrip(self, valid_action_plan, mock_llm):
        """Report deve ser serializavel e deserializavel."""
        tool = MilestoneTrackerTool(llm=mock_llm)

        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-25",
        )

        # Serializar
        report_dict = report.model_dump()
        assert isinstance(report_dict, dict)

        # Deserializar
        restored = MilestoneTrackerReport(**report_dict)
        assert restored.total_milestones == report.total_milestones
        assert restored.overall_progress == report.overall_progress
