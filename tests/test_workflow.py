"""
Testes para o LangGraph Workflow BSC.
"""
import pytest
from src.graph.workflow import BSCWorkflow, get_workflow
from src.graph.states import BSCState, PerspectiveType


class TestBSCWorkflow:
    """Suite de testes para BSCWorkflow."""
    
    @pytest.fixture
    def workflow(self):
        """Fixture que retorna instância do workflow."""
        return BSCWorkflow()
    
    def test_workflow_initialization(self, workflow):
        """Testa inicialização do workflow."""
        assert workflow is not None
        assert workflow.orchestrator is not None
        assert workflow.judge is not None
        assert workflow.graph is not None
    
    def test_get_workflow_singleton(self):
        """Testa função singleton get_workflow."""
        workflow1 = get_workflow()
        workflow2 = get_workflow()
        assert workflow1 is workflow2  # Mesma instância
    
    def test_analyze_query_node(self, workflow):
        """Testa nó analyze_query."""
        state = BSCState(
            query="Quais são os principais KPIs da perspectiva financeira?"
        )
        
        result = workflow.analyze_query(state)
        
        assert "relevant_perspectives" in result
        assert len(result["relevant_perspectives"]) > 0
        assert "query_type" in result
        assert "complexity" in result
    
    def test_workflow_run_simple_query(self, workflow):
        """Testa execução completa com query simples."""
        result = workflow.run(
            query="O que é Balanced Scorecard?",
            session_id="test-session-001"
        )
        
        # Verificar estrutura da resposta
        assert "query" in result
        assert "final_response" in result
        assert "perspectives" in result
        assert "agent_responses" in result
        assert "judge_evaluation" in result
        assert "refinement_iterations" in result
        
        # Verificar conteúdo
        assert result["query"] == "O que é Balanced Scorecard?"
        assert len(result["final_response"]) > 0
        assert isinstance(result["perspectives"], list)
        assert isinstance(result["agent_responses"], list)
    
    def test_workflow_run_specific_perspective(self, workflow):
        """Testa workflow com query específica de uma perspectiva."""
        result = workflow.run(
            query="Como melhorar o ROI da empresa?"
        )
        
        # Deve acionar perspectiva financeira
        assert "final_response" in result
        assert len(result["agent_responses"]) >= 1
        
        # Verificar se perspectiva financeira foi acionada
        perspectives = result.get("perspectives", [])
        assert "financial" in perspectives or "financeira" in perspectives
    
    def test_workflow_run_multiple_perspectives(self, workflow):
        """Testa workflow com query que envolve múltiplas perspectivas."""
        result = workflow.run(
            query="Como a satisfação do cliente impacta a lucratividade?"
        )
        
        # Deve acionar pelo menos 2 perspectivas
        assert len(result["agent_responses"]) >= 2
        
        # Verificar se múltiplas perspectivas foram consultadas
        perspectives = result.get("perspectives", [])
        assert len(perspectives) >= 2
    
    def test_workflow_with_chat_history(self, workflow):
        """Testa workflow com histórico de conversa."""
        chat_history = [
            {"role": "user", "content": "O que é BSC?"},
            {"role": "assistant", "content": "BSC é uma metodologia..."}
        ]
        
        result = workflow.run(
            query="Quais são as 4 perspectivas?",
            chat_history=chat_history
        )
        
        assert "final_response" in result
        assert len(result["final_response"]) > 0
    
    def test_workflow_graph_visualization(self, workflow):
        """Testa visualização do grafo."""
        viz = workflow.get_graph_visualization()
        
        assert isinstance(viz, str)
        assert "START" in viz
        assert "END" in viz
        assert "analyze_query" in viz
        assert "execute_agents" in viz
        assert "synthesize_response" in viz
        assert "judge_evaluation" in viz
        assert "finalize" in viz
    
    def test_execute_agents_node(self, workflow):
        """Testa nó execute_agents."""
        state = BSCState(
            query="Quais KPIs financeiros são importantes?",
            relevant_perspectives=[PerspectiveType.FINANCIAL]
        )
        
        result = workflow.execute_agents(state)
        
        assert "agent_responses" in result
        assert isinstance(result["agent_responses"], list)
    
    def test_synthesize_response_node(self, workflow):
        """Testa nó synthesize_response."""
        from src.graph.states import AgentResponse
        
        state = BSCState(
            query="O que é BSC?",
            agent_responses=[
                AgentResponse(
                    perspective=PerspectiveType.FINANCIAL,
                    content="BSC ajuda a medir performance financeira...",
                    confidence=0.9
                ),
                AgentResponse(
                    perspective=PerspectiveType.CUSTOMER,
                    content="BSC inclui métricas de satisfação do cliente...",
                    confidence=0.85
                )
            ]
        )
        
        result = workflow.synthesize_response(state)
        
        assert "aggregated_response" in result
        assert len(result["aggregated_response"]) > 0
    
    def test_judge_evaluation_node(self, workflow):
        """Testa nó judge_evaluation."""
        state = BSCState(
            query="O que é BSC?",
            aggregated_response="Balanced Scorecard é uma metodologia estratégica..."
        )
        
        result = workflow.judge_evaluation(state)
        
        assert "judge_evaluation" in result
        assert result["judge_evaluation"] is not None
        assert "needs_refinement" in result
    
    def test_decide_next_step_approved(self, workflow):
        """Testa decisão quando Judge aprova."""
        from src.graph.states import JudgeEvaluation
        
        state = BSCState(
            query="Teste",
            judge_evaluation=JudgeEvaluation(
                approved=True,
                score=0.9,
                feedback="Excelente resposta"
            )
        )
        
        decision = workflow.decide_next_step(state)
        assert decision == "finalize"
    
    def test_decide_next_step_needs_refinement(self, workflow):
        """Testa decisão quando Judge reprova e precisa refinamento."""
        from src.graph.states import JudgeEvaluation
        
        state = BSCState(
            query="Teste",
            judge_evaluation=JudgeEvaluation(
                approved=False,
                score=0.6,
                feedback="Precisa melhorar"
            ),
            needs_refinement=True,
            refinement_iteration=0,
            max_refinement_iterations=2
        )
        
        decision = workflow.decide_next_step(state)
        assert decision == "refine"
    
    def test_decide_next_step_max_iterations(self, workflow):
        """Testa decisão quando atinge máximo de refinamentos."""
        from src.graph.states import JudgeEvaluation
        
        state = BSCState(
            query="Teste",
            judge_evaluation=JudgeEvaluation(
                approved=False,
                score=0.6,
                feedback="Ainda precisa melhorar"
            ),
            needs_refinement=True,
            refinement_iteration=2,
            max_refinement_iterations=2
        )
        
        decision = workflow.decide_next_step(state)
        assert decision == "finalize"  # Finaliza pois atingiu máximo
    
    def test_finalize_node(self, workflow):
        """Testa nó finalize."""
        from src.graph.states import JudgeEvaluation
        
        state = BSCState(
            query="Teste",
            aggregated_response="Resposta final sintetizada...",
            judge_evaluation=JudgeEvaluation(
                approved=True,
                score=0.95,
                feedback="Aprovado"
            ),
            refinement_iteration=0
        )
        
        result = workflow.finalize(state)
        
        assert "final_response" in result
        assert "is_complete" in result
        assert result["is_complete"] is True


@pytest.mark.integration
class TestBSCWorkflowIntegration:
    """Testes de integração que requerem APIs reais."""
    
    def test_full_workflow_real_query(self):
        """
        Teste de integração completo com query real.
        
        Nota: Requer:
        - OPENAI_API_KEY configurada
        - ANTHROPIC_API_KEY configurada
        - COHERE_API_KEY configurada
        - Qdrant rodando (docker-compose up)
        - Knowledge base indexada
        """
        workflow = get_workflow()
        
        result = workflow.run(
            query="Quais são os 4 pilares do Balanced Scorecard e como eles se relacionam?",
            session_id="integration-test-001"
        )
        
        # Verificações básicas
        assert result is not None
        assert "final_response" in result
        assert len(result["final_response"]) > 100  # Resposta substancial
        
        # Deve ter acionado múltiplas perspectivas para essa query
        assert len(result["agent_responses"]) >= 3
        
        # Deve ter avaliação do Judge
        assert result["judge_evaluation"] is not None
        
        # Print resultado para inspeção manual
        print("\n" + "="*80)
        print("RESULTADO DO TESTE DE INTEGRAÇÃO")
        print("="*80)
        print(f"\nQuery: {result['query']}")
        print(f"\nPerspectivas consultadas: {result['perspectives']}")
        print(f"\nRefinamentos: {result['refinement_iterations']}")
        print(f"\nJudge Score: {result['judge_evaluation']['score']}")
        print(f"\nResposta Final:\n{result['final_response']}")
        print("="*80 + "\n")


if __name__ == "__main__":
    """Executa testes básicos sem pytest."""
    print("Executando testes básicos do BSCWorkflow...\n")
    
    # Teste 1: Inicialização
    print("[TESTE] Inicialização do workflow...")
    workflow = BSCWorkflow()
    print("[OK] Workflow inicializado\n")
    
    # Teste 2: Singleton
    print("[TESTE] Singleton get_workflow...")
    w1 = get_workflow()
    w2 = get_workflow()
    assert w1 is w2
    print("[OK] Singleton funcionando\n")
    
    # Teste 3: Visualização do grafo
    print("[TESTE] Visualização do grafo...")
    viz = workflow.get_graph_visualization()
    print(viz)
    print("[OK] Visualização gerada\n")
    
    # Teste 4: Query simples (se APIs configuradas)
    try:
        print("[TESTE] Executando query simples...")
        result = workflow.run(
            query="O que é Balanced Scorecard?",
            session_id="test-001"
        )
        print(f"[OK] Query executada")
        print(f"Perspectivas: {result['perspectives']}")
        print(f"Refinamentos: {result['refinement_iterations']}")
        print(f"Resposta (primeiros 200 chars): {result['final_response'][:200]}...\n")
    except Exception as e:
        print(f"[WARN] Teste com API falhou (esperado se APIs não configuradas): {e}\n")
    
    print("="*80)
    print("[OK] Todos os testes básicos concluídos!")
    print("="*80)

