# Sprint 2 - Strategy Map MVP - Design Document

**Data:** 2025-11-20
**Sessão:** 38
**Status:** [EMOJI] PLANEJAMENTO COMPLETO | [EMOJI] PRONTO PARA IMPLEMENTAÇÃO

---

## [EMOJI] OBJETIVO

Converter diagnóstico BSC aprovado em **Strategy Map visual** com 4 perspectivas balanceadas, objetivos estratégicos, KPIs e conexões causa-efeito.

**Entregável:** Strategy Map estruturado e validado, com UI Streamlit para visualização.

---

## [EMOJI] RESEARCH BRIGHTDATA (2024-2025 Best Practices)

### Fontes Validadas:
1. **BSCDesigner.com** (2025 update) - Framework Kaplan & Norton oficial
2. **Spider Strategies** (2025) - Balanced Scorecard guide atualizado
3. **Strategy Institute** (Mar 2024) - Implementação BSC completa

### 8 Steps Validados (Kaplan & Norton):
1. Define Mission, Vision, Values
2. Define Four Perspectives (Finance, Customer, Internal, Learning/Growth)
3. Strategic Priorities (top 3 goals)
4. Define Business Goals (8-10 por perspectiva, causa-efeito)
5. Describe Rationale (WHY cada goal)
6. Define Leading & Lagging Metrics (par de KPIs)
7. Define Initiatives (HOW executar)
8. Cascade (versões locais por business unit)

### Cause-Effect Principles:
- **Logic: TOP->BOTTOM** (Financial -> Customer -> Process -> Learning)
- Lower perspectives EXPLAIN HOW achieve higher perspectives
- Every goal MUST have connections (não isolated)
- Typical: 8-10 goals per perspective (RED FLAG se >10)

### 8 Mistakes Típicos (EVITAR):
1. Goals without connections
2. Focusing on operational (not strategic) goals
3. No rationale
4. Using lagging metrics only
5. Having top-level map only
6. Too many goals (>10 per perspective)
7. Mixing goals and metrics
8. Using business jargon

---

## [EMOJI] ARQUITETURA SPRINT 2

### Schemas Pydantic (src/memory/schemas.py)

```python
class CauseEffectConnection(BaseModel):
    """Conexão causa-efeito entre objetivos."""

    source_objective_id: str = Field(description="ID objetivo origem")
    target_objective_id: str = Field(description="ID objetivo destino")
    relationship_type: Literal["enables", "drives", "supports"] = Field(
        description="Tipo de relacionamento causa-efeito"
    )
    strength: Literal["strong", "medium", "weak"] = Field(
        default="medium",
        description="Força da conexão"
    )
    rationale: str = Field(
        min_length=30,
        description="Explicação do relacionamento causa-efeito"
    )

class StrategyMapPerspective(BaseModel):
    """Uma perspectiva do Strategy Map."""

    name: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
    objectives: list[StrategicObjective] = Field(
        min_length=2,
        max_length=10,
        description="2-10 objetivos estratégicos (validado Kaplan & Norton)"
    )

class StrategyMap(BaseModel):
    """Strategy Map completo com 4 perspectivas BSC."""

    financial: StrategyMapPerspective
    customer: StrategyMapPerspective
    process: StrategyMapPerspective
    learning: StrategyMapPerspective

    cause_effect_connections: list[CauseEffectConnection] = Field(
        min_length=4,
        description="Mínimo 4 conexões causa-efeito entre perspectivas"
    )

    strategic_priorities: list[str] = Field(
        min_length=1,
        max_length=3,
        description="1-3 prioridades estratégicas top-level"
    )

    mission: str | None = None
    vision: str | None = None
    values: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlignmentReport(BaseModel):
    """Report de validação do Strategy Map."""

    score: float = Field(ge=0, le=100, description="Score de alinhamento 0-100")
    is_balanced: bool = Field(description="4 perspectivas balanceadas?")

    gaps: list[str] = Field(
        default_factory=list,
        description="Lista de gaps detectados"
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings (não-bloqueantes)"
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Recomendações de correção"
    )

    validation_checks: dict[str, bool] = Field(
        description="Checklist de 8 validações executadas"
    )
```

### Tools (src/tools/)

**1. strategy_map_designer.py**

```python
class StrategyMapDesignerTool:
    """
    Converte diagnóstico BSC em Strategy Map visual com RAG.

    Reutiliza PADRÃO VALIDADO Sprint 1:
    - _retrieve_bsc_knowledge() (mesmo pattern SWOT, Five Whys, Issue Tree)
    - 4 specialist agents em paralelo (asyncio.gather)
    - Contexto RAG enriquece design do Strategy Map

    Reutiliza Tools FASE 3:
    - StrategicObjectivesTool (já implementada)
    - KPIDefinerTool (já implementada)

    Adiciona com RAG:
    - Mapeamento causa-efeito validado contra literatura K&N (NOVO)
    - Validação de objectives contra framework BSC (NOVO)
    - Sugestão de KPIs baseados em benchmarks (NOVO)

    Best Practice (BSCDesigner 2025): 8-10 objectives per perspective.
    """

    def __init__(
        self,
        llm: BaseLLM,
        financial_agent,
        customer_agent,
        process_agent,
        learning_agent
    ):
        """
        Inicializa Strategy Map Designer com LLM e 4 specialist agents.

        Args:
            llm: Language model para structured output
            financial_agent: Agent perspectiva Financeira (com RAG)
            customer_agent: Agent perspectiva Clientes (com RAG)
            process_agent: Agent perspectiva Processos (com RAG)
            learning_agent: Agent perspectiva Aprendizado (com RAG)
        """
        self.llm = llm
        self.financial_agent = financial_agent
        self.customer_agent = customer_agent
        self.process_agent = process_agent
        self.learning_agent = learning_agent

    async def design_strategy_map(
        self,
        diagnostic: CompleteDiagnostic,
        tools_results: DiagnosticToolsResult,
        use_rag: bool = True
    ) -> StrategyMap:
        """Gera Strategy Map completo a partir do diagnóstico com RAG."""

        # ETAPA 0: Buscar contexto RAG (MESMO PATTERN Sprint 1) [OK]
        rag_context = ""
        if use_rag:
            rag_context = await self._retrieve_bsc_knowledge(
                diagnostic=diagnostic,
                topic="strategy map design and cause-effect mapping"
            )

        # ETAPA 1: Extrair objetivos estratégicos de cada perspectiva
        # Reutiliza StrategicObjectivesTool + RAG context
        objectives = await self._extract_objectives_by_perspective(
            diagnostic,
            rag_context
        )

        # ETAPA 2: Definir KPIs para cada objetivo
        # Reutiliza KPIDefinerTool + RAG benchmarks
        objectives_with_kpis = await self._define_kpis_for_objectives(
            objectives,
            rag_context
        )

        # ETAPA 3: Mapear conexões causa-efeito (NOVO - core do Sprint 2)
        # Framework K&N validado contra literatura RAG
        connections = await self._map_cause_effect_connections(
            objectives_with_kpis,
            rag_context  # Literatura K&N sobre causa-efeito
        )

        # ETAPA 4: Identificar prioridades estratégicas top-level
        priorities = await self._identify_strategic_priorities(
            diagnostic,
            rag_context
        )

        # ETAPA 5: Criar Strategy Map estruturado
        strategy_map = StrategyMap(
            financial=StrategyMapPerspective(
                name="Financeira",
                objectives=objectives_with_kpis.financial
            ),
            customer=StrategyMapPerspective(
                name="Clientes",
                objectives=objectives_with_kpis.customer
            ),
            process=StrategyMapPerspective(
                name="Processos Internos",
                objectives=objectives_with_kpis.process
            ),
            learning=StrategyMapPerspective(
                name="Aprendizado e Crescimento",
                objectives=objectives_with_kpis.learning
            ),
            cause_effect_connections=connections,
            strategic_priorities=priorities,
            mission=diagnostic.mission if hasattr(diagnostic, 'mission') else None,
            vision=diagnostic.vision if hasattr(diagnostic, 'vision') else None
        )

        return strategy_map

    async def _retrieve_bsc_knowledge(
        self,
        diagnostic: CompleteDiagnostic,
        topic: str
    ) -> str:
        """
        Busca conhecimento BSC usando 4 specialist agents em paralelo.

        PADRÃO REUTILIZADO (Sprint 1 - validado SWOT, Five Whys, Issue Tree):
        - asyncio.gather() com 4 agents
        - agent.ainvoke() (não invoke())
        - Contexto enriquece design do Strategy Map

        Args:
            diagnostic: Diagnóstico BSC completo
            topic: Tópico específico (ex: "strategy map design", "cause-effect mapping")

        Returns:
            String com conhecimento BSC recuperado das 4 perspectivas
        """
        # Query RAG focada em Strategy Map
        rag_query = f"""
        CONTEXTO EMPRESA: {diagnostic.executive_summary[:500]}

        TÓPICO: {topic}

        Buscar na literatura BSC (Kaplan & Norton):
        - Framework de Strategy Map design
        - Conexões causa-efeito típicas entre perspectivas
        - KPIs leading e lagging recomendados
        - Exemplos de objectives estratégicos validados
        - Erros comuns a evitar (jargon, goals operacionais)
        """

        # Buscar em paralelo nas 4 perspectivas (MESMO PATTERN Sprint 1)
        results = await asyncio.gather(
            self.financial_agent.ainvoke(rag_query),
            self.customer_agent.ainvoke(rag_query),
            self.process_agent.ainvoke(rag_query),
            self.learning_agent.ainvoke(rag_query),
            return_exceptions=True
        )

        # Consolidar contexto RAG
        context_parts = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and "output" in result:
                context_parts.append(f"[PERSPECTIVA {i+1}]\n{result['output'][:2000]}")

        return "\n\n".join(context_parts)

    async def _map_cause_effect_connections(
        self,
        objectives_by_perspective: dict,
        rag_context: str
    ) -> list[CauseEffectConnection]:
        """
        Mapeia conexões causa-efeito entre objetivos com RAG.

        Framework Kaplan & Norton (validado contra literatura):
        - Learning enables Process
        - Process drives Customer
        - Customer drives Financial

        LLM identifica conexões específicas usando:
        1. Objectives do diagnóstico
        2. RAG context (exemplos validados K&N)
        3. Framework causa-efeito oficial
        """
        # Prompt LLM com RAG context + framework
        # Ver src/prompts/strategy_map_prompts.py
        pass
```

**2. alignment_validator.py**

```python
class AlignmentValidatorTool:
    """
    Valida se Strategy Map está balanceado e completo.

    8 Validações (baseadas em research BSCDesigner 2025):
    1. Todas 4 perspectivas têm 2-10 objetivos
    2. Cada objetivo tem ≥1 KPI (leading + lagging)
    3. Existem conexões causa-efeito entre perspectivas
    4. Não há objetivos isolados (sem conexões)
    5. KPIs são mensuráveis (SMART)
    6. Goals são estratégicos (não operacionais)
    7. Objectives têm rationale explicado
    8. Não usa business jargon genérico
    """

    def validate_alignment(
        self,
        strategy_map: StrategyMap
    ) -> AlignmentReport:
        """Executa 8 validações e retorna report."""

        checks = {
            "balanced_perspectives": self._check_balanced_perspectives(strategy_map),
            "all_objectives_have_kpis": self._check_objectives_have_kpis(strategy_map),
            "cause_effect_exists": self._check_cause_effect_exists(strategy_map),
            "no_isolated_objectives": self._check_no_isolated_objectives(strategy_map),
            "kpis_are_smart": self._check_kpis_are_smart(strategy_map),
            "goals_are_strategic": self._check_goals_are_strategic(strategy_map),
            "has_rationale": self._check_has_rationale(strategy_map),
            "no_jargon": self._check_no_jargon(strategy_map)
        }

        # Score: % de checks passando
        score = (sum(checks.values()) / len(checks)) * 100

        # Detectar gaps e gerar recomendações
        gaps = self._identify_gaps(checks, strategy_map)
        recommendations = self._generate_recommendations(gaps)

        return AlignmentReport(
            score=score,
            is_balanced=checks["balanced_perspectives"],
            gaps=gaps,
            recommendations=recommendations,
            validation_checks=checks
        )
```

### Prompts (src/prompts/strategy_map_prompts.py)

```python
DESIGN_STRATEGY_MAP_PROMPT = """
Você é um consultor BSC sênior especialista em Strategy Maps (Kaplan & Norton framework).

Converta o diagnóstico BSC em Strategy Map estruturado com 4 perspectivas balanceadas.

DIAGNÓSTICO BSC:
{diagnostic}

CONTEXTO RAG - LITERATURA BSC (Kaplan & Norton):
{rag_context}

IMPORTANTE: Use o contexto RAG acima para:
- Validar objectives contra framework K&N oficial
- Sugerir KPIs baseados em benchmarks da indústria
- Mapear causa-efeito usando conexões validadas na literatura
- Evitar jargon usando terminologia BSC oficial

FRAMEWORK STRATEGY MAP (Kaplan & Norton 2025):
- 4 Perspectivas: Financial, Customer, Process, Learning/Growth
- 8-10 objetivos estratégicos por perspectiva (RED FLAG se >10)
- Cada objetivo: goal + rationale + leading KPI + lagging KPI
- Conexões causa-efeito: Learning -> Process -> Customer -> Financial

REGRAS CRÍTICAS (validadas BSCDesigner 2025):
1. Goals ESTRATÉGICOS (não operacionais: "implementar ERP" é operacional [ERRO])
2. Goals com CONEXÕES (não isolated)
3. Rationale EXPLÍCITO (WHY escolheu esse goal)
4. KPIs SMART (específicos, mensuráveis)
5. SEM jargon genérico ("leverage synergies" [ERRO], "optimize resources" [ERRO])

EXEMPLOS DO RAG CONTEXT:
Use os exemplos de Strategy Maps recuperados do contexto RAG como referência
para objectives, KPIs e conexões causa-efeito validados pela literatura.

RETORNE JSON:
{{
  "financial": {{
    "objectives": [
      {{
        "title": "Aumentar EBITDA para 18% através de eficiência operacional",
        "rationale": "Crescimento sustentável requer margem EBITDA >15% para reinvestimento em inovação e capacitação, baseado em benchmark setor manufatura (literatura BSC: 15-20% típico para PMEs industriais)",
        "leading_kpis": ["Custo por unidade produzida", "Produtividade por FTE"],
        "lagging_kpis": ["Margem EBITDA %", "ROI"]
      }},
      ...
    ]
  }},
  "customer": {{ ... }},
  "process": {{ ... }},
  "learning": {{ ... }},
  "cause_effect_connections": [
    {{
      "source": "learning_obj_1",
      "target": "process_obj_2",
      "type": "enables",
      "strength": "strong",
      "rationale": "Certificação Lean Six Sigma Green Belt (120h) capacita equipe a identificar e eliminar waste, habilitando redução de 30% no lead time através de VSM e eliminação de gargalos (validado em literatura BSC: correlação típica 0.7-0.8 entre treinamento e melhoria de processos)"
    }}
  ],
  "strategic_priorities": ["Excelência Operacional", "Inovação Produto", "Customer Intimacy"]
}}
"""

MAP_CAUSE_EFFECT_PROMPT = """
Mapeie conexões causa-efeito entre objetivos estratégicos.

FRAMEWORK (Kaplan & Norton):
- Learning ENABLES Process (ex: treinamento -> melhoria processos)
- Process DRIVES Customer (ex: qualidade -> satisfação)
- Customer DRIVES Financial (ex: retenção -> receita)

OBJETIVOS POR PERSPECTIVA:
{objectives}

REGRAS:
- Mínimo 1 conexão por objetivo (não isolated)
- Rationale específico (não genérico)
- Tipos: "enables", "drives", "supports"

RETORNE lista de conexões causa-efeito.
"""
```

### Workflow Integration (src/graph/workflow.py)

```python
def design_solution(self, state: BSCState) -> dict[str, Any]:
    """
    Node: Gera Strategy Map a partir do diagnóstico aprovado.

    Routing:
    APPROVAL_PENDING (aprovado) -> SOLUTION_DESIGN -> design_solution()

    Best Practice: Reutilizar ferramentas existentes (FASE 3).
    """
    logger.info("[SOLUTION_DESIGN] Gerando Strategy Map...")

    # ETAPA 1: Chamar Strategy_Map_Designer_Tool
    strategy_map = self.strategy_map_designer.design_strategy_map(
        diagnostic=state.diagnostic,
        tools_results=state.diagnostic_tools_results
    )

    # ETAPA 2: Validar alinhamento
    alignment_report = self.alignment_validator.validate_alignment(strategy_map)

    # ETAPA 3: Decidir próximo estado
    if alignment_report.score >= 80:
        # Strategy Map aprovado
        return {
            "strategy_map": strategy_map,
            "alignment_report": alignment_report,
            "current_phase": ConsultingPhase.SOLUTION_DESIGN,
            "final_response": self._format_strategy_map_response(strategy_map)
        }
    else:
        # Strategy Map precisa refinamento
        return {
            "strategy_map": strategy_map,
            "alignment_report": alignment_report,
            "current_phase": ConsultingPhase.REFINEMENT,
            "final_response": f"Strategy Map gerado mas score {alignment_report.score:.0f}/100. Gaps: {', '.join(alignment_report.gaps[:3])}"
        }
```

---

## [EMOJI] TAREFAS DETALHADAS

### Tarefa 2.1: Schema StrategyMap (2h)

**Objetivo:** Criar schemas Pydantic validados para Strategy Map.

**Arquivos:**
- `src/memory/schemas.py` (+150 linhas)

**Schemas a Criar:**
1. `CauseEffectConnection` - Conexão causa-efeito
2. `StrategyMapPerspective` - Perspectiva com objetivos
3. `StrategyMap` - Container principal
4. `AlignmentReport` - Report de validação

**DoD:**
- [ ] 4 schemas criados e validados
- [ ] Type hints completos
- [ ] Docstrings em português
- [ ] Examples em Field() onde aplicável
- [ ] 10+ testes unitários (fixtures válidas)

---

### Tarefa 2.2: Strategy_Map_Designer_Tool (6-8h)

**Objetivo:** Implementar tool que converte diagnóstico em Strategy Map.

**Arquivos:**
- `src/tools/strategy_map_designer.py` (+300 linhas)
- `src/prompts/strategy_map_prompts.py` (+200 linhas)

**Métodos Principais:**
1. `design_strategy_map()` - Entry point
2. `_extract_objectives_by_perspective()` - Reutiliza StrategicObjectivesTool
3. `_define_kpis_for_objectives()` - Reutiliza KPIDefinerTool
4. `_map_cause_effect_connections()` - **CORE** do Sprint 2 (causa-efeito LLM)
5. `_identify_strategic_priorities()` - Top 3 priorities

**DoD:**
- [ ] Tool implementado e testado
- [ ] Reutiliza StrategicObjectivesTool e KPIDefinerTool
- [ ] Causa-efeito mapeado com LLM
- [ ] 12+ testes unitários (mocks + fixtures)
- [ ] 2 testes E2E com LLM real

---

### Tarefa 2.3: Alignment_Validator_Tool (2-3h)

**Objetivo:** Validar balanceamento e completude do Strategy Map.

**Arquivos:**
- `src/tools/alignment_validator.py` (+200 linhas)

**8 Validações:**
1. `_check_balanced_perspectives()` - 2-10 objectives cada
2. `_check_objectives_have_kpis()` - ≥1 KPI por objective
3. `_check_cause_effect_exists()` - ≥4 connections
4. `_check_no_isolated_objectives()` - Todos conectados
5. `_check_kpis_are_smart()` - KPIs mensuráveis
6. `_check_goals_are_strategic()` - Não operacionais
7. `_check_has_rationale()` - Rationale explicado
8. `_check_no_jargon()` - Sem jargon genérico

**DoD:**
- [ ] Tool implementado e testado
- [ ] 8 validações executadas
- [ ] Score 0-100 calculado
- [ ] Gaps e recommendations gerados
- [ ] 10+ testes unitários (edge cases)

---

### Tarefa 2.4: Node design_solution() (4-6h)

**Objetivo:** Integrar Strategy Map Designer no LangGraph workflow.

**Arquivos:**
- `src/graph/workflow.py` (+80 linhas)
- `src/graph/states.py` (+2 fields: strategy_map, alignment_report)

**Implementação:**
1. Node `design_solution()` - Gera Strategy Map
2. Routing: APPROVAL_PENDING -> SOLUTION_DESIGN
3. Conditional routing: score ≥80 -> SOLUTION_DESIGN | <80 -> REFINEMENT

**DoD:**
- [ ] Node implementado e testado
- [ ] State expandido com strategy_map field
- [ ] Routing condicional funcional
- [ ] 8+ testes unitários (mocks)
- [ ] 2 testes E2E (workflow completo)

---

### Tarefa 2.5: UI Streamlit (6-8h)

**Objetivo:** Visualizar Strategy Map com 4 perspectivas e causa-efeito.

**Arquivos:**
- `app/pages/strategy_map.py` (+400 linhas)

**Features:**
1. **4 Perspectivas em Grid** (2x2 layout)
2. **Cards por Objective** (title, rationale, KPIs, initiatives)
3. **Diagrama Causa-Efeito** (Mermaid ou Plotly)
4. **Alignment Score** (gauge chart 0-100)
5. **Gaps & Recommendations** (expander)

**DoD:**
- [ ] Página strategy_map.py criada
- [ ] 4 perspectivas visualizadas
- [ ] Diagrama causa-efeito renderizado
- [ ] Alignment score visível
- [ ] UI responsiva e profissional

---

### Tarefa 2.6: Documentação (2h)

**Objetivo:** Documentar implementação completa Sprint 2.

**Arquivos:**
- `docs/sprints/SPRINT_2_IMPLEMENTATION_SUMMARY.md` (+800 linhas)
- `docs/architecture/STRATEGY_MAP_ARCHITECTURE.md` (+600 linhas)

**Conteúdo:**
1. Research Brightdata (8 steps validados)
2. Arquitetura (schemas, tools, prompts, workflow)
3. Métricas (latência, alignment score, coverage)
4. Lições aprendidas
5. Próximos passos Sprint 3

**DoD:**
- [ ] Documentação técnica completa
- [ ] Diagrama Mermaid arquitetura
- [ ] Exemplos de código
- [ ] Referências (BSCDesigner, Kaplan & Norton)

---

## [EMOJI] MÉTRICAS DE SUCESSO

**KPIs Sprint 2:**
- [OK] Strategy Map com 4 perspectivas balanceadas (2-10 objectives cada)
- [OK] ≥4 conexões causa-efeito mapeadas
- [OK] Alignment Score ≥80/100 em 80% dos casos
- [OK] UI Streamlit funcional e profissional
- [OK] Latência design_solution() <30s (P95)
- [OK] 100% testes passando (42+ unitários + 4 E2E)
- [OK] Coverage >85% em strategy_map_designer.py

**Critérios de Aceitação:**
- [ ] `design_solution()` node integrado no workflow
- [ ] Strategy Map gerado automaticamente após diagnóstico aprovado
- [ ] 8 validações executadas (AlignmentValidator)
- [ ] UI Streamlit mostra 4 perspectivas + causa-efeito
- [ ] Diagrama causa-efeito renderizado (Mermaid ou Plotly)
- [ ] Zero regressões em testes existentes (27 E2E passando)
- [ ] Documentação completa criada

---

## [WARN] RISCOS E MITIGAÇÕES

**Risco 1: LLM não consegue mapear causa-efeito bem**
- **Probabilidade**: MÉDIA
- **Impacto**: ALTO (core do Sprint 2)
- **Mitigação**: Prompt estruturado com framework K&N, examples no schema, fallback para heurísticas

**Risco 2: Alignment score sempre baixo (<80)**
- **Probabilidade**: BAIXA
- **Impacto**: MÉDIO (muitos refinements)
- **Mitigação**: Validações realistas, thresholds ajustáveis, warnings vs erros

**Risco 3: UI causa-efeito complexa demais**
- **Probabilidade**: ALTA
- **Impacto**: MÉDIO (atraso UI)
- **Mitigação**: Começar com Mermaid simples, iterar depois para Plotly

---

## [EMOJI] ESFORÇO E ROI

**Esforço Total**: 22-29h (3-4 dias)

**ROI**: [EMOJI] ALTO
- Strategy Map é core do BSC (Kaplan & Norton)
- Visualização facilita discussão estratégica
- Base para Sprint 3-6 (Action Plans, Cascading)

**Prioridade**: [EMOJI] ALTA (após Sprint 1 completo)

---

**Última Atualização:** 2025-11-20
**Próxima Revisão:** Após conclusão Tarefa 2.1
