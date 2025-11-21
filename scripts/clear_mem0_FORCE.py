"""Script FORCE para limpar Mem0 - Execucao IMEDIATA sem confirmacao.

SPRINT 4 - ATENCAO: Deleta TUDO imediatamente!

USO: python scripts/clear_mem0_FORCE.py
"""

from dotenv import load_dotenv

load_dotenv()

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings
from mem0 import MemoryClient

print("\n[EXEC] Limpando Mem0...\n")

client = MemoryClient(api_key=settings.mem0_api_key)
users_response = client.users()

users = users_response["results"] if isinstance(users_response, dict) else users_response

print(f"[INFO] Users encontrados: {len(users)}\n")

deleted = 0
for idx, user in enumerate(users, 1):
    user_id = user.get("name") if isinstance(user, dict) else user.name
    mems = user.get("total_memories", 0) if isinstance(user, dict) else 0

    try:
        client.delete_all(user_id=user_id)
        print(f"[{idx:02d}/{len(users)}] [OK] {user_id[:13]}... ({mems} mem)")
        deleted += 1
    except Exception as e:
        print(f"[{idx:02d}/{len(users)}] [ERRO] {user_id[:13]}...: {e}")

print(f"\n[DONE] {deleted}/{len(users)} users deletados\n")
