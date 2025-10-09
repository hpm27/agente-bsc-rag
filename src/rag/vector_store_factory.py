"""
Factory para criar Vector Stores.

Facilita a troca entre diferentes implementações (Qdrant, Weaviate, Redis)
sem modificar código que usa o vector store.
"""

from typing import Literal
from loguru import logger

from .base_vector_store import BaseVectorStore
from .qdrant_vector_store import QdrantVectorStore
from .weaviate_vector_store import WeaviateVectorStore
from .redis_vector_store import RedisVectorStore
from config.settings import settings


VectorStoreType = Literal["qdrant", "weaviate", "redis"]


def create_vector_store(
    store_type: VectorStoreType = None,
    embedding_dim: int = 3072,
    **kwargs
) -> BaseVectorStore:
    """
    Factory para criar vector store.
    
    Args:
        store_type: Tipo de vector store ('qdrant', 'weaviate', 'redis')
                   Se None, usa configuração do settings
        embedding_dim: Dimensão dos embeddings
        **kwargs: Parâmetros específicos do vector store
        
    Returns:
        Instância de BaseVectorStore configurada
        
    Raises:
        ValueError: Se store_type não for suportado
        
    Examples:
        >>> # Usar configuração padrão
        >>> store = create_vector_store()
        
        >>> # Criar Qdrant explicitamente
        >>> store = create_vector_store('qdrant', embedding_dim=3072)
        
        >>> # Criar Weaviate com parâmetros customizados
        >>> store = create_vector_store('weaviate', host='10.0.0.1', port=8080)
    """
    # Usa configuração do settings se não especificado
    if store_type is None:
        store_type = getattr(settings, 'vector_store_type', 'qdrant').lower()
    
    store_type = store_type.lower()
    
    logger.info(f"Criando vector store: {store_type}")
    
    if store_type == 'qdrant':
        return QdrantVectorStore(
            host=kwargs.get('host', getattr(settings, 'qdrant_host', 'localhost')),
            port=kwargs.get('port', getattr(settings, 'qdrant_port', 6333)),
            embedding_dim=embedding_dim,
            default_index_name=kwargs.get('index_name', getattr(settings, 'vector_store_index', 'bsc_documents'))
        )
    
    elif store_type == 'weaviate':
        return WeaviateVectorStore(
            host=kwargs.get('host', getattr(settings, 'weaviate_host', 'localhost')),
            port=kwargs.get('port', getattr(settings, 'weaviate_port', 8080)),
            embedding_dim=embedding_dim,
            default_index_name=kwargs.get('index_name', getattr(settings, 'vector_store_index', 'BscDocuments'))
        )
    
    elif store_type == 'redis':
        return RedisVectorStore(
            host=kwargs.get('host', getattr(settings, 'redis_host', 'localhost')),
            port=kwargs.get('port', getattr(settings, 'redis_port', 6379)),
            password=kwargs.get('password', getattr(settings, 'redis_password', None)),
            embedding_dim=embedding_dim,
            default_index_name=kwargs.get('index_name', getattr(settings, 'vector_store_index', 'bsc_documents'))
        )
    
    else:
        raise ValueError(
            f"Tipo de vector store não suportado: {store_type}. "
            f"Opções válidas: 'qdrant', 'weaviate', 'redis'"
        )


def get_recommended_vector_store() -> VectorStoreType:
    """
    Retorna a recomendação de vector store baseado em 2025 best practices.
    
    Returns:
        Nome do vector store recomendado
    """
    return 'qdrant'


def compare_vector_stores() -> dict:
    """
    Retorna comparação entre vector stores para ajudar na escolha.
    
    Returns:
        Dict com comparação de features
    """
    return {
        'qdrant': {
            'performance': 9,
            'hybrid_search': 7,  # Requer implementação customizada
            'integration': 9,
            'ease_of_use': 9,
            'production_ready': 9,
            'best_for': 'RAG em produção, melhor performance geral',
            'pros': [
                'Excelente performance',
                'Integração LangChain nativa',
                'Filtros avançados',
                'Open-source ativo'
            ],
            'cons': [
                'Hybrid search requer integração externa',
                'BM25 não nativo'
            ]
        },
        'weaviate': {
            'performance': 8,
            'hybrid_search': 10,  # Hybrid nativo com BM25
            'integration': 8,
            'ease_of_use': 7,
            'production_ready': 9,
            'best_for': 'RAG avançado, hybrid search nativo crítico',
            'pros': [
                'Hybrid search nativo (BM25 + vetorial)',
                'Muitas features RAG',
                'GraphQL API',
                'Multi-modal'
            ],
            'cons': [
                'Mais complexo de configurar',
                'Maior uso de recursos',
                'Integração LangChain menos madura'
            ]
        },
        'redis': {
            'performance': 8,
            'hybrid_search': 5,  # Híbrido manual, sem BM25 robusto
            'integration': 6,
            'ease_of_use': 9,
            'production_ready': 7,
            'best_for': 'MVP rápido, já usa Redis no stack',
            'pros': [
                'Muito rápido',
                'Familiaridade',
                'Versátil (cache + vector)',
                'Fácil setup'
            ],
            'cons': [
                'Menos features RAG',
                'Sem BM25/hybrid robusto',
                'Integração LangChain limitada',
                'Não especializado em vectors'
            ]
        }
    }


def print_vector_store_comparison():
    """Imprime comparação formatada dos vector stores."""
    comparison = compare_vector_stores()
    
    print("\n" + "="*80)
    print("COMPARAÇÃO DE VECTOR STORES - 2025")
    print("="*80)
    
    for name, info in comparison.items():
        print(f"\n{name.upper()}")
        print("-" * 40)
        print(f"Performance:        {info['performance']}/10")
        print(f"Hybrid Search:      {info['hybrid_search']}/10")
        print(f"Integração:         {info['integration']}/10")
        print(f"Facilidade de Uso:  {info['ease_of_use']}/10")
        print(f"Production Ready:   {info['production_ready']}/10")
        print(f"\nMelhor para: {info['best_for']}")
        print(f"\nPrós:")
        for pro in info['pros']:
            print(f"  + {pro}")
        print(f"Contras:")
        for con in info['cons']:
            print(f"  - {con}")
    
    print("\n" + "="*80)
    print(f"RECOMENDAÇÃO 2025: {get_recommended_vector_store().upper()}")
    print("="*80 + "\n")


# Alias para retrocompatibilidade
RedisVectorStore = RedisVectorStore  # noqa


if __name__ == "__main__":
    # Exibe comparação quando executado diretamente
    print_vector_store_comparison()

