"""SWOT Analysis Tool - Ferramenta consultiva estruturada.

Esta tool facilita análise SWOT contextualizada usando:
- ClientProfile do onboarding
- Conhecimento BSC via RAG (specialist agents)
- LLM structured output (Pydantic)
- Optional refinement via diagnostic results

Architecture Pattern: Tool → Prompt → LLM + RAG → Structured Output → Validation

References:
- Kore.ai LLM SWOT Analysis with RAG (Jul 2024)
- AI-Agent Applications Best Practices (Medium 2024)
- LangChain Structured Output patterns (2025)

Created: 2025-10-19 (FASE 3.1)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import logging

from pydantic import ValidationError
from langchain_core.language_models import BaseLLM

from src.memory.schemas import SWOTAnalysis, CompanyInfo, StrategicContext
from src.prompts.swot_prompts import (
    FACILITATE_SWOT_PROMPT,
    SYNTHESIZE_SWOT_PROMPT,
    build_company_context,
    build_bsc_knowledge_context,
    build_diagnostic_context,
)

if TYPE_CHECKING:
    from src.agents.financial_agent import FinancialAgent
    from src.agents.customer_agent import CustomerAgent
    from src.agents.process_agent import ProcessAgent
    from src.agents.learning_agent import LearningAgent
    from src.memory.schemas import CompleteDiagnostic

logger = logging.getLogger(__name__)


class SWOTAnalysisTool:
    """Ferramenta para facilitar análise SWOT estruturada com contexto BSC.
    
    Esta tool combina:
    1. Contexto da empresa (ClientProfile)
    2. Conhecimento BSC (via RAG com specialist agents)
    3. LLM facilitation (GPT-4o-mini structured output)
    4. Optional refinement (se diagnostic disponível)
    
    Attributes:
        llm: Language model para facilitation
        financial_agent: Agente financeira para RAG
        customer_agent: Agente clientes para RAG
        process_agent: Agente processos para RAG
        learning_agent: Agente aprendizado para RAG
        
    Example:
        >>> tool = SWOTAnalysisTool(llm, financial, customer, process, learning)
        >>> swot = tool.facilitate_swot(company_info, strategic_context)
        >>> swot.is_complete()  # True se >= 2 itens/quadrante
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        financial_agent: FinancialAgent,
        customer_agent: CustomerAgent,
        process_agent: ProcessAgent,
        learning_agent: LearningAgent,
    ):
        """Inicializa SWOT tool com LLM e 4 specialist agents.
        
        Args:
            llm: LLM para structured output (recomendado GPT-4o-mini)
            financial_agent: Agente perspectiva financeira
            customer_agent: Agente perspectiva clientes
            process_agent: Agente perspectiva processos
            learning_agent: Agente perspectiva aprendizado
        """
        self.llm = llm
        self.financial_agent = financial_agent
        self.customer_agent = customer_agent
        self.process_agent = process_agent
        self.learning_agent = learning_agent
        
        # LLM configurado para structured output SWOTAnalysis
        self.llm_structured = self.llm.with_structured_output(SWOTAnalysis)
        
        logger.info("[SWOT Tool] Inicializado com 4 specialist agents para RAG")
    
    def facilitate_swot(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        use_rag: bool = True,
    ) -> SWOTAnalysis:
        """Facilita análise SWOT estruturada para a empresa.
        
        Workflow:
        1. Constrói contexto da empresa
        2. (Opcional) Recupera conhecimento BSC via RAG
        3. Prompt LLM com contexto + conhecimento
        4. Retorna SWOTAnalysis estruturado validado
        
        Args:
            company_info: Informações básicas da empresa
            strategic_context: Desafios e objetivos estratégicos
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)
            
        Returns:
            SWOTAnalysis: Objeto Pydantic validado com 4 quadrantes
            
        Raises:
            ValidationError: Se LLM retorna SWOT inválido
            ValueError: Se contexto empresa insuficiente
            
        Example:
            >>> company = CompanyInfo(name="TechCorp", sector="Tecnologia", size="Média")
            >>> context = StrategicContext(
            ...     current_challenges=["Crescimento rápido", "Processos manuais"],
            ...     strategic_objectives=["Profissionalizar gestão"]
            ... )
            >>> swot = tool.facilitate_swot(company, context)
            >>> swot.total_items()  # >= 8 (2 por quadrante mínimo)
        """
        logger.info(
            f"[SWOT Tool] Facilitando SWOT para {company_info.name} "
            f"(use_rag={use_rag})"
        )
        
        # STEP 1: Construir contexto empresa
        company_context = build_company_context(company_info, strategic_context)
        
        if not company_context or len(company_context) < 100:
            logger.warning(
                "[SWOT Tool] Contexto empresa muito curto "
                f"({len(company_context)} chars), SWOT pode ser genérico"
            )
        
        # STEP 2: (Opcional) Recuperar conhecimento BSC via RAG
        bsc_knowledge = ""
        if use_rag:
            bsc_knowledge = self._retrieve_bsc_knowledge(company_info, strategic_context)
            logger.info(
                f"[SWOT Tool] Conhecimento BSC recuperado "
                f"({len(bsc_knowledge)} chars)"
            )
        else:
            logger.info("[SWOT Tool] RAG desabilitado, usando apenas contexto empresa")
        
        # STEP 3: Prompt LLM com contexto + conhecimento
        prompt = FACILITATE_SWOT_PROMPT.format(
            company_context=company_context,
            bsc_knowledge=bsc_knowledge or "Nenhum conhecimento adicional fornecido."
        )
        
        try:
            # Structured output garante SWOTAnalysis válido
            swot = self.llm_structured.invoke(prompt)
            
            logger.info(
                f"[SWOT Tool] SWOT gerado: {swot.total_items()} itens total "
                f"(S:{len(swot.strengths)}, W:{len(swot.weaknesses)}, "
                f"O:{len(swot.opportunities)}, T:{len(swot.threats)})"
            )
            
            # Validar completude (warning se < 2 itens/quadrante)
            if not swot.is_complete(min_items_per_quadrant=2):
                logger.warning(
                    f"[SWOT Tool] SWOT incompleto! Resumo: {swot.quadrant_summary()}"
                )
            
            return swot
            
        except ValidationError as e:
            logger.error(f"[SWOT Tool] LLM retornou SWOT inválido: {e}")
            raise
        except Exception as e:
            logger.error(f"[SWOT Tool] Erro inesperado ao gerar SWOT: {e}")
            raise ValueError(f"Falha ao facilitar SWOT: {e}") from e
    
    def refine_swot(
        self,
        preliminary_swot: SWOTAnalysis,
        diagnostic_result: CompleteDiagnostic,
    ) -> SWOTAnalysis:
        """Refina SWOT preliminar com insights do diagnóstico BSC completo.
        
        Use este método quando:
        - Diagnostic BSC já foi executado
        - SWOT preliminar precisa ser enriquecido com análise 4 perspectivas
        - Cliente solicitou refinamento baseado em diagnóstico
        
        Args:
            preliminary_swot: SWOT inicial gerado via facilitate_swot()
            diagnostic_result: CompleteDiagnostic com análise 4 perspectivas
            
        Returns:
            SWOTAnalysis: SWOT refinado e enriquecido
            
        Example:
            >>> swot_v1 = tool.facilitate_swot(company, context)
            >>> diagnostic = await diagnostic_agent.run_diagnostic(profile)
            >>> swot_v2 = tool.refine_swot(swot_v1, diagnostic)
            >>> swot_v2.total_items() >= swot_v1.total_items()  # Enriquecido
        """
        logger.info("[SWOT Tool] Refinando SWOT com diagnóstico BSC")
        
        # Construir contexto diagnóstico
        diagnostic_context = build_diagnostic_context(diagnostic_result)
        
        # Prompt LLM para refinamento
        prompt = SYNTHESIZE_SWOT_PROMPT.format(
            preliminary_swot=preliminary_swot.model_dump_json(indent=2),
            diagnostic_context=diagnostic_context,
        )
        
        try:
            refined_swot = self.llm_structured.invoke(prompt)
            
            logger.info(
                f"[SWOT Tool] SWOT refinado: "
                f"{preliminary_swot.total_items()} → {refined_swot.total_items()} itens"
            )
            
            return refined_swot
            
        except Exception as e:
            logger.error(f"[SWOT Tool] Erro ao refinar SWOT: {e}")
            # Fallback: retorna preliminary se refinamento falhar
            logger.warning("[SWOT Tool] Retornando SWOT preliminar (refinamento falhou)")
            return preliminary_swot
    
    def _retrieve_bsc_knowledge(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
    ) -> str:
        """Recupera conhecimento BSC relevante via RAG (4 specialist agents).
        
        Query construction:
        - Menciona setor da empresa
        - Inclui desafios estratégicos
        - Foca em SWOT + BSC implementation
        
        Args:
            company_info: Info empresa para contextualizar query
            strategic_context: Desafios/objetivos para query específica
            
        Returns:
            String com conhecimento BSC formatado (top 5 chunks)
        """
        # Construir query RAG contextualizada
        query_parts = [
            f"Análise SWOT para implementação BSC no setor {company_info.sector}",
        ]
        
        if strategic_context.current_challenges:
            # Incluir primeiro desafio na query (mais relevante)
            main_challenge = strategic_context.current_challenges[0]
            query_parts.append(f"considerando desafio: {main_challenge}")
        
        rag_query = " ".join(query_parts)
        
        logger.debug(f"[SWOT Tool] RAG query: {rag_query}")
        
        # Recuperar conhecimento via 4 specialist agents (invoke method)
        # Nota: Specialist agents retornam dict com 'context' key
        try:
            financial_result = self.financial_agent.invoke(rag_query)
            customer_result = self.customer_agent.invoke(rag_query)
            process_result = self.process_agent.invoke(rag_query)
            learning_result = self.learning_agent.invoke(rag_query)
            
            # Extrair contexts (specialist agents retornam dict['context'])
            contexts = []
            for agent_name, result in [
                ("Financial", financial_result),
                ("Customer", customer_result),
                ("Process", process_result),
                ("Learning", learning_result),
            ]:
                if isinstance(result, dict) and "context" in result:
                    context_str = result["context"]
                    if context_str and len(context_str) > 50:  # Filtrar contexts vazios
                        contexts.append(context_str)
                        logger.debug(
                            f"[SWOT Tool] {agent_name} agent: {len(context_str)} chars"
                        )
            
            # Formatar conhecimento recuperado
            bsc_knowledge = build_bsc_knowledge_context(contexts)
            
            return bsc_knowledge
            
        except Exception as e:
            logger.error(f"[SWOT Tool] Erro ao recuperar conhecimento BSC via RAG: {e}")
            # Fallback: retorna string vazia (SWOT será baseado apenas em contexto empresa)
            return ""

