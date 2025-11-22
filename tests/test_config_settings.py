"""
Testes unitários para config/settings.py - FASE 1.6

Valida configurações Mem0 e função validate_memory_config().

NOTA: Testes de Settings com monkeypatch não funcionam porque Settings
é um singleton já inicializado. Focamos em testar validate_memory_config().
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Adicionar project root ao sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_memory_config
from src.memory.factory import MemoryFactory


class TestMem0SettingsLoaded:
    """Testes para validar que Settings foi carregado corretamente do .env."""

    def test_mem0_api_key_loaded(self):
        """Teste 1: MEM0_API_KEY deve estar carregada do .env."""
        assert settings.mem0_api_key is not None
        assert settings.mem0_api_key.startswith("m0-")
        assert len(settings.mem0_api_key) >= 20

    def test_memory_provider_default(self):
        """Teste 2: MEMORY_PROVIDER deve ser 'mem0' por default."""
        assert settings.memory_provider == "mem0"

    def test_mem0_org_info_loaded(self):
        """Teste 3: Informações da organização Mem0 devem estar carregadas."""
        # Essas são opcionais, mas devem existir no .env do projeto
        assert settings.mem0_org_name is not None
        assert settings.mem0_org_id is not None
        assert settings.mem0_project_id is not None

    def test_all_required_keys_present(self):
        """Teste 4: Todas as chaves obrigatórias devem estar presentes."""
        assert settings.openai_api_key is not None
        assert settings.cohere_api_key is not None
        assert settings.mem0_api_key is not None


class TestValidateMemoryConfig:
    """Testes para função validate_memory_config()."""

    def test_validate_memory_config_success(self):
        """Teste 5: Validação bem-sucedida com config real do .env."""
        # Execute: Deve passar porque config está correta
        validate_memory_config()

        # Assert: Verificar que 'mem0' está disponível no factory
        available = MemoryFactory.list_providers()
        assert "mem0" in available
        assert settings.memory_provider in available

    def test_memory_factory_has_mem0_registered(self):
        """Teste 6: MemoryFactory deve ter 'mem0' registrado."""
        available = MemoryFactory.list_providers()
        assert "mem0" in available
        assert isinstance(available, list)

    def test_validate_memory_config_uses_correct_provider(self):
        """Teste 7: validate_memory_config deve validar o provider correto."""
        # Não deve levantar exceção
        validate_memory_config()

        # Settings deve estar usando um provider válido
        assert settings.memory_provider in MemoryFactory.list_providers()

    def test_mem0_api_key_format(self):
        """Teste 8: MEM0_API_KEY deve ter formato válido."""
        # Validar formato
        assert settings.mem0_api_key.startswith("m0-")
        assert len(settings.mem0_api_key) > 20

        # Validar que não está vazia ou com placeholder
        assert settings.mem0_api_key != "m0-your-mem0-api-key-here"
        assert "your" not in settings.mem0_api_key.lower()
        assert "placeholder" not in settings.mem0_api_key.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
