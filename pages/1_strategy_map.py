"""Pagina Streamlit - Strategy Map BSC (Conexoes Causa-Efeito).

Visualiza objetivos estrategicos BSC gerados no chat com Consultor BSC.
Carrega automaticamente da sessao atual.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st
from ui.components.bsc_network_graph import BSCNetworkGraph
from ui.helpers.mem0_loader import load_strategy_map

st.set_page_config(page_title="Strategy Map BSC", layout="wide")

st.title("Strategy Map BSC - Conexoes Causa-Efeito")

# Carregar user_id da sessao atual (criado no chat com Consultor BSC)
# CRITICAL: Ler de query_params PRIMEIRO (persiste entre páginas)
#
# WORKAROUND BUG STREAMLIT #10406 (Feb 2025): st.query_params NAO persiste apos refresh
# Solucao temporaria: usar st.experimental_get_query_params (deprecated mas FUNCIONA)
# Fonte: https://github.com/streamlit/streamlit/issues/10406
if "user_id" not in st.session_state:
    query_params = st.experimental_get_query_params()
    user_id_from_url = query_params.get("uid", [None])[0]
    if user_id_from_url:
        st.session_state.user_id = user_id_from_url
    else:
        st.warning("[INFO] Sessao nao iniciada. Faca uma pergunta ao Consultor BSC primeiro.")
        st.info("Navegue para 'Consultor BSC' no menu lateral e comece a conversa.")
        st.stop()  # Para execução se não tem user_id

# CORREÇÃO SESSAO 40: SEMPRE sincronizar query_params com session_state
if "user_id" in st.session_state:
    st.experimental_set_query_params(uid=st.session_state.user_id)

user_id = st.session_state.user_id

# Carregar objectives do Mem0 (sessao atual)
with st.spinner("Carregando Strategy Map da sessao atual..."):
    objectives, error = load_strategy_map(user_id)

if error:
    st.warning(error)
    st.info("Execute o workflow consultivo completo no chat para gerar o Strategy Map.")
    st.info("**Fases:** ONBOARDING -> DISCOVERY -> APPROVAL -> SOLUTION DESIGN")
    st.stop()

if not objectives:
    st.warning("Nenhum objetivo estrategico encontrado para esta sessao.")
    st.info("Complete a fase SOLUTION DESIGN no chat para gerar o Strategy Map.")
    st.stop()

# Mensagem de contexto
st.info(f"Exibindo Strategy Map da sessao atual (user_id: {user_id[:8]}...)")
st.markdown("---")

# KPIs do Strategy Map
st.subheader("Visao Geral do Strategy Map")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Objetivos", len(objectives))
with col2:
    # BUG FIX (Sessao 41, 2025-11-22): StrategicObjective.priority usa "Alta" (nao "ALTA")
    # Schema: Literal["Alta", "Média", "Baixa"] - case-sensitive!
    alta_prioridade = len([o for o in objectives if o.priority == "Alta"])
    pct = (alta_prioridade / len(objectives) * 100) if objectives else 0
    st.metric("Alta Prioridade", alta_prioridade, delta=f"{pct:.0f}%")
with col3:
    perspectivas = set([o.perspective for o in objectives])
    st.metric("Perspectivas", len(perspectivas))
with col4:
    # BUG FIX (Sessao 41, 2025-11-22): cause_effect_links nao existe em StrategicObjective
    # Usando dependencies como proxy para relacoes entre objetivos
    total_deps = sum([len(o.dependencies) for o in objectives])
    st.metric("Total de Dependencias", total_deps)

# Network Graph
st.subheader("Grafo de Conexoes BSC")

graph = BSCNetworkGraph(objectives)
fig = graph.create_plotly_figure(
    filter_perspective=None, filter_priority=None  # Mostrar todas  # Mostrar todas
)
st.plotly_chart(fig, use_container_width=True)

# Tabela de objetivos detalhada
st.subheader("Detalhes dos Objetivos Estrategicos")

# BUG FIX (Sessao 41, 2025-11-22): BSCNetworkGraph nao tem create_details_table()
# Criar tabela manualmente a partir de objectives (lista de StrategicObjective)
if objectives:
    import pandas as pd

    table_df = pd.DataFrame(
        [
            {
                "Objetivo": obj.name,
                "Perspectiva": obj.perspective,
                "Prioridade": obj.priority,
                "Prazo": obj.timeframe,
                "KPIs Relacionados": ", ".join(obj.related_kpis) if obj.related_kpis else "N/A",
                "Dependencias": ", ".join(obj.dependencies) if obj.dependencies else "Nenhuma",
                "Descricao": (
                    obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
                ),
            }
            for obj in objectives
        ]
    )

    st.dataframe(table_df, use_container_width=True, hide_index=True)

    # Botao export CSV
    csv = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Exportar CSV", data=csv, file_name="strategy_map_bsc.csv", mime="text/csv"
    )
else:
    st.info("Nenhum objetivo corresponde aos criterios.")
