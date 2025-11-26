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
from typing import Any, Literal, Optional, cast

from api.middleware.performance import track_llm_tokens
from config.settings import get_llm_for_agent, settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.agents.customer_agent import CustomerAgent
from src.agents.financial_agent import FinancialAgent
from src.agents.learning_agent import LearningAgent
from src.agents.process_agent import ProcessAgent
from src.graph.states import BSCState
from src.memory.schemas import (
    ClientProfile,
    CompleteDiagnostic,
    ConsolidatedAnalysis,
    DiagnosticResult,
    DiagnosticToolsResult,
    KPIFramework,
    Recommendation,
)
from src.prompts.diagnostic_prompts import (
    ANALYZE_CUSTOMER_PERSPECTIVE_PROMPT,
    ANALYZE_FINANCIAL_PERSPECTIVE_PROMPT,
    ANALYZE_LEARNING_PERSPECTIVE_PROMPT,
    ANALYZE_PROCESS_PERSPECTIVE_PROMPT,
    CONSOLIDATE_DIAGNOSTIC_PROMPT,
    GENERATE_RECOMMENDATIONS_PROMPT,
    REFINE_DIAGNOSTIC_PROMPT,
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
        >>> diagnostic = await diagnostic_agent.run_diagnostic(state)
        >>> diagnostic.executive_summary
        'Empresa TechCorp apresenta sólido EBITDA mas...'
        >>> len(diagnostic.recommendations)
        7
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        """Inicializa DiagnosticAgent com LLM e agentes BSC.

        Args:
            llm: Modelo LLM customizado (opcional). Se None, usa configuração via .env.
        """
        # SESSAO 45: LLM análise (Claude Opus 4.5 - auto-correção, tarefas longas)
        # max_tokens alto para análises detalhadas, timeout de 2 minutos
        self.llm = llm or get_llm_for_agent(
            "analysis",
            max_tokens=settings.gpt5_max_completion_tokens,  # 128K tokens
            timeout=120,  # Timeout de 2 minutos
        )

        # Log para identificar temperatura do LLM
        if hasattr(self.llm, "temperature"):
            logger.info(f"[DIAGNOSTIC] LLM temperatura: {self.llm.temperature}")
        else:
            logger.warning("[DIAGNOSTIC] LLM não tem atributo 'temperature'")

        # Log para identificar modelo do LLM
        if hasattr(self.llm, "model"):
            logger.info(f"[DIAGNOSTIC] LLM modelo: {self.llm.model}")
        elif hasattr(self.llm, "model_name"):
            logger.info(f"[DIAGNOSTIC] LLM modelo: {self.llm.model_name}")
        else:
            logger.info("[DIAGNOSTIC] LLM tipo: %s", type(self.llm).__name__)

        logger.info(
            f"[DIAGNOSTIC] LLM configurado: model={settings.diagnostic_llm_model}, timeout=120s"
        )

        # Agentes BSC especializados (já existentes)
        self.financial_agent = FinancialAgent()
        self.customer_agent = CustomerAgent()
        self.process_agent = ProcessAgent()
        self.learning_agent = LearningAgent()

        logger.info(
            f"[DIAGNOSTIC v3.5] DiagnosticAgent __init__() completo - model={settings.diagnostic_llm_model}"
        )
        logger.info(
            f"[DIAGNOSTIC v3.5-20251022-11:45] DiagnosticAgent inicializado: "
            f"model={settings.diagnostic_llm_model}, max_completion_tokens={settings.gpt5_max_completion_tokens} | "
            f"CORREÇÃO: Logs salvando em arquivo .log (print -> logger.info)"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, ValueError, AttributeError)),
        reraise=True,
    )
    async def _call_llm_perspective(
        self,
        perspective: Literal[
            "Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"
        ],
        client_profile: ClientProfile,
        state: BSCState,
    ) -> DiagnosticResult:
        """Chama o LLM para gerar o DiagnosticResult de uma perspectiva (com retry e timeout)."""
        logger.info(
            f"[DIAGNOSTIC v3.0 LOG] [{perspective}] >>>>> ENTROU em _call_llm_perspective() <<<<<"
        )
        logger.info(
            f"[DIAGNOSTIC v3.0] [{perspective}] >>>>> ENTROU em _call_llm_perspective() <<<<<"
        )

        # Selecionar prompt
        prompt_map = {
            "Financeira": ANALYZE_FINANCIAL_PERSPECTIVE_PROMPT,
            "Clientes": ANALYZE_CUSTOMER_PERSPECTIVE_PROMPT,
            "Processos Internos": ANALYZE_PROCESS_PERSPECTIVE_PROMPT,
            "Aprendizado e Crescimento": ANALYZE_LEARNING_PERSPECTIVE_PROMPT,
        }
        if perspective not in prompt_map:
            raise ValueError(f"Perspectiva inválida: {perspective}")
        prompt_template = prompt_map[perspective]

        company = client_profile.company
        context = client_profile.context
        challenges_text = (
            ", ".join(context.current_challenges)
            if context.current_challenges
            else "Não informados"
        )
        objectives_text = (
            ", ".join(context.strategic_objectives)
            if context.strategic_objectives
            else "Não informados"
        )

        perspective_map: dict[str, str] = cast(
            dict[str, str], state.metadata.get("perspective_context", {}) or {}
        )
        client_context_str: str = perspective_map.get(perspective, "Contexto BSC não disponível.")
        formatted_prompt = prompt_template.format(
            client_context=client_context_str,
            company_name=company.name,
            sector=company.sector,
            size=company.size,
            challenges=challenges_text,
            objectives=objectives_text,
        )

        logger.info(
            f"[DIAGNOSTIC v3.0 LOG] [{perspective}] Criando structured_llm com method=function_calling..."
        )

        # LOG SCHEMA PARA DEBUG
        try:
            schema_dict = DiagnosticResult.model_json_schema()
            logger.debug(
                f"[DIAGNOSTIC] [{perspective}] Schema Pydantic gerado (primeiros 500 chars): {str(schema_dict)[:500]}..."
            )
        except Exception as schema_err:
            logger.warning(f"[DIAGNOSTIC] [{perspective}] Erro ao gerar schema: {schema_err}")

        structured_llm: Any = self.llm.with_structured_output(
            DiagnosticResult,
            method="function_calling",  # CRITICAL: force function_calling method (LangChain 0.3.0+ compatibility)
        )

        logger.info(
            f"[DIAGNOSTIC v3.0 LOG] [{perspective}] Structured LLM criado! Type: {type(structured_llm)}"
        )

        messages = [
            SystemMessage(
                content="Você é um especialista em Balanced Scorecard conduzindo análise diagnóstica."
            ),
            HumanMessage(content=formatted_prompt),
        ]

        # Timeout por perspectiva (evita travas)
        # Log da raw response para debug (verificar se LLM está gerando algo)
        logger.info(
            f"[DIAGNOSTIC v3.0 LOG] [{perspective}] Iniciando try/except para chamadas LLM..."
        )
        try:
            logger.info(
                f"[DIAGNOSTIC] [{perspective}] STEP 2/2: Chamando LLM structured output (GPT-5)..."
            )

            logger.info(f"[DIAGNOSTIC v3.0 LOG] [{perspective}] PASSO 1: Testando raw LLM...")
            # PASSO 1: Testar raw LLM primeiro (sem structured)
            logger.debug(
                f"[DIAGNOSTIC] [{perspective}] PASSO 1: Testando raw LLM (sem structured)..."
            )
            raw_test = await asyncio.wait_for(self.llm.ainvoke(messages), timeout=120)
            logger.info(
                f"[DIAGNOSTIC] [{perspective}] Raw LLM OK: type={type(raw_test).__name__}, has_content={hasattr(raw_test, 'content')}"
            )

            # CRITICO: Verificar response_metadata para MALFORMED_FUNCTION_CALL
            if hasattr(raw_test, "response_metadata"):
                metadata = raw_test.response_metadata
                finish_reason = metadata.get("finish_reason", "N/A")
                finish_message = metadata.get("finish_message", "")
                logger.info(
                    f"[DIAGNOSTIC v3.0 LOG] [{perspective}] Raw finish_reason: {finish_reason}"
                )
                logger.warning(
                    f"[DIAGNOSTIC] [{perspective}] Response metadata: finish_reason={finish_reason}, finish_message={finish_message[:100]}"
                )
                logger.info(
                    f"[CHECKPOINT v3.5] [{perspective}] APÓS log finish_reason - continuando..."
                )

                # FASE 4.9: Instrumentar LLM tokens para performance monitoring
                token_usage = metadata.get("token_usage", {})
                if token_usage:
                    model_name = metadata.get("model_name", settings.diagnostic_llm_model)
                    tokens_in = token_usage.get("prompt_tokens", 0)
                    tokens_out = token_usage.get("completion_tokens", 0)
                    track_llm_tokens(tokens_in, tokens_out, model_name)
                    logger.debug(
                        f"[PERFORMANCE] [{perspective}] Tokens capturados: {model_name} in={tokens_in} out={tokens_out}"
                    )

                if finish_reason == "MALFORMED_FUNCTION_CALL":
                    logger.error(
                        f"[DIAGNOSTIC] [{perspective}] CRITICO: MALFORMED_FUNCTION_CALL detectado! Message: {finish_message}"
                    )
                    logger.info(
                        f"[DIAGNOSTIC v3.0 LOG] [{perspective}] ERRO: MALFORMED_FUNCTION_CALL - {finish_message}"
                    )

            if hasattr(raw_test, "content"):
                content_str = str(raw_test.content) if raw_test.content else "[VAZIO]"
                logger.info(
                    f"[DIAGNOSTIC] [{perspective}] Raw content (primeiros 300 chars): {content_str[:300]}..."
                )
                logger.debug(
                    f"[DIAGNOSTIC] [{perspective}] Raw content length: {len(content_str)} chars"
                )

            logger.info(
                f"[DIAGNOSTIC v3.0 LOG] [{perspective}] PASSO 2: Testando structured output..."
            )
            logger.info(
                f"[CHECKPOINT v3.5] [{perspective}] ANTES de structured_llm.ainvoke() - timeout=120s..."
            )
            # PASSO 2: Testar structured output
            logger.debug(
                f"[DIAGNOSTIC] [{perspective}] PASSO 2: Chamando structured_llm.ainvoke() (method=function_calling)..."
            )
            result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=120)  # type: ignore[attr-defined]
            logger.info(
                f"[CHECKPOINT v3.5] [{perspective}] DEPOIS de structured_llm.ainvoke() - result type: {type(result).__name__ if result else 'NoneType'}"
            )

            logger.info(
                f"[DIAGNOSTIC v3.0 LOG] [{perspective}] Result type: {type(result).__name__ if result else 'NoneType'}"
            )
            logger.info(
                f"[DIAGNOSTIC] [{perspective}] Structured retornou: type={type(result).__name__ if result else 'NoneType'}, is_None={result is None}"
            )

            if result is not None:
                logger.debug(
                    f"[DIAGNOSTIC] [{perspective}] Structured object attrs: {dir(result)[:10]}..."
                )
                if hasattr(result, "perspective"):
                    logger.info(
                        f"[DIAGNOSTIC] [{perspective}] Structured SUCESSO: perspective={result.perspective}, priority={getattr(result, 'priority', 'N/A')}"
                    )

        except asyncio.TimeoutError as e:
            logger.error(f"[DIAGNOSTIC] [{perspective}] Timeout do LLM na análise da perspectiva")
            raise ValueError("Timeout LLM analyze_perspective") from e
        except Exception:
            logger.exception(f"[DIAGNOSTIC] [{perspective}] Erro inesperado na chamada LLM")
            raise

        if result is None:
            logger.warning(
                f"[DIAGNOSTIC] [{perspective}] Structured LLM retornou None. Tentando fallback com prompt JSON estrito..."
            )
            strict_instructions = (
                "Você DEVE responder estritamente em JSON compatível com o schema DiagnosticResult: "
                '{ "perspective": one of ["Financeira","Clientes","Processos Internos","Aprendizado e Crescimento"], '
                '"current_state": string (>=20 chars), "gaps": ["string"], "opportunities": ["string"], '
                '"priority": one of ["HIGH","MEDIUM","LOW"], "key_insights": ["string"] }.'
            )
            strict_messages = [
                SystemMessage(content=strict_instructions),
                HumanMessage(
                    content=formatted_prompt
                    + "\n\nIMPORTANTE: Responda APENAS com JSON válido, sem texto extra."
                ),
            ]
            try:
                # 1) Tentar novamente via structured output com instruções estritas
                result = await asyncio.wait_for(structured_llm.ainvoke(strict_messages), timeout=120)  # type: ignore[attr-defined]
            except asyncio.TimeoutError as e:
                logger.error(
                    f"[DIAGNOSTIC] [{perspective}] Timeout também no fallback JSON estrito"
                )
                raise ValueError("Timeout LLM analyze_perspective (fallback)") from e
            if result is None:
                logger.warning(
                    f"[DIAGNOSTIC] [{perspective}] Structured ainda None. Tentando fallback via JSON plano + parse..."
                )
                # 2) Fallback final: pedir JSON plano e parsear manualmente
                raw_messages = [
                    SystemMessage(content=strict_instructions),
                    HumanMessage(
                        content=formatted_prompt + "\n\nApenas JSON válido, sem texto extra."
                    ),
                ]
                try:
                    raw_response = await asyncio.wait_for(
                        self.llm.ainvoke(raw_messages), timeout=120
                    )
                    data = json.loads(str(getattr(raw_response, "content", "")).strip())  # type: ignore
                    candidate = DiagnosticResult.model_validate(data)
                    # Checagem rápida de campos críticos
                    if (
                        not candidate.gaps
                        or not candidate.opportunities
                        or candidate.priority is None
                    ):
                        raise ValueError("Campos críticos ausentes no JSON plano")
                    return candidate
                except Exception as parse_err:
                    logger.error(
                        f"[DIAGNOSTIC] [{perspective}] Fallback JSON plano falhou: {parse_err}"
                    )
                    # 3) Default seguro para não travar fluxo
                    return DiagnosticResult(
                        perspective=perspective,
                        current_state="Análise indisponível no momento. Estado atual não pôde ser obtido do LLM.",
                        gaps=["Falta de dados estruturados para esta perspectiva"],
                        opportunities=[
                            "Reexecutar análise desta perspectiva ou fornecer mais contexto"
                        ],
                        priority="MEDIUM",
                        key_insights=[],
                    )

        if (
            getattr(result, "priority", None) is None
            or getattr(result, "gaps", None) is None
            or getattr(result, "opportunities", None) is None
        ):
            logger.error(
                f"[DIAGNOSTIC] [{perspective}] Campos críticos ausentes no resultado (priority/gaps/opportunities). Requisitando retry."
            )
            raise ValueError("DiagnosticResult incompleto (priority/gaps/opportunities ausentes)")

        return result

    async def analyze_perspective(
        self,
        perspective: Literal[
            "Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"
        ],
        client_profile: ClientProfile,
        state: BSCState,
    ) -> DiagnosticResult:
        """Analisa uma perspectiva BSC: faz retrieval uma vez e chama LLM com retry isolado."""
        logger.info(
            f"[DIAGNOSTIC v3.1 LOG] [{perspective}] >>>>> analyze_perspective() CHAMADO <<<<<"
        )
        logger.info(f"[DIAGNOSTIC v3.1] [{perspective}] ===== INICIANDO analyze_perspective =====")
        logger.info(f"[DIAGNOSTIC v3.1] [{perspective}] Analisando perspectiva: {perspective}")

        # 1) Retrieval de contexto via agente especialista (sem retry)
        agent_map = {
            "Financeira": self.financial_agent,
            "Clientes": self.customer_agent,
            "Processos Internos": self.process_agent,
            "Aprendizado e Crescimento": self.learning_agent,
        }
        specialist_agent = agent_map[perspective]
        query = f"Quais são os principais conceitos e KPIs da perspectiva {perspective} no BSC segundo Kaplan & Norton?"
        try:
            logger.info(
                f"[DIAGNOSTIC v3.1 LOG] [{perspective}] ANTES de await specialist_agent.ainvoke()"
            )
            logger.info(
                f"[DIAGNOSTIC v3.1] [{perspective}] STEP 1/2: Buscando contexto BSC via specialist agent..."
            )

            context_response = await specialist_agent.ainvoke(query)

            logger.info(
                f"[DIAGNOSTIC v3.1 LOG] [{perspective}] DEPOIS de await specialist_agent.ainvoke() - type={type(context_response).__name__}"
            )
            logger.info(
                f"[DIAGNOSTIC v3.1] [{perspective}] STEP 1/2: Contexto BSC obtido - type={type(context_response)}"
            )
            logger.info(
                f"[DIAGNOSTIC v3.1] [{perspective}] context_response keys: {context_response.keys() if isinstance(context_response, dict) else 'not_dict'}"
            )

            client_context = context_response.get("answer", "Contexto BSC não disponível.")
            logger.info(
                f"[DIAGNOSTIC v3.1 LOG] [{perspective}] client_context extraído ({len(client_context)} chars)"
            )
        except Exception as e:
            logger.info(
                f"[DIAGNOSTIC v3.1 LOG] [{perspective}] EXCEÇÃO em retrieval: {type(e).__name__}: {e}"
            )
            logger.warning(f"[DIAGNOSTIC] Erro ao buscar contexto BSC: {e}")
            client_context = "Contexto BSC não disponível. Análise baseada em princípios gerais."

        # 2) Salvar contexto em metadata para o método de LLM
        if not hasattr(state, "metadata") or state.metadata is None:
            state.metadata = {}
        perspective_ctx = state.metadata.get("perspective_context", {})
        perspective_ctx[perspective] = client_context
        state.metadata["perspective_context"] = perspective_ctx

        # 3) Chamada LLM com retry/timeout isolados
        logger.info(f"[DIAGNOSTIC v3.0] [{perspective}] ===== CHAMANDO _call_llm_perspective =====")
        result = await self._call_llm_perspective(perspective, client_profile, state)
        logger.info(
            f"[DIAGNOSTIC v3.0] [{perspective}] ===== RETORNOU de _call_llm_perspective ====="
        )

        logger.info(
            f"[DIAGNOSTIC] Perspectiva {perspective} analisada: priority={result.priority}, gaps={len(result.gaps)}, opportunities={len(result.opportunities)}"
        )
        logger.info(
            f"[CHECKPOINT v3.5] [{perspective}] PRONTO para retornar analyze_perspective() - result válido"
        )
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
        # TIMING DETALHADO - SESSAO 43 (2025-11-24)
        import time

        parallel_start = time.time()

        logger.info("[TIMING] [DIAGNOSTIC] >>>>> run_parallel_analysis() INICIADO <<<<<")
        logger.info("[TIMING] [DIAGNOSTIC] Criando 4 tasks assincronas para asyncio.gather()...")

        # Criar tasks para execução paralela (ASYNC coroutines, não threads)
        tasks = {
            "Financeira": self.analyze_perspective(
                "Financeira",
                client_profile,
                state,
            ),
            "Clientes": self.analyze_perspective(
                "Clientes",
                client_profile,
                state,
            ),
            "Processos Internos": self.analyze_perspective(
                "Processos Internos",
                client_profile,
                state,
            ),
            "Aprendizado e Crescimento": self.analyze_perspective(
                "Aprendizado e Crescimento",
                client_profile,
                state,
            ),
        }

        tasks_created_elapsed = time.time() - parallel_start
        logger.info(f"[TIMING] [DIAGNOSTIC] Tasks criadas em {tasks_created_elapsed:.2f}s")

        # Executar em paralelo via event loop (não threads, sem GIL)
        logger.info("[TIMING] [DIAGNOSTIC] Executando asyncio.gather() com 4 tasks...")
        gather_start = time.time()

        try:
            results_list = await asyncio.gather(*tasks.values())
            gather_elapsed = time.time() - gather_start
            total_elapsed = time.time() - parallel_start
            logger.info(
                f"[TIMING] [DIAGNOSTIC] asyncio.gather() CONCLUIDO em {gather_elapsed:.2f}s | "
                f"Total run_parallel: {total_elapsed:.2f}s | "
                f"results_list len={len(results_list)}"
            )
        except Exception as gather_err:
            logger.error(f"[DIAGNOSTIC] ERRO em asyncio.gather(): {gather_err}", exc_info=True)
            raise

        # Mapear resultados de volta às perspectivas
        try:
            perspectives = list(tasks.keys())
            logger.debug(
                f"[DIAGNOSTIC] Mapeando {len(results_list)} results para {len(perspectives)} perspectivas"
            )
            results = {perspectives[i]: results_list[i] for i in range(4)}
            logger.info(f"[DIAGNOSTIC] Mapping completo - keys: {list(results.keys())}")
        except Exception as map_err:
            logger.error(f"[DIAGNOSTIC] ERRO ao mapear results: {map_err}", exc_info=True)
            raise

        # Logs defensivos: validar que priority existe em todos
        try:
            priorities_snapshot = {
                name: getattr(res, "priority", None) for name, res in results.items()
            }
            logger.debug(f"[DIAGNOSTIC] Priorities snapshot pós-gather: {priorities_snapshot}")
            missing = [k for k, v in priorities_snapshot.items() if v is None]
            if missing:
                logger.warning(
                    f"[DIAGNOSTIC] Resultados sem priority detectados: {missing}. Conteúdos parciais podem causar erros adiante."
                )
        except Exception as snap_err:
            logger.warning(f"[DIAGNOSTIC] Falha ao inspecionar prioridades: {snap_err}")

        logger.info("[DIAGNOSTIC] Análise paralela concluída: 4 perspectivas processadas")
        logger.info(
            f"[CHECKPOINT v3.7] >>>>> run_parallel_analysis() RETORNANDO results com {len(results)} keys <<<<<"
        )

        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, ValueError)),
        reraise=True,
    )
    async def consolidate_diagnostic(
        self,
        perspective_results: dict[str, DiagnosticResult],
        tools_results: DiagnosticToolsResult | None = None,  # SPRINT 1 (GAP #2): Novo parâmetro!
    ) -> dict[str, Any]:
        """
        Consolida análises das 4 perspectivas identificando synergies cross-perspective.

        SPRINT 1 (GAP #2): Modificado para aceitar tools_results e enriquecer prompt
        com outputs das 7 ferramentas consultivas.

        Args:
            perspective_results: Mapa {perspective: DiagnosticResult} das 4 análises
            tools_results: Outputs das 7 ferramentas consultivas (opcional, SPRINT 1)

        Returns:
            dict: {
                "cross_perspective_synergies": list[str],
                "executive_summary": str,
                "next_phase": str
            }

        Example:
            >>> consolidated = agent.consolidate_diagnostic(results, tools_results)
            >>> len(consolidated["cross_perspective_synergies"])
            4
            >>> "Processos manuais" in consolidated["cross_perspective_synergies"][0]
            True
        """
        logger.info(
            "[DIAGNOSTIC] [SPRINT 1] Consolidando análises cross-perspective (enriquecido com ferramentas)..."
        )

        # Fallback offline: se todos resultados são defaults (sem análise), pular LLM
        try:
            all_defaults = all(
                isinstance(r.current_state, str)
                and "Análise indisponível no momento" in r.current_state
                for r in perspective_results.values()
            )
        except Exception:
            all_defaults = False
        if all_defaults:
            logger.warning(
                "[DIAGNOSTIC] Todos os resultados vieram em fallback default. Pulando LLM de consolidação (offline)."
            )
            return {
                "cross_perspective_synergies": [],
                "executive_summary": (
                    "Diagnóstico indisponível: as análises por perspectiva não puderam ser geradas agora. "
                    "Recomenda-se reexecutar a DISCOVERY com mais contexto ou em nova sessão."
                ),
                "next_phase": "APPROVAL_PENDING",
            }

        # Preparar resumo das 4 análises para o prompt
        analyses_text = ""
        for perspective, result in perspective_results.items():
            prio = getattr(result, "priority", None)
            if prio is None:
                logger.warning(
                    f"[DIAGNOSTIC] Consolidation: priority ausente em '{perspective}'. Usando 'MEDIUM' como fallback."
                )
                prio = "MEDIUM"
            state_text = getattr(result, "current_state", "(sem current_state)")
            gaps_list = getattr(result, "gaps", []) or []
            opps_list = getattr(result, "opportunities", []) or []
            analyses_text += f"\n\n{perspective} (Priority: {prio}):\n"
            analyses_text += f"Current State: {state_text}\n"
            analyses_text += f"Gaps: {', '.join(gaps_list)}\n"
            analyses_text += f"Opportunities: {', '.join(opps_list)}\n"

        # SPRINT 1 (GAP #2): Formatar resultados das ferramentas consultivas (se disponíveis)
        tools_context = ""
        if tools_results:
            tools_context = self._format_tools_results(tools_results)
            logger.info(
                f"[DIAGNOSTIC] [SPRINT 1] Ferramentas consultivas incluídas no prompt: {len(tools_results.tools_executed)} ferramentas"
            )

        # Formatar prompt de consolidação (enriquecido com ferramentas)
        formatted_prompt = CONSOLIDATE_DIAGNOSTIC_PROMPT.format(perspective_analyses=analyses_text)

        # SPRINT 1: Adicionar seção de ferramentas consultivas ao prompt
        if tools_context:
            formatted_prompt += f"\n\n# ANÁLISES CONSULTIVAS COMPLEMENTARES\n\n{tools_context}\n\n"
            formatted_prompt += (
                "# INSTRUÇÕES ADICIONAIS\n\n"
                "Use os insights das análises consultivas acima para:\n"
                "- Enriquecer o executive summary com dados específicos (SWOT, Five Whys, KPIs)\n"
                "- Priorizar recomendações baseadas na Prioritization Matrix\n"
                "- Identificar root causes usando Five Whys\n"
                "- Mencionar KPIs sugeridos quando relevante\n"
            )

        # [CORREÇÃO Oct/2025] Usar with_structured_output() ao invés de json.loads()
        # PROBLEMA: LLM.ainvoke() sem structured output retorna content='' vazio quando usa function calling
        # SOLUÇÃO: Usar with_structured_output(ConsolidatedAnalysis, method="function_calling")
        # ConsolidatedAnalysis importado no topo do arquivo (linha 36)

        messages = [
            SystemMessage(content="Você é um consultor BSC sênior com visão sistêmica."),
            HumanMessage(content=formatted_prompt),
        ]

        logger.info("[DIAGNOSTIC v3.2 LOG] Criando structured_llm com ConsolidatedAnalysis...")

        # Criar structured LLM com schema Pydantic
        structured_llm = self.llm.with_structured_output(
            ConsolidatedAnalysis,
            method="function_calling",  # Usar OpenAI function calling (mais preciso)
            include_raw=False,
        )

        logger.info("[DIAGNOSTIC v3.2 LOG] structured_llm criado! Chamando com timeout 150s...")
        logger.info(
            "[DIAGNOSTIC v3.2] Chamando LLM estruturado para consolidação (timeout=150s)..."
        )

        try:
            # PASSO 1: Testar raw LLM primeiro (debug)
            logger.info("[DIAGNOSTIC v3.2 LOG] PASSO 1: Testando raw LLM...")
            raw_test = await asyncio.wait_for(self.llm.ainvoke(messages), timeout=150)

            # Verificar response_metadata
            if hasattr(raw_test, "response_metadata"):
                metadata = raw_test.response_metadata
                finish_reason = metadata.get("finish_reason", "N/A")

                # [DIAGNOSTICO TOKEN USAGE] Extrair estatísticas de tokens
                token_usage = metadata.get("token_usage", {})
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = token_usage.get("total_tokens", 0)

                logger.info(f"[DIAGNOSTIC v3.2 LOG] Raw finish_reason: {finish_reason}")
                logger.info(
                    f"[DIAGNOSTIC v3.2 LOG] TOKEN USAGE: input={prompt_tokens}, output={completion_tokens}, total={total_tokens}"
                )
                logger.info(
                    f"[DIAGNOSTIC v3.2 LOG] MAX ALLOWED: max_completion_tokens={settings.gpt5_max_completion_tokens}"
                )

                # FASE 4.9: Instrumentar LLM tokens para performance monitoring
                if token_usage:
                    model_name = metadata.get("model_name", settings.diagnostic_llm_model)
                    track_llm_tokens(prompt_tokens, completion_tokens, model_name)
                    logger.debug(
                        f"[PERFORMANCE] [CONSOLIDATION] Tokens capturados: {model_name} in={prompt_tokens} out={completion_tokens}"
                    )

                logger.info(f"[DIAGNOSTIC v3.2] Raw LLM finish_reason: {finish_reason}")
                logger.info(
                    f"[DIAGNOSTIC v3.2] TOKEN USAGE: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}"
                )
                logger.info(
                    f"[DIAGNOSTIC v3.2] MAX CONFIG: max_completion_tokens={settings.gpt5_max_completion_tokens}"
                )

                # Calcular % utilizado
                if completion_tokens > 0 and settings.gpt5_max_completion_tokens > 0:
                    usage_percent = (completion_tokens / settings.gpt5_max_completion_tokens) * 100
                    logger.info(
                        f"[DIAGNOSTIC v3.2 LOG] OUTPUT TOKEN USAGE: {usage_percent:.1f}% do limite ({completion_tokens}/{settings.gpt5_max_completion_tokens})"
                    )
                    logger.info(
                        f"[DIAGNOSTIC v3.2] OUTPUT TOKEN USAGE: {usage_percent:.1f}% do limite"
                    )

                if finish_reason == "length":
                    logger.error(
                        f"[DIAGNOSTIC v3.2] ERRO: finish_reason=length! LLM truncado. Tokens usados: {completion_tokens}/{settings.gpt5_max_completion_tokens}"
                    )
                    raise ValueError(
                        f"LLM response truncada: finish_reason={finish_reason}, tokens={completion_tokens}/{settings.gpt5_max_completion_tokens}"
                    )
                if finish_reason == "MALFORMED_FUNCTION_CALL":
                    logger.error(
                        "[DIAGNOSTIC v3.2] ERRO: MALFORMED_FUNCTION_CALL! Schema muito complexo."
                    )
                    raise ValueError(
                        f"Schema Pydantic muito complexo: {metadata.get('finish_message')}"
                    )

            # PASSO 2: Chamar structured output
            logger.info("[DIAGNOSTIC v3.2 LOG] PASSO 2: Chamando structured output...")
            result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=150)

            logger.info(
                f"[DIAGNOSTIC v3.2 LOG] Result type: {type(result).__name__ if result else 'NoneType'}"
            )
            logger.info(
                f"[DIAGNOSTIC v3.2] Structured output retornou: type={type(result).__name__ if result else 'NoneType'}"
            )

            if result is None:
                logger.error("[DIAGNOSTIC v3.2] ERRO: Structured output retornou None!")
                raise ValueError("Structured output retornou None - verificar finish_reason acima")

            # Converter Pydantic para dict (compatibilidade backwards)
            consolidated = result.model_dump()
            logger.info(
                f"[DIAGNOSTIC v3.2] Consolidação SUCESSO: {len(consolidated['cross_perspective_synergies'])} synergies"
            )

        except asyncio.TimeoutError as e:
            logger.error("[DIAGNOSTIC v3.2] Timeout na consolidação do diagnóstico")
            raise ValueError("Timeout consolidating diagnostic (LLM)") from e
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                logger.error(
                    "[DIAGNOSTIC v3.2] Executor fechado durante consolidação. Usando fallback offline."
                )
                return {
                    "cross_perspective_synergies": [],
                    "executive_summary": (
                        "Consolidação indisponível no momento devido a recurso de execução encerrado. "
                        "Reexecute a DISCOVERY ou tente novamente."
                    ),
                    "next_phase": "APPROVAL_PENDING",
                }
            raise

        # Validação automática via Pydantic (já garantida pelo with_structured_output)
        # Campos obrigatórios: cross_perspective_synergies (min_items=2), executive_summary (min_length=200), next_phase
        logger.info(
            f"[DIAGNOSTIC v3.2 LOG] Consolidação concluída! {len(consolidated['cross_perspective_synergies'])} synergies"
        )
        logger.info(
            f"[DIAGNOSTIC v3.2] Consolidação concluída: {len(consolidated['cross_perspective_synergies'])} synergies, "
            f"next_phase={consolidated['next_phase']}"
        )

        return consolidated

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, ValueError)),
        reraise=True,
    )
    async def generate_recommendations(
        self,
        perspective_results: dict[str, DiagnosticResult],
        consolidated: dict[str, Any],
    ) -> list[Recommendation]:
        """Gera recomendações priorizadas baseadas no diagnóstico completo.

        Args:
            perspective_results: Resultados das 4 perspectivas
            consolidated: Consolidação cross-perspective

        Returns:
            list[Recommendation]: 5-10 recomendações priorizadas (HIGH -> MEDIUM -> LOW)

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

        # Fallback offline: se consolidação é minimal/offline ou se todos resultados são defaults, pular LLM
        try:
            all_defaults = all(
                isinstance(r.current_state, str)
                and "Análise indisponível no momento" in r.current_state
                for r in perspective_results.values()
            )
        except Exception:
            all_defaults = False
        if all_defaults:
            logger.warning(
                "[DIAGNOSTIC] Resultados default detectados. Pulando geração de recomendações (offline=sem recomendações)."
            )
            return []

        # Preparar dados completos do diagnóstico para o prompt
        diagnostic_summary = f"""
EXECUTIVE SUMMARY:
{consolidated['executive_summary']}

CROSS-PERSPECTIVE SYNERGIES:
{chr(10).join(f"- {s}" for s in consolidated['cross_perspective_synergies'])}

ANÁLISES POR PERSPECTIVA:
"""

        for perspective, result in perspective_results.items():
            prio = getattr(result, "priority", None) or "MEDIUM"
            gaps_list = getattr(result, "gaps", []) or []
            opps_list = getattr(result, "opportunities", []) or []
            diagnostic_summary += f"\n{perspective} (Priority: {prio}):\n"
            diagnostic_summary += f"Gaps: {', '.join(gaps_list)}\n"
            diagnostic_summary += f"Opportunities: {', '.join(opps_list)}\n"

        # Formatar prompt de recomendações
        formatted_prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(
            complete_diagnostic=diagnostic_summary
        )

        # Chamar LLM com structured output (lista de Recommendations)
        messages = [
            SystemMessage(
                content="Você é um consultor BSC especialista em transformação organizacional."
            ),
            HumanMessage(content=formatted_prompt),
        ]

        logger.info(
            "[CHECKPOINT v3.7] Iniciando generate_recommendations LLM call com structured output..."
        )
        logger.debug(
            "[DIAGNOSTIC] Chamando LLM para gerar recomendações (with_structured_output)..."
        )
        try:
            # PASSO 1: Testar raw LLM primeiro (diagnóstico)
            logger.info("[CHECKPOINT v3.7] ANTES de raw LLM test (recomendações)...")
            raw_test = await asyncio.wait_for(self.llm.ainvoke(messages), timeout=300)
            logger.info("[CHECKPOINT v3.7] DEPOIS de raw LLM test (recomendações)")

            # Verificar response_metadata
            if hasattr(raw_test, "response_metadata"):
                metadata = raw_test.response_metadata
                finish_reason = metadata.get("finish_reason", "N/A")
                token_usage = metadata.get("token_usage", {})
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = token_usage.get("total_tokens", 0)

                logger.info(f"[CHECKPOINT v3.7] finish_reason: {finish_reason}")
                logger.info(
                    f"[CHECKPOINT v3.7] TOKEN USAGE: input={prompt_tokens}, output={completion_tokens}, total={total_tokens}"
                )
                logger.info("[CHECKPOINT v3.7] MAX ALLOWED: max_completion_tokens=64000")
                logger.info(
                    f"[CHECKPOINT v3.7] OUTPUT TOKEN USAGE: {(completion_tokens/64000)*100:.1f}% do limite ({completion_tokens}/64000)"
                )

                # FASE 4.9: Instrumentar LLM tokens para performance monitoring
                if token_usage:
                    model_name = metadata.get("model_name", settings.diagnostic_llm_model)
                    track_llm_tokens(prompt_tokens, completion_tokens, model_name)
                    logger.debug(
                        f"[PERFORMANCE] [RECOMMENDATIONS] Tokens capturados: {model_name} in={prompt_tokens} out={completion_tokens}"
                    )

                if finish_reason == "length":
                    logger.error(
                        "[DIAGNOSTIC] ERRO: finish_reason=length! LLM truncado ao gerar recomendações."
                    )
                    raise ValueError(f"LLM response truncada: finish_reason={finish_reason}")

            # PASSO 2: Usar with_structured_output para garantir schema Pydantic
            logger.info("[CHECKPOINT v3.7] ANTES de structured output call...")
            from src.memory.schemas import RecommendationsList

            structured_llm = self.llm.with_structured_output(
                RecommendationsList,
                method="function_calling",  # CRÍTICO: forçar function calling (garante campo 'impact')
            )

            try:
                result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=300)
            except Exception as fc_err:
                logger.warning(
                    f"[DIAGNOSTIC] function_calling falhou ({type(fc_err).__name__}: {fc_err}). Tentando json_mode..."
                )
                structured_llm = self.llm.with_structured_output(
                    RecommendationsList, method="json_mode"
                )
                result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=240)
            logger.info("[CHECKPOINT v3.7] DEPOIS de structured output call")

            if result is None:
                logger.error("[DIAGNOSTIC] ERRO: with_structured_output retornou None!")
                raise ValueError("LLM structured output retornou None - verificar schema Pydantic")

            recommendations = result.recommendations  # Lista de Recommendation já validada!
            logger.info(
                f"[CHECKPOINT v3.7] Structured output retornou {len(recommendations)} recomendações válidas"
            )

        except asyncio.TimeoutError as e:
            logger.error("[DIAGNOSTIC] Timeout ao gerar recomendações (300s)")
            # Converter para ValueError para acionar retry do tenacity
            raise ValueError("Timeout generating recommendations (LLM)") from e

        logger.debug(
            f"[DIAGNOSTIC] LLM retornou {len(recommendations)} recomendações (schema Pydantic garantido via function calling)"
        )

        # Logar snapshot de prioridades antes de ordenar
        try:
            rec_priorities = [getattr(r, "priority", None) for r in recommendations]
            logger.debug(
                f"[DIAGNOSTIC] Prioridades das recomendações (pré-ordenação): {rec_priorities}"
            )
        except Exception:
            pass

        # Ordenar por prioridade: HIGH -> MEDIUM -> LOW (com fallback defensivo)
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

        def _safe_priority(rec: Recommendation) -> int:
            pr = getattr(rec, "priority", None) or "MEDIUM"
            return priority_order.get(pr, 1)

        recommendations.sort(key=_safe_priority)

        logger.info(
            f"[DIAGNOSTIC] {len(recommendations)} recomendações geradas: "
            f"HIGH={sum(1 for r in recommendations if r.priority == 'HIGH')}, "
            f"MEDIUM={sum(1 for r in recommendations if r.priority == 'MEDIUM')}, "
            f"LOW={sum(1 for r in recommendations if r.priority == 'LOW')}"
        )

        return recommendations

    async def _run_diagnostic_inner(self, state: BSCState) -> CompleteDiagnostic:
        """Implementação interna do diagnóstico (sem timeout externo)."""
        logger.info("[DIAGNOSTIC v3.1 LOG] >>>>> _run_diagnostic_inner() CHAMADO <<<<<")
        # Log ÚNICO para confirmar versão nova do código (detectar cache antigo)
        logger.info(
            "[DIAGNOSTIC v3.1-20251021-19:10] _run_diagnostic_inner() VERSAO NOVA EXECUTANDO!"
        )
        logger.debug("[DEBUG] [DIAGNOSTIC] run_diagnostic() FOI CHAMADO! Iniciando diagnóstico...")
        logger.info("[DIAGNOSTIC v3.1] ========== INICIANDO DIAGNÓSTICO BSC COMPLETO ==========")

        # Validação: client_profile obrigatório
        logger.info(
            f"[DIAGNOSTIC v3.1 LOG] Validando client_profile... exists={state.client_profile is not None}"
        )
        if not state.client_profile:
            raise ValueError("client_profile ausente no state. Execute onboarding primeiro.")
        logger.info("[DIAGNOSTIC v3.1 LOG] client_profile existe! Validação OK")

        # Converter dict para ClientProfile Pydantic se necessário (RECURSIVO para nested dicts)
        client_profile_raw = state.client_profile
        if isinstance(client_profile_raw, dict):
            logger.debug(
                "[DIAGNOSTIC] Convertendo client_profile de dict para ClientProfile Pydantic"
            )
            from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

            # CRITICAL: Converter nested dicts ANTES de criar ClientProfile
            # Pydantic V2 com extra='allow' não converte nested automaticamente

            # Converter context se é dict
            if "context" in client_profile_raw and isinstance(client_profile_raw["context"], dict):
                logger.debug(
                    "[DIAGNOSTIC] Convertendo nested context de dict para StrategicContext"
                )
                client_profile_raw["context"] = StrategicContext(**client_profile_raw["context"])

            # Converter company se é dict
            if "company" in client_profile_raw and isinstance(client_profile_raw["company"], dict):
                logger.debug("[DIAGNOSTIC] Convertendo nested company de dict para CompanyInfo")
                client_profile_raw["company"] = CompanyInfo(**client_profile_raw["company"])

            # Agora converter para ClientProfile (com nested objects corretos)
            client_profile = ClientProfile(**client_profile_raw)
        else:
            client_profile = client_profile_raw
            # Defensive: mesmo quando o topo já é Pydantic, nested podem vir como dict
            try:
                from src.memory.schemas import CompanyInfo, StrategicContext

                if hasattr(client_profile, "context") and isinstance(client_profile.context, dict):
                    logger.debug(
                        "[DIAGNOSTIC] Normalizando nested context (dict -> StrategicContext)"
                    )
                    client_profile.context = StrategicContext(**client_profile.context)
                if hasattr(client_profile, "company") and isinstance(client_profile.company, dict):
                    logger.debug("[DIAGNOSTIC] Normalizando nested company (dict -> CompanyInfo)")
                    client_profile.company = CompanyInfo(**client_profile.company)
            except Exception as conv_err:
                logger.warning(f"[DIAGNOSTIC] Falha ao normalizar nested dicts: {conv_err}")

        # VALIDAÇÃO CRÍTICA: Dados completos necessários para diagnóstico confiável
        logger.info("[DIAGNOSTIC] Validando completude dos dados do cliente...")

        validation_errors = []

        # Validar company info
        if not hasattr(client_profile, "company") or not client_profile.company:
            validation_errors.append("Informações da empresa (company) ausentes")
        else:
            if not client_profile.company.name or len(client_profile.company.name.strip()) < 2:
                validation_errors.append("Nome da empresa não informado")
            if not client_profile.company.sector or len(client_profile.company.sector.strip()) < 3:
                validation_errors.append("Setor de atuação não informado")

        # Validar context (strategic)
        if not hasattr(client_profile, "context") or not client_profile.context:
            validation_errors.append("Contexto estratégico (context) ausente")
        else:
            # Validar challenges (mínimo 2)
            challenges = getattr(client_profile.context, "current_challenges", None) or []
            if len(challenges) < 2:
                validation_errors.append(
                    f"Desafios estratégicos insuficientes (fornecidos: {len(challenges)}, mínimo: 2)"
                )

            # Validar objectives (mínimo 3)
            objectives = getattr(client_profile.context, "strategic_objectives", None) or []
            if len(objectives) < 3:
                validation_errors.append(
                    f"Objetivos estratégicos insuficientes (fornecidos: {len(objectives)}, mínimo: 3)"
                )

        # Se há erros de validação, retornar diagnóstico com mensagem explicativa
        if validation_errors:
            logger.warning(
                f"[DIAGNOSTIC] Dados insuficientes para diagnóstico confiável: {len(validation_errors)} problemas identificados"
            )
            logger.warning(f"[DIAGNOSTIC] Problemas: {validation_errors}")

            # Construir mensagem explicativa
            error_list = "\n".join([f"  • {err}" for err in validation_errors])

            insufficient_data_message = f"""**Diagnóstico BSC Indisponível - Dados Insuficientes**

Para realizar um diagnóstico BSC confiável e personalizado, preciso de informações mais completas sobre sua empresa.

**Problemas identificados:**
{error_list}

**O que preciso:**
• Nome da empresa e setor de atuação (para contextualizar)
• Pelo menos 2 desafios estratégicos específicos que você enfrenta
• Pelo menos 3 objetivos estratégicos que deseja alcançar

**Por que isso é importante:**
Um diagnóstico BSC genérico baseado apenas em "melhores práticas" não teria valor real para você. Preciso entender seus desafios e objetivos específicos para:
1. Identificar gaps relevantes para seu contexto
2. Priorizar as 4 perspectivas BSC de acordo com sua situação
3. Gerar recomendações acionáveis e personalizadas

**Próximo passo:**
Por favor, volte ao onboarding e forneça as informações faltantes. Depois podemos fazer um diagnóstico rico e útil!"""

            # Retornar diagnostic vazio com mensagem
            from src.memory.schemas import DiagnosticResult

            empty_result = DiagnosticResult(
                perspective="Geral",
                current_state="Diagnóstico não realizado devido a dados insuficientes",
                gaps=[],
                opportunities=[],
                priority="MEDIUM",
                key_insights=[],
            )

            incomplete_diagnostic = CompleteDiagnostic(
                financial=empty_result,
                customer=empty_result,
                process=empty_result,
                learning=empty_result,
                recommendations=[],
                cross_perspective_synergies=[],
                executive_summary=insufficient_data_message,
                next_phase="ONBOARDING",  # Voltar para onboarding para completar dados
            )

            logger.info(
                "[DIAGNOSTIC] Retornando diagnóstico de dados insuficientes (sem chamar LLM)"
            )
            return incomplete_diagnostic

        logger.info("[DIAGNOSTIC] Validação OK - Dados completos para diagnóstico confiável")

        # TIMING DETALHADO - SESSAO 43 (2025-11-24)
        import time

        diag_inner_start = time.time()

        # ETAPA 1: Análise paralela das 4 perspectivas (AsyncIO)
        etapa1_start = time.time()
        logger.info("[TIMING] [DIAGNOSTIC] ETAPA 1/6: Analise paralela das 4 perspectivas BSC...")

        perspective_results = await self.run_parallel_analysis(client_profile, state)

        etapa1_elapsed = time.time() - etapa1_start
        logger.info(
            f"[TIMING] [DIAGNOSTIC] ETAPA 1/6 CONCLUIDA em {etapa1_elapsed:.2f}s | "
            f"Keys: {list(perspective_results.keys())}"
        )

        # ETAPA 1.5: Análises consultivas (7 ferramentas) - SPRINT 1 (GAP #2)!
        etapa15_start = time.time()
        logger.info("[TIMING] [DIAGNOSTIC] ETAPA 2/6: Ferramentas consultivas em paralelo...")

        tools_results = await self._run_consultative_tools(
            client_profile, state, perspective_results
        )

        etapa15_elapsed = time.time() - etapa15_start
        logger.info(
            f"[TIMING] [DIAGNOSTIC] ETAPA 2/6 CONCLUIDA em {etapa15_elapsed:.2f}s | "
            f"{len(tools_results.tools_executed)}/7 sucesso, "
            f"{len(tools_results.tools_failed)}/7 falhas"
        )

        # ETAPA 2: Consolidação cross-perspective (enriquecida com ferramentas)
        etapa2_start = time.time()
        logger.info("[TIMING] [DIAGNOSTIC] ETAPA 3/6: Consolidacao cross-perspective (LLM)...")

        consolidated = await self.consolidate_diagnostic(perspective_results, tools_results)

        etapa2_elapsed = time.time() - etapa2_start
        logger.info(
            f"[TIMING] [DIAGNOSTIC] ETAPA 3/6 CONCLUIDA em {etapa2_elapsed:.2f}s | "
            f"{len(consolidated.get('cross_perspective_synergies', []))} synergies"
        )

        # ETAPA 3: Geração de recomendações priorizadas
        etapa3_start = time.time()
        logger.info("[TIMING] [DIAGNOSTIC] ETAPA 4/6: Geracao de recomendacoes (LLM)...")

        recommendations = await self.generate_recommendations(
            perspective_results,
            consolidated,
        )

        etapa3_elapsed = time.time() - etapa3_start
        logger.info(
            f"[TIMING] [DIAGNOSTIC] ETAPA 4/6 CONCLUIDA em {etapa3_elapsed:.2f}s | "
            f"{len(recommendations)} recomendacoes"
        )

        # ETAPA 4: Construir CompleteDiagnostic
        etapa4_start = time.time()
        logger.info("[TIMING] [DIAGNOSTIC] ETAPA 5/6: Construindo diagnostico completo...")

        # Pydantic V2: Converter instâncias para dict usando .model_dump()
        # CRÍTICO: CompleteDiagnostic NÃO aceita instâncias Pydantic diretamente
        financial_dict = perspective_results["Financeira"].model_dump()
        customer_dict = perspective_results["Clientes"].model_dump()
        process_dict = perspective_results["Processos Internos"].model_dump()
        learning_dict = perspective_results["Aprendizado e Crescimento"].model_dump()

        # Converter recommendations list
        recommendations_dicts = [
            rec.model_dump() if hasattr(rec, "model_dump") else rec for rec in recommendations
        ]

        # Converter tools_results (pode ser None)
        tools_results_dict = tools_results.model_dump() if tools_results else None

        complete_diagnostic = CompleteDiagnostic(
            financial=financial_dict,
            customer=customer_dict,
            process=process_dict,
            learning=learning_dict,
            recommendations=recommendations_dicts,
            cross_perspective_synergies=consolidated["cross_perspective_synergies"],
            executive_summary=consolidated["executive_summary"],
            next_phase=consolidated["next_phase"],  # type: ignore
            diagnostic_tools_results=tools_results_dict,  # SPRINT 1: Incluir outputs das ferramentas
        )

        etapa4_elapsed = time.time() - etapa4_start

        # ETAPA 4.5: 2ª FASE - Gerar KPI Framework (SESSAO 49 - BUG FIX)
        # KPI Framework precisa do CompleteDiagnostic para contexto
        etapa45_start = time.time()
        logger.info("[TIMING] [DIAGNOSTIC] ETAPA 6/6: Gerando KPI Framework...")

        kpi_framework = None
        try:
            kpi_framework = self.generate_kpi_framework(
                client_profile=client_profile,
                diagnostic_result=complete_diagnostic,
                use_rag=True,
            )
            if kpi_framework:
                logger.info(
                    f"[OK] [DIAGNOSTIC] KPI Framework gerado: {kpi_framework.total_kpis()} KPIs"
                )
                # Atualizar tools_results com KPI Framework (com null-check defensivo)
                if tools_results is not None:
                    tools_results.kpi_framework = kpi_framework
                    if "kpi_framework" not in tools_results.tools_executed:
                        tools_results.tools_executed.append("kpi_framework")
                    if "kpi_framework" in tools_results.tools_failed:
                        tools_results.tools_failed.remove("kpi_framework")
                else:
                    logger.warning("[WARN] [DIAGNOSTIC] tools_results is None, cannot update KPI Framework")
            else:
                # Falha: retornou None/falsy - rastrear em tools_failed
                logger.warning("[WARN] [DIAGNOSTIC] KPI Framework retornou None/vazio")
                if tools_results is not None and "kpi_framework" not in tools_results.tools_failed:
                    tools_results.tools_failed.append("kpi_framework")
        except Exception as e:
            logger.warning(f"[WARN] [DIAGNOSTIC] Falha ao gerar KPI Framework: {e}")
            # Falha: excecao - rastrear em tools_failed
            if tools_results is not None and "kpi_framework" not in tools_results.tools_failed:
                tools_results.tools_failed.append("kpi_framework")

        etapa45_elapsed = time.time() - etapa45_start

        # Atualizar diagnostic com tools_results atualizado (inclui KPI Framework)
        complete_diagnostic.diagnostic_tools_results = (
            tools_results.model_dump() if tools_results else None
        )

        total_elapsed = time.time() - diag_inner_start

        logger.info(
            f"[TIMING] [DIAGNOSTIC] ========== DIAGNOSTICO CONCLUIDO ==========\n"
            f"[TIMING] [DIAGNOSTIC] RESUMO DE TEMPOS:\n"
            f"[TIMING] [DIAGNOSTIC]   ETAPA 1/6 (4 Agents paralelo): {etapa1_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC]   ETAPA 2/6 (7 Ferramentas):     {etapa15_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC]   ETAPA 3/6 (Consolidacao LLM):  {etapa2_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC]   ETAPA 4/6 (Recomendacoes LLM): {etapa3_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC]   ETAPA 5/6 (Build diagnostic):  {etapa4_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC]   ETAPA 6/6 (KPI Framework):     {etapa45_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC]   TOTAL:                         {total_elapsed:.2f}s\n"
            f"[TIMING] [DIAGNOSTIC] Recommendations: {len(recommendations)} | "
            f"KPI Framework: {'[OK]' if kpi_framework else '[--]'} | "
            f"Next Phase: {complete_diagnostic.next_phase}"
        )

        return complete_diagnostic

    async def _run_consultative_tools(
        self,
        client_profile: ClientProfile,
        state: BSCState,
        parallel_results: dict[str, DiagnosticResult],
    ) -> DiagnosticToolsResult:
        """
        SPRINT 1 (GAP #2): Executa 7 ferramentas consultivas em paralelo.

        Usa asyncio.gather() com return_exceptions=True para execução paralela robusta.
        Ferramentas sync são executadas via asyncio.to_thread() para não bloquear event loop.

        Args:
            client_profile: Perfil completo do cliente
            state: Estado LangGraph atual
            parallel_results: Outputs dos 4 agentes BSC (dict {perspective: DiagnosticResult})

        Returns:
            DiagnosticToolsResult com outputs de todas ferramentas (sucesso + falhas)

        Raises:
            Exception: Se TODAS ferramentas falharem (crítico - diagnóstico inválido)
        """
        import time

        start_time = time.time()

        logger.info("[DIAGNOSTIC] [TOOLS] Executando 7 ferramentas consultivas em paralelo...")

        # Preparar contexto comum para ferramentas
        # Extrair primeiro desafio para Five Whys e Issue Tree
        first_challenge = None
        if (
            hasattr(client_profile, "context")
            and hasattr(client_profile.context, "current_challenges")
            and client_profile.context.current_challenges
        ):
            first_challenge = client_profile.context.current_challenges[0]

        # Preparar items para priorização (extrair de recommendations futuras ou usar gaps)
        items_to_prioritize = []
        for perspective, result in parallel_results.items():
            gaps = getattr(result, "gaps", []) or []
            for gap in gaps[:2]:  # Top 2 gaps por perspectiva
                items_to_prioritize.append(
                    {
                        "title": gap,
                        "description": f"Gap identificado na perspectiva {perspective}",
                        "perspective": perspective,
                        "type": "gap",
                    }
                )

        # ETAPA 1: Criar tasks async para execução paralela
        # SPRINT 1 CORREÇÃO: Todos métodos agora são async, usar asyncio.gather() diretamente

        async def _return_none():
            """Helper para retornar None de forma async."""
            return

        tasks = [
            # SWOT Analysis (ASYNC - executa diretamente)
            self.generate_swot_analysis(
                client_profile, use_rag=True, refine_with_diagnostic=False, diagnostic_result=None
            ),
            # Five Whys (ASYNC - executa diretamente)
            (
                self.generate_five_whys_analysis(
                    client_profile,
                    problem_statement=first_challenge or "Desafios estratégicos da organização",
                    use_rag=True,
                )
                if first_challenge
                else _return_none()
            ),
            # Issue Tree (ASYNC - executa diretamente)
            (
                self.generate_issue_tree_analysis(
                    client_profile,
                    root_problem=first_challenge or "Desafios estratégicos da organização",
                    max_depth=3,
                    use_rag=True,
                )
                if first_challenge
                else _return_none()
            ),
            # KPI Framework - precisa diagnostic completo, será None por enquanto
            # Será executado na 2ª fase após diagnostic completo
            _return_none(),
            # Strategic Objectives - precisa diagnostic completo
            # Será executado na 2ª fase após diagnostic completo
            _return_none(),
            # Benchmarking Report - precisa client_id
            # Será executado na 2ª fase se client_id disponível
            _return_none(),
            # Prioritization Matrix (ASYNC)
            (
                self.generate_prioritization_matrix(
                    items_to_prioritize=items_to_prioritize[:8] if items_to_prioritize else [],
                    client_profile=client_profile,
                    prioritization_context="Priorização de gaps identificados nas 4 perspectivas BSC",
                    use_rag=True,
                )
                if items_to_prioritize
                else _return_none()
            ),
        ]

        # ETAPA 2: Executar em paralelo com tratamento de erros robusto
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # ETAPA 3: Processar results e separar sucessos de falhas
        swot, five_whys, issue_tree, kpi, objectives, benchmarking, prioritization = results

        tools_executed = []
        tools_failed = []

        # Processar cada resultado
        if not isinstance(swot, Exception) and swot is not None:
            tools_executed.append("swot_analysis")
        else:
            tools_failed.append("swot_analysis")
            logger.error(f"[TOOLS] SWOT failed: {swot}")
            swot = None

        if not isinstance(five_whys, Exception) and five_whys is not None:
            tools_executed.append("five_whys_analysis")
        else:
            tools_failed.append("five_whys_analysis")
            logger.error(f"[TOOLS] Five Whys failed: {five_whys}")
            five_whys = None

        if not isinstance(issue_tree, Exception) and issue_tree is not None:
            tools_executed.append("issue_tree")
        else:
            tools_failed.append("issue_tree")
            logger.error(f"[TOOLS] Issue Tree failed: {issue_tree}")
            issue_tree = None

        if not isinstance(kpi, Exception) and kpi is not None:
            tools_executed.append("kpi_framework")
        else:
            tools_failed.append("kpi_framework")
            logger.debug("[TOOLS] KPI Framework skipped (precisa diagnostic completo)")
            kpi = None

        if not isinstance(objectives, Exception) and objectives is not None:
            tools_executed.append("strategic_objectives")
        else:
            tools_failed.append("strategic_objectives")
            logger.debug("[TOOLS] Strategic Objectives skipped (precisa diagnostic completo)")
            objectives = None

        if not isinstance(benchmarking, Exception) and benchmarking is not None:
            tools_executed.append("benchmarking_report")
        else:
            tools_failed.append("benchmarking_report")
            logger.debug("[TOOLS] Benchmarking skipped (precisa client_id)")
            benchmarking = None

        if not isinstance(prioritization, Exception) and prioritization is not None:
            tools_executed.append("prioritization_matrix")
        else:
            tools_failed.append("prioritization_matrix")
            logger.error(f"[TOOLS] Prioritization Matrix failed: {prioritization}")
            prioritization = None

        execution_time = time.time() - start_time

        logger.info(
            f"[DIAGNOSTIC] [TOOLS] Concluído em {execution_time:.2f}s | "
            f"Sucesso: {len(tools_executed)}/7 | "
            f"Falhas: {len(tools_failed)}/7"
        )

        # ETAPA 4: Validar que pelo menos algumas ferramentas executaram
        if len(tools_executed) == 0:
            raise Exception(
                "CRITICAL: Todas 7 ferramentas consultivas falharam! Diagnóstico inválido."
            )

        # ETAPA 5: Retornar result agregado
        # CORREÇÃO SESSAO 49: Converter para dict antes de passar para Pydantic
        # Evita ValidationError causado por reimport de módulos (Streamlit hot reload)
        # Pydantic v2 compara tipos por identidade, não por estrutura
        def _to_dict_if_model(obj):
            """Converte BaseModel para dict, evitando type mismatch."""
            if obj is None:
                return None
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            return obj

        return DiagnosticToolsResult(
            swot_analysis=_to_dict_if_model(swot),
            five_whys_analysis=_to_dict_if_model(five_whys),
            kpi_framework=_to_dict_if_model(kpi),
            strategic_objectives=_to_dict_if_model(objectives),
            benchmarking_report=_to_dict_if_model(benchmarking),
            issue_tree=_to_dict_if_model(issue_tree),
            prioritization_matrix=_to_dict_if_model(prioritization),
            execution_time=execution_time,
            tools_executed=tools_executed,
            tools_failed=tools_failed,
        )

    def _format_tools_results(self, tools_results: DiagnosticToolsResult) -> str:
        """
        Formata outputs das 7 ferramentas consultivas para inclusão no prompt de consolidação.

        SPRINT 1 (GAP #2): Método criado para enriquecer prompt com insights das ferramentas.

        Args:
            tools_results: Resultados agregados das ferramentas consultivas

        Returns:
            String formatada para inclusão no prompt (markdown-style)
        """
        sections = []

        # SWOT Analysis
        if tools_results.swot_analysis:
            swot = tools_results.swot_analysis
            sections.append(
                f"""
## SWOT ANALYSIS

**Forças (Strengths):**
{chr(10).join(f"- {s}" for s in swot.strengths) if swot.strengths else "- Nenhuma identificada"}

**Fraquezas (Weaknesses):**
{chr(10).join(f"- {w}" for w in swot.weaknesses) if swot.weaknesses else "- Nenhuma identificada"}

**Oportunidades (Opportunities):**
{chr(10).join(f"- {o}" for o in swot.opportunities) if swot.opportunities else "- Nenhuma identificada"}

**Ameaças (Threats):**
{chr(10).join(f"- {t}" for t in swot.threats) if swot.threats else "- Nenhuma identificada"}
"""
            )

        # Five Whys
        if tools_results.five_whys_analysis:
            fw = tools_results.five_whys_analysis
            iterations_text = ""
            if hasattr(fw, "iterations") and fw.iterations:
                iterations_text = chr(10).join(
                    f"- Why {i+1}: {it.why_question if hasattr(it, 'why_question') else str(it)}"
                    for i, it in enumerate(fw.iterations[:5])  # Limitar a 5 iterações
                )
            sections.append(
                f"""
## FIVE WHYS (ROOT CAUSE ANALYSIS)

**Problema:** {fw.problem_statement if hasattr(fw, 'problem_statement') else 'N/A'}

**Iterações:**
{iterations_text if iterations_text else "- Nenhuma iteração disponível"}

**Root Cause Final:** {fw.root_cause if hasattr(fw, 'root_cause') else 'N/A'}

**Confiança:** {fw.confidence_score if hasattr(fw, 'confidence_score') else 'N/A'}%
"""
            )

        # Issue Tree
        if tools_results.issue_tree:
            it = tools_results.issue_tree
            sections.append(
                f"""
## ISSUE TREE (MECE DECOMPOSITION)

**Problema Raiz:** {it.root_problem if hasattr(it, 'root_problem') else 'N/A'}

**Sub-problemas Identificados:**
{chr(10).join(f"- {sp}" for sp in (it.sub_problems if hasattr(it, 'sub_problems') else [])) if hasattr(it, 'sub_problems') and it.sub_problems else "- Nenhum sub-problema disponível"}
"""
            )

        # Prioritization Matrix
        if tools_results.prioritization_matrix:
            pm = tools_results.prioritization_matrix
            items_text = ""
            if hasattr(pm, "items") and pm.items:
                # Agrupar por quadrante/prioridade
                top_items = sorted(pm.items, key=lambda x: getattr(x, "rank", 999))[:5]
                items_text = chr(10).join(
                    f"- {getattr(item, 'title', 'N/A')} (Rank: {getattr(item, 'rank', 'N/A')}, Priority: {getattr(item, 'priority_level', 'N/A')})"
                    for item in top_items
                )
            sections.append(
                f"""
## PRIORITIZATION MATRIX (Impact/Effort)

**Top 5 Items Priorizados:**
{items_text if items_text else "- Nenhum item disponível"}
"""
            )

        # KPI Framework (se disponível)
        if tools_results.kpi_framework:
            kpi_fw = tools_results.kpi_framework
            kpi_section = "## KPI FRAMEWORK\n\n"
            for perspective in ["financial", "customer", "process", "learning"]:
                kpis = getattr(kpi_fw, f"{perspective}_kpis", [])
                if kpis:
                    kpi_section += f"**{perspective.title()} Perspective:**\n"
                    for kpi in kpis[:3]:  # Top 3 KPIs por perspectiva
                        name = getattr(kpi, "name", "N/A")
                        desc = getattr(kpi, "description", "N/A")[:100]  # Limitar descrição
                        kpi_section += f"- {name}: {desc}\n"
                    kpi_section += "\n"
            sections.append(kpi_section)

        # Strategic Objectives (se disponível)
        if tools_results.strategic_objectives:
            so = tools_results.strategic_objectives
            obj_section = "## STRATEGIC OBJECTIVES\n\n"
            for perspective in ["financial", "customer", "process", "learning"]:
                objs = getattr(so, f"{perspective}_objectives", [])
                if objs:
                    obj_section += f"**{perspective.title()}:**\n"
                    for obj in objs[:2]:  # Top 2 objetivos por perspectiva
                        desc = getattr(obj, "description", "N/A")[:150]
                        obj_section += f"- {desc}\n"
                    obj_section += "\n"
            sections.append(obj_section)

        # Benchmarking (se disponível)
        if tools_results.benchmarking_report:
            br = tools_results.benchmarking_report
            sections.append(
                f"""
## BENCHMARKING REPORT

**Setor:** {getattr(br, 'sector', 'N/A')}

**Comparações Realizadas:** {len(getattr(br, 'comparisons', [])) if hasattr(br, 'comparisons') else 0}
"""
            )

        return "\n\n".join(sections) if sections else "Nenhuma análise consultiva disponível."

    async def run_diagnostic(
        self,
        state: BSCState,
    ) -> CompleteDiagnostic:
        """Orquestrador completo do diagnóstico com timeout global (failsafe)."""
        logger.info("[DIAGNOSTIC v3.4 PRINT] >>>>> run_diagnostic() CHAMADO <<<<<")
        # SESSAO 49: Aumentar timeout para 20 min (adicionada ETAPA 4.5 KPI Framework)
        global_timeout_sec = 1200  # 20 minutos para diagnóstico completo + KPI Framework
        logger.info(
            f"[DIAGNOSTIC v3.4] Iniciando run_diagnostic com timeout global de {global_timeout_sec}s (20 min)"
        )
        logger.info(
            f"[DIAGNOSTIC v3.4 PRINT] Timeout global: {global_timeout_sec}s (20 min) - Inclui KPI Framework (ETAPA 4.5)"
        )
        try:
            logger.info("[DIAGNOSTIC v3.1 LOG] ANTES de asyncio.wait_for(_run_diagnostic_inner)")
            result = await asyncio.wait_for(
                self._run_diagnostic_inner(state), timeout=global_timeout_sec
            )
            logger.info("[DIAGNOSTIC v3.1 LOG] DEPOIS de asyncio.wait_for - SUCCESS!")
            logger.info("[DIAGNOSTIC] run_diagnostic concluído dentro do timeout global")
            return result
        except asyncio.TimeoutError as e:
            logger.error(
                f"[DIAGNOSTIC] Timeout global ({global_timeout_sec}s) no diagnóstico completo"
            )
            raise ValueError("Timeout global no diagnóstico BSC") from e

    async def refine_diagnostic(
        self,
        existing_diagnostic: CompleteDiagnostic,
        feedback: str,
        state: BSCState,
    ) -> CompleteDiagnostic:
        """
        FASE 4.6: Refina diagnóstico existente baseado em feedback do usuário.

        Quando um diagnóstico é rejeitado ou modificado (approval_status REJECTED/MODIFIED),
        este método usa o approval_feedback para melhorar o diagnóstico ao invés de recriar do zero.

        Estratégias de refinement:
        - TARGETED: Refina apenas perspectivas/recomendações específicas mencionadas no feedback
        - FULL: Refaz diagnóstico completo (se feedback muito amplo)
        - RECOMMENDATIONS_ONLY: Refina apenas recomendações (se feedback foca em ações)

        Args:
            existing_diagnostic: Diagnóstico original a ser refinado
            feedback: Feedback textual do usuário sobre o que melhorar
            state: Estado atual com client_profile e contexto

        Returns:
            CompleteDiagnostic refinado

        Raises:
            ValueError: Se feedback vazio, diagnóstico inválido, ou state sem client_profile

        Example:
            >>> diagnostic = await agent.run_diagnostic(state)
            >>> refined = await agent.refine_diagnostic(
            ...     diagnostic,
            ...     "SWOT precisa mais Opportunities relacionadas ao mercado enterprise",
            ...     state
            ... )
            >>> len(refined.recommendations) >= len(diagnostic.recommendations)
            True
        """
        logger.info("[DIAGNOSTIC] [REFINEMENT] ========== INICIANDO REFINEMENT ==========")
        logger.info(f"[DIAGNOSTIC] [REFINEMENT] Feedback recebido: {feedback[:100]}...")

        # Validações
        if not feedback or not feedback.strip():
            raise ValueError(
                "Feedback não pode ser vazio. Forneça feedback específico sobre o que melhorar."
            )

        if not existing_diagnostic:
            raise ValueError("Diagnóstico existente não pode ser None.")

        if not state.client_profile:
            raise ValueError("client_profile ausente no state. Execute onboarding primeiro.")

        # Converter client_profile se necessário
        client_profile_raw = state.client_profile
        if isinstance(client_profile_raw, dict):
            logger.debug(
                "[DIAGNOSTIC] [REFINEMENT] Convertendo client_profile de dict para ClientProfile"
            )
            from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext

            if "context" in client_profile_raw and isinstance(client_profile_raw["context"], dict):
                client_profile_raw["context"] = StrategicContext(**client_profile_raw["context"])
            if "company" in client_profile_raw and isinstance(client_profile_raw["company"], dict):
                client_profile_raw["company"] = CompanyInfo(**client_profile_raw["company"])

            client_profile = ClientProfile(**client_profile_raw)
        else:
            client_profile = client_profile_raw

        # Formatar contexto do cliente
        company = client_profile.company
        context = client_profile.context
        challenges_text = (
            ", ".join(context.current_challenges)
            if context.current_challenges
            else "Não informados"
        )
        objectives_text = (
            ", ".join(context.strategic_objectives)
            if context.strategic_objectives
            else "Não informados"
        )

        client_context = (
            f"Empresa: {company.name}\n"
            f"Setor: {company.sector}\n"
            f"Porte: {company.size}\n"
            f"Desafios: {challenges_text}\n"
            f"Objetivos: {objectives_text}"
        )

        # Converter diagnóstico existente para JSON
        diagnostic_json = existing_diagnostic.model_dump_json(indent=2)

        # Formatar prompt
        formatted_prompt = REFINE_DIAGNOSTIC_PROMPT.format(
            feedback=feedback.strip(),
            diagnostic_json=diagnostic_json,
            client_context=client_context,
        )

        logger.info("[DIAGNOSTIC] [REFINEMENT] Chamando LLM para refinement...")

        # Criar structured LLM
        structured_llm = self.llm.with_structured_output(
            CompleteDiagnostic, method="function_calling"
        )

        messages = [
            SystemMessage(
                content="Você é um consultor BSC especializado em refinar diagnósticos baseado em feedback específico."
            ),
            HumanMessage(content=formatted_prompt),
        ]

        try:
            # Chamar LLM com timeout
            logger.info("[DIAGNOSTIC] [REFINEMENT] Aguardando resposta do LLM (timeout: 300s)...")
            refined_diagnostic = await asyncio.wait_for(
                structured_llm.ainvoke(messages), timeout=300  # 5 minutos para refinement
            )

            logger.info("[DIAGNOSTIC] [REFINEMENT] LLM retornou diagnóstico refinado")

            # Validar diagnóstico refinado
            if not refined_diagnostic:
                logger.warning(
                    "[DIAGNOSTIC] [REFINEMENT] LLM retornou None. Fallback: retornar diagnóstico original."
                )
                return existing_diagnostic

            # Verificar se melhorias foram aplicadas (heurística simples)
            if refined_diagnostic.executive_summary == existing_diagnostic.executive_summary:
                logger.warning(
                    "[DIAGNOSTIC] [REFINEMENT] Executive summary não mudou. Pode indicar que refinement não foi aplicado."
                )

            logger.info(
                f"[DIAGNOSTIC] [REFINEMENT] ========== REFINEMENT CONCLUÍDO ========== "
                f"(Recommendations: {len(refined_diagnostic.recommendations)}, "
                f"Executive Summary atualizado: {refined_diagnostic.executive_summary != existing_diagnostic.executive_summary})"
            )

            return refined_diagnostic

        except asyncio.TimeoutError:
            logger.error("[DIAGNOSTIC] [REFINEMENT] Timeout no refinement (300s)")
            logger.warning("[DIAGNOSTIC] [REFINEMENT] Fallback: retornar diagnóstico original")
            return existing_diagnostic
        except Exception as e:
            logger.error(f"[DIAGNOSTIC] [REFINEMENT] Erro durante refinement: {e}", exc_info=True)
            logger.warning("[DIAGNOSTIC] [REFINEMENT] Fallback: retornar diagnóstico original")
            return existing_diagnostic

    async def generate_swot_analysis(
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
            >>> diagnostic = await agent.run_diagnostic(state)
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

        if not client_profile.context:
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

        # STEP 1: Facilitar SWOT inicial (ASYNC)
        swot = await swot_tool.facilitate_swot(
            company_info=client_profile.company,
            strategic_context=client_profile.context,
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

    async def generate_action_plan(
        self,
        client_profile: ClientProfile,
        diagnostic_result: CompleteDiagnostic | None = None,
        use_rag: bool = True,
    ):
        """Gera plano de ação estruturado para implementação BSC.

        Utiliza ActionPlanTool para facilitar criação de plano de ação contextualizado
        com conhecimento BSC (via RAG) e baseado em diagnóstico realizado.

        Workflow:
        1. Valida contexto da empresa e diagnóstico disponível
        2. Chama ActionPlanTool.facilitate() para criar plano inicial
        3. Valida qualidade e balanceamento do plano gerado

        Args:
            client_profile: ClientProfile com contexto da empresa
            diagnostic_result: CompleteDiagnostic para base do plano (recomendado)
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)

        Returns:
            ActionPlan: Objeto Pydantic validado com ações específicas e acionáveis

        Raises:
            ValueError: Se client_profile.company ausente
            ValueError: Se diagnostic_result=None (recomendado ter diagnóstico)

        Example:
            >>> # Action Plan baseado em diagnóstico
            >>> diagnostic = await agent.run_diagnostic(state)
            >>> action_plan = await agent.generate_action_plan(
            ...     profile,
            ...     diagnostic_result=diagnostic
            ... )
            >>> print(f"Plano criado: {action_plan.total_actions} ações")
            >>> print(f"Score qualidade: {action_plan.quality_score():.1%}")
        """
        from src.tools.action_plan import ActionPlanTool

        logger.info(
            f"[DIAGNOSTIC] Gerando Action Plan para {client_profile.company.name} "
            f"(use_rag={use_rag}, diagnostic={'disponível' if diagnostic_result else 'ausente'})"
        )

        # Validações
        if not client_profile.company:
            raise ValueError("ClientProfile.company ausente. Dados insuficientes para Action Plan.")

        if not diagnostic_result:
            logger.warning(
                "[DIAGNOSTIC] diagnostic_result=None. "
                "Recomendado executar diagnóstico completo antes de criar Action Plan."
            )

        # Instanciar ActionPlanTool
        action_plan_tool = ActionPlanTool(llm=self.llm)

        # STEP 1: Facilitar Action Plan
        action_plan = await action_plan_tool.facilitate(
            client_profile=client_profile,
            financial_agent=self.financial_agent if use_rag else None,
            customer_agent=self.customer_agent if use_rag else None,
            process_agent=self.process_agent if use_rag else None,
            learning_agent=self.learning_agent if use_rag else None,
            diagnostic_results=diagnostic_result,
        )

        logger.info(
            f"[DIAGNOSTIC] Action Plan gerado: {action_plan.total_actions} ações "
            f"(score: {action_plan.quality_score():.1%}, balanceado: {action_plan.is_balanced()})"
        )

        # Validar qualidade
        if action_plan.quality_score() < 0.5:
            logger.warning(
                f"[DIAGNOSTIC] Action Plan com score baixo: {action_plan.quality_score():.1%}. "
                "Considere refinar com mais contexto ou diagnóstico."
            )

        if not action_plan.is_balanced():
            logger.warning(
                "[DIAGNOSTIC] Action Plan não está balanceado entre as 4 perspectivas BSC. "
                f"Distribuição: {action_plan.by_perspective}"
            )

        logger.info("[DIAGNOSTIC] Action Plan criado e validado!")
        return action_plan

    async def generate_prioritization_matrix(
        self,
        items_to_prioritize: list[dict],
        client_profile: ClientProfile,
        prioritization_context: str,
        use_rag: bool = True,
        weights_config: dict[str, float] | None = None,
    ):
        """Gera matriz de priorização para objetivos/ações estratégicas BSC.

        Utiliza PrioritizationMatrixTool para facilitar avaliação e ranking de items
        estratégicos usando framework híbrido (Impact/Effort + RICE + BSC-specific).

        Framework de Priorização (4 critérios, 0-100 scale):
        - Strategic Impact (40% peso): Potencial contribuição objetivos BSC
        - Implementation Effort (30% peso, invertido): Recursos necessários
        - Urgency (15% peso): Time sensitivity
        - Strategic Alignment (15% peso): Alinhamento com 4 perspectivas BSC

        4 Níveis de Prioridade (baseado no score final):
        - CRITICAL (75-100): Quick wins + strategic imperatives
        - HIGH (50-74): Important projects
        - MEDIUM (25-49): Nice-to-have improvements
        - LOW (0-24): Deprioritize or eliminate

        Workflow:
        1. Valida items a priorizar e contexto da empresa
        2. Chama PrioritizationMatrixTool.prioritize() com RAG opcional
        3. Valida qualidade e balanceamento da matriz gerada

        Args:
            items_to_prioritize: Lista de items a priorizar. Cada item deve ser dict com:
                - id (str, opcional): Identificador único
                - type (str, opcional): "strategic_objective", "action_item", "initiative", "project", "gap"
                - title (str, obrigatório): Nome do item (10-200 caracteres)
                - description (str, obrigatório): Descrição detalhada (20+ caracteres)
                - perspective (str, obrigatório): Perspectiva BSC ("Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento")
            client_profile: ClientProfile com contexto da empresa
            prioritization_context: Contexto da priorização (ex: "Objetivos estratégicos Q1 2025 - TechCorp")
            use_rag: Se True, busca conhecimento BSC via specialist agents (default: True)
            weights_config: Configuração customizada de pesos (opcional). Default: impact 40%, effort 30%, urgency 15%, alignment 15%

        Returns:
            PrioritizationMatrix: Objeto Pydantic validado com items priorizados, scores e ranks

        Raises:
            ValueError: Se client_profile.company ausente ou items_to_prioritize vazio/inválido
            ValidationError: Se LLM retornar dados inválidos

        Example:
            >>> items = [
            ...     {"id": "obj_001", "title": "Aumentar NPS em 20 pontos",
            ...      "description": "Melhorar experiência cliente...", "perspective": "Clientes"},
            ...     {"id": "obj_002", "title": "Reduzir custos operacionais 15%",
            ...      "description": "Otimizar processos...", "perspective": "Financeira"}
            ... ]
            >>> matrix = await agent.generate_prioritization_matrix(
            ...     items_to_prioritize=items,
            ...     client_profile=profile,
            ...     prioritization_context="Objetivos estratégicos Q1 2025 - TechCorp"
            ... )
            >>> print(f"Matriz criada: {matrix.total_items} items priorizados")
            >>> print(f"Top 3: {[item.title for item in matrix.top_n(3)]}")
            >>> print(f"Distribuição: {matrix.critical_count} CRITICAL, {matrix.high_count} HIGH")
        """
        from src.tools.prioritization_matrix import PrioritizationMatrixTool

        logger.info(
            f"[DIAGNOSTIC] Gerando Prioritization Matrix para {client_profile.company.name} "
            f"(items={len(items_to_prioritize)}, use_rag={use_rag})"
        )

        # Validações
        if not client_profile.company:
            raise ValueError(
                "ClientProfile.company ausente. Dados insuficientes para Prioritization Matrix."
            )

        if not items_to_prioritize:
            raise ValueError(
                "items_to_prioritize não pode ser vazio. Forneça ao menos 1 item para priorizar."
            )

        if not prioritization_context or not prioritization_context.strip():
            raise ValueError(
                "prioritization_context não pode ser vazio. Forneça contexto da priorização."
            )

        # Instanciar PrioritizationMatrixTool
        prioritization_tool = PrioritizationMatrixTool(llm=self.llm)

        # STEP 1: Priorizar items
        matrix = await prioritization_tool.prioritize(
            items_to_prioritize=items_to_prioritize,
            client_profile=client_profile,
            prioritization_context=prioritization_context,
            financial_agent=self.financial_agent if use_rag else None,
            customer_agent=self.customer_agent if use_rag else None,
            process_agent=self.process_agent if use_rag else None,
            learning_agent=self.learning_agent if use_rag else None,
            weights_config=weights_config,
        )

        logger.info(
            f"[DIAGNOSTIC] Prioritization Matrix gerada: {matrix.total_items} items "
            f"({matrix.critical_count} CRITICAL, {matrix.high_count} HIGH, "
            f"{matrix.medium_count} MEDIUM, {matrix.low_count} LOW)"
        )

        # Validar qualidade
        if matrix.total_items >= 3:
            critical_ratio = matrix.critical_count / matrix.total_items
            if critical_ratio > 0.5:
                logger.warning(
                    f"[DIAGNOSTIC] Prioritization Matrix com muitos items CRITICAL: {critical_ratio:.1%}. "
                    "Considere revisar critérios de avaliação (possível inflação de scores)."
                )

        if matrix.total_items >= 4 and not matrix.is_balanced():
            logger.warning(
                "[DIAGNOSTIC] Prioritization Matrix não está balanceada entre as 4 perspectivas BSC. "
                "Considere adicionar mais items de perspectivas sub-representadas."
            )

        logger.info(
            f"[DIAGNOSTIC] Prioritization Matrix criada e validada! "
            f"(balanceada: {matrix.is_balanced()})"
        )
        return matrix

    async def generate_five_whys_analysis(
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

        if not client_profile.context:
            raise ValueError(
                "ClientProfile.strategic_context ausente. "
                "Execute onboarding completo antes de gerar 5 Whys."
            )

        if not problem_statement or len(problem_statement) < 10:
            raise ValueError(
                f"problem_statement deve ter >= 10 chars " f"(recebeu: '{problem_statement}')"
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

        # Facilitar 5 Whys iterativo (ASYNC)
        analysis = await five_whys_tool.facilitate_five_whys(
            company_info=client_profile.company,
            strategic_context=client_profile.context,
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

    async def generate_issue_tree_analysis(
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

        if not client_profile.context:
            raise ValueError(
                "ClientProfile.strategic_context ausente. "
                "Execute onboarding completo antes de gerar Issue Tree."
            )

        if not root_problem or len(root_problem) < 10:
            raise ValueError(f"root_problem deve ter >= 10 chars " f"(recebeu: '{root_problem}')")

        if not (1 <= max_depth <= 4):
            raise ValueError(f"max_depth deve ser 1-4 " f"(recebeu: {max_depth})")

        # Instanciar IssueTreeTool
        issue_tree_tool = IssueTreeTool(
            llm=self.llm,
            financial_agent=self.financial_agent,
            customer_agent=self.customer_agent,
            process_agent=self.process_agent,
            learning_agent=self.learning_agent,
        )

        # Facilitar Issue Tree decomposicao MECE (ASYNC)
        tree_analysis = await issue_tree_tool.facilitate_issue_tree(
            company_info=client_profile.company,
            strategic_context=client_profile.context,
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
                "[DIAGNOSTIC] Issue Tree incompleto! "
                "Alguns niveis tem < 2 branches (nao MECE Collectively Exhaustive)"
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
            >>> diagnostic = await agent.run_diagnostic(state)
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

        if not client_profile.context:
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
            strategic_context=client_profile.context,
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
            "Aprendizado": len(framework.learning_kpis),
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
            logger.info(f"[DIAGNOSTIC] Framework balanceado! Distribuicao: {counts}")

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
            client_profile.context or diagnostic_result.executive_summary[:200]
            if diagnostic_result.executive_summary
            else "Contexto estrategico nao fornecido"
        )

        # Lazy load tool
        if not hasattr(self, "_strategic_objectives_tool"):
            rag_agents = None
            if use_rag:
                rag_agents = (
                    self.financial_agent,
                    self.customer_agent,
                    self.process_agent,
                    self.learning_agent,
                )

            self._strategic_objectives_tool = StrategicObjectivesTool(
                llm=self.llm, use_rag=use_rag, rag_agents=rag_agents
            )
            logger.info("[DIAGNOSTIC] StrategicObjectivesTool inicializada (lazy loading)")

        # Gerar framework de objetivos
        try:
            framework = self._strategic_objectives_tool.define_objectives(
                company_info=company_info,
                strategic_context=strategic_context,
                diagnostic_result=diagnostic_result,
                existing_kpis=existing_kpis,
            )

            logger.info(
                f"[DIAGNOSTIC] Strategic Objectives Framework gerado: "
                f"{framework.total_objectives()} objetivos totais"
            )

        except Exception as e:
            logger.error(f"[DIAGNOSTIC] Erro ao gerar Strategic Objectives Framework: {e}")
            raise RuntimeError(f"Falha ao gerar Strategic Objectives Framework: {e!s}") from e

        # Validar balanceamento (warning se desbalanceado, mas nao bloqueia)
        counts = {
            "Financeira": len(framework.financial_objectives),
            "Clientes": len(framework.customer_objectives),
            "Processos": len(framework.process_objectives),
            "Aprendizado": len(framework.learning_objectives),
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
            logger.info(f"[DIAGNOSTIC] Framework balanceado! Distribuicao: {counts}")

        # Log vinculacao com KPIs (se fornecidos)
        if existing_kpis:
            with_kpis = len(framework.with_related_kpis())
            kpi_percentage = (with_kpis / total) * 100 if total > 0 else 0
            logger.info(
                f"[DIAGNOSTIC] Vinculacao com KPIs: {with_kpis}/{total} objetivos "
                f"({kpi_percentage:.0f}%) tem KPIs relacionados"
            )

        return framework

    def generate_benchmarking_report(self, client_id: str, use_rag: bool = False):
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
            >>> logger.info(report.summary())
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
                f"Cliente '{client_id}' não encontrado. " f"Execute onboarding primeiro."
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
            "Aprendizado e Crescimento": diagnostic_result.learning,
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

            self._benchmarking_tool = BenchmarkingTool(llm=self.llm, retriever=retriever)
            logger.info("[DIAGNOSTIC] BenchmarkingTool inicializada (lazy loading)")

        # ========== GENERATE BENCHMARKS ==========

        try:
            report = self._benchmarking_tool.generate_benchmarks(
                company_info=client_profile.company,
                diagnostic=diagnostic_dict,
                kpi_framework=kpi_framework,
                use_rag=use_rag,
            )

            logger.info(
                f"[DIAGNOSTIC] Benchmark Report gerado: "
                f"{len(report.comparisons)} comparações, "
                f"performance={report.overall_performance}"
            )

        except Exception as e:
            logger.error(f"[DIAGNOSTIC] Erro ao gerar Benchmark Report: {e}")
            raise RuntimeError(f"Falha ao gerar Benchmark Report: {e!s}") from e

        # ========== SAVE TO MEMORY ==========

        try:
            self.memory_client.save_benchmark_report(client_id, report)
            logger.info(f"[DIAGNOSTIC] Benchmark Report salvo em memória (client_id={client_id})")
        except Exception as e:
            logger.warning(
                f"[DIAGNOSTIC] Erro ao salvar Benchmark Report em memória: {e}. "
                f"Report gerado mas não persistido."
            )

        return report
