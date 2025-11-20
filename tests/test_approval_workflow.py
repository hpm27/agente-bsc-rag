"""
Testes para FASE 2.8 - APPROVAL State (approval_handler + route_by_approval).

Validações:
1. approval_handler processa APPROVED corretamente
2. approval_handler processa REJECTED corretamente
3. route_by_approval roteia APPROVED -> END
4. route_by_approval roteia REJECTED -> discovery
5. Fallback para diagnostic ausente

CHECKLIST [[memory:9969868]] APLICADO:
- [OK] Assinatura completa lida via grep
- [OK] Tipo retorno verificado (dict[str, Any])
- [OK] Dados válidos com MARGEM DE SEGURANÇA

Created: 2025-10-16 (FASE 2.8)
"""

from __future__ import annotations

from typing import Any

import pytest

from src.graph.consulting_states import ApprovalStatus, ConsultingPhase
from src.graph.states import BSCState
from src.graph.workflow import BSCWorkflow

# ===== FIXTURES =====


@pytest.fixture
def valid_diagnostic() -> dict[str, Any]:
    """Diagnostic completo válido (4 perspectivas BSC)."""
    return {
        "financial": {
            "current_state": "EBITDA 15%, meta 20%",
            "gaps": ["Margem baixa"],
            "opportunities": ["Otimizar custos"],
            "priority": "HIGH",
        },
        "customer": {
            "current_state": "NPS 45, meta 75",
            "gaps": ["Satisfação baixa"],
            "opportunities": ["Melhorar atendimento"],
            "priority": "HIGH",
        },
        "process": {
            "current_state": "Processos manuais",
            "gaps": ["Eficiência baixa"],
            "opportunities": ["Automatizar"],
            "priority": "MEDIUM",
        },
        "learning": {
            "current_state": "Treinamento ad-hoc",
            "gaps": ["Sem desenvolvimento estruturado"],
            "opportunities": ["Programa de capacitação"],
            "priority": "MEDIUM",
        },
        "recommendations": [
            {"title": "Otimização de Custos", "impact": "HIGH", "effort": "MEDIUM"}
        ],
    }


@pytest.fixture
def workflow():
    """Instância BSCWorkflow."""
    return BSCWorkflow()


# ===== TESTES approval_handler =====


def test_approval_handler_approved(workflow, valid_diagnostic):
    """Teste 1: approval_handler processa APPROVED corretamente."""
    state = BSCState(
        query="Teste aprovação",
        diagnostic=valid_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
        approval_feedback="Diagnóstico aprovado, excelente trabalho!",
    )

    result = workflow.approval_handler(state)

    assert result["approval_status"] == ApprovalStatus.APPROVED
    assert result["approval_feedback"] == "Diagnóstico aprovado, excelente trabalho!"
    assert result["current_phase"] == ConsultingPhase.APPROVAL_PENDING


def test_approval_handler_rejected(workflow, valid_diagnostic):
    """Teste 2: approval_handler processa REJECTED corretamente."""
    state = BSCState(
        query="Teste rejeição",
        diagnostic=valid_diagnostic,
        approval_status=ApprovalStatus.REJECTED,
        approval_feedback="Precisa mais detalhes na perspectiva financeira",
    )

    result = workflow.approval_handler(state)

    assert result["approval_status"] == ApprovalStatus.REJECTED
    assert result["approval_feedback"] == "Precisa mais detalhes na perspectiva financeira"
    assert result["current_phase"] == ConsultingPhase.APPROVAL_PENDING


def test_approval_handler_diagnostic_ausente(workflow):
    """Teste 5: Fallback quando diagnostic ausente."""
    state = BSCState(
        query="Teste sem diagnostic",
        diagnostic=None,  # Ausente!
        approval_status=ApprovalStatus.PENDING,
    )

    result = workflow.approval_handler(state)

    assert result["approval_status"] == ApprovalStatus.REJECTED
    assert "ausente ou incompleto" in result["approval_feedback"].lower()


# ===== TESTES route_by_approval =====


def test_route_by_approval_approved(workflow):
    """Teste 3: route_by_approval roteia APPROVED -> END."""
    state = BSCState(query="Teste routing approved", approval_status=ApprovalStatus.APPROVED)

    next_node = workflow.route_by_approval(state)

    assert next_node == "end"


def test_route_by_approval_rejected(workflow):
    """Teste 4: route_by_approval roteia REJECTED -> discovery."""
    state = BSCState(query="Teste routing rejected", approval_status=ApprovalStatus.REJECTED)

    next_node = workflow.route_by_approval(state)

    assert next_node == "discovery"


def test_route_by_approval_modified(workflow):
    """Teste extra: route_by_approval roteia MODIFIED -> discovery."""
    state = BSCState(query="Teste routing modified", approval_status=ApprovalStatus.MODIFIED)

    next_node = workflow.route_by_approval(state)

    assert next_node == "discovery"


def test_route_by_approval_timeout(workflow):
    """Teste extra: route_by_approval roteia TIMEOUT -> discovery."""
    state = BSCState(query="Teste routing timeout", approval_status=ApprovalStatus.TIMEOUT)

    next_node = workflow.route_by_approval(state)

    assert next_node == "discovery"


def test_route_by_approval_pending_fallback(workflow):
    """Teste extra: route_by_approval PENDING -> END (fallback)."""
    state = BSCState(query="Teste routing pending", approval_status=ApprovalStatus.PENDING)

    next_node = workflow.route_by_approval(state)

    assert next_node == "end"


# ===== VALIDAÇÃO INTEGRAÇÃO (MOCK) =====


def test_approval_persistencia_mem0(workflow, valid_diagnostic):
    """Teste extra: Validar que approval_status e feedback são retornados para sincronização Mem0."""
    state = BSCState(
        query="Teste persistência",
        diagnostic=valid_diagnostic,
        approval_status=ApprovalStatus.APPROVED,
        approval_feedback="Diagnóstico excelente, prosseguir para implementação",
    )

    result = workflow.approval_handler(state)

    # Validar que campos necessários para Mem0 estão presentes
    assert "approval_status" in result
    assert "approval_feedback" in result
    assert result["approval_status"] == ApprovalStatus.APPROVED
    assert len(result["approval_feedback"]) > 20  # Feedback não trivial
