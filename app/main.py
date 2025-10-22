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
import asyncio

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
# Configuracao de Logging por Sessao
# ============================================================================

def setup_session_logging():
    """
    Configura logging por sessao Streamlit com dual output (console + arquivo).
    
    Cada sessao tem arquivo separado em logs/session_TIMESTAMP_PID.log
    Console: output simplificado (INFO level)
    Arquivo: output completo (DEBUG level) com timestamps precisos e thread IDs
    
    Returns:
        str: Path do arquivo de log criado
    """
    from loguru import logger
    from datetime import datetime
    
    # Gerar session_id unico (timestamp + PID para garantir unicidade)
    if 'session_id' not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.session_id = f"{timestamp}_{os.getpid()}"
    
    session_id = st.session_state.session_id
    
    # Criar pasta logs se nao existir
    os.makedirs("logs", exist_ok=True)
    
    # Path do arquivo de log
    log_file = f"logs/session_{session_id}.log"
    
    # Configurar loguru (apenas se ainda nao configurado para esta sessao)
    if 'logging_configured' not in st.session_state:
        # Remover handler padrao
        logger.remove()
        
        # Handler 1: Console (simplificado, apenas INFO+)
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # Handler 2: Arquivo (completo, DEBUG+, com thread IDs)
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {thread.name:<20} | {level:<8} | {message}",
            level="DEBUG",
            rotation="50 MB",  # Rotacionar se arquivo > 50MB
            retention="7 days",  # Manter logs por 7 dias
            compression="zip",  # Comprimir logs antigos
            enqueue=False  # ⚡ DESABILITADO: enqueue=True causa delay de segundos nos logs (Issue #2 Out/2025)
        )
        
        st.session_state.logging_configured = True
        st.session_state.log_file = log_file
        logger.info(f"[LOGGING] Sessao iniciada | arquivo={log_file}")
    
    return st.session_state.get('log_file', log_file)


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
    # Configurar logging por sessao
    log_file = setup_session_logging()
    
    # [VERSAO] Log de versao para confirmar codigo carregado
    from loguru import logger
    logger.info("[APP v3.8-20251022-15:00] Streamlit - Logging fix (enqueue=False) + defensive try/except asyncio.gather")
    logger.info(f"[APP v3.8-20251022-15:00] Python executable: {sys.executable}")
    logger.info(f"[APP v3.8-20251022-15:00] Python version: {sys.version}")
    logger.info(f"[APP v3.8-20251022-15:00] Working directory: {os.getcwd()}")
    logger.info(f"[APP v3.8-20251022-15:00] Project root: {root_dir}")
    
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

    # Gerar/recuperar user_id unico para o cliente (persistente na sessao)
    import uuid
    if "user_id" not in st.session_state:
        # Primeira interacao: gerar user_id unico
        st.session_state.user_id = f"streamlit_user_{uuid.uuid4().hex[:8]}"
    
    # CRÍTICO: Gerar session_id UMA VEZ por sessão (persistente entre mensagens)
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    user_id = st.session_state.user_id
    session_id = st.session_state.session_id  # Reutilizar mesmo session_id

    # Obter historico de chat
    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages[-5:]  # Ultimas 5 mensagens
        if msg["role"] in ["user", "assistant"]
    ]

    try:
        # Executar workflow consultivo (ONBOARDING → DISCOVERY → APPROVAL)
        result = workflow.run(
            query=query,
            session_id=session_id,
            user_id=user_id,  # CRÍTICO: Habilita workflow consultivo!
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
    
    # Mostrar path do log da sessao atual
    if 'log_file' in st.session_state:
        with st.expander("[INFO] Log da Sessao", expanded=False):
            st.info(f"📝 **Arquivo de log completo**: `{st.session_state.log_file}`")
            st.caption("Este arquivo contem logs detalhados com timestamps precisos e thread IDs para analise de performance.")

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
