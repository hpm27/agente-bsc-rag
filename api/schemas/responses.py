"""Response schemas Pydantic para API REST.

Define estruturas de output para todos os endpoints.

Fase: 4.3 - Integration APIs
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# STANDARD RESPONSES
# ============================================================================

class ErrorResponse(BaseModel):
    """Response padrão para erros."""
    
    error: str = Field(description="Tipo de erro")
    message: str = Field(description="Mensagem detalhada")
    details: dict | None = Field(default=None, description="Detalhes adicionais")


class SuccessResponse(BaseModel):
    """Response padrão para operações de sucesso simples."""
    
    success: bool = True
    message: str


# ============================================================================
# CLIENTS
# ============================================================================

class ClientResponse(BaseModel):
    """Response ao criar/obter cliente."""
    
    client_id: str = Field(examples=["cli_abc123"])
    company_name: str
    sector: str
    size: str | None = None
    current_phase: str = Field(examples=["ONBOARDING", "DISCOVERY", "IMPLEMENTATION"])
    created_at: str  # ISO 8601
    updated_at: str
    total_challenges: int = 0
    total_objectives: int = 0
    has_diagnostic: bool = False


class ClientListResponse(BaseModel):
    """Response para listagem paginada de clientes."""
    
    clients: list[ClientResponse]
    total: int = Field(description="Total de clientes (sem filtros)")
    page: int = Field(default=1, description="Página atual")
    page_size: int = Field(default=50, description="Items por página")
    has_next: bool = Field(description="Se há próxima página")


class ClientSummaryResponse(BaseModel):
    """Response resumida de cliente (para dashboard)."""
    
    client_id: str
    company_name: str
    sector: str
    current_phase: str
    updated_at: str
    tools_executed: int = 0
    diagnostic_status: Literal["none", "in_progress", "completed"] = "none"


# ============================================================================
# DIAGNOSTICS
# ============================================================================

class DiagnosticResponse(BaseModel):
    """Response ao criar diagnóstico BSC."""
    
    diagnostic_id: str = Field(examples=["diag_xyz789"])
    client_id: str
    status: Literal["processing", "completed", "failed"] = "processing"
    created_at: str
    estimated_completion: str | None = None  # ISO 8601
    webhook_configured: bool = False


class DiagnosticCompleteResponse(BaseModel):
    """Response com diagnóstico BSC completo."""
    
    diagnostic_id: str
    client_id: str
    executive_summary: str
    perspectives_analyzed: int = 4
    recommendations_count: int
    synergies_count: int
    created_at: str
    
    # Opcionalmente incluir detalhes completos
    full_diagnostic: dict | None = None  # CompleteDiagnostic.model_dump()


class PerspectiveResponse(BaseModel):
    """Response de perspectiva BSC individual."""
    
    perspective: str = Field(examples=["Financeira", "Clientes"])
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    current_state: str
    opportunities: list[str]
    risks: list[str]
    recommendations: list[dict]  # Simplified Recommendation


# ============================================================================
# TOOLS
# ============================================================================

class ToolExecutionResponse(BaseModel):
    """Response base para execução de ferramenta."""
    
    tool_output_id: str = Field(examples=["swot_123", "5whys_456"])
    tool_name: str = Field(examples=["SWOT Analysis", "5 Whys"])
    client_id: str
    status: Literal["completed", "processing", "failed"]
    created_at: str
    execution_time_seconds: float | None = None


class SwotResponse(ToolExecutionResponse):
    """Response específica para SWOT."""
    
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]
    strategic_recommendations: list[str]


class FiveWhysResponse(ToolExecutionResponse):
    """Response específica para 5 Whys."""
    
    problem_statement: str
    root_causes: list[str]  # 1-5 root causes identificadas
    whys_chain: list[dict]  # [{why_number, question, answer}, ...]
    recommended_actions: list[str]


class KpiDefinitionResponse(ToolExecutionResponse):
    """Response específica para KPI Definition."""
    
    perspective: str | None
    kpis: list[dict]  # [{name, description, formula, target, ...}, ...]
    total_kpis: int


class ToolsListResponse(BaseModel):
    """Response para listagem de ferramentas disponíveis."""
    
    tools: list[dict] = Field(
        description="Lista de ferramentas consultivas",
        examples=[[
            {"name": "swot", "description": "Análise SWOT", "endpoint": "/api/v1/tools/swot"},
            {"name": "five-whys", "description": "5 Porquês", "endpoint": "/api/v1/tools/five-whys"}
        ]]
    )
    total: int


# ============================================================================
# REPORTS
# ============================================================================

class ReportResponse(BaseModel):
    """Response ao gerar report."""
    
    report_id: str = Field(examples=["rpt_abc456"])
    report_type: str = Field(examples=["pdf_diagnostic", "csv_clients"])
    status: Literal["processing", "completed", "failed"]
    download_url: str | None = Field(
        default=None,
        description="URL para download (disponível quando status=completed)",
        examples=["/api/v1/reports/rpt_abc456/download"]
    )
    expires_at: str | None = Field(
        default=None,
        description="Data de expiração do download (7 dias típico)"
    )
    file_size_bytes: int | None = None


# ============================================================================
# WEBHOOKS
# ============================================================================

class WebhookResponse(BaseModel):
    """Response ao registrar webhook."""
    
    webhook_id: str = Field(examples=["whk_xyz789"])
    url: str
    events: list[str]
    secret_provided: bool = Field(description="Se secret foi fornecido para HMAC")
    is_active: bool = True
    created_at: str
    last_triggered: str | None = None
    total_deliveries: int = 0
    failed_deliveries: int = 0


class WebhookListResponse(BaseModel):
    """Response para listagem de webhooks."""
    
    webhooks: list[WebhookResponse]
    total: int


class WebhookTestResponse(BaseModel):
    """Response ao testar webhook (ping)."""
    
    webhook_id: str
    test_event_sent: bool
    response_status: int | None = Field(description="HTTP status code do endpoint")
    response_time_ms: float | None = Field(description="Latência em milissegundos")
    error: str | None = None


# ============================================================================
# ADMIN
# ============================================================================

class APIKeyResponse(BaseModel):
    """Response ao criar/obter API key."""
    
    api_key: str = Field(examples=["bsc_live_abc123def456..."])
    client_id: str | None = None
    tier: Literal["free", "professional", "enterprise"]
    permissions: list[str]
    created_at: str
    expires_at: str | None = None
    is_active: bool = True
    
    # Warning se test key
    environment: Literal["live", "test"] = "live"


class APIKeyListResponse(BaseModel):
    """Response para listagem de API keys."""
    
    api_keys: list[APIKeyResponse]
    total: int

