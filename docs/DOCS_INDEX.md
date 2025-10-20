# 📇 ÍNDICE DE DOCUMENTAÇÃO - BSC RAG Project

**Versão:** 1.4  
**Última Atualização:** 2025-10-19  
**Total de Documentos:** 50 (44 docs/ + 4 rules/ + 2 tool docs) - +1 lesson + 1 tool session 20!

---

## 🎯 COMO USAR ESTE ÍNDICE

**3 formas de navegação rápida:**

1. **Por Tag (A-Z)** → Seção 1 - Ctrl+F tag específica (ex: "retrieval", "agents")
2. **Por Categoria** → Seção 2 - Explorar por tipo (Techniques, Patterns, History, Guides)
3. **Quick Search Matrix** → Seção 3 - Cenários comuns mapeados

**Quando usar:**
- ✅ Preciso encontrar documentação sobre [tópico específico]
- ✅ Onde está documentado [feature/técnica]?
- ✅ Quais docs existem sobre [categoria]?
- ✅ Como fazer [tarefa comum]?

---

## 📑 SEÇÃO 1: TAGS PRINCIPAIS (A-Z)

### A

**adaptive-reranking** (Docs: 2)
- `docs/techniques/ADAPTIVE_RERANKING.md` - Técnica completa (500+ linhas)
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-002

**agents** (Docs: 5)
- `docs/LANGGRAPH_WORKFLOW.md` - Workflow completo
- `docs/ARCHITECTURE.md` - Arquitetura geral
- `src/agents/*.py` - 7 arquivos (orchestrator, judge, 4 specialists)
- `src/prompts/specialist_prompts.py` - Prompts dos agents
- `src/prompts/orchestrator_prompt.py` - Prompt orquestrador

**api** (Docs: 2)
- `docs/API_REFERENCE.md` - Referência completa da API
- `src/rag/*.py` - 16 módulos RAG

**api-contracts** (Docs: 1)
- `docs/architecture/API_CONTRACTS.md` - Contratos API completos (8 agentes, 23 métodos, 7 schemas Pydantic)

**architecture** (Docs: 4)
- `docs/ARCHITECTURE.md` - Visão geral arquitetural
- `docs/LANGGRAPH_WORKFLOW.md` - Workflow LangGraph
- `docs/architecture/DATA_FLOW_DIAGRAMS.md` - 5 diagramas Mermaid (fluxos dados)
- `docs/architecture/API_CONTRACTS.md` - Contratos API 8 agentes (1200+ linhas)

**asyncio** (Docs: 3)
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - AsyncIO 3.34x speedup
- `.cursor/rules/rag-recipes.mdc` - RECIPE-002
- `src/agents/orchestrator.py` - Parallel retrieval

---

### B

**benchmark** (Docs: 4)
- `tests/benchmark_fase2a/` - Benchmark Fase 2A
- `tests/benchmark_queries.json` - Dataset 50 queries
- `tests/benchmark_query_decomposition.py` - Benchmark Query Decomp
- `docs/VECTOR_DB_COMPARISON.md` - Benchmark Qdrant vs Weaviate

**bsc** (Docs: ALL - 37)
- Todo o projeto é focado em Balanced Scorecard
- Ver categorias específicas abaixo

---

### C

**cache** (Docs: 3)
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - Cache 949x speedup
- `.cursor/rules/rag-recipes.mdc` - RECIPE-003
- `src/rag/embeddings.py` - Embedding cache

**chunking** (Docs: 3)
- `docs/GPT5_CONTEXTUAL_RETRIEVAL.md` - Contextual chunking
- `src/rag/chunker.py` - TableAwareChunker
- `src/rag/contextual_chunker.py` - ContextualChunker

**cohere** (Docs: 3)
- `docs/TUTORIAL.md` - Setup Cohere
- `src/rag/reranker.py` - CohereReranker
- `.cursor/rules/rag-recipes.mdc` - RECIPE-001

**contextual-retrieval** (Docs: 3)
- `docs/GPT5_CONTEXTUAL_RETRIEVAL.md` - Técnica completa
- `docs/history/IMPLEMENTATION_GPT5_CONTEXTUAL.md` - Implementação
- `src/rag/contextual_chunker.py` - Código

**crag** (Docs: 2)
- `docs/techniques/FASE_2B_OVERVIEW.md` - Planejamento
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-005

---

### D

**deployment** (Docs: 2)
- `docs/DEPLOYMENT.md` - Guia de deploy
- `docker-compose.yml` - Configuração Docker

**diagrams** (Docs: 1)
- `docs/architecture/DATA_FLOW_DIAGRAMS.md` - 5 diagramas Mermaid (ClientProfile Lifecycle, Diagnostic Workflow, Schema Dependencies, Agent Interactions, State Transitions)

**diversity** (Docs: 2)
- `docs/techniques/ADAPTIVE_RERANKING.md` - MMR algorithm
- `src/rag/reranker.py` - rerank_with_diversity()

**docker** (Docs: 2)
- `docker-compose.yml` - Qdrant + Weaviate
- `docs/DEPLOYMENT.md` - Setup Docker

---

### E

**e2e-tests** (Docs: 4)
- `tests/integration/test_e2e.py` - Suite completa (22 testes)
- `docs/history/E2E_TESTS_IMPLEMENTATION_SUMMARY.md` - Implementação
- `docs/history/E2E_VALIDATION_FASE_2A_COMPLETA.md` - Validação
- `docs/lessons/lesson-e2e-validation-corrections-2025-10-14.md` - Correções

**embeddings** (Docs: 4)
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - Cache 949x
- `src/rag/embeddings.py` - EmbeddingManager
- `.cursor/rules/rag-recipes.mdc` - RECIPE-003
- `docs/TUTORIAL.md` - Configuração

---

### F

**filters** (Docs: 2)
- `src/rag/retriever.py` - Filtros de metadados
- `src/rag/qdrant_vector_store.py` - Filtros Qdrant

---

### G

**graph-rag** (Docs: 2)
- `docs/techniques/FASE_2B_OVERVIEW.md` - Avaliação futura
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-007 (condicional)

**gpt5** (Docs: 2)
- `docs/GPT5_CONTEXTUAL_RETRIEVAL.md` - Contextual Retrieval
- `docs/history/IMPLEMENTATION_GPT5_CONTEXTUAL.md` - Implementação

---

### H

**history** (Docs: 14)
- `docs/history/MVP_100_COMPLETO.md` - MVP completo
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - Otimizações massivas
- `docs/history/E2E_VALIDATION_FASE_2A_COMPLETA.md` - E2E Fase 2A
- `docs/history/LANGGRAPH_IMPLEMENTATION_SUMMARY.md` - LangGraph
- `docs/history/PRE_COMMIT_IMPLEMENTATION.md` - Pre-commit
- `docs/history/STREAMLIT_IMPLEMENTATION.md` - Streamlit
- `docs/history/IMPLEMENTATION_GPT5_CONTEXTUAL.md` - Contextual
- `docs/history/IMPLEMENTATION_SUMMARY.md` - Resumo geral
- `docs/history/PROGRESS.md` - Progresso histórico
- `docs/history/SETUP.md` - Setup inicial
- `docs/history/INSTALACAO_SUCESSO.md` - Instalação
- `docs/history/PROXIMAS_ETAPAS_E2E.md` - Próximas etapas
- `docs/history/E2E_TESTS_IMPLEMENTATION_SUMMARY.md` - E2E tests
- `docs/history/DOCUMENTACAO_FINAL_MVP_SUMMARY.md` - Docs MVP
- `docs/history/LIMPEZA_PROJETO_2025-10-14.md` - Limpeza

**hybrid-search** (Docs: 4)
- `docs/TUTORIAL.md` - Hybrid search setup
- `.cursor/rules/rag-recipes.mdc` - RECIPE-001
- `src/rag/hybrid_search.py` - Implementação
- `src/rag/retriever.py` - BSCRetriever com hybrid

**hyde** (Docs: 1)
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-006 (condicional)

---

### J

**judge-agent** (Docs: 4)
- `docs/LANGGRAPH_WORKFLOW.md` - Judge no workflow
- `src/agents/judge_agent.py` - Implementação
- `src/prompts/judge_prompt.py` - Prompt
- `docs/ARCHITECTURE.md` - Arquitetura

---

### L

**langgraph** (Docs: 4)
- `docs/LANGGRAPH_WORKFLOW.md` - Guia completo
- `docs/history/LANGGRAPH_IMPLEMENTATION_SUMMARY.md` - Implementação
- `src/graph/workflow.py` - Código
- `src/graph/states.py` - Estados

**lessons** (Docs: 9 - Todas criadas!)
- `docs/lessons/lesson-e2e-validation-corrections-2025-10-14.md` - E2E corrections (validado)
- `docs/lessons/lesson-query-decomposition-2025-10-14.md` - Query Decomp (545 linhas, GPT-5 mini)
- `docs/lessons/lesson-adaptive-reranking-2025-10-14.md` - Adaptive Re-ranking (626 linhas, TDD)
- `docs/lessons/lesson-router-2025-10-14.md` - Router Inteligente (786 linhas, 10x speedup)
- `docs/lessons/antipadrões-rag.md` - 32 antipadrões catalogados (903 linhas)
- `docs/lessons/lesson-memory-hierarchy-2025-10-14.md` - Hierarquia Mem0 (700+ linhas)
- `docs/lessons/lesson-test-debugging-methodology-2025-10-15.md` - Test Debug (FASE 2.4, 5 erros)
- `docs/lessons/lesson-diagnostic-agent-test-methodology-2025-10-16.md` - Test Methodology (FASE 2.5, 7 erros, 1.100+ linhas)
- `docs/lessons/lesson-onboarding-state-e2e-tests-2025-10-16.md` - E2E Workflow Tests (FASE 2.6, 4 problemas, 11.900+ linhas, checklist 12 pontos)
- `docs/lessons/lesson-swot-testing-methodology-2025-10-19.md` - Implementation-First Testing (FASE 3.1, APIs desconhecidas, 700+ linhas, 30-40 min economizados)
- `docs/lessons/lesson-kpi-testing-5whys-methodology-2025-10-19.md` - 5 Whys Root Cause Debugging (FASE 3.4, mock múltiplas chamadas, itertools.cycle, 950+ linhas, 15-20 min economizados)

---

### M

**mermaid** (Docs: 1)
- `docs/architecture/DATA_FLOW_DIAGRAMS.md` - 5 diagramas Mermaid v11.1.0+ (sequenceDiagram, flowchart TD, classDiagram, stateDiagram-v2)

**metadata** (Docs: 3)
- `data/README.md` - Metadados index.json + auto-geração
- `data/bsc_literature/index.json` - Metadados 5 livros BSC
- `scripts/build_knowledge_base.py` - Auto-geração LLM

**multilingual** (Docs: 3)
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - RRF +106% recall
- `src/rag/query_translator.py` - Tradutor PT-EN
- `src/rag/retriever.py` - Busca multilíngue

**mvp** (Docs: 6)
- `docs/history/MVP_100_COMPLETO.md` - MVP completo
- `docs/history/DOCUMENTACAO_FINAL_MVP_SUMMARY.md` - Docs finais
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - Otimizações
- `.cursor/rules/rag-bsc-core.mdc` - Lições MVP
- `README.md` - Overview MVP
- `docs/TUTORIAL.md` - Tutorial MVP

---

### O

**orchestrator** (Docs: 4)
- `src/agents/orchestrator.py` - BSCOrchestrator
- `src/prompts/orchestrator_prompt.py` - Prompt
- `docs/LANGGRAPH_WORKFLOW.md` - Workflow
- `docs/ARCHITECTURE.md` - Arquitetura

**optimization** (Docs: 3)
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - AsyncIO + Cache + RRF
- `.cursor/rules/rag-recipes.mdc` - Recipes validados
- `.cursor/rules/rag-bsc-core.mdc` - Lições MVP

**organization** (Docs: 3)
- `.cursor/rules/rag-bsc-core.mdc` - Router central (TIER 1)
- `.cursor/rules/rag-techniques-catalog.mdc` - Catalog (TIER 2)
- `.cursor/rules/rag-recipes.mdc` - Recipes (TIER 2)
- [TIER 3] `docs/DOCS_INDEX.md` (este arquivo!)
- [TIER 3] `docs/lessons/` (a criar)

---

### P

**patterns** (Docs: 1 + 3 planejados)
- `docs/patterns/EXEMPLO_USO_ROUTER.md` - Exemplo router
- [Futuro] `HYBRID_SEARCH.md` - Pattern MVP
- [Futuro] `COHERE_RERANK.md` - Pattern MVP
- [Futuro] `ASYNCIO_PARALLEL.md` - Pattern MVP

**perspectives** (Docs: 5)
- `src/agents/financial_agent.py` - Perspectiva Financeira
- `src/agents/customer_agent.py` - Perspectiva Clientes
- `src/agents/process_agent.py` - Perspectiva Processos
- `src/agents/learning_agent.py` - Perspectiva Aprendizado
- `src/prompts/specialist_prompts.py` - Prompts especializados

**pre-commit** (Docs: 2)
- `docs/PRE_COMMIT_SETUP.md` - Setup hooks
- `docs/history/PRE_COMMIT_IMPLEMENTATION.md` - Implementação

---

### Q

**qdrant** (Docs: 4)
- `docs/VECTOR_DB_COMPARISON.md` - Qdrant vs Weaviate
- `docs/VECTOR_STORE_MIGRATION_GUIDE.md` - Migração
- `src/rag/qdrant_vector_store.py` - Implementação
- `docker-compose.yml` - Setup Docker

**query-decomposition** (Docs: 4)
- `docs/techniques/QUERY_DECOMPOSITION.md` - Técnica completa (400+ linhas)
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-001
- `src/rag/query_decomposer.py` - Implementação (270 linhas)
- `tests/test_query_decomposer.py` - Testes (20 tests, 91% coverage)

**query-router** (Docs: 3)
- `docs/techniques/ROUTER.md` - Técnica completa (650+ linhas)
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-003
- `src/rag/query_router.py` - Implementação (570 linhas)
- `src/rag/strategies.py` - 4 estratégias (420 linhas)
- `tests/test_query_router.py` - Testes (15 tests, 92% accuracy)

**quickstart** (Docs: 2)
- `docs/QUICKSTART.md` - Início rápido
- `README.md` - Overview geral

---

### R

**rag-advanced** (Docs: 6 - Técnicas Fase 2)
- `docs/techniques/QUERY_DECOMPOSITION.md` - TECH-001 ✅
- `docs/techniques/ADAPTIVE_RERANKING.md` - TECH-002 ✅
- `docs/techniques/ROUTER.md` - TECH-003 ✅
- `docs/techniques/FASE_2B_OVERVIEW.md` - Self-RAG + CRAG (planejado)
- `.cursor/rules/rag-techniques-catalog.mdc` - Catálogo completo
- `.cursor/rules/rag-recipes.mdc` - Recipes validados

**recipes** (Docs: 1)
- `.cursor/rules/rag-recipes.mdc` - 3 recipes validados
  - RECIPE-001: Hybrid Search + Re-ranking
  - RECIPE-002: AsyncIO Parallel Retrieval  
  - RECIPE-003: Embedding Cache

**reranking** (Docs: 4)
- `docs/techniques/ADAPTIVE_RERANKING.md` - Técnica completa
- `.cursor/rules/rag-recipes.mdc` - RECIPE-001
- `src/rag/reranker.py` - CohereReranker (638 linhas)
- `tests/test_adaptive_reranking.py` - Testes (38 tests, 100% coverage)

**retrieval** (Docs: 6)
- `docs/TUTORIAL.md` - Tutorial retrieval
- `docs/GPT5_CONTEXTUAL_RETRIEVAL.md` - Contextual Retrieval
- `src/rag/retriever.py` - BSCRetriever (570+ linhas)
- `src/rag/hybrid_search.py` - Hybrid search
- `tests/test_retriever.py` - Testes
- `.cursor/rules/rag-recipes.mdc` - RECIPE-001

**router** (Docs: 5)
- `docs/techniques/ROUTER.md` - Técnica completa (650+ linhas)
- `docs/patterns/EXEMPLO_USO_ROUTER.md` - Exemplo uso
- `.cursor/rules/rag-bsc-core.mdc` - Router central
- `src/rag/query_router.py` - Implementação
- `src/rag/strategies.py` - Estratégias

**rules** (Docs: 4 - Cursor Rules)
- `.cursor/rules/rag-bsc-core.mdc` - Router central (always-applied)
- `.cursor/rules/rag-techniques-catalog.mdc` - Catálogo (1.200+ linhas)
- `.cursor/rules/rag-recipes.mdc` - Recipes (800+ linhas)
- `.cursor/rules/derived-cursor-rules.mdc` - Rules derivadas

**rrf** (Docs: 3)
- `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` - RRF +106% recall
- `src/rag/retriever.py` - Reciprocal Rank Fusion
- `docs/techniques/QUERY_DECOMPOSITION.md` - RRF em decomposição

---

### S

**self-rag** (Docs: 2)
- `docs/techniques/FASE_2B_OVERVIEW.md` - Planejamento completo
- `.cursor/rules/rag-techniques-catalog.mdc` - TECH-004

**setup** (Docs: 5)
- `docs/QUICKSTART.md` - Início rápido
- `docs/history/SETUP.md` - Setup inicial
- `docs/history/INSTALACAO_SUCESSO.md` - Instalação validada
- `docs/DEPLOYMENT.md` - Deploy
- `docs/PRE_COMMIT_SETUP.md` - Pre-commit hooks

**streamlit** (Docs: 3)
- `docs/STREAMLIT_GUIDE.md` - Guia interface
- `docs/history/STREAMLIT_IMPLEMENTATION.md` - Implementação
- `app/` - Código Streamlit (main.py, components/, utils.py)

**strategies** (Docs: 3)
- `docs/techniques/ROUTER.md` - 4 estratégias detalhadas
- `src/rag/strategies.py` - Implementação (420 linhas)
- `tests/test_strategies.py` - Testes (10 tests, 95% coverage)

---

### T

**techniques** (Docs: 3 implementados + 1 planejado)
- `docs/techniques/QUERY_DECOMPOSITION.md` - TECH-001 ✅
- `docs/techniques/ADAPTIVE_RERANKING.md` - TECH-002 ✅
- `docs/techniques/ROUTER.md` - TECH-003 ✅
- `docs/techniques/FASE_2B_OVERVIEW.md` - Self-RAG + CRAG (planejado)

**testing** (Docs: 3)
- `docs/TESTING_GUIDE.md` - Guia completo de testes
- `tests/` - 19 arquivos de teste
- `docs/history/E2E_TESTS_IMPLEMENTATION_SUMMARY.md` - E2E

**tutorial** (Docs: 2)
- `docs/TUTORIAL.md` - Tutorial completo MVP
- `docs/QUICKSTART.md` - Início rápido

---

### V

**vector-store** (Docs: 5)
- `docs/VECTOR_DB_COMPARISON.md` - Benchmark Qdrant vs Weaviate
- `docs/VECTOR_STORE_MIGRATION_GUIDE.md` - Guia migração
- `src/rag/qdrant_vector_store.py` - Qdrant
- `src/rag/weaviate_vector_store.py` - Weaviate
- `src/rag/redis_vector_store.py` - Redis

---

### W

**workflow** (Docs: 4)
- `docs/LANGGRAPH_WORKFLOW.md` - Guia completo
- `src/graph/workflow.py` - Implementação
- `src/graph/states.py` - Estados LangGraph
- `docs/ARCHITECTURE.md` - Arquitetura

---

## 📂 SEÇÃO 2: DOCS POR CATEGORIA

### 🔧 Techniques - RAG Avançado (3 implementados + 2 planejados)

| Técnica | Doc | Código | Testes | Status |
|---------|-----|--------|--------|--------|
| **Query Decomposition** | `techniques/QUERY_DECOMPOSITION.md` | `src/rag/query_decomposer.py` | `tests/test_query_decomposer.py` | ✅ 100% |
| **Adaptive Re-ranking** | `techniques/ADAPTIVE_RERANKING.md` | `src/rag/reranker.py` | `tests/test_adaptive_reranking.py` | ✅ 100% |
| **Router Inteligente** | `techniques/ROUTER.md` | `src/rag/query_router.py` + `strategies.py` | `tests/test_query_router.py` | ✅ 100% |
| **Self-RAG** | `techniques/FASE_2B_OVERVIEW.md` | [Fase 2B] | [Fase 2B] | 📋 Planejado |
| **CRAG** | `techniques/FASE_2B_OVERVIEW.md` | [Fase 2B] | [Fase 2B] | 📋 Planejado |

---

### 📊 Patterns - Configurações Validadas (1 + 3 planejados)

| Pattern | Doc | Status |
|---------|-----|--------|
| **Exemplo Uso Router** | `patterns/EXEMPLO_USO_ROUTER.md` | ✅ Criado |
| **Hybrid Search** | [Futuro] `patterns/HYBRID_SEARCH.md` | 📋 Planejado |
| **Cohere Re-ranking** | [Futuro] `patterns/COHERE_RERANK.md` | 📋 Planejado |
| **AsyncIO Parallel** | [Futuro] `patterns/ASYNCIO_PARALLEL.md` | 📋 Planejado |

---

### 📚 Lessons - Lições Aprendidas (9 completas)

| Lição | Técnica | ROI Observado | Status |
|-------|---------|---------------|--------|
| **E2E Validation Corrections** | `lessons/lesson-e2e-validation-corrections-2025-10-14.md` | 3 correções críticas | ✅ |
| **Query Decomposition** | `lessons/lesson-query-decomposition-2025-10-14.md` (545L) | $9.90/dia, heurística 100%, 91% coverage | ✅ |
| **Adaptive Re-ranking** | `lessons/lesson-adaptive-reranking-2025-10-14.md` (626L) | TDD -93% bugs, 100% coverage, MMR validado | ✅ |
| **Router Inteligente** | `lessons/lesson-router-2025-10-14.md` (786L) | 10x speedup, 92% accuracy, 70% reuso | ✅ |
| **Antipadrões RAG** | `lessons/antipadrões-rag.md` (903L) | 32 antipadrões, 2-8h economizadas/antipadrão | ✅ |
| **Memory Hierarchy** | `lessons/lesson-memory-hierarchy-2025-10-14.md` (700+L) | Hierarquia Mem0, persistência, factory pattern | ✅ |
| **Test Debugging (FASE 2.4)** | `lessons/lesson-test-debugging-methodology-2025-10-15.md` | 5 erros, 40 min, ClientProfileAgent | ✅ |
| **Test Methodology (FASE 2.5)** | `lessons/lesson-diagnostic-agent-test-methodology-2025-10-16.md` (1.100+L) | 7 erros, 38 min economizados, checklist 8 pontos | ✅ |
| **E2E Workflow Tests (FASE 2.6)** | `lessons/lesson-onboarding-state-e2e-tests-2025-10-16.md` (11.900+L) | 32-60 min economizados, checklist 12 pontos, in-memory sessions | ✅ |
| **SWOT Testing Methodology (FASE 3.1)** | `lessons/lesson-swot-testing-methodology-2025-10-19.md` (700+L) | Implementation-First Testing, APIs desconhecidas, 30-40 min economizados, checklist ponto 13 | ✅ |
| **KPI Testing 5 Whys Debugging (FASE 3.4)** | `lessons/lesson-kpi-testing-5whys-methodology-2025-10-19.md` (950+L) | 5 Whys meta-análise, mock múltiplas chamadas, itertools.cycle, 15-20 min economizados, checklist ponto 14 | ✅ |

---

### 📖 Guides - Guias de Uso (7)

| Guia | Audiência | Páginas |
|------|-----------|---------|
| `QUICKSTART.md` | Novos usuários | ~10 |
| `TUTORIAL.md` | Desenvolvedores | ~50 |
| `ARCHITECTURE.md` | Arquitetos | ~30 |
| `API_REFERENCE.md` | Desenvolvedores | ~40 |
| `TESTING_GUIDE.md` | QA/Dev | ~25 |
| `DEPLOYMENT.md` | DevOps | ~20 |
| `STREAMLIT_GUIDE.md` | Usuários finais | ~15 |

---

### 🏛️ History - Progresso Histórico (14)

| Documento | Fase | Data Estimada |
|-----------|------|---------------|
| `SETUP.md` | Setup Inicial | 2025-10-10 |
| `INSTALACAO_SUCESSO.md` | Setup | 2025-10-10 |
| `PROGRESS.md` | Progresso Geral | 2025-10-11 |
| `IMPLEMENTATION_SUMMARY.md` | MVP Core | 2025-10-11 |
| `STREAMLIT_IMPLEMENTATION.md` | MVP UI | 2025-10-12 |
| `LANGGRAPH_IMPLEMENTATION_SUMMARY.md` | MVP Workflow | 2025-10-12 |
| `PRE_COMMIT_IMPLEMENTATION.md` | MVP DevOps | 2025-10-13 |
| `IMPLEMENTATION_GPT5_CONTEXTUAL.md` | MVP Contextual | 2025-10-13 |
| `MULTILINGUAL_OPTIMIZATION_SUMMARY.md` | MVP Otimização | 2025-10-14 |
| `E2E_TESTS_IMPLEMENTATION_SUMMARY.md` | MVP Tests | 2025-10-14 |
| `DOCUMENTACAO_FINAL_MVP_SUMMARY.md` | MVP Docs | 2025-10-14 |
| `MVP_100_COMPLETO.md` | MVP Completo | 2025-10-14 |
| `LIMPEZA_PROJETO_2025-10-14.md` | Limpeza | 2025-10-14 |
| `E2E_VALIDATION_FASE_2A_COMPLETA.md` | Fase 2A E2E | 2025-10-14 |

---

### 🎯 Cursor Rules - Organização AI (4)

| Rule | Tipo | Linhas | Descrição |
|------|------|--------|-----------|
| `rag-bsc-core.mdc` | Always Applied | 850+ | Router central + Workflow 7 steps + Lições MVP |
| `rag-techniques-catalog.mdc` | Agent Requested | 1.200+ | Catálogo 5 técnicas RAG (3 implementadas + 2 planejadas) |
| `rag-recipes.mdc` | Agent Requested | 800+ | 3 recipes validados (Hybrid, AsyncIO, Cache) |
| `derived-cursor-rules.mdc` | Agent Requested | 500+ | Rules derivadas SpecStory |

---

## 🎯 SEÇÃO 3: QUICK SEARCH MATRIX

**Cenários comuns → documentação direta**

| Preciso de... | Tags | Documentos Principais | Arquivos Código |
|---------------|------|----------------------|-----------------|
| **Implementar técnica RAG nova** | rag-advanced, techniques | `.cursor/rules/rag-bsc-core.mdc` (Workflow 7 steps) | - |
| **Descobrir qual técnica usar** | techniques, catalog | `.cursor/rules/rag-techniques-catalog.mdc` | - |
| **Usar padrão rápido (recipe)** | recipes, patterns | `.cursor/rules/rag-recipes.mdc` | - |
| **Configurar hybrid search** | hybrid-search, retrieval | `TUTORIAL.md`, `rag-recipes.mdc#RECIPE-001` | `src/rag/retriever.py` |
| **Otimizar latência** | optimization, asyncio | `MULTILINGUAL_OPTIMIZATION_SUMMARY.md` | `src/agents/orchestrator.py` |
| **Reduzir alucinações** | self-rag, hallucination | `FASE_2B_OVERVIEW.md` → Self-RAG | [Fase 2B] |
| **Melhorar retrieval ruim** | crag, corrective | `FASE_2B_OVERVIEW.md` → CRAG | [Fase 2B] |
| **Query complexa multi-parte** | query-decomposition | `techniques/QUERY_DECOMPOSITION.md` | `src/rag/query_decomposer.py` |
| **Melhorar diversidade docs** | adaptive-reranking, diversity | `techniques/ADAPTIVE_RERANKING.md` | `src/rag/reranker.py` |
| **Otimizar estratégia por query** | query-router, strategies | `techniques/ROUTER.md` | `src/rag/query_router.py` |
| **Entender workflow LangGraph** | langgraph, workflow, agents | `LANGGRAPH_WORKFLOW.md` | `src/graph/workflow.py` |
| **Entender fluxos de dados** | diagrams, mermaid, architecture | `architecture/DATA_FLOW_DIAGRAMS.md` | - |
| **Chamar métodos de agentes** | api-contracts, agents, architecture | `architecture/API_CONTRACTS.md` | `src/agents/*.py` |
| **Setup inicial do projeto** | quickstart, setup | `QUICKSTART.md` | `setup.ps1` |
| **Configurar vector store** | qdrant, vector-store | `VECTOR_STORE_MIGRATION_GUIDE.md` | `src/rag/qdrant_vector_store.py` |
| **Criar testes E2E** | e2e-tests, testing | `TESTING_GUIDE.md`, `E2E_TESTS_IMPLEMENTATION_SUMMARY.md` | `tests/integration/test_e2e.py` |
| **Deploy em produção** | deployment, docker | `DEPLOYMENT.md` | `docker-compose.yml` |
| **Usar interface Streamlit** | streamlit, ui | `STREAMLIT_GUIDE.md` | `app/main.py` |
| **Adicionar metadados docs** | metadata, index-json | `data/README.md` (Auto-Geração seção) | `scripts/build_knowledge_base.py` |
| **Entender lições aprendidas** | lessons, antipadrões | `lessons/` directory | - |
| **Ver progresso histórico** | history, mvp | `history/MVP_100_COMPLETO.md` | - |
| **Benchmarkar técnicas RAG** | benchmark, metrics | `tests/benchmark_fase2a/` | `run_benchmark.py` |

---

## 📊 ESTATÍSTICAS DA DOCUMENTAÇÃO

### Por Categoria

| Categoria | Quantidade | % Total |
|-----------|-----------|---------|
| **History** | 14 docs | 38% |
| **Guides** | 7 docs | 19% |
| **Techniques** | 4 docs | 11% |
| **Rules** | 4 docs | 11% |
| **Tests/Benchmarks** | 4 docs | 11% |
| **Patterns** | 1 doc | 3% |
| **Lessons** | 8 docs (5.600+ linhas) | 22% |
| **Vector Stores** | 2 docs | 5% |

**Total:** 46 documentos

---

### Por Tamanho Estimado

| Tamanho | Docs | Exemplos |
|---------|------|----------|
| **Pequeno** (<100 linhas) | ~10 | QUICKSTART, patterns |
| **Médio** (100-300 linhas) | ~15 | TESTING_GUIDE, history docs |
| **Grande** (300-600 linhas) | ~8 | TUTORIAL, ARCHITECTURE, techniques |
| **Muito Grande** (600+ linhas) | ~4 | Rules, ROUTER.md |

---

### Top 10 Documentos Mais Importantes

| # | Documento | Categoria | Por Quê |
|---|-----------|-----------|---------|
| 1 | `.cursor/rules/rag-bsc-core.mdc` | Rules | Router central always-applied |
| 2 | `docs/TUTORIAL.md` | Guide | Tutorial completo MVP |
| 3 | `docs/techniques/ROUTER.md` | Technique | Técnica mais complexa (650+ linhas) |
| 4 | `docs/LANGGRAPH_WORKFLOW.md` | Guide | Workflow LangGraph |
| 5 | `docs/history/MULTILINGUAL_OPTIMIZATION_SUMMARY.md` | History | Otimizações massivas validadas |
| 6 | `.cursor/rules/rag-techniques-catalog.mdc` | Rules | Catálogo 5 técnicas |
| 7 | `docs/techniques/QUERY_DECOMPOSITION.md` | Technique | 1ª técnica Fase 2A |
| 8 | `docs/techniques/ADAPTIVE_RERANKING.md` | Technique | 2ª técnica Fase 2A |
| 9 | `docs/ARCHITECTURE.md` | Guide | Arquitetura geral |
| 10 | `docs/TESTING_GUIDE.md` | Guide | Guia de testes |

---

## 🔗 NAVEGAÇÃO RÁPIDA

### Para Novos Usuários:

1. **Início:** `README.md` → `docs/QUICKSTART.md`
2. **Tutorial:** `docs/TUTORIAL.md`
3. **Arquitetura:** `docs/ARCHITECTURE.md`

### Para Desenvolvedores:

1. **API:** `docs/API_REFERENCE.md`
2. **Testes:** `docs/TESTING_GUIDE.md`
3. **Deploy:** `docs/DEPLOYMENT.md`

### Para Implementar Técnicas RAG:

1. **Workflow:** `.cursor/rules/rag-bsc-core.mdc` (7 steps obrigatórios)
2. **Discovery:** `.cursor/rules/rag-techniques-catalog.mdc`
3. **Recipes:** `.cursor/rules/rag-recipes.mdc`
4. **Técnica Específica:** `docs/techniques/[TECHNIQUE].md`

---

## 📝 CHANGELOG

### v1.0 - 2025-10-14 (Versão Inicial)

**Criado:**
- ✅ Índice completo de 37 documentos
- ✅ 25+ tags navegáveis (A-Z)
- ✅ 5 categorias organizadas
- ✅ Quick Search Matrix com 20+ cenários
- ✅ Estatísticas da documentação
- ✅ Top 10 docs mais importantes
- ✅ Navegação rápida por audiência

**ROI Esperado:**
- 50-70% redução tempo de busca
- 3-8 min economizados por busca
- 10-25 usos estimados na Fase 2
- **Total:** 30-200 min economizados

---

### v1.2 - 2025-10-16 (Lições Aprendidas)

**Adicionado:**
- ✅ 9 lições completas em docs/lessons/
- ✅ Antipadrões RAG catalogados

---

### v1.3 - 2025-10-19 (Architecture Docs)

**Adicionado:**
- ✅ `docs/architecture/DATA_FLOW_DIAGRAMS.md` - 5 diagramas Mermaid
- ✅ `docs/architecture/API_CONTRACTS.md` - Contratos API 8 agentes
- ✅ 3 novas tags: diagrams, api-contracts, mermaid
- ✅ 2 novos cenários Quick Search Matrix
- ✅ Estatísticas atualizadas: 44→46 docs

**ROI:**
- ~1h economizada por task (consulta diagrams/contracts vs leitura código)

---

**Última Atualização:** 2025-10-19  
**Próximo:** FASE 3.1 SWOT Analysis Tool


