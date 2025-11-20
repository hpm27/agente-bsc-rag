"""
Script para avaliar resultados existentes com RAGAS.

Carrega os resultados baseline e fase2a já salvos e executa apenas
a avaliação RAGAS + geração de relatório.

Uso:
    python tests/benchmark_fase2a/evaluate_existing_results.py
"""

import json
import sys
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datasets import Dataset
from loguru import logger
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness

# Diretórios
RESULTS_DIR = Path("tests/benchmark_fase2a/results")


def load_results(system_name: str) -> list:
    """Carrega resultados de um sistema."""
    results_file = RESULTS_DIR / f"{system_name}_results.json"

    if not results_file.exists():
        logger.error(f"[ERRO] Arquivo {results_file} não encontrado")
        return []

    with open(results_file, encoding="utf-8") as f:
        results = json.load(f)

    logger.info(f"[OK] Carregado {len(results)} resultados de {system_name}")
    return results


def evaluate_with_ragas(results: list, system_name: str) -> dict:
    """
    Avaliar resultados com RAGAS.

    Args:
        results: Lista de resultados do sistema
        system_name: Nome do sistema

    Returns:
        Dict com métricas RAGAS agregadas
    """
    logger.info(f"[RAGAS] Avaliando {system_name} com RAGAS...")

    # Preparar dados para RAGAS
    data_dict = {"question": [], "answer": [], "contexts": []}

    for result in results:
        if result.get("error"):
            continue  # Skip queries com erro

        # Skip queries sem resposta
        if not result.get("answer") or not result.get("contexts"):
            logger.warning(f"[SKIP] Query {result.get('query_id')} sem answer/contexts")
            continue

        data_dict["question"].append(result["query"])
        data_dict["answer"].append(result["answer"])
        data_dict["contexts"].append(result["contexts"])

    logger.info(f"[RAGAS] {len(data_dict['question'])} queries válidas para avaliação")

    # Criar Dataset
    dataset = Dataset.from_dict(data_dict)

    # Avaliar com RAGAS
    # NOTA: Usando apenas métricas que NÃO exigem ground truth (reference)
    ragas_result = evaluate(
        dataset,
        metrics=[
            answer_relevancy,  # Relevância da resposta para query
            faithfulness,  # Fidelidade da resposta aos contextos
        ],
    )

    # Extrair métricas (calcular média se for lista)
    def get_metric_value(metric_data):
        """Extrai valor da métrica (média se for lista)."""
        if isinstance(metric_data, list):
            # Filtrar valores válidos (não-None, não-NaN)
            valid_values = [
                v for v in metric_data if v is not None and not (isinstance(v, float) and v != v)
            ]
            return sum(valid_values) / len(valid_values) if valid_values else 0.0
        return float(metric_data) if metric_data is not None else 0.0

    metrics = {
        "answer_relevancy": get_metric_value(ragas_result["answer_relevancy"]),
        "faithfulness": get_metric_value(ragas_result["faithfulness"]),
    }

    logger.info(f"[RAGAS] {system_name} métricas:")
    for metric, value in metrics.items():
        logger.info(f"  - {metric}: {value:.3f}")

    # Salvar métricas
    metrics_file = RESULTS_DIR / f"{system_name}_ragas_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"[OK] Métricas RAGAS salvas em {metrics_file}")

    return metrics


def main():
    """Função principal."""
    logger.info("[INICIO] Avaliação RAGAS de resultados existentes")
    logger.info("=" * 80)

    # Carregar resultados
    baseline_results = load_results("baseline")
    fase2a_results = load_results("fase2a")

    if not baseline_results or not fase2a_results:
        logger.error("[ERRO] Resultados não encontrados. Execute o benchmark primeiro.")
        return

    # Avaliar com RAGAS
    logger.info("\n[STEP 1/3] Avaliando baseline com RAGAS...")
    baseline_metrics = evaluate_with_ragas(baseline_results, "baseline")

    logger.info("\n[STEP 2/3] Avaliando fase2a com RAGAS...")
    fase2a_metrics = evaluate_with_ragas(fase2a_results, "fase2a")

    # Comparação
    logger.info("\n[STEP 3/3] Comparação de métricas:")
    logger.info("=" * 80)

    for metric in ["answer_relevancy", "faithfulness"]:
        baseline_val = baseline_metrics[metric]
        fase2a_val = fase2a_metrics[metric]
        diff = fase2a_val - baseline_val
        pct = (diff / baseline_val) * 100 if baseline_val > 0 else 0

        logger.info(f"{metric}:")
        logger.info(f"  Baseline: {baseline_val:.3f}")
        logger.info(f"  Fase2A:   {fase2a_val:.3f}")
        logger.info(f"  Delta:    {diff:+.3f} ({pct:+.1f}%)")
        logger.info("")

    logger.info("[FIM] Avaliação RAGAS concluída com sucesso!")
    logger.info("\nPróximo passo:")
    logger.info("  python tests/benchmark_fase2a/analyze_results.py")


if __name__ == "__main__":
    main()
