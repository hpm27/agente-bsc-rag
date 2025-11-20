# [ERRO] ANTIPADRÕES RAG - BSC Project

**Data:** 2025-10-14
**Fonte:** Lições aprendidas Fase 2A (Query Decomposition, Adaptive Re-ranking, Router)
**Objetivo:** Documentar armadilhas evitadas para acelerar Fase 2B e projetos futuros

---

## [EMOJI] COMO USAR ESTE DOCUMENTO

**Checklist antes de implementar qualquer técnica RAG:**

1. [OK] Revisar seção relevante (Query Enhancement, Retrieval, Re-ranking, Testing)
2. [OK] Verificar se antipadrão se aplica à técnica
3. [OK] Implementar solução recomendada
4. [OK] Validar que antipadrão foi evitado

**ROI:** Evitar 1 antipadrão = economia de 2-8h debugging/refactoring

---

## [EMOJI] ÍNDICE DE ANTIPADRÕES

1. [Query Enhancement](#1-query-enhancement)
2. [Retrieval e Busca](#2-retrieval-e-busca)
3. [Re-ranking e Diversidade](#3-re-ranking-e-diversidade)
4. [Metadados e Ground Truth](#4-metadados-e-ground-truth)
5. [Testing e Validação](#5-testing-e-validação)
6. [Performance e Custos](#6-performance-e-custos)
7. [Arquitetura e Integração](#7-arquitetura-e-integração)
8. [LLMs e APIs](#8-llms-e-apis)

---

## 1. QUERY ENHANCEMENT

### [ERRO] ANTIPADRÃO 1.1: Usar GPT-4o para Tarefas Simples

**Problema:**
- Usar GPT-4o/GPT-5 para decomposição, classificação, extração

**Por quê é ruim:**
- [ERRO] **Custo 100x maior** ($0.01 vs $0.0001 GPT-4o-mini)
- [ERRO] **Latência +40%** (~2s vs ~1.2s)
- [ERRO] **Qualidade similar** (não justifica custo)

**Solução:**

```python
# [ERRO] EVITAR
decomposer = QueryDecomposer(llm="gpt-4o")  # Caro!

# [OK] USAR
decomposer = QueryDecomposer(llm="gpt-4o-mini")  # 100x mais barato

# Reservar GPT-4o/GPT-5 para:
# - Synthesis complexa
# - Generation final de respostas
# - Reasoning multi-step avançado
```

**Economia:** $9.90/dia em 1000 queries

**Fonte:** lesson-query-decomposition (Aprendizado #3)

---

### [ERRO] ANTIPADRÃO 1.2: Regex Sem Word Boundaries

**Problema:**
- Regex `"e" in query` detecta falsos positivos ("é", "presente", "mente")

**Por quê é ruim:**
- [ERRO] **-8% accuracy** em classificação
- [ERRO] **Falsos positivos** abundantes
- [ERRO] **Heurística não-confiável**

**Solução:**

```python
# [ERRO] EVITAR
if "e" in query.lower():
    score += 1  # Detecta "é", "presente", "mente"!

# [OK] USAR
import re
if re.search(r'\be\b', query.lower()):  # Word boundaries!
    score += 1  # Só detecta " e " isolado
```

**Melhoria:** +8% accuracy

**Fonte:** lesson-query-decomposition (Aprendizado #4), lesson-router (Aprendizado #4)

---

### [ERRO] ANTIPADRÃO 1.3: Sub-Queries Sem Contexto

**Problema:**
- Sub-queries isoladas perdem especificidade da query original

**Exemplo:**

```python
# [ERRO] EVITAR
Query original: "Como implementar BSC em manufatura?"
Sub-queries isoladas:
- "Quais KPIs financeiros?" <- Perdeu "manufatura"!
- "Como medir processos?" <- Perdeu "manufatura"!

# [OK] USAR
Sub-queries contextualizadas:
- "Quais KPIs financeiros em manufatura?"
- "Como medir processos em manufatura?"
```

**Impacto:** +15% precision

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #2)

---

### [ERRO] ANTIPADRÃO 1.4: Thresholds Altos Sem Validação

**Problema:**
- Definir thresholds arbitrariamente sem testar com dataset

**Exemplo:**

```python
# [ERRO] EVITAR
DECOMPOSITION_SCORE_THRESHOLD=2  # Arbitrário!
# Resultado: Coverage 40% (queries válidas não decompostas)

# [OK] USAR
DECOMPOSITION_SCORE_THRESHOLD=1  # Testado com dataset
# Resultado: Coverage 100%
```

**Regra:**
- [OK] Começar com thresholds **BAIXOS** e aumentar se necessário
- [OK] Validar coverage com dataset variado (50+ queries)
- [OK] A/B testing com thresholds diferentes

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #4)

---

## 2. RETRIEVAL E BUSCA

### [ERRO] ANTIPADRÃO 2.1: Reimplementar Funcionalidades Existentes

**Problema:**
- Implementar RRF do zero quando já existe

**Por quê é ruim:**
- [ERRO] **+1 dia desenvolvimento** desnecessário
- [ERRO] **Bugs novos** (não validado)
- [ERRO] **Duplicação de código**

**Solução:**

```python
# [ERRO] EVITAR
def my_own_rrf(results_list):  # Reimplementar RRF
    # ... 100 linhas de código novo (não testado)

# [OK] USAR
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()
fused = retriever.reciprocal_rank_fusion(results_list)  # Reutilizar!
```

**Economia:** 8h (1 dia de trabalho)

**Fonte:** lesson-query-decomposition (O Que Funcionou #2)

---

### [ERRO] ANTIPADRÃO 2.2: Retrieval Sem Metadados

**Problema:**
- Não usar metadados (title, authors, year, perspectives) para ground truth e filtros

**Por quê é ruim:**
- [ERRO] **Métricas não-validáveis** (Recall/Precision 0%)
- [ERRO] **Filtros avançados impossíveis**
- [ERRO] **UI pobre** (filenames longos vs títulos)

**Solução:**

```python
# [OK] IMPLEMENTAR
# 1. Criar index.json com metadados
# 2. Auto-geração com LLM para docs novos
# 3. document_title SEMPRE presente
# 4. Usar filtros em retrieval
```

**Benefícios:**
- [OK] Ground truth validável
- [OK] Filtros por autor/ano/tipo/perspectiva
- [OK] UI profissional

**Fonte:** Seção "MELHORIAS DE INFRAESTRUTURA" do plano

---

## 3. RE-RANKING E DIVERSIDADE

### [ERRO] ANTIPADRÃO 3.1: Embeddings Não-Normalizados

**Problema:**
- Usar embeddings raw em MMR ou similaridade cosseno

**Por quê é ruim:**
- [ERRO] **Erros numéricos** (underflow, overflow)
- [ERRO] **Similaridade incorreta** (valores fora de 0-1)
- [ERRO] **MMR instável**

**Solução:**

```python
# [ERRO] EVITAR
similarity = cosine_similarity(emb1, emb2)  # Embeddings raw

# [OK] USAR
emb1_norm = emb1 / np.linalg.norm(emb1)  # Normalizar!
emb2_norm = emb2 / np.linalg.norm(emb2)
similarity = cosine_similarity(emb1_norm, emb2_norm)

# OU usar sklearn (já normaliza internamente)
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity([emb1], [emb2])[0][0]
```

**Benefício:** Cálculos estáveis e corretos

**Fonte:** lesson-adaptive-reranking (O Que Funcionou #2)

---

### [ERRO] ANTIPADRÃO 3.2: Float Comparisons com `==`

**Problema:**
- Usar `assert similarity == 0.96` em testes

**Por quê é ruim:**
- [ERRO] **Falhas spurias** (0.9599999... ≠ 0.96)
- [ERRO] **Testes não-determinísticos**
- [ERRO] **Debugging frustrante**

**Solução:**

```python
# [ERRO] EVITAR
assert similarity == 0.96  # Vai falhar!

# [OK] USAR
import numpy as np
assert np.allclose(similarity, 0.96, atol=1e-6)

# OU
from pytest import approx
assert similarity == approx(0.96, abs=1e-6)
```

**Regra:** **NUNCA** use `==` para floats. **SEMPRE** use `allclose()` ou `approx()`.

**Fonte:** lesson-adaptive-reranking (O Que Não Funcionou #1)

---

## 4. METADADOS E GROUND TRUTH

### [ERRO] ANTIPADRÃO 4.1: Ground Truth Sem document_title

**Problema:**
- Criar benchmark sem campo rastreável (source, title, doc_id)

**Por quê é ruim:**
- [ERRO] **Recall@10 não-validável** (impossível saber se doc correto foi recuperado)
- [ERRO] **Precision@5 não-validável**
- [ERRO] **Benchmark inútil** (métricas 0%)

**Solução:**

```python
# [OK] IMPLEMENTAR ANTES de benchmarks
# 1. Adicionar document_title ao Qdrant payload
# 2. Ground truth usa document_title para match
# 3. Validação objetiva funciona

# Exemplo ground truth
{
  "query_id": "Q001",
  "expected_documents": [
    "The Balanced Scorecard: Translating Strategy into Action",  // title rastreável!
    "Strategy Maps"
  ]
}
```

**Benefício:** Métricas objetivas funcionam

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #3)

---

### [ERRO] ANTIPADRÃO 4.2: Metadados Manuais Apenas

**Problema:**
- Exigir edição manual de index.json para cada documento novo

**Por quê é ruim:**
- [ERRO] **5-10 min manutenção** por documento
- [ERRO] **Erro humano** (esquecimento, typos)
- [ERRO] **Barreira de entrada** (usuário não técnico não consegue)

**Solução:**

```python
# [OK] IMPLEMENTAR auto-geração
# 1. GPT-4o-mini extrai metadados automaticamente
# 2. Salva em index.json (cache)
# 3. Zero manutenção manual

# Custo: ~$0.002/documento (irrisório)
# ROI: 5-10 min economizados/documento
```

**Economia:** 50-100 min em 10-20 docs futuros

**Fonte:** Seção "Auto-Geração de Metadados" do plano

---

## 5. TESTING E VALIDAÇÃO

### [ERRO] ANTIPADRÃO 5.1: Testes Depois da Implementação

**Problema:**
- Implementar funcionalidade completa, DEPOIS criar testes

**Por quê é ruim:**
- [ERRO] **Coverage baixa** (60-80% típico vs 100% TDD)
- [ERRO] **Bugs descobertos tarde** (produção vs desenvolvimento)
- [ERRO] **Design pobre** (código difícil de testar)

**Solução:**

```python
# [OK] TEST-DRIVEN DEVELOPMENT

# 1. Escrever teste PRIMEIRO
def test_calculate_similarity():
    vec1 = np.array([1.0, 0.0])
    vec2 = np.array([1.0, 0.0])

    similarity = reranker._calculate_similarity(vec1, vec2)

    assert np.allclose(similarity, 1.0)

# 2. Implementar função (teste falha -> implementa -> teste passa)
def _calculate_similarity(self, vec1, vec2):
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity([vec1], [vec2])[0][0]

# 3. Coverage naturalmente alto!
```

**Benefícios:**
- [OK] **Coverage 90-100%** (vs 60-80% típico)
- [OK] **Zero bugs** em produção (tudo validado)
- [OK] **Design modular** (código testável)

**ROI:** +4-6h economizadas (debugging evitado)

**Fonte:** lesson-adaptive-reranking (Aprendizado #1)

---

### [ERRO] ANTIPADRÃO 5.2: Testes Sem Mocking de APIs

**Problema:**
- Chamar Cohere API, OpenAI API, Qdrant real em testes

**Por quê é ruim:**
- [ERRO] **Testes lentos** (500ms-1s por API call)
- [ERRO] **Custo $$$** (38 testes = $0.38 se usar API real)
- [ERRO] **Dependência externa** (falha se API offline)
- [ERRO] **Não-reprodutível** (resultados variam)

**Solução:**

```python
# [OK] MOCKAR APIs externas

from unittest.mock import Mock, patch

@patch('cohere.Client')
def test_rerank(mock_cohere_client):
    # Mock response
    mock_client = Mock()
    mock_response = Mock()
    mock_response.results = [Mock(index=0, relevance_score=0.95)]
    mock_client.rerank.return_value = mock_response

    # Teste rápido! (~0.1s vs ~1s real)
    reranker = CohereReranker()
    results = reranker.rerank(query, docs)

    assert len(results) > 0
```

**Benefícios:**
- [OK] **Testes 2-10x mais rápidos**
- [OK] **Custo $0** (sem API calls)
- [OK] **Reprodutível** (sempre mesmo resultado)

**Fonte:** lesson-adaptive-reranking (Aprendizado #4)

---

### [ERRO] ANTIPADRÃO 5.3: Assumir Código Quebrado Antes de Verificar Testes

**Problema:**
- "Heurística não funciona!" -> modificar código -> ainda quebrado -> debugging profundo

**Exemplo Real:**
- should_decompose() reportava 0% accuracy
- Problema: TESTES estavam errados (tupla vs bool), NÃO o código!

**Solução:**

```python
# [OK] WORKFLOW CORRETO

# 1. Teste falha
assert heuristic_accuracy == 100%  # Resultado: 0%

# 2. ANTES de modificar código: VERIFICAR TESTE
# Descoberta: should_decompose() retorna (bool, int) mas teste usa como bool
# Tupla sempre é True em Python!

# 3. Corrigir TESTE (não código)
should_decompose_decision, score = self.decomposer.should_decompose(query)
if should_decompose_decision:  # Correto!
    decompose()

# 4. Teste passa! Código estava correto.
```

**Lição:**
- [OK] **Sempre verificar testes PRIMEIRO** antes de modificar código
- [OK] **Criar scripts de diagnóstico** (diagnose_heuristics.py)
- [OK] **Type hints estritos** evitam bugs (tupla vs bool)

**Economia:** 2h de debugging evitadas

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #5)

---

## 6. PERFORMANCE E CUSTOS

### [ERRO] ANTIPADRÃO 6.1: Retrieval Sequencial para Múltiplas Queries

**Problema:**
- Executar 4 sub-queries sequencialmente

**Por quê é ruim:**
- [ERRO] **Latência 4x maior** (4 × 3s = 12s vs 3-4s paralelo)
- [ERRO] **Não aproveita concorrência**

**Solução:**

```python
# [ERRO] EVITAR
sub_results = []
for sq in sub_queries:
    results = retriever.retrieve(sq)  # Sequencial!
    sub_results.append(results)

# [OK] USAR
sub_results = await asyncio.gather(*[
    retriever.retrieve_async(sq) for sq in sub_queries
])  # Paralelo!
```

**Melhoria:** 3-4x mais rápido

**Fonte:** lesson-query-decomposition (O Que Funcionou #5), MVP AsyncIO (3.34x speedup)

---

### [ERRO] ANTIPADRÃO 6.2: LLM para Classificação Sempre

**Problema:**
- Usar LLM para classificar TODAS queries (não apenas ambíguas)

**Por quê é ruim:**
- [ERRO] **Custo:** $0.0001 × 1000 queries = $0.10/dia = **$3/mês desnecessários**
- [ERRO] **Latência:** ~500ms todas queries vs ~50ms heurísticas

**Solução:**

```python
# [OK] HÍBRIDO: Heurísticas (80%) + LLM Fallback (20%)

def classify(self, query):
    # Tentar heurísticas PRIMEIRO
    category, confidence = self._heuristic_classify(query)

    # SE confiança baixa (<0.8), usar LLM
    if confidence < 0.8:
        return self._llm_classify(query)  # 20% casos

    return category  # 80% casos
```

**Economia:** ~$2.40/mês + latência -70%

**Fonte:** lesson-router (O Que Funcionou #2, Aprendizado #2)

---

## 7. ARQUITETURA E INTEGRAÇÃO

### [ERRO] ANTIPADRÃO 7.1: Integração Invasiva (Modificar MVP)

**Problema:**
- Modificar métodos existentes do MVP para adicionar feature nova

**Por quê é ruim:**
- [ERRO] **Alto risco** de quebrar funcionalidade validada
- [ERRO] **Rollback difícil** (código entrelaçado)
- [ERRO] **Testing complexo** (não sabe se bug é MVP ou feature nova)

**Solução:**

```python
# [ERRO] EVITAR - Modificar método existente
class Orchestrator:
    def invoke(self, state):  # Método MVP
        # MODIFICAR código MVP aqui <- RISCO!
        routing = self.router.route(...)  # Novo código misturado
        ...

# [OK] USAR - Adicionar novo método
class Orchestrator:
    def invoke(self, state):  # Método MVP INTOCADO
        # MVP code inalterado
        ...

    def get_retrieval_strategy_metadata(self):  # NOVO método
        # Feature nova isolada
        if self.router:
            return self.router.route(...)
        return {}  # Fallback
```

**Benefícios:**
- [OK] **MVP preservado** 100%
- [OK] **Rollback fácil** (desabilitar flag)
- [OK] **Zero risco** de quebrar MVP
- [OK] **Testing isolado**

**Fonte:** lesson-router (O Que Funcionou #3)

---

### [ERRO] ANTIPADRÃO 7.2: Feature Sem Feature Flag

**Problema:**
- Implementar feature nova sem toggle de habilitação/desabilitação

**Por quê é ruim:**
- [ERRO] **Rollback requer redeploy** (não pode desabilitar em produção)
- [ERRO] **A/B testing impossível**
- [ERRO] **Gradual rollout impossível** (0% ou 100%, não 10%->50%->100%)

**Solução:**

```python
# [OK] SEMPRE implementar feature flag

# config/settings.py
enable_query_router: bool = True

# .env
ENABLE_QUERY_ROUTER=True  # Toggle fácil!

# Código
if settings.enable_query_router:
    # Feature nova
else:
    # Fallback (MVP ou padrão)
```

**Benefícios:**
- [OK] Rollback instantâneo (mudar .env)
- [OK] A/B testing (50% users com flag True)
- [OK] Gradual rollout (10% -> 100%)
- [OK] Debugging (comparar com/sem feature)

**Fonte:** lesson-router (O Que Funcionou #4)

---

## 8. LLMs E APIS

### [ERRO] ANTIPADRÃO 8.1: AsyncIO Event Loop Duplo

**Problema:**
- `asyncio.run()` dentro de event loop ativo (pytest-asyncio, Jupyter)

**Erro:**
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Solução:**

```python
# [OK] DETECTAR loop e usar ThreadPoolExecutor

import asyncio
import concurrent.futures

def execute_async_safely(coro):
    try:
        loop = asyncio.get_running_loop()
        # Loop ativo! Usar thread separada
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # Sem loop, criar novo
        return asyncio.run(coro)
```

**Aplicação:**
- [OK] DecompositionStrategy (resolvido)
- [OK] Self-RAG (iterações assíncronas)
- [OK] CRAG (re-retrieval assíncrono)

**Fonte:** lesson-router (O Que Funcionou #2, O Que Não Funcionou #2)

---

### [ERRO] ANTIPADRÃO 8.2: Timeout Sem Fallback

**Problema:**
- LLM call sem timeout ou sem fallback se timeout

**Por quê é ruim:**
- [ERRO] **Query travada** (aguarda forever)
- [ERRO] **UX ruim** (loading infinito)
- [ERRO] **Sistema quebrado** por 1 LLM lento

**Solução:**

```python
# [OK] TIMEOUT + FALLBACK

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[...],
        timeout=30  # 30s timeout
    )
    metadata = parse_response(response)
except TimeoutError:
    logger.warning("[TIMEOUT] LLM timeout, usando fallback")
    metadata = {}  # Fallback: metadados vazios (graceful degradation)
```

**Regra:**
- [OK] **Sempre timeout** em LLM calls (10-30s típico)
- [OK] **Sempre fallback** (dict vazio, default, MVP)
- [OK] **Graceful degradation** (sistema continua funcionando)

**Fonte:** Auto-geração metadados (Error Handling)

---

## 9. DOCUMENTAÇÃO E ORGANIZAÇÃO

### [ERRO] ANTIPADRÃO 9.1: Documentar Tudo no Final

**Problema:**
- Implementar 3 técnicas -> Documentar tudo de uma vez

**Por quê é ruim:**
- [ERRO] **Esquece detalhes** (implementou há 2 semanas)
- [ERRO] **Docs incompletas** (decisões arquiteturais perdidas)
- [ERRO] **Bloqueio de tempo** (8h contínuas de docs)

**Solução:**

```
# [OK] DOCUMENTAÇÃO PARALELA

Implementação Router:
├─ Hora 1-2: Código core
├─ Hora 2.5: Docs parciais (arquitetura, como funciona)  <- Paralelo!
├─ Hora 3-4: Strategies
├─ Hora 4.5: Atualizar docs (strategies, exemplos)  <- Paralelo!
├─ Hora 5-6: Testes + integration
└─ Hora 6: Finalizar docs  <- Quick!
```

**Benefícios:**
- [OK] **Código fresco** (fácil documentar)
- [OK] **Docs precisas** (não esquece decisões)
- [OK] **Economia -0.5 dias** vs doc big bang

**Fonte:** lesson-router (O Que Funcionou #5)

---

### [ERRO] ANTIPADRÃO 9.2: Sem Índice de Documentação

**Problema:**
- 30+ documentos sem índice navegável

**Por quê é ruim:**
- [ERRO] **Busca lenta** (Ctrl+F em múltiplos arquivos)
- [ERRO] **Descoberta difícil** ("onde está doc sobre X?")
- [ERRO] **Duplicação** (não sabe que doc já existe)

**Solução:**

```markdown
# [OK] CRIAR DOCS_INDEX.md (TIER 3)

- Tags A-Z (retrieval, reranking, agents, etc)
- Docs por categoria (Techniques, Patterns, History)
- Quick Search Matrix ("Preciso de X" -> "Consulte Y")
```

**ROI:** 3-8 min economizados por busca × 15-25 buscas = **45-200 min**

**Fonte:** TIER 3 Organização (este documento!)

---

## 10. PADRÕES GERAIS RAG

### [ERRO] ANTIPADRÃO 10.1: Over-Engineering (Implementar Tudo)

**Problema:**
- Implementar Graph RAG, Multi-modal RAG, HyDE sem validar necessidade

**Por quê é ruim:**
- [ERRO] **Weeks de trabalho** sem benefício
- [ERRO] **Complexidade** sem ROI
- [ERRO] **Manutenção** de código não-usado

**Solução:**

```
# [OK] DECISÃO DATA-DRIVEN

1. Benchmark baseline
2. Identificar gap (recall <70%? hallucination >10%?)
3. SE gap existe -> implementar técnica específica
4. SE não existe -> SKIP (não implementar)
```

**Exemplo Validado:**
- Graph RAG: **SKIP agora** (dataset inadequado, ROI zero)
- HyDE: **Avaliar SE** recall <70% (condicional Fase 2C)
- Self-RAG: **Implementar SE** faithfulness <0.85 (decisão baseada em benchmark)

**Fonte:** Decisão Arquitetural #2 do plano (Por quê NÃO Graph RAG agora)

---

### [ERRO] ANTIPADRÃO 10.2: Todas Queries Usam Mesma Estratégia

**Problema:**
- Query simples "O que é BSC?" usa workflow completo (4 agents + synthesis + judge)

**Por quê é ruim:**
- [ERRO] **Latência desnecessária** (70s vs <5s ideal)
- [ERRO] **Custo desnecessário** ($0.05 vs $0.000015)
- [ERRO] **UX ruim** (usuário espera 70s para resposta trivial)

**Solução:**

```python
# [OK] QUERY ROUTER (TECH-003)

# Classify query -> Choose optimal strategy
if query_category == SIMPLE_FACTUAL:
    return DirectAnswerStrategy()  # <5s, cache
elif query_category == COMPLEX_MULTI_PART:
    return DecompositionStrategy()  # ~70s, melhor qualidade
else:
    return HybridSearchStrategy()  # Padrão MVP
```

**Benefícios:**
- [OK] **-85% latência** queries simples (70s -> 5s)
- [OK] **-99.7% custo** queries simples ($0.05 -> $0.000015)
- [OK] **UX melhorado** (respostas rápidas para queries simples)

**Fonte:** lesson-router (Descoberta Extraordinária)

---

## [EMOJI] RESUMO - ANTIPADRÕES EVITADOS

### Fase 2A Completa (3 Técnicas)

| Antipadrão | Economia | Fonte |
|------------|----------|-------|
| **GPT-4o para tarefas simples** | $3/mês | Query Decomp |
| **Regex sem word boundaries** | +8% accuracy | Query Decomp + Router |
| **Sub-queries sem contexto** | +15% precision | Query Decomp |
| **Thresholds altos** | Coverage 40% -> 100% | Query Decomp |
| **Reimplementar RRF** | -8h (1 dia) | Query Decomp |
| **Testes depois** | +4-6h (bugs evitados) | Adaptive Re-rank |
| **Embeddings não-normalizados** | Estabilidade numérica | Adaptive Re-rank |
| **Float `==`** | Testes estáveis | Adaptive Re-rank |
| **Sem mocking APIs** | Testes 2-10x rápidos | Adaptive Re-rank |
| **Integração invasiva** | MVP preservado | Router |
| **Sem feature flags** | Rollback fácil | Router |
| **AsyncIO event loop duplo** | -2h debugging | Router |
| **Reutilização <50%** | -5 dias (70% reuso) | Router |

**Total Economia Estimada:** 6-8 dias de trabalho (48-64h)

---

## [EMOJI] TOP 10 REGRAS DE OURO RAG

**Checklist antes de implementar qualquer técnica:**

1. [OK] **Heurísticas PRIMEIRO, LLM fallback** (80% accuracy, custo $0)
2. [OK] **Reutilizar componentes** agressivamente (70% reuso = -5 dias)
3. [OK] **Test-Driven Development** (testes durante, não depois)
4. [OK] **Mockar APIs externas** em testes (2-10x mais rápido)
5. [OK] **Word boundaries em regex** (`\b` sempre)
6. [OK] **AsyncIO paralelo** quando possível (3-4x speedup)
7. [OK] **Feature flags** em todas features (rollback fácil)
8. [OK] **Integração não-invasiva** (preservar MVP)
9. [OK] **Documentação paralela** (durante implementação)
10. [OK] **Decisão data-driven** (benchmark -> implementar SE necessário)

---

## [EMOJI] REFERÊNCIAS

### Lições Aprendidas

- `docs/lessons/lesson-query-decomposition-2025-10-14.md`
- `docs/lessons/lesson-adaptive-reranking-2025-10-14.md`
- `docs/lessons/lesson-router-2025-10-14.md`
- `docs/lessons/lesson-e2e-validation-corrections-2025-10-14.md`

### Técnicas

- `docs/techniques/QUERY_DECOMPOSITION.md`
- `docs/techniques/ADAPTIVE_RERANKING.md`
- `docs/techniques/ROUTER.md`

### Plano

- `.cursor/plans/fase-2-rag-avancado.plan.md` - Decisões Arquiteturais

### Rules

- `.cursor/rules/rag-bsc-core.mdc` - Workflow 7 steps
- `.cursor/rules/rag-techniques-catalog.mdc` - Catálogo técnicas

---

## [EMOJI] PRÓXIMOS PASSOS

### Usar em Fase 2B:

1. [OK] Revisar este doc ANTES de implementar Self-RAG
2. [OK] Checklist de antipadrões antes de merge
3. [OK] Adicionar novos antipadrões descobertos (documento vivo)

### Adicionar Futuramente:

- Antipadrão: CRAG sem web search (quando adicionar CRAG)
- Antipadrão: Self-RAG sem max_iterations (quando adicionar Self-RAG)
- Antipadrão: [Novos descobertos na Fase 2B]

---

**Criado:** 2025-10-14
**Autor:** Claude Sonnet 4.5 (via Cursor)
**Tipo:** Documento Vivo (atualizar com novas descobertas)
