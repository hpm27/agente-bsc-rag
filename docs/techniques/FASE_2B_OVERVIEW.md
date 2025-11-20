# Fase 2B - Técnicas RAG Avançadas: Self-RAG vs CRAG

**Data:** 2025-10-14
**Status:** [EMOJI] Planejamento Completo
**Decisão:** Aguardando Benchmark Fase 2A

---

## [EMOJI] VISÃO GERAL

Fase 2B introduz duas técnicas RAG avançadas complementares:

1. **Self-RAG** - Self-reflection para reduzir alucinações
2. **CRAG** - Corrective retrieval para melhorar qualidade

---

## [EMOJI] SELF-RAG - Self-Reflective RAG

### O Que É?

Sistema RAG que **auto-avalia** suas próprias decisões e outputs usando LLM como "crítico interno".

### Como Funciona?

```
Query -> [Precisa retrieval?]
        ├─ SIM -> Retrieve -> [Docs relevantes?]
        │                   ├─ SIM -> Keep
        │                   └─ NÃO -> Discard
        │        -> Generate -> [Suportado por docs?]
        │                     ├─ SIM -> Return
        │                     └─ NÃO -> Re-generate
        └─ NÃO -> Generate direto
```

### Componentes

1. **Retrieval Decision** - LLM decide SE query precisa de retrieval
2. **Document Grading** - Filtra docs irrelevantes
3. **Answer Grading** - Verifica suporte factual
4. **Hallucination Check** - Detecta informação inventada

### Reflection Tokens

Tokens especiais que guiam o comportamento:

- `[Retrieve]` / `[No Retrieve]`
- `[Relevant]` / `[Irrelevant]`
- `[Supported]` / `[Partially]` / `[Not Supported]`
- `[Useful]` / `[Not Useful]`

### Quando Usar?

[OK] **BOM para:**
- Alta necessidade de acurácia factual
- Hallucination rate > 10%
- Queries complexas com múltiplas partes
- Domínios onde inventar informação é crítico (médico, legal, financeiro)

[ERRO] **RUIM para:**
- Latência crítica (<10s requirement)
- Faithfulness já > 0.90
- Orçamento muito limitado
- Queries simples diretas

### ROI Esperado

| Métrica | Melhoria | Trade-off |
|---------|----------|-----------|
| Hallucination Rate | -40 a -50% | - |
| Faithfulness | +10 a +15% | - |
| Judge Approval | +8 a +12% | - |
| Latência | - | +20 a +30% |
| Custo | - | +30 a +40% |

**Complexidade:** ⭐⭐⭐⭐ Média-Alta
**Tempo Implementação:** 3-4 dias (13-16h)

---

## [EMOJI] CRAG - Corrective RAG

### O Que É?

Sistema RAG que **auto-corrige** retrieval ruim via query reformulation e web search fallback.

### Como Funciona?

```
Query -> Retrieve -> [Qualidade?]
                   ├─ CORRECT (>0.7) -> Usar docs internos
                   ├─ AMBIGUOUS (0.3-0.7) -> Docs + Web search
                   └─ INCORRECT (<0.3) -> Rewrite query -> Web search
                   -> Generate
```

### Componentes

1. **Retrieval Grading** - Avalia qualidade (score 0-1)
2. **Query Rewriting** - Reformula queries ambíguas
3. **Knowledge Refinement** - Decompõe docs em strips úteis
4. **Web Search Fallback** - Busca externa quando falha
5. **Fusion** - Combina fontes múltiplas (RRF)

### Grading Thresholds

- **Correct** (confidence > 0.7): Docs altamente relevantes -> Usar
- **Ambiguous** (0.3 < conf ≤ 0.7): Incerto -> Combinar docs + web
- **Incorrect** (conf ≤ 0.3): Docs irrelevantes -> Web search only

### Quando Usar?

[OK] **BOM para:**
- Retrieval frequentemente falha (<70% precision)
- Queries ambíguas ou mal formuladas
- Dataset incompleto para domínio
- Necessidade de informação externa (web)

[ERRO] **RUIM para:**
- Retrieval já excelente (>80% precision)
- Dataset completo e bem curado
- Latência muito crítica
- Sem acesso a web search (air-gapped)

### ROI Esperado

| Métrica | Melhoria | Trade-off |
|---------|----------|-----------|
| Context Precision | +15 a +25% | - |
| Retrieval Quality | 0.65 -> 0.80 | - |
| Accuracy (queries corrigidas) | +15% | - |
| Latência | - | +30 a +40% |
| Custo | - | +40 a +50% |

**Complexidade:** ⭐⭐⭐⭐⭐ Alta
**Tempo Implementação:** 4-5 dias (18-21h)

---

## 🆚 COMPARAÇÃO DIRETA

### Self-RAG vs CRAG

| Aspecto | Self-RAG | CRAG |
|---------|----------|------|
| **Objetivo** | Reduzir alucinações | Melhorar retrieval ruim |
| **Approach** | Self-reflection em generation | Correção de retrieval |
| **Quando Aplicar** | Geração é problema | Retrieval é problema |
| **Complexidade** | Média-Alta | Alta |
| **Latência Adicional** | +20-30% | +30-40% |
| **Custo Adicional** | +30-40% | +40-50% |
| **ROI** | Alto (SE alucinações >10%) | Alto (SE precision <70%) |
| **Web Search** | Não precisa | **Precisa** (Tavily/Bing) |
| **LLM Calls** | +2-3 calls/query | +3-4 calls/query |

### Quando Usar Ambas?

[OK] **Combinação Ideal:**
- Self-RAG: Post-processing de generation
- CRAG: Pre-processing de retrieval

**Workflow Combinado:**
```
Query -> CRAG (corrige retrieval)
      -> Agents (com docs corrigidos)
      -> Self-RAG (valida resposta)
      -> Final Answer
```

**Trade-off:** Latência +50-70%, Custo +70-90%, mas qualidade máxima.

---

## [EMOJI] MATRIZ DE DECISÃO

Use esta matriz para decidir qual técnica implementar:

| Seu Problema | Técnica Recomendada | Prioridade |
|--------------|---------------------|------------|
| Hallucination rate > 15% | Self-RAG | [EMOJI] ALTA |
| Context Precision < 0.60 | CRAG | [EMOJI] ALTA |
| Ambos problemas | Self-RAG + CRAG | [EMOJI] ALTA |
| Hallucination 10-15% | Self-RAG | MÉDIA |
| Precision 0.60-0.70 | CRAG | MÉDIA |
| Hallucination < 10% | [ERRO] Pular Self-RAG | BAIXA |
| Precision > 0.80 | [ERRO] Pular CRAG | BAIXA |
| Ambas métricas boas | [ERRO] Pular Fase 2B | BAIXA |

---

## [EMOJI] LIÇÕES DE PLANEJAMENTO

### 1. Brightdata Research

**Descoberta:** Implementações modernas 2025 (LangGraph, Meilisearch, DataCamp) simplificam muito vs paper original.

**Economia:** ~40% tempo de desenvolvimento (usa código validado)

### 2. Decisão Data-Driven

**Princípio:** NÃO implementar antes de validar necessidade com benchmark.

**Benefício:** Evita over-engineering, foco em ROI real.

### 3. Modularidade

**Design:** Self-RAG e CRAG como módulos independentes com feature flags.

**Benefício:** A/B testing fácil, rollback rápido, customização por cliente.

---

## [EMOJI] REFERÊNCIAS

### Self-RAG

**Papers:**
- [Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511) (Oct 2023)

**Tutorials:**
- [LangGraph Self-RAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/) (Oficial)
- [Analytics Vidhya - Self-RAG 2025](https://www.analyticsvidhya.com/blog/2025/01/self-rag/)
- [Medium - Reflective Agentic RAG](https://nayakpplaban.medium.com/build-a-reflective-agentic-rag-workflow-using-langgraph)

**GitHub:**
- [AkariAsai/self-rag](https://github.com/AkariAsai/self-rag)

### CRAG

**Papers:**
- [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) (Jan 2024)

**Tutorials:**
- [Meilisearch - CRAG Workflow](https://www.meilisearch.com/blog/corrective-rag) (Sep 2025)
- [DataCamp - CRAG Implementation](https://www.datacamp.com/tutorial/corrective-rag-crag) (Sep 2024)
- [LangGraph CRAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)

**GitHub:**
- [HuskyInSalt/CRAG](https://github.com/HuskyInSalt/CRAG)

---

## [EMOJI] PRÓXIMO PASSO

**AGUARDAR:** Benchmark Fase 2A completar
**ANALISAR:** Faithfulness, Context Precision, Judge Approval
**DECIDIR:** Implementar Fase 2B baseado em métricas objetivas

---

**Última Atualização:** 2025-10-14
**Status:** [OK] PLANEJAMENTO COMPLETO
