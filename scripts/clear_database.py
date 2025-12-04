#!/usr/bin/env python
"""Script para limpar bancos de dados e cache do Agente BSC.

Uso:
    python scripts/clear_database.py           # Limpa tudo (interativo)
    python scripts/clear_database.py --all     # Limpa tudo sem perguntar
    python scripts/clear_database.py --checkpoints  # Apenas checkpoints LangGraph
    python scripts/clear_database.py --bsc     # Apenas banco BSC
    python scripts/clear_database.py --mem0    # Apenas memorias Mem0
    python scripts/clear_database.py --cache   # Apenas cache de embeddings

Criado: Dez/2025
Motivo: Evitar dados de conversas anteriores interferindo em testes
"""

import argparse
import os
import shutil
import sqlite3
import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Paths dos bancos de dados
DATA_DIR = PROJECT_ROOT / "data"
LANGGRAPH_DB = DATA_DIR / "langgraph_checkpoints.db"
LANGGRAPH_SHM = DATA_DIR / "langgraph_checkpoints.db-shm"
LANGGRAPH_WAL = DATA_DIR / "langgraph_checkpoints.db-wal"
BSC_DB = DATA_DIR / "bsc_data.db"
CONTEXTUAL_CACHE = DATA_DIR / "contextual_cache"


def clear_langgraph_checkpoints() -> bool:
    """Limpa checkpoints do LangGraph (conversas e estados)."""
    print("\n[LANGGRAPH] Limpando checkpoints...")
    
    files_to_delete = [LANGGRAPH_DB, LANGGRAPH_SHM, LANGGRAPH_WAL]
    deleted = 0
    
    for file_path in files_to_delete:
        if file_path.exists():
            try:
                os.remove(file_path)
                print(f"  [OK] Removido: {file_path.name}")
                deleted += 1
            except Exception as e:
                print(f"  [ERRO] Falha ao remover {file_path.name}: {e}")
                return False
        else:
            print(f"  [INFO] Nao existe: {file_path.name}")
    
    if deleted > 0:
        print(f"  [OK] {deleted} arquivo(s) removido(s)")
    else:
        print("  [INFO] Nenhum arquivo de checkpoint encontrado")
    
    return True


def clear_bsc_database() -> bool:
    """Limpa banco de dados BSC (clientes, diagnosticos, etc)."""
    print("\n[BSC] Limpando banco de dados...")
    
    if not BSC_DB.exists():
        print("  [INFO] Banco BSC nao existe")
        # Criar banco vazio com tabelas
        _recreate_bsc_tables()
        return True
    
    try:
        # Opção 1: Deletar arquivo completamente
        os.remove(BSC_DB)
        print(f"  [OK] Removido: {BSC_DB.name}")
        # Recriar banco vazio com tabelas
        _recreate_bsc_tables()
        return True
    except Exception as e:
        print(f"  [ERRO] Falha ao remover {BSC_DB.name}: {e}")
        
        # Opção 2: Tentar limpar tabelas individualmente
        try:
            print("  [INFO] Tentando limpar tabelas...")
            conn = sqlite3.connect(str(BSC_DB))
            cursor = conn.cursor()
            
            # Listar tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if table_name != "sqlite_sequence":
                    cursor.execute(f"DELETE FROM {table_name};")
                    print(f"  [OK] Limpa tabela: {table_name}")
            
            conn.commit()
            conn.close()
            print("  [OK] Tabelas limpas")
            return True
        except Exception as e2:
            print(f"  [ERRO] Falha ao limpar tabelas: {e2}")
            return False


def _recreate_bsc_tables() -> None:
    """Recria as tabelas do banco BSC (vazio)."""
    try:
        from src.database.database import init_db
        init_db()
        print("  [OK] Tabelas BSC recriadas (vazias)")
    except Exception as e:
        print(f"  [WARN] Nao foi possivel recriar tabelas: {e}")


def clear_contextual_cache() -> bool:
    """Limpa cache de embeddings contextuais."""
    print("\n[CACHE] Limpando cache de embeddings...")
    
    if not CONTEXTUAL_CACHE.exists():
        print("  [INFO] Cache nao existe")
        return True
    
    try:
        # Contar arquivos antes
        files_before = list(CONTEXTUAL_CACHE.glob("*.npy"))
        count = len(files_before)
        
        # Remover diretorio completo
        shutil.rmtree(CONTEXTUAL_CACHE)
        
        # Recriar diretorio vazio
        CONTEXTUAL_CACHE.mkdir(parents=True, exist_ok=True)
        
        print(f"  [OK] Removidos {count} arquivos de cache")
        return True
    except Exception as e:
        print(f"  [ERRO] Falha ao limpar cache: {e}")
        return False


def clear_mem0_memories() -> bool:
    """Limpa memorias armazenadas no Mem0 (API externa).
    
    OTIMIZADO (Dez/2025): Usa client.users() + delete_all(user_id) ao inves de
    deletar memoria por memoria. Reduz N chamadas API para ~N_usuarios chamadas.
    
    Exemplo: 100 memorias de 3 usuarios = 4 chamadas (1 list + 3 delete_all)
    vs 100 chamadas na implementacao antiga.
    """
    print("\n[MEM0] Limpando memorias Mem0 (metodo otimizado)...")
    
    try:
        from config.settings import settings
        
        if not settings.mem0_api_key:
            print("  [INFO] mem0_api_key nao configurada, pulando...")
            return True
        
        from mem0 import MemoryClient
        
        client = MemoryClient(api_key=settings.mem0_api_key)
        
        try:
            # METODO OTIMIZADO: Listar usuarios + delete_all por usuario
            # 1. Listar todos os usuarios (entidades) - 1 chamada API
            print("  [INFO] Listando usuarios...")
            users = client.users()
            
            if not users:
                print("  [INFO] Nenhum usuario encontrado no Mem0")
                return True
            
            print(f"  [INFO] Encontrados {len(users)} usuario(s)")
            
            # 2. delete_all para cada usuario - 1 chamada por usuario
            total_deleted = 0
            for user in users:
                # Suporta tanto dict (API v2) quanto string (API v1)
                if isinstance(user, dict):
                    user_id = user.get("id") or user.get("name")
                    memories_count = user.get("total_memories", 0)
                else:
                    # user eh uma string (ID diretamente)
                    user_id = str(user)
                    memories_count = "?"
                
                if user_id:
                    try:
                        client.delete_all(user_id=user_id)
                        print(f"  [OK] Usuario '{user_id}': {memories_count} memoria(s) deletadas")
                        if isinstance(memories_count, int):
                            total_deleted += memories_count
                    except Exception as e:
                        print(f"  [WARN] Erro ao deletar memorias do usuario '{user_id}': {e}")
            
            print(f"  [OK] Total: {total_deleted} memoria(s) removida(s) de {len(users)} usuario(s)")
            return True
            
        except Exception as e:
            # Fallback: Metodo antigo se users() falhar
            print(f"  [WARN] Metodo otimizado falhou: {e}")
            print("  [INFO] Tentando metodo alternativo (batch_delete)...")
            return _clear_mem0_memories_fallback(client)
            
    except ImportError:
        print("  [INFO] mem0 nao instalado, pulando...")
        return True
    except Exception as e:
        print(f"  [ERRO] Falha ao limpar Mem0: {e}")
        return False


def _clear_mem0_memories_fallback(client) -> bool:
    """Fallback: Usa batch_delete (ate 1000 por chamada) se users() falhar."""
    try:
        from mem0 import MemoryClient
        
        # Listar memorias
        filters = {"AND": [{"user_id": "*"}]}
        memories = client.get_all(filters=filters, page=1, page_size=1000)
        
        if isinstance(memories, dict) and "results" in memories:
            memories_list = memories["results"]
        elif isinstance(memories, list):
            memories_list = memories
        else:
            memories_list = []
        
        if not memories_list:
            print("  [INFO] Nenhuma memoria encontrada")
            return True
        
        # batch_delete - ate 1000 por chamada
        memory_ids = [{"memory_id": m.get("id")} for m in memories_list if m.get("id")]
        
        if memory_ids:
            # Processar em lotes de 1000
            batch_size = 1000
            for i in range(0, len(memory_ids), batch_size):
                batch = memory_ids[i:i + batch_size]
                try:
                    client.batch_delete(batch)
                    print(f"  [OK] Lote {i // batch_size + 1}: {len(batch)} memoria(s) deletadas")
                except Exception as e:
                    print(f"  [WARN] Erro no batch_delete: {e}")
                    # Fallback final: deletar uma por uma
                    for mem in batch:
                        try:
                            client.delete(mem["memory_id"])
                        except Exception:
                            pass
            
            print(f"  [OK] {len(memory_ids)} memoria(s) removida(s) via batch_delete")
        
        return True
        
    except Exception as e:
        print(f"  [ERRO] Fallback batch_delete falhou: {e}")
        return False


def clear_all(interactive: bool = True) -> bool:
    """Limpa todos os dados."""
    print("=" * 60)
    print("LIMPEZA COMPLETA DO BANCO DE DADOS - AGENTE BSC")
    print("=" * 60)
    
    if interactive:
        print("\nATENCAO: Esta acao ira remover:")
        print("  - Checkpoints LangGraph (historico de conversas)")
        print("  - Banco BSC (clientes, diagnosticos)")
        print("  - Cache de embeddings")
        print("  - Memorias Mem0 (se configurado)")
        print("")
        
        confirm = input("Tem certeza que deseja continuar? (s/N): ").strip().lower()
        if confirm != "s":
            print("\n[CANCELADO] Nenhum dado foi removido.")
            return False
    
    success = True
    
    success = clear_langgraph_checkpoints() and success
    success = clear_bsc_database() and success
    success = clear_contextual_cache() and success
    success = clear_mem0_memories() and success
    
    print("\n" + "=" * 60)
    if success:
        print("[SUCESSO] Todos os dados foram limpos!")
    else:
        print("[AVISO] Alguns dados nao puderam ser limpos.")
    print("=" * 60)
    
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Limpa bancos de dados e cache do Agente BSC"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Limpa tudo sem confirmacao"
    )
    parser.add_argument(
        "--checkpoints", "-c",
        action="store_true",
        help="Limpa apenas checkpoints LangGraph"
    )
    parser.add_argument(
        "--bsc", "-b",
        action="store_true",
        help="Limpa apenas banco BSC"
    )
    parser.add_argument(
        "--mem0", "-m",
        action="store_true",
        help="Limpa apenas memorias Mem0"
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Limpa apenas cache de embeddings"
    )
    
    args = parser.parse_args()
    
    # Se nenhum flag especifico, limpar tudo
    if not any([args.checkpoints, args.bsc, args.mem0, args.cache]):
        success = clear_all(interactive=not args.all)
        sys.exit(0 if success else 1)
    
    # Limpar apenas o que foi especificado
    success = True
    
    if args.checkpoints:
        success = clear_langgraph_checkpoints() and success
    
    if args.bsc:
        success = clear_bsc_database() and success
    
    if args.mem0:
        success = clear_mem0_memories() and success
    
    if args.cache:
        success = clear_contextual_cache() and success
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

