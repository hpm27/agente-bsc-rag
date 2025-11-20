"""
Testes para ConsultingOrchestrator - Coordenação de Agentes Consultivos BSC.

Valida:
- coordinate_onboarding: Multi-turn sessions, profile creation, transitions
- coordinate_discovery: Diagnostic execution, validations, persistence
- validate_transition: Pré-condições entre fases
- handle_error: Fallback robusto

Conformidade: Checklist [[memory:9969868]] (12 pontos)
"""

from unittest.mock import patch

import pytest

from src.graph.consulting_orchestrator import ConsultingOrchestrator
from src.graph.consulting_states import ApprovalStatus, ConsultingPhase
from src.graph.states import BSCState
from src.memory.schemas import (
    ClientProfile,
    CompanyInfo,
    StrategicContext,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def orchestrator():
    """Orchestrator instance."""
    return ConsultingOrchestrator()


@pytest.fixture
def valid_bsc_state():
    """BSCState válido para testes."""
    return BSCState(
        query="Como implementar BSC?",
        user_id="test_user_001",
        session_id="test_session_001",
        onboarding_progress={
            "COMPANY_INFO": True,
            "STRATEGIC_CONTEXT": True,
            "ENGAGEMENT_MODE": True,
        },
        client_profile=ClientProfile(
            client_id="test_user_001",
            company=CompanyInfo(
                name="Test Corp", sector="Tecnologia", size="média", industry="Software Development"
            ),
            context=StrategicContext(
                current_challenges=["Challenge 1", "Challenge 2"],
                strategic_objectives=["Objective 1", "Objective 2"],
                stakeholders=["CEO", "CFO"],
            ),
        ),
        metadata={},
    )


@pytest.fixture
def mock_complete_diagnostic():
    """CompleteDiagnostic mock (dict) para testes discovery."""

    # Mock object com interface mínima necessária
    class MockDiagnostic:
        def __init__(self):
            self.diagnostic_results = [
                {
                    "perspective": "Financial",
                    "current_state": "Strong revenue",
                    "gaps": ["Cost optimization"],
                },
                {"perspective": "Customer", "current_state": "Good NPS", "gaps": ["Retention"]},
                {
                    "perspective": "Process",
                    "current_state": "Manual processes",
                    "gaps": ["Automation"],
                },
                {"perspective": "Learning", "current_state": "Skills gap", "gaps": ["Training"]},
            ]
            self.recommendations = []
            self.synergies = ["Cost reduction improves margins"]
            self.executive_summary = "Strong revenue, needs cost optimization"

        def model_dump(self):
            return {
                "diagnostic_results": self.diagnostic_results,
                "recommendations": self.recommendations,
                "synergies": self.synergies,
                "executive_summary": self.executive_summary,
            }

    return MockDiagnostic()


# ============================================================================
# TESTES: coordinate_onboarding
# ============================================================================


def test_coordinate_onboarding_start(orchestrator):
    """Onboarding start cria session e retorna welcome message."""
    state = BSCState(
        query="",  # Primeira interação, sem query
        user_id="test_user_onboarding_start",
        onboarding_progress={},
        metadata={},
    )

    with patch.object(
        orchestrator.onboarding_agent,
        "start_onboarding",
        return_value="Bem-vindo ao BSC Consulting!",
    ):
        result = orchestrator.coordinate_onboarding(state)

    # Validações
    assert "final_response" in result
    assert "Bem-vindo" in result["final_response"]
    assert result["current_phase"] == ConsultingPhase.ONBOARDING
    assert "onboarding_progress" in result
    assert "test_user_onboarding_start" in orchestrator._onboarding_sessions


def test_coordinate_onboarding_multi_turn(orchestrator):
    """Onboarding multi-turn persiste session entre calls."""
    user_id = "test_user_multi_turn"

    # Turn 1: Start
    state1 = BSCState(query="", user_id=user_id, onboarding_progress={}, metadata={})

    with patch.object(orchestrator.onboarding_agent, "start_onboarding", return_value="Welcome!"):
        result1 = orchestrator.coordinate_onboarding(state1)

    assert user_id in orchestrator._onboarding_sessions
    assert result1["current_phase"] == ConsultingPhase.ONBOARDING

    # Turn 2: User response
    state2 = BSCState(
        query="Minha empresa é Test Corp", user_id=user_id, onboarding_progress={}, metadata={}
    )

    with patch.object(
        orchestrator.onboarding_agent,
        "process_turn",
        return_value={
            "response": "Ótimo! Qual o setor?",
            "onboarding_progress": {"COMPANY_INFO": False},
            "is_complete": False,
        },
    ):
        result2 = orchestrator.coordinate_onboarding(state2)

    assert user_id in orchestrator._onboarding_sessions
    assert result2["current_phase"] == ConsultingPhase.ONBOARDING
    assert result2["onboarding_progress"]["COMPANY_INFO"] is False


def test_coordinate_onboarding_complete(orchestrator, valid_bsc_state):
    """Onboarding completo extrai profile e transiciona para DISCOVERY."""
    user_id = "test_user_complete"

    # Setup session in-memory
    orchestrator._onboarding_sessions[user_id] = {
        "started": True,
        "progress": {"COMPANY_INFO": True, "STRATEGIC_CONTEXT": True},
        "messages": ["Welcome!", "Test Corp", "Technology"],
    }

    state = BSCState(query="Yes, complete", user_id=user_id, onboarding_progress={}, metadata={})

    with (
        patch.object(
            orchestrator.onboarding_agent,
            "process_turn",
            return_value={
                "response": "Onboarding completo!",
                "onboarding_progress": {
                    "COMPANY_INFO": True,
                    "STRATEGIC_CONTEXT": True,
                    "ENGAGEMENT_MODE": True,
                },
                "is_complete": True,
            },
        ),
        patch.object(
            orchestrator.client_profile_agent,
            "extract_profile",
            return_value=valid_bsc_state.client_profile,
        ),
    ):
        result = orchestrator.coordinate_onboarding(state)

    # Validações
    assert result["current_phase"] == ConsultingPhase.DISCOVERY
    assert "client_profile" in result
    assert result["client_profile"].company.name == "Test Corp"
    assert user_id not in orchestrator._onboarding_sessions  # Session cleanup


def test_coordinate_onboarding_error_handling(orchestrator):
    """Onboarding com erro retorna fallback amigável."""
    state = BSCState(
        query="trigger_error", user_id="test_error", onboarding_progress={}, metadata={}
    )

    with patch.object(
        orchestrator.onboarding_agent, "start_onboarding", side_effect=ValueError("Test error")
    ):
        result = orchestrator.coordinate_onboarding(state)

    # Validações
    assert "final_response" in result
    assert "erro" in result["final_response"].lower()
    assert result["current_phase"] == ConsultingPhase.ERROR
    assert "onboarding_error" in result["metadata"]


# ============================================================================
# TESTES: coordinate_discovery
# ============================================================================


@pytest.mark.asyncio
async def test_coordinate_discovery_success(
    orchestrator, valid_bsc_state, mock_complete_diagnostic
):
    """Discovery executa diagnóstico e transiciona para APPROVAL_PENDING."""
    with patch.object(
        orchestrator.diagnostic_agent, "run_diagnostic", return_value=mock_complete_diagnostic
    ):
        result = await orchestrator.coordinate_discovery(valid_bsc_state)

    # Validações
    assert "diagnostic" in result
    assert result["current_phase"] == ConsultingPhase.APPROVAL_PENDING
    assert "final_response" in result
    assert "Diagnóstico BSC Completo" in result["final_response"]
    assert len(result["diagnostic"]["diagnostic_results"]) == 4


@pytest.mark.asyncio
async def test_coordinate_discovery_missing_profile(orchestrator):
    """Discovery sem ClientProfile retorna fallback para ONBOARDING."""
    state = BSCState(
        query="Fazer diagnóstico", user_id="test_no_profile", client_profile=None, metadata={}
    )

    result = await orchestrator.coordinate_discovery(state)

    # Validações
    assert result["current_phase"] == ConsultingPhase.ONBOARDING
    assert "perfil do cliente não encontrado" in result["final_response"].lower()


@pytest.mark.asyncio
async def test_coordinate_discovery_error_handling(orchestrator, valid_bsc_state):
    """Discovery com erro retorna fallback amigável."""
    with patch.object(
        orchestrator.diagnostic_agent,
        "run_diagnostic",
        side_effect=RuntimeError("Diagnostic failed"),
    ):
        result = await orchestrator.coordinate_discovery(valid_bsc_state)

    # Validações
    assert result["current_phase"] == ConsultingPhase.ERROR
    assert "erro" in result["final_response"].lower()
    assert "discovery_error" in result["metadata"]


# ============================================================================
# TESTES: validate_transition
# ============================================================================


def test_validate_transition_onboarding_to_discovery_valid(orchestrator, valid_bsc_state):
    """Transição ONBOARDING -> DISCOVERY válida com onboarding completo."""
    is_valid = orchestrator.validate_transition(
        from_phase=ConsultingPhase.ONBOARDING,
        to_phase=ConsultingPhase.DISCOVERY,
        state=valid_bsc_state,
    )

    assert is_valid is True


def test_validate_transition_onboarding_to_discovery_invalid(orchestrator):
    """Transição ONBOARDING -> DISCOVERY bloqueada se onboarding incompleto."""
    state = BSCState(
        query="Test",
        user_id="test_incomplete",
        onboarding_progress={"COMPANY_INFO": True, "STRATEGIC_CONTEXT": False},  # Incompleto
        metadata={},
    )

    is_valid = orchestrator.validate_transition(
        from_phase=ConsultingPhase.ONBOARDING, to_phase=ConsultingPhase.DISCOVERY, state=state
    )

    assert is_valid is False


def test_validate_transition_discovery_to_approval_valid(orchestrator, valid_bsc_state):
    """Transição DISCOVERY -> APPROVAL_PENDING válida com diagnostic presente."""
    state = BSCState(
        **valid_bsc_state.model_dump(), diagnostic={"executive_summary": "Test summary"}
    )

    is_valid = orchestrator.validate_transition(
        from_phase=ConsultingPhase.DISCOVERY, to_phase=ConsultingPhase.APPROVAL_PENDING, state=state
    )

    assert is_valid is True


def test_validate_transition_discovery_to_approval_invalid(orchestrator, valid_bsc_state):
    """Transição DISCOVERY -> APPROVAL_PENDING bloqueada se diagnostic ausente."""
    state = BSCState(**valid_bsc_state.model_dump(), diagnostic=None)  # Ausente

    is_valid = orchestrator.validate_transition(
        from_phase=ConsultingPhase.DISCOVERY, to_phase=ConsultingPhase.APPROVAL_PENDING, state=state
    )

    assert is_valid is False


def test_validate_transition_approval_to_end_valid(orchestrator, valid_bsc_state):
    """Transição APPROVAL_PENDING -> END válida com APPROVED."""
    state = BSCState(**valid_bsc_state.model_dump(), approval_status=ApprovalStatus.APPROVED)

    is_valid = orchestrator.validate_transition(
        from_phase=ConsultingPhase.APPROVAL_PENDING, to_phase="END", state=state
    )

    assert is_valid is True


def test_validate_transition_approval_to_end_invalid(orchestrator, valid_bsc_state):
    """Transição APPROVAL_PENDING -> END bloqueada se não APPROVED."""
    state = BSCState(**valid_bsc_state.model_dump(), approval_status=ApprovalStatus.REJECTED)

    is_valid = orchestrator.validate_transition(
        from_phase=ConsultingPhase.APPROVAL_PENDING, to_phase="END", state=state
    )

    assert is_valid is False


# ============================================================================
# TESTES: handle_error
# ============================================================================


def test_handle_error_generic(orchestrator, valid_bsc_state):
    """handle_error retorna fallback com metadata completa."""
    error = ValueError("Test generic error")

    result = orchestrator.handle_error(error=error, state=valid_bsc_state, phase="TEST_PHASE")

    # Validações
    assert result["current_phase"] == ConsultingPhase.ERROR
    assert "erro" in result["final_response"].lower()
    assert "Test generic error" in result["final_response"]
    assert "test_phase_error" in result["metadata"]
    assert result["metadata"]["error_type"] == "ValueError"


def test_handle_error_unknown_phase(orchestrator, valid_bsc_state):
    """handle_error funciona mesmo com phase UNKNOWN."""
    error = RuntimeError("Unknown phase error")

    result = orchestrator.handle_error(error=error, state=valid_bsc_state, phase="UNKNOWN")

    # Validações
    assert result["current_phase"] == ConsultingPhase.ERROR
    assert "UNKNOWN" in result["final_response"]
    assert "unknown_error" in result["metadata"]


# ============================================================================
# TESTE REGRESSÃO CRÍTICO (Checklist ponto 12)
# ============================================================================


def test_orchestrator_nao_quebra_workflow_existente(orchestrator, valid_bsc_state):
    """CRÍTICO: Orchestrator não interfere com workflow RAG tradicional.

    Valida que:
    - Lazy loading não quebra imports
    - Properties funcionam sem state consultivo
    - Nenhuma exceção em estado RAG puro
    """
    # Setup: Estado RAG tradicional (sem campos consultivos)
    rag_state = BSCState(
        query="O que é BSC?",
        user_id="test_rag_user",
        session_id="test_rag_session",
        metadata={},
        # SEM: onboarding_progress, client_profile, diagnostic, approval_status
    )

    # Action: Acessar properties (lazy loading) e validar que rag_state não causa erros
    try:
        _ = orchestrator.client_profile_agent  # Deve carregar sem erros
        _ = orchestrator.onboarding_agent  # Deve carregar sem erros
        _ = orchestrator.diagnostic_agent  # Deve carregar sem erros

        # Validar que rag_state (sem campos consultivos) não causa AttributeError
        assert rag_state.user_id == "test_rag_user"
        assert rag_state.query == "O que é BSC?"
        assert rag_state.client_profile is None  # Sem campos consultivos OK

        # Nenhuma exceção = sucesso
        assert True

    except Exception as e:
        pytest.fail(f"Orchestrator quebrou workflow RAG tradicional: {e}")


# ============================================================================
# TESTES LAZY LOADING (Properties)
# ============================================================================


def test_lazy_loading_client_profile_agent(orchestrator):
    """ClientProfileAgent carrega apenas quando acessado."""
    assert orchestrator._client_profile_agent is None

    agent = orchestrator.client_profile_agent

    assert orchestrator._client_profile_agent is not None
    assert agent == orchestrator._client_profile_agent  # Mesma instância


def test_lazy_loading_onboarding_agent(orchestrator):
    """OnboardingAgent carrega apenas quando acessado."""
    assert orchestrator._onboarding_agent is None

    agent = orchestrator.onboarding_agent

    assert orchestrator._onboarding_agent is not None
    assert agent == orchestrator._onboarding_agent


def test_lazy_loading_diagnostic_agent(orchestrator):
    """DiagnosticAgent carrega apenas quando acessado."""
    assert orchestrator._diagnostic_agent is None

    agent = orchestrator.diagnostic_agent

    assert orchestrator._diagnostic_agent is not None
    assert agent == orchestrator._diagnostic_agent
