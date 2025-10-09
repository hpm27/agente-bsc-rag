# 🎯 Agente de IA Consultor em Balanced Scorecard (BSC)

Sistema avançado de IA para consultoria especializada em implementação de Balanced Scorecard, utilizando arquitetura multi-agente com RAG otimizado e tecnologias de ponta 2025.

## 🏗️ Arquitetura MVP (Fase 1 - Completa)

```
LangGraph (Orquestração Multi-Agente)
  ├── Qdrant/Weaviate (Vector Store Moderno + Hybrid Search Nativo)
  ├── GPT-5 (Modelo LLM Estado da Arte - Ago/2025)
  ├── Claude Sonnet 4.5 (Contextual Retrieval - Set/2025)
  ├── OpenAI text-embedding-3-large (Embeddings 3072-dim)
  ├── Cohere Rerank v3.0 Multilingual (Re-ranking)
  ├── LLM as Judge (Validação de Qualidade)
  └── Streamlit (Interface Web Moderna)
```

## 🆕 Novidades 2025

- ✅ **GPT-5** - Lançado em 07/08/2025 (400K context, melhor raciocínio)
- ✅ **Claude Sonnet 4.5** - Lançado em 29/09/2025 (best-in-class para agentes)
- ✅ **Contextual Retrieval** - Técnica Anthropic que melhora precisão em 35-49%
- ✅ **Qdrant** - Vector DB moderno com hybrid search nativo
- ✅ **LangGraph** - Orquestração de workflows complexos com estados

## ✨ Características Principais

### 🤖 Sistema Multi-Agente

- **4 Agentes Especialistas BSC** (Financeira, Cliente, Processos, Aprendizado)
- **Orchestrator Inteligente** para roteamento de queries
- **Judge Agent** para validação de qualidade das respostas
- **LangGraph Workflow** com estados e ciclos de refinamento

### 📚 RAG Avançado

- **Contextual Retrieval** (Anthropic) - +35-49% precisão
- **Hybrid Search** - Semântica (70%) + BM25 (30%)
- **Cohere Rerank v3.0** - Re-ranking multilíngue de alta qualidade
- **Semantic Chunking** - Preserva contexto semântico
- **Table-Aware Chunking** - Mantém tabelas intactas

### 🔧 Tecnologias 2025

- **GPT-5** (400K tokens context) - Raciocínio superior
- **Claude Sonnet 4.5** - Best-in-class para agentes e código
- **text-embedding-3-large** (3072 dimensões) - Embeddings estado da arte
- **Qdrant/Weaviate** - Vector stores modernos
- **Streamlit** - Interface web responsiva e intuitiva

### 📊 Qualidade e Validação

- **LLM as Judge** - Validação automática de respostas
- **Refinement Loops** - Até 2 iterações para melhorar qualidade
- **Source Attribution** - Rastreabilidade completa
- **Confidence Scores** - Métricas de confiança por resposta
- **Multi-Perspective Coverage** - Respostas abrangentes

## 📋 Pré-requisitos

- **Python 3.9+** (Testado em 3.9, 3.10, 3.11)
- **Docker Desktop** (para Qdrant/Weaviate/Redis)
- **10GB RAM** (mínimo recomendado)
- **Chaves de API:**
  - ✅ **OpenAI API Key** (GPT-5 + Embeddings) - **OBRIGATÓRIO**
  - ✅ **Cohere API Key** (Re-ranking) - **OBRIGATÓRIO**
  - ⚠️ **Anthropic API Key** (Contextual Retrieval) - **OPCIONAL** (mas recomendado)

## 🚀 Instalação Rápida (5 minutos)

### Setup Automatizado (Windows PowerShell)

```powershell
# 1. Clone o repositório
git clone https://github.com/seu-usuario/agente-bsc-rag.git
cd agente-bsc-rag

# 2. Execute o setup automatizado
.\setup.ps1
```

O script `setup.ps1` fará **TUDO** automaticamente:

- ✅ Criar ambiente virtual Python
- ✅ Instalar todas as dependências
- ✅ Iniciar Docker containers (Qdrant, Weaviate, Redis)
- ✅ Criar arquivo `.env` com templates
- ✅ Validar configuração completa

### 3. Configure suas API Keys

Edite `.env` e adicione suas chaves:

```env
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...  # Opcional
```

### 4. Indexe Documentos BSC

```powershell
# Adicione PDFs/MD em data/bsc_literature/
# Depois execute:
.\venv\Scripts\Activate.ps1
python scripts/build_knowledge_base.py
```

### 5. Inicie a Interface Web

```powershell
streamlit run app/main.py
```

🎉 **Pronto!** Acesse: [http://localhost:8501](http://localhost:8501)

---

## 📖 Documentação Completa

- 📘 **[Guia Rápido](docs/QUICKSTART.md)** - Tutoriais e exemplos
- 📗 **[API Reference](docs/API_REFERENCE.md)** - Referência completa da API
- 📕 **[Arquitetura](docs/ARCHITECTURE.md)** - Detalhes da arquitetura
- 📙 **[Plano de Desenvolvimento](moderniza--o-rag-bsc.plan.md)** - Roadmap completo

## 📁 Estrutura do Projeto

```
agente-bsc-rag/
├── app/
│   └── main.py                 # Interface Streamlit
├── src/
│   ├── agents/
│   │   ├── orchestrator.py     # Agente orquestrador principal
│   │   ├── financial_agent.py  # Agente perspectiva financeira
│   │   ├── customer_agent.py   # Agente perspectiva do cliente
│   │   ├── process_agent.py    # Agente perspectiva de processos
│   │   ├── learning_agent.py   # Agente perspectiva de aprendizado
│   │   └── judge_agent.py      # Agente validador (LLM as Judge)
│   ├── rag/
│   │   ├── vector_store.py     # Gerenciamento do Redis
│   │   ├── embeddings.py       # Embeddings e fine-tuning
│   │   ├── retriever.py        # Retrieval com hybrid search
│   │   ├── reranker.py         # Re-ranking com Cohere
│   │   └── chunker.py          # Chunking semântico
│   ├── tools/
│   │   ├── strategy_analyzer.py    # Análise de estratégia
│   │   ├── kpi_generator.py        # Gerador de indicadores
│   │   ├── map_creator.py          # Criador de mapas estratégicos
│   │   └── bsc_validator.py        # Validador de BSC
│   ├── prompts/
│   │   ├── orchestrator_prompt.py
│   │   ├── specialist_prompts.py
│   │   └── judge_prompt.py
│   └── graph/
│       └── workflow.py         # Definição do grafo LangGraph
├── config/
│   ├── settings.py             # Configurações gerais
│   └── redis_config.py         # Configurações do Redis
├── data/
│   └── bsc_literature/         # PDFs da literatura BSC
├── tests/
│   ├── test_rag.py
│   ├── test_agents.py
│   └── test_tools.py
├── scripts/
│   ├── build_knowledge_base.py # Script para indexar documentos
│   ├── finetune_embeddings.py  # Script para fine-tuning
│   └── evaluate_rag.py         # Script para avaliar qualidade
├── docs/
│   ├── ARCHITECTURE.md         # Documentação da arquitetura
│   ├── RAG_OPTIMIZATION.md     # Guia de otimização do RAG
│   └── DEPLOYMENT.md           # Guia de deployment
├── docker-compose.yml          # Redis Stack
├── Dockerfile                  # Container da aplicação
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Configuração Avançada

### Redis

O Redis Stack é usado como vector store com suporte a:

- **RedisSearch:** Busca vetorial e full-text
- **RedisJSON:** Armazenamento de metadados

Configuração no `docker-compose.yml`:

```yaml
version: '3.8'
services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
      - "8001:8001"  # RedisInsight (UI)
    volumes:
      - redis-data:/data
```

### Hybrid Search

Combina busca vetorial (semântica) com BM25 (palavras-chave):

```python
# Peso para busca semântica: 0.7
# Peso para BM25: 0.3
results = retriever.hybrid_search(query, k=10, weights=(0.7, 0.3))
```

### Re-ranking

Usa Cohere Rerank para reordenar os top-K resultados:

```python
reranked = reranker.rerank(query, documents, top_n=5)
```

### Fine-tuning de Embeddings

Treine embeddings customizados com literatura BSC:

```bash
python scripts/finetune_embeddings.py \
  --base_model sentence-transformers/all-mpnet-base-v2 \
  --training_data data/training_pairs.json \
  --output_dir models/bsc-embeddings
```

## 📊 Avaliação de Qualidade

Execute testes de qualidade do RAG:

```bash
python scripts/evaluate_rag.py --test_set data/test_questions.json
```

Métricas avaliadas:

- **Precision@K:** Relevância dos top-K resultados
- **Recall@K:** Cobertura dos documentos relevantes
- **MRR (Mean Reciprocal Rank):** Posição do primeiro resultado relevante
- **NDCG (Normalized Discounted Cumulative Gain):** Qualidade do ranking
- **Faithfulness:** Fidelidade da resposta ao contexto (LLM as Judge)

## 🎯 Uso

### Interface de Chat

```python
# A interface Streamlit permite:
# 1. Fazer perguntas sobre BSC
# 2. Solicitar análise de estratégia
# 3. Gerar indicadores (KPIs)
# 4. Criar mapas estratégicos
# 5. Validar BSC completo
```

### API Programática

```python
from src.graph.workflow import create_bsc_agent

agent = create_bsc_agent()

response = agent.invoke({
    "messages": [("user", "Como definir objetivos para a perspectiva financeira?")]
})

print(response["messages"][-1])
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Testes específicos
pytest tests/test_rag.py -v
pytest tests/test_agents.py -v

# Com cobertura
pytest --cov=src tests/
```

## 📚 Documentação

- [Arquitetura Detalhada](docs/ARCHITECTURE.md)
- [Otimização do RAG](docs/RAG_OPTIMIZATION.md)
- [Guia de Deployment](docs/DEPLOYMENT.md)

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Seu Nome** - *Desenvolvimento Inicial*

## 🙏 Agradecimentos

- Robert S. Kaplan e David P. Norton - Criadores do Balanced Scorecard
- Comunidade LangChain e LangGraph
- Redis Labs pela excelente documentação

## 📞 Suporte

Para dúvidas ou suporte:

- Abra uma [Issue](https://github.com/seu-usuario/agente-bsc-rag/issues)
- Email: <seu-email@exemplo.com>

---

**Desenvolvido com ❤️ usando LangGraph, Redis e GPT-4**
