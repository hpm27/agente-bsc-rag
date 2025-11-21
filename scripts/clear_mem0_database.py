"""Script para limpar TODAS as memorias do Mem0 Platform.

SPRINT 4 - Utility para resetar database Mem0 e comecar testes do zero.

USO:
    python scripts/clear_mem0_database.py

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


def clear_all_mem0_memories():
    """Deleta TODAS as memorias de TODOS os users no Mem0 Platform.

    CUIDADO: Esta operacao e IRREVERSIVEL!

    Steps:
    1. Listar todos users via client.users()
    2. Para cada user, executar client.delete_all(user_id=...)
    3. Confirmar delecao

    Returns:
        Total de users deletados
    """
    print("\n" + "=" * 60)
    print("[WARN] DELETAR TODAS AS MEMORIAS DO MEM0")
    print("=" * 60 + "\n")

    # Inicializar client
    try:
        client = MemoryClient(api_key=settings.mem0_api_key)
        print("[OK] Conectado ao Mem0 Platform")
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

        print(f"\n[INFO] Total de users encontrados: {total_count}")
        print(f"[INFO] Users na pagina atual: {len(users)}\n")

        if not users:
            print("[INFO] Nenhum user para deletar. Database ja esta limpo!")
            return 0

        # Confirmar com usuario
        print("[WARN] Esta operacao deletara TODAS as memorias de TODOS os users!")
        print("[WARN] Operacao IRREVERSIVEL!")
        confirmacao = input("\nDigite 'SIM' (maiusculo) para confirmar: ")

        if confirmacao != "SIM":
            print("\n[CANCEL] Operacao cancelada pelo usuario")
            return 0

        # Deletar cada user
        print("\n[START] Iniciando delecao...\n")
        deleted_count = 0

        for idx, user in enumerate(users, 1):
            user_id = user.get("name") if isinstance(user, dict) else getattr(user, "name", None)
            total_mems = user.get("total_memories", 0) if isinstance(user, dict) else 0

            if not user_id:
                continue

            try:
                # Deletar todas memorias deste user
                client.delete_all(user_id=user_id)

                print(
                    f"[{idx}/{len(users)}] [OK] User deletado: {user_id[:8]}... "
                    f"({total_mems} memorias removidas)"
                )
                deleted_count += 1

            except Exception as e:
                print(f"[{idx}/{len(users)}] [ERRO] Falha ao deletar {user_id[:8]}...: {e}")
                continue

        print(f"\n{'='*60}")
        print("[DONE] Delecao completa!")
        print(f"[STATS] Users deletados: {deleted_count}/{len(users)}")
        print(f"{'='*60}\n")

        return deleted_count

    except Exception as e:
        print(f"[ERRO] Falha ao listar users: {e}")
        return 0


if __name__ == "__main__":
    total_deleted = clear_all_mem0_memories()

    if total_deleted > 0:
        print("\n[SUCCESS] Database Mem0 limpo com sucesso!")
        print("[NEXT] Execute workflow novamente para testar sem duplicatas")
        print("[CMD] streamlit run app.py")
    else:
        print("\n[INFO] Nenhuma delecao realizada")

    sys.exit(0)
