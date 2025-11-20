"""
Interface abstrata para Vector Stores.

Esta classe define a interface comum para todos os vector stores,
permitindo trocar facilmente entre diferentes implementações
(Qdrant, Weaviate, Redis, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class SearchResult:
    """Resultado de uma busca no vector store.

    Compatível com testes que fornecem apenas `id`, `content`, `metadata` e `score`.
    Campos `source`, `page` e `search_type` recebem defaults seguros.
    """

    # Opcional/compatibilidade com testes
    id: str | None = None
    # Conteúdo e metadados
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    # Atributos de origem/posição
    source: str = "unknown"
    page: int = 0
    # Scoring e tipo de busca
    score: float = 0.0
    search_type: str = "hybrid"  # 'vector', 'text', 'hybrid'


@dataclass
class VectorStoreStats:
    """Estatísticas do vector store."""

    num_documents: int
    index_size_mb: float
    vector_dimensions: int
    distance_metric: str
    additional_info: dict[str, Any] = None

    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


class BaseVectorStore(ABC):
    """
    Classe abstrata para Vector Stores.

    Todos os vector stores devem implementar esta interface para
    garantir compatibilidade com o resto do sistema RAG.
    """

    def __init__(self, embedding_dim: int = 3072):
        """
        Inicializa o vector store.

        Args:
            embedding_dim: Dimensão dos embeddings (default: 3072 para text-embedding-3-large)
        """
        self.embedding_dim = embedding_dim

    @abstractmethod
    def create_index(self, index_name: str, force_recreate: bool = False, **kwargs):
        """
        Cria um índice/coleção no vector store.

        Args:
            index_name: Nome do índice/coleção
            force_recreate: Se True, recria mesmo se já existir
            **kwargs: Parâmetros específicos do vector store
        """

    @abstractmethod
    def add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[np.ndarray],
        index_name: str | None = None,
    ):
        """
        Adiciona documentos ao vector store.

        Args:
            documents: Lista de documentos com metadados
                Formato esperado: [{
                    'id': str,
                    'content': str,
                    'source': str,
                    'page': int,
                    'metadata': dict (opcional)
                }, ...]
            embeddings: Lista de embeddings correspondentes
            index_name: Nome do índice (usa default se não especificado)
        """

    @abstractmethod
    def vector_search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_dict: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> list[SearchResult]:
        """
        Busca vetorial (semântica) pura.

        Args:
            query_embedding: Embedding da query
            k: Número de resultados
            filter_dict: Filtros de metadados (ex: {'source': 'doc1.pdf'})
            index_name: Nome do índice

        Returns:
            Lista de SearchResult ordenada por relevância
        """

    @abstractmethod
    def text_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> list[SearchResult]:
        """
        Busca por texto (BM25/keyword) pura.

        Args:
            query: Query em texto
            k: Número de resultados
            filter_dict: Filtros de metadados
            index_name: Nome do índice

        Returns:
            Lista de SearchResult ordenada por relevância
        """

    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        query_embedding: np.ndarray,
        k: int = 10,
        weights: tuple[float, float] = (0.7, 0.3),
        filter_dict: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> list[SearchResult]:
        """
        Busca híbrida (semântica + texto).

        Args:
            query: Query em texto
            query_embedding: Embedding da query
            k: Número de resultados finais
            weights: (peso_vetorial, peso_texto)
            filter_dict: Filtros de metadados
            index_name: Nome do índice

        Returns:
            Lista de SearchResult ordenada por score combinado
        """

    @abstractmethod
    def delete_documents(self, document_ids: list[str], index_name: str | None = None):
        """
        Remove documentos do vector store.

        Args:
            document_ids: Lista de IDs de documentos a remover
            index_name: Nome do índice
        """

    @abstractmethod
    def delete_index(self, index_name: str | None = None):
        """
        Remove completamente um índice/coleção.

        Args:
            index_name: Nome do índice (usa default se não especificado)
        """

    @abstractmethod
    def get_stats(self, index_name: str | None = None) -> VectorStoreStats:
        """
        Retorna estatísticas do índice.

        Args:
            index_name: Nome do índice

        Returns:
            VectorStoreStats com informações do índice
        """

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verifica se o vector store está saudável e acessível.

        Returns:
            True se saudável, False caso contrário
        """

    def batch_add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[np.ndarray],
        batch_size: int = 100,
        index_name: str | None = None,
    ):
        """
        Adiciona documentos em batches para melhor performance.

        Args:
            documents: Lista de documentos
            embeddings: Lista de embeddings
            batch_size: Tamanho do batch
            index_name: Nome do índice
        """
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_embs = embeddings[i : i + batch_size]
            self.add_documents(batch_docs, batch_embs, index_name)

    def _normalize_score(self, score: float, search_type: str) -> float:
        """
        Normaliza scores para escala 0-1 para facilitar combinação.

        Args:
            score: Score original
            search_type: Tipo de busca ('vector', 'text', 'hybrid')

        Returns:
            Score normalizado entre 0 e 1
        """
        # Vector search (cosine similarity) já está em [-1, 1], normalizar para [0, 1]
        if search_type == "vector":
            return (score + 1) / 2

        # Text search (BM25) pode variar, aplicar sigmoid
        if search_type == "text":
            return 1 / (1 + np.exp(-score))

        # Hybrid já deve estar normalizado
        return score

    def __repr__(self) -> str:
        """Representação string do vector store."""
        return f"{self.__class__.__name__}(embedding_dim={self.embedding_dim})"
