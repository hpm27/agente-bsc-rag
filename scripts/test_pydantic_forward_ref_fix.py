#!/usr/bin/env python3
"""Script para testar a correção do erro Pydantic forward reference.

Testa se CompleteDiagnostic consegue ser criado sem o erro:
"CompleteDiagnostic is not fully defined; you should define DiagnosticToolsResult"

Created: 2025-11-21 (SPRINT 4 - Forward Reference Fix)
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent))

# Importar schemas (deve executar model_rebuild() automaticamente no final)
from src.memory.schemas import (
    CompleteDiagnostic,
    DiagnosticResult,
    DiagnosticToolsResult,
    Recommendation,
)


def test_forward_reference():
    """Testa se CompleteDiagnostic pode ser criado sem erros."""

    print("\n" + "=" * 60)
    print("TESTE FORWARD REFERENCE FIX - SPRINT 4")
    print("=" * 60)

    # Criar DiagnosticResult para cada perspectiva
    financial = DiagnosticResult(
        perspective="Financeira",
        current_state="Empresa com crescimento mas margens baixas",
        gaps=["Falta visibilidade custos", "Margens baixas"],
        opportunities=["Implementar ABC Costing", "Otimizar pricing"],
        priority="HIGH",
        key_insights=["Margem EBITDA 12% vs 20% mercado"],
    )

    customer = DiagnosticResult(
        perspective="Clientes",
        current_state="NPS bom mas churn alto",
        gaps=["Churn 25% SMB", "Falta programa retenção"],
        opportunities=["Customer Success", "Programa fidelidade"],
        priority="HIGH",
        key_insights=["NPS 45 mas churn alto"],
    )

    process = DiagnosticResult(
        perspective="Processos Internos",
        current_state="Processos manuais e ineficientes",
        gaps=["Falta automação", "Lead time alto"],
        opportunities=["RPA", "Lean Six Sigma"],
        priority="MEDIUM",
        key_insights=["70% processos manuais"],
    )

    learning = DiagnosticResult(
        perspective="Aprendizado e Crescimento",
        current_state="Equipe desmotivada e turnover alto",
        gaps=["Turnover 30%", "Falta treinamento"],
        opportunities=["Academia interna", "Plano carreira"],
        priority="MEDIUM",
        key_insights=["Turnover vendas 30%/ano"],
    )

    # Criar recomendações (mínimo 3 requerido)
    rec1 = Recommendation(
        title="Implementar ABC Costing",
        description="Implementar sistema de custeio ABC para visibilidade completa de custos por produto e cliente, permitindo análise detalhada de rentabilidade",
        impact="HIGH",
        effort="MEDIUM",
        priority="HIGH",
        timeframe="3-6 meses",
        next_steps=["Contratar consultoria especializada", "Mapear processos atuais"],
    )

    rec2 = Recommendation(
        title="Customer Success para SMB",
        description="Criar programa de Customer Success dedicado para clientes SMB visando reduzir churn de 25% para 15% em 12 meses",
        impact="HIGH",
        effort="MEDIUM",
        priority="HIGH",
        timeframe="6-9 meses",
        next_steps=["Definir playbook CS", "Contratar 2 CSMs"],
    )

    rec3 = Recommendation(
        title="Automação RPA",
        description="Implementar RPA para automatizar processos repetitivos e manuais, liberando 30% da capacidade da equipe para atividades estratégicas",
        impact="MEDIUM",
        effort="HIGH",
        priority="MEDIUM",
        timeframe="9-12 meses",
        next_steps=["Mapear processos candidatos", "POC com 2 processos"],
    )

    # CompleteDiagnostic usa lista direta, não RecommendationsList
    recommendations = [rec1, rec2, rec3]

    # Synergies e executive summary são campos diretos
    cross_perspective_synergies = [
        "ABC Costing (Financeira) melhora pricing (Clientes) e reduz churn SMB",
        "Customer Success (Clientes) aumenta lifetime value (Financeira) e reduz custos aquisição",
    ]

    executive_summary = (
        "Empresa Engelar apresenta crescimento sólido mas enfrenta desafios críticos de rentabilidade e eficiência. "
        "Principais gaps identificados: margens comprimidas (12% vs 20% mercado), churn alto SMB (25%), processos "
        "70% manuais e turnover comercial de 30%. Prioridades imediatas: (1) Implementar ABC Costing para "
        "visibilidade de custos, (2) Customer Success SMB para reduzir churn, (3) RPA para eficiência operacional. "
        "ROI esperado: +5pp margem EBITDA em 12 meses."
    )

    # Criar DiagnosticToolsResult (opcional)
    tools_result = DiagnosticToolsResult(
        execution_time=45.2, tools_executed=["swot_analysis", "five_whys"], tools_failed=[]
    )

    try:
        # TESTE PRINCIPAL: Criar CompleteDiagnostic com forward reference
        diagnostic = CompleteDiagnostic(
            financial=financial,
            customer=customer,
            process=process,
            learning=learning,
            recommendations=recommendations,  # Lista direta de Recommendation
            cross_perspective_synergies=cross_perspective_synergies,  # Lista de strings
            executive_summary=executive_summary,  # String direta
            next_phase="APPROVAL_PENDING",
            diagnostic_tools_results=tools_result,  # Forward reference!
        )

        print("\n[OK] CompleteDiagnostic criado com sucesso!")
        print(f"  - financial priority: {diagnostic.financial.priority}")
        print(f"  - recommendations count: {len(diagnostic.recommendations)}")
        print(f"  - next_phase: {diagnostic.next_phase}")
        print(
            f"  - tools_executed: {diagnostic.diagnostic_tools_results.tools_executed if diagnostic.diagnostic_tools_results else 'N/A'}"
        )

        # Testar acesso a campos nested
        print("\n[INFO] Testando acesso a campos nested:")
        print(
            f"  - financial.gaps[0]: {diagnostic.financial.gaps[0] if diagnostic.financial.gaps else 'N/A'}"
        )
        print(f"  - recommendations[0].title: {diagnostic.recommendations[0].title}")

        print("\n[OK] TESTE PASSOU - Forward references resolvidas!")
        return True

    except Exception as e:
        print(f"\n[ERRO] Falha ao criar CompleteDiagnostic: {e}")
        print(f"  - Tipo do erro: {type(e).__name__}")

        # Se for erro de forward reference, dar dica
        if "not fully defined" in str(e):
            print("\n[DICA] Adicione CompleteDiagnostic.model_rebuild() no final de schemas.py")

        return False


def test_direct_import():
    """Testa se a importação direta funciona sem erros."""
    print("\n[TEST] Importação direta de CompleteDiagnostic...")

    try:
        # Tentar importar e usar diretamente
        from src.memory.schemas import CompleteDiagnostic as CD

        # Verificar se tem os campos esperados
        fields = CD.model_fields.keys()
        expected = ["financial", "customer", "process", "learning", "diagnostic_tools_results"]

        missing = [f for f in expected if f not in fields]
        if missing:
            print(f"[WARN] Campos faltando: {missing}")
            return False

        print("[OK] Importação direta funcionando!")
        return True

    except Exception as e:
        print(f"[ERRO] Importação falhou: {e}")
        return False


if __name__ == "__main__":
    # Executar testes
    test1 = test_direct_import()
    test2 = test_forward_reference()

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES:")
    print("-" * 60)
    print(f"  - Importação direta: {'[OK] PASSOU' if test1 else '[ERRO] FALHOU'}")
    print(f"  - Forward reference: {'[OK] PASSOU' if test2 else '[ERRO] FALHOU'}")

    if test1 and test2:
        print("\n[OK] TODOS OS TESTES PASSARAM!")
        print("[OK] Forward references resolvidas com model_rebuild()")
    else:
        print("\n[ERRO] Alguns testes falharam. Verifique schemas.py")

    print("=" * 60 + "\n")
