"""Componente NetworkX + Plotly para Strategy Map BSC.

Cria grafo direcionado com 4 perspectivas BSC, posicionamento hierarquico,
conexoes causa-efeito baseadas em dependencies, e customizacao de cores.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
Usar ASCII: [OK], [ERRO], [INFO].
"""

import networkx as nx
import plotly.graph_objects as go

from src.memory.schemas import StrategicObjective, CauseEffectConnection
from ui.styles.bsc_colors import PERSPECTIVE_COLORS

# MELHORIAS SESSAO 41 (2025-11-22): Cores Material Design vibrantes
# Fonte: Data Visualization Best Practices 2025 + Plotly Official Docs
PERSPECTIVE_COLORS_VIVID = {
    "Financeira": "#EF5350",  # Vermelho vibrante Material Design
    "Clientes": "#FFC107",  # Amarelo ouro
    "Processos Internos": "#42A5F5",  # Azul profissional
    "Aprendizado e Crescimento": "#66BB6A",  # Verde crescimento
}


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

    def __init__(
        self,
        objectives: list[StrategicObjective],
        connections: list[CauseEffectConnection] | None = None,
    ):
        """Inicializa componente com lista de objetivos e conexões causa-efeito.

        CORREÇÃO SESSAO 43 (2025-11-24): Agora aceita connections para visualizar
        setas direcionadas entre objetivos (padrão Kaplan & Norton).

        Args:
            objectives: Lista de objetivos estrategicos BSC
            connections: Lista de conexões causa-efeito (CauseEffectConnection)
        """
        self.objectives = objectives
        self.connections = connections or []
        self.graph = nx.DiGraph()

        # Mapear objective IDs para nomes (para encontrar conexões)
        self.objective_id_to_name = {obj.name: obj.name for obj in objectives}

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

        # CORREÇÃO SESSAO 43: Adicionar arestas a partir de connections (causa-efeito)
        # Usar CauseEffectConnection ao invés de dependencies (padrão BSC)
        if self.connections:
            for conn in self.connections:
                # Mapear source_objective_id e target_objective_id para nomes
                # NOTA: IDs podem ser diferentes dos nomes (ex: "learning_obj_1")
                # Precisamos encontrar o objective correspondente
                source_name = self._find_objective_name_by_id(conn.source_objective_id)
                target_name = self._find_objective_name_by_id(conn.target_objective_id)

                if source_name and target_name:
                    if self.graph.has_node(source_name) and self.graph.has_node(target_name):
                        # Adicionar aresta com metadados da conexão
                        self.graph.add_edge(
                            source_name,
                            target_name,
                            relationship_type=conn.relationship_type,
                            strength=conn.strength,
                            rationale=(
                                conn.rationale[:50] + "..."
                                if len(conn.rationale) > 50
                                else conn.rationale
                            ),
                        )
        else:
            # Fallback: Usar dependencies se connections não disponíveis
            for obj in self.objectives:
                if obj.dependencies:
                    for dep in obj.dependencies:
                        # Aresta: dependencia -> objetivo atual (causa -> efeito)
                        if self.graph.has_node(dep):  # Validar que no existe
                            self.graph.add_edge(dep, obj.name)

        return self.graph

    def _find_objective_name_by_id(self, obj_id: str) -> str | None:
        """Encontra nome do objetivo pelo ID.

        CORREÇÃO SESSAO 43: IDs como 'learning_obj_1' precisam ser mapeados para nomes reais.

        Args:
            obj_id: ID do objetivo (ex: 'learning_obj_1')

        Returns:
            Nome do objetivo ou None se não encontrado
        """
        # Estratégia: Buscar objetivo cuja posição corresponde ao número no ID
        # Ex: 'learning_obj_1' -> primeiro objetivo da perspectiva Aprendizado

        if not obj_id:
            return None

        # Extrair perspectiva e número do ID
        # Formato esperado: 'perspective_obj_N'
        parts = obj_id.split("_obj_")
        if len(parts) != 2:
            # Se não segue padrão, tentar encontrar por nome exato
            for obj in self.objectives:
                if obj.name == obj_id:
                    return obj.name
            return None

        perspective_prefix = parts[0]  # Ex: 'learning', 'process', 'customer', 'financial'
        try:
            obj_index = int(parts[1]) - 1  # Converter 1-based para 0-based
        except ValueError:
            return None

        # Mapear prefixo para perspectiva completa
        perspective_map = {
            "learning": "Aprendizado e Crescimento",
            "process": "Processos Internos",
            "customer": "Clientes",
            "financial": "Financeira",
        }

        perspective_full = perspective_map.get(perspective_prefix)
        if not perspective_full:
            return None

        # Buscar objetivo na perspectiva correspondente
        objs_in_perspective = [
            obj for obj in self.objectives if obj.perspective == perspective_full
        ]

        if 0 <= obj_index < len(objs_in_perspective):
            return objs_in_perspective[obj_index].name

        return None

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

        # MELHORIA SESSAO 43: Componentes visuais baseados em Kaplan & Norton 2025

        # 1. Traces de nos (objectives)
        node_trace = self._create_node_trace(pos, filter_perspective, filter_priority)

        # 2. Annotations de texto dos objetivos
        text_annotations = self._create_text_annotations(pos)

        # 3. NOVO: Setas direcionadas (causa -> efeito)
        arrow_annotations = self._create_arrow_annotations(pos)

        # 4. NOVO: Labels das 4 perspectivas
        perspective_labels = self._create_perspective_labels()

        # 5. NOVO: Faixas de fundo das perspectivas
        perspective_shapes = self._create_perspective_backgrounds()

        # 6. NOVO: Legenda de cores
        legend_traces = self._create_legend_traces()

        # Consolidar todas annotations
        all_annotations = text_annotations + arrow_annotations + perspective_labels

        # Criar figura com TODOS os componentes
        fig = go.Figure(
            data=[node_trace] + legend_traces,
            layout=go.Layout(
                title=dict(
                    text="<b>Strategy Map BSC - Conexoes Causa-Efeito</b>",
                    font=dict(size=20, color="#1f1f1f"),
                    x=0.5,
                    xanchor="center",
                ),
                annotations=all_annotations,
                shapes=perspective_shapes,  # [NOVO] Faixas de fundo
                showlegend=True,  # [NOVO] Mostrar legenda
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.05,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12),
                ),
                hovermode="closest",
                margin=dict(b=80, l=120, r=20, t=80),  # Margem esquerda para labels
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-0.15, 1.05],  # Expandido para labels laterais
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-0.5, 3.5],  # Expandido para spacing
                ),
                plot_bgcolor="white",
                height=700,  # Aumentado para melhor visualização
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

        # MELHORIA SESSAO 41: Layout horizontal mais espaçado
        # Fonte: Network Graph Best Practices 2025
        for persp, nodes in by_perspective.items():
            y = y_levels[persp]
            num_nodes = len(nodes)

            # Espaçamento dinâmico - mais nós = mais espaço
            if num_nodes == 1:
                spacing = 0.5  # Centro
            elif num_nodes == 2:
                spacing_list = [0.3, 0.7]
            elif num_nodes == 3:
                spacing_list = [0.2, 0.5, 0.8]
            else:
                # Distribuição uniforme para 4+ nós
                spacing_list = [0.1 + (i * 0.8 / (num_nodes - 1)) for i in range(num_nodes)]

            for i, node in enumerate(nodes):
                x = spacing_list[i] if num_nodes > 1 else spacing
                pos[node] = (x, y)

        return pos

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

            # MELHORIA SESSAO 41: Cores vibrantes Material Design
            color = PERSPECTIVE_COLORS_VIVID.get(persp, "#CCCCCC")
            node_color.append(color)

            # Texto do no (usado apenas para hover, nao para display)
            node_text.append(node)

            # Hover info
            hover_text = f"<b>{node}</b><br>"
            hover_text += f"Perspectiva: {persp}<br>"
            hover_text += f"Prioridade: {priority}<br>"
            hover_text += f"Descricao: {desc[:100]}...<br>"
            if kpis:
                hover_text += f"KPIs: {', '.join(kpis[:3])}"
            node_hover.append(hover_text)

        # MELHORIA SESSAO 41: Nós menores SEM texto sobreposto
        # Fonte: Plotly Network Graph Best Practices + Community 2025
        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",  # [REMOVIDO] 'text' - evita sobreposição!
            hoverinfo="text",
            hovertext=node_hover,
            marker=dict(
                showscale=False,
                color=node_color,
                size=20,  # Reduzido de 30 para 20
                opacity=node_opacity,
                line_width=2,
                line_color="white",  # Borda branca para contraste
            ),
            showlegend=False,
            name="Objetivos",
        )

    def _create_text_annotations(self, pos: dict[str, tuple[float, float]]) -> list[dict]:
        """Cria annotations de texto SEPARADAS dos nós (evita sobreposição).

        MELHORIA SESSAO 41 (2025-11-22): Pattern recomendado Plotly Community
        Fonte: https://plotly.com/python/text-and-annotations/ + Stack Overflow

        Args:
            pos: Posicoes dos nos {node_name: (x, y)}

        Returns:
            list[dict]: Lista de annotations Plotly
        """
        annotations = []

        for node in self.graph.nodes():
            if node not in pos:
                continue

            x, y = pos[node]

            # Truncar texto longo (max 40 chars)
            display_text = node[:40] + "..." if len(node) > 40 else node

            annotations.append(
                dict(
                    x=x,
                    y=y + 0.15,  # Posição ACIMA do nó (evita sobreposição)
                    text=f"<b>{display_text}</b>",
                    showarrow=False,
                    font=dict(size=9, color="#1f1f1f", family="Arial"),
                    bgcolor="rgba(255, 255, 255, 0.85)",  # Fundo semi-transparente
                    borderpad=4,
                    bordercolor="#ccc",
                    borderwidth=1,
                    xanchor="center",
                    yanchor="bottom",
                )
            )

        return annotations

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

    def _create_arrow_annotations(self, pos: dict[str, tuple[float, float]]) -> list[dict]:
        """Cria setas direcionadas para conexões causa-efeito.

        MELHORIA SESSAO 43 (2025-11-24): Pattern Kaplan & Norton oficial
        Fonte: Balanced Scorecard Institute, HBS 2023, Intrafocus 2025

        "Arrows are used to illustrate the cause-and-effect relationship between objectives"

        Args:
            pos: Posicoes dos nos {node_name: (x, y)}

        Returns:
            list[dict]: Lista de arrow annotations Plotly
        """
        arrows = []

        for source, target, edge_data in self.graph.edges(data=True):
            if source not in pos or target not in pos:
                continue

            x0, y0 = pos[source]
            x1, y1 = pos[target]

            # Criar seta direcionada (causa -> efeito)
            arrows.append(
                dict(
                    ax=x0,
                    ay=y0,  # Start point (causa)
                    x=x1,
                    y=y1,  # End point (efeito)
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=2,  # Seta triangular
                    arrowsize=1.5,  # Tamanho da seta
                    arrowwidth=2.5,  # Largura da linha
                    arrowcolor="#555",  # Cinza escuro
                    standoff=22,  # Offset da seta (não sobrepor nó de 20px)
                )
            )

        return arrows

    def _create_perspective_labels(self) -> list[dict]:
        """Cria labels laterais das 4 perspectivas BSC.

        MELHORIA SESSAO 43 (2025-11-24): Pattern Intrafocus 2025
        Fonte: "Strategy Maps - A 2025 Guide" + ClearPoint Strategy

        Labels grandes à esquerda identificando cada perspectiva.

        Returns:
            list[dict]: Lista de text annotations para labels
        """
        labels = []

        y_positions = {"FINANCEIRA": 3, "CLIENTES": 2, "PROCESSOS": 1, "APRENDIZADO": 0}

        colors = {
            "FINANCEIRA": "#EF5350",
            "CLIENTES": "#FFC107",
            "PROCESSOS": "#42A5F5",
            "APRENDIZADO": "#66BB6A",
        }

        for label, y in y_positions.items():
            labels.append(
                dict(
                    x=-0.1,  # Posição à esquerda do grafo
                    y=y,
                    text=f"<b>{label}</b>",
                    font=dict(size=14, color=colors[label], family="Arial Bold"),
                    showarrow=False,
                    xanchor="right",
                    yanchor="middle",
                    xref="x",
                    yref="y",
                )
            )

        return labels

    def _create_perspective_backgrounds(self) -> list[dict]:
        """Cria faixas de fundo coloridas para cada perspectiva.

        MELHORIA SESSAO 43 (2025-11-24): Pattern Kaplan & Norton oficial
        Fonte: Intrafocus 2025, ClearPoint Strategy

        "Use horizontal swim lanes to separate perspectives visually"

        Returns:
            list[dict]: Lista de shapes (retângulos) Plotly
        """
        shapes = []

        # Definir limites verticais de cada perspectiva
        y_ranges = {
            "Financeira": (2.65, 3.35),
            "Clientes": (1.65, 2.35),
            "Processos Internos": (0.65, 1.35),
            "Aprendizado e Crescimento": (-0.35, 0.35),
        }

        for perspective, (y_min, y_max) in y_ranges.items():
            color = PERSPECTIVE_COLORS_VIVID[perspective]

            shapes.append(
                dict(
                    type="rect",
                    x0=-0.05,
                    x1=1.05,  # Largura total
                    y0=y_min,
                    y1=y_max,
                    fillcolor=color,
                    opacity=0.12,  # Fundo leve (não obstruir nós)
                    layer="below",  # Atrás de tudo
                    line=dict(width=1, color=color, dash="dash"),  # Borda tracejada
                )
            )

        return shapes

    def _create_legend_traces(self) -> list[go.Scatter]:
        """Cria traces invisíveis para legenda de cores.

        MELHORIA SESSAO 43 (2025-11-24): Pattern Plotly Best Practices

        Returns:
            list[go.Scatter]: Traces para legenda
        """
        legend_traces = []

        perspectives = [
            ("Financeira", "#EF5350"),
            ("Clientes", "#FFC107"),
            ("Processos Internos", "#42A5F5"),
            ("Aprendizado e Crescimento", "#66BB6A"),
        ]

        for name, color in perspectives:
            legend_traces.append(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(size=15, color=color, line=dict(width=2, color="white")),
                    showlegend=True,
                    name=name,
                    hoverinfo="skip",
                )
            )

        return legend_traces
