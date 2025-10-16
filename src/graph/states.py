"""
Definição de estados para o grafo LangGraph.

Este módulo define os estados do workflow BSC, unificando:
- Campos RAG (Q&A multi-agente existente)
- Campos Consultivos (workflow estruturado de consultoria)

Versão: 2.0 (FASE 2.2 - Expand ConsultingState)
- Mantém 100% compatibilidade com RAG existente
- Adiciona campos consultivos (phase tracking, approval, error recovery)
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Import ClientProfile para integração com memória
from src.memory.schemas import ClientProfile

# Import enums consultivos compartilhados
from src.graph.consulting_states import (
    ConsultingPhase,
    ApprovalStatus,
    ErrorSeverity
)


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
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: Optional[str] = None


class JudgeEvaluation(BaseModel):
    """Avaliação do Judge Agent."""
    approved: bool
    score: float = Field(ge=0.0, le=1.0)
    feedback: str
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    verdict: Optional[str] = None
    is_complete: Optional[bool] = None
    is_grounded: Optional[bool] = None
    has_sources: Optional[bool] = None


class ErrorInfo(BaseModel):
    """Informações de erro para recovery automático.
    
    Usado no estado ERROR do workflow consultivo para rastrear
    erros, tentativas de retry, e estado estável para rollback.
    
    Attributes:
        severity: Severidade do erro (LOW, MEDIUM, HIGH, CRITICAL)
        message: Mensagem de erro legível
        timestamp: Timestamp ISO 8601 do erro
        retry_count: Número de tentativas de retry realizadas
        last_stable_phase: Última fase estável conhecida (para rollback)
        stack_trace: Stack trace completo (opcional, apenas debug)
    """
    severity: ErrorSeverity
    message: str
    timestamp: str
    retry_count: int = 0
    last_stable_phase: Optional[ConsultingPhase] = None
    stack_trace: Optional[str] = None


class BSCState(BaseModel):
    """Estado unificado do grafo de execução BSC (RAG + Consultoria).
    
    Versão 2.0 (FASE 2.2): Expandido com campos consultivos mantendo
    100% compatibilidade retroativa com workflow RAG existente.
    
    SEÇÃO 1: CAMPOS RAG EXISTENTES
    - Query processing, análise, roteamento
    - Respostas dos agentes especialistas
    - Síntese, validação Judge, refinamento
    - Memória persistente (Mem0)
    
    SEÇÃO 2: CAMPOS CONSULTIVOS (novos)
    - Phase tracking (IDLE → ONBOARDING → DISCOVERY → APPROVAL → ...)
    - Approval workflow (human-in-the-loop)
    - Error recovery (retry, rollback)
    - Tool outputs (SWOT, 5 Whys, Issue Tree)
    - Onboarding progress
    """
    
    # ===== SEÇÃO 1: CAMPOS RAG EXISTENTES =====
    
    # Input
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Memória persistente do cliente (integração Mem0)
    client_profile: Optional[ClientProfile] = None
    
    # Análise da query
    relevant_perspectives: List[PerspectiveType] = Field(default_factory=list)
    query_type: Optional[str] = None  # "factual", "conceptual", "comparative"
    complexity: Optional[str] = None  # "simple", "moderate", "complex"
    
    # Respostas dos agentes
    agent_responses: List[AgentResponse] = Field(default_factory=list)
    
    # Agregação
    aggregated_response: Optional[str] = None
    
    # Validação
    judge_evaluation: Optional[JudgeEvaluation] = None
    
    # Refinamento (se necessário)
    refinement_iteration: int = 0
    max_refinement_iterations: int = 2
    
    # Output final
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Controle de fluxo RAG
    needs_refinement: bool = False
    is_complete: bool = False
    
    # ===== SEÇÃO 2: CAMPOS CONSULTIVOS (FASE 2.2+) =====
    
    # Phase tracking
    current_phase: ConsultingPhase = Field(default=ConsultingPhase.IDLE)
    """Fase atual do workflow consultivo (IDLE, ONBOARDING, DISCOVERY, etc)."""
    
    previous_phase: Optional[ConsultingPhase] = None
    """Fase anterior (usado para rollback em caso de erro)."""
    
    phase_history: List[Dict[str, Any]] = Field(default_factory=list)
    """Histórico completo de transições de fase.
    
    Formato:
    [{
        "from_phase": "onboarding",
        "to_phase": "discovery",
        "timestamp": "2025-10-15T14:30:00Z",
        "trigger": "profile_completed",
        "duration_seconds": 120
    }]
    """
    
    # Approval workflow (human-in-the-loop)
    approval_status: Optional[ApprovalStatus] = None
    """Status de aprovação (PENDING, APPROVED, REJECTED, MODIFIED, TIMEOUT).
    
    Usado apenas quando current_phase == APPROVAL_PENDING.
    """
    
    approval_feedback: Optional[str] = None
    """Feedback textual do usuário ao aprovar/rejeitar diagnóstico."""
    
    # Error recovery
    error_info: Optional[ErrorInfo] = None
    """Informações de erro para recovery automático.
    
    Preenchido apenas quando current_phase == ERROR.
    Contém: severity, message, retry_count, last_stable_phase, stack_trace.
    """
    
    # Tool outputs (ferramentas consultivas)
    tool_outputs: Dict[str, Any] = Field(default_factory=dict)
    """Outputs das ferramentas consultivas executadas.
    
    Exemplos:
    - "swot_analysis": {strengths: [...], weaknesses: [...], ...}
    - "five_whys": {root_cause: "...", why_chain: [...]}
    - "issue_tree": {root_issue: "...", branches: [...]}
    - "parallel_research": {sources: [...], insights: [...]}
    """
    
    # Onboarding progress
    onboarding_progress: Dict[str, bool] = Field(default_factory=dict)
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
    
    model_config = ConfigDict(arbitrary_types_allowed=True)



