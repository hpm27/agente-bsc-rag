"""Script DIRETO para limpar TODAS as memorias do Mem0 Platform.

SPRINT 4 - ATENCAO: Este script NAO PEDE CONFIRMACAO!
Executa delecao imediatamente ao rodar.

USO:
    python scripts/clear_mem0_NOW.py

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import os
import sys

from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Carregar .env
load_dotenv()

from config.settings import settings
from mem0 import MemoryClient


def clear_all_mem0_memories_NOW():
    """Deleta TODAS as memorias de TODOS os users IMEDIATAMENTE.

    SEM confirmacao! Use com cuidado!
    """
    print("\n" + "=" * 60)
    print("[EXEC] DELETANDO TODAS AS MEMORIAS DO MEM0 - SEM CONFIRMACAO")
    print("=" * 60 + "\n")

    # Inicializar client
    try:
        client = MemoryClient(api_key=settings.mem0_api_key)
        print("[OK] Conectado ao Mem0 Platform\n")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar Mem0: {e}")
        return 0

    # Listar todos users
    try:
        users_response = client.users()

        # Parsear estrutura
        if isinstance(users_response, dict) and "results" in users_response:
            users = users_response["results"]
            total_count = users_response.get("count", len(users))
        elif isinstance(users_response, list):
            users = users_response
            total_count = len(users)
        else:
            print(f"[ERRO] Estrutura inesperada: {type(users_response)}")
            return 0

        print(f"[INFO] Total de users: {total_count}")
        print(f"[INFO] Users na pagina: {len(users)}\n")

        if not users:
            print("[INFO] Database ja esta limpo!")
            return 0

        # Deletar cada user (SEM CONFIRMACAO!)
        print("[START] Deletando users...\n")
        deleted_count = 0
        failed_count = 0

        for idx, user in enumerate(users, 1):
            user_id = user.get("name") if isinstance(user, dict) else getattr(user, "name", None)
            total_mems = user.get("total_memories", 0) if isinstance(user, dict) else 0

            if not user_id:
                continue

            try:
                # Deletar todas memorias deste user
                result = client.delete_all(user_id=user_id)

                print(f"[{idx:02d}/{len(users)}] [OK] {user_id[:13]}... " f"({total_mems} mem)")
                deleted_count += 1

            except Exception as e:
                print(f"[{idx:02d}/{len(users)}] [ERRO] {user_id[:13]}...: {e}")
                failed_count += 1
                continue

        print(f"\n{'='*60}")
        print("[DONE] Delecao completa!")
        print(f"[STATS] Sucesso: {deleted_count} | Falhas: {failed_count} | Total: {len(users)}")
        print(f"{'='*60}\n")

        return deleted_count

    except Exception as e:
        print(f"[ERRO] Falha ao processar: {e}")
        import traceback

        traceback.print_exc()
        return 0


if __name__ == "__main__":
    print("[WARN] Este script deletara TODAS as memorias SEM CONFIRMACAO!")
    print("[WARN] Pressione Ctrl+C nos proximos 3 segundos para cancelar...\n")

    import time

    for i in range(3, 0, -1):
        print(f"[COUNTDOWN] {i}...")
        time.sleep(1)

    print("\n[EXEC] Iniciando delecao...\n")

    total_deleted = clear_all_mem0_memories_NOW()

    if total_deleted > 0:
        print("\n[SUCCESS] Database Mem0 completamente limpo!")
        print(f"[STATS] {total_deleted} users deletados")
        print("\n[NEXT] Execute workflow novamente:")
        print("       streamlit run app.py")
        print("       Pagina 0 - Consultor BSC")
    else:
        print("\n[INFO] Nenhuma delecao realizada")

    sys.exit(0)
