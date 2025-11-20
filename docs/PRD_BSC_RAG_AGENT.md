# [EMOJI] PRD - Agente BSC RAG (Product Requirements Document)

**Versão**: 1.0  
**Data Criação**: 2025-11-20  
**Última Atualização**: 2025-11-20  
**Status**: Aprovado - Opção B (Integração Completa)

---

## [EMOJI] EXECUTIVE SUMMARY

### Product Vision

**Missão**: Democratizar a implementação do Balanced Scorecard (BSC) através de um agente consultivo inteligente baseado em AI, tornando estratégia empresarial acessível para empresas de 50-500 funcionários.

**Problema**: Consultoria BSC tradicional custa R$50-150K e demora 3-6 meses. Empresas médias não têm acesso a expertise estratégica de qualidade.

**Solução**: Agente AI consultivo que:
- Conduz onboarding conversacional inteligente
- Realiza diagnóstico BSC completo em 5-10 minutos
- Gera Strategy Map visual e alinhado
- Cria Action Plans executáveis com milestones
- Integra com ferramentas de produtividade (Asana, Calendar)

**Usuários-Alvo**:
- **Primary**: Consultores BSC independentes (aumentar escala 10x)
- **Secondary**: Empresas 50-500 funcionários (acesso direto a expertise BSC)
- **Tertiary**: PMOs e Gerentes de Projetos (implementação estratégica)

---

## [EMOJI] PRODUCT GOALS

### Objetivos de Negócio

1. **Democratizar BSC**: Tornar consultoria BSC acessível financeiramente (custo 90% menor)
2. **Escalar Consultores**: Permitir consultores atenderem 10x mais clientes simultaneamente
3. **Qualidade Consistente**: Garantir diagnósticos BSC sempre completos e alinhados com literatura

### Objetivos de Produto

1. **Experiência Conversacional**: Onboarding natural e intuitivo (7-10 perguntas, 5-8 min)
2. **Diagnóstico Completo**: 100% diagnósticos usam 7 ferramentas consultivas (SWOT, Five Whys, KPIs, etc)
3. **Estratégia Acionável**: Strategy Maps com 0 gaps de alinhamento
4. **Implementação Guiada**: Action Plans com milestones, responsáveis e prazos
5. **Integração Seamless**: Exportar para Asana/Calendar com 1 clique

---

## [EMOJI] USER PERSONAS

### Persona 1: Ricardo - Consultor BSC Independente

**Demografia**:
- Idade: 42 anos
- Formação: MBA em Gestão Estratégica
- Experiência: 15 anos em consultoria BSC
- Faturamento: R$30-50K/mês (2-3 clientes simultâneos)

**Pain Points**:
- Tempo dedicado a diagnóstico inicial (40-60h por cliente)
- Dificuldade em escalar atendimento (limitado a 3 clientes/mês)
- Clientes menores (50-100 funcionários) não pagam consultoria full

**Jobs-to-be-Done**:
- Reduzir tempo de diagnóstico de 40h para 5h (review do agente)
- Atender 10-15 clientes/mês ao invés de 2-3
- Oferecer serviço "lite" para clientes menores (margem maior)

**Success Criteria**:
- Diagnóstico AI tem 90%+ qualidade vs manual
- Economiza 35h por cliente
- Pode cobrar R$5-10K vs R$50K (volume compensa)

---

### Persona 2: Ana - Gerente de PMO em Empresa Média

**Demografia**:
- Idade: 35 anos
- Formação: Engenharia + MBA
- Empresa: Manufatura, 200 funcionários
- Orçamento: R$20-30K para consultoria estratégica

**Pain Points**:
- Orçamento não cobre consultoria BSC tradicional (R$80-120K)
- CEO cobra implementação de BSC mas sem budget
- Tentou implementar BSC sozinha mas ficou confuso e incompleto

**Jobs-to-be-Done**:
- Criar Strategy Map BSC profissional sem contratar consultor
- Validar se Strategy Map está alinhado (não quer errar)
- Ter guia passo-a-passo de implementação

**Success Criteria**:
- Strategy Map gerado em <1 dia vs 3-4 semanas tentando sozinha
- Validação automática de alinhamento (0 gaps)
- Action Plan com milestones claros para apresentar ao CEO

---

### Persona 3: João - CEO de Startup em Crescimento

**Demografia**:
- Idade: 38 anos
- Formação: Engenharia + Startup experience
- Empresa: SaaS B2B, 80 funcionários, crescimento 3x/ano
- Pain: Crescimento rápido sem estratégia clara

**Pain Points**:
- Time executivo desalinhado (cada um puxa para um lado)
- Métricas espalhadas (20+ dashboards, nenhum conectado)
- Investidor cobra "pensamento estratégico" mas não sabe por onde começar

**Jobs-to-be-Done**:
- Alinhar time executivo em torno de estratégia clara
- Conectar métricas operacionais com objetivos estratégicos
- Criar cultura de execução estratégica (OKRs alinhados com BSC)

**Success Criteria**:
- Time executivo entende Strategy Map em 1 reunião (visual claro)
- KPIs atuais mapeados para objetivos BSC
- Revisões estratégicas trimestrais estruturadas

---

## [EMOJI] FEATURE REQUIREMENTS

### FASE 1-4: IMPLEMENTADAS (92% completo - 46/50 tarefas)

#### FASE 1: Onboarding Agent [OK]

**Descrição**: Conversação natural para coletar contexto do cliente.

**Features Implementadas**:
- Conversação multi-turn (7-10 perguntas)
- Extração de entidades (empresa, setor, porte, desafios, objetivos)
- Validação e confirmação de informações
- Persistência em Mem0 (multi-client)

**User Story**: 
> "Como consultor, quero que o agente conduza onboarding natural para que o cliente não perceba que está falando com AI."

**Acceptance Criteria**:
- [x] Conversação natural (não parece formulário)
- [x] 7-10 perguntas adaptativas
- [x] Validação antes de prosseguir
- [x] Profile salvo em Mem0

---

#### FASE 2A: RAG Avançado [OK]

**Descrição**: Técnicas RAG avançadas para melhorar qualidade das respostas.

**Features Implementadas**:
- Query Decomposition (queries complexas -> sub-queries)
- Adaptive Re-ranking (diversity + metadata boost)
- Router Inteligente (otimiza latência por tipo de query)

**User Story**:
> "Como usuário, quero respostas precisas e completas para que minhas decisões estratégicas sejam embasadas."

**Acceptance Criteria**:
- [x] Recall@10: +30-40% vs baseline
- [x] Latência: -20% média (routing inteligente)
- [x] Answer quality: +30-50% (query decomposition)

---

#### FASE 3: Ferramentas Consultivas [OK]

**Descrição**: 7 ferramentas consultivas estruturadas.

**Features Implementadas**:
1. SWOT Analysis (4 quadrantes)
2. Five Whys (root cause analysis)
3. KPI Definer (framework completo)
4. Strategic Objectives (SMART)
5. Benchmarking (comparação com mercado)
6. Issue Tree (decomposição de problemas)
7. Prioritization Matrix (Impact/Effort)

**User Story**:
> "Como consultor, quero ferramentas estruturadas para que diagnósticos tenham qualidade consistente."

**Acceptance Criteria**:
- [x] 7 ferramentas implementadas e testadas
- [x] Outputs estruturados (Pydantic schemas)
- [x] Documentação completa de cada ferramenta

**GAP IDENTIFICADO (Nov 2025)**:
- [ERRO] Ferramentas NÃO integradas ao fluxo de diagnóstico
- [ERRO] DiagnosticAgent não chama ferramentas automaticamente
- [ERRO] 70% do valor da FASE 3 desperdiçado
- [OK] **SPRINT 1 resolverá este gap**

---

#### FASE 4: Advanced Features [OK]

**Descrição**: Features de produção e qualidade.

**Features Implementadas**:
- Judge Context-Aware (avalia qualidade com contexto)
- Performance Monitoring (tracking de métricas)
- Multi-Client Dashboard (gerenciamento de clientes)
- Reports & Exports (geração de reports)
- Integration APIs (REST APIs)
- LangChain v1.0 Migration (atualização de deps)

**User Story**:
> "Como administrador, quero monitorar qualidade do sistema para garantir diagnósticos confiáveis."

**Acceptance Criteria**:
- [x] Judge avalia 100% respostas
- [x] Performance dashboard funcional
- [x] Multi-client suportado (Mem0)
- [x] Exports em PDF/Markdown

---

### FASE 5: SOLUTION_DESIGN (NOVO - Sprint 2-3)

**Descrição**: Converter diagnóstico em Strategy Map visual e alinhado.

**Status**: [EMOJI] A IMPLEMENTAR (4 semanas)

**Features Planejadas**:

#### Feature 5.1: Strategy Map Designer

**Descrição**: Ferramenta que converte diagnóstico em Strategy Map com objetivos e KPIs nas 4 perspectivas.

**User Story**:
> "Como consultor, quero converter diagnóstico em Strategy Map visual para que cliente visualize estratégia claramente."

**Acceptance Criteria**:
- [ ] Strategy Map tem 4 perspectivas balanceadas
- [ ] Cada perspectiva tem 2-4 objetivos estratégicos
- [ ] Cada objetivo tem 1-3 KPIs mensuráveis
- [ ] Conexões causa-efeito mapeadas entre perspectivas
- [ ] Latência geração <2 min

**Dependencies**:
- Reutiliza StrategicObjectivesTool (FASE 3)
- Reutiliza KPIDefinerTool (FASE 3)

**Prioridade**: [EMOJI] ALTA

---

#### Feature 5.2: Alignment Validator

**Descrição**: Valida se Strategy Map está balanceado e completo.

**User Story**:
> "Como usuário, quero validação automática de alinhamento para garantir que Strategy Map está correto."

**Acceptance Criteria**:
- [ ] Detecta 5 tipos de gaps (perspectiva sem objetivos, objetivo sem KPI, etc)
- [ ] Report estruturado com score 0-100
- [ ] Recomendações de correção específicas
- [ ] 0 gaps em 80% dos casos

**Validações Implementadas**:
1. Todas 4 perspectivas têm ≥2 objetivos
2. Cada objetivo tem ≥1 KPI
3. Conexões causa-efeito entre perspectivas existem
4. Não há objetivos "isolados" (sem conexões)
5. KPIs são mensuráveis (SMART)

**Prioridade**: [EMOJI] ALTA

---

#### Feature 5.3: KPI Alignment Checker

**Descrição**: Verifica se KPIs estão alinhados com objetivos.

**User Story**:
> "Como gerente de PMO, quero KPIs alinhados com objetivos para garantir métricas corretas."

**Acceptance Criteria**:
- [ ] Cada KPI tem objetivo pai válido
- [ ] KPI é mensurável (SMART)
- [ ] KPI não é duplicado
- [ ] KPI não é "órfão" (sem objetivo)
- [ ] 100% KPIs validados

**Prioridade**: MÉDIA

---

#### Feature 5.4: Cause-Effect Mapper

**Descrição**: Mapeia relações causa-efeito entre objetivos de diferentes perspectivas.

**User Story**:
> "Como consultor, quero visualizar conexões causa-efeito para explicar lógica estratégica ao cliente."

**Acceptance Criteria**:
- [ ] Grafo de conexões mapeado
- [ ] Força da relação calculada (0-100)
- [ ] Visualização interativa (grafo)
- [ ] Mapa tem ≥6 conexões entre perspectivas

**Exemplo de Conexão**:
```
Learning: "Treinar equipe em vendas consultivas"
    ↓ (força: 85%)
Process: "Melhorar processo de vendas"
    ↓ (força: 75%)
Customer: "Aumentar satisfação de clientes"
    ↓ (força: 90%)
Financial: "Aumentar receita recorrente"
```

**Prioridade**: MÉDIA

---

#### Feature 5.5: Strategy Map UI Interativa

**Descrição**: UI Streamlit para visualizar e editar Strategy Map.

**User Story**:
> "Como consultor, quero editar Strategy Map manualmente para customizar estratégia ao contexto específico do cliente."

**Acceptance Criteria**:
- [ ] Visualização de 4 perspectivas em cards
- [ ] Mostrar objetivos e KPIs de cada perspectiva
- [ ] Editar objetivos (adicionar/remover/modificar)
- [ ] Editar KPIs (adicionar/remover/modificar)
- [ ] Visualizar grafo causa-efeito (interativo)
- [ ] Validar alinhamento em tempo real

**Prioridade**: MÉDIA

---

### FASE 6: IMPLEMENTATION (NOVO - Sprint 4)

**Descrição**: Converter Strategy Map em Action Plans executáveis.

**Status**: [EMOJI] A IMPLEMENTAR (2-3 semanas)

**Features Planejadas**:

#### Feature 6.1: Action Plan Generator

**Descrição**: Ferramenta que converte Strategy Map em Action Plans com milestones, responsáveis e prazos.

**User Story**:
> "Como gerente de PMO, quero action plans detalhados para executar estratégia passo-a-passo."

**Acceptance Criteria**:
- [ ] Action Plans têm 3-5 milestones por objetivo
- [ ] Cada milestone tem responsável (role, não nome)
- [ ] Cada milestone tem prazo (30/60/90 dias)
- [ ] Cada milestone tem status (todo/in progress/done)
- [ ] Latência geração <3 min

**Output Esperado**:
```
Objetivo: "Aumentar receita recorrente 30%"
Perspectiva: Financial

Action Plan:
  Milestone 1: "Implementar modelo de precificação por valor"
    Responsável: CFO
    Prazo: 30 dias
    Status: todo
    
  Milestone 2: "Treinar time comercial em upsell/cross-sell"
    Responsável: Diretor Comercial
    Prazo: 45 dias
    Status: todo
    
  Milestone 3: "Lançar programa de fidelidade"
    Responsável: CMO
    Prazo: 90 dias
    Status: todo
```

**Prioridade**: [EMOJI] ALTA

---

#### Feature 6.2: Milestone Tracker

**Descrição**: Tracking de progresso de cada milestone.

**User Story**:
> "Como CEO, quero acompanhar progresso de milestones para garantir execução estratégica."

**Acceptance Criteria**:
- [ ] Marcar milestone como "todo", "in_progress", "done"
- [ ] Calcular % de progresso por perspectiva
- [ ] Alertas de milestones atrasados
- [ ] Timeline visual de milestones
- [ ] Filtros por perspectiva/responsável

**Prioridade**: ALTA

---

#### Feature 6.3: MCP Asana Integration (OPCIONAL)

**Descrição**: Criar tasks no Asana a partir de Action Plans.

**User Story**:
> "Como gerente de projetos, quero exportar action plans para Asana para gerenciar execução na ferramenta que já uso."

**Acceptance Criteria**:
- [ ] Criar projeto Asana por perspectiva
- [ ] Criar task por milestone
- [ ] Sincronizar status (bidirecional)
- [ ] Webhook para updates em tempo real
- [ ] 100% action plans podem ser exportados

**Prioridade**: BAIXA (opcional)

---

#### Feature 6.4: MCP Google Calendar Integration (OPCIONAL)

**Descrição**: Criar meetings no Google Calendar para milestones.

**User Story**:
> "Como executivo, quero reuniões de revisão agendadas automaticamente para acompanhar progresso."

**Acceptance Criteria**:
- [ ] Criar meeting para cada milestone (revisão)
- [ ] Sincronizar datas de prazo
- [ ] Enviar convites para responsáveis
- [ ] Alertas 1 semana antes do prazo

**Prioridade**: BAIXA (opcional)

---

#### Feature 6.5: Progress Dashboard

**Descrição**: Dashboard visual de progresso por perspectiva.

**User Story**:
> "Como CEO, quero dashboard de progresso para apresentar em reuniões de board."

**Acceptance Criteria**:
- [ ] Gráfico de progresso por perspectiva (% concluído)
- [ ] Timeline de milestones
- [ ] Alertas de milestones atrasados (destaque vermelho)
- [ ] Filtros por perspectiva/responsável
- [ ] Export para PDF (apresentação)

**Prioridade**: MÉDIA

---

## [EMOJI] TECHNICAL REQUIREMENTS

### Architecture

**Stack Tecnológico**:
- Backend: Python 3.12, LangChain v1.0, LangGraph
- LLMs: GPT-5 (complexo), GPT-5 mini (simples), Claude Sonnet 4.5 (contextual)
- Vector DB: Chroma (embeddings OpenAI ada-002)
- Memory: Mem0 API v2 (multi-client)
- UI: Streamlit
- MCPs: Asana, Google Calendar (FASE 6)

**Componentes**:
```
┌─────────────────────────────────────────┐
│         Streamlit UI (app.py)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│    LangGraph Workflow (workflow.py)     │
│  ┌────────────────────────────────────┐ │
│  │ Nodes:                             │ │
│  │ - onboarding()                     │ │
│  │ - discovery()  [FASE 1-4]          │ │
│  │ - design_solution()  [FASE 5 NEW]  │ │
│  │ - generate_action_plans() [FASE 6] │ │
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Agents & Tools                  │
│  ┌────────────────────────────────────┐ │
│  │ DiagnosticAgent [7 tools]          │ │
│  │ Strategy_Map_Designer_Tool [NEW]   │ │
│  │ Action_Plan_Generator_Tool [NEW]   │ │
│  │ Alignment_Validator_Tool [NEW]     │ │
│  └────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     Data Layer (Schemas + Memory)       │
│  ┌────────────────────────────────────┐ │
│  │ Pydantic Schemas:                  │ │
│  │ - ClientProfile                    │ │
│  │ - CompleteDiagnostic               │ │
│  │ - DiagnosticToolsResult [NEW]      │ │
│  │ - StrategyMap [NEW]                │ │
│  │ - ActionPlan [NEW]                 │ │
│  │                                    │ │
│  │ Memory: Mem0 API v2                │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

### Data Schemas (Pydantic)

#### Existing Schemas [OK]

```python
# src/memory/schemas.py

class CompanyInfo(BaseModel):
    """Informações da empresa."""
    name: str
    sector: str
    size: Literal["pequena", "média", "grande"]

class StrategicContext(BaseModel):
    """Contexto estratégico do cliente."""
    current_challenges: List[str]  # 3-5 desafios
    strategic_goals: List[str]     # 3-5 objetivos

class ClientProfile(BaseModel):
    """Profile completo do cliente."""
    company: CompanyInfo
    context: StrategicContext
    metadata: dict

class CompleteDiagnostic(BaseModel):
    """Diagnóstico BSC completo."""
    executive_summary: str
    perspectives: List[DiagnosticResult]  # 4 perspectivas
    recommendations: List[Recommendation]  # Priorizadas HIGH/MEDIUM/LOW
```

---

#### New Schemas (FASE 5-6) [EMOJI]

```python
# src/memory/schemas.py

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

class StrategicObjective(BaseModel):
    """Objetivo estratégico SMART."""
    id: str
    perspective: Literal["financial", "customer", "process", "learning"]
    description: str
    kpis: List[KPI]
    
class KPI(BaseModel):
    """Key Performance Indicator."""
    id: str
    name: str
    description: str
    target: float
    unit: str
    measurement_frequency: Literal["daily", "weekly", "monthly", "quarterly"]

class CauseEffectConnection(BaseModel):
    """Conexão causa-efeito entre objetivos."""
    from_objective_id: str
    to_objective_id: str
    strength: float  # 0-100
    rationale: str

class StrategyMap(BaseModel):
    """Strategy Map BSC completo."""
    financial_objectives: List[StrategicObjective]
    customer_objectives: List[StrategicObjective]
    process_objectives: List[StrategicObjective]
    learning_objectives: List[StrategicObjective]
    
    cause_effect_connections: List[CauseEffectConnection]
    
    created_at: datetime
    validated: bool
    alignment_score: float  # 0-100

class Milestone(BaseModel):
    """Milestone de Action Plan."""
    id: str
    description: str
    responsible_role: str  # Role, não nome
    deadline_days: int     # Dias a partir de hoje
    status: Literal["todo", "in_progress", "done"]
    dependencies: List[str]  # IDs de milestones dependentes

class ActionPlan(BaseModel):
    """Action Plan para um objetivo estratégico."""
    objective_id: str
    perspective: Literal["financial", "customer", "process", "learning"]
    milestones: List[Milestone]
    
    created_at: datetime
    total_milestones: int
    completed_milestones: int
    progress_percentage: float  # 0-100
```

---

### Performance Requirements

**Latência (P95)**:
- Onboarding: <3s por interação
- Diagnóstico completo (com 7 ferramentas): <5 min
- Strategy Map generation: <2 min
- Action Plans generation: <3 min

**Throughput**:
- 10 diagnósticos simultâneos (multi-client)
- 100 queries RAG/min

**Availability**:
- 99% uptime (允許 7h downtime/mês)

**Storage**:
- Mem0: 1000 clientes, 10MB/cliente = 10GB
- Chroma: 10,000 chunks, 1.5KB/chunk = 15MB

---

### Quality Requirements

**Métricas de Qualidade**:

**Diagnóstico**:
- Judge Approval Rate: >80%
- Answer Relevancy (RAGAS): >0.85
- Faithfulness (RAGAS): >0.90
- 100% diagnósticos usam 7 ferramentas consultivas (SPRINT 1)

**Strategy Map**:
- 0 gaps de alinhamento em 80% casos
- 4 perspectivas balanceadas (cada com ≥2 objetivos)
- ≥6 conexões causa-efeito entre perspectivas

**Action Plans**:
- 3-5 milestones por objetivo
- 100% milestones têm responsável e prazo
- Latência geração <3 min

---

### Security Requirements

**Autenticação**:
- Mem0 API Key (env var)
- OpenAI API Key (env var)
- Cohere API Key (env var)

**Data Privacy**:
- Dados de cliente armazenados APENAS em Mem0 (LGPD compliant)
- Zero logs com informações sensíveis
- Exports em PDF/Markdown protegidos por senha (opcional)

**API Rate Limiting**:
- OpenAI: 10,000 RPM (GPT-5 mini), 500 RPM (GPT-5)
- Mem0: 1000 requests/min
- Cohere: 10,000 requests/min

---

## [EMOJI] SUCCESS METRICS

### Business Metrics

**Consultores (Persona 1)**:
- [OK] Redução de 40h -> 5h por diagnóstico (economia 35h)
- [OK] Aumento de 3 -> 12 clientes/mês (4x capacity)
- [OK] ROI: 300% (economia de tempo vs custo da ferramenta)

**Empresas (Persona 2 e 3)**:
- [OK] Custo R$80K -> R$5K (redução 94%)
- [OK] Tempo 3-6 meses -> 1 semana (redução 95%)
- [OK] Acesso a expertise BSC profissional (antes inacessível)

---

### Product Metrics

**Adoção**:
- 100 clientes onboardados em 3 meses
- 80% taxa de conclusão de diagnóstico
- 60% taxa de uso de Strategy Map
- 40% taxa de uso de Action Plans

**Qualidade**:
- Judge Approval Rate: >80%
- Answer Relevancy (RAGAS): >0.85
- Strategy Maps com 0 gaps: >80%
- User satisfaction (NPS): >50

**Performance**:
- Latência P95 diagnóstico: <5 min
- Latência P95 Strategy Map: <2 min
- Latência P95 Action Plans: <3 min
- 99% uptime

---

### User Satisfaction Metrics

**Net Promoter Score (NPS)**:
- Target: >50 (good)
- Stretch: >70 (excellent)

**Feature Adoption**:
- Onboarding: 100% (obrigatório)
- Diagnóstico: 90% (core feature)
- Strategy Map: 60% (FASE 5)
- Action Plans: 40% (FASE 6)
- MCP Integrations: 20% (optional)

**Time-to-Value**:
- Onboarding completado: <10 min
- Diagnóstico recebido: <15 min total
- Strategy Map gerado: <20 min total
- Action Plans criados: <30 min total

---

## [EMOJI] ROADMAP

### FASE 1-4: COMPLETADA (Nov 2025) [OK]

**Progresso**: 92% (46/50 tarefas)

**Features Entregues**:
- Onboarding conversacional
- Diagnóstico BSC (4 perspectivas)
- 7 ferramentas consultivas
- Judge Context-Aware
- Multi-Client Dashboard
- LangChain v1.0 Migration

**Gap Identificado**: Ferramentas não integradas ao diagnóstico (GAP #2)

---

### FASE 5: SOLUTION_DESIGN (4 semanas) [EMOJI]

**Sprint 1 (Semana 1)**: Integração Ferramentas no Diagnóstico (GAP #2)
- Refatorar run_diagnostic() para chamar 7 ferramentas
- Criar DiagnosticToolsResult schema
- Testes E2E completos
- **Prioridade**: [EMOJI] CRÍTICA

**Sprint 2 (Semana 2)**: Strategy Map MVP
- Implementar Strategy_Map_Designer_Tool
- Implementar Alignment_Validator_Tool
- Criar node design_solution()
- UI básica para Strategy Map
- **Prioridade**: [EMOJI] ALTA

**Sprint 3 (Semana 3)**: Validações Avançadas
- Implementar KPI_Alignment_Checker
- Implementar Cause_Effect_Mapper
- UI interativa para edição de Strategy Map
- **Prioridade**: MÉDIA

---

### FASE 6: IMPLEMENTATION (2-3 semanas) [EMOJI]

**Sprint 4 (Semana 4)**: Action Plans MVP
- Implementar Action_Plan_Generator_Tool
- Implementar Milestone_Tracker_Tool
- Criar node generate_action_plans()
- UI para visualização de Action Plans
- **Prioridade**: ALTA

**Sprint 5-6 (Semanas 5-6)**: MCPs + Dashboard (OPCIONAL)
- MCP Asana Integration
- MCP Google Calendar Integration
- Progress Dashboard
- **Prioridade**: BAIXA (condicional)

---

### FASE 7: PRODUCTION & SCALE (Futuro) [EMOJI]

**Planejado** (não detalhado ainda):
- Docker Containerization
- CI/CD Pipeline
- Monitoring & Logging (Datadog/New Relic)
- Security Hardening
- Load Testing (1000 users simultâneos)
- Multi-language Support (inglês + português)

---

## [EMOJI] NEXT STEPS

**HOJE (Sessão 36 - Nov 20, 2025)**:
- [OK] Criar este PRD
- [OK] Criar SPRINT_PLAN_OPÇÃO_B.md
- [OK] Atualizar consulting-progress.md
- [OK] Atualizar documentação técnica (ARCHITECTURE.md, LANGGRAPH_WORKFLOW.md)

**PRÓXIMA SESSÃO (Sessão 37)**:
- [EMOJI] **COMEÇAR SPRINT 1** - Integração Ferramentas no Diagnóstico (GAP #2)
- Executar baseline E2E ANTES de qualquer mudança
- Implementar Tarefa 1.1 (refatorar run_diagnostic)

---

## [EMOJI] REFERENCES

**Literatura BSC**:
- Kaplan & Norton - The Balanced Scorecard (1996)
- Kaplan & Norton - The Strategy-Focused Organization (2000)
- Kaplan & Norton - The Execution Premium (2008)

**AI/RAG Research**:
- Self-RAG: Learning to Retrieve, Generate, and Critique (2023)
- CRAG: Corrective Retrieval Augmented Generation (2024)
- Anthropic Contextual Retrieval (2024)

**Implementação**:
- LangChain Docs v1.0 (2025)
- LangGraph Tutorial (2025)
- Mem0 API Docs v2 (2025)

---

**Última Atualização**: 2025-11-20  
**Status**: [OK] APROVADO - Opção B (Integração Completa)  
**Próximo Review**: Pós-Sprint 2 (após Strategy Map MVP)

