"""Testes smoke para Action Plan Timeline (Plotly Gantt).

Valida FUNCIONALIDADE (filtros, rendering, export),
NAO texto especifico (anti-pattern LLM, memoria [[10267391]]).

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import plotly.graph_objects as go
import pytest
from ui.components.gantt_timeline import GanttTimeline

from src.memory.schemas import ActionItem


@pytest.fixture
def valid_action_items():
    """Fixture de acoes validas (4 perspectivas balanceadas)."""
    return [
        ActionItem(
            action_title="Acao Financeira 1",
            description="Implementar dashboard financeiro consolidado com 10 KPIs",
            perspective="Financeira",
            priority="HIGH",
            effort="MEDIUM",
            responsible="Diretoria Financeira",
            start_date="2025-12-01",
            due_date="2026-03-15",
            resources_needed=["Power BI", "Analista BI"],
            success_criteria="Dashboard com 10 KPIs atualizados diariamente",
            dependencies=[],
        ),
        ActionItem(
            action_title="Acao Clientes 1",
            description="Implementar sistema de coleta de feedback de clientes",
            perspective="Clientes",
            priority="HIGH",
            effort="LOW",
            responsible="Gerencia Marketing",
            start_date="2025-11-15",
            due_date="2026-01-30",
            resources_needed=["Plataforma CRM"],
            success_criteria="80% clientes respondendo surveys",
            dependencies=[],
        ),
        ActionItem(
            action_title="Acao Processos 1",
            description="Automatizar processo de aprovacao de pedidos",
            perspective="Processos Internos",
            priority="MEDIUM",
            effort="HIGH",
            responsible="Gerencia Operacoes",
            start_date="2026-01-01",
            due_date="2026-06-30",
            resources_needed=["Software BPM"],
            success_criteria="Lead time reducao 40%",
            dependencies=[],
        ),
        ActionItem(
            action_title="Acao Aprendizado 1",
            description="Treinar equipe em automacao e RPA",
            perspective="Aprendizado e Crescimento",
            priority="LOW",
            effort="MEDIUM",
            responsible="Gerencia RH",
            start_date="2025-12-01",
            due_date="2026-05-31",
            resources_needed=["e-learning"],
            success_criteria="80% equipe treinada",
            dependencies=[],
        ),
    ]


def test_create_dataframe_filters_perspective(valid_action_items):
    """Valida que filtro de perspectiva funciona."""
    gantt = GanttTimeline(valid_action_items)
    df = gantt.create_dataframe(filter_perspective=["Financeira"])

    # Funcional: Apenas 1 acao filtrada
    assert len(df) == 1
    # Funcional: Perspectiva correta
    assert df.iloc[0]["Perspective"] == "Financeira"


def test_create_plotly_figure_renders(valid_action_items):
    """Smoke test: valida que figura Plotly e criada."""
    gantt = GanttTimeline(valid_action_items)
    df = gantt.create_dataframe()
    fig = gantt.create_plotly_figure(df)

    # Funcional: Tipo correto (Figure ou resultado px.timeline)
    assert isinstance(fig, go.Figure)
    # Funcional: Tem layout configurado
    assert "Timeline" in fig.layout.title.text or "Gantt" in fig.layout.title.text


def test_empty_dataframe_shows_message(valid_action_items):
    """Valida que DataFrame vazio mostra mensagem ao invés de erro."""
    gantt = GanttTimeline([])  # Vazio
    df = gantt.create_dataframe()
    fig = gantt.create_plotly_figure(df)

    # Funcional: DataFrame vazio
    assert df.empty
    # Funcional: Figura criada (com mensagem)
    assert isinstance(fig, go.Figure)
    # Funcional: Tem annotation de mensagem
    assert len(fig.layout.annotations) > 0


def test_details_table_renames_columns(valid_action_items):
    """Valida que tabela de detalhes renomeia colunas para portugues."""
    gantt = GanttTimeline(valid_action_items)
    df = gantt.create_dataframe()
    table = gantt.create_details_table(df)

    # Funcional: Colunas renomeadas
    assert "Acao" in table.columns
    assert "Prioridade" in table.columns
    assert "Responsavel" in table.columns
    assert "Perspectiva" in table.columns
    # Funcional: Quantidade de linhas
    assert len(table) == 4
