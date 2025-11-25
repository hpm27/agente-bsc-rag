"""
Orchestrator Agent - Coordenador dos Agentes Especialistas.

Responsável por:
- Analisar a pergunta do usuário
- Determinar quais agentes especialistas devem ser acionados
- Coordenar a execução dos agentes
- Combinar e sintetizar respostas
- Usar Judge Agent para validação
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from api.middleware.performance import track_llm_tokens
from config.settings import get_llm_for_agent, settings
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, Field

from src.agents.customer_agent import CustomerAgent
from src.agents.financial_agent import FinancialAgent
from src.agents.judge_agent import JudgeAgent
from src.agents.learning_agent import LearningAgent
from src.agents.process_agent import ProcessAgent
from src.rag.query_router import QueryRouter


class RoutingDecision(BaseModel):
    """Decisão de roteamento para agentes."""

    agents_to_use: list[str] = Field(
        description="Lista de perspectivas a acionar: 'financeira', 'cliente', 'processos', 'aprendizado'"
    )
    reasoning: str = Field(description="Justificativa da escolha dos agentes")
    is_general_question: bool = Field(
        description="Se é uma pergunta geral sobre BSC (acionar todos)"
    )


class SynthesisResult(BaseModel):
    """Resultado da síntese de múltiplas respostas."""

    synthesized_answer: str = Field(
        description="Resposta sintetizada combinando insights de múltiplos agentes"
    )
    perspectives_covered: list[str] = Field(description="Perspectivas BSC cobertas na resposta")
    confidence: float = Field(description="Confiança na resposta (0-1)", ge=0.0, le=1.0)


class Orchestrator:
    """Orquestrador dos agentes especialistas BSC."""

    def __init__(self):
        """Inicializa o orquestrador."""
        self.name = "Orchestrator"

        # SESSAO 45: LLM síntese (Claude Opus 4.5 - Infinite Chat, 40-60K tokens input)
        self.llm = get_llm_for_agent("synthesis", timeout=600)

        # Agentes especialistas
        self.agents = {
            "financeira": FinancialAgent(),
            "cliente": CustomerAgent(),
            "processos": ProcessAgent(),
            "aprendizado": LearningAgent(),
        }

        # Judge agent
        self.judge = JudgeAgent()

        # Query Router Inteligente (RAG Avançado - Fase 2A.3)
        self.enable_query_router = (
            settings.enable_query_router if hasattr(settings, "enable_query_router") else False
        )
        self.query_router = QueryRouter() if self.enable_query_router else None

        # Prompts
        self.routing_prompt = self._create_routing_prompt()
        self.synthesis_prompt = self._create_synthesis_prompt()

        # Chains
        self.routing_chain = self.routing_prompt | self.llm.with_structured_output(RoutingDecision)
        self.synthesis_chain = self.synthesis_prompt | self.llm.with_structured_output(
            SynthesisResult
        )

        logger.info(
            f"[OK] {self.name} inicializado com {len(self.agents)} agentes especialistas "
            f"(QueryRouter={'enabled' if self.enable_query_router else 'disabled'})"
        )

    def _create_routing_prompt(self) -> ChatPromptTemplate:
        """Cria prompt para routing de agentes."""
        template = """Você é um roteador inteligente para sistema multi-agente de Balanced Scorecard.

Sua tarefa é analisar a pergunta do usuário e determinar qual(is) agente(s) especialista(s) deve(m) ser acionado(s):

**Agentes Disponíveis:**
- **financeira**: Indicadores financeiros, ROI, lucro, custos, receita
- **cliente**: Satisfação, NPS, retenção, proposta de valor, experiência do cliente
- **processos**: Eficiência operacional, qualidade, ciclo de tempo, produtividade
- **aprendizado**: Capacitação, cultura, inovação, sistemas de informação, crescimento

**Pergunta do Usuário:**
{query}

**Instruções:**
1. Se a pergunta for GERAL sobre BSC (ex: "O que é BSC?", "Como funciona o BSC?"):
   - Marque is_general_question=True
   - Inclua TODAS as 4 perspectivas

2. Se a pergunta menciona EXPLICITAMENTE uma ou mais perspectivas:
   - Selecione apenas as perspectivas mencionadas

3. Se a pergunta é ESPECÍFICA mas não menciona perspectiva:
   - Identifique a(s) perspectiva(s) mais relevante(s) baseado no conteúdo
   - Exemplos:
     * "Como melhorar lucratividade?" -> financeira
     * "Como aumentar satisfação do cliente?" -> cliente
     * "Como reduzir tempo de produção?" -> processos
     * "Como capacitar equipe?" -> aprendizado

4. Se a pergunta aborda MÚLTIPLAS perspectivas:
   - Selecione TODAS as perspectivas relevantes

Seja preciso e justifique sua decisão."""

        return ChatPromptTemplate.from_template(template)

    def _create_synthesis_prompt(self) -> ChatPromptTemplate:
        """Cria prompt para síntese de respostas."""
        template = """Você é um sintetizador especializado em Balanced Scorecard.

Sua tarefa é combinar múltiplas respostas de agentes especialistas em uma resposta coesa e completa.

**Pergunta Original:**
{original_query}

**Respostas dos Agentes Especialistas:**
{agent_responses}

**Instruções:**
1. Combine as respostas em uma resposta **unificada e coerente**
2. Mantenha TODAS as citações de fontes (Fonte, Página)
3. Organize por tópicos/perspectivas quando apropriado
4. Destaque conexões entre as perspectivas quando relevante
5. Seja conciso mas completo
6. Use markdown para formatação (títulos, listas, negrito)

**Formato da Resposta Sintetizada:**
- Comece com uma visão geral
- Organize por perspectiva se múltiplas foram consultadas
- Termine com uma síntese ou conclusão
- Sempre cite fontes

Calcule confidence baseado em:
- 1.0: Múltiplos agentes concordam, bem fundamentado
- 0.7-0.9: Respostas consistentes mas com algumas lacunas
- 0.5-0.7: Respostas parciais ou com conflitos menores
- <0.5: Informações insuficientes ou conflitantes"""

        return ChatPromptTemplate.from_template(template)

    def get_retrieval_strategy_metadata(self, query: str) -> dict[str, Any]:
        """
        Usa Query Router para obter metadata sobre estratégia de retrieval.

        Esta metadata é adicionada ao BSCState para analytics e pode ser
        usada pelos agentes para otimizar retrieval.

        Args:
            query: Query do usuário

        Returns:
            Dict com metadata de routing (categoria, estratégia, confidence, etc)
        """
        if not self.enable_query_router or self.query_router is None:
            # Router desabilitado -> retorna metadata padrão
            return {
                "router_enabled": False,
                "category": "conceptual_broad",
                "strategy": "HybridSearch",
                "confidence": 1.0,
                "complexity_score": 0,
            }

        try:
            # Obter decisão de routing
            routing_decision = self.query_router.route(query)

            logger.info(
                f"[Router] Query classified: category={routing_decision.category.value}, "
                f"strategy={routing_decision.strategy}, "
                f"confidence={routing_decision.confidence:.2f}"
            )

            # Retornar metadata para BSCState
            return {
                "router_enabled": True,
                "category": routing_decision.category.value,
                "strategy": routing_decision.strategy,
                "confidence": routing_decision.confidence,
                "heuristic_match": routing_decision.heuristic_match,
                "complexity_score": routing_decision.complexity_score,
                **routing_decision.metadata,
            }

        except Exception as e:
            logger.error(f"[Router] Erro ao rotear query: {e}")
            # Fallback para metadata padrão
            return {
                "router_enabled": True,
                "router_error": str(e),
                "category": "conceptual_broad",
                "strategy": "HybridSearch",
                "confidence": 0.5,
                "complexity_score": 0,
            }

    def route_query(self, query: str) -> RoutingDecision:
        """
        Determina quais agentes devem processar a query.

        Args:
            query: Pergunta do usuário

        Returns:
            Decisão de roteamento
        """
        try:
            logger.info(f"[ROUTING] {self.name} roteando query: '{query[:50]}...'")

            decision = self.routing_chain.invoke({"query": query})

            logger.info(
                f"[OK] Roteamento: {len(decision.agents_to_use)} agente(s) - "
                f"{', '.join(decision.agents_to_use)}"
            )

            return decision

        except Exception as e:
            logger.error(f"[ERRO] Erro no roteamento: {e}")
            # Fallback: aciona todos os agentes
            return RoutingDecision(
                agents_to_use=["financeira", "cliente", "processos", "aprendizado"],
                reasoning=f"Erro no roteamento, acionando todos os agentes. Erro: {e!s}",
                is_general_question=True,
            )

    def _invoke_single_agent(
        self, agent_name: str, query: str, chat_history: list[dict[str, str]] | None = None
    ) -> dict[str, Any] | None:
        """
        Invoca um unico agente especialista.
        Metodo auxiliar para execucao paralela com ThreadPoolExecutor.

        Args:
            agent_name: Nome do agente a invocar
            query: Pergunta do usuario
            chat_history: Historico da conversa

        Returns:
            Dicionario com resposta do agente ou None se agente nao encontrado
        """
        if agent_name not in self.agents:
            logger.warning(f"[WARN] Agente '{agent_name}' nao encontrado")
            return None

        agent = self.agents[agent_name]
        agent_start = time.time()

        try:
            result = agent.invoke(query, chat_history)
            elapsed = time.time() - agent_start

            logger.info(f"[OK] {agent.get_name()} concluido em {elapsed:.2f}s")

            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_time": elapsed,
            }

        except Exception as e:
            elapsed = time.time() - agent_start
            logger.error(f"[ERRO] Erro ao invocar {agent.get_name()}: {e}")
            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": f"Erro ao processar consulta: {e!s}",
                "intermediate_steps": [],
                "execution_time": elapsed,
            }

    def invoke_agents(
        self,
        query: str,
        agent_names: list[str],
        chat_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Invoca multiplos agentes especialistas EM PARALELO usando ThreadPoolExecutor.

        Args:
            query: Pergunta do usuario
            agent_names: Lista de perspectivas a acionar
            chat_history: Historico da conversa

        Returns:
            Lista de respostas dos agentes (com execution_time para cada)
        """
        # Timer total de execucao
        start_time = time.time()

        # Determinar max_workers (minimo entre num de agentes e config)
        max_workers = min(len(agent_names), settings.agent_max_workers)

        logger.info(
            f"[TIMING] [invoke_agents] INICIADO | "
            f"Executando {len(agent_names)} agente(s) em PARALELO "
            f"com {max_workers} worker(s) | Agentes: {agent_names}"
        )

        responses = []

        # ThreadPoolExecutor para paralelizacao
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks simultaneamente
            future_to_agent = {
                executor.submit(
                    self._invoke_single_agent, agent_name, query, chat_history
                ): agent_name
                for agent_name in agent_names
            }

            # Collect results conforme completam
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result()
                    if result is not None:
                        responses.append(result)
                except Exception as e:
                    logger.error(f"[ERRO] Excecao ao aguardar {agent_name}: {e}")

        # Log final com performance detalhado
        total_elapsed = time.time() - start_time
        avg_time = total_elapsed / len(responses) if responses else 0

        # Calcular tempos individuais de cada agente
        individual_times = [r.get("execution_time", 0) for r in responses]
        max_individual = max(individual_times) if individual_times else 0

        logger.info(
            f"[TIMING] [invoke_agents] CONCLUÍDO em {total_elapsed:.3f}s | "
            f"{len(responses)} agente(s) executados | "
            f"Tempo médio: {avg_time:.3f}s/agente | "
            f"Tempo máximo individual: {max_individual:.3f}s | "
            f"Workers: {max_workers}"
        )

        return responses

    async def _ainvoke_single_agent(
        self, agent_name: str, query: str, chat_history: list[dict[str, str]] | None = None
    ) -> dict[str, Any] | None:
        """
        Invoca um unico agente especialista de forma assincrona.
        Metodo auxiliar para execucao paralela com asyncio.gather().

        Args:
            agent_name: Nome do agente a invocar
            query: Pergunta do usuario
            chat_history: Historico da conversa

        Returns:
            Dicionario com resposta do agente ou None se agente nao encontrado
        """
        if agent_name not in self.agents:
            logger.warning(f"[WARN] Agente '{agent_name}' nao encontrado")
            return None

        agent = self.agents[agent_name]
        agent_start = time.time()

        try:
            # Chamar ainvoke() do agente (async)
            result = await agent.ainvoke(query, chat_history)
            elapsed = time.time() - agent_start

            logger.info(f"[OK] {agent.get_name()} concluido em {elapsed:.2f}s (async)")

            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_time": elapsed,
            }

        except Exception as e:
            elapsed = time.time() - agent_start
            logger.error(f"[ERRO] Erro ao invocar {agent.get_name()} (async): {e}")
            return {
                "agent_name": agent.get_name(),
                "perspective": agent.get_perspective(),
                "response": f"Erro ao processar consulta: {e!s}",
                "intermediate_steps": [],
                "execution_time": elapsed,
            }

    async def ainvoke_agents(
        self,
        query: str,
        agent_names: list[str],
        chat_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Invoca multiplos agentes especialistas EM PARALELO usando asyncio.gather().
        VERSAO ASYNC: 10-15% mais rapida que ThreadPoolExecutor para I/O-bound tasks.

        Args:
            query: Pergunta do usuario
            agent_names: Lista de perspectivas a acionar
            chat_history: Historico da conversa

        Returns:
            Lista de respostas dos agentes (com execution_time para cada)
        """
        # Timer total de execucao
        start_time = time.time()

        logger.info(f"[ASYNC] Executando {len(agent_names)} agente(s) com asyncio.gather()")

        # Criar tasks para todos os agentes
        tasks = [
            self._ainvoke_single_agent(agent_name, query, chat_history)
            for agent_name in agent_names
        ]

        # Executar todos simultaneamente com asyncio.gather()
        # return_exceptions=True garante que erros nao quebrem todo o gather
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filtrar resultados validos (None ou Exception sao ignorados)
        responses = []
        for result in results:
            if result is not None and not isinstance(result, Exception):
                responses.append(result)
            elif isinstance(result, Exception):
                logger.error(f"[ERRO] Excecao durante gather: {result}")

        # Log final com performance
        total_elapsed = time.time() - start_time
        avg_time = total_elapsed / len(responses) if responses else 0

        logger.info(
            f"[OK] {len(responses)} agente(s) executado(s) em {total_elapsed:.2f}s "
            f"(media {avg_time:.2f}s/agente, async com asyncio.gather)"
        )

        return responses

    def synthesize_responses(
        self, original_query: str, agent_responses: list[dict[str, Any]]
    ) -> SynthesisResult:
        """
        Sintetiza múltiplas respostas em uma resposta unificada.

        Args:
            original_query: Pergunta original
            agent_responses: Respostas dos agentes

        Returns:
            Resposta sintetizada
        """
        try:
            # TIMING DETALHADO - SESSAO 43 (2025-11-24)
            synth_start = time.time()

            logger.info(
                f"[TIMING] [SYNTH] INICIADO | {len(agent_responses)} respostas para sintetizar"
            )

            # Formata respostas para o prompt
            formatted_responses = "\n\n".join(
                [
                    f"**{resp['agent_name']} (Perspectiva {resp['perspective'].title()}):**\n{resp['response']}"
                    for resp in agent_responses
                ]
            )

            # Log tamanho do input (causa comum de latência)
            input_chars = len(formatted_responses)
            input_tokens_estimate = input_chars // 4  # ~4 chars por token
            logger.info(
                f"[TIMING] [SYNTH] Input formatado | "
                f"~{input_chars:,} chars (~{input_tokens_estimate:,} tokens estimados) | "
                f"Elapsed: {time.time() - synth_start:.2f}s"
            )

            # FASE 4.9: Capturar tokens para performance monitoring
            # Testar raw LLM para obter metadata (synthesis_chain esconde metadata)
            logger.info(
                f"[TIMING] [SYNTH] Invocando LLM raw para captura de metadata | "
                f"Elapsed: {time.time() - synth_start:.2f}s"
            )

            llm_raw_start = time.time()
            try:
                raw_messages = self.synthesis_prompt.format_messages(
                    original_query=original_query, agent_responses=formatted_responses
                )
                raw_test = self.llm.invoke(raw_messages)

                llm_raw_elapsed = time.time() - llm_raw_start
                logger.info(
                    f"[TIMING] [SYNTH] LLM raw completou em {llm_raw_elapsed:.2f}s | "
                    f"Total elapsed: {time.time() - synth_start:.2f}s"
                )

                if hasattr(raw_test, "response_metadata"):
                    metadata = raw_test.response_metadata
                    token_usage = metadata.get("token_usage", {})
                    if token_usage:
                        model_name = metadata.get("model_name", settings.orchestrator_llm_model)
                        tokens_in = token_usage.get("prompt_tokens", 0)
                        tokens_out = token_usage.get("completion_tokens", 0)
                        track_llm_tokens(tokens_in, tokens_out, model_name)
                        logger.info(
                            f"[TIMING] [SYNTH] Tokens: {model_name} | "
                            f"in={tokens_in:,} out={tokens_out:,} total={tokens_in + tokens_out:,}"
                        )
            except Exception as e:
                logger.warning(f"[PERFORMANCE] [SYNTHESIS] Erro ao capturar tokens: {e}")

            # Chamada principal de síntese (estruturada)
            logger.info(
                f"[TIMING] [SYNTH] Invocando synthesis_chain (structured output) | "
                f"Elapsed: {time.time() - synth_start:.2f}s"
            )

            synth_chain_start = time.time()
            synthesis = self.synthesis_chain.invoke(
                {"original_query": original_query, "agent_responses": formatted_responses}
            )
            synth_chain_elapsed = time.time() - synth_chain_start

            total_synth_elapsed = time.time() - synth_start
            logger.info(
                f"[TIMING] [SYNTH] CONCLUIDO | "
                f"synthesis_chain: {synth_chain_elapsed:.2f}s | "
                f"Total: {total_synth_elapsed:.2f}s | "
                f"confidence: {synthesis.confidence:.2f}"
            )

            return synthesis

        except Exception as e:
            logger.error(f"[ERRO] Erro na síntese: {e}")
            # Fallback: concatena respostas
            fallback_answer = "## Respostas dos Especialistas\n\n" + "\n\n".join(
                [f"### {resp['agent_name']}\n{resp['response']}" for resp in agent_responses]
            )

            return SynthesisResult(
                synthesized_answer=fallback_answer,
                perspectives_covered=[r["perspective"] for r in agent_responses],
                confidence=0.5,
            )

    def process_query(
        self,
        query: str,
        chat_history: list[dict[str, str]] | None = None,
        use_judge: bool = True,
    ) -> dict[str, Any]:
        """
        Processa uma query end-to-end.

        Args:
            query: Pergunta do usuário
            chat_history: Histórico da conversa
            use_judge: Se deve usar Judge Agent para validação

        Returns:
            Resultado completo com resposta sintetizada e metadados
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"[START] {self.name} processando query")
            logger.info(f"{'='*70}")

            # 1. Roteamento
            routing = self.route_query(query)

            # 2. Invocar agentes
            agent_responses = self.invoke_agents(
                query=query, agent_names=routing.agents_to_use, chat_history=chat_history
            )

            if not agent_responses:
                return {
                    "answer": "Nenhum agente pôde processar a consulta.",
                    "perspectives": [],
                    "confidence": 0.0,
                    "routing": routing.model_dump(),
                    "evaluations": [],
                }

            # 3. Síntese
            synthesis = self.synthesize_responses(query, agent_responses)

            # 4. Avaliação (opcional)
            evaluations = []
            if use_judge:
                logger.info("[JUDGE] Executando avaliação com Judge Agent")
                evaluations = self.judge.evaluate_multiple(
                    original_query=query,
                    agent_responses=agent_responses,
                    retrieved_documents="[Documentos recuperados pelos agentes]",
                )

            result = {
                "answer": synthesis.synthesized_answer,
                "perspectives": synthesis.perspectives_covered,
                "confidence": synthesis.confidence,
                "routing": routing.model_dump(),
                "agent_responses": agent_responses,
                "evaluations": (
                    [e["judgment"].model_dump() for e in evaluations] if evaluations else []
                ),
            }

            logger.info(f"{'='*70}")
            logger.info("[OK] Query processada com sucesso")
            logger.info(f"{'='*70}\n")

            return result

        except Exception as e:
            logger.error(f"[ERRO] Erro no processamento: {e}")
            return {
                "answer": f"Erro ao processar consulta: {e!s}",
                "perspectives": [],
                "confidence": 0.0,
                "routing": {},
                "agent_responses": [],
                "evaluations": [],
            }

    def get_name(self) -> str:
        """Retorna o nome do orchestrator."""
        return self.name
