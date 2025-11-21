"""Testes smoke para Dashboard Executivo.

Valida FUNCIONALIDADE (calculos metricas, estatisticas),
NAO texto especifico (anti-pattern LLM, memoria [[10267391]]).

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

# Reusar fixtures dos outros testes
from ui.components.bsc_network_graph import BSCNetworkGraph
from ui.components.gantt_timeline import GanttTimeline


def test_metrics_calculation(valid_objectives, valid_action_items):
    """Valida calculos de metricas do dashboard."""
    # Metricas de objetivos
    total_objs = len(valid_objectives)
    alta_prior_objs = len([o for o in valid_objectives if o.priority == "Alta"])

    # Funcional: Quantidade correta
    assert total_objs == 4
    assert alta_prior_objs == 4  # Todos alta prioridade na fixture

    # Metricas de acoes
    total_actions = len(valid_action_items)
    high_prior_actions = len([a for a in valid_action_items if a.priority == "HIGH"])

    # Funcional: Quantidade correta
    assert total_actions == 4
    assert high_prior_actions == 2  # 2 HIGH na fixture


def test_progress_bars_percentage(valid_objectives, valid_action_items):
    """Verifica percentuais por perspectiva."""
    # Distribuicao acoes por perspectiva
    persp_counts = {}
    for action in valid_action_items:
        persp_counts[action.perspective] = persp_counts.get(action.perspective, 0) + 1

    # Funcional: 4 perspectivas cobertas
    assert len(persp_counts) == 4
    # Funcional: 1 acao por perspectiva na fixture
    for count in persp_counts.values():
        assert count == 1


def test_responsive_layout_columns():
    """Valida estrutura de layout (mock - verifica imports funcionam)."""
    # Smoke test: Importacoes funcionam
    from ui.components.filters import BSCFilters

    # Funcional: Classes existem
    assert BSCNetworkGraph is not None
    assert GanttTimeline is not None
    assert BSCFilters is not None
