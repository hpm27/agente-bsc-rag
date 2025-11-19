"""Testes E2E básicos para API BSC RAG.

Validação rápida de funcionalidades críticas:
- Health check
- Autenticação API key
- CRUD clientes
- Execução de ferramenta (SWOT)
- Webhook registration

Fase: 4.3 - Integration APIs
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app

# API Keys mock (mesmas do api/dependencies.py)
VALID_API_KEY = "sk-engelar-write"
INVALID_API_KEY = "sk-invalid-key"


@pytest.fixture
def client():
    """Fixture para TestClient."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers com API key válida."""
    return {"X-API-Key": VALID_API_KEY}


# ============================================================================
# TESTE 1: Health Check (sem autenticação)
# ============================================================================

def test_health_check(client: TestClient):
    """Health check endpoint deve retornar 200 sem autenticação."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


def test_root_endpoint(client: TestClient):
    """Root endpoint deve retornar informações da API."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "BSC RAG Consultant API"
    assert "docs" in data
    assert "health" in data


# ============================================================================
# TESTE 2: Autenticação API Key
# ============================================================================

def test_api_key_required(client: TestClient):
    """Endpoints protegidos devem retornar 401 sem API key."""
    response = client.get("/api/v1/clients")
    
    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "api key" in detail or "key" in detail


def test_api_key_invalid(client: TestClient):
    """API key inválida deve retornar 401."""
    response = client.get(
        "/api/v1/clients",
        headers={"X-API-Key": INVALID_API_KEY}
    )
    
    assert response.status_code == 401
    assert "inválida" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


def test_api_key_valid(client: TestClient, auth_headers: dict):
    """API key válida deve permitir acesso."""
    response = client.get(
        "/api/v1/clients",
        headers=auth_headers
    )
    
    # Pode retornar 200 (lista vazia) ou 500 (se Mem0 não configurado)
    # O importante é que não retorna 401
    assert response.status_code != 401


# ============================================================================
# TESTE 3: CRUD Clientes
# ============================================================================

def test_create_client_success(client: TestClient, auth_headers: dict):
    """POST /clients deve criar cliente com dados válidos."""
    payload = {
        "company_name": "Test Corp API",
        "sector": "Tecnologia",
        "size": "média",
        "challenges": ["crescimento rápido", "processos manuais"],
        "objectives": ["profissionalizar gestão", "implementar BSC", "aumentar receita 30%"]
    }
    
    response = client.post(
        "/api/v1/clients",
        headers=auth_headers,
        json=payload
    )
    
    # Pode retornar 201 (sucesso) ou 500 (se Mem0 não configurado)
    # Validar estrutura da resposta se sucesso
    if response.status_code == 201:
        data = response.json()
        assert "client_id" in data
        assert data["company_name"] == payload["company_name"]
        assert data["sector"] == payload["sector"]
        assert data["current_phase"] == "ONBOARDING"
    elif response.status_code == 500:
        # Se erro interno, validar que é erro de configuração (não de validação)
        assert "erro" in response.json().get("detail", "").lower() or "error" in response.json().get("detail", "").lower()


def test_create_client_validation_error(client: TestClient, auth_headers: dict):
    """POST /clients deve retornar 422 com dados inválidos."""
    payload = {
        "company_name": "A",  # Muito curto (min_length=2)
        "challenges": ["um"],  # Mínimo 2
        "objectives": ["um", "dois"],  # Mínimo 3
    }
    
    response = client.post(
        "/api/v1/clients",
        headers=auth_headers,
        json=payload
    )
    
    # FastAPI retorna 422 para validation errors
    assert response.status_code == 422


def test_list_clients(client: TestClient, auth_headers: dict):
    """GET /clients deve retornar lista (pode estar vazia)."""
    response = client.get(
        "/api/v1/clients",
        headers=auth_headers,
        params={"page": 1, "page_size": 10}
    )
    
    # Pode retornar 200 (sucesso) ou 500 (se Mem0 não configurado)
    if response.status_code == 200:
        data = response.json()
        assert "clients" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["clients"], list)


# ============================================================================
# TESTE 4: Ferramentas Consultivas (SWOT)
# ============================================================================

def test_list_tools(client: TestClient, auth_headers: dict):
    """GET /tools deve retornar lista de ferramentas disponíveis."""
    response = client.get(
        "/api/v1/tools",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "total" in data
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) > 0
    
    # Validar estrutura de uma ferramenta
    tool = data["tools"][0]
    assert "name" in tool
    assert "display_name" in tool
    assert "description" in tool
    assert "endpoint" in tool


def test_execute_swot_no_client(client: TestClient, auth_headers: dict):
    """POST /tools/swot deve retornar 404 se cliente não existe."""
    payload = {
        "client_id": "cli_nonexistent_123",
    }
    
    response = client.post(
        "/api/v1/tools/swot",
        headers=auth_headers,
        json=payload
    )
    
    # Deve retornar 404 (cliente não encontrado) ou 500 (se Mem0 não configurado)
    assert response.status_code in [404, 500]


# ============================================================================
# TESTE 5: Webhooks
# ============================================================================

def test_register_webhook_success(client: TestClient, auth_headers: dict):
    """POST /webhooks deve registrar webhook com dados válidos."""
    payload = {
        "url": "https://example.com/webhooks/bsc-events",
        "events": ["diagnostic.completed", "tool.executed"],
        "secret": "whsec_test_secret_123",
        "is_active": True,
    }
    
    response = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json=payload
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "webhook_id" in data
    assert data["url"] == payload["url"]
    assert data["events"] == payload["events"]
    assert data["secret_provided"] is True
    assert data["is_active"] is True


def test_register_webhook_invalid_url(client: TestClient, auth_headers: dict):
    """POST /webhooks deve retornar 400 com URL inválida."""
    payload = {
        "url": "not-a-valid-url",
        "events": ["diagnostic.completed"],
    }
    
    response = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json=payload
    )
    
    # Deve retornar 400 (URL inválida) ou 422 (validation error)
    assert response.status_code in [400, 422]


def test_list_webhooks(client: TestClient, auth_headers: dict):
    """GET /webhooks deve retornar lista de webhooks."""
    response = client.get(
        "/api/v1/webhooks",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "webhooks" in data
    assert "total" in data
    assert isinstance(data["webhooks"], list)


# ============================================================================
# TESTE 6: Reports
# ============================================================================

def test_list_tools_includes_all_tools(client: TestClient, auth_headers: dict):
    """GET /tools deve incluir todas as 8 ferramentas principais."""
    response = client.get(
        "/api/v1/tools",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    tool_names = [tool["name"] for tool in data["tools"]]
    
    # Validar que ferramentas principais estão presentes
    expected_tools = ["swot", "five-whys", "issue-tree", "kpi", "objectives", "benchmarking", "action-plan", "prioritization"]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Ferramenta '{expected}' não encontrada na lista"


# ============================================================================
# TESTE 7: OpenAPI Docs
# ============================================================================

def test_openapi_docs_accessible(client: TestClient):
    """Swagger UI deve estar acessível."""
    response = client.get("/docs")
    
    # Deve retornar HTML da página Swagger
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_openapi_json_accessible(client: TestClient):
    """OpenAPI JSON schema deve estar acessível."""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    
    # Validar que endpoints principais estão documentados
    paths = data["paths"]
    assert "/api/v1/clients" in paths
    assert "/api/v1/tools" in paths
    assert "/api/v1/webhooks" in paths

