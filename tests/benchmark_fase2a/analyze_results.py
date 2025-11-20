"""
Script de análise de resultados do Benchmark Fase 2A.

Processa baseline_results.json e fase2a_results.json para gerar:
- Métricas agregadas (latência, success rate)
- Comparação baseline vs fase2a
- Gráficos (boxplot, barras, scatter)
- Relatório executivo em Markdown

Uso:
    python tests/benchmark_fase2a/analyze_results.py
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Configurar estilo de gráficos
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10


def format_doc_reference(metadata: dict[str, Any]) -> str:
    """
    Formata referência de documento para relatórios.

    Usa document_title, authors, year quando disponíveis para criar
    citações acadêmicas profissionais ao invés de mostrar filenames.

    Args:
        metadata: Metadados do documento (do Qdrant payload)

    Returns:
        Referência formatada do documento

    Examples:
        >>> # Com metadados completos:
        >>> format_doc_reference({
        ...     "document_title": "The Balanced Scorecard",
        ...     "authors": ["Robert S. Kaplan", "David P. Norton"],
        ...     "year": 1996
        ... })
        "The Balanced Scorecard (Kaplan & Norton, 1996)"

        >>> # Com título apenas:
        >>> format_doc_reference({"document_title": "Strategy Maps", "year": 2004})
        "Strategy Maps (2004)"

        >>> # Fallback para source:
        >>> format_doc_reference({"source": "doc_filename.pdf"})
        "doc_filename.pdf"
    """
    # Extrair campos
    title = metadata.get("document_title", "")
    source = metadata.get("source", "Desconhecido")
    authors = metadata.get("authors", [])
    year = metadata.get("year")

    # Usar título se disponível, senão filename
    display_name = title if title else source

    # Formatar autores (primeiros 2 + et al se >2)
    if authors and len(authors) > 0:
        if len(authors) == 1:
            authors_str = authors[0].split()[-1]  # Último nome
        elif len(authors) == 2:
            authors_str = f"{authors[0].split()[-1]} & {authors[1].split()[-1]}"
        else:
            authors_str = f"{authors[0].split()[-1]} et al."

        # Com autores e ano
        if year:
            return f"{display_name} ({authors_str}, {year})"
        # Com autores sem ano
        return f"{display_name} ({authors_str})"

    # Sem autores, mas com ano
    if year:
        return f"{display_name} ({year})"

    # Apenas título/source
    return display_name


class BenchmarkAnalyzer:
    """Analisador de resultados do benchmark Fase 2A."""

    def __init__(self, results_dir: Path):
        """
        Inicializa analisador.

        Args:
            results_dir: Diretório com resultados (baseline_results.json, fase2a_results.json)
        """
        self.results_dir = results_dir

        # Carregar resultados
        with open(results_dir / "baseline_results.json", encoding="utf-8") as f:
            self.baseline_results = json.load(f)

        with open(results_dir / "fase2a_results.json", encoding="utf-8") as f:
            self.fase2a_results = json.load(f)

        # Carregar métricas RAGAS se existirem
        self.baseline_ragas = self._load_ragas("baseline_ragas_metrics.json")
        self.fase2a_ragas = self._load_ragas("fase2a_ragas_metrics.json")

        print(f"[OK] Carregados {len(self.baseline_results)} queries baseline")
        print(f"[OK] Carregados {len(self.fase2a_results)} queries fase2a")

    def _load_ragas(self, filename: str) -> dict:
        """Carrega métricas RAGAS se existirem."""
        filepath = self.results_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return {}

    def calculate_latency_metrics(self, results: list[dict]) -> dict[str, float]:
        """Calcula métricas de latência."""
        latencies = [r["latency"] for r in results if r.get("latency", -1) > 0]

        if not latencies:
            return {}

        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        return {
            "count": len(results),
            "successful": len(latencies),
            "failed": len(results) - len(latencies),
            "success_rate": len(latencies) / len(results),
            "mean": np.mean(latencies),
            "median": np.median(latencies),
            "std": np.std(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "p25": np.percentile(latencies, 25),
            "p50": np.percentile(latencies, 50),
            "p75": np.percentile(latencies, 75),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99),
        }

    def calculate_metrics_by_category(self, results: list[dict]) -> dict[str, dict]:
        """Calcula métricas por categoria de query."""
        categories = {}

        for result in results:
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        metrics_by_cat = {}
        for cat, cat_results in categories.items():
            metrics_by_cat[cat] = self.calculate_latency_metrics(cat_results)

        return metrics_by_cat

    def plot_latency_comparison(self):
        """Gera boxplot de latências baseline vs fase2a."""
        baseline_latencies = [
            r["latency"] for r in self.baseline_results if r.get("latency", -1) > 0
        ]
        fase2a_latencies = [r["latency"] for r in self.fase2a_results if r.get("latency", -1) > 0]

        fig, ax = plt.subplots(figsize=(10, 6))

        data = [baseline_latencies, fase2a_latencies]
        labels = ["Baseline", "Fase 2A"]

        bp = ax.boxplot(data, labels=labels, patch_artist=True)

        # Cores
        colors = ["#ff9999", "#66b3ff"]
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)

        ax.set_ylabel("Latência (segundos)")
        ax.set_title("Comparação de Latência: Baseline vs Fase 2A")
        ax.grid(axis="y", alpha=0.3)

        # Adicionar médias
        means = [np.mean(baseline_latencies), np.mean(fase2a_latencies)]
        ax.plot([1, 2], means, "D", color="red", markersize=8, label="Média")
        ax.legend()

        plt.tight_layout()
        plt.savefig(self.results_dir / "latency_boxplot.png", dpi=300)
        print("[OK] Gráfico salvo: latency_boxplot.png")
        plt.close()

    def plot_latency_by_category(self):
        """Gera gráfico de barras de latência por categoria."""
        baseline_by_cat = self.calculate_metrics_by_category(self.baseline_results)
        fase2a_by_cat = self.calculate_metrics_by_category(self.fase2a_results)

        categories = list(baseline_by_cat.keys())
        baseline_means = [baseline_by_cat[cat]["mean"] for cat in categories]
        fase2a_means = [fase2a_by_cat[cat]["mean"] for cat in categories]

        x = np.arange(len(categories))
        width = 0.35

        fig, ax = plt.subplots(figsize=(14, 6))

        bars1 = ax.bar(x - width / 2, baseline_means, width, label="Baseline", color="#ff9999")
        bars2 = ax.bar(x + width / 2, fase2a_means, width, label="Fase 2A", color="#66b3ff")

        ax.set_ylabel("Latência Média (s)")
        ax.set_title("Latência Média por Categoria de Query")
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        # Adicionar valores nas barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.1f}s",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        plt.tight_layout()
        plt.savefig(self.results_dir / "latency_by_category.png", dpi=300)
        print("[OK] Gráfico salvo: latency_by_category.png")
        plt.close()

    def plot_ragas_metrics(self):
        """Gera gráfico de métricas RAGAS."""
        if not self.baseline_ragas or not self.fase2a_ragas:
            print("[WARN] Métricas RAGAS não disponíveis")
            return

        metrics = ["context_precision", "answer_relevancy", "faithfulness"]
        baseline_values = [self.baseline_ragas.get(m, 0) for m in metrics]
        fase2a_values = [self.fase2a_ragas.get(m, 0) for m in metrics]

        x = np.arange(len(metrics))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))

        bars1 = ax.bar(x - width / 2, baseline_values, width, label="Baseline", color="#ff9999")
        bars2 = ax.bar(x + width / 2, fase2a_values, width, label="Fase 2A", color="#66b3ff")

        ax.set_ylabel("Score")
        ax.set_title("Métricas RAGAS: Baseline vs Fase 2A")
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace("_", " ").title() for m in metrics])
        ax.legend()
        ax.set_ylim(0, 1.1)
        ax.grid(axis="y", alpha=0.3)

        # Adicionar valores
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.3f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        plt.tight_layout()
        plt.savefig(self.results_dir / "ragas_metrics.png", dpi=300)
        print("[OK] Gráfico salvo: ragas_metrics.png")
        plt.close()

    def generate_summary_report(self):
        """Gera relatório executivo em Markdown."""
        baseline_metrics = self.calculate_latency_metrics(self.baseline_results)
        fase2a_metrics = self.calculate_latency_metrics(self.fase2a_results)

        # Calcular melhorias
        latency_improvement = (
            (baseline_metrics["mean"] - fase2a_metrics["mean"]) / baseline_metrics["mean"]
        ) * 100
        p95_improvement = (
            (baseline_metrics["p95"] - fase2a_metrics["p95"]) / baseline_metrics["p95"]
        ) * 100

        report = []
        report.append("# Benchmark Fase 2A - Relatório Executivo\n")
        report.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total Queries:** {len(self.baseline_results)}\n\n")
        report.append("---\n\n")

        # Resumo Executivo
        report.append("## [EMOJI] RESUMO EXECUTIVO\n\n")
        report.append("```\n")
        report.append(f"[OK] Queries Executadas: {baseline_metrics['count']}\n")
        report.append(f"[OK] Taxa de Sucesso: {baseline_metrics['success_rate']:.1%}\n")
        report.append(
            f"[TIMER]  Latência Média: {fase2a_metrics['mean']:.2f}s (Baseline: {baseline_metrics['mean']:.2f}s)\n"
        )

        if latency_improvement > 0:
            report.append(f"[EMOJI] Melhoria: {latency_improvement:.1f}% mais rápido\n")
        else:
            report.append(
                f"[WARN]  Trade-off: {abs(latency_improvement):.1f}% mais lento (features adicionais)\n"
            )

        report.append("```\n\n")

        # Métricas de Latência
        report.append("## [TIMER] MÉTRICAS DE LATÊNCIA\n\n")
        report.append("| Métrica | Baseline | Fase 2A | Diferença | Melhoria |\n")
        report.append("|---------|----------|---------|-----------|----------|\n")

        metrics_to_compare = [
            ("Média", "mean"),
            ("Mediana (P50)", "p50"),
            ("P95", "p95"),
            ("P99", "p99"),
            ("Mínimo", "min"),
            ("Máximo", "max"),
        ]

        for label, metric in metrics_to_compare:
            baseline_val = baseline_metrics[metric]
            fase2a_val = fase2a_metrics[metric]
            diff = baseline_val - fase2a_val
            improvement = (diff / baseline_val) * 100

            emoji = "[OK]" if improvement > 0 else "[WARN]"
            report.append(
                f"| {label} | {baseline_val:.2f}s | {fase2a_val:.2f}s | "
                f"{diff:+.2f}s | {emoji} {improvement:+.1f}% |\n"
            )

        report.append("\n")

        # Métricas RAGAS
        if self.baseline_ragas and self.fase2a_ragas:
            report.append("## [EMOJI] MÉTRICAS RAGAS (Qualidade)\n\n")
            report.append("| Métrica | Baseline | Fase 2A | Melhoria |\n")
            report.append("|---------|----------|---------|----------|\n")

            for metric in ["context_precision", "answer_relevancy", "faithfulness"]:
                baseline_val = self.baseline_ragas.get(metric, 0)
                fase2a_val = self.fase2a_ragas.get(metric, 0)
                improvement = (
                    ((fase2a_val - baseline_val) / baseline_val) * 100 if baseline_val > 0 else 0
                )

                emoji = "[OK]" if improvement > 0 else "[ERRO]"
                report.append(
                    f"| {metric.replace('_', ' ').title()} | {baseline_val:.3f} | "
                    f"{fase2a_val:.3f} | {emoji} {improvement:+.1f}% |\n"
                )

            report.append("\n")

        # Por Categoria
        report.append("## [EMOJI] ANÁLISE POR CATEGORIA\n\n")
        baseline_by_cat = self.calculate_metrics_by_category(self.baseline_results)
        fase2a_by_cat = self.calculate_metrics_by_category(self.fase2a_results)

        report.append("| Categoria | Baseline (média) | Fase 2A (média) | Melhoria |\n")
        report.append("|-----------|------------------|-----------------|----------|\n")

        for category in sorted(baseline_by_cat.keys()):
            baseline_mean = baseline_by_cat[category]["mean"]
            fase2a_mean = fase2a_by_cat[category]["mean"]
            improvement = ((baseline_mean - fase2a_mean) / baseline_mean) * 100

            emoji = "[OK]" if improvement > 0 else "[WARN]"
            report.append(
                f"| {category} | {baseline_mean:.2f}s | {fase2a_mean:.2f}s | "
                f"{emoji} {improvement:+.1f}% |\n"
            )

        report.append("\n")

        # Visualizações
        report.append("## [EMOJI] VISUALIZAÇÕES\n\n")
        report.append("![Latency Boxplot](latency_boxplot.png)\n\n")
        report.append("![Latency by Category](latency_by_category.png)\n\n")

        if self.baseline_ragas and self.fase2a_ragas:
            report.append("![RAGAS Metrics](ragas_metrics.png)\n\n")

        # Salvar relatório
        report_file = self.results_dir / "executive_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.writelines(report)

        print("[OK] Relatório executivo salvo: executive_report.md")

    def run_full_analysis(self):
        """Executa análise completa."""
        print("\n" + "=" * 80)
        print("ANÁLISE DE RESULTADOS - BENCHMARK FASE 2A")
        print("=" * 80 + "\n")

        print("[STEP 1/4] Gerando gráfico de latências...")
        self.plot_latency_comparison()

        print("[STEP 2/4] Gerando gráfico por categoria...")
        self.plot_latency_by_category()

        print("[STEP 3/4] Gerando gráfico de métricas RAGAS...")
        self.plot_ragas_metrics()

        print("[STEP 4/4] Gerando relatório executivo...")
        self.generate_summary_report()

        print("\n" + "=" * 80)
        print("ANÁLISE COMPLETA!")
        print("=" * 80 + "\n")


def main():
    """Main function."""
    results_dir = Path("tests/benchmark_fase2a/results")

    if not (results_dir / "baseline_results.json").exists():
        print("[ERRO] baseline_results.json não encontrado")
        return

    if not (results_dir / "fase2a_results.json").exists():
        print("[ERRO] fase2a_results.json não encontrado")
        return

    analyzer = BenchmarkAnalyzer(results_dir)
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
