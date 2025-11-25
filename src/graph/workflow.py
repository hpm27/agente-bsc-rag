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
import atexit
import os
import sys
import time
import warnings
from typing import TYPE_CHECKING, Any, Literal

import nest_asyncio

# CORREÇÃO SESSAO 44 (2025-11-24): Usar AsyncSqliteSaver para suportar handlers async
# SqliteSaver é SYNC-ONLY e não suporta ainvoke() (NotImplementedError)
# AsyncSqliteSaver suporta ainvoke() necessário para handlers async (execute_agents, implementation_handler)
# SqliteSaver usado para operações sync (get_state, update_state) em chat_loader.py
# Pacote: pip install langgraph-checkpoint-sqlite aiosqlite
import sqlite3

import aiosqlite  # SESSAO 45: Para configurar PRAGMAs na conexão async

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
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

from src.agents.customer_agent import CustomerAgent
from src.agents.financial_agent import FinancialAgent
from src.agents.judge_agent import JudgeAgent
from src.agents.learning_agent import LearningAgent
from src.agents.orchestrator import Orchestrator
from src.agents.process_agent import ProcessAgent
from src.graph.memory_nodes import load_client_memory, save_client_memory
from src.graph.states import AgentResponse, BSCState, JudgeEvaluation, PerspectiveType
from src.tools.action_plan import ActionPlanTool
from src.tools.alignment_validator import AlignmentValidatorTool
from src.tools.cause_effect_mapper import CauseEffectMapperTool
from src.tools.kpi_alignment_checker import KPIAlignmentCheckerTool
from src.tools.milestone_tracker import MilestoneTrackerTool
from src.tools.strategy_map_designer import StrategyMapDesignerTool

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

        # SPRINT 2: Inicializar 4 specialist agents para Strategy Map Design
        self.financial_agent = FinancialAgent()
        self.customer_agent = CustomerAgent()
        self.process_agent = ProcessAgent()
        self.learning_agent = LearningAgent()

        # SPRINT 2: Strategy Map Design tools (passando os 4 agents)
        self.strategy_map_designer = StrategyMapDesignerTool(
            financial_agent=self.financial_agent,
            customer_agent=self.customer_agent,
            process_agent=self.process_agent,
            learning_agent=self.learning_agent,
        )
        self.alignment_validator = AlignmentValidatorTool()

        # SPRINT 3: Action Plan tool - SESSAO 45: LLM ferramentas (Claude Opus 4.5)
        from config.settings import get_llm_for_agent

        self.action_plan_tool = ActionPlanTool(llm=get_llm_for_agent("tools"))

        # SPRINT 3 - SESSAO 48: Validações Avançadas (KPI Alignment + Cause-Effect Mapping)
        # Estas ferramentas são executadas APÓS o AlignmentValidator para validações profundas
        self.kpi_alignment_checker = KPIAlignmentCheckerTool(llm=get_llm_for_agent("tools"))
        self.cause_effect_mapper = CauseEffectMapperTool(llm=get_llm_for_agent("tools"))
        self.milestone_tracker = MilestoneTrackerTool(llm=get_llm_for_agent("tools"))

        # SESSAO 44: Path do DB para checkpointer async
        self._checkpoint_db_path = "data/langgraph_checkpoints.db"
        os.makedirs(os.path.dirname(self._checkpoint_db_path), exist_ok=True)

        # CORREÇÃO SESSAO 45: Wrap inicialização em try-except para garantir cleanup em falha
        # PROBLEMA: Se setup(), _build_graph(), ou compile() falharem após criar conexão,
        #           a conexão SQLite fica aberta (dangling file lock) porque atexit.register()
        #           só é chamado no final do __init__
        # SOLUÇÃO: Registrar atexit ANTES de criar recursos, e fazer cleanup em exceção
        self._sqlite_conn = None  # Pré-inicializar para _cleanup_resources funcionar
        atexit.register(self._cleanup_resources)  # Registrar ANTES de criar recursos

        try:
            # SESSAO 44: Conexão SQLite sync para operações get_state/update_state (chat_loader.py)
            # check_same_thread=False necessário para Streamlit (múltiplas threads)
            self._sqlite_conn = sqlite3.connect(self._checkpoint_db_path, check_same_thread=False)

            # CORREÇÃO SESSAO 45: Habilitar WAL mode para permitir concorrência sync/async
            # PROBLEMA: Duas conexões ao mesmo DB (sync persistente + async por ainvoke())
            #           podem causar "database is locked" sem WAL mode
            # SOLUÇÃO: WAL (Write-Ahead Logging) permite:
            #          - Um writer + múltiplos readers simultâneos
            #          - Leituras não bloqueiam escritas
            #          - Melhor performance para padrão read-heavy (get_state frequente)
            # Fonte: SQLite WAL mode documentation, LangGraph Checkpointer best practices
            self._sqlite_conn.execute("PRAGMA journal_mode=WAL;")
            self._sqlite_conn.execute("PRAGMA busy_timeout=5000;")  # 5s timeout para locks
            self._sqlite_conn.commit()  # CORREÇÃO SESSAO 45: Commit para garantir PRAGMA persista

            self._sync_checkpointer = SqliteSaver(self._sqlite_conn)

            # CORREÇÃO SESSAO 45: Inicializar tabelas SQLite ANTES de usar o checkpointer
            # Sem setup(), chat_loader.py falha com "table not found" ao chamar get_state()
            # ANTES de qualquer ainvoke() (que inicializa o async checkpointer separadamente)
            self._sync_checkpointer.setup()

            # SESSAO 44: Armazenar workflow builder E graph compilado (sem checkpointer)
            # workflow_builder: usado para recompilar com checkpointer em ainvoke()
            # graph: usado para chamadas que não precisam de persistência
            self._workflow_builder, self.graph = self._build_graph()

            # SESSAO 44: Graph com checkpointer sync para operações get_state/update_state
            # Usado por chat_loader.py e outras funções que precisam acessar checkpoints
            self._graph_with_checkpointer = self._workflow_builder.compile(
                checkpointer=self._sync_checkpointer
            )

        except Exception as e:
            # CORREÇÃO SESSAO 45: Cleanup em caso de falha na inicialização
            # Previne dangling file lock se setup/build_graph/compile falharem
            logger.error(f"[ERROR] Falha na inicialização do BSCWorkflow: {e}")
            self._cleanup_resources()
            raise  # Re-raise para caller saber que inicialização falhou

        logger.info("[OK] BSCWorkflow inicializado com grafo LangGraph")

    def get_graph_with_checkpointer(self) -> CompiledStateGraph:
        """
        Retorna graph compilado COM checkpointer sync para operações get_state/update_state.

        SESSAO 44 (2025-11-24): Necessário para chat_loader.py e outras funções que
        precisam acessar checkpoints de forma síncrona (get_state, update_state).

        Usa SqliteSaver (sync) compartilhando o mesmo arquivo DB do AsyncSqliteSaver.

        Returns:
            CompiledStateGraph com SqliteSaver checkpointer
        """
        return self._graph_with_checkpointer

    def _cleanup_resources(self) -> None:
        """
        Cleanup interno de recursos (SQLite connection).

        SESSAO 45 (2025-11-25): Previne resource leak da conexão SQLite.
        Chamado por: atexit handler, close(), __del__

        Idempotente - pode ser chamado múltiplas vezes sem efeito.
        """
        if hasattr(self, "_sqlite_conn") and self._sqlite_conn is not None:
            try:
                self._sqlite_conn.close()
                self._sqlite_conn = None
                logger.debug("[CLEANUP] SQLite connection fechada com sucesso")
            except Exception as e:
                # Silenciar erros no cleanup (pode estar em shutdown)
                logger.debug(f"[CLEANUP] Erro ao fechar SQLite connection: {e}")

    def close(self) -> None:
        """
        Fecha recursos do workflow explicitamente.

        SESSAO 45 (2025-11-25): Método público para fechamento programático.
        Usar quando o workflow não será mais utilizado.

        Exemplo:
            workflow = BSCWorkflow()
            try:
                result = await workflow.ainvoke(state, config)
            finally:
                workflow.close()
        """
        self._cleanup_resources()

    def __del__(self):
        """
        Fallback cleanup quando objeto é garbage collected.

        SESSAO 45 (2025-11-25): Última linha de defesa contra resource leak.
        Não é garantido ser chamado (Python GC não garante __del__),
        mas serve como fallback. atexit é mais confiável.
        """
        self._cleanup_resources()

    async def ainvoke(self, state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """
        Executa o workflow de forma assíncrona com checkpointer persistente.

        CORREÇÃO SESSAO 44 (2025-11-24):
        - Handlers async (execute_agents, implementation_handler) requerem ainvoke()
        - ainvoke() requer checkpointer async (AsyncSqliteSaver)
        - AsyncSqliteSaver precisa ser criado em contexto async
        - Checkpointer DEVE ser passado em compile(), não em config!
        - Solução: Usar from_conn_string como context manager e recompilar graph
        - Fonte: Medium "LangGraph + FastAPI + AsyncSqliteSaver" (Jun 2025)

        Args:
            state: Estado inicial do workflow
            config: Configuração incluindo thread_id

        Returns:
            Estado final após execução do workflow
        """
        # CORREÇÃO SESSAO 45: Configurar WAL mode e busy_timeout na conexão async
        # PROBLEMA: AsyncSqliteSaver.from_conn_string() cria conexão nova que não herda
        #           PRAGMAs da conexão sync (WAL mode, busy_timeout)
        # SOLUÇÃO: Usar aiosqlite diretamente para configurar PRAGMAs antes de usar
        # Fonte: SQLite docs - PRAGMA settings são per-connection
        async with aiosqlite.connect(self._checkpoint_db_path) as pragma_conn:
            # Aplicar mesmas configurações da conexão sync
            await pragma_conn.execute("PRAGMA journal_mode=WAL;")
            await pragma_conn.execute("PRAGMA busy_timeout=5000;")
            await pragma_conn.commit()

        # Usar from_conn_string como context manager (pattern validado Jun 2025)
        # Checkpointer DEVE ser passado em compile(), não em config runtime!
        async with AsyncSqliteSaver.from_conn_string(self._checkpoint_db_path) as checkpointer:
            # CORREÇÃO SESSAO 45: Inicializar tabelas SQLite antes de usar checkpointer
            # Sem setup(), primeira execução falha com "table not found"
            await checkpointer.setup()

            # Recompilar graph COM checkpointer (necessário para LangGraph)
            compiled_graph = self._workflow_builder.compile(checkpointer=checkpointer)

            # Executar workflow async
            result = await compiled_graph.ainvoke(state, config=config)

            # CORREÇÃO SESSAO 45: Garantir que todas operações IO completaram
            # PROBLEMA: Context manager pode fechar conexão antes de writes pendentes
            # SOLUÇÃO: await asyncio.sleep(0) força yield para event loop processar
            #          todas tasks pendentes antes de sair do context manager
            # Fonte: Python asyncio docs - "Yield to event loop"
            await asyncio.sleep(0)

            return result

    def _build_graph(self) -> tuple[StateGraph, CompiledStateGraph]:
        """
        Constrói o grafo de execução LangGraph.

        SESSAO 44: Retorna tuple (workflow_builder, compiled_graph)
        - workflow_builder: StateGraph não compilado, usado para recompilar com checkpointer
        - compiled_graph: Graph compilado sem checkpointer, para uso básico

        Fluxo:
        START -> load_client_memory -> analyze_query -> execute_agents
        -> synthesize_response -> judge_validation -> decide_next
        -> [finalize OR execute_agents (refinement)] -> save_client_memory -> END

        Returns:
            Tuple[StateGraph, CompiledStateGraph]: workflow builder e graph compilado
        """
        # Criar grafo com schema BSCState
        workflow = StateGraph(BSCState)

        # Adicionar nós (incluindo memória)
        workflow.add_node("load_client_memory", load_client_memory)

        # FASE 2.10: Consulting nodes
        workflow.add_node("onboarding", self.onboarding_handler)
        workflow.add_node("discovery", self.discovery_handler)
        workflow.add_node("approval", self.approval_handler)

        # SPRINT 2: Solution Design node
        workflow.add_node("design_solution", self.design_solution_handler)

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

        # discovery -> approval -> route_by_approval -> {design_solution, discovery, END}
        workflow.add_edge("discovery", "approval")
        workflow.add_conditional_edges(
            "approval",
            self.route_by_approval,
            {
                "design_solution": "design_solution",  # APPROVED -> criar Strategy Map
                "discovery": "discovery",  # REJECTED -> refazer diagnóstico
                "end": END,  # PENDING -> aguardar input humano
            },
        )

        # SPRINT 2+3: design_solution -> route_by_alignment_score -> {implementation, discovery}
        workflow.add_node("implementation", self.implementation_handler)
        workflow.add_conditional_edges(
            "design_solution",
            self.route_by_alignment_score,
            {"implementation": "implementation", "discovery": "discovery"},
        )

        # implementation -> save_client_memory -> END
        workflow.add_edge("implementation", "save_client_memory")

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

        # CORREÇÃO SESSAO 44 (2025-11-24): Retornar workflow builder + graph compilado
        # - workflow: StateGraph não compilado, para recompilar com checkpointer em ainvoke()
        # - compiled: Graph compilado sem checkpointer, para uso básico/fallback
        # Checkpointer DEVE ser passado em compile(), não em config runtime!
        # Fonte: Medium "LangGraph + FastAPI + AsyncSqliteSaver" (Jun 2025)
        return workflow, workflow.compile()

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

    async def execute_agents(self, state: BSCState) -> dict[str, Any]:
        """
        Nó 2: Executa agentes especialistas em paralelo COM RAG.
        IMPORTANTE: Async para usar ainvoke_agents() que faz retrieval RAG.

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

            # SESSAO 47: FEEDBACK LOOP - Enriquecer query com feedback do Judge no refinamento
            # Pattern: Reflexion (LangChain best practice) - feedback estruturado e grounded
            if state.refinement_iteration > 0 and state.judge_evaluation:
                judge = state.judge_evaluation

                # Formatar issues como lista
                issues_text = ""
                if judge.issues:
                    issues_text = "\n".join(f"  - {issue}" for issue in judge.issues)
                else:
                    issues_text = "  - Nenhum problema especifico listado"

                # Formatar suggestions como lista
                suggestions_text = ""
                if judge.suggestions:
                    suggestions_text = "\n".join(f"  - {sug}" for sug in judge.suggestions)
                else:
                    suggestions_text = "  - Nenhuma sugestao especifica"

                refinement_context = f"""
=== REFINAMENTO #{state.refinement_iteration} - FEEDBACK DO JUDGE ===

[SCORE ANTERIOR]: {judge.score:.2f} (minimo para aprovacao: 0.85)

[PROBLEMAS IDENTIFICADOS]:
{issues_text}

[SUGESTOES DE MELHORIA]:
{suggestions_text}

[FEEDBACK COMPLETO]:
{judge.feedback}

=== INSTRUCAO ===
Ao responder a query abaixo, FOQUE nas melhorias indicadas acima.
Enderece especificamente os problemas identificados e siga as sugestoes.
=================

"""
                query_to_use = refinement_context + query_to_use

                logger.info(
                    f"[FEEDBACK] [execute_agents] Refinamento #{state.refinement_iteration} | "
                    f"Score anterior: {judge.score:.2f} | "
                    f"Issues: {len(judge.issues) if judge.issues else 0} | "
                    f"Suggestions: {len(judge.suggestions) if judge.suggestions else 0}"
                )

            # Invocar agentes usando Orchestrator ASYNC (COM RAG!)
            chat_history = state.metadata.get("chat_history", None)
            raw_responses = await self.orchestrator.ainvoke_agents(
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

    def route_by_approval(self, state: BSCState) -> Literal["design_solution", "discovery", "end"]:
        """
        FASE 2.8: Routing condicional baseado em approval_status.

        Decide próximo node baseado na decisão do cliente:
        - APPROVED -> design_solution (criar Strategy Map)
        - REJECTED / MODIFIED / TIMEOUT -> discovery (refazer)
        - PENDING (fallback) -> end (aguardar input humano)
        - ERROR (fase) -> end (impedir loop infinito)

        Args:
            state: Estado com approval_status

        Returns:
            Nome do próximo node ("design_solution", "discovery" ou "end")
        """
        # Lazy import (evitar circular)
        from src.graph.consulting_states import ApprovalStatus, ConsultingPhase

        # CORRECAO SESSAO 45: Verificar se estamos em fase de ERRO antes de qualquer routing
        # PROBLEMA: Se discovery falha (timeout), approval_handler define REJECTED,
        #           route_by_approval manda para discovery novamente -> LOOP INFINITO
        # SOLUÇÃO: Se current_phase == ERROR, ir para END (não tentar refazer)
        if state.current_phase == ConsultingPhase.ERROR:
            logger.warning(
                "[WARN] [ROUTING] current_phase=ERROR detectado. "
                "Encerrando workflow para evitar loop infinito."
            )
            return "end"

        approval_status = state.approval_status

        # CORREÇÃO SESSAO 46: Verificar APPROVED ANTES de discovery_attempts
        # PROBLEMA: Diagnóstico aprovado (score 0.92) estava sendo bloqueado por
        #           discovery_attempts >= max_discovery_attempts (2 >= 2)
        # SOLUÇÃO: Se APPROVED, ir para design_solution INDEPENDENTE de discovery_attempts
        if approval_status == ApprovalStatus.APPROVED:
            logger.info(
                "[INFO] [ROUTING] Aprovação APPROVED -> design_solution (criar Strategy Map)"
            )
            return "design_solution"

        # CORREÇÃO SESSAO 45/46: Verificar discovery_attempts APENAS se for refazer discovery
        # Isso evita loop infinito quando REJECTED/MODIFIED/TIMEOUT mas permite APPROVED prosseguir
        if approval_status in (
            ApprovalStatus.REJECTED,
            ApprovalStatus.MODIFIED,
            ApprovalStatus.TIMEOUT,
        ):
            # Verificar se pode tentar novamente
            # NOTA: Usa >= porque discovery_attempts ja foi incrementado APOS a tentativa
            # (o handler salva discovery_attempts=N apos executar a N-esima tentativa)
            # Com max=2: apos 1a tentativa (1>=2=F->retry), apos 2a tentativa (2>=2=T->end)
            # Resultado: permite exatamente max_discovery_attempts tentativas
            # Ver tambem: discovery_handler linha ~1776 usa > com current_attempts (valor futuro)
            if state.discovery_attempts >= state.max_discovery_attempts:
                logger.warning(
                    f"[WARN] [ROUTING] discovery_attempts ({state.discovery_attempts}) >= "
                    f"max ({state.max_discovery_attempts}) com status {approval_status.value}. "
                    "Encerrando workflow para evitar loop infinito."
                )
                return "end"

            logger.info(
                f"[INFO] [ROUTING] Aprovação {approval_status.value} -> discovery (refazer) | "
                f"attempt={state.discovery_attempts}/{state.max_discovery_attempts}"
            )
            return "discovery"
        # PENDING (ou None) -> END por design (aguardar input humano via UI futura)
        logger.info(
            f"[INFO] [ROUTING] Approval status PENDING/None detectado ({approval_status}). "
            "Encerrando workflow (aguardar input humano)."
        )
        return "end"

    def route_by_alignment_score(self, state: BSCState) -> Literal["implementation", "discovery"]:
        """
        SPRINT 2 - Tarefa 2.4: Routing condicional baseado em alignment score.

        Decide próximo node baseado no score de alinhamento do Strategy Map:
        - score >= 70 -> implementation (strategy map validado, criar plano de ação)
        - score < 70 -> discovery (refazer diagnóstico considerando gaps)

        Args:
            state: Estado com alignment_report contendo score

        Returns:
            Nome do próximo node ("implementation" ou "discovery")
        """
        try:
            # Validar se alignment_report existe
            if not state.alignment_report:
                logger.warning(
                    "[WARN] [ROUTING] alignment_report ausente. "
                    "Fallback para discovery (refazer diagnóstico)."
                )
                return "discovery"

            score = state.alignment_report.score
            threshold = 70  # Threshold reduzido para aceitar Strategy Maps com warnings (SESSAO 40)

            if score >= threshold:
                next_node = "implementation"
                logger.info(f"[OK] [ROUTING] alignment_score={score} >= {threshold} -> {next_node}")
            else:
                next_node = "discovery"
                logger.info(
                    f"[WARN] [ROUTING] alignment_score={score} < {threshold} -> {next_node} "
                    f"(gaps={len(state.alignment_report.gaps)} identificados)"
                )

            return next_node

        except Exception as e:
            logger.error(
                f"[ERROR] [ROUTING] Erro ao decidir routing por alignment score: {e}. "
                "Fallback para discovery."
            )
            return "discovery"

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

            # FASE 2.8 MVP: Aprovação automática baseada em Judge (ou manual via state)
            # Se state já tem approval_status (input humano via UI), usar esse
            # Se não, usar avaliação do Judge automaticamente
            approval_status = state.approval_status
            approval_feedback = state.approval_feedback or ""

            # Se aprovação ainda PENDING e Judge já avaliou, usar avaliação do Judge
            if approval_status in (None, ApprovalStatus.PENDING):
                # Extrair avaliação do Judge do diagnostic metadata
                judge_evaluation = None
                if state.diagnostic and isinstance(state.diagnostic, dict):
                    judge_evaluation = state.diagnostic.get("metadata", {}).get("judge_evaluation")

                if judge_evaluation:
                    judge_verdict = judge_evaluation.get("verdict", "").lower()
                    judge_score = judge_evaluation.get("quality_score", 0.0)

                    # Aprovar automaticamente se Judge aprovou
                    if judge_verdict == "approved" and judge_score >= 0.7:
                        approval_status = ApprovalStatus.APPROVED
                        approval_feedback = (
                            f"Diagnóstico aprovado automaticamente pelo Judge Agent "
                            f"(score: {judge_score:.2f}). Prosseguindo para design de Strategy Map."
                        )
                        logger.info(
                            f"[INFO] [APPROVAL] Aprovação AUTOMÁTICA via Judge | "
                            f"Score: {judge_score:.2f} | Verdict: {judge_verdict}"
                        )
                    else:
                        # Rejeitar se score baixo ou verdict negativo
                        approval_status = ApprovalStatus.REJECTED
                        approval_feedback = (
                            f"Diagnóstico rejeitado automaticamente (score: {judge_score:.2f}, "
                            f"verdict: {judge_verdict}). Refinamento necessário."
                        )
                        logger.warning(
                            f"[WARN] [APPROVAL] Diagnóstico REJEITADO via Judge | "
                            f"Score: {judge_score:.2f} | Verdict: {judge_verdict}"
                        )
                else:
                    # Fallback: sem Judge, manter PENDING (aguardar input humano)
                    approval_status = ApprovalStatus.PENDING
                    logger.warning(
                        "[WARN] [APPROVAL] Judge evaluation ausente. "
                        "Mantendo PENDING (aguardar input humano)"
                    )

            logger.info(
                f"[INFO] [APPROVAL] Status final: {approval_status.value} | "
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

    def design_solution_handler(self, state: BSCState) -> dict[str, Any]:
        """
        SPRINT 2 - Tarefa 2.4: Handler para design do Strategy Map BSC.

        Orquestra StrategyMapDesignerTool + AlignmentValidatorTool para criar
        Strategy Map visual estruturado baseado no diagnóstico aprovado.

        STEPS:
        1. Validar diagnostic existe e está approved
        2. Converter diagnostic dict -> CompleteDiagnostic Pydantic
        3. Chamar StrategyMapDesignerTool.design_strategy_map() (async)
        4. Chamar AlignmentValidatorTool.validate_strategy_map() (sync)
        5. Retornar strategy_map + alignment_report no state
        6. Routing condicional baseado em alignment_report.score

        Args:
            state: Estado atual com diagnostic e approval_status=APPROVED

        Returns:
            Estado atualizado com strategy_map, alignment_report, final_response

        Routing:
            - score >= 70 -> IMPLEMENTATION (strategy map validado)
            - score < 70 -> DISCOVERY (precisa refazer diagnóstico - gaps críticos)
        """
        # Lazy import (evitar circular)
        from src.graph.consulting_states import ApprovalStatus, ConsultingPhase
        from src.memory.schemas import CompleteDiagnostic, DiagnosticToolsResult

        try:
            logger.info("[START] [SOLUTION_DESIGN] Handler iniciado")
            start_time = time.time()

            # ========== STEP 1: Validações iniciais ==========

            # Validar se diagnostic existe
            if not state.diagnostic:
                logger.error(
                    "[ERROR] [SOLUTION_DESIGN] Diagnostic ausente. "
                    "Não é possível criar Strategy Map."
                )
                return {
                    "final_response": (
                        "Erro: Diagnóstico ausente. "
                        "Execute a fase DISCOVERY primeiro para criar o diagnóstico BSC."
                    ),
                    "current_phase": ConsultingPhase.DISCOVERY,
                    "metadata": {**state.metadata, "solution_design_error": "diagnostic_missing"},
                }

            # Validar se aprovação foi concedida
            if state.approval_status != ApprovalStatus.APPROVED:
                logger.warning(
                    f"[WARN] [SOLUTION_DESIGN] Diagnostic não aprovado (status: {state.approval_status}). "
                    "Strategy Map NÃO será criado."
                )
                return {
                    "final_response": (
                        f"Diagnóstico com status '{state.approval_status.value}'. "
                        "Aprove o diagnóstico primeiro para criar o Strategy Map."
                    ),
                    "current_phase": ConsultingPhase.APPROVAL_PENDING,
                    "metadata": {
                        **state.metadata,
                        "solution_design_error": "diagnostic_not_approved",
                    },
                }

            logger.info("[OK] [SOLUTION_DESIGN] Validações iniciais passaram")

            # ========== STEP 2: Converter diagnostic dict -> Pydantic ==========

            try:
                diagnostic_pydantic = CompleteDiagnostic(**state.diagnostic)
                logger.info(
                    f"[OK] [SOLUTION_DESIGN] Diagnostic convertido para Pydantic | "
                    f"has_executive_summary={diagnostic_pydantic.executive_summary is not None} | "
                    f"num_recommendations={len(diagnostic_pydantic.recommendations) if diagnostic_pydantic.recommendations else 0}"
                )
            except Exception as e:
                logger.error(
                    f"[ERROR] [SOLUTION_DESIGN] Falha ao converter diagnostic para Pydantic: {e}"
                )
                return {
                    "final_response": (
                        f"Erro ao processar diagnóstico: {e}. "
                        "Por favor, refaça o diagnóstico na fase DISCOVERY."
                    ),
                    "current_phase": ConsultingPhase.DISCOVERY,
                    "metadata": {
                        **state.metadata,
                        "solution_design_error": f"pydantic_conversion_failed: {e}",
                    },
                }

            # ========== STEP 3: Extrair tool_outputs se disponível ==========

            tools_results = None
            if state.tool_outputs:
                try:
                    # Tentar converter tool_outputs dict -> DiagnosticToolsResult Pydantic
                    tools_results = DiagnosticToolsResult(**state.tool_outputs)
                    logger.info(
                        f"[OK] [SOLUTION_DESIGN] Tools results disponíveis | "
                        f"swot={tools_results.swot_analysis is not None} | "
                        f"kpis={tools_results.kpi_definitions is not None} | "
                        f"objectives={tools_results.strategic_objectives is not None}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[WARN] [SOLUTION_DESIGN] Falha ao converter tool_outputs: {e}. "
                        "Continuando sem tools_results..."
                    )
                    tools_results = None

            # ========== STEP 4: Chamar StrategyMapDesignerTool (ASYNC) ==========

            logger.info("[INFO] [SOLUTION_DESIGN] Iniciando design do Strategy Map...")
            design_start = time.time()  # SESSAO 48 FIX: Track phase start timestamp

            try:
                # CORREÇÃO SESSAO 43 (2025-11-24): Executar sempre, não apenas no except
                # Python 3.12 compatible - usar loop existente ou criar novo
                try:
                    loop = asyncio.get_running_loop()
                    # CORREÇÃO: Se loop existe (Streamlit + nest_asyncio), usar run_until_complete
                    strategy_map = loop.run_until_complete(
                        self.strategy_map_designer.design_strategy_map(
                            diagnostic=diagnostic_pydantic,
                            client_profile=state.client_profile,
                            tools_results=tools_results,
                        )
                    )
                except RuntimeError:
                    # Sem running loop - criar novo
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        strategy_map = loop.run_until_complete(
                            self.strategy_map_designer.design_strategy_map(
                                diagnostic=diagnostic_pydantic,
                                client_profile=state.client_profile,
                                tools_results=tools_results,
                            )
                        )
                    finally:
                        loop.close()  # Previne resource leak

                design_time = time.time() - design_start  # SESSAO 48 FIX: Duration from phase start
                logger.info(
                    f"[OK] [SOLUTION_DESIGN] Strategy Map criado em {design_time:.2f}s | "
                    f"perspectives: Financial={len(strategy_map.financial.objectives)} objs, "
                    f"Customer={len(strategy_map.customer.objectives)} objs, "
                    f"Process={len(strategy_map.process.objectives)} objs, "
                    f"Learning={len(strategy_map.learning.objectives)} objs | "
                    f"connections={len(strategy_map.cause_effect_connections)}"
                )

            except Exception as e:
                logger.error(f"[ERROR] [SOLUTION_DESIGN] Falha ao criar Strategy Map: {e}")
                return {
                    "final_response": (
                        f"Erro ao criar Strategy Map: {e}. "
                        "Por favor, tente novamente ou refaça o diagnóstico."
                    ),
                    "current_phase": ConsultingPhase.SOLUTION_DESIGN,
                    "metadata": {
                        **state.metadata,
                        "solution_design_error": f"strategy_map_creation_failed: {e}",
                    },
                }

            # ========== STEP 5: Chamar AlignmentValidatorTool (SYNC) ==========

            logger.info("[INFO] [SOLUTION_DESIGN] Iniciando validação de alinhamento...")
            validation_start = time.time()  # SESSAO 48 FIX: Track phase start timestamp
            validation_time = 0.0  # SESSAO 49 FIX: Inicializar para evitar NameError se exceção

            try:
                alignment_report = self.alignment_validator.validate_strategy_map(
                    strategy_map=strategy_map
                )

                validation_time = (
                    time.time() - validation_start
                )  # SESSAO 48 FIX: Duration from phase start
                logger.info(
                    f"[OK] [SOLUTION_DESIGN] Validação completa em {validation_time:.2f}s | "
                    f"score={alignment_report.score}/100 | "
                    f"is_balanced={alignment_report.is_balanced} | "
                    f"gaps={len(alignment_report.gaps)} | "
                    f"warnings={len(alignment_report.warnings)}"
                )

            except Exception as e:
                logger.error(f"[ERROR] [SOLUTION_DESIGN] Falha ao validar Strategy Map: {e}")
                return {
                    "final_response": (
                        f"Strategy Map criado, mas falhou validação: {e}. "
                        "Por favor, tente novamente."
                    ),
                    "strategy_map": strategy_map,  # Retornar mesmo sem validação
                    "current_phase": ConsultingPhase.SOLUTION_DESIGN,
                    "metadata": {
                        **state.metadata,
                        "solution_design_error": f"alignment_validation_failed: {e}",
                    },
                }

            # ========== STEP 5.5: KPI Alignment Checker (SPRINT 3 - SESSAO 48) ==========

            kpi_alignment_report = None
            kpi_validation_time = 0.0  # Inicializar para evitar NameError
            if tools_results and tools_results.kpi_framework:
                logger.info("[INFO] [SOLUTION_DESIGN] Iniciando validação de alinhamento KPI...")
                kpi_validation_start = time.time()  # SESSAO 48 FIX: Track phase start timestamp
                try:
                    # NOTA: validate_kpi_alignment é async - usar pattern existente do projeto
                    try:
                        loop = asyncio.get_running_loop()
                        kpi_alignment_report = loop.run_until_complete(
                            self.kpi_alignment_checker.validate_kpi_alignment(
                                strategy_map=strategy_map,
                                kpi_framework=tools_results.kpi_framework,
                            )
                        )
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        try:
                            asyncio.set_event_loop(loop)
                            kpi_alignment_report = loop.run_until_complete(
                                self.kpi_alignment_checker.validate_kpi_alignment(
                                    strategy_map=strategy_map,
                                    kpi_framework=tools_results.kpi_framework,
                                )
                            )
                        finally:
                            loop.close()
                    kpi_validation_time = (
                        time.time() - kpi_validation_start
                    )  # SESSAO 48 FIX: Duration from phase start
                    logger.info(
                        f"[OK] [SOLUTION_DESIGN] KPI Alignment validado em {kpi_validation_time:.2f}s | "
                        f"score={kpi_alignment_report.overall_score}/100 | "
                        f"is_aligned={kpi_alignment_report.is_aligned} | "
                        f"issues={len(kpi_alignment_report.alignment_issues)}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[WARN] [SOLUTION_DESIGN] KPI Alignment falhou (não crítico): {e}"
                    )
                    kpi_alignment_report = None
            else:
                logger.info(
                    "[INFO] [SOLUTION_DESIGN] KPI Alignment pulado (KPI Framework não disponível)"
                )

            # ========== STEP 5.6: Cause-Effect Mapper (SPRINT 3 - SESSAO 48) ==========

            cause_effect_analysis = None
            cause_effect_time = 0.0  # SESSAO 48 FIX: Inicializar para evitar NameError
            logger.info("[INFO] [SOLUTION_DESIGN] Iniciando análise causa-efeito...")
            cause_effect_start = time.time()  # SESSAO 48 FIX: Track phase start timestamp
            try:
                # NOTA: analyze_cause_effect é async - usar pattern existente do projeto
                try:
                    loop = asyncio.get_running_loop()
                    cause_effect_analysis = loop.run_until_complete(
                        self.cause_effect_mapper.analyze_cause_effect(
                            strategy_map=strategy_map,
                        )
                    )
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        cause_effect_analysis = loop.run_until_complete(
                            self.cause_effect_mapper.analyze_cause_effect(
                                strategy_map=strategy_map,
                            )
                        )
                    finally:
                        loop.close()
                cause_effect_time = (
                    time.time() - cause_effect_start
                )  # SESSAO 48 FIX: Duration from phase start
                logger.info(
                    f"[OK] [SOLUTION_DESIGN] Causa-Efeito analisado em {cause_effect_time:.2f}s | "
                    f"score={cause_effect_analysis.completeness_score}/100 | "
                    f"is_complete={cause_effect_analysis.is_complete} | "
                    f"gaps={len(cause_effect_analysis.gaps)}"
                )
            except Exception as e:
                logger.warning(
                    f"[WARN] [SOLUTION_DESIGN] Análise Causa-Efeito falhou (não crítico): {e}"
                )
                cause_effect_analysis = None

            # ========== STEP 6: Preparar resposta final baseada no score ==========

            total_time = time.time() - start_time

            # SESSAO 46: Recuperar relatório do diagnóstico (se existir)
            # Usuário quer SEMPRE ver o relatório, mesmo quando aprova automaticamente
            diagnostic_report = state.metadata.get("diagnostic_report", "")

            if alignment_report.score >= 70:
                # Construir resposta do Strategy Map
                strategy_map_response = (
                    f"# [CHECK] Strategy Map Criado com Sucesso!\n\n"
                    f"**Score de Alinhamento:** {alignment_report.score}/100\n"
                    f"**Status:** {'Balanceado' if alignment_report.is_balanced else 'Precisa Ajustes'}\n\n"
                    f"## PERSPECTIVAS:\n"
                    f"- **Financeira:** {len(strategy_map.financial.objectives)} objetivos\n"
                    f"- **Clientes:** {len(strategy_map.customer.objectives)} objetivos\n"
                    f"- **Processos:** {len(strategy_map.process.objectives)} objetivos\n"
                    f"- **Aprendizado:** {len(strategy_map.learning.objectives)} objetivos\n\n"
                    f"**CONEXÕES CAUSA-EFEITO:** {len(strategy_map.cause_effect_connections)} mapeadas\n\n"
                )

                # SESSAO 46: Concatenar diagnóstico + Strategy Map
                # Se há relatório do diagnóstico, mostrar PRIMEIRO, depois o Strategy Map
                if diagnostic_report:
                    final_response = (
                        f"{diagnostic_report}\n\n" f"---\n\n" f"{strategy_map_response}"
                    )
                else:
                    final_response = strategy_map_response

                if alignment_report.warnings:
                    final_response += f"## AVISOS ({len(alignment_report.warnings)}):\n"
                    for warning in alignment_report.warnings[:3]:  # Top 3
                        final_response += f"- {warning}\n"
                    final_response += "\n"

                # SPRINT 3 - SESSAO 48: Adicionar resultados das validações avançadas
                if kpi_alignment_report:
                    final_response += (
                        f"## [KPI] ALINHAMENTO KPIs:\n"
                        f"- **Score:** {kpi_alignment_report.overall_score:.1f}/100\n"
                        f"- **Status:** {'Alinhado [OK]' if kpi_alignment_report.is_aligned else 'Precisa Ajustes [WARN]'}\n"
                    )
                    if kpi_alignment_report.alignment_issues:
                        final_response += f"- **Issues:** {len(kpi_alignment_report.alignment_issues)} encontrados\n"
                        critical = kpi_alignment_report.critical_issues_count()
                        if critical > 0:
                            final_response += f"  - [WARN] {critical} issues criticos\n"
                    final_response += "\n"

                if cause_effect_analysis:
                    final_response += (
                        f"## [LINKS] ANALISE CAUSA-EFEITO:\n"
                        f"- **Score:** {cause_effect_analysis.completeness_score:.1f}/100\n"
                        f"- **Status:** {'Completo [OK]' if cause_effect_analysis.is_complete else 'Gaps Identificados [WARN]'}\n"
                    )
                    if cause_effect_analysis.gaps:
                        final_response += (
                            f"- **Gaps:** {len(cause_effect_analysis.gaps)} encontrados\n"
                        )
                    final_response += "\n"

                final_response += (
                    "---\n\n**Próxima fase:** IMPLEMENTATION (plano de ação detalhado)"
                )
                next_phase = ConsultingPhase.IMPLEMENTATION

            else:
                # Construir resposta de refinamento necessário
                refinement_response = (
                    f"# [WARN] Strategy Map Precisa Refinamento\n\n"
                    f"**Score de Alinhamento:** {alignment_report.score}/100 (mínimo: 70)\n"
                    f"**Status:** Precisa Refinamento\n\n"
                    f"## GAPS CRÍTICOS ({len(alignment_report.gaps)}):\n"
                )
                for gap in alignment_report.gaps[:5]:  # Top 5
                    refinement_response += f"- {gap}\n"

                refinement_response += (
                    f"\n## RECOMENDAÇÕES ({len(alignment_report.recommendations)}):\n"
                )
                for rec in alignment_report.recommendations[:3]:  # Top 3
                    refinement_response += f"- {rec}\n"

                # SPRINT 3 - SESSAO 48: Adicionar resultados das validações avançadas na resposta de refinamento
                if kpi_alignment_report and not kpi_alignment_report.is_aligned:
                    refinement_response += (
                        f"\n## [WARN] PROBLEMAS DE ALINHAMENTO KPIs:\n"
                        f"- **Score:** {kpi_alignment_report.overall_score:.1f}/100\n"
                    )
                    for issue in kpi_alignment_report.alignment_issues[:3]:  # Top 3
                        refinement_response += f"- [{issue.severity.upper()}] {issue.description}\n"
                        if issue.recommendation:
                            refinement_response += f"  [TIP] {issue.recommendation}\n"

                if cause_effect_analysis and not cause_effect_analysis.is_complete:
                    refinement_response += (
                        f"\n## [WARN] GAPS CAUSA-EFEITO:\n"
                        f"- **Score:** {cause_effect_analysis.completeness_score:.1f}/100\n"
                    )
                    for gap in cause_effect_analysis.gaps[:3]:  # Top 3
                        refinement_response += f"- [{gap.gap_type.upper()}] {gap.description}\n"

                refinement_response += (
                    "\n**Próxima ação:** Refazer diagnóstico considerando os gaps identificados."
                )

                # SESSAO 46: Concatenar diagnóstico + resposta de refinamento
                if diagnostic_report:
                    final_response = f"{diagnostic_report}\n\n" f"---\n\n" f"{refinement_response}"
                else:
                    final_response = refinement_response

                next_phase = ConsultingPhase.DISCOVERY

            logger.info(
                f"[OK] [SOLUTION_DESIGN] Handler completo em {total_time:.2f}s | "
                f"score={alignment_report.score} | next_phase={next_phase.value}"
            )

            # ========== STEP 7: Retornar state atualizado ==========

            # Construir metadata com novos reports (se disponíveis)
            result_metadata = {
                **state.metadata,
                "solution_design_time": total_time,
                "design_time": design_time,
                "validation_time": validation_time,
                "alignment_score": alignment_report.score,
                "is_balanced": alignment_report.is_balanced,
                "num_gaps": len(alignment_report.gaps),
                "num_warnings": len(alignment_report.warnings),
                "routing_decision": next_phase.value,
            }

            # SPRINT 3 - SESSAO 48: Adicionar métricas das validações avançadas
            if kpi_alignment_report:
                result_metadata["kpi_alignment_score"] = kpi_alignment_report.overall_score
                result_metadata["kpi_is_aligned"] = kpi_alignment_report.is_aligned
                result_metadata["kpi_issues_count"] = len(kpi_alignment_report.alignment_issues)
                result_metadata["kpi_critical_issues"] = (
                    kpi_alignment_report.critical_issues_count()
                )

            if cause_effect_analysis:
                result_metadata["cause_effect_score"] = cause_effect_analysis.completeness_score
                result_metadata["cause_effect_is_complete"] = cause_effect_analysis.is_complete
                result_metadata["cause_effect_gaps_count"] = len(cause_effect_analysis.gaps)

            return {
                "strategy_map": strategy_map,
                "alignment_report": alignment_report,
                "kpi_alignment_report": kpi_alignment_report,
                "cause_effect_analysis": cause_effect_analysis,
                "final_response": final_response,
                "current_phase": next_phase,
                "metadata": result_metadata,
            }

        except Exception as e:
            logger.error(
                f"[ERROR] [SOLUTION_DESIGN] Erro inesperado no handler: {e}", exc_info=True
            )
            # Import aqui também para except
            from src.graph.consulting_states import ConsultingPhase

            return {
                "final_response": (
                    f"Erro inesperado ao criar Strategy Map: {e}. "
                    "Por favor, tente novamente ou contate o suporte."
                ),
                "current_phase": ConsultingPhase.SOLUTION_DESIGN,
                "metadata": {**state.metadata, "solution_design_error": f"unexpected_error: {e}"},
            }

    async def implementation_handler(self, state: BSCState) -> dict[str, Any]:
        """
        SPRINT 3 - Handler para criação do Action Plan (plano de ação).

        Usa ActionPlanTool para criar plano de ação estruturado baseado em:
        1. Strategy Map aprovado (objetivos estratégicos mapeados)
        2. Diagnostic completo (4 perspectivas BSC)
        3. ClientProfile (contexto da empresa)
        4. Conhecimento BSC (via 4 specialist agents)

        Args:
            state: Estado com strategy_map, diagnostic e client_profile

        Returns:
            Estado atualizado com action_plan e final_response
        """
        # Lazy import
        from src.graph.consulting_states import ConsultingPhase

        logger.info("[START] [IMPLEMENTATION] Handler iniciado - Criando Action Plan")

        try:
            # Validar inputs necessários
            if not state.strategy_map:
                logger.error("[ERROR] [IMPLEMENTATION] Strategy Map ausente!")
                return {
                    "final_response": (
                        "Erro: Strategy Map não encontrado. "
                        "Execute a fase SOLUTION_DESIGN primeiro."
                    ),
                    "current_phase": ConsultingPhase.IMPLEMENTATION,
                    "metadata": {**state.metadata, "implementation_error": "strategy_map_missing"},
                }

            if not state.client_profile:
                logger.error("[ERROR] [IMPLEMENTATION] ClientProfile ausente!")
                return {
                    "final_response": (
                        "Erro: Perfil do cliente não encontrado. "
                        "Execute a fase ONBOARDING primeiro."
                    ),
                    "current_phase": ConsultingPhase.IMPLEMENTATION,
                    "metadata": {
                        **state.metadata,
                        "implementation_error": "client_profile_missing",
                    },
                }

            # Extrair diagnostic do state (pode estar como dict)
            diagnostic = None
            if state.diagnostic:
                if isinstance(state.diagnostic, dict):
                    # Converter dict para CompleteDiagnostic
                    from src.memory.schemas import CompleteDiagnostic

                    try:
                        diagnostic = CompleteDiagnostic(**state.diagnostic)
                        logger.info(
                            "[INFO] [IMPLEMENTATION] Diagnostic convertido de dict para Pydantic"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[WARN] [IMPLEMENTATION] Falha ao converter diagnostic: {e}"
                        )
                        diagnostic = None
                else:
                    diagnostic = state.diagnostic

            logger.info(
                f"[INFO] [IMPLEMENTATION] Criando Action Plan para {state.client_profile.company.name} "
                f"(setor: {state.client_profile.company.sector})"
            )

            # Chamar ActionPlanTool.facilitate() de forma async
            action_plan = await self.action_plan_tool.facilitate(
                client_profile=state.client_profile,
                financial_agent=self.financial_agent,
                customer_agent=self.customer_agent,
                process_agent=self.process_agent,
                learning_agent=self.learning_agent,
                diagnostic_results=diagnostic,
            )

            logger.info(
                f"[OK] [IMPLEMENTATION] Action Plan criado com sucesso | "
                f"Total ações: {action_plan.total_actions} | "
                f"Prioritárias: {action_plan.high_priority_count}"
            )

            # ========== SPRINT 4 - SESSAO 49: Gerar Milestones ==========
            milestone_report = None
            milestone_report_dict = None
            try:
                from datetime import datetime

                current_date = datetime.now().strftime("%Y-%m-%d")
                milestone_report = (
                    await self.milestone_tracker.generate_milestones_from_action_plan(
                        action_plan=action_plan,
                        current_date=current_date,
                    )
                )
                milestone_report_dict = milestone_report.model_dump()
                logger.info(
                    f"[OK] [IMPLEMENTATION] Milestones gerados | "
                    f"total={milestone_report.total_milestones} | "
                    f"progresso={milestone_report.overall_progress:.1f}% | "
                    f"em_risco={milestone_report.at_risk_count}"
                )
            except Exception as e:
                logger.warning(
                    f"[WARN] [IMPLEMENTATION] Falha ao gerar milestones (não crítico): {e}"
                )

            # Gerar resumo executivo do Action Plan
            summary = self._generate_action_plan_summary(
                action_plan, state.strategy_map, state.client_profile, milestone_report
            )

            # Serializar action_plan para dict (BSCState aceita dict)
            action_plan_dict = action_plan.model_dump()

            # Construir metadata
            result_metadata = {
                **state.metadata,
                "action_plan_created_at": time.time(),
                "total_actions": action_plan.total_actions,
                "high_priority_actions": action_plan.high_priority_count,
            }

            # Adicionar métricas de milestones se disponíveis
            if milestone_report:
                result_metadata["milestone_total"] = milestone_report.total_milestones
                result_metadata["milestone_progress"] = milestone_report.overall_progress
                result_metadata["milestone_at_risk"] = milestone_report.at_risk_count

            return {
                "action_plan": action_plan_dict,
                "milestone_report": milestone_report_dict,
                "final_response": summary,
                "current_phase": ConsultingPhase.IMPLEMENTATION,
                "is_complete": True,
                "metadata": result_metadata,
            }

        except Exception as e:
            logger.exception("[ERROR] [IMPLEMENTATION] Erro ao criar Action Plan")
            return {
                "final_response": (
                    f"Erro inesperado ao criar Action Plan: {e}. "
                    "Por favor, tente novamente ou contate o suporte."
                ),
                "current_phase": ConsultingPhase.IMPLEMENTATION,
                "metadata": {**state.metadata, "implementation_error": f"unexpected_error: {e}"},
            }

    def _generate_action_plan_summary(
        self, action_plan, strategy_map, client_profile, milestone_report=None
    ) -> str:
        """
        Gera resumo executivo do Action Plan criado.

        Args:
            action_plan: ActionPlan completo
            strategy_map: StrategyMap relacionado
            client_profile: ClientProfile com company info
            milestone_report: MilestoneTrackerReport opcional (SPRINT 4)

        Returns:
            String com resumo formatado
        """
        # Extrair nome da empresa do ClientProfile
        company_name = (
            client_profile.company.name if client_profile and client_profile.company else "Cliente"
        )

        # Contar objetivos do Strategy Map
        num_objectives = 0
        if strategy_map:
            num_objectives = (
                len(strategy_map.financial.objectives)
                + len(strategy_map.customer.objectives)
                + len(strategy_map.process.objectives)
                + len(strategy_map.learning.objectives)
            )

        # Agrupar ações por prioridade
        high_priority = [a for a in action_plan.action_items if a.priority == "HIGH"]
        medium_priority = [a for a in action_plan.action_items if a.priority == "MEDIUM"]
        low_priority = [a for a in action_plan.action_items if a.priority == "LOW"]

        # Construir resumo
        summary_lines = [
            "# Action Plan - Plano de Ação BSC [OK]",
            "",
            f"**Empresa**: {company_name}",
            f"**Cronograma**: {action_plan.timeline_summary}",
            "",
            "## Resumo Executivo",
            "",
            f"- **Objetivos Estratégicos Mapeados**: {num_objectives}",
            f"- **Total de Ações Planejadas**: {action_plan.total_actions}",
            f"- **Ações Prioritárias (HIGH)**: {len(high_priority)}",
            f"- **Ações Médias (MEDIUM)**: {len(medium_priority)}",
            f"- **Ações Rápidas (LOW)**: {len(low_priority)}",
            "",
            "## Ações por Prioridade",
            "",
        ]

        # Listar top 3 ações HIGH
        if high_priority:
            summary_lines.append("### Prioridade ALTA (executar primeiro)")
            summary_lines.append("")
            for i, action in enumerate(high_priority[:3], 1):
                summary_lines.append(f"{i}. **{action.action_title}**")
                summary_lines.append(f"   - Responsável: {action.responsible}")
                summary_lines.append(f"   - Prazo: {action.due_date}")
                summary_lines.append(f"   - Critério Sucesso: {action.success_criteria}")
                summary_lines.append("")

        # Listar top 2 ações MEDIUM
        if medium_priority:
            summary_lines.append("### Prioridade MÉDIA")
            summary_lines.append("")
            for i, action in enumerate(medium_priority[:2], 1):
                summary_lines.append(f"{i}. **{action.action_title}**")
                summary_lines.append(f"   - Prazo: {action.due_date}")
                summary_lines.append("")

        # SPRINT 4 - SESSAO 49: Adicionar resumo de milestones
        if milestone_report:
            summary_lines.extend(
                [
                    "## Rastreamento de Milestones",
                    "",
                    f"- **Total de Milestones**: {milestone_report.total_milestones}",
                    f"- **Progresso Geral**: {milestone_report.overall_progress:.1f}%",
                    f"- **Completados**: {milestone_report.completed_count}",
                    f"- **Em Andamento**: {milestone_report.in_progress_count}",
                    f"- **Em Risco**: {milestone_report.at_risk_count}",
                    "",
                ]
            )

            # Próximos milestones
            if milestone_report.next_due_milestones:
                summary_lines.append("### Próximos Prazos")
                summary_lines.append("")
                for m_name in milestone_report.next_due_milestones[:3]:
                    summary_lines.append(f"- {m_name}")
                summary_lines.append("")

            # Recomendações
            if milestone_report.recommendations:
                summary_lines.append("### Recomendações")
                summary_lines.append("")
                for rec in milestone_report.recommendations[:3]:
                    summary_lines.append(f"- {rec}")
                summary_lines.append("")

        summary_lines.extend(
            [
                "---",
                "",
                "**Próximos Passos:**",
                "1. Revisar e ajustar Action Plan conforme necessário",
                "2. Designar responsáveis e confirmar prazos",
                "3. Estabelecer rituais de acompanhamento (weekly/monthly)",
                "4. Configurar dashboards de monitoramento de KPIs",
                "",
                "Consulte as páginas Strategy Map e Action Plan no menu lateral para detalhes completos.",
            ]
        )

        return "\n".join(summary_lines)

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

            # CORREÇÃO SESSAO 43 (2025-11-24): Executar sempre, não apenas no except
            # Python 3.12 compatible - usar loop existente ou criar novo
            try:
                loop = asyncio.get_running_loop()
                # CORREÇÃO: Se loop existe (Streamlit + nest_asyncio), usar run_until_complete
                result = loop.run_until_complete(
                    self.consulting_orchestrator.coordinate_onboarding(state)
                )
            except RuntimeError:
                # Sem running loop - criar novo
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        self.consulting_orchestrator.coordinate_onboarding(state)
                    )
                finally:
                    loop.close()  # Previne resource leak

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
            return self.consulting_orchestrator.handle_error(e, state, "ONBOARDING")

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
            # CORREÇÃO SESSAO 45: Incrementar contador de tentativas
            # Isso permite limitar loops infinitos via route_by_approval
            current_attempts = state.discovery_attempts + 1

            logger.info(
                f"[INFO] [DISCOVERY] Handler iniciado | "
                f"user_id={state.user_id} | has_profile={state.client_profile is not None} | "
                f"attempt={current_attempts}/{state.max_discovery_attempts}"
            )

            # CORREÇÃO SESSAO 46: Verificar se atingiu limite de tentativas
            # NOTA: Usa > (nao >=) porque current_attempts e incrementado ANTES de verificar
            # (current_attempts = discovery_attempts + 1, ou seja, valor FUTURO)
            # Com max=2: tentativa 1 (1>2=F->executa), tentativa 2 (2>2=F->executa), tentativa 3 (3>2=T->bloqueia)
            # Resultado: permite exatamente max_discovery_attempts tentativas
            # Ver tambem: route_by_approval linha ~964 usa >= com discovery_attempts (valor atual)
            # AMBOS OPERADORES SAO CORRETOS - diferenca e QUANDO a verificacao acontece:
            #   - Aqui: ANTES de executar (com valor futuro) -> usa >
            #   - Router: DEPOIS de executar (com valor atual) -> usa >=
            if current_attempts > state.max_discovery_attempts:
                logger.error(
                    f"[ERROR] [DISCOVERY] Limite de tentativas atingido "
                    f"({current_attempts} > {state.max_discovery_attempts}). "
                    "Encerrando para evitar loop infinito."
                )
                from src.graph.consulting_states import ConsultingPhase

                return {
                    "discovery_attempts": current_attempts,
                    "current_phase": ConsultingPhase.ERROR,
                    "final_response": (
                        "Desculpe, não foi possível completar o diagnóstico após múltiplas tentativas. "
                        "Por favor, tente novamente mais tarde ou reformule sua pergunta."
                    ),
                    "metadata": {
                        **state.metadata,
                        "discovery_error": "max_attempts_exceeded",
                        "discovery_attempts": current_attempts,
                    },
                }

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
                # CORREÇÃO SESSAO 43 (2025-11-24): Executar sempre, não apenas no except
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    # CORREÇÃO: Se loop existe (Streamlit + nest_asyncio), usar run_until_complete
                    result = loop.run_until_complete(
                        self.consulting_orchestrator.coordinate_refinement(state)
                    )
                except RuntimeError:
                    # Sem running loop - criar novo
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(
                            self.consulting_orchestrator.coordinate_refinement(state)
                        )
                    finally:
                        loop.close()  # Previne resource leak
            else:
                # Discovery normal: criar diagnóstico novo
                logger.info("[INFO] [DISCOVERY] Discovery normal (criar novo diagnóstico)")
                # Delegar para ConsultingOrchestrator (ASYNC para paralelizar 4 agentes)
                # CORREÇÃO SESSAO 43 (2025-11-24): Executar sempre, não apenas no except
                # Python 3.12 compatible - usar loop existente ou criar novo
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    # CORREÇÃO: Se loop existe (Streamlit + nest_asyncio), usar run_until_complete
                    result = loop.run_until_complete(
                        self.consulting_orchestrator.coordinate_discovery(state)
                    )
                except RuntimeError:
                    # Sem running loop - criar novo
                    loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(
                            self.consulting_orchestrator.coordinate_discovery(state)
                        )
                    finally:
                        loop.close()  # Previne resource leak

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
                f"next_phase={result.get('current_phase', 'N/A')} | "
                f"attempt={current_attempts}/{state.max_discovery_attempts}"
            )

            # CORREÇÃO SESSAO 45: Incluir discovery_attempts no resultado
            # Isso permite que route_by_approval verifique o contador
            result["discovery_attempts"] = current_attempts

            # SESSAO 46: Preservar relatório do diagnóstico em metadata
            # Motivo: Usuário quer SEMPRE ver o relatório, mesmo se aprovar automaticamente
            # Quando design_solution_handler executa, ele sobrescreve final_response
            # Salvando em metadata["diagnostic_report"], garantimos que não se perde
            if result.get("final_response"):
                result_metadata = result.get("metadata", {})
                result_metadata["diagnostic_report"] = result["final_response"]
                result["metadata"] = result_metadata
                logger.info(
                    f"[INFO] [DISCOVERY] Relatório diagnóstico salvo em metadata "
                    f"({len(result['final_response'])} chars)"
                )

            return result

        except RuntimeError as e:
            # ERRO CRÍTICO: ThreadPoolExecutor shutdown (comum em Streamlit)
            # Evitar crash completo do workflow - fallback para ERROR (não ONBOARDING!)
            # CORREÇÃO SESSAO 45: Usar ERROR para evitar loop infinito via route_by_approval
            error_msg = str(e)
            from src.graph.consulting_states import ConsultingPhase

            logger.error(
                f"[ERROR] [DISCOVERY] RuntimeError (ThreadPoolExecutor shutdown): {error_msg} | "
                f"Fase=ERROR (evitar loop infinito)"
            )

            return {
                "discovery_attempts": state.discovery_attempts + 1,  # Incrementar tentativa
                "current_phase": ConsultingPhase.ERROR,  # ERROR para evitar loop
                "final_response": (
                    "Ocorreu um erro durante o processamento do diagnóstico.\n\n"
                    "Por favor, tente novamente ou reformule sua pergunta."
                ),
                "metadata": {
                    **state.metadata,
                    "discovery_error": error_msg,
                    "discovery_error_type": "RuntimeError_ThreadPoolExecutor",
                },
            }

        except Exception as e:
            logger.error(f"[ERROR] [DISCOVERY] Erro no handler: {e}")
            # CORREÇÃO SESSAO 45: Incluir discovery_attempts no resultado de erro
            # Para que route_by_approval possa verificar o contador
            error_result = self.consulting_orchestrator.handle_error(e, state, "DISCOVERY")
            error_result["discovery_attempts"] = state.discovery_attempts + 1
            return error_result

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
                # SESSAO 44 (2025-11-24): Usar graph COM checkpointer para get_state
                # self.graph não tem checkpointer, usar _graph_with_checkpointer
                existing_state = self._graph_with_checkpointer.get_state(config)

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

                    # CORREÇÃO SESSAO 45: Update com campos consistentes para merge com checkpoint
                    # PROBLEMA: Antes passava apenas query+metadata, mas primeira invocação
                    #           passa todos campos via BSCState.model_dump()
                    # SOLUÇÃO: Incluir session_id e user_id para consistência
                    #          Checkpoint merge sobrescreve apenas campos fornecidos
                    state_to_invoke = {
                        "query": query,
                        "session_id": session_id,  # Manter consistência com primeira invocação
                        "user_id": user_id,  # Manter consistência com primeira invocação
                        "metadata": (
                            {**(existing_metadata), "chat_history": chat_history}
                            if chat_history
                            else existing_metadata
                        ),
                    }

                    logger.info(
                        "[CHECKPOINT] Update sendo enviado ao invoke: metadata keys=%s",
                        list(state_to_invoke.get("metadata", {}).keys()),
                    )
                else:
                    # Primeira invocação: criar state completo
                    logger.info(
                        "[CHECKPOINT] Primeira invocação (checkpoint vazio) | "
                        "Criando state inicial completo"
                    )

                    # CORREÇÃO SESSAO 45: Converter para dict - ainvoke() espera dict[str, Any]
                    # BSCState.model_dump() garante serialização correta para checkpoints
                    state_to_invoke = BSCState(
                        query=query,
                        session_id=session_id,
                        user_id=user_id,
                        metadata={"chat_history": chat_history} if chat_history else {},
                    ).model_dump()

                # BUG FIX (Sessao 42, 2025-11-22): execute_agents é async def
                # LangGraph exige .ainvoke() para async nodes (não .invoke())
                # Pattern manual event loop com CLEANUP (Python 3.12 + Streamlit compatible)
                try:
                    asyncio.get_running_loop()
                    # Se chegou aqui, loop já existe - cenário inesperado em Streamlit
                    logger.warning(
                        "[WARN] Loop já rodando - comportamento inesperado em Streamlit ScriptRunner thread"
                    )
                except RuntimeError:
                    pass  # Esperado - Streamlit ScriptRunner thread não tem loop

                # Criar loop novo SEMPRE (pattern consistente)
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    # CORREÇÃO SESSAO 45: Usar self.ainvoke() para persistência de checkpoints
                    # self.graph não tem checkpointer, self.ainvoke() usa AsyncSqliteSaver
                    final_state = loop.run_until_complete(self.ainvoke(state_to_invoke, config))
                finally:
                    # CORREÇÃO SESSAO 45: Cleanup completo antes de fechar loop
                    # Sequencia: shutdown_asyncgens -> shutdown_default_executor -> close
                    try:
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    except Exception:
                        pass  # Ignorar erros de cleanup
                    try:
                        loop.run_until_complete(loop.shutdown_default_executor())
                    except Exception:
                        pass  # Ignorar erros de cleanup
                    loop.close()  # Previne resource leak

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

            except Exception as e:
                # Fallback: se get_state falhar, assumir primeira invocação
                logger.warning(
                    f"[CHECKPOINT] Erro ao verificar checkpoint existente: {e} | "
                    "Assumindo primeira invocação"
                )

                # CORREÇÃO SESSAO 45: Converter para dict - ainvoke() espera dict[str, Any]
                # BSCState.model_dump() garante serialização correta para checkpoints
                initial_state = BSCState(
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    metadata={"chat_history": chat_history} if chat_history else {},
                ).model_dump()

                # Executar com state inicial em caso de erro
                # Pattern manual event loop com CLEANUP (Python 3.12 + Streamlit compatible)
                try:
                    asyncio.get_running_loop()
                    logger.warning(
                        "[WARN] Loop já rodando - comportamento inesperado em Streamlit ScriptRunner thread"
                    )
                except RuntimeError:
                    pass  # Esperado - Streamlit ScriptRunner thread não tem loop

                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    # CORREÇÃO SESSAO 45: Usar self.ainvoke() para persistência de checkpoints
                    final_state = loop.run_until_complete(self.ainvoke(initial_state, config))
                finally:
                    # CORREÇÃO SESSAO 45: Cleanup completo antes de fechar loop
                    # Sequencia: shutdown_asyncgens -> shutdown_default_executor -> close
                    try:
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    except Exception:
                        pass  # Ignorar erros de cleanup
                    try:
                        loop.run_until_complete(loop.shutdown_default_executor())
                    except Exception:
                        pass  # Ignorar erros de cleanup
                    loop.close()  # Previne resource leak

            # Extrair resultado
            # CORREÇÃO SESSAO 45: Checkpoint pode deserializar Pydantic models como dicts
            # Usar acesso defensivo (dict.get() ou getattr()) para evitar AttributeError
            def _safe_perspective_value(p):
                """Extrai value de enum ou string de forma segura."""
                if hasattr(p, "value"):
                    return p.value
                return str(p) if p else None

            def _safe_agent_response(r):
                """Extrai campos de AgentResponse (objeto ou dict) de forma segura."""
                if isinstance(r, dict):
                    perspective = r.get("perspective", "")
                    if hasattr(perspective, "value"):
                        perspective = perspective.value
                    return {
                        "perspective": perspective,
                        "content": r.get("content", ""),
                        "confidence": r.get("confidence", 0.0),
                        "sources": r.get("sources", []),
                    }
                # É objeto AgentResponse
                return {
                    "perspective": (
                        r.perspective.value
                        if hasattr(r.perspective, "value")
                        else str(r.perspective)
                    ),
                    "content": r.content,
                    "confidence": r.confidence,
                    "sources": r.sources,
                }

            def _safe_sources(r):
                """Extrai sources de AgentResponse (objeto ou dict) de forma segura."""
                if isinstance(r, dict):
                    return r.get("sources", [])
                return getattr(r, "sources", [])

            def _safe_judge_evaluation(je):
                """Converte JudgeEvaluation (objeto ou dict) para dict de forma segura."""
                if je is None:
                    return None
                if isinstance(je, dict):
                    return je  # Já é dict
                if hasattr(je, "model_dump"):
                    return je.model_dump()
                return dict(je)  # Fallback

            def _safe_judge_approved(je):
                """Extrai approved de JudgeEvaluation (objeto ou dict) de forma segura."""
                if je is None:
                    return None
                if isinstance(je, dict):
                    return je.get("approved")
                return getattr(je, "approved", None)

            result = {
                "query": final_state["query"],
                "final_response": final_state.get("final_response", ""),
                "client_profile": final_state.get("client_profile"),
                "perspectives": [
                    _safe_perspective_value(p) for p in final_state.get("relevant_perspectives", [])
                ],
                "agent_responses": [
                    _safe_agent_response(r) for r in final_state.get("agent_responses", [])
                ],
                # Agregar retrieved_documents de todas as respostas dos agentes
                "retrieved_documents": [
                    doc for r in final_state.get("agent_responses", []) for doc in _safe_sources(r)
                ],
                "judge_evaluation": _safe_judge_evaluation(final_state.get("judge_evaluation")),
                "refinement_iterations": final_state.get("refinement_iteration", 0),
                "metadata": final_state.get("metadata", {}),
            }

            # Adicionar judge_approved ao metadata top-level para E2E tests
            judge_approved = _safe_judge_approved(final_state.get("judge_evaluation"))
            if judge_approved is not None:
                result["metadata"]["judge_approved"] = judge_approved

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
