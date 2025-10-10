<!-- 2005d8aa-1b1e-4371-b931-540c026d8825 2956b390-5d29-4fa5-8a7d-98638a32730f -->
# Plano de Desenvolvimento - Agente BSC RAG 2025 (MVP-First)

## 🎯 Visão Geral

**IMPORTANTE**: Este projeto está em fase INICIAL (sem dados no database). O plano foi ajustado para abordagem **MVP-First**: criar sistema funcional end-to-end PRIMEIRO, validar com dados reais, DEPOIS adicionar features avançadas.

**Estratégia**:

- **FASE 1 (3-4 semanas)**: MVP completo funcional com arquitetura moderna
- **FASE 2 (4-6 semanas)**: Features avançadas baseadas em necessidade real validada

---

## ✅ JÁ IMPLEMENTADO

### 📅 Resumo de Progresso Recente (09/10/2025)

**Fase 0B - Setup de Ambiente**: COMPLETA ✅

- Ambiente Python configurado com todas as dependências
- Docker Compose rodando (Qdrant, Weaviate, Redis)
- Scripts de automação e validação criados
- Documentação completa de setup

**Fase 1A - Pipeline RAG**: COMPLETA ✅

- Embeddings OpenAI implementado
- Retriever com Hybrid Search funcional
- Re-ranker Cohere integrado
- Pipeline de ingestão completo

**Fase 1B - Sistema Multi-Agente**: COMPLETA ✅

- 4 Agentes Especialistas BSC implementados
- Judge Agent para validação de respostas
- Orchestrator para coordenação
- Ferramentas RAG integradas

**Próximo**: Fase 1C - LangGraph Workflow + Interface Streamlit

---

### 📅 Otimizações Implementadas (09/10/2025 - Tarde) ⚡

**Pipeline de Ingestão Otimizado**: COMPLETO ✅

**Contextual Retrieval com Processamento Paralelo**:

- ✅ ThreadPoolExecutor com 10 workers simultâneos (20% do limite Tier 4 Anthropic)
- ✅ Retry logic com exponential backoff para rate limits
- ✅ Progress logging thread-safe (logs a cada 10 chunks ou 5 segundos)
- ✅ Cache otimizado salvando 100% do tempo em re-execuções

**Batch Upload para Qdrant**:

- ✅ Sistema de batches (100 docs/batch) resolvendo limite de 32MB do Qdrant
- ✅ Progress tracking por batch com percentual
- ✅ 14 batches processados com sucesso (1332 documentos totais)

**Atualização para API Moderna do Qdrant**:

- ✅ Migração de `search()` (deprecado) para `query_points()` (API unificada 2025)
- ✅ Sem warnings de deprecation
- ✅ Código futureproof

**Métricas Alcançadas**:

- 📊 **1332 chunks** contextualizados e indexados do documento BSC
- ⚡ **0.4 segundos** para processar 1332 chunks (com cache ativo)
- 🎯 **Score de retrieval: 0.66-0.67** (boa relevância)
- 🚀 **Batch upload: 3.8 segundos** para 1332 documentos em 14 batches

**Arquivos Otimizados**:

- `src/rag/contextual_chunker.py` - Processamento paralelo + retry logic
- `scripts/build_knowledge_base.py` - Batch upload + progress tracking
- `src/rag/qdrant_vector_store.py` - API moderna query_points()

---

### 0.1 Vector Store Moderno ✅

- Interface `BaseVectorStore` abstrata
- `QdrantVectorStore` (recomendado 2025)
- `WeaviateVectorStore` (alternativa com hybrid search nativo)
- `RedisVectorStore` (legacy/compatibilidade)
- Factory pattern para fácil troca
- Docker configurado com Qdrant, Weaviate e Redis
- Benchmark script completo

### 0.2 Contextual Retrieval (Anthropic) ✅

- `ContextualChunker` com Claude 3.5 Sonnet
- Prompt Caching para reduzir custos
- Cache local de contextos
- Redução esperada: 35-49% em falhas de retrieval
- Prompts especializados para BSC

### 0.3 Chunking ✅

- `SemanticChunker` (respeita limites semânticos)
- `TableAwareChunker` (preserva tabelas intactas)
- Configuração flexível (chunk_size, overlap)

### 0.4 Setup de Ambiente ✅

- Ambiente virtual Python criado (`venv/`)
- Todas as dependências instaladas via `requirements.txt`
- Docker Compose configurado e containers iniciados:
- Qdrant (localhost:6333)
- Weaviate (localhost:8080)
- Redis (localhost:6379)
- Arquivo `.env` criado com templates de configuração
- Scripts de automação:
- `setup.ps1` - Setup automatizado completo
- `scripts/validate_setup.py` - Validação de ambiente
- Documentação de setup:
- `SETUP.md` - Guia passo a passo detalhado
- `PROGRESS.md` - Acompanhamento de progresso
- Estrutura de diretórios criada (data/, models/, logs/)
- Memória criada: Nunca usar emojis em código (ID: 9592459)

---

## FASE 1: MVP FUNCIONAL (3-4 semanas)

### 📦 FASE 1A - Pipeline RAG Completo (Semana 1)

#### 1.1 Implementar Embeddings ✅ CONCLUÍDO

**Objetivo**: Módulo de embeddings com OpenAI text-embedding-3-large

**Ações**:

- Criar `src/rag/embeddings.py`
- Implementar `EmbeddingGenerator` com OpenAI
- Suporte a batch processing para performance
- Cache opcional de embeddings
- Tratamento de rate limiting
- Integração com settings

**Arquivos**:

- `src/rag/embeddings.py` (novo)
- `tests/test_embeddings.py` (novo)

**Tempo estimado**: 1 dia

---

#### 1.2 Implementar Retriever com Hybrid Search ✅ CONCLUÍDO

**Objetivo**: Retriever que usa vector store com hybrid search (70% semântica + 30% BM25)

**Ações**:

- Criar `src/rag/retriever.py`
- Implementar `HybridRetriever`
- Integrar com vector store (via factory)
- Suporte a filtros de metadados
- Implementar RRF (Reciprocal Rank Fusion)
- Logging detalhado de retrieval
- Métricas de performance

**Arquivos**:

- `src/rag/retriever.py` (novo ou atualizar existente)
- `tests/test_retriever.py` (novo)

**Tempo estimado**: 2 dias

---

#### 1.3 Implementar Re-ranker ✅ CONCLUÍDO

**Objetivo**: Re-ranking com Cohere Rerank Multilingual v3.0

**Ações**:

- Criar/atualizar `src/rag/reranker.py`
- Implementar `CohereReranker`
- Fallback para scoring local se API falhar
- Integração com retriever
- Configuração de top_n
- Cache de re-rankings

**Arquivos**:

- `src/rag/reranker.py` (novo ou atualizar)
- `tests/test_reranker.py` (novo)

**Tempo estimado**: 1 dia

---

#### 1.4 Pipeline de Ingestão ✅ CONCLUÍDO + OTIMIZADO ⚡

**Objetivo**: Script para indexar documentos BSC no vector store

**Ações**:

- ✅ Criar/atualizar `scripts/build_knowledge_base.py`
- ✅ Integrar: Chunking → Contextual Retrieval → Embeddings → Vector Store
- ✅ Suporte a múltiplos formatos (PDF, DOCX, TXT, MD)
- ✅ Progress bar e logging detalhado
- ✅ Estatísticas de ingestão
- ✅ Configuração via CLI args

**Otimizações Implementadas (09/10/2025)**:

- ⚡ **Processamento Paralelo**: 10 workers simultâneos no Contextual Chunker (20% tier 4 Anthropic)
- ⚡ **Retry Logic**: Exponential backoff para rate limits da API Anthropic
- ⚡ **Progress Logging**: Thread-safe, logs a cada 10 chunks ou 5 segundos
- ⚡ **Batch Upload**: 100 documentos por batch para Qdrant (resolveu limite 32MB)
- ⚡ **Cache Otimizado**: Re-execuções processam 1332 chunks em 0.4s
- ⚡ **API Moderna**: Migração de `search()` para `query_points()`

**Métricas Alcançadas**:

- 📊 1332 chunks indexados do documento BSC principal
- ⚡ 0.4s para processar chunks com cache ativo
- 🎯 Score de retrieval: 0.66-0.67 (boa relevância)
- 🚀 3.8s para upload de 1332 docs em 14 batches

**Arquivos**:

- `scripts/build_knowledge_base.py` ✅ (otimizado)
- `src/rag/contextual_chunker.py` ✅ (processamento paralelo)
- `src/rag/qdrant_vector_store.py` ✅ (API moderna)

**Tempo estimado**: 2 dias (implementação) + 1 dia (otimizações)

---

### 🤖 FASE 1B - Sistema Multi-Agente (Semana 2-3)

#### 1.5 Ferramentas RAG para Agentes ✅ CONCLUÍDO

**Objetivo**: Ferramentas que agentes usarão para buscar informações

**Ações**:

- Criar `src/tools/rag_tools.py`
- Implementar `SearchTool` (busca híbrida)
- Implementar `DetailedSearchTool` (busca com contexto expandido)
- Implementar `FilteredSearchTool` (busca com filtros)
- Integração com Retriever + Re-ranker
- Formatação de resultados para agentes

**Arquivos**:

- `src/tools/__init__.py` (atualizar)
- `src/tools/rag_tools.py` (novo)
- `tests/test_rag_tools.py` (novo)

**Tempo estimado**: 1 dia

---

#### 1.6 Agentes Especialistas BSC (4 agentes) ✅ CONCLUÍDO

**Objetivo**: Criar os 4 agentes especialistas (Financeira, Clientes, Processos, Aprendizado)

**Ações**:

- Criar `src/agents/financial_agent.py` - Perspectiva Financeira
- Criar `src/agents/customer_agent.py` - Perspectiva de Clientes
- Criar `src/agents/process_agent.py` - Perspectiva de Processos Internos
- Criar `src/agents/learning_agent.py` - Perspectiva de Aprendizado e Crescimento
- Cada agente com:
- Prompt especializado (usar prompts já existentes)
- Acesso às ferramentas RAG
- Lógica de raciocínio específica da perspectiva
- Capacidade de pedir mais informações
- Integração com LangChain/LangGraph

**Arquivos**:

- `src/agents/financial_agent.py` (novo)
- `src/agents/customer_agent.py` (novo)
- `src/agents/process_agent.py` (novo)
- `src/agents/learning_agent.py` (novo)
- `src/agents/base_agent.py` (novo - classe base comum)
- `tests/test_agents.py` (novo)

**Tempo estimado**: 3 dias (1 agente por dia + base)

---

#### 1.7 Judge Agent (LLM as Judge) ✅ CONCLUÍDO

**Objetivo**: Agente que valida e julga respostas dos especialistas

**Ações**:

- Criar `src/agents/judge_agent.py`
- Implementar validação de:
- Completude da resposta
- Relevância para a query
- Coerência entre perspectivas
- Detecção de alucinações
- Usar prompt judge já existente
- Score de confiança (0-1)
- Sugestões de melhorias

**Arquivos**:

- `src/agents/judge_agent.py` (novo)
- `tests/test_judge_agent.py` (novo)

**Tempo estimado**: 1 dia

---

#### 1.8 Orchestrator ✅ CONCLUÍDO

**Objetivo**: Orquestrador que coordena os 4 especialistas + judge

**Ações**:

- Criar `src/agents/orchestrator.py`
- Lógica de orquestração:

1. Recebe query do usuário
2. Decide quais perspectivas BSC são relevantes
3. Dispara agentes relevantes em paralelo
4. Agrega respostas
5. Envia para Judge validar
6. Consolida resposta final

- Usar prompt orchestrator já existente
- Tratamento de conflitos entre agentes
- Logging detalhado do fluxo

**Arquivos**:

- `src/agents/orchestrator.py` (novo)
- `tests/test_orchestrator.py` (novo)

**Tempo estimado**: 2 dias

---

### 🔗 FASE 1C - Orquestração e Interface (Semana 3-4)

#### 1.9 LangGraph Workflow

**Objetivo**: Grafo de execução com LangGraph para orquestração

**Ações**:

- Criar `src/graph/workflow.py`
- Definir nós do grafo:
- `start` → `analyze_query` → `route_agents` → `execute_agents` → `aggregate` → `judge` → `finalize` → `end`
- Implementar estados do grafo
- Suporte a ciclos (se judge reprovar, refinar)
- Visualização do grafo (opcional)
- Integração com Orchestrator

**Arquivos**:

- `src/graph/__init__.py` (novo)
- `src/graph/workflow.py` (novo)
- `src/graph/states.py` (novo - definição de estados)
- `tests/test_workflow.py` (novo)

**Tempo estimado**: 2 dias

---

#### 1.10 Dataset BSC de Exemplo

**Objetivo**: Criar dataset de documentos BSC para teste

**Ações**:

- Coletar/criar 10-20 documentos BSC:
- Papers acadêmicos sobre BSC
- Estudos de caso
- Guias de implementação
- Exemplos de KPIs por perspectiva
- Organizar em `data/bsc_literature/`
- Criar metadados (autor, ano, perspectiva, etc)
- Documentar fontes

**Arquivos**:

- `data/bsc_literature/*.pdf` (documentos)
- `data/bsc_literature/index.json` (metadados)
- `data/README.md` (documentação)

**Tempo estimado**: 1 dia (coleta) + indexação usando pipeline

---

#### 1.11 Interface Streamlit

**Objetivo**: Interface web simples para interagir com o agente

**Ações**:

- Criar `app/main.py`
- Componentes:
- Input de query
- Visualização de resposta final
- Expandible: respostas de cada perspectiva
- Documentos recuperados (com scores)
- Avaliação do Judge
- Histórico de conversação
- Configurações (ex: quais perspectivas ativar)
- Design limpo e responsivo
- Chat-like interface

**Arquivos**:

- `app/__init__.py` (novo)
- `app/main.py` (novo)
- `app/components/` (componentes Streamlit)
- `app/utils.py` (utilitários)

**Tempo estimado**: 2 dias

---

### ✅ FASE 1D - Validação e Testes (Semana 4)

#### 1.12 Testes End-to-End

**Objetivo**: Validar sistema completo funcionando

**Ações**:

- Criar suite de testes E2E
- Testar fluxo completo:

1. Indexar documentos
2. Fazer queries BSC
3. Validar respostas

- Queries de teste:
- "Quais são os principais KPIs da perspectiva financeira?"
- "Como implementar BSC em uma empresa?"
- "Qual a relação entre satisfação de clientes e lucratividade?"
- Medir métricas:
- Latência P50, P95, P99
- Qualidade de resposta (manual)
- Coverage (% de docs relevantes recuperados)

**Arquivos**:

- `tests/integration/test_e2e.py` (novo)
- `tests/integration/test_queries.json` (queries de teste)
- `docs/TESTING_GUIDE.md` (novo)

**Tempo estimado**: 2 dias

---

#### 1.13 Documentação MVP

**Objetivo**: Documentar sistema MVP para uso

**Ações**:

- Atualizar `README.md` com arquitetura MVP
- Criar `docs/QUICKSTART.md`
- Criar `docs/API_REFERENCE.md`
- Documentar configurações `.env`
- Tutorial de uso passo-a-passo
- Exemplos de queries

**Arquivos**:

- `README.md` (atualizar)
- `docs/QUICKSTART.md` (novo)
- `docs/API_REFERENCE.md` (novo)
- `docs/ARCHITECTURE_MVP.md` (novo)

**Tempo estimado**: 1 dia

---

## 🎯 FASE 1 - ENTREGÁVEIS

Ao final da Fase 1, teremos:

✅ Sistema RAG completo e funcional
✅ 4 agentes especialistas BSC
✅ Orquestração com LangGraph
✅ Interface Streamlit
✅ Dataset BSC indexado
✅ Testes E2E
✅ Documentação completa

**Métrica de Sucesso**:

- Sistema responde queries BSC com latência < 3s
- Respostas cobrem múltiplas perspectivas relevantes
- Interface funcional e intuitiva
- Código testado e documentado

---

## FASE 2: FEATURES AVANÇADAS (4-6 semanas)

> **IMPORTANTE**: Implementar APENAS após validar MVP com dados reais e identificar necessidades específicas

### 📈 FASE 2A - Query Enhancement (Semanas 5-6)

#### 2.1 Query Decomposition

**Quando implementar**: Se queries reais forem muito complexas e retrieval básico falhar

**Objetivo**: Quebrar queries complexas em sub-queries

**Ações**:

- Criar `src/rag/query_enhancement.py`
- Implementar `QueryDecomposer`
- Prompts especializados para BSC
- Agregar resultados de sub-queries com RRF
- Integrar com Retriever

**Tempo estimado**: 2 dias

---

#### 2.2 HyDE (Hypothetical Document Embeddings)

**Quando implementar**: Se retrieval direto tiver baixo recall

**Objetivo**: Gerar documento hipotético para melhorar busca

**Ações**:

- Adicionar `HyDERetriever` em query_enhancement.py
- Prompt para documento hipotético
- Pipeline: query → doc hipotético → embedding → search
- Combinar com retrieval tradicional

**Tempo estimado**: 2 dias

---

### 🎨 FASE 2B - Retrieval Avançado (Semanas 7-8)

#### 2.3 Adaptive Retrieval

**Quando implementar**: Se houver padrões claros de tipos de query

**Objetivo**: Ajustar estratégia dinamicamente

**Ações**:

- Classificador de queries (simples/complexa, factual/conceitual)
- Roteamento inteligente
- Ajuste de pesos híbridos por tipo de query

**Tempo estimado**: 3 dias

---

#### 2.4 Iterative Retrieval

**Quando implementar**: Se respostas frequentemente precisarem de mais contexto

**Objetivo**: Refinar retrieval iterativamente

**Ações**:

- Loop: retrieve → generate → avaliar → retrieve novamente
- Limite de 3 iterações
- Critérios de parada

**Tempo estimado**: 3 dias

---

#### 2.5 Melhorias no Re-ranking

**Objetivo**: Otimizar qualidade de re-ranking

**Ações**:

- Diversity re-ranking (evitar docs similares)
- Temporal re-ranking (priorizar recentes quando relevante)
- Cross-encoder local como fallback
- Ensemble de re-rankers

**Tempo estimado**: 2 dias

---

### 🚀 FASE 2C - Otimizações (Semanas 9-10)

#### 2.6 Fine-tuning de Embeddings (Opcional)

**Quando implementar**: Se houver dataset suficiente de (query, doc relevante) do domínio BSC

**Objetivo**: Embeddings especializados para BSC

**Ações**:

- Coletar dataset de pares
- Fine-tune com Sentence-Transformers
- Validar melhorias
- Implementar fallback

**Tempo estimado**: 1 semana

---

#### 2.7 Avaliação de RAPTOR (Opcional)

**Quando implementar**: Se documentos BSC forem muito longos e estruturados

**Objetivo**: Retrieval hierárquico multi-nível

**Ações**:

- Estudar casos de uso
- POC com documentos BSC
- Implementar se ROI positivo

**Tempo estimado**: 3-5 dias (avaliação) ou 2 semanas (implementação completa)

---

#### 2.8 Avaliação de Graph RAG (Opcional)

**Quando implementar**: Se relações entre conceitos BSC forem críticas

**Objetivo**: Knowledge graph para relações BSC

**Ações**:

- Avaliar benefícios para BSC
- Extração de entidades e relações
- Neo4j integration
- Hybrid retrieval: vector + graph

**Tempo estimado**: 3-5 dias (avaliação) ou 2-3 semanas (implementação completa)

---

## 📊 Métricas de Sucesso

### Fase 1 (MVP)

- ✅ Sistema funciona end-to-end
- ✅ Latência < 3s (P95)
- ✅ Respostas cobrem perspectivas relevantes
- ✅ Interface utilizável

### Fase 2 (Otimizado)

- 📈 Recall@10: +30-40% vs MVP
- 📈 Precision@5: +25-35% vs MVP
- 📈 Latência P95: < 2s
- 📈 Redução de Alucinações: 40-50%
- 📈 Satisfação de Usuário: > 80%

---

## 🎯 Próximos Passos Imediatos

1. ✅ Revisar e aprovar plano revisado
2. ⏳ Iniciar Fase 1A.1: Implementar Embeddings
3. ⏳ Completar Pipeline RAG (1A.1 → 1A.4)
4. ⏳ Implementar Sistema Multi-Agente (1B)
5. ⏳ Criar Interface e Dataset (1C)
6. ⏳ Validar MVP completo (1D)
7. ⏳ **DEPOIS**: Decidir features Fase 2 baseado em resultados

---

## ✅ To-dos Atualizados

### Fase 1A - Pipeline RAG (Semana 1)

- [ ] 1.1 Implementar Embeddings OpenAI
- [ ] 1.2 Implementar Retriever com Hybrid Search
- [ ] 1.3 Implementar Re-ranker Cohere
- [ ] 1.4 Criar Pipeline de Ingestão

### Fase 1B - Multi-Agente (Semanas 2-3)

- [ ] 1.5 Criar Ferramentas RAG para Agentes
- [ ] 1.6 Implementar 4 Agentes Especialistas BSC
- [ ] 1.7 Implementar Judge Agent
- [ ] 1.8 Implementar Orchestrator

### Fase 1C - Orquestração e Interface (Semanas 3-4)

- [ ] 1.9 Criar LangGraph Workflow
- [ ] 1.10 Criar Dataset BSC de Exemplo
- [ ] 1.11 Implementar Interface Streamlit

### Fase 1D - Validação (Semana 4)

- [ ] 1.12 Criar Testes End-to-End
- [ ] 1.13 Documentar MVP

### Fase 2 - Features Avançadas (APÓS validar MVP)

- [ ] 2.1 Implementar Query Decomposition (se necessário)
- [ ] 2.2 Implementar HyDE (se necessário)
- [ ] 2.3 Implementar Adaptive Retrieval (se necessário)
- [ ] 2.4 Implementar Iterative Retrieval (se necessário)
- [ ] 2.5 Melhorar Re-ranking (se necessário)
- [ ] 2.6 Fine-tune Embeddings (opcional)
- [ ] 2.7 Avaliar RAPTOR (opcional)
- [ ] 2.8 Avaliar Graph RAG (opcional)

---

## 📝 Notas Importantes

**Por que MVP-First?**

1. ✅ Sistema funcional rapidamente (3-4 semanas vs 6 meses)
2. ✅ Valida arquitetura com dados reais cedo
3. ✅ Features avançadas baseadas em necessidade real (não especulação)
4. ✅ Mais ágil e menos risco de over-engineering
5. ✅ Usuário pode começar a usar e dar feedback

**O que mudou do plano original?**

- Foco em completar pipeline básico PRIMEIRO
- Sistema multi-agente ANTES de features avançadas
- Validação com dados reais ANTES de otimizar
- Features avançadas movidas para Fase 2 (após validação)

**Componentes já implementados que serão usados**:

- ✅ Vector Store moderno (Qdrant/Weaviate)
- ✅ Contextual Retrieval (Anthropic)
- ✅ Chunking semântico
- ✅ Prompts especializados BSC

---

## 🎯 PRÓXIMAS ETAPAS PRIORITÁRIAS

### ⚡ IMEDIATO (Próxima Sessão)

1. **Expandir Dataset BSC** 📚

- Adicionar mais documentos acadêmicos sobre BSC
- Casos de uso e exemplos práticos
- Papers de Kaplan & Norton
- **Objetivo**: Enriquecer base de conhecimento

2. **LangGraph Workflow** 🔗 (Fase 1C.9)

- Criar `src/graph/workflow.py`
- Orquestração visual do fluxo multi-agente
- State management e branching condicional
- **Tempo estimado**: 2 dias

3. **Interface Streamlit** 🖥️ (Fase 1C.11)

- Criar `app/main.py`
- Chat interface web
- Visualização de perspectivas BSC consultadas
- Display de fontes e scores
- **Tempo estimado**: 2 dias

### 📅 CURTO PRAZO (Esta Semana)

4. **Testes End-to-End** 🧪 (Fase 1D.12)

- Suite completa de testes E2E
- Validar fluxo: query → orchestrator → synthesis
- Métricas de latência e qualidade

5. **Documentação Final** 📖 (Fase 1D.13)

- Atualizar README com arquitetura completa
- QUICKSTART.md para onboarding rápido
- API Reference dos agentes

---

**Última atualização**: 2025-10-09 (tarde - otimizações implementadas)
**Status**: Fase 1A e 1B COMPLETAS ✅ | Otimizações de Performance ✅ | Fase 1C EM ANDAMENTO ⏳
**Progresso MVP**: ~80% (16/20 tarefas + otimizações críticas)

### To-dos Consolidados

#### ✅ Fase 1A & 1B - COMPLETAS

- [x] Setup Completo do Ambiente (venv + deps + Docker)
- [x] Implementar módulo de Embeddings OpenAI
- [x] Implementar Retriever com Hybrid Search
- [x] Implementar Re-ranker Cohere
- [x] Criar Pipeline de Ingestão completo
- [x] Criar Ferramentas RAG para Agentes
- [x] Implementar 4 Agentes Especialistas BSC
- [x] Implementar Judge Agent
- [x] Implementar Orchestrator

#### ⚡ Otimizações Implementadas (09/10/2025)

- [x] **Processamento Paralelo no Contextual Chunker** (10 workers)
- [x] **Retry Logic com Exponential Backoff** (rate limits)
- [x] **Progress Logging Thread-Safe** (visibilidade do processo)
- [x] **Batch Upload para Qdrant** (100 docs/batch, resolveu limite 32MB)
- [x] **Migração para API Moderna** (query_points vs search deprecado)
- [x] **Indexação BSC Completa** (1332 chunks do documento principal)

#### ⏳ Fase 1C - EM ANDAMENTO

- [ ] **Criar LangGraph Workflow** (próximo!)
- [ ] **Expandir Dataset BSC** (adicionar mais documentos)
- [ ] **Implementar Interface Streamlit** (interface web)

#### 📅 Fase 1D - PENDENTE

- [ ] Criar Testes End-to-End
- [ ] Documentar MVP completo

#### 🚀 Fase 2 - FUTURO (Após validar MVP)

- [ ] Implementar Query Decomposition (se necessário)
- [ ] Implementar HyDE (se necessário)
- [ ] Implementar Adaptive Retrieval (se necessário)
- [ ] Implementar Iterative Retrieval (se necessário)
- [ ] Melhorar sistema de re-ranking (se necessário)
- [ ] Fine-tune embeddings para domínio BSC (opcional)
- [ ] Avaliar RAPTOR (opcional)
- [ ] Avaliar Graph RAG (opcional)

### To-dos

#### ✅ Fase 0 & 1A-1B: CONCLUÍDAS

- [x] Setup Completo do Ambiente (venv + deps + Docker)
- [x] Implementar módulo de Embeddings OpenAI
- [x] Implementar Retriever com Hybrid Search
- [x] Implementar Re-ranker Cohere
- [x] Implementar Contextual Retrieval (Anthropic) + Cache + Paralelização (10 workers)
- [x] Criar Pipeline de Ingestão completo + Batch Upload Qdrant + Otimizações
- [x] Avaliar Qdrant vs Weaviate (escolhemos Qdrant)
- [x] Migrar de Redis para Qdrant (implementado com query_points API moderna)
- [x] Criar Ferramentas RAG para Agentes
- [x] Implementar 4 Agentes Especialistas BSC (Financeiro, Cliente, Processos, Aprendizado)
- [x] Implementar Judge Agent
- [x] Implementar Orchestrator

#### ⏳ Fase 1C-1D: EM ANDAMENTO (MVP)

- [ ] Expandir Dataset BSC de Exemplo (atualmente: 1 documento apenas)
- [ ] Criar LangGraph Workflow (src/graph/workflow.py)
- [ ] Implementar Interface Streamlit (app/main.py)
- [ ] Criar Testes End-to-End
- [ ] Documentar MVP completo
- [ ] Testes e validação completa da Fase 1

#### 🔮 Fase 2: RAG Avançado (PLANEJADO)

- [ ] Implementar Query Decomposition
- [ ] Implementar HyDE (Hypothetical Document Embeddings)
- [ ] Implementar Adaptive Retrieval
- [ ] Implementar Iterative Retrieval
- [ ] Melhorar sistema de re-ranking
- [ ] Testes e validação completa da Fase 2

#### 🚀 Fase 3: Produção (FUTURO)

- [ ] Fine-tune embeddings para domínio BSC
- [ ] Avaliar e decidir sobre implementação de RAPTOR
- [ ] Avaliar e decidir sobre implementação de Graph RAG
- [ ] Otimizações de performance para produção
- [ ] Documentação final e preparação para deploy
