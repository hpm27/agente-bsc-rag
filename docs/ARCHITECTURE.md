# Arquitetura do Agente BSC

## Visão Geral

O Agente BSC é um sistema multi-agente avançado para consultoria em Balanced Scorecard, construído com as melhores práticas de RAG (Retrieval-Augmented Generation) e arquitetura de agentes de IA.

## Componentes Principais

### 1. Camada de Orquestração (LangGraph)

**Responsabilidade:** Coordenar o fluxo de execução entre agentes, ferramentas e o usuário.

**Tecnologia:** LangGraph (framework para grafos de agentes)

**Características:**
- Define estados e transições entre nós
- Gerencia memória de curto prazo (sessão)
- Implementa human-in-the-loop quando necessário
- Controla o fluxo condicional baseado em decisões do LLM

**Nós do Grafo:**
1. **Orchestrator Node:** Agente principal que recebe input do usuário
2. **Knowledge Retrieval Node:** Busca informações na base de conhecimento
3. **Specialist Nodes:** Um para cada perspectiva do BSC
4. **Tool Execution Node:** Executa ferramentas especializadas
5. **Judge Node:** Valida qualidade das respostas
6. **Human Approval Node:** Solicita aprovação para decisões críticas

### 2. Sistema RAG Otimizado

#### 2.1 Vector Store (Redis)

**Por que Redis?**
- Mais rápido vector database em benchmarks
- Suporte nativo a hybrid search (vetorial + BM25)
- Alta performance em produção
- RedisInsight para debugging visual

**Configuração:**
- Índice FLAT para datasets pequenos/médios
- HNSW para datasets grandes (>100k documentos)
- Dimensão: 3072 (text-embedding-3-large)
- Métrica de distância: Cosine

#### 2.2 Embeddings

**Opção 1: OpenAI (Padrão)**
- Modelo: `text-embedding-3-large`
- Dimensão: 3072
- Custo: $0.13 / 1M tokens
- Qualidade: Excelente out-of-the-box

**Opção 2: Fine-tuned (Avançado)**
- Base: `sentence-transformers/all-mpnet-base-v2`
- Treinamento: Contrastive learning com pares (query, doc relevante, docs irrelevantes)
- Benefício: Captura nuances do domínio BSC
- Trade-off: Requer dados de treinamento e infraestrutura

#### 2.3 Chunking Semântico

**Estratégia:**
- Respeita limites lógicos (seções, parágrafos, sentenças)
- Preserva tabelas intactas (crítico para BSC!)
- Adiciona contexto de chunks adjacentes
- Tamanho: 1000 caracteres (configurável)
- Overlap: 200 caracteres

**Classes:**
- `SemanticChunker`: Chunking básico respeitando estrutura
- `TableAwareChunker`: Detecta e preserva tabelas

#### 2.4 Hybrid Search

**Combinação:**
- **70% Busca Vetorial (Semântica):** Captura conceitos e significado
- **30% BM25 (Palavras-chave):** Captura termos exatos e jargão

**Por quê?**
- BSC tem terminologia específica (ex: "perspectiva financeira", "mapa estratégico")
- Busca puramente semântica pode perder termos técnicos exatos
- Hybrid search melhora recall em ~15-20%

#### 2.5 Re-ranking

**Cohere Rerank:**
- Modelo: `rerank-multilingual-v3.0` (suporta português)
- Reordena top-K resultados por relevância real
- Melhora precisão em ~30% vs. busca vetorial pura

**Fusion (RRF):**
- Combina resultados de múltiplas fontes
- Reciprocal Rank Fusion: `score = 1 / (k + rank)`
- Usado quando há múltiplas queries ou fontes

**Pipeline:**
1. Hybrid search retorna top-20
2. Fusion combina resultados vetoriais e BM25
3. Cohere rerank seleciona top-5 mais relevantes

### 3. Agentes Especializados

#### 3.1 Agente Orquestrador

**Prompt:** `src/prompts/orchestrator_prompt.py`

**Responsabilidades:**
- Entender intenção do usuário
- Quebrar tarefas complexas em subtarefas
- Delegar para agentes especialistas
- Sintetizar respostas de múltiplas fontes
- Manter controle do fluxo da conversa

**Ferramentas Disponíveis:**
- `retrieve_knowledge`: Busca na base de conhecimento
- `delegate_to_specialist`: Delega para agente especialista
- `analyze_strategy`: Analisa missão/visão/valores
- `generate_kpis`: Gera indicadores
- `create_strategy_map`: Cria mapa estratégico
- `validate_bsc`: Valida BSC completo
- `validate_response`: Envia para LLM as Judge

#### 3.2 Agentes Especialistas

**Um para cada perspectiva do BSC:**

1. **Financial Agent:** Perspectiva Financeira
2. **Customer Agent:** Perspectiva do Cliente
3. **Process Agent:** Perspectiva de Processos Internos
4. **Learning Agent:** Perspectiva de Aprendizado e Crescimento

**Cada agente:**
- Tem prompt especializado com conhecimento da perspectiva
- Acessa a base de conhecimento (RAG)
- Sugere objetivos, KPIs, metas e iniciativas
- Retorna resposta estruturada para o orquestrador

#### 3.3 Agente Validador (LLM as Judge)

**Prompt:** `src/prompts/judge_prompt.py`

**Função:**
- Avaliar qualidade das respostas antes de enviar ao usuário
- Critérios: Fundamentação, Completude, Clareza, Precisão, Praticidade
- Decisão: APROVADO (score >= 40/50) ou REVISAR
- Feedback específico para melhorias

**Por quê?**
- Reduz alucinações
- Garante alinhamento com metodologia BSC
- Melhora consistência das respostas
- Detecta erros antes que cheguem ao usuário

### 4. Ferramentas (Tools)

**Localização:** `src/tools/`

**Ferramentas Planejadas:**
1. **Strategy Analyzer:** Analisa coerência de missão/visão/valores
2. **KPI Generator:** Sugere indicadores baseados em objetivos
3. **Map Creator:** Gera mapas estratégicos (Mermaid.js)
4. **BSC Validator:** Valida estrutura completa do BSC

**Implementação:**
- Decorador `@tool` do LangChain
- Schema de input com Pydantic
- Docstrings descritivas para o LLM entender quando usar

### 5. Memória

#### 5.1 Memória de Curto Prazo (Sessão)

**Implementação:** LangGraph State

**Armazena:**
- Histórico de mensagens da conversa atual
- Contexto da organização (setor, tamanho, etc.)
- Objetivos e KPIs definidos na sessão
- Decisões tomadas

**Duração:** Apenas durante a sessão ativa

#### 5.2 Memória de Longo Prazo (Persistente)

**Implementação:** Redis ou PostgreSQL

**Armazena:**
- Informações da organização entre sessões
- BSCs parciais ou completos
- Histórico de interações
- Preferências do usuário

**Acesso:** Via `Store` do LangGraph

### 6. Human-in-the-Loop

**Quando Ativar:**
- Definição final de objetivos estratégicos
- Aprovação de mapa estratégico
- Validação de BSC completo
- Qualquer decisão marcada como "crítica"

**Fluxo:**
1. Agente prepara recomendação
2. Valida com LLM as Judge
3. Apresenta ao usuário com justificativa
4. Aguarda aprovação explícita
5. Prossegue ou revisa baseado no feedback

## Fluxo de Dados

### Exemplo: "Sugira KPIs para a perspectiva financeira"

```
1. Usuário → Interface Streamlit
2. Interface → Orchestrator Agent
3. Orchestrator → retrieve_knowledge("KPIs perspectiva financeira BSC")
4. retrieve_knowledge → Retriever
5. Retriever → Embedding Manager (gera embedding da query)
6. Retriever → Redis Vector Store (hybrid search)
7. Redis → Retriever (top-20 resultados)
8. Retriever → Cohere Reranker (reordena)
9. Reranker → Retriever (top-5 resultados)
10. Retriever → Orchestrator (contexto formatado)
11. Orchestrator → Financial Agent (delega tarefa com contexto)
12. Financial Agent → GPT-4 (gera resposta)
13. Financial Agent → Orchestrator (resposta estruturada)
14. Orchestrator → Judge Agent (valida resposta)
15. Judge Agent → GPT-4 (avalia qualidade)
16. Judge Agent → Orchestrator (APROVADO ou REVISAR)
17. Se APROVADO: Orchestrator → Interface → Usuário
18. Se REVISAR: Orchestrator revisa e repete 14-17
```

## Tecnologias e Bibliotecas

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| Orquestração | LangGraph | 0.0.20 |
| LLM | GPT-4 Turbo | latest |
| Embeddings | OpenAI text-embedding-3-large | latest |
| Vector Store | Redis Stack | latest |
| Re-ranking | Cohere Rerank Multilingual | v3.0 |
| Interface | Streamlit | 1.29.0 |
| Chunking | LangChain Text Splitters | 0.1.0 |
| Document Loading | pypdf, python-docx | latest |

## Métricas de Qualidade Esperadas

Com esta arquitetura, esperamos:

- **Acurácia do RAG:** >90% (vs. 64% do LangChain+Pinecone básico)
- **Relevância dos Resultados:** >95% após re-ranking
- **Precisão das Respostas:** >85% após validação com LLM as Judge
- **Latência P95:** <5s para queries simples, <15s para queries complexas
- **Taxa de Aprovação (Judge):** >80% na primeira tentativa

## Escalabilidade

### Pequena Escala (<10k documentos)
- Redis local
- OpenAI embeddings
- Índice FLAT
- Custo: ~$50/mês

### Média Escala (10k-100k documentos)
- Redis Cloud
- OpenAI embeddings
- Índice HNSW
- Custo: ~$200-500/mês

### Grande Escala (>100k documentos)
- Redis Enterprise
- Fine-tuned embeddings (reduz custo)
- Índice HNSW otimizado
- Cache agressivo
- Custo: ~$1000+/mês

## Próximos Passos

1. **Implementar Grafo LangGraph Completo**
2. **Desenvolver Ferramentas Especializadas**
3. **Criar Interface Streamlit**
4. **Testes de Integração**
5. **Fine-tuning de Embeddings**
6. **Avaliação de Qualidade (RAGAS)**
7. **Deployment em Produção**

---

## Documentação Arquitetural Relacionada

Para informações mais detalhadas sobre a arquitetura do sistema, consulte:

### Data Flow Diagrams
**Arquivo:** `docs/architecture/DATA_FLOW_DIAGRAMS.md`

Visualização de fluxos de dados críticos através de 5 diagramas Mermaid:
- **ClientProfile Lifecycle**: Criação, persistência Mem0, recuperação
- **Diagnostic Workflow**: Estado DISCOVERY, análise paralela AsyncIO das 4 perspectivas BSC
- **Schema Dependencies**: Relações Pydantic entre ClientProfile, BSCState, DiagnosticResult
- **Agent Interactions**: Comunicação entre OnboardingAgent, ClientProfileAgent, DiagnosticAgent
- **State Transitions**: Estados LangGraph (ONBOARDING → DISCOVERY → APPROVAL_PENDING)

**Quando consultar:** Implementando features que interagem com workflow existente, debugando fluxos de dados ou transições de estado.

### API Contracts
**Arquivo:** `docs/architecture/API_CONTRACTS.md`

Contratos API completos de todos os agentes do sistema (1200+ linhas):
- **8 agentes documentados**: ClientProfileAgent, OnboardingAgent, DiagnosticAgent, Specialist Agents (4), ConsultingOrchestrator, JudgeAgent
- **23 métodos públicos**: Assinaturas completas com type hints, parâmetros, retornos, exceções esperadas
- **7 schemas Pydantic**: CompanyInfo, StrategicContext, ClientProfile, BSCState, DiagnosticResult, Recommendation, CompleteDiagnostic
- **Changelog e Versioning**: v1.0.0 baseline (FASE 2) + v1.1.0 planejado (FASE 3)
- **Exemplos de uso**: Code snippets mínimos testáveis para cada método

**Quando consultar:** Chamando métodos de outros agentes, criando testes, precisando saber tipos de retorno e exceções.