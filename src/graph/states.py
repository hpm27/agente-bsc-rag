"""
Definição de estados para o grafo LangGraph.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.graph.consulting_states import ApprovalStatus, ConsultingPhase
from src.memory.schemas import ClientProfile


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
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Controle de fluxo
    needs_refinement: bool = False
    is_complete: bool = False

    # ===== CAMPOS CONSULTIVOS (FASE 2.2+) =====

    # Phase tracking
    current_phase: ConsultingPhase | None = None
    previous_phase: ConsultingPhase | None = None
    phase_history: list[str] = Field(default_factory=list)

    # Approval workflow (FASE 2.8)
    approval_status: ApprovalStatus | None = None
    approval_feedback: str | None = None

    # Onboarding (FASE 2.6)
    onboarding_progress: dict[str, bool] = Field(default_factory=dict)

    # Diagnostic (FASE 2.7)
    diagnostic: dict[str, Any] | None = None

    # Tool outputs (FASE 3)
    tool_outputs: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)



