# Guia Rápido - Agente BSC RAG

## 🚀 Início Rápido (5 minutos)

### 1. Pré-requisitos

- Python 3.9+
- Docker Desktop
- Git

### 2. Clone e Setup

```powershell
# Clone o repositório
git clone <repository-url>
cd agente-bsc-rag

# Execute o setup automatizado
.\setup.ps1
```

O script `setup.ps1` irá:
- Criar ambiente virtual Python
- Instalar todas as dependências
- Iniciar containers Docker (Qdrant, Weaviate, Redis)
- Criar arquivo `.env` com templates
- Validar a configuração

### 3. Configure as API Keys

Edite o arquivo `.env` e adicione suas chaves:

```env
# OpenAI (OBRIGATÓRIO)
OPENAI_API_KEY=sua-chave-aqui

# Cohere (OBRIGATÓRIO para re-ranking)
COHERE_API_KEY=sua-chave-aqui

# Anthropic (OPCIONAL - para Contextual Retrieval)
ANTHROPIC_API_KEY=sua-chave-aqui
```

### 4. Indexe Documentos BSC

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Adicione PDFs em data/bsc_literature/
# Depois execute:
python scripts/build_knowledge_base.py
```

### 5. Inicie a Interface

```powershell
streamlit run app/main.py
```

Acesse: [http://localhost:8501](http://localhost:8501)

---

## 📖 Uso Básico

### Interface Streamlit

1. **Digite sua pergunta** no campo de chat
2. **Aguarde o processamento** (2-5 segundos típico)
3. **Veja a resposta** com:
   - Resposta agregada
   - Respostas por perspectiva
   - Fontes consultadas
   - Avaliação do Judge

### Exemplos de Perguntas

**Factuais (simples):**
```
Quais são os principais KPIs da perspectiva financeira?
Como medir satisfação do cliente no BSC?
```

**Conceituais (moderadas):**
```
Como implementar BSC em uma empresa?
Por que o BSC é importante para estratégia?
```

**Complexas:**
```
Como alinhar objetivos estratégicos com métricas BSC?
Como criar um mapa estratégico completo?
```

---

## 🔧 Configurações Importantes

### Vector Store

No `.env`, você pode escolher:
```env
VECTOR_STORE_TYPE=qdrant  # ou 'weaviate' ou 'redis'
```

**Recomendado**: `qdrant` (melhor performance, hybrid search nativo)

### Contextual Retrieval

Para ativar a técnica avançada da Anthropic:
```env
ENABLE_CONTEXTUAL_RETRIEVAL=true
ANTHROPIC_API_KEY=sua-chave-aqui
```

Isso melhora a precisão em 35-49%, mas requer chave Anthropic.

### Chunking

Ajuste o tamanho dos chunks:
```env
CHUNK_SIZE=1000        # Tamanho de cada chunk (tokens)
CHUNK_OVERLAP=200      # Sobreposição entre chunks
```

### Retrieval

Configure quantos documentos buscar:
```env
TOP_K_RETRIEVAL=10     # Documentos retornados pela busca
TOP_N_RERANK=5         # Documentos após re-ranking
```

### Hybrid Search

Ajuste pesos da busca híbrida:
```env
HYBRID_SEARCH_WEIGHT_SEMANTIC=0.7   # Peso da busca semântica
HYBRID_SEARCH_WEIGHT_BM25=0.3       # Peso da busca por palavras-chave
```

---

## 🧪 Executar Testes

```powershell
# Ativar ambiente
.\venv\Scripts\Activate.ps1

# Testes unitários
pytest tests/ -v

# Testes E2E (requer documentos indexados)
pytest tests/integration/test_e2e.py -v

# Testes com cobertura
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Monitoramento

### Logs

Logs são salvos em `logs/`:
- `app.log` - Logs gerais da aplicação
- `errors.log` - Apenas erros

### Métricas

Na interface Streamlit, você pode ver:
- Perspectivas ativadas
- Score do Judge
- Número de fontes consultadas
- Iterações de refinamento
- Latência de processamento

---

## 🐛 Troubleshooting

### Docker não inicia

```powershell
# Verificar se Docker está rodando
docker ps

# Iniciar apenas serviços essenciais
docker-compose up -d qdrant redis
```

### Erro de importação

```powershell
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro de API Key

Verifique se o `.env` está no diretório raiz e com as chaves corretas:
```powershell
cat .env | Select-String "API_KEY"
```

### Indexação lenta

Para documentos grandes, a indexação pode levar tempo. Com Contextual Retrieval ativado:
- ~5-10 documentos: 2-5 minutos
- ~20-50 documentos: 10-30 minutos

Use `ENABLE_CONTEXTUAL_RETRIEVAL=false` para indexação mais rápida (mas menos precisa).

---

## 📚 Próximos Passos

1. **Leia a documentação completa**: `docs/ARCHITECTURE.md`
2. **Explore a API Reference**: `docs/API_REFERENCE.md`
3. **Teste diferentes queries**: Veja exemplos em `tests/integration/test_queries.json`
4. **Ajuste configurações**: Experimente diferentes valores no `.env`
5. **Adicione mais documentos**: Coloque mais PDFs BSC em `data/bsc_literature/`

---

## 🆘 Suporte

- **Issues**: Abra uma issue no GitHub
- **Documentação**: Consulte `docs/`
- **Logs**: Verifique `logs/app.log` para mais detalhes

---

## 🎯 Métricas de Sucesso

Seu sistema está funcionando bem se:

✅ Latência P95 < 5 segundos
✅ Score do Judge > 0.7
✅ Múltiplas perspectivas ativadas em queries complexas
✅ Fontes relevantes recuperadas (>3 documentos relevantes)
✅ Respostas coerentes e completas

