"""Pagina Streamlit - Dashboard Executivo BSC.

Consolida KPIs de Strategy Map e Action Plan da sessao atual.
Carrega automaticamente do chat com Consultor BSC.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import streamlit as st
from ui.helpers.mem0_loader import load_action_plan, load_strategy_map

st.set_page_config(page_title="Dashboard Executivo", layout="wide")

st.title("Dashboard Executivo BSC")

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

# Carregar dados da sessao atual
with st.spinner("Carregando dados do BSC da sessao atual..."):
    objectives, objectives_error = load_strategy_map(user_id)
    actions, actions_error = load_action_plan(user_id)

# Mensagem de contexto
st.info(f"Exibindo Dashboard da sessao atual (user_id: {user_id[:8]}...)")
st.markdown("---")

# KPIs Consolidados
st.subheader("Visao Geral Consolidada")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_obj = len(objectives) if objectives else 0
    st.metric("Total Objetivos", total_obj)

with col2:
    total_actions = len(actions) if actions else 0
    st.metric("Total Acoes", total_actions)

with col3:
    if objectives:
        alta_prio_obj = len([o for o in objectives if o.priority == "ALTA"])
        pct = (alta_prio_obj / total_obj * 100) if total_obj else 0
        st.metric("Objetivos Alta Prioridade", alta_prio_obj, delta=f"{pct:.0f}%")
    else:
        st.metric("Objetivos Alta Prioridade", "N/A")

with col4:
    if actions:
        alta_prio_act = len([a for a in actions if a.priority == "HIGH"])
        pct = (alta_prio_act / total_actions * 100) if total_actions else 0
        st.metric("Acoes Alta Prioridade", alta_prio_act, delta=f"{pct:.0f}%")
    else:
        st.metric("Acoes Alta Prioridade", "N/A")

st.divider()

# Strategy Map Section
st.subheader("Strategy Map BSC")

if objectives:
    st.success(f"[OK] {len(objectives)} objetivos estrategicos carregados")

    # Objetivos por perspectiva
    st.markdown("**Distribuicao por Perspectiva:**")
    persp_counts = {}
    for obj in objectives:
        persp = obj.perspective
        persp_counts[persp] = persp_counts.get(persp, 0) + 1

    cols = st.columns(4)
    for idx, (persp, count) in enumerate(persp_counts.items()):
        with cols[idx % 4]:
            st.metric(persp, count)
else:
    st.warning("Strategy Map ainda nao foi gerado")
    st.info("Complete a fase SOLUTION DESIGN no chat para gerar")

st.divider()

# Action Plan Section
st.subheader("Action Plan - Timeline de Implementacao")

if actions:
    st.success(f"[OK] {len(actions)} acoes mapeadas")

    # Distribuição por fase
    st.markdown("**Distribuicao por Fase:**")

    # Agrupar ações por mês de início
    from collections import defaultdict

    phase_counts = defaultdict(int)

    for action in actions:
        # Extrair mês de start_date (formato: YYYY-MM-DD)
        try:
            month = action.start_date[:7]  # YYYY-MM
            phase_counts[month] += 1
        except:
            phase_counts["Indefinido"] += 1

    # Mostrar top 3 meses com mais ações
    sorted_phases = sorted(phase_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    cols = st.columns(3)
    for idx, (month, count) in enumerate(sorted_phases):
        with cols[idx]:
            st.metric(month, count, label="Acoes agendadas")
else:
    st.warning("Action Plan ainda nao foi gerado")
    st.info("Complete o workflow consultivo completo para gerar")

st.divider()

# Botões de navegação
col1, col2 = st.columns(2)

with col1:
    if st.button("Ver Strategy Map Detalhado", type="primary", use_container_width=True):
        st.switch_page("pages/1_strategy_map.py")

with col2:
    if st.button("Ver Action Plan Completo", type="primary", use_container_width=True):
        st.switch_page("pages/2_action_plan.py")
