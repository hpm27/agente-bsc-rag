"""Pagina Streamlit - Strategy Map BSC (Conexoes Causa-Efeito).

Visualiza objetivos estrategicos BSC em grafo NetworkX + Plotly
com filtros por perspectiva e prioridade.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st

from ui.components.bsc_network_graph import BSCNetworkGraph
from ui.components.filters import BSCFilters
from ui.helpers.mem0_loader import list_all_clients, load_strategy_map

st.set_page_config(page_title="Strategy Map BSC", layout="wide")

st.title("Strategy Map BSC - Conexoes Causa-Efeito")

# SPRINT 4: Integracao Mem0 completa
st.markdown("**Selecione um cliente para visualizar o Strategy Map BSC:**")

# Carregar lista de clientes
clients, error = list_all_clients()

if error:
    st.error(error)
    st.stop()

if not clients:
    st.warning(
        "[INFO] Nenhum cliente encontrado no sistema. Execute o workflow consultivo (ONBOARDING -> SOLUTION_DESIGN) primeiro."
    )
    st.stop()

# Seletor de cliente
client_options = {f"{c['company_name']} ({c['sector']})": c["user_id"] for c in clients}
selected_client = st.selectbox(
    "Cliente:", options=list(client_options.keys()), key="strategy_map_client_selector"
)

if not selected_client:
    st.info("Selecione um cliente acima para visualizar o Strategy Map.")
    st.stop()

# Buscar user_id do cliente selecionado
user_id = client_options[selected_client]

# Carregar objectives do Mem0
with st.spinner(f"Carregando Strategy Map de '{selected_client}'..."):
    # CORREÇÃO SESSAO 43: load_strategy_map agora retorna 3 valores
    objectives, connections, error = load_strategy_map(user_id)

if error:
    st.warning(error)
    st.info("Execute a fase SOLUTION_DESIGN do workflow consultivo para gerar o Strategy Map.")
    st.stop()

if not objectives:
    st.warning("Nenhum objetivo estrategico encontrado. Execute a fase SOLUTION_DESIGN primeiro.")
    st.stop()

# Filtros na sidebar
with st.sidebar:
    st.header("Filtros")

    filter_persp = BSCFilters.perspective_filter(
        key="strategy_map_perspective",
        default=["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"],
    )

    filter_prior = BSCFilters.priority_filter(
        key="strategy_map_priority", default=["Alta", "Media", "Baixa"]
    )

# Criar grafo
# CORREÇÃO SESSAO 43: Passar connections para visualizar setas
graph_component = BSCNetworkGraph(objectives, connections=connections if connections else [])
graph = graph_component.build_graph()

# Estatisticas rapidas
st.subheader("Visao Geral")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Objetivos", len(objectives))
with col2:
    high_count = len([o for o in objectives if o.priority == "Alta"])
    st.metric("Alta Prioridade", high_count)
with col3:
    st.metric("Conexoes", graph.number_of_edges())
with col4:
    perspectives = set([o.perspective for o in objectives])
    st.metric("Perspectivas", len(perspectives))

# Visualizacao
st.subheader("Grafo de Conexoes Causa-Efeito")

fig = graph_component.create_plotly_figure(
    filter_perspective=filter_persp[0] if len(filter_persp) == 1 else None,
    filter_priority=filter_prior,
)

st.plotly_chart(fig, use_container_width=True)

# Detalhes por perspectiva
st.subheader("Detalhes por Perspectiva")

for persp in ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]:
    if persp not in filter_persp:
        continue

    persp_objs = [o for o in objectives if o.perspective == persp]

    if not persp_objs:
        continue

    with st.expander(f"{persp} ({len(persp_objs)} objetivos)", expanded=False):
        for obj in persp_objs:
            st.markdown(f"**{obj.name}**")
            st.write(f"- Prioridade: {obj.priority}")
            st.write(f"- Prazo: {obj.timeframe}")
            st.write(f"- KPIs: {', '.join(obj.related_kpis)}")
            st.write("- Criterios de Sucesso:")
            for criteria in obj.success_criteria:
                st.write(f"  - {criteria}")
            if obj.dependencies:
                st.write(f"- Dependencias: {', '.join(obj.dependencies)}")
            st.divider()
