"""
Script de instalação da persistência SQLite local.

EXECUÇÃO ÚNICA após implementação:
1. Cria database SQLite (data/bsc_data.db)
2. Instala dependências SQLAlchemy
3. Testa conexão

Usage:
    python scripts/install_sqlite_persistence.py
"""

import os
import subprocess
import sys
from pathlib import Path

# Configurar PYTHONPATH para importar módulos src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 70)
print("INSTALANDO SQLite PERSISTENCE LAYER")
print("=" * 70 + "\n")

# 1. Instalar SQLAlchemy (versão compatível com Mem0)
print("[1/3] Instalando SQLAlchemy...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy>=2.0.31"])
    print("[OK] SQLAlchemy instalado\n")
except Exception as e:
    print(f"[ERRO] Falha ao instalar SQLAlchemy: {e}\n")
    sys.exit(1)

# 2. Criar database
print("[2/3] Criando database SQLite...")
try:
    from src.database import init_db

    init_db()
    print("[OK] Database criado em data/bsc_data.db\n")
except Exception as e:
    print(f"[ERRO] Falha ao criar database: {e}\n")
    sys.exit(1)

# 3. Testar conexão
print("[3/3] Testando conexão...")
try:
    from src.database import get_db_session
    from src.database.repository import BSCRepository

    with get_db_session() as db:
        repo = BSCRepository(db)
        clients = repo.clients.get_all(db, limit=1)
        print(f"[OK] Conexão testada com sucesso! (Clients: {len(clients)})\n")
except Exception as e:
    print(f"[ERRO] Falha ao testar conexão: {e}\n")
    sys.exit(1)

print("=" * 70)
print("[SUCESSO] SQLite Persistence instalado!")
print("=" * 70)
print("\n[INFO] Próximos passos:")
print("1. Restart do Streamlit: .\\scripts\\restart_streamlit.ps1")
print("2. Executar workflow completo para testar dual persistence")
print("3. Strategy Map e Action Plan agora salvam em SQLite (zero latency!)\n")
