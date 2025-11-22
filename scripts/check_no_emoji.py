#!/usr/bin/env python3
"""
Pre-commit hook para detectar emojis e caracteres Unicode em arquivos Python.

Este script previne que emojis sejam commitados em codigo Python,
evitando problemas de encoding no Windows (cp1252) e riscos de seguranca.

Uso:
    python scripts/check_no_emoji.py arquivo1.py arquivo2.py ...

Exit codes:
    0: Sem emojis encontrados
    1: Emojis encontrados (bloqueia commit)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


# Regex para detectar emojis e caracteres Unicode problematicos
# Ranges Unicode comuns de emojis e simbolos
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f300-\U0001f9ff"  # Simbolos e pictogramas (emojis principais)
    "\U0001f600-\U0001f64f"  # Emoticons
    "\U0001f680-\U0001f6ff"  # Transporte e simbolos de mapa
    "\U0001f1e0-\U0001f1ff"  # Bandeiras (iOS)
    "\U00002600-\U000026ff"  # Simbolos diversos
    "\U00002700-\U000027bf"  # Dingbats
    "\U0000fe00-\U0000fe0f"  # Seletores de variacao
    "\U00002b50-\U00002bff"  # Estrelas e simbolos
    "\U0001f900-\U0001f9ff"  # Simbolos suplementares
    "\U0001fa00-\U0001fa6f"  # Simbolos estendidos-A
    "\U0001fa70-\U0001faff"  # Simbolos estendidos-B
    "\U00002190-\U000021ff"  # Setas (exceto basicas)
    "\U000025a0-\U000025ff"  # Formas geometricas (exceto basicas)
    "]+",
    flags=re.UNICODE,
)


def find_emojis_in_file(filepath: Path) -> List[Tuple[int, int, str, str]]:
    """
    Encontra todos os emojis em um arquivo Python.

    Args:
        filepath: Caminho para o arquivo Python

    Returns:
        Lista de tuplas (linha, coluna, emoji, linha_completa)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, FileNotFoundError) as e:
        print(f"[ERRO] Nao foi possivel ler {filepath}: {e}")
        return []

    emojis_found = []

    for line_num, line in enumerate(lines, start=1):
        for match in EMOJI_PATTERN.finditer(line):
            emoji = match.group()
            col = match.start() + 1
            emojis_found.append((line_num, col, emoji, line.rstrip()))

    return emojis_found


def check_files(filepaths: List[str]) -> int:
    """
    Verifica multiplos arquivos Python em busca de emojis.

    Args:
        filepaths: Lista de caminhos de arquivos

    Returns:
        0 se nenhum emoji encontrado, 1 caso contrario
    """
    total_emojis = 0
    files_with_emojis = []

    for filepath_str in filepaths:
        filepath = Path(filepath_str)

        # Ignorar arquivos que nao sao Python
        if filepath.suffix != ".py":
            continue

        # Ignorar diretorios venv, __pycache__, etc
        if any(part in filepath.parts for part in ["venv", "__pycache__", ".git", "node_modules"]):
            continue

        emojis = find_emojis_in_file(filepath)

        if emojis:
            total_emojis += len(emojis)
            files_with_emojis.append((filepath, emojis))

    # Relatorio de resultados
    if total_emojis == 0:
        print("[OK] Nenhum emoji encontrado nos arquivos verificados.")
        return 0

    print("\n" + "=" * 80)
    print(f"[ERRO] {total_emojis} emoji(s) encontrado(s) em {len(files_with_emojis)} arquivo(s)!")
    print("=" * 80 + "\n")

    for filepath, emojis in files_with_emojis:
        print(f"\n{filepath}:")
        for line_num, col, emoji, line_content in emojis:
            # Representacao Unicode do emoji para debugging
            unicode_repr = " ".join(f"U+{ord(c):04X}" for c in emoji)
            print(f"  Linha {line_num}, Coluna {col}: {unicode_repr}")
            # Remover emojis da linha antes de imprimir (para evitar UnicodeEncodeError)
            clean_line = EMOJI_PATTERN.sub("[EMOJI]", line_content)
            print(f"    > {clean_line}")
            print()

    print("=" * 80)
    print("[ERRO] Commit bloqueado!")
    print("=" * 80)
    print("\nPor que este erro ocorreu?")
    print("- Emojis causam UnicodeEncodeError no Windows (cp1252)")
    print("- Emojis sao vetores de ataque em LLMs (jailbreaks, exploits)")
    print("- Problemas de portabilidade cross-platform e acessibilidade")
    print("\nSolucao:")
    print("- Substituir emojis por marcadores ASCII: [OK], [ERRO], [WARN], [INFO]")
    print("- Ver LESSONS_LEARNED.md para mais detalhes")
    print("- Consultar memoria [[9592459]] sobre best practices\n")

    return 1


def main() -> int:
    """Ponto de entrada principal."""
    if len(sys.argv) < 2:
        print("Uso: python check_no_emoji.py <arquivo1.py> <arquivo2.py> ...")
        return 0

    filepaths = sys.argv[1:]
    return check_files(filepaths)


if __name__ == "__main__":
    sys.exit(main())
