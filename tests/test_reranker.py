"""
Testes para o módulo de re-ranking.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

import pytest

from src.rag.reranker import CohereReranker, FusionReranker, HybridReranker


class TestCohereReranker:
    """Testes para CohereReranker."""

    @pytest.fixture
    def mock_cohere_client(self):
        """Mock do cliente Cohere."""
        mock_client = MagicMock()

        # Mock da resposta de rerank
        mock_result_1 = MagicMock()
        mock_result_1.index = 1
        mock_result_1.relevance_score = 0.95

        mock_result_2 = MagicMock()
        mock_result_2.index = 0
        mock_result_2.relevance_score = 0.85

        mock_response = MagicMock()
        mock_response.results = [mock_result_1, mock_result_2]

        mock_client.rerank.return_value = mock_response
        return mock_client

    @pytest.fixture
    def reranker(self, mock_cohere_client):
        """Cria reranker com mock."""
        with patch("src.rag.reranker.cohere.Client", return_value=mock_cohere_client):
            with patch("src.rag.reranker.settings") as mock_settings:
                mock_settings.cohere_api_key = "test-key"
                mock_settings.top_n_rerank = 5
                reranker = CohereReranker()
                return reranker

    def test_init(self, reranker):
        """Testa inicialização do reranker."""
        assert reranker.client is not None
        assert reranker.model == "rerank-multilingual-v3.0"

    def test_rerank_success(self, reranker):
        """Testa re-ranking bem sucedido."""
        documents = [
            {"id": "doc1", "content": "content 1", "metadata": {}, "score": 0.7},
            {"id": "doc2", "content": "content 2", "metadata": {}, "score": 0.8},
        ]

        reranked = reranker.rerank(query="test query", documents=documents, top_n=2)

        # Verifica se API foi chamada
        reranker.client.rerank.assert_called_once()

        # Verifica resultados
        assert len(reranked) == 2
        assert reranked[0]["id"] == "doc2"  # doc2 teve maior rerank_score
        assert "rerank_score" in reranked[0]
        assert reranked[0]["rerank_score"] == 0.95

    def test_rerank_empty_documents(self, reranker):
        """Testa re-ranking com lista vazia."""
        reranked = reranker.rerank(query="test query", documents=[], top_n=5)

        assert len(reranked) == 0
        reranker.client.rerank.assert_not_called()

    def test_rerank_with_error(self, reranker):
        """Testa comportamento quando API falha."""
        # Configura mock para lançar exceção
        reranker.client.rerank.side_effect = Exception("API Error")

        documents = [{"id": "doc1", "content": "content 1", "metadata": {}, "score": 0.7}]

        # Deve retornar documentos originais em caso de erro
        reranked = reranker.rerank(query="test query", documents=documents, top_n=5)

        assert len(reranked) == 1
        assert reranked[0]["id"] == "doc1"

    def test_rerank_with_scores(self, reranker):
        """Testa re-ranking com threshold de score."""
        documents = [
            {"id": "doc1", "content": "content 1", "metadata": {}, "score": 0.7},
            {"id": "doc2", "content": "content 2", "metadata": {}, "score": 0.8},
        ]

        # Configura mock para retornar scores específicos
        mock_result_1 = MagicMock()
        mock_result_1.index = 0
        mock_result_1.relevance_score = 0.6  # Abaixo do threshold

        mock_result_2 = MagicMock()
        mock_result_2.index = 1
        mock_result_2.relevance_score = 0.9  # Acima do threshold

        mock_response = MagicMock()
        mock_response.results = [mock_result_1, mock_result_2]
        reranker.client.rerank.return_value = mock_response

        filtered = reranker.rerank_with_scores(
            query="test query", documents=documents, threshold=0.7
        )

        # Apenas doc2 deve passar o threshold
        assert len(filtered) == 1
        assert filtered[0]["id"] == "doc2"


class TestFusionReranker:
    """Testes para FusionReranker (RRF)."""

    @pytest.fixture
    def reranker(self):
        """Cria fusion reranker."""
        return FusionReranker(k=60)

    def test_init(self, reranker):
        """Testa inicialização."""
        assert reranker.k == 60

    def test_fuse_single_list(self, reranker):
        """Testa fusão de uma única lista."""
        results = [
            [
                {"id": "doc1", "content": "c1", "metadata": {}, "source": "test.pdf", "page": 1},
                {"id": "doc2", "content": "c2", "metadata": {}, "source": "test.pdf", "page": 2},
            ]
        ]

        fused = reranker.fuse(results, top_n=5)

        assert len(fused) == 2
        assert "rrf_score" in fused[0]
        assert fused[0]["rrf_score"] > fused[1]["rrf_score"]

    def test_fuse_multiple_lists(self, reranker):
        """Testa fusão de múltiplas listas."""
        results = [
            [  # Lista 1
                {"id": "doc1", "content": "c1", "metadata": {}, "source": "test.pdf", "page": 1},
                {"id": "doc2", "content": "c2", "metadata": {}, "source": "test.pdf", "page": 2},
            ],
            [  # Lista 2
                {
                    "id": "doc2",
                    "content": "c2",
                    "metadata": {},
                    "source": "test.pdf",
                    "page": 2,
                },  # Aparece em ambas
                {"id": "doc3", "content": "c3", "metadata": {}, "source": "test.pdf", "page": 3},
            ],
        ]

        fused = reranker.fuse(results, top_n=10)

        # doc2 aparece em ambas as listas, deve ter maior RRF score
        assert len(fused) >= 3
        assert "rrf_score" in fused[0]

        # Encontra doc2
        doc2 = next(d for d in fused if "doc2" in d.get("id", ""))
        assert doc2["rrf_score"] > 0

    def test_fuse_respects_top_n(self, reranker):
        """Testa que fusão respeita top_n."""
        results = [
            [
                {
                    "id": f"doc{i}",
                    "content": f"c{i}",
                    "metadata": {},
                    "source": "test.pdf",
                    "page": i,
                }
                for i in range(20)
            ]
        ]

        fused = reranker.fuse(results, top_n=5)

        assert len(fused) == 5

    def test_rrf_score_calculation(self, reranker):
        """Testa cálculo correto do RRF score."""
        # Documento em posição 1 deve ter score 1/(k+1)
        results = [
            [{"id": "doc1", "content": "c1", "metadata": {}, "source": "test.pdf", "page": 1}]
        ]

        fused = reranker.fuse(results)

        expected_score = 1.0 / (reranker.k + 1)
        assert abs(fused[0]["rrf_score"] - expected_score) < 1e-6


class TestHybridReranker:
    """Testes para HybridReranker."""

    @pytest.fixture
    def mock_cohere(self):
        """Mock do Cohere reranker."""
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = [
            {"id": "doc1", "content": "c1", "metadata": {}, "rerank_score": 0.9}
        ]
        return mock_reranker

    @pytest.fixture
    def mock_fusion(self):
        """Mock do Fusion reranker."""
        mock_reranker = MagicMock()
        mock_reranker.fuse.return_value = [
            {"id": "doc1", "content": "c1", "metadata": {}, "rrf_score": 0.8}
        ]
        return mock_reranker

    @pytest.fixture
    def hybrid_reranker(self, mock_cohere, mock_fusion):
        """Cria hybrid reranker com mocks."""
        with patch("src.rag.reranker.CohereReranker", return_value=mock_cohere):
            with patch("src.rag.reranker.FusionReranker", return_value=mock_fusion):
                reranker = HybridReranker()
                return reranker

    def test_init(self, hybrid_reranker):
        """Testa inicialização."""
        assert hybrid_reranker.cohere_reranker is not None
        assert hybrid_reranker.fusion_reranker is not None

    def test_rerank_combines_methods(self, hybrid_reranker):
        """Testa que rerank combina RRF + Cohere."""
        vector_results = [{"id": "doc1", "content": "c1", "metadata": {}, "score": 0.9}]
        text_results = [{"id": "doc2", "content": "c2", "metadata": {}, "score": 0.8}]

        with patch("src.rag.reranker.settings") as mock_settings:
            mock_settings.top_n_rerank = 5

            results = hybrid_reranker.rerank(
                query="test query",
                vector_results=vector_results,
                text_results=text_results,
                top_n=5,
            )

            # Verifica que fusion foi chamado primeiro
            hybrid_reranker.fusion_reranker.fuse.assert_called_once()

            # Verifica que cohere foi chamado depois
            hybrid_reranker.cohere_reranker.rerank.assert_called_once()

            assert len(results) > 0
