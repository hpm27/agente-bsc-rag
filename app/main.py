"""
Aplicacao principal Streamlit para o Agente BSC RAG.

Interface web interativa para consultar o sistema multi-agente
de Balanced Scorecard com LangGraph.

Uso:
    streamlit run app/main.py
"""

# Fix PyTorch-Streamlit path inspection warning
# Ref: https://github.com/streamlit/streamlit/issues/9845
import os
os.environ["STREAMLIT_SERVER_ENABLE_FILE_WATCHER"] = "false"

import streamlit as st
from typing import Dict, Any
import sys
from pathlib import Path

# Adicionar diretorio raiz ao path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.utils import (
    load_environment,
    check_required_env_vars,
    init_workflow,
    init_session_state,
    save_message,
)
from app.components.sidebar import render_sidebar, get_active_perspectives
from app.components.results import render_results


# ============================================================================
# Configuracao da Pagina
# ============================================================================

st.set_page_config(
    page_title="Agente BSC RAG",
    page_icon="[BSC]",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/seu-usuario/agente-bsc-rag",
        "Report a bug": "https://github.com/seu-usuario/agente-bsc-rag/issues",
        "About": "Sistema multi-agente para consultoria em Balanced Scorecard",
    },
)


# ============================================================================
# CSS Customizado
# ============================================================================

st.markdown(
    """
<style>
    /* Estilo geral */
    .main {
        padding: 1rem;
    }

    /* Mensagens de chat */
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Badges de perspectiva */
    .perspective-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }

    /* Cores das perspectivas */
    .financial { background-color: #1f77b4; color: white; }
    .customer { background-color: #2ca02c; color: white; }
    .process { background-color: #ff7f0e; color: white; }
    .learning { background-color: #9467bd; color: white; }

    /* Metricas */
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }

    /* Loading spinner customizado */
    .stSpinner > div {
        border-color: #1f77b4;
    }
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# Inicializacao
# ============================================================================

def initialize_app() -> None:
    """
    Inicializa a aplicacao: carrega env vars, verifica config, inicializa workflow.
    """
    # Carregar variaveis de ambiente
    load_environment()

    # Verificar variaveis obrigatorias
    if not check_required_env_vars():
        st.error("[ERRO] Configuracao incompleta. Corrija as variaveis de ambiente e recarregue.")
        st.stop()

    # Inicializar session state
    init_session_state()

    # Inicializar workflow (cached)
    if not st.session_state.workflow_initialized:
        with st.spinner("Inicializando workflow LangGraph..."):
            st.session_state.workflow = init_workflow()
            st.session_state.workflow_initialized = True


def process_query(query: str) -> Dict[str, Any]:
    """
    Processa query do usuario usando o workflow LangGraph.

    Args:
        query: Pergunta do usuario

    Returns:
        Dict: Resultado do workflow (BSCState)
    """
    workflow = st.session_state.workflow
    config = st.session_state.config

    # Gerar session_id unico para rastreamento
    import uuid
    session_id = f"streamlit_{uuid.uuid4().hex[:8]}"

    # Obter historico de chat
    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages[-5:]  # Ultimas 5 mensagens
        if msg["role"] in ["user", "assistant"]
    ]

    try:
        # Executar workflow (configuracoes vem do .env por enquanto)
        # TODO: Refatorar workflow para aceitar config dinamico
        result = workflow.run(
            query=query,
            session_id=session_id,
            chat_history=chat_history if chat_history else None
        )

        # Converter BSCState para dict se necessario
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        elif hasattr(result, "dict"):
            result = result.dict()

        return result

    except Exception as e:
        st.error(f"[ERRO] Falha ao processar query: {e}")
        raise


def render_chat_history() -> None:
    """
    Renderiza historico de mensagens do chat.
    """
    for message in st.session_state.messages:
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            st.markdown(content)

            # Se for resposta do assistant, mostrar detalhes
            if role == "assistant" and "metadata" in message:
                metadata = message["metadata"]
                render_results(metadata)


def render_welcome_message() -> None:
    """
    Renderiza mensagem de boas-vindas quando nao ha historico.
    """
    st.markdown(
        """
        # Bem-vindo ao Agente BSC RAG

        Sistema inteligente de consultoria em **Balanced Scorecard** usando IA generativa
        e arquitetura multi-agente.

        ## Como usar

        1. **Configure as perspectivas** na barra lateral (Financeira, Cliente, Processos, Aprendizado)
        2. **Digite sua pergunta** no campo abaixo
        3. **Receba uma resposta** consultando multiplas perspectivas BSC simultaneamente

        ## Exemplos de perguntas

        - "Quais sao os principais KPIs da perspectiva financeira?"
        - "Como implementar um Balanced Scorecard em uma empresa?"
        - "Qual a relacao entre satisfacao de clientes e lucratividade?"
        - "Explique o conceito de mapa estrategico no BSC"
        - "Quais indicadores usar para processos internos?"

        ## Recursos

        - [OK] Sistema multi-agente com 4 especialistas BSC
        - [OK] Validacao de qualidade com Judge Agent
        - [OK] Base de conhecimento com livros de Kaplan & Norton
        - [OK] Refinamento iterativo de respostas
        - [OK] Rastreabilidade de fontes

        **Digite sua pergunta abaixo para comecar!**
        """
    )


# ============================================================================
# Interface Principal
# ============================================================================

def main() -> None:
    """
    Funcao principal da aplicacao.
    """
    # Inicializar aplicacao
    initialize_app()

    # Renderizar sidebar
    render_sidebar()

    # Header principal
    st.title("Agente BSC RAG")
    st.caption("Consultor Inteligente em Balanced Scorecard")

    # Mostrar mensagem de boas-vindas ou historico
    if not st.session_state.messages:
        render_welcome_message()
    else:
        render_chat_history()

    # Chat input
    user_query = st.chat_input("Digite sua pergunta sobre Balanced Scorecard...")

    if user_query:
        # Adicionar pergunta do usuario ao chat
        save_message("user", user_query)

        with st.chat_message("user"):
            st.markdown(user_query)

        # Processar query
        with st.chat_message("assistant"):
            with st.spinner("Consultando especialistas BSC..."):
                try:
                    # Executar workflow
                    result = process_query(user_query)

                    # Extrair resposta final
                    final_answer = result.get(
                        "final_response", "Desculpe, nao consegui gerar uma resposta."
                    )

                    # Mostrar resposta
                    st.markdown(final_answer)

                    # Mostrar detalhes
                    render_results(result)

                    # Salvar resposta no historico
                    save_message("assistant", final_answer, metadata=result)

                    # Rerun para atualizar interface
                    st.rerun()

                except Exception as e:
                    error_msg = f"Erro ao processar sua pergunta: {str(e)}"
                    st.error(f"[ERRO] {error_msg}")

                    # Salvar erro no historico
                    save_message("assistant", error_msg)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
