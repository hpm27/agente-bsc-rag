"""Memory nodes para LangGraph workflow.

Este módulo implementa os nodes de memória persistente que integram
o Mem0 Platform no workflow BSC, permitindo carregar e salvar perfis
de clientes (ClientProfile) entre sessões.

Nodes implementados:
- load_client_memory: Carrega perfil existente do Mem0
- save_client_memory: Persiste atualizações do perfil no Mem0
"""

import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from loguru import logger

from src.graph.states import BSCState
from src.memory.exceptions import Mem0ClientError, ProfileNotFoundError
from src.memory.factory import MemoryFactory
from src.memory.schemas import ClientProfile, CompanyInfo, EngagementState


def load_client_memory(state: BSCState) -> dict[str, Any]:
    """Node 1: Carrega ClientProfile do Mem0 Platform.

    Recupera o perfil persistente do cliente baseado no user_id.
    Se o perfil não existir (cliente novo), retorna None.
    Se user_id não for fornecido (query anônima), skip load.

    Este node NÃO deve falhar o workflow - todas exceções são capturadas
    e o workflow continua normalmente (modo degradado sem memória).

    Args:
        state: Estado atual do workflow (BSCState)

    Returns:
        Dict com client_profile atualizado (ou None)

    Examples:
        >>> # Cliente existente
        >>> state = BSCState(query="...", user_id="cliente_123")
        >>> result = load_client_memory(state)
        >>> result["client_profile"]  # ClientProfile carregado

        >>> # Cliente novo
        >>> state = BSCState(query="...", user_id="cliente_novo")
        >>> result = load_client_memory(state)
        >>> result["client_profile"]  # None (será criado depois)

        >>> # Query anônima
        >>> state = BSCState(query="...")
        >>> result = load_client_memory(state)
        >>> result["client_profile"]  # None (sem user_id)
    """
    start_time = time.time()

    try:
        # Skip se não há user_id (query anônima)
        if not state.user_id:
            logger.info(
                "[INFO] [load_client_memory] Skip - query anônima (sem user_id)"
            )
            return {"client_profile": None}

        logger.info(
            f"[TIMING] [load_client_memory] INICIADO | user_id: {state.user_id}"
        )

        # Obter memory provider (Mem0)
        try:
            provider = MemoryFactory.get_provider("mem0")
        except Exception as e:
            logger.error(
                f"[ERRO] [load_client_memory] Falha ao inicializar Mem0: {e}"
            )
            # Continua sem memória (modo degradado)
            return {"client_profile": None}

        # Tentar carregar profile existente
        try:
            profile = provider.load_profile(state.user_id)

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [load_client_memory] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"Profile carregado: {profile.company.name} | "
                f"Fase: {profile.engagement.current_phase}"
            )

            return {"client_profile": profile}

        except ProfileNotFoundError:
            # Cliente novo - não é erro, é esperado
            elapsed_time = time.time() - start_time
            logger.info(
                f"[INFO] [load_client_memory] Cliente novo (sem profile) | "
                f"user_id: {state.user_id} | "
                f"Tempo: {elapsed_time:.3f}s"
            )
            return {"client_profile": None}

    except Mem0ClientError as e:
        # Erro de API Mem0 - log mas não falha workflow
        elapsed_time = time.time() - start_time
        logger.error(
            f"[ERRO] [load_client_memory] Falha Mem0 API: {e} | "
            f"Tempo: {elapsed_time:.3f}s"
        )
        return {"client_profile": None}

    except Exception as e:
        # Qualquer outro erro - log mas não falha workflow
        elapsed_time = time.time() - start_time
        logger.error(
            f"[ERRO] [load_client_memory] Erro inesperado: {e} | "
            f"Tempo: {elapsed_time:.3f}s"
        )
        return {"client_profile": None}


def save_client_memory(state: BSCState) -> dict[str, Any]:
    """Node 2: Salva ClientProfile no Mem0 Platform.

    Persiste o perfil do cliente (criação ou atualização) no Mem0.
    Se não houver client_profile no state, skip (nada a salvar).
    Se não houver user_id, gera um novo UUID automaticamente.

    Atualiza automaticamente:
    - engagement.last_interaction (timestamp atual)

    Este node NÃO deve falhar o workflow - todas exceções são capturadas
    e o workflow continua (perda de memória é aceitável neste caso).

    Args:
        state: Estado atual do workflow (BSCState)

    Returns:
        Dict com user_id atualizado (se foi gerado novo)

    Examples:
        >>> # Salvar profile existente
        >>> state = BSCState(
        ...     query="...",
        ...     user_id="cliente_123",
        ...     client_profile=profile
        ... )
        >>> result = save_client_memory(state)
        >>> # Profile atualizado no Mem0

        >>> # Criar novo profile (gera UUID)
        >>> state = BSCState(query="...", client_profile=new_profile)
        >>> result = save_client_memory(state)
        >>> result["user_id"]  # Novo UUID gerado
    """
    start_time = time.time()

    try:
        # Skip se não há profile para salvar
        if not state.client_profile:
            logger.info(
                "[INFO] [save_client_memory] Skip - sem client_profile para salvar"
            )
            return {}

        # Gera user_id se não existir
        user_id = state.user_id or str(uuid4())

        logger.info(
            f"[TIMING] [save_client_memory] INICIADO | "
            f"user_id: {user_id} | "
            f"Empresa: {state.client_profile.company.name}"
        )

        # Atualizar timestamps
        profile = state.client_profile
        profile.engagement.last_interaction = datetime.now(timezone.utc)

        # Adicionar query ao histórico (últimas 10 queries)
        if not hasattr(profile, "_query_history"):
            profile._query_history = []
        profile._query_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": state.query[:100]  # Limita tamanho
        })
        profile._query_history = profile._query_history[-10:]  # Mantém só últimas 10

        # Obter memory provider (Mem0)
        try:
            provider = MemoryFactory.get_provider("mem0")
        except Exception as e:
            logger.error(
                f"[ERRO] [save_client_memory] Falha ao inicializar Mem0: {e}"
            )
            # Continua sem salvar (perda aceitável)
            return {"user_id": user_id}

        # Salvar profile
        try:
            provider.save_profile(profile)

            # ⏱️ CRÍTICO: Aguardar API Mem0 processar completamente (eventual consistency)
            # O save_profile já tem sleep(1) interno entre delete e add,
            # mas precisamos de OUTRO sleep após o add para garantir que
            # a memória está disponível para leitura subsequente
            time.sleep(1)
            logger.debug("[TIMING] [save_client_memory] Sleep 1s após save_profile (garantir disponibilidade)")

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [save_client_memory] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"Profile salvo: {profile.company.name} | "
                f"Fase: {profile.engagement.current_phase}"
            )

            return {"user_id": user_id}

        except Mem0ClientError as e:
            # Erro de API - log mas não falha workflow
            elapsed_time = time.time() - start_time
            logger.error(
                f"[ERRO] [save_client_memory] Falha Mem0 API: {e} | "
                f"Tempo: {elapsed_time:.3f}s"
            )
            return {"user_id": user_id}

    except Exception as e:
        # Qualquer outro erro - log mas não falha workflow
        elapsed_time = time.time() - start_time
        logger.error(
            f"[ERRO] [save_client_memory] Erro inesperado: {e} | "
            f"Tempo: {elapsed_time:.3f}s"
        )
        return {"user_id": state.user_id} if state.user_id else {}


def create_placeholder_profile(user_id: str, company_name: str = "Cliente") -> ClientProfile:
    """Cria ClientProfile placeholder para novos clientes.

    NOTA: Esta é uma função utilitária temporária para FASE 1.7.
    Na FASE 2, o OnboardingAgent criará profiles completos via formulário.

    Args:
        user_id: ID único do cliente
        company_name: Nome da empresa (default: "Cliente")

    Returns:
        ClientProfile: Profile básico placeholder

    Examples:
        >>> profile = create_placeholder_profile("cliente_123", "Acme Corp")
        >>> profile.company.name
        'Acme Corp'
        >>> profile.engagement.current_phase
        'ONBOARDING'
    """
    return ClientProfile(
        client_id=user_id,
        company=CompanyInfo(
            name=company_name,
            sector="A definir",
            size="média"
        ),
        engagement=EngagementState(
            current_phase="ONBOARDING",
            created_at=datetime.now(timezone.utc),
            last_interaction=datetime.now(timezone.utc)
        )
    )

