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

from src.graph.consulting_states import ConsultingPhase
from src.graph.states import BSCState
from src.memory.exceptions import Mem0ClientError, ProfileNotFoundError
from src.memory.factory import MemoryFactory
from src.memory.schemas import ClientProfile, CompanyInfo, EngagementState, StrategicContext


def map_phase_from_engagement(engagement_phase: str) -> ConsultingPhase:
    """Mapeia fase do EngagementState (Literal string) para ConsultingPhase (Enum).

    EngagementState.current_phase usa Literal strings ("ONBOARDING", "DISCOVERY", etc),
    enquanto ConsultingPhase usa Enum. Esta função faz o mapeamento bidirecional seguro.

    Args:
        engagement_phase: String da fase do engagement ("ONBOARDING", "DISCOVERY", etc)

    Returns:
        ConsultingPhase: Enum correspondente

    Examples:
        >>> map_phase_from_engagement("ONBOARDING")
        ConsultingPhase.ONBOARDING

        >>> map_phase_from_engagement("DESIGN")
        ConsultingPhase.SOLUTION_DESIGN

        >>> map_phase_from_engagement("COMPLETED")
        ConsultingPhase.IDLE

        >>> map_phase_from_engagement("INVALID")
        ConsultingPhase.ONBOARDING  # Default seguro
    """
    mapping = {
        "ONBOARDING": ConsultingPhase.ONBOARDING,
        "DISCOVERY": ConsultingPhase.DISCOVERY,
        "DESIGN": ConsultingPhase.SOLUTION_DESIGN,  # Mapeamento: DESIGN -> SOLUTION_DESIGN
        "APPROVAL_PENDING": ConsultingPhase.APPROVAL_PENDING,
        "IMPLEMENTATION": ConsultingPhase.IMPLEMENTATION,
        "COMPLETED": ConsultingPhase.IDLE,  # Engajamento finalizado volta ao IDLE
    }

    # Default seguro: ONBOARDING (cliente sempre precisa onboarding)
    return mapping.get(engagement_phase, ConsultingPhase.ONBOARDING)


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
    # Import no topo da função (usado em múltiplos returns)
    from src.graph.consulting_states import ConsultingPhase

    start_time = time.time()

    try:
        # Skip se não há user_id (query anônima)
        # SPRINT 1 HOTFIX: Temporariamente desabilitar onboarding consultivo para queries BSC
        # Permite que testes E2E antigos passem (assumem RAG tradicional direto)
        # TODO FASE 6: Reimplementar detecção inteligente onboarding vs RAG tradicional
        if not state.user_id:
            logger.info(
                "[INFO] [load_client_memory] Query sem user_id -> "
                "current_phase=DISCOVERY (RAG tradicional, sem onboarding consultivo)"
            )
            return {"client_profile": None, "current_phase": ConsultingPhase.DISCOVERY}

        logger.info(f"[TIMING] [load_client_memory] INICIADO | user_id: {state.user_id}")

        # CRÍTICO: Se client_profile JÁ EXISTE no checkpoint, NÃO carregar do Mem0!
        # Evita ProfileNotFoundError quando profile foi salvo mas ainda não disponível em Mem0
        if state.client_profile is not None:
            elapsed_time = time.time() - start_time
            logger.info(
                "[LOAD] ===== CLIENT_PROFILE JÁ EXISTE NO CHECKPOINT! ===== | "
                "user_id='%s' | company='%s' | Skipping Mem0 load | Tempo: %.3fs",
                state.user_id,
                getattr(state.client_profile.company, "name", "N/A"),
                elapsed_time,
            )
            # Retornar dict vazio preserva tudo que já está no checkpoint
            return {}

        # Obter memory provider (Mem0)
        try:
            provider = MemoryFactory.get_provider("mem0")
        except Exception as e:
            logger.error(f"[ERRO] [load_client_memory] Falha ao inicializar Mem0: {e}")
            # Continua sem memória (modo degradado)
            return {"client_profile": None}

        # Tentar carregar profile existente
        try:
            logger.info("[LOAD] Tentando carregar profile do Mem0 | user_id='%s'", state.user_id)
            profile = provider.load_profile(state.user_id)

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [load_client_memory] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"Profile carregado: {profile.company.name} | "
                f"Fase Mem0: {profile.engagement.current_phase}"
            )

            # FASE 2.6: Sincronizar phase do profile com BSCState.current_phase
            # Usa helper function para mapear string Literal -> Enum seguro
            # Se profile tem fase definida, usa ela (cliente returning)
            # Se não, usa default seguro ONBOARDING (garantido por map_phase_from_engagement)
            consulting_phase = map_phase_from_engagement(profile.engagement.current_phase)
            logger.info(
                f"[INFO] [load_client_memory] Fase consultiva mapeada: "
                f"'{profile.engagement.current_phase}' -> {consulting_phase.value}"
            )

            return {"client_profile": profile, "current_phase": consulting_phase}

        except ProfileNotFoundError:
            # Cliente novo - não é erro, é esperado
            # FASE 2.6: Definir current_phase = ONBOARDING para iniciar onboarding
            elapsed_time = time.time() - start_time
            logger.warning(
                "[LOAD] ProfileNotFoundError no Mem0 | user_id='%s' | Tempo decorrido: %.3fs",
                state.user_id,
                elapsed_time,
            )

            # CRÍTICO: Preservar current_phase se já existe no state (ex: transição ONBOARDING->DISCOVERY)
            # Só setar ONBOARDING se current_phase ainda não está definido
            existing_phase = state.current_phase
            logger.info(
                "[LOAD] Verificando existing_phase no state: %s (None=%s, IDLE=%s)",
                existing_phase,
                existing_phase is None,
                existing_phase == ConsultingPhase.IDLE if existing_phase else False,
            )
            if existing_phase is None or existing_phase == ConsultingPhase.IDLE:
                # Cliente realmente novo ou idle -> iniciar onboarding
                logger.info(
                    f"[INFO] [load_client_memory] Cliente novo (sem profile) | "
                    f"user_id: {state.user_id} | "
                    f"Iniciando current_phase = ONBOARDING | "
                    f"Tempo: {elapsed_time:.3f}s"
                )
                return {"client_profile": None, "current_phase": ConsultingPhase.ONBOARDING}
            # Cliente em processo (ex: DISCOVERY) -> preservar phase existente
            logger.info(
                f"[INFO] [load_client_memory] Cliente novo mas current_phase já existe (%s) | "
                f"user_id: {state.user_id} | "
                f"Preservando phase | "
                f"Tempo: {elapsed_time:.3f}s",
                existing_phase,
            )
            return {
                "client_profile": None,
                # NÃO retornar current_phase (deixa LangGraph usar o existente do checkpoint)
            }

    except Mem0ClientError as e:
        # Erro de API Mem0 - log mas não falha workflow
        elapsed_time = time.time() - start_time
        logger.error(
            f"[ERRO] [load_client_memory] Falha Mem0 API: {e} | " f"Tempo: {elapsed_time:.3f}s"
        )
        # Fallback seguro: entra em ONBOARDING para iniciar fluxo consultivo
        return {"client_profile": None, "current_phase": ConsultingPhase.ONBOARDING}

    except Exception as e:
        # Qualquer outro erro - log mas não falha workflow
        elapsed_time = time.time() - start_time
        logger.error(
            f"[ERRO] [load_client_memory] Erro inesperado: {e} | " f"Tempo: {elapsed_time:.3f}s"
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
            logger.info("[INFO] [save_client_memory] Skip - sem client_profile para salvar")
            return {}

        # Gera user_id se não existir
        user_id = state.user_id or str(uuid4())

        phase_for_log = (
            state.current_phase.value if getattr(state, "current_phase", None) else "UNKNOWN"
        )
        logger.info(
            f"[TIMING] [save_client_memory] INICIADO | "
            f"user_id: {user_id} | "
            f"Empresa: {state.client_profile.company.name} | "
            f"Fase Consultiva: {phase_for_log}"
        )

        # Atualizar timestamps e fase consultiva
        profile = state.client_profile
        profile.engagement.last_interaction = datetime.now(timezone.utc)

        # FASE 2.6: Sincronizar fase do BSCState com ClientProfile (se disponível)
        if getattr(state, "current_phase", None):
            phase_value: str = state.current_phase.value
            # Validar se fase é válida no Literal antes de atribuir
            valid_phases = (
                "ONBOARDING",
                "DISCOVERY",
                "DESIGN",
                "APPROVAL_PENDING",
                "IMPLEMENTATION",
                "COMPLETED",
            )
            if phase_value.upper() in valid_phases:
                profile.engagement.current_phase = phase_value.upper()  # type: ignore
                logger.debug(
                    f"[INFO] [save_client_memory] Fase sincronizada no profile: " f"{phase_value}"
                )
            else:
                logger.warning(
                    f"[WARN] [save_client_memory] Fase inválida: {phase_value}. "
                    f"Mantendo fase atual do profile: {profile.engagement.current_phase}"
                )

        # FASE 2.7: Sincronizar diagnostic do BSCState com ClientProfile
        # Se state.diagnostic existe (preenchido pelo discovery_handler),
        # persistir no ClientProfile.complete_diagnostic
        if state.diagnostic:
            profile.complete_diagnostic = state.diagnostic
            logger.info(
                f"[INFO] [save_client_memory] Diagnostic sincronizado | "
                f"Perspectivas: 4 | "
                f"Recomendações: {len(state.diagnostic.get('recommendations', []))}"
            )

        # FASE 2.8: Sincronizar approval_status e approval_feedback
        # Persistir decisão de aprovação no metadata do ClientProfile (schema existente)
        if state.approval_status or state.approval_feedback:
            if not isinstance(profile.metadata, dict):
                profile.metadata = {}

            if state.approval_status:
                profile.metadata["approval_status"] = state.approval_status.value
                logger.info(
                    f"[INFO] [save_client_memory] Approval status sincronizado: "
                    f"{state.approval_status.value}"
                )

            if state.approval_feedback:
                profile.metadata["approval_feedback"] = state.approval_feedback
                logger.debug(
                    f"[INFO] [save_client_memory] Approval feedback sincronizado: "
                    f"{state.approval_feedback[:50]}..."
                )

        # Obter memory provider (Mem0)
        try:
            provider = MemoryFactory.get_provider("mem0")
        except Exception as e:
            logger.error(f"[ERRO] [save_client_memory] Falha ao inicializar Mem0: {e}")
            # Continua sem salvar (perda aceitável)
            return {"user_id": user_id}

        # Salvar profile com TIMEOUT (30s) para evitar travar processo inteiro
        try:
            from concurrent.futures import ThreadPoolExecutor
            from concurrent.futures import TimeoutError as FuturesTimeoutError

            logger.info("[SAVE] Salvando profile no Mem0 com timeout de 30s...")

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(provider.save_profile, profile)
                try:
                    # Aguardar com timeout de 30s
                    future.result(timeout=30.0)

                    # [TIMER] CRÍTICO: Aguardar API Mem0 processar completamente (eventual consistency)
                    # O save_profile já tem sleep(1) interno entre delete e add,
                    # mas precisamos de OUTRO sleep após o add para garantir que
                    # a memória está disponível para leitura subsequente
                    time.sleep(1)
                    logger.debug(
                        "[TIMING] [save_client_memory] Sleep 1s após save_profile (garantir disponibilidade)"
                    )

                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"[TIMING] [save_client_memory] CONCLUÍDO em {elapsed_time:.3f}s | "
                        f"Profile salvo: {profile.company.name} | "
                        f"Fase: {profile.engagement.current_phase}"
                    )

                    return {"user_id": user_id}

                except FuturesTimeoutError:
                    logger.error(
                        "[TIMEOUT] save_client_memory excedeu 30s! Profile NÃO foi salvo no Mem0. "
                        "Continuando workflow (client_profile persiste no checkpoint LangGraph)."
                    )
                    # Continuar sem salvar (checkpoint LangGraph tem o profile)
                    return {"user_id": user_id}

        except Mem0ClientError as e:
            # Erro de API - log mas não falha workflow
            elapsed_time = time.time() - start_time
            logger.error(
                f"[ERRO] [save_client_memory] Falha Mem0 API: {e} | " f"Tempo: {elapsed_time:.3f}s"
            )
            return {"user_id": user_id}

    except Exception as e:
        # Qualquer outro erro - log mas não falha workflow
        elapsed_time = time.time() - start_time
        logger.error(
            f"[ERRO] [save_client_memory] Erro inesperado: {e} | " f"Tempo: {elapsed_time:.3f}s"
        )
        return {"user_id": state.user_id} if state.user_id else {}


# ============================================================================
# HELPER FUNCTIONS (Utilitários para testes)
# ============================================================================


def create_placeholder_profile(user_id: str, company_name: str = "Cliente") -> ClientProfile:
    """
    Cria ClientProfile placeholder com valores padrão.

    Função utilitária para testes rapidamente criarem profiles sem
    precisar preencher todos os campos manualmente.

    Args:
        user_id: ID único do cliente
        company_name: Nome da empresa (default: "Cliente")

    Returns:
        ClientProfile com campos básicos preenchidos e demais em default

    Example:
        >>> profile = create_placeholder_profile("test_123", "Acme Corp")
        >>> assert profile.client_id == "test_123"
        >>> assert profile.company.name == "Acme Corp"
        >>> assert profile.engagement.current_phase == "ONBOARDING"
    """
    return ClientProfile(
        client_id=user_id,
        company=CompanyInfo(
            name=company_name, sector="A definir", size="média", industry=None, founded_year=None
        ),
        context=StrategicContext(),  # Valores default
        engagement=EngagementState(
            current_phase="ONBOARDING", last_interaction=datetime.now(timezone.utc)
        ),
        diagnostics=None,
    )
