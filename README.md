# 🎯 Agente de IA Consultor em Balanced Scorecard (BSC)

Sistema avançado de IA para consultoria especializada em implementação de Balanced Scorecard, utilizando arquitetura multi-agente com RAG otimizado.

## 🏗️ Arquitetura

```
LangGraph (Orquestração Multi-Agente)
  ├── Redis (Vector Store + Hybrid Search)
  ├── Fine-tuned Embeddings (Domínio BSC)
  ├── Re-ranking (Cohere Rerank)
  ├── LLM as Judge (Validação de Qualidade)
  └── GPT-4 (Geração de Respostas)
```

## ✨ Características

- **🎯 Multi-Agente:** Agentes especializados para cada perspectiva do BSC
- **📚 RAG Otimizado:** Retrieval de alta qualidade (>95% acurácia esperada)
- **🔍 Hybrid Search:** Busca semântica + palavras-chave (BM25)
- **🎓 Fine-tuned Embeddings:** Treinado com literatura especializada em BSC
- **📊 Re-ranking:** Reordenação inteligente dos resultados
- **✅ LLM as Judge:** Validação automática da qualidade das respostas
- **💾 Memória Persistente:** Contexto mantido entre sessões
- **🔄 Human-in-the-loop:** Aprovação para decisões críticas

## 📋 Pré-requisitos

- Python 3.11+
- Redis Stack (com RedisSearch e RedisJSON)
- Docker e Docker Compose (opcional, mas recomendado)
- Chaves de API:
  - OpenAI API Key (GPT-4)
  - Cohere API Key (Re-ranking)

## 🚀 Instalação Rápida

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/agente-bsc-rag.git
cd agente-bsc-rag
```

### 2. Configure o ambiente

```bash
# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas chaves de API
```

### 4. Inicie o Redis com Docker

```bash
docker-compose up -d
```

### 5. Prepare a base de conhecimento

```bash
# Adicione PDFs da literatura BSC em data/bsc_literature/
# Execute o script de indexação
python scripts/build_knowledge_base.py
```

### 6. (Opcional) Fine-tune dos embeddings

```bash
# Se você tiver dados de treinamento
python scripts/finetune_embeddings.py
```

### 7. Execute a aplicação

```bash
streamlit run app/main.py
```

Acesse: http://localhost:8501

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
- Email: seu-email@exemplo.com

---

**Desenvolvido com ❤️ usando LangGraph, Redis e GPT-4**
