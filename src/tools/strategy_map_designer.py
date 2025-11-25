"""
Strategy Map Designer Tool - Sprint 2

Converte diagnóstico BSC em Strategy Map visual estruturado com:
- 4 perspectivas balanceadas (Financial, Customer, Process, Learning)
- Objetivos estratégicos SMART por perspectiva (8-10 cada)
- Conexões causa-efeito (Learning -> Process -> Customer -> Financial)
- Validação contra framework Kaplan & Norton

PATTERN: Reutiliza pattern RAG validado do Sprint 1 (_retrieve_bsc_knowledge + asyncio.gather).

Best Practices (BSCDesigner 2025):
- 8-10 objectives per perspective (RED FLAG se >10)
- Cada objetivo: goal + rationale + leading KPI + lagging KPI
- Conexões causa-efeito explícitas entre perspectivas
- Goals ESTRATÉGICOS (não operacionais)
- SEM jargon genérico
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Dict
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

if TYPE_CHECKING:
    from src.memory.schemas import ClientProfile

from src.memory.schemas import (
    CompleteDiagnostic,
    StrategyMap,
    StrategyMapPerspective,
    CauseEffectConnection,
    DiagnosticToolsResult,
)
from config.settings import get_llm_for_agent

logger = logging.getLogger(__name__)


# ============================================================================
# PROMPTS (Baseados em research Brightdata 2024-2025)
# ============================================================================

DESIGN_STRATEGY_MAP_PROMPT = """Você é um consultor BSC sênior especialista em Strategy Maps (Kaplan & Norton framework).

Converta o diagnóstico BSC em Strategy Map estruturado com 4 perspectivas balanceadas.

DIAGNÓSTICO BSC:
{diagnostic}

FERRAMENTAS CONSULTIVAS (SWOT, KPIs, Objectives):
{tools_results}

CONTEXTO RAG DA LITERATURA BSC (Kaplan & Norton):
{rag_context}

FRAMEWORK STRATEGY MAP (Kaplan & Norton 2025):
- 4 Perspectivas: Financial, Customer, Process, Learning/Growth
- 8-10 objetivos estratégicos por perspectiva (RED FLAG se >10)
- Cada objetivo: goal + rationale + leading KPI + lagging KPI
- Conexões causa-efeito: Learning -> Process -> Customer -> Financial

REGRAS CRÍTICAS (BSCDesigner 2025):
1. Goals ESTRATÉGICOS (não operacionais: "implementar ERP" é operacional [ERRO])
2. Goals com CONEXÕES causa-efeito (não isolated goals [ERRO])
3. Rationale EXPLÍCITO (WHY escolheu esse goal)
4. KPIs SMART (específicos, mensuráveis, atingíveis, relevantes, temporais)
5. SEM jargon genérico ("leverage synergies", "drive innovation" [ERRO])
6. USE terminologia BSC oficial da literatura (contexto RAG)

STRATEGIC PRIORITIES (top 3):
Identifique as 3 prioridades estratégicas mais críticas do diagnóstico.
Típico: "Serve clients better", "Improve operations", "Improve product/service".

RETORNE StrategyMap completo (JSON schema fornecido).
"""

MAP_CAUSE_EFFECT_PROMPT = """Você é um consultor BSC especialista em mapeamento causa-efeito.

Identifique TODAS as conexões causa-efeito entre objetivos estratégicos das 4 perspectivas.

OBJECTIVES POR PERSPECTIVA:
{objectives_by_perspective}

FRAMEWORK CAUSA-EFEITO (Kaplan & Norton):
- Lógica TOP-DOWN: Financial <- Customer <- Process <- Learning
- Lower perspectives EXPLICAM como atingir higher perspectives
- Todo goal DEVE ter conexões (não isolated)
- Conexões típicas:
  * Learning -> Process: "Capacitar equipe em Lean" -> "Reduzir waste em 30%"
  * Process -> Customer: "Reduzir lead time em 40%" -> "Aumentar OTIF para 95%"
  * Customer -> Financial: "Aumentar NPS para 50+" -> "Reduzir churn para <5%" -> "Aumentar EBITDA para 18%"

RELATIONSHIP TYPES:
- "enables": Permite alcançar (ex: capacitação -> melhor execução)
- "supports": Suporta diretamente (ex: OEE alto -> lead time baixo)
- "drives": Impulsiona resultado (ex: OTIF alto -> NPS alto)

STRENGTH LEVELS:
- "strong": Conexão direta e validada na literatura BSC
- "medium": Conexão provável mas dependente de contexto
- "weak": Conexão indireta ou condicional

RETORNE lista de CauseEffectConnection (JSON schema fornecido).
Mínimo: 4 conexões (1 entre cada par de perspectivas adjacentes).
Ideal: 8-12 conexões para Strategy Map completo.
"""


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================


class StrategyMapDesignerTool:
    """
    Converte diagnóstico BSC em Strategy Map estruturado.

    ARQUITETURA:
    1. _retrieve_bsc_knowledge() - Consulta RAG (4 agents paralelos)
    2. _extract_objectives_by_perspective() - LLM estruturado (com RAG context)
    3. _map_cause_effect_connections() - LLM estruturado (mapeamento conexões)
    4. design_strategy_map() - Orquestração completa

    DEPENDENCIES:
    - 4 specialist agents (Financial, Customer, Process, Learning) - via RAG
    - StrategicObjectivesTool (reutilização FASE 3)
    - KPIDefinerTool (reutilização FASE 3)
    """

    def __init__(self, financial_agent, customer_agent, process_agent, learning_agent, llm=None):
        self.financial_agent = financial_agent
        self.customer_agent = customer_agent
        self.process_agent = process_agent
        self.learning_agent = learning_agent
        # SESSAO 45: LLM ferramentas (Claude Opus 4.5 - structured output confiável)
        self.llm = llm or get_llm_for_agent("tools")

        logger.info("[StrategyMapDesigner] Inicializado com 4 specialist agents + LLM")

    async def _retrieve_bsc_knowledge(
        self,
        diagnostic: CompleteDiagnostic,
        tools_results: DiagnosticToolsResult | None,
        client_profile: "ClientProfile",
    ) -> str:
        """
        Consulta RAG para recuperar contexto da literatura BSC.

        PATTERN VALIDADO (Sprint 1): asyncio.gather() com 4 agents.ainvoke().

        Query focus: Strategy Map design, causa-efeito, KPIs por perspectiva.

        Args:
            diagnostic: Diagnóstico completo BSC
            tools_results: Resultados ferramentas consultivas (opcional)
            client_profile: Profile empresa (para nome e setor)
        """
        logger.info("[StrategyMapDesigner] Iniciando retrieval RAG (4 agents paralelos)")

        # Construir query RAG focada em Strategy Map (usando ClientProfile)
        company_name = client_profile.company.name if client_profile.company else "Empresa"
        sector = client_profile.company.sector if client_profile.company else "Geral"

        rag_query = f"""Strategy Map BSC para {company_name} (setor {sector}):

Preciso de conhecimento da literatura BSC (Kaplan & Norton) sobre:
1. Objetivos estratégicos típicos por perspectiva (Financial, Customer, Process, Learning)
2. Conexões causa-efeito comuns entre perspectivas
3. KPIs leading e lagging recomendados
4. Best practices de balanceamento (8-10 objectives per perspective)

Contexto do diagnóstico:
- Principais oportunidades: {', '.join([rec.title for rec in diagnostic.recommendations[:3]]) if diagnostic.recommendations else 'N/A'}
- Perspectivas: Financial, Customer, Process, Learning

Foco: Framework Kaplan & Norton oficial, terminologia BSC, exemplos validados.
"""

        # EXECUÇÃO PARALELA (pattern Sprint 1 validado)
        financial_task = self.financial_agent.ainvoke(rag_query)
        customer_task = self.customer_agent.ainvoke(rag_query)
        process_task = self.process_agent.ainvoke(rag_query)
        learning_task = self.learning_agent.ainvoke(rag_query)

        financial_result, customer_result, process_result, learning_result = await asyncio.gather(
            financial_task, customer_task, process_task, learning_task
        )

        # Consolidar contexto RAG
        rag_context = f"""
CONTEXTO FINANCEIRO BSC (literatura Kaplan & Norton):
{financial_result.get('output', '')[:1500]}

CONTEXTO CLIENTES BSC (literatura Kaplan & Norton):
{customer_result.get('output', '')[:1500]}

CONTEXTO PROCESSOS BSC (literatura Kaplan & Norton):
{process_result.get('output', '')[:1500]}

CONTEXTO APRENDIZADO BSC (literatura Kaplan & Norton):
{learning_result.get('output', '')[:1500]}
"""

        logger.info(f"[StrategyMapDesigner] RAG retrieval completo: {len(rag_context)} chars")
        return rag_context

    async def _extract_objectives_by_perspective(
        self,
        diagnostic: CompleteDiagnostic,
        tools_results: DiagnosticToolsResult | None,
        rag_context: str,
    ) -> Dict[str, StrategyMapPerspective]:
        """
        Extrai objetivos estratégicos por perspectiva usando LLM structured output.

        IMPORTANTE: Usa RAG context para validar contra framework K&N oficial.
        """
        logger.info("[StrategyMapDesigner] Extraindo objectives por perspectiva (LLM structured)")

        # Preparar contexto de ferramentas consultivas (SWOT, KPIs, Strategic Objectives)
        tools_summary = "N/A"
        if tools_results:
            swot = tools_results.swot_analysis or {}
            kpis = tools_results.kpi_framework or {}
            objectives = tools_results.strategic_objectives or {}

            tools_summary = f"""
SWOT Analysis:
- Forças: {', '.join(swot.get('strengths', [])[:3]) if swot.get('strengths') else 'N/A'}
- Oportunidades: {', '.join(swot.get('opportunities', [])[:3]) if swot.get('opportunities') else 'N/A'}

KPI Framework:
- Financial KPIs: {', '.join(kpis.get('financial_kpis', [])[:5]) if kpis.get('financial_kpis') else 'N/A'}
- Customer KPIs: {', '.join(kpis.get('customer_kpis', [])[:5]) if kpis.get('customer_kpis') else 'N/A'}

Strategic Objectives (já definidos):
{objectives.get('objectives_summary', 'N/A')[:500] if objectives else 'N/A'}
"""

        # Montar prompt com RAG context
        prompt_content = DESIGN_STRATEGY_MAP_PROMPT.format(
            diagnostic=str(diagnostic)[:2000], tools_results=tools_summary, rag_context=rag_context
        )

        messages = [
            SystemMessage(
                content="Você é um consultor BSC sênior especialista em Strategy Maps (Kaplan & Norton framework)."
            ),
            HumanMessage(content=prompt_content),
        ]

        # Usar LLM structured output para StrategyMap
        structured_llm = self.llm.with_structured_output(StrategyMap, method="function_calling")

        try:
            strategy_map = await structured_llm.ainvoke(messages)

            if strategy_map is None:
                logger.error("[StrategyMapDesigner] LLM retornou None (structured output failed)")
                raise ValueError(
                    "LLM structured output retornou None - possível finish_reason != 'stop'"
                )

            logger.info("[StrategyMapDesigner] Strategy Map extraído: 4 perspectivas completas")

            # Converter StrategyMap em dict por nome de perspectiva
            perspectives_dict = {
                "Financeira": strategy_map.financial,
                "Clientes": strategy_map.customer,
                "Processos Internos": strategy_map.process,
                "Aprendizado e Crescimento": strategy_map.learning,
            }

            return perspectives_dict

        except Exception as e:
            logger.error(f"[StrategyMapDesigner] Erro ao extrair objectives: {e}")
            raise

    async def _map_cause_effect_connections(
        self, perspectives_dict: Dict[str, StrategyMapPerspective]
    ) -> list[CauseEffectConnection]:
        """
        Mapeia conexões causa-efeito entre objetivos de diferentes perspectivas.

        FRAMEWORK: Learning -> Process -> Customer -> Financial (top-down logic).
        """
        logger.info("[StrategyMapDesigner] Mapeando conexões causa-efeito (LLM structured)")

        # Preparar objetivos por perspectiva para o prompt
        objectives_summary = ""
        for perspective_name, perspective in perspectives_dict.items():
            if perspective:
                objectives_summary += f"\n{perspective_name}:\n"
                for idx, obj in enumerate(perspective.objectives, 1):
                    # Bug #9 fix: StrategicObjective NÃO tem campo 'owner' (campos reais: name, description, perspective, timeframe, success_criteria, related_kpis, priority, dependencies)
                    objectives_summary += f"  {idx}. {obj.name} (timeframe: {obj.timeframe}, priority: {obj.priority})\n"

        # Montar prompt de mapeamento
        prompt_content = MAP_CAUSE_EFFECT_PROMPT.format(
            objectives_by_perspective=objectives_summary
        )

        messages = [
            SystemMessage(
                content="Você é um consultor BSC especialista em mapeamento causa-efeito."
            ),
            HumanMessage(content=prompt_content),
        ]

        # Schema temporário para lista de conexões
        from pydantic import BaseModel

        class CauseEffectList(BaseModel):
            connections: list[CauseEffectConnection]

        structured_llm = self.llm.with_structured_output(CauseEffectList, method="function_calling")

        try:
            result = await structured_llm.ainvoke(messages)

            if result is None or not result.connections:
                logger.warning(
                    "[StrategyMapDesigner] LLM não retornou conexões causa-efeito (usando mínimo)"
                )
                # Criar conexões mínimas default (4 obrigatórias)
                return self._create_default_connections(perspectives_dict)

            logger.info(
                f"[StrategyMapDesigner] Conexões causa-efeito mapeadas: {len(result.connections)}"
            )
            return result.connections

        except Exception as e:
            logger.error(f"[StrategyMapDesigner] Erro ao mapear causa-efeito: {e}")
            # Fallback: criar conexões mínimas
            return self._create_default_connections(perspectives_dict)

    def _create_default_connections(
        self, perspectives_dict: Dict[str, StrategyMapPerspective]
    ) -> list[CauseEffectConnection]:
        """
        Cria conexões causa-efeito mínimas default (fallback).

        Conecta o primeiro objetivo de cada perspectiva seguindo lógica K&N:
        Learning -> Process -> Customer -> Financial
        """
        logger.info("[StrategyMapDesigner] Criando conexões causa-efeito default (fallback)")

        connections = []

        # Learning -> Process
        learning_obj = perspectives_dict.get("Aprendizado e Crescimento")
        process_obj = perspectives_dict.get("Processos Internos")
        if learning_obj and process_obj and learning_obj.objectives and process_obj.objectives:
            connections.append(
                CauseEffectConnection(
                    source_objective_id=learning_obj.objectives[0].name,
                    target_objective_id=process_obj.objectives[0].name,
                    relationship_type="enables",
                    strength="medium",
                    rationale="Capacitação da equipe permite melhorar execução dos processos internos críticos",
                )
            )

        # Process -> Customer
        customer_obj = perspectives_dict.get("Clientes")
        if process_obj and customer_obj and process_obj.objectives and customer_obj.objectives:
            connections.append(
                CauseEffectConnection(
                    source_objective_id=process_obj.objectives[0].name,
                    target_objective_id=customer_obj.objectives[0].name,
                    relationship_type="drives",
                    strength="strong",
                    rationale="Melhoria nos processos internos impulsiona diretamente satisfação e retenção de clientes",
                )
            )

        # Customer -> Financial
        financial_obj = perspectives_dict.get("Financeira")
        if customer_obj and financial_obj and customer_obj.objectives and financial_obj.objectives:
            connections.append(
                CauseEffectConnection(
                    source_objective_id=customer_obj.objectives[0].name,
                    target_objective_id=financial_obj.objectives[0].name,
                    relationship_type="drives",
                    strength="strong",
                    rationale="Maior satisfação e retenção de clientes impulsiona crescimento de receita e margem EBITDA",
                )
            )

        # Process -> Financial (conexão direta adicional)
        if process_obj and financial_obj and process_obj.objectives and financial_obj.objectives:
            connections.append(
                CauseEffectConnection(
                    source_objective_id=process_obj.objectives[0].name,
                    target_objective_id=financial_obj.objectives[0].name,
                    relationship_type="supports",
                    strength="medium",
                    rationale="Eficiência operacional suporta redução de custos e melhoria de margem EBITDA",
                )
            )

        logger.info(f"[StrategyMapDesigner] Conexões default criadas: {len(connections)}")
        return connections

    async def design_strategy_map(
        self,
        diagnostic: CompleteDiagnostic,
        client_profile: "ClientProfile",
        tools_results: DiagnosticToolsResult | None = None,
    ) -> StrategyMap:
        """
        Orquestração completa: diagnóstico -> Strategy Map estruturado.

        STEPS:
        1. Retrieve RAG knowledge (4 agents paralelos)
        2. Extract objectives por perspectiva (LLM structured + RAG)
        3. Map causa-efeito connections (LLM structured)
        4. Consolidate em StrategyMap validado

        Args:
            diagnostic: Diagnóstico BSC completo
            client_profile: Profile empresa (nome, setor, contexto)
            tools_results: Resultados ferramentas consultivas (opcional)

        Returns:
            StrategyMap completo e validado (schemas Pydantic).
        """
        logger.info("[StrategyMapDesigner] Iniciando design completo do Strategy Map")
        start_time = datetime.now(timezone.utc)

        try:
            # STEP 1: RAG retrieval (pattern Sprint 1)
            rag_context = await self._retrieve_bsc_knowledge(
                diagnostic, tools_results, client_profile
            )

            # STEP 2: Extract objectives por perspectiva (LLM + RAG)
            perspectives_dict = await self._extract_objectives_by_perspective(
                diagnostic, tools_results, rag_context
            )

            # STEP 3: Map causa-efeito connections (LLM structured)
            connections = await self._map_cause_effect_connections(perspectives_dict)

            # STEP 4: Consolidar em StrategyMap
            # Identificar strategic priorities (top 3 do diagnóstico)
            strategic_priorities = []
            if diagnostic.recommendations:
                top_3_recs = diagnostic.recommendations[:3]
                strategic_priorities = [rec.title[:80] for rec in top_3_recs]

            # Garantir mínimo 1, máximo 3
            if not strategic_priorities:
                strategic_priorities = ["Melhorar performance BSC geral"]
            elif len(strategic_priorities) > 3:
                strategic_priorities = strategic_priorities[:3]

            strategy_map = StrategyMap(
                financial=perspectives_dict["Financeira"],
                customer=perspectives_dict["Clientes"],
                process=perspectives_dict["Processos Internos"],
                learning=perspectives_dict["Aprendizado e Crescimento"],
                cause_effect_connections=connections,
                strategic_priorities=strategic_priorities,
                created_at=datetime.now(timezone.utc),
            )

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"[StrategyMapDesigner] Strategy Map completo: 4 perspectivas, "
                f"{len(connections)} conexões, {execution_time:.2f}s"
            )

            return strategy_map

        except Exception as e:
            logger.error(f"[StrategyMapDesigner] Erro ao design Strategy Map: {e}")
            raise


# ============================================================================
# FACTORY FUNCTION (convenienza para criar tool)
# ============================================================================


def create_strategy_map_designer_tool(
    financial_agent, customer_agent, process_agent, learning_agent, llm=None
) -> StrategyMapDesignerTool:
    """Factory function para criar Strategy Map Designer Tool."""
    return StrategyMapDesignerTool(
        financial_agent=financial_agent,
        customer_agent=customer_agent,
        process_agent=process_agent,
        learning_agent=learning_agent,
        llm=llm,
    )
