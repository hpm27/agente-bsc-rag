"""
Utilitarios para a interface Streamlit.

Funcoes helper para inicializacao do workflow, formatacao de resultados
e gerenciamento de configuracoes.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv


def load_environment() -> None:
    """
    Carrega variaveis de ambiente do arquivo .env.
    """
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        st.warning(
            "[WARN] Arquivo .env nao encontrado. "
            "Certifique-se de configurar as variaveis de ambiente."
        )


def check_required_env_vars() -> bool:
    """
    Verifica se todas as variaveis de ambiente obrigatorias estao configuradas.

    Returns:
        bool: True se todas configuradas, False caso contrario
    """
    required_vars = [
        "OPENAI_API_KEY",
        "COHERE_API_KEY",
    ]

    optional_vars = [
        "ANTHROPIC_API_KEY",
    ]

    missing_required = [var for var in required_vars if not os.getenv(var)]
    missing_optional = [var for var in optional_vars if not os.getenv(var)]

    if missing_required:
        st.error(
            f"[ERRO] Variaveis de ambiente obrigatorias faltando: {', '.join(missing_required)}"
        )
        st.info(
            "[INFO] Configure as variaveis no arquivo .env ou como variaveis de ambiente do sistema."
        )
        return False

    if missing_optional:
        st.warning(
            f"[WARN] Variaveis opcionais faltando: {', '.join(missing_optional)}. "
            "Contextual Retrieval pode nao funcionar."
        )

    return True


@st.cache_resource
def init_workflow():
    """
    Inicializa o workflow LangGraph (singleton com cache).

    Returns:
        BSCWorkflow: Instancia do workflow
    """
    try:
        from src.graph.workflow import get_workflow

        workflow = get_workflow()
        st.success("[OK] Workflow LangGraph inicializado com sucesso!")
        return workflow
    except Exception as e:
        st.error(f"[ERRO] Falha ao inicializar workflow: {e}")
        st.stop()


def get_default_config() -> Dict[str, Any]:
    """
    Retorna configuracao padrao da aplicacao.

    Returns:
        Dict: Configuracao padrao
    """
    return {
        "perspectives": {
            "financial": True,
            "customer": True,
            "process": True,
            "learning": True,
        },
        "top_k": 10,
        "confidence_threshold": 0.7,
        "max_refinement_iterations": 2,
        "vector_store": "Qdrant",
        "enable_judge": True,
        "llm_temperature": 0.7,
        "llm_model": "GPT-5",
    }


def format_perspective_name(perspective: str) -> str:
    """
    Formata nome de perspectiva para display.

    Args:
        perspective: Nome interno da perspectiva

    Returns:
        str: Nome formatado
    """
    names = {
        "financial": "Perspectiva Financeira",
        "customer": "Perspectiva de Clientes",
        "process": "Perspectiva de Processos Internos",
        "learning": "Perspectiva de Aprendizado e Crescimento",
    }
    return names.get(perspective, perspective.capitalize())


def get_perspective_color(perspective: str) -> str:
    """
    Retorna cor associada a uma perspectiva BSC.

    Args:
        perspective: Nome da perspectiva

    Returns:
        str: Codigo de cor hexadecimal
    """
    colors = {
        "financial": "#1f77b4",  # Azul
        "customer": "#2ca02c",  # Verde
        "process": "#ff7f0e",  # Laranja
        "learning": "#9467bd",  # Roxo
    }
    return colors.get(perspective, "#808080")


def format_confidence_score(score: float) -> str:
    """
    Formata score de confianca para display.

    Args:
        score: Score entre 0 e 1

    Returns:
        str: Score formatado com emoji de status
    """
    percentage = score * 100

    if percentage >= 80:
        status = "[HIGH]"
    elif percentage >= 60:
        status = "[MED]"
    else:
        status = "[LOW]"

    return f"{status} {percentage:.1f}%"


def format_document_source(doc: Dict[str, Any]) -> str:
    """
    Formata informacao de fonte do documento.
    
    Usa document_title (titulo legivel) quando disponivel,
    com fallback para source (filename).

    Args:
        doc: Dicionario com metadados do documento

    Returns:
        str: Fonte formatada com titulo legivel
        
    Example:
        >>> # Com document_title:
        >>> format_document_source({"metadata": {"document_title": "The Balanced Scorecard", "page": 5}})
        "The Balanced Scorecard (pag. 5)"
        
        >>> # Sem document_title (fallback):
        >>> format_document_source({"metadata": {"source": "doc.pdf", "page": 3}})
        "doc.pdf (pag. 3)"
    """
    metadata = doc.get("metadata", {})
    
    # Tentar usar document_title primeiro (mais legivel)
    title = metadata.get("document_title", "")
    source = metadata.get("source", "Desconhecido")
    page = metadata.get("page", None)
    
    # Usar titulo se disponivel, senao filename
    display_name = title if title else source

    if page is not None:
        return f"{display_name} (pag. {page})"
    return display_name


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Trunca texto para exibicao.

    Args:
        text: Texto completo
        max_length: Comprimento maximo

    Returns:
        str: Texto truncado com reticencias se necessario
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def init_session_state() -> None:
    """
    Inicializa o session state do Streamlit com valores padrao.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "config" not in st.session_state:
        st.session_state.config = get_default_config()

    if "workflow_initialized" not in st.session_state:
        st.session_state.workflow_initialized = False


def clear_chat_history() -> None:
    """
    Limpa historico de chat do session state.
    """
    st.session_state.messages = []
    st.success("[OK] Historico de conversacao limpo!")


def save_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Salva mensagem no historico de chat.

    Args:
        role: 'user' ou 'assistant'
        content: Conteudo da mensagem
        metadata: Metadados adicionais (para assistant)
    """
    message = {
        "role": role,
        "content": content,
    }

    if metadata:
        message["metadata"] = metadata

    st.session_state.messages.append(message)
