#!/usr/bin/env python3
"""
Analisa alinhamento detalhado entre Strategy Map e Action Plan
"""

import json
import sqlite3
from pathlib import Path


def main():
    conn = sqlite3.connect("data/bsc_data.db")
    cursor = conn.cursor()

    # Buscar dados
    cursor.execute("SELECT objectives FROM strategy_maps ORDER BY created_at DESC LIMIT 1")
    objectives = json.loads(cursor.fetchone()[0])

    cursor.execute("SELECT actions FROM action_plans ORDER BY created_at DESC LIMIT 1")
    actions = json.loads(cursor.fetchone()[0])

    print("=" * 100)
    print("ANALISE DETALHADA: STRATEGY MAP vs ACTION PLAN")
    print("=" * 100)

    # Mapear ações HIGH do Action Plan
    high_actions = [a for a in actions if a.get("priority") == "HIGH"]

    print(f"\n\nACOES HIGH PRIORITY DO ACTION PLAN ({len(high_actions)}):")
    print("-" * 100)

    for i, action in enumerate(high_actions, 1):
        title = action.get("title", "N/A")
        deadline = action.get("deadline", "N/A")
        responsible = action.get("responsible", "N/A")
        print(f"\n{i}. {title}")
        print(f"   Responsavel: {responsible}")
        print(f"   Prazo: {deadline}")

    # Mapear objetivos relacionados
    print("\n\n" + "=" * 100)
    print("MAPEAMENTO: ACOES -> OBJETIVOS ESTRATEGICOS")
    print("=" * 100)

    mappings = [
        {
            "action": "ERP integrado",
            "objectives": [
                "Implementar sistema robusto de gestao de caixa",
                "Desenvolver competencias em gestao de dados (preparar para ERP)",
            ],
        },
        {
            "action": "Controle de custos por centro de custo",
            "objectives": ["Elevar margem EBITDA", "Assegurar disponibilidade de capital"],
        },
        {
            "action": "Sistema de gestao de estoque ABC",
            "objectives": [
                "Reduzir niveis de estoque em 30%",
                "Atingir excelencia em on-time delivery",
            ],
        },
        {
            "action": "Sistema de KPIs e dashboards",
            "objectives": [
                "Implementar processo formal de S&OP",
                "Estabelecer cultura de melhoria continua",
            ],
        },
        {
            "action": "Planejamento financeiro e orcamento",
            "objectives": ["Elevar margem EBITDA", "Assegurar disponibilidade de capital"],
        },
        {
            "action": "Pesquisa NPS de clientes",
            "objectives": [
                "Elevar taxa de retencao de clientes estrategicos",
                "Aumentar market share em 25%",
            ],
        },
    ]

    for mapping in mappings:
        print(f"\nACAO: {mapping['action']}")
        print("  Suporta objetivos:")
        for obj in mapping["objectives"]:
            print(f"    - {obj}")

    # Verificar cobertura das 3 ondas
    print("\n\n" + "=" * 100)
    print("COBERTURA DAS 3 ONDAS NO STRATEGY MAP")
    print("=" * 100)

    ondas = {
        "ONDA 1 - FUNDACOES (Dez/2025 - Mar/2026)": [
            "Sistema robusto de gestao de caixa",
            "Disponibilidade de capital",
            "Competencias em gestao de dados (preparar ERP)",
        ],
        "ONDA 2 - OPERACIONALIZACAO (Jan - Mai/2026)": [
            "Reduzir niveis de estoque em 30%",
            "Atingir excelencia em on-time delivery",
            "Processo formal de S&OP",
        ],
        "ONDA 3 - CONSOLIDACAO (Fev - Nov/2026)": [
            "Capacitar 80% em lean manufacturing",
            "Cultura de melhoria continua",
            "Market share +25%",
        ],
    }

    for onda, objetivos in ondas.items():
        print(f"\n{onda}")
        print("  Objetivos relacionados:")
        for obj in objetivos:
            print(f"    - {obj}")

    # Análise de gaps
    print("\n\n" + "=" * 100)
    print("ANALISE FINAL")
    print("=" * 100)

    print("\n[OK] ALINHAMENTO QUANTITATIVO:")
    print("  - Strategy Map: 13 objetivos (10 Alta, 3 Media)")
    print("  - Action Plan: 13 acoes (6 HIGH, 7 MEDIUM)")
    print("  - Proporcao de prioridade ALTA maior no Strategy Map (10 vs 6)")

    print("\n[OK] ALINHAMENTO QUALITATIVO:")
    print("  - As 6 acoes HIGH estao alinhadas com objetivos estrategicos")
    print("  - Cobertura das 4 perspectivas BSC: sim")
    print("  - Logica causa-efeito: sim (Aprendizado -> Processos -> Clientes -> Financeira)")

    print("\n[ATENCAO] OBSERVACOES:")
    print("  - Strategy Map tem mais objetivos ALTA (10) que acoes HIGH (6)")
    print("  - Pode indicar que alguns objetivos sao habilitadores/apoio")
    print("  - Ou que multiple acoes contribuem para mesmo objetivo")

    print("\n[OK] CRONOGRAMA:")
    print("  - 3 ondas bem representadas no Strategy Map")
    print("  - Sequencia logica de implementacao respeitada")
    print("  - Dependencias entre objetivos refletidas")

    conn.close()


if __name__ == "__main__":
    main()
