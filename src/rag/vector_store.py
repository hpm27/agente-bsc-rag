"""
Gerenciamento do Redis como Vector Store.

NOTA: Esta implementação está mantida para compatibilidade,
mas Qdrant ou Weaviate são recomendados para novos projetos.
"""

from typing import Any

import numpy as np
import redis
from config.settings import settings
from loguru import logger
from redis.commands.search.field import NumericField, TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from .base_vector_store import BaseVectorStore


class RedisVectorStore(BaseVectorStore):
    """Redis Vector Store com suporte a Hybrid Search."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        db: int = 0,
        embedding_dim: int = 3072,
    ):
        """Inicializa conexão com Redis."""
        super().__init__(embedding_dim)

        self.client = redis.Redis(
            host=host or settings.redis_host,
            port=port or settings.redis_port,
            password=password or getattr(settings, "redis_password", None),
            db=db,
            decode_responses=False,
        )

        self.default_index_name = getattr(settings, "redis_index_name", "bsc_documents")

        logger.info(
            f"Conectado ao Redis em {self.client.connection_pool.connection_kwargs['host']}:{self.client.connection_pool.connection_kwargs['port']}"
        )

    def create_index(self, force_recreate: bool = False):
        """
        Cria o índice Redis para busca vetorial e full-text.

        Args:
            force_recreate: Se True, recria o índice mesmo se já existir
        """
        try:
            # Verifica se índice já existe
            self.client.ft(self.index_name).info()
            if force_recreate:
                logger.info(f"Removendo índice existente: {self.index_name}")
                self.client.ft(self.index_name).dropindex()
            else:
                logger.info(f"Índice {self.index_name} já existe")
                return
        except:
            pass

        # Define schema do índice
        schema = (
            TextField("content", weight=1.0),  # Texto completo
            TextField("source", weight=0.5),  # Fonte do documento
            NumericField("page"),  # Número da página
            VectorField(
                "embedding",
                "FLAT",  # ou "HNSW" para datasets maiores
                {"TYPE": "FLOAT32", "DIM": self.embedding_dim, "DISTANCE_METRIC": "COSINE"},
            ),
        )

        # Cria o índice
        definition = IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)

        self.client.ft(self.index_name).create_index(fields=schema, definition=definition)

        logger.info(f"Índice {self.index_name} criado com sucesso")

    def add_documents(self, documents: list[dict[str, Any]], embeddings: list[np.ndarray]):
        """
        Adiciona documentos ao vector store.

        Args:
            documents: Lista de documentos com metadados
            embeddings: Lista de embeddings correspondentes
        """
        pipeline = self.client.pipeline()

        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = f"doc:{doc.get('id', i)}"

            # Prepara dados
            data = {
                "content": doc["content"],
                "source": doc.get("source", "unknown"),
                "page": doc.get("page", 0),
                "embedding": embedding.astype(np.float32).tobytes(),
            }

            # Adiciona ao pipeline
            pipeline.hset(doc_id, mapping=data)

        # Executa pipeline
        pipeline.execute()
        logger.info(f"Adicionados {len(documents)} documentos ao vector store")

    def vector_search(self, query_embedding: np.ndarray, k: int = 10) -> list[dict[str, Any]]:
        """
        Busca vetorial (semântica).

        Args:
            query_embedding: Embedding da query
            k: Número de resultados

        Returns:
            Lista de documentos relevantes com scores
        """
        # Prepara query vetorial
        query_vector = query_embedding.astype(np.float32).tobytes()

        # Cria query
        q = (
            Query(f"*=>[KNN {k} @embedding $vec AS score]")
            .return_fields("content", "source", "page", "score")
            .sort_by("score")
            .dialect(2)
        )

        # Executa busca
        results = self.client.ft(self.index_name).search(q, query_params={"vec": query_vector})

        # Processa resultados
        documents = []
        for doc in results.docs:
            documents.append(
                {
                    "content": doc.content,
                    "source": doc.source,
                    "page": int(doc.page),
                    "score": float(doc.score),
                    "search_type": "vector",
                }
            )

        return documents

    def text_search(self, query: str, k: int = 10) -> list[dict[str, Any]]:
        """
        Busca por texto (BM25).

        Args:
            query: Query em texto
            k: Número de resultados

        Returns:
            Lista de documentos relevantes com scores
        """
        # Cria query de texto
        q = Query(query).return_fields("content", "source", "page").paging(0, k)

        # Executa busca
        results = self.client.ft(self.index_name).search(q)

        # Processa resultados
        documents = []
        for doc in results.docs:
            documents.append(
                {
                    "content": doc.content,
                    "source": doc.source,
                    "page": int(doc.page),
                    "score": 1.0,  # BM25 score normalizado
                    "search_type": "text",
                }
            )

        return documents

    def hybrid_search(
        self,
        query: str,
        query_embedding: np.ndarray,
        k: int = 10,
        weights: tuple[float, float] = (0.7, 0.3),
    ) -> list[dict[str, Any]]:
        """
        Busca híbrida (semântica + texto).

        Args:
            query: Query em texto
            query_embedding: Embedding da query
            k: Número de resultados
            weights: (peso_vetorial, peso_texto)

        Returns:
            Lista de documentos relevantes com scores combinados
        """
        # Busca vetorial
        vector_results = self.vector_search(query_embedding, k=k * 2)

        # Busca por texto
        text_results = self.text_search(query, k=k * 2)

        # Combina resultados
        combined = {}

        # Adiciona resultados vetoriais
        for doc in vector_results:
            key = f"{doc['source']}:{doc['page']}"
            combined[key] = {**doc, "combined_score": doc["score"] * weights[0]}

        # Adiciona/atualiza com resultados de texto
        for doc in text_results:
            key = f"{doc['source']}:{doc['page']}"
            if key in combined:
                combined[key]["combined_score"] += doc["score"] * weights[1]
                combined[key]["search_type"] = "hybrid"
            else:
                combined[key] = {**doc, "combined_score": doc["score"] * weights[1]}

        # Ordena por score combinado
        results = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)

        return results[:k]

    def delete_index(self):
        """Remove o índice."""
        try:
            self.client.ft(self.index_name).dropindex()
            logger.info(f"Índice {self.index_name} removido")
        except Exception as e:
            logger.error(f"Erro ao remover índice: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Retorna estatísticas do índice."""
        try:
            info = self.client.ft(self.index_name).info()
            return {
                "num_docs": info["num_docs"],
                "num_terms": info["num_terms"],
                "num_records": info["num_records"],
                "inverted_sz_mb": info["inverted_sz_mb"],
                "vector_index_sz_mb": info.get("vector_index_sz_mb", 0),
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
