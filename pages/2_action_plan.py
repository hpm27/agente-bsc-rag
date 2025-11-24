"""Pagina Streamlit - Action Plan (Timeline Gantt).

Visualiza plano de acao BSC gerado no chat com Consultor BSC.
Carrega automaticamente da sessao atual.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st
from ui.components.gantt_timeline import GanttTimeline
from ui.helpers.mem0_loader import load_action_plan

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
