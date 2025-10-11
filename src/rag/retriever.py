"""
Retriever que integra vector store, embeddings e re-ranking.
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from src.rag.vector_store_factory import create_vector_store
from src.rag.base_vector_store import BaseVectorStore, SearchResult
from src.rag.embeddings import EmbeddingManager
from src.rag.reranker import CohereReranker, FusionReranker
from config.settings import settings


class BSCRetriever:
    """Retriever otimizado para documentos BSC com Hybrid Search."""
    
    def __init__(self, vector_store: Optional[BaseVectorStore] = None):
        """
        Inicializa o retriever.
        
        Args:
            vector_store: Vector store a usar (se None, cria via factory)
        """
        self.vector_store = vector_store or create_vector_store()
        self.embedding_manager = EmbeddingManager()
        self.cohere_reranker = CohereReranker()
        self.fusion_reranker = FusionReranker()
        
        logger.info(f"BSC Retriever inicializado com {type(self.vector_store).__name__}")
    
    def retrieve(
        self,
        query: str,
        k: int = None,
        use_rerank: bool = True,
        use_hybrid: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Recupera documentos relevantes para a query com Hybrid Search.
        
        Args:
            query: Query do usuário
            k: Número de documentos a retornar
            use_rerank: Se deve usar re-ranking Cohere
            use_hybrid: Se deve usar busca híbrida (semantic + BM25)
            filters: Filtros de metadados (ex: {"source": "kaplan.pdf"})
            
        Returns:
            Lista de documentos relevantes (SearchResult objects)
        """
        k = k or settings.top_k_retrieval
        
        # Gera embedding da query
        # embed_text ja retorna lista (nao precisa .tolist())
        query_embedding = self.embedding_manager.embed_text(query)
        
        if use_hybrid:
            # Busca híbrida (semântica + BM25 keyword)
            # Converter alpha (0.0-1.0) para weights (peso_vector, peso_text)
            weight_vector = settings.hybrid_search_weight_semantic
            weight_text = 1.0 - weight_vector
            
            results = self.vector_store.hybrid_search(
                query=query,
                query_embedding=query_embedding,
                k=k * 2,  # Pega mais para re-rankear
                weights=(weight_vector, weight_text),
                filter_dict=filters
            )
        else:
            # Apenas busca vetorial semântica
            results = self.vector_store.vector_search(
                query_embedding=query_embedding,
                k=k * 2,
                filter_dict=filters
            )
        
        # Re-ranking com Cohere
        if use_rerank and len(results) > 0:
            # Converte SearchResult para dict para Cohere (inclui source e page)
            docs_dict = [
                {
                    "content": r.content,
                    "source": r.source,
                    "page": r.page,
                    "metadata": r.metadata,
                    "score": r.score
                }
                for r in results
            ]
            
            reranked_docs = self.cohere_reranker.rerank(
                query=query,
                documents=docs_dict,
                top_n=k
            )
            
            # Converte de volta para SearchResult
            results = [
                SearchResult(
                    content=doc["content"],
                    source=doc.get("source", "unknown"),
                    page=doc.get("page", 0),
                    score=doc.get("rerank_score", doc["score"]),
                    search_type="reranked",
                    metadata=doc["metadata"]
                )
                for doc in reranked_docs
            ]
        else:
            results = results[:k]
        
        logger.info(f"Recuperados {len(results)} documentos para query: '{query[:50]}...'")
        return results
    
    def retrieve_with_context(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera documentos considerando histórico da conversa.
        
        Args:
            query: Query atual
            conversation_history: Histórico de mensagens
            k: Número de documentos
            
        Returns:
            Documentos relevantes
        """
        # Enriquece query com contexto da conversa
        if conversation_history:
            context_queries = [msg["content"] for msg in conversation_history[-3:]]
            enriched_query = " ".join(context_queries + [query])
        else:
            enriched_query = query
        
        return self.retrieve(enriched_query, k=k)
    
    def retrieve_multi_query(
        self,
        queries: List[str],
        k: int = None
    ) -> List[SearchResult]:
        """
        Recupera documentos para múltiplas queries e combina com RRF.
        
        Args:
            queries: Lista de queries
            k: Número total de documentos
            
        Returns:
            Documentos combinados e ranqueados
        """
        k = k or settings.top_k_retrieval
        
        all_results = []
        for query in queries:
            results = self.retrieve(query, k=k, use_rerank=False)
            # Converte SearchResult para dict para RRF (inclui source e page)
            results_dict = [
                {
                    "content": r.content,
                    "source": r.source,
                    "page": r.page,
                    "metadata": r.metadata,
                    "score": r.score
                }
                for r in results
            ]
            all_results.append(results_dict)
        
        # Fuse resultados com RRF
        fused_dicts = self.fusion_reranker.fuse(all_results, top_n=k)
        
        # Converte de volta para SearchResult
        fused = [
            SearchResult(
                content=doc["content"],
                source=doc.get("source", "unknown"),
                page=doc.get("page", 0),
                score=doc.get("rrf_score", doc["score"]),
                search_type="hybrid",
                metadata=doc["metadata"]
            )
            for doc in fused_dicts
        ]
        
        return fused
    
    def retrieve_by_perspective(
        self,
        query: str,
        perspective: str,
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera documentos focados em uma perspectiva específica do BSC.
        
        Args:
            query: Query do usuário
            perspective: Perspectiva BSC (financeira, cliente, processos, aprendizado)
            k: Número de documentos
            
        Returns:
            Documentos relevantes para a perspectiva
        """
        # Enriquece query com perspectiva
        perspective_keywords = {
            "financeira": "receita lucro ROI custos financeiro",
            "cliente": "satisfação NPS retenção valor cliente",
            "processos": "eficiência qualidade processos operacional",
            "aprendizado": "capacitação inovação conhecimento crescimento"
        }
        
        keywords = perspective_keywords.get(perspective.lower(), "")
        enriched_query = f"{query} {keywords}"
        
        return self.retrieve(enriched_query, k=k)
    
    def get_similar_documents(
        self,
        document_id: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Encontra documentos similares a um documento específico.
        
        Args:
            document_id: ID do documento de referência
            k: Número de documentos similares
            
        Returns:
            Documentos similares
        """
        # Recupera documento original
        # (implementação simplificada - em produção, buscar do Redis)
        # Por ora, retorna lista vazia
        logger.warning("get_similar_documents não implementado completamente")
        return []
    
    def format_context(
        self,
        documents: List[SearchResult],
        max_tokens: int = 32000
    ) -> str:
        """
        Formata documentos recuperados como contexto para o LLM.
        
        Args:
            documents: Documentos recuperados (SearchResult objects)
            max_tokens: Número máximo de tokens (aproximado)
            
        Returns:
            Contexto formatado
        """
        context_parts = []
        current_tokens = 0
        
        for i, doc in enumerate(documents, 1):
            # Estimativa grosseira: 1 token ≈ 4 caracteres
            doc_tokens = len(doc.content) // 4
            
            if current_tokens + doc_tokens > max_tokens:
                break
            
            # Formata documento
            # Usa campos diretos do SearchResult (source e page nao estao em metadata)
            source = doc.source if hasattr(doc, 'source') else doc.metadata.get("source", "unknown")
            page = doc.page if hasattr(doc, 'page') else doc.metadata.get("page", "?")
            score = doc.score
            
            # Para arquivos .md, usar "Seção" ao invés de "Página"
            page_label = "Seção" if source.endswith('.md') else "Página"
            
            context_parts.append(
                f"[Documento {i}] (Fonte: {source}, {page_label}: {page}, Relevância: {score:.3f})\n"
                f"{doc.content}\n"
            )
            
            current_tokens += doc_tokens
        
        context = "\n---\n".join(context_parts)
        
        logger.debug(f"Contexto formatado com {len(context_parts)} documentos (~{current_tokens} tokens)")
        return context
