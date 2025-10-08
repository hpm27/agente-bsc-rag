"""
Re-ranking de resultados de busca usando Cohere.
"""
from typing import List, Dict, Any
import cohere
from loguru import logger

from config.settings import settings


class CohereReranker:
    """Re-ranker usando Cohere Rerank API."""
    
    def __init__(self):
        """Inicializa o cliente Cohere."""
        self.client = cohere.Client(settings.cohere_api_key)
        self.model = "rerank-multilingual-v3.0"  # Suporta português
        logger.info("Cohere Reranker inicializado")
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rankeia documentos baseado na relevância para a query.
        
        Args:
            query: Query do usuário
            documents: Lista de documentos recuperados
            top_n: Número de documentos a retornar (None = todos)
            
        Returns:
            Documentos reordenados por relevância
        """
        if not documents:
            return []
        
        top_n = top_n or settings.top_n_rerank
        
        # Extrai textos dos documentos
        texts = [doc["content"] for doc in documents]
        
        try:
            # Chama API de rerank
            results = self.client.rerank(
                model=self.model,
                query=query,
                documents=texts,
                top_n=min(top_n, len(documents)),
                return_documents=False
            )
            
            # Reordena documentos originais
            reranked_docs = []
            for result in results.results:
                doc = documents[result.index].copy()
                doc["rerank_score"] = result.relevance_score
                doc["original_rank"] = result.index
                reranked_docs.append(doc)
            
            logger.debug(f"Re-rankeados {len(reranked_docs)} documentos")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Erro no re-ranking: {e}")
            # Em caso de erro, retorna documentos originais
            return documents[:top_n]
    
    def rerank_with_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Re-rankeia e filtra por score mínimo.
        
        Args:
            query: Query do usuário
            documents: Lista de documentos
            threshold: Score mínimo para incluir documento
            
        Returns:
            Documentos filtrados e reordenados
        """
        reranked = self.rerank(query, documents, top_n=len(documents))
        
        # Filtra por threshold
        filtered = [
            doc for doc in reranked
            if doc.get("rerank_score", 0) >= threshold
        ]
        
        logger.debug(f"Filtrados {len(filtered)}/{len(reranked)} documentos (threshold={threshold})")
        return filtered


class FusionReranker:
    """Re-ranker usando Reciprocal Rank Fusion (RRF)."""
    
    def __init__(self, k: int = 60):
        """
        Inicializa o fusion reranker.
        
        Args:
            k: Parâmetro de suavização do RRF
        """
        self.k = k
    
    def fuse(
        self,
        results_list: List[List[Dict[str, Any]]],
        top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Combina múltiplas listas de resultados usando RRF.
        
        Args:
            results_list: Lista de listas de resultados
            top_n: Número de resultados finais
            
        Returns:
            Resultados fusionados e reordenados
        """
        # Calcula RRF score para cada documento
        doc_scores = {}
        
        for results in results_list:
            for rank, doc in enumerate(results, start=1):
                # Usa source+page como chave única
                key = f"{doc.get('source', '')}:{doc.get('page', 0)}"
                
                # RRF score: 1 / (k + rank)
                rrf_score = 1.0 / (self.k + rank)
                
                if key in doc_scores:
                    doc_scores[key]["rrf_score"] += rrf_score
                else:
                    doc_scores[key] = {
                        **doc,
                        "rrf_score": rrf_score
                    }
        
        # Ordena por RRF score
        fused = sorted(
            doc_scores.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )
        
        if top_n:
            fused = fused[:top_n]
        
        logger.debug(f"Fusionados resultados de {len(results_list)} fontes")
        return fused


class HybridReranker:
    """Combina Cohere Rerank com Fusion."""
    
    def __init__(self):
        """Inicializa os rerankers."""
        self.cohere_reranker = CohereReranker()
        self.fusion_reranker = FusionReranker()
    
    def rerank(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        text_results: List[Dict[str, Any]],
        top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rankeia combinando resultados vetoriais e de texto.
        
        Args:
            query: Query do usuário
            vector_results: Resultados da busca vetorial
            text_results: Resultados da busca por texto
            top_n: Número de resultados finais
            
        Returns:
            Resultados re-rankeados
        """
        top_n = top_n or settings.top_n_rerank
        
        # Primeiro: Fusion dos resultados
        fused = self.fusion_reranker.fuse(
            [vector_results, text_results],
            top_n=top_n * 2  # Pega mais para re-rankear
        )
        
        # Segundo: Cohere Rerank
        reranked = self.cohere_reranker.rerank(query, fused, top_n=top_n)
        
        return reranked
