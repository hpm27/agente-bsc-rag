"""Pagina Streamlit - Action Plan (Timeline Gantt).

Visualiza plano de acao BSC em timeline Gantt com filtros por
perspectiva, prioridade e responsavel.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st

from ui.components.filters import BSCFilters
from ui.components.gantt_timeline import GanttTimeline
from ui.helpers.mem0_loader import list_all_clients, load_action_plan

st.set_page_config(page_title="Action Plan", layout="wide")

st.title("Action Plan - Timeline de Implementacao BSC")

# SPRINT 4: Integracao Mem0 completa
st.markdown("**Selecione um cliente para visualizar o Action Plan:**")

# Carregar lista de clientes
clients, error = list_all_clients()

if error:
    st.error(error)
    st.stop()

if not clients:
    st.warning(
        "[INFO] Nenhum cliente encontrado no sistema. Execute o workflow consultivo (ONBOARDING -> IMPLEMENTATION) primeiro."
    )
    st.stop()

# Seletor de cliente
client_options = {f"{c['company_name']} ({c['sector']})": c["user_id"] for c in clients}
selected_client = st.selectbox(
    "Cliente:", options=list(client_options.keys()), key="action_plan_client_selector"
)

if not selected_client:
    st.info("Selecione um cliente acima para visualizar o Action Plan.")
    st.stop()

# Buscar user_id do cliente selecionado
user_id = client_options[selected_client]

# Carregar action items do Mem0
with st.spinner(f"Carregando Action Plan de '{selected_client}'..."):
    actions, error = load_action_plan(user_id)

if error:
    st.warning(error)
    st.info("Execute a fase IMPLEMENTATION do workflow consultivo para gerar o Action Plan.")
    st.stop()

if not actions:
    st.warning("Nenhum plano de acao encontrado. Execute a fase IMPLEMENTATION primeiro.")
    st.stop()

# Filtros na sidebar
with st.sidebar:
    st.header("Filtros")

    filter_persp = BSCFilters.perspective_filter(key="action_plan_perspective")
    filter_prior = BSCFilters.priority_filter(key="action_plan_priority", use_english=True)

    # Filtro de responsavel
    all_responsibles = sorted(set([a.responsible for a in actions]))
    filter_resp = BSCFilters.responsible_filter(
        responsibles=all_responsibles, key="action_plan_responsible"
    )

# KPIs do Action Plan
st.subheader("Visao Geral")

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
st.plotly_chart(fig, use_container_width=True)

# Tabela de detalhes
st.subheader("Detalhes das Acoes")

table_df = gantt_component.create_details_table(df)

if not table_df.empty:
    # Tabela interativa
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    # Botao de export CSV
    csv = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(label="Exportar CSV", data=csv, file_name="action_plan.csv", mime="text/csv")
else:
    st.info("Nenhuma acao corresponde aos filtros selecionados.")
