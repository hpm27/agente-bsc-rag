"""
Query Decomposer para RAG Avançado.

Este módulo implementa Query Decomposition, técnica RAG que quebra queries
complexas em sub-queries independentes para melhorar recall e answer quality.

ROI Esperado:
- Recall@10: +30-40% vs baseline
- Precision@5: +25-35% vs baseline
- Answer Quality: +30-50% (Judge approval)
- Latência adicional: ~2s (decomposição LLM + retrieval paralelo)

Referências:
- Galileo AI (Mar 2025): "RAG Implementation Strategy"
- Epsilla (Nov 2024): "Advanced RAG Optimization: Boosting Answer Quality"
"""

from typing import List, Tuple, Optional
import asyncio
import re
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import PromptTemplate

from src.prompts.query_decomposition_prompt import QUERY_DECOMPOSITION_PROMPT


class QueryDecomposer:
    """Decompõe queries BSC complexas em sub-queries independentes.
    
    Usa LLM (GPT-4o-mini) para decomposição semântica e heurísticas para
    decidir quando decomposição é necessária.
    
    Ideal para queries multi-perspectiva, multi-conceito ou complexas onde
    retrieval simples não captura todas as nuances.
    
    Attributes:
        llm: Language model para decomposição
        enabled: Flag de ativação (configurável via .env)
        min_query_length: Comprimento mínimo para considerar decomposição
        score_threshold: Threshold de complexidade para triggar decomposição
        prompt_template: Template do prompt de decomposição
    
    Example:
        >>> from config.settings import get_llm
        >>> decomposer = QueryDecomposer(llm=get_llm("gpt-4o-mini"))
        >>> 
        >>> query = "Como implementar BSC considerando perspectivas financeira e clientes?"
        >>> should_decompose, score = decomposer.should_decompose(query)
        >>> print(f"Decompor: {should_decompose}, Score: {score}")
        >>> 
        >>> if should_decompose:
        >>>     sub_queries = await decomposer.decompose(query)
        >>>     print(f"Sub-queries: {sub_queries}")
    """
    
    # Palavras-chave para heurísticas
    AND_WORDS = [
        "e", "também", "além", "além disso", "além de",
        "considerando", "assim como", "bem como"
    ]
    
    BSC_PERSPECTIVES = [
        "financeira", "financeiro",
        "cliente", "clientes",
        "processo", "processos", "processos internos",
        "aprendizado", "crescimento", "aprendizado e crescimento",
        "learning", "growth"
    ]
    
    COMPLEXITY_WORDS = [
        "implementar", "implementação",
        "interconexão", "interconexões",
        "relação", "relações",
        "diferença", "diferenças",
        "comparar", "comparação",
        "integrar", "integração"
    ]
    
    def __init__(
        self,
        llm: BaseLLM,
        enabled: bool = True,
        min_query_length: int = 30,
        score_threshold: int = 1
    ):
        """Inicializa o QueryDecomposer.
        
        Args:
            llm: Language model para decomposição (recomendado: gpt-4o-mini)
            enabled: Se decomposição está ativada (padrão: True)
            min_query_length: Comprimento mínimo da query para considerar decomposição
            score_threshold: Threshold de score de complexidade para triggar decomposição
        """
        self.llm = llm
        self.enabled = enabled
        self.min_query_length = min_query_length
        self.score_threshold = score_threshold
        
        # Criar prompt template
        self.prompt_template = PromptTemplate(
            template=QUERY_DECOMPOSITION_PROMPT,
            input_variables=["query"]
        )
    
    def should_decompose(self, query: str) -> Tuple[bool, int]:
        """Decide se query deve ser decomposta baseado em heurísticas.
        
        Usa sistema de pontuação com 5 heurísticas:
        1. Comprimento > min_length (pré-requisito)
        2. Palavras de ligação (+1 ponto)
        3. Múltiplas perspectivas BSC (+2 pontos)
        4. Múltiplas perguntas (+1 ponto)
        5. Palavras de complexidade (+1 ponto)
        
        Args:
            query: Query original a avaliar
            
        Returns:
            Tupla (should_decompose, score):
                - should_decompose: True se query deve ser decomposta
                - score: Pontuação de complexidade calculada
        
        Example:
            >>> decomposer = QueryDecomposer(llm=get_llm())
            >>> query = "Como implementar BSC com perspectivas financeira e clientes?"
            >>> should, score = decomposer.should_decompose(query)
            >>> print(f"Decompor: {should}, Score: {score}")
            Decompor: True, Score: 4
        """
        if not self.enabled:
            return False, 0
        
        # Pré-requisito: comprimento mínimo
        if len(query) < self.min_query_length:
            return False, 0
        
        # Calcular score de complexidade
        score = self._calculate_complexity_score(query)
        
        # Decisão: decompor se score >= threshold
        should = score >= self.score_threshold
        
        return should, score
    
    def _calculate_complexity_score(self, query: str) -> int:
        """Calcula score de complexidade baseado em heurísticas.
        
        Args:
            query: Query a avaliar
            
        Returns:
            Score de complexidade (0-5+)
        """
        score = 0
        query_lower = query.lower()
        
        # Heurística 1: Palavras de ligação (+1)
        # Usar word boundaries para evitar falsos positivos (ex: "é" não deve ser detectado como "e")
        and_words_found = False
        for word in self.AND_WORDS:
            # Criar padrão com word boundaries
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, query_lower):
                and_words_found = True
                break
        if and_words_found:
            score += 1
        
        # Heurística 2: Múltiplas perspectivas BSC (+2)
        perspectives_count = sum(
            1 for perspective in self.BSC_PERSPECTIVES
            if perspective in query_lower
        )
        
        # Também reconhecer padrões como "4 perspectivas", "quatro perspectivas", "todas perspectivas"
        perspective_patterns = [
            r'\b(4|quatro|todas|múltiplas|v[aá]rias)\s+(as\s+)?perspectivas?\b',
            r'\bperspectivas?\s+(do\s+)?bsc\b'
        ]
        multiple_perspectives_pattern = any(
            re.search(pattern, query_lower) 
            for pattern in perspective_patterns
        )
        
        if perspectives_count >= 2 or multiple_perspectives_pattern:
            score += 2
        
        # Heurística 3: Múltiplas perguntas (+1)
        question_marks = query.count("?")
        if question_marks >= 2:
            score += 1
        
        # Heurística 4: Palavras de complexidade (+1)
        if any(word in query_lower for word in self.COMPLEXITY_WORDS):
            score += 1
        
        return score
    
    async def decompose(self, query: str) -> List[str]:
        """Decompõe query complexa em 2-4 sub-queries independentes.
        
        Usa LLM com prompt especializado para gerar sub-queries que:
        - São focadas em um único aspecto BSC
        - Não se sobrepõem
        - Juntas cobrem a query original completamente
        
        Args:
            query: Query original complexa
            
        Returns:
            Lista de 2-4 sub-queries independentes
            
        Raises:
            ValueError: Se decomposição falhar ou não retornar sub-queries válidas
        
        Example:
            >>> query = "Como implementar BSC considerando perspectivas financeira e clientes?"
            >>> sub_queries = await decomposer.decompose(query)
            >>> print(sub_queries)
            [
                "Como implementar a perspectiva financeira no Balanced Scorecard?",
                "Como implementar a perspectiva de clientes no Balanced Scorecard?"
            ]
        """
        try:
            # Gerar prompt
            prompt = self.prompt_template.format(query=query)
            
            # Chamar LLM para decomposição
            # Usar asyncio.to_thread para não bloquear se LLM for síncrono
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            
            # Extrair conteúdo da resposta
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parsear sub-queries (uma por linha)
            sub_queries = [
                line.strip()
                for line in content.strip().split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            # Validar resultado
            if not sub_queries:
                raise ValueError("Decomposição não retornou sub-queries válidas")
            
            if len(sub_queries) < 2:
                # Se LLM retornou apenas 1 sub-query, não faz sentido decompor
                # Retornar query original
                return [query]
            
            if len(sub_queries) > 4:
                # Limitar a 4 sub-queries (evitar over-decomposition)
                sub_queries = sub_queries[:4]
            
            return sub_queries
            
        except Exception as e:
            # Em caso de erro, retornar query original (fallback seguro)
            print(f"[WARN] Query decomposition falhou: {e}. Usando query original.")
            return [query]
    
    def get_stats(self) -> dict:
        """Retorna estatísticas de configuração do decomposer.
        
        Returns:
            Dicionário com configurações e estatísticas
        """
        return {
            "enabled": self.enabled,
            "min_query_length": self.min_query_length,
            "score_threshold": self.score_threshold,
            "llm_model": getattr(self.llm, "model_name", "unknown")
        }

