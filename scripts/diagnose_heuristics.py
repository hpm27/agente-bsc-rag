"""
Script de diagnóstico para testar heurísticas de Query Decomposition.

Testa queries do benchmark para entender por que should_decompose está
retornando False para todas as queries.
"""

import sys
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from langchain_openai import ChatOpenAI

from src.rag.query_decomposer import QueryDecomposer


def diagnose_queries():
    """Testa queries do benchmark e mostra scores detalhados."""

    # Inicializar decomposer com configurações padrão
    llm = ChatOpenAI(
        model=settings.decomposition_llm, temperature=0, api_key=settings.openai_api_key
    )
    decomposer = QueryDecomposer(llm)

    # Queries do benchmark para testar
    test_queries = [
        "Como implementar BSC considerando as 4 perspectivas e suas interconexões?",
        "Quais são as diferenças entre BSC em manufatura versus serviços?",
        "Como relacionar indicadores financeiros com aprendizado organizacional?",
        "Quais KPIs financeiros e de clientes são recomendados por Kaplan & Norton?",
        "O que é BSC?",  # Query simples (não deve decompor)
        "Explique a perspectiva financeira",  # Query simples
    ]

    print("=" * 80)
    print("DIAGNÓSTICO DE HEURÍSTICAS - QUERY DECOMPOSITION")
    print("=" * 80)
    print()
    print("Configuração atual:")
    print(f"  - min_query_length: {decomposer.min_query_length}")
    print(f"  - score_threshold: {decomposer.score_threshold}")
    print(f"  - enabled: {decomposer.enabled}")
    print()
    print("-" * 80)
    print()

    for i, query in enumerate(test_queries, 1):
        print(f"[Query {i}] {query}")
        print(f"  Comprimento: {len(query)} caracteres")

        # Usar score oficial do decomposer
        should, score = decomposer.should_decompose(query)

        print(f"  Score de complexidade: {score}")
        print(f"  Threshold: {decomposer.score_threshold}")
        print(f"  Decisão: {'DECOMPOR' if should else 'NÃO DECOMPOR'}")

        if should:
            print(
                f"  [OK] Query será decomposta (score {score} >= threshold {decomposer.score_threshold})"
            )
        elif len(query) < decomposer.min_query_length:
            print(f"  [SKIP] Query muito curta ({len(query)} < {decomposer.min_query_length})")
        else:
            print(f"  [SKIP] Score insuficiente ({score} < {decomposer.score_threshold})")

        print()

    print("-" * 80)
    print()
    print("CONCLUSÃO:")
    print()
    print("Se queries complexas não estão sendo decompostas, considerar:")
    print("  1. Reduzir score_threshold de 2 para 1")
    print("  2. Reduzir min_query_length de 50 para 30")
    print("  3. Adicionar heurística para '4 perspectivas' / 'todas perspectivas'")
    print("  4. Adicionar mais palavras de ligação")
    print()


if __name__ == "__main__":
    diagnose_queries()
