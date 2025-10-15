"""Configuração global do pytest para o projeto BSC RAG.

Este arquivo é automaticamente carregado pelo pytest antes de executar os testes
e garante que os imports funcionem corretamente adicionando o diretório raiz ao sys.path.

Referência: https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py
"""

import sys
from pathlib import Path

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

