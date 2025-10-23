# PROMPT DE CONTINUIDADE - BLOCO 2 Onboarding Conversacional

**Branch:** `feature/onboarding-conversational-redesign`  
**Status:** 87% COMPLETO (34/39 testes passando)  
**Tempo Pendente:** 1h 30min (mocks 30min + benchmark 30min + commit 30min)  
**Data Sessao Anterior:** 23/10/2025 (8h 30min trabalho)

---

## 🎯 MISSÃO: FINALIZAR BLOCO 2 (13% RESTANTE)

**Objetivo:** Corrigir 5 mocks AsyncMock nos testes E2E, validar 39/39 testes (100%), executar benchmark UX, commit final.

---

## 📊 STATUS ATUAL (O QUE JÁ FOI FEITO)

### ✅ BLOCO 1 - COMPLETO 100% (5h trabalho)

**Implementado:**
- ✅ 3 métodos core: `_extract_all_entities()`, `_analyze_conversation_context()`, `_generate_contextual_response()`
- ✅ 6 métodos helpers: `_calculate_completeness()`, `_calculate_missing_info()`, `_format_conversation_history()`, `_get_fallback_response()`
- ✅ 2 schemas Pydantic: `ExtractedEntities`, `ConversationContext` (src/memory/schemas.py linhas 2421-2588)
- ✅ 3 prompts ICL: `EXTRACT_ALL_ENTITIES_PROMPT`, `ANALYZE_CONVERSATION_CONTEXT_PROMPT`, `GENERATE_CONTEXTUAL_RESPONSE_PROMPT` (src/prompts/client_profile_prompts.py linhas 516-929)
- ✅ 9 smoke tests passando (100% mockados, zero custo API)
- ✅ 5 bugs pré-existentes resolvidos (mocks sem .model_dump())

**Testes:** 33/33 passando (100%)  
**Coverage:** 19% → 40% (+21pp onboarding_agent.py)  
**Documentação:** 1.877 linhas (4 documentos)

---

### ✅ BLOCO 2 - 87% COMPLETO (2h 15min trabalho)

**Implementado:**
- ✅ **INTEGRAÇÃO COMPLETA** em `collect_client_info()` (src/agents/onboarding_agent.py linhas 294-579):
  - Linha 350: Chama `_extract_all_entities()` ✅
  - Linhas 522-525: Chama `_analyze_conversation_context()` ✅
  - Linhas 535-539: Chama `_generate_contextual_response()` ✅
  - Linhas 516-579: Refatoração STEP 6 (substituiu lógica antiga de geração de pergunta)

- ✅ **6 TESTES E2E CRIADOS** (tests/test_onboarding_agent.py linhas 1102-1243):
  - test_e2e_objectives_before_challenges (linha 1103)
  - test_e2e_all_info_first_turn (linha 1129)
  - test_e2e_incremental_completion (linha 1153)
  - test_e2e_no_regression_standard_flow (linha 1176)
  - test_e2e_frustration_recovery (linha 1199)
  - test_e2e_integration_complete (linha 1223)

**Testes:** 34/39 passando (87%)  
**Coverage:** 17% → 21% (+4pp)  
**Documentação:** Lesson learned completa (800 linhas)

---

## ⏳ TRABALHO PENDENTE (13% RESTANTE - 1h 30min)

### 🔧 PASSO 1: Corrigir 5 Mocks AsyncMock (30 min)

**PROBLEMA:** 5 testes E2E falhando com `TypeError: object Mock can't be used in 'await' expression`

**LOCALIZAÇÃO DO ERRO:**
```
ERROR src.agents.onboarding_agent:onboarding_agent.py:772 [EXTRACT_ALL] Erro na extracao: object Mock can't be used in 'await' expression
ERROR src.agents.onboarding_agent:onboarding_agent.py:956 [ANALYZE_CONTEXT] Erro na analise: object Mock can't be used in 'await' expression
```

**ROOT CAUSE:** `mock_llm` fixture (tests/test_onboarding_agent.py linha 18) usa `Mock()` para métodos async.

**SOLUÇÃO:**

```python
# ARQUIVO: tests/test_onboarding_agent.py
# LINHA: ~18-30 (fixture mock_llm)

# ANTES (ERRADO):
@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.invoke = Mock(return_value="Test response")
    llm.ainvoke = AsyncMock(return_value=Mock(content="Test async response"))
    llm.with_structured_output = Mock(return_value=llm)  # ❌ PROBLEMA!
    return llm

# DEPOIS (CORRETO):
@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.invoke = Mock(return_value="Test response")
    llm.ainvoke = AsyncMock(return_value=Mock(content="Test async response"))
    
    # ✅ CORRECAO: with_structured_output retorna objeto com ainvoke AsyncMock
    mock_structured = Mock()
    mock_structured.ainvoke = AsyncMock(
        return_value=Mock(content="Structured async response")
    )
    llm.with_structured_output = Mock(return_value=mock_structured)
    
    return llm
```

**VALIDAÇÃO:** Executar `pytest tests/test_onboarding_agent.py -k "test_e2e" -v --tb=short 2>&1`

**EXPECTATIVA:** 6/6 testes E2E passando

---

### 🧪 PASSO 2: Validar Suite Completa (15 min)

**COMANDO:**
```bash
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
python -m pytest tests/test_onboarding_agent.py -v --tb=long 2>&1
```

**EXPECTATIVA:** 39/39 testes passando (100%)

**SE FALHAR:** Ler traceback COMPLETO (sem filtros PowerShell - memória [[9969628]]), identificar erro, corrigir, reexecutar.

---

### 📊 PASSO 3: Executar Benchmark UX (30 min)

**CRIAR SCRIPT:** `tests/benchmark_onboarding_ux.py`

**ESTRUTURA:**

```python
\"\"\"Benchmark UX - Validar metricas de onboarding conversacional.

Metricas a validar:
- Turns medios por onboarding: 10-15 → 6-8 (-40% target)
- Taxa de reconhecimento: 60% → 100% (+67% target)
- Taxa de frustracao NAO detectada: 100% → 20% (-80% target)
\"\"\"

import asyncio
from src.agents.onboarding_agent import OnboardingAgent
from src.graph.states import BSCState
from config.settings import settings

# Dataset: 20 queries BSC variadas
BENCHMARK_QUERIES = [
    # 5 queries "fora de ordem" (objectives → challenges)
    "Queremos crescer 50% e aumentar NPS para 80.",
    
    # 5 queries "tudo de uma vez"
    "Sou da TechCorp, startup com 50 funcionarios. Desafios: rotatividade alta. Objetivos: crescer 40%.",
    
    # 5 queries "com frustracao"
    "Como mencionei antes, somos do setor de tecnologia!",
    
    # 5 queries "padrao sequencial"
    "Sou da MegaCorp, empresa de manufatura.",
]

async def run_benchmark():
    agent = OnboardingAgent(llm=settings.get_onboarding_llm(), ...)
    
    results = []
    for query in BENCHMARK_QUERIES:
        state = BSCState(...)
        result = await agent.collect_client_info("test_user", query, state)
        results.append(result)
    
    # Analisar resultados
    analyze_results(results)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
```

**VALIDAÇÃO:** Comparar métricas reais vs targets (turns, reconhecimento, frustração).

---

### 💾 PASSO 4: Commit e PR (30 min)

**COMANDOS:**

```bash
# Verificar arquivos modificados
git status

# Adicionar todos arquivos
git add .

# Commit com mensagem descritiva
git commit -m "feat: implementa onboarding conversacional inteligente (BLOCO 1+2)

- Implementa 3 padroes RAG avancados (Opportunistic Extraction, Context Awareness, Adaptive Response)
- Adiciona 9 metodos core + helpers (914 linhas)
- Cria 2 schemas Pydantic (ExtractedEntities, ConversationContext)
- Adiciona 3 prompts ICL baseados em research 2025 (413 linhas)
- Integra metodos em collect_client_info() (linhas 294-579)
- Cria 15 testes (9 smoke + 6 E2E)
- Resolve 5 bugs pre-existentes (mocks .model_dump())
- Documentacao completa (3.294 linhas, 5 docs)

Testes: 39/39 passando (100%)
Coverage: 17% → 21% (+4pp)
Timeline: 8h 30min (vs 7h 45min estimado, +10%)

Referencias:
- Plano: .cursor/plans/Plano_refatoracao_onboarding_conversacional.plan.md
- Lesson Learned: docs/lessons/lesson-onboarding-conversational-redesign-2025-10-23.md
- Resumo: .cursor/progress/sessao-2025-10-23-resumo-executivo.md
"

# Push branch
git push origin feature/onboarding-conversational-redesign
```

**VALIDAÇÃO:** PR criado com link para documentação.

---

## 🔍 CONTEXTO TÉCNICO DETALHADO

### Descoberta Crítica: Arquitetura Dual

**2 MÉTODOS PARALELOS (não substituir um pelo outro!):**

```python
# MÉTODO NOVO (OFICIAL) - linha 294:
async def collect_client_info(user_id: str, user_message: str, state: BSCState):
    \"\"\"Coleta informacoes usando Opportunistic Extraction (FASE 1).\"\"\"
    # ✅ USA _extract_all_entities() (linha 350)
    # ✅ USA _analyze_conversation_context() (linha 522)
    # ✅ USA _generate_contextual_response() (linha 535)
    # ✅ Context-aware, adaptive, intelligent

# MÉTODO ANTIGO (LEGACY) - linha 1228:
def _extract_information(user_message: str, current_step: int, state: BSCState):
    \"\"\"Extrai informacoes usando ClientProfileAgent (LEGACY).\"\"\"
    # ❌ USA profile_agent (design antigo)
    # ❌ Mono-processamento (1 entidade por turn)
    # ❌ Usado por process_turn() (sera deprecado FASE 2B)
```

**DECISÃO:** Trabalhar APENAS em `collect_client_info()`. NÃO modificar `_extract_information()` (deprecação planejada para FASE 2B).

---

### Decisões Técnicas Tomadas

1. **ICL Zero-Shot > Few-Shot** - ANALYZE_CONVERSATION_CONTEXT_PROMPT usa zero-shot (paper Telepathy Labs 2025: F1 0.86 zero-shot = 0.84 two-shot)

2. **Completeness Manual > LLM** - `_calculate_completeness()` calcula score MANUALMENTE (100% precisão vs ~85% LLM)

3. **Free-Form Text para Respostas** - `_generate_contextual_response()` usa `ainvoke()` direto (não structured output)

4. **Temperatura 0.8 para Respostas** - Mais natural que 1.0 padrão GPT-5 (conversação livre)

5. **Conversation History Tracking** - state.metadata["conversation_history"] persiste diálogo completo (necessário para context analysis)

---

### Integrações Realizadas

**ARQUIVO:** `src/agents/onboarding_agent.py`  
**MÉTODO:** `collect_client_info()` (linhas 294-579)

**STEP 6 REFATORADO (linhas 512-579):**

```python
# STEP 6.1: Preparar conversation_history
conversation_history = state.metadata.get("conversation_history", [])
conversation_history.append({"role": "user", "content": user_message})

# STEP 6.2: Analisar contexto (BLOCO 1)
context = await self._analyze_conversation_context(
    conversation_history=conversation_history,
    extracted_entities=extraction_result
)

# STEP 6.3: Gerar resposta adaptativa (BLOCO 1)
next_question = await self._generate_contextual_response(
    context=context,
    user_message=user_message,
    extracted_entities=extraction_result
)

# STEP 6.4: Atualizar historico
conversation_history.append({"role": "assistant", "content": next_question})
state.metadata["conversation_history"] = conversation_history
```

---

## 📋 PRÓXIMOS PASSOS ESPECÍFICOS

### PASSO 1: Corrigir Mock LLM (10 min)

**ARQUIVO:** `tests/test_onboarding_agent.py`  
**LOCALIZAÇÃO:** Fixture `mock_llm` (linha ~18-30)

**PROBLEMA EXATO:**
```
ERROR src.agents.onboarding_agent:onboarding_agent.py:772 [EXTRACT_ALL] 
TypeError: object Mock can't be used in 'await' expression
```

**CORREÇÃO:**

```python
@pytest.fixture
def mock_llm():
    \"\"\"Mock de LLM com suporte completo a async e structured output.\"\"\"
    llm = Mock()
    
    # Metodo sincrono
    llm.invoke = Mock(return_value="Test response")
    
    # Metodo assincrono
    llm.ainvoke = AsyncMock(return_value=Mock(content="Test async response"))
    
    # ✅ CORRECAO: with_structured_output retorna objeto COM ainvoke AsyncMock
    mock_structured = Mock()
    mock_structured.ainvoke = AsyncMock(
        return_value=Mock(content="Structured async response")
    )
    llm.with_structured_output = Mock(return_value=mock_structured)
    
    return llm
```

**COMANDO VALIDAÇÃO:**
```bash
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
python -m pytest tests/test_onboarding_agent.py::test_extract_all_entities_smoke_todas_categorias -v --tb=long 2>&1
```

**EXPECTATIVA:** 1/1 teste passando (confirma mock correto).

---

### PASSO 2: Validar Testes E2E (10 min)

**COMANDO:**
```bash
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
python -m pytest tests/test_onboarding_agent.py -k "test_e2e" -v --tb=long 2>&1
```

**EXPECTATIVA:** 6/6 testes E2E passando

**SE FALHAR:**
- Ler traceback COMPLETO (sem filtros PowerShell - memória [[9969628]])
- Identificar erro específico
- Corrigir (provável: ajustar assertions ou adicionar campos faltando em fixtures)
- Reexecutar

---

### PASSO 3: Validar Suite Completa (5 min)

**COMANDO:**
```bash
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"
python -m pytest tests/test_onboarding_agent.py -v --tb=line 2>&1 | Select-Object -Last 15
```

**EXPECTATIVA:** 39/39 testes passando (100%)

**SE FALHAR:** Aplicar PASSO 2 (debugging detalhado).

---

### PASSO 4: Executar Benchmark UX (30 min) - OPCIONAL

**SE TEMPO DISPONÍVEL**, criar e executar benchmark para validar métricas UX:

**ARQUIVO:** `tests/benchmark_onboarding_ux.py` (criar novo)

**DATASET:** 20 queries BSC variadas:
- 5 queries "fora de ordem" (objectives antes de challenges)
- 5 queries "tudo de uma vez"
- 5 queries "com frustração" ("como mencionei", "já disse")
- 5 queries "padrão sequencial"

**MÉTRICAS A VALIDAR:**
- Turns médios: 10-15 → 6-8 (-40%)
- Taxa de reconhecimento: 60% → 100% (+67%)
- Taxa de frustração NÃO detectada: 100% → 20% (-80%)

**SE NÃO HOUVER TEMPO:** Pular benchmark (pode ser feito em sessão futura). Priorizar: testes 39/39 + commit.

---

### PASSO 5: Commit e PR (30 min)

**CHECKLIST PRÉ-COMMIT:**

- [ ] Executar linter: `read_lints(["src/agents/onboarding_agent.py", "tests/test_onboarding_agent.py"])`
- [ ] Verificar zero emojis Unicode: `grep -r "[\u1F600-\u1F64F]" src/ tests/ --include="*.py"`
- [ ] Validar 39/39 testes passando
- [ ] Verificar coverage >= 21%

**COMANDOS GIT:**

```bash
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"

# Status
git status

# Add
git add src/agents/onboarding_agent.py
git add src/memory/schemas.py
git add src/prompts/client_profile_prompts.py
git add tests/test_onboarding_agent.py
git add docs/lessons/lesson-onboarding-conversational-redesign-2025-10-23.md
git add .cursor/progress/
git add .cursor/diagnostics/
git add .cursor/plans/Plano_refatoracao_onboarding_conversacional.plan.md

# Commit
git commit -m "feat: implementa onboarding conversacional inteligente (BLOCO 1+2)

- Implementa 3 padroes RAG avancados (Opportunistic Extraction, Context Awareness, Adaptive Response)
- Adiciona 9 metodos core + helpers (914 linhas)
- Cria 2 schemas Pydantic (ExtractedEntities, ConversationContext)
- Adiciona 3 prompts ICL baseados em research 2025 (413 linhas)
- Integra metodos em collect_client_info() (linhas 294-579)
- Cria 15 testes (9 smoke + 6 E2E)
- Resolve 5 bugs pre-existentes (mocks .model_dump())
- Documentacao completa (3.294 linhas, 5 docs)

Testes: 39/39 passando (100%)
Coverage: 17% → 21% (+4pp)
Timeline: 8h 30min

Referencias:
- Plano: .cursor/plans/Plano_refatoracao_onboarding_conversacional.plan.md
- Lesson: docs/lessons/lesson-onboarding-conversational-redesign-2025-10-23.md
- Resumo: .cursor/progress/sessao-2025-10-23-resumo-executivo.md
"

# Push
git push origin feature/onboarding-conversational-redesign
```

---

## 📚 REFERÊNCIAS PARA LEITURA

### Documentação OBRIGATÓRIA (LER ANTES DE COMEÇAR)

1. **Lesson Learned Completa** (800 linhas):
   - `docs/lessons/lesson-onboarding-conversational-redesign-2025-10-23.md`
   - Seções críticas: "Top 5 Lições-Chave" (linhas ~250-350), "Top 5 Antipadrões" (linhas ~350-450)

2. **Resumo Executivo** (200 linhas):
   - `.cursor/progress/sessao-2025-10-23-resumo-executivo.md`
   - Seções críticas: "Status Atual", "Trabalho Pendente", "Próximos Passos"

3. **Plano Atualizado** (1.617 linhas):
   - `.cursor/plans/Plano_refatoracao_onboarding_conversacional.plan.md`
   - Linhas críticas: 1533-1617 (progresso BLOCO 1+2)

### Código Modificado (LER SE NECESSÁRIO)

4. **Integração Completa:**
   - `src/agents/onboarding_agent.py` linhas 294-579 (`collect_client_info` integrado)

5. **Testes E2E:**
   - `tests/test_onboarding_agent.py` linhas 1102-1243 (6 testes E2E)

6. **Schemas:**
   - `src/memory/schemas.py` linhas 2421-2588 (ExtractedEntities, ConversationContext)

7. **Prompts:**
   - `src/prompts/client_profile_prompts.py` linhas 516-929 (3 prompts ICL)

---

## 🧠 MEMÓRIAS E LIÇÕES APLICÁVEIS

### Memórias Críticas

- **[[9969628]]** - NUNCA usar filtros PowerShell em pytest (Select-Object oculta traceback)
- **[[10230048]]** - Prompt schema alignment (LLM segue EXEMPLO primeiro, não schema)
- **[[9776249]]** - Checklist zero emojis (SEMPRE verificar antes de commit)
- **[[9969868]]** - Checklist 15 pontos testes (ler schema via grep ANTES de criar fixture)
- **[[10182063]]** - with_structured_output pode retornar None (verificar finish_reason)

### Antipadrões a Evitar

1. ❌ **Mock() para métodos async** → Usar AsyncMock
2. ❌ **Mocks Pydantic sem .model_dump()** → Adicionar .model_dump() E .dict()
3. ❌ **Filtros PowerShell em pytest** → Comando direto sem pipes
4. ❌ **Assumir estrutura de código** → Ler via grep ANTES de modificar
5. ❌ **Structured output para free-form text** → Usar ainvoke() direto

---

## 🎯 CRITÉRIO DE SUCESSO (100% COMPLETO)

**Checklist Obrigatório:**

- [ ] **39/39 testes passando** (100%)
- [ ] **Coverage >= 21%** (manter ou aumentar)
- [ ] **Zero linter errors** (verificar com read_lints)
- [ ] **Zero emojis Unicode** (checklist [[9776249]])
- [ ] **Benchmark UX executado** (ou documentar skip com justificativa)
- [ ] **Commit realizado** (mensagem descritiva com referências)
- [ ] **PR criado** (link para docs)
- [ ] **Lesson learned atualizada** (métricas UX reais se benchmark executado)

---

## ⚡ QUICK START (COMANDO INICIAL)

**COPIE E EXECUTE ESTE BLOCO:**

```bash
# 1. Navegar para projeto
cd "d:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag"

# 2. Ler resumo executivo (contexto completo)
cat .cursor/progress/sessao-2025-10-23-resumo-executivo.md

# 3. Ler lesson learned (top 5 lições + antipadrões)
cat docs/lessons/lesson-onboarding-conversational-redesign-2025-10-23.md | Select-Object -First 450

# 4. Ver erro específico dos testes E2E falhando
python -m pytest tests/test_onboarding_agent.py -k "test_e2e" -v --tb=short 2>&1 | Select-String "ERROR|TypeError|assert" | Select-Object -First 20

# 5. Começar correção do mock_llm (fixture linha ~18-30)
code tests/test_onboarding_agent.py
```

---

## 💡 DICAS PARA SUCESSO

1. **LER DOCUMENTAÇÃO PRIMEIRO** (15 min investimento economiza 1-2h debugging)
   - Lesson learned tem TOP 5 lições + TOP 5 antipadrões (linhas 250-450)
   - Resumo executivo tem checklist acionável

2. **EXECUTAR COMANDOS SEM FILTROS** (memória [[9969628]])
   - CORRETO: `pytest ... --tb=long 2>&1`
   - ERRADO: `pytest ... | Select-Object -Last 20`

3. **VERIFICAR LINTERS SEMPRE** (previne 93% bugs - lição FASE 2A)
   - Após cada mudança: `read_lints(["arquivo.py"])`

4. **COMMITS INCREMENTAIS** (não um commit gigante final)
   - Mock corrigido → commit
   - Testes passando → commit
   - Benchmark executado → commit

5. **USAR SEQUENTIAL THINKING** (planejamento antes de implementar)
   - Planejar 5-6 thoughts ANTES de modificar código
   - Economiza 30-50% tempo (decisões validadas)

---

## ❓ TROUBLESHOOTING

### Se testes continuarem falhando após corrigir mock_llm:

**CAUSA PROVÁVEL:** Fixtures específicas dos testes E2E precisam configuration adicional.

**SOLUÇÃO:**

```python
# Verificar se testes E2E precisam de mock_profile_agent ou mock_memory_client
# Adicionar fixtures conforme necessário

@pytest.mark.asyncio
async def test_e2e_objectives_before_challenges(
    onboarding_agent,  # ← Depende de mock_llm, mock_profile_agent, mock_memory_client
    initial_state
):
    # Se falhar, verificar quais fixtures estão configuradas
```

**COMANDO DEBUG:**
```bash
pytest tests/test_onboarding_agent.py::test_e2e_objectives_before_challenges -v --tb=long -s 2>&1 | Select-String "fixture|mock|ERROR" -CaseSensitive
```

---

### Se coverage cair abaixo de 21%:

**CAUSA PROVÁVEL:** Testes E2E não estão executando código novo (mocks evitando execução real).

**SOLUÇÃO:** Ajustar mocks para permitir execução dos métodos core (não apenas retornar valores fixos).

---

### Se commit falhar (pre-commit hooks):

**COMANDO:**
```bash
# Verificar hooks instalados
cat .pre-commit-config.yaml

# Executar manualmente
pre-commit run --all-files

# Se falhar, corrigir issues apontados (lint, format, etc)
```

---

## 🏁 RESULTADO ESPERADO FINAL

**Após 1h 30min de trabalho:**

```
============================= 39 passed in 15.00s ==============================
Coverage: 21% (+4pp vs inicial)
Branch: feature/onboarding-conversational-redesign
Commit: feat: implementa onboarding conversacional inteligente (BLOCO 1+2)
PR: #XXX (criado, aguardando review)
```

**Documentação atualizada:**
- Lesson learned com métricas UX reais (se benchmark executado)
- Plano marcado 100% completo

**Projeto pronto para:**
- Merge para main
- Deploy em ambiente de staging
- Validação com usuários reais

---

**Fim do Prompt de Continuidade**

---

## 📝 INSTRUÇÕES DE USO

**COPIE O BLOCO ABAIXO E COLE NO NOVO CHAT:**

---

# Continue BLOCO 2 - Onboarding Conversacional (87% → 100%)

**Branch:** `feature/onboarding-conversational-redesign`  
**Status:** 87% completo (34/39 testes passando)  
**Trabalho Pendente:** 1h 30min (mocks AsyncMock + validação + commit)

## CONTEXTO

Sessão anterior (23/10/2025, 8h 30min) implementou **BLOCO 1** (100%) + **BLOCO 2** (87%):
- ✅ 9 métodos core + helpers (914 linhas)
- ✅ 3 prompts ICL research 2025 (413 linhas)
- ✅ 2 schemas Pydantic (ExtractedEntities, ConversationContext)
- ✅ 15 testes (9 smoke passando + 6 E2E criados)
- ✅ Integração completa em `collect_client_info()` (src/agents/onboarding_agent.py linhas 294-579)

**PROBLEMA ATUAL:** 5 testes E2E falhando com `TypeError: object Mock can't be used in 'await' expression`

## DOCUMENTAÇÃO CRÍTICA (LER PRIMEIRO)

1. **Resumo Executivo:** `.cursor/progress/sessao-2025-10-23-resumo-executivo.md` (200 linhas)
2. **Lesson Learned:** `docs/lessons/lesson-onboarding-conversational-redesign-2025-10-23.md` (800 linhas)
3. **Plano Completo:** `.cursor/plans/Plano_refatoracao_onboarding_conversacional.plan.md` (linhas 1533-1617)

## PRÓXIMOS PASSOS

**PASSO 1 (10 min):** Corrigir fixture `mock_llm` (tests/test_onboarding_agent.py linha ~18-30)
- **Problema:** `llm.with_structured_output = Mock(return_value=llm)` não funciona para async
- **Solução:** Criar `mock_structured` com `ainvoke = AsyncMock(...)`
- **Validar:** `pytest tests/test_onboarding_agent.py::test_extract_all_entities_smoke_todas_categorias -v --tb=long 2>&1`

**PASSO 2 (10 min):** Validar 6 testes E2E
- **Comando:** `pytest tests/test_onboarding_agent.py -k "test_e2e" -v --tb=long 2>&1`
- **Expectativa:** 6/6 passando

**PASSO 3 (5 min):** Suite completa
- **Comando:** `pytest tests/test_onboarding_agent.py -v --tb=line 2>&1 | Select-Object -Last 15`
- **Expectativa:** 39/39 passando (100%)

**PASSO 4 (30 min - OPCIONAL):** Benchmark UX (se tempo disponível)

**PASSO 5 (30 min):** Commit + PR

## MEMÓRIAS APLICÁVEIS

- [[9969628]] NUNCA usar filtros PowerShell em pytest
- [[10230048]] Prompt schema alignment (examples primeiro)
- [[9776249]] Checklist zero emojis
- [[9969868]] Checklist 15 pontos testes

**Prompt completo disponível em:** `.cursor/prompts/continuidade-bloco2-onboarding.md`

---

**ESTÁ PRONTO! Copie o bloco acima e cole no novo chat para continuar.** 🚀

