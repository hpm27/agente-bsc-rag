"""
Implementação de Vector Store usando Qdrant.

Qdrant é um vector database otimizado para retrieval semântico,
com excelente performance e integração com LangChain.
"""

from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np
from loguru import logger

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint
)

from .base_vector_store import BaseVectorStore, SearchResult, VectorStoreStats
from config.settings import settings


class QdrantVectorStore(BaseVectorStore):
    """
    Vector Store implementado com Qdrant.
    
    Features:
    - Busca vetorial eficiente com HNSW
    - Filtros de metadados avançados
    - Suporte a payload filtering
    - Quantização para otimizar memória
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        embedding_dim: int = 3072,
        default_index_name: str = "bsc_documents"
    ):
        """
        Inicializa conexão com Qdrant.
        
        Args:
            host: Host do Qdrant
            port: Porta do Qdrant
            embedding_dim: Dimensão dos embeddings
            default_index_name: Nome padrão da coleção
        """
        super().__init__(embedding_dim)
        
        self.client = QdrantClient(host=host, port=port)
        self.default_index_name = default_index_name
        
        logger.info(f"Conectado ao Qdrant em {host}:{port}")
    
    def create_index(
        self,
        index_name: str = None,
        force_recreate: bool = False,
        distance_metric: str = "cosine",
        **kwargs
    ):
        """
        Cria uma coleção no Qdrant.
        
        Args:
            index_name: Nome da coleção
            force_recreate: Se True, recria mesmo se existir
            distance_metric: 'cosine', 'euclidean', 'dot'
            **kwargs: Parâmetros adicionais (ex: on_disk, quantization)
        """
        index_name = index_name or self.default_index_name
        
        # Se force_recreate, tenta deletar independentemente de existir ou não
        if force_recreate:
            logger.info(f"force_recreate=True: tentando deletar coleção {index_name}")
            try:
                self.client.delete_collection(index_name)
                logger.info(f"Coleção {index_name} deletada com sucesso")
                # Aguarda um pouco para garantir que a deleção foi processada
                import time
                time.sleep(0.5)
            except Exception as e:
                # Se não existe, está ok - vamos criar
                logger.info(f"Coleção {index_name} não existia (ou erro ao deletar): {e}")
        else:
            # Verifica se já existe
            try:
                self.client.get_collection(index_name)
                logger.info(f"Coleção {index_name} já existe. Use force_recreate=True para recriar.")
                return
            except:
                # Não existe, vamos criar
                pass
        
        # Mapeia distância
        distance_map = {
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID,
            "dot": Distance.DOT
        }
        
        # Cria coleção
        try:
            self.client.create_collection(
                collection_name=index_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=distance_map.get(distance_metric, Distance.COSINE)
                ),
                **kwargs
            )
            logger.info(f"Coleção {index_name} criada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar coleção {index_name}: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[np.ndarray],
        index_name: Optional[str] = None
    ):
        """
        Adiciona documentos ao Qdrant.
        
        Args:
            documents: Lista de documentos
            embeddings: Lista de embeddings
            index_name: Nome da coleção
        """
        index_name = index_name or self.default_index_name
        
        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # ID único: usar ID do documento ou gerar sequencial
            point_id = doc.get('id', f"{index_name}_{i}")
            
            # Payload com todos os metadados
            payload = {
                'content': doc['content'],
                'source': doc.get('source', 'unknown'),
                'page': doc.get('page', 0),
            }
            
            # Adiciona metadados customizados
            if 'metadata' in doc and doc['metadata']:
                payload.update(doc['metadata'])
            
            # Cria ponto
            # Converte embedding para lista se necessário
            if hasattr(embedding, 'tolist'):
                vector = embedding.tolist()
            elif isinstance(embedding, list):
                vector = embedding
            else:
                vector = list(embedding)
            
            points.append(
                PointStruct(
                    id=hash(point_id) % (2**63),  # Qdrant usa int64 como ID
                    vector=vector,
                    payload=payload
                )
            )
        
        # Upsert em batch
        self.client.upsert(
            collection_name=index_name,
            points=points
        )
        
        logger.info(f"Adicionados {len(documents)} documentos à coleção {index_name}")
    
    def vector_search(
        self,
        query_embedding: Union[List[float], np.ndarray],
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Busca vetorial no Qdrant.
        
        Args:
            query_embedding: Embedding da query
            k: Número de resultados
            filter_dict: Filtros (ex: {'source': 'doc1.pdf', 'page': 5})
            index_name: Nome da coleção
            
        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name
        
        # Cria filtros se especificados
        search_filter = self._build_filter(filter_dict) if filter_dict else None
        
        # Converte query_embedding para lista se necessário
        if hasattr(query_embedding, 'tolist'):
            query_vector = query_embedding.tolist()
        elif isinstance(query_embedding, list):
            query_vector = query_embedding
        else:
            query_vector = list(query_embedding)
        
        # Executa busca vetorial (versão 1.15+ usa query_points)
        results = self.client.query_points(
            collection_name=index_name,
            query=query_vector,
            limit=k,
            query_filter=search_filter
        )
        
        # query_points retorna um objeto com atributo 'points'
        return self._convert_results(results.points, search_type='vector')
    
    def text_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Busca por texto no Qdrant.
        
        Nota: Qdrant não tem BM25 nativo. Esta implementação faz
        busca por keywords no payload. Para BM25 real, considere
        combinar com Elasticsearch ou usar Weaviate.
        
        Args:
            query: Query em texto
            k: Número de resultados
            filter_dict: Filtros
            index_name: Nome da coleção
            
        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name
        
        # Busca simples por texto no conteúdo
        # TODO: Integrar com BM25 externo se necessário
        
        logger.warning(
            "Qdrant não tem BM25 nativo. "
            "Use hybrid_search com embeddings ou integre com Elasticsearch."
        )
        
        # Por enquanto, retorna lista vazia
        # Na prática, você usaria scroll + filtragem manual ou BM25 externo
        return []
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: Union[List[float], np.ndarray],
        k: int = 10,
        weights: Tuple[float, float] = (0.7, 0.3),
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Busca híbrida no Qdrant.
        
        Como Qdrant não tem BM25 nativo, esta implementação:
        1. Faz busca vetorial
        2. (Opcionalmente) combina com BM25 externo
        
        Para hybrid search real com BM25, considere:
        - Usar Weaviate (BM25 nativo)
        - Integrar Qdrant + Elasticsearch
        - Usar sparse vectors do Qdrant (feature experimental)
        
        Args:
            query: Query em texto
            query_embedding: Embedding da query
            k: Número de resultados
            weights: (peso_vetorial, peso_texto)
            filter_dict: Filtros
            index_name: Nome da coleção
            
        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name
        
        # Por enquanto, apenas busca vetorial com peso maior
        # TODO: Integrar com BM25 quando disponível
        
        logger.info(
            f"Hybrid search no Qdrant usa apenas busca vetorial. "
            f"Weight vetorial: {weights[0]}, Weight texto: {weights[1]}"
        )
        
        results = self.vector_search(
            query_embedding=query_embedding,
            k=k,
            filter_dict=filter_dict,
            index_name=index_name
        )
        
        # Ajusta scores com peso
        for result in results:
            result.score *= weights[0]
            result.search_type = 'hybrid'
        
        return results
    
    def delete_documents(
        self,
        document_ids: List[str],
        index_name: Optional[str] = None
    ):
        """
        Remove documentos do Qdrant.
        
        Args:
            document_ids: Lista de IDs
            index_name: Nome da coleção
        """
        index_name = index_name or self.default_index_name
        
        # Converte IDs para hash int64
        point_ids = [hash(doc_id) % (2**63) for doc_id in document_ids]
        
        self.client.delete(
            collection_name=index_name,
            points_selector=point_ids
        )
        
        logger.info(f"Removidos {len(document_ids)} documentos da coleção {index_name}")
    
    def delete_index(
        self,
        index_name: Optional[str] = None
    ):
        """
        Remove uma coleção do Qdrant.
        
        Args:
            index_name: Nome da coleção
        """
        index_name = index_name or self.default_index_name
        
        try:
            self.client.delete_collection(index_name)
            logger.info(f"Coleção {index_name} removida")
        except Exception as e:
            logger.error(f"Erro ao remover coleção {index_name}: {e}")
    
    def get_stats(
        self,
        index_name: Optional[str] = None
    ) -> VectorStoreStats:
        """
        Retorna estatísticas da coleção Qdrant.
        
        Args:
            index_name: Nome da coleção
            
        Returns:
            VectorStoreStats
        """
        index_name = index_name or self.default_index_name
        
        try:
            # Usa REST API direta para evitar problemas de Pydantic validation
            from qdrant_client.http.models import CollectionInfo
            info = self.client.get_collection(index_name)
            
            # Acessa campos com segurança
            num_docs = getattr(info, 'points_count', 0) or 0
            indexed_count = getattr(info, 'indexed_vectors_count', 0) or 0
            
            # Tenta extrair distância de forma segura
            distance_metric = 'cosine'
            try:
                if hasattr(info, 'config') and hasattr(info.config, 'params'):
                    if hasattr(info.config.params, 'vectors'):
                        if hasattr(info.config.params.vectors, 'distance'):
                            distance_metric = info.config.params.vectors.distance.name.lower()
            except:
                pass
            
            return VectorStoreStats(
                num_documents=num_docs,
                index_size_mb=0,  # Qdrant não expõe tamanho facilmente
                vector_dimensions=self.embedding_dim,
                distance_metric=distance_metric,
                additional_info={
                    'indexed_vectors_count': indexed_count
                }
            )
        except Exception as e:
            logger.warning(f"Não foi possível obter estatísticas detalhadas: {e}")
            # Tenta método alternativo usando count
            try:
                count = self.client.count(collection_name=index_name)
                return VectorStoreStats(
                    num_documents=count.count if hasattr(count, 'count') else 0,
                    index_size_mb=0,
                    vector_dimensions=self.embedding_dim,
                    distance_metric='cosine'
                )
            except:
                return VectorStoreStats(
                    num_documents=0,
                    index_size_mb=0,
                    vector_dimensions=self.embedding_dim,
                    distance_metric='unknown'
                )
    
    def health_check(self) -> bool:
        """
        Verifica se Qdrant está acessível.
        
        Returns:
            True se saudável
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check falhou: {e}")
            return False
    
    def _build_filter(self, filter_dict: Dict[str, Any]) -> Filter:
        """
        Constrói filtro Qdrant a partir de dict.
        
        Args:
            filter_dict: Dict com filtros (ex: {'source': 'doc1.pdf'})
            
        Returns:
            Filter do Qdrant
        """
        conditions = []
        
        for key, value in filter_dict.items():
            conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
            )
        
        return Filter(must=conditions) if conditions else None
    
    def _convert_results(
        self,
        results: List[ScoredPoint],
        search_type: str
    ) -> List[SearchResult]:
        """
        Converte resultados Qdrant para SearchResult.
        
        Args:
            results: Lista de ScoredPoint do Qdrant
            search_type: Tipo de busca
            
        Returns:
            Lista de SearchResult
        """
        search_results = []
        
        for point in results:
            payload = point.payload
            
            search_results.append(SearchResult(
                content=payload.get('content', ''),
                source=payload.get('source', 'unknown'),
                page=payload.get('page', 0),
                score=point.score,
                search_type=search_type,
                metadata={k: v for k, v in payload.items() 
                         if k not in ['content', 'source', 'page']}
            ))
        
        return search_results


# Factory function para facilitar criação
def create_qdrant_vector_store(
    host: str = None,
    port: int = None,
    embedding_dim: int = 3072
) -> QdrantVectorStore:
    """
    Cria instância de QdrantVectorStore com configurações do settings.
    
    Args:
        host: Host do Qdrant (usa settings se não especificado)
        port: Porta do Qdrant (usa settings se não especificado)
        embedding_dim: Dimensão dos embeddings
        
    Returns:
        QdrantVectorStore configurado
    """
    return QdrantVectorStore(
        host=host or getattr(settings, 'qdrant_host', 'localhost'),
        port=port or getattr(settings, 'qdrant_port', 6333),
        embedding_dim=embedding_dim
    )

