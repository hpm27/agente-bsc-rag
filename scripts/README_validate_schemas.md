# Validate Pydantic Schemas - CI/CD Check

**Criado**: SESSÃO 40 (2025-11-21)
**Objetivo**: Prevenir contradições json_schema_extra vs validators Pydantic

---

## 📋 O QUE ESTE SCRIPT FAZ

Valida automaticamente que TODOS exemplos em `json_schema_extra` respeitam validators customizados Pydantic (`@field_validator`, `@model_validator`).

**Problema que resolve**: LLM segue EXEMPLO do `json_schema_extra` ANTES de validators, causando ValidationError em runtime quando exemplo contradiz validators (memória [[10230048]]).

**Exemplo de bug prevenido** (Sessão 40):
```python
# Schema Pydantic:
@model_validator(mode="after")
def validate_priority_score(self):
    if 75 <= self.final_score <= 100 and self.priority_level != "CRITICAL":
        raise ValueError("Score 75-100 deve ser CRITICAL")

# json_schema_extra ERRADO (contradiz validator):
json_schema_extra = {
    "example": {
        "final_score": 79.0,
        "priority_level": "HIGH"  # ❌ CONTRADIÇÃO! Score 79 deve ser CRITICAL
    }
}
```

---

## 🚀 COMO USAR

### **Execução Manual (Desenvolvimento)**

```bash
# Validar todos schemas Pydantic
python scripts/validate_pydantic_schemas.py

# Validar com output verbose (mostra cada schema verificado)
python scripts/validate_pydantic_schemas.py --verbose

# Validar módulo customizado
python scripts/validate_pydantic_schemas.py --module "src.tools.schemas"
```

### **Output Esperado (Sucesso)**

```
======================================================================
VALIDACAO PYDANTIC SCHEMAS - json_schema_extra vs validators
======================================================================
[INFO] Carregando schemas de src.memory.schemas...
[INFO] Encontrados 38 schemas Pydantic
[INFO] 18 schemas com validators customizados (@field_validator ou @model_validator)

======================================================================
RESULTADO FINAL
======================================================================
[OK] TODOS schemas validados com sucesso! (18/18)

[INFO] Nenhuma contradicao json_schema_extra vs validators encontrada.
```

### **Output Esperado (Falha - Exemplo)**

```
======================================================================
VALIDACAO PYDANTIC SCHEMAS - json_schema_extra vs validators
======================================================================
[INFO] Carregando schemas de src.memory.schemas...
[INFO] Encontrados 38 schemas Pydantic
[INFO] 18 schemas com validators customizados

[ERRO] PrioritizedItem:
  json_schema_extra['example'] contradiz validators!
  ValidationError: 1 validation error for PrioritizedItem
  priority_level
    Score 79 deve ter priority_level='CRITICAL', encontrado 'HIGH'
  ACAO: Atualizar example em model_config para respeitar validators

======================================================================
RESULTADO FINAL
======================================================================
[ERRO] 1/18 schemas com contradições!

[RESUMO] Schemas com problemas:
...

[ACAO] Corrija os exemplos json_schema_extra para respeitar validators.
Consulte memoria [[10230048]] sobre Prompt-Schema Alignment.
```

---

## 🔧 INTEGRAÇÃO CI/CD

### **Pre-Commit Hook (Recomendado)**

Adicione ao `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-pydantic-schemas
        name: Validate Pydantic json_schema_extra vs validators
        entry: python scripts/validate_pydantic_schemas.py
        language: system
        pass_filenames: false
        files: ^src/memory/schemas\.py$
```

**Benefício**: Valida automaticamente ANTES de commit. Se exemplo contradiz validator → commit bloqueado.

### **GitHub Actions CI/CD**

Adicione ao workflow `.github/workflows/tests.yml`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install pydantic

      - name: Validate Pydantic Schemas
        run: python scripts/validate_pydantic_schemas.py
```

---

## 📊 ESTATÍSTICAS PROJETO

**Sessão 40 (2025-11-21)** - Primeira execução:
- **Schemas Pydantic encontrados**: 38
- **Com validators customizados**: 18 (47%)
- **Contradições detectadas**: 3
  1. `PrioritizedItem` - score 79 = HIGH vs CRITICAL (CORRIGIDO)
  2. `PrioritizationMatrix` - rank não sequencial (CORRIGIDO)
  3. `StrategyMapPerspective` - campos obrigatórios faltando (CORRIGIDO)

**Após correções**: ✅ 18/18 passando (100%)

---

## 🎓 COMO FUNCIONA (Detalhes Técnicos)

### **1. Carrega Todos Schemas Pydantic**

```python
# Importa dinamicamente módulo Python
module = importlib.import_module('src.memory.schemas')

# Filtra apenas classes BaseModel
models = [obj for name, obj in inspect.getmembers(module, inspect.isclass)
          if issubclass(obj, BaseModel) and obj is not BaseModel]
```

### **2. Identifica Schemas com Validators Customizados**

```python
# Pydantic V2 armazena validators em __pydantic_decorators__
has_validators = bool(
    getattr(model.__pydantic_decorators__, 'field_validators', {}) or
    getattr(model.__pydantic_decorators__, 'model_validators', {})
)
```

### **3. Valida json_schema_extra Example**

```python
# Tenta instanciar model com dados do exemplo
example = model.model_config.get('json_schema_extra', {}).get('example')
try:
    instance = model(**example)  # ✅ Exemplo válido
except ValidationError as e:
    # ❌ Exemplo contradiz validators!
    print(f"ERRO: {model.__name__} - {e}")
```

### **4. Retorna Exit Code**

- **Exit 0** (sucesso): Todos exemplos respeitam validators
- **Exit 1** (falha): Pelo menos 1 exemplo contradiz validator

---

## 🔗 REFERÊNCIAS

**Baseado em**:
- Stefanie Molin - Pre-Commit Hook Creation Guide (Sep 2024)
  - Featured: PyCoder's Weekly #646, Real Python Podcast #220
  - https://stefaniemolin.com/articles/devx/pre-commit/hook-creation-guide/

**Lições Aprendidas**:
- `docs/lessons/lesson-streamlit-ui-debugging-2025-10-22.md` (Prompt-Schema Alignment)
- Memória [[10230048]] - LLM segue exemplo ANTES de validator

**Best Practices**:
- Pydantic Official Docs - json_schema_extra
- LangChain Docs - How to return structured data
- leocon.dev - Mastering LLM Outputs (Nov 2024)

---

## 💡 QUANDO EXECUTAR

**SEMPRE executar APÓS**:
1. Adicionar/modificar `@field_validator` ou `@model_validator`
2. Adicionar/modificar `json_schema_extra`
3. Criar novo schema Pydantic com validators

**FREQUÊNCIA RECOMENDADA**:
- Manual: Antes de cada commit que modifica schemas
- Automático: Pre-commit hook (recomendado)
- CI/CD: Em todas as PRs que tocam `src/memory/schemas.py`

---

## 🐛 TROUBLESHOOTING

### **Erro: "No module named 'src'"**

**Causa**: Script não consegue importar módulo do projeto.

**Solução**: Script já adiciona PROJECT_ROOT ao PYTHONPATH automaticamente (linha 11-13). Se ainda falhar:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/validate_pydantic_schemas.py
```

### **Erro: "ModuleNotFoundError: No module named 'pydantic'"**

**Solução**: Instalar Pydantic:
```bash
pip install pydantic
```

### **Script reporta falha mas exemplo parece válido**

**Causa**: Validator customizado tem regra que não está óbvia no schema.

**Solução**:
1. Executar com `--verbose` para ver ValidationError completo
2. Grep validator: `grep "@field_validator\|@model_validator" src/memory/schemas.py -A 20`
3. Ler regras do validator e ajustar exemplo

---

## 📝 CHANGELOG

### v1.0 (2025-11-21) - Sessão 40

**Criado**:
- ✅ Script completo de validação
- ✅ 4 steps recipe (Stefanie Molin Sep 2024)
- ✅ CLI com argparse (--verbose, --module)
- ✅ Exit codes para CI/CD (0=success, 1=failure)
- ✅ Logs estruturados

**Validado**:
- ✅ 18 schemas com validators customizados
- ✅ 3 contradições detectadas e corrigidas
- ✅ 100% schemas passando após correções

**ROI**:
- **Prevenção**: Evita ValidationError em runtime (LLM segue exemplo errado)
- **Tempo economizado**: ~90 min debugging por contradição não detectada
- **Manutenção**: Script roda em <2s (execução rápida para CI/CD)

---

## ✅ CHECKLIST PRÉ-COMMIT

Ao criar/modificar schema Pydantic com validators customizados:

- [ ] Grep validator para ver regras: `grep "@field_validator" src/memory/schemas.py -A 20`
- [ ] Criar `json_schema_extra` com exemplo COMPLETO e VÁLIDO
- [ ] Todos campos obrigatórios presentes no exemplo
- [ ] Literal values corretos (ex: "CRITICAL", não "HIGH" quando score >= 75)
- [ ] Executar script: `python scripts/validate_pydantic_schemas.py`
- [ ] Script retorna exit 0 (sucesso)
- [ ] Commit apenas após validação passar

**Consulte também**: Memória [[10230048]] - Checklist PRÉ-PROMPT completo

---

**PRÓXIMO**: Integrar como pre-commit hook para validação automática! 🚀
