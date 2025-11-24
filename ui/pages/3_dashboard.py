"""Pagina Streamlit - Dashboard Executivo BSC.

Consolida KPIs de Strategy Map e Action Plan com metricas executivas.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st

from ui.helpers.mem0_loader import list_all_clients, load_action_plan, load_strategy_map

st.set_page_config(page_title="Dashboard Executivo", layout="wide")

st.title("Dashboard Executivo BSC")

# SPRINT 4: Integracao Mem0 completa
st.markdown("**Selecione um cliente para visualizar o Dashboard Executivo:**")

# Carregar lista de clientes
clients, error = list_all_clients()

if error:
    st.error(error)
    st.stop()

if not clients:
    st.warning(
        "[INFO] Nenhum cliente encontrado no sistema. Execute o workflow consultivo primeiro."
    )
    st.stop()

# Seletor de cliente
client_options = {f"{c['company_name']} ({c['sector']})": c["user_id"] for c in clients}
selected_client = st.selectbox(
    "Cliente:", options=list(client_options.keys()), key="dashboard_client_selector"
)

if not selected_client:
    st.info("Selecione um cliente acima para visualizar o Dashboard.")
    st.stop()

# Buscar user_id do cliente selecionado
user_id = client_options[selected_client]

# Carregar dados do Mem0
with st.spinner(f"Carregando dados de '{selected_client}'..."):
    # CORREÇÃO SESSAO 43: load_strategy_map agora retorna 3 valores
    objectives, connections, error_obj = load_strategy_map(user_id)
    actions, error_act = load_action_plan(user_id)

# Tratamento de erros
has_objectives = objectives is not None and not error_obj
has_actions = actions is not None and not error_act

if not has_objectives and not has_actions:
    st.warning("[INFO] Cliente ainda nao tem dados para Dashboard.")
    st.info(
        "Execute as fases SOLUTION_DESIGN (Strategy Map) e IMPLEMENTATION (Action Plan) do workflow consultivo."
    )
    st.stop()

if not has_objectives:
    st.warning(error_obj)
    objectives = []  # Lista vazia para evitar erros

if not has_actions:
    st.warning(error_act)
    actions = []  # Lista vazia para evitar erros

# Dados carregados - prosseguir com dashboard

# KPIs consolidados
st.subheader("KPIs Consolidados")

col1, col2, col3, col4 = st.columns(4)

with col1:
    alta_prior_obj = len([o for o in objectives if o.priority == "Alta"])
    st.metric(
        label="Objetivos Estrategicos",
        value=len(objectives),
        delta=f"{alta_prior_obj} alta prioridade",
    )

with col2:
    high_prior_act = len([a for a in actions if a.priority == "HIGH"])
    st.metric(
        label="Acoes Planejadas",
        value=len(actions),
        delta=f"{high_prior_act}/{len(actions)} criticas",
    )

with col3:
    total_kpis = sum([len(o.related_kpis) for o in objectives])
    st.metric(
        label="KPIs Definidos",
        value=total_kpis,
        delta=f"{total_kpis/len(objectives):.1f} por objetivo",
    )

with col4:
    responsibles = set([a.responsible for a in actions])
    st.metric(label="Envolvidos", value=len(responsibles))

# Progress por perspectiva
st.subheader("Distribuicao por Perspectiva BSC")

for persp in ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]:
    persp_objs = len([o for o in objectives if o.perspective == persp])
    persp_actions = len([a for a in actions if a.perspective == persp])

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.write(f"**{persp}**")
    with col2:
        st.write(f"{persp_objs} objetivos")
    with col3:
        st.write(f"{persp_actions} acoes")

    # Progress bar (simulacao - no futuro, calcular real)
    progress = persp_actions / len(actions) if actions else 0
    st.progress(progress)
    st.divider()

# Export completo
st.subheader("Export Completo")

col1, col2 = st.columns(2)

with col1:
    if st.button("Exportar Strategy Map (PNG)"):
        st.info(
            "[INFO] Funcionalidade de export PNG sera implementada no Sprint 4 TODO 7 (integracao completa)"
        )

with col2:
    # Export CSV do Action Plan
    import pandas as pd

    actions_data = [
        {
            "Acao": a.action_title,
            "Perspectiva": a.perspective,
            "Prioridade": a.priority,
            "Responsavel": a.responsible,
            "Inicio": a.start_date,
            "Prazo": a.due_date,
        }
        for a in actions
    ]

    df = pd.DataFrame(actions_data)
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Exportar Action Plan (CSV)",
        data=csv,
        file_name="action_plan_completo.csv",
        mime="text/csv",
    )
