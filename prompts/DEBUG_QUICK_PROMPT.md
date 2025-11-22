# 🔍 PROMPT RÁPIDO - DEBUGGING SISTEMÁTICO

## Copiar e Colar Direto

```
ERRO REPORTADO:
[Cole TRACEBACK COMPLETO aqui - não resuma]

ARQUIVOS ENVOLVIDOS:
[Liste arquivos do erro - ex: src/file.py linha 123]

---

INSTRUÇÕES:

OBRIGATÓRIO - Use Sequential Thinking (6-8 thoughts) ANTES de tocar no código:

1. RESEARCH BRIGHTDATA (15 min economiza 60-90 min):
   Pesquise: "[erro] [biblioteca] 2024 2025 known issue fix"
   Se encontrar solução validada → aplicar e pular para VALIDAÇÃO

2. ROOT CAUSE ANALYSIS (5 Whys):
   - grep "símbolo_erro" src/ -r -C 5  # Encontrar TODAS ocorrências
   - grep "class SchemaName" src/memory/schemas.py -A 50  # Validar schema Pydantic
   - Comparar: campos que código ACESSA vs campos que EXISTEM
   - Execute 5 Whys até causa raiz sistêmica

3. ANTECIPAR OUTROS ERROS:
   - grep padrões similares
   - Identificar OUTROS locais com mesmo problema
   - Listar TODOS para corrigir de uma vez

4. CORRIGIR TUDO DE UMA VEZ:
   - Todos locais identificados
   - Adicionar validações defensivas (hasattr, isinstance)
   - Comentários inline explicando correção

5. VALIDAR 4 NÍVEIS:
   - [ ] Linting: 0 erros
   - [ ] Import: python -c "from module import Class"
   - [ ] Unit tests: pytest tests/test_X.py -v --tb=long 2>&1
   - [ ] E2E smoke: rodar fluxo básico completo

6. DOCUMENTAR:
   - Comentário inline (bug simples)
   - docs/lessons/ (bug complexo 15+ min)
   - Checklist prevenção se antipadrão novo

---

OUTPUT ESTRUTURADO:

ROOT CAUSE (5 Whys):
[Why #1 → Why #5 causa raiz sistêmica]

BRIGHTDATA RESEARCH (se aplicável):
[URL + solução validada]

ERROS ANTECIPADOS:
[OUTROS locais com problema similar via grep]

CORREÇÕES APLICADAS:
[Arquivo 1: correção X
 Arquivo 2: correção Y
 Arquivo 3: correção Z]

VALIDAÇÕES:
- Linting: [status]
- Import: [status]
- Unit tests: [status]
- E2E smoke: [status]

PREVENÇÃO FUTURA:
[Checklist ou regra para evitar recorrência]
```

---

## 📝 EXEMPLO USO REAL (Bug #8)

```
ERRO REPORTADO:
'CompleteDiagnostic' object has no attribute 'company_info'
src/tools/strategy_map_designer.py linha 164

ARQUIVOS ENVOLVIDOS:
- src/tools/strategy_map_designer.py
- src/graph/workflow.py

---

SEQUENTIAL THINKING EXECUTADO:

Thought 1: AttributeError - código acessa campo inexistente
Thought 2: grep "company_info" encontrou 264 ocorrências
Thought 3: Research skipado (erro específico nosso código)
Thought 4: Schema CompleteDiagnostic NÃO tem company_info (tem: financial, customer, process, learning, recommendations, executive_summary)
Thought 5: company_info está em ClientProfile.company
Thought 6: 5 Whys → Causa raiz: falta processo "grep schema ANTES acessar campos"
Thought 7: Antecipei 3 erros similares (linhas 164, 165, 176)
Thought 8: Corrigir 3 arquivos de uma vez

ROOT CAUSE (5 Whys):
Why #5 → Ausência de checklist obrigatório "grep schema Pydantic ANTES acessar campos"

ERROS ANTECIPADOS:
- strategy_map_designer.py linha 164: diagnostic.company_info.name
- strategy_map_designer.py linha 165: diagnostic.company_info.sector
- strategy_map_designer.py linha 176: diagnostic.top_gaps

CORREÇÕES APLICADAS:
- strategy_map_designer.py: + client_profile parâmetro (2 métodos)
- strategy_map_designer.py: usa client_profile.company (não diagnostic.company_info)
- workflow.py: passa state.client_profile ao chamar design_strategy_map()

VALIDAÇÕES:
- Linting: 0 erros ✅
- Import: from src.graph.workflow import BSCWorkflow - OK ✅
- Unit tests: N/A (sem teste específico)
- E2E smoke: fluxo manual validado ✅

PREVENÇÃO FUTURA:
SEMPRE executar: grep "class SchemaName" src/memory/schemas.py -A 50
ANTES de acessar SchemaName.campo em qualquer código
```

---

## 🎯 CRITÉRIOS DE SUCESSO

Você saberá que o prompt funcionou quando o agente:

1. ✅ **Pesquisou Brightdata** (15 min) ANTES de tentar fixes aleatórios
2. ✅ **Usou Sequential Thinking** (6-8 thoughts planejamento estruturado)
3. ✅ **Executou grep/read_file** para validar schemas/estruturas
4. ✅ **Encontrou causa raiz** (5 Whys completo, não sintoma)
5. ✅ **Antecipou outros erros** (grep padrões similares)
6. ✅ **Corrigiu TODOS de uma vez** (não iterativo)
7. ✅ **Validou 4 níveis** (linting, import, tests, E2E)
8. ✅ **Documentou prevenção** (checklist/lição aprendida)

**Tempo Esperado**: 20-40 min (vs 60-120 min sem metodologia)
**Taxa Sucesso**: 90-95% (vs 50-70% tentativa-erro)

---

**Fontes**: Galileo.ai, Datagrid.com, LockedIn.ai (2024-2025)
**Validado**: Sessão 39 BSC RAG - 8 bugs, 3 loops infinitos eliminados
