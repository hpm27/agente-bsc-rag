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
1. Usuário -> Interface Streamlit
2. Interface -> Orchestrator Agent
3. Orchestrator -> retrieve_knowledge("KPIs perspectiva financeira BSC")
4. retrieve_knowledge -> Retriever
5. Retriever -> Embedding Manager (gera embedding da query)
6. Retriever -> Redis Vector Store (hybrid search)
7. Redis -> Retriever (top-20 resultados)
8. Retriever -> Cohere Reranker (reordena)
9. Reranker -> Retriever (top-5 resultados)
10. Retriever -> Orchestrator (contexto formatado)
11. Orchestrator -> Financial Agent (delega tarefa com contexto)
12. Financial Agent -> GPT-4 (gera resposta)
13. Financial Agent -> Orchestrator (resposta estruturada)
14. Orchestrator -> Judge Agent (valida resposta)
15. Judge Agent -> GPT-4 (avalia qualidade)
16. Judge Agent -> Orchestrator (APROVADO ou REVISAR)
17. Se APROVADO: Orchestrator -> Interface -> Usuário
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

## Roadmap de Evolução (FASE 5-6) - Nov 2025

### Novas Fases Planejadas

**Decisão (2025-11-20):** Opção B aprovada - Integração Completa SOLUTION_DESIGN + IMPLEMENTATION (6 sprints, 4-6 semanas).

#### FASE 5: SOLUTION_DESIGN (Sprints 1-3)

**Objetivo:** Converter diagnóstico BSC em Strategy Map visual e validado.

**Novos Componentes:**

1. **Strategy_Map_Designer_Tool** (Sprint 2)
   - Converte CompleteDiagnostic em StrategyMap
   - Reutiliza StrategicObjectivesTool e KPIDefinerTool (FASE 3)
   - Mapeia conexões causa-efeito entre perspectivas
   - Output: StrategyMap com 4 perspectivas + objetivos + KPIs + conexões

2. **Alignment_Validator_Tool** (Sprint 2)
   - Valida balanceamento do Strategy Map
   - Detecta 5 tipos de gaps (perspectiva sem objetivos, objetivo sem KPI, etc)
   - Output: AlignmentReport com score 0-100 e lista de gaps

3. **KPI_Alignment_Checker** (Sprint 3)
   - Verifica KPIs alinhados com objetivos
   - Detecta KPIs órfãos ou duplicados
   - Output: KPIAlignmentReport

4. **Cause_Effect_Mapper** (Sprint 3)
   - Mapeia relações causa-efeito entre objetivos
   - Calcula força da relação (0-100)
   - Output: Grafo de conexões

**Novos Schemas Pydantic:**

```python
# src/memory/schemas.py (FASE 5)

class StrategicObjective(BaseModel):
    id: str
    perspective: Literal["financial", "customer", "process", "learning"]
    description: str
    kpis: List[KPI]

class CauseEffectConnection(BaseModel):
    from_objective_id: str
    to_objective_id: str
    strength: float  # 0-100
    rationale: str

class StrategyMap(BaseModel):
    financial_objectives: List[StrategicObjective]
    customer_objectives: List[StrategicObjective]
    process_objectives: List[StrategicObjective]
    learning_objectives: List[StrategicObjective]
    cause_effect_connections: List[CauseEffectConnection]
    alignment_score: float  # 0-100
```

**Novo Node LangGraph:**
- `design_solution()` - Gera Strategy Map a partir do diagnóstico aprovado

**Routing Modificado:**
- `APPROVAL_PENDING` (aprovado) -> `SOLUTION_DESIGN` -> `design_solution()`

---

#### FASE 6: IMPLEMENTATION (Sprint 4)

**Objetivo:** Converter Strategy Map em Action Plans executáveis com milestones.

**Novos Componentes:**

1. **Action_Plan_Generator_Tool** (Sprint 4)
   - Converte StrategyMap em ActionPlans
   - Gera 3-5 milestones por objetivo
   - Define responsáveis (role) e prazos (30/60/90 dias)
   - Output: List[ActionPlan]

2. **Milestone_Tracker_Tool** (Sprint 4)
   - Tracking de progresso de milestones
   - Atualiza status (todo -> in_progress -> done)
   - Calcula % progresso por perspectiva
   - Alertas de milestones atrasados

**Novos Schemas Pydantic:**

```python
# src/memory/schemas.py (FASE 6)

class Milestone(BaseModel):
    id: str
    description: str
    responsible_role: str
    deadline_days: int
    status: Literal["todo", "in_progress", "done"]
    dependencies: List[str]

class ActionPlan(BaseModel):
    objective_id: str
    perspective: Literal["financial", "customer", "process", "learning"]
    milestones: List[Milestone]
    progress_percentage: float  # 0-100
```

**Novo Node LangGraph:**
- `generate_action_plans()` - Cria Action Plans a partir do Strategy Map

**Routing Modificado:**
- `SOLUTION_DESIGN` -> `IMPLEMENTATION` -> `generate_action_plans()`

---

#### MCP Integrations (Sprints 5-6 - OPCIONAL)

**Objetivo:** Integrar ferramentas externas para tracking e automação.

**Componentes (Opcionais):**

1. **MCP Asana Integration**
   - Criar tasks no Asana a partir de Action Plans
   - Sincronizar status (bidirecional)
   - Webhook para updates em tempo real

2. **MCP Google Calendar Integration**
   - Criar meetings para milestones (revisões)
   - Sincronizar prazos
   - Alertas 1 semana antes

3. **Progress_Dashboard**
   - Visualização de progresso por perspectiva
   - Timeline de milestones
   - Alertas de atrasos

---

### GAP CRÍTICO #2 Identificado (Nov 2025)

**Problema:** DiagnosticAgent NÃO usa as 7 ferramentas consultivas implementadas na FASE 3.

**Root Cause:** `run_diagnostic()` chama APENAS 4 agentes BSC + RAG, ignora ferramentas consultivas.

**Impacto:** 70% do valor da FASE 3 desperdiçado (ferramentas implementadas mas não integradas).

**Solução (Sprint 1):**

1. Criar schema `DiagnosticToolsResult` para agregar outputs
2. Implementar método `_run_consultative_tools()` que executa 7 ferramentas em paralelo
3. Modificar `consolidate_diagnostic()` para usar outputs das ferramentas no prompt
4. Validar com testes E2E completos

**Novo Schema:**

```python
# src/memory/schemas.py (Sprint 1)

class DiagnosticToolsResult(BaseModel):
    """Agregador de outputs das 7 ferramentas consultivas."""
    swot_analysis: Optional[SWOTAnalysisResult] = None
    five_whys_analysis: Optional[FiveWhysResult] = None
    kpi_framework: Optional[KPIFrameworkResult] = None
    strategic_objectives: Optional[StrategicObjectivesResult] = None
    benchmarking_report: Optional[BenchmarkingResult] = None
    issue_tree: Optional[IssueTreeResult] = None
    prioritization_matrix: Optional[PrioritizationMatrixResult] = None
    execution_time: float
    tools_executed: List[str]
```

**Métricas Esperadas (Sprint 1):**
- 7/7 ferramentas integradas
- Latência adicional <60s (execução paralela)
- 100% testes E2E passando
- Diagnóstico rico com SWOT, Five Whys, KPIs visíveis

---

### Diagrama de Arquitetura Atualizado (FASE 5-6)

```
┌─────────────────────────────────────────┐
│         Streamlit UI (app.py)           │
│  ┌───────────────────────────────────┐  │
│  │ - Diagnóstico BSC                 │  │
│  │ - Strategy Map Visualizer (NOVO)  │  │
│  │ - Action Plans Dashboard (NOVO)   │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    LangGraph Workflow (workflow.py)     │
│  ┌────────────────────────────────────┐ │
│  │ Phases:                            │ │
│  │ - ONBOARDING [FASE 1]              │ │
│  │ - DISCOVERY [FASE 1-4]             │ │
│  │ - SOLUTION_DESIGN [FASE 5 NOVO]    │ │
│  │ - IMPLEMENTATION [FASE 6 NOVO]     │ │
│  │                                    │ │
│  │ Nodes:                             │ │
│  │ - onboarding()                     │ │
│  │ - discovery()                      │ │
│  │ - design_solution() [NOVO]         │ │
│  │ - generate_action_plans() [NOVO]   │ │
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Agents & Tools                  │
│  ┌────────────────────────────────────┐ │
│  │ FASE 1-4 (Existentes):             │ │
│  │ - OnboardingAgent                  │ │
│  │ - DiagnosticAgent [7 tools]        │ │
│  │ - 4 Specialist Agents (BSC)        │ │
│  │ - JudgeAgent                       │ │
│  │                                    │ │
│  │ FASE 5 (Novos):                    │ │
│  │ - Strategy_Map_Designer_Tool       │ │
│  │ - Alignment_Validator_Tool         │ │
│  │ - KPI_Alignment_Checker            │ │
│  │ - Cause_Effect_Mapper              │ │
│  │                                    │ │
│  │ FASE 6 (Novos):                    │ │
│  │ - Action_Plan_Generator_Tool       │ │
│  │ - Milestone_Tracker_Tool           │ │
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     Data Layer (Schemas + Memory)       │
│  ┌────────────────────────────────────┐ │
│  │ Pydantic Schemas:                  │ │
│  │ - ClientProfile                    │ │
│  │ - CompleteDiagnostic               │ │
│  │ - DiagnosticToolsResult [NOVO]     │ │
│  │ - StrategyMap [NOVO]               │ │
│  │ - ActionPlan [NOVO]                │ │
│  │                                    │ │
│  │ Memory: Mem0 API v2                │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

### Progresso Geral (Nov 2025)

**FASE 1-4**: [OK] 100% COMPLETAS (46/50 tarefas)
- Onboarding Agent
- RAG Avançado (Query Decomposition, Adaptive Re-ranking, Router)
- 7 Ferramentas Consultivas
- Advanced Features (Judge, Performance, Multi-Client, APIs)

**FASE 5-6**: [EMOJI] 0% (0/44 tarefas - planejadas)
- Sprint 1 (Semana 1): Integração Ferramentas (GAP #2) - [EMOJI] CRÍTICO
- Sprint 2 (Semana 2): Strategy Map MVP - [EMOJI] ALTO
- Sprint 3 (Semana 3): Validações Avançadas - MÉDIO
- Sprint 4 (Semana 4): Action Plans MVP - ALTO
- Sprint 5-6 (Semanas 5-6): MCPs + Dashboard - BAIXO (opcional)

**Progresso Total**: 46/90 tarefas (51%)

**Próximos Passos:**
1. Executar baseline E2E (capturar métricas antes mudanças)
2. Implementar Sprint 1 (integração ferramentas)
3. Implementar Sprint 2 (Strategy Map MVP)
4. Continuar sprints 3-4 conforme planejado

**Documentos Relacionados:**
- `docs/sprints/SPRINT_PLAN_OPÇÃO_B.md` - Roadmap completo 6 sprints
- `docs/PRD_BSC_RAG_AGENT.md` - Product Requirements Document
- `docs/implementation_guides/INTEGRATION_PLAN_GAP2.md` - Guia técnico resolução GAP #2
- `docs/analysis/GAP_CRITICAL_TOOLS_NOT_INTEGRATED.md` - Análise detalhada GAP #2

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
- **State Transitions**: Estados LangGraph (ONBOARDING -> DISCOVERY -> APPROVAL_PENDING)

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
