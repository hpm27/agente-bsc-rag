#!/usr/bin/env python
"""
Script para testar o fix do erro 400 ao carregar profile do Mem0.

SPRINT 4 FIX: Mem0 v2 EXIGE parâmetro 'filters' em TODOS os métodos de busca.
Memória [[memory:10138398]] confirma que filters é OBRIGATÓRIO em v2.

Execução: python scripts/test_mem0_load_fix.py
"""

from dotenv import load_dotenv

load_dotenv()

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

from config.settings import settings
from mem0 import MemoryClient

print("\n" + "=" * 70)
print("TESTE MEM0 LOAD FIX - Verificando erro 400")
print("=" * 70 + "\n")

# Inicializar cliente
print("[1/3] Inicializando cliente Mem0...")
client = MemoryClient(api_key=settings.mem0_api_key)
print("    [OK] Cliente inicializado\n")

# Testar search() com filters obrigatório
print("[2/3] Testando search() com filters obrigatório...")
test_user_id = "test_user_sprint4_" + str(int(time.time()))

try:
    # Primeiro adicionar uma memória de teste
    print(f"    Criando memória de teste para user_id: {test_user_id}")
    client.add(
        messages=[{"role": "user", "content": f"Teste SPRINT 4 - user {test_user_id}"}],
        user_id=test_user_id,
        metadata={"type": "client_profile"},  # Metadata para filtro
    )
    print("    [OK] Memória criada\n")

    # Aguardar eventual consistency
    time.sleep(2)

    # Testar search COM filters (CORRETO em v2)
    print("    Testando search() COM filters (v2 compliant)...")
    results = client.search(
        query="teste",
        user_id=test_user_id,
        filters={"AND": [{"metadata.type": "client_profile"}]},  # OBRIGATÓRIO!
        limit=10,
    )

    # Parsear resultado
    if isinstance(results, dict) and "results" in results:
        results_list = results["results"]
    elif isinstance(results, list):
        results_list = results
    else:
        results_list = []

    if results_list:
        print(f"    [OK] search() funcionou! {len(results_list)} resultado(s)\n")
    else:
        print("    [WARN] search() retornou vazio (pode ser eventual consistency)\n")

except Exception as e:
    print(f"    [ERRO] Falha no search(): {e}\n")
    if "400" in str(e):
        print("    [CRÍTICO] Erro 400 ainda ocorrendo! Verificar implementação.\n")

# Limpar dados de teste
print("[3/3] Limpando dados de teste...")
try:
    client.delete_all(user_id=test_user_id)
    print(f"    [OK] Memórias de {test_user_id} deletadas\n")
except Exception as e:
    print(f"    [WARN] Falha ao limpar: {e}\n")

print("=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)
print("\nCONCLUSÃO:")
print("- Se erro 400 persistir, verificar documentação Mem0 v2")
print("- Memória [[memory:10138398]] confirma filters obrigatório")
print("- Workaround: usar search() com filters ao invés de get_all()")
