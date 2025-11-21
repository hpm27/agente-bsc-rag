"""Streamlit App - BSC RAG Agent UI.

Entry point para aplicacao Streamlit multipage.
Navegue pelas paginas usando a sidebar.

Paginas disponiveis:
1. Strategy Map BSC - Visualizacao grafo conexoes causa-efeito
2. Action Plan - Timeline Gantt de implementacao
3. Dashboard Executivo - KPIs consolidados

Para executar:
    streamlit run app.py

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

# CRITICAL: Carregar .env ANTES de qualquer import que use variáveis de ambiente
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="BSC RAG Agent", page_icon="[BSC]", layout="wide"  # ASCII apenas, sem emojis
)

st.title("BSC RAG Agent - Consultor Estrategico")

st.markdown(
    """
## Bem-vindo ao BSC RAG Agent UI

### [INFO] Como navegar

Use a **sidebar** (menu lateral a esquerda, indicado por ">") para acessar as paginas:

**PRINCIPAL:**
0. **Consultor BSC** - Chat interativo com workflow consultivo (START HERE!)

**VISUALIZACOES:**
1. **Strategy Map BSC** - Visualize objetivos estrategicos e conexoes causa-efeito
2. **Action Plan** - Timeline Gantt de acoes de implementacao
3. **Dashboard Executivo** - KPIs consolidados e metricas

**NOTA:** Clique no icone ">" no canto superior esquerdo se a sidebar nao estiver visivel.

---

### [INFO] Status Sprint 4

- [OK] Components: bsc_network_graph, gantt_timeline, filters
- [OK] Pages: strategy_map, action_plan, dashboard
- [OK] Testes smoke: 11/11 passando (100%)
- [OK] Integracao Mem0 completa (backend + frontend)

Para informacoes tecnicas completas, consulte:
- `docs/sprints/SPRINT_4_UI_VISUALIZATION.md`
"""
)

# Footer
st.divider()
st.caption("BSC RAG Agent - Sessao 40 (Nov 21, 2025) - Sprint 4: UI Visualization")
