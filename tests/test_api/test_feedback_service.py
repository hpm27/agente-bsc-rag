"""Testes unitários para FeedbackService.

Valida coleta, armazenamento e análise de feedback no Mem0.

Fase: 4.5 - Feedback Collection System
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from api.services.feedback_service import FeedbackService
from src.memory.schemas import Feedback


@pytest.fixture
def mock_mem0_client():
    """Mock do Mem0 MemoryClient para testes."""
    client = Mock()
    
    # Mock para add()
    client.add = Mock()
    
    # Mock para get_all() - retorna lista direta
    client.get_all = Mock(return_value=[])
    
    # Mock para search() - retorna lista direta
    client.search = Mock(return_value=[])
    
    return client


@pytest.fixture
def feedback_service(mock_mem0_client):
    """FeedbackService com Mem0 mockado."""
    with patch("api.services.feedback_service.MemoryClient", return_value=mock_mem0_client):
        with patch("api.services.feedback_service.os.getenv", return_value="test_api_key"):
            service = FeedbackService()
            service.client = mock_mem0_client
            return service


@pytest.fixture
def sample_feedback():
    """Feedback de exemplo para testes."""
    return Feedback(
        rating=5,
        comment="Excelente diagnóstico!",
        diagnostic_id="diag_123",
        user_id="user_456",
        phase="discovery",
        metadata={"tools_used": ["swot"]}
    )


def test_collect_feedback_stores_in_mem0(feedback_service, mock_mem0_client, sample_feedback):
    """collect_feedback deve armazenar feedback no Mem0."""
    feedback_id = feedback_service.collect_feedback(sample_feedback)
    
    # Verificar que add foi chamado
    assert mock_mem0_client.add.called
    
    # Verificar que feedback_id foi retornado (UUID)
    assert feedback_id is not None
    assert len(feedback_id) == 36  # UUID tem 36 caracteres com hífens
    
    # Verificar argumentos do add
    call_args = mock_mem0_client.add.call_args
    assert call_args is not None
    assert "messages" in call_args.kwargs
    assert "user_id" in call_args.kwargs
    assert "metadata" in call_args.kwargs


def test_collect_feedback_without_comment(feedback_service, mock_mem0_client):
    """collect_feedback deve funcionar sem comment (apenas rating)."""
    feedback = Feedback(
        rating=4,
        diagnostic_id="diag_123",
        user_id="user_456",
        phase="discovery"
    )
    
    feedback_id = feedback_service.collect_feedback(feedback)
    
    assert feedback_id is not None
    assert mock_mem0_client.add.called
    
    # Verificar que message contém "Feedback rating:"
    call_args = mock_mem0_client.add.call_args
    messages = call_args.kwargs.get("messages", [])
    assert len(messages) > 0
    assert "Feedback rating:" in messages[0] or "4" in messages[0]


def test_get_feedback_returns_feedback(feedback_service, mock_mem0_client):
    """get_feedback deve retornar Feedback quando encontrado."""
    # Mock memória do Mem0
    memory = {
        "metadata": {
            "feedback_id": "fb_123",
            "diagnostic_id": "diag_123",
            "rating": 5,
            "phase": "discovery",
            "user_id": "user_456",
            "created_at": "2025-11-19T14:30:00Z"
        },
        "messages": [{"content": "Excelente diagnóstico!"}]
    }
    
    mock_mem0_client.get_all = Mock(return_value=[memory])
    
    feedback = feedback_service.get_feedback("fb_123", user_id="user_456")
    
    assert feedback is not None
    assert feedback.rating == 5
    assert feedback.diagnostic_id == "diag_123"
    assert feedback.comment == "Excelente diagnóstico!"


def test_get_feedback_returns_none_when_not_found(feedback_service, mock_mem0_client):
    """get_feedback deve retornar None quando feedback não encontrado."""
    mock_mem0_client.get_all = Mock(return_value=[])
    
    feedback = feedback_service.get_feedback("fb_nonexistent")
    
    assert feedback is None


def test_list_feedback_filters_by_diagnostic_id(feedback_service, mock_mem0_client):
    """list_feedback deve filtrar por diagnostic_id."""
    # Mock memórias - Mem0 retorna apenas memórias que matcham o filtro
    # Quando diagnostic_id="diag_123", Mem0 retorna apenas essa memória
    memories_filtered = [
        {
            "metadata": {
                "feedback_id": "fb_1",
                "diagnostic_id": "diag_123",
                "rating": 5,
                "phase": "discovery",
                "user_id": "user_456",
                "created_at": "2025-11-19T14:30:00Z",
                "memory_type": "feedback"
            },
            "messages": [{"content": "Comentário 1"}]
        }
    ]
    
    # Mock retorna apenas memórias filtradas (como Mem0 faria)
    mock_mem0_client.get_all = Mock(return_value=memories_filtered)
    
    feedbacks = feedback_service.list_feedback(diagnostic_id="diag_123")
    
    # Deve retornar apenas feedbacks com diagnostic_id="diag_123"
    assert len(feedbacks) == 1
    assert feedbacks[0].diagnostic_id == "diag_123"


def test_list_feedback_filters_by_rating(feedback_service, mock_mem0_client):
    """list_feedback deve filtrar por rating_min e rating_max."""
    # Mock memórias com ratings variados
    memories = [
        {
            "metadata": {
                "feedback_id": f"fb_{i}",
                "diagnostic_id": "diag_123",
                "rating": i,
                "phase": "discovery",
                "user_id": "user_456",
                "created_at": "2025-11-19T14:30:00Z"
            },
            "messages": [{"content": f"Comentário {i}"}]
        }
        for i in range(1, 6)  # Ratings 1-5
    ]
    
    mock_mem0_client.get_all = Mock(return_value=memories)
    
    # Filtrar ratings >= 4
    feedbacks = feedback_service.list_feedback(rating_min=4)
    
    assert len(feedbacks) == 2  # Ratings 4 e 5
    assert all(f.rating >= 4 for f in feedbacks)
    
    # Filtrar ratings <= 2
    feedbacks = feedback_service.list_feedback(rating_max=2)
    
    assert len(feedbacks) == 2  # Ratings 1 e 2
    assert all(f.rating <= 2 for f in feedbacks)


def test_get_feedback_stats_calculates_average(feedback_service, mock_mem0_client):
    """get_feedback_stats deve calcular média de ratings corretamente."""
    # Mock memórias com ratings variados
    memories = [
        {
            "metadata": {
                "feedback_id": f"fb_{i}",
                "diagnostic_id": "diag_123",
                "rating": i,
                "phase": "discovery",
                "user_id": "user_456",
                "created_at": "2025-11-19T14:30:00Z"
            },
            "messages": [{"content": f"Comentário {i}"}]
        }
        for i in [5, 5, 4, 3, 2]  # Ratings variados
    ]
    
    mock_mem0_client.get_all = Mock(return_value=memories)
    
    stats = feedback_service.get_feedback_stats(diagnostic_id="diag_123")
    
    assert stats["total_count"] == 5
    assert stats["avg_rating"] == 3.8  # (5+5+4+3+2)/5 = 3.8
    assert stats["positive_count"] == 3  # Ratings >= 4: 5, 5, 4 (3 positivos)
    assert stats["negative_count"] == 1  # Ratings <= 2: 2 (1 negativo)
    assert stats["neutral_count"] == 1  # Rating == 3: 3 (1 neutro)


def test_get_feedback_stats_handles_empty_list(feedback_service, mock_mem0_client):
    """get_feedback_stats deve retornar zeros quando não há feedbacks."""
    mock_mem0_client.get_all = Mock(return_value=[])
    
    stats = feedback_service.get_feedback_stats()
    
    assert stats["total_count"] == 0
    assert stats["avg_rating"] == 0.0
    assert stats["positive_count"] == 0
    assert stats["negative_count"] == 0
    assert stats["neutral_count"] == 0
    assert stats["rating_distribution"] == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


def test_memory_to_feedback_converts_correctly(feedback_service):
    """_memory_to_feedback deve converter memória Mem0 para Feedback corretamente."""
    memory = {
        "metadata": {
            "feedback_id": "fb_123",
            "diagnostic_id": "diag_123",
            "rating": 5,
            "phase": "discovery",
            "user_id": "user_456",
            "created_at": "2025-11-19T14:30:00Z",
            "memory_type": "feedback"
        },
        "messages": [{"content": "Excelente diagnóstico!"}]
    }
    
    feedback = feedback_service._memory_to_feedback(memory)
    
    assert feedback.rating == 5
    assert feedback.comment == "Excelente diagnóstico!"
    assert feedback.diagnostic_id == "diag_123"
    assert feedback.user_id == "user_456"
    assert feedback.phase == "discovery"
    assert "_feedback_id" in feedback.metadata
    assert feedback.metadata["_feedback_id"] == "fb_123"


def test_memory_to_feedback_handles_rating_only_message(feedback_service):
    """_memory_to_feedback deve tratar mensagem 'Feedback rating: X' corretamente."""
    memory = {
        "metadata": {
            "feedback_id": "fb_123",
            "diagnostic_id": "diag_123",
            "rating": 4,
            "phase": "discovery",
            "user_id": "user_456",
            "created_at": "2025-11-19T14:30:00Z"
        },
        "messages": [{"content": "Feedback rating: 4"}]
    }
    
    feedback = feedback_service._memory_to_feedback(memory)
    
    assert feedback.rating == 4
    assert feedback.comment is None  # Mensagem é apenas rating, não comment real


def test_sanitize_metadata_truncates_large_metadata(feedback_service):
    """_sanitize_metadata deve truncar metadata > 2000 chars."""
    # Criar metadata grande
    large_metadata = {
        "feedback_id": "fb_123",
        "diagnostic_id": "diag_123",
        "rating": 5,
        "phase": "discovery",
        "user_id": "user_456",
        "created_at": "2025-11-19T14:30:00Z",
        "memory_type": "feedback",
        "large_field": "X" * 3000  # Campo muito grande
    }
    
    sanitized = feedback_service._sanitize_metadata(large_metadata)
    
    # Verificar que foi truncado ou removido
    import json
    size = len(json.dumps(sanitized, separators=(",", ":"), ensure_ascii=False))
    assert size <= 2000 or "large_field" not in sanitized


def test_list_feedback_handles_mem0_dict_response(feedback_service, mock_mem0_client):
    """list_feedback deve tratar retorno dict com 'results' do Mem0."""
    # Mock retorno dict com 'results' (formato alternativo Mem0)
    memory = {
        "metadata": {
            "feedback_id": "fb_123",
            "diagnostic_id": "diag_123",
            "rating": 5,
            "phase": "discovery",
            "user_id": "user_456",
            "created_at": "2025-11-19T14:30:00Z"
        },
        "messages": [{"content": "Comentário"}]
    }
    
    mock_mem0_client.get_all = Mock(return_value={"results": [memory]})
    
    feedbacks = feedback_service.list_feedback()
    
    assert len(feedbacks) == 1
    assert feedbacks[0].rating == 5

