"""
Script de conveniencia para executar a aplicacao Streamlit.

Uso:
    python run_streamlit.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Executa aplicacao Streamlit."""
    app_path = Path(__file__).parent / "app" / "main.py"

    if not app_path.exists():
        print(f"[ERRO] Arquivo nao encontrado: {app_path}")
        sys.exit(1)

    print("[INFO] Iniciando Streamlit...")
    print(f"[INFO] Executando: streamlit run {app_path}")
    print("[INFO] A aplicacao sera aberta no navegador automaticamente.")
    print("[INFO] Pressione Ctrl+C para encerrar.")
    print()

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n[INFO] Aplicacao encerrada pelo usuario.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Falha ao executar Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
