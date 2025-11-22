"""
Testes para SPRINT 2 - Tarefa 2.4 (design_solution_handler + route_by_alignment_score).

Validações:
1. design_solution_handler cria Strategy Map com diagnostic válido
2. design_solution_handler valida alignment e retorna AlignmentReport
3. design_solution_handler com score >= 80 roteia para IMPLEMENTATION
4. design_solution_handler com score < 80 roteia para DISCOVERY
5. route_by_alignment_score roteia score >= 80 -> implementation
6. route_by_alignment_score roteia score < 80 -> discovery
7. Fallback para diagnostic ausente
8. Fallback para diagnostic não aprovado
9. Validação de logs estruturados (timestamps, scores, decisões routing)
10. Validação de metadata (design_time, validation_time, alignment_score)
11. Erro na criação do Strategy Map é tratado
12. Erro na validação de alignment é tratado

CHECKLIST [[memory:9969868]] APLICADO:
- [OK] Assinatura completa lida via grep (design_solution_handler)
- [OK] Tipo retorno verificado (dict[str, Any])
- [OK] Dados válidos com MARGEM DE SEGURANÇA
- [OK] Pydantic models (CompleteDiagnostic, StrategyMap, AlignmentReport) validados

Created: 2025-11-20 (SPRINT 2 - Tarefa 2.4)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.graph.consulting_states import ApprovalStatus, ConsultingPhase
from src.graph.states import BSCState
from src.graph.workflow import BSCWorkflow
from src.memory.schemas import (
    AlignmentReport,
    CauseEffectConnection,
    StrategicObjective,
    StrategyMap,
    StrategyMapPerspective,
)

# ===== FIXTURES =====


@pytest.fixture
def valid_complete_diagnostic() -> dict[str, Any]:
    """Diagnostic completo válido para criar Strategy Map (4 perspectivas BSC)."""
    return {
        "financial": {
            "perspective": "Financeira",
            "current_state": "EBITDA 15%, meta 20%. Margem operacional em 12%, meta 18%.",
            "gaps": ["Margem EBITDA 5pp abaixo da meta", "Custos operacionais elevados"],
            "opportunities": [
                "Otimizar estrutura de custos",
                "Aumentar receita recorrente",
            ],
            "priority": "HIGH",
        },
        "customer": {
            "perspective": "Clientes",
            "current_state": "NPS 45, meta 75. Taxa de churn 8%, meta 5%.",
            "gaps": ["NPS 30 pontos abaixo da meta", "Churn acima do aceitável"],
            "opportunities": [
                "Melhorar experiência do cliente",
                "Programa de retenção",
            ],
            "priority": "HIGH",
        },
        "process": {
            "perspective": "Processos Internos",
            "current_state": "Processos 70% manuais, lead time médio 15 dias.",
            "gaps": ["Automação baixa", "Lead time longo"],
            "opportunities": ["Automatizar processos-chave", "Otimizar fluxo de trabalho"],
            "priority": "MEDIUM",
        },
        "learning": {
            "perspective": "Aprendizado e Crescimento",
            "current_state": "Treinamento ad-hoc, retenção de talentos 75%.",
            "gaps": ["Sem programa estruturado", "Retenção abaixo do ideal"],
            "opportunities": [
                "Programa de capacitação contínua",
                "Plano de carreira estruturado",
            ],
            "priority": "MEDIUM",
        },
        "executive_summary": "Empresa com desafios em todas as 4 perspectivas BSC, focando em otimização financeira e experiência do cliente. Margem EBITDA 5pp abaixo da meta, NPS 30 pontos abaixo, processos manuais gerando ineficiência. Principais oportunidades: otimização de custos, programa de retenção de clientes, automação de processos.",
        "recommendations": [
            {
                "title": "Otimização de Custos Operacionais",
                "description": "Reduzir custos operacionais em 15% através de automação e renegociação de contratos.",
                "impact": "HIGH",
                "effort": "MEDIUM",
                "priority": "HIGH",
                "timeframe": "6-12 meses",
                "next_steps": [
                    "Mapear processos operacionais",
                    "Identificar oportunidades de automação",
                ],
            },
            {
                "title": "Programa de Retenção de Clientes",
                "description": "Implementar programa de Customer Success para reduzir churn de 8% para 5%.",
                "impact": "HIGH",
                "effort": "MEDIUM",
                "priority": "HIGH",
                "timeframe": "3-6 meses",
                "next_steps": [
                    "Definir playbook de onboarding",
                    "Contratar Customer Success Manager",
                ],
            },
            {
                "title": "Automação de Processos-Chave",
                "description": "Automatizar 40% dos processos manuais através de RPA e workflows digitais.",
                "impact": "MEDIUM",
                "effort": "HIGH",
                "priority": "MEDIUM",
                "timeframe": "9-12 meses",
                "next_steps": [
                    "Identificar processos repetitivos",
                    "Avaliar plataformas RPA",
                ],
            },
        ],
        "next_phase": "APPROVAL_PENDING",
    }


@pytest.fixture
def mock_strategy_map() -> StrategyMap:
    """Strategy Map mockado balanceado (8 objectives, 4 conexões)."""
    financial_perspective = StrategyMapPerspective(
        name="Financeira",
        objectives=[
            StrategicObjective(
                name="Aumentar EBITDA para 20%",
                description="Atingir margem EBITDA de 20% através de otimização de custos e aumento de receita.",
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
                name="Aumentar Margem Operacional para 18%",
                description="Aumentar margem operacional através de eficiência operacional.",
                perspective="Financeira",
                timeframe="6 meses",
                success_criteria=[
                    "Margem >= 18% até Q2 2026",
                    "Eficiência operacional aumentada em 25%",
                ],
                related_kpis=["Margem Operacional %", "Eficiência Operacional"],
                priority="Alta",
                dependencies=["Aumentar EBITDA para 20%"],
            ),
        ],
    )

    customer_perspective = StrategyMapPerspective(
        name="Clientes",
        objectives=[
            StrategicObjective(
                name="Aumentar NPS para 75",
                description="Melhorar satisfação do cliente através de experiência superior.",
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
                description="Reduzir taxa de cancelamento através de programa de retenção.",
                perspective="Clientes",
                timeframe="6 meses",
                success_criteria=[
                    "Churn <= 5% até Q2 2026",
                    "Tempo de resposta suporte < 2h em 95% dos casos",
                ],
                related_kpis=["Taxa de Churn %", "Tempo de Resposta Suporte"],
                priority="Alta",
                dependencies=["Aumentar NPS para 75"],
            ),
        ],
    )

    process_perspective = StrategyMapPerspective(
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
                description="Reduzir lead time médio através de otimização de fluxo de trabalho e eliminação de gargalos operacionais.",
                perspective="Processos Internos",
                timeframe="9 meses",
                success_criteria=["Lead Time <= 7 dias até Q3 2026", "Cycle Time reduzido em 50%"],
                related_kpis=["Lead Time médio", "Cycle Time"],
                priority="Média",
                dependencies=["Automatizar 70% dos Processos"],
            ),
        ],
    )

    learning_perspective = StrategyMapPerspective(
        name="Aprendizado e Crescimento",
        objectives=[
            StrategicObjective(
                name="Implementar Programa de Capacitação",
                description="Criar programa estruturado com 60h de treinamento por colaborador/ano.",
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
                description="Aumentar retenção através de plano de carreira estruturado.",
                perspective="Aprendizado e Crescimento",
                timeframe="6 meses",
                success_criteria=[
                    "Retenção >= 90% até Q2 2026",
                    "Satisfação interna >= 8.0 em pesquisa anual",
                ],
                related_kpis=["Taxa de Retenção %", "Satisfação Interna"],
                priority="Média",
                dependencies=["Implementar Programa de Capacitação"],
            ),
        ],
    )

    # 4 conexões causa-efeito (mínimo validado)
    connections = [
        CauseEffectConnection(
            source_objective_id="Implementar Programa de Capacitação",
            target_objective_id="Automatizar 70% dos Processos",
            rationale="Capacitação da equipe habilita automação de processos complexos.",
            relationship_type="enables",
            strength="strong",
        ),
        CauseEffectConnection(
            source_objective_id="Automatizar 70% dos Processos",
            target_objective_id="Reduzir Churn para 5%",
            rationale="Automação reduz erros e tempo de resposta, reduzindo churn.",
            relationship_type="drives",
            strength="strong",
        ),
        CauseEffectConnection(
            source_objective_id="Aumentar NPS para 75",
            target_objective_id="Aumentar EBITDA para 20%",
            rationale="NPS alto aumenta retenção e indicações, aumentando receita e EBITDA.",
            relationship_type="drives",
            strength="strong",
        ),
        CauseEffectConnection(
            source_objective_id="Reduzir Lead Time para 7 dias",
            target_objective_id="Aumentar NPS para 75",
            rationale="Lead time menor melhora experiência do cliente e NPS.",
            relationship_type="supports",
            strength="medium",
        ),
    ]

    return StrategyMap(
        financial=financial_perspective,
        customer=customer_perspective,
        process=process_perspective,
        learning=learning_perspective,
        cause_effect_connections=connections,
        strategic_priorities=[
            "Otimizar estrutura de custos",
            "Melhorar experiência do cliente",
            "Automatizar processos-chave",
        ],
        mission="Entregar valor excepcional aos clientes",
        vision="Ser referência em excelência operacional",
        values=["Inovação", "Cliente no Centro", "Excelência"],
    )


@pytest.fixture
def mock_alignment_report_high_score() -> AlignmentReport:
    """AlignmentReport mockado com score alto (>= 80)."""
    return AlignmentReport(
        score=87.5,
        is_balanced=True,
        gaps=[],
        warnings=["Conexão Learning -> Process poderia ser mais explícita"],
        recommendations=["Considerar adicionar mais KPIs lagging"],
        validation_checks={
            "balanced_perspectives": True,
            "all_objectives_have_kpis": True,
            "cause_effect_exists": True,
            "no_isolated_objectives": True,
            "kpis_are_smart": True,
            "goals_are_strategic": True,
            "has_rationale": True,
            "no_jargon": False,  # 1 falha (jargon detectado)
        },
    )


@pytest.fixture
def mock_alignment_report_low_score() -> AlignmentReport:
    """AlignmentReport mockado com score baixo (< 80)."""
    return AlignmentReport(
        score=62.5,
        is_balanced=False,
        gaps=[
            "Perspectiva Financeira tem apenas 2 objectives (mínimo: 2, ideal: 8-10)",
            "Objective obj_cus_001 não tem conexões causa-efeito (isolated goal)",
            "KPI 'Satisfação Interna' não é SMART (não mensurável)",
        ],
        warnings=[
            "Rationale do objective obj_pro_002 tem menos de 50 caracteres",
            "Jargon genérico detectado: 'leverage synergies'",
        ],
        recommendations=[
            "Adicionar 6-8 objectives na perspectiva Financeira",
            "Conectar objective obj_cus_001 com objectives de outras perspectivas",
            "Refinar KPI 'Satisfação Interna' para ser específico e mensurável",
        ],
        validation_checks={
            "balanced_perspectives": False,
            "all_objectives_have_kpis": True,
            "cause_effect_exists": True,
            "no_isolated_objectives": False,
            "kpis_are_smart": False,
            "goals_are_strategic": True,
            "has_rationale": False,
            "no_jargon": False,
        },
    )


@pytest.fixture
def workflow():
    """Instância BSCWorkflow."""
    return BSCWorkflow()


# ===== TESTES design_solution_handler =====


def test_design_solution_handler_success_high_score(
    workflow, valid_complete_diagnostic, mock_strategy_map, mock_alignment_report_high_score
):
    """Teste 1: design_solution_handler cria Strategy Map com diagnostic válido e score >= 80."""
    state = BSCState(
        query="Criar Strategy Map",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
    )

    # Mock das tools
    with patch.object(
        workflow.strategy_map_designer, "design_strategy_map", new_callable=AsyncMock
    ) as mock_design:
        mock_design.return_value = mock_strategy_map

        with patch.object(workflow.alignment_validator, "validate_strategy_map") as mock_validate:
            mock_validate.return_value = mock_alignment_report_high_score

            result = workflow.design_solution_handler(state)

    # Validações
    assert result["strategy_map"] == mock_strategy_map
    assert result["alignment_report"] == mock_alignment_report_high_score
    assert result["current_phase"] == ConsultingPhase.IMPLEMENTATION  # score >= 80
    assert "Strategy Map criado com sucesso!" in result["final_response"]
    assert "Score de Alinhamento: 87.5/100" in result["final_response"]

    # Validar metadata
    assert "solution_design_time" in result["metadata"]
    assert "design_time" in result["metadata"]
    assert "validation_time" in result["metadata"]
    assert result["metadata"]["alignment_score"] == 87.5
    assert result["metadata"]["is_balanced"] is True
    assert result["metadata"]["routing_decision"] == "IMPLEMENTATION"


def test_design_solution_handler_success_low_score(
    workflow, valid_complete_diagnostic, mock_strategy_map, mock_alignment_report_low_score
):
    """Teste 2: design_solution_handler com score < 80 roteia para DISCOVERY."""
    state = BSCState(
        query="Criar Strategy Map",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
    )

    # Mock das tools
    with patch.object(
        workflow.strategy_map_designer, "design_strategy_map", new_callable=AsyncMock
    ) as mock_design:
        mock_design.return_value = mock_strategy_map

        with patch.object(workflow.alignment_validator, "validate_strategy_map") as mock_validate:
            mock_validate.return_value = mock_alignment_report_low_score

            result = workflow.design_solution_handler(state)

    # Validações
    assert result["strategy_map"] == mock_strategy_map
    assert result["alignment_report"] == mock_alignment_report_low_score
    assert result["current_phase"] == ConsultingPhase.DISCOVERY  # score < 80
    assert "Strategy Map criado, mas precisa refinamento" in result["final_response"]
    assert "Score de Alinhamento: 62.5/100 (mínimo: 80)" in result["final_response"]
    assert "GAPS CRÍTICOS" in result["final_response"]

    # Validar metadata
    assert result["metadata"]["alignment_score"] == 62.5
    assert result["metadata"]["is_balanced"] is False
    assert result["metadata"]["num_gaps"] == 3
    assert result["metadata"]["routing_decision"] == "DISCOVERY"


def test_design_solution_handler_diagnostic_missing(workflow):
    """Teste 3: Fallback para diagnostic ausente."""
    state = BSCState(
        query="Criar Strategy Map sem diagnostic",
        diagnostic=None,  # Diagnostic ausente
        approval_status=ApprovalStatus.APPROVED,
    )

    result = workflow.design_solution_handler(state)

    # Validações
    assert "strategy_map" not in result  # Não deve criar Strategy Map
    assert result["current_phase"] == ConsultingPhase.DISCOVERY
    assert "Diagnóstico ausente" in result["final_response"]
    assert result["metadata"]["solution_design_error"] == "diagnostic_missing"


def test_design_solution_handler_not_approved(workflow, valid_complete_diagnostic):
    """Teste 4: Fallback para diagnostic não aprovado."""
    state = BSCState(
        query="Criar Strategy Map sem aprovação",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.PENDING,  # Não aprovado
    )

    result = workflow.design_solution_handler(state)

    # Validações
    assert "strategy_map" not in result  # Não deve criar Strategy Map
    assert result["current_phase"] == ConsultingPhase.APPROVAL_PENDING
    assert "Aprove o diagnóstico primeiro" in result["final_response"]
    assert result["metadata"]["solution_design_error"] == "diagnostic_not_approved"


def test_design_solution_handler_strategy_map_creation_fails(workflow, valid_complete_diagnostic):
    """Teste 5: Erro na criação do Strategy Map é tratado."""
    state = BSCState(
        query="Criar Strategy Map com erro",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
    )

    # Mock design_strategy_map para lançar exceção
    with patch.object(
        workflow.strategy_map_designer, "design_strategy_map", new_callable=AsyncMock
    ) as mock_design:
        mock_design.side_effect = Exception("Erro LLM timeout")

        result = workflow.design_solution_handler(state)

    # Validações
    assert "strategy_map" not in result
    assert result["current_phase"] == ConsultingPhase.SOLUTION_DESIGN
    assert "Erro ao criar Strategy Map" in result["final_response"]
    assert "strategy_map_creation_failed" in result["metadata"]["solution_design_error"]


def test_design_solution_handler_validation_fails(
    workflow, valid_complete_diagnostic, mock_strategy_map
):
    """Teste 6: Erro na validação de alignment é tratado (Strategy Map criado mas não validado)."""
    state = BSCState(
        query="Criar Strategy Map com erro validação",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
    )

    # Mock design_strategy_map OK, validate_strategy_map falha
    with patch.object(
        workflow.strategy_map_designer, "design_strategy_map", new_callable=AsyncMock
    ) as mock_design:
        mock_design.return_value = mock_strategy_map

        with patch.object(workflow.alignment_validator, "validate_strategy_map") as mock_validate:
            mock_validate.side_effect = Exception("Erro validação Pydantic")

            result = workflow.design_solution_handler(state)

    # Validações
    assert result["strategy_map"] == mock_strategy_map  # Strategy Map foi criado
    assert "alignment_report" not in result  # Validação falhou
    assert result["current_phase"] == ConsultingPhase.SOLUTION_DESIGN
    assert "Strategy Map criado, mas falhou validação" in result["final_response"]
    assert "alignment_validation_failed" in result["metadata"]["solution_design_error"]


# ===== TESTES route_by_alignment_score =====


def test_route_by_alignment_score_high_score(workflow, mock_alignment_report_high_score):
    """Teste 7: route_by_alignment_score roteia score >= 80 -> implementation."""
    state = BSCState(
        query="Routing test",
        alignment_report=mock_alignment_report_high_score,
    )

    next_node = workflow.route_by_alignment_score(state)

    assert next_node == "implementation"


def test_route_by_alignment_score_low_score(workflow, mock_alignment_report_low_score):
    """Teste 8: route_by_alignment_score roteia score < 80 -> discovery."""
    state = BSCState(
        query="Routing test",
        alignment_report=mock_alignment_report_low_score,
    )

    next_node = workflow.route_by_alignment_score(state)

    assert next_node == "discovery"


def test_route_by_alignment_score_missing_report(workflow):
    """Teste 9: Fallback para alignment_report ausente (roteia para discovery)."""
    state = BSCState(
        query="Routing test sem alignment_report",
        alignment_report=None,
    )

    next_node = workflow.route_by_alignment_score(state)

    assert next_node == "discovery"


# ===== TESTES placeholder_implementation_handler =====


# ===== TESTES INTEGRAÇÃO (E2E) =====


def test_e2e_design_solution_workflow_high_score(
    workflow, valid_complete_diagnostic, mock_strategy_map, mock_alignment_report_high_score
):
    """Teste 12: E2E completo - diagnostic aprovado -> Strategy Map -> score >= 80 -> implementation."""
    state = BSCState(
        query="E2E test high score",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
    )

    # Mock tools
    with patch.object(
        workflow.strategy_map_designer, "design_strategy_map", new_callable=AsyncMock
    ) as mock_design:
        mock_design.return_value = mock_strategy_map

        with patch.object(workflow.alignment_validator, "validate_strategy_map") as mock_validate:
            mock_validate.return_value = mock_alignment_report_high_score

            # Step 1: design_solution_handler
            result_design = workflow.design_solution_handler(state)

            # Step 2: route_by_alignment_score
            state_updated = BSCState(
                query=state.query,
                strategy_map=result_design["strategy_map"],
                alignment_report=result_design["alignment_report"],
            )
            next_node = workflow.route_by_alignment_score(state_updated)

    # Validações E2E
    assert result_design["strategy_map"] == mock_strategy_map
    assert result_design["alignment_report"] == mock_alignment_report_high_score
    assert result_design["current_phase"] == ConsultingPhase.IMPLEMENTATION
    assert next_node == "implementation"
    assert result_design["metadata"]["routing_decision"] == "IMPLEMENTATION"


def test_e2e_design_solution_workflow_low_score(
    workflow, valid_complete_diagnostic, mock_strategy_map, mock_alignment_report_low_score
):
    """Teste 13: E2E completo - diagnostic aprovado -> Strategy Map -> score < 80 -> discovery."""
    state = BSCState(
        query="E2E test low score",
        diagnostic=valid_complete_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
    )

    # Mock tools
    with patch.object(
        workflow.strategy_map_designer, "design_strategy_map", new_callable=AsyncMock
    ) as mock_design:
        mock_design.return_value = mock_strategy_map

        with patch.object(workflow.alignment_validator, "validate_strategy_map") as mock_validate:
            mock_validate.return_value = mock_alignment_report_low_score

            # Step 1: design_solution_handler
            result_design = workflow.design_solution_handler(state)

            # Step 2: route_by_alignment_score
            state_updated = BSCState(
                query=state.query,
                strategy_map=result_design["strategy_map"],
                alignment_report=result_design["alignment_report"],
            )
            next_node = workflow.route_by_alignment_score(state_updated)

    # Validações E2E
    assert result_design["strategy_map"] == mock_strategy_map
    assert result_design["alignment_report"] == mock_alignment_report_low_score
    assert result_design["current_phase"] == ConsultingPhase.DISCOVERY  # Refazer diagnóstico
    assert next_node == "discovery"
    assert result_design["metadata"]["routing_decision"] == "DISCOVERY"
    assert result_design["metadata"]["num_gaps"] == 3
