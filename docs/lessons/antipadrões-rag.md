# ❌ ANTIPADRÕES RAG - BSC Project

**Data:** 2025-10-16 (Atualizado com FASE 2.5)  
**Fonte:** Lições aprendidas Fase 2A + 2.5 (Query Decomposition, Adaptive Re-ranking, Router, DiagnosticAgent Testing)  
**Objetivo:** Documentar armadilhas evitadas para acelerar Fase 2B e projetos futuros  
**Total:** 39 antipadrões catalogados (32 originais + 7 testing FASE 2.5)

---

## 🎯 COMO USAR ESTE DOCUMENTO

**Checklist antes de implementar qualquer técnica RAG:**

1. ✅ Revisar seção relevante (Query Enhancement, Retrieval, Re-ranking, Testing)
2. ✅ Verificar se antipadrão se aplica à técnica
3. ✅ Implementar solução recomendada
4. ✅ Validar que antipadrão foi evitado

**ROI:** Evitar 1 antipadrão = economia de 2-8h debugging/refactoring

---

## 📋 ÍNDICE DE ANTIPADRÕES

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

### ❌ ANTIPADRÃO 1.1: Usar GPT-4o para Tarefas Simples

**Problema:**
- Usar GPT-4o/GPT-5 para decomposição, classificação, extração

**Por quê é ruim:**
- ❌ **Custo 100x maior** ($0.01 vs $0.0001 GPT-4o-mini)
- ❌ **Latência +40%** (~2s vs ~1.2s)
- ❌ **Qualidade similar** (não justifica custo)

**Solução:**

```python
# ❌ EVITAR
decomposer = QueryDecomposer(llm="gpt-4o")  # Caro!

# ✅ USAR
decomposer = QueryDecomposer(llm="gpt-4o-mini")  # 100x mais barato

# Reservar GPT-4o/GPT-5 para:
# - Synthesis complexa
# - Generation final de respostas
# - Reasoning multi-step avançado
```

**Economia:** $9.90/dia em 1000 queries

**Fonte:** lesson-query-decomposition (Aprendizado #3)

---

### ❌ ANTIPADRÃO 1.2: Regex Sem Word Boundaries

**Problema:**
- Regex `"e" in query` detecta falsos positivos ("é", "presente", "mente")

**Por quê é ruim:**
- ❌ **-8% accuracy** em classificação
- ❌ **Falsos positivos** abundantes
- ❌ **Heurística não-confiável**

**Solução:**

```python
# ❌ EVITAR
if "e" in query.lower():
    score += 1  # Detecta "é", "presente", "mente"!

# ✅ USAR
import re
if re.search(r'\be\b', query.lower()):  # Word boundaries!
    score += 1  # Só detecta " e " isolado
```

**Melhoria:** +8% accuracy

**Fonte:** lesson-query-decomposition (Aprendizado #4), lesson-router (Aprendizado #4)

---

### ❌ ANTIPADRÃO 1.3: Sub-Queries Sem Contexto

**Problema:**
- Sub-queries isoladas perdem especificidade da query original

**Exemplo:**

```python
# ❌ EVITAR
Query original: "Como implementar BSC em manufatura?"
Sub-queries isoladas:
- "Quais KPIs financeiros?" ← Perdeu "manufatura"!
- "Como medir processos?" ← Perdeu "manufatura"!

# ✅ USAR
Sub-queries contextualizadas:
- "Quais KPIs financeiros em manufatura?"
- "Como medir processos em manufatura?"
```

**Impacto:** +15% precision

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #2)

---

### ❌ ANTIPADRÃO 1.4: Thresholds Altos Sem Validação

**Problema:**
- Definir thresholds arbitrariamente sem testar com dataset

**Exemplo:**

```python
# ❌ EVITAR
DECOMPOSITION_SCORE_THRESHOLD=2  # Arbitrário!
# Resultado: Coverage 40% (queries válidas não decompostas)

# ✅ USAR
DECOMPOSITION_SCORE_THRESHOLD=1  # Testado com dataset
# Resultado: Coverage 100%
```

**Regra:**
- ✅ Começar com thresholds **BAIXOS** e aumentar se necessário
- ✅ Validar coverage com dataset variado (50+ queries)
- ✅ A/B testing com thresholds diferentes

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #4)

---

## 2. RETRIEVAL E BUSCA

### ❌ ANTIPADRÃO 2.1: Reimplementar Funcionalidades Existentes

**Problema:**
- Implementar RRF do zero quando já existe

**Por quê é ruim:**
- ❌ **+1 dia desenvolvimento** desnecessário
- ❌ **Bugs novos** (não validado)
- ❌ **Duplicação de código**

**Solução:**

```python
# ❌ EVITAR
def my_own_rrf(results_list):  # Reimplementar RRF
    # ... 100 linhas de código novo (não testado)

# ✅ USAR
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()
fused = retriever.reciprocal_rank_fusion(results_list)  # Reutilizar!
```

**Economia:** 8h (1 dia de trabalho)

**Fonte:** lesson-query-decomposition (O Que Funcionou #2)

---

### ❌ ANTIPADRÃO 2.2: Retrieval Sem Metadados

**Problema:**
- Não usar metadados (title, authors, year, perspectives) para ground truth e filtros

**Por quê é ruim:**
- ❌ **Métricas não-validáveis** (Recall/Precision 0%)
- ❌ **Filtros avançados impossíveis**
- ❌ **UI pobre** (filenames longos vs títulos)

**Solução:**

```python
# ✅ IMPLEMENTAR
# 1. Criar index.json com metadados
# 2. Auto-geração com LLM para docs novos
# 3. document_title SEMPRE presente
# 4. Usar filtros em retrieval
```

**Benefícios:**
- ✅ Ground truth validável
- ✅ Filtros por autor/ano/tipo/perspectiva
- ✅ UI profissional

**Fonte:** Seção "MELHORIAS DE INFRAESTRUTURA" do plano

---

## 3. RE-RANKING E DIVERSIDADE

### ❌ ANTIPADRÃO 3.1: Embeddings Não-Normalizados

**Problema:**
- Usar embeddings raw em MMR ou similaridade cosseno

**Por quê é ruim:**
- ❌ **Erros numéricos** (underflow, overflow)
- ❌ **Similaridade incorreta** (valores fora de 0-1)
- ❌ **MMR instável**

**Solução:**

```python
# ❌ EVITAR
similarity = cosine_similarity(emb1, emb2)  # Embeddings raw

# ✅ USAR
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

### ❌ ANTIPADRÃO 3.2: Float Comparisons com `==`

**Problema:**
- Usar `assert similarity == 0.96` em testes

**Por quê é ruim:**
- ❌ **Falhas spurias** (0.9599999... ≠ 0.96)
- ❌ **Testes não-determinísticos**
- ❌ **Debugging frustrante**

**Solução:**

```python
# ❌ EVITAR
assert similarity == 0.96  # Vai falhar!

# ✅ USAR
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

### ❌ ANTIPADRÃO 4.1: Ground Truth Sem document_title

**Problema:**
- Criar benchmark sem campo rastreável (source, title, doc_id)

**Por quê é ruim:**
- ❌ **Recall@10 não-validável** (impossível saber se doc correto foi recuperado)
- ❌ **Precision@5 não-validável**
- ❌ **Benchmark inútil** (métricas 0%)

**Solução:**

```python
# ✅ IMPLEMENTAR ANTES de benchmarks
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

### ❌ ANTIPADRÃO 4.2: Metadados Manuais Apenas

**Problema:**
- Exigir edição manual de index.json para cada documento novo

**Por quê é ruim:**
- ❌ **5-10 min manutenção** por documento
- ❌ **Erro humano** (esquecimento, typos)
- ❌ **Barreira de entrada** (usuário não técnico não consegue)

**Solução:**

```python
# ✅ IMPLEMENTAR auto-geração
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

### ❌ ANTIPADRÃO 5.1: Testes Depois da Implementação

**Problema:**
- Implementar funcionalidade completa, DEPOIS criar testes

**Por quê é ruim:**
- ❌ **Coverage baixa** (60-80% típico vs 100% TDD)
- ❌ **Bugs descobertos tarde** (produção vs desenvolvimento)
- ❌ **Design pobre** (código difícil de testar)

**Solução:**

```python
# ✅ TEST-DRIVEN DEVELOPMENT

# 1. Escrever teste PRIMEIRO
def test_calculate_similarity():
    vec1 = np.array([1.0, 0.0])
    vec2 = np.array([1.0, 0.0])
    
    similarity = reranker._calculate_similarity(vec1, vec2)
    
    assert np.allclose(similarity, 1.0)

# 2. Implementar função (teste falha → implementa → teste passa)
def _calculate_similarity(self, vec1, vec2):
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity([vec1], [vec2])[0][0]

# 3. Coverage naturalmente alto!
```

**Benefícios:**
- ✅ **Coverage 90-100%** (vs 60-80% típico)
- ✅ **Zero bugs** em produção (tudo validado)
- ✅ **Design modular** (código testável)

**ROI:** +4-6h economizadas (debugging evitado)

**Fonte:** lesson-adaptive-reranking (Aprendizado #1)

---

### ❌ ANTIPADRÃO 5.2: Testes Sem Mocking de APIs

**Problema:**
- Chamar Cohere API, OpenAI API, Qdrant real em testes

**Por quê é ruim:**
- ❌ **Testes lentos** (500ms-1s por API call)
- ❌ **Custo $$$** (38 testes = $0.38 se usar API real)
- ❌ **Dependência externa** (falha se API offline)
- ❌ **Não-reprodutível** (resultados variam)

**Solução:**

```python
# ✅ MOCKAR APIs externas

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
- ✅ **Testes 2-10x mais rápidos**
- ✅ **Custo $0** (sem API calls)
- ✅ **Reprodutível** (sempre mesmo resultado)

**Fonte:** lesson-adaptive-reranking (Aprendizado #4)

---

### ❌ ANTIPADRÃO 5.3: Assumir Código Quebrado Antes de Verificar Testes

**Problema:**
- "Heurística não funciona!" → modificar código → ainda quebrado → debugging profundo

**Exemplo Real:**
- should_decompose() reportava 0% accuracy
- Problema: TESTES estavam errados (tupla vs bool), NÃO o código!

**Solução:**

```python
# ✅ WORKFLOW CORRETO

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
- ✅ **Sempre verificar testes PRIMEIRO** antes de modificar código
- ✅ **Criar scripts de diagnóstico** (diagnose_heuristics.py)
- ✅ **Type hints estritos** evitam bugs (tupla vs bool)

**Economia:** 2h de debugging evitadas

**Fonte:** lesson-query-decomposition (O Que Não Funcionou #5)

---

### ❌ ANTIPADRÃO 5.4: Não Aplicar Checklist Antes de Escrever Testes ⚠️ **CRÍTICO**

**Problema:**
- Escrever testes ANTES de aplicar [[memory:9969868]] - Checklist de 8 pontos

**Por quê é ruim:**
- ❌ **38 minutos perdidos** em debugging evitável (FASE 2.5 validado)
- ❌ **7 problemas previsíveis** (assinatura incorreta, dados inválidos, decorators)
- ❌ **Retrabalho constante**

**Solução:**

```python
# ✅ CHECKLIST ANTES (não durante ou depois!)

# 1. Ler assinatura completa
grep "def analyze_perspective" src/agents/diagnostic_agent.py -A 10
# Output: def analyze_perspective(self, perspective, client_profile, state) -> DiagnosticResult

# 2. Verificar tipo retorno
# DiagnosticResult (Pydantic BaseModel)

# 3. Contar parâmetros (não contar self)
# 3 params: perspective, client_profile, state

# 4. Validações pré-flight
# - perspective: Literal["Financeira", "Clientes", ...]
# - current_state: min_length=20
# - gaps: min 3 items

# 5. Entender decorators
# @retry(reraise=True) → relança ValidationError, NÃO RetryError!

# 6-8. Fixtures, Dados Válidos, Método Correto
# ...

# AGORA escrever teste!
def test_analyze_perspective():
    # Teste baseado em conhecimento COMPLETO
    pass
```

**Benefícios:**
- ✅ **38 minutos economizados** por implementação
- ✅ **95% problemas evitados**
- ✅ **Testes corretos primeira tentativa**

**ROI:** 10:1 (10 min checklist vs 40 min debugging)

**Fonte:** lesson-diagnostic-agent-test-methodology (Custo Real vs Evitável)

---

### ❌ ANTIPADRÃO 5.5: Assumir Nome de Método Sem Verificar

**Problema:**
- Assumir que specialist agents têm `process_query()` sem grep

**Erro Real:**
```python
AttributeError: 'FinancialAgent' object has no attribute 'process_query'
```

**Por quê é ruim:**
- ❌ **8 minutos perdidos** por erro (FASE 2.5)
- ❌ **Múltiplas ocorrências** (código + testes)
- ❌ **100% evitável** com 30 segundos de grep

**Solução:**

```python
# ✅ VERIFICAR ASSINATURA ANTES

# Comando:
grep "def " src/agents/financial_agent.py -C 2

# Output:
# def invoke(self, query: str) -> dict:  ← MÉTODO CORRETO!
#     """Processa query e retorna resposta."""

# Agora usar no código/testes:
specialist_agent.invoke(query)  # ✅ Correto

# ❌ NUNCA:
specialist_agent.process_query(state, query)  # Método não existe!
```

**Economia:** 8 minutos por erro evitado

**Fonte:** lesson-diagnostic-agent-test-methodology (Problema #3)

---

### ❌ ANTIPADRÃO 5.6: Dados Inválidos em Fixtures Pydantic

**Problema:**
- Criar fixtures Pydantic com dados que FALHAM validações

**Erro Real:**
```python
ValidationError: current_state
  String should have at least 20 characters [type=string_too_short]
```

**Por quê é ruim:**
- ❌ **6 minutos perdidos** por fixture (FASE 2.5)
- ❌ **Múltiplas fixtures** precisam correção
- ❌ **Não testa código, testa Pydantic** (desnecessário)

**Solução:**

```python
# ❌ EVITAR - Dados mínimos ou inválidos
@pytest.fixture
def sample_diagnostic_result():
    return DiagnosticResult(
        perspective="Financeira",
        current_state="Financial state",  # 15 chars < 20 MIN! ❌
        gaps=["Gap 1"],  # <3 items (field_validator requer 3+)
        ...
    )

# ✅ USAR - Dados com MARGEM DE SEGURANÇA
@pytest.fixture
def sample_diagnostic_result():
    return DiagnosticResult(
        perspective="Financeira",
        current_state="Estado financeiro detalhado da empresa com contexto completo",  # 66 chars ✅
        gaps=["Gap 1", "Gap 2", "Gap 3", "Gap 4", "Gap 5"],  # 5 items (margem segurança) ✅
        opportunities=["Opp A", "Opp B", "Opp C"],  # Múltiplos
        priority="HIGH",
        key_insights=["Insight X", "Insight Y"],
    )
```

**Regra Geral:**
- ✅ **Se min_length=20 → usar 50+ chars**
- ✅ **Se min_items=3 → usar 5+ items**
- ✅ **Margem de segurança > requisito mínimo**

**Economia:** 6 minutos por fixture

**Fonte:** lesson-diagnostic-agent-test-methodology (Problema #4)

---

### ❌ ANTIPADRÃO 5.7: Ignorar Campos Obrigatórios em Fixtures

**Problema:**
- Omitir campos obrigatórios (sem default) em fixtures Pydantic

**Erro Real:**
```python
TypeError: BSCState.__init__() missing 1 required positional argument: 'query'
```

**Por quê é ruim:**
- ❌ **4 minutos perdidos** por fixture (FASE 2.5)
- ❌ **Erro confuso** (TypeError vs campo ausente)
- ❌ **Múltiplos testes quebrados**

**Solução:**

```python
# ✅ VERIFICAR SCHEMA ANTES

# Verificar campos obrigatórios:
grep "class BSCState" src/graph/states.py -A 15

# Output:
# query: str = Field(..., description="Query do usuário")  ← SEM DEFAULT = OBRIGATÓRIO!
# conversation_history: list[dict] = Field(default_factory=list)  ← TEM DEFAULT = OPCIONAL

# ❌ EVITAR - Omitir query
@pytest.fixture
def sample_bsc_state():
    return BSCState(
        conversation_history=[],
        # query faltando! ← ERRO
    )

# ✅ USAR - Incluir TODOS campos obrigatórios
@pytest.fixture
def sample_bsc_state():
    return BSCState(
        query="Como implementar BSC?",  # ✅ Campo obrigatório
        conversation_history=[],
        client_profile=None,  # Opcional mas explícito
    )
```

**Economia:** 4 minutos por erro evitado

**Fonte:** lesson-diagnostic-agent-test-methodology (Problema #5)

---

### ❌ ANTIPADRÃO 5.8: Não Entender Comportamento de Decorators

**Problema:**
- Não estudar decorators (@retry, @cache) ANTES de testar

**Erro Real:**
```python
# Esperado: RetryError
# Real: ValidationError relançada!
```

**Por quê é ruim:**
- ❌ **10 minutos perdidos** (FASE 2.5)
- ❌ **Testes incorretos** (espera tipo errado de exceção)
- ❌ **Debugging confuso** (por quê lança ValidationError?)

**Solução:**

```python
# ✅ ESTUDAR DECORATOR ANTES

# Decorator no código:
@retry(
    stop=stop_after_attempt(3),
    reraise=True  # ← IMPORTANTE!
)
def analyze_perspective(...):
    # Pode lançar ValidationError
    pass

# Comportamento:
# - Tentativa 1: ValidationError → retry
# - Tentativa 2: ValidationError → retry
# - Tentativa 3: ValidationError → RELANÇA ValidationError (NÃO RetryError!)

# ❌ TESTE ERRADO
def test_retry():
    with pytest.raises(RetryError):  # Espera tipo errado!
        agent.analyze_perspective(...)

# ✅ TESTE CORRETO
def test_retry():
    with pytest.raises(ValidationError):  # Exceção ORIGINAL ✅
        agent.analyze_perspective(...)

# Nota: Se reraise=False (padrão), lançaria RetryError
```

**Economia:** 10 minutos por erro evitado

**Fonte:** lesson-diagnostic-agent-test-methodology (Problema #6)

---

### ❌ ANTIPADRÃO 5.9: Criar ValidationError Manualmente em Testes

**Problema:**
- Tentar criar `ValidationError` manualmente com sintaxe complexa

**Erro Real:**
```python
TypeError: ValidationError.from_exception_data() missing required argument: 'input_type'
```

**Por quê é ruim:**
- ❌ **4 minutos perdidos** por teste (FASE 2.5)
- ❌ **Sintaxe complexa** propenso a erros
- ❌ **Abordagem frágil** (muda entre versões Pydantic)

**Solução:**

```python
# ❌ EVITAR - Criar ValidationError manualmente
def test_validation():
    def mock_invoke_error():
        raise ValidationError.from_exception_data(
            "test",
            [{"type": "value_error", "loc": ("test",), ...}]  # Complexo!
        )

# ✅ USAR - Passar dados inválidos e deixar Pydantic lançar
def test_validation():
    with pytest.raises(ValidationError):
        DiagnosticResult(
            perspective="INVALID",  # Não está no Literal ← Pydantic lança auto!
            current_state="Short",  # <20 chars
            gaps=[],  # Lista vazia (<3 items)
            ...
        )
    # Pydantic lança ValidationError AUTOMATICAMENTE ✅
```

**Benefícios:**
- ✅ **Teste mais limpo** (dados inválidos vs exceção manual)
- ✅ **Resiliente** (funciona em qualquer versão Pydantic)
- ✅ **Testa validação REAL**

**Economia:** 4 minutos por teste

**Fonte:** lesson-diagnostic-agent-test-methodology (Problema #7)

---

### ❌ ANTIPADRÃO 5.10: Traceback Truncado em Debugging ⚠️ **CRÍTICO**

**Problema:**
- Usar `--tb=short`, `Select-Object`, `Select-String` ao debuggar testes

**Por quê é ruim:**
- ❌ **60+ minutos perdidos** por sessão (estimado FASE 2.5)
- ❌ **Informação crítica oculta** (stack trace, valores, contexto)
- ❌ **Causa raiz invisível**

**Comandos ERRADOS:**
```bash
# ❌ NUNCA USAR
pytest tests/file.py --tb=short  # Trunca traceback!
pytest tests/file.py -v | Select-Object -First 50  # Oculta linhas!
pytest tests/file.py 2>&1 | Select-String -Pattern "FAILED"  # Filtra output!
```

**Comando CORRETO:**
```bash
# ✅ SEMPRE USAR
pytest tests/file.py -v --tb=long 2>&1
# SEM filtros! SEM truncamento! SEM head/tail!
```

**Exemplo Real:**
```
# --tb=long revela:
AttributeError: 'FinancialAgent' object has no attribute 'process_query'
  File "src/agents/diagnostic_agent.py", line 174, in analyze_perspective
    context_response = specialist_agent.process_query(state, query)  ← LINHA EXATA!

# --tb=short ocultaria a linha 174, perderia 10+ minutos procurando erro
```

**Benefícios:**
- ✅ **Causa raiz em 1-2 min** (vs 10-15 min com traceback truncado)
- ✅ **Stack trace completo**
- ✅ **Valores de variáveis visíveis**

**ROI:** 60+ minutos economizados por sessão

**Fonte:** lesson-diagnostic-agent-test-methodology (Metodologia #1) + [[memory:9969628]]

---

## 6. PERFORMANCE E CUSTOS

### ❌ ANTIPADRÃO 6.1: Retrieval Sequencial para Múltiplas Queries

**Problema:**
- Executar 4 sub-queries sequencialmente

**Por quê é ruim:**
- ❌ **Latência 4x maior** (4 × 3s = 12s vs 3-4s paralelo)
- ❌ **Não aproveita concorrência**

**Solução:**

```python
# ❌ EVITAR
sub_results = []
for sq in sub_queries:
    results = retriever.retrieve(sq)  # Sequencial!
    sub_results.append(results)

# ✅ USAR
sub_results = await asyncio.gather(*[
    retriever.retrieve_async(sq) for sq in sub_queries
])  # Paralelo!
```

**Melhoria:** 3-4x mais rápido

**Fonte:** lesson-query-decomposition (O Que Funcionou #5), MVP AsyncIO (3.34x speedup)

---

### ❌ ANTIPADRÃO 6.2: LLM para Classificação Sempre

**Problema:**
- Usar LLM para classificar TODAS queries (não apenas ambíguas)

**Por quê é ruim:**
- ❌ **Custo:** $0.0001 × 1000 queries = $0.10/dia = **$3/mês desnecessários**
- ❌ **Latência:** ~500ms todas queries vs ~50ms heurísticas

**Solução:**

```python
# ✅ HÍBRIDO: Heurísticas (80%) + LLM Fallback (20%)

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

### ❌ ANTIPADRÃO 7.1: Integração Invasiva (Modificar MVP)

**Problema:**
- Modificar métodos existentes do MVP para adicionar feature nova

**Por quê é ruim:**
- ❌ **Alto risco** de quebrar funcionalidade validada
- ❌ **Rollback difícil** (código entrelaçado)
- ❌ **Testing complexo** (não sabe se bug é MVP ou feature nova)

**Solução:**

```python
# ❌ EVITAR - Modificar método existente
class Orchestrator:
    def invoke(self, state):  # Método MVP
        # MODIFICAR código MVP aqui ← RISCO!
        routing = self.router.route(...)  # Novo código misturado
        ...

# ✅ USAR - Adicionar novo método
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
- ✅ **MVP preservado** 100%
- ✅ **Rollback fácil** (desabilitar flag)
- ✅ **Zero risco** de quebrar MVP
- ✅ **Testing isolado**

**Fonte:** lesson-router (O Que Funcionou #3)

---

### ❌ ANTIPADRÃO 7.2: Feature Sem Feature Flag

**Problema:**
- Implementar feature nova sem toggle de habilitação/desabilitação

**Por quê é ruim:**
- ❌ **Rollback requer redeploy** (não pode desabilitar em produção)
- ❌ **A/B testing impossível**
- ❌ **Gradual rollout impossível** (0% ou 100%, não 10%→50%→100%)

**Solução:**

```python
# ✅ SEMPRE implementar feature flag

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
- ✅ Rollback instantâneo (mudar .env)
- ✅ A/B testing (50% users com flag True)
- ✅ Gradual rollout (10% → 100%)
- ✅ Debugging (comparar com/sem feature)

**Fonte:** lesson-router (O Que Funcionou #4)

---

## 8. LLMs E APIS

### ❌ ANTIPADRÃO 8.1: AsyncIO Event Loop Duplo

**Problema:**
- `asyncio.run()` dentro de event loop ativo (pytest-asyncio, Jupyter)

**Erro:**
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Solução:**

```python
# ✅ DETECTAR loop e usar ThreadPoolExecutor

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
- ✅ DecompositionStrategy (resolvido)
- ✅ Self-RAG (iterações assíncronas)
- ✅ CRAG (re-retrieval assíncrono)

**Fonte:** lesson-router (O Que Funcionou #2, O Que Não Funcionou #2)

---

### ❌ ANTIPADRÃO 8.2: Timeout Sem Fallback

**Problema:**
- LLM call sem timeout ou sem fallback se timeout

**Por quê é ruim:**
- ❌ **Query travada** (aguarda forever)
- ❌ **UX ruim** (loading infinito)
- ❌ **Sistema quebrado** por 1 LLM lento

**Solução:**

```python
# ✅ TIMEOUT + FALLBACK

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
- ✅ **Sempre timeout** em LLM calls (10-30s típico)
- ✅ **Sempre fallback** (dict vazio, default, MVP)
- ✅ **Graceful degradation** (sistema continua funcionando)

**Fonte:** Auto-geração metadados (Error Handling)

---

## 9. DOCUMENTAÇÃO E ORGANIZAÇÃO

### ❌ ANTIPADRÃO 9.1: Documentar Tudo no Final

**Problema:**
- Implementar 3 técnicas → Documentar tudo de uma vez

**Por quê é ruim:**
- ❌ **Esquece detalhes** (implementou há 2 semanas)
- ❌ **Docs incompletas** (decisões arquiteturais perdidas)
- ❌ **Bloqueio de tempo** (8h contínuas de docs)

**Solução:**

```
# ✅ DOCUMENTAÇÃO PARALELA

Implementação Router:
├─ Hora 1-2: Código core
├─ Hora 2.5: Docs parciais (arquitetura, como funciona)  ← Paralelo!
├─ Hora 3-4: Strategies
├─ Hora 4.5: Atualizar docs (strategies, exemplos)  ← Paralelo!
├─ Hora 5-6: Testes + integration
└─ Hora 6: Finalizar docs  ← Quick!
```

**Benefícios:**
- ✅ **Código fresco** (fácil documentar)
- ✅ **Docs precisas** (não esquece decisões)
- ✅ **Economia -0.5 dias** vs doc big bang

**Fonte:** lesson-router (O Que Funcionou #5)

---

### ❌ ANTIPADRÃO 9.2: Sem Índice de Documentação

**Problema:**
- 30+ documentos sem índice navegável

**Por quê é ruim:**
- ❌ **Busca lenta** (Ctrl+F em múltiplos arquivos)
- ❌ **Descoberta difícil** ("onde está doc sobre X?")
- ❌ **Duplicação** (não sabe que doc já existe)

**Solução:**

```markdown
# ✅ CRIAR DOCS_INDEX.md (TIER 3)

- Tags A-Z (retrieval, reranking, agents, etc)
- Docs por categoria (Techniques, Patterns, History)
- Quick Search Matrix ("Preciso de X" → "Consulte Y")
```

**ROI:** 3-8 min economizados por busca × 15-25 buscas = **45-200 min**

**Fonte:** TIER 3 Organização (este documento!)

---

## 10. PADRÕES GERAIS RAG

### ❌ ANTIPADRÃO 10.1: Over-Engineering (Implementar Tudo)

**Problema:**
- Implementar Graph RAG, Multi-modal RAG, HyDE sem validar necessidade

**Por quê é ruim:**
- ❌ **Weeks de trabalho** sem benefício
- ❌ **Complexidade** sem ROI
- ❌ **Manutenção** de código não-usado

**Solução:**

```
# ✅ DECISÃO DATA-DRIVEN

1. Benchmark baseline
2. Identificar gap (recall <70%? hallucination >10%?)
3. SE gap existe → implementar técnica específica
4. SE não existe → SKIP (não implementar)
```

**Exemplo Validado:**
- Graph RAG: **SKIP agora** (dataset inadequado, ROI zero)
- HyDE: **Avaliar SE** recall <70% (condicional Fase 2C)
- Self-RAG: **Implementar SE** faithfulness <0.85 (decisão baseada em benchmark)

**Fonte:** Decisão Arquitetural #2 do plano (Por quê NÃO Graph RAG agora)

---

### ❌ ANTIPADRÃO 10.2: Todas Queries Usam Mesma Estratégia

**Problema:**
- Query simples "O que é BSC?" usa workflow completo (4 agents + synthesis + judge)

**Por quê é ruim:**
- ❌ **Latência desnecessária** (70s vs <5s ideal)
- ❌ **Custo desnecessário** ($0.05 vs $0.000015)
- ❌ **UX ruim** (usuário espera 70s para resposta trivial)

**Solução:**

```python
# ✅ QUERY ROUTER (TECH-003)

# Classify query → Choose optimal strategy
if query_category == SIMPLE_FACTUAL:
    return DirectAnswerStrategy()  # <5s, cache
elif query_category == COMPLEX_MULTI_PART:
    return DecompositionStrategy()  # ~70s, melhor qualidade
else:
    return HybridSearchStrategy()  # Padrão MVP
```

**Benefícios:**
- ✅ **-85% latência** queries simples (70s → 5s)
- ✅ **-99.7% custo** queries simples ($0.05 → $0.000015)
- ✅ **UX melhorado** (respostas rápidas para queries simples)

**Fonte:** lesson-router (Descoberta Extraordinária)

---

## 📊 RESUMO - ANTIPADRÕES EVITADOS

### Fase 2A Completa (3 Técnicas)

| Antipadrão | Economia | Fonte |
|------------|----------|-------|
| **GPT-4o para tarefas simples** | $3/mês | Query Decomp |
| **Regex sem word boundaries** | +8% accuracy | Query Decomp + Router |
| **Sub-queries sem contexto** | +15% precision | Query Decomp |
| **Thresholds altos** | Coverage 40% → 100% | Query Decomp |
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

## 🎓 TOP 10 REGRAS DE OURO RAG

**Checklist antes de implementar qualquer técnica:**

1. ✅ **Heurísticas PRIMEIRO, LLM fallback** (80% accuracy, custo $0)
2. ✅ **Reutilizar componentes** agressivamente (70% reuso = -5 dias)
3. ✅ **Test-Driven Development** (testes durante, não depois)
4. ✅ **Mockar APIs externas** em testes (2-10x mais rápido)
5. ✅ **Word boundaries em regex** (`\b` sempre)
6. ✅ **AsyncIO paralelo** quando possível (3-4x speedup)
7. ✅ **Feature flags** em todas features (rollback fácil)
8. ✅ **Integração não-invasiva** (preservar MVP)
9. ✅ **Documentação paralela** (durante implementação)
10. ✅ **Decisão data-driven** (benchmark → implementar SE necessário)

---

## 📚 REFERÊNCIAS

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

## 📝 PRÓXIMOS PASSOS

### Usar em Fase 2B:

1. ✅ Revisar este doc ANTES de implementar Self-RAG
2. ✅ Checklist de antipadrões antes de merge
3. ✅ Adicionar novos antipadrões descobertos (documento vivo)

### Adicionar Futuramente:

- Antipadrão: CRAG sem web search (quando adicionar CRAG)
- Antipadrão: Self-RAG sem max_iterations (quando adicionar Self-RAG)
- Antipadrão: [Novos descobertos na Fase 2B]

---

**Criado:** 2025-10-14  
**Autor:** Claude Sonnet 4.5 (via Cursor)  
**Tipo:** Documento Vivo (atualizar com novas descobertas)


