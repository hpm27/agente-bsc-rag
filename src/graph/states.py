"""
Definição de estados para o grafo LangGraph.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from src.graph.consulting_states import ApprovalStatus, ConsultingPhase
from src.memory.schemas import AlignmentReport, ClientProfile, StrategyMap

# ============================================================================
# CUSTOM REDUCER: Deep Merge para Metadata
# ============================================================================


def deep_merge_dicts(current: Any, update: Any) -> dict[str, Any]:
    """
    Custom reducer para LangGraph: deep merge de dicts aninhados.

    Preserva nested keys como partial_profile entre turnos do onboarding multi-turn.
    Solução baseada em Stack Overflow (Hans Bouwmeester, 2018) + best practices comunidade 2024-2025.

    Args:
        current: Dict existente no checkpoint LangGraph
        update: Dict novo retornado pelo handler

    Returns:
        Dict merged (deep recursivo, não shallow)

    Behavior:
        - Se current ou update não são dicts: retorna update
        - Chaves novas em update: adicionadas ao result
        - Chaves existentes com valores dict em ambos: merge recursivo
        - Chaves existentes com outros tipos: update sobrescreve current

    Example:
        >>> current = {"partial_profile": {"challenges": ["A"], "company_name": "TechCorp"}, "chat_history": [1]}
        >>> update = {"partial_profile": {"challenges": ["A", "B"]}, "chat_history": [1, 2]}
        >>> deep_merge_dicts(current, update)
        {"partial_profile": {"challenges": ["A", "B"], "company_name": "TechCorp"}, "chat_history": [1, 2]}
        # NOTE: company_name preservado mesmo não estando em update!

    Use Case (BSC RAG):
        - Onboarding multi-turn: acumula company_name, industry, challenges, goals entre turnos
        - Sem deep merge: partial_profile seria substituído inteiro (perda de dados)
        - Com deep merge: apenas campos em update são atualizados, demais preservados

    References:
        - Stack Overflow Q7204805 (167K views, solução validada Hans Bouwmeester)
        - LangGraph Docs - Custom Reducers (langchain-ai.github.io/langgraph/concepts/low_level/#reducers)
    """
    # Base case: se qualquer um não é MutableMapping, retornar update como dict
    if not isinstance(current, MutableMapping) or not isinstance(update, MutableMapping):
        result_dict: dict[str, Any] = dict(update) if isinstance(update, MutableMapping) else {}
        return result_dict

    # Converter para dict e criar cópia para evitar mutação
    result: dict[str, Any] = dict(current)  # Converte MutableMapping -> dict

    # Iterar sobre chaves do update
    for key, update_value in update.items():
        current_value = result.get(key)

        # Se ambos são MutableMapping (dicts), merge recursivo
        if isinstance(current_value, MutableMapping) and isinstance(update_value, MutableMapping):
            result[key] = deep_merge_dicts(current_value, update_value)
        else:
            # Caso contrário, update substitui current (comportamento padrão dict.update())
            result[key] = update_value

    return result


# ============================================================================
# GRAPH STATE SCHEMAS
# ============================================================================


class PerspectiveType(str, Enum):
    """Perspectivas do BSC."""

    FINANCIAL = "financial"
    CUSTOMER = "customer"
    PROCESS = "process"
    LEARNING = "learning"


class AgentResponse(BaseModel):
    """Resposta de um agente especialista."""

    perspective: PerspectiveType
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: str | None = None


class JudgeEvaluation(BaseModel):
    """Avaliação do Judge Agent."""

    approved: bool
    score: float = Field(ge=0.0, le=1.0)
    feedback: str
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    verdict: str | None = None
    is_complete: bool | None = None
    is_grounded: bool | None = None
    has_sources: bool | None = None


class BSCState(BaseModel):
    """Estado do grafo de execução BSC."""

    # Input
    query: str
    session_id: str | None = None
    user_id: str | None = None

    # Memória persistente do cliente (integração Mem0)
    client_profile: ClientProfile | None = None

    # Análise da query
    relevant_perspectives: list[PerspectiveType] = Field(default_factory=list)
    query_type: str | None = None  # "factual", "conceptual", "comparative"
    complexity: str | None = None  # "simple", "moderate", "complex"

    # Respostas dos agentes
    agent_responses: list[AgentResponse] = Field(default_factory=list)

    # Agregação
    aggregated_response: str | None = None

    # Validação
    judge_evaluation: JudgeEvaluation | None = None

    # Refinamento (se necessário)
    refinement_iteration: int = 0
    max_refinement_iterations: int = 2

    # Output final
    final_response: str | None = None
    metadata: Annotated[dict[str, Any], deep_merge_dicts] = Field(default_factory=dict)

    # Controle de fluxo
    needs_refinement: bool = False
    is_complete: bool = False

    # ===== CAMPOS CONSULTIVOS (FASE 2.2+) =====

    # Phase tracking
    current_phase: ConsultingPhase | None = None
    previous_phase: ConsultingPhase | None = None
    phase_history: list[dict[str, Any]] = Field(default_factory=list)

    # Approval workflow (FASE 2.8)
    approval_status: ApprovalStatus | None = None
    approval_feedback: str | None = None

    # Onboarding (FASE 2.6)
    # Estrutura: {"current_step": int, "followup_counts": dict[int, int], "challenges": bool, "objectives": bool}
    onboarding_progress: dict[str, Any] = Field(default_factory=dict)

    # Diagnostic (FASE 2.7)
    diagnostic: dict[str, Any] | None = None

    # Tool outputs (FASE 3)
    tool_outputs: dict[str, Any] = Field(default_factory=dict)

    # Strategy Map (SPRINT 2 - FASE 5)
    strategy_map: StrategyMap | None = None
    alignment_report: AlignmentReport | None = None

    # Action Plan (SPRINT 3 - FASE 6) - BUG FIX SESSAO 41 (2025-11-22)
    # Campo ausente causava action_plan não ser salvo no state (LangGraph ignora campos não definidos)
    action_plan: dict[str, Any] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    def model_dump(self, *args, **kwargs):  # type: ignore[override]
        """Sobrescreve dump para excluir campos None por padrão.
        Evita duplicidade de kwargs ao reconstruir BSCState com overrides.
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        return super().model_dump(*args, **kwargs)
