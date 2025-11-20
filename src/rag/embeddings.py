"""
Gerenciamento de embeddings com suporte a fine-tuning e caching.
"""

import hashlib
import os

import numpy as np
from config.settings import settings
from diskcache import Cache
from loguru import logger
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


class EmbeddingManager:
    """Gerenciador de embeddings com caching persistente."""

    def __init__(self):
        """Inicializa o gerenciador de embeddings."""
        self.use_finetuned = settings.use_finetuned_embeddings

        # Inicializar cache (tolerante a mocks/valores inválidos em testes)
        self.cache_enabled = bool(getattr(settings, "embedding_cache_enabled", False))
        self.cache: Cache | None = None
        self.cache_hits = 0
        self.cache_misses = 0

        if self.cache_enabled:
            cache_dir = getattr(settings, "embedding_cache_dir", ".cache/embeddings")
            # Validar tipo do diretório (pode vir como MagicMock em testes)
            if not isinstance(cache_dir, (str, os.PathLike)) or not str(cache_dir).strip():
                logger.warning(
                    "[CACHE] Diretório de cache inválido; desativando cache para evitar erros em testes"
                )
                self.cache_enabled = False

        if self.cache_enabled:
            try:
                # Criar diretorio de cache
                os.makedirs(cache_dir, exist_ok=True)

                # Inicializar diskcache com TTL e tamanho maximo
                ttl_seconds = int(getattr(settings, "embedding_cache_ttl_days", 30)) * 24 * 60 * 60
                size_limit_gb = getattr(settings, "embedding_cache_max_size_gb", 5)
                try:
                    size_limit_bytes = int(size_limit_gb) * 1024 * 1024 * 1024
                except Exception:
                    size_limit_bytes = 5 * 1024 * 1024 * 1024

                self.cache = Cache(
                    directory=str(cache_dir),
                    size_limit=size_limit_bytes,
                    eviction_policy="least-recently-used",
                )
                self.cache_ttl = ttl_seconds
                logger.info(
                    f"[CACHE] Embedding cache ativado: {cache_dir} "
                    f"(TTL: {getattr(settings, 'embedding_cache_ttl_days', 30)} dias, "
                    f"Max Size: {getattr(settings, 'embedding_cache_max_size_gb', 5)} GB)"
                )
            except Exception as cache_err:
                # Tolerante a ambientes de teste com configurações incompletas
                logger.warning(
                    f"[CACHE] Falha ao inicializar cache ({cache_err}); desativando cache"
                )
                self.cache_enabled = False
                self.cache = None
        else:
            logger.info("[CACHE] Embedding cache desativado")

        if self.use_finetuned:
            # Carrega modelo fine-tuned
            logger.info(f"Carregando modelo fine-tuned: {settings.finetuned_model_path}")
            self.model = SentenceTransformer(settings.finetuned_model_path)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.provider = "finetuned"
        else:
            # Usa OpenAI embeddings
            logger.info(f"Usando OpenAI embeddings: {settings.openai_embedding_model}")
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model_name = settings.openai_embedding_model
            self.embedding_dim = 3072  # text-embedding-3-large
            self.provider = "openai"

    def _get_cache_key(self, text: str) -> str:
        """
        Gera chave de cache unica para um texto.
        Usa SHA256 do texto normalizado + provedor + modelo.

        Args:
            text: Texto para gerar chave

        Returns:
            Chave de cache (hash SHA256)
        """
        # Normalizar texto (strip whitespace, lowercase)
        normalized_text = text.strip().lower()

        # Incluir provedor e modelo na chave para evitar colisoes
        if self.provider == "openai":
            cache_input = f"{self.provider}:{self.model_name}:{normalized_text}"
        else:
            cache_input = f"{self.provider}:{self.model.model_name_or_path}:{normalized_text}"

        # Gerar hash SHA256
        return hashlib.sha256(cache_input.encode("utf-8")).hexdigest()

    def _log_cache_stats(self):
        """Log periodico de estatisticas do cache."""
        if self.cache_enabled and (self.cache_hits + self.cache_misses) > 0:
            total = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total) * 100
            logger.info(
                f"[CACHE STATS] Hits: {self.cache_hits}, "
                f"Misses: {self.cache_misses}, "
                f"Hit Rate: {hit_rate:.1f}%"
            )

    def embed_text(self, text: str) -> list[float]:
        """
        Gera embedding para um texto (com caching automático).

        Args:
            text: Texto para gerar embedding

        Returns:
            Embedding como lista de floats
        """
        # Verificar cache primeiro
        if self.cache_enabled and self.cache is not None:
            cache_key = self._get_cache_key(text)
            cached_embedding = self.cache.get(cache_key)

            if cached_embedding is not None:
                self.cache_hits += 1
                logger.debug("[CACHE HIT] Embedding recuperado do cache")
                return cached_embedding
            self.cache_misses += 1
            logger.debug("[CACHE MISS] Gerando novo embedding")

        # Gerar embedding
        if self.provider == "finetuned":
            # Fine-tuned retorna numpy array
            embedding = self.model.encode(text, convert_to_numpy=True)
        else:
            # OpenAI API retorna lista; converter para numpy array para consistência
            response = self.client.embeddings.create(input=text, model=self.model_name)
            embedding = np.array(response.data[0].embedding)

        # Armazenar em cache
        if self.cache_enabled and self.cache is not None:
            self.cache.set(cache_key, embedding, expire=self.cache_ttl)

        # Log stats periodicamente (a cada 100 chamadas)
        if (self.cache_hits + self.cache_misses) % 100 == 0:
            self._log_cache_stats()

        return embedding

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[np.ndarray]:
        """
        Gera embeddings para um lote de textos (com caching automático).
        Processa apenas textos que não estão em cache.

        Args:
            texts: Lista de textos
            batch_size: Tamanho do lote para processamento

        Returns:
            Lista de embeddings
        """
        embeddings = [None] * len(texts)
        texts_to_process = []
        indices_to_process = []

        # Verificar cache para cada texto
        if self.cache_enabled and self.cache is not None:
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                cached_embedding = self.cache.get(cache_key)

                if cached_embedding is not None:
                    self.cache_hits += 1
                    embeddings[i] = np.array(cached_embedding)
                else:
                    self.cache_misses += 1
                    texts_to_process.append(text)
                    indices_to_process.append(i)

            if texts_to_process:
                logger.info(
                    f"[CACHE] {len(texts) - len(texts_to_process)}/{len(texts)} "
                    f"embeddings recuperados do cache ({(1 - len(texts_to_process)/len(texts))*100:.1f}%)"
                )
        else:
            # Cache desativado, processar todos
            texts_to_process = texts
            indices_to_process = list(range(len(texts)))

        # Processar textos que não estão em cache
        if texts_to_process:
            if self.provider == "finetuned":
                new_embeddings = self.model.encode(
                    texts_to_process,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=True,
                )
            else:
                new_embeddings = []
                for i in range(0, len(texts_to_process), batch_size):
                    batch = texts_to_process[i : i + batch_size]
                    response = self.client.embeddings.create(input=batch, model=self.model_name)
                    batch_embeddings = [np.array(item.embedding) for item in response.data]
                    new_embeddings.extend(batch_embeddings)

                    if (i + batch_size) % 100 == 0:
                        logger.info(f"Processados {i + batch_size}/{len(texts_to_process)} textos")

            # Armazenar novos embeddings em cache e preencher resultado
            for idx, text_idx in enumerate(indices_to_process):
                embeddings[text_idx] = new_embeddings[idx]

                # Armazenar em cache
                if self.cache_enabled and self.cache is not None:
                    cache_key = self._get_cache_key(texts_to_process[idx])
                    self.cache.set(cache_key, new_embeddings[idx].tolist(), expire=self.cache_ttl)

        # Log stats
        self._log_cache_stats()

        return embeddings

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calcula similaridade de cosseno entre dois embeddings.

        Args:
            emb1: Primeiro embedding
            emb2: Segundo embedding

        Returns:
            Similaridade de cosseno (0 a 1)
        """
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    @staticmethod
    def prepare_training_data(
        queries: list[str], positive_docs: list[str], negative_docs: list[list[str]]
    ) -> list[dict]:
        """
        Prepara dados para fine-tuning de embeddings.

        Args:
            queries: Lista de queries
            positive_docs: Documentos relevantes para cada query
            negative_docs: Lista de documentos não relevantes para cada query

        Returns:
            Dados formatados para treinamento
        """
        training_data = []

        for query, pos_doc, neg_docs in zip(queries, positive_docs, negative_docs):
            training_data.append({"query": query, "positive": pos_doc, "negatives": neg_docs})

        return training_data


class FineTuner:
    """Fine-tuning de modelos de embedding."""

    def __init__(self, base_model: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Inicializa o fine-tuner.

        Args:
            base_model: Modelo base para fine-tuning
        """
        self.base_model = base_model
        self.model = SentenceTransformer(base_model)
        logger.info(f"Modelo base carregado: {base_model}")

    def train(
        self,
        training_data: list[dict],
        output_path: str,
        epochs: int = 3,
        batch_size: int = 16,
        warmup_steps: int = 100,
    ):
        """
        Treina o modelo com dados de domínio específico.

        Args:
            training_data: Dados de treinamento (query, positive, negatives)
            output_path: Caminho para salvar o modelo treinado
            epochs: Número de épocas
            batch_size: Tamanho do lote
            warmup_steps: Passos de warmup
        """
        from sentence_transformers import InputExample, losses
        from torch.utils.data import DataLoader

        # Prepara exemplos de treinamento
        train_examples = []
        for item in training_data:
            # Positive pair
            train_examples.append(InputExample(texts=[item["query"], item["positive"]], label=1.0))

            # Negative pairs
            for neg in item["negatives"]:
                train_examples.append(InputExample(texts=[item["query"], neg], label=0.0))

        # Cria DataLoader
        train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

        # Define loss function
        train_loss = losses.CosineSimilarityLoss(self.model)

        # Treina
        logger.info(f"Iniciando treinamento com {len(train_examples)} exemplos")
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=output_path,
            show_progress_bar=True,
        )

        logger.info(f"Modelo treinado salvo em: {output_path}")

    def evaluate(
        self, test_queries: list[str], test_docs: list[str], test_labels: list[int]
    ) -> dict:
        """
        Avalia o modelo em dados de teste.

        Args:
            test_queries: Queries de teste
            test_docs: Documentos de teste
            test_labels: Labels (1 para relevante, 0 para não relevante)

        Returns:
            Métricas de avaliação
        """

        # Gera embeddings
        query_embeddings = self.model.encode(test_queries)
        doc_embeddings = self.model.encode(test_docs)

        # Calcula similaridades
        similarities = []
        for q_emb, d_emb in zip(query_embeddings, doc_embeddings):
            sim = np.dot(q_emb, d_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(d_emb))
            similarities.append(sim)

        # Threshold para classificação
        threshold = 0.5
        predictions = [1 if sim > threshold else 0 for sim in similarities]

        # Calcula métricas
        accuracy = accuracy_score(test_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            test_labels, predictions, average="binary"
        )

        metrics = {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

        logger.info(f"Métricas de avaliação: {metrics}")
        return metrics
