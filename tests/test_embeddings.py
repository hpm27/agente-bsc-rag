"""
Testes para o módulo de embeddings.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

import numpy as np

from src.rag.embeddings import EmbeddingManager, FineTuner


class TestEmbeddingManager:
    """Testes para EmbeddingManager."""

    @patch("src.rag.embeddings.OpenAI")
    def test_init_openai(self, mock_openai):
        """Testa inicialização com OpenAI."""
        with patch("src.rag.embeddings.settings") as mock_settings:
            mock_settings.use_finetuned_embeddings = False
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_embedding_model = "text-embedding-3-large"

            manager = EmbeddingManager()

            assert manager.provider == "openai"
            assert manager.embedding_dim == 3072
            mock_openai.assert_called_once_with(api_key="test-key")

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_init_finetuned(self, mock_st):
        """Testa inicialização com modelo fine-tuned."""
        with patch("src.rag.embeddings.settings") as mock_settings:
            mock_settings.use_finetuned_embeddings = True
            mock_settings.finetuned_model_path = "./models/test"

            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 768
            mock_st.return_value = mock_model

            manager = EmbeddingManager()

            assert manager.provider == "finetuned"
            assert manager.embedding_dim == 768
            mock_st.assert_called_once_with("./models/test")

    @patch("src.rag.embeddings.OpenAI")
    def test_embed_text_openai(self, mock_openai):
        """Testa geração de embedding único com OpenAI."""
        with patch("src.rag.embeddings.settings") as mock_settings:
            mock_settings.use_finetuned_embeddings = False
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_embedding_model = "text-embedding-3-large"

            # Mock da resposta da API
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client

            manager = EmbeddingManager()
            embedding = manager.embed_text("test text")

            assert isinstance(embedding, np.ndarray)
            assert len(embedding) == 3
            np.testing.assert_array_equal(embedding, np.array([0.1, 0.2, 0.3]))

    @patch("src.rag.embeddings.OpenAI")
    def test_embed_batch_openai(self, mock_openai):
        """Testa geração de embeddings em batch com OpenAI."""
        with patch("src.rag.embeddings.settings") as mock_settings:
            mock_settings.use_finetuned_embeddings = False
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_embedding_model = "text-embedding-3-large"

            # Mock da resposta da API
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3]),
                MagicMock(embedding=[0.4, 0.5, 0.6]),
            ]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client

            manager = EmbeddingManager()
            embeddings = manager.embed_batch(["text1", "text2"], batch_size=2)

            assert len(embeddings) == 2
            assert all(isinstance(emb, np.ndarray) for emb in embeddings)

    def test_similarity(self):
        """Testa cálculo de similaridade de cosseno."""
        with patch("src.rag.embeddings.settings") as mock_settings:
            mock_settings.use_finetuned_embeddings = False
            mock_settings.openai_api_key = "test-key"

            with patch("src.rag.embeddings.OpenAI"):
                manager = EmbeddingManager()

                emb1 = np.array([1.0, 0.0, 0.0])
                emb2 = np.array([1.0, 0.0, 0.0])
                emb3 = np.array([0.0, 1.0, 0.0])

                # Embeddings idênticos = similaridade 1.0
                sim1 = manager.similarity(emb1, emb2)
                assert abs(sim1 - 1.0) < 1e-6

                # Embeddings ortogonais = similaridade 0.0
                sim2 = manager.similarity(emb1, emb3)
                assert abs(sim2) < 1e-6

    def test_prepare_training_data(self):
        """Testa preparação de dados de treinamento."""
        queries = ["query1", "query2"]
        positives = ["doc1", "doc2"]
        negatives = [["neg1", "neg2"], ["neg3", "neg4"]]

        data = EmbeddingManager.prepare_training_data(queries, positives, negatives)

        assert len(data) == 2
        assert data[0]["query"] == "query1"
        assert data[0]["positive"] == "doc1"
        assert data[0]["negatives"] == ["neg1", "neg2"]


class TestFineTuner:
    """Testes para FineTuner."""

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_init(self, mock_st):
        """Testa inicialização do fine-tuner."""
        tuner = FineTuner(base_model="test-model")

        mock_st.assert_called_once_with("test-model")
        assert tuner.base_model == "test-model"

    @patch("src.rag.embeddings.SentenceTransformer")
    def test_train(self, mock_st):
        """Testa treinamento do modelo."""
        mock_model = MagicMock()
        mock_st.return_value = mock_model

        tuner = FineTuner()

        training_data = [{"query": "q1", "positive": "p1", "negatives": ["n1", "n2"]}]

        tuner.train(
            training_data=training_data, output_path="./test_output", epochs=1, batch_size=2
        )

        # Verifica se fit foi chamado
        mock_model.fit.assert_called_once()

    @patch("src.rag.embeddings.SentenceTransformer")
    @patch("src.rag.embeddings.accuracy_score")
    def test_evaluate(self, mock_accuracy, mock_st):
        """Testa avaliação do modelo."""
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_st.return_value = mock_model

        mock_accuracy.return_value = 0.8

        with patch("src.rag.embeddings.precision_recall_fscore_support") as mock_prf:
            mock_prf.return_value = (0.85, 0.75, 0.8, None)

            tuner = FineTuner()

            metrics = tuner.evaluate(
                test_queries=["q1", "q2"], test_docs=["d1", "d2"], test_labels=[1, 0]
            )

            assert "accuracy" in metrics
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1" in metrics
