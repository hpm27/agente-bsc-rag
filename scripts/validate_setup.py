"""
Script de validação do setup do ambiente.
Verifica se todas as dependências e configurações estão corretas.
"""

import sys
from pathlib import Path

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_status(message, status):
    """Imprime status colorido."""
    symbols = {"ok": "[OK]", "error": "[ERRO]", "warning": "[WARN]", "info": "[INFO]"}
    print(f"{symbols.get(status, '[-]')} {message}")


def check_python_version():
    """Verifica versão do Python."""
    print("\n[CHECK] Verificando Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "ok")
        return True
    print_status(f"Python {version.major}.{version.minor} (requer 3.10+)", "error")
    return False


def check_dependencies():
    """Verifica dependências instaladas."""
    print("\n[CHECK] Verificando Dependencias...")

    dependencies = {
        "loguru": "Logging",
        "pydantic": "Validação",
        "pydantic_settings": "Configurações",
        "openai": "OpenAI API",
        "cohere": "Cohere API",
        "anthropic": "Anthropic API",
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "qdrant_client": "Qdrant",
        "weaviate": "Weaviate",
        "redis": "Redis",
    }

    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print_status(f"{name}: instalado", "ok")
        except ImportError:
            print_status(f"{name}: não instalado", "error")
            all_ok = False

    return all_ok


def check_env_file():
    """Verifica arquivo .env."""
    print("\n[CHECK] Verificando Configuracoes...")

    env_file = Path(".env")
    if not env_file.exists():
        print_status("Arquivo .env: não encontrado", "error")
        print_status("Execute: cp .env.example .env e configure as keys", "info")
        return False

    print_status("Arquivo .env: encontrado", "ok")

    # Verifica configurações críticas
    try:
        from config.settings import settings

        checks = {
            "OPENAI_API_KEY": (settings.openai_api_key, "sk-"),  # OpenAI keys start with sk-
            "COHERE_API_KEY": (settings.cohere_api_key, None),  # Cohere keys have variable format
        }

        for key, (value, required_prefix) in checks.items():
            # Check if value exists and is not placeholder
            is_valid = value and "your-" not in value.lower()

            # For OpenAI/Anthropic, also check prefix
            if required_prefix and is_valid:
                is_valid = required_prefix in value

            if is_valid:
                print_status(f"{key}: configurado", "ok")
            else:
                print_status(f"{key}: não configurado", "warning")

        return True
    except Exception as e:
        print_status(f"Erro ao carregar settings: {e}", "error")
        return False


def check_directories():
    """Verifica estrutura de diretórios."""
    print("\n[CHECK] Verificando Diretorios...")

    dirs = [
        "data",
        "data/bsc_literature",
        "models",
        "logs",
        "src/rag",
        "src/agents",
        "src/tools",
        "tests",
    ]

    all_ok = True
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            print_status(f"{dir_path}: existe", "ok")
        else:
            print_status(f"{dir_path}: não existe", "error")
            all_ok = False

    return all_ok


def check_docker():
    """Verifica se Docker está rodando."""
    print("\n[CHECK] Verificando Docker...")

    import subprocess

    try:
        result = subprocess.run(
            ["docker", "ps"], check=False, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print_status("Docker: rodando", "ok")

            # Verifica containers
            if "qdrant" in result.stdout or "weaviate" in result.stdout:
                print_status("Containers BSC: rodando", "ok")
            else:
                print_status("Containers BSC: não iniciados", "warning")
                print_status("Execute: docker-compose up -d", "info")
            return True
        print_status("Docker: não rodando", "error")
        return False
    except Exception as e:
        print_status(f"Docker: erro ao verificar ({e})", "error")
        return False


def check_modules():
    """Verifica se módulos do projeto são importáveis."""
    print("\n[CHECK] Verificando Modulos do Projeto...")

    modules = [
        ("src.rag.embeddings", "Embeddings"),
        ("src.rag.retriever", "Retriever"),
        ("src.rag.reranker", "Reranker"),
        ("src.tools.rag_tools", "RAG Tools"),
        ("src.agents.orchestrator", "Orchestrator"),
        ("src.agents.financial_agent", "Financial Agent"),
        ("config.settings", "Settings"),
    ]

    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print_status(f"{display_name}: importável", "ok")
        except Exception as e:
            print_status(f"{display_name}: erro ({type(e).__name__})", "error")
            all_ok = False

    return all_ok


def check_bsc_documents():
    """Verifica se há documentos BSC."""
    print("\n[CHECK] Verificando Documentos BSC...")

    lit_dir = Path("data/bsc_literature")
    if not lit_dir.exists():
        print_status("Pasta bsc_literature: não existe", "error")
        return False

    # Verificar múltiplos formatos (PDF, Markdown, Word, TXT)
    pdfs = list(lit_dir.glob("*.pdf"))
    mds = list(lit_dir.glob("*.md"))
    docs = list(lit_dir.glob("*.docx")) + list(lit_dir.glob("*.doc"))
    txts = list(lit_dir.glob("*.txt"))

    all_docs = pdfs + mds + docs + txts

    if all_docs:
        # Mostrar estatísticas por tipo
        stats = []
        if pdfs:
            stats.append(f"{len(pdfs)} PDF")
        if mds:
            stats.append(f"{len(mds)} Markdown")
        if docs:
            stats.append(f"{len(docs)} Word")
        if txts:
            stats.append(f"{len(txts)} TXT")

        print_status(f"Documentos: {len(all_docs)} encontrados ({', '.join(stats)})", "ok")

        # Mostrar primeiros 5 documentos (safe encoding para Windows)
        for doc in all_docs[:5]:
            try:
                print(f"   - {doc.name}")
            except UnicodeEncodeError:
                # Fallback para nomes com caracteres especiais
                safe_name = doc.name.encode("ascii", errors="replace").decode("ascii")
                print(f"   - {safe_name}")
        if len(all_docs) > 5:
            print(f"   ... e mais {len(all_docs) - 5}")

        return True
    print_status("Documentos: nenhum encontrado", "warning")
    print_status("Adicione documentos BSC em data/bsc_literature/", "info")
    print_status("Formatos aceitos: PDF, Markdown (.md), Word (.docx), TXT", "info")
    return False


def main():
    """Executa todas as verificações."""
    print("=" * 60)
    print("[VALIDATE] Setup - Agente BSC RAG")
    print("=" * 60)

    checks = [
        ("Python", check_python_version()),
        ("Dependências", check_dependencies()),
        ("Configurações", check_env_file()),
        ("Diretórios", check_directories()),
        ("Docker", check_docker()),
        ("Módulos", check_modules()),
        ("Documentos BSC", check_bsc_documents()),
    ]

    print("\n" + "=" * 60)
    print("[SUMMARY] Resumo da Validacao")
    print("=" * 60)

    for name, status in checks:
        symbol = "[OK]" if status else "[ERRO]"
        print(f"{symbol} {name}")

    total = len(checks)
    passed = sum(1 for _, status in checks if status)
    percentage = (passed / total) * 100

    print(f"\n[SCORE] {passed}/{total} ({percentage:.0f}%)")

    if percentage == 100:
        print("\n[SUCCESS] Setup completo! Tudo pronto para usar.")
        print("\n[INFO] Proximos passos:")
        print("   1. Adicione documentos BSC (se ainda nao adicionou)")
        print("   2. Execute: python scripts/build_knowledge_base.py")
        print("   3. Rode testes: pytest tests/ -v")
        print("   4. Inicie a aplicacao!")
    elif percentage >= 70:
        print("\n[WARN] Setup quase completo! Alguns itens precisam de atencao.")
        print("   Verifique os itens marcados com [ERRO] acima.")
    else:
        print("\n[ERRO] Setup incompleto. Siga o guia SETUP.md:")
        print("   1. Execute: ./setup.ps1 (Windows)")
        print("   2. Configure API keys no .env")
        print("   3. Rode: docker-compose up -d")
        print("   4. Execute este script novamente")

    print("\n" + "=" * 60)

    return percentage == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
