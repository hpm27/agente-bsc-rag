# Benchmark Report - Query Decomposition vs Baseline

**Data:** 2025-10-14 12:56:50
**Queries Testadas:** 10
**Configuração:** gpt-4o-mini | Cohere Rerank | Hybrid Search (BM25 + Qdrant)

---

## [EMOJI] Métricas Agregadas

### Recall@10

| Métrica | Baseline | Decomposition | Improvement |
|---------|----------|---------------|-------------|
| **Mean** | 0.00% | 0.00% | **+0.0%** |
| **Median** | 0.00% | 0.00% | +0.0% |
| **Min** | 0.00% | 0.00% | - |
| **Max** | 0.00% | 0.00% | - |

### Precision@5

| Métrica | Baseline | Decomposition | Improvement |
|---------|----------|---------------|-------------|
| **Mean** | 0.00% | 0.00% | **+0.0%** |
| **Median** | 0.00% | 0.00% | +0.0% |
| **Min** | 0.00% | 0.00% | - |
| **Max** | 0.00% | 0.00% | - |

### Latência (segundos)

| Métrica | Baseline | Decomposition | Overhead |
|---------|----------|---------------|----------|
| **Mean** | 1.49s | 5.74s | **+4.25s** |
| **Median (P50)** | 1.45s | 5.62s | +4.17s |
| **P95** | 2.00s | 8.49s | - |

### Query Decomposition Stats

| Métrica | Valor |
|---------|-------|
| **Heurística Accuracy** | **100.0%** |
| **Queries Decompostas** | 10 / 10 |
| **Total Sub-queries Geradas** | 40 |
| **Média Sub-queries (quando decompostas)** | 4.0 |

---

## [OK] Critérios de Sucesso

| Critério | Target | Real | Status |
|----------|--------|------|--------|
| **Recall@10 Improvement** | > +30% | +0.0% | [ERRO] FAIL |
| **Precision@5 Improvement** | > +25% | +0.0% | [ERRO] FAIL |
| **Latência Adicional** | < 3s | +4.25s | [ERRO] FAIL |
| **Heurística Accuracy** | > 80% | 100.0% | [OK] PASS |

---

## [EMOJI] Resultados Detalhados

### Por Query

| Query ID | Category | Recall Baseline | Recall Decomp | Δ | Precision Baseline | Precision Decomp | Δ |
|----------|----------|-----------------|---------------|---|-------------------|------------------|---|
| multi_persp_001 | multi_perspectiva | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| multi_persp_002 | multi_perspectiva | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| multi_persp_003 | multi_perspectiva | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| multi_persp_004 | multi_perspectiva | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| multi_persp_005 | multi_perspectiva | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| relacional_001 | relacional | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| relacional_002 | relacional | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| relacional_003 | relacional | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| relacional_004 | relacional | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |
| relacional_005 | relacional | 0.00% | 0.00% | +0.00% | 0.00% | 0.00% | +0.00% |

---

## [EMOJI] Conclusões

**Recall@10:**
- [ERRO] Baseline teve melhor recall
- [ERRO] Target de +30% NÃO foi atingido

**Precision@5:**
- [ERRO] Baseline teve melhor precision
- [ERRO] Target de +25% NÃO foi atingido

**Latência:**
- Overhead médio: +4.25s
- [ERRO] Acima do target de 3s

**Heurística:**
- Accuracy: 100.0%
- [OK] Target de >80% foi ATINGIDO

**Recomendação Final:**

[ERRO] **NO-GO** - Query Decomposition precisa de ajustes antes de produção.

Ajustes recomendados:
- Ajustar decomposição para gerar sub-queries mais diversas
- Melhorar RRF ou adicionar re-ranking adicional
- Otimizar chamadas LLM ou usar modelo mais rápido

---

**Gerado por:** `tests/benchmark_query_decomposition.py`
**Configuração:** Hybrid Search + Cohere Rerank + gpt-4o-mini
