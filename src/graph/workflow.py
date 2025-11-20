"""
LangGraph Workflow para Sistema Multi-Agente BSC.

Orquestra o fluxo completo:
1. Análise da query e roteamento
2. Execução paralela de agentes especialistas
3. Síntese de respostas
4. Avaliação com Judge Agent
5. Refinamento iterativo (se necessário)
6. Resposta final
"""

from __future__ import annotations

import asyncio
import sys
import time
import warnings
from typing import TYPE_CHECKING, Any, Literal

import nest_asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

# CRÍTICO: Aplicar nest_asyncio para permitir asyncio.run() dentro de event loops
# Necessário para Streamlit (já roda em event loop) chamar handlers async
nest_asyncio.apply()

# CRÍTICO: Configurar event loop policy para Windows (melhor gerenciamento SSL)
# ProactorEventLoop gerencia conexões SSL/HTTP de forma mais eficiente no Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Suprimir ResourceWarnings de SSL sockets/event loops (informativos, não críticos)
# Root cause: LangGraph usa ThreadPoolExecutor internamente, cada thread cria seu próprio loop
# Esses loops são gerenciados pelo LangGraph e fechados corretamente, mas warnings aparecem
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*ssl.SSLSocket")
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed transport")
warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed event loop")

from src.agents.judge_agent import JudgeAgent
from src.agents.orchestrator import Orchestrator
from src.graph.memory_nodes import load_client_memory, save_client_memory
from src.graph.states import AgentResponse, BSCState, JudgeEvaluation, PerspectiveType
from src.tools.strategy_map_designer import StrategyMapDesignerTool
from src.tools.alignment_validator import AlignmentValidatorTool

if TYPE_CHECKING:
    pass


def extract_text_from_response(response: Any) -> str:
    """
    Extrai texto de resposta de LLM de forma agnóstica (Claude ou OpenAI).

    Claude retorna lista de blocos: [{'text': '...', 'type': 'text'}, ...]
    OpenAI retorna string direta: "..."

    Args:
        response: Resposta do LLM (string ou lista)

    Returns:
        Texto extraído como string
    """
    if isinstance(response, list):
        # Claude format: lista de content blocks
        texts = []
        for block in response:
            if isinstance(block, dict):
                if (block.get("type") == "text" and "text" in block) or "text" in block:
                    texts.append(block["text"])
        return " ".join(texts) if texts else str(response)
    if isinstance(response, str):
        # OpenAI format: string direta
        return response
    # Fallback: converter para string
    return str(response)


class BSCWorkflow:
    """Workflow LangGraph para sistema BSC multi-agente."""

    def __init__(self):
        """Inicializa o workflow."""
        self.orchestrator = Orchestrator()
        self.judge = JudgeAgent()

        # FASE 2.10: Consulting orchestrator lazy loading (previne circular imports)
        self._consulting_orchestrator_cached = None

        # SPRINT 2: Strategy Map Design tools
        self.strategy_map_designer = StrategyMapDesignerTool()
        self.alignment_validator = AlignmentValidatorTool()

        self.graph = self._build_graph()

        logger.info("[OK] BSCWorkflow inicializado com grafo LangGraph")

    def _build_graph(self) -> CompiledStateGraph:
        """
        Constrói o grafo de execução LangGraph.

        Fluxo:
        START -> load_client_memory -> analyze_query -> execute_agents
        -> synthesize_response -> judge_validation -> decide_next
        -> [finalize OR execute_agents (refinement)] -> save_client_memory -> END
        """
        # Criar grafo com schema BSCState
        workflow = StateGraph(BSCState)

        # Adicionar nós (incluindo memória)
        workflow.add_node("load_client_memory", load_client_memory)

        # FASE 2.10: Consulting nodes
        workflow.add_node("onboarding", self.onboarding_handler)
        workflow.add_node("discovery", self.discovery_handler)
        workflow.add_node("approval", self.approval_handler)

        # RAG traditional nodes
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("execute_agents", self.execute_agents)
        workflow.add_node("synthesize_response", self.synthesize_response)
        workflow.add_node("judge_validation", self.judge_evaluation)
        workflow.add_node("finalize", self.finalize)

        workflow.add_node("save_client_memory", save_client_memory)

        # Definir entry point (começa com load de memória)
        workflow.set_entry_point("load_client_memory")

        # FASE 2.10: Routing condicional por fase consultiva
        # load_client_memory -> route_by_phase -> {onboarding, discovery, analyze_query}
        workflow.add_conditional_edges(
            "load_client_memory",
            self.route_by_phase,
            {
                "onboarding": "onboarding",
                "discovery": "discovery",
                "analyze_query": "analyze_query",
            },
        )

        # Consulting flows
        # onboarding -> save_client_memory -> END (multi-turn stateless)
        workflow.add_edge("onboarding", "save_client_memory")

        # discovery -> approval -> route_by_approval -> {end, discovery}
        workflow.add_edge("discovery", "approval")
        workflow.add_conditional_edges(
            "approval",
            self.route_by_approval,
            {"end": "save_client_memory", "discovery": "discovery"},  # Refazer diagnóstico
        )

        # RAG traditional flow (mantido intacto)
        workflow.add_edge("analyze_query", "execute_agents")
        workflow.add_edge("execute_agents", "synthesize_response")
        workflow.add_edge("synthesize_response", "judge_validation")

        # Edge condicional: judge_validation -> decide_next
        workflow.add_conditional_edges(
            "judge_validation",
            self.decide_next_step,
            {"finalize": "finalize", "refine": "execute_agents", "end": END},  # Loop de refinamento
        )

        # Edge final: finalize -> save_client_memory -> END
        workflow.add_edge("finalize", "save_client_memory")
        workflow.add_edge("save_client_memory", END)

        logger.info(
            "[OK] Grafo LangGraph construído: "
            "10 nodes (2 memória + 3 consulting + 5 RAG) + "
            "3 conditional edges (route_by_phase, route_by_approval, decide_next_step)"
        )

        # Adicionar checkpointer para persistir state entre turnos (CRITICAL para onboarding)
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    def analyze_query(self, state: BSCState) -> dict[str, Any]:
        """
        Nó 1: Analisa a query e determina roteamento.

        FASE 4.7: Se há diagnóstico aprovado, enriquece query com contexto das recomendações.

        Args:
            state: Estado atual do workflow

        Returns:
            Estado atualizado com perspectivas relevantes
        """
        start_time = time.time()
        try:
            # FASE 4.7: Enriquecer query com contexto do diagnóstico (se existir)
            enriched_query = self._enrich_query_with_diagnostic_context(state)

            logger.info(
                f"\n[TIMING] [analyze_query] INICIADO | "
                f"Query: '{state.query[:60]}...' | "
                f"Contexto diagnóstico: {enriched_query != state.query}"
            )

            # Usa Orchestrator para routing (com query enriquecida se houver diagnóstico)
            routing_decision = self.orchestrator.route_query(enriched_query)

            # Mapear nomes de agentes para PerspectiveType
            perspective_map = {
                "financeira": PerspectiveType.FINANCIAL,
                "cliente": PerspectiveType.CUSTOMER,
                "processos": PerspectiveType.PROCESS,
                "aprendizado": PerspectiveType.LEARNING,
            }

            relevant_perspectives = [
                perspective_map[agent_name]
                for agent_name in routing_decision.agents_to_use
                if agent_name in perspective_map
            ]

            # Determinar tipo e complexidade da query
            query_type = "general" if routing_decision.is_general_question else "specific"
            complexity = "complex" if len(relevant_perspectives) > 2 else "simple"

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [analyze_query] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"{len(relevant_perspectives)} perspectiva(s) | "
                f"Tipo: {query_type} | Complexidade: {complexity}"
            )

            result = {
                "relevant_perspectives": relevant_perspectives,
                "query_type": query_type,
                "complexity": complexity,
                "metadata": {**state.metadata, "routing_reasoning": routing_decision.reasoning},
            }

            # FASE 4.7: Se query foi enriquecida, armazenar para use nos agentes
            if enriched_query != state.query:
                result["metadata"]["enriched_query"] = enriched_query
                result["metadata"]["diagnostic_context_added"] = True

            return result

        except Exception as e:
            logger.error(f"[ERRO] analyze_query: {e}")
            # Fallback: aciona todas as perspectivas
            return {
                "relevant_perspectives": list(PerspectiveType),
                "query_type": "general",
                "complexity": "complex",
                "metadata": {"error": str(e)},
            }

    def execute_agents(self, state: BSCState) -> dict[str, Any]:
        """
        Nó 2: Executa agentes especialistas em paralelo.

        Args:
            state: Estado atual do workflow

        Returns:
            Estado atualizado com respostas dos agentes
        """
        start_time = time.time()
        try:
            iteration_label = ""
            if state.refinement_iteration > 0:
                iteration_label = f" (Refinamento #{state.refinement_iteration})"

            logger.info(
                f"[TIMING] [execute_agents] INICIADO{iteration_label} | "
                f"Perspectivas: {[p.value for p in state.relevant_perspectives]}"
            )

            # Mapear PerspectiveType de volta para nomes de agentes
            perspective_to_agent = {
                PerspectiveType.FINANCIAL: "financeira",
                PerspectiveType.CUSTOMER: "cliente",
                PerspectiveType.PROCESS: "processos",
                PerspectiveType.LEARNING: "aprendizado",
            }

            agent_names = [
                perspective_to_agent[p]
                for p in state.relevant_perspectives
                if p in perspective_to_agent
            ]

            # Validação defensiva: Se nenhum agente relevante, retornar resposta padrão
            if not agent_names:
                logger.warning(
                    f"[WARN] [execute_agents] Nenhuma perspectiva relevante identificada para query: '{state.query[:60]}...'"
                )
                elapsed_time = time.time() - start_time
                return {
                    "agent_responses": [],
                    "metadata": {
                        "execution_time": elapsed_time,
                        "warning": "Nenhuma perspectiva BSC relevante para esta query",
                    },
                }

            # FASE 4.7: Usar query enriquecida se disponível (diagnóstico aprovado)
            query_to_use = state.metadata.get("enriched_query", state.query)

            # Invocar agentes usando Orchestrator
            chat_history = state.metadata.get("chat_history", None)
            raw_responses = self.orchestrator.invoke_agents(
                query=query_to_use, agent_names=agent_names, chat_history=chat_history
            )

            # Converter para AgentResponse (modelo Pydantic)
            agent_responses = []
            for resp in raw_responses:
                # Extrair confidence dos intermediate_steps se disponível
                confidence = 0.8  # default

                # Mapear nome de perspectiva para PerspectiveType
                perspective_str = resp["perspective"].lower()
                perspective_map = {
                    "financeira": PerspectiveType.FINANCIAL,
                    "cliente": PerspectiveType.CUSTOMER,
                    "processos": PerspectiveType.PROCESS,
                    "aprendizado": PerspectiveType.LEARNING,
                    "financial": PerspectiveType.FINANCIAL,
                    "customer": PerspectiveType.CUSTOMER,
                    "process": PerspectiveType.PROCESS,
                    "learning": PerspectiveType.LEARNING,
                }

                perspective = perspective_map.get(perspective_str, PerspectiveType.FINANCIAL)

                # Extrair texto da resposta (compatível com Claude e OpenAI)
                response_text = extract_text_from_response(resp["response"])

                agent_responses.append(
                    AgentResponse(
                        perspective=perspective,
                        content=response_text,
                        confidence=confidence,
                        sources=[],  # TODO: extrair sources dos intermediate_steps
                        reasoning=f"Resposta do {resp['agent_name']}",
                    )
                )

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [execute_agents] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"Executados {len(agent_responses)} agente(s)"
            )

            return {"agent_responses": agent_responses}

        except Exception as e:
            logger.error(f"[ERRO] execute_agents: {e}")
            return {
                "agent_responses": [],
                "metadata": {**state.metadata, "execution_error": str(e)},
            }

    def synthesize_response(self, state: BSCState) -> dict[str, Any]:
        """
        Nó 3: Sintetiza respostas dos agentes em uma resposta unificada.

        Args:
            state: Estado atual do workflow

        Returns:
            Estado atualizado com resposta agregada
        """
        start_time = time.time()
        try:
            logger.info(
                f"[TIMING] [synthesize_response] INICIADO | "
                f"Sintetizando {len(state.agent_responses)} resposta(s)"
            )

            if not state.agent_responses:
                logger.warning("[WARN] Nenhuma resposta de agente para sintetizar")
                return {
                    "aggregated_response": "Nenhuma resposta foi gerada pelos agentes.",
                    "metadata": {**state.metadata, "synthesis_warning": "No agent responses"},
                }

            # Converter AgentResponse para formato esperado pelo Orchestrator
            agent_responses_dict: list[dict[str, Any]] = []
            for agent_resp in state.agent_responses:
                perspective_to_name = {
                    PerspectiveType.FINANCIAL: "Financial Agent",
                    PerspectiveType.CUSTOMER: "Customer Agent",
                    PerspectiveType.PROCESS: "Process Agent",
                    PerspectiveType.LEARNING: "Learning Agent",
                }

                agent_responses_dict.append(
                    {
                        "agent_name": perspective_to_name.get(
                            agent_resp.perspective, "Unknown Agent"
                        ),
                        "perspective": agent_resp.perspective.value,
                        "response": agent_resp.content,
                        "intermediate_steps": [],
                    }
                )

            # Usar Orchestrator para síntese
            synthesis = self.orchestrator.synthesize_responses(
                original_query=state.query, agent_responses=agent_responses_dict
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [synthesize_response] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"Confidence: {synthesis.confidence:.2f}"
            )

            return {
                "aggregated_response": synthesis.synthesized_answer,
                "metadata": {
                    **state.metadata,
                    "synthesis_confidence": synthesis.confidence,
                    "perspectives_covered": synthesis.perspectives_covered,
                },
            }

        except Exception as e:
            logger.error(f"[ERRO] synthesize_response: {e}")
            # Fallback: concatena respostas
            fallback = "\n\n".join(
                [
                    f"**{resp.perspective.value.title()}**:\n{resp.content}"
                    for resp in state.agent_responses
                ]
            )

            return {
                "aggregated_response": fallback,
                "metadata": {**state.metadata, "synthesis_error": str(e)},
            }

    def judge_evaluation(self, state: BSCState) -> dict[str, Any]:
        """
        Nó 4: Avalia qualidade da resposta com Judge Agent.

        Args:
            state: Estado atual do workflow

        Returns:
            Estado atualizado com avaliação do Judge
        """
        start_time = time.time()
        try:
            logger.info("[TIMING] [judge_validation] INICIADO | Avaliando resposta agregada")

            if not state.aggregated_response:
                logger.warning("[WARN] Nenhuma resposta agregada para avaliar")
                return {
                    "judge_evaluation": JudgeEvaluation(
                        approved=False,
                        score=0.0,
                        feedback="Nenhuma resposta foi gerada para avaliar.",
                        issues=["No aggregated response"],
                        suggestions=["Verifique execução dos agentes"],
                    ),
                    "needs_refinement": True,
                }

            # Usar Judge para avaliar
            # Nota: Judge.evaluate espera retrieved_documents, mas no nosso caso
            # os documentos já foram recuperados pelos agentes individuais
            judgment = self.judge.evaluate(
                original_query=state.query,
                agent_response=state.aggregated_response,
                retrieved_documents="[Documentos recuperados pelos agentes]",
                agent_name="Synthesized Response",
            )

            # Converter JudgmentResult para JudgeEvaluation
            approved = judgment.verdict == "approved"
            needs_refinement = (
                judgment.verdict != "approved"  # Refina para "needs_improvement" OU "rejected"
                and state.refinement_iteration < state.max_refinement_iterations
            )

            judge_evaluation = JudgeEvaluation(
                approved=approved,
                score=judgment.quality_score,
                feedback=judgment.reasoning,
                issues=judgment.issues,
                suggestions=judgment.suggestions,
                verdict=judgment.verdict,
                is_complete=judgment.is_complete,
                is_grounded=judgment.is_grounded,
                has_sources=judgment.has_sources,
            )

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TIMING] [judge_validation] CONCLUÍDO em {elapsed_time:.3f}s | "
                f"{'APROVADA' if approved else 'REPROVADA'} | "
                f"Score: {judgment.quality_score:.2f} | "
                f"Veredito: {judgment.verdict} | "
                f"Refinamento: {'SIM' if needs_refinement else 'NÃO'}"
            )

            # Preparar dict de retorno
            result_dict = {
                "judge_evaluation": judge_evaluation,
                "needs_refinement": needs_refinement,
            }

            # CRÍTICO: Incrementar contador de refinamento AQUI (nó retorna dict)
            # NÃO em decide_next_step (edge não persiste mutações!)
            if needs_refinement:
                result_dict["refinement_iteration"] = state.refinement_iteration + 1

            return result_dict

        except Exception as e:
            logger.error(f"[ERRO] judge_evaluation: {e}")
            # Em caso de erro, aprova para não travar o fluxo
            return {
                "judge_evaluation": JudgeEvaluation(
                    approved=True,
                    score=0.7,
                    feedback=f"Erro na avaliação: {e!s}. Aprovando por padrão.",
                    issues=[str(e)],
                    suggestions=["Revisar manualmente"],
                ),
                "needs_refinement": False,
                "metadata": {**state.metadata, "judge_error": str(e)},
            }

    def decide_next_step(self, state: BSCState) -> Literal["finalize", "refine", "end"]:
        """
        Edge condicional: Decide próximo passo após avaliação do Judge.

        Args:
            state: Estado atual do workflow

        Returns:
            Nome do próximo nó: "finalize", "refine", ou "end"
        """
        try:
            # Se não há avaliação, finaliza
            if not state.judge_evaluation:
                logger.info("[INFO] Decisão: FINALIZE (sem avaliação)")
                return "finalize"

            # Se aprovado, finaliza
            if state.judge_evaluation.approved:
                logger.info("[INFO] Decisão: FINALIZE (aprovado)")
                return "finalize"

            # Se precisa refinamento e ainda há iterações disponíveis, refina
            if state.needs_refinement:
                # Nota: O contador já foi incrementado em judge_evaluation()
                # Aqui apenas verificamos se ainda há iterações disponíveis
                if state.refinement_iteration <= state.max_refinement_iterations:
                    logger.info(
                        f"[INFO] Decisão: REFINE (iteração {state.refinement_iteration}/"
                        f"{state.max_refinement_iterations}) | "
                        f"Score: {state.judge_evaluation.score:.2f} | "
                        f"Verdict: {state.judge_evaluation.verdict}"
                    )
                    return "refine"
                logger.warning(
                    f"[WARN] Máximo de refinamentos atingido "
                    f"({state.max_refinement_iterations}). Finalizando."
                )
                return "finalize"

            # Caso padrão: finaliza (NÃO deveria chegar aqui se Judge rejeitou!)
            verdict = state.judge_evaluation.verdict if state.judge_evaluation else "N/A"
            score = state.judge_evaluation.score if state.judge_evaluation else 0.0
            logger.info(
                f"[INFO] Decisão: FINALIZE (padrão) | "
                f"needs_refinement={state.needs_refinement} | "
                f"Verdict: {verdict} | Score: {score:.2f}"
            )
            return "finalize"

        except Exception as e:
            logger.error(f"[ERRO] decide_next_step: {e}. Finalizando por segurança.")
            return "finalize"

    def finalize(self, state: BSCState) -> dict[str, Any]:
        """
        Nó 5: Finaliza o workflow e prepara resposta final.

        Args:
            state: Estado atual do workflow

        Returns:
            Estado atualizado com resposta final
        """
        try:
            logger.info("[INFO] Nó: finalize | Preparando resposta final")

            # Resposta final é a resposta agregada
            final_response = state.aggregated_response or "Não foi possível gerar uma resposta."

            # Adicionar aviso se foi reprovado mas finalizamos mesmo assim
            if state.judge_evaluation and not state.judge_evaluation.approved:
                warning = (
                    "\n\n---\n**[AVISO]** Esta resposta não atingiu o score de qualidade ideal. "
                    f"Score: {state.judge_evaluation.score:.2f}. "
                    f"Feedback: {state.judge_evaluation.feedback}"
                )
                final_response += warning

            logger.info(
                f"[OK] Workflow finalizado | "
                f"Perspectivas consultadas: {len(state.agent_responses)} | "
                f"Refinamentos: {state.refinement_iteration} | "
                f"Aprovado: {state.judge_evaluation.approved if state.judge_evaluation else 'N/A'}"
            )

            return {
                "final_response": final_response,
                "is_complete": True,
                "metadata": {
                    **state.metadata,
                    "total_refinements": state.refinement_iteration,
                    "final_score": state.judge_evaluation.score if state.judge_evaluation else 0.0,
                },
            }

        except Exception as e:
            logger.error(f"[ERRO] finalize: {e}")
            return {
                "final_response": state.aggregated_response or f"Erro ao finalizar: {e!s}",
                "is_complete": True,
                "metadata": {**state.metadata, "finalize_error": str(e)},
            }

    def route_by_approval(self, state: BSCState) -> Literal["end", "discovery"]:
        """
        FASE 2.8: Routing condicional baseado em approval_status.

        Decide próximo node baseado na decisão do cliente:
        - APPROVED -> END (ou SOLUTION_DESIGN futuro)
        - REJECTED / MODIFIED / TIMEOUT -> discovery (refazer)
        - PENDING (fallback) -> END

        Args:
            state: Estado com approval_status

        Returns:
            Nome do próximo node ("end" ou "discovery")
        """
        # Lazy import (evitar circular)
        from src.graph.consulting_states import ApprovalStatus

        approval_status = state.approval_status

        if approval_status == ApprovalStatus.APPROVED:
            logger.info("[INFO] [ROUTING] Aprovação APPROVED -> END")
            return "end"
        if approval_status in (
            ApprovalStatus.REJECTED,
            ApprovalStatus.MODIFIED,
            ApprovalStatus.TIMEOUT,
        ):
            logger.info(
                f"[INFO] [ROUTING] Aprovação {approval_status.value} -> discovery (refazer)"
            )
            return "discovery"
        # PENDING (ou None) -> END por design (fase futura pode reabrir)
        logger.info(
            f"[INFO] [ROUTING] Approval status PENDING/None detectado ({approval_status}). Encerrando por design."
        )
        return "end"

    def approval_handler(self, state: BSCState) -> dict[str, Any]:
        """
        FASE 2.8: Handler para aprovação humana do diagnóstico BSC.

        Processa aprovação/rejeição do diagnóstico pelo cliente.
        Single-turn: Cliente vê diagnóstico completo, aprova ou rejeita de uma vez.

        Args:
            state: Estado atual com diagnostic e approval_status mockado

        Returns:
            Estado atualizado com approval_status e approval_feedback

        Routing:
            - APPROVED -> END (ou SOLUTION_DESIGN futuro)
            - REJECTED -> discovery (refazer diagnóstico)
            - MODIFIED -> discovery (refazer com feedback)
        """
        # Lazy import (evitar circular)
        from src.graph.consulting_states import ApprovalStatus, ConsultingPhase

        try:
            logger.info("[INFO] [APPROVAL] Handler iniciado")

            # Validar se diagnostic existe
            if not state.diagnostic:
                logger.warning(
                    "[WARN] [APPROVAL] Diagnostic ausente. "
                    "Fallback para approval_status REJECTED"
                )
                return {
                    "approval_status": ApprovalStatus.REJECTED,
                    "approval_feedback": "Diagnóstico ausente ou incompleto. Por favor, execute a fase DISCOVERY novamente.",
                }

            # FASE 2.8 MVP: Aprovação mockada via state (testes)
            # Produção futura: interrupt() para input humano real
            approval_status = state.approval_status or ApprovalStatus.PENDING
            approval_feedback = state.approval_feedback or ""

            logger.info(
                f"[INFO] [APPROVAL] Status recebido: {approval_status.value} | "
                f"Feedback: {approval_feedback[:50] if approval_feedback else 'N/A'}..."
            )

            # FASE 4.5: Tentar coletar feedback opcional (não bloqueia workflow)
            # Feedback é coletado quando diagnóstico está completo e usuário interage
            # Por enquanto, feedback é coletado via API REST manualmente
            # Futuro: Integrar UI Streamlit com prompt de feedback após diagnóstico
            self._collect_feedback_after_diagnostic(state, approval_status)

            # Persistir decisão (save_client_memory sincroniza)
            return {
                "approval_status": approval_status,
                "approval_feedback": approval_feedback,
                "current_phase": ConsultingPhase.APPROVAL_PENDING,
            }

        except Exception as e:
            logger.error(f"[ERROR] [APPROVAL] Erro no handler: {e}")
            # Import aqui também para except
            from src.graph.consulting_states import ApprovalStatus

            return {
                "approval_status": ApprovalStatus.REJECTED,
                "approval_feedback": f"Erro durante aprovação: {e!s}",
                "metadata": {**state.metadata, "approval_error": str(e)},
            }

    # ============ FASE 2.10: PROPERTIES LAZY LOADING ============

    @property
    def consulting_orchestrator(self):
        """
        Lazy loading do ConsultingOrchestrator (previne circular imports).

        Returns:
            Instância cached do ConsultingOrchestrator
        """
        if self._consulting_orchestrator_cached is None:
            # Import local evita circular (workflow -> orchestrator -> agentes -> workflow)
            from src.graph.consulting_orchestrator import ConsultingOrchestrator

            self._consulting_orchestrator_cached = ConsultingOrchestrator()
            logger.info("[OK] ConsultingOrchestrator lazy loaded")
        return self._consulting_orchestrator_cached

    # ============ FASE 2.10: CONSULTING HANDLERS ============

    def onboarding_handler(self, state: BSCState) -> dict[str, Any]:
        """
        FASE 2.10: Handler de onboarding multi-turn.

        Integra ConsultingOrchestrator.coordinate_onboarding() no LangGraph.
        Gerencia sessões in-memory para workflow stateless.

        Args:
            state: Estado atual com user_id, query (mensagem usuário)

        Returns:
            Estado atualizado com onboarding_progress, client_profile (se completo)

        Routing:
            - is_complete=True -> Transição ONBOARDING -> DISCOVERY
            - is_complete=False -> Aguarda próxima mensagem usuário
        """
        import asyncio

        try:
            logger.info(
                f"[INFO] [ONBOARDING] Handler iniciado | "
                f"user_id={state.user_id} | query={state.query[:50]}..."
            )

            # Chamar método async - Python 3.12 compatible
            # Criar event loop se não existir (Streamlit ScriptRunner thread)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.consulting_orchestrator.coordinate_onboarding(state)
            )

            logger.info(
                f"[INFO] [ONBOARDING] Result: is_complete={result.get('is_complete', False)} | "
                f"next_action={result.get('next_action', 'N/A')}"
            )
            logger.info(
                "[ONBOARDING] ===== HANDLER RETORNANDO: current_phase=%s, previous_phase=%s, is_complete=%s =====",
                result.get("current_phase"),
                result.get("previous_phase"),
                result.get("is_complete"),
            )

            return result

        except Exception as e:
            logger.error(f"[ERROR] [ONBOARDING] Erro no handler: {e}")
            return self.consulting_orchestrator.handle_error(state, e, "ONBOARDING")

    def discovery_handler(self, state: BSCState) -> dict[str, Any]:
        """
        FASE 2.10: Handler de discovery (diagnóstico BSC).

        Integra ConsultingOrchestrator.coordinate_discovery() no LangGraph.
        Executa DiagnosticAgent.run_diagnostic() single-turn.

        FASE 4.6: Suporta refinement quando approval_status é REJECTED/MODIFIED.

        Args:
            state: Estado atual com client_profile (obrigatório)

        Returns:
            Estado atualizado com diagnostic (CompleteDiagnostic serializado)

        Routing:
            - diagnostic completo -> Transição DISCOVERY -> APPROVAL_PENDING
            - erro/profile ausente -> Fallback para ONBOARDING
            - refinement necessário -> Refina diagnóstico existente (FASE 4.6)
        """
        try:
            logger.info(
                f"[INFO] [DISCOVERY] Handler iniciado | "
                f"user_id={state.user_id} | has_profile={state.client_profile is not None}"
            )

            # FASE 4.6: Detectar se refinement é necessário
            from src.graph.consulting_states import ApprovalStatus

            needs_refinement = (
                state.diagnostic is not None
                and state.approval_status in (ApprovalStatus.REJECTED, ApprovalStatus.MODIFIED)
                and state.approval_feedback
                and state.approval_feedback.strip()
            )

            if needs_refinement:
                logger.info(
                    "[INFO] [DISCOVERY] [REFINEMENT] Refinement necessário baseado em feedback | "
                    f"approval_status={state.approval_status.value if hasattr(state.approval_status, 'value') else state.approval_status}"
                )
                # Delegar para coordinate_refinement
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                result = loop.run_until_complete(
                    self.consulting_orchestrator.coordinate_refinement(state)
                )
            else:
                # Discovery normal: criar diagnóstico novo
                logger.info("[INFO] [DISCOVERY] Discovery normal (criar novo diagnóstico)")
                # Delegar para ConsultingOrchestrator (ASYNC para paralelizar 4 agentes)
                # Python 3.12 compatible - criar loop se não existir
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                result = loop.run_until_complete(
                    self.consulting_orchestrator.coordinate_discovery(state)
                )

            # LOGS DEFENSIVOS: Rastrear estado do resultado
            logger.info("[DEBUG] [DISCOVERY] coordinate_discovery retornou:")
            logger.info(
                f"[DEBUG] [DISCOVERY]   - has_diagnostic: {result.get('diagnostic') is not None}"
            )
            logger.info(
                f"[DEBUG] [DISCOVERY]   - current_phase: {result.get('current_phase', 'N/A')}"
            )
            logger.info(
                f"[DEBUG] [DISCOVERY]   - final_response length: {len(result.get('final_response', ''))}"
            )
            logger.info(
                f"[DEBUG] [DISCOVERY]   - metadata keys: {list(result.get('metadata', {}).keys())}"
            )
            logger.info(
                f"[DEBUG] [DISCOVERY]   - use_rag_traditional: {result.get('metadata', {}).get('use_rag_traditional', False)}"
            )

            # IMPORTANTE: Detectar se coordinate_discovery sinalizou uso de RAG tradicional
            if result.get("metadata", {}).get("use_rag_traditional"):
                logger.info(
                    "[INFO] [DISCOVERY] RAG tradicional sinalizado. Delegando para rag_handler..."
                )
                # Chamar rag_handler diretamente
                return self.rag_handler(state)

            logger.info(
                f"[INFO] [DISCOVERY] Result: has_diagnostic={result.get('diagnostic') is not None} | "
                f"next_phase={result.get('current_phase', 'N/A')}"
            )

            return result

        except RuntimeError as e:
            # ERRO CRÍTICO: ThreadPoolExecutor shutdown (comum em Streamlit)
            # Evitar crash completo do workflow - fallback para ONBOARDING
            error_msg = str(e)
            logger.error(
                f"[ERROR] [DISCOVERY] RuntimeError (ThreadPoolExecutor shutdown): {error_msg} | "
                f"Fallback para ONBOARDING (permitir save_client_memory antes de retry)"
            )

            # Retornar para ONBOARDING para salvar profile (se existir)
            # Na próxima interação, usuário pode tentar discovery novamente
            return {
                "final_response": (
                    "Seu perfil foi criado com sucesso, mas não consegui completar o diagnóstico agora.\n\n"
                    "Por favor, faça uma nova pergunta sobre BSC para continuar."
                ),
                "current_phase": self._get_consulting_phase("ONBOARDING"),
                "metadata": {
                    **state.metadata,
                    "discovery_error": error_msg,
                    "discovery_error_type": "RuntimeError_ThreadPoolExecutor",
                },
            }

        except Exception as e:
            logger.error(f"[ERROR] [DISCOVERY] Erro no handler: {e}")
            return self.consulting_orchestrator.handle_error(state, e, "DISCOVERY")

    def _collect_feedback_after_diagnostic(self, state: BSCState, approval_status: Any) -> None:
        """
        FASE 4.5: Coleta opcional de feedback após diagnóstico completo.

        Este método é chamado após diagnóstico ser apresentado ao usuário.
        Feedback é opcional e não bloqueia o workflow se falhar.

        Por enquanto, feedback é coletado via API REST manualmente.
        Futuro: Integrar UI Streamlit com prompt de feedback após diagnóstico.

        Args:
            state: Estado atual com diagnostic completo
            approval_status: Status de aprovação (APPROVED, REJECTED, etc)
        """
        try:
            # Lazy import para evitar circular

            # Apenas tentar coletar feedback se diagnóstico existe e user_id disponível
            if not state.diagnostic or not state.user_id:
                logger.debug("[FEEDBACK] Feedback não coletado: diagnostic ou user_id ausente")
                return

            # Gerar diagnostic_id se não existir
            diagnostic_id = (
                state.metadata.get("diagnostic_id") or f"diag_{state.user_id}_{int(time.time())}"
            )

            # Por enquanto, feedback é coletado via API REST manualmente
            # Este método apenas prepara o sistema para coleta futura
            # Futuro: Quando UI Streamlit integrar prompt de feedback,
            # este método pode ser chamado automaticamente após diagnóstico

            logger.debug(
                "[FEEDBACK] Sistema pronto para coleta de feedback: "
                f"diagnostic_id={diagnostic_id}, user_id={state.user_id}, "
                f"approval_status={approval_status.value if hasattr(approval_status, 'value') else approval_status}"
            )

            # NOTA: Coleta real de feedback será feita via:
            # 1. API REST POST /api/v1/feedback (manual)
            # 2. UI Streamlit com prompt após diagnóstico (futuro)
            # Este método apenas registra que sistema está pronto para feedback

        except Exception as e:
            # Feedback é opcional - não falhar workflow se erro
            logger.warning(
                f"[WARN] [FEEDBACK] Erro ao preparar coleta de feedback (não crítico): {e}"
            )

    def _enrich_query_with_diagnostic_context(self, state: BSCState) -> str:
        """
        FASE 4.7: Enriquece query com contexto do diagnóstico aprovado.

        Quando usuário está em APPROVAL_PENDING e faz queries sobre implementação,
        adiciona contexto das recomendações específicas para RAG mais preciso.

        Exemplo:
        - Query original: "me ajude a implementar a recomendação 1"
        - Query enriquecida: "me ajude a implementar BSC enxuto com Strategy Map.
          Contexto: empresa Engelar, manufatura, 50 funcionários, meta 250 ton/mês.
          Recomendação: Desenhar Strategy Map e BSC enxuto (6-8 objetivos/KPIs)
          em 4 semanas conectando throughput a receita e margem."

        Args:
            state: Estado com diagnostic (opcional) e query

        Returns:
            Query original OU query enriquecida com contexto do diagnóstico
        """
        # Sem diagnóstico -> retornar query original
        if not state.diagnostic:
            return state.query

        try:
            diagnostic = state.diagnostic

            # Extrair contexto da empresa (se disponível via client_profile)
            company_context = ""
            if state.client_profile and state.client_profile.company:
                company = state.client_profile.company
                company_context = (
                    f"Empresa: {company.name}, "
                    f"Setor: {company.sector}, "
                    f"Porte: {company.size}"
                )

            # Extrair recomendações prioritárias (top 3 HIGH priority)
            recommendations = diagnostic.get("recommendations", [])
            if isinstance(recommendations, list) and recommendations:
                # Filtrar recomendações HIGH priority
                high_priority_recs = [
                    rec
                    for rec in recommendations[:5]  # Top 5 máximo
                    if isinstance(rec, dict) and rec.get("priority") == "HIGH"
                ]

                if high_priority_recs:
                    recs_context = "\n\nRecomendações prioritárias do diagnóstico BSC:\n"
                    for i, rec in enumerate(high_priority_recs[:3], 1):  # Top 3
                        title = rec.get("title", "N/A")
                        description = rec.get("description", "")[:150]  # Limitar tamanho
                        impact = rec.get("impact", "N/A")
                        recs_context += (
                            f"{i}. {title} (Impacto: {impact})\n" f"   {description}...\n"
                        )

                    # Enriquecer query
                    enriched_query = (
                        f"{state.query}\n\n" f"[CONTEXTO BSC] {company_context}" f"{recs_context}"
                    )

                    logger.info(
                        "[INFO] [CONTEXTO] Query enriquecida com diagnóstico | "
                        f"Recomendações: {len(high_priority_recs)}"
                    )

                    return enriched_query

            # Fallback: query original se não houver recomendações estruturadas
            logger.debug(
                "[DEBUG] [CONTEXTO] Diagnóstico sem recomendações HIGH priority estruturadas"
            )
            return state.query

        except Exception as e:
            logger.warning(
                f"[WARN] [CONTEXTO] Erro ao enriquecer query com diagnóstico (não crítico): {e}"
            )
            return state.query

    def route_by_phase(
        self, state: BSCState
    ) -> Literal["onboarding", "discovery", "analyze_query"]:
        """
        FASE 2.10: Routing function por fase consultiva.

        Decide próximo node baseado em current_phase:
        - ONBOARDING -> node 'onboarding' (processo multi-turn)
        - DISCOVERY -> node 'discovery' (diagnóstico BSC)
        - APPROVAL_PENDING -> node 'analyze_query' (RAG contextual com recomendações)
        - Outros (COMPLETED, ERROR, etc) -> node 'analyze_query' (RAG tradicional)

        Args:
            state: Estado atual com current_phase

        Returns:
            Nome do próximo node (string literal)
        """
        # Lazy import (evitar circular)
        from src.graph.consulting_states import ConsultingPhase

        phase = state.current_phase

        if phase == ConsultingPhase.ONBOARDING:
            logger.info("[INFO] [ROUTING] current_phase=ONBOARDING -> node='onboarding'")
            return "onboarding"

        if phase == ConsultingPhase.DISCOVERY:
            logger.info("[INFO] [ROUTING] current_phase=DISCOVERY -> node='discovery'")
            return "discovery"

        # FASE 4.7: APPROVAL_PENDING com diagnóstico aprovado -> RAG contextual
        if phase == ConsultingPhase.APPROVAL_PENDING:
            logger.info(
                "[INFO] [ROUTING] current_phase=APPROVAL_PENDING -> "
                "node='analyze_query' (RAG contextual com diagnóstico)"
            )
            return "analyze_query"

        # Fallback: RAG tradicional (COMPLETED, ERROR, None, etc)
        logger.info(
            f"[INFO] [ROUTING] current_phase={phase.value if phase else 'None'} -> "
            f"node='analyze_query' (RAG tradicional)"
        )
        return "analyze_query"

    def run(
        self,
        query: str,
        session_id: str = None,
        user_id: str = None,
        chat_history: list[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Executa o workflow completo para uma query.

        Args:
            query: Pergunta do usuário
            session_id: ID da sessão (opcional)
            user_id: ID do usuário/cliente para persistência de memória (opcional)
            chat_history: Histórico de conversa (opcional)

        Returns:
            Resultado completo com resposta final e metadados
        """
        workflow_start_time = time.time()
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"[TIMING] [WORKFLOW] INICIADO para query: '{query[:60]}...'")
            logger.info(f"{'='*80}\n")

            # CRÍTICO: Configuração com thread_id para checkpointer
            config = {"configurable": {"thread_id": session_id or "default"}}

            # Verificar se é primeira invocação ou turno subsequente
            # Para multi-turn: apenas passar campos NOVOS (query), não state completo!
            try:
                # Tentar obter state existente do checkpoint
                existing_state = self.graph.get_state(config)

                if existing_state and existing_state.values:
                    # Turno subsequente: passar apenas updates (não sobrescrever checkpoint!)
                    logger.info(
                        "[CHECKPOINT] Turno subsequente detectado (checkpoint existe) | "
                        "Atualizando apenas query e metadata"
                    )

                    # DEBUGGING: Log metadata do checkpoint
                    existing_metadata = existing_state.values.get("metadata", {})
                    logger.info(
                        "[CHECKPOINT] Metadata EXISTENTE no checkpoint: partial_profile=%s",
                        existing_metadata.get("partial_profile", "N/A"),
                    )

                    # Update apenas campos necessários para merge com checkpoint
                    update = {
                        "query": query,
                        "metadata": (
                            {**(existing_metadata), "chat_history": chat_history}
                            if chat_history
                            else existing_metadata
                        ),
                    }

                    logger.info(
                        "[CHECKPOINT] Update sendo enviado ao invoke: metadata keys=%s",
                        list(update.get("metadata", {}).keys()),
                    )

                    final_state = self.graph.invoke(update, config)

                    # DEBUGGING: Log do state após invoke
                    logger.info(
                        "[CHECKPOINT] State APÓS invoke: current_phase=%s, is_complete=%s, has_client_profile=%s",
                        (
                            final_state.get("current_phase")
                            if isinstance(final_state, dict)
                            else getattr(final_state, "current_phase", "N/A")
                        ),
                        (
                            final_state.get("is_complete")
                            if isinstance(final_state, dict)
                            else getattr(final_state, "is_complete", "N/A")
                        ),
                        (
                            (final_state.get("client_profile") is not None)
                            if isinstance(final_state, dict)
                            else (getattr(final_state, "client_profile", None) is not None)
                        ),
                    )
                else:
                    # Primeira invocação: criar state completo
                    logger.info(
                        "[CHECKPOINT] Primeira invocação (checkpoint vazio) | "
                        "Criando state inicial completo"
                    )

                    initial_state = BSCState(
                        query=query,
                        session_id=session_id,
                        user_id=user_id,
                        metadata={"chat_history": chat_history} if chat_history else {},
                    )

                    final_state = self.graph.invoke(initial_state, config)

            except Exception as e:
                # Fallback: se get_state falhar, assumir primeira invocação
                logger.warning(
                    f"[CHECKPOINT] Erro ao verificar checkpoint existente: {e} | "
                    "Assumindo primeira invocação"
                )

                initial_state = BSCState(
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    metadata={"chat_history": chat_history} if chat_history else {},
                )

                final_state = self.graph.invoke(initial_state, config)

            # Extrair resultado
            result = {
                "query": final_state["query"],
                "final_response": final_state.get("final_response", ""),
                "client_profile": final_state.get("client_profile"),
                "perspectives": [p.value for p in final_state.get("relevant_perspectives", [])],
                "agent_responses": [
                    {
                        "perspective": r.perspective.value,
                        "content": r.content,
                        "confidence": r.confidence,
                        "sources": r.sources,  # Campo omitido - Streamlit precisa!
                    }
                    for r in final_state.get("agent_responses", [])
                ],
                # Agregar retrieved_documents de todas as respostas dos agentes
                "retrieved_documents": [
                    doc for r in final_state.get("agent_responses", []) for doc in r.sources
                ],
                "judge_evaluation": (
                    final_state["judge_evaluation"].model_dump()
                    if final_state.get("judge_evaluation")
                    else None
                ),
                "refinement_iterations": final_state.get("refinement_iteration", 0),
                "metadata": final_state.get("metadata", {}),
            }

            # Adicionar judge_approved ao metadata top-level para E2E tests
            if final_state.get("judge_evaluation"):
                result["metadata"]["judge_approved"] = final_state["judge_evaluation"].approved

            # FASE 2.10: Adicionar current_phase, diagnostic e metadados consultivos
            result["current_phase"] = final_state.get("current_phase")
            result["diagnostic"] = final_state.get("diagnostic")
            result["previous_phase"] = final_state.get("previous_phase")
            result["phase_history"] = final_state.get("phase_history", [])
            result["is_complete"] = final_state.get("is_complete")

            workflow_elapsed_time = time.time() - workflow_start_time
            logger.info(f"\n{'='*80}")
            logger.info(
                f"[TIMING] [WORKFLOW] CONCLUÍDO em {workflow_elapsed_time:.3f}s "
                f"({workflow_elapsed_time/60:.2f} min)"
            )
            logger.info(f"{'='*80}\n")

            return result

        except Exception as e:
            logger.error(f"[ERRO] BSCWorkflow.run: {e}")
            return {
                "query": query,
                "final_response": f"Erro ao processar consulta: {e!s}",
                "perspectives": [],
                "agent_responses": [],
                "judge_evaluation": None,
                "refinement_iterations": 0,
                "metadata": {"error": str(e)},
            }

    def get_graph_visualization(self) -> str:
        """
        Retorna representação em texto do grafo (para debug).

        Returns:
            String com estrutura do grafo
        """
        viz = """
BSC LangGraph Workflow (com Memória Persistente):

START
  |
  v
load_client_memory (Carrega perfil do cliente do Mem0)
  |
  v
analyze_query (Analisa query e determina perspectivas relevantes)
  |
  v
execute_agents (Executa agentes especialistas em paralelo)
  |
  v
synthesize_response (Sintetiza respostas em resposta unificada)
  |
  v
judge_validation (Avalia qualidade com Judge Agent)
  |
  v
decide_next_step (Decisao condicional)
  |-- [approved] --> finalize
  |-- [needs_refinement] --> execute_agents (loop de refinamento)
  |-- [default] --> finalize
       |
       v
save_client_memory (Salva atualizações do perfil no Mem0)
       |
       v
     END

Caracteristicas:
- Memoria persistente com Mem0 Platform (ClientProfile)
- Refinamento iterativo (max 2 iteracoes)
- Execucao paralela de agentes
- Validacao rigorosa com Judge
- State management com Pydantic
"""
        return viz


# Singleton global para facilitar acesso
_workflow_instance = None


def get_workflow() -> BSCWorkflow:
    """
    Retorna instância singleton do workflow.

    Returns:
        Instância do BSCWorkflow
    """
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = BSCWorkflow()
    return _workflow_instance
