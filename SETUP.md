# 🚀 Setup Completo - Agente BSC RAG

Este guia configura o ambiente completo para o projeto.

## 📋 Pré-requisitos

- Python 3.10+ instalado
- Docker Desktop instalado e rodando
- Git instalado

## 🔧 Passo 1: Ambiente Virtual

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Ou se estiver usando CMD
.\venv\Scripts\activate.bat

# Verificar ativação (deve mostrar (venv) no prompt)
python --version
```

## 📦 Passo 2: Instalar Dependências

```powershell
# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências principais
pip install -r requirements.txt
```

**Nota**: Se houver erros com algumas bibliotecas específicas (torch, faiss), você pode instalá-las separadamente:

```powershell
# Torch (versão CPU)
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# FAISS
pip install faiss-cpu

# Outras essenciais
pip install loguru pydantic pydantic-settings openai anthropic cohere langchain langgraph langchain-openai langchain-community
```

## 🔑 Passo 3: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```powershell
# Copiar template (se existir)
# Ou criar manualmente
notepad .env
```

**Conteúdo do `.env`**:

```env
# OpenAI (OBRIGATÓRIO)
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Cohere (OBRIGATÓRIO para re-ranking)
COHERE_API_KEY=your-cohere-key-here

# Anthropic (OPCIONAL - para Contextual Retrieval)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Vector Store Configuration
VECTOR_STORE_TYPE=qdrant
VECTOR_STORE_INDEX=bsc_documents

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080

# Redis (mantido para compatibilidade)
REDIS_HOST=localhost
REDIS_PORT=6379

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=10
TOP_N_RERANK=5
HYBRID_SEARCH_WEIGHT_SEMANTIC=0.7
HYBRID_SEARCH_WEIGHT_BM25=0.3

# Contextual Retrieval (Anthropic)
ENABLE_CONTEXTUAL_RETRIEVAL=true
CONTEXTUAL_MODEL=claude-3-5-sonnet-20241022
CONTEXTUAL_CACHE_ENABLED=true

# Agent Configuration
MAX_ITERATIONS=10
TEMPERATURE=0.0
MAX_TOKENS=2000

# Paths
DATA_DIR=./data
LITERATURE_DIR=./data/bsc_literature
MODELS_DIR=./models
LOGS_DIR=./logs

# Monitoring
ENABLE_METRICS=true
DEBUG=false
LOG_LEVEL=INFO
```

## 🐳 Passo 4: Iniciar Serviços Docker

```powershell
# Iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs (se necessário)
docker-compose logs -f

# Serviços disponíveis:
# - Qdrant: http://localhost:6333
# - Weaviate: http://localhost:8080
# - Redis: localhost:6379
```

**Verificar Health Checks**:

```powershell
# Qdrant
curl http://localhost:6333/healthz

# Weaviate
curl http://localhost:8080/v1/.well-known/ready
```

## 🧪 Passo 5: Rodar Testes

```powershell
# Ativar venv primeiro (se não estiver)
.\venv\Scripts\Activate.ps1

# Rodar todos os testes
pytest tests/ -v

# Rodar testes específicos
pytest tests/test_embeddings.py -v
pytest tests/test_retriever.py -v
pytest tests/test_reranker.py -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📚 Passo 6: Preparar Dados BSC

1. **Adicionar Documentos BSC** em `data/bsc_literature/`:
   - Papers acadêmicos sobre Balanced Scorecard
   - Artigos de Kaplan & Norton
   - Casos de uso e melhores práticas
   - Formato: PDF

2. **Rodar Pipeline de Ingestão**:

```powershell
python scripts/build_knowledge_base.py
```

Isso irá:
- ✅ Carregar PDFs
- ✅ Fazer chunking (TableAware)
- ✅ Aplicar Contextual Retrieval (se habilitado)
- ✅ Gerar embeddings OpenAI
- ✅ Indexar no Vector Store (Qdrant/Weaviate)

## ✅ Passo 7: Validar Setup

### Teste Rápido de Retrieval:

```python
from src.rag.retriever import BSCRetriever

retriever = BSCRetriever()
results = retriever.retrieve("O que é Balanced Scorecard?", k=3)

for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result.score:.3f}")
    print(f"   Fonte: {result.metadata.get('source', 'N/A')}")
    print(f"   Preview: {result.content[:100]}...")
```

### Teste dos Agentes:

```python
from src.agents.orchestrator import Orchestrator

orchestrator = Orchestrator()
result = orchestrator.process_query(
    "Quais são as 4 perspectivas do BSC?"
)

print(result["answer"])
```

## 🐛 Troubleshooting

### Erro: "Module not found"
```powershell
# Verificar se venv está ativado
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: "Docker não está rodando"
```powershell
# Iniciar Docker Desktop
# Verificar status
docker ps
```

### Erro: "API Key inválida"
```powershell
# Verificar se .env está na raiz do projeto
# Verificar se as keys estão corretas
# Testar keys individualmente
```

### Erro: "Port already in use"
```powershell
# Parar containers
docker-compose down

# Limpar volumes (CUIDADO: apaga dados)
docker-compose down -v

# Reiniciar
docker-compose up -d
```

## 📊 Estrutura Final

```
agente-bsc-rag/
├── .env                          # ✅ Configurações
├── venv/                         # ✅ Ambiente virtual
├── data/
│   └── bsc_literature/          # ✅ PDFs aqui
├── src/
│   ├── rag/                     # ✅ Pipeline RAG
│   ├── agents/                  # ✅ Multi-agente
│   └── tools/                   # ✅ Ferramentas
├── tests/                       # ✅ Testes
├── scripts/                     # ✅ Utilitários
└── docker-compose.yml           # ✅ Serviços
```

## 🎯 Próximos Passos Após Setup

1. ✅ Validar testes passando
2. ✅ Confirmar ingestão de dados BSC
3. ⏭️ Implementar FASE 1C (LangGraph + Interface)
4. ⏭️ Testes end-to-end
5. ⏭️ Documentação final

---

## 📞 Suporte

Se encontrar problemas, verifique:
1. Logs do Docker: `docker-compose logs`
2. Logs da aplicação: `./logs/`
3. Versões das dependências: `pip list`

**Dica**: Execute cada passo sequencialmente e valide antes de avançar!

