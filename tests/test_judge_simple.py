"""
Teste simples e direto do Judge Context-Aware (sem dependências complexas).
"""

import os
import sys

# Adicionar diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_judge_context_aware_basic():
    """Teste básico: importar e instanciar Judge."""
    # Import direto para evitar dependências circulares/quebradas
    import importlib.util
    import os

    # Carregar judge_agent.py diretamente
    spec = importlib.util.spec_from_file_location(
        "judge_agent",
        os.path.join(os.path.dirname(__file__), "..", "src", "agents", "judge_agent.py"),
    )
    judge_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(judge_module)

    JudgeAgent = judge_module.JudgeAgent
    JudgmentResult = judge_module.JudgmentResult

    judge = JudgeAgent()

    # Teste 1: Context 'DIAGNOSTIC' (fontes não esperadas)
    judgment_diagnostic = judge.evaluate(
        original_query="Diagnóstico BSC",
        agent_response="Análise diagnóstica sem fontes...",
        retrieved_documents="[Perfil cliente...]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC",
    )

    assert isinstance(judgment_diagnostic, JudgmentResult)
    assert judgment_diagnostic.verdict in ["approved", "needs_improvement", "rejected"]
    print(
        f"[OK] DIAGNOSTIC: score={judgment_diagnostic.quality_score:.2f}, verdict={judgment_diagnostic.verdict}"
    )

    # Teste 2: Context 'RAG' (fontes esperadas)
    judgment_rag = judge.evaluate(
        original_query="O que é BSC?",
        agent_response="BSC é um sistema...",
        retrieved_documents="[Docs...]",
        agent_name="RAG Agent",
        evaluation_context="RAG",
    )

    assert isinstance(judgment_rag, JudgmentResult)
    assert judgment_rag.verdict in ["approved", "needs_improvement", "rejected"]
    print(f"[OK] RAG: score={judgment_rag.quality_score:.2f}, verdict={judgment_rag.verdict}")

    # Teste 3: Default context (deve ser 'RAG')
    judgment_default = judge.evaluate(
        original_query="Query",
        agent_response="Resposta...",
        retrieved_documents="[Docs...]",
        agent_name="Agent",
    )

    assert isinstance(judgment_default, JudgmentResult)
    print(
        f"[OK] DEFAULT: score={judgment_default.quality_score:.2f}, verdict={judgment_default.verdict}"
    )

    print("\n[SUCCESS] Todos os testes básicos passaram!")


if __name__ == "__main__":
    test_judge_context_aware_basic()
