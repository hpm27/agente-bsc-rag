"""
Script para remover TODOS os emojis detectados pelo pre-commit.
"""

import re
import sys
from pathlib import Path

# Mapeamento de emojis Unicode para ASCII
EMOJI_REPLACEMENTS = {
    "\u2192": "->",  # SETA DIREITA
    "\u2190": "<-",  # SETA ESQUERDA
    "\u2194": "<->",  # SETA BIDIRECIONAL
    "\u2705": "[OK]",  # CHECKMARK VERDE
    "\u2713": "[OK]",  # CHECKMARK SIMPLES
    "\u2717": "[X]",  # CROSS MARK
    "\u274c": "[ERRO]",  # X VERMELHO
    "\u26a0\ufe0f": "[WARN]",  # AVISO
    "\u26a0": "[WARN]",  # AVISO (sem variation selector)
    "\u26a1": "[FAST]",  # RAIO
    "\u1f4cA": "[CHART]",  # GRAFICO
    "\u1f4cB": "[CLIPBOARD]",  # PRANCHETA
    "\u1f4c8": "[TRENDING]",  # GRAFICO SUBINDO
    "\u1f4c5": "[CALENDAR]",  # CALENDARIO
    "\u1f4dD": "[MEMO]",  # MEMO
    "\u1f3aF": "[TARGET]",  # ALVO
    "\u1f534": "[HIGH]",  # CIRCULO VERMELHO
    "\u1f7e1": "[MEDIUM]",  # CIRCULO AMARELO
    "\u1f7e2": "[LOW]",  # CIRCULO VERDE
    "\u1f527": "[TOOL]",  # FERRAMENTA
    "\u1fab6": "[FEATHER]",  # PENA
    "\u1f393": "[LEARN]",  # CHAPEU GRADUACAO
    "\u1f4e4": "[OUTPUT]",  # CAIXA SAIDA
    "\u1f4dA": "[BOOK]",  # LIVRO
    "\u1f916": "[BOT]",  # ROBO
    "\u1f464": "[USER]",  # USUARIO
    "\u1f504": "[LOOP]",  # LOOP
    "\u2753": "[?]",  # INTERROGACAO
    "\u23f1\ufe0f": "[TIMER]",  # CRONOMETRO (com variation selector)
    "\u23f1": "[TIMER]",  # CRONOMETRO
    "\ufe0f": "",  # VARIATION SELECTOR (remover)
    "\u0304": "",  # COMBINING MACRON (remover)
}


def remove_emojis_from_file(file_path: Path) -> bool:
    """Remove emojis de um arquivo."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Substituir emojis conhecidos
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)

        # Remover qualquer outro emoji Unicode (U+1F300 a U+1F9FF, U+2600 a U+26FF)
        content = re.sub(r"[\U0001F300-\U0001F9FF\U00002600-\U000026FF]", "[EMOJI]", content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            print(f"[OK] {file_path}")
            return True
        return False

    except Exception as e:
        print(f"[ERRO] {file_path}: {e}")
        return False


def main():
    """Remove emojis de todos os arquivos Python e Markdown."""
    root = Path(__file__).parent.parent

    # Buscar arquivos com emojis
    patterns = ["**/*.py", "**/*.md"]
    files_processed = 0
    files_modified = 0

    for pattern in patterns:
        for file_path in root.glob(pattern):
            # Ignorar venv e node_modules
            if "venv" in str(file_path) or "node_modules" in str(file_path):
                continue

            files_processed += 1
            if remove_emojis_from_file(file_path):
                files_modified += 1

    print("\n[SUMMARY]")
    print(f"  Arquivos processados: {files_processed}")
    print(f"  Arquivos modificados: {files_modified}")

    return 0 if files_modified == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
