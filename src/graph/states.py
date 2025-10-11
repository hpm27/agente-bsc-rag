"""
Definição de estados para o grafo LangGraph.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


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


class BSCState(BaseModel):
    """Estado do grafo de execução BSC."""
    
    # Input
    query: str
    session_id: Optional[str] = None
    
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
    
    # Controle de fluxo
    needs_refinement: bool = False
    is_complete: bool = False
    
    class Config:
        arbitrary_types_allowed = True



