"""Testes unitários para memory nodes (LangGraph integration).

Valida comportamento de load_client_memory e save_client_memory
em diversos cenários: cliente existente, cliente novo, query anônima,
erros de API, etc.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from src.graph.memory_nodes import (
    create_placeholder_profile,
    load_client_memory,
    save_client_memory,
)
from src.graph.states import BSCState
from src.memory.exceptions import Mem0ClientError, ProfileNotFoundError
from src.memory.schemas import ClientProfile, CompanyInfo, EngagementState

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_profile():
    """ClientProfile de exemplo para testes."""
    return ClientProfile(
        client_id="cliente_test_123",
        company=CompanyInfo(name="Test Corp", sector="Tecnologia", size="média"),
        engagement=EngagementState(
            current_phase="DISCOVERY",
            started_at=datetime.now(timezone.utc),
            last_interaction=datetime.now(timezone.utc),
        ),
    )


@pytest.fixture
def sample_state():
    """BSCState de exemplo para testes."""
    return BSCState(
        query="Como implementar BSC em tecnologia?",
        session_id="session_123",
        user_id="cliente_test_123",
    )


@pytest.fixture
def sample_state_no_user_id():
    """BSCState sem user_id (query anônima)."""
    return BSCState(query="O que é BSC?", session_id="session_456")


# ============================================================================
# TESTES: load_client_memory
# ============================================================================


def test_load_client_memory_success(sample_state, sample_profile):
    """Deve carregar profile existente com sucesso."""
    # Mock MemoryFactory e provider
    mock_provider = Mock()
    mock_provider.load_profile.return_value = sample_profile

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        result = load_client_memory(sample_state)

    # Verificações
    assert "client_profile" in result
    assert result["client_profile"] is not None
    assert result["client_profile"].company.name == "Test Corp"
    assert result["client_profile"].engagement.current_phase == "DISCOVERY"

    # Provider foi chamado corretamente
    mock_provider.load_profile.assert_called_once_with("cliente_test_123")


def test_load_client_memory_not_found(sample_state):
    """Deve retornar None para cliente novo (ProfileNotFoundError)."""
    # Mock MemoryFactory e provider
    mock_provider = Mock()
    mock_provider.load_profile.side_effect = ProfileNotFoundError("cliente_test_123")

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        result = load_client_memory(sample_state)

    # Verificações
    assert "client_profile" in result
    assert result["client_profile"] is None  # Cliente novo


def test_load_client_memory_no_user_id(sample_state_no_user_id):
    """Deve skip load para query anônima (sem user_id)."""
    # Não deve nem tentar acessar MemoryFactory
    result = load_client_memory(sample_state_no_user_id)

    # Verificações
    assert "client_profile" in result
    assert result["client_profile"] is None


def test_load_client_memory_api_error(sample_state):
    """Deve continuar graciosamente em erro de API Mem0."""
    # Mock MemoryFactory e provider
    mock_provider = Mock()
    mock_provider.load_profile.side_effect = Mem0ClientError("API timeout")

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        result = load_client_memory(sample_state)

    # Verificações - não deve falhar, apenas retorna None
    assert "client_profile" in result
    assert result["client_profile"] is None


def test_load_client_memory_factory_init_error(sample_state):
    """Deve continuar graciosamente se MemoryFactory.get_provider falhar."""
    # Mock MemoryFactory para falhar na inicialização
    with patch(
        "src.graph.memory_nodes.MemoryFactory.get_provider", side_effect=Exception("Config error")
    ):
        result = load_client_memory(sample_state)

    # Verificações - não deve falhar, apenas retorna None
    assert "client_profile" in result
    assert result["client_profile"] is None


# ============================================================================
# TESTES: save_client_memory
# ============================================================================


def test_save_client_memory_success(sample_state, sample_profile):
    """Deve salvar profile existente com sucesso."""
    # Adicionar profile ao state
    sample_state.client_profile = sample_profile

    # Mock MemoryFactory e provider
    mock_provider = Mock()
    mock_provider.save_profile.return_value = "cliente_test_123"

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        result = save_client_memory(sample_state)

    # Verificações
    assert "user_id" in result
    assert result["user_id"] == "cliente_test_123"

    # Provider foi chamado
    mock_provider.save_profile.assert_called_once()

    # Profile foi atualizado (last_interaction atualizado)
    # Não verificamos total_interactions pois esse campo foi removido do schema


def test_save_client_memory_no_profile(sample_state):
    """Deve skip save se não houver client_profile no state."""
    # State sem profile
    result = save_client_memory(sample_state)

    # Verificações - retorna dict vazio (não há user_id para retornar)
    assert result == {}


def test_save_client_memory_generates_user_id(sample_profile):
    """Deve gerar UUID se user_id não existir."""
    # State sem user_id mas com profile
    state = BSCState(query="Como implementar BSC?", client_profile=sample_profile)

    # Mock MemoryFactory e provider
    mock_provider = Mock()
    mock_provider.save_profile.return_value = "new_uuid"

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        result = save_client_memory(state)

    # Verificações - deve ter gerado UUID
    assert "user_id" in result
    assert result["user_id"] is not None
    assert len(result["user_id"]) > 0  # UUID válido


def test_save_client_memory_updates_timestamps(sample_state, sample_profile):
    """Deve atualizar last_interaction."""
    # Timestamp original
    original_timestamp = sample_profile.engagement.last_interaction

    # Adicionar profile ao state
    sample_state.client_profile = sample_profile

    # Mock MemoryFactory e provider
    mock_provider = Mock()

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        save_client_memory(sample_state)

    # Verificações - timestamps atualizados
    assert sample_profile.engagement.last_interaction >= original_timestamp


def test_save_client_memory_api_error(sample_state, sample_profile):
    """Deve continuar graciosamente em erro de API Mem0."""
    # Adicionar profile ao state
    sample_state.client_profile = sample_profile

    # Mock MemoryFactory e provider com erro
    mock_provider = Mock()
    mock_provider.save_profile.side_effect = Mem0ClientError("API timeout")

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        result = save_client_memory(sample_state)

    # Verificações - não deve falhar, retorna user_id mesmo sem salvar
    assert "user_id" in result
    assert result["user_id"] == "cliente_test_123"


def test_save_client_memory_factory_init_error(sample_state, sample_profile):
    """Deve continuar graciosamente se MemoryFactory.get_provider falhar."""
    # Adicionar profile ao state
    sample_state.client_profile = sample_profile

    # Mock MemoryFactory para falhar na inicialização
    with patch(
        "src.graph.memory_nodes.MemoryFactory.get_provider", side_effect=Exception("Config error")
    ):
        result = save_client_memory(sample_state)

    # Verificações - não deve falhar, retorna user_id
    assert "user_id" in result
    assert result["user_id"] == "cliente_test_123"


# ============================================================================
# TESTES: create_placeholder_profile
# ============================================================================


def test_create_placeholder_profile():
    """Deve criar profile placeholder com campos básicos."""
    user_id = "new_cliente_123"
    company_name = "Acme Corp"

    profile = create_placeholder_profile(user_id, company_name)

    # Verificações
    assert profile.client_id == user_id
    assert profile.company.name == company_name
    assert profile.company.sector == "A definir"
    assert profile.company.size == "média"
    assert profile.engagement.current_phase == "ONBOARDING"
    # total_interactions foi removido do schema (não existe mais)


def test_create_placeholder_profile_default_name():
    """Deve usar nome default se não fornecido."""
    user_id = "new_cliente_456"

    profile = create_placeholder_profile(user_id)

    # Verificações
    assert profile.company.name == "Cliente"  # Default


# ============================================================================
# TESTES INTEGRAÇÃO: load -> save cycle
# ============================================================================


def test_load_save_integration(sample_state):
    """Deve funcionar ciclo completo: load (não encontra) -> save (cria)."""
    # Mock provider
    mock_provider = Mock()
    mock_provider.load_profile.side_effect = ProfileNotFoundError("cliente_test_123")
    mock_provider.save_profile.return_value = "cliente_test_123"

    with patch("src.graph.memory_nodes.MemoryFactory.get_provider", return_value=mock_provider):
        # Load (cliente novo)
        load_result = load_client_memory(sample_state)
        assert load_result["client_profile"] is None

        # Criar profile placeholder
        new_profile = create_placeholder_profile(sample_state.user_id, "Test Corp")
        sample_state.client_profile = new_profile

        # Save (persiste)
        save_result = save_client_memory(sample_state)
        assert save_result["user_id"] == "cliente_test_123"

        # Provider foi chamado
        mock_provider.load_profile.assert_called_once()
        mock_provider.save_profile.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
