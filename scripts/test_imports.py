#!/usr/bin/env python3
"""Script para testar se os imports estão funcionando."""

import os
import sys

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("TESTE DE IMPORTS")
print("=" * 60)
print()

# Testar imports críticos
try:
    print("[1/4] Testando import src.graph.workflow...")
    from src.graph.workflow import BSCWorkflow

    print("   [OK] BSCWorkflow importado com sucesso")
except ImportError as e:
    print(f"   [ERRO] Falha ao importar BSCWorkflow: {e}")

try:
    print("[2/4] Testando import src.graph.states...")
    from src.graph.states import BSCState

    print("   [OK] BSCState importado com sucesso")
except ImportError as e:
    print(f"   [ERRO] Falha ao importar BSCState: {e}")

try:
    print("[3/4] Testando import src.memory.schemas...")
    from src.memory.schemas import CompleteDiagnostic

    print("   [OK] CompleteDiagnostic importado com sucesso")
except ImportError as e:
    print(f"   [ERRO] Falha ao importar CompleteDiagnostic: {e}")

try:
    print("[4/4] Testando import src.tools.alignment_validator...")
    from src.tools.alignment_validator import AlignmentValidatorTool

    print("   [OK] AlignmentValidatorTool importado com sucesso")
except ImportError as e:
    print(f"   [ERRO] Falha ao importar AlignmentValidatorTool: {e}")

print()
print("=" * 60)
print("Python Path:")
for path in sys.path[:3]:
    print(f"  - {path}")
print("=" * 60)
