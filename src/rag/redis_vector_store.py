"""
Implementação de Vector Store usando Redis Stack.

NOTA: Esta implementação está mantida para compatibilidade,
mas Qdrant ou Weaviate são recomendados para novos projetos RAG.

Redis é excelente para:
- Prototipagem rápida
- Quando já se usa Redis no stack
- Caching + vector search combinado

Limitações:
- Sem BM25/hybrid search robusto
- Menos features RAG-específicas
- Integração LangChain menos madura
"""

import redis
from redis.commands.search.field import TextField, VectorField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

from .base_vector_store import BaseVectorStore, SearchResult, VectorStoreStats
from config.settings import settings


class RedisVectorStore(BaseVectorStore):
    """Vector Store implementado com Redis Stack."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        embedding_dim: int = 3072,
        default_index_name: str = "bsc_documents"
    ):
        """
        Inicializa conexão com Redis.
        
        Args:
            host: Host do Redis
            port: Porta do Redis
            password: Senha (opcional)
            db: Database number
            embedding_dim: Dimensão dos embeddings
            default_index_name: Nome padrão do índice
        """
        super().__init__(embedding_dim)
        
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=False
        )
        
        self.default_index_name = default_index_name
        
        logger.info(f"Conectado ao Redis em {host}:{port}")
    
    def create_index(
        self,
        index_name: str = None,
        force_recreate: bool = False,
        algorithm: str = "FLAT",  # ou "HNSW"
        **kwargs
    ):
        """
        Cria índice Redis para busca vetorial e full-text.
        
        Args:
            index_name: Nome do índice
            force_recreate: Se True, recria mesmo se existir
            algorithm: "FLAT" ou "HNSW"
            **kwargs: Parâmetros adicionais do algoritmo
        """
        index_name = index_name or self.default_index_name
        
        try:
            # Verifica se índice existe
            self.client.ft(index_name).info()
            if force_recreate:
                logger.info(f"Removendo índice existente: {index_name}")
                self.client.ft(index_name).dropindex()
            else:
                logger.info(f"Índice {index_name} já existe")
                return
        except:
            pass
        
        # Define schema
        schema = (
            TextField("content", weight=1.0),
            TextField("source", weight=0.5),
            NumericField("page"),
            VectorField(
                "embedding",
                algorithm,
                {
                    "TYPE": "FLOAT32",
                    "DIM": self.embedding_dim,
                    "DISTANCE_METRIC": "COSINE",
                    **kwargs
                }
            )
        )
        
        # Cria índice
        definition = IndexDefinition(
            prefix=["doc:"],
            index_type=IndexType.HASH
        )
        
        self.client.ft(index_name).create_index(
            fields=schema,
            definition=definition
        )
        
        logger.info(f"Índice {index_name} criado com sucesso")
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[np.ndarray],
        index_name: Optional[str] = None
    ):
        """
        Adiciona documentos ao Redis.
        
        Args:
            documents: Lista de documentos
            embeddings: Lista de embeddings
            index_name: Nome do índice (não usado no Redis, mantém compatibilidade)
        """
        pipeline = self.client.pipeline()
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = f"doc:{doc.get('id', i)}"
            
            # Prepara dados
            data = {
                "content": doc["content"],
                "source": doc.get("source", "unknown"),
                "page": doc.get("page", 0),
                "embedding": embedding.astype(np.float32).tobytes()
            }
            
            # Adiciona metadados customizados
            if 'metadata' in doc and doc['metadata']:
                for key, value in doc['metadata'].items():
                    data[f"meta_{key}"] = str(value)
            
            # Adiciona ao pipeline
            pipeline.hset(doc_id, mapping=data)
        
        # Executa pipeline
        pipeline.execute()
        logger.info(f"Adicionados {len(documents)} documentos ao Redis")
    
    def vector_search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Busca vetorial no Redis.
        
        Args:
            query_embedding: Embedding da query
            k: Número de resultados
            filter_dict: Filtros (limitado no Redis)
            index_name: Nome do índice
            
        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name
        
        # Prepara query vetorial
        query_vector = query_embedding.astype(np.float32).tobytes()
        
        # Cria query (filtros são limitados no Redis)
        q = Query(f"*=>[KNN {k} @embedding $vec AS score]").return_fields(
            "content", "source", "page", "score"
        ).sort_by("score").dialect(2)
        
        # Executa busca
        results = self.client.ft(index_name).search(
            q,
            query_params={"vec": query_vector}
        )
        
        # Converte resultados
        return self._convert_results(results.docs, search_type='vector')
    
    def text_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Busca por texto (full-text) no Redis.
        
        Args:
            query: Query em texto
            k: Número de resultados
            filter_dict: Filtros
            index_name: Nome do índice
            
        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name
        
        # Cria query de texto
        q = Query(query).return_fields(
            "content", "source", "page"
        ).paging(0, k)
        
        # Executa busca
        results = self.client.ft(index_name).search(q)
        
        # Converte resultados
        return self._convert_results(results.docs, search_type='text')
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: np.ndarray,
        k: int = 10,
        weights: Tuple[float, float] = (0.7, 0.3),
        filter_dict: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Busca híbrida (semântica + texto) no Redis.
        
        Combina vector search e text search manualmente,
        pois Redis não tem hybrid search nativo como Weaviate.
        
        Args:
            query: Query em texto
            query_embedding: Embedding da query
            k: Número de resultados
            weights: (peso_vetorial, peso_texto)
            filter_dict: Filtros
            index_name: Nome do índice
            
        Returns:
            Lista de SearchResult
        """
        index_name = index_name or self.default_index_name
        
        # Busca vetorial
        vector_results = self.vector_search(
            query_embedding,
            k=k*2,
            filter_dict=filter_dict,
            index_name=index_name
        )
        
        # Busca por texto
        text_results = self.text_search(
            query,
            k=k*2,
            filter_dict=filter_dict,
            index_name=index_name
        )
        
        # Combina resultados
        combined = {}
        
        # Adiciona resultados vetoriais
        for result in vector_results:
            key = f"{result.source}:{result.page}"
            combined[key] = SearchResult(
                content=result.content,
                source=result.source,
                page=result.page,
                score=result.score * weights[0],
                search_type='hybrid',
                metadata=result.metadata
            )
        
        # Adiciona/atualiza com resultados de texto
        for result in text_results:
            key = f"{result.source}:{result.page}"
            if key in combined:
                combined[key].score += result.score * weights[1]
            else:
                combined[key] = SearchResult(
                    content=result.content,
                    source=result.source,
                    page=result.page,
                    score=result.score * weights[1],
                    search_type='hybrid',
                    metadata=result.metadata
                )
        
        # Ordena por score combinado
        results = sorted(
            combined.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return results[:k]
    
    def delete_documents(
        self,
        document_ids: List[str],
        index_name: Optional[str] = None
    ):
        """
        Remove documentos do Redis.
        
        Args:
            document_ids: Lista de IDs
            index_name: Nome do índice (não usado, compatibilidade)
        """
        pipeline = self.client.pipeline()
        
        for doc_id in document_ids:
            key = f"doc:{doc_id}"
            pipeline.delete(key)
        
        pipeline.execute()
        logger.info(f"Removidos {len(document_ids)} documentos do Redis")
    
    def delete_index(
        self,
        index_name: Optional[str] = None
    ):
        """
        Remove índice do Redis.
        
        Args:
            index_name: Nome do índice
        """
        index_name = index_name or self.default_index_name
        
        try:
            self.client.ft(index_name).dropindex()
            logger.info(f"Índice {index_name} removido")
        except Exception as e:
            logger.error(f"Erro ao remover índice: {e}")
    
    def get_stats(
        self,
        index_name: Optional[str] = None
    ) -> VectorStoreStats:
        """
        Retorna estatísticas do índice Redis.
        
        Args:
            index_name: Nome do índice
            
        Returns:
            VectorStoreStats
        """
        index_name = index_name or self.default_index_name
        
        try:
            info = self.client.ft(index_name).info()
            
            return VectorStoreStats(
                num_documents=int(info.get("num_docs", 0)),
                index_size_mb=float(info.get("inverted_sz_mb", 0)) + 
                             float(info.get("vector_index_sz_mb", 0)),
                vector_dimensions=self.embedding_dim,
                distance_metric='cosine',
                additional_info={
                    'num_terms': info.get("num_terms", 0),
                    'num_records': info.get("num_records", 0),
                }
            )
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return VectorStoreStats(
                num_documents=0,
                index_size_mb=0,
                vector_dimensions=self.embedding_dim,
                distance_metric='unknown'
            )
    
    def health_check(self) -> bool:
        """
        Verifica se Redis está acessível.
        
        Returns:
            True se saudável
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check falhou: {e}")
            return False
    
    def _convert_results(
        self,
        results: List[Any],
        search_type: str
    ) -> List[SearchResult]:
        """
        Converte resultados Redis para SearchResult.
        
        Args:
            results: Lista de documentos do Redis
            search_type: Tipo de busca
            
        Returns:
            Lista de SearchResult
        """
        search_results = []
        
        for doc in results:
            # Extrai metadados customizados
            metadata = {}
            for key in dir(doc):
                if key.startswith('meta_'):
                    metadata[key[5:]] = getattr(doc, key)
            
            search_results.append(SearchResult(
                content=getattr(doc, 'content', ''),
                source=getattr(doc, 'source', 'unknown'),
                page=int(getattr(doc, 'page', 0)),
                score=float(getattr(doc, 'score', 1.0)),
                search_type=search_type,
                metadata=metadata
            ))
        
        return search_results


# Factory function
def create_redis_vector_store(
    host: str = None,
    port: int = None,
    password: str = None,
    embedding_dim: int = 3072
) -> RedisVectorStore:
    """
    Cria instância de RedisVectorStore com configurações do settings.
    
    Args:
        host: Host do Redis (usa settings se não especificado)
        port: Porta do Redis (usa settings se não especificado)
        password: Senha (usa settings se não especificado)
        embedding_dim: Dimensão dos embeddings
        
    Returns:
        RedisVectorStore configurado
    """
    return RedisVectorStore(
        host=host or getattr(settings, 'redis_host', 'localhost'),
        port=port or getattr(settings, 'redis_port', 6379),
        password=password or getattr(settings, 'redis_password', None),
        embedding_dim=embedding_dim
    )

