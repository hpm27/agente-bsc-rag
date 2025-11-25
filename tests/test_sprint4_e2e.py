"""
Testes E2E SPRINT 4: Action Plans MVP

Valida fluxo completo de:
1. ActionPlanTool (geracao de action plans)
2. MilestoneTrackerTool (rastreamento de milestones)
3. Integracao no workflow (implementation_handler)
4. UI Action Plans (pages/2_action_plan.py)

IMPORTANTE: Testes E2E usam mocks para LLM (custo zero).
Para testes com LLM real, usar pytest markers.
"""

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.memory.schemas import (
    ActionItem,
    ActionPlan,
    ClientProfile,
    CompanyInfo,
    Milestone,
    MilestoneTrackerReport,
    StrategicObjective,
    StrategyMap,
    StrategyMapPerspective,
)
from src.tools.milestone_tracker import MilestoneTrackerTool


# ============================================================================
# FIXTURES COMPLETAS
# ============================================================================


@pytest.fixture
def valid_company_info():
    """CompanyInfo valido para testes."""
    return CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="medio_porte",
        annual_revenue="R$ 50M",
        employee_count=150,
        main_products=["Software ERP", "Consultoria TI", "Cloud Services"],
        geographic_coverage="nacional",
    )


@pytest.fixture
def valid_client_profile(valid_company_info):
    """ClientProfile valido para testes."""
    return ClientProfile(
        user_id="test_user_sprint4",
        company_info=valid_company_info,
        strategic_goals=[
            "Aumentar receita em 20%",
            "Melhorar satisfacao cliente",
            "Reduzir custos",
        ],
        current_challenges=["Alta rotatividade", "Processos manuais", "Baixo NPS"],
        bsc_familiarity="intermediario",
        industry_context="Empresa de tecnologia B2B com foco em PMEs",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def valid_strategy_map():
    """StrategyMap valido com 4 perspectivas."""
    return StrategyMap(
        financial=StrategyMapPerspective(
            name="Financeira",
            objectives=[
                StrategicObjective(
                    name="Aumentar receita recorrente em 20% ate 2026",
                    description="Expandir base de clientes SaaS e aumentar ticket medio atraves de upsell e cross-sell",
                    perspective="Financeira",
                    timeframe="24 meses",
                    success_criteria=["Receita recorrente >= R$ 60M", "Ticket medio >= R$ 5K/mes"],
                    related_kpis=["MRR", "ARPU", "LTV"],
                    priority="Alta",
                ),
            ],
        ),
        customer=StrategyMapPerspective(
            name="Clientes",
            objectives=[
                StrategicObjective(
                    name="Atingir NPS de 50 pontos em 12 meses",
                    description="Melhorar experiencia do cliente atraves de suporte proativo e produto mais intuitivo",
                    perspective="Clientes",
                    timeframe="12 meses",
                    success_criteria=["NPS >= 50", "Churn < 5%"],
                    related_kpis=["NPS", "Churn Rate", "CSAT"],
                    priority="Alta",
                ),
            ],
        ),
        process=StrategyMapPerspective(
            name="Processos Internos",
            objectives=[
                StrategicObjective(
                    name="Automatizar 80% dos processos repetitivos",
                    description="Implementar RPA e workflows automatizados para reduzir tempo de operacoes manuais",
                    perspective="Processos Internos",
                    timeframe="18 meses",
                    success_criteria=[
                        "80% processos automatizados",
                        "Reducao 50% tempo operacional",
                    ],
                    related_kpis=["Taxa Automacao", "Tempo Ciclo", "Erros Operacionais"],
                    priority="Alta",
                ),
            ],
        ),
        learning=StrategyMapPerspective(
            name="Aprendizado e Crescimento",
            objectives=[
                StrategicObjective(
                    name="Reduzir turnover para menos de 10% ao ano",
                    description="Implementar programa de desenvolvimento de carreira e beneficios competitivos",
                    perspective="Aprendizado e Crescimento",
                    timeframe="12 meses",
                    success_criteria=["Turnover < 10%", "Engajamento >= 80%"],
                    related_kpis=["Turnover Rate", "eNPS", "Engajamento"],
                    priority="Alta",
                ),
            ],
        ),
        cause_effect_connections=[],
        strategic_priorities=["Customer Success", "Automacao", "Retencao Talentos"],
    )


@pytest.fixture
def valid_action_items():
    """Lista de ActionItems validos para testes."""
    return [
        ActionItem(
            action_title="Implementar sistema de NPS automatizado com coleta mensal",
            description="Configurar plataforma de pesquisa NPS com envio automatico mensal para todos clientes ativos, integrando com CRM para segmentacao",
            perspective="Clientes",
            priority="HIGH",
            effort="MEDIUM",
            responsible="Customer Success / TI",
            start_date="2025-11-15",
            due_date="2025-12-30",
            resources_needed=["Plataforma NPS", "Integracao CRM", "Treinamento equipe"],
            success_criteria="100% clientes ativos recebendo pesquisa, taxa resposta >= 30%",
            dependencies=[],
        ),
        ActionItem(
            action_title="Desenvolver programa de onboarding estruturado para novos clientes",
            description="Criar jornada de onboarding de 30 dias com checkpoints, treinamentos e acompanhamento proativo para garantir sucesso inicial",
            perspective="Clientes",
            priority="HIGH",
            effort="HIGH",
            responsible="Customer Success",
            start_date="2025-12-01",
            due_date="2026-01-31",
            resources_needed=["Conteudo treinamento", "Plataforma LMS", "Equipe CS dedicada"],
            success_criteria="90% clientes completando onboarding, time to value < 15 dias",
            dependencies=["Implementar sistema de NPS automatizado com coleta mensal"],
        ),
        ActionItem(
            action_title="Automatizar processo de faturamento e cobranca",
            description="Implementar sistema de faturamento automatico integrado ao ERP com gestao de cobranca e dunning automatizado",
            perspective="Processos Internos",
            priority="MEDIUM",
            effort="HIGH",
            responsible="Financeiro / TI",
            start_date="2025-12-15",
            due_date="2026-02-28",
            resources_needed=["Sistema faturamento", "Integracao ERP", "Gateway pagamento"],
            success_criteria="100% faturas automaticas, inadimplencia < 3%",
            dependencies=[],
        ),
        ActionItem(
            action_title="Criar programa de desenvolvimento de carreira tech",
            description="Estruturar trilhas de carreira para desenvolvedores com certificacoes, mentoria e progressao clara de niveis",
            perspective="Aprendizado e Crescimento",
            priority="HIGH",
            effort="MEDIUM",
            responsible="RH / Tech Lead",
            start_date="2025-11-20",
            due_date="2026-01-15",
            resources_needed=["Plataforma educacional", "Budget certificacoes", "Mentores"],
            success_criteria="100% devs com PDI, 50% com certificacao em 6 meses",
            dependencies=[],
        ),
    ]


@pytest.fixture
def valid_action_plan(valid_action_items):
    """ActionPlan valido completo."""
    items = valid_action_items

    by_perspective = {}
    for item in items:
        persp = item.perspective
        if persp not in by_perspective:
            by_perspective[persp] = []
        by_perspective[persp].append(item.action_title)

    return ActionPlan(
        action_items=items,
        total_actions=len(items),
        high_priority_count=sum(1 for i in items if i.priority == "HIGH"),
        by_perspective=by_perspective,
        summary="Plano de acao BSC com 4 iniciativas estrategicas distribuidas em 3 perspectivas (Clientes, Processos Internos, Aprendizado). Foco em Customer Success e automacao.",
        timeline_summary="Execucao entre Nov/2025 e Fev/2026, total 4 meses. Maior concentracao em Dez/2025-Jan/2026.",
    )


@pytest.fixture
def mock_llm():
    """Mock LLM para testes sem custo de API."""
    mock = Mock()
    mock.ainvoke = AsyncMock(return_value=Mock(content="{}"))
    return mock


# ============================================================================
# TESTES E2E - MILESTONE TRACKER
# ============================================================================


class TestMilestoneTrackerE2E:
    """Testes E2E para MilestoneTrackerTool."""

    @pytest.mark.asyncio
    async def test_complete_milestone_tracking_flow(self, valid_action_plan, mock_llm):
        """
        TESTE E2E: Fluxo completo de milestone tracking.

        Valida:
        1. Geracao de milestones a partir de action plan
        2. Calculo de metricas (progress, at_risk, etc)
        3. Identificacao de caminho critico
        4. Geracao de recomendacoes
        """
        # Setup
        tool = MilestoneTrackerTool(llm=mock_llm)

        # Execucao
        start = time.time()
        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-12-15",
        )
        latency = time.time() - start

        # VALIDACAO 1: Report gerado
        assert report is not None
        assert isinstance(report, MilestoneTrackerReport)

        # VALIDACAO 2: Milestones correspondem aos action items
        assert report.total_milestones == len(valid_action_plan.action_items)

        # VALIDACAO 3: Metricas calculadas
        assert 0 <= report.overall_progress <= 100
        assert report.completed_count >= 0
        assert report.in_progress_count >= 0
        assert report.at_risk_count >= 0

        # VALIDACAO 4: Contagens consistentes
        total_counted = report.completed_count + report.in_progress_count + report.at_risk_count
        not_started = sum(1 for m in report.milestones if m.status == "NOT_STARTED")
        assert total_counted + not_started == report.total_milestones

        # VALIDACAO 5: Summary e recommendations presentes
        assert len(report.summary) >= 20
        assert len(report.recommendations) >= 1

        # VALIDACAO 6: Latencia aceitavel
        assert latency < 5.0, f"Latencia muito alta: {latency:.2f}s"

        # Log resultados
        print("\n[OK] Milestone Tracking E2E")
        print(f"[OK] Total: {report.total_milestones} milestones")
        print(f"[OK] Progresso: {report.overall_progress:.1f}%")
        print(f"[OK] Em risco: {report.at_risk_count}")
        print(f"[OK] Latencia: {latency:.2f}s")

    @pytest.mark.asyncio
    async def test_milestone_status_progression(self, valid_action_plan, mock_llm):
        """
        TESTE E2E: Progressao de status ao longo do tempo.

        Simula diferentes datas para verificar calculo de status.
        """
        tool = MilestoneTrackerTool(llm=mock_llm)

        # Cenario 1: Inicio (muitos NOT_STARTED)
        report_early = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-11-10",  # Antes de maioria iniciar
        )

        # Cenario 2: Meio (maioria IN_PROGRESS)
        report_mid = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-12-15",  # No meio da execucao
        )

        # Cenario 3: Fim (alguns AT_RISK se atrasados)
        report_late = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2026-03-01",  # Apos prazos
        )

        # VALIDACAO: Progresso deve aumentar ao longo do tempo
        # (ou pelo menos nao diminuir muito)
        assert report_late.overall_progress >= report_early.overall_progress - 10

        # VALIDACAO: No cenario tardio, mais milestones em risco
        # (pois passaram dos prazos)
        assert report_late.at_risk_count >= report_early.at_risk_count

        print("\n[OK] Progressao de Status")
        print(f"[OK] Early: {report_early.overall_progress:.1f}%")
        print(f"[OK] Mid: {report_mid.overall_progress:.1f}%")
        print(f"[OK] Late: {report_late.overall_progress:.1f}%")


# ============================================================================
# TESTES E2E - ACTION PLAN COMPLETO
# ============================================================================


class TestActionPlanE2E:
    """Testes E2E para validacao de ActionPlan."""

    def test_action_plan_structure_validation(self, valid_action_plan):
        """
        TESTE E2E: Validacao estrutural do ActionPlan.
        """
        # VALIDACAO 1: Campos obrigatorios
        assert valid_action_plan.action_items is not None
        assert len(valid_action_plan.action_items) >= 3
        assert valid_action_plan.total_actions == len(valid_action_plan.action_items)

        # VALIDACAO 2: High priority count correto
        actual_high = sum(1 for i in valid_action_plan.action_items if i.priority == "HIGH")
        assert valid_action_plan.high_priority_count == actual_high

        # VALIDACAO 3: By perspective preenchido
        assert len(valid_action_plan.by_perspective) >= 1

        # VALIDACAO 4: Summary e timeline presentes
        assert len(valid_action_plan.summary) >= 50
        assert len(valid_action_plan.timeline_summary) >= 30

    def test_action_items_completeness(self, valid_action_items):
        """
        TESTE E2E: Validacao de campos dos ActionItems.
        """
        for item in valid_action_items:
            # Campos obrigatorios
            assert len(item.action_title) >= 10
            assert len(item.description) >= 50
            assert item.perspective in [
                "Financeira",
                "Clientes",
                "Processos Internos",
                "Aprendizado e Crescimento",
            ]
            assert item.priority in ["HIGH", "MEDIUM", "LOW"]
            assert item.effort in ["HIGH", "MEDIUM", "LOW"]
            assert len(item.responsible) >= 3
            assert item.start_date is not None
            assert item.due_date is not None

            # Datas validas
            start = datetime.strptime(item.start_date, "%Y-%m-%d")
            due = datetime.strptime(item.due_date, "%Y-%m-%d")
            assert due >= start, f"Due date antes de start date: {item.action_title}"


# ============================================================================
# TESTES E2E - SERIALIZACAO
# ============================================================================


class TestSerializationE2E:
    """Testes E2E de serializacao para persistencia."""

    @pytest.mark.asyncio
    async def test_milestone_report_serialization(self, valid_action_plan, mock_llm):
        """
        TESTE E2E: Serializacao de MilestoneTrackerReport.
        """
        tool = MilestoneTrackerTool(llm=mock_llm)

        report = await tool.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-12-15",
        )

        # Serializar
        report_dict = report.model_dump()

        # VALIDACAO 1: Dict gerado
        assert isinstance(report_dict, dict)
        assert "milestones" in report_dict
        assert "total_milestones" in report_dict
        assert "overall_progress" in report_dict

        # VALIDACAO 2: Deserializar
        restored = MilestoneTrackerReport(**report_dict)
        assert restored.total_milestones == report.total_milestones
        assert restored.overall_progress == report.overall_progress

        # VALIDACAO 3: Milestones individuais preservados
        assert len(restored.milestones) == len(report.milestones)
        for orig, rest in zip(report.milestones, restored.milestones):
            assert orig.name == rest.name
            assert orig.status == rest.status
            assert orig.progress_percent == rest.progress_percent

    def test_action_plan_serialization(self, valid_action_plan):
        """
        TESTE E2E: Serializacao de ActionPlan.
        """
        # Serializar
        plan_dict = valid_action_plan.model_dump()

        # VALIDACAO 1: Dict gerado
        assert isinstance(plan_dict, dict)
        assert "action_items" in plan_dict
        assert "total_actions" in plan_dict

        # VALIDACAO 2: Deserializar
        restored = ActionPlan(**plan_dict)
        assert restored.total_actions == valid_action_plan.total_actions
        assert len(restored.action_items) == len(valid_action_plan.action_items)


# ============================================================================
# TESTES E2E - INTEGRACAO
# ============================================================================


class TestIntegrationE2E:
    """Testes E2E de integracao entre componentes."""

    @pytest.mark.asyncio
    async def test_action_plan_to_milestones_pipeline(self, valid_action_plan, mock_llm):
        """
        TESTE E2E: Pipeline completo Action Plan -> Milestones.

        Simula fluxo real de geracao de milestones a partir de action plan.
        """
        # ETAPA 1: Validar action plan
        assert valid_action_plan.total_actions >= 3
        assert valid_action_plan.high_priority_count >= 1

        # ETAPA 2: Gerar milestones
        tracker = MilestoneTrackerTool(llm=mock_llm)
        report = await tracker.generate_milestones_from_action_plan(
            action_plan=valid_action_plan,
            current_date="2025-12-15",
        )

        # ETAPA 3: Validar mapeamento 1:1
        assert report.total_milestones == valid_action_plan.total_actions

        # ETAPA 4: Verificar que cada action item tem milestone
        action_titles = {a.action_title for a in valid_action_plan.action_items}
        milestone_refs = {m.action_item_ref for m in report.milestones}

        for title in action_titles:
            assert title in milestone_refs, f"Action item sem milestone: {title}"

        # ETAPA 5: Verificar responsaveis preservados
        for action in valid_action_plan.action_items:
            milestone = next(
                (m for m in report.milestones if m.action_item_ref == action.action_title), None
            )
            assert milestone is not None
            assert milestone.responsible == action.responsible

        print("\n[OK] Pipeline Action Plan -> Milestones")
        print(
            f"[OK] {valid_action_plan.total_actions} actions -> {report.total_milestones} milestones"
        )
        print("[OK] Responsaveis preservados: 100%")
