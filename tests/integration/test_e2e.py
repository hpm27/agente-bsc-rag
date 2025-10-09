"""
Testes End-to-End do sistema BSC RAG completo.
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graph.workflow import create_bsc_workflow
from config.settings import settings


class TestE2EWorkflow:
    """Testes end-to-end do workflow completo."""
    
    @pytest.fixture
    def workflow(self):
        """Cria instância do workflow para testes."""
        return create_bsc_workflow()
    
    @pytest.mark.asyncio
    async def test_simple_factual_query(self, workflow):
        """Testa query factual simples."""
        query = "Quais são os principais KPIs da perspectiva financeira?"
        
        result = await workflow.run(query, session_id="test-001")
        
        assert result is not None
        assert "response" in result
        assert result["response"] is not None
        assert len(result["response"]) > 0
        
        metadata = result.get("metadata", {})
        assert "perspectives_used" in metadata
        assert "judge_score" in metadata
        assert metadata["judge_score"] > 0.0
    
    @pytest.mark.asyncio
    async def test_conceptual_query(self, workflow):
        """Testa query conceitual."""
        query = "Como implementar BSC em uma empresa?"
        
        result = await workflow.run(query, session_id="test-002")
        
        assert result is not None
        assert "response" in result
        
        # Deve envolver múltiplas perspectivas
        perspectives = result.get("perspectives", [])
        assert len(perspectives) > 1
    
    @pytest.mark.asyncio
    async def test_comparative_query(self, workflow):
        """Testa query comparativa."""
        query = "Qual a relação entre satisfação de clientes e lucratividade?"
        
        result = await workflow.run(query, session_id="test-003")
        
        assert result is not None
        assert "response" in result
        
        # Deve envolver perspectiva financeira e de clientes
        metadata = result.get("metadata", {})
        perspectives_used = metadata.get("perspectives_used", [])
        assert "financial" in perspectives_used or "customer" in perspectives_used
    
    @pytest.mark.asyncio
    async def test_complex_query(self, workflow):
        """Testa query complexa."""
        query = "Como alinhar objetivos estratégicos com métricas BSC?"
        
        result = await workflow.run(query, session_id="test-004")
        
        assert result is not None
        assert "response" in result
        
        # Query complexa deve ter resposta detalhada
        response = result.get("response", "")
        assert len(response) > 100
        
        # Deve ter score Judge razoável
        metadata = result.get("metadata", {})
        assert metadata.get("judge_score", 0.0) > 0.5
    
    @pytest.mark.asyncio
    async def test_workflow_latency(self, workflow):
        """Testa latência do workflow."""
        import time
        
        query = "O que é Balanced Scorecard?"
        
        start = time.time()
        result = await workflow.run(query, session_id="test-005")
        end = time.time()
        
        latency = end - start
        
        assert result is not None
        # Latência deve ser menor que 10 segundos (MVP)
        assert latency < 10.0, f"Latência muito alta: {latency:.2f}s"
    
    @pytest.mark.asyncio
    async def test_refinement_process(self, workflow):
        """Testa processo de refinamento quando Judge reprova."""
        # Esta query propositalmente vaga deve acionar refinamento
        query = "BSC?"
        
        result = await workflow.run(query, session_id="test-006")
        
        assert result is not None
        metadata = result.get("metadata", {})
        
        # Pode ou não ter refinamento, mas deve completar
        refinement_iterations = metadata.get("refinement_iterations", 0)
        assert refinement_iterations >= 0
        assert refinement_iterations <= 2  # Máximo configurado
    
    @pytest.mark.asyncio
    async def test_multiple_perspectives(self, workflow):
        """Testa ativação de múltiplas perspectivas."""
        query = "Como criar um mapa estratégico BSC completo?"
        
        result = await workflow.run(query, session_id="test-007")
        
        perspectives = result.get("perspectives", [])
        
        # Query abrangente deve ativar várias perspectivas
        assert len(perspectives) >= 2
        
        # Todas as respostas devem ter conteúdo
        for perspective in perspectives:
            assert len(perspective.get("content", "")) > 0
            assert perspective.get("confidence", 0.0) > 0.0


class TestQueryScenarios:
    """Testes de cenários específicos de queries."""
    
    @pytest.fixture
    def workflow(self):
        """Cria instância do workflow para testes."""
        return create_bsc_workflow()
    
    @pytest.mark.asyncio
    async def test_financial_perspective_query(self, workflow):
        """Testa query específica da perspectiva financeira."""
        queries = [
            "Quais métricas financeiras são importantes no BSC?",
            "Como medir ROI no Balanced Scorecard?",
            "Exemplos de KPIs financeiros no BSC?"
        ]
        
        for query in queries:
            result = await workflow.run(query, session_id="test-fin")
            
            assert result is not None
            perspectives_used = result.get("metadata", {}).get("perspectives_used", [])
            assert "financial" in perspectives_used
    
    @pytest.mark.asyncio
    async def test_customer_perspective_query(self, workflow):
        """Testa query específica da perspectiva de clientes."""
        queries = [
            "Como medir satisfação do cliente no BSC?",
            "KPIs de retenção de clientes?",
            "Métricas de valor para o cliente?"
        ]
        
        for query in queries:
            result = await workflow.run(query, session_id="test-cust")
            
            assert result is not None
            perspectives_used = result.get("metadata", {}).get("perspectives_used", [])
            assert "customer" in perspectives_used
    
    @pytest.mark.asyncio
    async def test_process_perspective_query(self, workflow):
        """Testa query específica da perspectiva de processos."""
        queries = [
            "Métricas de eficiência operacional no BSC?",
            "Como medir qualidade de processos?",
            "KPIs de processos internos?"
        ]
        
        for query in queries:
            result = await workflow.run(query, session_id="test-proc")
            
            assert result is not None
            perspectives_used = result.get("metadata", {}).get("perspectives_used", [])
            assert "process" in perspectives_used
    
    @pytest.mark.asyncio
    async def test_learning_perspective_query(self, workflow):
        """Testa query específica da perspectiva de aprendizado."""
        queries = [
            "Métricas de desenvolvimento de colaboradores?",
            "Como medir capacitação no BSC?",
            "KPIs de aprendizado organizacional?"
        ]
        
        for query in queries:
            result = await workflow.run(query, session_id="test-learn")
            
            assert result is not None
            perspectives_used = result.get("metadata", {}).get("perspectives_used", [])
            assert "learning" in perspectives_used


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "-s"])

