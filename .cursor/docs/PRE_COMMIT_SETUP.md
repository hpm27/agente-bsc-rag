# Pre-Commit Hooks - Guia Completo

**Atualizado**: SESSÃO 40 (2025-11-21)
**Status**: ✅ Hook de validação Pydantic schemas integrado

---

## 📋 O QUE SÃO PRE-COMMIT HOOKS

Pre-commit hooks são **scripts automáticos** executados **ANTES** de cada commit. Eles:

- ✅ Validam código automaticamente (formatação, linting, testes)
- ✅ Bloqueiam commit se validações falharem
- ✅ Economizam tempo de code review (detectam problemas antes)
- ✅ Garantem padrões de qualidade consistentes

**Framework usado**: https://pre-commit.com/ (mainstream 2024-2025)

---

## 🚀 INSTALAÇÃO (PRIMEIRA VEZ)

### **1. Instalar pre-commit**

```bash
# Via pip
pip install pre-commit

# Ou via venv do projeto (recomendado)
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install pre-commit
```

### **2. Instalar hooks no repositório**

```bash
# Na raiz do projeto
pre-commit install

# Output esperado:
# pre-commit installed at .git/hooks/pre-commit
```

### **3. Testar instalação**

```bash
# Executar todos hooks manualmente (primeira vez lenta - download de dependências)
pre-commit run --all-files

# Se tudo passar:
# [OK] Todos hooks passaram!
```

---

## 🔧 HOOKS CONFIGURADOS NO PROJETO

### **1. Hooks Básicos de Limpeza**

- `trailing-whitespace`: Remove espaços em branco no final de linhas
- `end-of-file-fixer`: Garante nova linha no final dos arquivos
- `check-yaml`: Valida sintaxe YAML
- `check-json`: Valida sintaxe JSON
- `check-toml`: Valida sintaxe TOML
- `check-added-large-files`: Previne commit de arquivos >500KB
- `check-merge-conflict`: Detecta marcadores de conflito
- `check-case-conflict`: Detecta conflitos de case-sensitivity
- `mixed-line-ending`: Normaliza terminações de linha (LF)

### **2. Black - Formatação Python**

- **O que faz**: Formata código Python automaticamente (PEP 8)
- **Quando roda**: SEMPRE (em todos commits com arquivos .py)
- **Configuração**: `--line-length=100`

### **3. Ruff - Linter Python**

- **O que faz**: Linter moderno Python (substituto de flake8)
- **Quando roda**: SEMPRE (em todos commits com arquivos .py)
- **Configuração**: `--fix` (corrige automaticamente), `--exit-non-zero-on-fix`

### **4. MyPy - Type Checking (Manual)**

- **O que faz**: Verificação de tipos Python
- **Quando roda**: APENAS MANUAL (`pre-commit run mypy --all-files`)
- **Por quê manual**: Pode ter muitos falsos positivos (informativo)

### **5. Pylint - Deep Code Analysis**

- **O que faz**: Análise profunda de código Python
- **Quando roda**: SEMPRE (apenas arquivos em `src/`)
- **Score mínimo**: 7.0/10.0 (tolerante para pre-commit)

### **6. Check No Emoji - CRÍTICO (Custom)**

- **O que faz**: Detecta emojis Unicode em arquivos Python
- **Por quê**: Windows cp1252 não suporta emojis (causa crashes)
- **Quando roda**: SEMPRE (em todos commits com arquivos .py)
- **Memória**: [[9592459]], [[9776249]]

### **7. Validate Pydantic Schemas - NOVO (Custom)** ⭐

- **O que faz**: Valida json_schema_extra vs validators Pydantic
- **Por quê**: LLM segue exemplo ANTES de validator (causa ValidationError)
- **Quando roda**: SEMPRE que `src/memory/schemas.py` é modificado
- **Duração**: ~1.2s
- **Criado**: Sessão 40 (2025-11-21)
- **Memória**: [[10230048]]
- **Documentação**: `scripts/README_validate_schemas.md`

---

## 💻 COMO USAR NO DIA A DIA

### **Workflow Normal (Automático)**

```bash
# 1. Fazer mudanças no código
vim src/memory/schemas.py

# 2. Adicionar ao staging
git add src/memory/schemas.py

# 3. Commit (pre-commit roda AUTOMATICAMENTE)
git commit -m "feat: adicionar novo schema Pydantic"

# Output (exemplo):
# Remove espacos em branco.....................................Passed
# Garante nova linha no final..................................Passed
# Valida sintaxe YAML..........................................Passed
# Black - Formatacao Python....................................Passed
# Ruff - Linter Python.........................................Passed
# Pylint - Deep code analysis..................................Passed
# CRITICO - Detecta emojis.....................................Passed
# Valida json_schema_extra vs validators.......................Passed
# [main abc1234] feat: adicionar novo schema Pydantic
```

### **Se Hook Falhar (Commit Bloqueado)**

```bash
git commit -m "feat: adicionar schema"

# Output (exemplo):
# Valida json_schema_extra vs validators.......................Failed
# - hook id: validate-pydantic-schemas
# - exit code: 1
#
# [ERRO] PrioritizedItem:
#   json_schema_extra['example'] contradiz validators!
#   ValidationError: Score 79 deve ser CRITICAL, encontrado HIGH
#   ACAO: Atualizar example em model_config para respeitar validators
#
# [ACAO] Corrija os exemplos json_schema_extra para respeitar validators.

# Commit foi BLOQUEADO! Corrigir problema primeiro:
vim src/memory/schemas.py  # Corrigir exemplo

# Adicionar mudança e tentar commit novamente
git add src/memory/schemas.py
git commit -m "feat: adicionar schema Pydantic"  # Agora passa!
```

### **Executar Hooks Manualmente (Sem Commit)**

```bash
# Executar TODOS hooks em TODOS arquivos
pre-commit run --all-files

# Executar hook específico
pre-commit run validate-pydantic-schemas --all-files
pre-commit run black --all-files
pre-commit run ruff --all-files

# Executar hook específico em arquivo específico
pre-commit run validate-pydantic-schemas --files src/memory/schemas.py
```

### **Pular Hooks Temporariamente (NÃO RECOMENDADO)**

```bash
# Pular TODOS hooks (usar APENAS em emergências)
git commit -m "hotfix" --no-verify

# ⚠️ AVISO: Só usar se:
# - Hotfix crítico em produção
# - Hook bugado bloqueando commit válido
# - CI/CD vai validar depois de qualquer forma
```

---

## 🐛 TROUBLESHOOTING

### **Problema: "pre-commit: command not found"**

**Solução**: Instalar pre-commit
```bash
pip install pre-commit
# Ou adicionar ao PATH se instalado com --user
```

### **Problema: Hook demora muito (>10s)**

**Causa**: Primeira execução baixa dependências.

**Solução**: Esperar primeira vez completar (cria cache). Próximas execuções são rápidas (~2-5s).

### **Problema: "validate-pydantic-schemas: No such file or directory"**

**Causa**: Script não encontrado.

**Solução**: Verificar que `scripts/validate_pydantic_schemas.py` existe:
```bash
ls scripts/validate_pydantic_schemas.py
# Deve existir
```

### **Problema: Hook passa local mas falha no CI/CD**

**Causa**: Diferença de ambiente (Python version, dependências).

**Solução**:
```bash
# Garantir mesmo Python version
python --version  # Deve ser 3.12.x

# Atualizar pre-commit cache
pre-commit clean
pre-commit run --all-files
```

### **Problema: "RuntimeError: No module named 'pydantic'"**

**Causa**: Dependências não instaladas.

**Solução**:
```bash
pip install pydantic
# Ou instalar todas dependências do projeto
pip install -r requirements.txt
```

---

## 🔄 MANUTENÇÃO

### **Atualizar Hooks para Versões Mais Recentes**

```bash
# Atualizar TODOS hooks para latest stable
pre-commit autoupdate

# Output:
# Updating https://github.com/psf/black ... 25.11.0 -> 25.12.0
# Updating https://github.com/astral-sh/ruff-pre-commit ... v0.14.5 -> v0.15.0
```

### **Limpar Cache (Se Hooks Bugados)**

```bash
# Limpar cache de todos hooks
pre-commit clean

# Reinstalar hooks
pre-commit install --install-hooks
```

### **Desinstalar Pre-Commit Hooks**

```bash
# Remove hooks do repositório
pre-commit uninstall

# Hooks não rodam mais, mas .pre-commit-config.yaml permanece
```

---

## 📊 ESTATÍSTICAS DO PROJETO

**Hooks configurados**: 7 (5 externos + 2 custom)
**Duração média**: 3-5s (após primeira execução)
**Taxa de bloqueio**: ~10-15% commits (esperado - detecta problemas early)

**Custom Hooks**:
1. `check-no-emoji` - Detecta emojis (Windows cp1252)
2. `validate-pydantic-schemas` - Valida json_schema_extra vs validators ⭐ NOVO

---

## 🎓 BEST PRACTICES

### **1. Executar Hooks ANTES de Push**

```bash
# Boa prática: rodar todos hooks antes de push
pre-commit run --all-files
git push origin feature-branch
```

### **2. Commit Frequente (Small Commits)**

✅ Commits pequenos = hooks mais rápidos
❌ Commits gigantes = hooks lentos (muitos arquivos)

### **3. Não Pular Hooks Sistematicamente**

❌ **ERRADO**: `git commit --no-verify` sempre
✅ **CORRETO**: Corrigir problemas reportados pelos hooks

### **4. Manter .pre-commit-config.yaml Atualizado**

```bash
# Atualizar mensalmente (ou quando novo hook disponível)
pre-commit autoupdate
git add .pre-commit-config.yaml
git commit -m "chore: atualizar pre-commit hooks"
```

---

## 🔗 REFERÊNCIAS

**Framework**:
- https://pre-commit.com/ (documentação oficial)

**Hooks Usados**:
- https://github.com/pre-commit/pre-commit-hooks (básicos)
- https://github.com/psf/black (formatação)
- https://github.com/astral-sh/ruff-pre-commit (linter)
- https://github.com/pre-commit/mirrors-mypy (type checking)
- https://github.com/pycqa/pylint (deep analysis)

**Custom Hooks**:
- Baseado em: Stefanie Molin - Pre-Commit Hook Creation Guide (Sep 2024)
- `scripts/README_validate_schemas.md` (documentação validate-pydantic-schemas)

**Memórias Relacionadas**:
- [[9592459]], [[9776249]] - Check no emoji (Windows cp1252)
- [[10230048]] - Validate Pydantic schemas (Prompt-Schema Alignment)

---

## 💡 FAQ

**P: Preciso rodar `pre-commit install` toda vez que clono o repo?**
R: Sim! Pre-commit hooks são locais (`.git/hooks/`), não versionados.

**P: Posso configurar hooks diferentes para branches diferentes?**
R: Não nativamente. Alternativa: usar `stages` (pre-commit, pre-push, manual).

**P: Hooks rodam em CI/CD também?**
R: Não automaticamente. Mas pode adicionar ao workflow CI/CD:
```yaml
- name: Run pre-commit
  run: pre-commit run --all-files
```

**P: Quanto tempo hooks adicionam ao meu workflow?**
R: ~3-5s por commit (após cache). ROI: detecta problemas 5-10x mais rápido que code review.

**P: Posso desabilitar hook específico temporariamente?**
R: Sim! Editar `.pre-commit-config.yaml` e comentar hook:
```yaml
# - id: validate-pydantic-schemas  # Desabilitado temporariamente
```

---

**ÚLTIMA ATUALIZAÇÃO**: SESSÃO 40 (2025-11-21)
**STATUS**: ✅ 7 hooks configurados, 2 custom, funcionando perfeitamente
