"""Testes smoke para Strategy Map BSC (NetworkX + Plotly).

Valida FUNCIONALIDADE (dados renderizados, filtros funcionam),
NAO texto especifico (anti-pattern LLM, memoria [[10267391]]).

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import plotly.graph_objects as go
import pytest
from ui.components.bsc_network_graph import BSCNetworkGraph

from src.memory.schemas import StrategicObjective


@pytest.fixture
def valid_objectives():
    """Fixture de objetivos estrategicos validos (4 perspectivas balanceadas)."""
    return [
        StrategicObjective(
            name="Objetivo Financeira 1",
            description="Aumentar rentabilidade em 20% atraves de reducao de custos",
            perspective="Financeira",
            timeframe="12 meses",
            success_criteria=[
                "Margem EBITDA atingir ou superar 20% ao final do periodo",
                "ROI crescer e manter-se acima de 15% consistentemente",
            ],
            related_kpis=["EBITDA", "ROI"],
            priority="Alta",
            dependencies=[],
        ),
        StrategicObjective(
            name="Objetivo Clientes 1",
            description="Melhorar NPS de 45 para 70 atraves de implementacao de melhorias no atendimento ao cliente e experiencia de usuario",
            perspective="Clientes",
            timeframe="6 meses",
            success_criteria=[
                "NPS atingir score de 70 ou superior atraves de melhorias no atendimento ao cliente",
                "Reducao de reclamacoes de clientes em pelo menos 30% comparado ao periodo anterior",
            ],
            related_kpis=["NPS"],
            priority="Alta",
            dependencies=[],
        ),
        StrategicObjective(
            name="Objetivo Processos 1",
            description="Automatizar 40% dos processos manuais atraves de implementacao de RPA e ferramentas de automacao de workflows",
            perspective="Processos Internos",
            timeframe="9 meses",
            success_criteria=[
                "Automacao de processos atingir minimo de 40% dos processos manuais atuais identificados",
                "Lead time dos processos automatizados reduzir em pelo menos 50% comparado ao baseline",
            ],
            related_kpis=["Lead Time"],
            priority="Alta",
            dependencies=["Objetivo Aprendizado 1"],  # Dependencia para criar aresta
        ),
        StrategicObjective(
            name="Objetivo Aprendizado 1",
            description="Treinar 80% da equipe em ferramentas de automacao e RPA atraves de programa estruturado de capacitacao",
            perspective="Aprendizado e Crescimento",
            timeframe="6 meses",
            success_criteria=[
                "Minimo de 80% da equipe concluir treinamento completo em automacao com certificacao",
                "Obter pelo menos 10 certificacoes em ferramentas de RPA e automacao de processos",
            ],
            related_kpis=["Horas Treinamento"],
            priority="Alta",
            dependencies=[],
        ),
    ]


def test_build_graph_creates_nodes(valid_objectives):
    """Valida que grafo cria nos para cada objetivo."""
    graph_component = BSCNetworkGraph(valid_objectives)
    graph = graph_component.build_graph()

    # Funcional: Quantidade de nos criados
    assert len(graph.nodes()) == 4
    # Funcional: Nomes dos nos existem
    assert "Objetivo Financeira 1" in graph.nodes()
    assert "Objetivo Aprendizado 1" in graph.nodes()


def test_dependencies_create_edges(valid_objectives):
    """Valida que dependencies criam arestas no grafo."""
    graph_component = BSCNetworkGraph(valid_objectives)
    graph = graph_component.build_graph()

    # Funcional: Aresta existe (dependencia -> objetivo atual)
    assert graph.has_edge("Objetivo Aprendizado 1", "Objetivo Processos 1")
    # Funcional: Quantidade de arestas
    assert graph.number_of_edges() == 1  # Apenas 1 dependencia definida


def test_filter_perspective_changes_opacity(valid_objectives):
    """Valida que filtro de perspectiva altera opacidade."""
    graph_component = BSCNetworkGraph(valid_objectives)
    graph_component.build_graph()

    # Filtrar apenas Financeira
    fig = graph_component.create_plotly_figure(filter_perspective="Financeira")

    # Funcional: Figura criada
    assert isinstance(fig, go.Figure)
    # Funcional: Tem 2 traces (edges + nodes)
    assert len(fig.data) == 2

    node_trace = fig.data[1]  # Segundo trace sao os nos
    # Funcional: Opacidades variadas (algumas 1.0, outras 0.3)
    opacities = node_trace.marker.opacity
    assert any(op == 1.0 for op in opacities)  # Perspectiva filtrada
    assert any(op == 0.3 for op in opacities)  # Outras perspectivas


def test_plotly_figure_renders_without_error(valid_objectives):
    """Smoke test: valida que figura Plotly e criada sem erro."""
    graph_component = BSCNetworkGraph(valid_objectives)
    fig = graph_component.create_plotly_figure()

    # Funcional: Tipo correto
    assert isinstance(fig, go.Figure)
    # Funcional: Tem traces (edges + nodes)
    assert len(fig.data) == 2
    # Funcional: Layout configurado
    assert fig.layout.title.text == "Strategy Map BSC - Conexoes Causa-Efeito"
