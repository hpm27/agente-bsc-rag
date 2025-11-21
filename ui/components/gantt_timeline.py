"""Componente Plotly Express para timeline Gantt de Action Plan.

Cria timeline interativo com barras por action, cores por prioridade,
tooltips informativos e zoom temporal.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.memory.schemas import ActionItem
from ui.styles.bsc_colors import PRIORITY_COLORS


class GanttTimeline:
    """Componente Plotly Express para timeline Gantt de Action Plan.

    Cria timeline interativo com barras por action, cores por prioridade,
    tooltips informativos e zoom temporal.

    Attributes:
        action_items: Lista de acoes do plano

    Example:
        >>> actions = [...]  # Lista de ActionItem
        >>> gantt = GanttTimeline(actions)
        >>> df = gantt.create_dataframe()
        >>> fig = gantt.create_plotly_figure(df)
        >>> st.plotly_chart(fig, use_container_width=True)
    """

    def __init__(self, action_items: list[ActionItem]):
        """Inicializa componente com lista de acoes.

        Args:
            action_items: Lista de acoes do Action Plan
        """
        self.action_items = action_items

    def create_dataframe(
        self,
        filter_perspective: list[str] | None = None,
        filter_priority: list[str] | None = None,
        filter_responsible: list[str] | None = None,
    ) -> pd.DataFrame:
        """Converte ActionItems para DataFrame Pandas com filtros aplicados.

        Args:
            filter_perspective: Lista de perspectivas para filtrar
            filter_priority: Lista de prioridades para filtrar
            filter_responsible: Lista de responsaveis para filtrar

        Returns:
            pd.DataFrame: DataFrame com acoes filtradas
        """
        data = []

        for action in self.action_items:
            # Aplicar filtros
            if filter_perspective and action.perspective not in filter_perspective:
                continue
            if filter_priority and action.priority not in filter_priority:
                continue
            if filter_responsible and action.responsible not in filter_responsible:
                continue

            data.append(
                {
                    "Action": action.action_title,
                    "Start": action.start_date,
                    "Finish": action.due_date,
                    "Priority": action.priority,
                    "Effort": action.effort,
                    "Responsible": action.responsible,
                    "Perspective": action.perspective,
                    "Description": action.description,
                    "Resources": ", ".join(action.resources_needed),
                    "Success_Criteria": action.success_criteria,
                }
            )

        return pd.DataFrame(data)

    def create_plotly_figure(self, df: pd.DataFrame) -> go.Figure:
        """Cria figura Plotly timeline (Gantt chart).

        Args:
            df: DataFrame com acoes

        Returns:
            go.Figure: Figura Plotly timeline
        """
        if df.empty:
            # Retornar figura vazia com mensagem
            fig = go.Figure()
            fig.add_annotation(
                text="Nenhuma acao corresponde aos filtros selecionados",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="gray"),
            )
            fig.update_layout(title="Action Plan Timeline (Gantt Chart)", height=600)
            return fig

        # Criar timeline
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Action",
            color="Priority",
            color_discrete_map=PRIORITY_COLORS,
            hover_data={
                "Responsible": True,
                "Resources": True,
                "Effort": True,
                "Start": False,
                "Finish": False,
            },
            title="Action Plan Timeline (Gantt Chart)",
        )

        # Customizacao layout
        fig.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Acoes",
            height=600,
            showlegend=True,
            legend_title="Prioridade",
            hovermode="closest",
        )

        # Ordenar por data de inicio
        fig.update_yaxes(categoryorder="total ascending")

        return fig

    def create_details_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria DataFrame formatado para exibicao em tabela Streamlit.

        Args:
            df: DataFrame original com acoes

        Returns:
            pd.DataFrame: DataFrame formatado para tabela
        """
        if df.empty:
            return pd.DataFrame()

        table_df = df[
            ["Action", "Priority", "Responsible", "Start", "Finish", "Perspective"]
        ].copy()

        # Renomear colunas para portugues
        table_df.columns = ["Acao", "Prioridade", "Responsavel", "Inicio", "Prazo", "Perspectiva"]

        return table_df

    def get_timeline_stats(self, df: pd.DataFrame | None = None) -> dict:
        """Retorna estatisticas do timeline.

        Args:
            df: DataFrame opcional (se None, usa action_items completo)

        Returns:
            dict: Estatisticas do timeline
        """
        if df is None:
            df = self.create_dataframe()

        if df.empty:
            return {
                "total_actions": 0,
                "high_priority": 0,
                "by_perspective": {},
                "by_responsible": {},
            }

        by_perspective = df.groupby("Perspective").size().to_dict()
        by_responsible = df.groupby("Responsible").size().to_dict()
        high_priority = len(df[df["Priority"] == "HIGH"])

        return {
            "total_actions": len(df),
            "high_priority": high_priority,
            "by_perspective": by_perspective,
            "by_responsible": by_responsible,
        }
