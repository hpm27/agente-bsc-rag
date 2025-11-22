"""Helper functions para carregar dados do SQLite + Mem0 na UI Streamlit.

SPRINT 4: Dual Persistence Strategy (SQLite primary, Mem0 fallback)

Funcoes:
- load_strategy_map(user_id) -> Carrega objetivos estrategicos BSC do SQLite (instant)
- load_action_plan(user_id) -> Carrega plano de acao BSC do SQLite (instant)
- list_all_clients() -> Lista todos clientes salvos (SQLite + Mem0)

IMPORTANTE:
- Zero emojis (memoria [[9776249]], Windows cp1252)
- SQLite é fonte primária (zero latency, confiável)
- Mem0 é fallback (eventual consistency até 10 min)
"""

import logging

from src.database import get_db_session
from src.database.repository import BSCRepository
from src.memory.schemas import ActionItem, ActionPlan, StrategicObjective, StrategyMap
from src.memory.exceptions import ProfileNotFoundError

logger = logging.getLogger(__name__)


def load_strategy_map(user_id: str) -> tuple[list[StrategicObjective] | None, str | None]:
    """Carrega Strategy Map (objetivos estrategicos) do SQLite (primary) ou Mem0 (fallback).

    DUAL PERSISTENCE STRATEGY (SPRINT 4):
    1. Tenta carregar de SQLite primeiro (instant, confiável)
    2. Se falhar, tenta Mem0 como fallback (eventual consistency até 10 min)

    Args:
        user_id: ID do cliente

    Returns:
        Tupla (objectives, error_message):
        - objectives: Lista de StrategicObjective se sucesso, None se erro
        - error_message: Mensagem de erro se falha, None se sucesso

    Example:
        >>> objectives, error = load_strategy_map("cliente_123")
        >>> if error:
        ...     st.error(error)
        ... else:
        ...     st.write(f"[OK] {len(objectives)} objetivos carregados")
    """
    # ========== STEP 1: Tentar SQLite primeiro (PRIMARY) ==========
    try:
        repo = BSCRepository()
        with get_db_session() as db:
            # Buscar Strategy Map mais recente do user
            strategy_map_row = repo.strategy_maps.get_by_user_id(db, user_id)

            if strategy_map_row:
                # Converter SQLAlchemy model -> StrategyMap Pydantic
                # NOTA: SQLite armazena objectives como JSON flat list, não estrutura 4 perspectivas
                objectives_data = strategy_map_row.objectives  # JSON já parseado pelo SQLAlchemy
                objectives = [StrategicObjective(**obj) for obj in objectives_data]

                logger.info(
                    f"[OK] [SQLite PRIMARY] Strategy Map carregado | user_id: {user_id[:8]}... | Objectives: {len(objectives)}"
                )
                return objectives, None

            # SQLite não tem dados, tentar Mem0 fallback
            logger.warning(
                f"[WARN] [SQLite] Strategy Map não encontrado para user_id: {user_id[:8]}..."
            )

    except Exception as e:
        logger.warning(
            f"[WARN] [SQLite] Falha ao carregar Strategy Map: {e}. Tentando Mem0 fallback..."
        )

    # ========== STEP 2: Tentar Mem0 como fallback (SECONDARY) ==========
    try:
        from src.memory.mem0_client import Mem0ClientWrapper

        client = Mem0ClientWrapper()

        # Buscar profile completo (inclui strategy_map no metadata)
        try:
            profile = client.load_profile(user_id)
        except ProfileNotFoundError:
            # CORREÇÃO SESSAO 40: Capturar exceção específica
            return None, "[INFO] Perfil nao encontrado. Execute workflow ONBOARDING primeiro"

        # Extrair strategy_map do metadata
        strategy_map_dict = profile.metadata.get("strategy_map")

        if not strategy_map_dict:
            return (
                None,
                "[INFO] Strategy Map ainda nao foi gerado (execute workflow SOLUTION_DESIGN)",
            )

        # Converter dict -> StrategyMap Pydantic -> extrair objectives
        strategy_map = StrategyMap(**strategy_map_dict)

        # CORREÇÃO BUG #6 SESSAO 39: StrategyMap NÃO tem .objectives (estrutura: 4 perspectivas)
        # Fazer flatten das 4 perspectivas para extrair todos objectives
        objectives = []
        objectives.extend(strategy_map.financial.objectives)
        objectives.extend(strategy_map.customer.objectives)
        objectives.extend(strategy_map.process.objectives)
        objectives.extend(strategy_map.learning.objectives)

        logger.info(
            f"[OK] [Mem0 FALLBACK] Strategy Map carregado | user_id: {user_id[:8]}... | Objectives: {len(objectives)}"
        )

        return objectives, None

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar Strategy Map (SQLite + Mem0): {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg


def load_action_plan(user_id: str) -> tuple[list[ActionItem] | None, str | None]:
    """Carrega Action Plan (acoes de implementacao) do SQLite (primary) ou Mem0 (fallback).

    DUAL PERSISTENCE STRATEGY (SPRINT 4):
    1. Tenta carregar de SQLite primeiro (instant, confiável)
    2. Se falhar, tenta Mem0 como fallback (eventual consistency até 10 min)

    Args:
        user_id: ID do cliente

    Returns:
        Tupla (action_items, error_message):
        - action_items: Lista de ActionItem se sucesso, None se erro
        - error_message: Mensagem de erro se falha, None se sucesso

    Example:
        >>> actions, error = load_action_plan("cliente_123")
        >>> if error:
        ...     st.error(error)
        ... else:
        ...     st.write(f"[OK] {len(actions)} acoes carregadas")
    """
    # ========== STEP 1: Tentar SQLite primeiro (PRIMARY) ==========
    try:
        repo = BSCRepository()
        with get_db_session() as db:
            # Buscar Action Plan mais recente do user
            action_plan_row = repo.action_plans.get_by_user_id(db, user_id)

            if action_plan_row:
                # Converter SQLAlchemy model -> lista de ActionItem
                actions_data = action_plan_row.actions  # JSON já parseado pelo SQLAlchemy
                action_items = [ActionItem(**action) for action in actions_data]

                logger.info(
                    f"[OK] [SQLite PRIMARY] Action Plan carregado | user_id: {user_id[:8]}... | Actions: {len(action_items)}"
                )
                return action_items, None

            # SQLite não tem dados, tentar Mem0 fallback
            logger.warning(
                f"[WARN] [SQLite] Action Plan não encontrado para user_id: {user_id[:8]}..."
            )

    except Exception as e:
        logger.warning(
            f"[WARN] [SQLite] Falha ao carregar Action Plan: {e}. Tentando Mem0 fallback..."
        )

    # ========== STEP 2: Tentar Mem0 como fallback (SECONDARY) ==========
    try:
        from src.memory.mem0_client import Mem0ClientWrapper

        client = Mem0ClientWrapper()

        # Buscar profile completo (inclui action_plan no metadata)
        try:
            profile = client.load_profile(user_id)
        except ProfileNotFoundError:
            # CORREÇÃO SESSAO 40: Capturar exceção específica
            return None, "[INFO] Perfil nao encontrado. Execute workflow ONBOARDING primeiro"

        # Extrair action_plan do metadata
        action_plan_dict = profile.metadata.get("action_plan")

        if not action_plan_dict:
            return None, "[INFO] Action Plan ainda nao foi gerado (execute workflow IMPLEMENTATION)"

        # Converter dict -> ActionPlan Pydantic -> extrair action_items
        action_plan = ActionPlan(**action_plan_dict)
        action_items = action_plan.action_items

        logger.info(
            f"[OK] [Mem0 FALLBACK] Action Plan carregado | user_id: {user_id[:8]}... | Actions: {len(action_items)}"
        )

        return action_items, None

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar Action Plan (SQLite + Mem0): {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg


def list_all_clients() -> tuple[list[dict] | None, str | None]:
    """Lista todos clientes salvos no Mem0 (para selecao na UI).

    Usa Mem0ClientWrapper.list_all_profiles() com retry/fallback para buscar
    ClientProfiles completos. Mais robusto que busca direta na API.

    Retorna lista de dicts com informacoes basicas de cada cliente:
    - user_id: ID do cliente
    - company_name: Nome da empresa
    - sector: Setor
    - current_phase: Fase consultiva atual

    Returns:
        Tupla (clients, error_message):
        - clients: Lista de dicts com info dos clientes, None se erro
        - error_message: Mensagem de erro se falha, None se sucesso

    Example:
        >>> clients, error = list_all_clients()
        >>> if error:
        ...     st.error(error)
        ... else:
        ...     for client in clients:
        ...         st.write(f"{client['company_name']} - {client['sector']}")
    """
    try:
        # Usar Mem0ClientWrapper do projeto (tem retry logic + fallbacks)
        from src.memory.mem0_client import Mem0ClientWrapper

        client = Mem0ClientWrapper()

        # Buscar TODOS os profiles (usa retry + 3 métodos fallback)
        profiles = client.list_all_profiles(limit=100, include_archived=False)

        if not profiles:
            return None, "[INFO] Nenhum cliente encontrado. Execute workflow ONBOARDING primeiro"

        # Converter ClientProfile -> dict simplificado para UI
        clients = []
        for profile in profiles:
            clients.append(
                {
                    "user_id": profile.user_id,
                    "company_name": profile.company.name if profile.company else "Sem nome",
                    "sector": profile.company.sector if profile.company else "Indefinido",
                    "current_phase": (
                        profile.engagement.current_phase if profile.engagement else "ONBOARDING"
                    ),
                }
            )

        logger.info(f"[OK] {len(clients)} clientes carregados via list_all_profiles()")
        return clients, None

    except Exception as e:
        error_msg = f"[ERRO] Falha ao listar clientes do Mem0: {e}"
        logger.error(error_msg, exc_info=True)

        # Graceful degradation: retornar lista vazia ao invés de erro
        logger.info("[INFO] Retornando lista vazia (graceful degradation)")
        return [], None
