"""Testes E2E para endpoints de notificações.

Valida API REST de notificações:
- POST /api/v1/notifications - Criar notificação
- GET /api/v1/notifications/{id} - Buscar notificação
- PATCH /api/v1/notifications/{id}/read - Marcar como lida
- GET /api/v1/notifications - Listar notificações

Fase: 4.7 - Notification System
"""

from unittest.mock import Mock

import pytest
from api.dependencies import verify_api_key
from api.main import app
from fastapi.testclient import TestClient

from src.memory.schemas import Notification


# Override verify_api_key dependency para testes
async def override_verify_api_key():
    """Mock de autenticação para testes."""
    return {"api_key_id": "test_key", "user_id": "user_test"}


@pytest.fixture
def client():
    """Cliente de teste da API com dependency overrides."""
    # Configurar override ANTES de criar TestClient
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    # Criar client
    test_client = TestClient(app)

    yield test_client

    # Limpar overrides após teste
    app.dependency_overrides = {}


@pytest.fixture
def mock_api_key():
    """API key mockada para autenticação."""
    return "test_api_key_123"


@pytest.fixture
def sample_notification():
    """Notificação de exemplo para testes."""
    return Notification(
        id="notif_test_123",
        type="diagnostic_completed",
        user_id="user_test_123",
        diagnostic_id="diag_abc456",
        title="Diagnóstico BSC Pronto",
        message="Seu diagnóstico BSC completo está disponível para aprovação. Perspectivas: Financeira, Clientes, Processos, Aprendizado.",
        status="unread",
        priority="high",
        metadata={"perspectives_count": 4},
    )


# ============================================================================
# TESTES E2E - POST /api/v1/notifications
# ============================================================================


def test_create_notification_returns_201(client, mock_api_key):
    """POST /api/v1/notifications deve retornar 201 quando sucesso."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.create_notification = Mock(return_value="notif_new_123")

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.post(
            "/api/v1/notifications",
            headers={"X-API-Key": mock_api_key},
            json={
                "type": "diagnostic_completed",
                "user_id": "user_test_123",
                "diagnostic_id": "diag_abc",
                "title": "Diagnóstico Pronto",
                "message": "Seu diagnóstico BSC está disponível.",
                "priority": "high",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "diagnostic_completed"


def test_create_notification_validates_title_too_short(client, mock_api_key):
    """POST /api/v1/notifications deve validar title mínimo 5 caracteres."""
    response = client.post(
        "/api/v1/notifications",
        headers={"X-API-Key": mock_api_key},
        json={
            "type": "diagnostic_completed",
            "user_id": "user_test_123",
            "title": "Test",  # < 5 chars
            "message": "Mensagem válida com mais de 10 caracteres.",
            "priority": "high",
        },
    )

    # 422 = Unprocessable Entity (validação Pydantic)
    assert response.status_code == 422


# ============================================================================
# TESTES E2E - GET /api/v1/notifications/{notification_id}
# ============================================================================


def test_get_notification_returns_200(client, mock_api_key, sample_notification):
    """GET /api/v1/notifications/{id} deve retornar 200 quando encontrada."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.get_notification = Mock(return_value=sample_notification)

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.get(
            "/api/v1/notifications/notif_test_123", headers={"X-API-Key": mock_api_key}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "notif_test_123"
    assert data["title"] == "Diagnóstico BSC Pronto"


def test_get_notification_returns_404_when_not_found(client, mock_api_key):
    """GET /api/v1/notifications/{id} deve retornar 404 quando não encontrada."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.get_notification = Mock(return_value=None)

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.get(
            "/api/v1/notifications/notif_nonexistent", headers={"X-API-Key": mock_api_key}
        )

    assert response.status_code == 404
    assert "não encontrada" in response.json()["detail"].lower()


# ============================================================================
# TESTES E2E - PATCH /api/v1/notifications/{notification_id}/read
# ============================================================================


def test_mark_as_read_returns_200(client, mock_api_key):
    """PATCH /api/v1/notifications/{id}/read deve retornar 200 quando sucesso."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.mark_as_read = Mock(return_value=True)

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.patch(
            "/api/v1/notifications/notif_test_123/read", headers={"X-API-Key": mock_api_key}
        )

    assert response.status_code == 200
    data = response.json()
    assert "marcada como lida" in data["message"].lower()
    assert data["notification_id"] == "notif_test_123"


def test_mark_as_read_returns_404_when_not_found(client, mock_api_key):
    """PATCH /api/v1/notifications/{id}/read deve retornar 404 quando não encontrada."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.mark_as_read = Mock(return_value=False)

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.patch(
            "/api/v1/notifications/notif_nonexistent/read", headers={"X-API-Key": mock_api_key}
        )

    assert response.status_code == 404


# ============================================================================
# TESTES E2E - GET /api/v1/notifications (list)
# ============================================================================


def test_list_notifications_returns_200(client, mock_api_key, sample_notification):
    """GET /api/v1/notifications deve retornar 200 com lista."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.list_notifications = Mock(return_value=[sample_notification])

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.get(
            "/api/v1/notifications",
            headers={"X-API-Key": mock_api_key},
            params={"user_id": "user_test_123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert data["total"] == 1
    assert len(data["notifications"]) == 1


def test_list_notifications_filters_work(client, mock_api_key):
    """GET /api/v1/notifications deve aplicar filtros corretamente."""
    from unittest.mock import patch

    mock_service = Mock()
    mock_service.list_notifications = Mock(return_value=[])

    with patch("api.routers.notifications.get_notification_service", return_value=mock_service):
        response = client.get(
            "/api/v1/notifications",
            headers={"X-API-Key": mock_api_key},
            params={
                "user_id": "user_test_123",
                "status_filter": "unread",
                "priority_filter": "high",
            },
        )

    assert response.status_code == 200
    # Verificar que list_notifications foi chamado com filtros corretos
    mock_service.list_notifications.assert_called_once()
    call_kwargs = mock_service.list_notifications.call_args[1]
    assert call_kwargs["user_id"] == "user_test_123"
    assert call_kwargs["status_filter"] == "unread"
    assert call_kwargs["priority_filter"] == "high"
