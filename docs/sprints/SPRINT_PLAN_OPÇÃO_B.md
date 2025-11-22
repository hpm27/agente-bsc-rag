# [EMOJI] SPRINT PLAN - Opção B (Integração Completa)

**Versão**: 1.0
**Data Criação**: 2025-11-20
**Método**: Sequential Thinking (10 thoughts)
**Decisão**: Implementar SOLUTION_DESIGN + IMPLEMENTATION + GAP #2 (Integração Ferramentas)

---

## [EMOJI] EXECUTIVE SUMMARY

### Decisão do Usuário

**ESCOPO APROVADO:**
- [OK] **Opção B**: Integração Completa SOLUTION_DESIGN + IMPLEMENTATION (4-6 semanas)
- [OK] **GAP #2**: Integrar 7 ferramentas consultivas no DiagnosticAgent (prioridade crítica)
- [OK] **Documentação**: Atualizar tracking completo + criar PRD

**SPRINTS PLANEJADOS:**
- **Sprints 1-4**: OBRIGATÓRIOS (MVP funcional) - 4 semanas
- **Sprints 5-6**: OPCIONAIS (nice-to-have) - 2 semanas

**ESFORÇO TOTAL:**
- MVP (Sprints 1-4): 76-102h (10-13 dias úteis)
- Completo (Sprints 1-6): 110-146h (14-19 dias úteis)

---

## [EMOJI] ROADMAP VISUAL

### Dependency Graph

```
SPRINT 1 (Ferramentas no Diagnóstico) - CRÍTICO
    ↓
SPRINT 2 (Strategy Map MVP) - ALTO
    ↓
SPRINT 3 (Validações Avançadas) - MÉDIO
    ↓
SPRINT 4 (Action Plans MVP) - ALTO
    ↓
SPRINT 5-6 (MCPs + Dashboard) - BAIXO (OPCIONAL)
```

### Timeline Semanal

```
Semana 1: [=== SPRINT 1 ===] Ferramentas no Diagnóstico
Semana 2: [=== SPRINT 2 ===] Strategy Map MVP
Semana 3: [=== SPRINT 3 ===] Validações Avançadas
Semana 4: [=== SPRINT 4 ===] Action Plans MVP
Semana 5: [===== SPRINT 5-6 =====] MCPs (OPCIONAL)
Semana 6: [===== SPRINT 5-6 =====] Dashboard (OPCIONAL)
```

---

## [EMOJI] SPRINT 1 - Ferramentas no Diagnóstico (GAP #2)

### Objetivo

**Resolver GAP CRÍTICO #2**: DiagnosticAgent deve usar TODAS as 7 ferramentas consultivas implementadas na FASE 3.

**Situação Atual:**
- [ERRO] `run_diagnostic()` usa APENAS 4 agentes BSC + RAG + consolidação LLM
- [ERRO] 7 ferramentas consultivas implementadas mas NUNCA chamadas
- [ERRO] 70% do valor da FASE 3 desperdiçado

**Situação Desejada:**
- [OK] `run_diagnostic()` chama TODAS as 7 ferramentas em paralelo
- [OK] Diagnóstico rico e estruturado (SWOT, Five Whys, KPIs, etc)
- [OK] Latência adicional <60s (execução paralela)

---

### Tarefas Detalhadas

#### Tarefa 1.1: Refatorar run_diagnostic() (6-8h)

**Descrição**: Adicionar etapa "Análises Consultivas" no workflow de diagnóstico.

**Implementação**:
```python
async def run_diagnostic(self, context: dict) -> CompleteDiagnostic:
    # ETAPA 1: Análise paralela (4 agentes BSC) - JÁ EXISTE
    parallel_results = await self.run_parallel_analysis(context)

    # ETAPA 2: Análises consultivas (7 ferramentas) - NOVO!
    tools_results = await self._run_consultative_tools(context, parallel_results)

    # ETAPA 3: Consolidação enriquecida - MODIFICAR
    diagnostic = await self.consolidate_diagnostic(
        parallel_results,
        tools_results  # Novo parâmetro!
    )

    return diagnostic
```

**Subtarefas**:
1. Criar método `_run_consultative_tools()` (3h)
2. Modificar `consolidate_diagnostic()` para aceitar `tools_results` (2h)
3. Atualizar prompts de consolidação (1-2h)
4. Adicionar logs estruturados (1h)

**DoD**:
- [ ] Método `_run_consultative_tools()` implementado
- [ ] Ferramentas executam em paralelo (asyncio.gather)
- [ ] Logs mostram execução de cada ferramenta

---

#### Tarefa 1.2: Criar DiagnosticToolsResult schema (2h)

**Descrição**: Schema Pydantic para agregar outputs de todas ferramentas.

**Implementação**:
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

    execution_time: float  # Tempo total de execução
    tools_executed: List[str]  # Lista de ferramentas executadas
```

**DoD**:
- [ ] Schema criado e validado
- [ ] Type hints completos
- [ ] Docstrings em português brasileiro

---

#### Tarefa 1.3: Modificar consolidate_diagnostic() (3-4h)

**Descrição**: Enriquecer prompt de consolidação com outputs das ferramentas.

**Prompt Enriquecido**:
```python
prompt = f"""
Você é um consultor BSC sênior consolidando diagnóstico completo.

ANÁLISES DAS 4 PERSPECTIVAS BSC:
{parallel_results}

ANÁLISES CONSULTIVAS COMPLEMENTARES:

SWOT ANALYSIS:
{tools_results.swot_analysis}

FIVE WHYS (ROOT CAUSES):
{tools_results.five_whys_analysis}

KPI FRAMEWORK:
{tools_results.kpi_framework}

STRATEGIC OBJECTIVES:
{tools_results.strategic_objectives}

BENCHMARKING:
{tools_results.benchmarking_report}

Consolide em diagnóstico completo com recomendações priorizadas.
"""
```

**DoD**:
- [ ] Prompt usa TODAS as ferramentas
- [ ] Consolidação menciona insights de cada ferramenta
- [ ] Recomendações são mais ricas e acionáveis

---

#### Tarefa 1.4: Testes E2E (4-6h)

**Descrição**: Validar diagnóstico completo com ferramentas.

**Testes a Criar**:
1. `test_diagnostic_with_all_tools()` - Validar execução de 7 ferramentas
2. `test_diagnostic_tools_parallel()` - Validar paralelização
3. `test_diagnostic_latency()` - Validar latência <5 min
4. `test_diagnostic_consolidation_enriched()` - Validar consolidação usa ferramentas
5. `test_diagnostic_no_regression()` - Validar zero regressões

**Baseline a Capturar ANTES**:
```bash
pytest tests/test_workflow_e2e.py -v --tb=long 2>&1
# Capturar métricas: latência P50/P95, quality scores
```

**DoD**:
- [ ] 5 testes novos criados
- [ ] 100% testes E2E passando (22 existentes + 5 novos)
- [ ] Zero regressões detectadas
- [ ] Coverage >85% em diagnostic_agent.py

---

#### Tarefa 1.5: Documentação (2h)

**Documentos a Atualizar**:
1. `docs/ARCHITECTURE.md` - Adicionar DiagnosticToolsResult
2. `docs/LANGGRAPH_WORKFLOW.md` - Adicionar etapa "Análises Consultivas"
3. `docs/tools/TOOLS_INTEGRATION.md` (NOVO) - Guia de integração

**DoD**:
- [ ] Documentação técnica atualizada
- [ ] Diagrama Mermaid atualizado

---

### Métricas de Sucesso

**KPIs Sprint 1**:
- [OK] 7/7 ferramentas integradas no diagnóstico
- [OK] Latência adicional <60s (P95)
- [OK] Latência total diagnóstico <5 min (P95)
- [OK] 100% testes E2E passando
- [OK] Coverage >85% em diagnostic_agent.py
- [OK] Diagnóstico tem seções SWOT, Five Whys, KPIs visíveis

**Critérios de Aceitação**:
- [ ] `run_diagnostic()` chama todas 7 ferramentas consultivas
- [ ] Ferramentas executam em paralelo (asyncio.gather)
- [ ] DiagnosticToolsResult schema criado e validado
- [ ] `consolidate_diagnostic()` usa outputs das ferramentas no prompt
- [ ] 100% testes E2E passando (27 testes)
- [ ] Latência P95 <5 min (vs ~3 min baseline)
- [ ] Zero regressões em testes existentes
- [ ] Documentação atualizada

---

### Riscos e Mitigações

**Risco 1: Latência aumenta muito (>2 min adicional)**
- **Probabilidade**: MÉDIA
- **Impacto**: ALTO (usuário desiste)
- **Mitigação**: Executar ferramentas em paralelo, otimizar prompts, medir latência continuamente

**Risco 2: LLM não consegue consolidar 7 outputs**
- **Probabilidade**: BAIXA
- **Impacto**: ALTO (consolidação confusa)
- **Mitigação**: Usar Claude Sonnet 4.5 (200K context), prompt estruturado com seções claras

**Risco 3: Regressões em testes E2E**
- **Probabilidade**: ALTA
- **Impacto**: MÉDIO (debug adicional)
- **Mitigação**: Executar baseline ANTES, rodar suite completa após cada mudança

---

### Esforço e ROI

**Esforço Total**: 17-22h (2-3 dias)

**ROI**: [EMOJI] CRÍTICO
- 70% do valor da FASE 3 desbloqueado
- Diagnóstico muito mais rico e acionável
- Zero custo adicional (ferramentas já implementadas)

**Prioridade**: [EMOJI] MÁXIMA (resolve GAP #2)

---

## [EMOJI] SPRINT 2 - Strategy Map MVP

### Objetivo

**Converter diagnóstico em Strategy Map visual** nas 4 perspectivas BSC com objetivos e KPIs alinhados.

**Entregável**: Strategy Map estruturado com validação de alinhamento.

---

### Tarefas Detalhadas

#### Tarefa 2.1: Implementar Strategy_Map_Designer_Tool (6-8h)

**Descrição**: Ferramenta que converte diagnóstico em Strategy Map com objetivos e KPIs nas 4 perspectivas.

**Input**:
- `CompleteDiagnostic` (diagnóstico completo)
- `DiagnosticToolsResult` (ferramentas consultivas)

**Output**:
- `StrategyMap` (schema Pydantic com 4 perspectivas + objetivos + KPIs + conexões causa-efeito)

**Implementação**:
```python
# src/tools/strategy_map_designer_tool.py

class StrategyMapDesignerTool:
    """
    Converte diagnóstico BSC em Strategy Map visual.

    Reutiliza:
    - StrategicObjectivesTool (objetivos SMART)
    - KPIDefinerTool (KPIs alinhados)

    Adiciona:
    - Conexões causa-efeito entre perspectivas
    - Validação de balanceamento
    """

    async def design_strategy_map(
        self,
        diagnostic: CompleteDiagnostic,
        tools_results: DiagnosticToolsResult
    ) -> StrategyMap:
        # ETAPA 1: Extrair objetivos de cada perspectiva (reusa StrategicObjectivesTool)
        objectives = await self._extract_objectives(diagnostic)

        # ETAPA 2: Definir KPIs para cada objetivo (reusa KPIDefinerTool)
        kpis = await self._define_kpis(objectives)

        # ETAPA 3: Mapear conexões causa-efeito (NOVO)
        connections = await self._map_cause_effect(objectives)

        # ETAPA 4: Criar Strategy Map estruturado
        strategy_map = StrategyMap(
            financial_objectives=objectives.financial,
            customer_objectives=objectives.customer,
            process_objectives=objectives.process,
            learning_objectives=objectives.learning,
            kpis=kpis,
            cause_effect_connections=connections
        )

        return strategy_map
```

**Subtarefas**:
1. Criar schema `StrategyMap` Pydantic (2h)
2. Implementar `_extract_objectives()` reutilizando StrategicObjectivesTool (2h)
3. Implementar `_define_kpis()` reutilizando KPIDefinerTool (1h)
4. Implementar `_map_cause_effect()` com LLM (2-3h)

**DoD**:
- [ ] Tool implementado e testado
- [ ] Reutiliza StrategicObjectivesTool e KPIDefinerTool
- [ ] Strategy Map tem 4 perspectivas balanceadas
- [ ] Conexões causa-efeito mapeadas

---

#### Tarefa 2.2: Implementar Alignment_Validator_Tool (2-3h)

**Descrição**: Valida se Strategy Map está balanceado e completo.

**Validações**:
1. Todas 4 perspectivas têm ≥2 objetivos
2. Cada objetivo tem ≥1 KPI
3. Conexões causa-efeito entre perspectivas existem
4. Não há objetivos "isolados" (sem conexões)
5. KPIs são mensuráveis (SMART)

**Output**:
- `AlignmentReport` com score 0-100 e lista de gaps detectados

**DoD**:
- [ ] Tool implementado e testado
- [ ] Detecta 5 tipos de gaps
- [ ] Report estruturado com recomendações de correção

---

#### Tarefa 2.3: Criar node design_solution() no workflow (4-6h)

**Descrição**: Novo node no LangGraph workflow que gera Strategy Map.

**Localização**: `src/graph/workflow.py`

**Implementação**:
```python
def design_solution(self, state: BSCState) -> dict[str, Any]:
    """
    Node: Gera Strategy Map a partir do diagnóstico aprovado.

    Routing:
    APPROVAL_PENDING (aprovado) -> SOLUTION_DESIGN -> design_solution()
    """
    logger.info("[SOLUTION_DESIGN] Gerando Strategy Map...")

    # ETAPA 1: Chamar Strategy_Map_Designer_Tool
    strategy_map = await self.strategy_map_designer.design_strategy_map(
        diagnostic=state.diagnostic,
        tools_results=state.diagnostic_tools_results
    )

    # ETAPA 2: Validar alinhamento
    alignment_report = await self.alignment_validator.validate(strategy_map)

    # ETAPA 3: Salvar no state
    return {
        "strategy_map": strategy_map,
        "alignment_report": alignment_report,
        "current_phase": ConsultingPhase.SOLUTION_DESIGN
    }
```

**Subtarefas**:
1. Criar node `design_solution()` (2h)
2. Adicionar routing `APPROVAL_PENDING -> SOLUTION_DESIGN` (1h)
3. Atualizar `BSCState` com campos `strategy_map` e `alignment_report` (1h)
4. Adicionar logs estruturados (1h)

**DoD**:
- [ ] Node implementado e integrado no workflow
- [ ] Routing funcional
- [ ] State atualizado com Strategy Map

---

#### Tarefa 2.4: Testes E2E (4-6h)

**Testes a Criar**:
1. `test_design_solution_happy_path()` - Fluxo completo APPROVAL -> SOLUTION_DESIGN
2. `test_strategy_map_balanced()` - Validar 4 perspectivas balanceadas
3. `test_alignment_validation()` - Validar detecção de gaps
4. `test_strategy_map_kpis_aligned()` - Validar KPIs alinhados com objetivos

**DoD**:
- [ ] 4 testes novos criados
- [ ] 100% testes E2E passando

---

#### Tarefa 2.5: UI Streamlit para Strategy Map (6-8h)

**Descrição**: Visualização do Strategy Map na UI.

**Features**:
- Mostrar 4 perspectivas em cards
- Mostrar objetivos de cada perspectiva
- Mostrar KPIs de cada objetivo
- Mostrar conexões causa-efeito (grafo simples)

**DoD**:
- [ ] UI mostra Strategy Map completo
- [ ] Usuário pode visualizar conexões

---

#### Tarefa 2.6: Documentação (2h)

**Documentos a Atualizar**:
1. `docs/ARCHITECTURE.md` - Adicionar Strategy Map e Alignment Validator
2. `docs/LANGGRAPH_WORKFLOW.md` - Adicionar node design_solution()
3. `docs/tools/STRATEGY_MAP_DESIGNER.md` (NOVO) - Documentação da ferramenta

**DoD**:
- [ ] Documentação técnica atualizada
- [ ] Exemplos de uso incluídos

---

### Métricas de Sucesso

**KPIs Sprint 2**:
- [OK] Strategy Maps têm 4 perspectivas balanceadas
- [OK] 0 gaps detectados pelo Alignment_Validator em 80% casos
- [OK] Latência geração Strategy Map <2 min
- [OK] 100% testes E2E passando

**Critérios de Aceitação**:
- [ ] Strategy_Map_Designer_Tool implementado e testado
- [ ] Alignment_Validator_Tool implementado e testado
- [ ] Node design_solution() criado no workflow
- [ ] Routing APPROVAL_PENDING -> SOLUTION_DESIGN funcional
- [ ] StrategyMap schema criado (4 perspectivas + objetivos + KPIs + conexões)
- [ ] 100% testes E2E passando (incluindo novo fluxo)
- [ ] UI Streamlit mostra Strategy Map gerado
- [ ] Documentação atualizada

---

### Esforço e ROI

**Esforço Total**: 18-25h (2-3 dias)

**ROI**: [EMOJI] ALTO
- Strategy Map acionável converte diagnóstico em estratégia visual
- Alinhamento automático economiza 2-3h de consultoria manual
- Base para implementação (Sprint 4)

**Prioridade**: [EMOJI] ALTA

---

## [EMOJI] SPRINT 3 - Validações Avançadas

### Objetivo

**Enriquecer Strategy Map** com validações avançadas de alinhamento e mapeamento causa-efeito completo.

**Entregável**: Strategy Map com KPI Alignment Checker + Cause-Effect Mapper + UI interativa.

---

### Tarefas Detalhadas

#### Tarefa 3.1: Implementar KPI_Alignment_Checker (3-4h)

**Descrição**: Verifica se KPIs estão alinhados com objetivos estratégicos.

**Validações**:
1. Cada KPI tem objetivo pai válido
2. KPI é mensurável (SMART)
3. KPI não é duplicado
4. KPI não é "órfão" (sem objetivo)

**Output**:
- `KPIAlignmentReport` com score 0-100 e lista de KPIs problemáticos

**DoD**:
- [ ] Tool implementado e testado
- [ ] Detecta 4 tipos de problemas de alinhamento
- [ ] Report com recomendações de correção

---

#### Tarefa 3.2: Implementar Cause_Effect_Mapper (4-5h)

**Descrição**: Mapeia relações causa-efeito entre objetivos de diferentes perspectivas.

**Exemplo**:
```
Learning: "Treinar equipe em vendas consultivas"
    ↓ (causa)
Process: "Melhorar processo de vendas"
    ↓ (efeito)
Customer: "Aumentar satisfação de clientes"
    ↓ (efeito)
Financial: "Aumentar receita recorrente"
```

**Output**:
- Grafo de conexões com força da relação (0-100)

**DoD**:
- [ ] Tool implementado e testado
- [ ] Grafo de conexões mapeado
- [ ] Força das relações calculada

---

#### Tarefa 3.3: Integrar ferramentas no design_solution() (3-4h)

**Descrição**: Adicionar KPI Alignment Checker e Cause-Effect Mapper no workflow.

**DoD**:
- [ ] Ferramentas integradas
- [ ] Reports incluídos no state

---

#### Tarefa 3.4: UI interativa para Strategy Map (6-8h)

**Descrição**: UI Streamlit com edição manual de Strategy Map.

**Features**:
- Editar objetivos (adicionar/remover/modificar)
- Editar KPIs (adicionar/remover/modificar)
- Visualizar grafo causa-efeito (interativo)
- Validar alinhamento em tempo real

**DoD**:
- [ ] UI interativa funcional
- [ ] Usuário pode editar Strategy Map manualmente
- [ ] Validações em tempo real

---

#### Tarefa 3.5: Testes E2E (4-6h)

**Testes a Criar**:
1. `test_kpi_alignment_checker()` - Validar detecção de KPIs órfãos
2. `test_cause_effect_mapper()` - Validar mapeamento de conexões
3. `test_strategy_map_edit()` - Validar edição manual

**DoD**:
- [ ] 3 testes novos criados
- [ ] 100% testes E2E passando

---

#### Tarefa 3.6: Documentação (2h)

**Documentos a Atualizar**:
1. `docs/tools/KPI_ALIGNMENT_CHECKER.md` (NOVO)
2. `docs/tools/CAUSE_EFFECT_MAPPER.md` (NOVO)
3. `docs/ARCHITECTURE.md` - Atualizar diagrama

**DoD**:
- [ ] Documentação técnica atualizada

---

### Métricas de Sucesso

**KPIs Sprint 3**:
- [OK] 100% KPIs alinhados com objetivos
- [OK] Mapa causa-efeito tem ≥6 conexões entre perspectivas
- [OK] Usuário pode editar Strategy Map manualmente
- [OK] 100% testes E2E passando

---

### Esforço e ROI

**Esforço Total**: 22-29h (3-4 dias)

**ROI**: MÉDIO
- Qualidade do Strategy Map aumenta significativamente
- Edição manual permite customização por consultor

**Prioridade**: MÉDIA

---

## [EMOJI] SPRINT 4 - Action Plans MVP

### Objetivo

**Converter Strategy Map em Action Plans** com milestones, responsáveis e prazos.

**Entregável**: Action Plans estruturados com tracking de progresso.

---

### Tarefas Detalhadas

#### Tarefa 4.1: Implementar Action_Plan_Generator_Tool (5-7h)

**Descrição**: Ferramenta que converte Strategy Map em Action Plans.

**Input**:
- `StrategyMap` (Strategy Map completo)

**Output**:
- `ActionPlan` (lista de milestones por objetivo com responsáveis, prazos, status)

**Implementação**:
```python
class ActionPlanGeneratorTool:
    """
    Converte Strategy Map em Action Plans executáveis.

    Para cada objetivo estratégico:
    - Gera 3-5 milestones específicos
    - Define responsável (role, não nome)
    - Define prazo (timeline relativo: 30/60/90 dias)
    - Define status inicial: "todo"
    """

    async def generate_action_plans(
        self,
        strategy_map: StrategyMap
    ) -> List[ActionPlan]:
        action_plans = []

        for perspective in ["financial", "customer", "process", "learning"]:
            objectives = getattr(strategy_map, f"{perspective}_objectives")

            for objective in objectives:
                # Gerar 3-5 milestones por objetivo
                milestones = await self._generate_milestones(objective)

                action_plan = ActionPlan(
                    objective_id=objective.id,
                    perspective=perspective,
                    milestones=milestones
                )

                action_plans.append(action_plan)

        return action_plans
```

**DoD**:
- [ ] Tool implementado e testado
- [ ] Action Plans têm 3-5 milestones por objetivo
- [ ] Cada milestone tem responsável e prazo

---

#### Tarefa 4.2: Implementar Milestone_Tracker_Tool (4-5h)

**Descrição**: Tracking de progresso de cada milestone.

**Features**:
- Marcar milestone como "todo", "in_progress", "done"
- Calcular % de progresso por perspectiva
- Alertas de milestones atrasados

**DoD**:
- [ ] Tool implementado e testado
- [ ] Tracking de status funcional
- [ ] Cálculo de progresso por perspectiva

---

#### Tarefa 4.3: Criar node generate_action_plans() no workflow (4-6h)

**Descrição**: Novo node no LangGraph workflow que gera Action Plans.

**Implementação**:
```python
def generate_action_plans(self, state: BSCState) -> dict[str, Any]:
    """
    Node: Gera Action Plans a partir do Strategy Map.

    Routing:
    SOLUTION_DESIGN -> IMPLEMENTATION -> generate_action_plans()
    """
    logger.info("[IMPLEMENTATION] Gerando Action Plans...")

    # ETAPA 1: Chamar Action_Plan_Generator_Tool
    action_plans = await self.action_plan_generator.generate_action_plans(
        strategy_map=state.strategy_map
    )

    # ETAPA 2: Salvar no state
    return {
        "action_plans": action_plans,
        "current_phase": ConsultingPhase.IMPLEMENTATION
    }
```

**DoD**:
- [ ] Node implementado e integrado
- [ ] Routing SOLUTION_DESIGN -> IMPLEMENTATION funcional

---

#### Tarefa 4.4: Testes E2E (4-6h)

**Testes a Criar**:
1. `test_generate_action_plans()` - Validar geração completa
2. `test_action_plans_milestones()` - Validar estrutura milestones
3. `test_milestone_tracking()` - Validar tracking de status

**DoD**:
- [ ] 3 testes novos criados
- [ ] 100% testes E2E passando

---

#### Tarefa 4.5: UI Streamlit para Action Plans (6-8h)

**Descrição**: Visualização de Action Plans na UI.

**Features**:
- Mostrar action plans por perspectiva
- Mostrar milestones com status (todo/in progress/done)
- Permitir marcar milestone como concluído
- Mostrar % de progresso por perspectiva

**DoD**:
- [ ] UI mostra Action Plans completos
- [ ] Usuário pode atualizar status de milestones

---

#### Tarefa 4.6: Documentação (2h)

**Documentos a Atualizar**:
1. `docs/tools/ACTION_PLAN_GENERATOR.md` (NOVO)
2. `docs/tools/MILESTONE_TRACKER.md` (NOVO)
3. `docs/LANGGRAPH_WORKFLOW.md` - Adicionar node generate_action_plans()

**DoD**:
- [ ] Documentação técnica atualizada

---

### Métricas de Sucesso

**KPIs Sprint 4**:
- [OK] Action Plans têm 3-5 milestones por objetivo
- [OK] Cada milestone tem responsável e prazo definidos
- [OK] Latência geração Action Plans <3 min
- [OK] 100% testes E2E passando

---

### Esforço e ROI

**Esforço Total**: 19-26h (2-3 dias)

**ROI**: [EMOJI] ALTO
- Action Plans acionáveis convertem estratégia em ação
- Tracking de progresso permite acompanhamento contínuo

**Prioridade**: ALTA

---

## [EMOJI] SPRINT 5-6 - MCP Integrations + Dashboard (OPCIONAL)

### Objetivo

**Integrar ferramentas externas** (Asana, Google Calendar) e criar dashboard de progresso.

**Entregável**: Integração MCPs funcional + Progress Dashboard.

---

### Tarefas Detalhadas

#### Tarefa 5.1: MCP Asana Integration (8-10h)

**Descrição**: Criar tasks no Asana a partir de Action Plans.

**Features**:
- Criar projeto Asana por perspectiva
- Criar task por milestone
- Sincronizar status (todo -> in progress -> done)
- Webhook para updates bidirecionais

**DoD**:
- [ ] MCP Asana implementado
- [ ] Tasks criadas automaticamente
- [ ] Sincronização bidirecional funcional

---

#### Tarefa 5.2: MCP Google Calendar Integration (6-8h)

**Descrição**: Criar meetings no Google Calendar para milestones.

**Features**:
- Criar meeting para cada milestone (revisão)
- Sincronizar datas de prazo
- Enviar convites para responsáveis

**DoD**:
- [ ] MCP Calendar implementado
- [ ] Meetings criados automaticamente

---

#### Tarefa 5.3: Progress_Dashboard (10-12h)

**Descrição**: Dashboard visual de progresso por perspectiva.

**Features**:
- Gráfico de progresso por perspectiva (% concluído)
- Timeline de milestones
- Alertas de milestones atrasados
- Filtros por perspectiva/responsável

**DoD**:
- [ ] Dashboard implementado
- [ ] Visualizações interativas
- [ ] Alertas funcionais

---

#### Tarefa 5.4: Testes de Integração (6-8h)

**Testes a Criar**:
1. `test_asana_integration()` - Validar criação de tasks
2. `test_calendar_integration()` - Validar criação de meetings
3. `test_progress_dashboard()` - Validar cálculo de progresso

**DoD**:
- [ ] 3 testes de integração criados
- [ ] 100% testes passando

---

#### Tarefa 5.5: Documentação (4-6h)

**Documentos a Criar**:
1. `docs/integrations/ASANA_INTEGRATION.md` (NOVO)
2. `docs/integrations/CALENDAR_INTEGRATION.md` (NOVO)
3. `docs/integrations/PROGRESS_DASHBOARD.md` (NOVO)

**DoD**:
- [ ] Documentação completa de integração

---

### Métricas de Sucesso

**KPIs Sprint 5-6**:
- [OK] 100% action plans podem ser exportados para Asana
- [OK] Meetings são criados automaticamente no Calendar
- [OK] Dashboard mostra progresso real-time
- [OK] 100% testes de integração passando

---

### Esforço e ROI

**Esforço Total**: 34-44h (4-6 dias)

**ROI**: MÉDIO
- Automação economiza tempo de setup manual
- Dashboard aumenta visibilidade de progresso

**Prioridade**: BAIXA (condicional - implementar SE houver demanda)

---

## [EMOJI] RESUMO GERAL

### Esforço Total por Sprint

| Sprint | Objetivo | Esforço | ROI | Prioridade |
|---|---|---|---|---|
| 1 | Ferramentas no Diagnóstico (GAP #2) | 17-22h | CRÍTICO | [EMOJI] MÁXIMA |
| 2 | Strategy Map MVP | 18-25h | ALTO | [EMOJI] ALTA |
| 3 | Validações Avançadas | 22-29h | MÉDIO | MÉDIA |
| 4 | Action Plans MVP | 19-26h | ALTO | ALTA |
| 5-6 | MCPs + Dashboard | 34-44h | MÉDIO | BAIXA (opcional) |

**TOTAL MVP (Sprints 1-4)**: 76-102h (10-13 dias úteis)
**TOTAL COMPLETO (Sprints 1-6)**: 110-146h (14-19 dias úteis)

---

### Timeline Realista

**MVP (Obrigatório)**: 4 semanas
- Semana 1: Sprint 1 (GAP #2)
- Semana 2: Sprint 2 (Strategy Map)
- Semana 3: Sprint 3 (Validações)
- Semana 4: Sprint 4 (Action Plans)

**Completo (Opcional)**: +2 semanas
- Semana 5-6: Sprint 5-6 (MCPs + Dashboard)

---

### Riscos Gerais

**Risco 1: Escopo creep**
- **Probabilidade**: MÉDIA
- **Impacto**: BAIXO (não há deadline hard)
- **Mitigação**: Marcar Sprints 5-6 como OPCIONAIS

**Risco 2: Regressões em testes**
- **Probabilidade**: ALTA (mudanças grandes)
- **Impacto**: MÉDIO (debug adicional)
- **Mitigação**: Executar suite E2E ANTES de cada sprint, regression suite semanal

**Risco 3: Latência aumenta muito**
- **Probabilidade**: ALTA (muitas ferramentas)
- **Impacto**: ALTO (usuário desiste)
- **Mitigação**: Paralelização agressiva, monitoramento contínuo de latência

---

### Métricas de Sucesso Geral

**Após Sprint 1**:
- [OK] 100% diagnósticos usam ferramentas consultivas

**Após Sprint 2**:
- [OK] Strategy Maps têm 0 gaps de alinhamento

**Após Sprint 4**:
- [OK] 80% action plans são criados em <5 min

**Após Sprint 6**:
- [OK] 100% action plans podem ser exportados para Asana

---

## [EMOJI] PRÓXIMOS PASSOS

**HOJE (Sessão 36)**:
- [OK] Documentação completa criada (este documento + 7 outros)
- [OK] TODOs atualizados para refletir Sprints 1-6
- [OK] Tracking atualizado (consulting-progress.md)

**PRÓXIMA SESSÃO (Sessão 37)**:
- [EMOJI] **COMEÇAR SPRINT 1** - Integração Ferramentas no Diagnóstico (GAP #2)
- Executar baseline E2E ANTES de qualquer mudança
- Implementar Tarefa 1.1 (refatorar run_diagnostic)

---

**Última Atualização**: 2025-11-20
**Status**: [OK] PLANO APROVADO - Pronto para execução
