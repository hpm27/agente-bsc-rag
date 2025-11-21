"""Componente de filtros reutilizaveis para Strategy Map e Action Plan.

Widgets Streamlit customizados para filtragem por perspectiva, prioridade,
data, responsavel, etc.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

from datetime import datetime

import streamlit as st


class BSCFilters:
    """Componente de filtros reutilizaveis para Strategy Map e Action Plan.

    Fornece widgets Streamlit customizados para filtragem consistente
    em todas as paginas UI.

    Example:
        >>> # Em pagina Streamlit
        >>> persp = BSCFilters.perspective_filter(key="strategy_map_persp")
        >>> prior = BSCFilters.priority_filter(key="strategy_map_prior")
    """

    @staticmethod
    def perspective_filter(
        key: str = "perspective_filter", default: list[str] | None = None
    ) -> list[str]:
        """Multiselect de perspectivas BSC.

        Args:
            key: Chave unica para o widget Streamlit
            default: Lista de perspectivas selecionadas por default

        Returns:
            List[str]: Lista de perspectivas selecionadas
        """
        perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]

        selected = st.multiselect(
            "Filtrar por Perspectiva:",
            options=perspectives,
            default=default or perspectives,
            key=key,
        )

        return selected

    @staticmethod
    def priority_filter(
        key: str = "priority_filter", default: list[str] | None = None, use_english: bool = False
    ) -> list[str]:
        """Multiselect de prioridades.

        Args:
            key: Chave unica para o widget Streamlit
            default: Lista de prioridades selecionadas por default
            use_english: Se True, usa HIGH/MEDIUM/LOW. Se False, usa Alta/Media/Baixa

        Returns:
            List[str]: Lista de prioridades selecionadas
        """
        if use_english:
            priorities = ["HIGH", "MEDIUM", "LOW"]
            default = default or priorities
        else:
            priorities = ["Alta", "Media", "Baixa"]
            default = default or priorities

        selected = st.multiselect(
            "Filtrar por Prioridade:", options=priorities, default=default, key=key
        )

        return selected

    @staticmethod
    def effort_filter(key: str = "effort_filter", default: list[str] | None = None) -> list[str]:
        """Multiselect de esforco (HIGH/MEDIUM/LOW).

        Args:
            key: Chave unica para o widget Streamlit
            default: Lista de esforcos selecionados por default

        Returns:
            List[str]: Lista de esforcos selecionados
        """
        efforts = ["HIGH", "MEDIUM", "LOW"]

        selected = st.multiselect(
            "Filtrar por Esforco:", options=efforts, default=default or efforts, key=key
        )

        return selected

    @staticmethod
    def date_range_filter(
        min_date: str, max_date: str, key: str = "date_filter"
    ) -> tuple[str, str]:
        """Slider de range de datas.

        Args:
            min_date: Data minima (ISO format: YYYY-MM-DD)
            max_date: Data maxima (ISO format: YYYY-MM-DD)
            key: Chave unica para o widget Streamlit

        Returns:
            Tuple[str, str]: (data_inicio_selecionada, data_fim_selecionada) ISO format
        """
        min_dt = datetime.fromisoformat(min_date)
        max_dt = datetime.fromisoformat(max_date)

        selected = st.slider(
            "Filtrar por Periodo:",
            min_value=min_dt,
            max_value=max_dt,
            value=(min_dt, max_dt),
            key=key,
        )

        return selected[0].isoformat(), selected[1].isoformat()

    @staticmethod
    def responsible_filter(
        responsibles: list[str],
        key: str = "responsible_filter",
        default: list[str] | None = None,
    ) -> list[str]:
        """Multiselect de responsaveis (dinamico baseado em dados).

        Args:
            responsibles: Lista de responsaveis disponiveis (extraida dos dados)
            key: Chave unica para o widget Streamlit
            default: Lista de responsaveis selecionados por default

        Returns:
            List[str]: Lista de responsaveis selecionados
        """
        selected = st.multiselect(
            "Filtrar por Responsavel:",
            options=sorted(responsibles),
            default=default or responsibles,
            key=key,
        )

        return selected

    @staticmethod
    def search_filter(
        key: str = "search_filter", placeholder: str = "Buscar por titulo ou descricao..."
    ) -> str:
        """Campo de busca textual.

        Args:
            key: Chave unica para o widget Streamlit
            placeholder: Texto placeholder do input

        Returns:
            str: Termo de busca digitado pelo usuario
        """
        search_term = st.text_input("Buscar:", value="", placeholder=placeholder, key=key)

        return search_term.strip().lower()
