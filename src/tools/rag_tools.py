"""
Ferramentas RAG para os agentes utilizarem.

Estas ferramentas encapsulam as capacidades de retrieval e busca,
permitindo que os agentes especializados busquem informações relevantes
na base de conhecimento BSC.
"""
from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field
from loguru import logger

from src.rag.retriever import BSCRetriever
from config.settings import settings


class SearchInput(BaseModel):
    """Input para a ferramenta de busca."""
    query: str = Field(description="A consulta/pergunta a ser pesquisada na base de conhecimento")
    top_k: Optional[int] = Field(
        default=None,
        description="Número de documentos a retornar (padrão: configuração do sistema)"
    )


class PerspectiveSearchInput(BaseModel):
    """Input para busca por perspectiva BSC."""
    query: str = Field(description="A consulta/pergunta a ser pesquisada")
    perspective: str = Field(
        description="Perspectiva BSC: 'financeira', 'cliente', 'processos', ou 'aprendizado'"
    )
    top_k: Optional[int] = Field(default=None, description="Número de documentos")


class MultiQuerySearchInput(BaseModel):
    """Input para busca com múltiplas queries."""
    queries: List[str] = Field(description="Lista de consultas relacionadas")
    top_k: Optional[int] = Field(default=None, description="Número total de documentos")


class RAGTools:
    """
    Classe que encapsula todas as ferramentas RAG disponíveis para os agentes.
    """
    
    def __init__(self):
        """Inicializa as ferramentas RAG."""
        self.retriever = BSCRetriever()
        logger.info("RAG Tools inicializadas")
    
    def search_knowledge_base(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> str:
        """
        Busca na base de conhecimento BSC usando hybrid search e re-ranking.
        
        Args:
            query: A consulta/pergunta
            top_k: Número de documentos a retornar
            
        Returns:
            Contexto formatado com os documentos relevantes
        """
        try:
            logger.info(f"🔍 Buscando: '{query[:50]}...'")
            
            k = top_k or settings.top_k_retrieval
            
            # Retrieval com hybrid search + reranking
            results = self.retriever.retrieve(
                query=query,
                k=k,
                use_rerank=True,
                use_hybrid=True
            )
            
            if not results:
                return "Nenhum documento relevante encontrado na base de conhecimento."
            
            # Formata contexto
            context = self.retriever.format_context(
                documents=results,
                max_tokens=settings.max_tokens
            )
            
            logger.info(f"✅ Encontrados {len(results)} documentos relevantes")
            return context
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return f"Erro ao buscar na base de conhecimento: {str(e)}"
    
    def search_by_perspective(
        self,
        query: str,
        perspective: str,
        top_k: Optional[int] = None
    ) -> str:
        """
        Busca focada em uma perspectiva específica do BSC.
        
        Args:
            query: A consulta/pergunta
            perspective: Uma das perspectivas: 'financeira', 'cliente', 'processos', 'aprendizado'
            top_k: Número de documentos
            
        Returns:
            Contexto formatado focado na perspectiva
        """
        try:
            logger.info(f"🎯 Buscando (perspectiva {perspective}): '{query[:50]}...'")
            
            k = top_k or settings.top_k_retrieval
            
            # Valida perspectiva
            valid_perspectives = ["financeira", "cliente", "processos", "aprendizado"]
            if perspective.lower() not in valid_perspectives:
                return (
                    f"Perspectiva inválida: '{perspective}'. "
                    f"Use uma das seguintes: {', '.join(valid_perspectives)}"
                )
            
            # Busca por perspectiva
            results = self.retriever.retrieve_by_perspective(
                query=query,
                perspective=perspective,
                k=k
            )
            
            if not results:
                return f"Nenhum documento relevante encontrado para a perspectiva '{perspective}'."
            
            context = self.retriever.format_context(
                documents=results,
                max_tokens=settings.max_tokens
            )
            
            logger.info(f"✅ Encontrados {len(results)} documentos para perspectiva {perspective}")
            return context
            
        except Exception as e:
            logger.error(f"Erro na busca por perspectiva: {e}")
            return f"Erro ao buscar por perspectiva: {str(e)}"
    
    def search_multi_query(
        self,
        queries: List[str],
        top_k: Optional[int] = None
    ) -> str:
        """
        Busca usando múltiplas queries e combina resultados com RRF.
        
        Args:
            queries: Lista de consultas relacionadas
            top_k: Número total de documentos
            
        Returns:
            Contexto formatado com documentos mais relevantes
        """
        try:
            logger.info(f"🔍 Busca multi-query: {len(queries)} queries")
            
            k = top_k or settings.top_k_retrieval
            
            # Busca com múltiplas queries
            results = self.retriever.retrieve_multi_query(
                queries=queries,
                k=k
            )
            
            if not results:
                return "Nenhum documento relevante encontrado para as queries fornecidas."
            
            context = self.retriever.format_context(
                documents=results,
                max_tokens=settings.max_tokens
            )
            
            logger.info(f"✅ Combinados resultados de {len(queries)} queries")
            return context
            
        except Exception as e:
            logger.error(f"Erro na busca multi-query: {e}")
            return f"Erro ao buscar com múltiplas queries: {str(e)}"
    
    def get_langchain_tools(self) -> List[Tool]:
        """
        Retorna lista de ferramentas LangChain para uso pelos agentes.
        
        Returns:
            Lista de Tools do LangChain
        """
        tools = [
            Tool(
                name="search_knowledge_base",
                description=(
                    "Busca informações na base de conhecimento do Balanced Scorecard (BSC). "
                    "Use esta ferramenta quando precisar de informações sobre conceitos, "
                    "metodologias, melhores práticas ou exemplos relacionados ao BSC. "
                    "Input: Uma query/pergunta em linguagem natural."
                ),
                func=lambda query: self.search_knowledge_base(query),
                args_schema=SearchInput
            ),
            Tool(
                name="search_by_perspective",
                description=(
                    "Busca informações focadas em uma perspectiva específica do BSC: "
                    "'financeira' (receitas, custos, ROI), "
                    "'cliente' (satisfação, retenção, valor), "
                    "'processos' (eficiência, qualidade operacional), ou "
                    "'aprendizado' (capacitação, inovação, crescimento). "
                    "Input: query (a pergunta) e perspective (uma das 4 perspectivas)."
                ),
                func=lambda query, perspective: self.search_by_perspective(query, perspective),
                args_schema=PerspectiveSearchInput
            ),
            Tool(
                name="search_multi_query",
                description=(
                    "Busca usando múltiplas queries relacionadas e combina os resultados. "
                    "Útil quando você precisa explorar diferentes ângulos de um tópico ou "
                    "quando a pergunta pode ser decomposta em sub-perguntas. "
                    "Input: Lista de queries relacionadas."
                ),
                func=lambda queries: self.search_multi_query(queries),
                args_schema=MultiQuerySearchInput
            )
        ]
        
        logger.info(f"Criadas {len(tools)} ferramentas LangChain")
        return tools


def create_rag_tools() -> RAGTools:
    """
    Factory function para criar instância de RAGTools.
    
    Returns:
        Instância configurada de RAGTools
    """
    return RAGTools()


def get_tools_for_agent() -> List[Tool]:
    """
    Função de conveniência para obter tools LangChain prontas para uso.
    
    Returns:
        Lista de Tools configuradas
    """
    rag_tools = create_rag_tools()
    return rag_tools.get_langchain_tools()

