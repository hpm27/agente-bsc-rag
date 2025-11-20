"""
Script de teste para medir ganho de performance do caching de embeddings.

Uso:
    python tests/test_embedding_cache.py
"""

import sys
import time
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings

from src.rag.embeddings import EmbeddingManager


def test_embed_text_performance():
    """
    Testa performance de embed_text com e sem cache.
    """
    print("\n" + "=" * 70)
    print("TESTE 1: embed_text() - Performance com Cache")
    print("=" * 70)

    # Inicializar EmbeddingManager
    manager = EmbeddingManager()

    # Lista de textos para testar (com repetições)
    test_texts = [
        "O Balanced Scorecard é uma metodologia de gestão estratégica.",
        "A perspectiva financeira mede os resultados econômicos.",
        "A perspectiva do cliente avalia satisfação e retenção.",
        "A perspectiva de processos internos foca em eficiência operacional.",
        "A perspectiva de aprendizado e crescimento desenvolve capacidades.",
    ]

    # Repetir textos para simular uso realista
    all_texts = test_texts * 4  # 20 textos (5 únicos, 4 repetições cada)

    print(f"\nTestando com {len(all_texts)} textos ({len(test_texts)} únicos, 4x cada)")
    print("-" * 70)

    # Primeira execução (cold cache)
    print("\n[RUN 1] COLD CACHE - Primeira execução")
    start_time = time.time()
    for i, text in enumerate(all_texts):
        embedding = manager.embed_text(text)
        if i == 0:
            print(f"  Embedding dimension: {len(embedding)}")
    first_run_time = time.time() - start_time
    print(f"  Tempo total: {first_run_time:.3f}s")
    print(f"  Tempo médio por texto: {first_run_time/len(all_texts):.3f}s")

    # Segunda execução (warm cache)
    print("\n[RUN 2] WARM CACHE - Segunda execução (textos repetidos)")
    start_time = time.time()
    for text in all_texts:
        embedding = manager.embed_text(text)
    second_run_time = time.time() - start_time
    print(f"  Tempo total: {second_run_time:.3f}s")
    print(f"  Tempo médio por texto: {second_run_time/len(all_texts):.3f}s")

    # Estatísticas de cache
    print("\n" + "=" * 70)
    print("ESTATÍSTICAS DE CACHE")
    print("=" * 70)
    print(f"Cache Hits: {manager.cache_hits}")
    print(f"Cache Misses: {manager.cache_misses}")
    total = manager.cache_hits + manager.cache_misses
    if total > 0:
        hit_rate = (manager.cache_hits / total) * 100
        print(f"Cache Hit Rate: {hit_rate:.1f}%")

    # Ganho de performance
    if first_run_time > 0:
        speedup = first_run_time / second_run_time if second_run_time > 0 else float("inf")
        improvement = ((first_run_time - second_run_time) / first_run_time) * 100

        print("\n" + "=" * 70)
        print("GANHO DE PERFORMANCE")
        print("=" * 70)
        print(f"Speedup: {speedup:.2f}x")
        print(f"Redução de tempo: {improvement:.1f}%")
        print(f"Tempo economizado: {first_run_time - second_run_time:.3f}s")


def test_embed_batch_performance():
    """
    Testa performance de embed_batch com e sem cache.
    """
    print("\n" + "=" * 70)
    print("TESTE 2: embed_batch() - Performance com Cache em Lote")
    print("=" * 70)

    # Inicializar EmbeddingManager
    manager = EmbeddingManager()

    # Reset stats
    manager.cache_hits = 0
    manager.cache_misses = 0

    # Lista de textos para testar
    test_texts = [
        "Indicadores financeiros como ROI e margem de lucro são essenciais.",
        "A satisfação do cliente está diretamente ligada à receita.",
        "Processos eficientes reduzem custos e aumentam qualidade.",
        "Treinamento de equipe melhora produtividade e inovação.",
        "O mapa estratégico conecta as quatro perspectivas do BSC.",
        "Alinhamento organizacional é chave para execução da estratégia.",
        "KPIs devem ser específicos, mensuráveis e acionáveis.",
        "O cascateamento do scorecard garante foco em todos os níveis.",
    ]

    print(f"\nTestando com batch de {len(test_texts)} textos")
    print("-" * 70)

    # Primeira execução (cold cache)
    print("\n[RUN 1] COLD CACHE - Primeira execução (batch)")
    start_time = time.time()
    embeddings_1 = manager.embed_batch(test_texts, batch_size=4)
    first_run_time = time.time() - start_time
    print(f"  Tempo total: {first_run_time:.3f}s")
    print(f"  Embeddings gerados: {len(embeddings_1)}")

    # Segunda execução (warm cache)
    print("\n[RUN 2] WARM CACHE - Segunda execução (batch)")
    start_time = time.time()
    embeddings_2 = manager.embed_batch(test_texts, batch_size=4)
    second_run_time = time.time() - start_time
    print(f"  Tempo total: {second_run_time:.3f}s")
    print(f"  Embeddings gerados: {len(embeddings_2)}")

    # Estatísticas de cache
    print("\n" + "=" * 70)
    print("ESTATÍSTICAS DE CACHE (BATCH)")
    print("=" * 70)
    print(f"Cache Hits: {manager.cache_hits}")
    print(f"Cache Misses: {manager.cache_misses}")
    total = manager.cache_hits + manager.cache_misses
    if total > 0:
        hit_rate = (manager.cache_hits / total) * 100
        print(f"Cache Hit Rate: {hit_rate:.1f}%")

    # Ganho de performance
    if first_run_time > 0:
        speedup = first_run_time / second_run_time if second_run_time > 0 else float("inf")
        improvement = ((first_run_time - second_run_time) / first_run_time) * 100

        print("\n" + "=" * 70)
        print("GANHO DE PERFORMANCE (BATCH)")
        print("=" * 70)
        print(f"Speedup: {speedup:.2f}x")
        print(f"Redução de tempo: {improvement:.1f}%")
        print(f"Tempo economizado: {first_run_time - second_run_time:.3f}s")


def main():
    """
    Executa testes de performance do cache de embeddings.
    """
    print("\n" + "=" * 70)
    print("TESTE DE PERFORMANCE: Caching de Embeddings")
    print("=" * 70)
    print(f"Provider: {settings.openai_embedding_model}")
    print(f"Cache Enabled: {settings.embedding_cache_enabled}")
    print(f"Cache Directory: {settings.embedding_cache_dir}")
    print(f"Cache TTL: {settings.embedding_cache_ttl_days} dias")
    print(f"Cache Max Size: {settings.embedding_cache_max_size_gb} GB")

    # Teste 1: embed_text
    test_embed_text_performance()

    # Aguardar um pouco entre testes
    print("\n[WAIT] Aguardando 2s entre testes...")
    time.sleep(2)

    # Teste 2: embed_batch
    test_embed_batch_performance()

    print("\n" + "=" * 70)
    print("[OK] Testes de performance concluídos!")
    print("=" * 70)


if __name__ == "__main__":
    main()
