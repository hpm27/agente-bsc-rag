"""Estados e enums do workflow consultivo BSC.

Este módulo define os estados e transições do agente consultor empresarial,
transformando o sistema RAG Q&A em facilitador de processo consultivo estruturado.

Baseado em:
- LangGraph state machine patterns (2024-2025)
- Best practices: Human-in-the-loop, error recovery, state persistence
- Plano Consultor BSC v2.0 (FASE 2)
"""

from enum import Enum
from typing import Any

from typing_extensions import TypedDict

from src.memory.schemas import ClientProfile


class ConsultingPhase(str, Enum):
    """Fases do workflow consultivo BSC.

    Estados principais do agente consultor, seguindo pattern LangGraph StateGraph
    com suporte a human-in-the-loop via interrupt() e persistence via Mem0.

    MVP (Fase 2): IDLE -> ONBOARDING -> DISCOVERY -> APPROVAL_PENDING
    Futuro: SOLUTION_DESIGN, IMPLEMENTATION

    Referências:
    - DEV: "LangGraph State Machines" (Nov 2024)
    - Medium: "Human-in-the-Loop in LangGraph" (2024)
    - LangChain oficial: concepts/human_in_the_loop
    """

    # ===== ESTADOS MVP (Fase 2) =====

    IDLE = "idle"
    """Estado inicial. Aguardando primeira interação do usuário.

    Transições:
    - -> ONBOARDING: Detectar novo cliente (user_id sem ClientProfile em Mem0)
    - -> DISCOVERY: Cliente existente com profile completo
    """

    ONBOARDING = "onboarding"
    """Coleta de contexto empresarial (5-7 perguntas estruturadas).

    Objetivo: Criar ClientProfile completo (company, industry, challenges, objectives).
    Agente responsável: OnboardingAgent

    Transições:
    - -> DISCOVERY: Profile completo (5-7 perguntas respondidas)
    - -> ERROR: Falhas na coleta ou persistência
    """

    DISCOVERY = "discovery"
    """Diagnóstico estruturado usando ferramentas consultivas.

    Ferramentas disponíveis:
    - SWOT_Builder: Análise dos 4 quadrantes
    - FiveWhys_Facilitator: Root cause analysis
    - IssueTree_Analyzer: Decomposição de problemas
    - Parallel_Research: Benchmarks externos via Brightdata

    Agente responsável: DiagnosticAgent

    Transições:
    - -> APPROVAL_PENDING: Diagnóstico completo (1+ ferramenta executada)
    - -> DISCOVERY: Refinar diagnóstico (usuário rejeita ou pede mais análise)
    - -> ERROR: Falhas na execução de ferramentas
    """

    APPROVAL_PENDING = "approval_pending"
    """Aguarda aprovação humana do diagnóstico (Human-in-the-Loop).

    Usa LangGraph interrupt() pattern para pausar graph e aguardar input.
    Usuário pode: Aprovar, Rejeitar, Modificar, ou Solicitar refinamento.

    Transições:
    - -> SOLUTION_DESIGN: Aprovado (Fase futura, pós-MVP)
    - -> DISCOVERY: Rejeitado (refinar diagnóstico)
    - -> ERROR: Timeout ou falhas de persistência
    """

    # ===== ESTADOS FUTUROS (Pós-MVP) =====

    SOLUTION_DESIGN = "solution_design"
    """Design de soluções estratégicas (mapa estratégico BSC completo).

    FASE 5 (Sprints 2-3 - Planejado Nov 2025):
    - Strategy_Map_Designer_Tool: Converte diagnóstico em Strategy Map visual
    - Alignment_Validator_Tool: Valida balanceamento (4 perspectivas, objetivos, KPIs)
    - KPI_Alignment_Checker: Verifica KPIs alinhados com objetivos
    - Cause_Effect_Mapper: Mapeia conexões causa-efeito entre perspectivas

    Node LangGraph: design_solution()

    Transições:
    - -> IMPLEMENTATION: Strategy Map aprovado
    - -> APPROVAL_PENDING: Revisar Strategy Map
    """

    IMPLEMENTATION = "implementation"
    """Plano de ação e acompanhamento (execution premium).

    FASE 6 (Sprint 4 - Planejado Nov 2025):
    - Action_Plan_Generator_Tool: Converte Strategy Map em Action Plans
    - Milestone_Tracker_Tool: Tracking de progresso de milestones
    - MCP Asana Integration: Criar tasks (opcional Sprints 5-6)
    - MCP Google Calendar: Criar meetings (opcional Sprints 5-6)
    - Progress_Dashboard: Visualização progresso (opcional Sprints 5-6)

    Node LangGraph: generate_action_plans()

    Transições:
    - -> IDLE: Projeto concluído
    - -> IMPLEMENTATION: Ciclo iterativo
    """

    # ===== ESTADO DE ERRO =====

    ERROR = "error"
    """Estado de erro com recovery automático.

    Estratégia de recovery:
    - Retry: 3 tentativas com backoff exponencial
    - Rollback: Retornar ao último estado estável
    - Logging: Detalhes completos do erro para debugging

    Transições:
    - -> [LAST_STABLE_STATE]: Após retry ou rollback
    - -> IDLE: Se recovery falhar (reset completo)
    """


class ApprovalStatus(str, Enum):
    """Status de aprovação no estado APPROVAL_PENDING."""

    PENDING = "pending"
    """Aguardando decisão humana."""

    APPROVED = "approved"
    """Diagnóstico aprovado pelo usuário."""

    REJECTED = "rejected"
    """Diagnóstico rejeitado, precisa refinamento."""

    MODIFIED = "modified"
    """Usuário modificou o diagnóstico."""

    TIMEOUT = "timeout"
    """Timeout de aprovação (ex: 24h sem resposta)."""


class ErrorSeverity(str, Enum):
    """Severidade de erros para estratégia de recovery."""

    LOW = "low"
    """Erro recuperável automaticamente (ex: timeout de API, retry OK)."""

    MEDIUM = "medium"
    """Erro que requer rollback (ex: ferramenta falhou)."""

    HIGH = "high"
    """Erro crítico, requer intervenção (ex: Mem0 indisponível)."""

    CRITICAL = "critical"
    """Erro fatal, reset completo (ex: corrupção de estado)."""


class ErrorInfo(TypedDict, total=False):
    """Informações de erro para recovery."""

    severity: ErrorSeverity
    """Severidade do erro."""

    message: str
    """Mensagem de erro."""

    timestamp: str
    """Timestamp do erro (ISO 8601)."""

    retry_count: int
    """Número de tentativas de retry."""

    last_stable_phase: ConsultingPhase
    """Última fase estável para rollback."""

    stack_trace: str | None
    """Stack trace completo (opcional, apenas em desenvolvimento)."""


class ConsultingState(TypedDict, total=False):
    """Estado do workflow consultivo BSC.

    Extends BSCState (RAG) com campos consultivos:
    - Tracking de fase (current_phase)
    - Memória persistente (client_profile via Mem0)
    - Approval workflow (approval_status)
    - Error recovery (error_info, phase_history)

    Integração com Mem0:
    - client_profile carregado no início (load_client_memory node)
    - client_profile salvo ao fim (save_client_memory node)
    - Persistência automática entre sessões

    Best practices:
    - Keep states simple (apenas dados necessários)
    - Consider serialization (JSON-friendly types)
    - Log state transitions (auditoria)
    """

    # ===== Campos RAG existentes (herdados de BSCState) =====

    user_query: str
    """Query do usuário (mantido para compatibilidade RAG)."""

    conversation_history: list[dict[str, str]]
    """Histórico de conversação completo."""

    retrieved_docs: list[Any]
    """Documentos recuperados (RAG context)."""

    current_agent: str | None
    """Agente RAG atual (Financial, Customer, Process, Learning)."""

    synthesis: str
    """Síntese final da resposta."""

    # ===== Campos consultivos (novos) =====

    user_id: str
    """ID único do usuário/empresa (chave para Mem0)."""

    client_profile: ClientProfile | None
    """Perfil do cliente carregado do Mem0.

    Estrutura completa:
    - company: CompanyInfo (name, industry, size, maturity)
    - strategic_context: StrategicContext (challenges, objectives, stakeholders)
    - diagnostic: DiagnosticData (swot, issue_tree, kpis_defined)
    - engagement: EngagementState (mode, current_phase, history)
    """

    current_phase: ConsultingPhase
    """Fase atual do workflow consultivo."""

    previous_phase: ConsultingPhase | None
    """Fase anterior (para rollback)."""

    phase_history: list[dict[str, Any]]
    """Histórico de mudanças de fase.

    Formato:
    [{
        "from_phase": "onboarding",
        "to_phase": "discovery",
        "timestamp": "2025-10-15T14:30:00Z",
        "trigger": "profile_completed",
        "duration_seconds": 120
    }]
    """

    approval_status: ApprovalStatus | None
    """Status de aprovação (apenas em APPROVAL_PENDING)."""

    approval_feedback: str | None
    """Feedback do usuário na aprovação/rejeição."""

    error_info: ErrorInfo | None
    """Informações de erro (apenas em ERROR phase)."""

    tool_outputs: dict[str, Any]
    """Outputs das ferramentas consultivas executadas.

    Exemplo:
    {
        "swot_analysis": {
            "strengths": [...],
            "weaknesses": [...],
            "opportunities": [...],
            "threats": [...]
        },
        "five_whys": {
            "root_cause": "...",
            "why_chain": [...]
        }
    }
    """

    onboarding_progress: dict[str, bool]
    """Progresso das perguntas de onboarding (5-7 perguntas).

    Exemplo:
    {
        "company_name": True,
        "industry": True,
        "main_challenge": False,
        "objectives": False,
        "stakeholders": False
    }
    """


class TransitionTrigger(str, Enum):
    """Triggers de transição entre fases.

    Usado para auditoria e debugging de mudanças de estado.
    """

    # IDLE triggers
    NEW_CLIENT = "new_client"
    """Novo cliente detectado (sem profile)."""

    RETURNING_CLIENT = "returning_client"
    """Cliente existente (profile carregado)."""

    # ONBOARDING triggers
    PROFILE_COMPLETED = "profile_completed"
    """5-7 perguntas respondidas, profile completo."""

    PROFILE_INCOMPLETE = "profile_incomplete"
    """Perguntas incompletas (permanece em onboarding)."""

    # DISCOVERY triggers
    DIAGNOSTIC_COMPLETED = "diagnostic_completed"
    """Diagnóstico completo (1+ ferramenta executada)."""

    REFINEMENT_REQUESTED = "refinement_requested"
    """Usuário solicitou refinar diagnóstico."""

    # APPROVAL triggers
    USER_APPROVED = "user_approved"
    """Usuário aprovou diagnóstico."""

    USER_REJECTED = "user_rejected"
    """Usuário rejeitou diagnóstico."""

    USER_MODIFIED = "user_modified"
    """Usuário modificou diagnóstico."""

    APPROVAL_TIMEOUT = "approval_timeout"
    """Timeout de aprovação (24h)."""

    # ERROR triggers
    API_ERROR = "api_error"
    """Erro de API (LLM, Mem0, Brightdata)."""

    VALIDATION_ERROR = "validation_error"
    """Erro de validação de dados."""

    TIMEOUT_ERROR = "timeout_error"
    """Timeout de operação."""

    RECOVERY_SUCCESS = "recovery_success"
    """Recovery bem-sucedido."""

    RECOVERY_FAILED = "recovery_failed"
    """Recovery falhou."""


def create_initial_consulting_state(user_id: str, user_query: str) -> ConsultingState:
    """Cria estado consultivo inicial para novo workflow.

    Args:
        user_id: ID único do usuário/empresa
        user_query: Query inicial do usuário

    Returns:
        ConsultingState inicializado em fase IDLE
    """
    return ConsultingState(
        # RAG fields
        user_query=user_query,
        conversation_history=[{"role": "user", "content": user_query}],
        retrieved_docs=[],
        current_agent=None,
        synthesis="",
        # Consulting fields
        user_id=user_id,
        client_profile=None,  # Será carregado do Mem0
        current_phase=ConsultingPhase.IDLE,
        previous_phase=None,
        phase_history=[],
        approval_status=None,
        approval_feedback=None,
        error_info=None,
        tool_outputs={},
        onboarding_progress={},
    )


def should_transition(
    current_phase: ConsultingPhase, target_phase: ConsultingPhase, state: ConsultingState
) -> bool:
    """Valida se transição entre fases é permitida.

    Implementa transition logic com validações de estado.

    Args:
        current_phase: Fase atual
        target_phase: Fase desejada
        state: Estado completo do workflow

    Returns:
        True se transição é válida, False caso contrário

    Examples:
        >>> should_transition(
        ...     ConsultingPhase.ONBOARDING,
        ...     ConsultingPhase.DISCOVERY,
        ...     state_with_complete_profile
        ... )
        True
    """
    # IDLE -> ONBOARDING: Sempre permitido para novos clientes
    if current_phase == ConsultingPhase.IDLE and target_phase == ConsultingPhase.ONBOARDING:
        return state.get("client_profile") is None

    # IDLE -> DISCOVERY: Permitido apenas se profile existe
    if current_phase == ConsultingPhase.IDLE and target_phase == ConsultingPhase.DISCOVERY:
        return state.get("client_profile") is not None

    # ONBOARDING -> DISCOVERY: Profile completo
    if current_phase == ConsultingPhase.ONBOARDING and target_phase == ConsultingPhase.DISCOVERY:
        profile = state.get("client_profile")
        if not profile:
            return False
        # Validar campos obrigatórios (company, industry, challenges, objectives)
        return profile.get("company") is not None and profile.get("strategic_context") is not None

    # DISCOVERY -> APPROVAL_PENDING: Pelo menos 1 ferramenta executada
    if (
        current_phase == ConsultingPhase.DISCOVERY
        and target_phase == ConsultingPhase.APPROVAL_PENDING
    ):
        tool_outputs = state.get("tool_outputs", {})
        return len(tool_outputs) > 0

    # APPROVAL_PENDING -> DISCOVERY: Refinamento solicitado
    if (
        current_phase == ConsultingPhase.APPROVAL_PENDING
        and target_phase == ConsultingPhase.DISCOVERY
    ):
        return state.get("approval_status") == ApprovalStatus.REJECTED

    # APPROVAL_PENDING -> SOLUTION_DESIGN: Aprovado (Fase futura)
    if (
        current_phase == ConsultingPhase.APPROVAL_PENDING
        and target_phase == ConsultingPhase.SOLUTION_DESIGN
    ):
        return state.get("approval_status") == ApprovalStatus.APPROVED

    # ERROR -> Qualquer fase anterior: Recovery
    if current_phase == ConsultingPhase.ERROR:
        error_info = state.get("error_info")
        if error_info:
            last_stable = error_info.get("last_stable_phase")
            return target_phase == last_stable
        return target_phase == ConsultingPhase.IDLE  # Fallback

    # Transição não mapeada
    return False
