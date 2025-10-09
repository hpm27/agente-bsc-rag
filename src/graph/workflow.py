"""
Workflow LangGraph para orquestração do sistema BSC.
"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from loguru import logger

from .states import BSCState, AgentResponse, JudgeEvaluation, PerspectiveType
from src.agents.orchestrator import Orchestrator
from src.agents.financial_agent import FinancialAgent
from src.agents.customer_agent import CustomerAgent
from src.agents.process_agent import ProcessAgent
from src.agents.learning_agent import LearningAgent
from src.agents.judge_agent import JudgeAgent
from config.settings import settings


class BSCWorkflow:
    """Workflow de execução do sistema BSC com LangGraph."""
    
    def __init__(self):
        """Inicializa o workflow com todos os agentes."""
        self.orchestrator = Orchestrator()
        self.agents = {
            PerspectiveType.FINANCIAL: FinancialAgent(),
            PerspectiveType.CUSTOMER: CustomerAgent(),
            PerspectiveType.PROCESS: ProcessAgent(),
            PerspectiveType.LEARNING: LearningAgent(),
        }
        self.judge = JudgeAgent()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de execução."""
        workflow = StateGraph(BSCState)
        
        # Adicionar nós
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("route_agents", self.route_agents)
        workflow.add_node("execute_agents", self.execute_agents)
        workflow.add_node("aggregate", self.aggregate_responses)
        workflow.add_node("judge", self.judge_responses)
        workflow.add_node("finalize", self.finalize_response)
        
        # Definir fluxo
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "route_agents")
        workflow.add_edge("route_agents", "execute_agents")
        workflow.add_edge("execute_agents", "aggregate")
        workflow.add_edge("aggregate", "judge")
        
        # Lógica condicional após judge
        workflow.add_conditional_edges(
            "judge",
            self.should_refine,
            {
                "refine": "execute_agents",  # Volta para executar agentes novamente
                "finalize": "finalize",      # Prossegue para finalização
            }
        )
        
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def analyze_query(self, state: BSCState) -> Dict[str, Any]:
        """Analisa a query para determinar complexidade e tipo."""
        logger.info(f"Analisando query: {state.query}")
        
        analysis = await self.orchestrator.analyze_query(state.query)
        
        return {
            "query_type": analysis.get("type", "factual"),
            "complexity": analysis.get("complexity", "moderate"),
            "metadata": {
                **state.metadata,
                "analysis": analysis
            }
        }
    
    async def route_agents(self, state: BSCState) -> Dict[str, Any]:
        """Determina quais agentes/perspectivas são relevantes."""
        logger.info(f"Roteando query para perspectivas relevantes")
        
        relevant_perspectives = await self.orchestrator.route_to_perspectives(
            query=state.query,
            query_type=state.query_type
        )
        
        logger.info(f"Perspectivas selecionadas: {relevant_perspectives}")
        
        return {
            "relevant_perspectives": relevant_perspectives
        }
    
    async def execute_agents(self, state: BSCState) -> Dict[str, Any]:
        """Executa os agentes especialistas em paralelo."""
        logger.info(f"Executando {len(state.relevant_perspectives)} agentes especialistas")
        
        responses = []
        
        # Executar agentes em paralelo (simulado com loop por simplicidade)
        for perspective in state.relevant_perspectives:
            agent = self.agents.get(perspective)
            if agent:
                try:
                    response = await agent.process(
                        query=state.query,
                        context=state.metadata.get("context", {})
                    )
                    
                    agent_response = AgentResponse(
                        perspective=perspective,
                        content=response.get("content", ""),
                        confidence=response.get("confidence", 0.5),
                        sources=response.get("sources", []),
                        reasoning=response.get("reasoning", None)
                    )
                    
                    responses.append(agent_response)
                    logger.info(f"Agente {perspective.value} completou com confiança {agent_response.confidence}")
                    
                except Exception as e:
                    logger.error(f"Erro ao executar agente {perspective.value}: {e}")
        
        return {
            "agent_responses": responses
        }
    
    async def aggregate_responses(self, state: BSCState) -> Dict[str, Any]:
        """Agrega as respostas dos múltiplos agentes."""
        logger.info(f"Agregando {len(state.agent_responses)} respostas")
        
        aggregated = await self.orchestrator.aggregate_responses(
            query=state.query,
            responses=[
                {
                    "perspective": r.perspective.value,
                    "content": r.content,
                    "confidence": r.confidence
                }
                for r in state.agent_responses
            ]
        )
        
        return {
            "aggregated_response": aggregated
        }
    
    async def judge_responses(self, state: BSCState) -> Dict[str, Any]:
        """Avalia a qualidade da resposta agregada."""
        logger.info("Avaliando resposta com Judge Agent")
        
        evaluation = await self.judge.evaluate(
            query=state.query,
            response=state.aggregated_response,
            sources=[
                source
                for agent_response in state.agent_responses
                for source in agent_response.sources
            ]
        )
        
        judge_eval = JudgeEvaluation(
            approved=evaluation.get("approved", False),
            score=evaluation.get("score", 0.0),
            feedback=evaluation.get("feedback", ""),
            issues=evaluation.get("issues", []),
            suggestions=evaluation.get("suggestions", [])
        )
        
        logger.info(f"Judge avaliou com score {judge_eval.score} - Aprovado: {judge_eval.approved}")
        
        return {
            "judge_evaluation": judge_eval,
            "needs_refinement": not judge_eval.approved and state.refinement_iteration < state.max_refinement_iterations
        }
    
    def should_refine(self, state: BSCState) -> str:
        """Decide se precisa refinar ou pode finalizar."""
        if state.needs_refinement:
            logger.info(f"Refinando resposta (iteração {state.refinement_iteration + 1})")
            return "refine"
        else:
            logger.info("Resposta aprovada, finalizando")
            return "finalize"
    
    async def finalize_response(self, state: BSCState) -> Dict[str, Any]:
        """Finaliza e formata a resposta."""
        logger.info("Finalizando resposta")
        
        final_response = state.aggregated_response
        
        # Adicionar metadados úteis
        metadata = {
            **state.metadata,
            "perspectives_used": [p.value for p in state.relevant_perspectives],
            "judge_score": state.judge_evaluation.score if state.judge_evaluation else 0.0,
            "refinement_iterations": state.refinement_iteration,
            "total_sources": sum(len(r.sources) for r in state.agent_responses)
        }
        
        return {
            "final_response": final_response,
            "is_complete": True,
            "metadata": metadata
        }
    
    async def run(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """
        Executa o workflow completo.
        
        Args:
            query: Query do usuário
            session_id: ID da sessão (opcional)
            
        Returns:
            Dict com a resposta final e metadados
        """
        logger.info(f"Iniciando workflow BSC para query: {query}")
        
        initial_state = BSCState(
            query=query,
            session_id=session_id
        )
        
        # Executar grafo
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info("Workflow BSC completado")
        
        return {
            "response": final_state.final_response,
            "metadata": final_state.metadata,
            "judge_evaluation": final_state.judge_evaluation.dict() if final_state.judge_evaluation else None,
            "perspectives": [r.dict() for r in final_state.agent_responses]
        }


def create_bsc_workflow() -> BSCWorkflow:
    """
    Factory function para criar uma instância do workflow BSC.
    
    Returns:
        BSCWorkflow configurado e pronto para uso
    """
    return BSCWorkflow()

