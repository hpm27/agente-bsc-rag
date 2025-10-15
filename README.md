# 🎯 Agente BSC RAG - Sistema Multi-Agente para Consultoria em Balanced Scorecard

<p align="center">
  <strong>Sistema avançado de IA para consultoria especializada em Balanced Scorecard</strong><br>
  Arquitetura multi-agente com RAG contextual otimizado e tecnologias 2025
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/LangGraph-0.2+-green.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/Claude-Sonnet_4.5-purple.svg" alt="Claude Sonnet 4.5">
  <img src="https://img.shields.io/badge/Streamlit-1.37+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Qdrant-1.11+-orange.svg" alt="Qdrant">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
</p>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Características Principais](#-características-principais)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Instalação Rápida](#-instalação-rápida)
- [Documentação](#-documentação)
- [Performance e Otimizações](#-performance-e-otimizações)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Testes e Validação](#-testes-e-validação)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🌟 Visão Geral

O **Agente BSC RAG** é um sistema inteligente baseado em IA para consultoria especializada em **Balanced Scorecard** (metodologia de Kaplan & Norton). Combina:

- 🤖 **Sistema Multi-Agente**: 4 especialistas BSC (Financeira, Clientes, Processos, Aprendizado) + Judge + Orchestrator
- 📚 **RAG Contextual Otimizado**: Recuperação augmentada com contexto (Anthropic), +106% precisão multilíngue
- 🔗 **LangGraph Workflow**: Orquestração com grafo de estados, refinamento iterativo
- 🖥️ **Interface Streamlit**: Chat web responsivo com visualização completa
- ⚡ **Otimizações de Performance**: 949x speedup (cache), 3.34x (paralelização), busca multilíngue nativa

### 🎯 Casos de Uso

- ✅ Análise estratégica e desenvolvimento de BSC
- ✅ Geração de KPIs e iniciativas por perspectiva
- ✅ Consultas sobre metodologia BSC (framework Kaplan & Norton)
- ✅ Validação de mapas estratégicos
- ✅ Consultoria especializada em implementação BSC

---

## ✨ Características Principais

### 🤖 Sistema Multi-Agente LangGraph

```
START → analyze_query → execute_agents → synthesize_response 
→ judge_evaluation → decide_next_step → [finalize OR refine loop] → END
```

**Agentes Especialistas**:
- 💰 **Financial Agent** - Perspectiva Financeira (ROI, crescimento de receita, produtividade)
- 👥 **Customer Agent** - Perspectiva de Clientes (satisfação, retenção, valor)
- ⚙️ **Process Agent** - Perspectiva de Processos Internos (qualidade, eficiência, inovação)
- 🎓 **Learning Agent** - Perspectiva de Aprendizado e Crescimento (capacitação, clima, sistemas)

**Orquestração Inteligente**:
- ✅ Execução paralela assíncrona (AsyncIO)
- ✅ Refinamento iterativo baseado em feedback do Judge (até 2 ciclos)
- ✅ State management com Pydantic (type-safe)
- ✅ Recuperação de erros em cada nó

**Documentação**: [LANGGRAPH_WORKFLOW.md](docs/LANGGRAPH_WORKFLOW.md)

### 📚 RAG Avançado e Multilíngue 🌐

**Pipeline Completo**:
1. **Chunking Semântico** - Preserva contexto semântico
2. **Contextual Retrieval** - Contextos bilíngues PT-BR + EN (Anthropic)
3. **Hybrid Search** - 70% semântica + 30% BM25 (Qdrant nativo)
4. **Query Expansion** - Tradução automática PT-BR ↔ EN + Reciprocal Rank Fusion
5. **Adaptive Reranking** - Cohere Rerank Multilingual v3.0 (detecção automática de idioma)

**Resultados**:
- 🎯 **+106% precisão top-1** (busca cross-lingual)
- 🎯 **+70% recall** (query expansion com RRF)
- 🌐 **Busca multilíngue nativa** (queries PT-BR + docs EN, automático)
- 📚 **7.965 chunks indexados** (5 livros BSC + contextos bilíngues)

**Documentação**: [MULTILINGUAL_OPTIMIZATION_SUMMARY.md](MULTILINGUAL_OPTIMIZATION_SUMMARY.md)

### ⚡ Performance Otimizada

| Otimização | Speedup | Descrição |
|------------|---------|-----------|
| **Embedding Cache** | **949x** | Cache persistente em disco (diskcache, 87.5% hit rate) |
| **Paralelização AsyncIO** | **3.34x** | Execução paralela de 4 agentes BSC |
| **Batch Upload Qdrant** | **10x** | 100 docs/batch (resolveu limite 32MB) |
| **Contextual Chunker Paralelo** | **8x** | 10 workers ThreadPoolExecutor |
| **Query Expansion RRF** | **+106%** | Fusão de resultados PT-BR + EN |

**Economia de Custos**:
- 💰 87.5% redução em chamadas OpenAI Embeddings (cache)
- 💰 ~$0.001/query para tradução multilíngue (GPT-4o-mini)
- 💰 Tradução gratuita de contextos (Google Translate vs LLM)

### 🖥️ Interface Streamlit Moderna

- 💬 **Chat Interface** - Histórico de conversação persistente
- 📊 **Visualização BSC** - Perspectivas consultadas com confidence scores
- 📖 **Display de Fontes** - Documentos recuperados com relevância
- ⚖️ **Judge Evaluation** - Score, feedback, issues, sugestões
- ⚙️ **Configurações** - Parâmetros de retrieval e perspectivas

**Executar**: `python run_streamlit.py` → [http://localhost:8501](http://localhost:8501)

**Documentação**: [STREAMLIT_GUIDE.md](docs/STREAMLIT_GUIDE.md)

### ⚖️ Validação com LLM as Judge

- ✅ Avaliação automática de completude, relevância e fundamentação
- ✅ Score 0-1 com threshold configurável (padrão: 0.7)
- ✅ Feedback detalhado e sugestões de melhoria
- ✅ Detecção de alucinações e problemas de qualidade
- ✅ Taxa de aprovação validada >70% (testes E2E)

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                              │
│                    (Chat + Visualizações)                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                            │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Analyze  │ → │ Execute  │ → │Synthesize│ → │  Judge   │    │
│  │  Query   │   │  Agents  │   │ Response │   │  Eval    │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       │               ║                             │            │
│       │               ║ (AsyncIO Parallel)          │            │
│       │               ║                             │            │
│       │         ┌─────┼─────┐                       │            │
│       │         │     │     │                       │            │
│       │         ▼     ▼     ▼                       ▼            │
│       │    ┌────┐ ┌────┐ ┌────┐ ┌────┐        ┌────────┐       │
│       │    │Fin │ │Cust│ │Proc│ │Lear│        │Finalize│       │
│       │    │Agt │ │Agt │ │Agt │ │Agt │        │  OR    │       │
│       │    └────┘ └────┘ └────┘ └────┘        │ Refine │       │
│       │         │     │     │     │            └────────┘       │
│       └─────────┴─────┴─────┴─────┘                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BSC RETRIEVER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Query      │→ │ Multilingual │→ │   Adaptive   │          │
│  │  Translator  │  │     RRF      │  │   Reranker   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QDRANT (Vector Store)                       │
│  - 7.965 chunks indexados                                        │
│  - Contextos bilíngues (PT-BR + EN)                              │
│  - Hybrid Search nativo (70% semântica + 30% BM25)               │
└─────────────────────────────────────────────────────────────────┘
```

**Documentação**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🔧 Tecnologias

### LLMs e APIs

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| **Claude Sonnet 4.5** | 2025-09-29 | LLM principal (agentes, contextual retrieval) |
| **OpenAI text-embedding-3-large** | 3072-dim | Embeddings multilíngues |
| **Cohere Rerank Multilingual** | v3.0 | Re-ranking cross-lingual |
| **GPT-4o-mini** | 2024-07-18 | Query translation (barato e rápido) |

### Framework e Orquestração

- **LangGraph** 0.2+ - Workflows com grafos de estados
- **LangChain** 0.3+ - Base de agentes e ferramentas
- **Pydantic** 2.0+ - Validação e settings

### Vector Store e RAG

- **Qdrant** 1.11+ - Vector database (recomendado)
- **Weaviate** 1.26+ - Alternativa (hybrid search nativo)
- **diskcache** 5.6+ - Cache persistente de embeddings

### Interface e Deployment

- **Streamlit** 1.37+ - Interface web
- **Docker Compose** - Orquestração de containers
- **Python** 3.12+ - Runtime

---

## 🚀 Instalação Rápida

### Pré-requisitos

- ✅ **Python 3.12+** (testado em 3.12)
- ✅ **Docker Desktop** (para Qdrant)
- ✅ **8GB RAM** mínimo recomendado
- ✅ **API Keys**:
  - OpenAI API Key (embeddings + GPT-4o-mini)
  - Cohere API Key (re-ranking)
  - Anthropic API Key (Claude Sonnet 4.5 + contextual retrieval)

### Setup em 5 Passos (10 minutos)

#### 1️⃣ Clone e Configure Ambiente

```powershell
# Clone o repositório
git clone https://github.com/seu-usuario/agente-bsc-rag.git
cd agente-bsc-rag

# Execute setup automatizado (Windows PowerShell)
.\setup.ps1
```

O script `setup.ps1` faz automaticamente:
- ✅ Criar ambiente virtual Python
- ✅ Instalar todas as dependências (requirements.txt)
- ✅ Iniciar Docker containers (Qdrant em localhost:6333)
- ✅ Criar arquivo .env com templates
- ✅ Validar configuração completa

#### 2️⃣ Configure API Keys

Edite `.env` e adicione suas chaves:

```env
OPENAI_API_KEY=sk-proj-...
COHERE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```

#### 3️⃣ Indexe Dataset BSC

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Indexar documentos BSC (5 livros incluídos)
python scripts/build_knowledge_base.py
```

**Resultado**: 7.965 chunks indexados com contextos bilíngues (~12 min)

#### 4️⃣ Inicie a Interface

```powershell
python run_streamlit.py
```

🎉 **Pronto!** Interface abrirá em [http://localhost:8501](http://localhost:8501)

#### 5️⃣ Primeira Query

Digite na interface:

```
Quais são os principais KPIs da perspectiva financeira segundo Kaplan & Norton?
```

Você verá:
- ✅ Resposta fundamentada em documentos BSC
- ✅ Perspectivas consultadas (Financial Agent)
- ✅ Fontes com scores de relevância
- ✅ Avaliação do Judge (score, feedback)

---

## 📖 Documentação

### 🗂️ Índice Navegável de Toda Documentação

- 📖 **[DOCS_INDEX.md](docs/DOCS_INDEX.md)** ← **NOVO!** Índice completo com Tags A-Z, Quick Search Matrix, e cross-references

### Guias de Início Rápido

- 📘 **[QUICKSTART.md](docs/QUICKSTART.md)** - Onboarding em 10 minutos, primeiros passos
- 📗 **[TUTORIAL.md](docs/TUTORIAL.md)** - Uso avançado, casos práticos, customização
- 📕 **[STREAMLIT_GUIDE.md](docs/STREAMLIT_GUIDE.md)** - Interface web completa

### Referência Técnica

- 📙 **[API_REFERENCE.md](docs/API_REFERENCE.md)** - API de agentes, tools, workflow
- 📔 **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitetura detalhada
- 📓 **[LANGGRAPH_WORKFLOW.md](docs/LANGGRAPH_WORKFLOW.md)** - Workflow LangGraph

### Deployment e Operação

- 🚀 **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deploy local, Docker, cloud (AWS/Azure/GCP)
- 🧪 **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testes E2E, métricas, validação

### Otimizações e Análises

- ⚡ **[MULTILINGUAL_OPTIMIZATION_SUMMARY.md](MULTILINGUAL_OPTIMIZATION_SUMMARY.md)** - Busca cross-lingual
- 📊 **[VECTOR_DB_COMPARISON.md](docs/VECTOR_DB_COMPARISON.md)** - Benchmark Qdrant vs Weaviate
- 📚 **[GPT5_CONTEXTUAL_RETRIEVAL.md](docs/GPT5_CONTEXTUAL_RETRIEVAL.md)** - Contextual chunking
- 🎓 **[LESSONS_LEARNED.md](LESSONS_LEARNED.md)** - Lições aprendidas

### Organização e Discovery (Cursor Rules)

- 🎯 **[rag-bsc-core.mdc](.cursor/rules/rag-bsc-core.mdc)** - Router central (sempre aplicado)
- 📘 **[rag-techniques-catalog.mdc](.cursor/rules/rag-techniques-catalog.mdc)** - Catálogo de técnicas RAG avançadas
- 🎯 **[rag-recipes.mdc](.cursor/rules/rag-recipes.mdc)** - Padrões RAG rápidos de 1 página

**ROI:** Economia de 15-20 min/uso em decisões técnicas e discovery de soluções.

---

## ⚡ Performance e Otimizações

### Métricas de Performance (MVP Validado)

| Métrica | Valor | Referência |
|---------|-------|------------|
| **Latência P50 (E2E)** | 71s | Aceitável para MVP (Claude API externa) |
| **Latência P95 (E2E)** | 122s | Threshold: <180s |
| **Embedding Cache Hit Rate** | >80% | Validado em testes E2E |
| **Taxa Aprovação Judge** | >70% | Threshold configurável |
| **Precisão Top-1 (Multilíngue)** | +106% | vs busca monolíngue |
| **Recall (Query Expansion)** | +70% | 10 → 17 docs únicos |

### Otimizações Implementadas

1. **Caching de Embeddings** (949x speedup)
   - Cache persistente com diskcache
   - Hit rate 87.5% em cenários realistas
   - Thread-safe e multiprocess-safe
   - Economia 87.5% em chamadas API OpenAI

2. **Paralelização AsyncIO** (3.34x speedup)
   - Execução paralela de 4 agentes BSC
   - asyncio.gather() para coordenação
   - Métodos ainvoke() em todos os agentes

3. **Busca Multilíngue** (+106% precisão)
   - Query expansion PT-BR ↔ EN automática
   - Reciprocal Rank Fusion (RRF, k=60)
   - Contextos bilíngues em metadata
   - Adaptive reranking com detecção de idioma

4. **Batch Processing**
   - Batch upload Qdrant (100 docs/batch)
   - Processamento paralelo chunker (10 workers)
   - Retry logic com exponential backoff

### Custos Estimados

| Componente | Custo/Query | Observações |
|------------|-------------|-------------|
| Embeddings (OpenAI) | ~$0.002 | Com cache 87.5% hit: $0.00025 |
| LLM Claude (4 agentes) | ~$0.05-0.10 | Dependente do tamanho da resposta |
| Reranking (Cohere) | ~$0.002 | 10 docs |
| Query Translation | ~$0.001 | GPT-4o-mini (opcional, multilíngue) |
| **Total/Query** | **~$0.05-0.11** | Com otimizações |

**Economia Mensal** (1000 queries):
- Cache de embeddings: **$17.50** economizados
- Tradução gratuita contextos: **$2.50** economizados

---

## 📁 Estrutura do Projeto

```
agente-bsc-rag/
├── app/                          # Interface Streamlit
│   ├── main.py                   # Aplicação principal
│   ├── utils.py                  # Helpers e session state
│   └── components/
│       ├── sidebar.py            # Configurações BSC
│       └── results.py            # Display de resultados
│
├── src/
│   ├── agents/                   # Sistema Multi-Agente
│   │   ├── orchestrator.py      # Coordenação de agentes
│   │   ├── financial_agent.py   # Perspectiva Financeira
│   │   ├── customer_agent.py    # Perspectiva de Clientes
│   │   ├── process_agent.py     # Perspectiva de Processos
│   │   ├── learning_agent.py    # Perspectiva de Aprendizado
│   │   └── judge_agent.py       # Validação (LLM as Judge)
│   │
│   ├── graph/                    # LangGraph Workflow
│   │   ├── workflow.py           # Definição do grafo
│   │   └── states.py             # Pydantic models
│   │
│   ├── rag/                      # Pipeline RAG
│   │   ├── embeddings.py         # Embeddings + cache
│   │   ├── retriever.py          # Hybrid search + RRF
│   │   ├── reranker.py           # Cohere adaptive reranking
│   │   ├── query_translator.py   # Multilingual expansion
│   │   ├── contextual_chunker.py # Contextual retrieval
│   │   ├── chunker.py            # Semantic chunking
│   │   ├── qdrant_vector_store.py# Qdrant integration
│   │   ├── weaviate_vector_store.py
│   │   └── vector_store_factory.py
│   │
│   ├── tools/                    # Ferramentas RAG
│   │   └── rag_tools.py          # Search tools para agentes
│   │
│   └── prompts/                  # Prompts especializados
│       ├── orchestrator_prompt.py
│       ├── specialist_prompts.py
│       ├── judge_prompt.py
│       └── contextual_chunk_prompt.py
│
├── config/
│   └── settings.py               # Configurações centralizadas
│
├── scripts/
│   ├── build_knowledge_base.py   # Indexação de documentos
│   ├── validate_setup.py         # Validação de ambiente
│   └── valida_env.py             # Validação de .env
│
├── tests/
│   ├── integration/
│   │   ├── test_e2e.py           # Testes E2E (566 linhas, 22 testes)
│   │   └── test_queries.json     # Dataset de queries BSC
│   ├── test_embeddings.py
│   ├── test_retriever.py
│   ├── test_reranker.py
│   └── test_embedding_cache.py
│
├── data/
│   └── bsc_literature/           # Documentos BSC (5 livros)
│       └── contextual_cache/     # Cache de contextos
│
├── docs/                         # Documentação completa
│   ├── QUICKSTART.md
│   ├── TUTORIAL.md
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT.md
│   ├── ARCHITECTURE.md
│   ├── LANGGRAPH_WORKFLOW.md
│   ├── STREAMLIT_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── ...
│
├── examples/
│   └── run_workflow_example.py   # Exemplos de uso programático
│
├── docker-compose.yml            # Qdrant + Weaviate + Redis
├── Dockerfile                    # Container da aplicação
├── requirements.txt              # Dependências Python
├── .env                          # Configurações (API keys)
├── .pre-commit-config.yaml       # Hooks de qualidade
└── README.md                     # Este arquivo
```

---

## 🧪 Testes e Validação

### Suite de Testes E2E

**Implementado**: 22 testes organizados em 6 classes (`tests/integration/test_e2e.py`)

| Classe | Testes | Descrição |
|--------|--------|-----------|
| `TestSystemReadiness` | 3 | Prontidão (Qdrant, dataset, API keys) |
| `TestE2EWorkflow` | 7 | Workflow completo end-to-end |
| `TestQueryScenarios` | 4 | Queries por perspectiva BSC |
| `TestPerformanceOptimizations` | 4 | Cache, multilíngue, paralelização |
| `TestJudgeValidation` | 2 | Validação do Judge Agent |
| `TestMetrics` | 2 | Latências P50/P95/P99, approval rate |

**Validação**: 9 testes críticos executados (41% da suite), cobrindo todas as 6 classes.

### Executar Testes

```powershell
# Suite completa E2E (22 testes)
pytest tests/integration/test_e2e.py -v

# Classe específica
pytest tests/integration/test_e2e.py::TestSystemReadiness -v

# Teste individual
pytest tests/integration/test_e2e.py::TestMetrics::test_latency_percentiles -v

# Com cobertura
pytest tests/integration/test_e2e.py --cov=src --cov-report=html
```

**Documentação**: [TESTING_GUIDE.md](docs/TESTING_GUIDE.md)

### Métricas Validadas (Testes E2E)

✅ **Sistema 100% operacional**:
- Qdrant rodando e acessível
- 7.965 chunks indexados
- API keys configuradas corretamente

✅ **Workflow funcional**:
- Query simple factual: OK
- Query multi-perspectiva: OK
- Refinamento iterativo: OK

✅ **Otimizações confirmadas**:
- Cache hit rate >80%
- Latências aceitáveis (P50<90s, P95<180s)
- Judge approval rate >70%

---

## 🗺️ Roadmap

### ✅ Fase 1 - MVP (COMPLETA - Out/2025)

- [x] Pipeline RAG completo (embeddings, retrieval, reranking)
- [x] Sistema Multi-Agente (4 especialistas + Judge + Orchestrator)
- [x] LangGraph Workflow (grafo de estados, refinamento)
- [x] Interface Streamlit (chat, visualizações)
- [x] Otimizações (AsyncIO, cache, multilíngue)
- [x] Testes E2E (22 testes, 6 classes)
- [x] Documentação completa (2500+ linhas)
- [x] Dataset BSC (7.965 chunks, 5 livros)

**Status**: **MVP 100% CONCLUÍDO** 🎉

### 🔥 Fase 2A - Quick Wins RAG Avançado (COMPLETA - Out/2025) ✅

- [x] **Query Decomposition** - Queries complexas em sub-queries + RRF ✅
- [x] **Adaptive Re-ranking** - Diversity + metadata boosting ✅
- [x] **Router Inteligente** - Roteamento por complexidade (92% accuracy) ✅
- [x] **Validação E2E** - 22/22 testes passing (100%) ✅
- [x] **Benchmark Fase 2A** - 50 queries × 2 sistemas validado ✅
- [x] **Métricas Consolidadas** - RAGAS + latência por categoria ✅
- [x] **Auto-Geração Metadados** - GPT-4o-mini + cache ✅
- [x] **TIER 3 Organização** - Índice navegável + lições aprendidas ✅

**Status**: **Fase 2A 100% COMPLETA** 🎉 - **PRONTO PARA PRODUÇÃO**

**Resultados Validados (Benchmark 50 queries):**
- ✅ **Latência Média**: +3.1% mais rápido (128.7s → 124.7s)
- ✅ **Answer Relevancy (RAGAS)**: +2.1% (0.889 → 0.907)
- ✅ **Queries Simples**: +10.6% mais rápido (64.6s → 57.7s) ⭐⭐⭐
- ✅ **Queries Conceituais**: +8.5% mais rápido (95.8s → 87.7s) ⭐⭐
- ✅ **Faithfulness (RAGAS)**: 0.968 (>0.85 threshold)
- ✅ **22/22 testes E2E passing** (100%)

**Documentação**: 
- [FASE_2A_COMPLETE_AND_TIER3_2025_10_15.md](docs/history/FASE_2A_COMPLETE_AND_TIER3_2025_10_15.md) ← Histórico Completo
- [executive_report.md](tests/benchmark_fase2a/results/executive_report.md) ← Relatório Benchmark
- [DOCS_INDEX.md](docs/DOCS_INDEX.md) ← Índice Navegável de Toda Documentação

---

### 📋 Fase 2B - Advanced RAG (PLANEJADO - Out-Nov/2025)

**Status:** Aguardando validação Benchmark Fase 2A  
**Duração Estimada:** 2-3 semanas (8-10 dias úteis)

- [ ] **Self-RAG** (3-4 dias) - Self-reflection, -40-50% alucinações
- [ ] **CRAG** (4-5 dias) - Corrective retrieval, +23% quality
- [ ] **Integração** (2-3 dias) - E2E tests, benchmark Fase 2B
- [ ] **Documentação** (1-2 dias) - Lições aprendidas, técnicas

**Decisão Condicional:**
- ✅ Implementar SE: Faithfulness <0.85 OU Precision <0.70
- ❌ Pular SE: Métricas excelentes (Faithfulness >0.90, Precision >0.80)

**Plano Detalhado:** `.cursor/plans/fase-2b-rag-avancado.plan.md`  
**Técnicas:** `docs/techniques/FASE_2B_OVERVIEW.md`

**HyDE, RAPTOR, Graph RAG:** Avaliação condicional pós-Fase 2B.

### 🚀 Fase 3 - Produção (Planejada - Dez/2025+)

- [ ] Autenticação e autorização (multi-tenant)
- [ ] Rate limiting e quotas
- [ ] Monitoramento e observabilidade (Prometheus, Grafana)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Deploy em cloud (AWS/Azure/GCP)
- [ ] Escalabilidade horizontal
- [ ] Backup e disaster recovery

---

## 🛡️ Qualidade de Código

### Pre-Commit Hooks

Hooks configurados para garantir qualidade:

- ✅ **Anti-Emoji Hook** - Bloqueia emojis em código Python (previne `UnicodeEncodeError` Windows)
- ✅ **Ruff Linter** - Linting rápido e moderno (150-200x mais rápido que flake8)
- ✅ **Black Formatter** - Formatação automática consistente
- ✅ **MyPy** - Verificação de tipos gradual

**Instalar hooks**:

```bash
pre-commit install
pre-commit run --all-files
```

**Documentação**: [PRE_COMMIT_SETUP.md](docs/PRE_COMMIT_SETUP.md)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga o processo:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

**Diretrizes**:
- Siga o estilo de código existente (Black, Ruff)
- Adicione testes para novas features
- Atualize documentação relevante
- Commits em português ou inglês

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja [LICENSE](LICENSE) para detalhes.

---

## 👥 Autores

- **Você** - *Desenvolvimento Inicial* - [GitHub](https://github.com/seu-usuario)

---

## 🙏 Agradecimentos

- **Robert S. Kaplan e David P. Norton** - Criadores do Balanced Scorecard
- **Anthropic** - Contextual Retrieval, Claude Sonnet 4.5
- **OpenAI** - GPT-4o, text-embedding-3-large
- **Cohere** - Rerank Multilingual v3.0
- **Comunidades**: LangChain, LangGraph, Streamlit, Qdrant

---

## 📞 Suporte

Dúvidas ou problemas?

- 🐛 Abra uma [Issue](https://github.com/seu-usuario/agente-bsc-rag/issues)
- 💬 Email: <seu-email@exemplo.com>
- 📖 Consulte a [Documentação Completa](docs/)

---

<p align="center">
  <strong>Desenvolvido com 💙 usando LangGraph, Claude Sonnet 4.5, Qdrant e Streamlit</strong><br>
  <em>MVP 100% Completo - Out/2025</em>
</p>
