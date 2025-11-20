"""Testes E2E para endpoints de feedback.

Valida que os endpoints retornam dados corretos
e seguem contratos de API.

Fase: 4.5 - Feedback Collection System
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from api.main import app
from fastapi.testclient import TestClient

from src.memory.schemas import Feedback


@pytest.fixture
def client():
    """TestClient para API."""
    return TestClient(app)


@pytest.fixture
def mock_api_key():
    """API key válida para testes."""
    return "bsc_test_valid"


@pytest.fixture
def mock_feedback_service():
    """Mock do FeedbackService para testes."""
    service = Mock()

    # Mock collect_feedback
    service.collect_feedback = Mock(return_value="fb_abc123")

    # Mock get_feedback
    feedback = Feedback(
        rating=5,
        comment="Excelente diagnóstico!",
        diagnostic_id="diag_123",
        user_id="user_456",
        phase="discovery",
        created_at=datetime.now(timezone.utc),
        metadata={},
    )
    service.get_feedback = Mock(return_value=feedback)

    # Mock list_feedback
    feedbacks = [
        Feedback(
            rating=5,
            comment="Comentário 1",
            diagnostic_id="diag_123",
            user_id="user_456",
            phase="discovery",
            created_at=datetime.now(timezone.utc),
            metadata={"_feedback_id": "fb_1"},
        ),
        Feedback(
            rating=4,
            comment="Comentário 2",
            diagnostic_id="diag_123",
            user_id="user_456",
            phase="discovery",
            created_at=datetime.now(timezone.utc),
            metadata={"_feedback_id": "fb_2"},
        ),
    ]
    service.list_feedback = Mock(return_value=feedbacks)

    # Mock get_feedback_stats
    service.get_feedback_stats = Mock(
        return_value={
            "total_count": 10,
            "avg_rating": 4.2,
            "positive_count": 7,
            "negative_count": 1,
            "neutral_count": 2,
            "rating_distribution": {1: 0, 2: 1, 3: 2, 4: 4, 5: 3},
        }
    )

    return service


def test_create_feedback_endpoint(client, mock_api_key, mock_feedback_service):
    """POST /feedback deve criar novo feedback."""
    with patch("api.routers.feedback.get_feedback_service", return_value=mock_feedback_service):
        response = client.post(
            "/api/v1/feedback",
            headers={"X-API-Key": mock_api_key},
            json={
                "rating": 5,
                "comment": "Excelente diagnóstico!",
                "diagnostic_id": "diag_123",
                "phase": "discovery",
            },
        )

    assert response.status_code == 201
    data = response.json()

    # Verificar estrutura da resposta
    assert "feedback_id" in data
    assert data["rating"] == 5
    assert data["comment"] == "Excelente diagnóstico!"
    assert data["diagnostic_id"] == "diag_123"
    assert "user_id" in data
    assert "created_at" in data

    # Verificar que service foi chamado
    assert mock_feedback_service.collect_feedback.called


def test_create_feedback_validates_rating_range(client, mock_api_key):
    """POST /feedback deve validar rating entre 1-5."""
    response = client.post(
        "/api/v1/feedback",
        headers={"X-API-Key": mock_api_key},
        json={"rating": 6, "diagnostic_id": "diag_123", "phase": "discovery"},  # Inválido (> 5)
    )

    assert response.status_code == 422  # Validation error


def test_create_feedback_validates_required_fields(client, mock_api_key):
    """POST /feedback deve validar campos obrigatórios."""
    # Sem diagnostic_id
    response = client.post(
        "/api/v1/feedback",
        headers={"X-API-Key": mock_api_key},
        json={"rating": 5, "phase": "discovery"},
    )

    assert response.status_code == 422  # Validation error


def test_get_feedback_endpoint(client, mock_api_key, mock_feedback_service):
    """GET /feedback/{feedback_id} deve retornar feedback específico."""
    with patch("api.routers.feedback.get_feedback_service", return_value=mock_feedback_service):
        response = client.get("/api/v1/feedback/fb_abc123", headers={"X-API-Key": mock_api_key})

    assert response.status_code == 200
    data = response.json()

    # Verificar estrutura da resposta
    assert data["feedback_id"] == "fb_abc123"
    assert data["rating"] == 5
    assert data["comment"] == "Excelente diagnóstico!"
    assert data["diagnostic_id"] == "diag_123"

    # Verificar que service foi chamado
    assert mock_feedback_service.get_feedback.called


def test_get_feedback_returns_404_when_not_found(client, mock_api_key):
    """GET /feedback/{feedback_id} deve retornar 404 quando não encontrado."""
    mock_service = Mock()
    mock_service.get_feedback = Mock(return_value=None)

    # Mock autenticação
    mock_auth = {"api_key_id": "test_key", "user_id": "user_test"}

    with (
        patch("api.routers.feedback.get_feedback_service", return_value=mock_service),
        patch("api.routers.feedback.verify_api_key", return_value=mock_auth),
    ):
        response = client.get(
            "/api/v1/feedback/fb_nonexistent", headers={"X-API-Key": mock_api_key}
        )

    assert response.status_code == 404
    response_json = response.json()
    assert "detail" in response_json, f"Response JSON: {response_json}"
    assert "não encontrado" in response_json["detail"].lower()


def test_list_feedback_endpoint(client, mock_api_key, mock_feedback_service):
    """GET /feedback deve listar feedbacks com filtros."""
    with patch("api.routers.feedback.get_feedback_service", return_value=mock_feedback_service):
        response = client.get(
            "/api/v1/feedback",
            headers={"X-API-Key": mock_api_key},
            params={"diagnostic_id": "diag_123", "rating_min": 4},
        )

    assert response.status_code == 200
    data = response.json()

    # Verificar estrutura da resposta
    assert "feedbacks" in data
    assert "total" in data
    assert len(data["feedbacks"]) == 2
    assert data["total"] == 2

    # Verificar que service foi chamado com filtros corretos
    assert mock_feedback_service.list_feedback.called
    call_kwargs = mock_feedback_service.list_feedback.call_args.kwargs
    assert call_kwargs["diagnostic_id"] == "diag_123"
    assert call_kwargs["rating_min"] == 4


def test_list_feedback_validates_rating_filters(client, mock_api_key):
    """GET /feedback deve validar que rating_min <= rating_max."""
    response = client.get(
        "/api/v1/feedback",
        headers={"X-API-Key": mock_api_key},
        params={"rating_min": 5, "rating_max": 3},  # Inválido (min > max)
    )

    assert response.status_code == 400
    assert "rating_min não pode ser maior" in response.json()["detail"].lower()


def test_feedback_stats_endpoint(client, mock_api_key, mock_feedback_service):
    """GET /feedback/stats/summary deve retornar estatísticas agregadas."""
    with patch("api.routers.feedback.get_feedback_service", return_value=mock_feedback_service):
        response = client.get(
            "/api/v1/feedback/stats/summary",
            headers={"X-API-Key": mock_api_key},
            params={"diagnostic_id": "diag_123"},
        )

    assert response.status_code == 200
    data = response.json()

    # Verificar estrutura da resposta
    assert "total_count" in data
    assert "avg_rating" in data
    assert "positive_count" in data
    assert "negative_count" in data
    assert "neutral_count" in data
    assert "rating_distribution" in data

    # Verificar valores
    assert data["total_count"] == 10
    assert data["avg_rating"] == 4.2
    assert data["positive_count"] == 7
    assert data["negative_count"] == 1

    # Verificar que service foi chamado
    assert mock_feedback_service.get_feedback_stats.called


def test_feedback_endpoints_require_authentication(client):
    """Endpoints de feedback devem exigir autenticação."""
    # POST sem API key
    response = client.post(
        "/api/v1/feedback", json={"rating": 5, "diagnostic_id": "diag_123", "phase": "discovery"}
    )
    assert response.status_code == 401

    # GET sem API key
    response = client.get("/api/v1/feedback/fb_123")
    assert response.status_code == 401

    # GET list sem API key
    response = client.get("/api/v1/feedback")
    assert response.status_code == 401

    # GET stats sem API key
    response = client.get("/api/v1/feedback/stats/summary")
    assert response.status_code == 401
