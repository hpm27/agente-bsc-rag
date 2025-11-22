"""
Testes unitários para config/settings.py - FASE 1.6

Valida configurações Mem0 e função validate_memory_config().
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

# Adicionar project root ao sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings, validate_memory_config
from src.memory.factory import MemoryFactory


class TestMem0Settings:
    """Testes para validações de configurações Mem0."""

    def test_valid_mem0_api_key(self, monkeypatch):
        """Teste 1: MEM0_API_KEY válida deve passar."""
        # Setup: Definir variáveis de ambiente válidas
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Execute
        settings = Settings()

        # Assert
        assert settings.mem0_api_key == "m0-valid-key-with-40-plus-characters-here"
        assert settings.memory_provider == "mem0"  # default

    def test_mem0_api_key_empty_raises_error(self, monkeypatch):
        """Teste 2: MEM0_API_KEY vazia deve levantar ValidationError."""
        # Setup
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("COHERE_API_KEY", "test-cohere-key")
        monkeypatch.setenv("MEM0_API_KEY", "")

        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "MEM0_API_KEY" in str(exc_info.value)

    def test_mem0_api_key_missing_raises_error(self, monkeypatch):
        """Teste 3: MEM0_API_KEY ausente deve levantar ValidationError."""
        # Setup: Não definir MEM0_API_KEY
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
        monkeypatch.setenv("COHERE_API_KEY", "test-cohere-key")
        monkeypatch.delenv("MEM0_API_KEY", raising=False)

        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_str = str(exc_info.value)
        assert "MEM0_API_KEY" in error_str or "mem0_api_key" in error_str

    def test_mem0_api_key_invalid_prefix_raises_error(self, monkeypatch):
        """Teste 4: MEM0_API_KEY sem prefixo 'm0-' deve levantar ValidationError."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "invalid-key-without-m0-prefix-but-long-enough",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "m0-" in str(exc_info.value).lower()

    def test_mem0_api_key_too_short_raises_error(self, monkeypatch):
        """Teste 5: MEM0_API_KEY muito curta deve levantar ValidationError."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-short",  # < 20 caracteres
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_str = str(exc_info.value).lower()
        assert "muito curta" in error_str or "too short" in error_str

    def test_memory_provider_default_is_mem0(self, monkeypatch):
        """Teste 6: MEMORY_PROVIDER default deve ser 'mem0'."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Execute
        settings = Settings()

        # Assert
        assert settings.memory_provider == "mem0"

    def test_memory_provider_custom_valid(self, monkeypatch):
        """Teste 7: MEMORY_PROVIDER customizado válido deve passar."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
            "MEMORY_PROVIDER": "supabase",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Execute
        settings = Settings()

        # Assert
        assert settings.memory_provider == "supabase"

    def test_memory_provider_invalid_raises_error(self, monkeypatch):
        """Teste 8: MEMORY_PROVIDER inválido deve levantar ValidationError."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
            "MEMORY_PROVIDER": "invalid_provider",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_str = str(exc_info.value).lower()
        assert "memory_provider" in error_str or "inválido" in error_str


class TestValidateMemoryConfig:
    """Testes para função validate_memory_config()."""

    @patch("config.settings.MemoryFactory")
    def test_validate_memory_config_success_mem0(self, mock_factory, monkeypatch):
        """Teste 9: Validação bem-sucedida com MEMORY_PROVIDER='mem0'."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
            "MEMORY_PROVIDER": "mem0",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Mock MemoryFactory para retornar ['mem0'] como providers disponíveis
        mock_factory.list_providers.return_value = ["mem0"]

        # Execute (não deve levantar exceção)
        validate_memory_config()

        # Assert
        mock_factory.list_providers.assert_called_once()

    @patch("config.settings.MemoryFactory")
    def test_validate_memory_config_provider_not_registered(self, mock_factory, monkeypatch):
        """Teste 10: Validação deve falhar se provider não estiver registrado."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
            "MEMORY_PROVIDER": "supabase",  # Provider não registrado
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Mock MemoryFactory retornando apenas ['mem0']
        mock_factory.list_providers.return_value = ["mem0"]

        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            validate_memory_config()

        assert "não está registrado" in str(exc_info.value)
        assert "supabase" in str(exc_info.value)

    def test_validate_memory_config_integration_real_factory(self):
        """Teste 11: Validação integrada com MemoryFactory real (mem0 registrado)."""
        # Execute: Deve passar porque 'mem0' está registrado no factory
        validate_memory_config()

        # Assert: Verificar que 'mem0' está disponível
        available = MemoryFactory.list_providers()
        assert "mem0" in available

    @patch("config.settings.MemoryFactory")
    def test_validate_memory_config_import_error(self, mock_factory, monkeypatch):
        """Teste 12: Validação deve falhar gracefully se MemoryFactory não puder ser importado."""
        # Setup
        env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "COHERE_API_KEY": "test-cohere-key",
            "MEM0_API_KEY": "m0-valid-key-with-40-plus-characters-here",
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Mock MemoryFactory.list_providers para levantar ImportError
        mock_factory.list_providers.side_effect = ImportError("Mock import error")

        # Execute & Assert
        with pytest.raises(ImportError) as exc_info:
            validate_memory_config()

        assert "Mock import error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
