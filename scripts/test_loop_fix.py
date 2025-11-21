#!/usr/bin/env python3
"""
Script para testar se o loop infinito foi resolvido no workflow BSC.

Testa os seguintes cenários:
1. Score < 80 na primeira tentativa -> deve ir para approval
2. Score < 80 na segunda tentativa -> deve ir para implementation (evitar loop)
3. Score >= 80 em qualquer tentativa -> deve ir direto para implementation
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.states import BSCState
from src.graph.workflow import BSCWorkflow
from src.memory.schemas import AlignmentReport


def test_loop_prevention():
    """Testa prevenção de loop infinito no workflow BSC."""

    print("[TEST] Testando prevenção de loop infinito no workflow BSC...")
    print("-" * 60)

    # Criar workflow
    workflow = BSCWorkflow()

    # ========== TESTE 1: Primeira tentativa com score < 80 ==========
    print("\n[1] Primeira tentativa com score < 80:")

    # Criar estado com score baixo
    alignment_report = AlignmentReport(
        score=75.0,
        is_balanced=True,
        missing_perspectives=[],
        gaps=[],
        warnings=["warning1", "warning2"],
        recommendations=[],
        validation_checks={},
    )

    state = BSCState(
        user_id="test-user",
        query="teste",
        alignment_report=alignment_report,
        metadata={"design_solution_retry_count": 0},  # Primeira tentativa
    )

    # Testar roteamento
    result = workflow.route_by_alignment_score(state)
    print(f"   Score: 75.0, Retry: 0 -> Resultado: {result}")
    assert result == "approval", f"Esperado 'approval', obtido '{result}'"
    print("   [OK] PASSOU - Vai para approval (permitir aprovação manual)")

    # ========== TESTE 2: Segunda tentativa com score < 80 ==========
    print("\n[2] Segunda tentativa com score < 80:")

    # Atualizar retry count para simular segunda tentativa
    state.metadata["design_solution_retry_count"] = 1

    # Testar roteamento
    result = workflow.route_by_alignment_score(state)
    print(f"   Score: 75.0, Retry: 1 -> Resultado: {result}")
    assert result == "implementation", f"Esperado 'implementation', obtido '{result}'"
    print("   [OK] PASSOU - Força implementation (evita loop infinito)")

    # ========== TESTE 3: Terceira tentativa (edge case) ==========
    print("\n[3] Terceira tentativa (edge case):")

    # Atualizar retry count para simular terceira tentativa
    state.metadata["design_solution_retry_count"] = 2

    # Testar roteamento
    result = workflow.route_by_alignment_score(state)
    print(f"   Score: 75.0, Retry: 2 -> Resultado: {result}")
    assert result == "implementation", f"Esperado 'implementation', obtido '{result}'"
    print("   [OK] PASSOU - Continua forçando implementation")

    # ========== TESTE 4: Score >= 80 (qualquer tentativa) ==========
    print("\n[4] Score >= 80 (qualquer tentativa):")

    # Criar estado com score alto
    alignment_report_high = AlignmentReport(
        score=85.0,
        is_balanced=True,
        missing_perspectives=[],
        gaps=[],
        warnings=[],
        recommendations=[],
        validation_checks={},
    )
    state.alignment_report = alignment_report_high
    state.metadata["design_solution_retry_count"] = 0

    # Testar roteamento
    result = workflow.route_by_alignment_score(state)
    print(f"   Score: 85.0, Retry: 0 -> Resultado: {result}")
    assert result == "implementation", f"Esperado 'implementation', obtido '{result}'"
    print("   [OK] PASSOU - Vai direto para implementation")

    # ========== TESTE 5: Sem alignment_report (fallback) ==========
    print("\n[5] Sem alignment_report (fallback):")

    # Criar estado sem alignment_report
    state_no_report = BSCState(
        user_id="test-user", query="teste", alignment_report=None, metadata={}
    )

    # Testar roteamento
    result = workflow.route_by_alignment_score(state_no_report)
    print(f"   Sem report -> Resultado: {result}")
    assert result == "discovery", f"Esperado 'discovery', obtido '{result}'"
    print("   [OK] PASSOU - Fallback para discovery")

    print("\n" + "=" * 60)
    print("[SUCCESS] TODOS OS TESTES PASSARAM!")
    print("Loop infinito RESOLVIDO com sucesso.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_loop_prevention()
    except Exception as e:
        print(f"\n[ERROR] ERRO NO TESTE: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
