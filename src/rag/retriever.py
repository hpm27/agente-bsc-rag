"""
Retriever que integra vector store, embeddings e re-ranking.
"""
from typing import List, Dict, Any
from loguru import logger

from src.rag.vector_store import RedisVectorStore
from src.rag.embeddings import EmbeddingManager
from src.rag.reranker import HybridReranker
from config.settings import settings


class BSCRetriever:
    """Retriever otimizado para documentos BSC."""
    
    def __init__(self):
        """Inicializa o retriever."""
        self.vector_store = RedisVectorStore()
        self.embedding_manager = EmbeddingManager()
        self.reranker = HybridReranker()
        
        logger.info("BSC Retriever inicializado")
    
    def retrieve(
        self,
        query: str,
        k: int = None,
        use_rerank: bool = True,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recupera documentos relevantes para a query.
        
        Args:
            query: Query do usuário
            k: Número de documentos a retornar
            use_rerank: Se deve usar re-ranking
            use_hybrid: Se deve usar busca híbrida
            
        Returns:
            Lista de documentos relevantes
        """
        k = k or settings.top_k_retrieval
        
        # Gera embedding da query
        query_embedding = self.embedding_manager.embed_text(query)
        
        if use_hybrid:
            # Busca híbrida (semântica + texto)
            results = self.vector_store.hybrid_search(
                query=query,
                query_embedding=query_embedding,
                k=k * 2,  # Pega mais para re-rankear
                weights=(
                    settings.hybrid_search_weight_semantic,
                    settings.hybrid_search_weight_bm25
                )
            )
        else:
            # Apenas busca vetorial
            results = self.vector_store.vector_search(
                query_embedding=query_embedding,
                k=k * 2
            )
        
        # Re-ranking
        if use_rerank and len(results) > 0:
            results = self.reranker.cohere_reranker.rerank(
                query=query,
                documents=results,
                top_n=k
            )
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
    ) -> List[Dict[str, Any]]:
        """
        Recupera documentos para múltiplas queries e combina resultados.
        
        Args:
            queries: Lista de queries
            k: Número total de documentos
            
        Returns:
            Documentos combinados
        """
        k = k or settings.top_k_retrieval
        
        all_results = []
        for query in queries:
            results = self.retrieve(query, k=k, use_rerank=False)
            all_results.append(results)
        
        # Fuse resultados
        fused = self.reranker.fusion_reranker.fuse(all_results, top_n=k)
        
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
        documents: List[Dict[str, Any]],
        max_tokens: int = 4000
    ) -> str:
        """
        Formata documentos recuperados como contexto para o LLM.
        
        Args:
            documents: Documentos recuperados
            max_tokens: Número máximo de tokens (aproximado)
            
        Returns:
            Contexto formatado
        """
        context_parts = []
        current_tokens = 0
        
        for i, doc in enumerate(documents, 1):
            # Estimativa grosseira: 1 token ≈ 4 caracteres
            doc_tokens = len(doc["content"]) // 4
            
            if current_tokens + doc_tokens > max_tokens:
                break
            
            # Formata documento
            source = doc.get("source", "unknown")
            page = doc.get("page", "?")
            score = doc.get("rerank_score", doc.get("combined_score", doc.get("score", 0)))
            
            context_parts.append(
                f"[Documento {i}] (Fonte: {source}, Página: {page}, Relevância: {score:.2f})\n"
                f"{doc['content']}\n"
            )
            
            current_tokens += doc_tokens
        
        context = "\n---\n".join(context_parts)
        
        logger.debug(f"Contexto formatado com {len(context_parts)} documentos (~{current_tokens} tokens)")
        return context
