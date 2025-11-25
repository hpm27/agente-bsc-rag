# [EMOJI] Guia de Execução - Agente BSC RAG

## [FAST] Início Rápido (Para Usuários)

### 1. Verifique Pré-requisitos

```powershell
# Docker rodando?
docker ps

# Python instalado?
python --version  # Deve ser 3.9+
```

### 2. Configure API Keys

Edite o arquivo `.env` na raiz do projeto:

```env
# OBRIGATÓRIOS
OPENAI_API_KEY=sk-proj-...
COHERE_API_KEY=...

# OPCIONAL (mas recomendado para melhor qualidade)
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Inicie os Serviços

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Verificar se tudo está OK
python scripts/validate_setup.py

# Se Docker não estiver rodando
docker-compose up -d qdrant weaviate redis
```

### 4. Indexe Documentos (Primeira Vez)

```powershell
# O livro BSC já está em data/bsc_literature/
# Execute a indexação:
python scripts/build_knowledge_base.py
```

**[TIMER] Tempo estimado:**

- Com Contextual Retrieval (recomendado): ~10-15 minutos
- Sem Contextual Retrieval: ~2-3 minutos

**[EMOJI] Dica:** A primeira indexação demora mais. Depois, você pode adicionar novos documentos e re-executar.

### 5. Inicie a Interface Web

```powershell
streamlit run app/main.py
```

Aguarde a mensagem:

```
Local URL: http://localhost:8501
```

### 6. Use o Sistema! [EMOJI]

Abra seu navegador em: [http://localhost:8501](http://localhost:8501)

**Experimente perguntas como:**

- "Quais são os principais KPIs da perspectiva financeira?"
- "Como implementar BSC em uma empresa?"
- "Qual a relação entre satisfação de clientes e lucratividade?"

---

## [EMOJI] Troubleshooting Comum

### Problema: Docker não inicia

**Solução:**

```powershell
# Verificar se Docker Desktop está aberto
# Se não, abrir e aguardar inicialização

# Iniciar apenas serviços essenciais
docker-compose up -d qdrant redis
```

### Problema: "ModuleNotFoundError"

**Solução:**

```powershell
# Reinstalar dependências
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Problema: "Invalid API Key"

**Solução:**

1. Verifique se o arquivo `.env` existe na raiz
2. Verifique se as chaves estão corretas (sem espaços)
3. OpenAI keys começam com `sk-proj-...`
4. Anthropic keys começam com `sk-ant-...`

### Problema: Indexação muito lenta

**Opção 1: Desativar Contextual Retrieval (mais rápido, menos preciso)**

```env
# No .env
ENABLE_CONTEXTUAL_RETRIEVAL=false
```

**Opção 2: Aguardar (recomendado)**

- Primeira indexação é lenta (API calls)
- Próximas serão incrementais e rápidas

### Problema: "Connection refused" ao Qdrant

**Solução:**

```powershell
# Verificar se container está rodando
docker ps | Select-String qdrant

# Se não estiver, iniciar
docker-compose up -d qdrant

# Aguardar 10 segundos para Qdrant inicializar
Start-Sleep -Seconds 10
```

### Problema: Streamlit não abre no navegador

**Solução:**

```powershell
# Abrir manualmente
Start-Process "http://localhost:8501"

# Ou especificar porta diferente
streamlit run app/main.py --server.port 8502
```

---

## [EMOJI] Executar Testes

### Testes Unitários

```powershell
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

### Testes End-to-End

[WARN] **Requer documentos indexados**

```powershell
pytest tests/integration/test_e2e.py -v -s
```

### Testes com Cobertura

```powershell
pytest tests/ --cov=src --cov-report=html
# Abrir htmlcov/index.html para ver relatório
```

---

## [EMOJI] Monitorar Sistema

### 1. Logs da Aplicação

```powershell
# Ver logs em tempo real
Get-Content logs/app.log -Wait -Tail 50

# Ver apenas erros
Get-Content logs/errors.log -Wait -Tail 20
```

### 2. Docker Containers

```powershell
# Status dos containers
docker-compose ps

# Logs do Qdrant
docker-compose logs -f qdrant

# Logs do Weaviate
docker-compose logs -f weaviate
```

### 3. Qdrant Web UI

Acesse: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

**Ver:**

- Collections (índices)
- Número de vetores
- Status do cluster

### 4. RedisInsight (se usar Redis)

Acesse: [http://localhost:8001](http://localhost:8001)

---

## [EMOJI] Configurações Avançadas

### Ajustar Performance

Edite `.env`:

```env
# Mais documentos recuperados = mais contexto (mas mais lento)
TOP_K_RETRIEVAL=20    # Padrão: 10
TOP_N_RERANK=10       # Padrão: 5

# Chunks maiores = mais contexto por chunk
CHUNK_SIZE=1500       # Padrão: 1000
CHUNK_OVERLAP=300     # Padrão: 200
```

### Ajustar Pesos Hybrid Search

```env
# Mais semântica (bom para queries conceituais)
HYBRID_SEARCH_WEIGHT_SEMANTIC=0.8
HYBRID_SEARCH_WEIGHT_BM25=0.2

# Mais keyword (bom para queries factuais)
HYBRID_SEARCH_WEIGHT_SEMANTIC=0.6
HYBRID_SEARCH_WEIGHT_BM25=0.4
```

### Trocar Vector Store

```env
# Qdrant (recomendado - melhor hybrid search)
VECTOR_STORE_TYPE=qdrant

# Weaviate (alternativa, excelente também)
VECTOR_STORE_TYPE=weaviate

# Redis (legacy, mas funciona)
VECTOR_STORE_TYPE=redis
```

### Ajustar Temperatura do LLM

```env
# Mais determinístico (respostas consistentes)
TEMPERATURE=0.0

# Mais criativo (respostas variadas)
TEMPERATURE=0.7
```

---

## [EMOJI] Adicionar Mais Documentos

### 1. Adicione arquivos

```powershell
# Coloque PDFs/MD em:
data/bsc_literature/

# Formatos aceitos:
# - PDF (.pdf)
# - Word (.docx)
# - Texto (.txt)
# - Markdown (.md)
```

### 2. Re-indexe

```powershell
.\venv\Scripts\Activate.ps1
python scripts/build_knowledge_base.py
```

**[EMOJI] Dica:** O sistema detecta documentos já indexados e pula (indexação incremental).

### 3. Verifique no Qdrant UI

- Acesse: <http://localhost:6333/dashboard>
- Verifique a collection `bsc_documents`
- Confirme aumento no número de vetores

---

## [EMOJI] Reiniciar Completamente

### Limpar TUDO e recomeçar

```powershell
# 1. Parar containers
docker-compose down -v

# 2. Limpar dados
Remove-Item data/bsc_literature/* -Exclude *.md
Remove-Item logs/* -ErrorAction SilentlyContinue

# 3. Reiniciar containers
docker-compose up -d

# 4. Re-indexar
.\venv\Scripts\Activate.ps1
python scripts/build_knowledge_base.py

# 5. Iniciar interface
streamlit run app/main.py
```

---

## [EMOJI] Comandos Úteis

```powershell
# Status geral
python scripts/validate_setup.py

# Ver configurações
Get-Content .env

# Ver estatísticas do índice
python -c "from src.rag.vector_store_factory import create_vector_store; store = create_vector_store(); print(store.get_stats())"

# Limpar cache Streamlit
streamlit cache clear

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Verificar portas em uso
netstat -ano | Select-String "6333|8501|6379"
```

---

## 🆘 Suporte

**Antes de abrir issue:**

1. [OK] Verifique logs: `logs/app.log` e `logs/errors.log`
2. [OK] Execute: `python scripts/validate_setup.py`
3. [OK] Confirme Docker rodando: `docker ps`
4. [OK] Verifique API keys no `.env`

**Se ainda tiver problemas:**

- [EMOJI] Abra uma issue no GitHub
- [EMOJI] Inclua logs relevantes
- [EMOJI] Mencione sistema operacional e versão Python

---

## [EMOJI] Checklist Pré-Execução

Antes de usar o sistema, confirme:

- [ ] Docker Desktop rodando
- [ ] Python 3.9+ instalado
- [ ] Arquivo `.env` configurado com API keys
- [ ] Ambiente virtual ativado (`.\venv\Scripts\Activate.ps1`)
- [ ] Containers Docker rodando (`docker ps`)
- [ ] Documentos indexados (executou `build_knowledge_base.py`)
- [ ] Script de validação passou (`validate_setup.py`)

**Se todos os itens estão OK, execute:**

```powershell
streamlit run app/main.py
```

E aproveite! [EMOJI]

---

## [EMOJI] Documentação Adicional

- [Guia Rápido](docs/QUICKSTART.md) - Tutorial completo
- [API Reference](docs/API_REFERENCE.md) - Documentação da API
- [Arquitetura](docs/ARCHITECTURE.md) - Detalhes técnicos
- [Resumo de Implementação](IMPLEMENTATION_SUMMARY.md) - O que foi feito

---

**Última atualização:** 09/10/2025
**Versão:** 1.0.0 (MVP)
