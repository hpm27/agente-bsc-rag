# Benchmark Fase 2A - Relatório Executivo
**Data:** 2025-10-15 01:48:15
**Total Queries:** 50

---

## 📊 RESUMO EXECUTIVO

```
✅ Queries Executadas: 50
✅ Taxa de Sucesso: 100.0%
⏱️  Latência Média: 124.66s (Baseline: 128.71s)
🚀 Melhoria: 3.1% mais rápido
```

## ⏱️ MÉTRICAS DE LATÊNCIA

| Métrica | Baseline | Fase 2A | Diferença | Melhoria |
|---------|----------|---------|-----------|----------|
| Média | 128.71s | 124.66s | +4.05s | ✅ +3.1% |
| Mediana (P50) | 93.11s | 90.10s | +3.00s | ✅ +3.2% |
| P95 | 252.32s | 268.81s | -16.49s | ⚠️ -6.5% |
| P99 | 327.09s | 355.14s | -28.05s | ⚠️ -8.6% |
| Mínimo | 44.28s | 42.30s | +1.98s | ✅ +4.5% |
| Máximo | 358.41s | 409.41s | -51.00s | ⚠️ -14.2% |

## 📈 MÉTRICAS RAGAS (Qualidade)

| Métrica | Baseline | Fase 2A | Melhoria |
|---------|----------|---------|----------|
| Context Precision | 0.000 | 0.000 | ❌ +0.0% |
| Answer Relevancy | 0.889 | 0.907 | ✅ +2.1% |
| Faithfulness | 0.974 | 0.968 | ❌ -0.6% |

## 📊 ANÁLISE POR CATEGORIA

| Categoria | Baseline (média) | Fase 2A (média) | Melhoria |
|-----------|------------------|-----------------|----------|
| avancada_multihop | 224.54s | 224.31s | ✅ +0.1% |
| comparativa | 121.74s | 118.37s | ✅ +2.8% |
| conceitual_complexa | 95.77s | 87.66s | ✅ +8.5% |
| multi_perspectiva | 105.21s | 101.01s | ✅ +4.0% |
| relacional | 97.07s | 93.49s | ✅ +3.7% |
| simples_factual | 64.57s | 57.72s | ✅ +10.6% |

## 📊 VISUALIZAÇÕES

![Latency Boxplot](latency_boxplot.png)

![Latency by Category](latency_by_category.png)

![RAGAS Metrics](ragas_metrics.png)

