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
from src.memory.schemas import (
    ActionItem,
    ActionPlan,
    CauseEffectAnalysis,
    CauseEffectConnection,
    KPIAlignmentReport,
    Milestone,
    MilestoneTrackerReport,
    StrategicObjective,
    StrategyMap,
)
from src.memory.exceptions import ProfileNotFoundError

logger = logging.getLogger(__name__)


def load_strategy_map(
    user_id: str,
) -> tuple[list[StrategicObjective] | None, list[CauseEffectConnection] | None, str | None]:
    """Carrega Strategy Map (objetivos + conexoes) do SQLite (primary) ou Mem0 (fallback).

    DUAL PERSISTENCE STRATEGY (SPRINT 4):
    1. Tenta carregar de SQLite primeiro (instant, confiável)
    2. Se falhar, tenta Mem0 como fallback (eventual consistency até 10 min)

    CORREÇÃO SESSAO 43 (2025-11-24): Agora retorna TAMBÉM as conexões causa-efeito
    para visualização completa do Strategy Map com setas direcionadas.

    Args:
        user_id: ID do cliente

    Returns:
        Tupla (objectives, connections, error_message):
        - objectives: Lista de StrategicObjective se sucesso, None se erro
        - connections: Lista de CauseEffectConnection se sucesso, None se erro
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
        with get_db_session() as db:
            repo = BSCRepository(db)  # CORREÇÃO SESSAO 40: passar db como argumento obrigatório
            # Buscar Strategy Map mais recente do user
            strategy_map_row = repo.strategy_maps.get_by_user_id(db, user_id)

            if strategy_map_row:
                # Converter SQLAlchemy model -> StrategyMap Pydantic
                # NOTA: SQLite armazena objectives como JSON flat list, não estrutura 4 perspectivas
                objectives_data = strategy_map_row.objectives  # JSON já parseado pelo SQLAlchemy
                objectives = [StrategicObjective(**obj) for obj in objectives_data]

                # CORREÇÃO SESSAO 43: Carregar TAMBÉM as conexões causa-efeito
                connections_data = strategy_map_row.connections  # JSON já parseado pelo SQLAlchemy
                connections = [CauseEffectConnection(**conn) for conn in connections_data]

                logger.info(
                    f"[OK] [SQLite PRIMARY] Strategy Map carregado | user_id: {user_id[:8]}... | "
                    f"Objectives: {len(objectives)} | Connections: {len(connections)}"
                )
                return objectives, connections, None

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
            return None, None, "[INFO] Perfil nao encontrado. Execute workflow ONBOARDING primeiro"

        # Extrair strategy_map do metadata
        strategy_map_dict = profile.metadata.get("strategy_map")

        if not strategy_map_dict:
            return (
                None,
                None,
                "[INFO] Strategy Map ainda nao foi gerado (execute workflow SOLUTION_DESIGN)",
            )

        # Converter dict -> StrategyMap Pydantic -> extrair objectives + connections
        strategy_map = StrategyMap(**strategy_map_dict)

        # CORREÇÃO BUG #6 SESSAO 39: StrategyMap NÃO tem .objectives (estrutura: 4 perspectivas)
        # Fazer flatten das 4 perspectivas para extrair todos objectives
        objectives = []
        objectives.extend(strategy_map.financial.objectives)
        objectives.extend(strategy_map.customer.objectives)
        objectives.extend(strategy_map.process.objectives)
        objectives.extend(strategy_map.learning.objectives)

        # CORREÇÃO SESSAO 43: Extrair TAMBÉM as conexões
        connections = strategy_map.cause_effect_connections

        logger.info(
            f"[OK] [Mem0 FALLBACK] Strategy Map carregado | user_id: {user_id[:8]}... | "
            f"Objectives: {len(objectives)} | Connections: {len(connections)}"
        )

        return objectives, connections, None

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar Strategy Map (SQLite + Mem0): {e}"
        logger.error(error_msg, exc_info=True)
        return None, None, error_msg


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
        with get_db_session() as db:
            repo = BSCRepository(db)  # CORREÇÃO SESSAO 40: passar db como argumento obrigatório
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


def load_all_clients_sqlite() -> tuple[list[dict] | None, str | None]:
    """Lista todos clientes salvos no SQLite (para selecao na UI).

    SESSAO 49 - SOLUCAO PERSISTENCIA: Carrega do SQLite local (instant, confiavel).
    Permite retomar consultas anteriores mostrando nome da empresa, setor e data.

    Retorna lista de dicts com informacoes amigaveis de cada cliente:
    - user_id: ID do cliente (UUID)
    - company_name: Nome da empresa
    - sector: Setor
    - created_at: Data de criacao formatada (DD/MM/AAAA)
    - display_name: String formatada para selectbox ("Empresa (Setor) - DD/MM/AAAA")

    Returns:
        Tupla (clients, error_message):
        - clients: Lista de dicts com info dos clientes, None se erro
        - error_message: Mensagem de erro se falha, None se sucesso

    Example:
        >>> clients, error = load_all_clients_sqlite()
        >>> if clients:
        ...     for client in clients:
        ...         st.write(client['display_name'])
    """
    try:
        from src.database.repository import ClientProfileRepository

        # CORREÇÃO SESSAO 49: Processar DENTRO do context manager
        # SQLAlchemy lazy loading requer sessão ativa para acessar atributos
        with get_db_session() as db:
            profiles = ClientProfileRepository.get_all(db, limit=100)

            if not profiles:
                return [], "[INFO] Nenhuma consulta anterior encontrada."

            # Converter ClientProfile ORM -> dict simplificado para UI
            # CRÍTICO: Fazer DENTRO do with, antes da sessão fechar
            clients = []
            for profile in profiles:
                # Formatar data no padrao brasileiro COM HORA para garantir unicidade
                # CORREÇÃO SESSAO 49: DD/MM/YYYY HH:MM evita colisão de chaves
                # quando múltiplos clientes criados no mesmo dia com mesmo nome/setor
                created_date = (
                    profile.created_at.strftime("%d/%m/%Y %H:%M")
                    if profile.created_at
                    else "Data desconhecida"
                )

                # Nome da empresa (fallback se vazio)
                company = profile.company_name or "[Sem nome]"

                # Setor (opcional)
                sector = profile.sector or ""

                # Display name formatado para selectbox (inclui hora para unicidade)
                if sector:
                    display = f"{company} ({sector}) - {created_date}"
                else:
                    display = f"{company} - {created_date}"

                clients.append(
                    {
                        "user_id": profile.user_id,
                        "company_name": company,
                        "sector": sector,
                        "created_at": created_date,
                        "display_name": display,
                    }
                )

        logger.info(f"[OK] {len(clients)} clientes carregados do SQLite")
        return clients, None

    except Exception as e:
        error_msg = f"[ERRO] Falha ao listar clientes do SQLite: {e}"
        logger.error(error_msg, exc_info=True)
        return [], error_msg


def load_validation_reports(
    user_id: str,
) -> tuple[KPIAlignmentReport | None, CauseEffectAnalysis | None, str | None]:
    """Carrega reports de validacao (KPI Alignment, Cause-Effect) do LangGraph state.

    SPRINT 3 - SESSAO 48: Novos reports de validacao do Strategy Map.
    Carrega do checkpoint LangGraph (state persistido automaticamente).

    Args:
        user_id: ID do cliente (thread_id do checkpoint)

    Returns:
        Tupla (kpi_alignment_report, cause_effect_analysis, error_message):
        - kpi_alignment_report: KPIAlignmentReport se disponivel, None caso contrario
        - cause_effect_analysis: CauseEffectAnalysis se disponivel, None caso contrario
        - error_message: Mensagem de erro se falha, None se sucesso

    Example:
        >>> kpi_report, ce_analysis, error = load_validation_reports("cliente_123")
        >>> if kpi_report:
        ...     st.write(f"KPI Score: {kpi_report.overall_score}")
    """
    try:
        from src.graph.workflow import get_workflow

        workflow = get_workflow()
        config = {"configurable": {"thread_id": user_id}}

        # Usar graph com checkpointer para acessar state
        graph_with_cp = workflow.get_graph_with_checkpointer()
        checkpoint_state = graph_with_cp.get_state(config)

        if not checkpoint_state or not checkpoint_state.values:
            logger.info(f"[INFO] Nenhum checkpoint encontrado para user_id: {user_id[:8]}...")
            return None, None, "[INFO] Nenhum state encontrado. Execute workflow primeiro."

        # Extrair reports do state
        state_values = checkpoint_state.values
        kpi_alignment_report = None
        cause_effect_analysis = None

        # KPI Alignment Report
        kpi_data = state_values.get("kpi_alignment_report")
        if kpi_data:
            if isinstance(kpi_data, KPIAlignmentReport):
                kpi_alignment_report = kpi_data
            elif isinstance(kpi_data, dict):
                kpi_alignment_report = KPIAlignmentReport(**kpi_data)
            logger.info(
                f"[OK] KPI Alignment Report carregado | score: {kpi_alignment_report.overall_score}"
            )

        # Cause-Effect Analysis
        ce_data = state_values.get("cause_effect_analysis")
        if ce_data:
            if isinstance(ce_data, CauseEffectAnalysis):
                cause_effect_analysis = ce_data
            elif isinstance(ce_data, dict):
                cause_effect_analysis = CauseEffectAnalysis(**ce_data)
            logger.info(
                f"[OK] Cause-Effect Analysis carregado | score: {cause_effect_analysis.completeness_score}"
            )

        if not kpi_alignment_report and not cause_effect_analysis:
            return (
                None,
                None,
                "[INFO] Reports de validacao nao disponiveis. Execute SOLUTION_DESIGN.",
            )

        return kpi_alignment_report, cause_effect_analysis, None

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar validation reports: {e}"
        logger.error(error_msg, exc_info=True)
        return None, None, error_msg


def load_milestone_report(
    user_id: str,
) -> tuple[MilestoneTrackerReport | None, str | None]:
    """Carrega MilestoneTrackerReport do LangGraph state.

    SPRINT 4 - SESSAO 49: Report de rastreamento de milestones do Action Plan.
    Carrega do checkpoint LangGraph (state persistido automaticamente).

    Args:
        user_id: ID do cliente (thread_id do checkpoint)

    Returns:
        Tupla (milestone_report, error_message):
        - milestone_report: MilestoneTrackerReport se disponivel, None caso contrario
        - error_message: Mensagem de erro se falha, None se sucesso

    Example:
        >>> report, error = load_milestone_report("cliente_123")
        >>> if report:
        ...     st.write(f"Progresso: {report.overall_progress}%")
    """
    try:
        from src.graph.workflow import get_workflow

        workflow = get_workflow()
        config = {"configurable": {"thread_id": user_id}}

        # Usar graph com checkpointer para acessar state
        graph_with_cp = workflow.get_graph_with_checkpointer()
        checkpoint_state = graph_with_cp.get_state(config)

        if not checkpoint_state or not checkpoint_state.values:
            logger.info(f"[INFO] Nenhum checkpoint encontrado para user_id: {user_id[:8]}...")
            return None, "[INFO] Nenhum state encontrado. Execute workflow primeiro."

        # Extrair milestone_report do state
        state_values = checkpoint_state.values
        milestone_report = None

        milestone_data = state_values.get("milestone_report")
        if milestone_data:
            if isinstance(milestone_data, MilestoneTrackerReport):
                milestone_report = milestone_data
            elif isinstance(milestone_data, dict):
                milestone_report = MilestoneTrackerReport(**milestone_data)
            else:
                # Tipo inesperado - log warning e retornar erro
                logger.warning(
                    f"[WARN] milestone_data tipo inesperado: {type(milestone_data).__name__}"
                )
                return (
                    None,
                    f"[ERRO] Tipo inesperado de milestone_data: {type(milestone_data).__name__}",
                )

            # Só loga se milestone_report foi criado com sucesso
            logger.info(
                f"[OK] Milestone Report carregado | "
                f"total={milestone_report.total_milestones} | "
                f"progresso={milestone_report.overall_progress:.1f}%"
            )
            return milestone_report, None

        return None, "[INFO] Milestone Report nao disponivel. Execute IMPLEMENTATION."

    except Exception as e:
        error_msg = f"[ERRO] Falha ao carregar milestone report: {e}"
        logger.error(error_msg, exc_info=True)
        return None, error_msg
