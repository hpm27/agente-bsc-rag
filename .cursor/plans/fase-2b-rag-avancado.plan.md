# Fase 2B - RAG Avançado: Self-RAG + CRAG

**Status:** [EMOJI] PLANEJADO
**Início Previsto:** Após validação Benchmark Fase 2A
**Duração Estimada:** 2-3 semanas (8-10 dias úteis)
**Última Atualização:** 2025-10-14

---

## [EMOJI] OBJETIVOS FASE 2B

Implementar técnicas RAG avançadas focadas em:

1. **Self-RAG** - Reduzir alucinações via self-reflection (-40-50%)
2. **CRAG** - Corrigir retrieval ruim via query reformulation (+23% quality)

**Pré-requisito:** Benchmark Fase 2A validar necessidade (faithfulness, precision)

---

## [EMOJI] DECISÃO CONDICIONAL (Baseada em Benchmark Fase 2A)

### Cenário 1: Implementar Self-RAG

**SE:**
- Faithfulness < 0.85 (alucinações detectadas)
- Judge approval rate < 85%
- Queries complexas com respostas incompletas

**ENTÃO:** Implementar Self-RAG (Prioridade ALTA)

---

### Cenário 2: Implementar CRAG

**SE:**
- Context Precision < 0.70 (retrieval ruim)
- Muitas queries com docs irrelevantes
- Retrieval falha em queries ambíguas

**ENTÃO:** Implementar CRAG (Prioridade ALTA)

---

### Cenário 3: Pular Fase 2B

**SE:**
- Faithfulness > 0.90 (alucinações mínimas)
- Context Precision > 0.80 (retrieval excelente)
- Judge approval > 90%

**ENTÃO:** Considerar Fase 2B **OPCIONAL** (sistema já muito bom)

---

## [EMOJI] ROADMAP FASE 2B

### Fase 2B.1 - Self-RAG (Semana 1)

**Duração:** 3-4 dias úteis (13-16h)
**Complexidade:** ⭐⭐⭐⭐ Média-Alta
**ROI Esperado:** ⭐⭐⭐⭐ Alto

#### Etapas

1. **Research & Discovery** (1h)
   - [ ] Ler tutorial LangGraph Self-RAG oficial
   - [ ] Estudar paper "Self-RAG: Learning to Retrieve, Generate, and Critique" (2023)
   - [ ] Analisar implementações 2025 (Analytics Vidhya, DataCamp)
   - [ ] Estudar reflection tokens ([Retrieve], [Relevant], [Supported], [Useful])

2. **Design & Architecture** (1h)
   - [ ] Desenhar workflow LangGraph com 5 nós:
     * `retrieve_decision` - Decide SE precisa retrieval
     * `retrieve` - Busca documentos
     * `grade_documents` - Avalia relevância (keep/discard)
     * `generate` - Gera resposta
     * `grade_answer` - Verifica suporte nos docs
   - [ ] Definir prompts para cada grading step
   - [ ] Planejar integração com workflow BSC atual

3. **Implementation** (6-8h)
   - [ ] Criar `src/rag/self_rag.py` com classe `SelfRAG`
   - [ ] Implementar `RetrievalGrader` (julga relevância de docs)
   - [ ] Implementar `AnswerGrader` (verifica suporte/alucinação)
   - [ ] Integrar com `BSCWorkflow` via feature flag
   - [ ] Adicionar `ENABLE_SELF_RAG=true/false` em `.env`
   - [ ] Criar prompts em `src/prompts/self_rag_prompts.py`

4. **Testing** (3h)
   - [ ] Criar `tests/test_self_rag.py` (15+ testes unitários)
   - [ ] Criar benchmark específico (20 queries propensas a alucinação)
   - [ ] Medir hallucination rate (baseline vs self-rag)
   - [ ] Validar métricas: Faithfulness >0.90, Latência +20-30%

5. **Documentation** (2h)
   - [ ] Criar `docs/techniques/SELF_RAG.md` (300+ linhas)
   - [ ] Documentar lição aprendida em `docs/lessons/`
   - [ ] Atualizar `README.md` e plano

**Métricas de Sucesso:**
- [OK] Hallucination rate < 5% (vs 10-15% baseline)
- [OK] Faithfulness > 0.90 (vs 0.80-0.85 baseline)
- [OK] Judge approval > 90%
- [WARN] Latência +20-30% (trade-off aceitável)

---

### Fase 2B.2 - CRAG (Semana 2)

**Duração:** 4-5 dias úteis (18-21h)
**Complexidade:** ⭐⭐⭐⭐⭐ Alta
**ROI Esperado:** ⭐⭐⭐⭐ Alto (SE retrieval ruim)

#### Etapas

1. **Research & Discovery** (1.5h)
   - [ ] Ler tutorial Meilisearch CRAG (Sep 2025)
   - [ ] Estudar tutorial DataCamp CRAG (Sep 2024)
   - [ ] Analisar código GitHub HuskyInSalt/CRAG
   - [ ] Entender grading algorithm (Correct/Incorrect/Ambiguous)
   - [ ] Estudar knowledge refinement (decomposição de docs)

2. **Design & Architecture** (1.5h)
   - [ ] Desenhar workflow com 4 decisões:
     * Grade retrieval (Correct/Incorrect/Ambiguous)
     * SE Correct -> usar docs
     * SE Incorrect -> web search fallback
     * SE Ambiguous -> combinar docs + web
   - [ ] Planejar query rewriter (reformulação automática)
   - [ ] Definir knowledge refinement strategy

3. **Web Search Integration** (2h)
   - [ ] Avaliar opções: Tavily API, Bing API, ou Brightdata MCP
   - [ ] Integrar web search como fallback
   - [ ] Criar filtro de resultados web (relevância BSC)
   - [ ] Combinar docs internos + web results (RRF)

4. **Implementation** (8-10h)
   - [ ] Criar `src/rag/corrective_rag.py` com classe `CorrectiveRAG`
   - [ ] Implementar `RetrievalGrader` (Correct/Incorrect/Ambiguous)
   - [ ] Implementar `QueryRewriter` (reformulação de queries)
   - [ ] Implementar `KnowledgeRefiner` (knowledge strips)
   - [ ] Integrar web search fallback
   - [ ] Adicionar `ENABLE_CRAG=true/false` em `.env`
   - [ ] Criar prompts em `src/prompts/crag_prompts.py`

5. **Testing** (3h)
   - [ ] Criar `tests/test_crag.py` (15+ testes unitários)
   - [ ] Criar benchmark específico (20 queries ambíguas)
   - [ ] Medir retrieval quality (baseline vs CRAG)
   - [ ] Validar métricas: Precision 0.65 -> 0.80, Correction rate 10-15%

6. **Documentation** (2h)
   - [ ] Criar `docs/techniques/CRAG.md` (300+ linhas)
   - [ ] Documentar lição aprendida
   - [ ] Atualizar documentação geral

**Métricas de Sucesso:**
- [OK] Context Precision: 0.65 -> 0.80 (+23%)
- [OK] Correction triggered: 10-15% queries
- [OK] Accuracy em queries corrigidas: +15%
- [WARN] Latência +30-40% (mais que Self-RAG)

---

### Fase 2B.3 - Integração & Validação (Semana 3)

**Duração:** 2-3 dias (8-10h)

1. **Integração Completa** (3h)
   - [ ] Integrar Self-RAG + CRAG ao workflow
   - [ ] Resolver conflitos (ambos ativos simultaneamente)
   - [ ] Otimizar trade-off latência vs qualidade
   - [ ] Testar combinações de features

2. **Validação E2E** (3h)
   - [ ] Executar suite E2E completa (22 testes)
   - [ ] Validar sem regressões
   - [ ] Ajustar thresholds se necessário

3. **Benchmark Fase 2B** (4h)
   - [ ] Executar benchmark com 50 queries
   - [ ] Comparar: Baseline -> Fase 2A -> Fase 2B
   - [ ] Validar ROI incremental
   - [ ] Gerar relatório comparativo

**Métricas de Sucesso:**
- [OK] E2E tests 100% passando
- [OK] Nenhuma regressão vs Fase 2A
- [OK] Melhoria incremental em qualidade

---

### Fase 2B.4 - Documentação & Lições (Semana 3-4)

**Duração:** 1-2 dias (5-8h)

1. **Documentação Técnica**
   - [ ] Finalizar `docs/techniques/SELF_RAG.md`
   - [ ] Finalizar `docs/techniques/CRAG.md`
   - [ ] Criar comparação técnica (quando usar cada uma)

2. **Lições Aprendidas**
   - [ ] `docs/lessons/lesson-self-rag-2025-10-XX.md`
   - [ ] `docs/lessons/lesson-crag-2025-10-XX.md`
   - [ ] Documentar trade-offs observados

3. **Atualização Geral**
   - [ ] Atualizar `README.md` (Fase 2B completa)
   - [ ] Atualizar `.cursor/rules/rag-bsc-core.mdc`
   - [ ] Criar `docs/history/FASE_2B_COMPLETA.md`

---

## [EMOJI] REFERÊNCIAS TÉCNICAS

### Self-RAG

**Papers:**
- [Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511) (2023)

**Tutorials (2025):**
- [LangGraph Self-RAG Official Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/)
- [Analytics Vidhya - Self-RAG Guide](https://www.analyticsvidhya.com/blog/2025/01/self-rag/)
- [Medium - Self-Reflective RAG with LangGraph](https://nayakpplaban.medium.com/build-a-reflective-agentic-rag-workflow-using-langgraph)

**GitHub:**
- [AkariAsai/self-rag](https://github.com/AkariAsai/self-rag) - Paper original implementation

---

### CRAG (Corrective RAG)

**Papers:**
- [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) (2024)

**Tutorials (2025):**
- [Meilisearch - CRAG Guide](https://www.meilisearch.com/blog/corrective-rag) (Sep 2025)
- [DataCamp - CRAG Implementation](https://www.datacamp.com/tutorial/corrective-rag-crag) (Sep 2024)
- [GeeksforGeeks - CRAG Tutorial](https://www.geeksforgeeks.org/artificial-intelligence/corrective-retrieval-augmented-generation-crag/) (Oct 2025)

**GitHub:**
- [HuskyInSalt/CRAG](https://github.com/HuskyInSalt/CRAG) - Official implementation
- [LangGraph CRAG Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)

---

## [EMOJI] CRITÉRIOS DE DECISÃO

### Quando Implementar Self-RAG?

[OK] **SIM, implementar SE:**
- Hallucination rate > 10%
- Faithfulness < 0.85
- Judge rejeita >15% respostas
- Queries complexas geram informação não suportada

[ERRO] **NÃO implementar SE:**
- Faithfulness já > 0.90
- Judge approval > 90%
- Alucinações raras (<5%)

---

### Quando Implementar CRAG?

[OK] **SIM, implementar SE:**
- Context Precision < 0.70
- Retrieval falha em >20% queries
- Queries ambíguas com docs irrelevantes
- Dataset incompleto para domínio

[ERRO] **NÃO implementar SE:**
- Context Precision > 0.80
- Retrieval já muito bom
- Dataset completo e bem curado

---

## [EMOJI] ARQUITETURA PLANEJADA

### Self-RAG Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    SELF-RAG WORKFLOW                    │
└─────────────────────────────────────────────────────────┘

1. Query Input
   ↓
2. Retrieve Decision (LLM)
   ├─ [Retrieve] -> Continuar
   └─ [No Retrieve] -> Generate direto
   ↓
3. Retrieve Documents (k=50)
   ↓
4. Grade Documents (LLM)
   ├─ [Relevant] -> Keep
   └─ [Irrelevant] -> Discard
   ↓
5. Generate Answer (LLM com docs relevantes)
   ↓
6. Grade Answer (LLM)
   ├─ [Supported] -> Retornar resposta
   ├─ [Partially Supported] -> Re-retrieve (iteração)
   └─ [Not Supported] -> Re-generate
   ↓
7. Final Answer
```

**Reflection Tokens:**
- `[Retrieve]` / `[No Retrieve]` - Decisão de retrieval
- `[Relevant]` / `[Irrelevant]` - Grading de docs
- `[Supported]` / `[Partially]` / `[Not Supported]` - Grading de resposta
- `[Useful]` / `[Not Useful]` - Utilidade final

---

### CRAG Workflow

```
┌─────────────────────────────────────────────────────────┐
│                     CRAG WORKFLOW                       │
└─────────────────────────────────────────────────────────┘

1. Query Input
   ↓
2. Retrieve Documents (k=50, hybrid search)
   ↓
3. Grade Retrieval Quality (LLM)
   ├─ [Correct] -> Usar docs (confidence > 0.7)
   ├─ [Incorrect] -> Web search fallback
   └─ [Ambiguous] -> Combinar docs + web
   ↓
4a. SE Correct:
    -> Knowledge Refinement (decompor docs longos)
    -> Generate com docs refinados
    ↓
4b. SE Incorrect:
    -> Query Rewrite (reformular query)
    -> Web Search (Tavily/Bing)
    -> Generate com web results
    ↓
4c. SE Ambiguous:
    -> Knowledge Refinement
    -> Web Search
    -> Combinar (RRF) docs + web
    -> Generate com combinação
    ↓
5. Final Answer
```

**Componentes-Chave:**
- `RetrievalGrader` - Avalia qualidade (score 0-1)
- `QueryRewriter` - Reformula queries ruins
- `KnowledgeRefiner` - Extrai knowledge strips
- `WebSearchTool` - Fallback externo

---

## [EMOJI] MICRO-TAREFAS DETALHADAS

### FASE 2B.1 - Self-RAG (13-16h)

#### TASK 1: Research & Discovery (1h)

**Artefatos:**
- [ ] Notas de estudo do paper Self-RAG
- [ ] Análise de código LangGraph tutorial
- [ ] Comparação implementações 2025

---

#### TASK 2: Design (1h)

**Artefatos:**
- [ ] Diagrama de workflow (draw.io ou Mermaid)
- [ ] Especificação de prompts (5 prompts)
- [ ] Definição de reflection tokens

**Prompts Necessários:**
1. `retrieve_decision_prompt` - "Esta query precisa de retrieval?"
2. `document_grading_prompt` - "Este documento é relevante?"
3. `answer_grading_prompt` - "Resposta está suportada pelos docs?"
4. `hallucination_check_prompt` - "Resposta contém informação inventada?"
5. `usefulness_prompt` - "Resposta é útil para query?"

---

#### TASK 3: Implementation (6-8h)

**Arquivos a Criar:**

```python
# src/rag/self_rag.py
class SelfRAG:
    """Self-Reflective RAG com grading de docs e respostas."""

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.retrieval_grader = RetrievalGrader(llm)
        self.answer_grader = AnswerGrader(llm)

    def should_retrieve(self, query: str) -> bool:
        """Decide se query precisa de retrieval."""
        pass

    def grade_documents(self, query: str, docs: List[Document]) -> List[Document]:
        """Filtra docs irrelevantes."""
        pass

    def grade_answer(self, query: str, answer: str, docs: List[Document]) -> Dict:
        """Verifica se resposta está suportada."""
        pass

# src/prompts/self_rag_prompts.py
RETRIEVE_DECISION_PROMPT = """..."""
DOCUMENT_GRADING_PROMPT = """..."""
ANSWER_GRADING_PROMPT = """..."""
```

**Integração com BSCWorkflow:**

```python
# src/graph/workflow.py - novo nó
def grade_and_refine(state: BSCState) -> BSCState:
    """Nó Self-RAG para grading de resposta."""
    if not settings.ENABLE_SELF_RAG:
        return state

    self_rag = SelfRAG(retriever, llm)
    grading = self_rag.grade_answer(
        state["query"],
        state["final_response"],
        state["agent_responses"]
    )

    if not grading["supported"]:
        # Re-retrieve ou re-generate
        pass

    return state
```

---

#### TASK 4: Testing (3h)

**Testes Unitários:**

```python
# tests/test_self_rag.py

def test_should_retrieve_complex_query():
    """Query complexa deve requerer retrieval."""
    self_rag = SelfRAG(retriever, llm)
    assert self_rag.should_retrieve("Como implementar BSC?") == True

def test_should_not_retrieve_simple_query():
    """Query muito simples pode não requerer retrieval."""
    self_rag = SelfRAG(retriever, llm)
    assert self_rag.should_retrieve("O que é BSC?") == False

def test_grade_documents_filters_irrelevant():
    """Grading deve filtrar docs irrelevantes."""
    # ... 13+ testes adicionais
```

**Benchmark Específico:**
- 20 queries propensas a alucinação
- Manual evaluation de hallucination rate
- Comparação baseline vs self-rag

---

#### TASK 5: Documentation (2h)

**Template `docs/techniques/SELF_RAG.md`:**

```markdown
# Self-RAG - Self-Reflective Retrieval Augmented Generation

## Visão Geral
[Descrição de 1-2 parágrafos]

## Problema que Resolve
- Alucinações em respostas RAG
- LLM inventando informação não presente nos docs
- Baixa fidelidade factual

## Como Funciona
[Diagrama + explicação detalhada]

## Componentes
### 1. Retrieval Decision
### 2. Document Grading
### 3. Answer Grading
### 4. Reflection Tokens

## Implementação
[Código completo com comentários]

## Métricas
| Métrica | Baseline | Self-RAG | Melhoria |
|---------|----------|----------|----------|
| Faithfulness | 0.82 | 0.93 | +13% |
| Hallucination Rate | 12% | 4% | -67% |
| Latência | 95s | 118s | +24% |

## Quando Usar
[OK] Alta necessidade de acurácia factual
[OK] Hallucination rate > 10%
[OK] Queries complexas multi-parte

## Quando NÃO Usar
[ERRO] Latência crítica (<10s)
[ERRO] Faithfulness já > 0.90
[ERRO] Custo muito limitado

## Lições Aprendidas
[O que funcionou, trade-offs, insights]

## Referências
[Papers, tutorials, código]
```

---

### FASE 2B.2 - CRAG (18-21h)

#### TASK 1: Research (1.5h)

**Artefatos:**
- [ ] Análise de paper CRAG (2024)
- [ ] Comparação 3 implementações (Meilisearch, DataCamp, GitHub)
- [ ] Notas sobre grading algorithm

---

#### TASK 2: Design (1.5h)

**Artefatos:**
- [ ] Diagrama workflow CRAG
- [ ] Especificação de grading (score thresholds)
- [ ] Estratégia de query rewrite

**Grading Thresholds:**
- **Correct**: confidence > 0.7 -> Usar docs
- **Ambiguous**: 0.3 < confidence ≤ 0.7 -> Combinar docs + web
- **Incorrect**: confidence ≤ 0.3 -> Web search only

---

#### TASK 3: Web Search Integration (2h)

**Opções Avaliadas:**

| Opção | Custo | Latência | Qualidade | Decisão |
|-------|-------|----------|-----------|---------|
| Tavily API | $$ | ~2s | Alta | [OK] Preferida |
| Bing API | $ | ~1s | Média | Alternativa |
| Brightdata MCP | Grátis | ~3s | Alta | [OK] Viável |

**Implementação:**

```python
# src/rag/web_search.py
class WebSearchTool:
    """Fallback web search para CRAG."""

    def __init__(self, provider="tavily"):
        self.provider = provider

    def search(self, query: str, k: int = 5) -> List[Document]:
        """Busca web com query reformulada."""
        if self.provider == "tavily":
            # Tavily API
            pass
        elif self.provider == "brightdata":
            # Brightdata MCP
            pass
```

---

#### TASK 4: Implementation (8-10h)

**Arquivos a Criar:**

```
src/rag/
├── corrective_rag.py        # Classe principal CRAG
├── retrieval_grader.py      # Avalia qualidade do retrieval
├── query_rewriter.py        # Reformula queries ruins (JÁ EXISTE - adaptar)
├── knowledge_refiner.py     # Extrai knowledge strips
└── web_search.py            # Web search fallback

src/prompts/
└── crag_prompts.py          # Prompts de grading e rewrite
```

**Código Principal:**

```python
# src/rag/corrective_rag.py
from enum import Enum

class RetrievalQuality(Enum):
    CORRECT = "correct"
    AMBIGUOUS = "ambiguous"
    INCORRECT = "incorrect"

class CorrectiveRAG:
    """Corrective RAG com query reformulation e web search fallback."""

    def __init__(self, retriever, llm, web_search):
        self.retriever = retriever
        self.llm = llm
        self.web_search = web_search
        self.grader = RetrievalGrader(llm)
        self.rewriter = QueryRewriter(llm)
        self.refiner = KnowledgeRefiner(llm)

    def grade_retrieval(self, query: str, docs: List[Document]) -> RetrievalQuality:
        """Avalia qualidade do retrieval."""
        score = self.grader.grade(query, docs)

        if score > 0.7:
            return RetrievalQuality.CORRECT
        elif score > 0.3:
            return RetrievalQuality.AMBIGUOUS
        else:
            return RetrievalQuality.INCORRECT

    def execute(self, query: str) -> Dict[str, Any]:
        """Executa CRAG completo."""
        # 1. Retrieval inicial
        docs = self.retriever.retrieve(query, k=50)

        # 2. Grade retrieval
        quality = self.grade_retrieval(query, docs)

        # 3. Decisão baseada em grading
        if quality == RetrievalQuality.CORRECT:
            # Refinar e usar
            refined_docs = self.refiner.refine(docs)
            return {"docs": refined_docs, "source": "internal"}

        elif quality == RetrievalQuality.INCORRECT:
            # Rewrite + Web search
            rewritten_query = self.rewriter.rewrite(query)
            web_docs = self.web_search.search(rewritten_query)
            return {"docs": web_docs, "source": "web"}

        else:  # AMBIGUOUS
            # Combinar internal + web
            refined_docs = self.refiner.refine(docs)
            rewritten_query = self.rewriter.rewrite(query)
            web_docs = self.web_search.search(rewritten_query)
            combined = self._combine_docs(refined_docs, web_docs)
            return {"docs": combined, "source": "hybrid"}
```

---

#### TASK 5: Testing (3h)

**Benchmark Específico:**

```json
{
  "queries_ambiguas": [
    "Diferenças BSC manufatura vs serviços",
    "BSC setor público adaptações",
    "KPIs inovação perspectiva aprendizado",
    ...
  ],
  "expected_corrections": 15-20% das queries
}
```

**Testes:**

```python
def test_crag_detects_poor_retrieval():
    """CRAG deve detectar retrieval ruim."""
    crag = CorrectiveRAG(retriever, llm, web_search)

    # Query ambígua com docs ruins
    quality = crag.grade_retrieval(
        "diferenças BSC manufatura serviços",
        low_quality_docs
    )

    assert quality == RetrievalQuality.INCORRECT

def test_crag_triggers_rewrite():
    """CRAG deve reescrever query quando retrieval falha."""
    # ... 13+ testes adicionais
```

---

## [EMOJI] MÉTRICAS DE VALIDAÇÃO

### Self-RAG

| Métrica | Baseline | Target Self-RAG | Como Medir |
|---------|----------|-----------------|------------|
| Hallucination Rate | 10-15% | <5% | Manual evaluation 50 queries |
| Faithfulness (RAGAS) | 0.82 | >0.90 | RAGAS metric |
| Judge Approval | 82% | >90% | Judge agent |
| Latência P50 | 90s | <120s | Benchmark |
| Custo por query | $0.05 | <$0.07 | Token counting |

### CRAG

| Métrica | Baseline | Target CRAG | Como Medir |
|---------|----------|-------------|------------|
| Context Precision | 0.65 | >0.80 | RAGAS metric |
| Correction Rate | N/A | 10-15% | Count triggers |
| Accuracy (corrigidas) | N/A | +15% | Manual eval subset |
| Latência P50 | 90s | <135s | Benchmark |
| Web search triggers | N/A | 5-10% | Logging |

---

## [EMOJI] FEATURE FLAGS

```bash
# .env - Fase 2B flags

# Self-RAG
ENABLE_SELF_RAG=true
SELF_RAG_MIN_CONFIDENCE=0.5  # Threshold para retrieval decision
SELF_RAG_MAX_ITERATIONS=2    # Max re-retrieve iterations

# CRAG
ENABLE_CRAG=true
CRAG_CORRECT_THRESHOLD=0.7   # Score > 0.7 = Correct
CRAG_AMBIGUOUS_THRESHOLD=0.3 # Score 0.3-0.7 = Ambiguous
CRAG_WEB_SEARCH_PROVIDER=tavily  # tavily, bing, brightdata
CRAG_MAX_REWRITES=2          # Max query reformulations
```

---

## [EMOJI] CRONOGRAMA ESTIMADO

### Semana 1 - Self-RAG

| Dia | Atividade | Horas | Status |
|-----|-----------|-------|--------|
| 1 | Research + Design | 2h | ⏸ |
| 2 | Implementation Part 1 | 4h | ⏸ |
| 3 | Implementation Part 2 | 4h | ⏸ |
| 4 | Testing + Ajustes | 3h | ⏸ |
| 5 | Documentation | 2h | ⏸ |

**Total:** 15h (3-4 dias)

---

### Semana 2 - CRAG

| Dia | Atividade | Horas | Status |
|-----|-----------|-------|--------|
| 1 | Research + Design | 3h | ⏸ |
| 2 | Web Search Integration | 2h | ⏸ |
| 3 | Implementation Part 1 | 5h | ⏸ |
| 4 | Implementation Part 2 | 5h | ⏸ |
| 5 | Testing | 3h | ⏸ |
| 6 | Documentation | 2h | ⏸ |

**Total:** 20h (4-5 dias)

---

### Semana 3 - Integração & Validação

| Dia | Atividade | Horas | Status |
|-----|-----------|-------|--------|
| 1 | Integração Self-RAG + CRAG | 3h | ⏸ |
| 2 | Testes E2E | 3h | ⏸ |
| 3 | Benchmark Fase 2B (50 queries) | 4h | ⏸ |
| 4 | Análise + Docs finais | 3h | ⏸ |

**Total:** 13h (2-3 dias)

---

## [EMOJI] CRITÉRIOS DE SUCESSO FASE 2B

### Funcional

- [OK] Self-RAG reduz hallucination rate em 50%+
- [OK] CRAG melhora precision em 20%+ quando trigado
- [OK] Ambas técnicas têm feature flags funcionais
- [OK] E2E tests 100% passando

### Performance

- [OK] Latência Self-RAG: baseline +20-30% (aceitável)
- [OK] Latência CRAG: baseline +30-40% (aceitável)
- [OK] Custo: +30-50% (justificável por qualidade)

### Qualidade

- [OK] RAGAS Faithfulness > 0.90
- [OK] RAGAS Context Precision > 0.80
- [OK] Judge Approval > 90%

---

## [EMOJI] DEPENDÊNCIAS

### Bibliotecas Python

```txt
# Já instaladas
langchain>=0.1.0
langchain-openai>=0.0.2
langgraph>=0.0.20

# A adicionar
tavily-python>=0.3.0  # Web search (SE usar Tavily)
```

### APIs Externas

- [OK] OpenAI (já configurada) - Para LLM grading
- ⏸ Tavily (opcional) - Web search fallback CRAG
- ⏸ Bing Search (alternativa) - Web search fallback

---

## [WARN] RISCOS & MITIGAÇÕES

### Risco 1: Latência Muito Alta

**Risco:** Self-RAG + CRAG podem adicionar +50-70% latência
**Mitigação:**
- Feature flags para ativar seletivamente
- Router pode decidir quando usar cada técnica
- Cache agressivo de grading results

### Risco 2: Custo Elevado

**Risco:** +3-4 LLM calls por query = +60-80% custo
**Mitigação:**
- Usar GPT-4o-mini para grading (barato)
- Batch grading quando possível
- Cache de decisions

### Risco 3: Over-Engineering

**Risco:** Fase 2A já pode ser suficiente
**Mitigação:**
- **AGUARDAR benchmark Fase 2A**
- Implementar APENAS se métricas justificarem
- Validar ROI incremental

---

## [EMOJI] LIÇÕES DO PLANEJAMENTO

### 1. Pesquisa Prévia Economiza Tempo

- Brightdata identificou implementações modernas (2025)
- LangGraph tutorials oficiais disponíveis
- Evita reinventar a roda

### 2. Decisão Baseada em Dados

- Não implementar cegamente
- Benchmark Fase 2A valida necessidade
- ROI incremental deve justificar esforço

### 3. Modularidade é Chave

- Feature flags permitem A/B testing
- Self-RAG e CRAG independentes
- Podem ser usadas separadamente ou em conjunto

---

## [EMOJI] PRÓXIMOS PASSOS IMEDIATOS

### AGORA (Enquanto Benchmark Fase 2A Roda)

1. [OK] Plano Fase 2B completo
2. ⏳ Aguardar benchmark terminar
3. [EMOJI] Analisar resultados Fase 2A
4. [EMOJI] **DECIDIR**: Implementar Fase 2B SIM/NÃO?

### SE SIM - Iniciar Fase 2B.1 (Self-RAG)

1. Ler tutoriais LangGraph (1h)
2. Criar workflow design (1h)
3. Implementar SelfRAG class (6-8h)
4. Testar + validar (3h)
5. Documentar (2h)

---

## [EMOJI] CHANGELOG

### v1.0 - 2025-10-14 (Planejamento Inicial)

**Criado:**
- [OK] Plano completo Fase 2B (Self-RAG + CRAG)
- [OK] Pesquisa Brightdata (implementações 2025)
- [OK] Micro-tarefas detalhadas (31-37h total)
- [OK] Cronograma (2-3 semanas)
- [OK] Critérios de decisão condicional
- [OK] Métricas de sucesso
- [OK] Referências técnicas

**Próximo:**
- ⏳ Aguardar benchmark Fase 2A
- [EMOJI] Decidir iniciar Fase 2B baseado em métricas

---

**Última Atualização:** 2025-10-14
**Status:** [OK] PLANEJAMENTO COMPLETO - Aguardando validação Fase 2A
