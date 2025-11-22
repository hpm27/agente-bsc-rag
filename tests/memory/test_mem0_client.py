"""Testes unitários para Mem0ClientWrapper.

Este módulo testa todas operações do wrapper Mem0, incluindo
save, load, update, search, serialização, e error handling.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.memory.exceptions import (
    Mem0ClientError,
    ProfileNotFoundError,
    ProfileValidationError,
)
from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_mem0_client():
    """Fixture que retorna MemoryClient mockado."""
    with patch("src.memory.mem0_client.MemoryClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_profile():
    """Fixture que retorna ClientProfile de exemplo válido."""
    return ClientProfile(
        client_id="test_client_123",
        company=CompanyInfo(
            name="Empresa Teste Ltda",
            sector="Technology",
            size="50-100",
        ),
        strategic_context=StrategicContext(
            main_challenge="Crescimento sustentável",
            objectives=["Aumentar receita 20%", "Melhorar NPS"],
        ),
    )


@pytest.fixture
def mem0_wrapper(mock_mem0_client):
    """Fixture que retorna Mem0ClientWrapper mockado."""
    with patch.dict(os.environ, {"MEM0_API_KEY": "test_api_key"}):
        return Mem0ClientWrapper()


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================


def test_init_with_api_key():
    """Testa inicialização com API key fornecida."""
    with patch("src.memory.mem0_client.MemoryClient"):
        wrapper = Mem0ClientWrapper(api_key="explicit_key")
        assert wrapper.api_key == "explicit_key"


def test_init_with_env_var():
    """Testa inicialização com API key do .env."""
    with (
        patch.dict(os.environ, {"MEM0_API_KEY": "env_key"}),
        patch("src.memory.mem0_client.MemoryClient"),
    ):
        wrapper = Mem0ClientWrapper()
        assert wrapper.api_key == "env_key"


def test_init_without_api_key_raises_error():
    """Testa que inicialização sem API key levanta Mem0ClientError."""
    with patch.dict(os.environ, {}, clear=True), pytest.raises(Mem0ClientError) as exc_info:
        Mem0ClientWrapper()

    assert "API key do Mem0 não encontrada" in str(exc_info.value)


def test_init_client_creation_failure():
    """Testa falha na criação do MemoryClient."""
    with (
        patch.dict(os.environ, {"MEM0_API_KEY": "test_key"}),
        patch("src.memory.mem0_client.MemoryClient", side_effect=Exception("Connection failed")),
        pytest.raises(Mem0ClientError) as exc_info,
    ):
        Mem0ClientWrapper()

    assert "Falha ao inicializar Mem0 Client" in str(exc_info.value)


# ============================================================================
# TESTES DE SERIALIZAÇÃO/DESERIALIZAÇÃO
# ============================================================================


def test_serialize_profile_success(mem0_wrapper, sample_profile):
    """Testa serialização bem-sucedida de ClientProfile."""
    data = mem0_wrapper._serialize_profile(sample_profile)

    assert isinstance(data, dict)
    assert data["client_id"] == "test_client_123"
    assert data["company"]["name"] == "Empresa Teste Ltda"


def test_deserialize_profile_success(mem0_wrapper, sample_profile):
    """Testa deserialização bem-sucedida de ClientProfile."""
    data = sample_profile.to_mem0()

    profile = mem0_wrapper._deserialize_profile("test_client_123", data)

    assert isinstance(profile, ClientProfile)
    assert profile.client_id == "test_client_123"
    assert profile.company.name == "Empresa Teste Ltda"


def test_deserialize_profile_invalid_data_raises_error(mem0_wrapper):
    """Testa que dados inválidos levantam ProfileValidationError."""
    invalid_data = {"client_id": "test", "company": "not_a_dict"}  # company deve ser dict

    with pytest.raises(ProfileValidationError) as exc_info:
        mem0_wrapper._deserialize_profile("test", invalid_data)

    assert "test" in str(exc_info.value)


# ============================================================================
# TESTES DE SAVE_PROFILE
# ============================================================================


def test_save_profile_success(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa salvamento bem-sucedido de ClientProfile."""
    mock_mem0_client.add.return_value = {"success": True}

    result = mem0_wrapper.save_profile(sample_profile)

    assert result == "test_client_123"
    mock_mem0_client.add.assert_called_once()

    # Verifica argumentos da chamada
    call_args = mock_mem0_client.add.call_args
    assert call_args.kwargs["user_id"] == "test_client_123"
    assert "profile_data" in call_args.kwargs["metadata"]


def test_save_profile_validation_error(mem0_wrapper):
    """Testa que profile inválido levanta ProfileValidationError."""
    # Cria profile inválido (sem company)
    invalid_profile = ClientProfile(client_id="test")

    # Força erro de serialização
    with (
        patch.object(invalid_profile, "to_mem0", side_effect=Exception("Validation failed")),
        pytest.raises(ProfileValidationError),
    ):
        mem0_wrapper.save_profile(invalid_profile)


# ============================================================================
# TESTES DE LOAD_PROFILE
# ============================================================================


def test_load_profile_success(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa carregamento bem-sucedido de ClientProfile."""
    # Mock resposta do Mem0
    mock_memory = MagicMock()
    mock_memory.metadata = {
        "profile_data": sample_profile.to_mem0(),
        "company_name": "Empresa Teste Ltda",
    }
    mock_mem0_client.get_all.return_value = [mock_memory]

    profile = mem0_wrapper.load_profile("test_client_123")

    assert isinstance(profile, ClientProfile)
    assert profile.client_id == "test_client_123"
    assert profile.company.name == "Empresa Teste Ltda"
    # API v2 usa filters estruturados
    expected_filters = {"AND": [{"user_id": "test_client_123"}]}
    mock_mem0_client.get_all.assert_called_once_with(filters=expected_filters, page=1, page_size=50)


def test_load_profile_not_found_raises_error(mem0_wrapper, mock_mem0_client):
    """Testa que user_id inexistente levanta ProfileNotFoundError."""
    mock_mem0_client.get_all.return_value = []

    with pytest.raises(ProfileNotFoundError) as exc_info:
        mem0_wrapper.load_profile("nonexistent_id")

    assert "nonexistent_id" in str(exc_info.value)


def test_load_profile_dict_format(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa carregamento quando Mem0 retorna dict ao invés de objeto."""
    mock_mem0_client.get_all.return_value = [
        {"metadata": {"profile_data": sample_profile.to_mem0()}}
    ]

    profile = mem0_wrapper.load_profile("test_client_123")

    assert isinstance(profile, ClientProfile)
    assert profile.client_id == "test_client_123"


# ============================================================================
# TESTES DE UPDATE_PROFILE
# ============================================================================


def test_update_profile_success(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa atualização bem-sucedida de ClientProfile."""
    # Mock load_profile
    mock_memory = MagicMock()
    mock_memory.metadata = {"profile_data": sample_profile.to_mem0()}
    mock_mem0_client.get_all.return_value = [mock_memory]
    mock_mem0_client.add.return_value = {"success": True}

    updates = {"company": {"sector": "Finance"}}
    updated_profile = mem0_wrapper.update_profile("test_client_123", updates)

    assert updated_profile.company.sector == "Finance"
    assert updated_profile.company.name == "Empresa Teste Ltda"  # Não afetado


def test_update_profile_not_found(mem0_wrapper, mock_mem0_client):
    """Testa que atualização de profile inexistente levanta erro."""
    mock_mem0_client.get_all.return_value = []

    with pytest.raises(ProfileNotFoundError):
        mem0_wrapper.update_profile("nonexistent", {"company": {"sector": "Tech"}})


def test_deep_update_nested_dict(mem0_wrapper):
    """Testa merge recursivo de dicionários nested."""
    base = {"company": {"name": "Test", "sector": "Tech"}, "engagement": {"phase": "ONBOARDING"}}
    updates = {
        "company": {"sector": "Finance"},  # Atualiza só sector
        "engagement": {"phase": "DISCOVERY"},
    }

    mem0_wrapper._deep_update(base, updates)

    assert base["company"]["name"] == "Test"  # Não afetado
    assert base["company"]["sector"] == "Finance"  # Atualizado
    assert base["engagement"]["phase"] == "DISCOVERY"


# ============================================================================
# TESTES DE SEARCH_PROFILES
# ============================================================================


def test_search_profiles_success(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa busca semântica bem-sucedida de ClientProfiles."""
    # Mock resposta do Mem0
    mock_result = MagicMock()
    mock_result.metadata = {"profile_data": sample_profile.to_mem0(), "user_id": "test_client_123"}
    mock_mem0_client.search.return_value = [mock_result]

    profiles = mem0_wrapper.search_profiles("empresas de tecnologia", limit=5)

    assert len(profiles) == 1
    assert isinstance(profiles[0], ClientProfile)
    assert profiles[0].company.name == "Empresa Teste Ltda"
    mock_mem0_client.search.assert_called_once_with(query="empresas de tecnologia", limit=5)


def test_search_profiles_empty_results(mem0_wrapper, mock_mem0_client):
    """Testa que busca sem resultados retorna lista vazia."""
    mock_mem0_client.search.return_value = []

    profiles = mem0_wrapper.search_profiles("query sem resultados")

    assert profiles == []


def test_search_profiles_with_corrupted_data(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa que profiles corrompidos são ignorados na busca."""
    # Mock 2 resultados: 1 válido, 1 corrompido
    mock_valid = MagicMock()
    mock_valid.metadata = {"profile_data": sample_profile.to_mem0()}

    mock_corrupted = MagicMock()
    mock_corrupted.metadata = {"profile_data": {"invalid": "data"}}

    mock_mem0_client.search.return_value = [mock_valid, mock_corrupted]

    profiles = mem0_wrapper.search_profiles("test query")

    # Apenas o válido deve retornar
    assert len(profiles) == 1
    assert profiles[0].client_id == "test_client_123"


# ============================================================================
# TESTES DE ERROR HANDLING E RETRY
# ============================================================================


def test_save_profile_retry_on_connection_error(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa retry automático em falha de conexão (save_profile)."""
    # Primeira chamada falha, segunda sucede
    mock_mem0_client.add.side_effect = [ConnectionError("Network error"), {"success": True}]

    result = mem0_wrapper.save_profile(sample_profile)

    assert result == "test_client_123"
    assert mock_mem0_client.add.call_count == 2  # Retry funcionou


def test_load_profile_retry_on_timeout_error(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa retry automático em timeout (load_profile)."""
    mock_memory = MagicMock()
    mock_memory.metadata = {"profile_data": sample_profile.to_mem0()}

    # Primeira chamada falha, segunda sucede
    mock_mem0_client.get_all.side_effect = [TimeoutError("Timeout"), [mock_memory]]

    profile = mem0_wrapper.load_profile("test_client_123")

    assert profile.client_id == "test_client_123"
    assert mock_mem0_client.get_all.call_count == 2  # Retry funcionou


def test_save_profile_max_retries_exceeded(mem0_wrapper, sample_profile, mock_mem0_client):
    """Testa que após 3 retries, erro é levantado."""
    mock_mem0_client.add.side_effect = ConnectionError("Network error")

    with pytest.raises(ConnectionError):
        mem0_wrapper.save_profile(sample_profile)

    assert mock_mem0_client.add.call_count == 3  # 3 tentativas


# ============================================================================
# SUMÁRIO DE TESTES
# ============================================================================

"""
SUMÁRIO: 18 testes unitários criados (target: 12+)

Cobertura por categoria:
- Inicialização: 4 testes
- Serialização/Deserialização: 3 testes
- save_profile: 2 testes
- load_profile: 3 testes
- update_profile: 3 testes
- search_profiles: 3 testes
- Error handling & Retry: 3 testes

Cobertura estimada: >= 90%
"""
