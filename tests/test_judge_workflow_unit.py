"""
Teste Unitario: Metodos Judge no ConsultingOrchestrator

Testa metodos _format_diagnostic_for_judge() isoladamente.
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_diagnostic():
    """Fixture: CompleteDiagnostic mockado."""
    # Criar mock simples sem importar classes reais
    diagnostic = Mock()
    diagnostic.executive_summary = "Diagnostico BSC para TechCorp apresenta oportunidades..."
    
    # Mock perspectivas
    financial = Mock()
    financial.insights = ["Insight financeiro 1", "Insight financeiro 2", "Insight financeiro 3"]
    
    customer = Mock()
    customer.insights = ["Insight cliente 1", "Insight cliente 2"]
    
    process = Mock()
    process.insights = ["Insight processo 1"]
    
    learning = Mock()
    learning.insights = ["Insight aprendizado 1", "Insight aprendizado 2"]
    
    diagnostic.financial_perspective = financial
    diagnostic.customer_perspective = customer
    diagnostic.process_perspective = process
    diagnostic.learning_perspective = learning
    
    # Mock recomendacoes
    rec1 = Mock()
    rec1.priority = "HIGH"
    rec1.title = "Implementar BSC completo"
    rec1.impact = "HIGH"
    rec1.description = "Implementar framework BSC nas 4 perspectivas"
    
    rec2 = Mock()
    rec2.priority = "HIGH"
    rec2.title = "Revisar KPIs financeiros"
    rec2.impact = "MEDIUM"
    rec2.description = "Alinhar KPIs com objetivos estrategicos"
    
    rec3 = Mock()
    rec3.priority = "MEDIUM"
    rec3.title = "Capacitar equipe"
    rec3.impact = "MEDIUM"
    rec3.description = "Treinamento em BSC"
    
    diagnostic.recommendations = [rec1, rec2, rec3]
    
    return diagnostic


def test_format_diagnostic_for_judge(mock_diagnostic):
    """Teste: _format_diagnostic_for_judge() formata corretamente."""
    # Import direto para evitar circular imports
    import importlib.util
    import os
    
    spec = importlib.util.spec_from_file_location(
        "consulting_orchestrator",
        os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'src', 
            'graph', 
            'consulting_orchestrator.py'
        )
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    ConsultingOrchestrator = module.ConsultingOrchestrator
    
    # Criar orchestrator
    orchestrator = ConsultingOrchestrator()
    
    # Chamar metodo
    formatted = orchestrator._format_diagnostic_for_judge(mock_diagnostic)
    
    # VALIDACOES:
    
    # 1. Output deve ser string
    assert isinstance(formatted, str)
    
    # 2. Deve conter executive summary
    assert "EXECUTIVE SUMMARY:" in formatted
    assert "Diagnostico BSC para TechCorp" in formatted
    
    # 3. Deve conter secao de insights
    assert "INSIGHTS PRINCIPAIS POR PERSPECTIVA:" in formatted
    
    # 4. Deve conter perspectivas
    assert "[FINANCEIRA]" in formatted
    assert "[CLIENTES]" in formatted
    assert "[PROCESSOS]" in formatted
    assert "[APRENDIZADO]" in formatted
    
    # 5. Deve conter insights (top 3 por perspectiva)
    assert "Insight financeiro 1" in formatted
    assert "Insight cliente 1" in formatted
    
    # 6. Deve conter recomendacoes HIGH priority
    assert "RECOMENDACOES PRIORITARIAS:" in formatted
    assert "Implementar BSC completo" in formatted
    assert "[HIGH]" in formatted
    
    # 7. Deve ter formato estruturado
    assert formatted.startswith("[DIAGNOSTICO BSC]")
    
    print("[OK] Teste unitario: _format_diagnostic_for_judge() formatou corretamente!")
    print(f"\nFormatted Output (primeiras 500 chars):\n{formatted[:500]}...")


def test_format_diagnostic_empty_recommendations():
    """Teste: _format_diagnostic_for_judge() lida com 0 recomendacoes."""
    import importlib.util
    import os
    
    spec = importlib.util.spec_from_file_location(
        "consulting_orchestrator",
        os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'src', 
            'graph', 
            'consulting_orchestrator.py'
        )
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    ConsultingOrchestrator = module.ConsultingOrchestrator
    
    # Mock diagnostic SEM recomendacoes
    diagnostic = Mock()
    diagnostic.executive_summary = "Executive summary"
    diagnostic.financial_perspective = Mock(insights=["Insight 1"])
    diagnostic.customer_perspective = Mock(insights=[])
    diagnostic.process_perspective = Mock(insights=[])
    diagnostic.learning_perspective = Mock(insights=[])
    diagnostic.recommendations = []  # VAZIO
    
    orchestrator = ConsultingOrchestrator()
    formatted = orchestrator._format_diagnostic_for_judge(diagnostic)
    
    # VALIDACOES:
    
    # 1. Deve funcionar sem crash
    assert isinstance(formatted, str)
    
    # 2. Nao deve ter secao de recomendacoes
    assert "RECOMENDACOES PRIORITARIAS:" not in formatted
    
    print("[OK] Teste: Lidou corretamente com 0 recomendacoes!")


if __name__ == "__main__":
    # Executar testes
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))

