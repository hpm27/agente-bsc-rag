# Milestone Tracker Tool - Documentacao Tecnica

**Sprint 4.2 - Action Plans MVP**
**Data**: 25 Nov 2025
**Versao**: 1.0

---

## Visao Geral

O **MilestoneTrackerTool** e uma ferramenta para rastrear o progresso de implementacao de Action Plans BSC. Gera milestones a partir de ActionItems e calcula metricas de acompanhamento, identificando riscos e gerando recomendacoes.

### Objetivos

1. Converter Action Items em Milestones rastreraveis
2. Calcular progresso geral do plano de acao
3. Identificar caminho critico e riscos
4. Gerar recomendacoes para mitigar atrasos

---

## Arquitetura

### Fluxo de Dados

```
ActionPlan (input)
    |
    v
MilestoneTrackerTool.generate_milestones_from_action_plan()
    |
    +-> _create_milestones_from_actions()
    |       - Para cada ActionItem, cria Milestone
    |       - Determina status baseado em datas
    |       - Estima progresso baseado em tempo decorrido
    |
    +-> _identify_critical_path()
    |       - Milestones em risco
    |       - Milestones com muitas dependencias
    |
    +-> _get_next_due_milestones()
    |       - Proximos prazos
    |
    +-> _generate_recommendations()
    |       - Baseado em status e riscos
    |
    +-> _generate_summary()
            - Resumo executivo
    |
    v
MilestoneTrackerReport (output)
```

### Schemas Pydantic

#### Milestone

```python
class Milestone(BaseModel):
    name: str                    # Nome do milestone
    description: str             # Descricao detalhada
    action_item_ref: str         # Referencia ao ActionItem
    status: Literal[             # Status atual
        "NOT_STARTED",
        "IN_PROGRESS",
        "COMPLETED",
        "BLOCKED",
        "AT_RISK"
    ]
    progress_percent: float      # 0-100
    target_date: str             # YYYY-MM-DD
    actual_date: str | None      # Data real conclusao
    responsible: str             # Responsavel
    dependencies: list[str]      # Dependencias
    blockers: list[str]          # Impedimentos
    notes: str | None            # Notas
```

#### MilestoneTrackerReport

```python
class MilestoneTrackerReport(BaseModel):
    milestones: list[Milestone]
    total_milestones: int
    completed_count: int
    in_progress_count: int
    at_risk_count: int
    overall_progress: float      # Media dos milestones
    critical_path: list[str]     # Milestones criticos
    next_due_milestones: list[str]
    summary: str
    recommendations: list[str]
    tracked_at: datetime
```

---

## Implementacao

### Localizacao

- **Tool**: `src/tools/milestone_tracker.py`
- **Schemas**: `src/memory/schemas.py` (Milestone, MilestoneTrackerReport)
- **Testes**: `tests/test_sprint4_milestone_tracker.py`, `tests/test_sprint4_e2e.py`

### Uso Basico

```python
from src.tools.milestone_tracker import MilestoneTrackerTool
from src.memory.schemas import ActionPlan

# Inicializar tool
tracker = MilestoneTrackerTool()

# Gerar milestones a partir de action plan
report = await tracker.generate_milestones_from_action_plan(
    action_plan=action_plan,
    current_date="2025-12-15",  # Opcional, default = hoje
)

# Acessar resultados
print(f"Progresso: {report.overall_progress}%")
print(f"Em risco: {report.at_risk_count}")
print(f"Recomendacoes: {report.recommendations}")
```

### Determinacao de Status

O status do milestone e calculado automaticamente baseado em:

1. **NOT_STARTED**: Data atual < start_date do ActionItem
2. **IN_PROGRESS**: Data atual >= start_date e <= due_date
3. **AT_RISK**: Data atual > due_date OU (>80% tempo decorrido E prioridade HIGH)
4. **BLOCKED**: Definido manualmente via blockers
5. **COMPLETED**: Definido manualmente (status = "COMPLETED")

### Calculo de Progresso

```python
# Progresso estimado baseado em tempo decorrido
days_elapsed = (current_date - start_date).days
days_total = (due_date - start_date).days
raw_progress = (days_elapsed / days_total) * 100

# Ajuste por esforco
if effort == "HIGH":
    progress = raw_progress * 0.7
elif effort == "MEDIUM":
    progress = raw_progress * 0.85
else:
    progress = raw_progress

# Overall progress = media dos milestones
overall_progress = sum(m.progress_percent for m in milestones) / len(milestones)
```

### Caminho Critico

O caminho critico inclui:

1. Milestones com status AT_RISK ou BLOCKED
2. Milestones que sao dependencia de 2+ outros milestones

```python
critical_path = [
    m.name for m in milestones
    if m.status in ["AT_RISK", "BLOCKED"]
       or dependency_count[m.name] >= 2
]
```

---

## Metricas e KPIs

### Metricas Calculadas

| Metrica | Descricao | Range |
|---------|-----------|-------|
| `overall_progress` | Progresso medio de todos milestones | 0-100% |
| `completed_count` | Milestones finalizados | 0-N |
| `in_progress_count` | Milestones em andamento | 0-N |
| `at_risk_count` | Milestones em risco ou bloqueados | 0-N |
| `critical_path` | Milestones no caminho critico | lista |

### Status Distribution

```
NOT_STARTED  -> Ainda nao iniciado
IN_PROGRESS  -> Em execucao normal
AT_RISK      -> Atrasado ou proximo de atrasar
BLOCKED      -> Impedido por dependencia ou blocker
COMPLETED    -> Finalizado
```

---

## Integracao no Workflow

### Uso no implementation_handler

```python
# src/graph/workflow.py

async def implementation_handler(state: BSCState) -> dict:
    # ... gerar action plan ...

    # Gerar milestones para tracking
    tracker = MilestoneTrackerTool()
    milestone_report = await tracker.generate_milestones_from_action_plan(
        action_plan=action_plan,
        current_date=datetime.now().strftime("%Y-%m-%d"),
    )

    return {
        "action_plan": action_plan,
        "milestone_report": milestone_report,
        # ...
    }
```

### Persistencia

Os reports sao serializaveis via `model_dump()`:

```python
# Serializar para SQLite/JSON
report_dict = report.model_dump()

# Deserializar
report = MilestoneTrackerReport(**report_dict)
```

---

## Testes

### Testes Unitarios (16 testes)

```bash
pytest tests/test_sprint4_milestone_tracker.py -v
```

Cobertura:
- Schema Milestone (3 testes)
- Schema MilestoneTrackerReport (2 testes)
- MilestoneTrackerTool (9 testes)
- Integracao (2 testes)

### Testes E2E (7 testes)

```bash
pytest tests/test_sprint4_e2e.py -v
```

Cobertura:
- Fluxo completo (2 testes)
- ActionPlan validation (2 testes)
- Serializacao (2 testes)
- Pipeline integracao (1 teste)

---

## Best Practices

### 1. Sempre fornecer current_date

```python
# BOM - data explicita
report = await tracker.generate_milestones_from_action_plan(
    action_plan=plan,
    current_date="2025-12-15",
)

# EVITAR - usa datetime.now() que pode variar
report = await tracker.generate_milestones_from_action_plan(
    action_plan=plan,
)
```

### 2. Verificar at_risk antes de prosseguir

```python
if report.at_risk_count > 0:
    # Alertar usuario
    blocked = report.get_blocked_milestones()
    for m in blocked:
        logger.warning(f"Milestone em risco: {m.name}")
```

### 3. Usar critical_path para priorizacao

```python
# Priorizar milestones no caminho critico
for milestone_name in report.critical_path:
    # Implementar acao de mitigacao
    pass
```

---

## Fontes e Referencias

1. **balancedscorecard.org** - OKR Basics 2025
2. **mooncamp.com** - BSC Complete Guide 2025
3. **profit.co** - BSC Relevance 2025
4. **actiosoftware.com** - KPIs, OKRs and BSC Integration

---

## Changelog

### v1.0 (25 Nov 2025)

- Implementacao inicial MilestoneTrackerTool
- Schemas Milestone e MilestoneTrackerReport
- Calculo automatico de status e progresso
- Identificacao de caminho critico
- 23 testes (16 unitarios + 7 E2E)
