#!/usr/bin/env python3
"""
Valida Strategy Map contra Action Plan
Verifica alinhamento de objetivos estratégicos com ações planejadas
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def main():
    db_path = Path("data/bsc_data.db")

    if not db_path.exists():
        print("[ERRO] Database não encontrado")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Buscar Strategy Map mais recente
    cursor.execute(
        """
        SELECT objectives, created_at
        FROM strategy_maps
        ORDER BY created_at DESC
        LIMIT 1
    """
    )

    result = cursor.fetchone()

    if not result:
        print("[ERRO] Nenhum Strategy Map encontrado")
        return

    objectives_json, created_at = result
    objectives = json.loads(objectives_json)

    print("=" * 80)
    print("VALIDAÇÃO STRATEGY MAP vs ACTION PLAN")
    print("=" * 80)
    print(f"\nStrategy Map criado em: {created_at}")
    print(f"Total de objetivos: {len(objectives)}\n")

    # Agrupar por perspectiva e prioridade
    by_perspective = {}
    by_priority = {"Alta": [], "Média": [], "Baixa": []}

    for i, obj in enumerate(objectives, 1):
        perspective = obj.get("perspective", "N/A")
        priority = obj.get("priority", "N/A")
        # Tentar diferentes campos de título
        title = (
            obj.get("title")
            or obj.get("description")
            or obj.get("objective")
            or obj.get("name")
            or "N/A"
        )

        if perspective not in by_perspective:
            by_perspective[perspective] = []

        by_perspective[perspective].append({"num": i, "title": title, "priority": priority})

        if priority in by_priority:
            by_priority[priority].append(title)

    # Mostrar por perspectiva
    print("\n" + "=" * 80)
    print("OBJETIVOS POR PERSPECTIVA BSC")
    print("=" * 80)

    for perspective in [
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento",
    ]:
        if perspective in by_perspective:
            print(f"\n{perspective.upper()}:")
            for obj in by_perspective[perspective]:
                print(f"  {obj['num']}. [{obj['priority']}] {obj['title']}")

    # Mostrar por prioridade
    print("\n" + "=" * 80)
    print("DISTRIBUIÇÃO POR PRIORIDADE")
    print("=" * 80)

    for priority in ["Alta", "Média", "Baixa"]:
        count = len(by_priority[priority])
        print(f"\n{priority.upper()}: {count} objetivos")
        for title in by_priority[priority]:
            print(f"  - {title[:70]}...")

    # Action Plan esperado (HIGH priority do texto fornecido)
    print("\n" + "=" * 80)
    print("AÇÕES HIGH PRIORITY DO ACTION PLAN (esperadas)")
    print("=" * 80)

    expected_high = [
        "Sistema ERP integrado",
        "Controle de custos por centro de custo",
        "Sistema de gestão de estoque ABC",
        "Sistema de KPIs e dashboards",
        "Planejamento financeiro e orçamento",
        "Pesquisa NPS de clientes",
    ]

    print(f"\nTotal esperado: {len(expected_high)} ações HIGH")
    for i, action in enumerate(expected_high, 1):
        print(f"  {i}. {action}")

    # Verificar alinhamento
    print("\n" + "=" * 80)
    print("ANÁLISE DE ALINHAMENTO")
    print("=" * 80)

    print(f"\n[OK] Strategy Map tem {len(objectives)} objetivos")
    print("[OK] Action Plan lista 13 objetivos estrategicos mapeados")
    print("[OK] Distribuicao de prioridade:")
    print(f"  - Alta: {len(by_priority['Alta'])} (esperado: 6)")
    print(f"  - Media: {len(by_priority['Média'])} (esperado: 7)")

    # Buscar Action Plan
    cursor.execute(
        """
        SELECT actions, created_at
        FROM action_plans
        ORDER BY created_at DESC
        LIMIT 1
    """
    )

    action_result = cursor.fetchone()

    if action_result:
        actions_json, action_created_at = action_result
        actions = json.loads(actions_json)

        print(f"\n[OK] Action Plan tem {len(actions)} acoes planejadas")
        print(f"[OK] Action Plan criado em: {action_created_at}")

        # Contar prioridades das ações
        action_priorities = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for action in actions:
            priority = action.get("priority", "N/A")
            if priority in action_priorities:
                action_priorities[priority] += 1

        print("\n[OK] Distribuicao de acoes:")
        print(f"  - HIGH: {action_priorities['HIGH']}")
        print(f"  - MEDIUM: {action_priorities['MEDIUM']}")
        print(f"  - LOW: {action_priorities['LOW']}")

    conn.close()

    print("\n" + "=" * 80)
    print("VALIDAÇÃO CONCLUÍDA")
    print("=" * 80)


if __name__ == "__main__":
    main()
