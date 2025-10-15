"""
Script principal de benchmark Fase 2A - Baseline vs Fase 2A otimizada.

Este script executa 50 queries BSC em dois sistemas:
1. BASELINE: RAG sem Query Decomposition, Adaptive Re-ranking e Router
2. FASE 2A: RAG completo com todas otimizações

Métricas Avaliadas:
- Context Relevancy (RAGAS)
- Answer Relevancy (RAGAS)
- Faithfulness (RAGAS)
- Latency P50/P95
- Judge Approval Rate
- Cost (tokens usados)

Uso:
    python tests/benchmark_fase2a/run_benchmark.py
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import os
import sys

# Adicionar src ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    answer_relevancy,
    faithfulness,
    context_recall
)
from datasets import Dataset

# Importar workflow e configurações
from src.graph.workflow import get_workflow
from config.settings import settings

# Configurar logging
logger.remove()
logger.add(sys.stderr, level="INFO")


class BSCBenchmark:
    """Benchmark completo para avaliar Baseline vs Fase 2A."""
    
    def __init__(self, queries_file: Path, output_dir: Path, limit: int = None):
        """
        Inicializa benchmark.
        
        Args:
            queries_file: Path para arquivo JSON com 50 queries
            output_dir: Diretório para salvar resultados
            limit: Limite de queries a executar (None = todas)
        """
        self.queries_file = queries_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Carregar queries
        with open(queries_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.queries = data["queries"]
        
        # Aplicar limite se especificado
        if limit:
            self.queries = self.queries[:limit]
            logger.info(f"[BENCHMARK] MODO PILOTO: Limitado a {limit} queries")
        
        logger.info(f"[BENCHMARK] Carregadas {len(self.queries)} queries do dataset")
    
    def run_system(
        self, 
        system_name: str, 
        enable_decomposition: bool,
        enable_adaptive_rerank: bool,
        enable_router: bool
    ) -> List[Dict[str, Any]]:
        """
        Executa todas queries em um sistema (baseline ou fase2a).
        
        Args:
            system_name: Nome do sistema ('baseline' ou 'fase2a')
            enable_decomposition: Habilitar query decomposition
            enable_adaptive_rerank: Habilitar adaptive re-ranking
            enable_router: Habilitar router inteligente
            
        Returns:
            Lista de resultados por query
        """
        logger.info(f"[BENCHMARK] Iniciando execução {system_name} ({len(self.queries)} queries)")
        
        # Configurar features via environment variables
        os.environ["ENABLE_QUERY_DECOMPOSITION"] = str(enable_decomposition).lower()
        os.environ["ENABLE_ADAPTIVE_RERANK"] = str(enable_adaptive_rerank).lower()
        os.environ["ENABLE_ROUTER"] = str(enable_router).lower()
        
        # Recarregar settings
        from importlib import reload
        import config.settings as settings_module
        reload(settings_module)
        
        # Criar workflow
        workflow = get_workflow()
        
        results = []
        
        for idx, query_data in enumerate(self.queries):
            query = query_data["query"]
            query_id = query_data["id"]
            
            logger.info(f"[{system_name.upper()}] Query {idx+1}/{len(self.queries)}: {query_id}")
            
            try:
                # Medir tempo
                start_time = time.time()
                
                # Executar workflow (síncrono, não async)
                result = workflow.run(query, session_id=f"benchmark-{system_name}-{query_id}")
                
                end_time = time.time()
                latency = end_time - start_time
                
                # Extrair informações
                final_answer = result.get("final_answer", "")
                contexts = result.get("retrieved_contexts", [])
                
                # Converter contexts para strings
                context_strs = []
                if contexts:
                    for ctx in contexts[:10]:  # Top-10 docs
                        if hasattr(ctx, "page_content"):
                            context_strs.append(ctx.page_content)
                        elif isinstance(ctx, dict):
                            context_strs.append(ctx.get("content", ""))
                        elif isinstance(ctx, str):
                            context_strs.append(ctx)
                
                results.append({
                    "query_id": query_id,
                    "query": query,
                    "answer": final_answer,
                    "contexts": context_strs,
                    "latency": latency,
                    "category": query_data["category"],
                    "complexity": query_data["complexity"],
                    "difficulty": query_data["difficulty"]
                })
                
                logger.info(f"[{system_name.upper()}] ✅ {query_id} concluída em {latency:.2f}s")
                
            except Exception as e:
                logger.error(f"[{system_name.upper()}] ❌ Erro em {query_id}: {e}")
                results.append({
                    "query_id": query_id,
                    "query": query,
                    "answer": "",
                    "contexts": [],
                    "latency": -1,
                    "error": str(e),
                    "category": query_data["category"],
                    "complexity": query_data["complexity"],
                    "difficulty": query_data["difficulty"]
                })
        
        # Salvar resultados
        output_file = self.output_dir / f"{system_name}_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[BENCHMARK] {system_name} completo. Resultados salvos em {output_file}")
        
        return results
    
    def evaluate_with_ragas(
        self, 
        results: List[Dict[str, Any]], 
        system_name: str
    ) -> Dict[str, float]:
        """
        Avalia resultados usando métricas RAGAS.
        
        Args:
            results: Lista de resultados do sistema
            system_name: Nome do sistema
            
        Returns:
            Dict com métricas RAGAS agregadas
        """
        logger.info(f"[RAGAS] Avaliando {system_name} com RAGAS...")
        
        # Preparar dados para RAGAS
        # RAGAS espera: question, answer, contexts, ground_truth (opcional)
        
        data_dict = {
            "question": [],
            "answer": [],
            "contexts": []
        }
        
        for result in results:
            if result.get("error"):
                continue  # Skip queries com erro
            
            data_dict["question"].append(result["query"])
            data_dict["answer"].append(result["answer"])
            data_dict["contexts"].append(result["contexts"])
        
        # Criar Dataset
        dataset = Dataset.from_dict(data_dict)
        
        # Avaliar com RAGAS
        ragas_result = evaluate(
            dataset,
            metrics=[
                context_precision,  # Precisão dos contextos recuperados
                answer_relevancy,   # Relevância da resposta para query
                faithfulness,       # Fidelidade da resposta aos contextos
                context_recall      # Recall dos contextos (requer ground truth)
            ]
        )
        
        # Extrair métricas
        metrics = {
            "context_precision": ragas_result["context_precision"],
            "answer_relevancy": ragas_result["answer_relevancy"],
            "faithfulness": ragas_result["faithfulness"],
            "context_recall": ragas_result.get("context_recall", None)
        }
        
        logger.info(f"[RAGAS] {system_name} métricas:")
        for metric, value in metrics.items():
            if value is not None:
                logger.info(f"  - {metric}: {value:.3f}")
        
        # Salvar métricas
        metrics_file = self.output_dir / f"{system_name}_ragas_metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)
        
        return metrics
    
    def calculate_additional_metrics(
        self, 
        results: List[Dict[str, Any]], 
        system_name: str
    ) -> Dict[str, Any]:
        """
        Calcula métricas adicionais (latência, cost, etc).
        
        Args:
            results: Lista de resultados
            system_name: Nome do sistema
            
        Returns:
            Dict com métricas adicionais
        """
        logger.info(f"[METRICS] Calculando métricas adicionais para {system_name}")
        
        latencies = [r["latency"] for r in results if r["latency"] > 0]
        
        if not latencies:
            return {}
        
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)
        
        metrics = {
            "latency_mean": sum(latencies) / n,
            "latency_p50": latencies_sorted[int(n * 0.5)],
            "latency_p95": latencies_sorted[int(n * 0.95)],
            "latency_p99": latencies_sorted[int(n * 0.99)],
            "total_queries": len(results),
            "successful_queries": len(latencies),
            "failed_queries": len(results) - len(latencies),
            "success_rate": len(latencies) / len(results)
        }
        
        logger.info(f"[METRICS] {system_name}:")
        logger.info(f"  - Latency Mean: {metrics['latency_mean']:.2f}s")
        logger.info(f"  - Latency P50: {metrics['latency_p50']:.2f}s")
        logger.info(f"  - Latency P95: {metrics['latency_p95']:.2f}s")
        logger.info(f"  - Success Rate: {metrics['success_rate']:.1%}")
        
        return metrics
    
    def run_full_benchmark(self):
        """Executa benchmark completo: baseline + fase2a + avaliação."""
        
        logger.info("="*80)
        logger.info("[BENCHMARK] INICIANDO BENCHMARK FASE 2A")
        logger.info("="*80)
        
        # BASELINE: Sem otimizações
        logger.info("[STEP 1/4] Executando BASELINE...")
        baseline_results = self.run_system(
            system_name="baseline",
            enable_decomposition=False,
            enable_adaptive_rerank=False,
            enable_router=False
        )
        
        # FASE 2A: Com todas otimizações
        logger.info("[STEP 2/4] Executando FASE 2A...")
        fase2a_results = self.run_system(
            system_name="fase2a",
            enable_decomposition=True,
            enable_adaptive_rerank=True,
            enable_router=True
        )
        
        # Avaliar com RAGAS
        logger.info("[STEP 3/4] Avaliando com RAGAS...")
        baseline_ragas = self.evaluate_with_ragas(baseline_results, "baseline")
        fase2a_ragas = self.evaluate_with_ragas(fase2a_results, "fase2a")
        
        # Métricas adicionais
        logger.info("[STEP 4/4] Calculando métricas adicionais...")
        baseline_metrics = self.calculate_additional_metrics(baseline_results, "baseline")
        fase2a_metrics = self.calculate_additional_metrics(fase2a_results, "fase2a")
        
        # Gerar relatório comparativo
        self.generate_comparative_report(
            baseline_ragas, baseline_metrics,
            fase2a_ragas, fase2a_metrics
        )
        
        logger.info("="*80)
        logger.info("[BENCHMARK] COMPLETO!")
        logger.info("="*80)
    
    def generate_comparative_report(
        self,
        baseline_ragas: Dict[str, float],
        baseline_metrics: Dict[str, Any],
        fase2a_ragas: Dict[str, float],
        fase2a_metrics: Dict[str, Any]
    ):
        """Gera relatório comparativo em Markdown."""
        
        report_file = self.output_dir / "comparative_report.md"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Benchmark Fase 2A - Relatório Comparativo\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Métricas RAGAS
            f.write("## 📊 Métricas RAGAS\n\n")
            f.write("| Métrica | Baseline | Fase 2A | Melhoria |\n")
            f.write("|---------|----------|---------|----------|\n")
            
            for metric in baseline_ragas:
                if baseline_ragas[metric] is not None and fase2a_ragas[metric] is not None:
                    baseline_val = baseline_ragas[metric]
                    fase2a_val = fase2a_ragas[metric]
                    improvement = ((fase2a_val - baseline_val) / baseline_val) * 100
                    
                    f.write(f"| {metric} | {baseline_val:.3f} | {fase2a_val:.3f} | ")
                    if improvement > 0:
                        f.write(f"✅ +{improvement:.1f}% |\n")
                    else:
                        f.write(f"❌ {improvement:.1f}% |\n")
            
            f.write("\n")
            
            # Métricas de Latência
            f.write("## ⏱️ Métricas de Latência\n\n")
            f.write("| Métrica | Baseline | Fase 2A | Diferença |\n")
            f.write("|---------|----------|---------|----------|\n")
            
            for metric in ["latency_mean", "latency_p50", "latency_p95"]:
                baseline_val = baseline_metrics[metric]
                fase2a_val = fase2a_metrics[metric]
                diff = fase2a_val - baseline_val
                
                f.write(f"| {metric} | {baseline_val:.2f}s | {fase2a_val:.2f}s | ")
                if diff > 0:
                    f.write(f"⚠️ +{diff:.2f}s |\n")
                else:
                    f.write(f"✅ {diff:.2f}s |\n")
            
            f.write("\n")
            
            # Taxa de Sucesso
            f.write("## ✅ Taxa de Sucesso\n\n")
            f.write(f"- **Baseline**: {baseline_metrics['success_rate']:.1%} ")
            f.write(f"({baseline_metrics['successful_queries']}/{baseline_metrics['total_queries']})\n")
            f.write(f"- **Fase 2A**: {fase2a_metrics['success_rate']:.1%} ")
            f.write(f"({fase2a_metrics['successful_queries']}/{fase2a_metrics['total_queries']})\n\n")
        
        logger.info(f"[REPORT] Relatório comparativo salvo em {report_file}")


def main():
    """Main function."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Fase 2A - Baseline vs Otimizado")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None,
        help="Limitar número de queries (padrão: todas as 50)"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Modo piloto: executar apenas 5 queries"
    )
    
    args = parser.parse_args()
    
    # Definir limite
    limit = None
    if args.pilot:
        limit = 5
        logger.info("[BENCHMARK] MODO PILOTO ativado (5 queries)")
    elif args.limit:
        limit = args.limit
        logger.info(f"[BENCHMARK] Limite customizado: {limit} queries")
    
    # Paths
    queries_file = Path("tests/benchmark_queries.json")
    output_dir = Path("tests/benchmark_fase2a/results")
    
    # Criar benchmark
    benchmark = BSCBenchmark(queries_file, output_dir, limit=limit)
    
    # Executar
    benchmark.run_full_benchmark()


if __name__ == "__main__":
    main()

