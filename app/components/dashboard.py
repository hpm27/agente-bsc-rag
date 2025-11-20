"""Dashboard multi-cliente para Agente Consultor BSC.

Este módulo implementa a interface de dashboard que exibe todos os clientes
cadastrados com suas informações relevantes (empresa, fase, last updated, etc).

Estrutura:
- render_dashboard(): Componente principal com grid de cards
- _render_client_card(): Card individual para cada cliente
- _render_filters(): Barra de filtros (setor, fase, search)
- _render_stats_summary(): Resumo executivo (total clientes, por fase)

Author: Sistema Consultor BSC
Date: 2025-10-27
"""

from datetime import datetime

import streamlit as st

from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ClientProfile


def render_dashboard() -> None:
    """Renderiza dashboard multi-cliente completo.

    Componente principal que orquestra a exibição de todos os clientes,
    incluindo filtros, stats summary e grid de cards.

    Features:
    - Grid responsivo de cards
    - Filtros por setor, fase, nome
    - Stats executivos (total, por fase)
    - Ordenação por updated_at desc (mais recentes primeiro)
    - Link direto para cada cliente

    Session State:
    - st.session_state.mem0_client: Instância de Mem0ClientWrapper
    - st.session_state.current_client_id: ID do cliente selecionado

    Example:
        >>> # app/main.py
        >>> if page == "Dashboard Multi-Cliente":
        >>>     render_dashboard()
    """
    # Injetar CSS customizado
    _inject_custom_css()

    st.title("Dashboard Multi-Cliente")
    st.markdown("Gerencie todos os seus clientes BSC em um só lugar")

    # Validar session_state
    if "mem0_client" not in st.session_state:
        st.error("[ERRO] Mem0Client não inicializado. Por favor, configure o sistema.")
        return

    mem0_client: Mem0ClientWrapper = st.session_state.mem0_client

    # Carregar todos os profiles
    with st.spinner("Carregando clientes..."):
        try:
            all_profiles: list[ClientProfile] = mem0_client.list_all_profiles(limit=100)
        except Exception as e:
            st.error(f"[ERRO] Falha ao carregar clientes: {e}")
            return

    if not all_profiles:
        st.info("[INFO] Nenhum cliente cadastrado ainda. Use 'Novo Cliente' para começar.")
        return

    # Gerar summaries para todos profiles
    summaries: list[dict] = []
    for profile in all_profiles:
        try:
            summary = mem0_client.get_client_summary(profile.client_id)
            summaries.append(summary)
        except Exception as e:
            st.warning(f"[WARN] Erro ao gerar summary para {profile.client_id}: {e}")
            continue

    # Renderizar stats summary
    _render_stats_summary(summaries)

    # Renderizar filtros
    filtered_summaries = _render_filters(summaries)

    st.markdown("---")

    # Renderizar grid de cards
    if not filtered_summaries:
        st.info("[INFO] Nenhum cliente encontrado com os filtros aplicados.")
        return

    st.subheader(f"Clientes ({len(filtered_summaries)})")

    # Grid 3 colunas
    cols = st.columns(3)
    for idx, summary in enumerate(filtered_summaries):
        col = cols[idx % 3]
        with col:
            _render_client_card(summary)


def _render_stats_summary(summaries: list[dict]) -> None:
    """Renderiza resumo executivo com métricas gerais.

    Args:
        summaries: Lista de dicts com summaries de todos clientes

    Métricas exibidas:
    - Total de clientes
    - Clientes por fase (ONBOARDING, DISCOVERY, etc)
    - Tools médias utilizadas por cliente
    - Clientes com diagnóstico completo
    """
    total_clients = len(summaries)

    # Contar por fase
    phases = {}
    total_tools = 0
    clients_with_diagnostic = 0

    for summary in summaries:
        phase = summary.get("current_phase", "UNKNOWN")
        phases[phase] = phases.get(phase, 0) + 1
        total_tools += summary.get("total_tools_used", 0)
        if summary.get("has_diagnostic"):
            clients_with_diagnostic += 1

    avg_tools = total_tools / total_clients if total_clients > 0 else 0

    # Renderizar métricas em 4 colunas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Clientes", total_clients)

    with col2:
        st.metric("Com Diagnóstico", clients_with_diagnostic)

    with col3:
        st.metric("Tools Médias", f"{avg_tools:.1f}")

    with col4:
        # Fase mais comum
        if phases:
            most_common_phase = max(phases, key=phases.get)
            st.metric("Fase Mais Comum", most_common_phase)
        else:
            st.metric("Fase Mais Comum", "N/A")

    # Expandir com breakdown por fase
    with st.expander("Breakdown por Fase", expanded=False):
        if phases:
            for phase, count in sorted(phases.items(), key=lambda x: x[1], reverse=True):
                st.markdown(f"- **{phase}**: {count} clientes")
        else:
            st.info("Nenhum cliente para exibir.")


def _render_filters(summaries: list[dict]) -> list[dict]:
    """Renderiza barra de filtros e retorna summaries filtrados.

    Args:
        summaries: Lista de summaries originais

    Returns:
        Lista filtrada de summaries baseado nos filtros aplicados

    Filtros disponíveis:
    - Setor: Dropdown com todos setores únicos
    - Fase: Dropdown com todas fases únicas
    - Nome: Campo de busca (case-insensitive)
    """
    st.subheader("Filtros")

    col1, col2, col3 = st.columns(3)

    # Filtro 1: Setor
    with col1:
        all_sectors = sorted(set(s.get("sector", "Desconhecido") for s in summaries))
        selected_sector = st.selectbox(
            "Setor", options=["Todos"] + all_sectors, key="filter_sector"
        )

    # Filtro 2: Fase
    with col2:
        all_phases = sorted(set(s.get("current_phase", "UNKNOWN") for s in summaries))
        selected_phase = st.selectbox("Fase", options=["Todas"] + all_phases, key="filter_phase")

    # Filtro 3: Nome (busca)
    with col3:
        search_query = st.text_input(
            "Buscar por nome", placeholder="Digite o nome da empresa...", key="filter_search"
        )

    # Aplicar filtros
    filtered = summaries.copy()

    if selected_sector != "Todos":
        filtered = [s for s in filtered if s.get("sector") == selected_sector]

    if selected_phase != "Todas":
        filtered = [s for s in filtered if s.get("current_phase") == selected_phase]

    if search_query:
        search_lower = search_query.lower()
        filtered = [s for s in filtered if search_lower in s.get("company_name", "").lower()]

    return filtered


def _render_client_card(summary: dict) -> None:
    """Renderiza card individual para um cliente.

    Args:
        summary: Dict retornado de get_client_summary() com:
            - client_id
            - company_name
            - sector
            - size
            - current_phase
            - last_updated
            - total_tools_used
            - has_diagnostic
            - approval_status

    Layout do card:
    - Título: Nome da empresa
    - Badge: Setor
    - Badge: Fase atual
    - Info: Tamanho da empresa
    - Info: Última atualização (formatada)
    - Info: Tools utilizadas
    - Info: Diagnóstico completo? (Yes/No)
    - Info: Status de aprovação (se presente)
    - Botão: "Abrir Cliente" (muda current_client_id e rerun)
    """
    client_id = summary.get("client_id")
    company_name = summary.get("company_name", "Empresa Desconhecida")
    sector = summary.get("sector", "N/A")
    size = summary.get("size", "N/A")
    phase = summary.get("current_phase", "UNKNOWN")
    last_updated = summary.get("last_updated")
    tools_used = summary.get("total_tools_used", 0)
    has_diagnostic = summary.get("has_diagnostic", False)
    approval_status = summary.get("approval_status")

    # Container com borda
    with st.container():
        # Título
        st.markdown(f"### {company_name}")

        # Badges (setor + fase)
        badge_sector = f'<span style="background:#4285f4;color:#fff;padding:4px 8px;border-radius:4px;font-size:12px;margin-right:8px;">{sector}</span>'
        badge_phase = f'<span style="background:#34a853;color:#fff;padding:4px 8px;border-radius:4px;font-size:12px;">{phase}</span>'
        st.markdown(badge_sector + badge_phase, unsafe_allow_html=True)

        st.markdown("")  # Espaçamento

        # Info: Tamanho
        st.markdown(f"**Tamanho:** {size}")

        # Info: Última atualização
        if last_updated:
            if isinstance(last_updated, datetime):
                formatted_date = last_updated.strftime("%d/%m/%Y %H:%M")
            else:
                formatted_date = str(last_updated)
            st.markdown(f"**Última atualização:** {formatted_date}")

        # Info: Tools utilizadas
        st.markdown(f"**Tools utilizadas:** {tools_used}/8")

        # Info: Diagnóstico completo
        diagnostic_icon = "[OK]" if has_diagnostic else "[PENDENTE]"
        st.markdown(f"**Diagnóstico:** {diagnostic_icon}")

        # Info: Approval status (opcional)
        if approval_status:
            st.markdown(f"**Aprovação:** {approval_status}")

        # Botão: Abrir Cliente
        if st.button("Abrir Cliente", key=f"btn_open_{client_id}", type="primary"):
            st.session_state.current_client_id = client_id
            st.rerun()

        st.markdown("---")  # Divider entre cards


def _inject_custom_css() -> None:
    """Injeta CSS customizado para melhorar visual do dashboard.

    Estilos aplicados:
    - Cards com sombra e hover effect
    - Badges com cores Material Design
    - Grid responsivo
    - Espaçamento consistente
    - Alto contraste para legibilidade
    """
    st.markdown(
        """
    <style>
    /* Cards de clientes */
    div[data-testid="stVerticalBlock"] > div[data-testid="column"] {
        background: #ffffff;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: box-shadow 0.2s ease;
        margin-bottom: 16px;
    }

    div[data-testid="stVerticalBlock"] > div[data-testid="column"]:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .badge-sector {
        background: #4285f4;
        color: #fff;
    }

    .badge-phase {
        background: #34a853;
        color: #fff;
    }

    .badge-pending {
        background: #fbbc04;
        color: #1f1f1f;
    }

    .badge-completed {
        background: #34a853;
        color: #fff;
    }

    /* Métricas do header */
    div[data-testid="metric-container"] {
        background: #f8f9fb;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #4285f4;
    }

    /* Títulos dos cards */
    h3 {
        color: #1f1f1f;
        margin-bottom: 12px;
    }

    /* Info do card */
    strong {
        color: #5f6368;
    }

    /* Botões primários */
    button[kind="primary"] {
        width: 100%;
        background: #4285f4;
        color: #fff;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
        transition: background 0.2s ease;
    }

    button[kind="primary"]:hover {
        background: #3367d6;
    }

    /* Espaçamento entre elementos */
    p {
        line-height: 1.6;
        margin-bottom: 8px;
    }

    /* Dividers */
    hr {
        margin: 16px 0;
        border: none;
        border-top: 1px solid #e8eaed;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
