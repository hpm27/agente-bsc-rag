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
    
    def generate_swot_analysis(
        self,
        client_profile: ClientProfile,
        use_rag: bool = True,
        refine_with_diagnostic: bool = False,
        diagnostic_result: CompleteDiagnostic | None = None,
    ):
        """Gera análise SWOT estruturada para a empresa.
        
        Utiliza SWOTAnalysisTool para facilitar análise SWOT contextualizada
        com conhecimento BSC (via RAG) e opcionalmente refinada com diagnóstico completo.
        
        Workflow:
        1. Extrai company_info e strategic_context do ClientProfile
        2. Chama SWOTAnalysisTool.facilitate_swot() para análise inicial
        3. (Opcional) Refina SWOT com diagnostic_result se disponível
        
        Args:
            client_profile: ClientProfile com contexto da empresa
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)
            refine_with_diagnostic: Se True, refina SWOT com diagnostic (default: False)
            diagnostic_result: CompleteDiagnostic para refinamento (obrigatório se refine_with_diagnostic=True)
            
        Returns:
            SWOTAnalysis: Objeto Pydantic validado com 4 quadrantes preenchidos
            
        Raises:
            ValueError: Se refine_with_diagnostic=True mas diagnostic_result=None
            ValueError: Se client_profile.company ou strategic_context ausentes
            
        Example:
            >>> # SWOT básico
            >>> swot = agent.generate_swot_analysis(profile, use_rag=True)
            >>> swot.is_complete()
            True
            
            >>> # SWOT refinado com diagnostic
            >>> diagnostic = agent.run_diagnostic(state)
            >>> swot = agent.generate_swot_analysis(
            ...     profile, 
            ...     refine_with_diagnostic=True, 
            ...     diagnostic_result=diagnostic
            ... )
        """
        from src.tools.swot_analysis import SWOTAnalysisTool
        
        logger.info(
            f"[DIAGNOSTIC] Gerando SWOT para {client_profile.company.name} "
            f"(use_rag={use_rag}, refine={refine_with_diagnostic})"
        )
        
        # Validações
        if not client_profile.company:
            raise ValueError("ClientProfile.company ausente. Dados insuficientes para SWOT.")
        
        if not client_profile.strategic_context:
            raise ValueError(
                "ClientProfile.strategic_context ausente. "
                "Execute onboarding completo antes de gerar SWOT."
            )
        
        if refine_with_diagnostic and not diagnostic_result:
            raise ValueError(
                "refine_with_diagnostic=True requer diagnostic_result. "
                "Execute run_diagnostic() primeiro ou desabilite refinamento."
            )
        
        # Instanciar SWOTAnalysisTool
        swot_tool = SWOTAnalysisTool(
            llm=self.llm,
            financial_agent=self.financial_agent,
            customer_agent=self.customer_agent,
            process_agent=self.process_agent,
            learning_agent=self.learning_agent,
        )
        
        # STEP 1: Facilitar SWOT inicial
        swot = swot_tool.facilitate_swot(
            company_info=client_profile.company,
            strategic_context=client_profile.strategic_context,
            use_rag=use_rag,
        )
        
        logger.info(
            f"[DIAGNOSTIC] SWOT gerado: {swot.total_items()} itens "
            f"(resumo: {swot.quadrant_summary()})"
        )
        
        # STEP 2: (Opcional) Refinar com diagnostic
        if refine_with_diagnostic and diagnostic_result:
            logger.info("[DIAGNOSTIC] Refinando SWOT com insights do diagnostic...")
            swot = swot_tool.refine_swot(swot, diagnostic_result)
            logger.info(
                f"[DIAGNOSTIC] SWOT refinado: {swot.total_items()} itens "
                f"(resumo: {swot.quadrant_summary()})"
            )
        
        # Validar completude
        if not swot.is_complete(min_items_per_quadrant=2):
            logger.warning(
                f"[DIAGNOSTIC] SWOT incompleto! Alguns quadrantes têm < 2 itens. "
                f"Resumo: {swot.quadrant_summary()}"
            )
        else:
            logger.info("[DIAGNOSTIC] SWOT completo e validado!")
        
        return swot
    
    def generate_five_whys_analysis(
        self,
        client_profile: ClientProfile,
        problem_statement: str,
        use_rag: bool = True,
    ):
        """Gera analise 5 Whys (causa raiz) para problema especifico da empresa.
        
        Utiliza FiveWhysTool para facilitar analise de causa raiz iterativa (3-7 niveis)
        contextualizada com conhecimento BSC (via RAG).
        
        Workflow:
        1. Extrai company_info e strategic_context do ClientProfile
        2. Chama FiveWhysTool.facilitate_five_whys() para analise iterativa
        3. Retorna FiveWhysAnalysis com iteracoes + root cause + acoes
        
        Args:
            client_profile: ClientProfile com contexto da empresa
            problem_statement: Problema especifico a analisar (ex: "Vendas baixas no Q3")
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)
            
        Returns:
            FiveWhysAnalysis: Objeto Pydantic validado com iteracoes + root cause
            
        Raises:
            ValueError: Se client_profile.company ou strategic_context ausentes
            ValueError: Se problem_statement vazio ou muito curto (< 10 chars)
            
        Example:
            >>> # 5 Whys basico
            >>> analysis = agent.generate_five_whys_analysis(
            ...     profile, 
            ...     problem_statement="Vendas baixas no ultimo trimestre",
            ...     use_rag=True
            ... )
            >>> analysis.is_complete()
            True
            >>> analysis.depth_reached()  # 3-7 iteracoes
            >>> analysis.root_cause_confidence()  # 0-100%
            
            >>> # Usar com desafio do ClientProfile
            >>> if profile.strategic_context.current_challenges:
            ...     main_challenge = profile.strategic_context.current_challenges[0]
            ...     analysis = agent.generate_five_whys_analysis(profile, main_challenge)
        """
        from src.tools.five_whys import FiveWhysTool
        
        logger.info(
            f"[DIAGNOSTIC] Gerando 5 Whys para {client_profile.company.name}: "
            f"'{problem_statement}' (use_rag={use_rag})"
        )
        
        # Validacoes
        if not client_profile.company:
            raise ValueError("ClientProfile.company ausente. Dados insuficientes para 5 Whys.")
        
        if not client_profile.strategic_context:
            raise ValueError(
                "ClientProfile.strategic_context ausente. "
                "Execute onboarding completo antes de gerar 5 Whys."
            )
        
        if not problem_statement or len(problem_statement) < 10:
            raise ValueError(
                f"problem_statement deve ter >= 10 chars "
                f"(recebeu: '{problem_statement}')"
            )
        
        # Instanciar FiveWhysTool
        five_whys_tool = FiveWhysTool(
            llm=self.llm,
            financial_agent=self.financial_agent,
            customer_agent=self.customer_agent,
            process_agent=self.process_agent,
            learning_agent=self.learning_agent,
            max_iterations=7,
        )
        
        # Facilitar 5 Whys iterativo
        analysis = five_whys_tool.facilitate_five_whys(
            company_info=client_profile.company,
            strategic_context=client_profile.strategic_context,
            problem_statement=problem_statement,
            use_rag=use_rag,
        )
        
        logger.info(
            f"[DIAGNOSTIC] 5 Whys gerado: {analysis.depth_reached()} iteracoes, "
            f"root cause: '{analysis.root_cause[:50]}...', "
            f"confidence: {analysis.root_cause_confidence()}%, "
            f"{len(analysis.recommended_actions)} acoes recomendadas"
        )
        
        # Validar completude
        if not analysis.is_complete():
            logger.warning(
                f"[DIAGNOSTIC] 5 Whys incompleto! "
                f"Iteracoes: {len(analysis.iterations)}, "
                f"Acoes: {len(analysis.recommended_actions)}"
            )
        else:
            logger.info("[DIAGNOSTIC] 5 Whys completo e validado!")
        
        # Validar confianca minima
        if analysis.root_cause_confidence() < 70.0:
            logger.warning(
                f"[DIAGNOSTIC] Confidence baixa ({analysis.root_cause_confidence()}%). "
                f"Considere aprofundar analise ou fornecer mais contexto."
            )
        
        return analysis
    
    def generate_issue_tree_analysis(
        self,
        client_profile: ClientProfile,
        root_problem: str,
        max_depth: int = 3,
        use_rag: bool = True,
    ):
        """Gera analise Issue Tree (decomposicao MECE) para problema estrategico.
        
        Utiliza IssueTreeTool para decomposicao hierarquica MECE (Mutually Exclusive,
        Collectively Exhaustive) do problema em sub-problemas, gerando arvore de solucoes
        contextualizada com conhecimento BSC (via RAG).
        
        Workflow:
        1. Extrai company_info e strategic_context do ClientProfile
        2. Chama IssueTreeTool.facilitate_issue_tree() para decomposicao iterativa
        3. Retorna IssueTreeAnalysis com nodes hierarquicos + solution paths
        
        Args:
            client_profile: ClientProfile com contexto da empresa
            root_problem: Problema raiz a decompor (ex: "Baixa lucratividade empresa")
            max_depth: Profundidade maxima arvore (default 3, min 1, max 4)
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)
            
        Returns:
            IssueTreeAnalysis: Objeto Pydantic validado com nodes + solution paths
            
        Raises:
            ValueError: Se client_profile.company ou strategic_context ausentes
            ValueError: Se root_problem vazio ou muito curto (< 10 chars)
            ValueError: Se max_depth fora do range (1-4)
            
        Example:
            >>> # Issue Tree basico
            >>> tree = agent.generate_issue_tree_analysis(
            ...     profile, 
            ...     root_problem="Baixa lucratividade empresa manufatura",
            ...     max_depth=3,
            ...     use_rag=True
            ... )
            >>> tree.is_complete()
            True
            >>> tree.total_nodes()  # 1 root + N sub-problemas
            15
            >>> tree.validate_mece()  # {"is_mece": True, "issues": [], "confidence": 0.85}
            
            >>> # Usar com desafio do ClientProfile
            >>> if profile.strategic_context.current_challenges:
            ...     main_challenge = profile.strategic_context.current_challenges[0]
            ...     tree = agent.generate_issue_tree_analysis(profile, main_challenge)
        """
        from src.tools.issue_tree import IssueTreeTool
        
        logger.info(
            f"[DIAGNOSTIC] Gerando Issue Tree para {client_profile.company.name}: "
            f"'{root_problem}' (max_depth={max_depth}, use_rag={use_rag})"
        )
        
        # Validacoes
        if not client_profile.company:
            raise ValueError("ClientProfile.company ausente. Dados insuficientes para Issue Tree.")
        
        if not client_profile.strategic_context:
            raise ValueError(
                "ClientProfile.strategic_context ausente. "
                "Execute onboarding completo antes de gerar Issue Tree."
            )
        
        if not root_problem or len(root_problem) < 10:
            raise ValueError(
                f"root_problem deve ter >= 10 chars "
                f"(recebeu: '{root_problem}')"
            )
        
        if not (1 <= max_depth <= 4):
            raise ValueError(
                f"max_depth deve ser 1-4 "
                f"(recebeu: {max_depth})"
            )
        
        # Instanciar IssueTreeTool
        issue_tree_tool = IssueTreeTool(
            llm=self.llm,
            financial_agent=self.financial_agent,
            customer_agent=self.customer_agent,
            process_agent=self.process_agent,
            learning_agent=self.learning_agent,
        )
        
        # Facilitar Issue Tree decomposicao MECE
        tree_analysis = issue_tree_tool.facilitate_issue_tree(
            company_info=client_profile.company,
            strategic_context=client_profile.strategic_context,
            root_problem=root_problem,
            max_depth=max_depth,
            use_rag=use_rag,
        )
        
        logger.info(
            f"[DIAGNOSTIC] Issue Tree gerado: {tree_analysis.total_nodes()} nodes, "
            f"{tree_analysis.max_depth} niveis profundidade, "
            f"{len(tree_analysis.get_leaf_nodes())} leaf nodes (solucoes), "
            f"{len(tree_analysis.solution_paths)} solution paths"
        )
        
        # Validar completude MECE
        if not tree_analysis.is_complete(min_branches=2):
            logger.warning(
                f"[DIAGNOSTIC] Issue Tree incompleto! "
                f"Alguns niveis tem < 2 branches (nao MECE Collectively Exhaustive)"
            )
        else:
            logger.info("[DIAGNOSTIC] Issue Tree completo (>= 2 branches por nivel)!")
        
        # Validar MECE heuristica
        mece_validation = tree_analysis.validate_mece()
        if not mece_validation["is_mece"]:
            logger.warning(
                f"[DIAGNOSTIC] MECE validation falhou! "
                f"Issues: {', '.join(mece_validation['issues'])}, "
                f"Confidence: {mece_validation['confidence']:.0%}"
            )
        else:
            logger.info(
                f"[DIAGNOSTIC] MECE validation OK! "
                f"Confidence: {mece_validation['confidence']:.0%}"
            )
        
        return tree_analysis
    
    def generate_kpi_framework(
        self,
        client_profile: ClientProfile,
        diagnostic_result: CompleteDiagnostic,
        use_rag: bool = True,
    ):
        """Gera framework de KPIs SMART para as 4 perspectivas BSC.
        
        Utiliza KPIDefinerTool para definir 2-8 KPIs por perspectiva BSC,
        totalizando 8-32 KPIs customizados para a empresa.
        
        Workflow:
        1. Extrai company_info e strategic_context do ClientProfile
        2. Usa diagnostic_result para contextualizar KPIs
        3. (Opcional) Busca conhecimento BSC via specialist agents (RAG)
        4. Chama KPIDefinerTool.define_kpis() para gerar framework completo
        5. Valida balanceamento (nenhuma perspectiva com >40% dos KPIs)
        
        Args:
            client_profile: ClientProfile com contexto da empresa
            diagnostic_result: Diagnostico BSC completo (4 perspectivas)
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)
        
        Returns:
            KPIFramework: Framework validado com 8-32 KPIs (2-8 por perspectiva)
        
        Raises:
            ValueError: Se dados insuficientes para definir KPIs
            ValidationError: Se KPIs gerados nao passam em validacoes Pydantic
        
        Example:
            >>> # Definir KPIs apos diagnostic
            >>> diagnostic = agent.run_diagnostic(state)
            >>> kpi_framework = agent.generate_kpi_framework(
            ...     client_profile=profile,
            ...     diagnostic_result=diagnostic,
            ...     use_rag=True
            ... )
            >>> kpi_framework.total_kpis()
            14
            >>> len(kpi_framework.financial_kpis)
            4
        """
        from src.tools.kpi_definer import KPIDefinerTool
        
        logger.info(
            f"[DIAGNOSTIC] Gerando KPI Framework para {client_profile.company.name} "
            f"(use_rag={use_rag})"
        )
        
        # Validacoes
        if not client_profile.company:
            raise ValueError("ClientProfile.company ausente. Dados insuficientes para KPIs.")
        
        if not client_profile.strategic_context:
            raise ValueError(
                "ClientProfile.strategic_context ausente. "
                "Execute onboarding completo antes de definir KPIs."
            )
        
        if not diagnostic_result:
            raise ValueError(
                "diagnostic_result ausente. "
                "Execute run_diagnostic() antes de definir KPIs para contextualizar."
            )
        
        # Instanciar KPIDefinerTool
        kpi_tool = KPIDefinerTool(
            llm=self.llm,
            financial_agent=self.financial_agent,
            customer_agent=self.customer_agent,
            process_agent=self.process_agent,
            learning_agent=self.learning_agent,
        )
        
        # Definir KPIs para 4 perspectivas
        framework = kpi_tool.define_kpis(
            company_info=client_profile.company,
            strategic_context=client_profile.strategic_context,
            diagnostic_result=diagnostic_result,
            use_rag=use_rag,
        )
        
        logger.info(
            f"[DIAGNOSTIC] KPI Framework gerado: {framework.total_kpis()} KPIs total "
            f"(Financeira: {len(framework.financial_kpis)}, "
            f"Clientes: {len(framework.customer_kpis)}, "
            f"Processos: {len(framework.process_kpis)}, "
            f"Aprendizado: {len(framework.learning_kpis)})"
        )
        
        # Validar balanceamento
        counts = {
            "Financeira": len(framework.financial_kpis),
            "Clientes": len(framework.customer_kpis),
            "Processos": len(framework.process_kpis),
            "Aprendizado": len(framework.learning_kpis)
        }
        
        total = framework.total_kpis()
        max_count = max(counts.values())
        max_percentage = (max_count / total) * 100
        
        if max_percentage > 40:
            logger.warning(
                f"[DIAGNOSTIC] Framework desbalanceado! Uma perspectiva tem "
                f"{max_percentage:.0f}% dos KPIs (recomendado <40%). "
                f"Distribuicao: {counts}"
            )
        else:
            logger.info(
                f"[DIAGNOSTIC] Framework balanceado! Distribuicao: {counts}"
            )
        
        return framework
    
    def generate_strategic_objectives(
        self,
        client_profile: ClientProfile,
        diagnostic_result: CompleteDiagnostic,
        existing_kpis: Optional["KPIFramework"] = None,
        use_rag: bool = True,
    ):
        """Gera framework de objetivos estrategicos SMART para as 4 perspectivas BSC.
        
        Utiliza StrategicObjectivesTool para definir 2-5 objetivos estrategicos por
        perspectiva BSC, totalizando 8-20 objetivos customizados para a empresa.
        
        Workflow:
        1. Extrai company_info e strategic_context do ClientProfile
        2. Usa diagnostic_result para contextualizar objetivos
        3. (Opcional) Vincula com KPIs existentes para alinhamento
        4. (Opcional) Busca conhecimento BSC via specialist agents (RAG)
        5. Chama StrategicObjectivesTool.define_objectives() para gerar framework completo
        6. Valida balanceamento entre perspectivas (warning se desbalanceado)
        7. Retorna StrategicObjectivesFramework completo
        
        Args:
            client_profile: Perfil do cliente com company_info
            diagnostic_result: Resultado completo do diagnostico BSC
            existing_kpis: Framework de KPIs existente para vinculacao (opcional)
            use_rag: Se True, busca conhecimento BSC via specialist agents
        
        Returns:
            StrategicObjectivesFramework: Framework com objetivos das 4 perspectivas
        
        Raises:
            ValueError: Se client_profile ou diagnostic_result invalidos
            RuntimeError: Se tool falha ao gerar objetivos
        
        Example:
            >>> agent = DiagnosticAgent(...)
            >>> 
            >>> # Sem KPIs
            >>> objectives = agent.generate_strategic_objectives(
            ...     client_profile=profile,
            ...     diagnostic_result=diagnostic,
            ...     use_rag=True
            ... )
            >>> objectives.total_objectives()
            12
            >>> 
            >>> # Com KPIs vinculados
            >>> objectives = agent.generate_strategic_objectives(
            ...     client_profile=profile,
            ...     diagnostic_result=diagnostic,
            ...     existing_kpis=kpi_framework,
            ...     use_rag=True
            ... )
            >>> len(objectives.with_related_kpis())
            8  # 8 de 12 objetivos tem KPIs vinculados
        """
        from src.tools.strategic_objectives import StrategicObjectivesTool
        
        logger.info(
            f"[DIAGNOSTIC] Gerando Strategic Objectives Framework para {client_profile.company.name} "
            f"(use_rag={use_rag}, com_kpis={existing_kpis is not None})"
        )
        
        # Validar inputs
        if not client_profile or not client_profile.company:
            raise ValueError(
                "client_profile com company obrigatorio para gerar strategic objectives"
            )
        
        if not diagnostic_result:
            raise ValueError(
                "diagnostic_result obrigatorio para contextualizar strategic objectives"
            )
        
        # Extrair company_info do ClientProfile
        company_info = client_profile.company
        
        # Extrair strategic_context do ClientProfile ou diagnostic
        strategic_context = (
            client_profile.context or
            diagnostic_result.executive_summary[:200] if diagnostic_result.executive_summary else
            "Contexto estrategico nao fornecido"
        )
        
        # Lazy load tool
        if not hasattr(self, "_strategic_objectives_tool"):
            rag_agents = None
            if use_rag:
                rag_agents = (
                    self.financial_agent,
                    self.customer_agent,
                    self.process_agent,
                    self.learning_agent
                )
            
            self._strategic_objectives_tool = StrategicObjectivesTool(
                llm=self.llm,
                use_rag=use_rag,
                rag_agents=rag_agents
            )
            logger.info("[DIAGNOSTIC] StrategicObjectivesTool inicializada (lazy loading)")
        
        # Gerar framework de objetivos
        try:
            framework = self._strategic_objectives_tool.define_objectives(
                company_info=company_info,
                strategic_context=strategic_context,
                diagnostic_result=diagnostic_result,
                existing_kpis=existing_kpis
            )
            
            logger.info(
                f"[DIAGNOSTIC] Strategic Objectives Framework gerado: "
                f"{framework.total_objectives()} objetivos totais"
            )
            
        except Exception as e:
            logger.error(
                f"[DIAGNOSTIC] Erro ao gerar Strategic Objectives Framework: {e}"
            )
            raise RuntimeError(
                f"Falha ao gerar Strategic Objectives Framework: {str(e)}"
            ) from e
        
        # Validar balanceamento (warning se desbalanceado, mas nao bloqueia)
        counts = {
            "Financeira": len(framework.financial_objectives),
            "Clientes": len(framework.customer_objectives),
            "Processos": len(framework.process_objectives),
            "Aprendizado": len(framework.learning_objectives)
        }
        
        total = framework.total_objectives()
        max_count = max(counts.values())
        max_percentage = (max_count / total) * 100 if total > 0 else 0
        
        if max_percentage > 50:
            logger.warning(
                f"[DIAGNOSTIC] Framework desbalanceado! Uma perspectiva tem "
                f"{max_percentage:.0f}% dos objetivos (recomendado <50%). "
                f"Distribuicao: {counts}"
            )
        else:
            logger.info(
                f"[DIAGNOSTIC] Framework balanceado! Distribuicao: {counts}"
            )
        
        # Log vinculacao com KPIs (se fornecidos)
        if existing_kpis:
            with_kpis = len(framework.with_related_kpis())
            kpi_percentage = (with_kpis / total) * 100 if total > 0 else 0
            logger.info(
                f"[DIAGNOSTIC] Vinculacao com KPIs: {with_kpis}/{total} objetivos "
                f"({kpi_percentage:.0f}%) tem KPIs relacionados"
            )
        
        return framework
    
    def generate_benchmarking_report(
        self,
        client_id: str,
        use_rag: bool = False
    ):
        """Gera relatório de benchmarking BSC comparando empresa com benchmarks externos.
        
        Utiliza BenchmarkingTool para comparar desempenho atual da empresa com
        benchmarks externos relevantes (setor, porte, região) nas 4 perspectivas BSC.
        
        Workflow:
        1. Retrieve client_profile (company_info, context)
        2. Retrieve diagnostic (4 perspectivas BSC)
        3. Retrieve kpi_framework (opcional, valores atuais)
        4. (Opcional) RAG para contexto literatura BSC
        5. Chama BenchmarkingTool.generate_benchmarks()
        6. Valida qualidade do report (gaps realistas, balanceamento)
        7. Salva em memória via memory_client
        8. Retorna BenchmarkReport completo
        
        Args:
            client_id: ID do cliente no sistema de memória
            use_rag: Se True, busca contexto da literatura BSC (default: False)
        
        Returns:
            BenchmarkReport: Relatório com 6-20 comparações balanceadas, gaps, recomendações
        
        Raises:
            ValueError: Se client_id não encontrado ou diagnostic incompleto
            RuntimeError: Se tool falha ao gerar benchmarks
        
        Example:
            >>> agent = DiagnosticAgent(...)
            >>> 
            >>> # Sem RAG (mais rápido)
            >>> report = agent.generate_benchmarking_report(
            ...     client_id="cliente_001",
            ...     use_rag=False
            ... )
            >>> print(report.summary())
            >>> 
            >>> # Com RAG (contexto literatura BSC)
            >>> report = agent.generate_benchmarking_report(
            ...     client_id="cliente_001",
            ...     use_rag=True
            ... )
            >>> report.overall_performance
            'abaixo_mercado'
            >>> len(report.high_priority_comparisons())
            5
        """
        from src.tools.benchmarking_tool import BenchmarkingTool
        
        logger.info(
            f"[DIAGNOSTIC] Gerando Benchmark Report para client_id={client_id} "
            f"(use_rag={use_rag})"
        )
        
        # ========== RETRIEVE DEPENDENCIES ==========
        
        # Retrieve client_profile (company_info)
        client_profile = self.memory_client.get_client_profile(client_id)
        if not client_profile:
            raise ValueError(
                f"Cliente '{client_id}' não encontrado. "
                f"Execute onboarding primeiro."
            )
        
        # Retrieve diagnostic (4 perspectivas)
        diagnostic_result = self.memory_client.get_diagnostic(client_id)
        if not diagnostic_result:
            raise ValueError(
                f"Diagnóstico não encontrado para cliente '{client_id}'. "
                f"Execute diagnóstico BSC primeiro."
            )
        
        # Convert CompleteDiagnostic to dict[str, DiagnosticResult]
        diagnostic_dict = {
            "Financeira": diagnostic_result.financial,
            "Clientes": diagnostic_result.customer,
            "Processos Internos": diagnostic_result.process,
            "Aprendizado e Crescimento": diagnostic_result.learning
        }
        
        # Retrieve kpi_framework (opcional)
        kpi_framework = None
        try:
            kpi_framework = self.memory_client.get_kpi_framework(client_id)
            if kpi_framework:
                logger.info(
                    f"[DIAGNOSTIC] KPI Framework encontrado "
                    f"({kpi_framework.total_kpis()} KPIs) - será usado no benchmarking"
                )
        except Exception as e:
            logger.warning(
                f"[DIAGNOSTIC] Erro ao recuperar KPI Framework (não crítico): {e}. "
                f"Continuando sem KPIs."
            )
        
        # ========== LAZY LOAD TOOL ==========
        
        if not hasattr(self, "_benchmarking_tool"):
            retriever = self.retriever if use_rag else None
            
            self._benchmarking_tool = BenchmarkingTool(
                llm=self.llm,
                retriever=retriever
            )
            logger.info("[DIAGNOSTIC] BenchmarkingTool inicializada (lazy loading)")
        
        # ========== GENERATE BENCHMARKS ==========
        
        try:
            report = self._benchmarking_tool.generate_benchmarks(
                company_info=client_profile.company,
                diagnostic=diagnostic_dict,
                kpi_framework=kpi_framework,
                use_rag=use_rag
            )
            
            logger.info(
                f"[DIAGNOSTIC] Benchmark Report gerado: "
                f"{len(report.comparisons)} comparações, "
                f"performance={report.overall_performance}"
            )
        
        except Exception as e:
            logger.error(
                f"[DIAGNOSTIC] Erro ao gerar Benchmark Report: {e}"
            )
            raise RuntimeError(
                f"Falha ao gerar Benchmark Report: {str(e)}"
            ) from e
        
        # ========== SAVE TO MEMORY ==========
        
        try:
            self.memory_client.save_benchmark_report(client_id, report)
            logger.info(
                f"[DIAGNOSTIC] Benchmark Report salvo em memória (client_id={client_id})"
            )
        except Exception as e:
            logger.warning(
                f"[DIAGNOSTIC] Erro ao salvar Benchmark Report em memória: {e}. "
                f"Report gerado mas não persistido."
            )
        
        return report

