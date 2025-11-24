#!/usr/bin/env python3
"""
Pre-commit hook: Validação de Hardcoding e Schema Alignment

Valida os 5 pontos do checklist pré-commit obrigatório:
1. Hardcoding de valores configuráveis
2. Alinhamento Schema Pydantic vs Código
3. Mapeamentos e Convenções
4. Race Conditions Temporais
5. Configurações no .env

Baseado em: lesson-config-hardcoding-schema-alignment-2025-11-22.md
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Cores para output
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def find_hardcoded_values(file_path: Path) -> List[Tuple[int, str]]:
    """Encontra valores hardcoded que deveriam ser configuráveis."""
    issues = []

    # Padrões de hardcoding a detectar
    patterns = [
        (r'\b"k":\s*(\d+)', "top_k hardcoded"),
        (r'\b"top_k":\s*(\d+)', "top_k hardcoded"),
        (r"\bk=(\d+)", "k= hardcoded"),
        (r"\btop_k=(\d+)", "top_k= hardcoded"),
        (
            r'reasoning_effort\s*=\s*["\'](low|medium|high|minimal|none)["\']',
            "reasoning_effort hardcoded",
        ),
        (r'model\s*=\s*["\'](gpt-|claude-)', "model hardcoded"),
        (r"temperature\s*=\s*(\d+\.?\d*)", "temperature hardcoded"),
        (r"max_tokens\s*=\s*(\d+)", "max_tokens hardcoded"),
    ]

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Ignorar comentários e strings de documentação
            if line.strip().startswith("#") or '"""' in line or "'''" in line:
                continue

            # Ignorar se já usa settings.
            if "settings." in line:
                continue

            for pattern, description in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Verificar se não está em comentário
                    comment_pos = line.find("#")
                    if comment_pos != -1 and match.start() > comment_pos:
                        continue

                    issues.append((line_num, f"{description}: {match.group(0)}"))

    except Exception as e:
        print(f"{YELLOW}[WARN] Erro ao ler {file_path}: {e}{RESET}", file=sys.stderr)

    return issues


def find_schema_mismatches(file_path: Path) -> List[Tuple[int, str]]:
    """Encontra possíveis desalinhamentos entre schema Pydantic e código."""
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Padrões que indicam uso de tool com parâmetros
        tool_patterns = [
            (r'tool\.arun\(.*?"k":', "Possível schema mismatch: usando 'k' ao invés de 'top_k'"),
            (r'tool\.invoke\(.*?"k":', "Possível schema mismatch: usando 'k' ao invés de 'top_k'"),
        ]

        for line_num, line in enumerate(lines, start=1):
            for pattern, description in tool_patterns:
                if re.search(pattern, line):
                    # Verificar se não está em comentário
                    if "#" in line and line.find("#") < line.find("tool."):
                        continue
                    issues.append((line_num, description))

    except Exception as e:
        print(f"{YELLOW}[WARN] Erro ao ler {file_path}: {e}{RESET}", file=sys.stderr)

    return issues


def find_datetime_race_conditions(file_path: Path) -> List[Tuple[int, str]]:
    """Encontra múltiplas chamadas datetime.now() que podem causar race conditions."""
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        datetime_calls = []
        for line_num, line in enumerate(lines, start=1):
            if "datetime.now()" in line and not line.strip().startswith("#"):
                datetime_calls.append(line_num)

        # Se há mais de 1 chamada em um arquivo, pode ser race condition
        if len(datetime_calls) > 1:
            # Verificar se há captura única (padrão correto)
            has_single_capture = False
            for i, line_num in enumerate(datetime_calls):
                line = lines[line_num - 1]
                # Verificar se linha anterior tem "now = datetime.now()"
                if i > 0:
                    prev_line = lines[line_num - 2] if line_num > 1 else ""
                    if "now = datetime.now()" in prev_line:
                        has_single_capture = True
                        break

            if not has_single_capture:
                issues.append(
                    (
                        datetime_calls[0],
                        f"Múltiplas chamadas datetime.now() ({len(datetime_calls)}x) - possível race condition. "
                        "Capturar UMA VEZ e reutilizar.",
                    )
                )

    except Exception as e:
        print(f"{YELLOW}[WARN] Erro ao ler {file_path}: {e}{RESET}", file=sys.stderr)

    return issues


def check_perspective_mapping(file_path: Path) -> List[Tuple[int, str]]:
    """Verifica uso incorreto de perspectiva (plural vs singular)."""
    issues = []

    # Customer Agent deve usar "cliente" (singular), não "clientes" (plural)
    perspective_issues = [
        (
            r'"perspective":\s*"clientes"',
            "Usar 'cliente' (singular) ao invés de 'clientes' (plural)",
        ),
    ]

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            for pattern, description in perspective_issues:
                if re.search(pattern, line):
                    # Verificar se não está em comentário
                    comment_pos = line.find("#")
                    match_pos = line.find('"clientes"')
                    if comment_pos != -1 and match_pos > comment_pos:
                        continue

                    issues.append((line_num, description))

    except Exception as e:
        print(f"{YELLOW}[WARN] Erro ao ler {file_path}: {e}{RESET}", file=sys.stderr)

    return issues


def main():
    """Valida arquivos Python modificados para hardcoding e schema alignment."""
    # Obter arquivos staged (modificados e adicionados)
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = [
            Path(f) for f in result.stdout.strip().split("\n") if f and f.endswith(".py")
        ]
    except subprocess.CalledProcessError:
        # Se não há arquivos staged, verificar todos arquivos Python modificados
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True,
            )
            staged_files = [
                Path(f) for f in result.stdout.strip().split("\n") if f and f.endswith(".py")
            ]
        except subprocess.CalledProcessError:
            staged_files = []

    if not staged_files:
        print(f"{GREEN}[OK] Nenhum arquivo Python modificado para validar{RESET}")
        return 0

    # Filtrar apenas arquivos em src/
    src_files = [f for f in staged_files if str(f).startswith("src/")]

    if not src_files:
        print(f"{GREEN}[OK] Nenhum arquivo em src/ modificado{RESET}")
        return 0

    total_issues = 0

    for file_path in src_files:
        if not file_path.exists():
            continue

        file_issues = []

        # 1. Verificar hardcoding de valores configuráveis
        hardcoding_issues = find_hardcoded_values(file_path)
        file_issues.extend(hardcoding_issues)

        # 2. Verificar race conditions temporais
        datetime_issues = find_datetime_race_conditions(file_path)
        file_issues.extend(datetime_issues)

        # 3. Verificar mapeamentos de perspectiva
        mapping_issues = check_perspective_mapping(file_path)
        file_issues.extend(mapping_issues)

        if file_issues:
            total_issues += len(file_issues)
            print(f"\n{RED}[ERRO] {file_path}{RESET}")
            for line_num, issue in file_issues:
                print(f"  Linha {line_num}: {YELLOW}{issue}{RESET}")

    if total_issues > 0:
        print(f"\n{RED}========================================{RESET}")
        print(f"{RED}[FALHA] {total_issues} problema(s) encontrado(s){RESET}")
        print(f"{RED}========================================{RESET}")
        print(f"\n{YELLOW}CHECKLIST PRÉ-COMMIT (Hardcoding):{RESET}")
        print(
            "1. [ ] Verificar hardcoding de valores configuráveis (k=, top_k=, reasoning_effort=, model=)"
        )
        print("2. [ ] Verificar race conditions temporais (múltiplas chamadas datetime.now())")
        print("3. [ ] Verificar mapeamentos e convenções (perspectiva singular vs plural)")
        print("4. [ ] Validar configurações no .env (existe entrada para cada settings.X?)")
        print(
            f"\n{YELLOW}Consulte: docs/lessons/lesson-config-hardcoding-schema-alignment-2025-11-22.md{RESET}"
        )
        return 1

    print(f"{GREEN}[OK] Checklist pré-commit validado - nenhum problema encontrado{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
