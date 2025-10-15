# 🎯 PLANO: Transformação em Agente Consultor Empresarial BSC v2.0

**Data**: 2025-10-15

**Status**: Aprovação Pendente

**Versão**: 2.0 (Atualizado com Mem0 + Deploy Nuvem)

---

## 📋 EXECUTIVE SUMMARY

### Objetivo

Transformar **Agente BSC RAG** (pergunta-resposta sobre literatura BSC) em **Agente Consultor Empresarial BSC** (facilitador de processo consultivo estruturado com C-level).

### Decisões Estratégicas Confirmadas

- ✅ **Memória**: Mem0 Platform (self-improving LLM memory, não Supabase inicialmente)
- ✅ **Escopo MVP**: Foco BSC exclusivo (multi-domain pós-validação)
- ✅ **Deploy**: Nuvem pós-validação (Fly.io free tier → Railway → Cloud Run)
- ✅ **Frameworks**: 12-Factor Agents + Anthropic Patterns + OpenAI Best Practices

### Esforço Estimado MVP

- **Micro-tarefas**: 48 (5 fases)
- **Horas**: 59-75h (15-19 sessões de 3-4h)
- **Timeline**: 4-5 semanas (sessões diárias)
- **Custo Operacional**: $70-140/mês (Mem0 + Cloud + APIs)

### Aproveitamento do Existente

- **RAG Core**: 100% reutilizado (retriever, embeddings, vector store, 4 agentes especialistas)
- **LangGraph**: 70% reutilizado (expandir states, manter orchestrator)
- **Infrastructure**: 90% reutilizado (config, logging, testing, Docker)
- **Novo Desenvolvimento**: 30% (~5.000-7.000 linhas código)

---

## 🏗️ ARCHITECTURE OVERVIEW

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
│  Deploy: Local (dev) → Fly.io (prod)             │
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

## 📊 FASES DO MVP (48 MICRO-TAREFAS)

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

**Objetivo**: Workflow ONBOARDING → DISCOVERY → APPROVAL

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

### FASE 3: DIAGNOSTIC TOOLS - Ferramentas Consultivas (12 tarefas, 16-20h, 5-6 sessões)

**Objetivo**: Co-criação de análises estratégicas (SWOT, 5 Whys, KPIs)

| ID | Tarefa | Duração | Entregável |

|----|--------|---------|------------|

| 3.1 | FacilitatorAgent | 1.5-2h | facilitator_agent.py (guia ferramentas) |

| 3.2 | ValidatorAgent | 1.5-2h | validator_agent.py (avalia qualidade) |

| 3.3 | SWOT_Builder | 2-2.5h | swot_builder.py (4 quadrantes estruturados) |

| 3.4 | FiveWhys_Facilitator | 1.5-2h | five_whys.py (root cause analysis) |

| 3.5 | IssueTree_Analyzer | 2h | issue_tree.py (problema → sub-problemas) |

| 3.6 | KPI_Definer | 2h | kpi_definer.py (template SMART) |

| 3.7 | Evaluator-Optimizer Loop | 1.5h | evaluator_loop.py (iteração até qualidade) |

| 3.8 | Tools LangGraph Integration | 1.5h | consulting_workflow.py (adicionar tools) |

| 3.9 | Tool Selection Logic | 1h | orchestrator.py (sugerir tool adequado) |

| 3.10 | Planning CoT | 1h | facilitator_cot_prompt.py |

| 3.11 | Persist Tool Outputs | 1h | mem0_client.py (save outputs) |

| 3.12 | Testes E2E Tools | 1.5-2h | test_diagnostic_tools.py (20+ testes) |

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

## ✅ VALIDAÇÃO CONTÍNUA (5 Checkpoints)

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

## 📂 SISTEMA DE PROGRESS TRACKING

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

## ⚠️ RISCOS E MITIGAÇÕES

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

## 💰 CUSTO OPERACIONAL

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
- **ROI**: **320x a 3.200x** 🚀

**Breakeven**: 1 cliente pagante/mês (R$ 500-1.000) cobre custos operacionais

---

## 🚀 DEPLOYMENT STRATEGY

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

## 🔮 EXPANSÕES FUTURAS (PÓS-VALIDAÇÃO MVP)

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

## 🎯 MÉTRICAS DE SUCESSO MVP

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

## 📋 APLICAÇÃO DOS 3 FRAMEWORKS

### 12-Factor Agents (5/12 aplicados - 42%)

- ✅ #3: Config in Environment (MEM0_API_KEY, CONSULTING_MODE)
- ✅ #4: Backing Services (Mem0 via factory, swappable)
- ✅ #6: Stateless Processes (estado em Mem0, agente stateless)
- ✅ #9: Human-in-the-Loop (approval workflow)
- ✅ #11: Telemetry (structured logging, metrics collector)

### Anthropic Patterns (5/5 aplicados - 100%)

- ✅ Workflows (ONBOARDING → DISCOVERY orquestrado)
- ✅ Orchestrator-Workers (ConsultingOrchestrator + 10 agentes)
- ✅ Parallelization (Parallel research AsyncIO)
- ✅ Evaluator-Optimizer (ValidatorAgent + refinement loop)
- ✅ Simplicidade Incremental (2 states MVP, não 5!)

### OpenAI Best Practices (6/7 aplicados - 86%)

- ✅ Clear Instructions (prompts bem definidos)
- ✅ Multi-Agent (10 agentes especializados)
- ✅ Tool Use (8 ferramentas consultivas)
- ✅ Evaluation-Driven (9 métricas, 5 checkpoints)
- ✅ Human Handoff (approval workflow, feedback)
- ✅ Planning/CoT (FacilitatorAgent raciocina antes)

---

## 🎬 PRÓXIMOS PASSOS

### Decisão Imediata

**Usuário aprova plano v2.0?** → SIM / NÃO / AJUSTES

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