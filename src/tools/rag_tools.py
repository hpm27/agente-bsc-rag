"""
Ferramentas RAG para os agentes utilizarem.

Estas ferramentas encapsulam as capacidades de retrieval e busca,
permitindo que os agentes especializados busquem informações relevantes
na base de conhecimento BSC.
"""

from config.settings import settings
from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field

from src.rag.retriever import BSCRetriever


class SearchInput(BaseModel):
    """Input para a ferramenta de busca."""

    query: str = Field(description="A consulta/pergunta a ser pesquisada na base de conhecimento")
    top_k: int | None = Field(
        default=None,
        description="Número de documentos a retornar (padrão: configuração do sistema)",
    )


class PerspectiveSearchInput(BaseModel):
    """Input para busca por perspectiva BSC."""

    query: str = Field(description="A consulta/pergunta a ser pesquisada")
    perspective: str = Field(
        description="Perspectiva BSC: 'financeira', 'cliente', 'processos', ou 'aprendizado'"
    )
    top_k: int | None = Field(default=None, description="Número de documentos")


class MultiQuerySearchInput(BaseModel):
    """Input para busca com múltiplas queries."""

    queries: list[str] = Field(description="Lista de consultas relacionadas")
    top_k: int | None = Field(default=None, description="Número total de documentos")


class RAGTools:
    """
    Classe que encapsula todas as ferramentas RAG disponíveis para os agentes.
    """

    def __init__(self):
        """Inicializa as ferramentas RAG."""
        self.retriever = BSCRetriever()
        logger.info("RAG Tools inicializadas")

    def search_knowledge_base(self, query: str, top_k: int | None = None) -> str:
        """
        Busca na base de conhecimento BSC usando hybrid search e re-ranking.

        Args:
            query: A consulta/pergunta
            top_k: Número de documentos a retornar

        Returns:
            Contexto formatado com os documentos relevantes
        """
        try:
            logger.info(f"[SEARCH] Buscando: '{query[:50]}...'")

            k = top_k or settings.top_k_retrieval

            # Retrieval com hybrid search + reranking
            results = self.retriever.retrieve(query=query, k=k, use_rerank=True, use_hybrid=True)

            if not results:
                return "Nenhum documento relevante encontrado na base de conhecimento."

            # Formata contexto
            context = self.retriever.format_context(
                documents=results, max_tokens=settings.max_tokens
            )

            logger.info(f"[OK] Encontrados {len(results)} documentos relevantes")
            return context

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return f"Erro ao buscar na base de conhecimento: {e!s}"

    def search_by_perspective(self, query: str, perspective: str, top_k: int | None = None) -> str:
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
            logger.info(f"[PERSPECTIVE] Buscando (perspectiva {perspective}): '{query[:50]}...'")

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
                query=query, perspective=perspective, k=k
            )

            if not results:
                return f"Nenhum documento relevante encontrado para a perspectiva '{perspective}'."

            context = self.retriever.format_context(
                documents=results, max_tokens=settings.max_tokens
            )

            logger.info(
                f"[OK] Encontrados {len(results)} documentos para perspectiva {perspective}"
            )
            return context

        except Exception as e:
            logger.error(f"Erro na busca por perspectiva: {e}")
            return f"Erro ao buscar por perspectiva: {e!s}"

    def search_multi_query(self, queries: list[str], top_k: int | None = None) -> str:
        """
        Busca usando múltiplas queries e combina resultados com RRF.

        Args:
            queries: Lista de consultas relacionadas
            top_k: Número total de documentos

        Returns:
            Contexto formatado com documentos mais relevantes
        """
        try:
            logger.info(f"[MULTI] Busca multi-query: {len(queries)} queries")

            k = top_k or settings.top_k_retrieval

            # Busca com múltiplas queries
            results = self.retriever.retrieve_multi_query(queries=queries, k=k)

            if not results:
                return "Nenhum documento relevante encontrado para as queries fornecidas."

            context = self.retriever.format_context(
                documents=results, max_tokens=settings.max_tokens
            )

            logger.info(f"[OK] Combinados resultados de {len(queries)} queries")
            return context

        except Exception as e:
            logger.error(f"Erro na busca multi-query: {e}")
            return f"Erro ao buscar com múltiplas queries: {e!s}"

    def get_langchain_tools(self) -> list[StructuredTool]:
        """
        Retorna lista de ferramentas LangChain para uso pelos agentes.

        Returns:
            Lista de StructuredTools do LangChain
        """
        tools = [
            StructuredTool.from_function(
                func=self.search_knowledge_base,
                name="search_knowledge_base",
                description=(
                    "Busca informações na base de conhecimento do Balanced Scorecard (BSC). "
                    "Use esta ferramenta quando precisar de informações sobre conceitos, "
                    "metodologias, melhores práticas ou exemplos relacionados ao BSC. "
                    "Input: Uma query/pergunta em linguagem natural."
                ),
                args_schema=SearchInput,
            ),
            StructuredTool.from_function(
                func=self.search_by_perspective,
                name="search_by_perspective",
                description=(
                    "Busca informações focadas em uma perspectiva específica do BSC: "
                    "'financeira' (receitas, custos, ROI), "
                    "'cliente' (satisfação, retenção, valor), "
                    "'processos' (eficiência, qualidade operacional), ou "
                    "'aprendizado' (capacitação, inovação, crescimento). "
                    "Input: query (a pergunta) e perspective (uma das 4 perspectivas)."
                ),
                args_schema=PerspectiveSearchInput,
            ),
            StructuredTool.from_function(
                func=self.search_multi_query,
                name="search_multi_query",
                description=(
                    "Busca usando múltiplas queries relacionadas e combina os resultados. "
                    "Útil quando você precisa explorar diferentes ângulos de um tópico ou "
                    "quando a pergunta pode ser decomposta em sub-perguntas. "
                    "Input: Lista de queries relacionadas."
                ),
                args_schema=MultiQuerySearchInput,
            ),
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


def get_tools_for_agent() -> list[StructuredTool]:
    """
    Função de conveniência para obter tools LangChain prontas para uso.

    Returns:
        Lista de StructuredTools configuradas
    """
    rag_tools = create_rag_tools()
    return rag_tools.get_langchain_tools()
