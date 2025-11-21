#!/usr/bin/env python3
"""Testa formato de resposta do Mem0 get_all()."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json

from config.settings import settings
from mem0 import MemoryClient


def test_get_all_format():
    """Verifica formato exato da resposta do get_all()."""

    print("[INFO] Testando formato de resposta do Mem0 get_all()...")

    client = MemoryClient(api_key=settings.mem0_api_key)

    # Buscar memórias de um user_id específico
    # NOTA: Usar user_id real que existe no sistema (user debde9e3...)
    test_user_id = "debde9e3-e33c-43fb-bdbb-d2dd4e4d8e41"

    try:
        response = client.get_all(
            filters={"AND": [{"user_id": test_user_id}]}, page=1, page_size=10  # Pegar até 10
        )

        print("\n[OK] Resposta recebida:")
        print(f"  Tipo: {type(response)}")

        if isinstance(response, dict):
            print(f"  Keys: {list(response.keys())}")

            # Verificar formato
            if "results" in response:
                mems = response["results"]
                print("  Formato: dict com 'results' key")
                print(f"  Num memories: {len(mems)}")
            elif "memories" in response:
                mems = response["memories"]
                print("  Formato: dict com 'memories' key")
                print(f"  Num memories: {len(mems)}")
            else:
                print("  Formato: dict sem keys conhecidas")
                mems = []
        elif isinstance(response, list):
            mems = response
            print("  Formato: lista direta")
            print(f"  Num memories: {len(mems)}")
        else:
            print(f"  Formato: desconhecido ({type(response)})")
            mems = []

        # Mostrar primeira memória de exemplo
        if mems:
            print("\n[OK] Exemplo de memória (primeira):")
            first_mem = mems[0]
            print(f"  Tipo: {type(first_mem)}")

            if isinstance(first_mem, dict):
                print(f"  Keys: {list(first_mem.keys())}")

                # Mostrar metadata se existir
                if "metadata" in first_mem:
                    metadata = first_mem["metadata"]
                    print(
                        f"  Metadata keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'N/A'}"
                    )

                # JSON pretty print (limitado a 500 chars)
                json_str = json.dumps(first_mem, indent=2)[:500]
                print(f"\n  JSON (primeiros 500 chars):\n{json_str}...")
        else:
            print("\n[WARN] Nenhuma memória encontrada")

    except Exception as e:
        print(f"\n[ERROR] Falha ao testar get_all(): {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_get_all_format()
