"""Request schemas Pydantic para API REST.

Define estruturas de input para todos os endpoints.

Fase: 4.3 - Integration APIs
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# CLIENTS
# ============================================================================

class CreateClientRequest(BaseModel):
    """Request para criar novo cliente BSC."""
    
    company_name: str = Field(
        min_length=2,
        max_length=200,
        description="Nome da empresa",
        examples=["Engelar Indústria Ltda"]
    )
    sector: str = Field(
        min_length=3,
        max_length=100,
        description="Setor de atuação",
        examples=["Manufatura", "Tecnologia", "Serviços"]
    )
    size: Literal["pequena", "média", "grande"] | None = Field(
        default=None,
        description="Porte da empresa (opcional)"
    )
    revenue: str | None = Field(
        default=None,
        description="Faixa de receita (opcional)",
        examples=["R$ 1-10M", "R$ 10-50M"]
    )
    challenges: list[str] = Field(
        min_length=2,
        description="Desafios estratégicos (mínimo 2)",
        examples=[["estoque", "fluxo caixa", "produtividade"]]
    )
    objectives: list[str] = Field(
        min_length=3,
        description="Objetivos estratégicos (mínimo 3)",
        examples=[["crescer 150t→250t/mês", "implementar ERP", "reduzir custos 15%"]]
    )


class UpdateClientRequest(BaseModel):
    """Request para atualizar cliente existente."""
    
    company_name: str | None = None
    sector: str | None = None
    size: Literal["pequena", "média", "grande"] | None = None
    revenue: str | None = None
    challenges: list[str] | None = None
    objectives: list[str] | None = None


# ============================================================================
# DIAGNOSTICS
# ============================================================================

class CreateDiagnosticRequest(BaseModel):
    """Request para criar diagnóstico BSC."""
    
    client_id: str = Field(
        description="ID do cliente para diagnosticar",
        examples=["cli_abc123"]
    )
    async_mode: bool = Field(
        default=False,
        description="Se True, retorna imediatamente e envia resultado via webhook"
    )
    webhook_url: str | None = Field(
        default=None,
        description="URL para webhook (obrigatório se async=True)",
        examples=["https://cliente.com/webhooks/diagnostic"]
    )
    force_regenerate: bool = Field(
        default=False,
        description="Se True, força re-gerar mesmo que já exista diagnóstico"
    )


# ============================================================================
# TOOLS (Ferramentas Consultivas)
# ============================================================================

class ToolExecutionRequest(BaseModel):
    """Request base para execução de ferramenta consultiva."""
    
    client_id: str = Field(
        description="ID do cliente",
        examples=["cli_abc123"]
    )
    context_override: dict | None = Field(
        default=None,
        description="Contexto customizado (sobrescreve dados do cliente)"
    )
    async_mode: bool = Field(
        default=False,
        description="Execução assíncrona (webhook quando completo)"
    )
    webhook_url: str | None = None


class SwotRequest(ToolExecutionRequest):
    """Request para análise SWOT."""
    pass  # Usa contexto do cliente


class FiveWhysRequest(ToolExecutionRequest):
    """Request para 5 Whys."""
    
    problem_statement: str = Field(
        min_length=10,
        description="Descrição do problema a ser analisado",
        examples=["Baixa produtividade no setor de dobra (150t/mês atual vs 250t/mês meta)"]
    )


class KpiDefinitionRequest(ToolExecutionRequest):
    """Request para definição de KPIs."""
    
    perspective: Literal["financial", "customer", "process", "learning"] | None = Field(
        default=None,
        description="Perspectiva BSC específica (None = todas)"
    )


# ============================================================================
# REPORTS
# ============================================================================

class GeneratePdfRequest(BaseModel):
    """Request para gerar PDF."""
    
    diagnostic_id: str | None = Field(
        default=None,
        description="ID do diagnóstico (obrigatório para PDF diagnóstico)"
    )
    client_id: str | None = Field(
        default=None,
        description="ID do cliente (alternativa a diagnostic_id)"
    )
    report_type: Literal["diagnostic_full", "diagnostic_perspective", "executive_summary"] = Field(
        default="diagnostic_full",
        description="Tipo de relatório PDF"
    )
    perspective: Literal["financial", "customer", "process", "learning"] | None = Field(
        default=None,
        description="Perspectiva específica (obrigatório se report_type=diagnostic_perspective)"
    )
    format_style: Literal["professional", "compact"] = Field(
        default="professional",
        description="Estilo de formatação"
    )
    async_mode: bool = False
    webhook_url: str | None = None


class GenerateCsvRequest(BaseModel):
    """Request para gerar CSV."""
    
    export_type: Literal["clients_list", "diagnostics_list", "recommendations"] = Field(
        description="Tipo de export CSV"
    )
    filters: dict | None = Field(
        default=None,
        description="Filtros (sector, tier, phase, etc)",
        examples=[{"sector": "Manufatura", "tier": "professional"}]
    )


# ============================================================================
# WEBHOOKS
# ============================================================================

class RegisterWebhookRequest(BaseModel):
    """Request para registrar webhook."""
    
    url: str = Field(
        description="URL endpoint para receber webhooks",
        examples=["https://cliente.com/webhooks/bsc-events"]
    )
    events: list[str] = Field(
        min_length=1,
        description="Lista de eventos para escutar",
        examples=[
            ["diagnostic.completed", "tool.executed"],
            ["report.generated", "client.phase_changed"]
        ]
    )
    secret: str | None = Field(
        default=None,
        description="Secret para HMAC signature verification (recomendado)",
        examples=["whsec_abc123def456"]
    )
    is_active: bool = True


# ============================================================================
# ADMIN
# ============================================================================

class CreateAPIKeyRequest(BaseModel):
    """Request para criar API key (admin endpoint)."""
    
    client_id: str | None = None
    tier: Literal["free", "professional", "enterprise"] = "free"
    permissions: list[str] = ["read", "write"]
    environment: Literal["live", "test"] = "live"
    expires_in_days: int | None = Field(
        default=None,
        description="Dias até expiração (None = sem expiração)",
        examples=[30, 90, 365]
    )

