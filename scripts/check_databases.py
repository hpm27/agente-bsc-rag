#!/usr/bin/env python
"""Script para verificar conteudo dos bancos de dados."""

import sqlite3
from pathlib import Path

def check_langgraph():
    """Verifica banco LangGraph."""
    db_path = Path("data/langgraph_checkpoints.db")
    if not db_path.exists():
        print("Banco LangGraph NAO existe")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Listar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("=== LANGGRAPH CHECKPOINTS ===")
    print(f"Tabelas: {[t[0] for t in tables]}")
    
    # Contar registros
    for table in tables:
        table_name = table[0]
        if table_name != "sqlite_sequence":
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} registros")
    
    # Ver ultimos checkpoints
    try:
        cursor.execute("SELECT thread_id, checkpoint_ns FROM checkpoints LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            print("\nUltimos checkpoints:")
            for r in rows:
                thread_id = r[0][:40] if r[0] else "N/A"
                print(f"  thread_id: {thread_id}...")
    except Exception as e:
        print(f"  Erro ao ler checkpoints: {e}")
    
    conn.close()


def check_bsc():
    """Verifica banco BSC."""
    db_path = Path("data/bsc_data.db")
    if not db_path.exists():
        print("\nBanco BSC NAO existe")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\n=== BSC DATA ===")
    print(f"Tabelas: {[t[0] for t in tables]}")
    
    for table in tables:
        table_name = table[0]
        if table_name != "sqlite_sequence":
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} registros")
    
    conn.close()


if __name__ == "__main__":
    check_langgraph()
    check_bsc()

