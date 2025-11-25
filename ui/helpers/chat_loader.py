"""Helper para carregar histórico de chat do LangGraph checkpoint.

CORREÇÃO SESSAO 43 (2025-11-24): Chat não persistia após reload da página.

SOLUÇÃO: Carregar chat_history do LangGraph checkpoint (thread_id=user_id).
O LangGraph já persiste todo o state automaticamente, incluindo metadata.chat_history.

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def load_chat_history(user_id: str) -> List[Dict[str, str]]:
    """Carrega histórico de chat do LangGraph checkpoint.

    Args:
        user_id: ID do usuário (usado como thread_id do checkpoint)

    Returns:
        Lista de mensagens [{role: "user"|"assistant", content: "..."}]
        Retorna lista vazia se não houver histórico ou erro

    Example:
        >>> messages = load_chat_history("usuario_123")
        >>> print(f"Carregadas {len(messages)} mensagens")
    """
    try:
        from src.graph.workflow import get_workflow

        workflow = get_workflow()
        config = {"configurable": {"thread_id": user_id}}

        # SESSAO 44 (2025-11-24): Usar graph COM checkpointer para get_state
        graph_with_cp = workflow.get_graph_with_checkpointer()

        # Tentar obter state existente do checkpoint
        checkpoint_state = graph_with_cp.get_state(config)

        if not checkpoint_state or not checkpoint_state.values:
            logger.info(f"[INFO] Nenhum checkpoint encontrado para user_id: {user_id[:8]}...")
            return []

        # Carregar chat_history do metadata
        metadata = checkpoint_state.values.get("metadata", {})
        chat_history = metadata.get("chat_history", [])

        if chat_history:
            logger.info(
                f"[OK] Chat history carregado do checkpoint | user_id: {user_id[:8]}... | "
                f"Messages: {len(chat_history)}"
            )
        else:
            logger.info(
                f"[INFO] Checkpoint existe mas chat_history vazio | user_id: {user_id[:8]}..."
            )

        return chat_history

    except Exception as e:
        logger.warning(
            f"[WARN] Falha ao carregar chat history do checkpoint: {e}. Retornando lista vazia."
        )
        return []


def save_chat_to_checkpoint(user_id: str, messages: List[Dict[str, str]]) -> bool:
    """Salva histórico de chat no LangGraph checkpoint.

    IMPORTANTE: Esta função atualiza APENAS o metadata.chat_history do checkpoint,
    preservando todo o resto do state (client_profile, diagnostic, etc.).

    Args:
        user_id: ID do usuário (thread_id do checkpoint)
        messages: Lista de mensagens a salvar

    Returns:
        True se sucesso, False se erro

    Example:
        >>> messages = [{"role": "user", "content": "Olá"}, {"role": "assistant", "content": "Oi!"}]
        >>> success = save_chat_to_checkpoint("usuario_123", messages)
    """
    try:
        from src.graph.workflow import get_workflow

        workflow = get_workflow()
        config = {"configurable": {"thread_id": user_id}}

        # SESSAO 44 (2025-11-24): Usar graph COM checkpointer para get_state/update_state
        # workflow.graph não tem checkpointer (compilado sem para permitir recompilação async)
        # get_graph_with_checkpointer() retorna graph com SqliteSaver (sync)
        graph_with_cp = workflow.get_graph_with_checkpointer()

        # Obter state atual do checkpoint
        checkpoint_state = graph_with_cp.get_state(config)

        if not checkpoint_state or not checkpoint_state.values:
            logger.warning(
                f"[WARN] Nenhum checkpoint para atualizar | user_id: {user_id[:8]}... | "
                f"Impossível salvar chat sem state inicial"
            )
            return False

        # Atualizar apenas metadata.chat_history (preserva resto do state)
        existing_metadata = checkpoint_state.values.get("metadata", {})
        updated_metadata = {**existing_metadata, "chat_history": messages}

        # Update do checkpoint (merge com state existente)
        graph_with_cp.update_state(
            config, values={"metadata": updated_metadata}, as_node="save_client_memory"
        )

        logger.info(
            f"[OK] Chat history salvo no checkpoint | user_id: {user_id[:8]}... | "
            f"Messages: {len(messages)}"
        )
        return True

    except Exception as e:
        logger.error(f"[ERRO] Falha ao salvar chat no checkpoint: {e}", exc_info=True)
        return False
