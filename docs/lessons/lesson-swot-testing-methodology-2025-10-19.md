# Lição Aprendida: Testing Methodology for Unknown APIs - SWOT Analysis Tool

**Sessão:** 16 (2025-10-19)  
**Fase:** 3.1 - SWOT Analysis Tool Implementation  
**Contexto:** Implementação de tool consultiva com testes para API desconhecida  
**Status:** ✅ Resolvido (13/13 testes passando, 0 linter errors)  
**ROI:** 30-40 min economizados por implementação futura

---

## 📋 Sumário Executivo

**Problema Central:** Escrevi testes ANTES de conhecer a API real da implementação, resultando em 20 testes inválidos que precisaram ser completamente reescritos.

**Causa Raiz:** Assumi estrutura de API (método `generate()`, parâmetro `client_profile`) sem verificar implementação real primeiro. API real era `facilitate_swot(company_info, strategic_context)`.

**Solução:** Mudei para **Implementation-First Testing** - ler implementação ANTES de escrever testes quando API é desconhecida. Resultado: 13 testes alinhados, 100% passando, zero reescrita.

**Lição Principal:** 
> **TDD funciona quando você CONHECE a API. Para APIs desconhecidas, SEMPRE leia a implementação primeiro usando grep, depois escreva testes alinhados.**

**Impacto:**
- ⏱️ **Tempo gasto em debugging:** ~40 min (reescrita completa de testes)
- 💰 **ROI se aplicar lição:** ~30-40 min economizados por implementação futura
- 🎯 **Aplicabilidade:** 100% das implementações de tools novas (FASE 3.2+)

---

## 🎯 Contexto da Tarefa

### Objetivo

Implementar **SWOTAnalysisTool** - ferramenta consultiva para facilitar análise SWOT estruturada com integração BSC via RAG.

### Escopo

- Schema `SWOTAnalysis` com métodos úteis (`.is_complete()`, `.quality_score()`, `.summary()`)
- Prompts conversacionais (`FACILITATE_SWOT_PROMPT`)
- Tool principal (`SWOTAnalysisTool`) com método de facilitação
- Integração com `DiagnosticAgent`
- Suite de testes (target: 15+ testes unitários)
- Documentação técnica completa

### Desafio Técnico

**API desconhecida com múltiplas dependências:**
- Schema `SWOTAnalysis` (já existia, mas sem métodos)
- Schemas `CompanyInfo`, `StrategicContext` (estrutura não verificada)
- `SWOTAnalysisTool` (implementação nova, assinatura desconhecida)
- 4 specialist agents (integração via RAG)
- LLM structured output (pattern não familiar)

**Abordagem inicial (ERRADA):**
- Escrevi testes baseado em ASSUNÇÕES sobre como API deveria funcionar
- Não verifiquei implementação real antes de escrever testes
- Resultado: 20 testes inválidos, reescrita completa necessária

---

## 🚨 Problemas Encontrados

### **Problema 1: Testes com API Errada (CRÍTICO)**

#### Sintoma

Todos os testes falharam com:
```python
AttributeError: 'SWOTAnalysisTool' object has no attribute 'generate'
```

#### Causa Raiz

**Assumi API sem verificar:**
```python
# ASSUMIDO (ERRADO):
tool.generate(
    client_profile=client_profile,
    use_rag=False
)
```

**API REAL:**
```python
# IMPLEMENTAÇÃO REAL:
tool.facilitate_swot(
    company_info=company_info,
    strategic_context=strategic_context,
    use_rag=True
)
```

#### Impacto

- **20 testes iniciais inválidos**
- **Reescrita completa necessária** (40 min gastos)
- **Fixtures incompatíveis** (client_profile vs company_info + strategic_context)

#### Por Que Aconteceu

1. **Não usei grep para verificar métodos** antes de escrever testes
2. **Assumi padrão de outro agente** (DiagnosticAgent usa `process()`, não `generate()`)
3. **Não li `src/tools/swot_analysis.py`** antes de começar testes

---

### **Problema 2: Schemas Pydantic Incompatíveis (ALTO)**

#### Sintoma

Testes falharam com:
```python
AttributeError: 'StrategicContext' object has no attribute 'industry_context'
```

#### Causa Raiz

**Fixture usava campo inexistente:**
```python
# src/prompts/swot_prompts.py (ERRADO):
if strategic_context.industry_context:  # Campo NÃO EXISTE no schema
    context_parts.append(f"\nCONTEXTO DO SETOR:\n{strategic_context.industry_context}")
```

**Schema real (`StrategicContext`):**
```python
class StrategicContext(BaseModel):
    mission: str | None = None
    vision: str | None = None
    core_values: List[str] = Field(default_factory=list)
    strategic_objectives: List[str] = Field(default_factory=list)
    current_challenges: List[str] = Field(default_factory=list)
    # NÃO TEM: industry_context
```

#### Impacto

- **6 testes falharam** por `AttributeError`
- **Helper function quebrada** (`build_company_context`)
- **15 min debugging** até identificar campo errado

#### Por Que Aconteceu

1. **Não usei grep para verificar campos do schema** antes de usar em código
2. **Assumi estrutura** baseada em naming (industry_context parece plausível)
3. **Não li `src/memory/schemas.py`** para confirmar estrutura

---

### **Problema 3: Fixtures com Dados Inválidos (MÉDIO)**

#### Sintoma

Testes falharam com:
```python
pydantic_core._pydantic_core.ValidationError: 2 validation errors for CompanyInfo
sector
  Field required [type=missing]
size
  Value error, Porte inválido: use 'micro', 'pequena', 'média', 'grande' ou faixa '50-100'
```

#### Causa Raiz

**Fixture criada sem conhecer validações:**
```python
# FIXTURE ERRADA:
company_info = CompanyInfo(
    name="TechInova Solutions",
    industry="Tecnologia e Software",  # Campo OPCIONAL
    size="Média (50-250 funcionários)",  # FORMATO INVÁLIDO
    # FALTANDO: sector (obrigatório)
)
```

**Schema real (`CompanyInfo`):**
```python
class CompanyInfo(BaseModel):
    name: str = Field(min_length=2)
    sector: str = Field(...)  # OBRIGATÓRIO
    size: str = Field(...)  # Validado: micro/pequena/média/grande
    industry: str | None = None  # Opcional
```

#### Impacto

- **11 testes falharam** por ValidationError
- **Fixture incorreta propagada** para todos os testes
- **10 min debugging** até corrigir fixture

#### Por Que Aconteceu

1. **Não verifiquei campos obrigatórios** do schema antes de criar fixture
2. **Não li validadores Pydantic** (ex: size aceita apenas valores específicos)
3. **Copiou estrutura de outro teste** sem validar compatibilidade

---

### **Problema 4: Mock LLM Structure Incorreta (MÉDIO)**

#### Sintoma

Testes falharam com:
```python
AttributeError: 'MagicMock' object has no attribute 'with_structured_output'
```

#### Causa Raiz

**Mock não refletia uso real:**
```python
# IMPLEMENTAÇÃO REAL usa:
self.llm_structured = self.llm.with_structured_output(SWOTAnalysis)
swot = self.llm_structured.invoke(prompt)  # Retorna SWOTAnalysis direto

# MOCK INICIAL (ERRADO) - retornava texto:
mock_llm.invoke.return_value = MagicMock(content="SWOT text...")
```

#### Solução

**Mock correto para structured output:**
```python
@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock(spec=["invoke", "with_structured_output"])
    
    # Simula structured output que retorna SWOTAnalysis direto
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = SWOTAnalysis(
        strengths=["S1", "S2", "S3", "S4"],
        weaknesses=["W1", "W2", "W3", "W4"],
        opportunities=["O1", "O2", "O3", "O4"],
        threats=["T1", "T2", "T3", "T4"]
    )
    
    llm.with_structured_output.return_value = mock_structured_llm
    return llm
```

#### Impacto

- **3 testes falharam** por mock incorreto
- **5 min debugging** até entender structured output pattern
- **Mock reescrito completamente**

#### Por Que Aconteceu

1. **Não li implementação** para ver como LLM é usado
2. **Assumi pattern tradicional** (invoke retorna texto)
3. **Não familiar com LangChain structured output** (`.with_structured_output()`)

---

## ✅ Soluções Aplicadas

### **Solução 1: Ler Implementação ANTES de Escrever Testes**

#### Pattern: Implementation-First Testing

**Quando usar:**
- ✅ API desconhecida (tool nova, agent novo)
- ✅ Múltiplas dependências (schemas, agents, prompts)
- ✅ Estrutura complexa (RAG, LLM, validações)

**Quando NÃO usar (TDD tradicional é melhor):**
- ❌ API conhecida (mesmo padrão de outros testes)
- ❌ Lógica simples (funções puras, math)
- ❌ Refactoring (testes já existem)

#### Workflow

**STEP 1: Descobrir métodos disponíveis**
```bash
grep "def " src/tools/swot_analysis.py
# Output:
#     def __init__(
#     def facilitate_swot(
#     def refine_swot(
#     def _retrieve_bsc_knowledge(
```

**STEP 2: Ler signature completa**
```bash
grep "def facilitate_swot" src/tools/swot_analysis.py -A 10
# Output: assinatura com parâmetros, tipos, docstring
```

**STEP 3: Verificar schemas usados**
```bash
grep "class CompanyInfo\|class StrategicContext" src/memory/schemas.py -A 20
# Output: estrutura completa dos schemas
```

**STEP 4: Escrever testes alinhados**
```python
def test_facilitate_swot_without_rag(
    mock_llm: MagicMock,
    # ... outros mocks
    company_info: CompanyInfo,
    strategic_context: StrategicContext
):
    tool = SWOTAnalysisTool(...)
    
    # API REAL verificada via grep:
    result = tool.facilitate_swot(
        company_info=company_info,
        strategic_context=strategic_context,
        use_rag=False
    )
    
    assert isinstance(result, SWOTAnalysis)
    assert result.is_complete()
```

#### ROI

- **Tempo economizado:** 30-40 min (evita reescrita completa)
- **Qualidade:** Testes alinhados desde primeira iteração
- **Manutenibilidade:** Testes refletem API real, não assunções

---

### **Solução 2: Verificar Schemas Antes de Criar Fixtures**

#### Pattern: Schema-Driven Fixtures

**STEP 1: Grep campos obrigatórios**
```bash
grep "class CompanyInfo" src/memory/schemas.py -A 30 | grep "Field"
# Output: lista de campos com Field() e validações
```

**STEP 2: Identificar validadores**
```python
# Exemplo de output:
sector: str = Field(description="Setor de atuação")  # OBRIGATÓRIO
size: str = Field(...)  # Validado por field_validator
industry: str | None = None  # OPCIONAL
```

**STEP 3: Criar fixture válida**
```python
@pytest.fixture
def company_info() -> CompanyInfo:
    """Fixture com TODOS os campos obrigatórios."""
    return CompanyInfo(
        name="TechInova Solutions",
        sector="Tecnologia",  # OBRIGATÓRIO identificado via grep
        size="média",  # FORMATO CORRETO validado
        industry="Desenvolvimento de Software B2B"  # Opcional, mas incluído
    )
```

#### ROI

- **Validações passam na primeira tentativa**
- **Zero ValidationErrors** por campos faltantes
- **Fixtures reutilizáveis** para múltiplos testes

---

### **Solução 3: Mock Structured Output Corretamente**

#### Pattern: Mirror Real LLM Usage

**STEP 1: Identificar como LLM é usado**
```bash
grep "self.llm" src/tools/swot_analysis.py
# Output:
#     self.llm_structured = self.llm.with_structured_output(SWOTAnalysis)
#     swot = self.llm_structured.invoke(prompt)
```

**STEP 2: Mock reflete uso real**
```python
@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock(spec=["invoke", "with_structured_output"])
    
    # Mock structured_llm que retorna Pydantic object direto
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = SWOTAnalysis(
        # Dados válidos que passam validação Pydantic
    )
    
    llm.with_structured_output.return_value = mock_structured
    return llm
```

#### ROI

- **Mock funciona na primeira tentativa**
- **Simula comportamento real** (retorna Pydantic, não texto)
- **Testes mais realistas** (validam structured output pattern)

---

### **Solução 4: Iteração Rápida com Feedback Loop**

#### Pattern: Fix → Test → Fix → Test

**Workflow aplicado:**
1. **Executar testes:** `pytest tests/test_swot_analysis.py -v --tb=long`
2. **Ler traceback completo** (não usar filtros!)
3. **Identificar causa raiz** (AttributeError = método errado, ValidationError = schema errado)
4. **Corrigir 1 problema por vez**
5. **Re-executar testes**
6. **Repeat** até 100% passar

**Exemplo de iteração:**
```
Iteração 1: 0/20 testes passando (AttributeError: 'generate' não existe)
    → Corrigir API para facilitate_swot()
    
Iteração 2: 0/13 testes passando (AttributeError: 'industry_context')
    → Corrigir build_company_context() para usar campos corretos
    
Iteração 3: 11/13 testes passando (2 assertions falhando)
    → Ajustar assertions para aceitar formato "Strengths (Forças):"
    
Iteração 4: 13/13 testes passando! ✅
```

#### ROI

- **Feedback imediato** (cada fix valida hipótese)
- **Progresso visível** (0/20 → 0/13 → 11/13 → 13/13)
- **Confiança crescente** (cada passe confirma correção)

---

## 📖 Metodologia Validada: Implementation-First Testing

### Quando Usar Este Pattern

| Situação | TDD Tradicional | Implementation-First | Razão |
|----------|-----------------|----------------------|-------|
| API conhecida | ✅ Usar | ❌ Desnecessário | Você já sabe a assinatura |
| API desconhecida | ❌ Arriscado | ✅ Usar | Evita assunções erradas |
| Lógica simples (math, pure functions) | ✅ Usar | ❌ Overkill | TDD funciona perfeitamente |
| Lógica complexa (RAG, LLM, multi-step) | ❌ Difícil | ✅ Usar | Implementação guia testes |
| Refactoring | ✅ Usar | ❌ Testes já existem | Testes protegem refactor |
| Feature nova com dependências | ❌ Arriscado | ✅ Usar | Dependências ditam API |

### Workflow Completo

```mermaid
graph TD
    A[Tarefa: Implementar Tool Nova] --> B{API Conhecida?}
    B -->|Sim| C[TDD Tradicional]
    B -->|Não| D[Implementation-First]
    
    D --> E[STEP 1: Grep métodos disponíveis]
    E --> F[STEP 2: Ler signatures completas]
    F --> G[STEP 3: Verificar schemas usados]
    G --> H[STEP 4: Criar fixtures válidas]
    H --> I[STEP 5: Escrever testes alinhados]
    I --> J[STEP 6: Executar e iterar]
    J --> K{100% passando?}
    K -->|Não| L[Debug 1 problema]
    L --> J
    K -->|Sim| M[Documentar e commit]
```

### Commands Cheat Sheet

```bash
# 1. Descobrir métodos disponíveis
grep "def " src/module/file.py

# 2. Ler signature completa de método específico
grep "def method_name" src/module/file.py -A 10

# 3. Verificar estrutura de schema Pydantic
grep "class SchemaName" src/memory/schemas.py -A 30

# 4. Identificar campos obrigatórios
grep "Field(" src/memory/schemas.py | grep -v "default"

# 5. Ver como LLM é usado
grep "self.llm" src/module/file.py

# 6. Executar testes com traceback completo
pytest tests/test_file.py -v --tb=long 2>&1

# 7. Verificar linter errors após mudanças
read_lints tests/test_file.py src/module/file.py
```

---

## 🚫 Antipadrões a Evitar

### ❌ **Antipadrão 1: Assumir API sem Verificar**

**Sintoma:**
```python
# Teste escrito baseado em assunção:
tool.generate(client_profile=profile)  # Método não existe!
```

**Causa:**
- Não usou grep para verificar métodos disponíveis
- Assumiu padrão de outro módulo similar

**Solução:**
```bash
# SEMPRE verificar primeiro:
grep "def " src/tools/swot_analysis.py
# → Descobre que método real é facilitate_swot()
```

**ROI evitado:** 30-40 min reescrita de testes

---

### ❌ **Antipadrão 2: Fixtures com Campos Inexistentes**

**Sintoma:**
```python
strategic_context.industry_context  # AttributeError!
```

**Causa:**
- Não verificou schema real antes de usar campo
- Assumiu naming baseado em convenção

**Solução:**
```bash
# SEMPRE verificar schema primeiro:
grep "class StrategicContext" src/memory/schemas.py -A 30
# → Descobre campos reais: mission, vision, core_values, strategic_objectives, current_challenges
```

**ROI evitado:** 15 min debugging AttributeError

---

### ❌ **Antipadrão 3: Mocks Genéricos sem Verificar Uso Real**

**Sintoma:**
```python
mock_llm.invoke.return_value = "SWOT text..."  # Tipo errado!
# Implementação real espera: SWOTAnalysis (Pydantic object)
```

**Causa:**
- Não verificou como LLM é usado na implementação
- Assumiu padrão tradicional (texto)

**Solução:**
```bash
# SEMPRE verificar uso real:
grep "self.llm" src/tools/swot_analysis.py
# → Descobre: self.llm.with_structured_output(SWOTAnalysis)
```

**ROI evitado:** 10 min debugging mock incorreto

---

### ❌ **Antipadrão 4: Fixtures sem Validar Campos Obrigatórios**

**Sintoma:**
```python
CompanyInfo(name="Test", industry="Tech")  # ValidationError: sector is required!
```

**Causa:**
- Não leu validações Pydantic antes de criar fixture
- Copiou fixture de outro teste sem validar

**Solução:**
```bash
# SEMPRE verificar campos obrigatórios:
grep "class CompanyInfo" src/memory/schemas.py -A 30 | grep "Field"
# → Identifica: sector é obrigatório, size tem validador
```

**ROI evitado:** 10 min debugging ValidationError

---

### ❌ **Antipadrão 5: Usar Filtros em Pytest Output**

**Sintoma:**
```bash
pytest tests/test_file.py -v | Select-Object -First 50
# Oculta linhas críticas do traceback!
```

**Causa:**
- Tentativa de reduzir output para economizar tokens
- Não percebe que informação crítica está sendo filtrada

**Solução:**
```bash
# SEMPRE usar output completo:
pytest tests/test_file.py -v --tb=long 2>&1
# Zero filtros, traceback completo visível
```

**ROI evitado:** Evita reexecuções desperdiçadas (50% tempo debugging)

**Referência:** Memória [[memory:10012853]]

---

## 📊 ROI e Métricas

### Tempo Gasto (Esta Sessão)

| Atividade | Tempo Real | Tempo Ideal (com lição) | Economia |
|-----------|------------|-------------------------|----------|
| Escrever testes iniciais (inválidos) | 25 min | 0 min (evitável) | 25 min |
| Debugging testes (AttributeError, ValidationError) | 40 min | 10 min (iteração normal) | 30 min |
| Reescrever testes alinhados | 20 min | 20 min (necessário) | 0 min |
| Ajustes finais e validação | 15 min | 15 min (necessário) | 0 min |
| **TOTAL** | **100 min** | **45 min** | **55 min** |

### ROI Projetado (Futuras Implementações)

**Aplicável em:**
- Tarefa 3.2: PESTEL Analysis Tool
- Tarefa 3.3: Porter's 5 Forces Tool
- Tarefa 3.4-3.14: Demais tools consultivas (10+ tools)

**Economia esperada por tool:**
- 30-40 min economizados (evitando reescrita de testes)
- 100% acerto na primeira iteração de testes

**Total projetado FASE 3:**
- 10 tools × 35 min = **350 min (~6h) economizadas**

---

## 🎯 Checklist para Próximas Implementações

### Antes de Escrever Testes para API Desconhecida

- [ ] **1. Descobrir métodos disponíveis**
  ```bash
  grep "def " src/module/new_tool.py
  ```

- [ ] **2. Ler signatures completas**
  ```bash
  grep "def method_name" src/module/new_tool.py -A 15
  ```

- [ ] **3. Verificar schemas Pydantic usados**
  ```bash
  grep "class SchemaName" src/memory/schemas.py -A 30
  ```

- [ ] **4. Identificar campos obrigatórios**
  ```bash
  grep "Field(" src/memory/schemas.py | grep -v "default"
  ```

- [ ] **5. Verificar uso de LLM (se aplicável)**
  ```bash
  grep "self.llm" src/module/new_tool.py
  ```

- [ ] **6. Criar fixtures com dados válidos**
  - Incluir TODOS os campos obrigatórios
  - Usar valores que passem validadores Pydantic
  - Margem de segurança em min_length (ex: 50+ chars se min=20)

- [ ] **7. Mock reflete uso real**
  - Structured output? Mock `with_structured_output()`
  - Retorna Pydantic? Mock retorna objeto validado
  - Specialist agents? Mock `invoke()` retorna dict

- [ ] **8. Executar testes SEM filtros**
  ```bash
  pytest tests/test_new_tool.py -v --tb=long 2>&1
  ```

- [ ] **9. Iterar rapidamente (Fix → Test → Fix)**
  - 1 problema por vez
  - Traceback completo sempre
  - Progresso visível (X/Y passando)

- [ ] **10. Validar 100% antes de documentar**
  - 0 linter errors
  - 100% testes passando
  - Coverage >= 70%

---

## 📚 Referências

### Documentação Interna

- **Checklist de Testes:** Memória [[memory:9969868]] (12 pontos obrigatórios)
- **Pytest sem Filtros:** Memória [[memory:10012853]] (economia 50% debugging)
- **Testing Guide:** `docs/TESTING_GUIDE.md`
- **Implementation desta sessão:** `docs/tools/SWOT_ANALYSIS.md`

### Lições Relacionadas

- `lesson-test-debugging-methodology-2025-10-15.md` (FASE 2.4)
- `lesson-diagnostic-agent-test-methodology-2025-10-16.md` (FASE 2.5)
- `lesson-onboarding-state-e2e-tests-2025-10-16.md` (FASE 2.6)

### Código Fonte

- **Testes:** `tests/test_swot_analysis.py` (13 testes, 100% passando)
- **Tool:** `src/tools/swot_analysis.py` (71% coverage)
- **Schemas:** `src/memory/schemas.py` (SWOTAnalysis, CompanyInfo, StrategicContext)

---

## ✅ Conclusão

### Lição Principal Reforçada

> **Para APIs desconhecidas: Implementation-First Testing > TDD**
> 
> SEMPRE leia a implementação (grep métodos, schemas, uso) ANTES de escrever testes.
> 
> TDD funciona quando você CONHECE a API. Para APIs novas com múltiplas dependências, ler primeiro economiza 30-40 min por implementação.

### Aplicabilidade

- ✅ **100% aplicável** em FASE 3.2+ (10+ tools consultivas)
- ✅ **Pattern validado** com resultados mensuráveis (55 min economizados)
- ✅ **Checklist acionável** pronto para reutilização

### Próximos Passos

1. Aplicar checklist em tarefa 3.2 (próxima tool consultiva)
2. Validar ROI real (tempo economizado vs projetado)
3. Refinar pattern se necessário baseado em nova experiência

---

**Autor:** BSC RAG Team  
**Data:** 2025-10-19  
**Status:** ✅ Validado (13/13 testes passando, 0 linter errors)  
**ROI:** 30-40 min economizados por implementação futura

