# Benchmark Report - Query Decomposition vs Baseline

**Data:** 2025-10-14 12:56:50  
**Queries Testadas:** 10  
**Configuração:** gpt-4o-mini | Cohere Rerank | Hybrid Search (BM25 + Qdrant)

---

## 📊 Métricas Agregadas

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

## ✅ Critérios de Sucesso

| Critério | Target | Real | Status |
|----------|--------|------|--------|
| **Recall@10 Improvement** | > +30% | +0.0% | ❌ FAIL |
| **Precision@5 Improvement** | > +25% | +0.0% | ❌ FAIL |
| **Latência Adicional** | < 3s | +4.25s | ❌ FAIL |
| **Heurística Accuracy** | > 80% | 100.0% | ✅ PASS |

---

## 📋 Resultados Detalhados

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

## 🎓 Conclusões

**Recall@10:**
- ❌ Baseline teve melhor recall
- ❌ Target de +30% NÃO foi atingido

**Precision@5:**
- ❌ Baseline teve melhor precision
- ❌ Target de +25% NÃO foi atingido

**Latência:**
- Overhead médio: +4.25s
- ❌ Acima do target de 3s

**Heurística:**
- Accuracy: 100.0%
- ✅ Target de >80% foi ATINGIDO

**Recomendação Final:**

❌ **NO-GO** - Query Decomposition precisa de ajustes antes de produção.

Ajustes recomendados:
- Ajustar decomposição para gerar sub-queries mais diversas
- Melhorar RRF ou adicionar re-ranking adicional
- Otimizar chamadas LLM ou usar modelo mais rápido

---

**Gerado por:** `tests/benchmark_query_decomposition.py`  
**Configuração:** Hybrid Search + Cohere Rerank + gpt-4o-mini
