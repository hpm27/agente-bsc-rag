

# Benchmark Fase 2A - Documentação Completa

**Objetivo:** Avaliar ROI das técnicas RAG avançadas implementadas na Fase 2A.

---

## [EMOJI] Estrutura

```
tests/benchmark_fase2a/
├── run_benchmark.py          # Script principal de execução
├── analyze_results.py        # Script de análise e visualização
├── results/                   # Resultados gerados
│   ├── baseline_results.json
│   ├── fase2a_results.json
│   ├── baseline_ragas_metrics.json
│   ├── fase2a_ragas_metrics.json
│   ├── comparative_report.md
│   ├── executive_report.md
│   ├── latency_boxplot.png
│   ├── latency_by_category.png
│   └── ragas_metrics.png
└── README.md                  # Este arquivo
```

---

## [EMOJI] Como Executar

### 1. Benchmark Completo (50 queries)

```bash
cd "D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
.\venv\Scripts\python.exe tests\benchmark_fase2a\run_benchmark.py
```

**Tempo:** ~2.5-3 horas
**Custo:** ~$1.60 USD

### 2. Teste Piloto (5 queries)

```bash
.\venv\Scripts\python.exe tests\benchmark_fase2a\run_benchmark.py --pilot
```

**Tempo:** ~10-15 minutos
**Custo:** ~$0.16 USD

### 3. Customizado (N queries)

```bash
.\venv\Scripts\python.exe tests\benchmark_fase2a\run_benchmark.py --limit 20
```

---

## [EMOJI] Análise de Resultados

Após o benchmark terminar:

```bash
.\venv\Scripts\python.exe tests\benchmark_fase2a\analyze_results.py
```

**Gera:**
- `executive_report.md` - Relatório executivo
- `latency_boxplot.png` - Comparação de latências
- `latency_by_category.png` - Latências por tipo de query
- `ragas_metrics.png` - Métricas de qualidade RAGAS

---

## [EMOJI] O Que é Avaliado

### Baseline (Sem Otimizações)
- [ERRO] Query Decomposition desabilitada
- [ERRO] Adaptive Re-ranking desabilitado
- [ERRO] Router Inteligente desabilitado

### Fase 2A (Com Otimizações)
- [OK] Query Decomposition ativa
- [OK] Adaptive Re-ranking ativo
- [OK] Router Inteligente ativo

---

## [EMOJI] Métricas Coletadas

### 1. Latência
- Mean, Median (P50)
- P95, P99
- Por categoria de query

### 2. RAGAS (Qualidade)
- **Context Precision** - Precisão dos contextos recuperados
- **Answer Relevancy** - Relevância da resposta
- **Faithfulness** - Fidelidade aos documentos

### 3. Taxa de Sucesso
- Queries bem-sucedidas vs falhadas

---

## [EMOJI] Dataset de Queries

**Arquivo:** `tests/benchmark_queries.json`

**Distribuição:**
- 15 queries **simples** (factuais diretas)
- 20 queries **moderadas** (conceituais, comparativas)
- 15 queries **complexas** (multi-hop, relacionais)

**Total:** 50 queries BSC variadas

---

## [EMOJI] Troubleshooting

### Problema: Benchmark falha com erro de import

**Solução:** Verificar que todas dependências estão instaladas:
```bash
pip install ragas datasets matplotlib seaborn pandas numpy
```

### Problema: RAGAS não gera métricas

**Causa:** Queries sem `answer` ou `contexts` vazios.
**Solução:** Verificar que workflow retorna `final_response` e `agent_responses`.

### Problema: Latências muito altas (>300s)

**Causa:** Muitas queries complexas ativando 4 agentes.
**Ação:** Isso é esperado. Queries complexas podem levar 3-5 min.

---

## [EMOJI] Interpretação de Resultados

### Latência

- **Melhoria positiva** (+X%): Fase 2A mais rápida (bom!)
- **Trade-off negativo** (-X%): Fase 2A mais lenta (esperado com features adicionais)

**Aceitável:** -10% a -20% mais lento com melhorias significativas em qualidade.

### RAGAS Metrics

- **Context Precision > 0.7**: Boa precisão de retrieval
- **Answer Relevancy > 0.8**: Respostas muito relevantes
- **Faithfulness > 0.85**: Alta fidelidade aos documentos

**Target Fase 2A:**
- Context Precision: +10-15% vs baseline
- Answer Relevancy: +20-30% vs baseline
- Faithfulness: +15-25% vs baseline

---

## [EMOJI] Lições Aprendidas

### 1. Query Decomposition

**Quando funciona bem:**
- Queries complexas multi-parte
- Múltiplas perspectivas BSC
- Relacionais ("Como X impacta Y?")

**ROI Esperado:** +30-50% answer quality

### 2. Adaptive Re-ranking

**Quando funciona bem:**
- Diversidade de fontes importante
- Evitar docs repetidos
- Metadata boosting

**ROI Esperado:** +15-25% precision

### 3. Router Inteligente

**Quando funciona bem:**
- Mix de queries simples e complexas
- Otimização de latência por tipo

**ROI Esperado:** -20% latência média (queries simples muito mais rápidas)

---

## [EMOJI] Próximos Passos

Após análise dos resultados:

1. [OK] Validar que targets foram atingidos
2. [EMOJI] Documentar lições em `docs/lessons/`
3. [EMOJI] Atualizar `docs/techniques/` com dados reais
4. [EMOJI] Decidir: Fase 2B (Self-RAG, CRAG) ou ajustes

---

## [EMOJI] Referências

- **RAGAS Framework:** https://docs.ragas.io/
- **Plano Fase 2:** `.cursor/plans/fase-2-rag-avancado.plan.md`
- **Router Central:** `.cursor/rules/rag-bsc-core.mdc`

---

**Última Atualização:** 2025-10-14
**Status:** [OK] Pronto para uso
