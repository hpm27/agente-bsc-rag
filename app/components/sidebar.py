"""
Componente de sidebar com configuracoes da aplicacao.
"""

import streamlit as st

from app.utils import clear_chat_history, get_default_config


def render_sidebar() -> str:
    """
    Renderiza sidebar com configuracoes e controles.

    Returns:
        str: Página selecionada ("Chat BSC", "Dashboard Multi-Cliente" ou "Analytics Dashboard")
    """
    with st.sidebar:
        # Logo e titulo
        st.title("Agente BSC RAG")
        st.markdown("**Consultor IA em Balanced Scorecard**")
        st.markdown("---")

        # Navegacao de paginas
        st.subheader("Navegação")
        selected_page = st.radio(
            "Selecione a página:",
            options=["Chat BSC", "Dashboard Multi-Cliente", "Analytics Dashboard"],
            index=0,
            key="page_selector",
        )
        st.markdown("---")

        # Secao: Perspectivas BSC
        st.subheader("Perspectivas BSC")
        st.caption("Selecione quais perspectivas consultar")

        config = st.session_state.config

        config["perspectives"]["financial"] = st.checkbox(
            "Financeira",
            value=config["perspectives"]["financial"],
            help="Indicadores financeiros, ROI, receita, lucro, EVA",
        )

        config["perspectives"]["customer"] = st.checkbox(
            "Clientes",
            value=config["perspectives"]["customer"],
            help="Satisfacao, retencao, proposta de valor, segmentacao",
        )

        config["perspectives"]["process"] = st.checkbox(
            "Processos Internos",
            value=config["perspectives"]["process"],
            help="Eficiencia operacional, qualidade, inovacao de processos",
        )

        config["perspectives"]["learning"] = st.checkbox(
            "Aprendizado e Crescimento",
            value=config["perspectives"]["learning"],
            help="Capital humano, tecnologia, cultura organizacional",
        )

        st.markdown("---")

        # Secao: Configuracoes de Retrieval
        st.subheader("Configuracoes de Busca")

        config["top_k"] = st.slider(
            "Top K Documentos",
            min_value=5,
            max_value=20,
            value=config["top_k"],
            step=1,
            help="Numero de documentos a recuperar do vector store",
        )

        config["confidence_threshold"] = st.slider(
            "Threshold de Confianca",
            min_value=0.0,
            max_value=1.0,
            value=config["confidence_threshold"],
            step=0.05,
            help="Score minimo de confianca para aceitar resposta",
        )

        st.markdown("---")

        # Secao: Configuracoes do Workflow
        st.subheader("Configuracoes do Workflow")

        config["max_refinement_iterations"] = st.slider(
            "Max Iteracoes de Refinamento",
            min_value=0,
            max_value=2,
            value=config["max_refinement_iterations"],
            step=1,
            help="Numero maximo de ciclos de refinamento com Judge",
        )

        config["enable_judge"] = st.checkbox(
            "Habilitar Judge Agent",
            value=config["enable_judge"],
            help="Usar Judge Agent para validacao de qualidade",
        )

        # Aviso sobre configuracoes (MVP v1)
        st.info(
            "[INFO] MVP v1: Configuracoes acima sao informativas. "
            "O workflow usa valores do arquivo .env por enquanto. "
            "Configuracao dinamica sera implementada na v2."
        )

        st.markdown("---")

        # Secao: Configuracoes Avancadas
        with st.expander("Configuracoes Avancadas"):
            config["llm_temperature"] = st.slider(
                "Temperatura LLM",
                min_value=0.0,
                max_value=1.0,
                value=config["llm_temperature"],
                step=0.1,
                help="Controla criatividade vs determinismo",
            )

            config["llm_model"] = st.selectbox(
                "Modelo LLM",
                options=["GPT-5", "Claude Sonnet 4.5"],
                index=0 if config["llm_model"] == "GPT-5" else 1,
                help="Modelo de linguagem a utilizar",
            )

            config["vector_store"] = st.selectbox(
                "Vector Store",
                options=["Qdrant", "Weaviate", "Redis"],
                index=["Qdrant", "Weaviate", "Redis"].index(config["vector_store"]),
                help="Vector database utilizado (informativo)",
            )

        st.markdown("---")

        # Botoes de acao
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Resetar Config", use_container_width=True):
                st.session_state.config = get_default_config()
                st.rerun()

        with col2:
            if st.button("Limpar Chat", use_container_width=True):
                clear_chat_history()
                st.rerun()

        st.markdown("---")

        # Informacoes do sistema
        st.caption("**Informacoes do Sistema**")

        # Contagem de perspectivas ativas
        active_perspectives = sum(config["perspectives"].values())
        st.caption(f"Perspectivas ativas: {active_perspectives}/4")

        # Status do Judge
        judge_status = "Ativo" if config["enable_judge"] else "Inativo"
        st.caption(f"Judge Agent: {judge_status}")

        # Vector Store
        st.caption(f"Vector Store: {config['vector_store']}")

        # Versao
        st.caption("Versao: 0.1.0 (MVP)")

        st.markdown("---")

        # Links uteis
        st.caption("**Links Uteis**")
        st.caption("[Documentacao](docs/QUICKSTART.md)")
        st.caption("[GitHub](https://github.com/seu-usuario/agente-bsc-rag)")

    return selected_page


def get_active_perspectives() -> list[str]:
    """
    Retorna lista de perspectivas ativas conforme configuracao.

    Returns:
        list[str]: Lista de perspectivas ativas
    """
    config = st.session_state.config
    active = []

    perspective_map = {
        "financial": "financial",
        "customer": "customer",
        "process": "process",
        "learning": "learning",
    }

    for key, value in config["perspectives"].items():
        if value and key in perspective_map:
            active.append(perspective_map[key])

    return active
