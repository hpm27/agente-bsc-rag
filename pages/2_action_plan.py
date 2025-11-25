"""Pagina Streamlit - Action Plan (Timeline Gantt + Milestones).

Visualiza plano de acao BSC gerado no chat com Consultor BSC.
Carrega automaticamente da sessao atual.

SPRINT 4 - SESSAO 49: Adiciona dashboard de milestones.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st
from ui.components.gantt_timeline import GanttTimeline
from ui.helpers.mem0_loader import load_action_plan, load_milestone_report

st.set_page_config(page_title="Action Plan", layout="wide")

st.title("Action Plan - Timeline de Implementacao BSC")

# Carregar user_id da sessao atual (criado no chat com Consultor BSC)
# CRITICAL: Ler de query_params PRIMEIRO (persiste entre páginas)
#
# CORREÇÃO SESSAO 43 (2025-11-24): Usar APENAS st.query_params (API moderna)
# Streamlit NÃO permite misturar experimental_get + query_params
# Fonte: StreamlitAPIException + Streamlit Docs 2025
if "user_id" not in st.session_state:
    user_id_from_url = st.query_params.get("uid")
    if user_id_from_url:
        st.session_state.user_id = user_id_from_url
    else:
        st.warning("[INFO] Sessao nao iniciada. Faca uma pergunta ao Consultor BSC primeiro.")
        st.info("Navegue para 'Consultor BSC' no menu lateral e comece a conversa.")
        st.stop()  # Para execução se não tem user_id

# CORREÇÃO SESSAO 40: SEMPRE sincronizar query_params com session_state
# CORREÇÃO SESSAO 43: Substituir experimental_set_query_params (deprecated após 2024-04-11)
if "user_id" in st.session_state:
    st.query_params["uid"] = st.session_state.user_id

user_id = st.session_state.user_id

# Carregar action items do Mem0 (sessao atual)
with st.spinner("Carregando Action Plan da sessao atual..."):
    actions, error = load_action_plan(user_id)

if error:
    st.warning(error)
    st.info("Execute o workflow consultivo completo no chat para gerar o Action Plan.")
    st.info("**Fases:** ONBOARDING -> DISCOVERY -> APPROVAL -> SOLUTION DESIGN -> IMPLEMENTATION")
    st.stop()

if not actions:
    st.warning("Nenhum plano de acao encontrado para esta sessao.")
    st.info("Complete o workflow consultivo no chat para gerar o Action Plan.")
    st.stop()

# Mensagem de contexto
st.info(f"Exibindo Action Plan da sessao atual (user_id: {user_id[:8]}...)")
st.markdown("---")

# Mostrar todas as acoes (sem filtros)
filter_persp = None
filter_prior = None
filter_resp = None

# KPIs do Action Plan
st.subheader("Visao Geral do Plano")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Acoes", len(actions))
with col2:
    high_count = len([a for a in actions if a.priority == "HIGH"])
    pct = (high_count / len(actions) * 100) if actions else 0
    st.metric("Alta Prioridade", high_count, delta=f"{pct:.0f}%")
with col3:
    efforts = [a.effort for a in actions]
    avg_effort = efforts.count("HIGH") / len(efforts) * 100 if efforts else 0
    st.metric("Esforco Alto", f"{avg_effort:.0f}%")
with col4:
    responsibles = set([a.responsible for a in actions])
    st.metric("Responsaveis", len(responsibles))

# Gantt Chart
st.subheader("Timeline Gantt")

gantt_component = GanttTimeline(actions)
df = gantt_component.create_dataframe(
    filter_perspective=filter_persp, filter_priority=filter_prior, filter_responsible=filter_resp
)

fig = gantt_component.create_plotly_figure(df)
# CORREÇÃO SESSAO 43: Substituir use_container_width (deprecated)
st.plotly_chart(fig, width="stretch")

# Tabela de detalhes
st.subheader("Detalhes das Acoes")

table_df = gantt_component.create_details_table(df)

if not table_df.empty:
    # Tabela interativa
    st.dataframe(table_df, width="stretch", hide_index=True)

    # Botao de export CSV
    csv = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(label="Exportar CSV", data=csv, file_name="action_plan.csv", mime="text/csv")
else:
    st.info("Nenhuma acao corresponde aos filtros selecionados.")

# ============================================================================
# SPRINT 4 - SESSAO 49: DASHBOARD DE MILESTONES
# ============================================================================

st.markdown("---")
st.subheader("Rastreamento de Milestones")

# Carregar milestone report
milestone_report, milestone_error = load_milestone_report(user_id)

if milestone_error:
    st.info(milestone_error)
elif milestone_report:
    # Row 1: Metricas de progresso
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

    with m_col1:
        st.metric("Total Milestones", milestone_report.total_milestones)
    with m_col2:
        st.metric("Progresso Geral", f"{milestone_report.overall_progress:.1f}%")
    with m_col3:
        st.metric("Completados", milestone_report.completed_count)
    with m_col4:
        st.metric("Em Andamento", milestone_report.in_progress_count)
    with m_col5:
        # Em risco - usar help para status ao inves de delta (delta espera numero)
        at_risk = milestone_report.at_risk_count
        status_msg = "[ATENCAO] Milestones em risco!" if at_risk > 0 else "[OK] Nenhum em risco"
        st.metric("Em Risco", at_risk, help=status_msg)

    # Proximos prazos
    if milestone_report.next_due_milestones:
        st.markdown("#### Proximos Prazos")
        for m_name in milestone_report.next_due_milestones[:5]:
            st.markdown(f"- {m_name}")

    # Recomendacoes
    if milestone_report.recommendations:
        st.markdown("#### Recomendacoes")
        for rec in milestone_report.recommendations[:5]:
            st.markdown(f"- {rec}")

    # Tabela de milestones
    st.markdown("#### Detalhes dos Milestones")

    milestone_data = []
    for m in milestone_report.milestones:
        status_emoji = {
            "NOT_STARTED": "[--]",
            "IN_PROGRESS": "[>>]",
            "COMPLETED": "[OK]",
            "BLOCKED": "[XX]",
            "AT_RISK": "[!!]",
        }.get(m.status, "[??]")

        milestone_data.append(
            {
                "Status": f"{status_emoji} {m.status}",
                "Milestone": m.name[:50] + "..." if len(m.name) > 50 else m.name,
                "Progresso": f"{m.progress_percent:.0f}%",
                "Prazo": m.target_date,
                "Responsavel": m.responsible,
            }
        )

    if milestone_data:
        import pandas as pd

        milestone_df = pd.DataFrame(milestone_data)
        st.dataframe(milestone_df, width="stretch", hide_index=True)

        # Export CSV de milestones
        ms_csv = milestone_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Exportar Milestones CSV",
            data=ms_csv,
            file_name="milestones.csv",
            mime="text/csv",
        )
else:
    st.info("Milestone report nao disponivel. Execute a fase IMPLEMENTATION no chat.")
