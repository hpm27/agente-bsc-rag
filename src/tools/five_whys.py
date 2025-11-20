"""Five Whys (5 Porques) Tool - Ferramenta de analise de causa raiz.

Esta tool facilita analise de causa raiz usando metodo 5 Whys desenvolvido
por Taiichi Ohno (Toyota), combinando:
- ClientProfile do onboarding
- Conhecimento BSC via RAG (specialist agents)
- LLM structured output (Pydantic)
- Iteracao inteligente ate root cause (3-7 niveis)

Architecture Pattern: Iterative Tool -> Prompt -> LLM + RAG -> Structured Output -> Validation

References:
- 5 Whys Root Cause Analysis Best Practices (Reliability Center Inc. May 2025)
- AI-assisted 5 Whys Root Cause Analysis (LinkedIn Dr. T. Justin W. Feb 2025)
- Root-Cause Analysis with AI (skan.ai Aug 2025)

Created: 2025-10-19 (FASE 3.2)
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseLLM
from pydantic import BaseModel, Field, ValidationError

from src.memory.schemas import (
    CompanyInfo,
    FiveWhysAnalysis,
    StrategicContext,
    WhyIteration,
)
from src.prompts.five_whys_prompts import (
    FACILITATE_FIVE_WHYS_PROMPT,
    SYNTHESIZE_ROOT_CAUSE_PROMPT,
    build_bsc_knowledge_context,
    build_company_context,
    build_iterations_context,
    build_previous_iterations_text,
)

if TYPE_CHECKING:
    from src.agents.customer_agent import CustomerAgent
    from src.agents.financial_agent import FinancialAgent
    from src.agents.learning_agent import LearningAgent
    from src.agents.process_agent import ProcessAgent

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER SCHEMAS (para structured output iterativo)
# ============================================================================


class IterationOutput(BaseModel):
    """Output estruturado de uma iteracao 5 Whys."""

    question: str = Field(min_length=10, description="Pergunta 'Por que?' formulada")
    answer: str = Field(min_length=10, description="Resposta que leva a proxima iteracao")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confianca de que esta resposta e relevante"
    )
    is_root_cause: bool = Field(
        default=False, description="True se esta resposta e a causa raiz fundamental"
    )
    reasoning: str = Field(min_length=20, description="Breve explicacao do raciocinio")


class RootCauseOutput(BaseModel):
    """Output estruturado da sintese de causa raiz."""

    root_cause: str = Field(min_length=20, description="Causa raiz fundamental identificada")
    confidence_score: float = Field(
        ge=0.0, le=100.0, description="Confianca de que root cause foi atingida (0-100%)"
    )
    reasoning: str = Field(min_length=50, description="Explicacao de como chegamos a esta causa")
    recommended_actions: list[str] = Field(
        min_length=2, description="Acoes concretas para resolver causa raiz"
    )


# ============================================================================
# FIVE WHYS TOOL
# ============================================================================


class FiveWhysTool:
    """Ferramenta para facilitar analise 5 Whys (causa raiz) com contexto BSC.

    Esta tool combina:
    1. Contexto da empresa (ClientProfile)
    2. Conhecimento BSC (via RAG com specialist agents)
    3. LLM facilitation iterativa (GPT-4o-mini structured output)
    4. Validacao inteligente de profundidade (3-7 iteracoes)

    Attributes:
        llm: Language model para facilitation
        financial_agent: Agente financeira para RAG
        customer_agent: Agente clientes para RAG
        process_agent: Agente processos para RAG
        learning_agent: Agente aprendizado para RAG
        max_iterations: Maximo de iteracoes "Por que?" (default: 7)

    Example:
        >>> tool = FiveWhysTool(llm, financial, customer, process, learning)
        >>> analysis = tool.facilitate_five_whys(
        ...     company_info,
        ...     strategic_context,
        ...     problem_statement="Vendas baixas no ultimo trimestre"
        ... )
        >>> analysis.is_complete()  # True
        >>> analysis.depth_reached()  # 3-7
    """

    def __init__(
        self,
        llm: BaseLLM,
        financial_agent: FinancialAgent | None = None,
        customer_agent: CustomerAgent | None = None,
        process_agent: ProcessAgent | None = None,
        learning_agent: LearningAgent | None = None,
        max_iterations: int = 7,
    ):
        """Inicializa Five Whys tool com LLM e specialist agents opcionais.

        Args:
            llm: LLM para structured output (recomendado GPT-4o-mini)
            financial_agent: Agente perspectiva financeira (opcional para RAG)
            customer_agent: Agente perspectiva clientes (opcional para RAG)
            process_agent: Agente perspectiva processos (opcional para RAG)
            learning_agent: Agente perspectiva aprendizado (opcional para RAG)
            max_iterations: Maximo de iteracoes "Por que?" (default: 7)
        """
        self.llm = llm
        self.financial_agent = financial_agent
        self.customer_agent = customer_agent
        self.process_agent = process_agent
        self.learning_agent = learning_agent
        self.max_iterations = max_iterations

        # LLMs configurados para structured output
        self.llm_iteration = self.llm.with_structured_output(IterationOutput)
        self.llm_synthesis = self.llm.with_structured_output(RootCauseOutput)

        rag_enabled = all(
            [
                financial_agent,
                customer_agent,
                process_agent,
                learning_agent,
            ]
        )

        logger.info(
            f"[Five Whys Tool] Inicializado "
            f"(max_iterations={max_iterations}, RAG={'enabled' if rag_enabled else 'disabled'})"
        )

    async def facilitate_five_whys(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        problem_statement: str,
        use_rag: bool = True,
    ) -> FiveWhysAnalysis:
        """Facilita analise 5 Whys (causa raiz) para problema especifico.

        Workflow iterativo:
        1. Constroi contexto empresa + problema
        2. (Opcional) Recupera conhecimento BSC via RAG
        3. Loop iterativo (3-7 vezes):
           a. Prompt LLM com contexto + iteracoes anteriores
           b. LLM gera proxima iteracao (question, answer, confidence)
           c. Valida se root cause foi atingida
           d. Se sim: sai do loop. Se nao: continua
        4. Sintese final da causa raiz + acoes recomendadas
        5. Retorna FiveWhysAnalysis estruturado validado

        Args:
            company_info: Informacoes basicas da empresa
            strategic_context: Desafios e objetivos estrategicos
            problem_statement: Problema especifico a analisar (ex: "Vendas baixas")
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)

        Returns:
            FiveWhysAnalysis: Objeto Pydantic validado com iteracoes + root cause

        Raises:
            ValidationError: Se LLM retorna dados invalidos
            ValueError: Se contexto empresa insuficiente ou problema vazio

        Example:
            >>> company = CompanyInfo(name="TechCorp", sector="Tecnologia", size="Media")
            >>> context = StrategicContext(
            ...     current_challenges=["Vendas baixas", "Processos manuais"]
            ... )
            >>> analysis = tool.facilitate_five_whys(
            ...     company,
            ...     context,
            ...     problem_statement="Vendas baixas no ultimo trimestre"
            ... )
            >>> analysis.depth_reached()  # 3-7 iteracoes
            >>> analysis.root_cause_confidence()  # 0-100%
        """
        logger.info(
            f"[Five Whys Tool] Facilitando 5 Whys para {company_info.name}: "
            f"'{problem_statement}' (use_rag={use_rag})"
        )

        # Validacoes basicas
        if not problem_statement or len(problem_statement) < 10:
            raise ValueError(
                f"problem_statement deve ter >= 10 chars (recebeu: '{problem_statement}')"
            )

        # STEP 1: Construir contexto empresa
        company_context = build_company_context(company_info, strategic_context)

        if len(company_context) < 100:
            logger.warning(
                f"[Five Whys Tool] Contexto empresa muito curto "
                f"({len(company_context)} chars), analise pode ser generica"
            )

        # STEP 2: (Opcional) Recuperar conhecimento BSC via RAG
        # STEP 2: (Opcional) Recuperar conhecimento BSC via RAG
        # SPRINT 1 OTIMIZAÇÃO: Execução paralela dos 4 specialist agents
        bsc_knowledge = ""
        if use_rag and self._rag_available():
            bsc_knowledge = await self._retrieve_bsc_knowledge(
                company_info, strategic_context, problem_statement
            )
            logger.info(
                f"[Five Whys Tool] Conhecimento BSC recuperado " f"({len(bsc_knowledge)} chars)"
            )
        else:
            logger.info(
                "[Five Whys Tool] RAG desabilitado ou indisponivel, "
                "usando apenas contexto empresa"
            )

        # STEP 3: Loop iterativo (3-7 iteracoes)
        iterations: list[WhyIteration] = []

        for i in range(1, self.max_iterations + 1):
            logger.debug(f"[Five Whys Tool] Iteracao {i}/{self.max_iterations}")

            # Construir contexto de iteracao
            previous_iterations_text = build_previous_iterations_text(iterations)
            iteration_context = (
                f"Iteracoes anteriores: {len(iterations)}"
                if iterations
                else "Esta e a primeira iteracao"
            )

            # Prompt LLM para proxima iteracao
            prompt = FACILITATE_FIVE_WHYS_PROMPT.format(
                company_context=company_context,
                problem_statement=problem_statement,
                bsc_knowledge=bsc_knowledge or "Nenhum conhecimento adicional fornecido.",
                current_iteration=i,
                max_iterations=self.max_iterations,
                iteration_context=iteration_context,
                previous_iterations_text=previous_iterations_text,
            )

            try:
                # Structured output garante IterationOutput valido
                iteration_output = self.llm_iteration.invoke(prompt)

                # Criar WhyIteration Pydantic
                iteration = WhyIteration(
                    iteration_number=i,
                    question=iteration_output.question,
                    answer=iteration_output.answer,
                    confidence=iteration_output.confidence,
                )

                iterations.append(iteration)

                logger.info(
                    f"[Five Whys Tool] Iteracao {i}: "
                    f"Q: {iteration.question[:50]}... "
                    f"A: {iteration.answer[:50]}... "
                    f"(confidence: {iteration.confidence:.2f})"
                )

                # Verificar se root cause foi atingida
                if iteration_output.is_root_cause:
                    logger.info(
                        f"[Five Whys Tool] Root cause atingida na iteracao {i}. "
                        f"Reasoning: {iteration_output.reasoning}"
                    )
                    break

                # Verificar minimo 3 iteracoes (sempre fazer pelo menos 3)
                if i >= 3 and iteration.confidence >= 0.85:
                    logger.info(
                        f"[Five Whys Tool] Alta confianca apos {i} iteracoes "
                        f"({iteration.confidence:.2f}), finalizando"
                    )
                    break

            except ValidationError as e:
                logger.error(f"[Five Whys Tool] LLM retornou iteracao invalida: {e}")
                # Se iteracao falhar, continuar com as validas ja coletadas
                if len(iterations) >= 3:
                    logger.warning(
                        f"[Five Whys Tool] Continuando com {len(iterations)} iteracoes validas"
                    )
                    break
                raise
            except Exception as e:
                logger.error(f"[Five Whys Tool] Erro inesperado na iteracao {i}: {e}")
                if len(iterations) >= 3:
                    logger.warning(
                        f"[Five Whys Tool] Continuando com {len(iterations)} iteracoes validas"
                    )
                    break
                raise ValueError(f"Falha ao facilitar iteracao {i}: {e}") from e

        # Validar minimo 3 iteracoes
        if len(iterations) < 3:
            raise ValueError(f"5 Whys requer minimo 3 iteracoes (coletadas: {len(iterations)})")

        logger.info(f"[Five Whys Tool] Loop iterativo completo: {len(iterations)} iteracoes")

        # STEP 4: Sintese final da causa raiz
        root_cause_output = self._synthesize_root_cause(
            problem_statement,
            iterations,
        )

        # STEP 5: Construir FiveWhysAnalysis completo
        analysis = FiveWhysAnalysis(
            problem_statement=problem_statement,
            iterations=iterations,
            root_cause=root_cause_output.root_cause,
            confidence_score=root_cause_output.confidence_score,
            recommended_actions=root_cause_output.recommended_actions,
            context_from_rag=[bsc_knowledge] if bsc_knowledge else [],
        )

        logger.info(
            f"[Five Whys Tool] Analise completa: "
            f"{len(iterations)} iteracoes, "
            f"root cause: '{analysis.root_cause[:50]}...', "
            f"confidence: {analysis.confidence_score}%"
        )

        return analysis

    def _synthesize_root_cause(
        self,
        problem_statement: str,
        iterations: list[WhyIteration],
    ) -> RootCauseOutput:
        """Sintetiza causa raiz fundamental a partir das iteracoes.

        Args:
            problem_statement: Problema original
            iterations: Lista de iteracoes "Por que?" realizadas

        Returns:
            RootCauseOutput: Causa raiz + confidence + acoes recomendadas
        """
        logger.debug(f"[Five Whys Tool] Sintetizando root cause de {len(iterations)} iteracoes")

        # Construir resumo de iteracoes
        iterations_summary = build_iterations_context(iterations)

        # Prompt LLM para sintese
        prompt = SYNTHESIZE_ROOT_CAUSE_PROMPT.format(
            problem_statement=problem_statement,
            num_iterations=len(iterations),
            iterations_summary=iterations_summary,
        )

        try:
            root_cause_output = self.llm_synthesis.invoke(prompt)

            logger.info(
                f"[Five Whys Tool] Root cause sintetizada: "
                f"'{root_cause_output.root_cause[:50]}...', "
                f"confidence: {root_cause_output.confidence_score}%, "
                f"{len(root_cause_output.recommended_actions)} acoes"
            )

            # Validar confianca minima
            if root_cause_output.confidence_score < 50.0:
                logger.warning(
                    f"[Five Whys Tool] Confidence muito baixa "
                    f"({root_cause_output.confidence_score}%), "
                    f"analise pode precisar ser aprofundada"
                )

            return root_cause_output

        except Exception as e:
            logger.error(f"[Five Whys Tool] Erro ao sintetizar root cause: {e}")
            raise ValueError(f"Falha ao sintetizar root cause: {e}") from e

    def _rag_available(self) -> bool:
        """Verifica se RAG esta disponivel (4 specialist agents configurados)."""
        return all(
            [
                self.financial_agent is not None,
                self.customer_agent is not None,
                self.process_agent is not None,
                self.learning_agent is not None,
            ]
        )

    async def _retrieve_bsc_knowledge(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        problem_statement: str,
    ) -> str:
        """Recupera conhecimento BSC relevante via RAG (4 specialist agents) EM PARALELO.

        Query construction:
        - Menciona setor da empresa
        - Inclui problema especifico
        - Foca em root cause analysis + BSC

        Args:
            company_info: Info empresa para contextualizar query
            strategic_context: Desafios/objetivos para query especifica
            problem_statement: Problema especifico sendo analisado

        Returns:
            String com conhecimento BSC formatado (top 5 chunks)
        """
        # Construir query RAG contextualizada
        query_parts = [
            f"Analise de causa raiz para problema '{problem_statement}' "
            f"no setor {company_info.sector} usando BSC",
        ]

        if strategic_context.current_challenges:
            # Incluir primeiro desafio na query (mais relevante)
            main_challenge = strategic_context.current_challenges[0]
            query_parts.append(f"considerando desafio: {main_challenge}")

        rag_query = " ".join(query_parts)

        logger.debug(f"[Five Whys Tool] RAG query: {rag_query}")

        # SPRINT 1 OTIMIZAÇÃO: Recuperar conhecimento via 4 specialist agents EM PARALELO
        # Usar asyncio.gather() com ainvoke() para execução paralela (~7s vs ~28s sequencial)
        try:
            # Executar ainvoke() dos 4 agents em paralelo
            results = await asyncio.gather(
                self.financial_agent.ainvoke(rag_query),
                self.customer_agent.ainvoke(rag_query),
                self.process_agent.ainvoke(rag_query),
                self.learning_agent.ainvoke(rag_query),
                return_exceptions=True,  # Não quebrar se um agent falhar
            )

            # Extrair contexts (specialist agents retornam dict['output'])
            contexts = []
            agent_names = ["Financial", "Customer", "Process", "Learning"]

            for agent_name, result in zip(agent_names, results):
                if isinstance(result, Exception):
                    logger.error(f"[Five Whys Tool] {agent_name} agent falhou: {result}")
                    continue

                if isinstance(result, dict):
                    # Tentar 'context' primeiro (formato antigo), depois 'output' (formato atual)
                    context_str = result.get("context") or result.get("output", "")

                    if context_str and len(context_str) > 50:  # Filtrar contexts vazios
                        contexts.append(context_str)
                        logger.debug(
                            f"[Five Whys Tool] {agent_name} agent: {len(context_str)} chars"
                        )

            # Formatar conhecimento recuperado
            bsc_knowledge = build_bsc_knowledge_context(contexts)

            return bsc_knowledge

        except Exception as e:
            logger.error(f"[Five Whys Tool] Erro ao recuperar conhecimento BSC via RAG: {e}")
            # Fallback: retorna string vazia (analise sera baseada apenas em contexto)
            return ""
