# [EMOJI] PLANO: Transformação em Agente Consultor Empresarial BSC v2.0

**Data**: 2025-10-15

**Status**: Aprovação Pendente

**Versão**: 2.0 (Atualizado com Mem0 + Deploy Nuvem)

---

## [EMOJI] EXECUTIVE SUMMARY

### Objetivo

Transformar **Agente BSC RAG** (pergunta-resposta sobre literatura BSC) em **Agente Consultor Empresarial BSC** (facilitador de processo consultivo estruturado com C-level).

### Decisões Estratégicas Confirmadas

- [OK] **Memória**: Mem0 Platform (self-improving LLM memory, não Supabase inicialmente)
- [OK] **Escopo MVP**: Foco BSC exclusivo (multi-domain pós-validação)
- [OK] **Deploy**: Nuvem pós-validação (Fly.io free tier -> Railway -> Cloud Run)
- [OK] **Frameworks**: 12-Factor Agents + Anthropic Patterns + OpenAI Best Practices

### Esforço Estimado MVP

- **Micro-tarefas**: 50 (48 originais + 2 prep arquitetural FASE 3)
- **Horas**: 59-75h (15-19 sessões de 3-4h)
- **Timeline**: 4-5 semanas (sessões diárias)
- **Custo Operacional**: $70-140/mês (Mem0 + Cloud + APIs)

### Aproveitamento do Existente

- **RAG Core**: 100% reutilizado (retriever, embeddings, vector store, 4 agentes especialistas)
- **LangGraph**: 70% reutilizado (expandir states, manter orchestrator)
- **Infrastructure**: 90% reutilizado (config, logging, testing, Docker)
- **Novo Desenvolvimento**: 30% (~5.000-7.000 linhas código)

---

## [EMOJI] ARCHITECTURE OVERVIEW

### Stack Tecnológico MVP

```
┌───────────────────────────────────────────────────┐
│    AGENTE CONSULTOR BSC (Cloud-Native MVP)       │
├───────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────┐       ┌──────────────────────┐ │
│  │  LangGraph  │───────│   Mem0 Platform      │ │
│  │  Workflow   │       │  (Memory Persistent) │ │
│  └─────────────┘       └──────────────────────┘ │
│        │                                          │
│        │               ┌──────────────────────┐  │
│        │               │  Qdrant Vector Store │  │
│        │               │  (BSC Literature)    │  │
│        │               └──────────────────────┘  │
│        │                                          │
│  ┌─────────────┐       ┌──────────────────────┐ │
│  │  10 Agentes │       │   8 Tools            │ │
│  │  Consultivos│       │   Consultivas        │ │
│  └─────────────┘       └──────────────────────┘ │
│                                                   │
│  MCPs: Brightdata (benchmarks externos)          │
│                                                   │
│  Deploy: Local (dev) -> Fly.io (prod)             │
└───────────────────────────────────────────────────┘
```

### Componentes

**Memória Persistente** (Mem0):

- ClientProfile (empresa, indústria, desafios, objetivos)
- Engagement history (sessions, decisões, tool outputs)
- Semantic search em memórias passadas
- Self-improving (otimiza-se com uso)

**Workflow** (LangGraph - MVP):

- ONBOARDING: Coleta contexto empresa (5-7 perguntas)
- DISCOVERY: Diagnóstico estruturado (SWOT, 5 Whys, análise)
- APPROVAL_PENDING: Confirmação humana antes de prosseguir
- (Futuro: SOLUTION_DESIGN, IMPLEMENTATION)

**Agentes** (10 total):

- **Existentes (4)**: Financial, Customer, Process, Learning - Respondem perguntas BSC teóricas
- **Novos (6)**: ClientProfile, Onboarding, Diagnostic, Facilitator, Validator, ReportGenerator

**Ferramentas** (8 consultivas):

- SWOT_Builder, FiveWhys_Facilitator, IssueTree_Analyzer, KPI_Definer
- StrategyMap_Designer, Benchmark_Retriever, Parallel_Research, Feedback_Collector

---

## [EMOJI] FASES DO MVP (50 MICRO-TAREFAS)

### FASE 1: FOUNDATION - Memória Persistente (8 tarefas, 5-7h, 2 sessões)

**Objetivo**: Infraestrutura Mem0 para contexto cliente persistente

| ID | Tarefa | Duração | Entregável |

|----|--------|---------|------------|

| 1.1 | Research Mem0 Platform | 30-45 min | Decisão Platform vs Open Source |

| 1.2 | Setup Mem0 Platform | 30 min | API key configurada, conexão testada |

| 1.3 | ClientProfile Schema | 45-60 min | schemas.py com Pydantic models |

| 1.4 | Mem0 Client Wrapper | 1-1.5h | mem0_client.py (CRUD operations) |

| 1.5 | Factory Pattern Memory | 30 min | factory.py (swappable providers) |

| 1.6 | Config Management | 30 min | settings.py + .env (MEMORY_PROVIDER, CONSULTING_MODE) |

| 1.7 | LangGraph Integration | 1-1.5h | ConsultingState com client_profile |

| 1.8 | Testes Integração | 1h | test_mem0_integration.py (12+ testes) |

**Checkpoint 1**: Memória persiste entre sessões? Profile recupera corretamente?

---

### FASE 2: CONSULTING WORKFLOW - LangGraph Expansion (10 tarefas, 13-17h, 4-5 sessões)

**Objetivo**: Workflow ONBOARDING -> DISCOVERY -> APPROVAL

| ID | Tarefa | Duração | Entregável |

|----|--------|---------|------------|

| 2.1 | Design Workflow States | 45-60 min | docs/consulting-workflow-design.md |

| 2.2 | Expand ConsultingState | 1h | consulting_states.py |

| 2.3 | ClientProfileAgent | 1.5-2h | client_profile_agent.py (gerencia perfil) |

| 2.4 | OnboardingAgent | 2-2.5h | onboarding_agent.py (5-7 perguntas) |

| 2.5 | DiagnosticAgent | 2-3h | diagnostic_agent.py (analisa + recomenda) |

| 2.6 | ONBOARDING State | 1.5-2h | consulting_workflow.py (node onboarding) |

| 2.7 | DISCOVERY State | 1.5-2h | consulting_workflow.py (node discovery) |

| 2.8 | Transition Logic | 1h | consulting_transitions.py (routing) |

| 2.9 | Consulting Orchestrator | 2h | consulting_orchestrator.py (coordena agentes) |

| 2.10 | Testes E2E Workflow | 1.5-2h | test_consulting_workflow.py (15+ testes) |

**Checkpoint 2**: Workflow completo funciona? Diagnóstico é contextualizado? Onboarding eficiente (<10 min)?

---

### FASE 3: DIAGNOSTIC TOOLS - Ferramentas Consultivas (14 tarefas, 17-21h, 6-7 sessões)

**Objetivo**: Co-criação de análises estratégicas (SWOT, 5 Whys, KPIs)

**Nota Arquitetural**: Tarefas 3.0.x são prep obrigatória (Data Flow Diagrams + API Contracts) adicionada baseado em lições FASE 2. ROI: ~7h economizadas em FASE 3 via documentação arquitetural.

| ID | Tarefa | Duração | Entregável |

|----|--------|---------|------------|

| 3.0.1 | Data Flow Diagrams | 20-30 min | DATA_FLOW_DIAGRAMS.md (5 diagramas Mermaid) |

| 3.0.2 | API Contracts | 30-40 min | API_CONTRACTS.md (contratos 8 agentes) |

| 3.1 | SWOTAnalysisTool | 2-3h | swot_analysis.py (4 quadrantes + RAG integration) |

| 3.2 | FiveWhysTool | 3-4h | five_whys.py (root cause analysis 3-7 iterations) |

| 3.3 | IssueTree_Analyzer | 2h | issue_tree.py (problema -> sub-problemas) |

| 3.4 | KPI_Definer | 2h | kpi_definer.py (template SMART) |

| 3.5 | Evaluator-Optimizer Loop | 1.5h | evaluator_loop.py (iteração até qualidade) |

| 3.6 | Tools LangGraph Integration | 1.5h | consulting_workflow.py (adicionar tools) |

| 3.7 | Tool Selection Logic | 1h | orchestrator.py (sugerir tool adequado) |

| 3.8 | Planning CoT | 1h | facilitator_cot_prompt.py |

| 3.9 | Persist Tool Outputs | 1h | mem0_client.py (save outputs) |

| 3.10 | Testes E2E Tools | 1.5-2h | test_diagnostic_tools.py (20+ testes) |

**Checkpoint 3**: Ferramentas facilitam adequadamente? Outputs estruturados melhores que brainstorming livre?

---

### FASE 4: DELIVERABLES - Reports + Human-in-the-Loop (9 tarefas, 13-16h, 4-5 sessões)

**Objetivo**: Diagnostic report profissional + Approval workflow

| ID | Tarefa | Duração | Entregável |

|----|--------|---------|------------|

| 4.1 | ReportGeneratorAgent | 2-2.5h | report_generator_agent.py |

| 4.2 | Diagnostic Report Template | 1.5h | diagnostic_report_template.md (salvo em Mem0) |

| 4.3 | Strategy Map Designer | 2h | strategy_map_designer.py (objetivos 4 perspectivas) |

| 4.4 | Approval Workflow | 2h | approval_workflow.py (confirmação humana) |

| 4.5 | Feedback Collection | 1.5h | feedback_collector.py (rating + textual) |

| 4.6 | Refinement Logic | 1.5h | diagnostic_agent.py (refinar baseado feedback) |

| 4.7 | Approval State Transitions | 1h | consulting_workflow.py (APPROVAL_PENDING state) |

| 4.8 | Notification System | 1h | notifications.py (alertas aprovação) |

| 4.9 | Testes E2E Human-in-Loop | 1.5h | test_approval_workflow.py (12+ testes) |

**Checkpoint 4**: Report é profissional? Approval workflow funciona? Refinamento melhora output?

---

### FASE 5: ENHANCEMENT - Context + Metrics + Cloud Prep (9 tarefas, 13-16h, 3-4 sessões)

**Objetivo**: Enriquecer com benchmarks externos + Métricas consultivas + Deploy prep

| ID | Tarefa | Duração | Entregável |

|----|--------|---------|------------|

| 5.1 | Brightdata Integration | 1.5-2h | brightdata_client.py (queries estruturadas) |

| 5.2 | Benchmark Retriever | 1.5h | benchmark_retriever.py (KPIs setor, cases) |

| 5.3 | Parallel Research | 2h | parallel_research.py (AsyncIO multi-fonte) |

| 5.4 | Diagnostic Enrichment | 1.5h | diagnostic_agent.py (adicionar benchmarks) |

| 5.5 | Metrics Definition | 1h | docs/consulting-metrics-definition.md |

| 5.6 | Metrics Collector | 1.5h | collector.py (captura eventos automaticamente) |

| 5.7 | Metrics Dashboard | 2h | analyze_consulting_metrics.py |

| 5.8 | Testes Enhancement | 1.5-2h | test_enhancement.py (10+ testes) |

| 5.9 | Cloud Deployment Prep | 1-1.5h | Dockerfile otimizado, deploy/README.md |

**Checkpoint 5**: Diagnóstico enriquecido? Métricas coletam? Agente pronto para cloud?

---

## [OK] VALIDAÇÃO CONTÍNUA (5 Checkpoints)

| Checkpoint | Quando | O Que Validar | Critério Sucesso |

|------------|--------|---------------|------------------|

| **1** | Após FASE 1 | Memória persiste | 100% testes passam |

| **2** | Após FASE 2 | Workflow útil | Diagnóstico contextualizado, onboarding <10 min |

| **3** | Após FASE 3 | Ferramentas entregam valor | Outputs estruturados > brainstorming |

| **4** | Após FASE 4 | Report profissional | Poderia apresentar para C-level real |

| **5** | Após FASE 5 | MVP completo | 80%+ expectativas atendidas |

### Metodologia (Inspirada em PRD v3.0)

- **Morning Briefing**: Revisar progress, definir objetivos sessão (10 min)
- **Development Sprint**: Implementar micro-tarefas (2-3h)
- **Validation**: Testar, rodar testes (30 min)
- **Evening Planning**: Atualizar tracker + log (15 min)

---

## [EMOJI] SISTEMA DE PROGRESS TRACKING

### Nível 1: Plano Mestre (Este Documento)

- **Localização**: `.cursor/plans/consulting-transformation-v2.plan.md`
- **Conteúdo**: 48 micro-tarefas detalhadas, arquitetura, validação
- **Atualização**: Apenas se arquitetura mudar (raro)

### Nível 2: Progress Tracker (Dinâmico)

- **Localização**: `.cursor/progress/consulting-progress.md`
- **Conteúdo**: Status tarefas, % progresso, descobertas, próxima sessão
- **Atualização**: Ao fim de CADA sessão (5-10 min)

### Nível 3: Session Logs (Histórico)

- **Localização**: `docs/history/session-logs-YYYY-MM-DD.md`
- **Conteúdo**: Tarefas executadas, problemas, decisões, métricas
- **Atualização**: Ao fim de cada sessão (10-15 min)

---

## [WARN] RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação | Contingência |

|-------|---------------|---------|-----------|--------------|

| FASE 1 bloqueia tudo | Baixa | Alto | Priorizar FASE 1 100% | Rollback para SQLite local (+2-3h) |

| Prompts inadequados | Média | Médio | Iterar em Checkpoint 2 | A/B test 2-3 variações (+3-4h) |

| Ferramentas complexas | Média | Médio | Simplicidade primeiro | Reduzir de 7 para 3 tools (-6-8h) |

| Brightdata irrelevante | Baixa | Baixo | Queries estruturadas | Usar apenas RAG interno (sem impacto) |

| Tempo ultrapassar | Média | Médio | Checkpoints frequentes | Pular FASE 5 (-11-14h) |

**Cenário Worst-Case**: 19 sessões + 8h contingência = 21 sessões (~5 semanas)

**Cenário Best-Case**: 15 sessões (~3.5 semanas)

**Cenário Mais Provável**: 17 sessões (~4 semanas)

---

## [EMOJI] CUSTO OPERACIONAL

### MVP (100 clientes/mês)

| Item | Free Tier | Paid (crescimento) |

|------|-----------|-------------------|

| **Mem0** | $0 (100k ops) | $29/mês (1M ops) |

| **Cloud Hosting** | $0 (Fly.io) | $5-20/mês (Railway) |

| **OpenAI** | $50-100/mês | $100-200/mês |

| **Cohere** | $20-40/mês | $40-80/mês |

| **Brightdata** | $0 | $0 |

| **TOTAL** | **$70-140/mês** | **$174-329/mês** |

### ROI vs Consultor Humano

- **Consultor humano**: R$ 8.000-32.000 por cliente (20-40h)
- **Agente**: R$ 10-25 por cliente (custo marginal)
- **ROI**: **320x a 3.200x** [EMOJI]

**Breakeven**: 1 cliente pagante/mês (R$ 500-1.000) cobre custos operacionais

---

## [EMOJI] DEPLOYMENT STRATEGY

### MVP (Local Development)

- Rodar localmente para dev + validação inicial
- Docker Compose (Qdrant local + agente)
- Beta test: 5-10 clientes conhecidos

### Deploy Fase 1 (Week 6-7 - MVP Validado)

- **Plataforma**: Fly.io (free tier: 3 VMs)
- **Qdrant**: Qdrant Cloud (free tier: 1GB)
- **Deploy**: `flyctl deploy` (Docker automático)
- **Custo**: $0 (free tiers)

### Deploy Fase 2 (Month 3-4 - 50+ clientes)

- **Plataforma**: Railway ($20/mês)
- **Qdrant**: Qdrant Cloud Pro ($25/mês)
- **Mem0**: Pro ($29/mês)
- **Custo**: $75-100/mês

### Deploy Fase 3 (Month 6+ - 500+ clientes)

- **Plataforma**: Cloud Run (serverless, auto-scaling)
- **Qdrant**: Cluster multi-node
- **Mem0**: Enterprise (self-hosted ou unlimited)
- **Custo**: $200-400/mês

---

## [EMOJI] EXPANSÕES FUTURAS (PÓS-VALIDAÇÃO MVP)

### FASE 6: Multi-Domain Knowledge (13-18h, 1-1.5 semanas)

**Trigger**: 3+ clientes pedem outro domínio (OKRs, Design Thinking)

- Curar materiais OKRs, Design Thinking, Lean Startup
- Multiple Qdrant collections
- Query Router - collection selection
- Cross-domain retrieval com RRF

### FASE 7: Supabase Integration (13-18h, 1-1.5 semanas)

**Trigger**: 50+ clientes ativos (multi-tenancy necessário)

- Supabase Auth (login/signup)
- Row-Level Security (isolamento dados)
- File Storage (PDFs, Excel exports)
- Analytics tables (metrics SQL queries)

### FASE 8-9: States Adicionais (32-40h, 3-4 semanas)

**Trigger**: Clientes pedem implementação hands-on

- SOLUTION_DESIGN state (mapa estratégico completo)
- IMPLEMENTATION state (action plans, milestones)
- MCPs adicionais (Asana, Google Calendar)

---

## [EMOJI] MÉTRICAS DE SUCESSO MVP

### Técnicas (Objetivas)

1. **Cobertura Testes**: >= 85% (89 testes: 22 existentes + 67 novos)
2. **Performance**: Time-to-First-Insight < 30 min, Memory load < 500ms
3. **Completion Rates**: Onboarding >= 80%, Discovery >= 70%, Approval >= 60%

### Qualitativas (Usuário Avalia)

4. **Diagnostic Quality**: Rating >= 4/5 (contextualizado, actionable)
5. **Facilitation Quality**: Rating >= 4/5 (ferramentas bem guiadas)
6. **Professional Output**: Rating >= 4/5 (report apresentável para board)

### Adoção (Pós-MVP Beta)

7. **Return Rate**: >= 60% (clientes retornam para sessão 2+)
8. **Tool Usage**: >= 2 ferramentas/sessão
9. **NPS**: >= 7/10 (recomendaria para outro C-level)

**Critério Sucesso Mínimo**: 7 de 9 métricas atingidas (77%)

---

## [EMOJI] APLICAÇÃO DOS 3 FRAMEWORKS

### 12-Factor Agents (5/12 aplicados - 42%)

- [OK] #3: Config in Environment (MEM0_API_KEY, CONSULTING_MODE)
- [OK] #4: Backing Services (Mem0 via factory, swappable)
- [OK] #6: Stateless Processes (estado em Mem0, agente stateless)
- [OK] #9: Human-in-the-Loop (approval workflow)
- [OK] #11: Telemetry (structured logging, metrics collector)

### Anthropic Patterns (5/5 aplicados - 100%)

- [OK] Workflows (ONBOARDING -> DISCOVERY orquestrado)
- [OK] Orchestrator-Workers (ConsultingOrchestrator + 10 agentes)
- [OK] Parallelization (Parallel research AsyncIO)
- [OK] Evaluator-Optimizer (ValidatorAgent + refinement loop)
- [OK] Simplicidade Incremental (2 states MVP, não 5!)

### OpenAI Best Practices (6/7 aplicados - 86%)

- [OK] Clear Instructions (prompts bem definidos)
- [OK] Multi-Agent (10 agentes especializados)
- [OK] Tool Use (8 ferramentas consultivas)
- [OK] Evaluation-Driven (9 métricas, 5 checkpoints)
- [OK] Human Handoff (approval workflow, feedback)
- [OK] Planning/CoT (FacilitatorAgent raciocina antes)

---

## [EMOJI] LIÇÕES ARQUITETURAIS (Atualização Contínua)

**Objetivo**: Capturar decisões técnicas e patterns validados durante implementação para orientar fases futuras.

### 1. Mem0 Eventual Consistency Pattern

**Problema**: API Mem0 é assíncrona, operações CRUD podem não ser imediatamente visíveis.

**Solução Validada**:

- Delete-then-Add pattern: `delete_all() + sleep(1) + add()` garante 1 memória por user_id
- Sleep 1s após write operations (add, update, delete)
- Mensagens contextuais ricas (evitar extraction filter)

**Quando Aplicar**: Todos os workflows que persistem/recuperam ClientProfile via Mem0

**ROI**: 100% reliability (vs 60-70% falhas intermitentes sem sleep)

**Referência**: `docs/lessons/lesson-mem0-integration-2025-10-15.md`

---

### 2. Pydantic V2 Migration Pattern

**Problema**: LangChain v0.3+ usa Pydantic V2, imports V1 deprecated.

**Solução Validada**:

- Imports: `from pydantic import BaseModel, Field` (NÃO langchain_core.pydantic_v1)
- Config: `model_config = ConfigDict(...)` (NÃO class Config:)
- Settings: `model_config = SettingsConfigDict(...)` para BaseSettings

**Quando Aplicar**: Todos os schemas Pydantic (agentes, tools, states)

**ROI**: Zero deprecation warnings, compatibilidade LangChain v0.3+

**Referência**: Memória [[memory:9969821]], LangChain oficial docs

---

### 3. Circular Imports Resolution Pattern

**Problema**: Agentes/Workflow interdependentes causam `ImportError: cannot import from partially initialized module`

**Solução Validada**:

- `from __future__ import annotations` (PEP 563 - postponed annotations)
- `from typing import TYPE_CHECKING` + imports dentro de `if TYPE_CHECKING:`
- Lazy imports em properties/métodos com cache (`@property` + `if self._agent is None`)

**Quando Aplicar**: Módulos interdependentes (workflow <-> agents, agent A <-> agent B)

**ROI**: Zero circular imports, type hints completos, IDE autocomplete funciona

**Referência**: Memória [[memory:9980685]], Stack Overflow Q39740632, PEP 484/563

---

### 4. Implementation-First Testing Methodology

**Problema**: TDD tradicional falha para APIs desconhecidas (testes baseados em assunções erradas).

**Solução Validada**:

1. `grep "def " src/module/file.py` -> Descobrir métodos disponíveis
2. `grep "def method_name" src/module/file.py -A 15` -> Ler signatures completas
3. `grep "class Schema" src/memory/schemas.py -A 30` -> Verificar schemas Pydantic
4. Escrever testes alinhados com API real (não assunções)

**Quando Aplicar**: APIs novas (tools consultivas FASE 3+), agentes novos, integrações complexas

**Quando NÃO Aplicar**: API conhecida, lógica simples (math, pure functions), refactoring

**ROI**: 30-40 min economizados por implementação (evita reescrita completa de testes)

**Referência**: Memória [[memory:9969868]] ponto 13, `docs/lessons/lesson-swot-testing-methodology-2025-10-19.md`

---

### 5. Sequential Thinking + Brightdata Proativo

**Problema**: Debugging trial-and-error desperdiça tempo, soluções não validadas pela comunidade.

**Solução Validada**:

- Sequential Thinking: 8-15 thoughts ANTES de implementar (planejamento estruturado)
- Brightdata proativo: Pesquisar durante thoughts 2-3 (não quando stuck >30 min)
- Micro-etapas: Dividir em A-H steps com validação incremental (pytest/read_lints após cada)

**Quando Aplicar**: Problemas complexos (circular imports, schemas P0, E2E workflows), debugging estruturado

**ROI**: 2.5-4x economia tempo (40-60 min debugging -> 15-20 min estruturado)

**Referência**: `docs/lessons/lesson-discovery-state-circular-import-2025-10-16.md`

---

**ROI Combinado Lições**: ~10-15h economizadas em FASE 3+ (patterns reutilizáveis aplicados)

---

## [EMOJI] PRÓXIMOS PASSOS

### Decisão Imediata

**Usuário aprova plano v2.0?** -> SIM / NÃO / AJUSTES

### Se Aprovado, Criar:

1. `.cursor/progress/consulting-progress.md` (tracker dinâmico)
2. `docs/decisions/001-memory-mem0.md` (ADR: Por que Mem0)
3. `docs/decisions/002-mvp-scope-bsc.md` (ADR: Por que BSC-only)
4. `docs/decisions/003-cloud-flyio.md` (ADR: Por que Fly.io)
5. `docs/consulting/workflow-design.md` (States, transitions)
6. `docs/consulting/tools-guide.md` (8 ferramentas)
7. `docs/consulting/metrics-definition.md` (9 métricas)

### Primeira Ação Técnica (FASE 1.1)

- **Quando**: Após aprovação (próxima sessão)
- **Duração**: 30-45 min
- **Ação**: Research Mem0 Platform (free tier vs paid, API vs self-hosted)
- **Entrega**: docs/decisions/001-memory-mem0.md
- **Validação**: Confirmar Platform free tier suficiente para MVP

---

**Status Atual**: ⏳ Aguardando aprovação do usuário

**Última Atualização**: 2025-10-15 23:30

**Versão**: 2.0 (Mem0 + BSC-only + Cloud-Native)
