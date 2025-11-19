"""Response schemas Pydantic para API REST.

Define estruturas de output para todos os endpoints.

Fase: 4.3 - Integration APIs
"""

from datetime import datetime
from typing import Literal, Optional, Dict, Any, List

from pydantic import BaseModel, Field


# ============================================================================
# STANDARD RESPONSES
# ============================================================================

class ErrorResponse(BaseModel):
    """Response padrão para erros."""
    
    error: str = Field(description="Tipo de erro")
    message: str = Field(description="Mensagem detalhada")
    details: dict | None = Field(default=None, description="Detalhes adicionais")


# ============================================================================
# ANALYTICS (FASE 4.4)
# ============================================================================

class OverviewMetricsResponse(BaseModel):
    """KPIs principais do dashboard analytics."""
    
    total_requests: int = Field(description="Total de requests no período")
    error_rate: float = Field(description="Taxa de erros (0.0 a 1.0)")
    avg_latency_ms: float = Field(description="Latência média em milissegundos")
    active_api_keys: int = Field(description="Número de API keys ativas")
    period: str = Field(description="Período analisado (ex: '24h')")


class TrafficDataPoint(BaseModel):
    """Ponto de dados de tráfego (time-series)."""
    
    timestamp: str = Field(description="Timestamp do ponto")
    endpoint: str = Field(description="Endpoint (ou 'total' para todos)")
    count: int = Field(description="Número de requests")
    errors: int = Field(description="Número de erros")
    error_4xx: int = Field(description="Erros 4xx")
    error_5xx: int = Field(description="Erros 5xx")
    
    class Config:
        # Permitir acesso via .4xx e .5xx além de error_4xx e error_5xx
        populate_by_name = True


class TrafficResponse(BaseModel):
    """Response com dados de tráfego (time-series)."""
    
    data: list[TrafficDataPoint] = Field(description="Pontos de dados")
    period: str = Field(description="Período analisado")
    interval: str = Field(description="Intervalo de agregação (minute/hour/day)")


class LatencyMetricsResponse(BaseModel):
    """Métricas de latência (percentis)."""
    
    endpoint: str = Field(description="Endpoint")
    p50: float = Field(description="Percentil 50 (mediana) em ms")
    p95: float = Field(description="Percentil 95 em ms")
    p99: float = Field(description="Percentil 99 em ms")
    mean: float = Field(description="Latência média em ms")
    max: float = Field(description="Latência máxima em ms")
    samples: int = Field(description="Número de amostras")


class ErrorMetricsResponse(BaseModel):
    """Métricas de erros por endpoint."""
    
    endpoint: str = Field(description="Endpoint")
    total_requests: int = Field(description="Total de requests")
    errors: int = Field(description="Total de erros")
    error_rate: float = Field(description="Taxa de erro (0.0 a 1.0)")


class ConsumerMetricsResponse(BaseModel):
    """Métricas de uso por cliente (API key)."""
    
    api_key: str = Field(description="API key (mascarado)")
    requests: int = Field(description="Total de requests")
    unique_endpoints: int = Field(description="Número de endpoints únicos acessados")
    last_request: str = Field(description="Timestamp da última requisição (ISO 8601)")


class EndpointMetricsResponse(BaseModel):
    """Métricas detalhadas por endpoint."""
    
    endpoint: str = Field(description="Endpoint")
    requests: int = Field(description="Total de requests")
    errors: int = Field(description="Total de erros")
    error_rate: float = Field(description="Taxa de erro")
    latency_p50: float | None = Field(default=None, description="Latência P50 em ms")
    latency_p95: float | None = Field(default=None, description="Latência P95 em ms")
    latency_p99: float | None = Field(default=None, description="Latência P99 em ms")


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


# ============================================================================
# FEEDBACK (FASE 4.5)
# ============================================================================

class FeedbackRequest(BaseModel):
    """Request para criar feedback."""
    
    rating: int = Field(ge=1, le=5, description="Avaliação de 1-5")
    comment: Optional[str] = Field(None, max_length=1000, description="Feedback textual opcional")
    diagnostic_id: str = Field(description="ID do diagnóstico avaliado")
    phase: str = Field(description="Fase do workflow (ex: discovery, approval_pending)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")


class FeedbackResponse(BaseModel):
    """Response com feedback criado."""
    
    feedback_id: str = Field(description="ID único do feedback")
    rating: int = Field(description="Avaliação de 1-5")
    comment: Optional[str] = Field(None, description="Feedback textual")
    diagnostic_id: str = Field(description="ID do diagnóstico")
    user_id: str = Field(description="ID do usuário")
    phase: str = Field(description="Fase do workflow")
    created_at: str = Field(description="Timestamp ISO 8601")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados")


class FeedbackListResponse(BaseModel):
    """Response para listagem de feedbacks."""
    
    feedbacks: List[FeedbackResponse] = Field(description="Lista de feedbacks")
    total: int = Field(description="Total de feedbacks encontrados")


class FeedbackStatsResponse(BaseModel):
    """Response com estatísticas agregadas de feedback."""
    
    total_count: int = Field(description="Total de feedbacks")
    avg_rating: float = Field(description="Média de ratings")
    positive_count: int = Field(description="Count de ratings >= 4")
    negative_count: int = Field(description="Count de ratings <= 2")
    neutral_count: int = Field(description="Count de ratings == 3")
    rating_distribution: Dict[int, int] = Field(description="Distribuição de ratings (1-5)")


# ============================================================================
# NOTIFICATION SCHEMAS (FASE 4.7)
# ============================================================================


class NotificationRequest(BaseModel):
    """Request para criar notificação."""
    
    type: str = Field(description="Tipo de evento (diagnostic_completed, refinement_completed, feedback_received, error_occurred)")
    user_id: str = Field(min_length=3, description="ID do usuário destinatário")
    diagnostic_id: Optional[str] = Field(None, description="ID do diagnóstico relacionado (se aplicável)")
    title: str = Field(min_length=5, max_length=100, description="Título resumido da notificação")
    message: str = Field(min_length=10, max_length=500, description="Mensagem detalhada sobre o evento")
    priority: str = Field(default="medium", description="Prioridade (high, medium, low)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadados adicionais")


class NotificationResponse(BaseModel):
    """Response com notificação criada/recuperada."""
    
    id: str = Field(description="ID único da notificação")
    type: str = Field(description="Tipo de evento")
    user_id: str = Field(description="ID do usuário destinatário")
    diagnostic_id: Optional[str] = Field(None, description="ID do diagnóstico")
    title: str = Field(description="Título da notificação")
    message: str = Field(description="Mensagem detalhada")
    status: str = Field(description="Estado de leitura (unread, read)")
    priority: str = Field(description="Prioridade (high, medium, low)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados")
    created_at: str = Field(description="Timestamp ISO 8601 de criação")
    read_at: Optional[str] = Field(None, description="Timestamp ISO 8601 de leitura (None se não lida)")


class NotificationListResponse(BaseModel):
    """Response para listagem de notificações."""
    
    notifications: List[NotificationResponse] = Field(description="Lista de notificações")
    total: int = Field(description="Total de notificações encontradas")


class NotificationStatsResponse(BaseModel):
    """Response com estatísticas de notificações."""
    
    total_count: int = Field(description="Total de notificações")
    unread_count: int = Field(description="Total de notificações não lidas")
    by_priority: Dict[str, int] = Field(description="Contagem por prioridade (high, medium, low)")
    by_type: Dict[str, int] = Field(description="Contagem por tipo de evento")


# ============================================================================
# PERFORMANCE METRICS SCHEMAS (FASE 4.8)
# ============================================================================


class MetricsListResponse(BaseModel):
    """Response com lista de métricas de performance."""
    
    metrics: List[Dict[str, Any]] = Field(description="Lista de métricas (PerformanceMetrics serializadas)")
    total: int = Field(description="Total de métricas retornadas")
    filters_applied: Dict[str, Any] = Field(description="Filtros aplicados na busca")


class MetricsStatsResponse(BaseModel):
    """Response com estatísticas agregadas de performance."""
    
    total_requests: int = Field(description="Total de requests no período")
    error_requests: int = Field(description="Total de requests com erro (status >= 400)")
    error_rate: float = Field(description="Taxa de erro em % (0-100)")
    throughput_per_min: float = Field(description="Throughput médio (requests/minuto)")
    latency: Dict[str, float] = Field(description="Latências (p50_ms, p95_ms, mean_ms, min_ms, max_ms)")
    tokens: Dict[str, Dict[str, int]] = Field(description="Tokens consumidos por modelo LLM")
    cost_usd: float = Field(description="Custo estimado em USD (baseado em pricing LLM)")
    period_hours: int = Field(description="Período analisado em horas")
    endpoint: str = Field(description="Endpoint filtrado (ou 'ALL')")

