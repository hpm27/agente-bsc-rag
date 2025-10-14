"""
Re-ranking de resultados de busca usando Cohere com suporte a MMR (Maximal Marginal Relevance).
"""
from typing import List, Dict, Any, Literal, Tuple
import cohere
from loguru import logger
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import settings


class CohereReranker:
    """Re-ranker usando Cohere Rerank API com suporte multilíngue."""
    
    def __init__(self):
        """Inicializa o cliente Cohere."""
        self.client = cohere.Client(settings.cohere_api_key)
        self.model = "rerank-multilingual-v3.0"  # Suporta 100+ idiomas
        self.enabled = True  # Sempre ativo se API key está presente
        logger.info(f"[INIT] Cohere Reranker inicializado (modelo: {self.model})")
    
    def _detect_language(self, text: str) -> Literal["pt-br", "en", "other"]:
        """
        Detecta o idioma do texto usando heurística simples.
        
        Args:
            text: Texto para detectar idioma
            
        Returns:
            "pt-br", "en" ou "other"
        """
        text_lower = text.lower()
        
        # Acentuação portuguesa (check mais forte)
        has_pt_accents = bool(re.search(r'[áàâãéêíóôõúüç]', text_lower))
        
        # Palavras comuns em português (expandido)
        pt_keywords = [
            "o que", "como", "por que", "porque", "quando", "onde", "qual", "quais",
            "é", "são", "está", "estão", "foi", "foram", "ser", "estar",
            "implementar", "gestão", "estratégia", "plano", "objetivo"
        ]
        
        # Palavras exclusivas EN
        en_keywords = ["what", "how", "why", "when", "where", "which", "is", "are", "was", "were"]
        
        # Contagem de keywords
        pt_count = sum(1 for kw in pt_keywords if kw in text_lower)
        en_count = sum(1 for kw in en_keywords if kw in text_lower)
        
        # Decisão
        if has_pt_accents:
            return "pt-br"
        elif pt_count >= 1 and en_count == 0:
            return "pt-br"
        elif en_count >= 1 and pt_count == 0:
            return "en"
        elif pt_count > en_count:
            return "pt-br"
        elif en_count > pt_count:
            return "en"
        else:
            return "other"
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = None,
        adaptive_multilingual: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rankeia documentos baseado na relevância para a query.
        
        Args:
            query: Query do usuário
            documents: Lista de documentos recuperados
            top_n: Número de documentos a retornar (None = todos)
            adaptive_multilingual: Se True, ajusta parâmetros para cross-lingual
            
        Returns:
            Documentos reordenados por relevância
        """
        if not documents:
            return []
        
        top_n = top_n or settings.top_n_rerank
        
        # Detecção de idioma para otimização multilíngue
        query_lang = self._detect_language(query) if adaptive_multilingual else "other"
        
        # Ajuste adaptativo: em cenários cross-lingual, aumentar top_n para compensar perda de precisão
        if adaptive_multilingual and query_lang == "pt-br":
            # Query em PT + docs em EN (provável) → solicitar +20% de documentos
            adjusted_top_n = min(int(top_n * 1.2), len(documents))
            logger.debug(f"[ADAPTIVE] Query PT-BR detectada, ajustando top_n: {top_n} -> {adjusted_top_n}")
        else:
            adjusted_top_n = min(top_n, len(documents))
        
        # Extrai textos dos documentos
        texts = [doc["content"] for doc in documents]
        
        try:
            # Chama API de rerank (return_documents removido - deprecated em Cohere v5+)
            results = self.client.rerank(
                model=self.model,
                query=query,
                documents=texts,
                top_n=adjusted_top_n
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
    
    def _calculate_similarity(
        self,
        embeddings_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Calcula matriz de similaridade cosine entre embeddings.
        
        Args:
            embeddings_matrix: Matrix de embeddings (n_docs, embedding_dim)
            
        Returns:
            Matriz de similaridade (n_docs, n_docs)
        """
        return cosine_similarity(embeddings_matrix)
    
    def _boost_by_metadata(
        self,
        documents: List[Dict[str, Any]],
        selected_indices: List[int],
        source_boost: float = 0.2,
        perspective_boost: float = 0.15
    ) -> Dict[int, float]:
        """
        Calcula boost de score baseado em diversidade de metadata.
        
        Estratégia:
        - Boost se documento tem source diferente dos já selecionados (+20%)
        - Boost se documento tem perspective BSC diferente (+15%)
        
        Args:
            documents: Lista de documentos
            selected_indices: Índices dos documentos já selecionados
            source_boost: Boost para sources diferentes (padrão: 0.2)
            perspective_boost: Boost para perspectives diferentes (padrão: 0.15)
            
        Returns:
            Dict {doc_index: boost_multiplier}
        """
        boost_scores = {}
        
        # Coletar sources e perspectives dos docs já selecionados
        selected_sources = set()
        selected_perspectives = set()
        
        for idx in selected_indices:
            doc = documents[idx]
            metadata = doc.get("metadata", {})
            
            source = metadata.get("source", "unknown")
            selected_sources.add(source)
            
            # Tentar inferir perspective do context ou metadata
            context_pt = metadata.get("context_pt", "")
            context_en = metadata.get("context_en", "")
            context = (context_pt + " " + context_en).lower()
            
            # Detectar perspectiva BSC
            if any(kw in context for kw in ["financeira", "financial", "revenue", "lucro"]):
                selected_perspectives.add("financial")
            elif any(kw in context for kw in ["cliente", "customer", "satisfação", "satisfaction"]):
                selected_perspectives.add("customer")
            elif any(kw in context for kw in ["processo", "process", "operação", "operation"]):
                selected_perspectives.add("process")
            elif any(kw in context for kw in ["aprendizado", "learning", "crescimento", "growth"]):
                selected_perspectives.add("learning")
        
        # Calcular boost para cada documento
        for idx, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            boost = 1.0  # Multiplicador base
            
            # Boost por source diferente
            source = metadata.get("source", "unknown")
            if source not in selected_sources:
                boost += source_boost
            
            # Boost por perspective diferente
            context_pt = metadata.get("context_pt", "")
            context_en = metadata.get("context_en", "")
            context = (context_pt + " " + context_en).lower()
            
            doc_perspectives = set()
            if any(kw in context for kw in ["financeira", "financial", "revenue", "lucro"]):
                doc_perspectives.add("financial")
            if any(kw in context for kw in ["cliente", "customer", "satisfação", "satisfaction"]):
                doc_perspectives.add("customer")
            if any(kw in context for kw in ["processo", "process", "operação", "operation"]):
                doc_perspectives.add("process")
            if any(kw in context for kw in ["aprendizado", "learning", "crescimento", "growth"]):
                doc_perspectives.add("learning")
            
            # Boost se tem perspective não selecionada
            if doc_perspectives and not doc_perspectives.intersection(selected_perspectives):
                boost += perspective_boost
            
            boost_scores[idx] = boost
        
        return boost_scores
    
    def calculate_adaptive_topn(
        self,
        query: str,
        base_top_n: int = 10
    ) -> int:
        """
        Calcula top_n adaptativo baseado na complexidade da query.
        
        Reutiliza heurísticas de complexidade do QueryDecomposer:
        - Score 0-1: top_n = 5 (queries simples)
        - Score 2-3: top_n = 10 (queries moderadas)
        - Score 4+: top_n = 15 (queries complexas)
        
        Args:
            query: Query do usuário
            base_top_n: Valor base (padrão: 10)
            
        Returns:
            top_n ajustado baseado em complexidade
        """
        query_lower = query.lower()
        complexity_score = 0
        
        # Heurística 1: Palavras de ligação
        linking_words = ["e", "também", "além", "ademais", "considerando", "levando em conta"]
        for word in linking_words:
            # Usar word boundaries para evitar falsos positivos
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, query_lower):
                complexity_score += 1
                break
        
        # Heurística 2: Múltiplas perspectivas BSC
        perspectives = ["financeira", "cliente", "processo", "aprendizado", "crescimento"]
        perspective_count = sum(1 for p in perspectives if p in query_lower)
        if perspective_count >= 2:
            complexity_score += 2
        elif perspective_count == 1:
            complexity_score += 0  # Neutro
        
        # Heurística 3: Múltiplas perguntas
        question_words = ["como", "por que", "quando", "onde", "qual", "quais", "o que"]
        question_count = sum(1 for qw in question_words if qw in query_lower)
        if question_count >= 2:
            complexity_score += 1
        
        # Heurística 4: Palavras de complexidade
        complexity_words = ["implementar", "integrar", "relação", "impacto", "diferença", "comparar"]
        if any(cw in query_lower for cw in complexity_words):
            complexity_score += 1
        
        # Mapear score para top_n
        if complexity_score <= 1:
            return 5  # Queries simples
        elif complexity_score <= 3:
            return base_top_n  # Queries moderadas
        else:
            return 15  # Queries complexas
    
    def rerank_with_diversity(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        embeddings: np.ndarray,
        top_n: int = None,
        lambda_param: float = None,
        diversity_threshold: float = None,
        enable_metadata_boost: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rankeia documentos usando MMR (Maximal Marginal Relevance) para diversidade.
        
        Algoritmo MMR:
        1. Recebe docs re-ranked pelo Cohere (com relevance_score)
        2. Itera selecionando doc com maior score MMR:
           MMR = λ * relevance - (1-λ) * max_similarity_to_selected
        3. λ controla trade-off: λ=1 (só relevância), λ=0 (só diversidade)
        
        Args:
            query: Query do usuário
            documents: Documentos re-ranked pelo Cohere
            embeddings: Embeddings dos documentos (n_docs, embedding_dim)
            top_n: Número de documentos finais (None = adaptativo)
            lambda_param: Balanceamento relevância vs diversidade (padrão: settings)
            diversity_threshold: Similaridade máxima permitida (padrão: settings)
            enable_metadata_boost: Se True, aplica boost por metadata
            
        Returns:
            Documentos re-rankeados com diversidade
            
        Example:
            >>> reranker = CohereReranker()
            >>> # Após retrieval e rerank inicial
            >>> diverse_docs = reranker.rerank_with_diversity(
            ...     query="Como implementar BSC?",
            ...     documents=reranked_docs,
            ...     embeddings=doc_embeddings,
            ...     top_n=5
            ... )
        """
        if not documents or len(documents) == 0:
            return []
        
        if embeddings.shape[0] != len(documents):
            logger.error(f"[MMR] Mismatch: {embeddings.shape[0]} embeddings vs {len(documents)} docs")
            return documents[:top_n] if top_n else documents
        
        # Configurações
        lambda_param = lambda_param if lambda_param is not None else settings.diversity_lambda
        diversity_threshold = diversity_threshold if diversity_threshold is not None else settings.diversity_threshold
        
        # Top-N adaptativo se não especificado
        if top_n is None:
            top_n = self.calculate_adaptive_topn(query)
            logger.debug(f"[MMR] Top-N adaptativo: {top_n}")
        
        top_n = min(top_n, len(documents))
        
        # Normalizar embeddings para cosine similarity
        if np.linalg.norm(embeddings[0]) > 1.1:  # Check se já normalizado
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Calcular matriz de similaridade documento-documento
        doc_similarities = self._calculate_similarity(embeddings)
        
        # Extrair relevance scores (assumindo que Cohere já re-rankeou)
        relevance_scores = np.array([
            doc.get("rerank_score", 0.5) for doc in documents
        ])
        
        # MMR Algorithm
        selected_indices = []
        remaining_indices = list(range(len(documents)))
        
        while len(selected_indices) < top_n and remaining_indices:
            mmr_scores = []
            
            # Calcular boost por metadata (se habilitado)
            if enable_metadata_boost:
                metadata_boosts = self._boost_by_metadata(documents, selected_indices)
            else:
                metadata_boosts = {i: 1.0 for i in remaining_indices}
            
            for idx in remaining_indices:
                relevance = relevance_scores[idx]
                
                # Aplicar metadata boost
                boosted_relevance = relevance * metadata_boosts.get(idx, 1.0)
                
                if not selected_indices:
                    # Primeiro documento: apenas relevância
                    mmr_score = boosted_relevance
                else:
                    # Calcular max similarity com docs já selecionados
                    max_similarity = np.max(doc_similarities[idx, selected_indices])
                    
                    # MMR formula: λ * relevance - (1-λ) * max_similarity
                    mmr_score = lambda_param * boosted_relevance - (1 - lambda_param) * max_similarity
                
                mmr_scores.append(mmr_score)
            
            # Selecionar documento com maior MMR score
            best_idx_in_remaining = np.argmax(mmr_scores)
            best_idx = remaining_indices[best_idx_in_remaining]
            
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        # Reordenar documentos
        diverse_docs = []
        for rank, idx in enumerate(selected_indices):
            doc = documents[idx].copy()
            doc["mmr_rank"] = rank
            doc["original_rerank_rank"] = idx
            diverse_docs.append(doc)
        
        logger.info(f"[MMR] Re-rankeados {len(diverse_docs)} documentos com diversidade (λ={lambda_param:.2f})")
        return diverse_docs


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
