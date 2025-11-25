"""Pagina Streamlit - Strategy Map BSC (Conexoes Causa-Efeito).

Visualiza objetivos estrategicos BSC gerados no chat com Consultor BSC.
Carrega automaticamente da sessao atual.

SPRINT 3 - SESSAO 48: Adiciona dashboard de validacoes (KPI Alignment, Cause-Effect)

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st
from ui.components.bsc_network_graph import BSCNetworkGraph
from ui.helpers.mem0_loader import load_strategy_map, load_validation_reports

st.set_page_config(page_title="Strategy Map BSC", layout="wide")

st.title("Strategy Map BSC - Conexoes Causa-Efeito")

# Carregar user_id da sessao atual (criado no chat com Consultor BSC)
# CRITICAL: Ler de query_params PRIMEIRO (persiste entre páginas)
#
# CORRECAO SESSAO 43 (2025-11-24): Usar APENAS st.query_params (API moderna)
# Streamlit NAO permite misturar experimental_get + query_params
# Fonte: StreamlitAPIException + Streamlit Docs 2025
if "user_id" not in st.session_state:
    user_id_from_url = st.query_params.get("uid")
    if user_id_from_url:
        st.session_state.user_id = user_id_from_url
    else:
        st.warning("[INFO] Sessao nao iniciada. Faca uma pergunta ao Consultor BSC primeiro.")
        st.info("Navegue para 'Consultor BSC' no menu lateral e comece a conversa.")
        st.stop()  # Para execução se não tem user_id

# CORRECAO SESSAO 40: SEMPRE sincronizar query_params com session_state
# CORRECAO SESSAO 43: Substituir experimental_set_query_params (deprecated após 2024-04-11)
if "user_id" in st.session_state:
    st.query_params["uid"] = st.session_state.user_id

user_id = st.session_state.user_id

# CORRECAO SESSAO 43: Carregar objectives E connections (causa-efeito)
with st.spinner("Carregando Strategy Map da sessao atual..."):
    objectives, connections, error = load_strategy_map(user_id)

if error:
    st.warning(error)
    st.info("Execute o workflow consultivo completo no chat para gerar o Strategy Map.")
    st.info("**Fases:** ONBOARDING -> DISCOVERY -> APPROVAL -> SOLUTION DESIGN")
    st.stop()

if not objectives:
    st.warning("Nenhum objetivo estrategico encontrado para esta sessao.")
    st.info("Complete a fase SOLUTION DESIGN no chat para gerar o Strategy Map.")
    st.stop()

# Fallback: Se connections não foram carregadas, usar lista vazia
if connections is None:
    connections = []

# SPRINT 3 - SESSAO 48: Carregar reports de validacao
kpi_report, ce_analysis, validation_error = load_validation_reports(user_id)

# Mensagem de contexto
st.info(f"Exibindo Strategy Map da sessao atual (user_id: {user_id[:8]}...)")
st.markdown("---")

# ============================================================================
# DASHBOARD DE METRICAS
# ============================================================================

st.subheader("Dashboard de Metricas")

# Row 1: Metricas basicas do Strategy Map
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Objetivos", len(objectives))
with col2:
    # BUG FIX (Sessao 41, 2025-11-22): StrategicObjective.priority usa "Alta" (nao "ALTA")
    # Schema: Literal["Alta", "Media", "Baixa"] - case-sensitive!
    alta_prioridade = len([o for o in objectives if o.priority == "Alta"])
    pct = (alta_prioridade / len(objectives) * 100) if objectives else 0
    st.metric("Alta Prioridade", alta_prioridade, delta=f"{pct:.0f}%")
with col3:
    perspectivas = set([o.perspective for o in objectives])
    st.metric("Perspectivas", len(perspectivas))
with col4:
    # CORRECAO SESSAO 43: Usar connections carregadas do banco
    total_connections = len(connections) if connections else 0
    st.metric("Conexoes Causa-Efeito", total_connections)

# Row 2: Scores de validacao (SPRINT 3)
col5, col6, col7 = st.columns(3)


def get_score_delta_color(score: float) -> str:
    """Retorna string de delta baseado no score para indicacao visual."""
    if score >= 80:
        return "[OK] Bom"
    elif score >= 60:
        return "[WARN] Regular"
    else:
        return "[ERRO] Ruim"


with col5:
    if kpi_report:
        kpi_score = kpi_report.overall_score
        st.metric(
            "KPI Alignment Score",
            f"{kpi_score:.1f}/100",
            delta=get_score_delta_color(kpi_score),
            delta_color="normal" if kpi_score >= 60 else "inverse",
        )
    else:
        st.metric("KPI Alignment Score", "N/A", delta="Nao disponivel")

with col6:
    if ce_analysis:
        ce_score = ce_analysis.completeness_score
        st.metric(
            "Causa-Efeito Score",
            f"{ce_score:.1f}/100",
            delta=get_score_delta_color(ce_score),
            delta_color="normal" if ce_score >= 60 else "inverse",
        )
    else:
        st.metric("Causa-Efeito Score", "N/A", delta="Nao disponivel")

with col7:
    # Score geral combinado
    if kpi_report and ce_analysis:
        overall = (kpi_report.overall_score + ce_analysis.completeness_score) / 2
        st.metric(
            "Score Geral",
            f"{overall:.1f}/100",
            delta=get_score_delta_color(overall),
            delta_color="normal" if overall >= 60 else "inverse",
        )
    elif kpi_report:
        st.metric("Score Geral", f"{kpi_report.overall_score:.1f}/100")
    elif ce_analysis:
        st.metric("Score Geral", f"{ce_analysis.completeness_score:.1f}/100")
    else:
        st.metric("Score Geral", "N/A", delta="Nao disponivel")

st.markdown("---")

# ============================================================================
# TABS DE CONTEUDO
# ============================================================================

tab_grafo, tab_kpi, tab_causa_efeito, tab_detalhes = st.tabs(
    ["Grafo Visual", "KPI Alignment", "Causa-Efeito", "Detalhes Objetivos"]
)

# ============================================================================
# TAB 1: GRAFO VISUAL
# ============================================================================
with tab_grafo:
    st.subheader("Grafo de Conexoes BSC")

    # CORRECAO SESSAO 43: Passar connections para o grafo
    graph = BSCNetworkGraph(objectives, connections=connections)
    fig = graph.create_plotly_figure(filter_perspective=None, filter_priority=None)
    # CORRECAO SESSAO 43: Substituir use_container_width (deprecated)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2: KPI ALIGNMENT
# ============================================================================
with tab_kpi:
    st.subheader("Validacao de Alinhamento KPI")

    if kpi_report:
        # Status geral
        status_col1, status_col2, status_col3 = st.columns(3)

        with status_col1:
            status = "[OK] Alinhado" if kpi_report.is_aligned else "[WARN] Precisa Ajustes"
            st.info(f"**Status:** {status}")

        with status_col2:
            st.info("**Total KPIs:** Verificados via objectives")

        with status_col3:
            st.info(f"**Issues:** {len(kpi_report.alignment_issues)} encontrados")

        # Score por perspectiva
        st.markdown("### Score por Perspectiva")
        if kpi_report.alignment_by_perspective:
            persp_cols = st.columns(len(kpi_report.alignment_by_perspective))
            for i, (persp, score) in enumerate(kpi_report.alignment_by_perspective.items()):
                with persp_cols[i]:
                    st.metric(persp[:15], f"{score:.1f}%")

        # Lista de issues
        if kpi_report.alignment_issues:
            st.markdown("### Issues Identificados")

            # Agrupar por severidade
            critical = [i for i in kpi_report.alignment_issues if i.severity == "critical"]
            high = [i for i in kpi_report.alignment_issues if i.severity == "high"]
            medium = [i for i in kpi_report.alignment_issues if i.severity == "medium"]
            low = [i for i in kpi_report.alignment_issues if i.severity == "low"]

            if critical:
                with st.expander(f"[CRITICO] {len(critical)} issues criticos", expanded=True):
                    for issue in critical:
                        st.error(f"**{issue.issue_type}:** {issue.description}")
                        if issue.recommendation:
                            st.caption(f"Recomendacao: {issue.recommendation}")

            if high:
                with st.expander(f"[ALTO] {len(high)} issues de alta severidade"):
                    for issue in high:
                        st.warning(f"**{issue.issue_type}:** {issue.description}")
                        if issue.recommendation:
                            st.caption(f"Recomendacao: {issue.recommendation}")

            if medium:
                with st.expander(f"[MEDIO] {len(medium)} issues de severidade media"):
                    for issue in medium:
                        st.info(f"**{issue.issue_type}:** {issue.description}")
                        if issue.recommendation:
                            st.caption(f"Recomendacao: {issue.recommendation}")

            if low:
                with st.expander(f"[BAIXO] {len(low)} issues de baixa severidade"):
                    for issue in low:
                        st.success(f"**{issue.issue_type}:** {issue.description}")
                        if issue.recommendation:
                            st.caption(f"Recomendacao: {issue.recommendation}")

        # Recomendacoes consolidadas
        if kpi_report.recommendations:
            st.markdown("### Recomendacoes")
            for rec in kpi_report.recommendations:
                st.markdown(f"- {rec}")

    else:
        st.info(
            "Report de KPI Alignment nao disponivel. "
            "Execute a fase SOLUTION_DESIGN com KPIs definidos."
        )

# ============================================================================
# TAB 3: CAUSA-EFEITO
# ============================================================================
with tab_causa_efeito:
    st.subheader("Analise de Conexoes Causa-Efeito")

    if ce_analysis:
        # Status geral
        status_col1, status_col2, status_col3 = st.columns(3)

        with status_col1:
            status = "[OK] Completo" if ce_analysis.is_complete else "[WARN] Incompleto"
            st.info(f"**Status:** {status}")

        with status_col2:
            st.info(f"**Total Conexoes:** {ce_analysis.total_connections}")

        with status_col3:
            st.info(f"**Gaps:** {len(ce_analysis.gaps)} encontrados")

        # Conexoes por tipo
        if ce_analysis.connections_by_type:
            st.markdown("### Conexoes por Tipo")
            type_cols = st.columns(len(ce_analysis.connections_by_type))
            for i, (conn_type, count) in enumerate(ce_analysis.connections_by_type.items()):
                with type_cols[i]:
                    st.metric(conn_type.title(), count)

        # Conexoes por par de perspectivas
        if ce_analysis.connections_by_perspective_pair:
            st.markdown("### Conexoes por Par de Perspectivas")
            pair_data = []
            for pair, count in ce_analysis.connections_by_perspective_pair.items():
                pair_data.append({"Par": pair, "Conexoes": count})

            if pair_data:
                import pandas as pd

                pair_df = pd.DataFrame(pair_data)
                st.dataframe(pair_df, hide_index=True, use_container_width=True)

        # Lista de gaps
        if ce_analysis.gaps:
            st.markdown("### Gaps Identificados")

            for gap in ce_analysis.gaps:
                severity_icon = {
                    "critical": "[CRITICO]",
                    "high": "[ALTO]",
                    "medium": "[MEDIO]",
                    "low": "[BAIXO]",
                }.get(gap.severity, "[INFO]")

                with st.expander(f"{severity_icon} {gap.gap_type}: {gap.description[:50]}..."):
                    st.markdown(f"**Tipo:** {gap.gap_type}")
                    st.markdown(
                        f"**Perspectivas:** {gap.source_perspective} -> {gap.target_perspective}"
                    )
                    st.markdown(f"**Descricao:** {gap.description}")
                    if gap.source_objective:
                        st.markdown(f"**Origem:** {gap.source_objective}")
                    if gap.target_objective:
                        st.markdown(f"**Destino:** {gap.target_objective}")

        # Objetivos isolados
        if ce_analysis.isolated_objectives:
            st.markdown("### Objetivos Isolados (sem conexoes)")
            for obj_name in ce_analysis.isolated_objectives:
                st.warning(f"- {obj_name}")

        # Recomendacoes
        if ce_analysis.recommendations:
            st.markdown("### Recomendacoes")
            for rec in ce_analysis.recommendations:
                st.markdown(f"- {rec}")

    else:
        st.info(
            "Analise de Causa-Efeito nao disponivel. "
            "Execute a fase SOLUTION_DESIGN para gerar a analise."
        )

# ============================================================================
# TAB 4: DETALHES DOS OBJETIVOS
# ============================================================================
with tab_detalhes:
    st.subheader("Detalhes dos Objetivos Estrategicos")

    # BUG FIX (Sessao 41, 2025-11-22): BSCNetworkGraph nao tem create_details_table()
    # Criar tabela manualmente a partir de objectives (lista de StrategicObjective)
    if objectives:
        import pandas as pd

        # DataFrame para exibicao (descricao truncada para melhor visualizacao)
        display_df = pd.DataFrame(
            [
                {
                    "Objetivo": obj.name,
                    "Perspectiva": obj.perspective,
                    "Prioridade": obj.priority,
                    "Prazo": obj.timeframe,
                    "KPIs Relacionados": (
                        ", ".join(obj.related_kpis) if obj.related_kpis else "N/A"
                    ),
                    "Dependencias": (
                        ", ".join(obj.dependencies) if obj.dependencies else "Nenhuma"
                    ),
                    "Descricao": (
                        obj.description[:100] + "..."
                        if len(obj.description) > 100
                        else obj.description
                    ),
                }
                for obj in objectives
            ]
        )

        # CORRECAO SESSAO 47: Desabilitar botao CSV nativo do Streamlit
        # O botao nativo usa display_df (truncado), causando confusao
        # Usuario deve usar botao "Exportar CSV" abaixo (dados completos)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Descricao": st.column_config.TextColumn(
                    "Descricao",
                    help="Descricao truncada na tabela. Use 'Exportar CSV' abaixo para versao completa.",
                    width="large",
                )
            },
        )

        # DataFrame para exportacao CSV (descricao COMPLETA - Sessao 47)
        export_df = pd.DataFrame(
            [
                {
                    "Objetivo": obj.name,
                    "Perspectiva": obj.perspective,
                    "Prioridade": obj.priority,
                    "Prazo": obj.timeframe,
                    "KPIs Relacionados": (
                        ", ".join(obj.related_kpis) if obj.related_kpis else "N/A"
                    ),
                    "Dependencias": (
                        ", ".join(obj.dependencies) if obj.dependencies else "Nenhuma"
                    ),
                    "Descricao": obj.description,  # Descricao COMPLETA para CSV
                }
                for obj in objectives
            ]
        )

        # AVISO: Botao nativo do Streamlit (canto superior direito) exporta dados TRUNCADOS
        st.caption(
            "[INFO] O botao 'Download as CSV' acima exporta descricoes TRUNCADAS. "
            "Use o botao abaixo para exportar dados COMPLETOS."
        )

        # Botao export CSV (usa export_df com descricao completa)
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Exportar CSV (Dados Completos)",
            data=csv,
            file_name="strategy_map_bsc.csv",
            mime="text/csv",
            type="primary",  # Destaque visual
        )
    else:
        st.info("Nenhum objetivo corresponde aos criterios.")
