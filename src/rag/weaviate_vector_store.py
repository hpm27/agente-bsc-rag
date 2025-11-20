"""
Implementação de Vector Store usando Weaviate.

Weaviate é um vector database com hybrid search nativo (BM25 + vetorial),
ideal para RAG com suporte a múltiplas features avançadas.
"""

from typing import Any

import numpy as np
import weaviate
from config.settings import settings
from loguru import logger
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import MetadataQuery

from .base_vector_store import BaseVectorStore, SearchResult, VectorStoreStats


class WeaviateVectorStore(BaseVectorStore):
    """
    Vector Store implementado com Weaviate.

    Features:
    - Hybrid search nativo (BM25 + vetorial)
    - Multi-tenancy
    - GraphQL API
    - Módulos de IA integrados
    - Excelente para RAG
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        embedding_dim: int = 3072,
        default_index_name: str = "BscDocuments",
    ):
        """
        Inicializa conexão com Weaviate.

        Args:
            host: Host do Weaviate
            port: Porta do Weaviate
            embedding_dim: Dimensão dos embeddings
            default_index_name: Nome padrão da coleção (deve ser PascalCase)
        """
        super().__init__(embedding_dim)

        self.client = weaviate.connect_to_local(host=host, port=port)
        self.default_index_name = default_index_name

        logger.info(f"Conectado ao Weaviate em {host}:{port}")

    def create_index(
        self,
        index_name: str = None,
        force_recreate: bool = False,
        distance_metric: str = "cosine",
        **kwargs,
    ):
        """
        Cria uma coleção no Weaviate.

        Args:
            index_name: Nome da coleção (PascalCase)
            force_recreate: Se True, recria mesmo se existir
            distance_metric: 'cosine', 'l2', 'dot'
            **kwargs: Parâmetros adicionais
        """
        index_name = index_name or self.default_index_name

        try:
            # Verifica se coleção existe
            self.client.collections.get(index_name)

            if force_recreate:
                logger.info(f"Removendo coleção existente: {index_name}")
                self.client.collections.delete(index_name)
            else:
                logger.info(f"Coleção {index_name} já existe")
                return
        except:
            pass

        # Mapeia distância
        distance_map = {"cosine": "cosine", "l2": "l2-squared", "dot": "dot"}

        # Cria coleção com schema
        self.client.collections.create(
            name=index_name,
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="page", data_type=DataType.INT),
                Property(name="doc_id", data_type=DataType.TEXT),
                # Metadados adicionais podem ser adicionados dinamicamente
            ],
            vectorizer_config=Configure.Vectorizer.none(),  # Usamos embeddings externos
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric=distance_map.get(distance_metric, "cosine")
            ),
            # Habilita hybrid search (BM25 + vetorial)
            inverted_index_config=Configure.inverted_index(bm25_b=0.75, bm25_k1=1.2),
        )

        logger.info(f"Coleção {index_name} criada com sucesso")

    def add_documents(
        self,
        documents: list[dict[str, Any]],
        embeddings: list[np.ndarray],
        index_name: str | None = None,
    ):
        """
        Adiciona documentos ao Weaviate.

        Args:
            documents: Lista de documentos
            embeddings: Lista de embeddings
            index_name: Nome da coleção
        """
        index_name = index_name or self.default_index_name

        collection = self.client.collections.get(index_name)

        # Batch insert para performance
        with collection.batch.dynamic() as batch:
            for doc, embedding in zip(documents, embeddings):
                properties = {
                    "content": doc["content"],
                    "source": doc.get("source", "unknown"),
                    "page": doc.get("page", 0),
                    "doc_id": doc.get("id", ""),
                }

                # Adiciona metadados customizados como strings JSON
                if doc.get("metadata"):
                    for key, value in doc["metadata"].items():
                        properties[f"meta_{key}"] = str(value)

                batch.add_object(properties=properties, vector=embedding.tolist())

        logger.info(f"Adicionados {len(documents)} documentos à coleção {index_name}")

    def vector_search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_dict: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> list[SearchResult]:
        """
        Busca vetorial no Weaviate.

        Args:
            query_embedding: Embedding da query
            k: Número de resultados
            filter_dict: Filtros (ex: {'source': 'doc1.pdf'})
            index_name: Nome da coleção

        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name

        collection = self.client.collections.get(index_name)

        # Cria filtro se especificado
        where_filter = self._build_filter(filter_dict) if filter_dict else None

        # Executa busca vetorial
        response = collection.query.near_vector(
            near_vector=query_embedding.tolist(),
            limit=k,
            where=where_filter,
            return_metadata=MetadataQuery(distance=True),
        )

        # Converte para SearchResult
        return self._convert_results(response.objects, search_type="vector")

    def text_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> list[SearchResult]:
        """
        Busca por texto (BM25) no Weaviate.

        Args:
            query: Query em texto
            k: Número de resultados
            filter_dict: Filtros
            index_name: Nome da coleção

        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name

        collection = self.client.collections.get(index_name)

        # Cria filtro se especificado
        where_filter = self._build_filter(filter_dict) if filter_dict else None

        # Executa busca BM25
        response = collection.query.bm25(
            query=query, limit=k, where=where_filter, return_metadata=MetadataQuery(score=True)
        )

        # Converte para SearchResult
        return self._convert_results(response.objects, search_type="text")

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
        Busca híbrida (BM25 + vetorial) no Weaviate.

        Esta é a grande vantagem do Weaviate: hybrid search nativo!

        Args:
            query: Query em texto
            query_embedding: Embedding da query
            k: Número de resultados
            weights: (peso_vetorial, peso_texto) - normalizado para alpha
            filter_dict: Filtros
            index_name: Nome da coleção

        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name

        collection = self.client.collections.get(index_name)

        # Weaviate usa 'alpha' para controlar peso:
        # alpha=1.0 -> apenas vetorial
        # alpha=0.0 -> apenas BM25
        # alpha=0.5 -> balanceado
        alpha = weights[0] / (weights[0] + weights[1])

        # Cria filtro se especificado
        where_filter = self._build_filter(filter_dict) if filter_dict else None

        # Executa hybrid search nativo
        response = collection.query.hybrid(
            query=query,
            vector=query_embedding.tolist(),
            limit=k,
            alpha=alpha,
            where=where_filter,
            return_metadata=MetadataQuery(score=True, explain_score=True),
        )

        # Converte para SearchResult
        return self._convert_results(response.objects, search_type="hybrid")

    def delete_documents(self, document_ids: list[str], index_name: str | None = None):
        """
        Remove documentos do Weaviate.

        Args:
            document_ids: Lista de IDs (doc_id field)
            index_name: Nome da coleção
        """
        index_name = index_name or self.default_index_name

        collection = self.client.collections.get(index_name)

        # Weaviate deleta por UUID, então precisamos buscar primeiro
        for doc_id in document_ids:
            response = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("doc_id").equal(doc_id), limit=1
            )

            if response.objects:
                uuid = response.objects[0].uuid
                collection.data.delete_by_id(uuid)

        logger.info(f"Removidos {len(document_ids)} documentos da coleção {index_name}")

    def delete_index(self, index_name: str | None = None):
        """
        Remove uma coleção do Weaviate.

        Args:
            index_name: Nome da coleção
        """
        index_name = index_name or self.default_index_name

        try:
            self.client.collections.delete(index_name)
            logger.info(f"Coleção {index_name} removida")
        except Exception as e:
            logger.error(f"Erro ao remover coleção {index_name}: {e}")

    def get_stats(self, index_name: str | None = None) -> VectorStoreStats:
        """
        Retorna estatísticas da coleção Weaviate.

        Args:
            index_name: Nome da coleção

        Returns:
            VectorStoreStats
        """
        index_name = index_name or self.default_index_name

        try:
            collection = self.client.collections.get(index_name)

            # Aggregate para contar objetos
            response = collection.aggregate.over_all(total_count=True)

            return VectorStoreStats(
                num_documents=response.total_count,
                index_size_mb=0,  # Weaviate não expõe facilmente
                vector_dimensions=self.embedding_dim,
                distance_metric="cosine",  # Default
                additional_info={"collection_name": index_name},
            )
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas da coleção {index_name}: {e}")
            return VectorStoreStats(
                num_documents=0,
                index_size_mb=0,
                vector_dimensions=self.embedding_dim,
                distance_metric="unknown",
            )

    def health_check(self) -> bool:
        """
        Verifica se Weaviate está acessível.

        Returns:
            True se saudável
        """
        try:
            self.client.is_ready()
            return True
        except Exception as e:
            logger.error(f"Weaviate health check falhou: {e}")
            return False

    def _build_filter(self, filter_dict: dict[str, Any]):
        """
        Constrói filtro Weaviate a partir de dict.

        Args:
            filter_dict: Dict com filtros

        Returns:
            Filter do Weaviate
        """
        from weaviate.classes.query import Filter

        filters = []
        for key, value in filter_dict.items():
            filters.append(Filter.by_property(key).equal(value))

        # Combina filtros com AND
        if len(filters) == 1:
            return filters[0]
        if len(filters) > 1:
            result = filters[0]
            for f in filters[1:]:
                result = result & f
            return result

        return None

    def _convert_results(self, results: list[Any], search_type: str) -> list[SearchResult]:
        """
        Converte resultados Weaviate para SearchResult.

        Args:
            results: Lista de objetos do Weaviate
            search_type: Tipo de busca

        Returns:
            Lista de SearchResult
        """
        search_results = []

        for obj in results:
            props = obj.properties

            # Score pode vir de metadata.distance ou metadata.score
            if hasattr(obj.metadata, "distance") and obj.metadata.distance is not None:
                score = 1 - obj.metadata.distance  # Converte distância para similaridade
            elif hasattr(obj.metadata, "score") and obj.metadata.score is not None:
                score = obj.metadata.score
            else:
                score = 0.0

            # Extrai metadados customizados
            metadata = {}
            for key, value in props.items():
                if key.startswith("meta_"):
                    metadata[key[5:]] = value

            search_results.append(
                SearchResult(
                    content=props.get("content", ""),
                    source=props.get("source", "unknown"),
                    page=props.get("page", 0),
                    score=score,
                    search_type=search_type,
                    metadata=metadata,
                )
            )

        return search_results

    def __del__(self):
        """Fecha conexão ao destruir objeto."""
        try:
            self.client.close()
        except:
            pass


# Factory function para facilitar criação
def create_weaviate_vector_store(
    host: str = None, port: int = None, embedding_dim: int = 3072
) -> WeaviateVectorStore:
    """
    Cria instância de WeaviateVectorStore com configurações do settings.

    Args:
        host: Host do Weaviate (usa settings se não especificado)
        port: Porta do Weaviate (usa settings se não especificado)
        embedding_dim: Dimensão dos embeddings

    Returns:
        WeaviateVectorStore configurado
    """
    return WeaviateVectorStore(
        host=host or getattr(settings, "weaviate_host", "localhost"),
        port=port or getattr(settings, "weaviate_port", 8080),
        embedding_dim=embedding_dim,
    )
