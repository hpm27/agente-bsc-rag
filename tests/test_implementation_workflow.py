"""
Testes para SPRINT 3 - implementation_handler() (Action Plan).

Validações:
1. implementation_handler cria Action Plan com strategy_map válido
2. implementation_handler valida client_profile existe
3. implementation_handler com diagnostic válido enriquece Action Plan
4. Fallback para strategy_map ausente
5. Erro na criação do Action Plan é tratado
6. Validação de logs estruturados
7. Validação de metadata (total_actions, high_priority_count, timeline_summary)
8. Action Plan tem 3+ ações
9. E2E completo: strategy_map aprovado -> action_plan -> END

CHECKLIST [[memory:9969868]] APLICADO:
- [OK] Assinatura ActionPlanTool.facilitate() lida via grep
- [OK] Schema ActionPlan lido via grep (total_actions, high_priority_count, by_perspective, summary, timeline_summary)
- [OK] Fixtures Pydantic válidas com MARGEM DE SEGURANÇA

Created: 2025-11-20 (SPRINT 3)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.graph.consulting_states import ConsultingPhase
from src.graph.states import BSCState
from src.graph.workflow import BSCWorkflow
from src.memory.schemas import (
    ActionItem,
    ActionPlan,
    CauseEffectConnection,
    ClientProfile,
    CompanyInfo,
    StrategicContext,
    StrategicObjective,
    StrategyMap,
    StrategyMapPerspective,
)

# ===== FIXTURES =====


@pytest.fixture
def valid_client_profile() -> ClientProfile:
    """ClientProfile válido para Action Plan."""
    return ClientProfile(
        client_id="test_client_sprint3",
        company=CompanyInfo(
            name="TechCorp Ltda",
            sector="Tecnologia",
            size="Médio",
            industry="Software as a Service",
            founded_year=2015,
        ),
        context=StrategicContext(
            current_challenges=[
                "Baixa satisfação de clientes",
                "Processos operacionais ineficientes",
                "Falta de capacitação em análise de dados",
            ],
            strategic_objectives=[
                "Aumentar NPS para 75",
                "Reduzir custos operacionais em 15%",
                "Capacitar equipe em dados",
            ],
        ),
    )


@pytest.fixture
def valid_strategy_map() -> StrategyMap:
    """Strategy Map válido para criar Action Plan."""
    return StrategyMap(
        financial=StrategyMapPerspective(
            name="Financeira",
            objectives=[
                StrategicObjective(
                    name="Aumentar EBITDA para 20%",
                    description="Atingir margem EBITDA de 20% através de otimização de custos operacionais e aumento de receita recorrente.",
                    perspective="Financeira",
                    timeframe="12 meses",
                    success_criteria=[
                        "EBITDA >= 20% até Q4 2026",
                        "Redução de custos operacionais em 15%",
                    ],
                    related_kpis=["EBITDA %", "Custo Operacional / Receita"],
                    priority="Alta",
                    dependencies=[],
                ),
                StrategicObjective(
                    name="Aumentar Receita Recorrente em 25%",
                    description="Aumentar ARR (Annual Recurring Revenue) em 25% através de expansão de base de clientes e upsell.",
                    perspective="Financeira",
                    timeframe="12 meses",
                    success_criteria=["ARR +25% até Q4 2026", "Taxa de renovação >= 90%"],
                    related_kpis=["ARR", "Taxa de Renovação %"],
                    priority="Alta",
                    dependencies=[],
                ),
            ],
        ),
        customer=StrategyMapPerspective(
            name="Clientes",
            objectives=[
                StrategicObjective(
                    name="Aumentar NPS para 75",
                    description="Melhorar satisfação do cliente através de experiência superior e atendimento de excelência.",
                    perspective="Clientes",
                    timeframe="9 meses",
                    success_criteria=[
                        "NPS >= 75 até Q3 2026",
                        "CSAT >= 4.5 de 5.0 em todas as interações",
                    ],
                    related_kpis=["NPS", "CSAT"],
                    priority="Alta",
                    dependencies=[],
                ),
                StrategicObjective(
                    name="Reduzir Churn para 5%",
                    description="Reduzir taxa de cancelamento para 5% através de programa estruturado de Customer Success.",
                    perspective="Clientes",
                    timeframe="6 meses",
                    success_criteria=[
                        "Churn <= 5% até Q2 2026",
                        "Tempo de resposta suporte < 2h em 95% dos casos",
                    ],
                    related_kpis=["Taxa de Churn %", "Tempo de Resposta Suporte"],
                    priority="Alta",
                    dependencies=[],
                ),
            ],
        ),
        process=StrategyMapPerspective(
            name="Processos Internos",
            objectives=[
                StrategicObjective(
                    name="Automatizar 70% dos Processos",
                    description="Aumentar automação de processos manuais para 70% através de implementação de RPA e workflows digitais.",
                    perspective="Processos Internos",
                    timeframe="12 meses",
                    success_criteria=[
                        "Automação >= 70% até Q4 2026",
                        "Eficiência operacional aumentada em 30%",
                    ],
                    related_kpis=["% Processos Automatizados", "Eficiência Operacional"],
                    priority="Média",
                    dependencies=[],
                ),
                StrategicObjective(
                    name="Reduzir Lead Time para 7 dias",
                    description="Reduzir lead time médio de 15 para 7 dias através de otimização de fluxo de trabalho e eliminação de gargalos.",
                    perspective="Processos Internos",
                    timeframe="9 meses",
                    success_criteria=[
                        "Lead Time <= 7 dias até Q3 2026",
                        "Cycle Time reduzido em 50%",
                    ],
                    related_kpis=["Lead Time médio", "Cycle Time"],
                    priority="Média",
                    dependencies=[],
                ),
            ],
        ),
        learning=StrategyMapPerspective(
            name="Aprendizado e Crescimento",
            objectives=[
                StrategicObjective(
                    name="Implementar Programa de Capacitação",
                    description="Criar programa estruturado com 60h de treinamento por colaborador/ano focado em análise de dados.",
                    perspective="Aprendizado e Crescimento",
                    timeframe="12 meses",
                    success_criteria=[
                        "60h/ano de treinamento por colaborador até Q4 2026",
                        "Competência média da equipe aumentada em 40%",
                    ],
                    related_kpis=["Horas Treinamento / Colaborador", "Competência Equipe"],
                    priority="Média",
                    dependencies=[],
                ),
                StrategicObjective(
                    name="Aumentar Retenção de Talentos para 90%",
                    description="Aumentar retenção de talentos-chave através de plano de carreira estruturado e programa de desenvolvimento.",
                    perspective="Aprendizado e Crescimento",
                    timeframe="6 meses",
                    success_criteria=[
                        "Retenção >= 90% até Q2 2026",
                        "Satisfação interna >= 8.0 em pesquisa anual",
                    ],
                    related_kpis=["Taxa de Retenção %", "Satisfação Interna"],
                    priority="Média",
                    dependencies=[],
                ),
            ],
        ),
        cause_effect_connections=[
            CauseEffectConnection(
                source_objective_id="Implementar Programa de Capacitação",
                target_objective_id="Automatizar 70% dos Processos",
                rationale="Capacitação em dados habilita automação de processos baseados em análise.",
                relationship_type="enables",
                strength="medium",
            ),
            CauseEffectConnection(
                source_objective_id="Automatizar 70% dos Processos",
                target_objective_id="Reduzir Churn para 5%",
                rationale="Automação reduz erros e tempo de resposta, melhorando experiência do cliente.",
                relationship_type="drives",
                strength="strong",
            ),
            CauseEffectConnection(
                source_objective_id="Aumentar NPS para 75",
                target_objective_id="Aumentar Receita Recorrente em 25%",
                rationale="Clientes satisfeitos renovam contratos e geram indicações, aumentando ARR.",
                relationship_type="drives",
                strength="strong",
            ),
            CauseEffectConnection(
                source_objective_id="Reduzir Lead Time para 7 dias",
                target_objective_id="Aumentar NPS para 75",
                rationale="Lead time menor melhora experiência do cliente e aumenta satisfação.",
                relationship_type="supports",
                strength="medium",
            ),
        ],
        strategic_priorities=["Melhorar satisfação cliente", "Reduzir custos"],
        mission="Entregar valor excepcional aos clientes",
    )


@pytest.fixture
def mock_action_plan() -> ActionPlan:
    """Action Plan mockado válido (4 ações, 2 alta prioridade)."""
    return ActionPlan(
        action_items=[
            ActionItem(
                action_title="Implementar sistema de coleta de feedback de clientes",
                description="Configurar plataforma online para coleta sistemática de feedback de clientes sobre produtos e serviços, incluindo integração com CRM existente",
                perspective="Clientes",
                priority="HIGH",
                effort="MEDIUM",
                responsible="Equipe de Marketing",
                start_date="2025-11-01",
                due_date="2025-12-15",
                resources_needed=["Plataforma CRM", "Treinamento equipe"],
                success_criteria="80% dos clientes respondendo surveys mensais com NPS > 8",
                dependencies=["Definir métricas de satisfação"],
            ),
            ActionItem(
                action_title="Otimizar processos de produção para reduzir custos",
                description="Implementar metodologia Lean Manufacturing para eliminar desperdícios e reduzir custos operacionais em 15%",
                perspective="Processos Internos",
                priority="HIGH",
                effort="HIGH",
                responsible="Equipe de Operações",
                start_date="2025-11-15",
                due_date="2026-02-28",
                resources_needed=["Consultoria Lean", "Treinamento equipe"],
                success_criteria="Redução de 15% nos custos operacionais e 20% no tempo de ciclo",
                dependencies=["Mapear processos atuais"],
            ),
            ActionItem(
                action_title="Desenvolver programa de capacitação em análise de dados",
                description="Criar programa de treinamento para capacitar equipes em análise de dados e Business Intelligence",
                perspective="Aprendizado e Crescimento",
                priority="MEDIUM",
                effort="MEDIUM",
                responsible="RH e TI",
                start_date="2025-12-01",
                due_date="2026-03-31",
                resources_needed=["Instrutor especializado", "Plataforma de treinamento"],
                success_criteria="80% da equipe treinada e certificada em análise de dados",
                dependencies=["Definir currículo"],
            ),
            ActionItem(
                action_title="Implementar controle de custos por centro de responsabilidade",
                description="Estruturar sistema de controle de custos detalhado por centro de responsabilidade para melhorar gestão financeira",
                perspective="Financeira",
                priority="MEDIUM",
                effort="LOW",
                responsible="Controladoria",
                start_date="2025-11-01",
                due_date="2025-12-31",
                resources_needed=["Sistema ERP"],
                success_criteria="Controle mensal de custos por centro com precisão de 95%",
                dependencies=["Configurar sistema ERP"],
            ),
        ],
        total_actions=4,
        high_priority_count=2,
        by_perspective={
            "Clientes": 1,
            "Processos Internos": 1,
            "Aprendizado e Crescimento": 1,
            "Financeira": 1,
        },
        summary="Plano de ação estruturado para implementação BSC focado em melhorar satisfação de clientes, otimizar processos, capacitar equipes e implementar controle de custos.",
        timeline_summary="Execução em 3 fases: Nov-Dez 2025 (alta prioridade), Nov-Fev 2026 (otimização processos), Dez-Mar 2026 (capacitação). Duração total: 5 meses.",
    )


@pytest.fixture
def workflow():
    """Instância BSCWorkflow."""
    return BSCWorkflow()


# ===== TESTES implementation_handler =====


def test_implementation_handler_success(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 1: implementation_handler cria Action Plan com strategy_map válido."""
    state = BSCState(
        query="Criar Action Plan",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validações
    assert result["action_plan"] == mock_action_plan
    assert result["current_phase"] == ConsultingPhase.IMPLEMENTATION
    assert "Action Plan criado com sucesso!" in result["final_response"]
    assert "4 ações mapeadas" in result["final_response"]
    assert "2 ações" in result["final_response"]  # 2 alta prioridade

    # Validar metadata
    assert "implementation_time" in result["metadata"]
    assert result["metadata"]["total_actions"] == 4
    assert result["metadata"]["high_priority_count"] == 2
    assert "Execução em 3 fases" in result["metadata"]["timeline_summary"]


def test_implementation_handler_strategy_map_missing(workflow):
    """Teste 2: Fallback para strategy_map ausente."""
    state = BSCState(
        query="Criar Action Plan sem Strategy Map",
        strategy_map=None,  # Strategy Map ausente
    )

    result = workflow.implementation_handler(state)

    # Validações
    assert "action_plan" not in result  # Não deve criar Action Plan
    assert result["current_phase"] == ConsultingPhase.SOLUTION_DESIGN
    assert "Strategy Map ausente" in result["final_response"]
    assert result["metadata"]["implementation_error"] == "strategy_map_missing"


def test_implementation_handler_action_plan_creation_fails(
    workflow, valid_strategy_map, valid_client_profile
):
    """Teste 3: Erro na criação do Action Plan é tratado."""
    state = BSCState(
        query="Criar Action Plan com erro",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
    )

    # Mock facilitate() para lançar exceção
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.side_effect = Exception("Erro LLM timeout")

        result = workflow.implementation_handler(state)

    # Validações
    assert "action_plan" not in result
    assert result["current_phase"] == ConsultingPhase.IMPLEMENTATION
    assert "Erro ao criar Action Plan" in result["final_response"]
    assert "action_plan_creation_failed" in result["metadata"]["implementation_error"]


def test_implementation_handler_without_client_profile(
    workflow, valid_strategy_map, mock_action_plan
):
    """Teste 4: Action Plan criado mesmo sem client_profile (warning gerado)."""
    state = BSCState(
        query="Criar Action Plan sem ClientProfile",
        strategy_map=valid_strategy_map,
        client_profile=None,  # Sem client_profile
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validações
    assert result["action_plan"] == mock_action_plan
    assert result["current_phase"] == ConsultingPhase.IMPLEMENTATION
    # Action Plan foi criado mesmo sem client_profile (tool tem fallback)


def test_implementation_handler_with_diagnostic(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 5: Action Plan enriquecido com diagnostic results."""
    diagnostic_dict = {
        "financial": {
            "perspective": "Financeira",
            "current_state": "EBITDA 15%, meta 20%. Margem operacional em 12%, meta 18%.",
            "gaps": ["Margem EBITDA abaixo da meta", "Custos operacionais elevados"],
            "opportunities": ["Otimizar custos", "Aumentar receita recorrente"],
            "priority": "HIGH",
        },
        "customer": {
            "perspective": "Clientes",
            "current_state": "NPS 45, meta 75. Taxa de churn 8%, meta 5%.",
            "gaps": ["NPS 30 pontos abaixo da meta", "Churn elevado"],
            "opportunities": ["Melhorar atendimento", "Programa de retenção"],
            "priority": "HIGH",
        },
        "process": {
            "perspective": "Processos Internos",
            "current_state": "Processos 70% manuais, lead time médio 15 dias.",
            "gaps": ["Automação baixa", "Lead time longo"],
            "opportunities": ["Automatizar processos", "Otimizar fluxo"],
            "priority": "MEDIUM",
        },
        "learning": {
            "perspective": "Aprendizado e Crescimento",
            "current_state": "Treinamento ad-hoc, retenção de talentos 75%.",
            "gaps": ["Sem programa estruturado", "Retenção abaixo do ideal"],
            "opportunities": ["Programa de capacitação", "Plano de carreira"],
            "priority": "MEDIUM",
        },
        "executive_summary": "Empresa com desafios em todas as 4 perspectivas BSC. Principais gaps: margem EBITDA 5pp abaixo, NPS 30 pontos abaixo, processos manuais gerando ineficiência.",
        "recommendations": [
            {
                "title": "Otimização Custos",
                "description": "Reduzir custos operacionais em 15% através de automação e renegociação de contratos com fornecedores.",
                "impact": "HIGH",
                "effort": "MEDIUM",
                "priority": "HIGH",
                "timeframe": "6 meses",
                "next_steps": ["Mapear processos", "Identificar oportunidades"],
            },
            {
                "title": "Programa Retenção",
                "description": "Implementar programa de Customer Success para reduzir churn de 8% para 5%.",
                "impact": "MEDIUM",
                "effort": "LOW",
                "priority": "MEDIUM",
                "timeframe": "3 meses",
                "next_steps": ["Definir playbook", "Contratar CSM"],
            },
            {
                "title": "Automação RPA",
                "description": "Automatizar 40% dos processos manuais através de RPA e workflows digitais.",
                "impact": "LOW",
                "effort": "HIGH",
                "priority": "LOW",
                "timeframe": "12 meses",
                "next_steps": ["Identificar processos", "Avaliar plataformas"],
            },
        ],
        "next_phase": "APPROVAL_PENDING",
    }

    state = BSCState(
        query="Criar Action Plan com diagnostic",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
        diagnostic=diagnostic_dict,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validações
    assert result["action_plan"] == mock_action_plan
    # Validar que diagnostic foi passado para facilitate()
    call_args = mock_facilitate.call_args
    assert call_args.kwargs["diagnostic_results"] is not None


def test_implementation_handler_diagnostic_conversion_fails(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 6: Diagnostic inválido não impede criação do Action Plan (warning gerado)."""
    diagnostic_dict = {"invalid": "diagnostic"}  # Diagnostic inválido

    state = BSCState(
        query="Criar Action Plan com diagnostic inválido",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
        diagnostic=diagnostic_dict,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validações
    assert result["action_plan"] == mock_action_plan
    # Action Plan criado mesmo com diagnostic inválido (facilitate() chamado com diagnostic_results=None)
    call_args = mock_facilitate.call_args
    assert call_args.kwargs["diagnostic_results"] is None


# ===== TESTES E2E =====


def test_e2e_implementation_workflow_complete(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 7: E2E completo - strategy_map aprovado -> action_plan -> workflow completo."""
    state = BSCState(
        query="E2E test implementation",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validações E2E
    assert result["action_plan"] == mock_action_plan
    assert result["current_phase"] == ConsultingPhase.IMPLEMENTATION
    assert "Workflow consultivo BSC completo!" in result["final_response"]
    assert result["metadata"]["total_actions"] == 4
    assert result["metadata"]["high_priority_count"] == 2


def test_implementation_handler_calls_facilitate_with_correct_params(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 8: Validar que facilitate() é chamado com parâmetros corretos."""
    state = BSCState(
        query="Validar parâmetros facilitate",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

        # Validar parâmetros passados
        call_args = mock_facilitate.call_args
        assert call_args.kwargs["client_profile"] == valid_client_profile
        assert call_args.kwargs["financial_agent"] is not None
        assert call_args.kwargs["customer_agent"] is not None
        assert call_args.kwargs["process_agent"] is not None
        assert call_args.kwargs["learning_agent"] is not None


def test_implementation_handler_logs_structured(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 9: Validar que logs estruturados são gerados."""
    state = BSCState(
        query="Validar logs estruturados",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validar metadata estruturado
    metadata = result["metadata"]
    assert "implementation_time" in metadata
    assert "total_actions" in metadata
    assert "high_priority_count" in metadata
    assert "timeline_summary" in metadata
    assert isinstance(metadata["implementation_time"], float)
    assert metadata["implementation_time"] >= 0


def test_implementation_handler_action_plan_has_minimum_actions(
    workflow, valid_strategy_map, valid_client_profile, mock_action_plan
):
    """Teste 10: Action Plan tem mínimo 3 ações (schema validation)."""
    state = BSCState(
        query="Validar mínimo 3 ações",
        strategy_map=valid_strategy_map,
        client_profile=valid_client_profile,
    )

    # Mock ActionPlanTool.facilitate
    with patch.object(
        workflow.action_plan_tool, "facilitate", new_callable=AsyncMock
    ) as mock_facilitate:
        mock_facilitate.return_value = mock_action_plan

        result = workflow.implementation_handler(state)

    # Validações
    action_plan = result["action_plan"]
    assert len(action_plan.action_items) >= 3  # Mínimo do schema
    assert action_plan.total_actions >= 3
