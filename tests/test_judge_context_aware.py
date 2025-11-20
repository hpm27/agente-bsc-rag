"""
Testes Unitários: Judge Agent Context-Aware

Valida que Judge avalia respostas de forma diferente dependendo do contexto.
"""

import pytest

from src.agents.judge_agent import JudgeAgent, JudgmentResult


@pytest.fixture
def judge():
    """Fixture: Judge Agent."""
    return JudgeAgent()


@pytest.fixture
def diagnostic_response():
    """Fixture: Resposta de diagnóstico (sem fontes)."""
    return """
    EXECUTIVE SUMMARY:
    Empresa TechCorp (setor tecnologia, 500 funcionários) apresenta sólido desempenho
    financeiro (EBITDA 35%) mas enfrenta desafios em retenção de clientes (churn 15%).

    RECOMENDAÇÕES:
    1. [HIGH] Implementar Customer Success estruturado
    2. [MEDIUM] Melhorar onboarding de clientes
    """


@pytest.fixture
def rag_response_with_sources():
    """Fixture: Resposta RAG COM fontes."""
    return """
    O Balanced Scorecard é um sistema de gestão estratégica criado por Kaplan & Norton
    que organiza objetivos em 4 perspectivas (Fonte: Kaplan & Norton, 1996, p. 8-12).
    """


@pytest.fixture
def rag_response_without_sources():
    """Fixture: Resposta RAG SEM fontes."""
    return """
    O Balanced Scorecard é um sistema de gestão que organiza objetivos em 4 perspectivas.
    """


# ============ TESTES CONTEXTO DIAGNOSTIC ============


def test_diagnostic_context_accepts_no_sources(judge, diagnostic_response):
    """
    [DIAGNOSTIC] Judge deve ACEITAR diagnóstico sem fontes.

    Validação: verdict não deve ser 'rejected' por falta de fontes.
    """
    judgment = judge.evaluate(
        original_query="Diagnóstico BSC para TechCorp",
        agent_response=diagnostic_response,
        retrieved_documents="[Perfil cliente: TechCorp...]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC",
    )

    # Diagnóstico de qualidade razoável não deve ser rejeitado por falta de fontes
    assert (
        judgment.verdict != "rejected"
    ), "Diagnóstico não deve ser rejeitado apenas por falta de fontes no contexto DIAGNOSTIC"

    # Score deve ser baseado em qualidade da análise, não fontes
    assert judgment.quality_score >= 0.5, "Diagnóstico coerente deve ter score razoável (>= 0.5)"


def test_diagnostic_context_focuses_on_analysis_quality(judge, diagnostic_response):
    """
    [DIAGNOSTIC] Judge deve focar em QUALIDADE DA ANÁLISE, não fontes.

    Validação: issues/suggestions devem ser sobre análise, não citações.
    """
    judgment = judge.evaluate(
        original_query="Diagnóstico BSC",
        agent_response=diagnostic_response,
        retrieved_documents="[Perfil cliente...]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC",
    )

    # Issues não devem mencionar "não cita fontes" ou similar
    issues_text = " ".join(judgment.issues).lower()
    assert (
        "fontes" not in issues_text
    ), "Issues em contexto DIAGNOSTIC não devem mencionar falta de fontes"
    assert (
        "citação" not in issues_text
    ), "Issues em contexto DIAGNOSTIC não devem mencionar falta de citação"


# ============ TESTES CONTEXTO RAG ============


def test_rag_context_requires_sources(judge, rag_response_without_sources):
    """
    [RAG] Judge deve EXIGIR fontes em respostas RAG.

    Validação: resposta sem fontes deve ter score mais baixo / verdict pior.
    """
    judgment = judge.evaluate(
        original_query="O que é BSC?",
        agent_response=rag_response_without_sources,
        retrieved_documents="[Kaplan & Norton, 1996...]",
        agent_name="RAG Agent",
        evaluation_context="RAG",
    )

    # Deve identificar falta de fontes
    assert judgment.has_sources is False, "Judge deve detectar que resposta não tem fontes"

    # Se resposta é mediana (< 0.85), deve ser penalizada
    if judgment.quality_score < 0.85:
        assert judgment.verdict in [
            "needs_improvement",
            "rejected",
        ], "Resposta RAG sem fontes e score < 0.85 deve ser penalizada"


def test_rag_context_approves_sources(judge, rag_response_with_sources):
    """
    [RAG] Judge deve APROVAR respostas RAG com fontes adequadas.

    Validação: resposta com fontes deve ter has_sources=True e score alto.
    """
    judgment = judge.evaluate(
        original_query="O que é BSC?",
        agent_response=rag_response_with_sources,
        retrieved_documents="[Kaplan & Norton, 1996...]",
        agent_name="RAG Agent",
        evaluation_context="RAG",
    )

    # Deve identificar presença de fontes
    assert (
        judgment.has_sources is True
    ), "Judge deve detectar que resposta cita fontes apropriadamente"

    # Resposta com fontes deve ter score razoável
    assert judgment.quality_score >= 0.7, "Resposta RAG com fontes deve ter score >= 0.7"


# ============ TESTES COMPARAÇÃO CONTEXTOS ============


def test_same_response_different_contexts(judge, diagnostic_response):
    """
    [COMPARAÇÃO] Mesmo diagnóstico deve ser avaliado diferente em contextos diferentes.

    Validação: context='DIAGNOSTIC' deve ser mais tolerante que context='RAG'.
    """
    # Avaliar como DIAGNOSTIC (tolerante)
    judgment_diagnostic = judge.evaluate(
        original_query="Diagnóstico BSC",
        agent_response=diagnostic_response,
        retrieved_documents="[Perfil...]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC",
    )

    # Avaliar como RAG (rigoroso)
    judgment_rag = judge.evaluate(
        original_query="Diagnóstico BSC",
        agent_response=diagnostic_response,
        retrieved_documents="[Perfil...]",
        agent_name="Diagnostic Agent",
        evaluation_context="RAG",
    )

    # DIAGNOSTIC deve ter score >= RAG (ou no mínimo não ser pior)
    # Pois não é penalizado por falta de fontes
    assert (
        judgment_diagnostic.quality_score >= judgment_rag.quality_score - 0.1
    ), "Context DIAGNOSTIC deve ser ao menos tão tolerante quanto RAG"

    # DIAGNOSTIC não deve ser rejeitado se RAG for rejeitado por falta de fontes
    if judgment_rag.verdict == "rejected" and "fontes" in " ".join(judgment_rag.issues).lower():
        assert (
            judgment_diagnostic.verdict != "rejected"
        ), "DIAGNOSTIC não deve ser rejeitado por falta de fontes (RAG seria)"


# ============ TESTES BACKWARD COMPATIBILITY ============


def test_default_context_is_rag(judge, rag_response_without_sources):
    """
    [COMPATIBILIDADE] Default evaluation_context deve ser 'RAG'.

    Validação: comportamento original (rigoroso) mantido quando context não especificado.
    """
    # Chamar evaluate SEM especificar evaluation_context (usa default 'RAG')
    judgment = judge.evaluate(
        original_query="O que é BSC?",
        agent_response=rag_response_without_sources,
        retrieved_documents="[Docs...]",
        agent_name="RAG Agent",
        # evaluation_context NÃO especificado -> default 'RAG'
    )

    # Deve comportar-se como RAG (rigoroso)
    assert judgment.has_sources is False, "Default context deve detectar falta de fontes"

    # Se resposta é mediana, deve ser penalizada (comportamento original)
    if judgment.quality_score < 0.85:
        assert judgment.verdict in [
            "needs_improvement",
            "rejected",
        ], "Default context deve manter rigor original (penalizar falta de fontes)"


def test_evaluate_multiple_accepts_context(judge):
    """
    [COMPATIBILIDADE] evaluate_multiple deve aceitar evaluation_context.

    Validação: método evaluate_multiple propaga context para evaluate.
    """
    agent_responses = [
        {"agent_name": "Diagnostic Agent", "response": "Análise diagnóstica sem fontes..."}
    ]

    # Chamar evaluate_multiple com context='DIAGNOSTIC'
    results = judge.evaluate_multiple(
        original_query="Diagnóstico",
        agent_responses=agent_responses,
        retrieved_documents="[Perfil...]",
        evaluation_context="DIAGNOSTIC",
    )

    assert len(results) == 1, "Deve retornar 1 avaliação"

    judgment = results[0]["judgment"]

    # Deve ter sido avaliado em contexto DIAGNOSTIC (tolerante)
    assert (
        judgment.verdict != "rejected" or "fontes" not in " ".join(judgment.issues).lower()
    ), "evaluate_multiple deve propagar context corretamente"


# ============ SMOKE TESTS ============


@pytest.mark.parametrize("context", ["RAG", "DIAGNOSTIC", "TOOLS"])
def test_smoke_all_contexts(judge, context):
    """
    [SMOKE] Judge deve funcionar com todos os contextos válidos.

    Validação: não deve crashar, deve retornar JudgmentResult válido.
    """
    judgment = judge.evaluate(
        original_query="Query teste",
        agent_response="Resposta teste...",
        retrieved_documents="[Docs...]",
        agent_name="Test Agent",
        evaluation_context=context,
    )

    # Deve retornar JudgmentResult válido
    assert isinstance(judgment, JudgmentResult), f"Context '{context}' deve retornar JudgmentResult"

    # Campos obrigatórios devem estar presentes
    assert (
        0.0 <= judgment.quality_score <= 1.0
    ), f"Context '{context}': quality_score deve estar entre 0 e 1"

    assert judgment.verdict in [
        "approved",
        "needs_improvement",
        "rejected",
    ], f"Context '{context}': verdict deve ser válido"

    assert (
        isinstance(judgment.reasoning, str) and judgment.reasoning
    ), f"Context '{context}': reasoning deve ser string não-vazia"
