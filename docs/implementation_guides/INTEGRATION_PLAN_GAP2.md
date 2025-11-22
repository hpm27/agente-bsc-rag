# [EMOJI] INTEGRATION PLAN - GAP #2: Ferramentas no Diagnóstico

**Versão**: 1.0
**Data**: 2025-11-20
**Sprint**: Sprint 1 (Semana 1)
**Prioridade**: [EMOJI] CRÍTICA

---

## [EMOJI] PROBLEMA (GAP #2)

### Situação Atual

**O QUE TEMOS**:
- [OK] 7 ferramentas consultivas implementadas e testadas (FASE 3)
- [OK] DiagnosticAgent com métodos wrapper para cada ferramenta
- [OK] Testes unitários para cada ferramenta (coverage >85%)

**O QUE FALTA**:
- [ERRO] `run_diagnostic()` NÃO chama nenhuma ferramenta
- [ERRO] Diagnóstico atual usa APENAS: 4 agentes BSC + RAG + consolidação LLM
- [ERRO] 70% do valor da FASE 3 desperdiçado

### Impacto

**Diagnóstico Atual (sem ferramentas)**:
```
ETAPA 1: run_parallel_analysis() -> 4 agentes BSC (Financial, Customer, Process, Learning)
ETAPA 2: consolidate_diagnostic() -> LLM consolida outputs dos 4 agentes
OUTPUT: Diagnóstico genérico
```

**Diagnóstico Desejado (com ferramentas)**:
```
ETAPA 1: run_parallel_analysis() -> 4 agentes BSC
ETAPA 2: _run_consultative_tools() -> 7 ferramentas consultivas (NOVO!)
ETAPA 3: consolidate_diagnostic() -> LLM consolida tudo (agentes + ferramentas)
OUTPUT: Diagnóstico rico e estruturado
```

**Valor Agregado**:
- SWOT Analysis (4 quadrantes)
- Five Whys (root causes)
- KPI Framework (métricas SMART)
- Strategic Objectives (objetivos alinhados)
- Benchmarking (comparação mercado)
- Issue Tree (decomposição problemas)
- Prioritization Matrix (Impact/Effort)

---

## [EMOJI] OBJETIVO DO SPRINT 1

**Goal**: Integrar 7 ferramentas consultivas no `run_diagnostic()` com latência adicional <60s.

**Success Criteria**:
- [  ] 7/7 ferramentas executam em paralelo
- [ ] Latência adicional <60s (P95)
- [ ] 100% testes E2E passando
- [ ] DiagnosticToolsResult schema criado
- [ ] `consolidate_diagnostic()` usa outputs das ferramentas

---

## [EMOJI] IMPLEMENTAÇÃO TÉCNICA

### Tarefa 1: Criar Schema DiagnosticToolsResult

**Arquivo**: `src/memory/schemas.py`

**Implementação**:
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DiagnosticToolsResult(BaseModel):
    """
    Agregador de outputs das 7 ferramentas consultivas.

    Usado em run_diagnostic() para passar resultados das ferramentas
    para consolidate_diagnostic().
    """

    # Ferramentas consultivas
    swot_analysis: Optional[SWOTAnalysisResult] = Field(
        None,
        description="SWOT Analysis (4 quadrantes)"
    )

    five_whys_analysis: Optional[FiveWhysResult] = Field(
        None,
        description="Five Whys root cause analysis"
    )

    kpi_framework: Optional[KPIFrameworkResult] = Field(
        None,
        description="KPI Framework completo"
    )

    strategic_objectives: Optional[StrategicObjectivesResult] = Field(
        None,
        description="Strategic Objectives SMART"
    )

    benchmarking_report: Optional[BenchmarkingResult] = Field(
        None,
        description="Benchmarking vs mercado"
    )

    issue_tree: Optional[IssueTreeResult] = Field(
        None,
        description="Issue Tree decomposição"
    )

    prioritization_matrix: Optional[PrioritizationMatrixResult] = Field(
        None,
        description="Prioritization Matrix Impact/Effort"
    )

    # Metadata de execução
    execution_time: float = Field(
        ...,
        description="Tempo total de execução das ferramentas (segundos)"
    )

    tools_executed: List[str] = Field(
        default_factory=list,
        description="Lista de ferramentas executadas com sucesso"
    )

    tools_failed: List[str] = Field(
        default_factory=list,
        description="Lista de ferramentas que falharam"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de criação"
    )
```

**DoD**:
- [ ] Schema criado em `src/memory/schemas.py`
- [ ] Type hints completos
- [ ] Docstrings em português brasileiro
- [ ] Validado com testes unitários

---

### Tarefa 2: Implementar _run_consultative_tools()

**Arquivo**: `src/agents/diagnostic_agent.py`

**Implementação**:
```python
import asyncio
import time
from typing import Dict, Any
from src.memory.schemas import DiagnosticToolsResult

async def _run_consultative_tools(
    self,
    context: Dict[str, Any],
    parallel_results: List[DiagnosticResult]
) -> DiagnosticToolsResult:
    """
    SPRINT 1: Executa 7 ferramentas consultivas em paralelo.

    Args:
        context: Contexto do cliente (company, strategic_context)
        parallel_results: Outputs dos 4 agentes BSC

    Returns:
        DiagnosticToolsResult com outputs de todas ferramentas

    Raises:
        Exception: Se TODAS ferramentas falharem (crítico)
    """
    start_time = time.time()

    logger.info("[DIAGNOSTIC] [TOOLS] Executando 7 ferramentas consultivas...")

    # ETAPA 1: Preparar tasks async para execução paralela
    tasks = [
        self._run_tool_safe("swot", self.generate_swot_analysis, context, parallel_results),
        self._run_tool_safe("five_whys", self.generate_five_whys_analysis, context, parallel_results),
        self._run_tool_safe("kpi", self.generate_kpi_framework, context, parallel_results),
        self._run_tool_safe("objectives", self.generate_strategic_objectives, context, parallel_results),
        self._run_tool_safe("benchmarking", self.generate_benchmarking_report, context, parallel_results),
        self._run_tool_safe("issue_tree", self.generate_issue_tree_analysis, context, parallel_results),
        self._run_tool_safe("prioritization", self.generate_prioritization_matrix, context, parallel_results),
    ]

    # ETAPA 2: Executar em paralelo com asyncio.gather
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # ETAPA 3: Processar results
    tools_executed = []
    tools_failed = []

    swot, five_whys, kpi, objectives, benchmarking, issue_tree, prioritization = results

    # Validar cada result
    if not isinstance(swot, Exception):
        tools_executed.append("swot_analysis")
    else:
        tools_failed.append("swot_analysis")
        logger.error(f"[TOOLS] SWOT failed: {swot}")
        swot = None

    if not isinstance(five_whys, Exception):
        tools_executed.append("five_whys")
    else:
        tools_failed.append("five_whys")
        logger.error(f"[TOOLS] Five Whys failed: {five_whys}")
        five_whys = None

    # ... (repetir para todas ferramentas)

    execution_time = time.time() - start_time

    logger.info(
        f"[DIAGNOSTIC] [TOOLS] Concluído em {execution_time:.2f}s | "
        f"Sucesso: {len(tools_executed)}/7 | "
        f"Falhas: {len(tools_failed)}/7"
    )

    # ETAPA 4: Se TODAS falharam, raise Exception (crítico)
    if len(tools_failed) == 7:
        raise Exception("CRITICAL: Todas 7 ferramentas consultivas falharam!")

    # ETAPA 5: Retornar result
    return DiagnosticToolsResult(
        swot_analysis=swot,
        five_whys_analysis=five_whys,
        kpi_framework=kpi,
        strategic_objectives=objectives,
        benchmarking_report=benchmarking,
        issue_tree=issue_tree,
        prioritization_matrix=prioritization,
        execution_time=execution_time,
        tools_executed=tools_executed,
        tools_failed=tools_failed
    )


async def _run_tool_safe(
    self,
    tool_name: str,
    tool_method: callable,
    context: Dict[str, Any],
    parallel_results: List[DiagnosticResult]
) -> Any:
    """
    Wrapper seguro para executar ferramenta com tratamento de erro.

    Args:
        tool_name: Nome da ferramenta (para logs)
        tool_method: Método a ser executado
        context: Contexto do cliente
        parallel_results: Outputs dos 4 agentes BSC

    Returns:
        Output da ferramenta OU Exception (se falhar)
    """
    try:
        logger.info(f"[TOOLS] [{tool_name}] Iniciando...")
        result = await tool_method(context, parallel_results)
        logger.info(f"[TOOLS] [{tool_name}] Concluído com sucesso")
        return result
    except Exception as e:
        logger.error(f"[TOOLS] [{tool_name}] ERRO: {str(e)}")
        return e  # Retornar Exception (asyncio.gather vai capturar)
```

**DoD**:
- [ ] Método `_run_consultative_tools()` implementado
- [ ] Método `_run_tool_safe()` implementado (error handling)
- [ ] Ferramentas executam em paralelo (asyncio.gather)
- [ ] Logs estruturados (sucesso/falha por ferramenta)
- [ ] Validado com testes unitários

---

### Tarefa 3: Refatorar run_diagnostic()

**Arquivo**: `src/agents/diagnostic_agent.py`

**Implementação**:
```python
async def run_diagnostic(
    self,
    context: Dict[str, Any]
) -> CompleteDiagnostic:
    """
    Executa diagnóstico BSC completo.

    SPRINT 1: Adicionada ETAPA 2 (ferramentas consultivas).

    Args:
        context: Contexto do cliente (company, strategic_context)

    Returns:
        CompleteDiagnostic completo
    """
    logger.info("[DIAGNOSTIC] Iniciando diagnóstico BSC completo...")

    # ETAPA 1: Análise paralela (4 agentes BSC) - JÁ EXISTE
    logger.info("[DIAGNOSTIC] ETAPA 1: Análise paralela (4 agentes BSC)...")
    parallel_results = await self.run_parallel_analysis(context)

    # ETAPA 2: Análises consultivas (7 ferramentas) - NOVO (SPRINT 1)!
    logger.info("[DIAGNOSTIC] ETAPA 2: Análises consultivas (7 ferramentas)...")
    tools_results = await self._run_consultative_tools(context, parallel_results)

    # ETAPA 3: Consolidação enriquecida - MODIFICADO (SPRINT 1)
    logger.info("[DIAGNOSTIC] ETAPA 3: Consolidação enriquecida...")
    diagnostic = await self.consolidate_diagnostic(
        parallel_results,
        tools_results  # Novo parâmetro!
    )

    logger.info("[DIAGNOSTIC] Diagnóstico BSC completo concluído")

    return diagnostic
```

**DoD**:
- [ ] `run_diagnostic()` refatorado com 3 etapas
- [ ] ETAPA 2 chama `_run_consultative_tools()`
- [ ] ETAPA 3 passa `tools_results` para `consolidate_diagnostic()`
- [ ] Logs estruturados
- [ ] Validado com testes E2E

---

### Tarefa 4: Modificar consolidate_diagnostic()

**Arquivo**: `src/agents/diagnostic_agent.py`

**Implementação**:
```python
async def consolidate_diagnostic(
    self,
    parallel_results: List[DiagnosticResult],
    tools_results: DiagnosticToolsResult  # NOVO PARÂMETRO!
) -> CompleteDiagnostic:
    """
    Consolida outputs dos 4 agentes BSC + 7 ferramentas consultivas.

    SPRINT 1: Modificado para aceitar tools_results e enriquecer prompt.

    Args:
        parallel_results: Outputs dos 4 agentes BSC
        tools_results: Outputs das 7 ferramentas consultivas

    Returns:
        CompleteDiagnostic com recomendações priorizadas
    """
    logger.info("[DIAGNOSTIC] [CONSOLIDATION] Iniciando consolidação...")

    # ETAPA 1: Preparar contexto dos 4 agentes BSC (JÁ EXISTE)
    context_4_perspectives = self._format_parallel_results(parallel_results)

    # ETAPA 2: Preparar contexto das 7 ferramentas (NOVO - SPRINT 1)
    context_tools = self._format_tools_results(tools_results)

    # ETAPA 3: Prompt enriquecido (MODIFICADO - SPRINT 1)
    prompt = f"""
Você é um consultor BSC sênior da McKinsey consolidando diagnóstico completo.

# ANÁLISES DAS 4 PERSPECTIVAS BSC

{context_4_perspectives}

# ANÁLISES CONSULTIVAS COMPLEMENTARES

{context_tools}

# TAREFA

Consolide em diagnóstico BSC completo com:
1. Executive Summary (2-3 parágrafos)
2. Insights key por perspectiva (use análises consultivas!)
3. Recomendações priorizadas (HIGH/MEDIUM/LOW) baseadas em:
   - SWOT (oportunidades e ameaças)
   - Five Whys (root causes)
   - Prioritization Matrix (Impact/Effort)
   - KPIs sugeridos
   - Strategic Objectives alinhados

Seja acionável e específico. Use dados das análises consultivas para embasar recomendações.
"""

    # ETAPA 4: Chamar LLM (JÁ EXISTE)
    diagnostic = await self.llm.ainvoke(prompt)

    logger.info("[DIAGNOSTIC] [CONSOLIDATION] Consolidação concluída")

    return diagnostic


def _format_tools_results(self, tools_results: DiagnosticToolsResult) -> str:
    """
    Formata outputs das 7 ferramentas para o prompt.

    Args:
        tools_results: Outputs das ferramentas

    Returns:
        String formatada para o prompt
    """
    sections = []

    # SWOT Analysis
    if tools_results.swot_analysis:
        sections.append(f"""
## SWOT ANALYSIS

**Forças (Strengths):**
{chr(10).join(f"- {s}" for s in tools_results.swot_analysis.strengths)}

**Fraquezas (Weaknesses):**
{chr(10).join(f"- {w}" for w in tools_results.swot_analysis.weaknesses)}

**Oportunidades (Opportunities):**
{chr(10).join(f"- {o}" for o in tools_results.swot_analysis.opportunities)}

**Ameaças (Threats):**
{chr(10).join(f"- {t}" for t in tools_results.swot_analysis.threats)}
""")

    # Five Whys
    if tools_results.five_whys_analysis:
        sections.append(f"""
## FIVE WHYS (ROOT CAUSES)

**Problema:** {tools_results.five_whys_analysis.problem}

**Root Causes Identificados:**
{chr(10).join(f"- Why {i+1}: {why}" for i, why in enumerate(tools_results.five_whys_analysis.whys))}

**Root Cause Final:** {tools_results.five_whys_analysis.root_cause}
""")

    # KPI Framework
    if tools_results.kpi_framework:
        kpis_by_perspective = {}
        for kpi in tools_results.kpi_framework.kpis:
            if kpi.perspective not in kpis_by_perspective:
                kpis_by_perspective[kpi.perspective] = []
            kpis_by_perspective[kpi.perspective].append(kpi)

        kpi_section = "## KPI FRAMEWORK\n\n"
        for perspective, kpis in kpis_by_perspective.items():
            kpi_section += f"**{perspective.title()} Perspective:**\n"
            for kpi in kpis:
                kpi_section += f"- {kpi.name}: {kpi.description} (Target: {kpi.target} {kpi.unit})\n"
            kpi_section += "\n"

        sections.append(kpi_section)

    # Strategic Objectives
    if tools_results.strategic_objectives:
        obj_section = "## STRATEGIC OBJECTIVES\n\n"
        for obj in tools_results.strategic_objectives.objectives:
            obj_section += f"**{obj.perspective.title()}:** {obj.description}\n"
        sections.append(obj_section)

    # Benchmarking
    if tools_results.benchmarking_report:
        sections.append(f"""
## BENCHMARKING

**Setor:** {tools_results.benchmarking_report.sector}

**Gaps Identificados:**
{chr(10).join(f"- {gap.metric}: Empresa {gap.company_value} vs Mercado {gap.market_average} (Gap: {gap.gap}%)" for gap in tools_results.benchmarking_report.gaps)}
""")

    # Prioritization Matrix
    if tools_results.prioritization_matrix:
        sections.append(f"""
## PRIORITIZATION MATRIX (Impact/Effort)

**High Impact, Low Effort (QUICK WINS):**
{chr(10).join(f"- {item.name}" for item in tools_results.prioritization_matrix.items if item.quadrant == "quick_wins")}

**High Impact, High Effort (MAJOR PROJECTS):**
{chr(10).join(f"- {item.name}" for item in tools_results.prioritization_matrix.items if item.quadrant == "major_projects")}
""")

    return "\n\n".join(sections)
```

**DoD**:
- [ ] `consolidate_diagnostic()` aceita `tools_results`
- [ ] Método `_format_tools_results()` implementado
- [ ] Prompt enriquecido usa TODAS ferramentas
- [ ] Validado com testes E2E

---

## [EMOJI] TESTES

### Testes Unitários (Novos)

**Arquivo**: `tests/test_diagnostic_tools_integration.py`

```python
import pytest
from src.agents.diagnostic_agent import DiagnosticAgent
from src.memory.schemas import DiagnosticToolsResult

@pytest.mark.asyncio
async def test_run_consultative_tools_all_success(diagnostic_agent, context):
    """Validar que 7 ferramentas executam com sucesso."""
    parallel_results = []  # Mock

    tools_results = await diagnostic_agent._run_consultative_tools(context, parallel_results)

    assert isinstance(tools_results, DiagnosticToolsResult)
    assert len(tools_results.tools_executed) == 7
    assert len(tools_results.tools_failed) == 0
    assert tools_results.execution_time < 60  # Latência <60s


@pytest.mark.asyncio
async def test_run_consultative_tools_partial_failure(diagnostic_agent, context, monkeypatch):
    """Validar que sistema continua mesmo se 1-2 ferramentas falharem."""
    # Mock: Five Whys falha
    async def mock_five_whys_fail(*args, **kwargs):
        raise Exception("Five Whys mock error")

    monkeypatch.setattr(diagnostic_agent, "generate_five_whys_analysis", mock_five_whys_fail)

    parallel_results = []
    tools_results = await diagnostic_agent._run_consultative_tools(context, parallel_results)

    assert len(tools_results.tools_executed) == 6
    assert len(tools_results.tools_failed) == 1
    assert "five_whys" in tools_results.tools_failed


@pytest.mark.asyncio
async def test_format_tools_results(diagnostic_agent):
    """Validar formatação de tools_results para prompt."""
    # Mock DiagnosticToolsResult
    tools_results = DiagnosticToolsResult(
        swot_analysis=...,
        five_whys_analysis=...,
        execution_time=30.5,
        tools_executed=["swot", "five_whys", "kpi"]
    )

    formatted = diagnostic_agent._format_tools_results(tools_results)

    assert "SWOT ANALYSIS" in formatted
    assert "FIVE WHYS" in formatted
    assert "KPI FRAMEWORK" in formatted
```

---

### Testes E2E (Modificados)

**Arquivo**: `tests/test_workflow_e2e.py`

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_diagnostic_with_tools_integration(workflow, client_profile):
    """
    SPRINT 1: Validar diagnóstico completo com 7 ferramentas integradas.
    """
    # GIVEN: Cliente com profile completo
    state = BSCState(
        query="Realizar diagnóstico BSC completo",
        client_profile=client_profile,
        current_phase=ConsultingPhase.DISCOVERY
    )

    # WHEN: Executar discovery
    result = await workflow.discovery(state)

    # THEN: Validar diagnóstico
    assert result["diagnostic"] is not None
    assert result["diagnostic_tools_results"] is not None  # NOVO!

    # Validar 7 ferramentas executadas
    tools_results = result["diagnostic_tools_results"]
    assert len(tools_results.tools_executed) >= 5  # Mínimo 5/7 sucesso

    # Validar diagnóstico menciona ferramentas
    diagnostic = result["diagnostic"]
    assert "SWOT" in diagnostic.executive_summary or any("SWOT" in rec.description for rec in diagnostic.recommendations)
    assert "Five Whys" in diagnostic.executive_summary or any("root cause" in rec.description.lower() for rec in diagnostic.recommendations)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_diagnostic_latency_with_tools(workflow, client_profile):
    """
    SPRINT 1: Validar latência P95 <5 min com ferramentas integradas.
    """
    import time

    state = BSCState(
        query="Realizar diagnóstico BSC completo",
        client_profile=client_profile,
        current_phase=ConsultingPhase.DISCOVERY
    )

    start_time = time.time()
    result = await workflow.discovery(state)
    elapsed_time = time.time() - start_time

    # Latência P95 <5 min (300s)
    assert elapsed_time < 300, f"Latência {elapsed_time:.2f}s > 300s (P95 target)"

    # Validar ferramentas executaram
    assert result["diagnostic_tools_results"] is not None
```

---

## [EMOJI] MÉTRICAS DE SUCESSO

### KPIs Sprint 1

**Integração**:
- [OK] 7/7 ferramentas integradas no diagnóstico
- [OK] 100% testes E2E passando (27 testes)
- [OK] Zero regressões detectadas

**Performance**:
- [OK] Latência adicional <60s (P95)
- [OK] Latência total diagnóstico <5 min (P95)
- [OK] Ferramentas executam em paralelo (asyncio.gather)

**Qualidade**:
- [OK] Coverage >85% em diagnostic_agent.py
- [OK] Diagnóstico tem seções SWOT, Five Whys, KPIs visíveis
- [OK] Judge Approval Rate mantido (>80%)

---

## [EMOJI] EXECUÇÃO

### Baseline ANTES (OBRIGATÓRIO)

```bash
# 1. Executar suite E2E completa
pytest tests/test_workflow_e2e.py -v --tb=long 2>&1 > baseline_e2e.log

# 2. Capturar métricas
# - Latência P50/P95/Mean
# - Judge Approval Rate
# - Answer Relevancy (RAGAS)

# 3. Documentar baseline
# - Diagnóstico SEM ferramentas (output atual)
# - Métricas atuais
```

### Implementação

**Ordem de execução**:
1. Criar schema `DiagnosticToolsResult` (1-2h)
2. Implementar `_run_consultative_tools()` (3-4h)
3. Implementar `_run_tool_safe()` (1h)
4. Refatorar `run_diagnostic()` (1h)
5. Modificar `consolidate_diagnostic()` (2-3h)
6. Implementar `_format_tools_results()` (2h)
7. Criar testes unitários (2-3h)
8. Criar testes E2E (2-3h)
9. Executar suite completa (1h)
10. Documentação (2h)

**Esforço Total**: 17-22h (2-3 dias)

---

## [EMOJI] NEXT STEPS

**HOJE**:
- [OK] Documentação completa (este documento)

**PRÓXIMA SESSÃO (Sessão 37)**:
- [EMOJI] Executar baseline E2E
- [EMOJI] Implementar Tarefa 1 (Schema DiagnosticToolsResult)
- [EMOJI] Implementar Tarefa 2 (_run_consultative_tools)

---

**Última Atualização**: 2025-11-20
**Status**: [OK] PLANO APROVADO - Pronto para implementação Sprint 1
