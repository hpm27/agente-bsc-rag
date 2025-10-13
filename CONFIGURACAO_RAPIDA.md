# [SETUP] Configuração Rápida - Agente BSC RAG

## Atualização Realizada (Outubro 2025)

Arquivo `.env` foi recriado com **todas as variáveis atualizadas** que o projeto está usando.

## Principais Mudanças

### Novas Funcionalidades

- **Suporte Multi-Provider LLM**: Agora suporta tanto OpenAI (GPT-4/GPT-5) quanto Anthropic (Claude)
- **Múltiplos Vector Stores**: Qdrant (recomendado), Weaviate e Redis
- **Cache de Embeddings**: Sistema de cache persistente com `diskcache` (30 dias TTL, 5GB max)
- **Contextual Retrieval**: Suporte para GPT-5 ou Claude para geração de contexto
- **Processamento Paralelo**: 4 workers paralelos para agentes

### Variáveis Obrigatórias

```bash
# SEMPRE NECESSARIAS
OPENAI_API_KEY=sk-...              # Embeddings (text-embedding-3-large)
COHERE_API_KEY=...                 # Re-ranking (rerank-multilingual-v3.0)

# NECESSARIA SE USAR CLAUDE
ANTHROPIC_API_KEY=sk-ant-...       # Apenas se DEFAULT_LLM_MODEL=claude-*
```

### Variáveis Importantes

```bash
# Escolha do Modelo LLM
DEFAULT_LLM_MODEL=claude-sonnet-4-5-20250929  # ou gpt-4-turbo-preview ou gpt-5-2025-08-07

# Vector Store (escolha uma)
VECTOR_STORE_TYPE=qdrant           # Recomendado: 'qdrant', 'weaviate' ou 'redis'

# Cache de Embeddings (economia massiva de tempo)
EMBEDDING_CACHE_ENABLED=True
EMBEDDING_CACHE_DIR=.cache/embeddings
EMBEDDING_CACHE_TTL_DAYS=30
EMBEDDING_CACHE_MAX_SIZE_GB=5

# Contextual Retrieval
ENABLE_CONTEXTUAL_RETRIEVAL=True
CONTEXTUAL_PROVIDER=openai         # 'openai' (GPT-5) ou 'anthropic' (Claude)
```

## [CHECK] Próximos Passos

### 1. Adicionar suas API Keys no `.env`

Edite o arquivo `.env` e substitua os placeholders:

```bash
OPENAI_API_KEY=sk-proj-...         # Sua chave real da OpenAI
COHERE_API_KEY=...                 # Sua chave real da Cohere
ANTHROPIC_API_KEY=sk-ant-...       # (Opcional) Sua chave real da Anthropic
```

### 2. Iniciar os Vector Stores

```powershell
# Iniciar todos os containers (Redis, Qdrant, Weaviate)
docker-compose up -d

# Ou iniciar apenas o Qdrant (recomendado)
docker-compose up -d qdrant

# Verificar se estão rodando
docker-compose ps
```

### 3. Criar Ambiente Virtual Python

```powershell
# Criar venv (se ainda nao existe)
python -m venv venv

# Ativar venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Indexar Documentos BSC

```powershell
# Indexar documentos na base de conhecimento
python scripts/build_knowledge_base.py

# O script vai:
# - Ler PDFs/MD de data/bsc_literature/
# - Criar chunks semanticos
# - Gerar embeddings (com cache!)
# - Indexar no vector store escolhido (Qdrant)
```

### 5. Testar o Sistema

```powershell
# Metodo 1: Interface Streamlit
streamlit run app/main.py

# Metodo 2: Script de teste rapido
python examples/run_workflow_example.py
```

## [INFO] Arquivos Atualizados

- `.env` - **CRIADO** com configuração completa e atualizada
- `.env.example` - **ATUALIZADO** com mesma estrutura

## [INFO] Escolha de Modelo LLM

### Opção 1: Claude Sonnet 4.5 (Recomendado para 2025)

```bash
DEFAULT_LLM_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=sk-ant-...       # OBRIGATORIO
```

**Vantagens:**

- Melhor raciocínio e análise estratégica
- Excelente para contextos longos (200K tokens)
- Melhor custo-benefício em 2025

### Opção 2: GPT-4 Turbo

```bash
DEFAULT_LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...              # OBRIGATORIO
```

**Vantagens:**

- Muito testado e estável
- Boa documentação

### Opção 3: GPT-5 (2025)

```bash
DEFAULT_LLM_MODEL=gpt-5-2025-08-07
OPENAI_API_KEY=sk-...              # OBRIGATORIO
GPT5_REASONING_EFFORT=medium       # minimal, low, medium, high
```

**Vantagens:**

- Raciocínio avançado nativo
- Excelente para análise complexa
- Pode usar para Contextual Retrieval

## [INFO] Vector Store - Qual Escolher?

### Qdrant (Recomendado)

```bash
VECTOR_STORE_TYPE=qdrant
docker-compose up -d qdrant
```

**Vantagens:**

- Muito rápido (Rust)
- Web UI em <http://localhost:6333/dashboard>
- Melhor para produção

### Weaviate (Alternativa)

```bash
VECTOR_STORE_TYPE=weaviate
docker-compose up -d weaviate
```

**Vantagens:**

- Integração nativa com OpenAI
- GraphQL API
- Mais features enterprise

### Redis (Compatibilidade)

```bash
VECTOR_STORE_TYPE=redis
docker-compose up -d redis
```

**Vantagens:**

- Já conhece Redis
- RedisInsight UI em <http://localhost:8001>
- Mais simples

## [WARN] Troubleshooting

### Erro: "ANTHROPIC_API_KEY não configurada"

**Causa:** Você definiu `DEFAULT_LLM_MODEL=claude-*` mas não tem chave Anthropic

**Solução:**

1. Adicionar `ANTHROPIC_API_KEY` no `.env`, OU
2. Mudar para `DEFAULT_LLM_MODEL=gpt-4-turbo-preview`

### Erro: Docker containers não iniciam

**Solução:**

```powershell
# Parar tudo
docker-compose down

# Limpar volumes (ATENCAO: apaga dados!)
docker-compose down -v

# Iniciar novamente
docker-compose up -d
```

### Erro: Import não encontrado

**Solução:**

```powershell
# Verificar se venv esta ativo
.\venv\Scripts\Activate.ps1

# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

## [INFO] Performance - Cache de Embeddings

O cache de embeddings reduz **drasticamente** o tempo de indexação:

- **Primeira execução:** ~15-20 min (gera embeddings)
- **Re-execuções:** ~2-3 min (usa cache)
- **Taxa de acerto:** 80-95% após primeira execução

Configuração no `.env`:

```bash
EMBEDDING_CACHE_ENABLED=True
EMBEDDING_CACHE_DIR=.cache/embeddings
EMBEDDING_CACHE_TTL_DAYS=30
EMBEDDING_CACHE_MAX_SIZE_GB=5
```

## [INFO] Documentação Adicional

- `README.md` - Documentação principal do projeto
- `docs/QUICKSTART.md` - Tutorial detalhado de início rápido
- `docs/STREAMLIT_GUIDE.md` - Guia da interface web
- `docs/ARCHITECTURE.md` - Arquitetura detalhada do sistema
- `docs/GPT5_CONTEXTUAL_RETRIEVAL.md` - Como usar GPT-5 para contextual retrieval

## [CHECK] Checklist de Configuração

- [ ] Arquivo `.env` criado com API keys reais
- [ ] Docker Desktop rodando
- [ ] Containers iniciados (`docker-compose up -d`)
- [ ] Ambiente virtual Python criado e ativado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Documentos BSC adicionados em `data/bsc_literature/`
- [ ] Base de conhecimento indexada (`python scripts/build_knowledge_base.py`)
- [ ] Interface Streamlit testada (`streamlit run app/main.py`)

## [INFO] Suporte

Problemas ou dúvidas:

1. Verificar logs em `logs/`
2. Testar conectividade: `python scripts/validate_setup.py`
3. Abrir issue no repositório

---

**Última Atualização:** Outubro 2025  
**Versão do Projeto:** 1.0.0  
**Python Requerido:** 3.9+
