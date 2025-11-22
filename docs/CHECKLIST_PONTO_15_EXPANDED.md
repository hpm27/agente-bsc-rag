# ✅ CHECKLIST PONTO 15 EXPANDIDO - Prevenção AttributeError

## Contexto

**9 Bugs de AttributeError resolvidos na Sessão 39** (2025-11-21):
- Bug #5: action_plan.company_name
- Bug #5: action.name → action.action_title
- Bug #6: strategy_map.objectives → flatten 4 perspectivas
- Bug #6: strategy_map.connections → cause_effect_connections
- Bug #7: diagnostic_pydantic.summary → executive_summary
- Bug #8: diagnostic.company_info → client_profile.company
- Bug #8: diagnostic.top_gaps → removido (não existe)
- **Bug #9: obj.owner → removido (não existe)** ← RESOLVIDO AGORA

**Causa Raiz Sistêmica**: Código assume estrutura de schemas Pydantic sem validação prévia.

---

## 📋 CHECKLIST OBRIGATÓRIO (Aplicar ANTES de usar qualquer schema Pydantic)

### STEP 1: GREP SCHEMA COMPLETO

```bash
grep "class SchemaName(BaseModel)" src/memory/schemas.py -A 50
```

**O que validar**:
- ✅ Lista COMPLETA de campos disponíveis
- ✅ Tipos de dados (str, int, list, Literal, Optional)
- ✅ Campos obrigatórios (sem default) vs opcionais (com default)
- ✅ Validators customizados (@field_validator)
- ✅ min_length, max_length, ge, le constraints

**Exemplo Bug #9 (StrategicObjective)**:
```bash
$ grep "class StrategicObjective" src/memory/schemas.py -A 60

# RESULTADO: Campos reais:
# - name: str (obrigatório)
# - description: str (obrigatório)
# - perspective: Literal[...] (obrigatório)
# - timeframe: str (obrigatório)
# - success_criteria: list[str] (obrigatório)
# - related_kpis: list[str] (opcional, default=[])
# - priority: Literal["Alta", "Media", "Baixa"] (opcional, default="Media")
# - dependencies: list[str] (opcional, default=[])

# ❌ CAMPO 'owner' NÃO EXISTE!
```

---

### STEP 2: LISTAR CAMPOS QUE CÓDIGO USA

```bash
grep "\.field_name|schema_var\['field_name'\]" src/ -r -C 3
```

**Exemplo Bug #9**:
```bash
$ grep "\.owner" src/ -r -C 3

# RESULTADO: 1 ocorrência
src/tools/strategy_map_designer.py:304: obj.owner  ← ❌ CAMPO INEXISTENTE
```

---

### STEP 3: COMPARAR USADO vs DISPONÍVEL

| Campo Usado no Código | Existe no Schema? | Status |
|---|---|---|
| obj.name | ✅ Sim | OK |
| obj.timeframe | ✅ Sim | OK |
| obj.priority | ✅ Sim | OK |
| obj.owner | ❌ NÃO | **BUG #9** |

---

### STEP 4: CORRIGIR TODOS DE UMA VEZ

**NÃO fazer**: Corrigir 1 local e esperar próximo erro
**FAZER**: Grep TODOS locais + corrigir TODOS simultaneamente

**Exemplo Bug #9**:
```python
# ANTES (1 local):
objectives_summary += f"  {idx}. {obj.name} (owner: {obj.owner}, timeframe: {obj.timeframe})\n"

# DEPOIS (1 local corrigido + comentário):
# Bug #9 fix: StrategicObjective NÃO tem campo 'owner' (campos reais: name, description, perspective, timeframe, success_criteria, related_kpis, priority, dependencies)
objectives_summary += f"  {idx}. {obj.name} (timeframe: {obj.timeframe}, priority: {obj.priority})\n"
```

---

### STEP 5: ADICIONAR VALIDAÇÃO DEFENSIVA (Opcional)

Para schemas que podem evoluir, adicionar validação hasattr():

```python
# Defensivo (para schemas instáveis):
priority_str = f"priority: {obj.priority}" if hasattr(obj, "priority") else "priority: N/A"
objectives_summary += f"  {idx}. {obj.name} ({priority_str}, timeframe: {obj.timeframe})\n"
```

**Quando usar**:
- ✅ Schemas de bibliotecas externas (podem mudar)
- ✅ Schemas com muitos campos opcionais
- ❌ Schemas internos estáveis (usar assert via testes ao invés de hasattr)

---

## 🎯 ROI VALIDADO

**Tempo Investido por Bug**:
- PONTO 15 aplicado: 5-10 min (grep schema + validar campos)
- SEM PONTO 15: 30-60 min (loop infinito + debugging runtime + correção iterativa)

**ROI**: 3-6x economia de tempo (5-10 min vs 30-60 min)

**Aplicável**: 100% bugs AttributeError (9 de 9 na Sessão 39)

---

## 📊 Estatísticas Sessão 39

| Métrica | Valor |
|---|---|
| **Bugs AttributeError** | 9 |
| **Tempo Total Debugging** | ~3h 30min |
| **Tempo Médio por Bug** | ~23 min |
| **Se PONTO 15 aplicado** | ~1h 15min estimado (-63%) |
| **ROI Prevenção** | 2h 15min economizados |

---

## 🚨 QUANDO APLICAR ESTE CHECKLIST

✅ **SEMPRE**:
- Criar código novo que usa schemas Pydantic
- Modificar schemas existentes
- Usar schemas de outra pessoa (code review)
- Refatorar código com schemas

❌ **SKIP**:
- Código já tem validação defensiva (hasattr/isinstance)
- Schema é seu e você acabou de criá-lo (mas valide em review!)
- Apenas lendo valores, não acessando campos (ex: print(obj))

---

## 🔗 Referências

- **Sessão 39**: 9 bugs resolvidos (2025-11-21)
- **Lição Completa**: `.cursor/progress/sessao-39-sprint2-bugs-action-plan.md`
- **Prompt Sistemático**: `prompts/DEBUG_QUICK_PROMPT.md`
- **Memória ID**: [[9969868]] - PONTO 15 original

---

**Última Atualização**: 2025-11-21 (após Bug #9)
**Status**: ✅ VALIDADO EM PRODUÇÃO
