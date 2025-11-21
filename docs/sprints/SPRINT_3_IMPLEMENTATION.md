# Sprint 3 - Action Plan & Implementation - Design Document

**Data:** 2025-11-20
**Sessão:** 39
**Status:** [OK] PLANEJAMENTO COMPLETO | [OK] PRONTO PARA IMPLEMENTAÇÃO

---

## [OK] OBJETIVO

Converter **Strategy Map aprovado** em **Action Plan detalhado** com ações específicas, owners, prazos, recursos e critérios de sucesso.

**Entregável:** Action Plan estruturado integrado ao workflow LangGraph, com testes E2E validados.

---

## [OK] RESEARCH BRIGHTDATA (2024-2025 Best Practices)

### Fontes Validadas:
1. **Strategy Institute** (Mar 2024) - Comprehensive Guide to BSC Implementation
2. **SME Strategy** (2025) - 7 Best Practices for Action Planning
3. **Mooncamp** (2025) - Balanced Scorecard Implementation Guide

### Step 3 do BSC Implementation (Kaplan & Norton):
**"Develop Action Plans"** - Criar planos estratégicos para atingir os KPIs

### 7 Best Practices Action Planning (SME Strategy 2025):
1. Align actions with goals
2. Prioritize based on importance and time sensitivity
3. Be specific rather than general
4. Set deadlines & assign owners
5. Ask for volunteers or delegate tasks
6. Develop action plan for implementation
7. Track and monitor progress

**Validação:** Nossa `ActionPlanTool` já implementa TODAS as 7 best practices!

---

## [OK] ARQUITETURA SPRINT 3

### Schema ActionPlan (src/memory/schemas.py) - JÁ EXISTE

```python
class ActionItem(BaseModel):
    """Ação específica do plano de implementação BSC.

    Attributes:
        action_title: Título da ação (10-150 caracteres)
        description: Descrição detalhada (20-1000 caracteres)
        perspective: Perspectiva BSC relacionada
        priority: Prioridade (HIGH, MEDIUM, LOW)
        effort: Esforço necessário (HIGH, MEDIUM, LOW)
        responsible: Responsável pela execução
        start_date: Data de início (YYYY-MM-DD)
        due_date: Data limite (YYYY-MM-DD)
        resources_needed: Lista de recursos necessários
        success_criteria: Critérios para medir sucesso (min_length=10)
        dependencies: Lista de ações dependentes
    """
    pass  # Schema completo já existe


class ActionPlan(BaseModel):
    """Plano de ação completo BSC.

    Attributes:
        action_items: Lista de 5-20 ações priorizadas
        implementation_timeline: Timeline geral (ex: "6-12 meses")
        critical_path: Lista de ações no caminho crítico
        quick_wins: Lista de quick wins (ações de alto impacto, baixo esforço)
        long_term_initiatives: Lista de iniciativas de longo prazo

    Methods:
        - total_actions -> int
        - by_perspective(perspective) -> List[ActionItem]
        - by_priority(priority) -> List[ActionItem]
        - high_priority_actions() -> List[ActionItem]
    """
    pass  # Schema completo já existe
```

### Tool ActionPlanTool (src/tools/action_plan.py) - JÁ EXISTE

```python
class ActionPlanTool:
    """Facilita criação de planos de ação estruturados com contexto BSC.

    Combina:
    1. Contexto da empresa (ClientProfile)
    2. Conhecimento BSC via RAG (specialist agents)
    3. Resultados de diagnóstico BSC (opcional)
    4. LLM structured output para gerar ActionPlan

    Methods:
        - facilitate(client_profile, diagnostic_results, financial_agent, customer_agent, process_agent, learning_agent) -> ActionPlan
    """
    pass  # Tool completa já existe (408 linhas)
```

### Workflow Integration (Sprint 3) - A CRIAR

```python
class BSCWorkflow:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.judge = JudgeAgent()
        self.strategy_map_designer = StrategyMapDesignerTool(...)  # Sprint 2
        self.alignment_validator = AlignmentValidatorTool()  # Sprint 2

        # SPRINT 3: Action Plan tool
        self.action_plan_tool = ActionPlanTool(llm=get_llm())

    def implementation_handler(self, state: BSCState) -> dict[str, Any]:
        """
        SPRINT 3: Handler para criação do Action Plan.

        STEPS:
        1. Validar strategy_map existe e está validado
        2. Buscar client_profile do state
        3. Converter diagnostic dict -> CompleteDiagnostic Pydantic
        4. Chamar ActionPlanTool.facilitate() (async)
        5. Retornar action_plan no state
        6. Routing: implementation -> END (workflow completo)

        Args:
            state: Estado com strategy_map, diagnostic, client_profile

        Returns:
            Estado atualizado com action_plan, final_response, phase IMPLEMENTATION
        """
        pass  # A implementar
```

---

## [OK] TAREFAS SPRINT 3

### Tarefa 3.1: Expandir BSCState (30 min)

**Objetivo:** Adicionar campo action_plan no estado do workflow.

**Arquivos:**
- `src/graph/states.py` (+3 linhas)

**Implementação:**
```python
# SPRINT 3: Action Plan
action_plan: ActionPlan | None = None
```

**DoD:**
- [ ] Import ActionPlan em states.py
- [ ] Campo action_plan adicionado
- [ ] Linter errors zero

---

### Tarefa 3.2: Implementar implementation_handler() (2-3h)

**Objetivo:** Substituir placeholder por handler real que gera Action Plan.

**Arquivos:**
- `src/graph/workflow.py` (+150-200 linhas)

**Implementação:**
1. Inicializar ActionPlanTool no `__init__` (passar llm)
2. Implementar `implementation_handler()`:
   - Validar strategy_map existe
   - Buscar client_profile do state
   - Converter diagnostic dict -> Pydantic
   - Chamar `action_plan_tool.facilitate()` (async)
   - Retornar action_plan + final_response
3. Logs estruturados (timestamps, num_actions, critical_path, quick_wins)

**DoD:**
- [ ] ActionPlanTool inicializada no __init__
- [ ] implementation_handler() implementado (~150-200 linhas)
- [ ] Error handling robusto
- [ ] Logs estruturados completos

---

### Tarefa 3.3: Atualizar Routing (15 min)

**Objetivo:** Configurar routing implementation -> END.

**Arquivos:**
- `src/graph/workflow.py` (modificar _build_graph)

**Implementação:**
- Edge já existe: `implementation -> save_client_memory -> END`
- Apenas garantir que node chama handler correto

**DoD:**
- [ ] Routing implementation -> save_client_memory configurado
- [ ] Workflow completo: ONBOARDING -> DISCOVERY -> APPROVAL -> SOLUTION_DESIGN -> IMPLEMENTATION -> END

---

### Tarefa 3.4: Testes E2E (2-3h)

**Objetivo:** Validar integração completa do Action Plan no workflow.

**Arquivos:**
- `tests/test_implementation_workflow.py` (~600-800 linhas)

**Testes (10+):**
1. implementation_handler cria Action Plan com strategy_map válido
2. implementation_handler valida client_profile existe
3. implementation_handler com diagnostic válido enriquece Action Plan
4. Fallback para strategy_map ausente
5. Erro na criação do Action Plan é tratado
6. Validação de logs estruturados
7. Validação de metadata (num_actions, critical_path, quick_wins)
8. Action Plan tem 5-20 ações
9. Action Plan tem quick_wins identificados
10. E2E completo: strategy_map aprovado -> action_plan -> END

**DoD:**
- [ ] 10+ testes criados
- [ ] 100% testes passando
- [ ] Mocks para ActionPlanTool.facilitate()
- [ ] Fixtures Pydantic válidas (aplicar PONTO 15 [[memory:9969868]])

---

### Tarefa 3.5: Validação Regressão (30 min)

**Objetivo:** Garantir que Sprint 1 e 2 continuam funcionando.

**Testes:**
- `tests/test_approval_workflow.py` (9 testes Sprint 1)
- `tests/test_design_solution_workflow.py` (13 testes Sprint 2)

**DoD:**
- [ ] 9/9 testes Sprint 1 passando
- [ ] 13/13 testes Sprint 2 passando
- [ ] Zero breaking changes

---

### Tarefa 3.6: Documentação (30 min)

**Objetivo:** Documentar Sprint 3 completo.

**Arquivos:**
- `.cursor/progress/consulting-progress.md` (+100-150 linhas)
- `docs/sprints/SPRINT_3_IMPLEMENTATION_SUMMARY.md` (opcional)

**Conteúdo:**
1. Trabalho realizado (implementation_handler, routing, testes)
2. Métricas (latência, num_actions, coverage)
3. Lições aprendidas (3-5 insights)
4. Próximos passos (Sprint 4 - UI Streamlit)

**DoD:**
- [ ] Sessão 39 documentada em consulting-progress.md
- [ ] Lições aprendidas consolidadas
- [ ] Métricas registradas

---

## [OK] ESFORÇO E ROI

**Esforço Total:** 4-6h (mesmo padrão Sprint 2 tarefa 2.4)

**ROI:** [OK] MUITO ALTO
- Action Plan é deliverable final do fluxo consultivo
- Ações específicas e acionáveis (não apenas diagnóstico)
- Base para tracking e monitoring (Sprint 4-6)

**Prioridade:** [OK] CRÍTICA (última peça do workflow consultivo completo)

---

## [OK] MÉTRICAS DE SUCESSO

**KPIs Sprint 3:**
- [OK] Action Plan com 5-20 ações específicas
- [OK] 100% ações têm owner, deadline, success_criteria
- [OK] Quick wins identificados (alto impacto, baixo esforço)
- [OK] Critical path mapeado
- [OK] Latência implementation_handler() <30s (P95)
- [OK] 100% testes passando (10+ E2E)
- [OK] Zero regressões

**Critérios de Aceitação:**
- [ ] `implementation_handler()` node integrado no workflow
- [ ] Action Plan gerado automaticamente após Strategy Map aprovado
- [ ] 100% testes E2E passando
- [ ] Zero regressões em Sprint 1 e 2
- [ ] Documentação completa criada

---

**Última Atualização:** 2025-11-20 (Sessão 39)
**Próxima Revisão:** Após conclusão Tarefa 3.1
