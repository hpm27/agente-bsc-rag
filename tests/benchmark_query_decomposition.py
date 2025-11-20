"""
Benchmark Query Decomposition vs Baseline Retrieval.

Compara performance de retrieval COM e SEM query decomposition em 20 queries BSC.

Métricas medidas:
- Recall@10: % de documentos relevantes recuperados
- Precision@5: % de documentos relevantes no top-5
- Latência P50/P95/Mean: Tempo de execução
- Heurística Accuracy: % de decisões corretas de should_decompose()
- # Sub-queries geradas

Gera relatório markdown: tests/benchmark_report_query_decomposition.md

Executar:
    python tests/benchmark_query_decomposition.py
    python tests/benchmark_query_decomposition.py --queries 5  # Apenas 5 queries (teste rápido)
"""

import argparse
import asyncio
import json
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean, median
from typing import Any

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from langchain_openai import ChatOpenAI

from src.rag.query_decomposer import QueryDecomposer
from src.rag.retriever import BSCRetriever

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

BENCHMARK_FILE = Path(__file__).parent / "benchmark_queries.json"
REPORT_FILE = Path(__file__).parent / "benchmark_report_query_decomposition.md"


# ============================================================================
# MÉTRICAS
# ============================================================================


def fuzzy_match_document(doc_source: str, ground_truth: str, threshold: float = 0.75) -> bool:
    """
    Verifica se um documento fonte faz match fuzzy com ground truth.

    Usa SequenceMatcher para aceitar variações como:
    - "The Balanced Scorecard" = "The_balanced_scorecard"
    - "Strategy Maps" = "strategy_maps"
    - Ignora case e underscores

    Args:
        doc_source: Source do documento recuperado
        ground_truth: Nome esperado do documento
        threshold: Threshold de similaridade (0.0 a 1.0)

    Returns:
        bool: True se há match suficiente
    """
    # Normalizar strings
    doc_normalized = doc_source.lower().replace("_", " ").replace("-", " ")
    gt_normalized = ground_truth.lower().replace("_", " ").replace("-", " ")

    # Match direto (substring)
    if gt_normalized in doc_normalized:
        return True

    # Fuzzy match usando SequenceMatcher
    similarity = SequenceMatcher(None, doc_normalized, gt_normalized).ratio()

    # Também testar apenas o nome do arquivo (sem caminho)
    doc_filename = doc_normalized.split("/")[-1].split("\\")[-1]
    filename_similarity = SequenceMatcher(None, doc_filename, gt_normalized).ratio()

    # Retornar True se qualquer similaridade passar o threshold
    return max(similarity, filename_similarity) >= threshold


def calculate_recall_at_k(
    retrieved_docs: list[Any], ground_truth_docs: list[str], k: int = 10
) -> float:
    """
    Calcula Recall@k.

    Recall@k = # docs relevantes recuperados no top-k / # docs relevantes totais

    Args:
        retrieved_docs: Documentos recuperados
        ground_truth_docs: Lista de nomes de documentos relevantes esperados
        k: Top-k documentos a considerar

    Returns:
        float: Recall@k (0.0 a 1.0)
    """
    if not ground_truth_docs:
        return 1.0  # Se não há ground truth, assumir sucesso

    # Pegar top-k docs
    top_k_docs = retrieved_docs[:k]

    # Contar quantos docs relevantes foram recuperados usando fuzzy matching
    retrieved_relevant = 0
    for doc in top_k_docs:
        doc_source = doc.metadata.get("source", "")
        for gt_doc in ground_truth_docs:
            if fuzzy_match_document(doc_source, gt_doc, threshold=0.70):
                retrieved_relevant += 1
                break

    recall = retrieved_relevant / len(ground_truth_docs)
    return min(recall, 1.0)


def calculate_precision_at_k(
    retrieved_docs: list[Any], ground_truth_docs: list[str], k: int = 5
) -> float:
    """
    Calcula Precision@k usando ground truth.

    Precision@k = # docs relevantes no top-k / k

    Args:
        retrieved_docs: Documentos recuperados
        ground_truth_docs: Lista de nomes de documentos relevantes esperados
        k: Top-k documentos a considerar

    Returns:
        float: Precision@k (0.0 a 1.0)
    """
    if not ground_truth_docs:
        return 1.0

    # Pegar top-k docs
    top_k_docs = retrieved_docs[:k]

    # Contar quantos docs relevantes no top-k usando fuzzy matching
    relevant_in_top_k = 0
    for doc in top_k_docs:
        doc_source = doc.metadata.get("source", "")
        for gt_doc in ground_truth_docs:
            if fuzzy_match_document(doc_source, gt_doc, threshold=0.70):
                relevant_in_top_k += 1
                break

    precision = relevant_in_top_k / k
    return precision


# ============================================================================
# BENCHMARK EXECUTOR
# ============================================================================


class BenchmarkExecutor:
    """Executa benchmark comparando baseline vs decomposition."""

    def __init__(self, max_queries: int = None):
        """
        Inicializa executor.

        Args:
            max_queries: Máximo de queries a executar (None = todas)
        """
        self.max_queries = max_queries
        self.retriever = BSCRetriever()

        # LLM para decomposição
        llm = ChatOpenAI(
            model=settings.decomposition_llm, temperature=0, api_key=settings.openai_api_key
        )
        self.decomposer = QueryDecomposer(llm)

        # Resultados
        self.baseline_results: list[dict[str, Any]] = []
        self.decomposition_results: list[dict[str, Any]] = []
        self.heuristic_decisions: list[dict[str, Any]] = []

    def load_queries(self) -> list[dict[str, Any]]:
        """Carrega queries do benchmark dataset."""
        with open(BENCHMARK_FILE, encoding="utf-8") as f:
            data = json.load(f)

        queries = data["queries"]

        if self.max_queries:
            queries = queries[: self.max_queries]

        print(f"[INFO] Carregadas {len(queries)} queries do benchmark")
        return queries

    async def run_baseline(self, query_data: dict[str, Any]) -> dict[str, Any]:
        """
        Executa retrieval BASELINE (sem decomposição).

        Args:
            query_data: Dados da query do benchmark

        Returns:
            Dict com resultados
        """
        query = query_data["query"]

        # Medir latência
        start_time = time.time()

        # Retrieval normal
        docs = await self.retriever.retrieve_async(query, k=10)

        latency = time.time() - start_time

        # Calcular métricas
        recall = calculate_recall_at_k(docs, query_data.get("ground_truth_docs", []), k=10)
        precision = calculate_precision_at_k(docs, query_data.get("ground_truth_docs", []), k=5)

        return {
            "query_id": query_data["id"],
            "latency": latency,
            "recall_at_10": recall,
            "precision_at_5": precision,
            "num_docs": len(docs),
        }

    async def run_decomposition(self, query_data: dict[str, Any]) -> dict[str, Any]:
        """
        Executa retrieval COM DECOMPOSITION.

        Args:
            query_data: Dados da query do benchmark

        Returns:
            Dict com resultados
        """
        query = query_data["query"]

        # Medir latência
        start_time = time.time()

        # Decisão da heurística (retorna tupla: bool, score)
        should_decompose_decision, complexity_score = self.decomposer.should_decompose(query)

        # Retrieval com decomposition
        if should_decompose_decision:
            # Decompor
            sub_queries = await self.decomposer.decompose(query)
            num_subqueries = len(sub_queries)

            # Retrieval paralelo
            tasks = [self.retriever.retrieve_async(sq, k=10) for sq in sub_queries]
            results_list = await asyncio.gather(*tasks)

            # RRF fusion
            docs = self.retriever._reciprocal_rank_fusion(results_list, k=60)[:10]
        else:
            # Retrieval normal (fallback)
            docs = await self.retriever.retrieve_async(query, k=10)
            num_subqueries = 0

        latency = time.time() - start_time

        # Calcular métricas
        recall = calculate_recall_at_k(docs, query_data.get("ground_truth_docs", []), k=10)
        precision = calculate_precision_at_k(docs, query_data.get("ground_truth_docs", []), k=5)

        # Validar decisão da heurística
        expected_should_decompose = query_data.get("should_decompose", False)
        heuristic_correct = should_decompose_decision == expected_should_decompose

        self.heuristic_decisions.append(
            {
                "query_id": query_data["id"],
                "expected": expected_should_decompose,
                "predicted": should_decompose_decision,
                "correct": heuristic_correct,
            }
        )

        return {
            "query_id": query_data["id"],
            "latency": latency,
            "recall_at_10": recall,
            "precision_at_5": precision,
            "num_docs": len(docs),
            "num_subqueries": num_subqueries,
            "should_decompose": should_decompose_decision,
            "complexity_score": complexity_score,
            "heuristic_correct": heuristic_correct,
        }

    async def run_benchmark(self):
        """Executa benchmark completo."""
        queries = self.load_queries()

        print(f"\n{'='*80}")
        print(f"BENCHMARK QUERY DECOMPOSITION - {len(queries)} queries")
        print(f"{'='*80}\n")

        for i, query_data in enumerate(queries, 1):
            query_id = query_data["id"]
            query = query_data["query"]
            category = query_data.get("category", "unknown")

            print(f"[{i}/{len(queries)}] {query_id} ({category})")
            print(f"  Query: {query[:80]}...")

            # Baseline
            print("  [BASELINE] Executando retrieval normal...")
            baseline_result = await self.run_baseline(query_data)
            self.baseline_results.append(baseline_result)
            print(
                f"    Latência: {baseline_result['latency']:.2f}s | Recall@10: {baseline_result['recall_at_10']:.2%} | Precision@5: {baseline_result['precision_at_5']:.2%}"
            )

            # Decomposition
            print("  [DECOMPOSITION] Executando retrieval com decomposição...")
            decomp_result = await self.run_decomposition(query_data)
            self.decomposition_results.append(decomp_result)
            print(
                f"    Latência: {decomp_result['latency']:.2f}s | Recall@10: {decomp_result['recall_at_10']:.2%} | Precision@5: {decomp_result['precision_at_5']:.2%}"
            )
            print(
                f"    Sub-queries: {decomp_result['num_subqueries']} | Heurística: {decomp_result['heuristic_correct']}"
            )

            print()

        print(f"{'='*80}")
        print("BENCHMARK COMPLETO - Gerando relatório...")
        print(f"{'='*80}\n")

    def generate_report(self):
        """Gera relatório markdown comparativo."""

        # Calcular estatísticas agregadas
        baseline_latencies = [r["latency"] for r in self.baseline_results]
        decomp_latencies = [r["latency"] for r in self.decomposition_results]

        baseline_recalls = [r["recall_at_10"] for r in self.baseline_results]
        decomp_recalls = [r["recall_at_10"] for r in self.decomposition_results]

        baseline_precisions = [r["precision_at_5"] for r in self.baseline_results]
        decomp_precisions = [r["precision_at_5"] for r in self.decomposition_results]

        heuristic_accuracy = sum(1 for d in self.heuristic_decisions if d["correct"]) / len(
            self.heuristic_decisions
        )

        total_subqueries = sum(r.get("num_subqueries", 0) for r in self.decomposition_results)
        avg_subqueries_when_decomposed = (
            mean(
                [r["num_subqueries"] for r in self.decomposition_results if r["num_subqueries"] > 0]
            )
            if any(r["num_subqueries"] > 0 for r in self.decomposition_results)
            else 0
        )

        # Improvements
        recall_improvement = (
            ((mean(decomp_recalls) - mean(baseline_recalls)) / mean(baseline_recalls) * 100)
            if mean(baseline_recalls) > 0
            else 0
        )
        precision_improvement = (
            (
                (mean(decomp_precisions) - mean(baseline_precisions))
                / mean(baseline_precisions)
                * 100
            )
            if mean(baseline_precisions) > 0
            else 0
        )
        latency_overhead = mean(decomp_latencies) - mean(baseline_latencies)

        # Median improvement (com proteção contra divisão por zero)
        median_recall_improvement = (
            ((median(decomp_recalls) - median(baseline_recalls)) / median(baseline_recalls) * 100)
            if median(baseline_recalls) > 0
            else 0
        )
        median_precision_improvement = (
            (
                (median(decomp_precisions) - median(baseline_precisions))
                / median(baseline_precisions)
                * 100
            )
            if median(baseline_precisions) > 0
            else 0
        )

        # Gerar relatório
        report = f"""# Benchmark Report - Query Decomposition vs Baseline

**Data:** {time.strftime("%Y-%m-%d %H:%M:%S")}
**Queries Testadas:** {len(self.baseline_results)}
**Configuração:** {settings.decomposition_llm} | Cohere Rerank | Hybrid Search (BM25 + Qdrant)

---

## [EMOJI] Métricas Agregadas

### Recall@10

| Métrica | Baseline | Decomposition | Improvement |
|---------|----------|---------------|-------------|
| **Mean** | {mean(baseline_recalls):.2%} | {mean(decomp_recalls):.2%} | **{recall_improvement:+.1f}%** |
| **Median** | {median(baseline_recalls):.2%} | {median(decomp_recalls):.2%} | {median_recall_improvement:+.1f}% |
| **Min** | {min(baseline_recalls):.2%} | {min(decomp_recalls):.2%} | - |
| **Max** | {max(baseline_recalls):.2%} | {max(decomp_recalls):.2%} | - |

### Precision@5

| Métrica | Baseline | Decomposition | Improvement |
|---------|----------|---------------|-------------|
| **Mean** | {mean(baseline_precisions):.2%} | {mean(decomp_precisions):.2%} | **{precision_improvement:+.1f}%** |
| **Median** | {median(baseline_precisions):.2%} | {median(decomp_precisions):.2%} | {median_precision_improvement:+.1f}% |
| **Min** | {min(baseline_precisions):.2%} | {min(decomp_precisions):.2%} | - |
| **Max** | {max(baseline_precisions):.2%} | {max(decomp_precisions):.2%} | - |

### Latência (segundos)

| Métrica | Baseline | Decomposition | Overhead |
|---------|----------|---------------|----------|
| **Mean** | {mean(baseline_latencies):.2f}s | {mean(decomp_latencies):.2f}s | **+{latency_overhead:.2f}s** |
| **Median (P50)** | {median(baseline_latencies):.2f}s | {median(decomp_latencies):.2f}s | +{(median(decomp_latencies) - median(baseline_latencies)):.2f}s |
| **P95** | {sorted(baseline_latencies)[int(len(baseline_latencies)*0.95)]:.2f}s | {sorted(decomp_latencies)[int(len(decomp_latencies)*0.95)]:.2f}s | - |

### Query Decomposition Stats

| Métrica | Valor |
|---------|-------|
| **Heurística Accuracy** | **{heuristic_accuracy:.1%}** |
| **Queries Decompostas** | {sum(1 for r in self.decomposition_results if r['num_subqueries'] > 0)} / {len(self.decomposition_results)} |
| **Total Sub-queries Geradas** | {total_subqueries} |
| **Média Sub-queries (quando decompostas)** | {avg_subqueries_when_decomposed:.1f} |

---

## [OK] Critérios de Sucesso

| Critério | Target | Real | Status |
|----------|--------|------|--------|
| **Recall@10 Improvement** | > +30% | {recall_improvement:+.1f}% | {'[OK] PASS' if recall_improvement > 30 else '[ERRO] FAIL'} |
| **Precision@5 Improvement** | > +25% | {precision_improvement:+.1f}% | {'[OK] PASS' if precision_improvement > 25 else '[ERRO] FAIL'} |
| **Latência Adicional** | < 3s | +{latency_overhead:.2f}s | {'[OK] PASS' if latency_overhead < 3.0 else '[ERRO] FAIL'} |
| **Heurística Accuracy** | > 80% | {heuristic_accuracy:.1%} | {'[OK] PASS' if heuristic_accuracy > 0.80 else '[ERRO] FAIL'} |

---

## [EMOJI] Resultados Detalhados

### Por Query

| Query ID | Category | Recall Baseline | Recall Decomp | Δ | Precision Baseline | Precision Decomp | Δ |
|----------|----------|-----------------|---------------|---|-------------------|------------------|---|
"""

        # Adicionar linha por query
        for baseline, decomp in zip(self.baseline_results, self.decomposition_results):
            recall_delta = decomp["recall_at_10"] - baseline["recall_at_10"]
            precision_delta = decomp["precision_at_5"] - baseline["precision_at_5"]

            # Buscar categoria
            query_id = baseline["query_id"]
            category = next(
                (q["category"] for q in self.load_queries() if q["id"] == query_id), "unknown"
            )

            report += f"| {query_id} | {category} | {baseline['recall_at_10']:.2%} | {decomp['recall_at_10']:.2%} | {recall_delta:+.2%} | {baseline['precision_at_5']:.2%} | {decomp['precision_at_5']:.2%} | {precision_delta:+.2%} |\n"

        report += f"""
---

## [EMOJI] Conclusões

**Recall@10:**
- {'[OK] Query Decomposition melhorou recall em ' + f'{recall_improvement:.1f}%' if recall_improvement > 0 else '[ERRO] Baseline teve melhor recall'}
- {'[OK] Target de +30% foi ATINGIDO' if recall_improvement > 30 else '[ERRO] Target de +30% NÃO foi atingido'}

**Precision@5:**
- {'[OK] Query Decomposition melhorou precision em ' + f'{precision_improvement:.1f}%' if precision_improvement > 0 else '[ERRO] Baseline teve melhor precision'}
- {'[OK] Target de +25% foi ATINGIDO' if precision_improvement > 25 else '[ERRO] Target de +25% NÃO foi atingido'}

**Latência:**
- Overhead médio: +{latency_overhead:.2f}s
- {'[OK] Dentro do target de <3s' if latency_overhead < 3.0 else '[ERRO] Acima do target de 3s'}

**Heurística:**
- Accuracy: {heuristic_accuracy:.1%}
- {'[OK] Target de >80% foi ATINGIDO' if heuristic_accuracy > 0.80 else '[ERRO] Target de >80% NÃO foi atingido'}

**Recomendação Final:**
"""

        # Decisão GO/NO-GO
        if (
            recall_improvement > 30
            and precision_improvement > 25
            and latency_overhead < 3.0
            and heuristic_accuracy > 0.80
        ):
            report += """
[OK] **GO** - Query Decomposition VALIDADA para produção!
- Todos os critérios de sucesso foram atingidos
- Melhoria significativa em qualidade (recall + precision)
- Latência adicional aceitável
- Heurística confiável
"""
        else:
            report += """
[ERRO] **NO-GO** - Query Decomposition precisa de ajustes antes de produção.

Ajustes recomendados:
"""
            if recall_improvement <= 30:
                report += "- Ajustar decomposição para gerar sub-queries mais diversas\n"
            if precision_improvement <= 25:
                report += "- Melhorar RRF ou adicionar re-ranking adicional\n"
            if latency_overhead >= 3.0:
                report += "- Otimizar chamadas LLM ou usar modelo mais rápido\n"
            if heuristic_accuracy <= 0.80:
                report += "- Ajustar heurísticas de decisão (limiares, palavras-chave)\n"

        report += f"""
---

**Gerado por:** `tests/benchmark_query_decomposition.py`
**Configuração:** Hybrid Search + Cohere Rerank + {settings.decomposition_llm}
"""

        # Salvar relatório
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"[OK] Relatório gerado: {REPORT_FILE}")
        print(f"\n{'='*80}")
        print("RESUMO EXECUTIVO")
        print(f"{'='*80}")
        print(
            f"Recall@10 Improvement:    {recall_improvement:+.1f}% {'[OK]' if recall_improvement > 30 else '[FAIL]'}"
        )
        print(
            f"Precision@5 Improvement:  {precision_improvement:+.1f}% {'[OK]' if precision_improvement > 25 else '[FAIL]'}"
        )
        print(
            f"Latência Adicional:       +{latency_overhead:.2f}s {'[OK]' if latency_overhead < 3.0 else '[FAIL]'}"
        )
        print(
            f"Heurística Accuracy:      {heuristic_accuracy:.1%} {'[OK]' if heuristic_accuracy > 0.80 else '[FAIL]'}"
        )
        print(f"{'='*80}\n")


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Executa benchmark."""
    parser = argparse.ArgumentParser(description="Benchmark Query Decomposition")
    parser.add_argument(
        "--queries",
        type=int,
        default=None,
        help="Número máximo de queries a executar (default: todas)",
    )
    args = parser.parse_args()

    executor = BenchmarkExecutor(max_queries=args.queries)
    await executor.run_benchmark()
    executor.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
