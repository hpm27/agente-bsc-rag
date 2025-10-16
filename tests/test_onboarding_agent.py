"""
Testes unitários para OnboardingAgent.

Valida workflow conversacional multi-turn, follow-up logic,
integração com BSCState e transição para DISCOVERY.

Autor: BSC Consulting Agent v2.0
Data: 2025-10-15
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.agents.onboarding_agent import OnboardingAgent, OnboardingStep
from src.graph.states import BSCState
from src.graph.consulting_states import ConsultingPhase
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext


@pytest.fixture
def mock_llm():
    """Mock de LLM para testes."""
    llm = Mock()
    llm.invoke = Mock(return_value="Test response")
    return llm


@pytest.fixture
def mock_profile_agent():
    """Mock de ClientProfileAgent."""
    agent = Mock()

    # Mock extract_company_info
    company_info = Mock()
    company_info.name = "Empresa Teste"
    company_info.sector = "Tecnologia"
    company_info.size = "50-200"
    company_info.dict = Mock(return_value={
        "name": "Empresa Teste",
        "sector": "Tecnologia",
        "size": "50-200"
    })
    agent.extract_company_info = Mock(return_value=company_info)

    # Mock identify_challenges
    challenges_result = Mock()
    challenges_result.challenges = ["Desafio 1", "Desafio 2"]
    challenges_result.dict = Mock(return_value={
        "challenges": ["Desafio 1", "Desafio 2"]
    })
    agent.identify_challenges = Mock(return_value=challenges_result)

    # Mock define_objectives
    objectives_result = Mock()
    objectives_result.objectives = ["Objetivo 1", "Objetivo 2", "Objetivo 3"]
    objectives_result.dict = Mock(return_value={
        "objectives": ["Objetivo 1", "Objetivo 2", "Objetivo 3"]
    })
    agent.define_objectives = Mock(return_value=objectives_result)

    return agent


@pytest.fixture
def mock_memory_client():
    """Mock de Mem0Client."""
    client = Mock()
    client.save_client_profile = Mock()
    return client


@pytest.fixture
def onboarding_agent(mock_llm, mock_profile_agent, mock_memory_client):
    """Fixture do OnboardingAgent configurado."""
    return OnboardingAgent(
        llm=mock_llm,
        client_profile_agent=mock_profile_agent,
        memory_client=mock_memory_client,
        max_followups_per_step=2
    )


@pytest.fixture
def initial_state():
    """Fixture de BSCState inicial."""
    state = BSCState(
        user_id="test_user_123",
        query="",
        messages=[],
        agent_responses=[],
        current_agent=None,
        synthesis="",
        judge_score=0.0,
        needs_followup=False,
        client_profile=ClientProfile(
            user_id="test_user_123",
            company=CompanyInfo(
                name="Pending",
                sector="Pending"
            ),
            context=StrategicContext()
        ),
        current_phase=ConsultingPhase.ONBOARDING
    )
    return state


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================

def test_onboarding_agent_initialization(onboarding_agent):
    """Testa inicialização do OnboardingAgent."""
    assert onboarding_agent is not None
    assert onboarding_agent.max_followups_per_step == 2
    assert onboarding_agent.conversation_history == []
    assert onboarding_agent.followup_count == {1: 0, 2: 0, 3: 0}


# ============================================================================
# TESTES DE start_onboarding()
# ============================================================================

def test_start_onboarding_creates_initial_state(onboarding_agent, initial_state):
    """Testa que start_onboarding() inicializa onboarding_progress."""
    result = onboarding_agent.start_onboarding("test_user_123", initial_state)

    assert initial_state.onboarding_progress is not None
    assert initial_state.onboarding_progress["company_info"] is False
    assert initial_state.onboarding_progress["challenges"] is False
    assert initial_state.onboarding_progress["objectives"] is False
    assert initial_state.onboarding_progress["current_step"] == OnboardingStep.COMPANY_INFO


def test_start_onboarding_returns_welcome_message(onboarding_agent, initial_state):
    """Testa que start_onboarding() retorna mensagem de boas-vindas."""
    result = onboarding_agent.start_onboarding("test_user_123", initial_state)

    assert "question" in result
    assert "Olá" in result["question"] or "olá" in result["question"]
    assert result["step"] == OnboardingStep.COMPANY_INFO
    assert result["is_complete"] is False
    assert result["followup_count"] == 0


def test_start_onboarding_adds_to_conversation_history(onboarding_agent, initial_state):
    """Testa que start_onboarding() adiciona ao histórico."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    assert len(onboarding_agent.conversation_history) == 1
    assert onboarding_agent.conversation_history[0]["role"] == "assistant"


# ============================================================================
# TESTES DE process_turn() - COMPANY_INFO
# ============================================================================

def test_process_turn_step1_complete_info(onboarding_agent, initial_state, mock_profile_agent):
    """Testa process_turn() com informações completas no step 1."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Empresa Teste, setor tecnologia, 150 funcionários",
        initial_state
    )

    # Deve avançar para próximo step
    assert result["step"] == OnboardingStep.CHALLENGES
    assert result["is_complete"] is False
    assert "Ótimo" in result["question"] or "desafio" in result["question"].lower()

    # State deve estar atualizado
    assert initial_state.onboarding_progress["company_info"] is True
    assert initial_state.client_profile.company.name == "Empresa Teste"


def test_process_turn_step1_incomplete_triggers_followup(
    onboarding_agent, initial_state, mock_profile_agent
):
    """Testa que informações incompletas no step 1 trigam follow-up."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    # Mock retorno incompleto (falta sector)
    incomplete_info = Mock()
    incomplete_info.name = "Empresa X"
    incomplete_info.sector = None
    incomplete_info.size = "100"
    incomplete_info.dict = Mock(return_value={
        "name": "Empresa X",
        "sector": None,
        "size": "100"
    })
    mock_profile_agent.extract_company_info = Mock(return_value=incomplete_info)

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Empresa X com 100 funcionários",
        initial_state
    )

    # Deve gerar follow-up
    assert result["step"] == OnboardingStep.COMPANY_INFO
    assert result["followup_count"] == 1
    assert result["is_complete"] is False
    assert "setor" in result["question"].lower() or "indústria" in result["question"].lower()


def test_process_turn_step1_max_followups_forces_continue(
    onboarding_agent, initial_state, mock_profile_agent
):
    """Testa que após max follow-ups, avança mesmo com info incompleta."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    # Simular 2 follow-ups já executados
    onboarding_agent.followup_count[OnboardingStep.COMPANY_INFO] = 2

    # Mock retorno ainda incompleto
    incomplete_info = Mock()
    incomplete_info.name = "Empresa Y"
    incomplete_info.sector = None
    incomplete_info.size = None
    incomplete_info.dict = Mock(return_value={"name": "Empresa Y", "sector": None, "size": None})
    mock_profile_agent.extract_company_info = Mock(return_value=incomplete_info)

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Empresa Y",
        initial_state
    )

    # Deve forçar avanço para próximo step
    assert result["step"] == OnboardingStep.CHALLENGES
    assert initial_state.onboarding_progress["company_info"] is True


# ============================================================================
# TESTES DE process_turn() - CHALLENGES
# ============================================================================

def test_process_turn_step2_complete_challenges(onboarding_agent, initial_state):
    """Testa process_turn() com desafios completos no step 2."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    # Simular step 1 completo
    initial_state.onboarding_progress["company_info"] = True
    initial_state.onboarding_progress["current_step"] = OnboardingStep.CHALLENGES

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Crescimento de receita, eficiência operacional, retenção de talentos",
        initial_state
    )

    # Deve avançar para step 3
    assert result["step"] == OnboardingStep.OBJECTIVES
    assert result["is_complete"] is False
    assert initial_state.onboarding_progress["challenges"] is True


def test_process_turn_step2_incomplete_triggers_followup(
    onboarding_agent, initial_state, mock_profile_agent
):
    """Testa follow-up quando menos de 2 desafios identificados."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    # Simular step 1 completo
    initial_state.onboarding_progress["company_info"] = True
    initial_state.onboarding_progress["current_step"] = OnboardingStep.CHALLENGES

    # Mock apenas 1 desafio
    challenges_result = Mock()
    challenges_result.challenges = ["Apenas um desafio"]
    challenges_result.dict = Mock(return_value={"challenges": ["Apenas um desafio"]})
    mock_profile_agent.identify_challenges = Mock(return_value=challenges_result)

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Crescer mais",
        initial_state
    )

    # Deve gerar follow-up
    assert result["step"] == OnboardingStep.CHALLENGES
    assert result["followup_count"] == 1
    assert result["is_complete"] is False


# ============================================================================
# TESTES DE process_turn() - OBJECTIVES (COMPLETO)
# ============================================================================

def test_process_turn_step3_completes_onboarding(onboarding_agent, initial_state):
    """Testa que completar step 3 finaliza onboarding."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    # Simular steps 1 e 2 completos
    initial_state.onboarding_progress["company_info"] = True
    initial_state.onboarding_progress["challenges"] = True
    initial_state.onboarding_progress["current_step"] = OnboardingStep.OBJECTIVES

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Aumentar receita 20%, NPS 50+, reduzir lead time 30%, engajamento 80%",
        initial_state
    )

    # Deve marcar como completo
    assert result["is_complete"] is True
    assert initial_state.onboarding_progress["objectives"] is True
    assert initial_state.current_phase == ConsultingPhase.DISCOVERY


def test_process_turn_step3_incomplete_triggers_followup(
    onboarding_agent, initial_state, mock_profile_agent
):
    """Testa follow-up quando menos de 3 objetivos definidos."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    # Simular steps 1 e 2 completos
    initial_state.onboarding_progress["company_info"] = True
    initial_state.onboarding_progress["challenges"] = True
    initial_state.onboarding_progress["current_step"] = OnboardingStep.OBJECTIVES

    # Mock apenas 2 objetivos
    objectives_result = Mock()
    objectives_result.objectives = ["Objetivo 1", "Objetivo 2"]
    objectives_result.dict = Mock(return_value={"objectives": ["Objetivo 1", "Objetivo 2"]})
    mock_profile_agent.define_objectives = Mock(return_value=objectives_result)

    result = onboarding_agent.process_turn(
        "test_user_123",
        "Aumentar receita, melhorar NPS",
        initial_state
    )

    # Deve gerar follow-up
    assert result["step"] == OnboardingStep.OBJECTIVES
    assert result["followup_count"] == 1
    assert result["is_complete"] is False


# ============================================================================
# TESTES DE is_onboarding_complete()
# ============================================================================

def test_is_onboarding_complete_returns_false_initially(onboarding_agent, initial_state):
    """Testa que is_onboarding_complete() retorna False no início."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    assert onboarding_agent.is_onboarding_complete(initial_state) is False


def test_is_onboarding_complete_returns_true_when_all_steps_done(
    onboarding_agent, initial_state
):
    """Testa que is_onboarding_complete() retorna True quando 3 steps completos."""
    onboarding_agent.start_onboarding("test_user_123", initial_state)

    initial_state.onboarding_progress["company_info"] = True
    initial_state.onboarding_progress["challenges"] = True
    initial_state.onboarding_progress["objectives"] = True

    assert onboarding_agent.is_onboarding_complete(initial_state) is True


# ============================================================================
# TESTES DE MÉTODOS PRIVADOS
# ============================================================================

def test_generate_initial_question_step1(onboarding_agent):
    """Testa _generate_initial_question para step 1."""
    question = onboarding_agent._generate_initial_question(OnboardingStep.COMPANY_INFO)

    assert "empresa" in question.lower()
    assert "nome" in question.lower() or "setor" in question.lower()


def test_generate_initial_question_step2(onboarding_agent):
    """Testa _generate_initial_question para step 2."""
    question = onboarding_agent._generate_initial_question(OnboardingStep.CHALLENGES)

    assert "desafio" in question.lower()


def test_generate_initial_question_step3(onboarding_agent):
    """Testa _generate_initial_question para step 3."""
    question = onboarding_agent._generate_initial_question(OnboardingStep.OBJECTIVES)

    assert "objetivo" in question.lower()
    assert "bsc" in question.lower() or "perspectiva" in question.lower()


def test_validate_extraction_company_info_complete(onboarding_agent):
    """Testa _validate_extraction com company info completo."""
    extraction = {"name": "Empresa X", "sector": "Tech", "size": "100"}

    is_complete, missing = onboarding_agent._validate_extraction(extraction, OnboardingStep.COMPANY_INFO)

    assert is_complete is True
    assert len(missing) == 0


def test_validate_extraction_company_info_incomplete(onboarding_agent):
    """Testa _validate_extraction com company info incompleto."""
    extraction = {"name": "Empresa X", "sector": None, "size": "100"}

    is_complete, missing = onboarding_agent._validate_extraction(extraction, OnboardingStep.COMPANY_INFO)

    assert is_complete is False
    assert len(missing) > 0
    assert "setor" in str(missing).lower() or "indústria" in str(missing).lower()


def test_validate_extraction_challenges_complete(onboarding_agent):
    """Testa _validate_extraction com 2+ desafios."""
    extraction = {"challenges": ["Desafio 1", "Desafio 2"]}

    is_complete, missing = onboarding_agent._validate_extraction(extraction, OnboardingStep.CHALLENGES)

    assert is_complete is True
    assert len(missing) == 0


def test_validate_extraction_challenges_incomplete(onboarding_agent):
    """Testa _validate_extraction com <2 desafios."""
    extraction = {"challenges": ["Apenas um"]}

    is_complete, missing = onboarding_agent._validate_extraction(extraction, OnboardingStep.CHALLENGES)

    assert is_complete is False
    assert len(missing) > 0


def test_validate_extraction_objectives_complete(onboarding_agent):
    """Testa _validate_extraction com 3+ objetivos."""
    extraction = {"objectives": ["Obj 1", "Obj 2", "Obj 3"]}

    is_complete, missing = onboarding_agent._validate_extraction(extraction, OnboardingStep.OBJECTIVES)

    assert is_complete is True
    assert len(missing) == 0


def test_validate_extraction_objectives_incomplete(onboarding_agent):
    """Testa _validate_extraction com <3 objetivos."""
    extraction = {"objectives": ["Obj 1", "Obj 2"]}

    is_complete, missing = onboarding_agent._validate_extraction(extraction, OnboardingStep.OBJECTIVES)

    assert is_complete is False
    assert len(missing) > 0


def test_build_conversation_context(onboarding_agent):
    """Testa _build_conversation_context."""
    onboarding_agent.conversation_history = [
        {"role": "assistant", "content": "Olá!", "step": 1},
        {"role": "user", "content": "Empresa X", "step": 1},
        {"role": "assistant", "content": "Obrigado!", "step": 1},
    ]

    context = onboarding_agent._build_conversation_context()

    assert "Agente: Olá!" in context
    assert "Cliente: Empresa X" in context
    assert "Agente: Obrigado!" in context


# ============================================================================
# TESTES DE INTEGRAÇÃO (WORKFLOW COMPLETO)
# ============================================================================

def test_complete_onboarding_workflow(onboarding_agent, initial_state):
    """Testa workflow completo de onboarding (3 steps)."""
    # Step 1: Start
    result1 = onboarding_agent.start_onboarding("test_user_123", initial_state)
    assert result1["step"] == OnboardingStep.COMPANY_INFO
    assert result1["is_complete"] is False

    # Step 2: Company info completo
    result2 = onboarding_agent.process_turn(
        "test_user_123",
        "Empresa Teste, tecnologia, 150 funcionários",
        initial_state
    )
    assert result2["step"] == OnboardingStep.CHALLENGES
    assert initial_state.onboarding_progress["company_info"] is True

    # Step 3: Challenges completo
    result3 = onboarding_agent.process_turn(
        "test_user_123",
        "Crescimento de receita e eficiência operacional",
        initial_state
    )
    assert result3["step"] == OnboardingStep.OBJECTIVES
    assert initial_state.onboarding_progress["challenges"] is True

    # Step 4: Objectives completo - onboarding finalizado
    result4 = onboarding_agent.process_turn(
        "test_user_123",
        "Aumentar receita 20%, NPS 50+, reduzir lead time 30%",
        initial_state
    )
    assert result4["is_complete"] is True
    assert initial_state.onboarding_progress["objectives"] is True
    assert initial_state.current_phase == ConsultingPhase.DISCOVERY
    assert onboarding_agent.is_onboarding_complete(initial_state) is True

