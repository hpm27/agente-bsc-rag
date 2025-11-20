# Análise de Bugs Pré-Existentes - Onboarding Agent

**Data:** 22/10/2025
**Contexto:** Detectados 5 bugs pré-existentes durante validação do BLOCO 1
**Status:** [ERRO] **BUGS REAIS NO CÓDIGO** (não são testes defasados)

---

## [EMOJI] RESUMO EXECUTIVO

**CONCLUSÃO:** Os 5 bugs são **BUGS REAIS NA LÓGICA DE VALIDAÇÃO** do método `process_turn()`. Os testes estão **corretos** e refletem o comportamento esperado. O código de produção tem **falha crítica** na detecção de informações incompletas.

**IMPACTO NO PROJETO:**
- [WARN] **MÉDIO-ALTO** - Afeta experiência do usuário no onboarding
- O agent **avança steps prematuramente** sem coletar informações necessárias
- Pode resultar em diagnósticos BSC incompletos/inadequados
- **NÃO bloqueia funcionalidade core** (DISCOVERY, SWOT, KPI funcionam), mas **degrada qualidade** do onboarding inicial

---

## [EMOJI] BUGS IDENTIFICADOS (5 TOTAL)

### **BUG #1: test_process_turn_step1_incomplete_triggers_followup**

**Status:** [ERRO] FALHANDO

**Comportamento Esperado (teste):**
- Usuário fornece informação **incompleta** (falta `sector`)
- Agent deve **permanecer no step 1** (COMPANY_INFO)
- Agent deve **gerar follow-up** perguntando pelo setor
- `followup_count` deve incrementar para 1

**Comportamento Real (código):**
- Agent **avança para step 2** (CHALLENGES)
- Follow-up **NÃO é gerado**
- Informação faltante é **ignorada**

**Root Cause:**
```python
# src/agents/onboarding_agent.py linha 219
is_complete, missing_info = self._validate_extraction(extraction_result, current_step)

# Linha 222
if not is_complete and self.followup_count[current_step] < self.max_followups_per_step:
    # [ERRO] ESTE BLOCO NÃO ESTÁ SENDO EXECUTADO
```

**Hipótese:** `_validate_extraction()` retorna **is_complete=True** mesmo com `sector=None`

---

### **BUG #2: test_process_turn_step1_max_followups_forces_continue**

**Status:** [ERRO] FALHANDO

**Comportamento Esperado (teste):**
- Após **2 follow-ups** (max_followups=2), mesmo com informação **ainda incompleta**
- Agent deve **forçar avanço** para step 2 (CHALLENGES)
- State deve marcar `company_info=True` (completo forçadamente)

**Comportamento Real (código):**
- Agent comportamento inconsistente (possivelmente avança, mas state não atualizado)

**Root Cause:**
Lógica de "forçar avanço após max follow-ups" (linha 249-250) pode não estar atualizando state corretamente.

---

### **BUG #3: test_process_turn_step2_challenges_extracted**

**Status:** [ERRO] FALHANDO (similar ao BUG #1)

**Comportamento:** Agent não valida corretamente **mínimo de 2 challenges**

---

### **BUG #4: test_process_turn_step3_objectives_extracted**

**Status:** [ERRO] FALHANDO (similar ao BUG #1)

**Comportamento:** Agent não valida corretamente **mínimo de 3 objectives**

---

### **BUG #5: test_process_turn_initial_company_extraction**

**Status:** [ERRO] FALHANDO (similar ao BUG #1)

**Comportamento:** Validação inicial de extração completa falhando

---

## [EMOJI] ROOT CAUSE ANALYSIS (5 WHYS)

**Problema:** Agent avança steps com informações incompletas

**Why #1:** Por que agent avança?
-> Porque condição `if not is_complete` (linha 222) retorna False

**Why #2:** Por que `is_complete` é True?
-> Porque `_validate_extraction()` não detecta campos faltantes

**Why #3:** Por que validação não detecta?
-> Possível causa: `extraction.get("sector")` retorna algo que não é None/False

**Why #4:** Por que `sector` não é None?
-> Hipótese 1: Mock do teste não está funcionando corretamente
-> Hipótese 2: `_extract_information()` está retornando formato diferente (dict vazio vs None)
-> Hipótese 3: Validação compara contra string vazia "" (Pythonic: `if not extraction.get("sector")` captura None E "")

**Why #5:** Por que formato mudou?
-> **PROVÁVEL INTERFERÊNCIA** com nossos novos métodos (`_extract_all_entities()`, adapter linha 352-364)

---

## [EMOJI] EVIDÊNCIAS

### **Evidência 1: Erro Concreto do Teste**
```python
assert result["step"] == OnboardingStep.COMPANY_INFO
AssertionError: assert 2 == <OnboardingStep.COMPANY_INFO: 1>
```
Step retornado: **2** (CHALLENGES)
Step esperado: **1** (COMPANY_INFO)

### **Evidência 2: Mock do Teste (correto)**
```python
incomplete_info = Mock()
incomplete_info.name = "Empresa X"
incomplete_info.sector = None  # <- EXPLICITAMENTE None
incomplete_info.size = "100"
incomplete_info.dict = Mock(return_value={
    "name": "Empresa X",
    "sector": None,
    "size": "100"
})
```

### **Evidência 3: Lógica de Validação (_validate_extraction)**
```python
def _validate_extraction(self, extraction: dict[str, Any], step: int) -> tuple[bool, list[str]]:
    missing = []

    if step == OnboardingStep.COMPANY_INFO:
        if not extraction.get("name"):  # [OK] Pythonic check
            missing.append("nome da empresa")
        if not extraction.get("sector"):  # [ERRO] DEVERIA detectar None!
            missing.append("setor/indústria")
        if not extraction.get("size"):
            missing.append("tamanho (número de funcionários)")

    is_complete = len(missing) == 0  # [ERRO] Se missing vazio -> True (ERRADO!)
    return is_complete, missing
```

**Análise:** A lógica **PARECE correta**, mas `extraction.get("sector")` pode estar retornando algo que não é None.

---

## [EMOJI] HIPÓTESE PRINCIPAL

**INTERFERÊNCIA COM NOVOS MÉTODOS (BLOCO 1):**

Criamos um **adapter** no método `collect_client_info()` (linha 352-364):
```python
extracted_entities = {
    "company_name": extraction_result.company_info.name if extraction_result.company_info else None,
    "industry": extraction_result.company_info.sector if extraction_result.company_info else None,
    "size": extraction_result.company_info.size if extraction_result.company_info else None,
    # ...
}
```

**MAS** este adapter **NÃO é usado** pelo método `process_turn()` (que usa `_extract_information()` linha 216).

**PROBLEMA POTENCIAL:**
- Os **testes antigos** mockam `profile_agent.extract_company_info()` (ClientProfileAgent)
- Mas pode haver **conflito de namespaces** ou **import order** após adicionarmos `ExtractedEntities` e `ConversationContext` aos imports

---

## [EMOJI] IMPACTO NO PROJETO

### **Severidade: MÉDIA-ALTA**

| Aspecto | Impacto |
|---|---|
| **Funcionalidade Core** | [OK] **NÃO afetada** (DISCOVERY, SWOT, KPI funcionam) |
| **Experiência de Onboarding** | [ERRO] **DEGRADADA** (usuário pode pular informações) |
| **Qualidade de Diagnósticos** | [WARN] **RISCO MÉDIO** (diagnósticos com base incompleta) |
| **Produção Atual** | [WARN] **DESCONHECIDO** (não sabemos se bug existe em prod ou só em testes) |

### **Cenário de Falha Real:**
```
USUÁRIO: "Sou da TechCorp"
AGENT: "Ótimo! Quais são os 2-3 principais desafios?" <- [ERRO] PULOU VALIDAÇÃO (falta sector, size)

[Resultado: Diagnóstico BSC sem contexto de indústria/tamanho]
```

---

## [OK] TESTES ESTÃO **CORRETOS** (NÃO defasados)

**Evidências:**
1. Testes refletem **comportamento esperado** de onboarding progressivo
2. Lógica de validação (follow-ups, max retries) é **padrão de UX** para chatbots
3. Requisitos de informações mínimas (name, sector, size, 2 challenges, 3 objectives) são **razoáveis** para diagnóstico BSC
4. Paper "User Frustration Detection" (Telepathy Labs 2025) valida **importância de follow-ups** vs avanço prematuro

---

## [EMOJI] RECOMENDAÇÕES DE CORREÇÃO

### **Prioridade 1: DEBUGGING IMEDIATO (1-2h)**

1. **Adicionar logs no `_validate_extraction()`:**
```python
def _validate_extraction(self, extraction: dict[str, Any], step: int) -> tuple[bool, list[str]]:
    logger.info("[VALIDATE] Extraction recebido: %s", extraction)
    logger.info("[VALIDATE] Step: %d", step)
    missing = []

    if step == OnboardingStep.COMPANY_INFO:
        name_value = extraction.get("name")
        sector_value = extraction.get("sector")
        size_value = extraction.get("size")

        logger.info("[VALIDATE] name=%s, sector=%s, size=%s", name_value, sector_value, size_value)

        if not name_value:
            missing.append("nome da empresa")
            logger.info("[VALIDATE] FALTANDO: nome da empresa")
        if not sector_value:
            missing.append("setor/indústria")
            logger.info("[VALIDATE] FALTANDO: setor/indústria")
        if not size_value:
            missing.append("tamanho (número de funcionários)")
            logger.info("[VALIDATE] FALTANDO: tamanho")

    is_complete = len(missing) == 0
    logger.info("[VALIDATE] is_complete=%s, missing=%s", is_complete, missing)
    return is_complete, missing
```

2. **Executar testes com logs verbosos:**
```bash
pytest tests/test_onboarding_agent.py::test_process_turn_step1_incomplete_triggers_followup -v -s --log-cli-level=INFO
```

3. **Verificar formato exato retornado por `_extract_information()`**

---

### **Prioridade 2: CORREÇÃO DEFINITIVA (2-4h)**

**Opção A: Corrigir validação pythonica**
```python
# Adicionar validação mais rigorosa
if not sector_value or sector_value == "" or sector_value == "None":
    missing.append("setor/indústria")
```

**Opção B: Refatorar `_extract_information()` para usar novos métodos**
- Integrar `_extract_all_entities()` no fluxo de `process_turn()`
- Remover dependência de `ClientProfileAgent` (deprecated após BLOCO 1)

---

### **Prioridade 3: REGRESSÃO PREVENTION (1h)**

1. Adicionar **3 unit tests** para `_validate_extraction()` isoladamente
2. Testar edge cases: None, "", "None", {}, []
3. Adicionar test de integração E2E simulando falha real

---

## [EMOJI] CONCLUSÃO

**RESPOSTA DIRETA À PERGUNTA:**

> **Os bugs pré-existentes indicam algum erro que pode prejudicar o funcionamento do projeto, ou são testes defasados?**

[OK] **Eram BUGS REAIS nos MOCKS dos testes** (não no código de produção!)
[OK] **Testes estavam corretos** (comportamento esperado adequado)
[OK] **TODOS OS 5 BUGS RESOLVIDOS** (2025-10-23)

---

## [OK] **SOLUÇÃO COMPLETA IMPLEMENTADA (2025-10-23)**

### **ROOT CAUSE FINAL:**

**Mock objects sem `.model_dump()` para Pydantic V2**

Código `_extract_information()` (linha 1261) tenta:
```python
return result.model_dump() if hasattr(result, "model_dump") else (result.dict() if hasattr(result, "dict") else result)
```

Mocks antigos só tinham `.dict()`, mas Mock objects **TÊM hasattr "model_dump"** naturalmente, retornando **outro Mock**. Resultado:
- `extraction.get("sector")` -> **Mock object** (não None!)
- `if not mock_object` -> **False** (Mocks são truthy!)
- `is_complete=True` (ERRADO!)

---

### **CORREÇÕES APLICADAS:**

**1. Fixture Base `mock_profile_agent` (linhas 36-76)**
```python
# ANTES (ERRADO):
company_info.dict = Mock(return_value={...})

# DEPOIS (CORRETO):
company_info_dict = {"name": "...", "sector": "...", "size": "..."}
company_info.model_dump = Mock(return_value=company_info_dict)  # [OK] Pydantic V2
company_info.dict = Mock(return_value=company_info_dict)  # [OK] Fallback V1
```

**2. Testes Específicos (4 locais)**
- `test_process_turn_step1_incomplete_triggers_followup` (linhas 192-208)
- `test_process_turn_step1_max_followups_forces_continue` (linhas 232-243)
- `test_process_turn_step2_incomplete_triggers_followup` (linhas 290-299)
- `test_process_turn_step3_incomplete_triggers_followup` (linhas 349-358)

**3. Teste `test_process_turn_step3_completes_onboarding` (linhas 333-338)**

Além do mock, precisava popular `state.client_profile.context.current_challenges` (validação exige >= 2 challenges antes de objectives).

---

### **RESULTADOS FINAIS:**

| Métrica | Antes | Depois | Delta |
|---|-----|---|---|
| **Testes Passando** | 28/33 | **33/33** | **+5 (100%)** |
| **Testes Falhando** | 5 | **0** | **-5 (resolvidos!)** |
| **Coverage** | 19% | **20%** | +1pp |
| **Tempo Resolução** | - | **75 min** | (debugging + correções) |

---

### **DESCOBERTAS CRÍTICAS:**

1. [OK] **Código de produção está CORRETO** - `_validate_extraction()` funciona perfeitamente
2. [OK] **Validação pythonica funciona** - `if not value` detecta None, "", [] corretamente
3. [ERRO] **Mocks Pydantic V2** - SEMPRE adicionar `.model_dump()` E `.dict()` (ordem importa!)
4. [ERRO] **State precisa de dados reais** - Marcar step completo NÃO basta, precisa popular dados

---

### **LIÇÃO APRENDIDA:**

**SEMPRE criar mocks Pydantic com ambos métodos:**
```python
mock_object = Mock()
mock_object.field1 = value1
mock_object.field2 = value2

# [OK] CORRETO (Pydantic V2 + V1 fallback):
data_dict = {"field1": value1, "field2": value2}
mock_object.model_dump = Mock(return_value=data_dict)
mock_object.dict = Mock(return_value=data_dict)
```

**ROI:** Economiza 30-60 min debugging por suite de testes.

---

**IMPACTO NO PROJETO:** [OK] **ZERO** - Bugs eram apenas nos testes, não afetavam produção

---

**Última Atualização:** 2025-10-23 [OK] **BUGS RESOLVIDOS 100%**
**Autor:** AI Agent (Claude Sonnet 4.5)
**Tempo Total:** 75 min (Sequential Thinking + debugging + correções + validação)
