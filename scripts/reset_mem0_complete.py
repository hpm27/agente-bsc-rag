"""Script COMPLETO para resetar Mem0 - Deleta memorias E entities.

SPRINT 4 - Reset total do database Mem0 (sem confirmacao).

Executa:
1. Lista todos users
2. Deleta todas memorias de cada user (delete_all)
3. Deleta a entity do user (DELETE /entities/user/{id})

USO: python scripts/reset_mem0_complete.py
"""

from dotenv import load_dotenv

load_dotenv()

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from config.settings import settings
from mem0 import MemoryClient

print("\n" + "=" * 70)
print("[EXEC] RESET COMPLETO MEM0 - MEMORIAS + ENTITIES")
print("=" * 70 + "\n")

# Inicializar client
client = MemoryClient(api_key=settings.mem0_api_key)

# Listar todos users
users_response = client.users()
users = users_response.get("results", []) if isinstance(users_response, dict) else users_response

print(f"[INFO] Users encontrados: {len(users)}\n")

if not users:
    print("[OK] Database ja esta limpo!")
    sys.exit(0)

# Processar cada user
deleted_memories = 0
deleted_entities = 0
failed = 0

for idx, user in enumerate(users, 1):
    user_id = user.get("name") if isinstance(user, dict) else getattr(user, "name", None)
    entity_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    total_mems = user.get("total_memories", 0) if isinstance(user, dict) else 0

    if not user_id or not entity_id:
        continue

    print(f"[{idx:02d}/{len(users)}] Processing {user_id[:13]}... ({total_mems} mem)")

    # STEP 1: Deletar memorias
    try:
        client.delete_all(user_id=user_id)
        print(f"          [OK] Memorias deletadas ({total_mems})")
        deleted_memories += 1
    except Exception as e:
        print(f"          [ERRO] Falha ao deletar memorias: {e}")
        failed += 1
        continue

    # STEP 2: Deletar entity
    try:
        # API direta: DELETE /v1/entities/user/{entity_id}
        url = f"https://api.mem0.ai/v1/entities/user/{entity_id}/"
        headers = {"Authorization": f"Token {settings.mem0_api_key}"}

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            print(f"          [OK] Entity deletada (ID: {entity_id})")
            deleted_entities += 1
        else:
            print(f"          [WARN] Entity retornou {response.status_code}: {response.text[:50]}")

    except Exception as e:
        print(f"          [ERRO] Falha ao deletar entity: {e}")
        continue

print(f"\n{'='*70}")
print("[DONE] Reset completo!")
print(f"[STATS] Memorias deletadas: {deleted_memories}/{len(users)}")
print(f"[STATS] Entities deletadas: {deleted_entities}/{len(users)}")
print(f"[STATS] Falhas: {failed}")
print(f"{'='*70}\n")

print("[SUCCESS] Database Mem0 completamente resetado!")
print("[NEXT] Teste workflow novamente: streamlit run app.py")
print("       Pagina 0 - Consultor BSC\n")
