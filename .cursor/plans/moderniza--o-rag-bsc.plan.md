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

## 🎯 **RESUMO EXECUTIVO - Avanços 09-10/10/2025**

### ✅ **Conquistas Principais**

1. **Dataset BSC Completo para MVP** 📚

- 2 livros fundamentais de Kaplan & Norton indexados
- 2.881 chunks contextualizados (+116% vs dia anterior)
- Base de conhecimento robusta pronta para validação

2. **Pipeline de Ingestão Otimizado** ⚡

- Processamento paralelo (10 workers simultâneos)
- Batch upload Qdrant (29 batches, 100 docs cada)
- Cache inteligente (0.4s para reprocessamento)
- API moderna (query_points do Qdrant)

3. **Qualidade de Código Aprimorada** 🔧

- Emojis removidos (encoding UTF-8 Windows)
- Warnings Pydantic v1 suprimidos
- Logs profissionais com marcadores de texto
- Bugs corrigidos (VectorStoreStats)

### 📊 **Status Atual do Projeto**

- **Progresso MVP**: 82% (17/20 tarefas)
- **Fase 1A-1B**: ✅ 100% COMPLETAS
- **Fase 1C**: ⏳ 40% (Dataset ✅ | Workflow ⏳ | Interface ⏳)
- **Próximo**: LangGraph Workflow → Interface Streamlit

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

**Métricas Alcançadas** (atualizado 10/10/2025):

- 📊 **2.881 chunks** contextualizados e indexados (2 documentos BSC)
- ⚡ **0.4 segundos** para processar 2881 chunks (com cache ativo)
- 🎯 **Score de retrieval: 0.66-0.67** (boa relevância)
- 🚀 **Batch upload: 29 batches** de 100 documentos cada

**Arquivos Otimizados**:

- `src/rag/contextual_chunker.py` - Processamento paralelo + retry logic
- `scripts/build_knowledge_base.py` - Batch upload + progress tracking
- `src/rag/qdrant_vector_store.py` - API moderna query_points()

---

### 📅 Avanços Implementados (10/10/2025) 🚀

**Dataset BSC Expandido**: COMPLETO ✅

- ✅ **2 livros fundamentais de Kaplan & Norton indexados**:
- "The Balanced Scorecard: Translating Strategy into Action" (1996) - 8.978 linhas
- "The Strategy-Focused Organization" (2000) - 11.490 linhas
- ✅ **2.881 chunks contextualizados** (vs 1.332 anterior) - crescimento de 116%
- ✅ **29 batches processados** com sucesso (vs 14 anterior)
- ✅ **Base de conhecimento BSC robusta** para MVP

**Correções Técnicas e Qualidade de Código**:

- ✅ Remoção de TODOS os emojis do código (seguindo best practice Windows encoding)
- ✅ Logs limpos com marcadores de texto: [OK], [ERRO], [WARN], [STATS], [INFO]
- ✅ Supressão de DeprecationWarnings do Pydantic v1 (warnings de dependências, não afetam funcionamento)
- ✅ Correção de bug VectorStoreStats: `num_docs` → `num_documents`
- ✅ Código mais limpo e profissional, sem problemas de encoding UTF-8 no Windows

**Performance Mantida**:

- ⚡ Cache funcionando perfeitamente (0.4s para reprocessamento de 2881 chunks)
- ⚡ Processamento paralelo estável (10 workers simultâneos)
- 🎯 Score de retrieval consistente: 0.66-0.67

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

- `ContextualChunker` com Claude Sonnet 4.5
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

#### 1.10 Dataset BSC de Exemplo ✅ PARCIALMENTE CONCLUÍDO (Atualizado 10/10/2025)

**Objetivo**: Criar dataset de documentos BSC para teste

**Status Atual**:

- ✅ **2 livros fundamentais de Kaplan & Norton indexados**:
- "The Balanced Scorecard: Translating Strategy into Action" (1996)
- "The Strategy-Focused Organization" (2000)
- ✅ **2.881 chunks contextualizados** e prontos para uso
- ✅ **Base robusta suficiente para MVP** - permite validar sistema completo
- ⏸️ **Expansão futura opcional**: Pode adicionar casos de uso, estudos específicos se necessário após MVP

**Ações Completadas**:

- ✅ Coletar literatura fundamental BSC (2 livros principais de Kaplan & Norton)
- ✅ Organizar em `data/bsc_literature/`
- ✅ Processar e indexar com pipeline completo (Contextual Retrieval + Embeddings + Qdrant)

**Ações Futuras (Opcional)**:

- Adicionar estudos de caso empresariais
- Guias de implementação práticos
- Exemplos de KPIs por perspectiva
- Criar metadados estruturados (autor, ano, perspectiva)
- Documentar fontes em `data/README.md`

**Arquivos**:

- ✅ `data/bsc_literature/*.md` (2 documentos markdown)
- ⏳ `data/bsc_literature/index.json` (metadados) - futuro
- ⏳ `data/README.md` (documentação) - futuro

**Tempo estimado**: ✅ COMPLETO para MVP (2 livros suficientes) | +1 dia opcional para expansão futura

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

**Objetivo**: Knowledge graph para relações BSC e raciocínio multi-hop

**Benchmarks e Critérios de Decisão**:

**Quando GraphRAG supera Vector RAG** (baseado em pesquisas out/2025):

- Queries envolvem **lógica de negócio** ou definições de métricas (ex: "como KPI X impacta objetivo Y?")
- Respostas requerem **relações causa-efeito** entre perspectivas BSC
- **Raciocínio multi-hop** necessário (ex: "Aprendizado → Processos → Clientes → Financeira")
- Domínios **relationship-intensive** com entidades fortemente conectadas
- Benchmarks: +35% precisão em queries relacionais (FalkorDB, 2025)

**Casos de Uso BSC Específicos**:

- Mapear causa-efeito entre KPIs de diferentes perspectivas
- Responder "quais objetivos de aprendizado impactam a receita?"
- Navegação por dependências: "mostre cadeia de valor do treinamento até lucro"
- Análise de impacto: "se melhorar satisfação cliente, qual efeito na perspectiva financeira?"
- Validação de mapas estratégicos (consistência de relações)

**Quando NÃO usar GraphRAG**:

- ❌ Dataset atual (literatura conceitual BSC) - Vector RAG apropriado
- ❌ Apenas busca por similaridade semântica
- ❌ Sem dados estruturados de BSCs reais com relações explícitas
- ❌ ROI negativo (custo de construir knowledge graph > benefício)

**Ações**:

- **Fase 1 - Avaliação (5-7 dias)**:
- Analisar dataset BSC para identificar entidades e relações
- POC com amostra: extrair entidades (Objetivos, KPIs, Iniciativas, Perspectivas)
- Modelar relações: causa-efeito, pertence-a, impacta, deriva-de
- Benchmark: comparar retrieval GraphRAG vs Vector RAG em queries relacionais
- Decisão GO/NO-GO baseada em métricas

- **Fase 2 - Implementação (3-4 semanas se GO)**:
- Extração de entidades e relações (spaCy + LLM-based NER)
- Construir Knowledge Graph com Neo4j
- Implementar Cypher query generation para queries estruturadas
- Hybrid retrieval: Vector RAG (similaridade) + Graph RAG (relações)
- Integração com LangGraph workflow existente
- Re-ranking combinando scores vector + graph

**Stack Tecnológico**:

- Neo4j (graph database) ou ArangoDB (multi-model)
- LangChain Neo4jGraph integration
- spaCy + GPT-5 para extração de entidades BSC
- Cypher (query language para Neo4j)
- LlamaIndex KnowledgeGraphIndex (alternativa)

**ROI Esperado**:

- ✅ **Alto ROI**: SE múltiplos BSCs empresariais com relações documentadas
- 🟡 **Médio ROI**: SE queries frequentemente envolvem causa-efeito
- ❌ **Baixo ROI**: Dataset atual (literatura conceitual, poucos relacionamentos estruturados)

**Tempo estimado**: 5-7 dias (avaliação) ou 3-4 semanas (implementação completa)

---

#### 2.9 Avaliação de Multi-modal RAG (Opcional)

**Quando implementar**: Se dataset incluir documentos BSC com elementos visuais relevantes

**Objetivo**: Processar e extrair informações de mapas estratégicos, dashboards e diagramas BSC

**Justificativa para BSC**:

Documentos BSC são **ricos em elementos visuais**:

- **Mapas Estratégicos (Strategy Maps)**: Diagramas de causa-efeito entre objetivos
- **Dashboards BSC**: Gráficos, KPI cards, gauges, semáforos de performance
- **Tabelas complexas**: KPIs, metas, iniciativas por perspectiva
- **Fluxogramas de Processos**: Perspectiva de Processos Internos
- **Apresentações executivas**: Slides com infográficos BSC

**Casos de Uso Concretos**:

1. **Extração de Strategy Maps**:

- Query: "Mostre o mapa estratégico da perspectiva financeira"
- Processar PDF com diagrama e extrair objetivos + relações causa-efeito

2. **Análise de Dashboards**:

- Query: "Quais KPIs estão em zona vermelha no dashboard?"
- OCR + Vision LLM para extrair valores e status de KPIs

3. **Comparação Visual**:

- Query: "Compare o BSC 2024 vs 2025 visualmente"
- Processar dois dashboards e identificar diferenças

4. **Extração de Tabelas Complexas**:

- Tabelas com múltiplas colunas (KPI, Meta, Atual, Responsável, Status)
- Table understanding com GPT-5 ou Claude Sonnet 4.5

5. **Interpretação de Processos**:

- Fluxogramas da perspectiva de Processos Internos
- Extrair etapas, gargalos, melhorias

**Quando NÃO usar Multi-modal RAG**:

- ❌ Dataset atual contém apenas texto (markdown, PDFs textuais)
- ❌ Elementos visuais são decorativos (não agregam informação crítica)
- ❌ ROI negativo (custo de processamento multimodal > benefício)
- ❌ Queries dos usuários não referenciam elementos visuais

**Ações**:

- **Fase 1 - Avaliação (1 semana)**:
- Audit do dataset: quantificar documentos com elementos visuais
- Identificar tipos de imagens (Strategy Maps, dashboards, tabelas, gráficos)
- POC com 5-10 documentos visuais BSC
- Testar extração com GPT-5 Vision API
- Métricas: precisão de extração, tempo de processamento, custo
- Decisão GO/NO-GO baseada em ROI

- **Fase 2 - Implementação (2-3 semanas se GO)**:
- Integrar Unstructured.io para parsing de PDFs multimodais
- Configurar GPT-5 Vision / Claude Sonnet 4.5 para análise de imagens
- Implementar extração de tabelas com table understanding
- CLIP embeddings para busca híbrida texto + imagem
- LangChain MultiModalRetriever integration
- Pipeline: PDF → extract images → Vision LLM → structured data → index

- **Fase 3 - Otimização (+1 semana)**:
- Cache de análise de imagens (evitar reprocessamento)
- Fallback: se Vision LLM falhar, usar OCR tradicional (Tesseract)
- Integração com agentes BSC (cada agente pode consultar imagens)
- Visualização de fontes visuais na interface Streamlit

**Stack Tecnológico**:

- **Vision LLMs**: GPT-5 Vision API, Claude Sonnet 4.5, LLaVA (open-source)
- **Document Processing**: Unstructured.io, PyMuPDF (extração de imagens)
- **Table Understanding**: Microsoft Table Transformer, GPT-5
- **OCR Fallback**: Tesseract OCR, Azure Form Recognizer
- **Embeddings**: CLIP (OpenAI) para embeddings multimodais
- **Framework**: LangChain MultiModalRetriever, LlamaIndex ImageReader

**ROI Esperado**:

- ✅ **Alto ROI**: SE 30%+ do dataset contém Strategy Maps ou dashboards críticos
- 🟡 **Médio ROI**: SE queries frequentemente referenciam elementos visuais
- 🟡 **Médio ROI**: SE apresentações executivas BSC são fonte primária
- ❌ **Baixo ROI**: Dataset atual (texto puro, sem diagramas BSC relevantes)

**Métricas de Sucesso**:

- Precisão de extração de KPIs de dashboards: >90%
- Acurácia de relações causa-efeito em Strategy Maps: >85%
- Latência de processamento multimodal: <10s por imagem
- Custo incremental: <30% vs pipeline text-only
- User satisfaction: +20% em queries visuais

**Tempo estimado**: 1 semana (avaliação) ou 2-3 semanas (implementação) + 1 semana (otimização)

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
- [ ] 2.9 Avaliar Multi-modal RAG (opcional)

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

1. ✅ ~~**Expandir Dataset BSC**~~ 📚 **CONCLUÍDO**

- ✅ 2 livros fundamentais de Kaplan & Norton indexados
- ✅ 2.881 chunks contextualizados
- ✅ Base robusta suficiente para MVP
- **Status**: COMPLETO - pode expandir futuramente se necessário

2. **LangGraph Workflow** 🔗 (Fase 1C.9) - **PRÓXIMO PASSO**

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

**Última atualização**: 2025-10-10 (Dataset BSC expandido + Correções técnicas + Logs limpos)
**Status**: Fase 1A e 1B COMPLETAS ✅ | Otimizações ✅ | Dataset BSC ✅ | Fase 1C EM ANDAMENTO ⏳
**Progresso MVP**: ~82% (17/20 tarefas concluídas + otimizações críticas)
**Dataset**: 2 livros fundamentais indexados (2.881 chunks contextualizados)
**Próximo**: LangGraph Workflow → Interface Streamlit → Testes E2E

### 📋 To-dos Consolidados (Atualizado 10/10/2025)

#### ✅ Fase 0 & 1A-1B: CONCLUÍDAS (100%)

- [x] Setup Completo do Ambiente (venv + deps + Docker)
- [x] Implementar módulo de Embeddings OpenAI
- [x] Implementar Retriever com Hybrid Search
- [x] Implementar Re-ranker Cohere
- [x] Implementar Contextual Retrieval (Anthropic) + Cache + Paralelização
- [x] Criar Pipeline de Ingestão completo + Batch Upload Qdrant
- [x] Avaliar Qdrant vs Weaviate (escolhemos Qdrant)
- [x] Migrar de Redis para Qdrant (com query_points API moderna)
- [x] Criar Ferramentas RAG para Agentes
- [x] Implementar 4 Agentes Especialistas BSC
- [x] Implementar Judge Agent
- [x] Implementar Orchestrator

#### ⚡ Otimizações Implementadas (09-10/10/2025)

- [x] **Processamento Paralelo no Contextual Chunker** (10 workers, 20% tier 4)
- [x] **Retry Logic com Exponential Backoff** (rate limits Anthropic)
- [x] **Progress Logging Thread-Safe** (visibilidade em tempo real)
- [x] **Batch Upload para Qdrant** (100 docs/batch, resolveu limite 32MB)
- [x] **Migração para API Moderna** (query_points vs search deprecado)
- [x] **Remoção de Emojis do Código** (encoding UTF-8 Windows)
- [x] **Supressão de Warnings Pydantic v1** (código mais limpo)
- [x] **Correção VectorStoreStats** (num_docs → num_documents)

#### ⏳ Fase 1C-1D: EM ANDAMENTO (MVP) - 40% completo

- [x] **Expandir Dataset BSC** ✅ (2 livros fundamentais: 2.881 chunks)
- [ ] **Criar LangGraph Workflow** (src/graph/workflow.py) - PRÓXIMO
- [ ] **Implementar Interface Streamlit** (app/main.py)
- [ ] Criar Testes End-to-End
- [ ] Documentar MVP completo

#### 🔮 Fase 2: RAG Avançado (APÓS validar MVP)

- [ ] Implementar Query Decomposition (se necessário)
- [ ] Implementar HyDE (se necessário)
- [ ] Implementar Adaptive Retrieval (se necessário)
- [ ] Implementar Iterative Retrieval (se necessário)
- [ ] Melhorar sistema de re-ranking (se necessário)
- [ ] Testes e validação completa da Fase 2

#### 🚀 Fase 3: Produção (FUTURO)

- [ ] Fine-tune embeddings para domínio BSC (opcional)
- [ ] Avaliar RAPTOR (opcional)
- [ ] Avaliar Graph RAG (opcional)
- [ ] Avaliar Multi-modal RAG (opcional)
- [ ] Otimizações de performance para produção
- [ ] Documentação final e preparação para deploy 

### To-dos

- [x] Implementar módulo de Embeddings OpenAI
- [x] Implementar Retriever com Hybrid Search
- [x] Implementar Re-ranker Cohere
- [x] Criar Pipeline de Ingestão completo
- [x] Criar Ferramentas RAG para Agentes
- [x] Implementar 4 Agentes Especialistas BSC
- [x] Implementar Judge Agent
- [x] Implementar Orchestrator
- [ ] Criar LangGraph Workflow
- [ ] Criar Dataset BSC de Exemplo
- [ ] Implementar Interface Streamlit
- [ ] Criar Testes End-to-End
- [ ] Documentar MVP completo
- [x] Setup Completo do Ambiente (venv + deps + Docker)
- [x] Implementar módulo de Embeddings OpenAI
- [x] Implementar Retriever com Hybrid Search
- [x] Implementar Re-ranker Cohere
- [x] Criar Pipeline de Ingestão completo
- [x] Criar Ferramentas RAG para Agentes
- [x] Implementar 4 Agentes Especialistas BSC
- [x] Implementar Judge Agent
- [x] Implementar Orchestrator
- [ ] Criar LangGraph Workflow
- [ ] Criar Dataset BSC de Exemplo
- [ ] Implementar Interface Streamlit
- [ ] Criar Testes End-to-End
- [ ] Documentar MVP completo
- [x] Setup Completo do Ambiente (venv + deps + Docker)
- [ ] Avaliar Qdrant vs Weaviate com POC e benchmarks
- [ ] Migrar de Redis para vector DB escolhido
- [ ] Implementar Contextual Retrieval (Anthropic)
- [ ] Implementar Query Decomposition
- [ ] Testes e validação completa da Fase 1
- [ ] Implementar HyDE (Hypothetical Document Embeddings)
- [ ] Implementar Adaptive Retrieval
- [ ] Implementar Iterative Retrieval
- [ ] Melhorar sistema de re-ranking
- [ ] Testes e validação completa da Fase 2
- [ ] Fine-tune embeddings para domínio BSC
- [ ] Avaliar e decidir sobre implementação de RAPTOR
- [ ] Avaliar e decidir sobre implementação de Graph RAG
- [ ] Otimizações de performance para produção
- [ ] Documentação final e preparação para deploy
- [ ] 