"""
Demonstração: Judge Agent Context-Aware

Este exemplo mostra como o Judge Agent avalia respostas de forma diferente
dependendo do contexto (RAG vs DIAGNOSTIC).

PROBLEMA RESOLVIDO:
- Na fase DIAGNÓSTICO, recomendações são baseadas APENAS no perfil do cliente (sem retrieval)
- Fontes de literatura BSC só virão em fases posteriores (Ferramentas Consultivas)
- Judge não deve penalizar diagnósticos por falta de fontes

SOLUÇÃO:
- Judge agora aceita parâmetro 'evaluation_context' ('RAG' ou 'DIAGNOSTIC')
- Contexto 'DIAGNOSTIC': relaxa critérios de fontes, foca em qualidade da análise
- Contexto 'RAG': mantém rigor original (fontes esperadas)
"""

import asyncio
from src.agents.judge_agent import JudgeAgent


def demo_rag_evaluation():
    """Demonstra avaliação RAG (fontes ESPERADAS)."""
    print("\n" + "="*70)
    print("[DEMO 1] AVALIAÇÃO RAG (Fontes Esperadas)")
    print("="*70)
    
    judge = JudgeAgent()
    
    query = "O que é Balanced Scorecard?"
    
    response_with_sources = """
    O Balanced Scorecard (BSC) é um sistema de gestão estratégica criado por Kaplan & Norton
    que traduz a visão e estratégia da organização em objetivos mensuráveis organizados
    em 4 perspectivas balanceadas: Financeira, Clientes, Processos Internos, e 
    Aprendizado e Crescimento (Fonte: Kaplan & Norton, 1996, p. 8-12).
    """
    
    response_without_sources = """
    O Balanced Scorecard é um sistema de gestão que organiza objetivos em 4 perspectivas.
    Ajuda a empresa a medir performance e executar estratégia de forma balanceada.
    """
    
    docs = "[Kaplan, R. S., & Norton, D. P. (1996). The Balanced Scorecard...]"
    
    # Avaliar resposta COM fontes (context='RAG')
    judgment1 = judge.evaluate(
        original_query=query,
        agent_response=response_with_sources,
        retrieved_documents=docs,
        agent_name="RAG Agent",
        evaluation_context="RAG"
    )
    
    print(f"\n[COM FONTES] Score: {judgment1.quality_score:.2f} | Verdict: {judgment1.verdict}")
    print(f"  has_sources: {judgment1.has_sources} | is_grounded: {judgment1.is_grounded}")
    print(f"  Reasoning: {judgment1.reasoning}")
    
    # Avaliar resposta SEM fontes (context='RAG')
    judgment2 = judge.evaluate(
        original_query=query,
        agent_response=response_without_sources,
        retrieved_documents=docs,
        agent_name="RAG Agent",
        evaluation_context="RAG"
    )
    
    print(f"\n[SEM FONTES] Score: {judgment2.quality_score:.2f} | Verdict: {judgment2.verdict}")
    print(f"  has_sources: {judgment2.has_sources} | is_grounded: {judgment2.is_grounded}")
    print(f"  Issues: {judgment2.issues}")


def demo_diagnostic_evaluation():
    """Demonstra avaliação DIAGNÓSTICO (fontes NÃO esperadas)."""
    print("\n" + "="*70)
    print("[DEMO 2] AVALIAÇÃO DIAGNÓSTICO (Fontes Não Esperadas)")
    print("="*70)
    
    judge = JudgeAgent()
    
    query = "Diagnóstico BSC para empresa XYZ"
    
    diagnostic_response = """
    EXECUTIVE SUMMARY:
    Empresa TechCorp (setor tecnologia, 500 funcionários) apresenta sólido desempenho
    financeiro (EBITDA 35%, crescimento 25% a.a.) mas enfrenta desafios críticos em
    retenção de clientes (churn 15%) e inovação de produtos (ciclo desenvolvimento 18 meses).
    
    GAPS IDENTIFICADOS:
    - Perspectiva Clientes: Baixa satisfação NPS (45, benchmark 70+)
    - Perspectiva Processos: Processos desenvolvimento lentos
    - Perspectiva Aprendizado: Turnover engenheiros (22% vs 10% mercado)
    
    RECOMENDAÇÕES PRIORIZADAS:
    1. [HIGH] Implementar Customer Success estruturado (ROI: -30% churn em 6 meses)
    2. [HIGH] Adotar metodologia Agile (ROI: -40% time-to-market em 12 meses)
    3. [MEDIUM] Programa retenção talentos (ROI: -50% turnover em 18 meses)
    """
    
    # Avaliar diagnóstico com context='DIAGNOSTIC'
    judgment = judge.evaluate(
        original_query=query,
        agent_response=diagnostic_response,
        retrieved_documents="[Perfil cliente: TechCorp, setor tecnologia, 500 funcionários...]",
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC"
    )
    
    print(f"\n[DIAGNÓSTICO] Score: {judgment.quality_score:.2f} | Verdict: {judgment.verdict}")
    print(f"  has_sources: {judgment.has_sources} | is_grounded: {judgment.is_grounded}")
    print(f"  Reasoning: {judgment.reasoning}")
    
    if judgment.issues:
        print(f"  Issues: {judgment.issues}")
    if judgment.suggestions:
        print(f"  Suggestions: {judgment.suggestions}")
    
    print("\n[INFO] Judge não penalizou por falta de fontes (contexto DIAGNOSTIC)")
    print("[INFO] Avaliação focou em QUALIDADE DA ANÁLISE e COERÊNCIA das recomendações")


def demo_comparison():
    """Compara avaliações do MESMO diagnóstico em contextos diferentes."""
    print("\n" + "="*70)
    print("[DEMO 3] COMPARAÇÃO: Mesmo Diagnóstico, Contextos Diferentes")
    print("="*70)
    
    judge = JudgeAgent()
    
    query = "Diagnóstico BSC"
    diagnostic = "Empresa XYZ precisa melhorar NPS (45 → 70+) via Customer Success..."
    docs = "[Perfil cliente...]"
    
    # Avaliar como DIAGNOSTIC (fontes não esperadas)
    judgment_diagnostic = judge.evaluate(
        original_query=query,
        agent_response=diagnostic,
        retrieved_documents=docs,
        agent_name="Diagnostic Agent",
        evaluation_context="DIAGNOSTIC"
    )
    
    # Avaliar como RAG (fontes ESPERADAS - penaliza falta)
    judgment_rag = judge.evaluate(
        original_query=query,
        agent_response=diagnostic,
        retrieved_documents=docs,
        agent_name="Diagnostic Agent",
        evaluation_context="RAG"
    )
    
    print(f"\n[CONTEXTO: DIAGNOSTIC]")
    print(f"  Score: {judgment_diagnostic.quality_score:.2f} | Verdict: {judgment_diagnostic.verdict}")
    
    print(f"\n[CONTEXTO: RAG]")
    print(f"  Score: {judgment_rag.quality_score:.2f} | Verdict: {judgment_rag.verdict}")
    print(f"  Issues: {judgment_rag.issues}")
    
    print("\n[COMPARAÇÃO]")
    print(f"  Diferença de score: {judgment_diagnostic.quality_score - judgment_rag.quality_score:.2f}")
    print(f"  Context='DIAGNOSTIC' → Foco em qualidade da análise")
    print(f"  Context='RAG' → Penaliza falta de fontes")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("JUDGE AGENT CONTEXT-AWARE - DEMONSTRAÇÃO")
    print("="*70)
    
    # Demo 1: Avaliação RAG (fontes esperadas)
    demo_rag_evaluation()
    
    # Demo 2: Avaliação DIAGNÓSTICO (fontes não esperadas)
    demo_diagnostic_evaluation()
    
    # Demo 3: Comparação lado a lado
    demo_comparison()
    
    print("\n" + "="*70)
    print("[OK] Demonstração completa!")
    print("="*70)
    print("\nUSO NO WORKFLOW:")
    print("  - FASE RAG: judge.evaluate(..., evaluation_context='RAG')")
    print("  - FASE DIAGNÓSTICO: judge.evaluate(..., evaluation_context='DIAGNOSTIC')")
    print("  - FASE FERRAMENTAS: judge.evaluate(..., evaluation_context='TOOLS')")

