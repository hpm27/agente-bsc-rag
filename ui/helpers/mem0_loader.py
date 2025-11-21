"""Helper functions para carregar dados do Mem0 na UI Streamlit.

SPRINT 4: Integracao Mem0 + Streamlit para visualizacao de Strategy Map e Action Plan.

Funcoes:
- load_strategy_map(user_id) -> Carrega objetivos estrategicos BSC do Mem0
- load_action_plan(user_id) -> Carrega plano de acao BSC do Mem0
- list_all_clients() -> Lista todos clientes salvos (para selecao na UI)

IMPORTANTE: Zero emojis (memoria [[9776249]], Windows cp1252).
"""

import logging

from src.memory.schemas import ActionItem, ActionPlan, StrategicObjective, StrategyMap

logger = logging.getLogger(__name__)


def load_strategy_map(user_id: str) -> tuple[list[StrategicObjective] | None, str | None]:
    """Carrega Strategy Map (objetivos estrategicos) do Mem0 para user_id.

    Usa Mem0ClientWrapper.load_profile() para buscar ClientProfile completo
    e extrair strategy_map do metadata. Mais robusto que busca direta.

    Args:
        user_id: ID do cliente no Mem0

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
    try:
        # Usar Mem0ClientWrapper do projeto (mais robusto que MemoryClient direto)
        from src.memory.mem0_client import Mem0ClientWrapper

        client = Mem0ClientWrapper()

        # Buscar profile completo (inclui strategy_map no metadata)
        profile = client.load_profile(user_id)

        if not profile:
            return None, "[INFO] Perfil nao encontrado. Execute workflow ONBOARDING primeiro"

        # Extrair strategy_map do metadata
        strategy_map_dict = profile.metadata.get("strategy_map")

        if not strategy_map_dict:
            return (
                None,
                "[INFO] Strategy Map ainda nao foi gerado (execute workflow SOLUTION_DESIGN)",
            )

        # Converter dict -> StrategyMap Pydantic -> extrair objectives
        try:
            strategy_map = StrategyMap(**strategy_map_dict)
            objectives = strategy_map.objectives

            logger.info(
                f"[OK] Strategy Map carregado | user_id: {user_id[:8]}... | Objectives: {len(objectives)}"
            )

            return objectives, None

        except Exception as e:
            error_msg = f"[ERRO] Falha ao converter strategy_map para Pydantic: {e}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar Strategy Map do Mem0: {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg


def load_action_plan(user_id: str) -> tuple[list[ActionItem] | None, str | None]:
    """Carrega Action Plan (acoes de implementacao) do Mem0 para user_id.

    Usa Mem0ClientWrapper.load_profile() para buscar ClientProfile completo
    e extrair action_plan do metadata. Mais robusto que busca direta.

    Args:
        user_id: ID do cliente no Mem0

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
    try:
        # Usar Mem0ClientWrapper do projeto (mais robusto que MemoryClient direto)
        from src.memory.mem0_client import Mem0ClientWrapper

        client = Mem0ClientWrapper()

        # Buscar profile completo (inclui action_plan no metadata)
        profile = client.load_profile(user_id)

        if not profile:
            return None, "[INFO] Perfil nao encontrado. Execute workflow ONBOARDING primeiro"

        # Extrair action_plan do metadata
        action_plan_dict = profile.metadata.get("action_plan")

        if not action_plan_dict:
            return None, "[INFO] Action Plan ainda nao foi gerado (execute workflow IMPLEMENTATION)"

        # Converter dict -> ActionPlan Pydantic -> extrair action_items
        try:
            action_plan = ActionPlan(**action_plan_dict)
            action_items = action_plan.action_items

            logger.info(
                f"[OK] Action Plan carregado | user_id: {user_id[:8]}... | Actions: {len(action_items)}"
            )

            return action_items, None

        except Exception as e:
            error_msg = f"[ERRO] Falha ao converter action_plan para Pydantic: {e}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar Action Plan do Mem0: {e}"
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
