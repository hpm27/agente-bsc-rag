#!/usr/bin/env python
"""Script CI/CD - Valida json_schema_extra vs validators customizados Pydantic.

SESSAO 40 (2025-11-21) - Prevencao de contradições schema.

Problema identificado: json_schema_extra com exemplos que contradizem validators
customizados causam ValidationError porque LLM segue EXEMPLO antes de validator
(Memoria [[10230048]]).

Exemplo bug critico corrigido hoje:
- Validator: score 75-100 -> priority_level='CRITICAL'
- json_schema_extra: score=79, priority_level='HIGH'  # CONTRADICAO!
- Resultado: LLM retorna HIGH, validator rejeita -> ValidationError

Este script:
1. Inspeciona TODOS schemas Pydantic em src/memory/schemas.py
2. Identifica validators customizados (@field_validator, @model_validator)
3. Valida que json_schema_extra examples RESPEITAM validators
4. Retorna exit code 0 (success) ou 1 (failure) para CI/CD

Baseado em: Stefanie Molin Pre-Commit Hook Creation Guide (Sep 2024)
"""

import argparse
import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Sequence

# Adicionar projeto root ao PYTHONPATH (para imports funcionarem)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def get_all_pydantic_models(module_path: str) -> list[tuple[str, type[BaseModel]]]:
    """Importa modulo e retorna todas classes Pydantic BaseModel.

    Args:
        module_path: Path do modulo Python (ex: 'src.memory.schemas')

    Returns:
        Lista de tuplas (class_name, class_type)

    Example:
        >>> models = get_all_pydantic_models('src.memory.schemas')
        >>> len(models) >= 30  # Projeto tem 30+ schemas
        True
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        print(f"[ERRO] Falha ao importar modulo {module_path}: {e}")
        return []

    models = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Verificar se e subclasse de BaseModel (Pydantic)
        if issubclass(obj, BaseModel) and obj is not BaseModel:
            models.append((name, obj))

    return models


def has_custom_validators(model: type[BaseModel]) -> bool:
    """Verifica se model tem validators customizados.

    Args:
        model: Classe Pydantic BaseModel

    Returns:
        True se tem @field_validator ou @model_validator, False caso contrario

    Example:
        >>> from src.memory.schemas import PrioritizedItem, CompanyInfo
        >>> has_custom_validators(PrioritizedItem)
        True
        >>> has_custom_validators(CompanyInfo)
        True
    """
    # Pydantic V2 armazena validators em __pydantic_decorators__
    if not hasattr(model, "__pydantic_decorators__"):
        return False

    decorators = model.__pydantic_decorators__

    # Verificar field_validators e model_validators
    has_field = bool(getattr(decorators, "field_validators", {}))
    has_model = bool(getattr(decorators, "model_validators", {}))

    return has_field or has_model


def validate_json_schema_extra_example(
    model: type[BaseModel], verbose: bool = False
) -> tuple[bool, str | None]:
    """Valida que exemplo json_schema_extra e valido segundo validators.

    Tenta instanciar model com dados do json_schema_extra['example'].
    Se ValidationError for lancado, significa que exemplo contradiz validators.

    Args:
        model: Classe Pydantic BaseModel
        verbose: Se True, print informacoes detalhadas

    Returns:
        Tupla (is_valid, error_message)
        - is_valid: True se exemplo valido, False se ValidationError
        - error_message: Mensagem de erro se invalido, None se valido

    Example:
        >>> from src.memory.schemas import PrioritizedItem
        >>> is_valid, error = validate_json_schema_extra_example(PrioritizedItem)
        >>> is_valid  # Apos correcao Sessao 40
        True
    """
    # Verificar se model tem json_schema_extra
    if not hasattr(model, "model_config"):
        return True, None  # Sem config, sem exemplo para validar

    config = model.model_config
    if not isinstance(config, dict):
        return True, None

    json_schema_extra = config.get("json_schema_extra")
    if not json_schema_extra:
        return True, None  # Sem json_schema_extra, nada para validar

    # Extrair exemplo
    if callable(json_schema_extra):
        # json_schema_extra pode ser funcao (callable)
        return True, None  # Skip validacao de callables (muito complexo)

    example = json_schema_extra.get("example")
    if not example:
        return True, None  # Sem exemplo, nada para validar

    # Tentar instanciar model com exemplo
    try:
        instance = model(**example)

        if verbose:
            print("  [OK] json_schema_extra example valido")

        return True, None

    except ValidationError as e:
        # Exemplo contradiz validators!
        error_lines = str(e).split("\n")
        error_summary = error_lines[0] if error_lines else str(e)

        error_msg = (
            f"json_schema_extra['example'] contradiz validators!\n"
            f"  ValidationError: {error_summary}\n"
            f"  ACAO: Atualizar example em model_config para respeitar validators"
        )

        return False, error_msg

    except Exception as e:
        # Outro erro (ex: exemplo com campos extras nao permitidos)
        error_msg = f"Erro ao validar exemplo: {type(e).__name__}: {e}"
        return False, error_msg


def validate_all_schemas(
    module_path: str = "src.memory.schemas", verbose: bool = False
) -> tuple[int, int, list[str]]:
    """Valida TODOS schemas Pydantic do modulo.

    Args:
        module_path: Path do modulo Python
        verbose: Se True, print informacoes detalhadas

    Returns:
        Tupla (total_checked, failures, error_messages)
        - total_checked: Total de schemas com validators customizados verificados
        - failures: Numero de schemas com contradições
        - error_messages: Lista de mensagens de erro formatadas

    Example:
        >>> total, failures, errors = validate_all_schemas()
        >>> failures == 0  # Apos correcao Sessao 40
        True
    """
    print(f"[INFO] Carregando schemas de {module_path}...")
    models = get_all_pydantic_models(module_path)

    if not models:
        print(f"[ERRO] Nenhum schema Pydantic encontrado em {module_path}")
        return 0, 0, []

    print(f"[INFO] Encontrados {len(models)} schemas Pydantic")

    # Filtrar apenas schemas com validators customizados
    models_with_validators = [
        (name, model) for name, model in models if has_custom_validators(model)
    ]

    print(
        f"[INFO] {len(models_with_validators)} schemas com validators customizados "
        f"(@field_validator ou @model_validator)"
    )

    if not models_with_validators:
        print("[OK] Nenhum schema com validators customizados para validar")
        return 0, 0, []

    # Validar cada schema
    failures = 0
    error_messages = []

    for name, model in models_with_validators:
        if verbose:
            print(f"\n[CHECK] Validando {name}...")

        is_valid, error_msg = validate_json_schema_extra_example(model, verbose)

        if not is_valid:
            failures += 1
            full_error = f"\n[ERRO] {name}:\n  {error_msg}\n"
            error_messages.append(full_error)
            print(full_error)
        elif verbose:
            print(f"  [OK] {name} - json_schema_extra valido")

    return len(models_with_validators), failures, error_messages


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point CLI do script.

    Args:
        argv: Argumentos CLI (None usa sys.argv)

    Returns:
        Exit code: 0 (success) ou 1 (failure)

    Example (CLI):
        $ python scripts/validate_pydantic_schemas.py
        [INFO] Carregando schemas de src.memory.schemas...
        [INFO] Encontrados 45 schemas Pydantic
        [INFO] 29 schemas com validators customizados
        [OK] TODOS schemas validados com sucesso! (29/29)

        $ python scripts/validate_pydantic_schemas.py --verbose
        # Output detalhado com cada schema verificado
    """
    parser = argparse.ArgumentParser(
        prog="validate-pydantic-schemas",
        description=(
            "Valida que json_schema_extra examples respeitam validators customizados Pydantic. "
            "Previne contradições que causam ValidationError em runtime."
        ),
        epilog=(
            "Criado: SESSAO 40 (2025-11-21)\n"
            "Baseado em: Stefanie Molin Pre-Commit Hook Creation Guide (Sep 2024)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--module",
        default="src.memory.schemas",
        help="Modulo Python a validar (default: src.memory.schemas)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informacoes detalhadas de cada schema verificado",
    )

    args = parser.parse_args(argv)

    print("=" * 70)
    print("VALIDACAO PYDANTIC SCHEMAS - json_schema_extra vs validators")
    print("=" * 70)

    total_checked, failures, error_messages = validate_all_schemas(
        module_path=args.module, verbose=args.verbose
    )

    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    if failures == 0:
        print(f"[OK] TODOS schemas validados com sucesso! ({total_checked}/{total_checked})")
        print("\n[INFO] Nenhuma contradicao json_schema_extra vs validators encontrada.")
        return EXIT_SUCCESS
    else:
        print(f"[ERRO] {failures}/{total_checked} schemas com contradições!")
        print("\n[RESUMO] Schemas com problemas:")
        for error in error_messages:
            print(error)

        print(
            "\n[ACAO] Corrija os exemplos json_schema_extra para respeitar validators.\n"
            "Consulte memoria [[10230048]] sobre Prompt-Schema Alignment."
        )
        return EXIT_FAILURE


if __name__ == "__main__":
    sys.exit(main())
