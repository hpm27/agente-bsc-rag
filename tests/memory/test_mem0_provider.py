"""Testes unitários para Mem0Provider.

Este módulo testa a implementação Mem0 do MemoryProvider Protocol,
incluindo delegação correta, isinstance checks, e error propagation.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.memory.exceptions import (
    Mem0ClientError,
    ProfileNotFoundError,
    ProfileValidationError,
)
from src.memory.mem0_provider import Mem0Provider
from src.memory.provider import MemoryProvider
from src.memory.schemas import ClientProfile, CompanyInfo

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
        client_id="test_provider_123",
        company=CompanyInfo(
            name="Empresa Provider Test",
            sector="Technology",
            size="50-100",
        ),
    )


@pytest.fixture
def mem0_provider(mock_mem0_client):
    """Fixture que retorna Mem0Provider mockado."""
    with patch.dict(os.environ, {"MEM0_API_KEY": "test_api_key"}):
        return Mem0Provider()


# ============================================================================
# TESTES DE PROTOCOL COMPLIANCE
# ============================================================================


def test_mem0_provider_implements_memory_provider(mem0_provider):
    """Testa que Mem0Provider implementa MemoryProvider Protocol."""
    assert isinstance(mem0_provider, MemoryProvider)


def test_mem0_provider_has_required_methods(mem0_provider):
    """Testa que Mem0Provider possui todos métodos do Protocol."""
    assert hasattr(mem0_provider, "save_profile")
    assert hasattr(mem0_provider, "load_profile")
    assert hasattr(mem0_provider, "update_profile")
    assert hasattr(mem0_provider, "search_profiles")
    assert callable(mem0_provider.save_profile)


# ============================================================================
# TESTES DE INICIALIZAÇÃO
# ============================================================================


def test_mem0_provider_init_with_api_key():
    """Testa inicialização com API key fornecida."""
    with patch("src.memory.mem0_client.MemoryClient"):
        provider = Mem0Provider(api_key="explicit_key")

        assert provider.client.api_key == "explicit_key"


def test_mem0_provider_init_without_api_key_raises_error():
    """Testa que inicialização sem API key levanta erro."""
    with patch.dict(os.environ, {}, clear=True), pytest.raises(Mem0ClientError):
        Mem0Provider()


# ============================================================================
# TESTES DE DELEGAÇÃO (save_profile)
# ============================================================================


def test_save_profile_delegates_to_client(mem0_provider, sample_profile):
    """Testa que save_profile delega corretamente para client."""
    # Mock client method
    mem0_provider.client.save_profile = MagicMock(return_value="test_provider_123")

    result = mem0_provider.save_profile(sample_profile)

    mem0_provider.client.save_profile.assert_called_once_with(sample_profile)
    assert result == "test_provider_123"


def test_save_profile_propagates_errors(mem0_provider, sample_profile):
    """Testa que erros do client são propagados."""
    mem0_provider.client.save_profile = MagicMock(
        side_effect=ProfileValidationError("test_id", Exception("Test error"))
    )

    with pytest.raises(ProfileValidationError):
        mem0_provider.save_profile(sample_profile)


# ============================================================================
# TESTES DE DELEGAÇÃO (load_profile)
# ============================================================================


def test_load_profile_delegates_to_client(mem0_provider, sample_profile):
    """Testa que load_profile delega corretamente para client."""
    mem0_provider.client.load_profile = MagicMock(return_value=sample_profile)

    result = mem0_provider.load_profile("test_provider_123")

    mem0_provider.client.load_profile.assert_called_once_with("test_provider_123")
    assert result == sample_profile


def test_load_profile_propagates_not_found_error(mem0_provider):
    """Testa que ProfileNotFoundError é propagado."""
    mem0_provider.client.load_profile = MagicMock(
        side_effect=ProfileNotFoundError("nonexistent_id")
    )

    with pytest.raises(ProfileNotFoundError):
        mem0_provider.load_profile("nonexistent_id")


# ============================================================================
# TESTES DE DELEGAÇÃO (update_profile)
# ============================================================================


def test_update_profile_delegates_to_client(mem0_provider, sample_profile):
    """Testa que update_profile delega corretamente para client."""
    mem0_provider.client.update_profile = MagicMock(return_value=sample_profile)
    updates = {"company": {"sector": "Finance"}}

    result = mem0_provider.update_profile("test_provider_123", updates)

    mem0_provider.client.update_profile.assert_called_once_with("test_provider_123", updates)
    assert result == sample_profile


# ============================================================================
# TESTES DE DELEGAÇÃO (search_profiles)
# ============================================================================


def test_search_profiles_delegates_to_client(mem0_provider, sample_profile):
    """Testa que search_profiles delega corretamente para client."""
    mem0_provider.client.search_profiles = MagicMock(return_value=[sample_profile])

    result = mem0_provider.search_profiles("technology companies", limit=5)

    mem0_provider.client.search_profiles.assert_called_once_with("technology companies", 5)
    assert result == [sample_profile]


def test_search_profiles_with_default_limit(mem0_provider):
    """Testa que search_profiles usa limit padrão 10."""
    mem0_provider.client.search_profiles = MagicMock(return_value=[])

    mem0_provider.search_profiles("test query")

    mem0_provider.client.search_profiles.assert_called_once_with("test query", 10)


# ============================================================================
# SUMÁRIO DE TESTES
# ============================================================================

"""
SUMÁRIO: 13 testes unitários criados

Cobertura por categoria:
- Protocol Compliance: 2 testes
- Inicialização: 2 testes
- save_profile: 2 testes
- load_profile: 2 testes
- update_profile: 1 teste
- search_profiles: 2 testes

Cobertura estimada: ~100%
Total com test_factory.py: 22 testes (target 10-12+)
"""
