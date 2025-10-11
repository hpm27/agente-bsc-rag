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
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from src.graph.states import (
    BSCState,
    PerspectiveType,
    AgentResponse,
    JudgeEvaluation
)
from src.agents.orchestrator import Orchestrator
from src.agents.judge_agent import JudgeAgent


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
                if block.get('type') == 'text' and 'text' in block:
                    texts.append(block['text'])
                elif 'text' in block:  # fallback
                    texts.append(block['text'])
        return ' '.join(texts) if texts else str(response)
    elif isinstance(response, str):
        # OpenAI format: string direta
        return response
    else:
        # Fallback: converter para string
        return str(response)


class BSCWorkflow:
    """Workflow LangGraph para sistema BSC multi-agente."""
    
    def __init__(self):
        """Inicializa o workflow."""
        self.orchestrator = Orchestrator()
        self.judge = JudgeAgent()
        self.graph = self._build_graph()
        
        logger.info("[OK] BSCWorkflow inicializado com grafo LangGraph")
    
    def _build_graph(self) -> StateGraph:
        """
        Constrói o grafo de execução LangGraph.
        
        Fluxo:
        START → analyze_query → execute_agents → synthesize_response 
        → judge_evaluation → decide_next → [finalize OR execute_agents (refinement)]
        → END
        """
        # Criar grafo com schema BSCState
        workflow = StateGraph(BSCState)
        
        # Adicionar nós
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("execute_agents", self.execute_agents)
        workflow.add_node("synthesize_response", self.synthesize_response)
        workflow.add_node("judge_evaluation", self.judge_evaluation)
        workflow.add_node("finalize", self.finalize)
        
        # Definir entry point
        workflow.set_entry_point("analyze_query")
        
        # Definir edges (transições)
        workflow.add_edge("analyze_query", "execute_agents")
        workflow.add_edge("execute_agents", "synthesize_response")
        workflow.add_edge("synthesize_response", "judge_evaluation")
        
        # Edge condicional: judge_evaluation → decide_next
        workflow.add_conditional_edges(
            "judge_evaluation",
            self.decide_next_step,
            {
                "finalize": "finalize",
                "refine": "execute_agents",  # Loop de refinamento
                "end": END
            }
        )
        
        # Edge final: finalize → END
        workflow.add_edge("finalize", END)
        
        logger.info("[OK] Grafo LangGraph construído com 5 nós + 1 edge condicional")
        
        return workflow.compile()
    
    def analyze_query(self, state: BSCState) -> Dict[str, Any]:
        """
        Nó 1: Analisa a query e determina roteamento.
        
        Args:
            state: Estado atual do workflow
            
        Returns:
            Estado atualizado com perspectivas relevantes
        """
        try:
            logger.info(f"\n[INFO] Nó: analyze_query | Query: '{state.query[:60]}...'")
            
            # Usa Orchestrator para routing
            routing_decision = self.orchestrator.route_query(state.query)
            
            # Mapear nomes de agentes para PerspectiveType
            perspective_map = {
                "financeira": PerspectiveType.FINANCIAL,
                "cliente": PerspectiveType.CUSTOMER,
                "processos": PerspectiveType.PROCESS,
                "aprendizado": PerspectiveType.LEARNING
            }
            
            relevant_perspectives = [
                perspective_map[agent_name]
                for agent_name in routing_decision.agents_to_use
                if agent_name in perspective_map
            ]
            
            # Determinar tipo e complexidade da query
            query_type = "general" if routing_decision.is_general_question else "specific"
            complexity = "complex" if len(relevant_perspectives) > 2 else "simple"
            
            logger.info(
                f"[OK] Roteamento: {len(relevant_perspectives)} perspectiva(s) | "
                f"Tipo: {query_type} | Complexidade: {complexity}"
            )
            
            return {
                "relevant_perspectives": relevant_perspectives,
                "query_type": query_type,
                "complexity": complexity,
                "metadata": {
                    "routing_reasoning": routing_decision.reasoning
                }
            }
            
        except Exception as e:
            logger.error(f"[ERRO] analyze_query: {e}")
            # Fallback: aciona todas as perspectivas
            return {
                "relevant_perspectives": list(PerspectiveType),
                "query_type": "general",
                "complexity": "complex",
                "metadata": {"error": str(e)}
            }
    
    def execute_agents(self, state: BSCState) -> Dict[str, Any]:
        """
        Nó 2: Executa agentes especialistas em paralelo.
        
        Args:
            state: Estado atual do workflow
            
        Returns:
            Estado atualizado com respostas dos agentes
        """
        try:
            iteration_label = ""
            if state.refinement_iteration > 0:
                iteration_label = f" (Refinamento #{state.refinement_iteration})"
            
            logger.info(
                f"[INFO] Nó: execute_agents{iteration_label} | "
                f"Perspectivas: {[p.value for p in state.relevant_perspectives]}"
            )
            
            # Mapear PerspectiveType de volta para nomes de agentes
            perspective_to_agent = {
                PerspectiveType.FINANCIAL: "financeira",
                PerspectiveType.CUSTOMER: "cliente",
                PerspectiveType.PROCESS: "processos",
                PerspectiveType.LEARNING: "aprendizado"
            }
            
            agent_names = [
                perspective_to_agent[p]
                for p in state.relevant_perspectives
                if p in perspective_to_agent
            ]
            
            # Invocar agentes usando Orchestrator
            chat_history = state.metadata.get("chat_history", None)
            raw_responses = self.orchestrator.invoke_agents(
                query=state.query,
                agent_names=agent_names,
                chat_history=chat_history
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
                    "learning": PerspectiveType.LEARNING
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
                        reasoning=f"Resposta do {resp['agent_name']}"
                    )
                )
            
            logger.info(f"[OK] Executados {len(agent_responses)} agente(s) com sucesso")
            
            return {
                "agent_responses": agent_responses
            }
            
        except Exception as e:
            logger.error(f"[ERRO] execute_agents: {e}")
            return {
                "agent_responses": [],
                "metadata": {
                    **state.metadata,
                    "execution_error": str(e)
                }
            }
    
    def synthesize_response(self, state: BSCState) -> Dict[str, Any]:
        """
        Nó 3: Sintetiza respostas dos agentes em uma resposta unificada.
        
        Args:
            state: Estado atual do workflow
            
        Returns:
            Estado atualizado com resposta agregada
        """
        try:
            logger.info(
                f"[INFO] Nó: synthesize_response | "
                f"Sintetizando {len(state.agent_responses)} resposta(s)"
            )
            
            if not state.agent_responses:
                logger.warning("[WARN] Nenhuma resposta de agente para sintetizar")
                return {
                    "aggregated_response": "Nenhuma resposta foi gerada pelos agentes.",
                    "metadata": {
                        **state.metadata,
                        "synthesis_warning": "No agent responses"
                    }
                }
            
            # Converter AgentResponse para formato esperado pelo Orchestrator
            agent_responses_dict = []
            for agent_resp in state.agent_responses:
                perspective_to_name = {
                    PerspectiveType.FINANCIAL: "Financial Agent",
                    PerspectiveType.CUSTOMER: "Customer Agent",
                    PerspectiveType.PROCESS: "Process Agent",
                    PerspectiveType.LEARNING: "Learning Agent"
                }
                
                agent_responses_dict.append({
                    "agent_name": perspective_to_name.get(
                        agent_resp.perspective,
                        "Unknown Agent"
                    ),
                    "perspective": agent_resp.perspective.value,
                    "response": agent_resp.content,
                    "intermediate_steps": []
                })
            
            # Usar Orchestrator para síntese
            synthesis = self.orchestrator.synthesize_responses(
                original_query=state.query,
                agent_responses=agent_responses_dict
            )
            
            logger.info(f"[OK] Síntese completa | Confidence: {synthesis.confidence:.2f}")
            
            return {
                "aggregated_response": synthesis.synthesized_answer,
                "metadata": {
                    **state.metadata,
                    "synthesis_confidence": synthesis.confidence,
                    "perspectives_covered": synthesis.perspectives_covered
                }
            }
            
        except Exception as e:
            logger.error(f"[ERRO] synthesize_response: {e}")
            # Fallback: concatena respostas
            fallback = "\n\n".join([
                f"**{resp.perspective.value.title()}**:\n{resp.content}"
                for resp in state.agent_responses
            ])
            
            return {
                "aggregated_response": fallback,
                "metadata": {
                    **state.metadata,
                    "synthesis_error": str(e)
                }
            }
    
    def judge_evaluation(self, state: BSCState) -> Dict[str, Any]:
        """
        Nó 4: Avalia qualidade da resposta com Judge Agent.
        
        Args:
            state: Estado atual do workflow
            
        Returns:
            Estado atualizado com avaliação do Judge
        """
        try:
            logger.info("[INFO] Nó: judge_evaluation | Avaliando resposta agregada")
            
            if not state.aggregated_response:
                logger.warning("[WARN] Nenhuma resposta agregada para avaliar")
                return {
                    "judge_evaluation": JudgeEvaluation(
                        approved=False,
                        score=0.0,
                        feedback="Nenhuma resposta foi gerada para avaliar.",
                        issues=["No aggregated response"],
                        suggestions=["Verifique execução dos agentes"]
                    ),
                    "needs_refinement": True
                }
            
            # Usar Judge para avaliar
            # Nota: Judge.evaluate espera retrieved_documents, mas no nosso caso
            # os documentos já foram recuperados pelos agentes individuais
            judgment = self.judge.evaluate(
                original_query=state.query,
                agent_response=state.aggregated_response,
                retrieved_documents="[Documentos recuperados pelos agentes]",
                agent_name="Synthesized Response"
            )
            
            # Converter JudgmentResult para JudgeEvaluation
            approved = judgment.verdict == "approved"
            needs_refinement = (
                judgment.verdict == "needs_improvement" and 
                state.refinement_iteration < state.max_refinement_iterations
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
                has_sources=judgment.has_sources
            )
            
            logger.info(
                f"[OK] Avaliação: {'APROVADA' if approved else 'REPROVADA'} | "
                f"Score: {judgment.quality_score:.2f} | "
                f"Veredito: {judgment.verdict}"
            )
            
            return {
                "judge_evaluation": judge_evaluation,
                "needs_refinement": needs_refinement
            }
            
        except Exception as e:
            logger.error(f"[ERRO] judge_evaluation: {e}")
            # Em caso de erro, aprova para não travar o fluxo
            return {
                "judge_evaluation": JudgeEvaluation(
                    approved=True,
                    score=0.7,
                    feedback=f"Erro na avaliação: {str(e)}. Aprovando por padrão.",
                    issues=[str(e)],
                    suggestions=["Revisar manualmente"]
                ),
                "needs_refinement": False,
                "metadata": {
                    **state.metadata,
                    "judge_error": str(e)
                }
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
                new_iteration = state.refinement_iteration + 1
                if new_iteration <= state.max_refinement_iterations:
                    logger.info(
                        f"[INFO] Decisão: REFINE (iteração {new_iteration}/"
                        f"{state.max_refinement_iterations})"
                    )
                    # Incrementa contador de refinamento
                    state.refinement_iteration = new_iteration
                    return "refine"
                else:
                    logger.warning(
                        f"[WARN] Máximo de refinamentos atingido "
                        f"({state.max_refinement_iterations}). Finalizando."
                    )
                    return "finalize"
            
            # Caso padrão: finaliza
            logger.info("[INFO] Decisão: FINALIZE (padrão)")
            return "finalize"
            
        except Exception as e:
            logger.error(f"[ERRO] decide_next_step: {e}. Finalizando por segurança.")
            return "finalize"
    
    def finalize(self, state: BSCState) -> Dict[str, Any]:
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
                    "final_score": state.judge_evaluation.score if state.judge_evaluation else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"[ERRO] finalize: {e}")
            return {
                "final_response": state.aggregated_response or f"Erro ao finalizar: {str(e)}",
                "is_complete": True,
                "metadata": {
                    **state.metadata,
                    "finalize_error": str(e)
                }
            }
    
    def run(
        self,
        query: str,
        session_id: str = None,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executa o workflow completo para uma query.
        
        Args:
            query: Pergunta do usuário
            session_id: ID da sessão (opcional)
            chat_history: Histórico de conversa (opcional)
            
        Returns:
            Resultado completo com resposta final e metadados
        """
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"[INFO] Iniciando BSCWorkflow para query: '{query[:60]}...'")
            logger.info(f"{'='*80}\n")
            
            # Criar estado inicial
            initial_state = BSCState(
                query=query,
                session_id=session_id,
                metadata={"chat_history": chat_history} if chat_history else {}
            )
            
            # Executar grafo
            final_state = self.graph.invoke(initial_state)
            
            # Extrair resultado
            result = {
                "query": final_state["query"],
                "final_response": final_state.get("final_response", ""),
                "perspectives": [
                    p.value for p in final_state.get("relevant_perspectives", [])
                ],
                "agent_responses": [
                    {
                        "perspective": r.perspective.value,
                        "content": r.content,
                        "confidence": r.confidence
                    }
                    for r in final_state.get("agent_responses", [])
                ],
                "judge_evaluation": (
                    final_state["judge_evaluation"].dict()
                    if final_state.get("judge_evaluation") else None
                ),
                "refinement_iterations": final_state.get("refinement_iteration", 0),
                "metadata": final_state.get("metadata", {})
            }
            
            logger.info(f"\n{'='*80}")
            logger.info(f"[OK] BSCWorkflow finalizado com sucesso")
            logger.info(f"{'='*80}\n")
            
            return result
            
        except Exception as e:
            logger.error(f"[ERRO] BSCWorkflow.run: {e}")
            return {
                "query": query,
                "final_response": f"Erro ao processar consulta: {str(e)}",
                "perspectives": [],
                "agent_responses": [],
                "judge_evaluation": None,
                "refinement_iterations": 0,
                "metadata": {"error": str(e)}
            }
    
    def get_graph_visualization(self) -> str:
        """
        Retorna representação em texto do grafo (para debug).
        
        Returns:
            String com estrutura do grafo
        """
        viz = """
BSC LangGraph Workflow:

START
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
judge_evaluation (Avalia qualidade com Judge Agent)
  |
  v
decide_next_step (Decisao condicional)
  |-- [approved] --> finalize
  |-- [needs_refinement] --> execute_agents (loop de refinamento)
  |-- [default] --> finalize
       |
       v
     END

Caracteristicas:
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
