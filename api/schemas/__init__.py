"""Schemas Pydantic para API REST (requests + responses).

Fase: 4.3 - Integration APIs
"""

from api.schemas.requests import *  # noqa: F403
from api.schemas.responses import *  # noqa: F403

# Exportar explicitamente os principais
__all__ = [
    # Requests
    "CreateClientRequest",
    "UpdateClientRequest",
    "CreateDiagnosticRequest",
    "ToolExecutionRequest",
    "SwotRequest",
    "FiveWhysRequest",
    "KpiDefinitionRequest",
    "GeneratePdfRequest",
    "GenerateCsvRequest",
    "RegisterWebhookRequest",
    "CreateAPIKeyRequest",
    
    # Responses
    "ErrorResponse",
    "SuccessResponse",
    "ClientResponse",
    "ClientListResponse",
    "ClientSummaryResponse",
    "DiagnosticResponse",
    "DiagnosticCompleteResponse",
    "PerspectiveResponse",
    "ToolExecutionResponse",
    "SwotResponse",
    "FiveWhysResponse",
    "KpiDefinitionResponse",
    "ToolsListResponse",
    "ReportResponse",
    "WebhookResponse",
    "WebhookListResponse",
    "WebhookTestResponse",
    "APIKeyResponse",
    "APIKeyListResponse",
]
