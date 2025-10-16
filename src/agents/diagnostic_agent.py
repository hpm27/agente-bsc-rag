"""DiagnosticAgent: Análise diagnóstica BSC multi-perspectiva.

Este módulo implementa o agente responsável por conduzir diagnóstico organizacional
estruturado nas 4 perspectivas do Balanced Scorecard durante a fase DISCOVERY.

Funcionalidades principais:
- Análise individual de cada perspectiva BSC (Financeira, Clientes, Processos, Aprendizado)
- Análise paralela AsyncIO (4 perspectivas simultaneamente)
- Consolidação cross-perspective (synergies e executive summary)
- Geração de recomendações priorizadas (impacto vs esforço)

Versão: 1.0 (FASE 2.5)
LLM: GPT-4o-mini (cost-effective) + structured output
Best Practices: Multi-agent pattern (Nature 2025), structured diagnostic output
"""

import asyncio
import json
import logging
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.settings import settings
from src.agents.customer_agent import CustomerAgent
from src.agents.financial_agent import FinancialAgent
from src.agents.learning_agent import LearningAgent
from src.agents.process_agent import ProcessAgent
from src.graph.states import BSCState
from src.memory.schemas import (
    ClientProfile,
    CompleteDiagnostic,
    DiagnosticResult,
    Recommendation,
)
from src.prompts.diagnostic_prompts import (
    ANALYZE_CUSTOMER_PERSPECTIVE_PROMPT,
    ANALYZE_FINANCIAL_PERSPECTIVE_PROMPT,
    ANALYZE_LEARNING_PERSPECTIVE_PROMPT,
    ANALYZE_PROCESS_PERSPECTIVE_PROMPT,
    CONSOLIDATE_DIAGNOSTIC_PROMPT,
    GENERATE_RECOMMENDATIONS_PROMPT,
)

# Setup logger
logger = logging.getLogger(__name__)


# ============================================================================
# DIAGNOSTIC AGENT
# ============================================================================


class DiagnosticAgent:
    """Agente especializado em diagnóstico BSC multi-perspectiva.
    
    Conduz análise estruturada da organização nas 4 perspectivas do Balanced
    Scorecard, identifica gaps, oportunidades e gera recomendações priorizadas.
    
    Workflow:
    1. Análise individual de cada perspectiva (paralelo AsyncIO)
    2. Consolidação cross-perspective (synergies)
    3. Geração de recomendações priorizadas (matriz impacto vs esforço)
    
    Attributes:
        llm: Modelo LLM para structured output (GPT-4o-mini)
        financial_agent: Agente especialista em perspectiva Financeira
        customer_agent: Agente especialista em perspectiva Clientes
        process_agent: Agente especialista em perspectiva Processos Internos
        learning_agent: Agente especialista em perspectiva Aprendizado e Crescimento
    
    Example:
        >>> diagnostic_agent = DiagnosticAgent()
        >>> state = BSCState(...)  # Com client_profile preenchido
        >>> diagnostic = diagnostic_agent.run_diagnostic(state)
        >>> diagnostic.executive_summary
        'Empresa TechCorp apresenta sólido EBITDA mas...'
        >>> len(diagnostic.recommendations)
        7
    """
    
    def __init__(self, llm: ChatOpenAI | None = None):
        """Inicializa DiagnosticAgent com LLM e agentes BSC.
        
        Args:
            llm: Modelo LLM customizado (opcional). Se None, usa GPT-4o-mini default.
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,  # Baixo para análise factual
            api_key=settings.openai_api_key,  # type: ignore
        )
        
        # Agentes BSC especializados (já existentes)
        self.financial_agent = FinancialAgent()
        self.customer_agent = CustomerAgent()
        self.process_agent = ProcessAgent()
        self.learning_agent = LearningAgent()
        
        logger.info("[DIAGNOSTIC] DiagnosticAgent inicializado com GPT-4o-mini")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, ValueError)),
        reraise=True,
    )
    def analyze_perspective(
        self,
        perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"],
        client_profile: ClientProfile,
        state: BSCState,
    ) -> DiagnosticResult:
        """Analisa uma perspectiva BSC individualmente.
        
        Usa o prompt especializado de cada perspectiva para analisar contexto
        do cliente e identificar gaps, oportunidades e prioridade.
        
        Args:
            perspective: Nome da perspectiva BSC a analisar
            client_profile: Perfil completo do cliente (company, context, engagement)
            state: Estado LangGraph atual (para contexto adicional)
        
        Returns:
            DiagnosticResult: Análise estruturada da perspectiva com gaps + oportunidades
        
        Raises:
            ValidationError: Se output LLM não passar validação Pydantic
            ValueError: Se perspectiva inválida ou dados insuficientes
        
        Example:
            >>> result = agent.analyze_perspective(
            ...     "Financeira",
            ...     client_profile,
            ...     state
            ... )
            >>> result.priority
            'HIGH'
            >>> len(result.gaps)
            4
        """
        logger.info(f"[DIAGNOSTIC] Analisando perspectiva: {perspective}")
        
        # Selecionar prompt correto por perspectiva
        prompt_map = {
            "Financeira": ANALYZE_FINANCIAL_PERSPECTIVE_PROMPT,
            "Clientes": ANALYZE_CUSTOMER_PERSPECTIVE_PROMPT,
            "Processos Internos": ANALYZE_PROCESS_PERSPECTIVE_PROMPT,
            "Aprendizado e Crescimento": ANALYZE_LEARNING_PERSPECTIVE_PROMPT,
        }
        
        if perspective not in prompt_map:
            raise ValueError(f"Perspectiva inválida: {perspective}")
        
        prompt_template = prompt_map[perspective]
        
        # Buscar contexto relevante da literatura BSC via agente especialista
        agent_map = {
            "Financeira": self.financial_agent,
            "Clientes": self.customer_agent,
            "Processos Internos": self.process_agent,
            "Aprendizado e Crescimento": self.learning_agent,
        }
        
        specialist_agent = agent_map[perspective]
        
        # Query específica para contexto BSC da perspectiva
        query = f"Quais são os principais conceitos e KPIs da perspectiva {perspective} no BSC segundo Kaplan & Norton?"
        
        try:
            context_response = specialist_agent.invoke(query)  # Método correto: invoke()
            client_context = context_response.get("answer", "Contexto BSC não disponível.")
        except Exception as e:
            logger.warning(f"[DIAGNOSTIC] Erro ao buscar contexto BSC: {e}")
            client_context = "Contexto BSC não disponível. Análise baseada em princípios gerais."
        
        # Preparar variáveis do prompt
        company = client_profile.company
        context = client_profile.context
        
        challenges_text = ", ".join(context.current_challenges) if context.current_challenges else "Não informados"
        objectives_text = ", ".join(context.strategic_objectives) if context.strategic_objectives else "Não informados"
        
        # Formatar prompt com dados do cliente
        formatted_prompt = prompt_template.format(
            client_context=client_context,
            company_name=company.name,
            sector=company.sector,
            size=company.size,
            challenges=challenges_text,
            objectives=objectives_text,
        )
        
        # Chamar LLM com structured output
        structured_llm = self.llm.with_structured_output(DiagnosticResult)

        messages = [
            SystemMessage(content="Você é um especialista em Balanced Scorecard conduzindo análise diagnóstica."),
            HumanMessage(content=formatted_prompt),
        ]

        result = structured_llm.invoke(messages)  # type: ignore
        
        logger.info(f"[DIAGNOSTIC] Perspectiva {perspective} analisada: priority={result.priority}, gaps={len(result.gaps)}, opportunities={len(result.opportunities)}")
        
        return result
    
    async def run_parallel_analysis(
        self,
        client_profile: ClientProfile,
        state: BSCState,
    ) -> dict[str, DiagnosticResult]:
        """Executa análise das 4 perspectivas BSC em paralelo (AsyncIO).
        
        Usa asyncio.gather() para executar simultaneamente as 4 análises,
        otimizando latência (lição MVP: 3.34x speedup vs sequencial).
        
        Args:
            client_profile: Perfil completo do cliente
            state: Estado LangGraph atual
        
        Returns:
            dict: Mapa {perspective_name: DiagnosticResult} para as 4 perspectivas
        
        Example:
            >>> results = await agent.run_parallel_analysis(client_profile, state)
            >>> results.keys()
            dict_keys(['Financeira', 'Clientes', 'Processos Internos', 'Aprendizado e Crescimento'])
            >>> results['Financeira'].priority
            'HIGH'
        """
        logger.info("[DIAGNOSTIC] Iniciando análise paralela das 4 perspectivas BSC...")
        
        # Criar tasks para execução paralela
        tasks = {
            "Financeira": asyncio.to_thread(
                self.analyze_perspective,
                "Financeira",
                client_profile,
                state,
            ),
            "Clientes": asyncio.to_thread(
                self.analyze_perspective,
                "Clientes",
                client_profile,
                state,
            ),
            "Processos Internos": asyncio.to_thread(
                self.analyze_perspective,
                "Processos Internos",
                client_profile,
                state,
            ),
            "Aprendizado e Crescimento": asyncio.to_thread(
                self.analyze_perspective,
                "Aprendizado e Crescimento",
                client_profile,
                state,
            ),
        }
        
        # Executar em paralelo e aguardar todos
        results_list = await asyncio.gather(*tasks.values())
        
        # Mapear resultados de volta às perspectivas
        perspectives = list(tasks.keys())
        results = {perspectives[i]: results_list[i] for i in range(4)}
        
        logger.info("[DIAGNOSTIC] Análise paralela concluída: 4 perspectivas processadas")
        
        return results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, ValueError)),
        reraise=True,
    )
    def consolidate_diagnostic(
        self,
        perspective_results: dict[str, DiagnosticResult],
    ) -> dict[str, Any]:
        """Consolida análises das 4 perspectivas identificando synergies cross-perspective.
        
        Args:
            perspective_results: Mapa {perspective: DiagnosticResult} das 4 análises
        
        Returns:
            dict: {
                "cross_perspective_synergies": list[str],
                "executive_summary": str,
                "next_phase": str
            }
        
        Example:
            >>> consolidated = agent.consolidate_diagnostic(results)
            >>> len(consolidated["cross_perspective_synergies"])
            4
            >>> "Processos manuais" in consolidated["cross_perspective_synergies"][0]
            True
        """
        logger.info("[DIAGNOSTIC] Consolidando análises cross-perspective...")
        
        # Preparar resumo das 4 análises para o prompt
        analyses_text = ""
        for perspective, result in perspective_results.items():
            analyses_text += f"\n\n{perspective} (Priority: {result.priority}):\n"
            analyses_text += f"Current State: {result.current_state}\n"
            analyses_text += f"Gaps: {', '.join(result.gaps)}\n"
            analyses_text += f"Opportunities: {', '.join(result.opportunities)}\n"
        
        # Formatar prompt de consolidação
        formatted_prompt = CONSOLIDATE_DIAGNOSTIC_PROMPT.format(
            perspective_analyses=analyses_text
        )
        
        # Chamar LLM (output é dict, não Pydantic - estrutura variável)
        messages = [
            SystemMessage(content="Você é um consultor BSC sênior com visão sistêmica."),
            HumanMessage(content=formatted_prompt),
        ]
        
        response = self.llm.invoke(messages)

        # Parse JSON do content
        try:
            consolidated = json.loads(str(response.content))  # type: ignore
        except json.JSONDecodeError as e:
            logger.error(f"[DIAGNOSTIC] Erro ao parsear consolidação: {e}")
            raise ValueError(f"LLM retornou JSON inválido: {response.content[:200]}") from e
        
        # Validar campos obrigatórios
        required_fields = ["cross_perspective_synergies", "executive_summary", "next_phase"]
        for field in required_fields:
            if field not in consolidated:
                raise ValueError(f"Campo obrigatório ausente na consolidação: {field}")
        
        logger.info(
            f"[DIAGNOSTIC] Consolidação concluída: {len(consolidated['cross_perspective_synergies'])} synergies, "
            f"next_phase={consolidated['next_phase']}"
        )
        
        return consolidated
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, ValueError)),
        reraise=True,
    )
    def generate_recommendations(
        self,
        perspective_results: dict[str, DiagnosticResult],
        consolidated: dict[str, Any],
    ) -> list[Recommendation]:
        """Gera recomendações priorizadas baseadas no diagnóstico completo.
        
        Args:
            perspective_results: Resultados das 4 perspectivas
            consolidated: Consolidação cross-perspective
        
        Returns:
            list[Recommendation]: 5-10 recomendações priorizadas (HIGH → MEDIUM → LOW)
        
        Example:
            >>> recommendations = agent.generate_recommendations(results, consolidated)
            >>> len(recommendations)
            7
            >>> recommendations[0].priority
            'HIGH'
            >>> recommendations[0].timeframe
            'quick win (1-3 meses)'
        """
        logger.info("[DIAGNOSTIC] Gerando recomendações priorizadas...")
        
        # Preparar dados completos do diagnóstico para o prompt
        diagnostic_summary = f"""
EXECUTIVE SUMMARY:
{consolidated['executive_summary']}

CROSS-PERSPECTIVE SYNERGIES:
{chr(10).join(f"- {s}" for s in consolidated['cross_perspective_synergies'])}

ANÁLISES POR PERSPECTIVA:
"""
        
        for perspective, result in perspective_results.items():
            diagnostic_summary += f"\n{perspective} (Priority: {result.priority}):\n"
            diagnostic_summary += f"Gaps: {', '.join(result.gaps)}\n"
            diagnostic_summary += f"Opportunities: {', '.join(result.opportunities)}\n"
        
        # Formatar prompt de recomendações
        formatted_prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(
            complete_diagnostic=diagnostic_summary
        )
        
        # Chamar LLM com structured output (lista de Recommendations)
        messages = [
            SystemMessage(content="Você é um consultor BSC especialista em transformação organizacional."),
            HumanMessage(content=formatted_prompt),
        ]
        
        response = self.llm.invoke(messages)

        # Parse JSON do content
        try:
            recommendations_data = json.loads(str(response.content))  # type: ignore
        except json.JSONDecodeError as e:
            logger.error(f"[DIAGNOSTIC] Erro ao parsear recomendações: {e}")
            raise ValueError(f"LLM retornou JSON inválido: {response.content[:200]}") from e
        
        # Validar e criar objetos Pydantic Recommendation
        if not isinstance(recommendations_data, list):
            raise ValueError("LLM deve retornar lista de recomendações")
        
        recommendations = [Recommendation.model_validate(rec) for rec in recommendations_data]
        
        # Ordenar por prioridade: HIGH → MEDIUM → LOW
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda r: priority_order[r.priority])
        
        logger.info(
            f"[DIAGNOSTIC] {len(recommendations)} recomendações geradas: "
            f"HIGH={sum(1 for r in recommendations if r.priority == 'HIGH')}, "
            f"MEDIUM={sum(1 for r in recommendations if r.priority == 'MEDIUM')}, "
            f"LOW={sum(1 for r in recommendations if r.priority == 'LOW')}"
        )
        
        return recommendations
    
    def run_diagnostic(
        self,
        state: BSCState,
    ) -> CompleteDiagnostic:
        """Orquestrador completo do diagnóstico BSC multi-perspectiva.
        
        Workflow:
        1. Valida que ClientProfile está disponível no state
        2. Executa análise paralela das 4 perspectivas (AsyncIO)
        3. Consolida análises identificando synergies cross-perspective
        4. Gera recomendações priorizadas (matriz impacto vs esforço)
        5. Constrói CompleteDiagnostic com todos resultados
        
        Args:
            state: Estado LangGraph com client_profile preenchido
        
        Returns:
            CompleteDiagnostic: Diagnóstico completo validado (4 perspectivas + recomendações)
        
        Raises:
            ValueError: Se client_profile ausente ou dados insuficientes
            ValidationError: Se algum output não passar validação Pydantic
        
        Example:
            >>> diagnostic = agent.run_diagnostic(state)
            >>> diagnostic.financial.priority
            'HIGH'
            >>> len(diagnostic.recommendations)
            7
            >>> diagnostic.executive_summary[:50]
            'Empresa TechCorp apresenta sólido desempenho fi...'
        """
        logger.info("[DIAGNOSTIC] ========== INICIANDO DIAGNÓSTICO BSC COMPLETO ==========")
        
        # Validação: client_profile obrigatório
        if not state.client_profile:
            raise ValueError("client_profile ausente no state. Execute onboarding primeiro.")
        
        client_profile = state.client_profile
        
        # ETAPA 1: Análise paralela das 4 perspectivas (AsyncIO)
        logger.info("[DIAGNOSTIC] ETAPA 1/4: Análise paralela das 4 perspectivas BSC...")
        
        # Usar asyncio.run() para executar coroutine
        perspective_results = asyncio.run(
            self.run_parallel_analysis(client_profile, state)
        )
        
        # ETAPA 2: Consolidação cross-perspective
        logger.info("[DIAGNOSTIC] ETAPA 2/4: Consolidação cross-perspective...")
        
        consolidated = self.consolidate_diagnostic(perspective_results)
        
        # ETAPA 3: Geração de recomendações priorizadas
        logger.info("[DIAGNOSTIC] ETAPA 3/4: Geração de recomendações priorizadas...")
        
        recommendations = self.generate_recommendations(
            perspective_results,
            consolidated,
        )
        
        # ETAPA 4: Construir CompleteDiagnostic
        logger.info("[DIAGNOSTIC] ETAPA 4/4: Construindo diagnóstico completo...")
        
        complete_diagnostic = CompleteDiagnostic(
            financial=perspective_results["Financeira"],
            customer=perspective_results["Clientes"],
            process=perspective_results["Processos Internos"],
            learning=perspective_results["Aprendizado e Crescimento"],
            recommendations=recommendations,
            cross_perspective_synergies=consolidated["cross_perspective_synergies"],
            executive_summary=consolidated["executive_summary"],
            next_phase=consolidated["next_phase"],  # type: ignore
        )
        
        logger.info(
            f"[DIAGNOSTIC] ========== DIAGNÓSTICO CONCLUÍDO ========== "
            f"(Perspectives: 4, Recommendations: {len(recommendations)}, "
            f"Next Phase: {complete_diagnostic.next_phase})"
        )
        
        return complete_diagnostic

