#!/usr/bin/env python3
"""Script para testar a correção da validação de success_criteria no StrategyMap.

Este script valida que KPIs concisos típicos do BSC são aceitos após a correção.

Created: 2025-11-21 (SPRINT 4 - KPI Validation Fix)
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent))

from pydantic import ValidationError

from src.memory.schemas import StrategicObjective, StrategyMap, StrategyMapPerspective


def test_kpi_validation():
    """Testa validação de success_criteria com diferentes formatos."""

    print("\n" + "=" * 60)
    print("TESTE DE VALIDAÇÃO KPI - SPRINT 4 FIX")
    print("=" * 60)

    # Cenário 1: KPIs concisos típicos do BSC (PROBLEMA ORIGINAL)
    print("\n[CENÁRIO 1] KPIs Concisos Típicos (11-15 caracteres)")
    try:
        obj1 = StrategicObjective(
            name="Aumentar Rentabilidade",
            description="Melhorar margens e retorno sobre capital investido",
            perspective="Financeira",
            success_criteria=[
                "ROCE >= 15%",  # 11 caracteres
                "ROI > 20%",  # 9 caracteres
                "Margem EBITDA > 25%",  # 19 caracteres
            ],
            timeframe="12 meses",
            priority="Alta",
        )
        print("  [OK] PASSOU! KPIs concisos aceitos:")
        for kpi in obj1.success_criteria:
            print(f"     - '{kpi}' ({len(kpi)} chars)")
    except ValidationError as e:
        print(f"  [ERRO] FALHOU: {e}")

    # Cenário 2: KPIs muito curtos (< 5 caracteres) - DEVE FALHAR
    print("\n[CENÁRIO 2] KPIs Muito Curtos (< 5 chars) - Deve Falhar")
    try:
        obj2 = StrategicObjective(
            name="Teste",
            description="Teste de KPIs muito curtos",
            perspective="Financeira",
            success_criteria=[
                "ROI",  # 3 caracteres - muito curto!
                "NPS",  # 3 caracteres - muito curto!
            ],
            timeframe="12 meses",
            priority="Alta",
        )
        print("  [ERRO] NAO DEVERIA PASSAR! KPIs muito curtos aceitos incorretamente")
    except ValidationError as e:
        print("  [OK] CORRETAMENTE REJEITADO: KPIs < 5 chars bloqueados")
        print(f"     Erro: {str(e).split('For further')[0].strip()}")

    # Cenário 3: Mix de KPIs concisos e descritivos
    print("\n[CENÁRIO 3] Mix de Formatos (Concisos e Descritivos)")
    try:
        obj3 = StrategicObjective(
            name="Melhorar Satisfação Cliente",
            description="Aumentar satisfação e retenção de clientes",
            perspective="Clientes",
            success_criteria=[
                "NPS >= 50",  # 9 chars - conciso
                "Taxa de retenção superior a 85% ao ano",  # 39 chars - descritivo
                "OTIF >= 90%",  # 11 chars - conciso
            ],
            timeframe="12 meses",
            priority="Alta",
        )
        print("  [OK] PASSOU! Mix de formatos aceito:")
        for kpi in obj3.success_criteria:
            tipo = "conciso" if len(kpi) < 20 else "descritivo"
            print(f"     - '{kpi}' ({len(kpi)} chars, {tipo})")
    except ValidationError as e:
        print(f"  [ERRO] FALHOU: {e}")

    # Cenário 4: Strategy Map completo com KPIs concisos
    print("\n[CENÁRIO 4] Strategy Map Completo com KPIs Concisos")
    try:
        financial = StrategyMapPerspective(
            name="Financeira",
            objectives=[
                StrategicObjective(
                    name="Aumentar Rentabilidade",
                    description="Melhorar margens e retorno",
                    perspective="Financeira",
                    success_criteria=["ROCE >= 15%", "Margem EBITDA > 25%"],
                    timeframe="12 meses",
                    priority="Alta",
                )
            ],
        )

        customer = StrategyMapPerspective(
            name="Clientes",
            objectives=[
                StrategicObjective(
                    name="Satisfação Cliente",
                    description="Aumentar satisfação",
                    perspective="Clientes",
                    success_criteria=["NPS >= 50", "OTIF >= 90%"],
                    timeframe="12 meses",
                    priority="Alta",
                )
            ],
        )

        process = StrategyMapPerspective(
            name="Processos Internos",
            objectives=[
                StrategicObjective(
                    name="Otimizar Produção",
                    description="Melhorar eficiência",
                    perspective="Processos Internos",
                    success_criteria=["OEE >= 85%", "First Pass Yield >= 95%"],
                    timeframe="12 meses",
                    priority="Media",
                )
            ],
        )

        learning = StrategyMapPerspective(
            name="Aprendizado e Crescimento",
            objectives=[
                StrategicObjective(
                    name="Capacitar Equipe",
                    description="Desenvolver competências",
                    perspective="Aprendizado e Crescimento",
                    success_criteria=["Horas treinamento >= 40h/ano", "Certificações >= 80%"],
                    timeframe="12 meses",
                    priority="Media",
                )
            ],
        )

        strategy_map = StrategyMap(
            financial=financial, customer=customer, process=process, learning=learning
        )

        print("  [OK] STRATEGY MAP COMPLETO VALIDADO!")
        print("     - 4 perspectivas com KPIs concisos")
        print(f"     - Total de {len(strategy_map.get_all_objectives())} objetivos")

    except ValidationError as e:
        print(f"  [ERRO] FALHOU: {e}")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA CORREÇÃO KPI:")
    print("-" * 60)
    print("[OK] ANTES: Exigia rigidamente 20+ caracteres")
    print("[OK] AGORA: Aceita KPIs concisos (5+ caracteres)")
    print("[OK] Formatos válidos:")
    print("     - Concisos: 'ROCE >= 15%', 'NPS > 50', 'OTIF >= 90%'")
    print("     - Descritivos: 'Aumentar ROI para 15% ou mais'")
    print("[OK] Benefício: KPIs típicos do BSC agora são aceitos!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_kpi_validation()
