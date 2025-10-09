"""
Testes para o módulo de retrieval.
"""
import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.rag.retriever import BSCRetriever
from src.rag.base_vector_store import SearchResult


class TestBSCRetriever:
    """Testes para BSCRetriever."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock do vector store."""
        mock_store = MagicMock()
        mock_store.hybrid_search.return_value = [
            SearchResult(
                id="doc1",
                content="Test content 1",
                metadata={"source": "test.pdf", "page": 1},
                score=0.9
            ),
            SearchResult(
                id="doc2",
                content="Test content 2",
                metadata={"source": "test.pdf", "page": 2},
                score=0.8
            )
        ]
        mock_store.vector_search.return_value = [
            SearchResult(
                id="doc1",
                content="Test content 1",
                metadata={"source": "test.pdf", "page": 1},
                score=0.9
            )
        ]
        return mock_store
    
    @pytest.fixture
    def mock_embedding_manager(self):
        """Mock do embedding manager."""
        mock_em = MagicMock()
        mock_em.embed_text.return_value = np.array([0.1, 0.2, 0.3])
        mock_em.embedding_dim = 3
        mock_em.provider = "openai"
        return mock_em
    
    @pytest.fixture
    def mock_cohere_reranker(self):
        """Mock do Cohere reranker."""
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [
            {
                "id": "doc1",
                "content": "Test content 1",
                "metadata": {"source": "test.pdf", "page": 1},
                "rerank_score": 0.95,
                "score": 0.9
            }
        ]
        return mock_reranker
    
    @pytest.fixture
    def retriever(self, mock_vector_store, mock_embedding_manager, mock_cohere_reranker):
        """Cria retriever com mocks."""
        with patch('src.rag.retriever.create_vector_store', return_value=mock_vector_store):
            with patch('src.rag.retriever.EmbeddingManager', return_value=mock_embedding_manager):
                with patch('src.rag.retriever.CohereReranker', return_value=mock_cohere_reranker):
                    retriever = BSCRetriever()
                    return retriever
    
    def test_init(self, retriever):
        """Testa inicialização do retriever."""
        assert retriever.vector_store is not None
        assert retriever.embedding_manager is not None
        assert retriever.cohere_reranker is not None
        assert retriever.fusion_reranker is not None
    
    def test_retrieve_hybrid_with_rerank(self, retriever, mock_embedding_manager):
        """Testa retrieval híbrido com re-ranking."""
        results = retriever.retrieve(
            query="test query",
            k=5,
            use_rerank=True,
            use_hybrid=True
        )
        
        # Verifica se embed_text foi chamado
        mock_embedding_manager.embed_text.assert_called_once_with("test query")
        
        # Verifica se hybrid_search foi chamado
        retriever.vector_store.hybrid_search.assert_called_once()
        
        # Verifica se rerank foi chamado
        retriever.cohere_reranker.rerank.assert_called_once()
        
        # Verifica resultados
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_retrieve_vector_only(self, retriever):
        """Testa retrieval apenas vetorial."""
        results = retriever.retrieve(
            query="test query",
            k=5,
            use_rerank=False,
            use_hybrid=False
        )
        
        # Verifica se vector_search foi chamado
        retriever.vector_store.vector_search.assert_called_once()
        
        # Verifica se rerank NÃO foi chamado
        retriever.cohere_reranker.rerank.assert_not_called()
        
        assert len(results) > 0
    
    def test_retrieve_with_filters(self, retriever):
        """Testa retrieval com filtros."""
        filters = {"source": "kaplan.pdf"}
        
        results = retriever.retrieve(
            query="test query",
            k=5,
            filters=filters
        )
        
        # Verifica se filtros foram passados
        call_args = retriever.vector_store.hybrid_search.call_args
        assert call_args[1]["filters"] == filters
    
    def test_retrieve_with_context(self, retriever):
        """Testa retrieval com histórico de conversa."""
        conversation_history = [
            {"role": "user", "content": "previous query"},
            {"role": "assistant", "content": "previous response"}
        ]
        
        results = retriever.retrieve_with_context(
            query="current query",
            conversation_history=conversation_history,
            k=5
        )
        
        assert len(results) > 0
        
        # Verifica se embed_text foi chamado com query enriquecida
        call_args = retriever.embedding_manager.embed_text.call_args
        assert "current query" in call_args[0][0]
    
    def test_retrieve_multi_query(self, retriever, mock_embedding_manager):
        """Testa retrieval com múltiplas queries."""
        queries = ["query1", "query2", "query3"]
        
        results = retriever.retrieve_multi_query(queries, k=5)
        
        # Verifica se embed_text foi chamado para cada query
        assert mock_embedding_manager.embed_text.call_count == len(queries)
        
        # Verifica se RRF fusion foi aplicado
        assert len(results) > 0
    
    def test_retrieve_by_perspective(self, retriever):
        """Testa retrieval por perspectiva BSC."""
        perspectives = ["financeira", "cliente", "processos", "aprendizado"]
        
        for perspective in perspectives:
            results = retriever.retrieve_by_perspective(
                query="test query",
                perspective=perspective,
                k=5
            )
            
            assert len(results) > 0
            
            # Verifica se a query foi enriquecida com keywords da perspectiva
            call_args = retriever.embedding_manager.embed_text.call_args
            query_used = call_args[0][0]
            assert "test query" in query_used
    
    def test_format_context(self, retriever):
        """Testa formatação de contexto."""
        documents = [
            SearchResult(
                id="doc1",
                content="Content 1 with some text",
                metadata={"source": "test.pdf", "page": 1},
                score=0.9
            ),
            SearchResult(
                id="doc2",
                content="Content 2 with more text",
                metadata={"source": "test.pdf", "page": 2},
                score=0.8
            )
        ]
        
        context = retriever.format_context(documents, max_tokens=1000)
        
        assert isinstance(context, str)
        assert "Documento 1" in context
        assert "Documento 2" in context
        assert "test.pdf" in context
        assert "Content 1" in context
    
    def test_format_context_respects_max_tokens(self, retriever):
        """Testa que format_context respeita limite de tokens."""
        large_content = "x" * 10000  # Conteúdo muito grande
        
        documents = [
            SearchResult(
                id=f"doc{i}",
                content=large_content,
                metadata={"source": "test.pdf", "page": i},
                score=0.9
            )
            for i in range(10)
        ]
        
        context = retriever.format_context(documents, max_tokens=100)
        
        # Verifica que o contexto não ultrapassa o limite
        estimated_tokens = len(context) // 4
        assert estimated_tokens <= 100 * 1.5  # Margem de erro na estimativa

