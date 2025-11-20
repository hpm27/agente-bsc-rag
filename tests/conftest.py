"""Configuração global do pytest para o projeto BSC RAG.

Este arquivo é automaticamente carregado pelo pytest antes de executar os testes
e garante que os imports funcionem corretamente adicionando o diretório raiz ao sys.path.

Referência: https://docs.pytest.org/en/stable/reference/fixtures.html#conftest.py
"""

import sys
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

# Adiciona o diretório raiz ao sys.path ANTES de qualquer import
# Isso é executado no momento que o módulo é carregado (module-level code)
project_root = Path(__file__).parent.parent.resolve()

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"[conftest.py] Project root added to sys.path: {project_root}")


def pytest_configure(config):
    """Hook do pytest que executa ANTES de qualquer teste ou import de módulo.

    Garante que o diretório raiz está no sys.path antes de importar qualquer módulo.
    """
    # Garantir que o project root está no sys.path (redundância intencional)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"[pytest_configure] Project root added to sys.path: {project_root}")


# ============================================================================
# FIXTURES PARA TESTES E2E DE MEMÓRIA (FASE 1.8)
# ============================================================================


@pytest.fixture(scope="function")
def test_user_id() -> str:
    """Gera um user_id único para cada teste.

    Usa UUID para garantir isolamento completo entre testes.

    Returns:
        str: UUID no formato 'test_user_<uuid>'
    """
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def mem0_client() -> Generator:
    """Fornece instância do Mem0ClientWrapper compartilhada.

    Best Practice (2025):
    - Scope function para isolamento
    - API real para validação E2E
    - Cleanup manual via test_user_id

    Yields:
        Mem0ClientWrapper: Instância configurada do cliente Mem0

    Note:
        Cleanup de profiles específicos deve ser feito manualmente no teste
        ou via fixture cleanup_test_profile.
    """
    from config.settings import settings

    from src.memory.mem0_client import Mem0ClientWrapper

    # Skip se MEM0_API_KEY não configurado (CI/CD)
    if not settings.mem0_api_key:
        pytest.skip("MEM0_API_KEY não configurado - pulando teste E2E")

    # Criar cliente passando api_key do settings
    client = Mem0ClientWrapper(api_key=settings.mem0_api_key)

    # Fornecer cliente para o teste
    yield client


@pytest.fixture(scope="function")
def cleanup_test_profile(mem0_client, test_user_id: str) -> Generator:
    """Fixture composta para mem0_client + cleanup automático.

    Combina mem0_client e test_user_id, garantindo cleanup automático.
    Usa o método client.delete_all(user_id) da API Mem0 para deletar
    todas as memórias associadas ao test_user_id.

    Args:
        mem0_client: Cliente Mem0 do fixture
        test_user_id: User ID do fixture

    Yields:
        tuple: (Mem0ClientWrapper, test_user_id)
    """
    # Fornecer cliente e user_id para o teste
    yield (mem0_client, test_user_id)

    # Cleanup: Deletar todas as memórias do user_id de teste
    try:
        # Usar o método delete_all da API Mem0 diretamente no client interno
        mem0_client.client.delete_all(user_id=test_user_id)
        print(f"[CLEANUP] Todas as memórias deletadas para: {test_user_id}")
    except Exception as e:
        print(f"[CLEANUP WARN] Erro ao deletar memórias de {test_user_id}: {e}")


@pytest.fixture(scope="function")
def cleanup_profiles() -> Generator[list[str], None, None]:
    """Fixture para rastrear e limpar múltiplos profiles de teste.

    Uso:
        def test_multiple_users(cleanup_profiles):
            user1 = "test_user_1"
            user2 = "test_user_2"
            cleanup_profiles.extend([user1, user2])
            # ... teste ...

    Yields:
        list[str]: Lista para adicionar user_ids que precisam cleanup
    """
    from config.settings import settings

    from src.memory.mem0_client import Mem0ClientWrapper

    profiles_to_cleanup = []

    # Fornecer lista para o teste
    yield profiles_to_cleanup

    # Cleanup: Deletar todos os profiles rastreados
    if settings.mem0_api_key:
        client = Mem0ClientWrapper(api_key=settings.mem0_api_key)
        for user_id in profiles_to_cleanup:
            try:
                # Usar delete_all da API Mem0 diretamente
                client.client.delete_all(user_id=user_id)
                print(f"[CLEANUP] Todas as memórias deletadas para: {user_id}")
            except Exception as e:
                print(f"[CLEANUP WARN] Erro ao deletar memórias de {user_id}: {e}")
