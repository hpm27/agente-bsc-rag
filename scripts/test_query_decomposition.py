"""
Script de teste manual para Query Decomposition (Fase 2A.1).

Testa:
1. QueryDecomposer.should_decompose() com queries simples e complexas
2. QueryDecomposer.decompose() gerando sub-queries
3. BSCRetriever.retrieve_with_decomposition() workflow completo

Usage:
    python scripts/test_query_decomposition.py
"""

import asyncio
import sys
import os

# Adicionar src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.rag.query_decomposer import QueryDecomposer
from src.rag.retriever import BSCRetriever
from config.settings import settings, get_llm
from loguru import logger


async def test_should_decompose():
    """Testa heurísticas de decisão de decomposição."""
    print("\n" + "="*80)
    print("TESTE 1: Heurísticas de Decisão (should_decompose)")
    print("="*80)
    
    # Criar decomposer
    decomposer = QueryDecomposer(
        llm=get_llm(settings.decomposition_llm),
        enabled=settings.enable_query_decomposition,
        min_query_length=settings.decomposition_min_query_length,
        score_threshold=settings.decomposition_score_threshold
    )
    
    # Queries de teste
    test_queries = [
        # Queries simples (NÃO deve decompor)
        ("O que é BSC?", False),
        ("Quem criou o Balanced Scorecard?", False),
        ("Definição de KPI", False),
        
        # Queries complexas (DEVE decompor)
        (
            "Como implementar BSC considerando as perspectivas financeira, "
            "clientes e processos internos?",
            True
        ),
        (
            "Quais são as diferenças entre a perspectiva de aprendizado e "
            "crescimento e a perspectiva de processos internos no BSC?",
            True
        ),
        (
            "Explique a relação entre objetivos estratégicos e KPIs nas "
            "quatro perspectivas do Balanced Scorecard",
            True
        ),
    ]
    
    print(f"\nConfiguração:")
    print(f"  - Min Length: {decomposer.min_query_length} chars")
    print(f"  - Score Threshold: {decomposer.score_threshold}")
    print(f"  - Enabled: {decomposer.enabled}")
    
    for i, (query, expected_decompose) in enumerate(test_queries, 1):
        should, score = decomposer.should_decompose(query)
        status = "[OK]" if should == expected_decompose else "[ERRO]"
        
        print(f"\n{status} Query {i}:")
        print(f"  Query: {query[:80]}{'...' if len(query) > 80 else ''}")
        print(f"  Length: {len(query)} chars")
        print(f"  Score: {score}")
        print(f"  Decisão: {'DECOMPOR' if should else 'NÃO DECOMPOR'}")
        print(f"  Esperado: {'DECOMPOR' if expected_decompose else 'NÃO DECOMPOR'}")


async def test_decompose():
    """Testa decomposição de queries complexas."""
    print("\n" + "="*80)
    print("TESTE 2: Decomposição de Queries (decompose)")
    print("="*80)
    
    # Criar decomposer
    decomposer = QueryDecomposer(
        llm=get_llm(settings.decomposition_llm),
        enabled=settings.enable_query_decomposition,
        min_query_length=settings.decomposition_min_query_length,
        score_threshold=settings.decomposition_score_threshold
    )
    
    # Queries complexas para decompor
    complex_queries = [
        "Como implementar BSC considerando as perspectivas financeira, clientes e processos?",
        "Quais são as diferenças entre objetivos estratégicos e KPIs no Balanced Scorecard?",
        "Explique a relação entre as quatro perspectivas do BSC e como elas se interconectam",
    ]
    
    for i, query in enumerate(complex_queries, 1):
        print(f"\n[TESTE] Query {i}:")
        print(f"  Original: {query}")
        
        try:
            # Decompor
            sub_queries = await decomposer.decompose(query)
            
            print(f"  Sub-queries geradas: {len(sub_queries)}")
            for j, sq in enumerate(sub_queries, 1):
                print(f"    {j}. {sq}")
            
            # Validar
            if len(sub_queries) >= 2 and len(sub_queries) <= 4:
                print(f"  [OK] Número de sub-queries válido (2-4)")
            else:
                print(f"  [WARN] Número de sub-queries fora do esperado: {len(sub_queries)}")
                
        except Exception as e:
            print(f"  [ERRO] Falha na decomposição: {e}")


async def test_retrieve_with_decomposition():
    """Testa retrieval integrado com decomposição."""
    print("\n" + "="*80)
    print("TESTE 3: Retrieval Integrado (retrieve_with_decomposition)")
    print("="*80)
    
    print("\n[INFO] Inicializando retriever e decomposer...")
    
    try:
        # Criar retriever
        retriever = BSCRetriever()
        
        # Criar decomposer
        decomposer = QueryDecomposer(
            llm=get_llm(settings.decomposition_llm),
            enabled=settings.enable_query_decomposition,
            min_query_length=settings.decomposition_min_query_length,
            score_threshold=settings.decomposition_score_threshold
        )
        
        # Queries de teste
        test_queries = [
            ("Query simples", "O que é Balanced Scorecard?"),
            (
                "Query complexa",
                "Como implementar BSC considerando perspectivas financeira e clientes?"
            ),
        ]
        
        for query_type, query in test_queries:
            print(f"\n[TESTE] {query_type}:")
            print(f"  Query: {query}")
            
            try:
                # Retrieval com decomposição
                results = await retriever.retrieve_with_decomposition(
                    query=query,
                    k=5,
                    decomposer=decomposer,
                    use_hybrid=True,
                    use_rerank=True
                )
                
                print(f"  [OK] Retrieval completo - {len(results)} documentos recuperados")
                
                # Mostrar top-3 documentos
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. Score: {result.score:.3f} | "
                          f"Fonte: {result.source} | "
                          f"Preview: {result.content[:80]}...")
                
            except Exception as e:
                print(f"  [ERRO] Falha no retrieval: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"\n[ERRO] Falha na inicialização: {e}")
        print("\n[INFO] Certifique-se de que:")
        print("  1. Vector store está rodando (docker-compose up -d)")
        print("  2. Knowledge base foi construída (scripts/build_knowledge_base.py)")
        print("  3. API keys estão configuradas no .env")


async def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("TESTE MANUAL - QUERY DECOMPOSITION (Fase 2A.1)")
    print("="*80)
    
    # Configurar logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Executar testes
    await test_should_decompose()
    await test_decompose()
    await test_retrieve_with_decomposition()
    
    print("\n" + "="*80)
    print("TESTES COMPLETOS")
    print("="*80)
    print("\nPróximos passos:")
    print("  1. DIA 3: Criar testes unitários (tests/test_query_decomposer.py)")
    print("  2. DIA 3: Criar benchmark com 20 queries complexas")
    print("  3. DIA 3: Medir métricas (Recall@10, Precision@5, Latência)")
    print("  4. DIA 4: Documentação completa (docs/techniques/QUERY_DECOMPOSITION.md)")


if __name__ == "__main__":
    asyncio.run(main())

