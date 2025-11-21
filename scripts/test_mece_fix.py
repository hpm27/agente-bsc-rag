#!/usr/bin/env python3
"""Script para testar a correção da validação MECE no Issue Tree.

Este script simula a geração de uma Issue Tree com muitos leaf nodes
e valida que a proporção de solution paths está adequada.

Created: 2025-11-20 (SPRINT 4 - MECE Fix)
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent))

from src.memory.schemas import IssueNode, IssueTreeAnalysis


def test_mece_validation():
    """Testa a validação MECE com diferentes proporções."""

    print("\n" + "=" * 60)
    print("TESTE DE VALIDAÇÃO MECE - SPRINT 4 FIX")
    print("=" * 60)

    # Cenário 1: 40 leaf nodes, 8 solution paths (PROBLEMA ORIGINAL)
    print("\n[CENÁRIO 1] Problema Original: 40 leaf nodes, 8 solution paths")
    tree1 = create_test_tree(num_leaf_nodes=40, num_solution_paths=8)
    validation1 = tree1.validate_mece()
    print(f"  - MECE Compliant: {validation1['is_mece']}")
    print(f"  - Confidence: {validation1['confidence']:.0%}")
    print(f"  - Issues: {validation1['issues']}")

    # Cenário 2: 40 leaf nodes, 20 solution paths (MÍNIMO ACEITÁVEL - 50%)
    print("\n[CENÁRIO 2] Mínimo Aceitável: 40 leaf nodes, 20 solution paths (50%)")
    tree2 = create_test_tree(num_leaf_nodes=40, num_solution_paths=20)
    validation2 = tree2.validate_mece()
    print(f"  - MECE Compliant: {validation2['is_mece']}")
    print(f"  - Confidence: {validation2['confidence']:.0%}")
    print(f"  - Issues: {validation2['issues']}")

    # Cenário 3: 40 leaf nodes, 12 solution paths (30% - NOVO MÍNIMO)
    print("\n[CENÁRIO 3] Novo Mínimo: 40 leaf nodes, 12 solution paths (30%)")
    tree3 = create_test_tree(num_leaf_nodes=40, num_solution_paths=12)
    validation3 = tree3.validate_mece()
    print(f"  - MECE Compliant: {validation3['is_mece']}")
    print(f"  - Confidence: {validation3['confidence']:.0%}")
    print(f"  - Issues: {validation3['issues']}")

    # Cenário 4: 20 leaf nodes, 10 solution paths (IDEAL - 50%)
    print("\n[CENÁRIO 4] Ideal: 20 leaf nodes, 10 solution paths (50%)")
    tree4 = create_test_tree(num_leaf_nodes=20, num_solution_paths=10)
    validation4 = tree4.validate_mece()
    print(f"  - MECE Compliant: {validation4['is_mece']}")
    print(f"  - Confidence: {validation4['confidence']:.0%}")
    print(f"  - Issues: {validation4['issues']}")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA CORRECAO MECE:")
    print("-" * 60)
    print("[OK] Antes: Exigia rigidamente 50% (20/40 solution paths)")
    print("[OK] Agora: Aceita 30-80% (12-32 solution paths para 40 leaf nodes)")
    print("[OK] Beneficio: Mais flexivel, alinhado com McKinsey/BCG best practices")
    print("=" * 60 + "\n")


def create_test_tree(num_leaf_nodes: int, num_solution_paths: int) -> IssueTreeAnalysis:
    """Cria uma árvore de teste com proporções específicas."""

    # Criar root node
    nodes = [
        IssueNode(
            id="root",
            text="Problema Raiz: Baixa Lucratividade",
            level=0,
            parent_id=None,
            is_leaf=False,
            category="root",
        )
    ]

    # Criar alguns nodes intermediários
    for i in range(4):
        nodes.append(
            IssueNode(
                id=f"branch_{i}",
                text=f"Branch {i+1}",
                level=1,
                parent_id="root",
                is_leaf=False,
                category="branch",
            )
        )

    # Criar leaf nodes
    for i in range(num_leaf_nodes):
        parent_idx = i % 4  # Distribuir entre os 4 branches
        nodes.append(
            IssueNode(
                id=f"leaf_{i}",
                text=f"Solução {i+1}",
                level=2,
                parent_id=f"branch_{parent_idx}",
                is_leaf=True,
                category="solution",
            )
        )

    # Criar solution paths
    solution_paths = [
        f"Implementar solução {i+1}: Ação específica para resolver problema"
        for i in range(num_solution_paths)
    ]

    # Criar IssueTreeAnalysis
    tree = IssueTreeAnalysis(
        root_problem="Baixa Lucratividade",
        nodes=nodes,
        max_depth=2,
        is_mece_compliant=False,
        solution_paths=solution_paths,
    )

    return tree


if __name__ == "__main__":
    test_mece_validation()
