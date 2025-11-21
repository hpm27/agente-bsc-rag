"""Componente NetworkX + Plotly para Strategy Map BSC.

Cria grafo direcionado com 4 perspectivas BSC, posicionamento hierarquico,
conexoes causa-efeito baseadas em dependencies, e customizacao de cores.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
Usar ASCII: [OK], [ERRO], [INFO].
"""

import networkx as nx
import plotly.graph_objects as go

from src.memory.schemas import StrategicObjective
from ui.styles.bsc_colors import PERSPECTIVE_COLORS


class BSCNetworkGraph:
    """Componente NetworkX + Plotly para Strategy Map BSC.

    Cria grafo direcionado com 4 perspectivas BSC, posicionamento hierarquico,
    conexoes causa-efeito baseadas em dependencies, e customizacao de cores.

    Attributes:
        objectives: Lista de objetivos estrategicos BSC
        graph: Grafo NetworkX direcionado

    Example:
        >>> objectives = [...]  # Lista de StrategicObjective
        >>> graph_component = BSCNetworkGraph(objectives)
        >>> graph = graph_component.build_graph()
        >>> fig = graph_component.create_plotly_figure()
        >>> st.plotly_chart(fig, use_container_width=True)
    """

    def __init__(self, objectives: list[StrategicObjective]):
        """Inicializa componente com lista de objetivos.

        Args:
            objectives: Lista de objetivos estrategicos BSC
        """
        self.objectives = objectives
        self.graph = nx.DiGraph()

    def build_graph(self) -> nx.DiGraph:
        """Constroi grafo direcionado com nos (objectives) e arestas (dependencies).

        Returns:
            nx.DiGraph: Grafo direcionado NetworkX
        """
        # Adicionar nos
        for obj in self.objectives:
            self.graph.add_node(
                obj.name,
                perspective=obj.perspective,
                description=obj.description,
                priority=obj.priority,
                related_kpis=obj.related_kpis,
                success_criteria=obj.success_criteria,
                timeframe=obj.timeframe,
            )

        # Adicionar arestas (dependencies)
        for obj in self.objectives:
            if obj.dependencies:
                for dep in obj.dependencies:
                    # Aresta: dependencia -> objetivo atual (causa -> efeito)
                    if self.graph.has_node(dep):  # Validar que no existe
                        self.graph.add_edge(dep, obj.name)

        return self.graph

    def create_plotly_figure(
        self, filter_perspective: str | None = None, filter_priority: list[str] | None = None
    ) -> go.Figure:
        """Cria figura Plotly interativa do grafo.

        Args:
            filter_perspective: Perspectiva para highlight (outras ficam opacas)
            filter_priority: Lista de prioridades para mostrar (ex: ["Alta"])

        Returns:
            go.Figure: Figura Plotly pronta para st.plotly_chart()
        """
        # Build graph se ainda nao foi construido
        if not self.graph.nodes():
            self.build_graph()

        # Layout hierarquico (4 camadas: Aprendizado -> Processos -> Clientes -> Financeira)
        pos = self._hierarchical_layout()

        # Criar traces de arestas (conexoes)
        edge_trace = self._create_edge_trace(pos)

        # Criar traces de nos (objectives)
        node_trace = self._create_node_trace(pos, filter_perspective, filter_priority)

        # Criar figura
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Strategy Map BSC - Conexoes Causa-Efeito",
                showlegend=True,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="white",
            ),
        )

        return fig

    def _hierarchical_layout(self) -> dict[str, tuple[float, float]]:
        """Layout hierarquico com 4 camadas verticais.

        Returns:
            dict: Dicionario {node_name: (x, y)}
        """
        # Agrupar por perspectiva
        by_perspective = {
            "Financeira": [],
            "Clientes": [],
            "Processos Internos": [],
            "Aprendizado e Crescimento": [],
        }

        for node in self.graph.nodes():
            persp = self.graph.nodes[node]["perspective"]
            by_perspective[persp].append(node)

        # Posicionar nos (y baseado em perspectiva, x distribuir igualmente)
        pos = {}
        y_levels = {
            "Financeira": 3,
            "Clientes": 2,
            "Processos Internos": 1,
            "Aprendizado e Crescimento": 0,
        }

        for persp, nodes in by_perspective.items():
            y = y_levels[persp]
            for i, node in enumerate(nodes):
                x = (i + 1) / (len(nodes) + 1)  # Distribuir entre 0 e 1
                pos[node] = (x, y)

        return pos

    def _create_edge_trace(self, pos: dict[str, tuple[float, float]]) -> go.Scatter:
        """Cria trace de arestas (setas direcionadas).

        Args:
            pos: Posicoes dos nos {node_name: (x, y)}

        Returns:
            go.Scatter: Trace de arestas Plotly
        """
        edge_x = []
        edge_y = []

        for edge in self.graph.edges():
            if edge[0] in pos and edge[1] in pos:  # Validar que ambos nos existem
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

        return go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=2, color="#888"),
            hoverinfo="none",
            mode="lines",
            showlegend=False,
        )

    def _create_node_trace(
        self,
        pos: dict[str, tuple[float, float]],
        filter_perspective: str | None,
        filter_priority: list[str] | None,
    ) -> go.Scatter:
        """Cria trace de nos com customizacao de cores e opacidade.

        Args:
            pos: Posicoes dos nos {node_name: (x, y)}
            filter_perspective: Perspectiva para highlight
            filter_priority: Lista de prioridades para mostrar

        Returns:
            go.Scatter: Trace de nos Plotly
        """
        node_x = []
        node_y = []
        node_color = []
        node_text = []
        node_hover = []
        node_opacity = []

        for node in self.graph.nodes():
            if node not in pos:
                continue

            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Dados do no
            persp = self.graph.nodes[node]["perspective"]
            priority = self.graph.nodes[node]["priority"]
            desc = self.graph.nodes[node]["description"]
            kpis = self.graph.nodes[node]["related_kpis"]

            # Filtros
            if (filter_perspective and persp != filter_perspective) or (
                filter_priority and priority not in filter_priority
            ):
                opacity = 0.3
            else:
                opacity = 1.0

            node_opacity.append(opacity)

            # Cor baseada em perspectiva
            color = PERSPECTIVE_COLORS.get(persp, "#CCCCCC")
            node_color.append(color)

            # Texto do no
            node_text.append(node)

            # Hover info
            hover_text = f"<b>{node}</b><br>"
            hover_text += f"Perspectiva: {persp}<br>"
            hover_text += f"Prioridade: {priority}<br>"
            hover_text += f"Descricao: {desc[:100]}...<br>"
            if kpis:
                hover_text += f"KPIs: {', '.join(kpis[:3])}"
            node_hover.append(hover_text)

        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=node_text,
            hovertext=node_hover,
            textposition="top center",
            marker=dict(
                showscale=False,
                color=node_color,
                size=30,
                opacity=node_opacity,
                line_width=2,
                line_color="#424242",
            ),
            showlegend=False,
        )

    def get_graph_stats(self) -> dict[str, int]:
        """Retorna estatisticas do grafo.

        Returns:
            dict: Estatisticas {total_nodes, total_edges, by_perspective}
        """
        if not self.graph.nodes():
            self.build_graph()

        by_perspective = {}
        for node in self.graph.nodes():
            persp = self.graph.nodes[node]["perspective"]
            by_perspective[persp] = by_perspective.get(persp, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "by_perspective": by_perspective,
        }
