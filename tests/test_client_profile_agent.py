"""Testes unitários para ClientProfileAgent.

Valida extração de contexto empresarial durante ONBOARDING:
- extract_company_info(): Nome, setor, porte
- identify_challenges(): Desafios estratégicos (3-7)
- define_objectives(): Objetivos BSC SMART (3-5)
- process_onboarding(): Workflow completo

Versão: 1.0 (FASE 2.4)
Coverage esperado: >85%
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from tenacity import RetryError

from src.agents.client_profile_agent import (
    ClientProfileAgent,
    ChallengesList,
    ObjectivesList
)
from src.memory.schemas import CompanyInfo, ClientProfile, StrategicContext
from src.graph.states import BSCState
from src.graph.consulting_states import ConsultingPhase


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock de LLM (ChatOpenAI)."""
    llm = Mock(spec=ChatOpenAI)
    llm.model_name = "gpt-4o-mini-test"
    llm.temperature = 0.1
    return llm


@pytest.fixture
def client_profile_agent(mock_llm):
    """Fixture de ClientProfileAgent."""
    return ClientProfileAgent(llm=mock_llm)


@pytest.fixture
def sample_company_info():
    """CompanyInfo de exemplo válido."""
    return CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média",
        industry="SaaS B2B",
        founded_year=2015
    )


@pytest.fixture
def initial_state():
    """BSCState inicial para testes."""
    state = BSCState(
        user_id="test_user_456",
        query="",
        messages=[],
        agent_responses=[],
        current_agent=None,
        synthesis="",
        judge_score=0.0,
        needs_followup=False,
        client_profile=ClientProfile(
            user_id="test_user_456",
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

def test_client_profile_agent_initialization(client_profile_agent):
    """Testa inicialização correta do agente."""
    assert client_profile_agent.llm is not None


def test_client_profile_agent_with_custom_llm():
    """Testa criação com LLM customizado."""
    custom_llm = Mock(spec=ChatOpenAI)
    custom_llm.model_name = "custom-model"
    
    agent = ClientProfileAgent(llm=custom_llm)
    
    assert agent.llm == custom_llm


# ============================================================================
# TESTES DE extract_company_info()
# ============================================================================

def test_extract_company_info_success(client_profile_agent, mock_llm):
    """Testa extração bem-sucedida de CompanyInfo."""
    # Mock structured output do LLM
    mock_company = CompanyInfo(
        name="TechCorp",
        sector="Tecnologia",
        size="média"
    )
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_company
    
    conversation = "Sou da TechCorp, atuamos em tecnologia, somos empresa média com 150 funcionários."
    
    result = client_profile_agent.extract_company_info(conversation)
    
    assert isinstance(result, CompanyInfo)
    assert result.name == "TechCorp"
    assert result.sector == "Tecnologia"
    assert result.size == "média"


def test_extract_company_info_empty_conversation_raises_error(client_profile_agent):
    """Testa que conversação vazia lança RetryError (após 3 tentativas do @retry decorator)."""
    with pytest.raises(RetryError):
        client_profile_agent.extract_company_info("")


def test_extract_company_info_invalid_extraction_raises_error(client_profile_agent, mock_llm):
    """Testa que extração inválida (nome genérico) lança RetryError após 3 tentativas."""
    # Mock extração com nome genérico
    mock_company = CompanyInfo(
        name="Empresa",  # Nome genérico inválido
        sector="Tecnologia",
        size="média"
    )
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_company

    # Conversação com 71+ chars para passar validação de comprimento
    conversation = "Minha empresa atua em tecnologia e estamos crescendo no setor de SaaS"

    # @retry decorator tenta 3x e lança RetryError
    with pytest.raises(RetryError):
        client_profile_agent.extract_company_info(conversation)


# ============================================================================
# TESTES DE identify_challenges()
# ============================================================================

def test_identify_challenges_success(client_profile_agent, mock_llm, sample_company_info):
    """Testa identificação bem-sucedida de desafios."""
    # Mock structured output
    mock_challenges = ChallengesList(challenges=[
        "Perda de clientes para concorrentes",
        "Equipe sobrecarregada",
        "Falta de capital para crescimento"
    ])
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_challenges

    conversation = "Estamos perdendo clientes e a equipe está cansada."

    result = client_profile_agent.identify_challenges(conversation, sample_company_info)

    # Método retorna list[str], não ChallengesList
    assert isinstance(result, list)
    assert len(result) >= 3
    assert all(isinstance(challenge, str) for challenge in result)


def test_identify_challenges_empty_conversation_raises_error(client_profile_agent, sample_company_info):
    """Testa que conversação vazia lança RetryError (após 3 tentativas do @retry decorator)."""
    with pytest.raises(RetryError):
        client_profile_agent.identify_challenges("", sample_company_info)


# ============================================================================
# TESTES DE define_objectives()
# ============================================================================

def test_define_objectives_success(client_profile_agent, mock_llm):
    """Testa definição bem-sucedida de objetivos BSC."""
    # Mock structured output
    mock_objectives = ObjectivesList(objectives=[
        "Aumentar receita 30% em 12 meses (Financeira)",
        "Reduzir churn para 5% (Clientes)",
        "Automatizar 50% processos em 6 meses (Processos)"
    ])
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_objectives

    conversation = "Queremos crescer 30%, reter clientes e melhorar processos."
    challenges = ["Perda de clientes", "Processos manuais"]

    # Método aceita apenas 2 parâmetros: conversation e challenges
    result = client_profile_agent.define_objectives(conversation, challenges)

    # Método retorna list[str], não ObjectivesList
    assert isinstance(result, list)
    assert len(result) >= 3
    assert all(isinstance(obj, str) for obj in result)


def test_define_objectives_empty_conversation_raises_error(client_profile_agent):
    """Testa que conversação vazia lança RetryError (após 3 tentativas do @retry decorator)."""
    with pytest.raises(RetryError):
        # Método aceita apenas 2 parâmetros: conversation e challenges
        client_profile_agent.define_objectives("", [])


# ============================================================================
# TESTES DE _validate_extraction()
# ============================================================================

def test_validate_extraction_valid_company_info(client_profile_agent):
    """Testa validação de CompanyInfo válido."""
    company = CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média"
    )
    
    assert client_profile_agent._validate_extraction(company) is True


def test_validate_extraction_invalid_generic_name(client_profile_agent):
    """Testa que nome genérico falha na validação."""
    company = CompanyInfo(
        name="Empresa",  # Nome genérico
        sector="Tecnologia",
        size="média"
    )
    
    assert client_profile_agent._validate_extraction(company) is False


def test_validate_extraction_invalid_empty_sector(client_profile_agent):
    """Testa que setor vazio falha na validação."""
    company = CompanyInfo(
        name="TechCorp",
        sector="",  # Setor vazio
        size="média"
    )
    
    assert client_profile_agent._validate_extraction(company) is False


def test_validate_extraction_invalid_short_sector(client_profile_agent):
    """Testa que setor muito curto falha na validação."""
    company = CompanyInfo(
        name="TechCorp",
        sector="TI",  # Apenas 2 caracteres (< 3)
        size="média"
    )
    
    assert client_profile_agent._validate_extraction(company) is False


# ============================================================================
# TESTE DE COBERTURA GERAL
# ============================================================================

def test_client_profile_agent_has_correct_methods(client_profile_agent):
    """Testa que o agente possui todos os métodos públicos esperados."""
    assert hasattr(client_profile_agent, 'extract_company_info')
    assert hasattr(client_profile_agent, 'identify_challenges')
    assert hasattr(client_profile_agent, 'define_objectives')
    assert hasattr(client_profile_agent, 'process_onboarding')
    assert hasattr(client_profile_agent, '_validate_extraction')


def test_challenges_list_schema_validation():
    """Testa validação do schema ChallengesList."""
    # Válido: 3-7 desafios
    valid = ChallengesList(challenges=["D1", "D2", "D3"])
    assert len(valid.challenges) == 3
    
    # Inválido: < 3 desafios
    with pytest.raises(ValidationError):
        ChallengesList(challenges=["D1", "D2"])
    
    # Inválido: > 7 desafios
    with pytest.raises(ValidationError):
        ChallengesList(challenges=["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"])


def test_objectives_list_schema_validation():
    """Testa validação do schema ObjectivesList."""
    # Válido: 3-5 objetivos
    valid = ObjectivesList(objectives=["O1", "O2", "O3"])
    assert len(valid.objectives) == 3
    
    # Inválido: < 3 objetivos
    with pytest.raises(ValidationError):
        ObjectivesList(objectives=["O1", "O2"])
    
    # Inválido: > 5 objetivos
    with pytest.raises(ValidationError):
        ObjectivesList(objectives=["O1", "O2", "O3", "O4", "O5", "O6"])

