"""Testes unitários para NotificationService.

Valida funcionalidade do serviço de notificações:
- Criação de notificações
- Marcação como lida
- Busca e listagem com filtros
- Estatísticas agregadas

Fase: 4.7 - Notification System
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from api.services.notification_service import NotificationService
from src.memory.schemas import Notification


@pytest.fixture
def mock_mem0_client():
    """Mock do MemoryClient do Mem0."""
    return Mock()


@pytest.fixture
def notification_service(mock_mem0_client):
    """Instância de NotificationService com Mem0 mockado."""
    return NotificationService(mem0_client=mock_mem0_client)


@pytest.fixture
def valid_notification():
    """Notificação válida para testes."""
    return Notification(
        type="diagnostic_completed",
        user_id="user_test_123",
        diagnostic_id="diag_abc456",
        title="Diagnóstico BSC Pronto",
        message="Seu diagnóstico BSC completo está disponível para aprovação.",
        priority="high"
    )


# ============================================================================
# TESTES UNITÁRIOS - create_notification()
# ============================================================================


def test_create_notification_returns_notification_id(notification_service, valid_notification, mock_mem0_client):
    """create_notification deve retornar notification_id quando sucesso."""
    # Mock Mem0 response
    mock_mem0_client.add = Mock(return_value={"id": "mem0_id_123"})
    
    # Executar
    notification_id = notification_service.create_notification(valid_notification)
    
    # Validar
    assert notification_id == valid_notification.id
    assert notification_id.startswith("notif_")
    mock_mem0_client.add.assert_called_once()


def test_create_notification_validates_user_id_too_short(notification_service, valid_notification):
    """create_notification deve validar user_id mínimo 3 caracteres."""
    # Notification com user_id curto
    valid_notification.user_id = "ab"  # < 3 chars
    
    # Executar e validar erro
    with pytest.raises(ValueError, match="user_id inválido"):
        notification_service.create_notification(valid_notification)


def test_create_notification_validates_title_too_short(notification_service, valid_notification):
    """create_notification deve validar title mínimo 5 caracteres."""
    # Notification com title curto
    valid_notification.title = "Test"  # < 5 chars
    
    # Executar e validar erro
    with pytest.raises(ValueError, match="title inválido"):
        notification_service.create_notification(valid_notification)


def test_create_notification_validates_message_too_short(notification_service, valid_notification):
    """create_notification deve validar message mínimo 10 caracteres."""
    # Notification com message curta
    valid_notification.message = "Short msg"  # < 10 chars
    
    # Executar e validar erro
    with pytest.raises(ValueError, match="message inválido"):
        notification_service.create_notification(valid_notification)


# ============================================================================
# TESTES UNITÁRIOS - mark_as_read()
# ============================================================================


def test_mark_as_read_returns_true_when_found(notification_service, mock_mem0_client):
    """mark_as_read deve retornar True quando notificação encontrada."""
    # Mock Mem0 search e update
    mock_mem0_client.search = Mock(return_value=[
        {
            "id": "mem0_id_123",
            "metadata": {
                "notification_id": "notif_test_123",
                "status": "unread"
            }
        }
    ])
    mock_mem0_client.update = Mock()
    
    # Executar
    success = notification_service.mark_as_read("notif_test_123")
    
    # Validar
    assert success is True
    mock_mem0_client.search.assert_called_once()
    mock_mem0_client.update.assert_called_once()


def test_mark_as_read_returns_false_when_not_found(notification_service, mock_mem0_client):
    """mark_as_read deve retornar False quando notificação não encontrada."""
    # Mock Mem0 search vazio
    mock_mem0_client.search = Mock(return_value=[])
    
    # Executar
    success = notification_service.mark_as_read("notif_nonexistent")
    
    # Validar
    assert success is False


# ============================================================================
# TESTES UNITÁRIOS - get_notification()
# ============================================================================


def test_get_notification_returns_notification_when_found(notification_service, mock_mem0_client):
    """get_notification deve retornar Notification quando encontrada."""
    # Mock Mem0 search
    mock_mem0_client.search = Mock(return_value=[
        {
            "id": "mem0_id_123",
            "memory": "Diagnóstico Pronto: Seu diagnóstico BSC está disponível.",
            "metadata": {
                "notification_id": "notif_test_123",
                "type": "diagnostic_completed",
                "user_id": "user_123",
                "diagnostic_id": "diag_abc",
                "status": "unread",
                "priority": "high",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "read_at": ""
            }
        }
    ])
    
    # Executar
    notification = notification_service.get_notification("notif_test_123")
    
    # Validar
    assert notification is not None
    assert isinstance(notification, Notification)
    assert notification.id == "notif_test_123"
    assert notification.type == "diagnostic_completed"
    assert notification.title == "Diagnóstico Pronto"


def test_get_notification_returns_none_when_not_found(notification_service, mock_mem0_client):
    """get_notification deve retornar None quando não encontrada."""
    # Mock Mem0 search vazio
    mock_mem0_client.search = Mock(return_value=[])
    
    # Executar
    notification = notification_service.get_notification("notif_nonexistent")
    
    # Validar
    assert notification is None


# ============================================================================
# TESTES UNITÁRIOS - list_notifications()
# ============================================================================


def test_list_notifications_returns_list(notification_service, mock_mem0_client):
    """list_notifications deve retornar lista de notificações."""
    # Mock Mem0 search com 3 notificações
    mock_mem0_client.search = Mock(return_value=[
        {
            "id": f"mem0_id_{i}",
            "memory": f"Título {i}: Mensagem da notificação {i}.",
            "metadata": {
                "notification_id": f"notif_test_{i}",
                "type": "diagnostic_completed",
                "user_id": "user_123",
                "diagnostic_id": f"diag_{i}",
                "status": "unread" if i % 2 == 0 else "read",
                "priority": "high",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "read_at": ""
            }
        }
        for i in range(3)
    ])
    
    # Executar
    notifications = notification_service.list_notifications(user_id="user_123")
    
    # Validar
    assert isinstance(notifications, list)
    assert len(notifications) == 3
    assert all(isinstance(n, Notification) for n in notifications)


def test_list_notifications_filters_by_user_id(notification_service, mock_mem0_client):
    """list_notifications deve passar user_id no filtro Mem0."""
    mock_mem0_client.search = Mock(return_value=[])
    
    # Executar
    notification_service.list_notifications(user_id="user_specific")
    
    # Validar filtro passado
    call_args = mock_mem0_client.search.call_args
    filters = call_args[1]["filters"]
    assert {"user_id": "user_specific"} in filters["AND"]


def test_list_notifications_filters_by_status(notification_service, mock_mem0_client):
    """list_notifications deve passar status no filtro Mem0."""
    mock_mem0_client.search = Mock(return_value=[])
    
    # Executar
    notification_service.list_notifications(user_id="user_123", status_filter="unread")
    
    # Validar filtro passado
    call_args = mock_mem0_client.search.call_args
    filters = call_args[1]["filters"]
    assert {"status": "unread"} in filters["AND"]

