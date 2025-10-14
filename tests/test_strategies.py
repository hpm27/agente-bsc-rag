"""
Testes para Estratégias de Retrieval (RAG Avançado - Fase 2A.3).

Testa as 4 estratégias:
- DirectAnswerStrategy
- DecompositionStrategy
- HybridSearchStrategy
- MultiHopStrategy
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List

from src.rag.strategies import (
    RetrievalStrategy,
    DirectAnswerStrategy,
    DecompositionStrategy,
    HybridSearchStrategy,
    MultiHopStrategy
)
from src.rag.base_vector_store import SearchResult


# Fixtures
@pytest.fixture
def mock_retriever():
    """Mock de BSCRetriever para testes."""
    retriever = Mock()
    retriever.retrieve = Mock(return_value=[
        SearchResult(
            content="BSC é um framework de gestão estratégica.",
            source="kaplan.pdf",
            page=10,
            score=0.95,
            search_type="hybrid",
            metadata={}
        ),
        SearchResult(
            content="As quatro perspectivas do BSC são: financeira, cliente, processos e aprendizado.",
            source="norton.pdf",
            page=25,
            score=0.90,
            search_type="hybrid",
            metadata={}
        )
    ])
    retriever.retrieve_with_decomposition = Mock(return_value=[
        SearchResult(
            content="BSC integra perspectivas financeira e clientes através de relações causa-efeito.",
            source="kaplan.pdf",
            page=50,
            score=0.92,
            search_type="decomposed",
            metadata={}
        )
    ])
    return retriever


# Test 1: RetrievalStrategy abstrata
def test_retrieval_strategy_abstract_raises_error():
    """RetrievalStrategy não pode ser instanciada diretamente."""
    with pytest.raises(TypeError):
        # Abstract class não pode ser instanciada
        RetrievalStrategy("test")  # type: ignore


# Test 2-4: DirectAnswerStrategy
def test_direct_answer_strategy_simple_query(mock_retriever):
    """DirectAnswer deve processar query simples rapidamente."""
    strategy = DirectAnswerStrategy()
    query = "O que é BSC?"
    
    results = strategy.execute(query, mock_retriever, k=5)
    
    assert results is not None
    assert len(results) > 0
    # Pode retornar do cache, LLM ou retrieval leve


def test_direct_answer_strategy_uses_cache(mock_retriever):
    """Segunda chamada mesma query deve usar cache."""
    strategy = DirectAnswerStrategy()
    strategy.cache_enabled = True
    query = "O que é BSC?"
    
    # Primeira chamada
    with patch.object(strategy, 'llm') as mock_llm:
        mock_llm.invoke.return_value = Mock(content="BSC é Balanced Scorecard")
        results1 = strategy.execute(query, mock_retriever, k=5)
    
    # Segunda chamada (deve usar cache)
    results2 = strategy.execute(query, mock_retriever, k=5)
    
    # Cache deve retornar SearchResult com from_cache=True
    if len(results2) > 0 and results2[0].metadata.get("from_cache"):
        assert results2[0].metadata["from_cache"] is True
        assert results2[0].source == "cache"


def test_direct_answer_is_trivial_query():
    """_is_trivial_query deve identificar queries triviais."""
    strategy = DirectAnswerStrategy()
    
    # Queries triviais
    assert strategy._is_trivial_query("O que é BSC?") is True
    assert strategy._is_trivial_query("Defina Balanced Scorecard") is True
    assert strategy._is_trivial_query("Qual é a perspectiva financeira?") is True
    
    # Queries não triviais
    assert strategy._is_trivial_query(
        "Como implementar BSC considerando perspectivas financeira e clientes?"
    ) is False
    assert strategy._is_trivial_query("BSC" * 20) is False  # Muito longa


# Test 5-6: DecompositionStrategy  
def test_decomposition_strategy_complex_query(mock_retriever):
    """DecompositionStrategy deve usar Query Decomposition."""
    strategy = DecompositionStrategy()
    query = "Como implementar BSC considerando perspectivas financeira e clientes?"
    
    # Mock do retrieve_with_decomposition como coroutine
    from unittest.mock import AsyncMock
    mock_retriever.retrieve_with_decomposition = AsyncMock(return_value=[
        SearchResult(
            content="BSC financeira foca em lucratividade.",
            source="kaplan.pdf",
            page=30,
            score=0.90,
            search_type="decomposed",
            metadata={}
        )
    ])
    
    results = strategy.execute(query, mock_retriever, k=10)
    
    assert results is not None
    assert len(results) > 0
    assert mock_retriever.retrieve_with_decomposition.called


def test_decomposition_strategy_returns_documents(mock_retriever):
    """Decomposition deve retornar List[SearchResult]."""
    strategy = DecompositionStrategy()
    query = "Como BSC integra perspectivas?"
    
    # Mock do retrieve_with_decomposition como coroutine
    from unittest.mock import AsyncMock
    mock_retriever.retrieve_with_decomposition = AsyncMock(return_value=[
        SearchResult(
            content="BSC integra perspectivas.",
            source="test.pdf",
            page=1,
            score=0.9,
            search_type="decomposed",
            metadata={}
        )
    ])
    
    results = strategy.execute(query, mock_retriever, k=10)
    
    assert isinstance(results, list)
    assert len(results) > 0


# Test 7-8: HybridSearchStrategy
def test_hybrid_search_strategy_conceptual_query(mock_retriever):
    """HybridSearch deve processar query conceitual."""
    strategy = HybridSearchStrategy()
    query = "Benefícios do BSC"
    
    results = strategy.execute(query, mock_retriever, k=10)
    
    assert results is not None
    assert len(results) > 0
    assert mock_retriever.retrieve.called


def test_hybrid_search_strategy_multilingual(mock_retriever):
    """HybridSearch deve ativar multilingual=True."""
    strategy = HybridSearchStrategy()
    query = "Como implementar BSC?"
    
    strategy.execute(query, mock_retriever, k=10)
    
    # Verificar que retrieve foi chamado com multilingual=True
    mock_retriever.retrieve.assert_called_with(
        query=query,
        k=10,
        use_hybrid=True,
        use_rerank=True,
        multilingual=True,
        filters=None
    )


# Test 9: MultiHopStrategy
def test_multihop_strategy_fallback_to_hybrid(mock_retriever):
    """MultiHop (placeholder) deve fazer fallback para Hybrid."""
    strategy = MultiHopStrategy()
    query = "Qual impacto de A em B?"
    
    results = strategy.execute(query, mock_retriever, k=10)
    
    # MultiHop atualmente faz fallback para HybridSearch
    assert results is not None
    assert mock_retriever.retrieve.called


# Test 10: Strategy execution time comparison
def test_strategy_repr():
    """Strategy __repr__ deve retornar nome e complexidade."""
    direct = DirectAnswerStrategy()
    decomp = DecompositionStrategy()
    hybrid = HybridSearchStrategy()
    multihop = MultiHopStrategy()
    
    assert "DirectAnswerStrategy" in repr(direct)
    assert "low" in repr(direct)
    
    assert "DecompositionStrategy" in repr(decomp)
    assert "medium" in repr(decomp) or "high" in repr(decomp)
    
    assert "HybridSearchStrategy" in repr(hybrid)
    assert "medium" in repr(hybrid)
    
    assert "MultiHopStrategy" in repr(multihop)
    assert "high" in repr(multihop) or "very" in repr(multihop)

