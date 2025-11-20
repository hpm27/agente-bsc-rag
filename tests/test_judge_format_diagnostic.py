"""
Teste: Metodo _format_diagnostic_for_judge() do ConsultingOrchestrator

Valida que CompleteDiagnostic e formatado corretamente para Judge avaliar.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import Mock


def test_format_diagnostic_for_judge():
    """Teste: _format_diagnostic_for_judge formata CompleteDiagnostic corretamente."""
    from src.graph.consulting_orchestrator import ConsultingOrchestrator

    # Mock CompleteDiagnostic com estrutura correta
    mock_diagnostic = Mock()
    mock_diagnostic.executive_summary = "Diagnostico BSC para TechCorp apresenta oportunidades..."

    # Mock DiagnosticResult para cada perspectiva
    financial = Mock()
    financial.key_insights = [
        "Insight financeiro 1",
        "Insight financeiro 2",
        "Insight financeiro 3",
    ]

    customer = Mock()
    customer.key_insights = ["Insight cliente 1", "Insight cliente 2"]

    process = Mock()
    process.key_insights = ["Insight processo 1"]

    learning = Mock()
    learning.key_insights = []  # Vazio (testar edge case)

    # Atribuir perspectivas (CORRIGIDO: usar nomes corretos do schema)
    mock_diagnostic.financial = financial
    mock_diagnostic.customer = customer
    mock_diagnostic.process = process
    mock_diagnostic.learning = learning

    # Mock recomendacoes
    rec1 = Mock()
    rec1.priority = "HIGH"
    rec1.title = "Implementar Dashboard Financeiro"
    rec1.impact = "HIGH"
    rec1.description = "Criar dashboard consolidado..."

    rec2 = Mock()
    rec2.priority = "MEDIUM"
    rec2.title = "Melhorar onboarding clientes"
    rec2.impact = "MEDIUM"
    rec2.description = "Estruturar processo..."

    rec3 = Mock()
    rec3.priority = "HIGH"
    rec3.title = "Customer Success"
    rec3.impact = "HIGH"
    rec3.description = "Implementar time CS..."

    mock_diagnostic.recommendations = [rec1, rec2, rec3]

    # Testar formatacao
    orchestrator = ConsultingOrchestrator()
    formatted = orchestrator._format_diagnostic_for_judge(mock_diagnostic)

    # Validacoes
    assert "[DIAGNOSTICO BSC]" in formatted
    assert "EXECUTIVE SUMMARY:" in formatted
    assert mock_diagnostic.executive_summary in formatted
    assert "INSIGHTS PRINCIPAIS POR PERSPECTIVA:" in formatted
    assert "[FINANCEIRA]" in formatted
    assert "Insight financeiro 1" in formatted
    assert "[CLIENTES]" in formatted
    assert "Insight cliente 1" in formatted
    assert "[PROCESSOS]" in formatted
    assert "Insight processo 1" in formatted
    assert "RECOMENDACOES PRIORITARIAS:" in formatted
    assert "1. [HIGH] Implementar Dashboard Financeiro" in formatted
    assert "2. [HIGH] Customer Success" in formatted  # Rec3 eh HIGH priority

    print("[OK] _format_diagnostic_for_judge() funciona corretamente!")
    print(f"\n[DEBUG] Formatted output ({len(formatted)} caracteres):\n")
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)


if __name__ == "__main__":
    test_format_diagnostic_for_judge()
