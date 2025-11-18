"""Testes unitários para Multi-Client Dashboard (FASE 4.1).

Suite completa de testes para os novos métodos Mem0ClientWrapper:
- list_all_profiles(): Listagem de todos os clientes
- get_client_summary(): Resumo executivo para dashboard

Metodologia aplicada: Checklist 15 pontos obrigatório (memory:9969868).
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.memory.exceptions import Mem0ClientError, ProfileNotFoundError
from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile, CompanyInfo, EngagementState, StrategicContext


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mem0_client():
    """Mem0ClientWrapper com client mockado."""
    with patch('src.memory.mem0_client.MemoryClient'):
        client = Mem0ClientWrapper(api_key="test_api_key")
        client.client = MagicMock()
        return client


@pytest.fixture
def valid_client_profile_1():
    """ClientProfile válido 1 (TechCorp - ONBOARDING).
    
    IMPORTANTE: Usa model_construct() para evitar default_factory do updated_at.
    """
    return ClientProfile.model_construct(
        client_id="client_001",
        company=CompanyInfo(
            name="TechCorp Brasil",
            sector="Tecnologia",
            size="média"
        ),
        context=StrategicContext(
            mission="Inovação tecnológica",
            vision="Líder em transformação digital"
        ),
        engagement=EngagementState(
            current_phase="ONBOARDING"
        ),
        metadata={},  # Metadata vazio inicial
        diagnostics=None,
        complete_diagnostic=None,
        created_at=datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 10, 27, 14, 30, 0, tzinfo=timezone.utc)  # Mais recente
    )


@pytest.fixture
def valid_client_profile_2():
    """ClientProfile válido 2 (FinanceGroup - DISCOVERY).
    
    IMPORTANTE: Usa model_construct() para evitar default_factory do updated_at.
    """
    return ClientProfile.model_construct(
        client_id="client_002",
        company=CompanyInfo(
            name="FinanceGroup SA",
            sector="Finanças",
            size="grande"
        ),
        context=StrategicContext(
            mission="Excelência financeira",
            vision="Banco digital top 3"
        ),
        engagement=EngagementState(
            current_phase="DISCOVERY"
        ),
        metadata={},  # Metadata vazio inicial
        diagnostics=None,
        complete_diagnostic=None,
        created_at=datetime(2025, 9, 15, 8, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 10, 25, 16, 0, 0, tzinfo=timezone.utc)  # Mais antigo
    )


@pytest.fixture
def valid_client_profile_3_archived():
    """ClientProfile válido 3 (Archived - COMPLETED).
    
    IMPORTANTE: Usa model_construct() para evitar default_factory do updated_at.
    """
    return ClientProfile.model_construct(
        client_id="client_003_archived",
        company=CompanyInfo(
            name="OldCorp Ltda",
            sector="Manufatura",
            size="pequena"
        ),
        context=StrategicContext(),
        engagement=EngagementState(
            current_phase="COMPLETED"
        ),
        metadata={'archived': True},
        diagnostics=None,
        complete_diagnostic=None,
        created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    )


# ============================================================================
# TESTES list_all_profiles()
# ============================================================================


def test_list_all_profiles_success_search_method(mem0_client, valid_client_profile_1, valid_client_profile_2):
    """list_all_profiles() deve retornar lista de profiles via search() (método primário)."""
    # Arrange
    mem0_client.client.search.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),
                'user_id': 'client_001',
                'archived': False
            }
        },
        {
            'metadata': {
                'profile_data': valid_client_profile_2.to_mem0(),
                'user_id': 'client_002',
                'archived': False
            }
        }
    ]
    
    # Act
    profiles = mem0_client.list_all_profiles(limit=50)
    
    # Assert
    assert len(profiles) == 2
    assert profiles[0].company.name in ["TechCorp Brasil", "FinanceGroup SA"]
    assert profiles[1].company.name in ["TechCorp Brasil", "FinanceGroup SA"]
    mem0_client.client.search.assert_called_once_with(query="*", limit=50)


def test_list_all_profiles_fallback_get_all(mem0_client, valid_client_profile_1):
    """list_all_profiles() deve usar fallback get_all() se search() falhar."""
    # Arrange
    mem0_client.client.search.side_effect = Exception("Search not available")
    mem0_client.client.get_all.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),
                'user_id': 'client_001'
            }
        }
    ]
    
    # Act
    profiles = mem0_client.list_all_profiles()
    
    # Assert
    assert len(profiles) == 1
    assert profiles[0].company.name == "TechCorp Brasil"
    mem0_client.client.get_all.assert_called()


def test_list_all_profiles_empty_results(mem0_client):
    """list_all_profiles() deve retornar lista vazia quando nenhum profile encontrado."""
    # Arrange
    mem0_client.client.search.return_value = []
    
    # Act
    profiles = mem0_client.list_all_profiles()
    
    # Assert
    assert profiles == []
    assert isinstance(profiles, list)


def test_list_all_profiles_filters_archived(mem0_client, valid_client_profile_1, valid_client_profile_3_archived):
    """list_all_profiles() deve filtrar profiles arquivados por padrão."""
    # Arrange
    mem0_client.client.search.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),
                'user_id': 'client_001',
                'archived': False
            }
        },
        {
            'metadata': {
                'profile_data': valid_client_profile_3_archived.to_mem0(),
                'user_id': 'client_003_archived',
                'archived': True
            }
        }
    ]
    
    # Act
    profiles = mem0_client.list_all_profiles(include_archived=False)
    
    # Assert
    assert len(profiles) == 1
    assert profiles[0].company.name == "TechCorp Brasil"


def test_list_all_profiles_includes_archived_when_requested(mem0_client, valid_client_profile_1, valid_client_profile_3_archived):
    """list_all_profiles() deve incluir arquivados quando include_archived=True."""
    # Arrange
    mem0_client.client.search.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),
                'user_id': 'client_001',
                'archived': False
            }
        },
        {
            'metadata': {
                'profile_data': valid_client_profile_3_archived.to_mem0(),
                'user_id': 'client_003_archived',
                'archived': True
            }
        }
    ]
    
    # Act
    profiles = mem0_client.list_all_profiles(include_archived=True)
    
    # Assert
    assert len(profiles) == 2


def test_list_all_profiles_sorted_by_updated_at_desc(mem0_client, valid_client_profile_1, valid_client_profile_2):
    """list_all_profiles() deve retornar profiles ordenados por updated_at decrescente."""
    # Arrange
    # valid_client_profile_2.updated_at = 2025-10-25 (mais antigo)
    # valid_client_profile_1.updated_at = 2025-10-27 (mais recente)
    mem0_client.client.search.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_2.to_mem0(),  # Mais antigo primeiro no mock
                'user_id': 'client_002'
            }
        },
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),  # Mais recente depois
                'user_id': 'client_001'
            }
        }
    ]
    
    # Act
    profiles = mem0_client.list_all_profiles()
    
    # Assert
    assert len(profiles) == 2
    assert profiles[0].updated_at > profiles[1].updated_at  # Mais recente primeiro
    assert profiles[0].company.name == "TechCorp Brasil"


def test_list_all_profiles_handles_corrupted_profile(mem0_client, valid_client_profile_1):
    """list_all_profiles() deve ignorar profile corrompido e continuar listagem."""
    # Arrange
    mem0_client.client.search.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),
                'user_id': 'client_001'
            }
        },
        {
            'metadata': {
                'profile_data': {'invalid': 'data'},  # Profile corrompido
                'user_id': 'client_corrupted'
            }
        }
    ]
    
    # Act
    profiles = mem0_client.list_all_profiles()
    
    # Assert
    assert len(profiles) == 1  # Apenas profile válido retornado
    assert profiles[0].company.name == "TechCorp Brasil"


def test_list_all_profiles_respects_limit_parameter(mem0_client):
    """list_all_profiles() deve passar parâmetro limit corretamente."""
    # Arrange
    mem0_client.client.search.return_value = []
    
    # Act
    mem0_client.list_all_profiles(limit=25)
    
    # Assert
    mem0_client.client.search.assert_called_once_with(query="*", limit=25)


def test_list_all_profiles_raises_error_on_connection_failure(mem0_client):
    """list_all_profiles() deve lançar ConnectionError e ativar retry."""
    # Arrange
    mem0_client.client.search.side_effect = ConnectionError("Network error")
    mem0_client.client.get_all.side_effect = ConnectionError("Network error")
    
    # Act & Assert
    with pytest.raises(ConnectionError):
        mem0_client.list_all_profiles()


# ============================================================================
# TESTES get_client_summary()
# ============================================================================


def test_get_client_summary_success(mem0_client, valid_client_profile_1):
    """get_client_summary() deve retornar dict com campos esperados."""
    # Arrange
    mem0_client.load_profile = MagicMock(return_value=valid_client_profile_1)
    mem0_client.client.get_all.return_value = [
        {
            'metadata': {
                'swot_analysis_data': {},
                'kpi_framework_data': {}
            }
        }
    ]
    
    # Act
    summary = mem0_client.get_client_summary("client_001")
    
    # Assert
    assert isinstance(summary, dict)
    assert summary['client_id'] == "client_001"
    assert summary['company_name'] == "TechCorp Brasil"
    assert summary['sector'] == "Tecnologia"
    assert summary['size'] == "média"
    assert summary['current_phase'] == "ONBOARDING"
    assert summary['total_tools_used'] == 2  # swot + kpi
    assert summary['has_diagnostic'] is False
    assert 'last_updated' in summary


def test_get_client_summary_with_diagnostic(mem0_client, valid_client_profile_1):
    """get_client_summary() deve detectar complete_diagnostic presente."""
    # Arrange
    valid_client_profile_1.complete_diagnostic = {'mock': 'diagnostic'}
    mem0_client.load_profile = MagicMock(return_value=valid_client_profile_1)
    mem0_client.client.get_all.return_value = []
    
    # Act
    summary = mem0_client.get_client_summary("client_001")
    
    # Assert
    assert summary['has_diagnostic'] is True


def test_get_client_summary_with_approval_status(mem0_client, valid_client_profile_1):
    """get_client_summary() deve incluir approval_status quando presente."""
    # Arrange
    valid_client_profile_1.metadata['approval_status'] = 'APPROVED'  # approval_status está em profile.metadata
    mem0_client.load_profile = MagicMock(return_value=valid_client_profile_1)
    mem0_client.client.get_all.return_value = []
    
    # Act
    summary = mem0_client.get_client_summary("client_001")
    
    # Assert
    assert summary['approval_status'] == 'APPROVED'


def test_get_client_summary_counts_all_tools(mem0_client, valid_client_profile_1):
    """get_client_summary() deve contar corretamente todas as 8 tools."""
    # Arrange
    mem0_client.load_profile = MagicMock(return_value=valid_client_profile_1)
    mem0_client.client.get_all.return_value = [
        {
            'metadata': {
                'swot_analysis_data': {},
                'five_whys_data': {},
                'issue_tree_data': {},
                'kpi_framework_data': {},
                'strategic_objectives_data': {},
                'benchmark_report_data': {},
                'action_plan_data': {},
                'prioritization_matrix_data': {}
            }
        }
    ]
    
    # Act
    summary = mem0_client.get_client_summary("client_001")
    
    # Assert
    assert summary['total_tools_used'] == 8


def test_get_client_summary_raises_profile_not_found(mem0_client):
    """get_client_summary() deve lançar ProfileNotFoundError se cliente não existir."""
    # Arrange
    mem0_client.load_profile = MagicMock(side_effect=ProfileNotFoundError("client_999"))
    
    # Act & Assert
    with pytest.raises(ProfileNotFoundError):
        mem0_client.get_client_summary("client_999")


def test_get_client_summary_handles_error_gracefully(mem0_client):
    """get_client_summary() deve capturar exceções genéricas e lançar Mem0ClientError."""
    # Arrange
    mem0_client.load_profile = MagicMock(side_effect=Exception("Unexpected error"))
    
    # Act & Assert
    with pytest.raises(Mem0ClientError) as exc_info:
        mem0_client.get_client_summary("client_001")
    
    assert "Erro ao gerar summary" in str(exc_info.value)


# ============================================================================
# TESTES INTEGRAÇÃO
# ============================================================================


def test_integration_list_and_summarize(mem0_client, valid_client_profile_1, valid_client_profile_2):
    """Integração: list_all_profiles() seguido de get_client_summary() para cada cliente."""
    # Arrange
    mem0_client.client.search.return_value = [
        {
            'metadata': {
                'profile_data': valid_client_profile_1.to_mem0(),
                'user_id': 'client_001'
            }
        },
        {
            'metadata': {
                'profile_data': valid_client_profile_2.to_mem0(),
                'user_id': 'client_002'
            }
        }
    ]
    mem0_client.load_profile = MagicMock(side_effect=[valid_client_profile_1, valid_client_profile_2])
    mem0_client.client.get_all.return_value = []
    
    # Act
    profiles = mem0_client.list_all_profiles()
    summaries = [mem0_client.get_client_summary(p.client_id) for p in profiles]
    
    # Assert
    assert len(profiles) == 2
    assert len(summaries) == 2
    assert summaries[0]['company_name'] in ["TechCorp Brasil", "FinanceGroup SA"]
    assert summaries[1]['company_name'] in ["TechCorp Brasil", "FinanceGroup SA"]

