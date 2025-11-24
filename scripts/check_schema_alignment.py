#!/usr/bin/env python3
"""
Pre-commit hook: Validação de Schema Alignment

Valida alinhamento entre schemas Pydantic e uso no código:
- Campos esperados pelo schema vs campos usados no código
- Nomes de campos corretos (ex: "top_k" não "k")
- Valores Literal corretos (ex: "cliente" não "clientes")
- Tipos corretos

Baseado em: lesson-config-hardcoding-schema-alignment-2025-11-22.md
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Cores para output
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Schemas conhecidos e seus campos esperados
KNOWN_SCHEMAS = {
    "PerspectiveSearchInput": {
        "fields": {"query": str, "perspective": str, "top_k": (int, type(None))},
        "file": "src/tools/rag_tools.py",
        "common_mistakes": {
            "k": "top_k",  # Campo incorreto -> correto
        },
    },
    "SearchInput": {
        "fields": {"query": str, "top_k": (int, type(None))},
        "file": "src/tools/rag_tools.py",
        "common_mistakes": {
            "k": "top_k",
        },
    },
    "MultiQuerySearchInput": {
        "fields": {"queries": list, "top_k": (int, type(None))},
        "file": "src/tools/rag_tools.py",
        "common_mistakes": {
            "k": "top_k",
        },
    },
}

# Valores Literal conhecidos
LITERAL_VALUES = {
    "perspective": {
        "valid": ["financeira", "cliente", "processos", "aprendizado"],
        "invalid": ["clientes", "financeiro", "processo", "aprendizado e crescimento"],
        "file": "src/rag/retriever.py",
    }
}


def find_schema_imports(file_path: Path) -> List[str]:
    """Encontra imports de schemas Pydantic no arquivo."""
    schemas_found = []

    try:
        content = file_path.read_text(encoding="utf-8")

        # Buscar imports de schemas
        patterns = [
            r"from src\.tools\.rag_tools import.*?(PerspectiveSearchInput|SearchInput|MultiQuerySearchInput)",
            r"from src\.tools import.*?(PerspectiveSearchInput|SearchInput|MultiQuerySearchInput)",
            r"PerspectiveSearchInput|SearchInput|MultiQuerySearchInput",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                schema_name = match.group(1) if match.groups() else match.group(0)
                if schema_name in KNOWN_SCHEMAS and schema_name not in schemas_found:
                    schemas_found.append(schema_name)

    except Exception as e:
        print(f"{YELLOW}[WARN] Erro ao ler {file_path}: {e}{RESET}", file=sys.stderr)

    return schemas_found


def find_tool_calls(file_path: Path) -> List[Tuple[int, str, Dict[str, str]]]:
    """Encontra chamadas a tools (tool.arun, tool.invoke) com parâmetros."""
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Buscar tool calls multi-linha
        # Padrão: tool.arun({ ... }) ou await tool.arun({ ... })
        tool_call_pattern = re.compile(r"(?:await\s+)?tool\.(arun|invoke)\s*\(\s*\{", re.MULTILINE)

        # Encontrar início de tool calls
        for match in tool_call_pattern.finditer(content):
            tool_name = f"tool.{match.group(1)}"
            start_pos = match.end() - 1  # Posição do {
            start_line = content[:start_pos].count("\n") + 1

            # Encontrar fechamento do dict (balanceamento de chaves)
            brace_count = 0
            end_pos = start_pos
            for i, char in enumerate(content[start_pos:], start=start_pos):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break

            # Extrair conteúdo do dict
            dict_content = content[start_pos + 1 : end_pos]

            # Extrair campos do dict (suporta multi-linha)
            params = {}
            # Buscar padrão: "campo": valor ou 'campo': valor
            field_pattern = r'["\'](\w+)["\']\s*:\s*([^,\n}]+)'
            for field_match in re.finditer(field_pattern, dict_content):
                field_name = field_match.group(1)
                field_value = field_match.group(2).strip().strip("\"'")
                params[field_name] = field_value

            if params:
                issues.append((start_line, tool_name, params))

    except Exception as e:
        print(f"{YELLOW}[WARN] Erro ao ler {file_path}: {e}{RESET}", file=sys.stderr)

    return issues


def validate_schema_fields(
    file_path: Path, schema_name: str, tool_calls: List[Tuple[int, str, Dict[str, str]]]
) -> List[Tuple[int, str]]:
    """Valida se campos usados em tool calls estão corretos conforme schema."""
    issues = []

    if schema_name not in KNOWN_SCHEMAS:
        return issues

    schema_info = KNOWN_SCHEMAS[schema_name]
    expected_fields = set(schema_info["fields"].keys())
    common_mistakes = schema_info.get("common_mistakes", {})

    for line_num, tool_name, params in tool_calls:
        # Verificar campos incorretos (common mistakes)
        for wrong_field, correct_field in common_mistakes.items():
            if wrong_field in params:
                issues.append(
                    (
                        line_num,
                        f"Schema {schema_name} espera '{correct_field}' não '{wrong_field}'. "
                        f"StructuredTool ignora campos não definidos no schema (silent failure).",
                    )
                )

        # Verificar valores Literal incorretos
        if "perspective" in params:
            perspective_value = params["perspective"].strip("\"'")
            if perspective_value in LITERAL_VALUES["perspective"]["invalid"]:
                valid_values = ", ".join(LITERAL_VALUES["perspective"]["valid"])
                issues.append(
                    (
                        line_num,
                        f"Perspectiva inválida: '{perspective_value}'. "
                        f"Valores válidos: {valid_values}",
                    )
                )

    return issues


def main():
    """Valida alinhamento schema-código em arquivos Python modificados."""
    import subprocess

    # Obter arquivos staged
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
        # Fallback: arquivos modificados
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

        # 1. Encontrar schemas importados
        schemas_used = find_schema_imports(file_path)

        if not schemas_used:
            continue  # Arquivo não usa schemas conhecidos

        # 2. Encontrar tool calls
        tool_calls = find_tool_calls(file_path)

        if not tool_calls:
            continue  # Arquivo não tem tool calls

        # 3. Validar cada schema usado
        file_issues = []
        for schema_name in schemas_used:
            schema_issues = validate_schema_fields(file_path, schema_name, tool_calls)
            file_issues.extend(schema_issues)

        if file_issues:
            total_issues += len(file_issues)
            print(f"\n{RED}[ERRO] {file_path}{RESET}")
            for line_num, issue in file_issues:
                print(f"  Linha {line_num}: {YELLOW}{issue}{RESET}")

    if total_issues > 0:
        print(f"\n{RED}========================================{RESET}")
        print(f"{RED}[FALHA] {total_issues} problema(s) de schema alignment encontrado(s){RESET}")
        print(f"{RED}========================================{RESET}")
        print(f"\n{YELLOW}CHECKLIST SCHEMA ALIGNMENT:{RESET}")
        print(
            "1. [ ] Verificar schema Pydantic completo (grep 'class SchemaName' src/path/file.py -A 30)"
        )
        print("2. [ ] Listar campos esperados (nomes exatos, tipos, defaults)")
        print("3. [ ] Verificar uso no código (campos usados existem no schema?)")
        print("4. [ ] Validar valores Literal (case-sensitive, valores exatos)")
        print(
            f"\n{YELLOW}Consulte: docs/lessons/lesson-config-hardcoding-schema-alignment-2025-11-22.md{RESET}"
        )
        return 1

    print(f"{GREEN}[OK] Schema alignment validado - nenhum problema encontrado{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
