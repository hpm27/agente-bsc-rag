"""
Testes End-to-End do sistema BSC RAG completo.
"""
import pytest
import asyncio
import sys
from pathlib import Path
from loguru import logger

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.graph.workflow import get_workflow
from config.settings import settings


class TestE2EWorkflow:
    """Testes end-to-end do workflow completo."""
    
    @pytest.fixture
    def workflow(self):
        """Cria instância do workflow para testes."""
        return get_workflow()
    
    def test_simple_factual_query(self, workflow):
        """Testa query factual simples."""
        query = "Quais são os principais KPIs da perspectiva financeira?"
        
        result = workflow.run(query, session_id="test-001")
        
        assert result is not None
        assert "final_response" in result
        assert result["final_response"] is not None
        assert len(result["final_response"]) > 0
        
        metadata = result.get("metadata", {})
        assert "perspectives_covered" in metadata
        assert "final_score" in metadata
        assert metadata["final_score"] > 0.0
    
    def test_conceptual_query(self, workflow):
        """Testa query conceitual."""
        query = "Como implementar BSC em uma empresa?"
        
        result = workflow.run(query, session_id="test-002")
        
        assert result is not None
        assert "final_response" in result
        
        # Deve envolver múltiplas perspectivas
        perspectives = result.get("perspectives", [])
        assert len(perspectives) > 1
    
    def test_comparative_query(self, workflow):
        """Testa query comparativa."""
        query = "Qual a relação entre satisfação de clientes e lucratividade?"
        
        result = workflow.run(query, session_id="test-003")
        
        assert result is not None
        assert "final_response" in result
        
        # Deve envolver perspectiva financeira e de clientes
        metadata = result.get("metadata", {})
        perspectives_covered = metadata.get("perspectives_covered", [])
        assert "financial" in perspectives_covered or "customer" in perspectives_covered
    
    def test_complex_query(self, workflow):
        """Testa query complexa."""
        query = "Como alinhar objetivos estratégicos com métricas BSC?"
        
        result = workflow.run(query, session_id="test-004")
        
        assert result is not None
        assert "final_response" in result
        
        # Query complexa deve ter resposta detalhada
        response = result.get("response", "")
        assert len(response) > 100
        
        # Deve ter score Judge razoável
        metadata = result.get("metadata", {})
        assert metadata.get("final_score", 0.0) > 0.5
    
    def test_workflow_latency(self, workflow):
        """Testa latência do workflow."""
        import time
        
        query = "O que é Balanced Scorecard?"
        
        start = time.time()
        result = workflow.run(query, session_id="test-005")
        end = time.time()
        
        latency = end - start
        
        assert result is not None
        # Latência deve ser menor que 10 segundos (MVP)
        assert latency < 10.0, f"Latência muito alta: {latency:.2f}s"
    
    def test_refinement_process(self, workflow):
        """Testa processo de refinamento quando Judge reprova."""
        # Esta query propositalmente vaga deve acionar refinamento
        query = "BSC?"
        
        result = workflow.run(query, session_id="test-006")
        
        assert result is not None
        metadata = result.get("metadata", {})
        
        # Pode ou não ter refinamento, mas deve completar
        refinement_iterations = metadata.get("refinement_iterations", 0)
        assert refinement_iterations >= 0
        assert refinement_iterations <= 2  # Máximo configurado
    
    def test_multiple_perspectives(self, workflow):
        """Testa ativação de múltiplas perspectivas."""
        query = "Como criar um mapa estratégico BSC completo?"
        
        result = workflow.run(query, session_id="test-007")
        
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
        return get_workflow()
    
    def test_financial_perspective_query(self, workflow):
        """Testa query específica da perspectiva financeira."""
        queries = [
            "Quais métricas financeiras são importantes no BSC?",
            "Como medir ROI no Balanced Scorecard?",
            "Exemplos de KPIs financeiros no BSC?"
        ]
        
        for query in queries:
            result = workflow.run(query, session_id="test-fin")
            
            assert result is not None
            perspectives_covered = result.get("metadata", {}).get("perspectives_covered", [])
            assert any(p.lower() == "financial" for p in perspectives_covered)
    
    def test_customer_perspective_query(self, workflow):
        """Testa query específica da perspectiva de clientes."""
        queries = [
            "Como medir satisfação do cliente no BSC?",
            "KPIs de retenção de clientes?",
            "Métricas de valor para o cliente?"
        ]
        
        for query in queries:
            result = workflow.run(query, session_id="test-cust")
            
            assert result is not None
            perspectives_covered = result.get("metadata", {}).get("perspectives_covered", [])
            assert any(p.lower() == "customer" for p in perspectives_covered)
    
    def test_process_perspective_query(self, workflow):
        """Testa query específica da perspectiva de processos."""
        queries = [
            "Métricas de eficiência operacional no BSC?",
            "Como medir qualidade de processos?",
            "KPIs de processos internos?"
        ]
        
        for query in queries:
            result = workflow.run(query, session_id="test-proc")
            
            assert result is not None
            perspectives_covered = result.get("metadata", {}).get("perspectives_covered", [])
            assert any(p.lower() == "process" for p in perspectives_covered)
    
    def test_learning_perspective_query(self, workflow):
        """Testa query específica da perspectiva de aprendizado."""
        queries = [
            "Métricas de desenvolvimento de colaboradores?",
            "Como medir capacitação no BSC?",
            "KPIs de aprendizado organizacional?"
        ]
        
        for query in queries:
            result = workflow.run(query, session_id="test-learn")
            
            assert result is not None
            perspectives_covered = result.get("metadata", {}).get("perspectives_covered", [])
            assert any(p.lower() == "learning" for p in perspectives_covered)


class TestPerformanceOptimizations:
    """Testes de otimizações de performance (cache, paralelização, multilíngue)."""
    
    @pytest.fixture
    def workflow(self):
        """Cria instância do workflow para testes."""
        return get_workflow()
    
    @pytest.fixture
    def embeddings_manager(self):
        """Cria instância do EmbeddingManager para testar cache."""
        from src.rag.embeddings import EmbeddingManager
        return EmbeddingManager()
    
    def test_embedding_cache_functionality(self, embeddings_manager):
        """Testa funcionalidade de cache de embeddings."""
        if not embeddings_manager.cache_enabled:
            pytest.skip("Cache de embeddings desativado no .env")
        
        # Texto de teste único (com timestamp para evitar cache de testes anteriores)
        import time
        test_text = f"Balanced Scorecard framework teste cache {time.time()}"
        
        # Reset cache stats
        embeddings_manager.cache_hits = 0
        embeddings_manager.cache_misses = 0
        
        # Primeira chamada - deve ser cache miss
        embedding1 = embeddings_manager.embed_text(test_text)
        assert embeddings_manager.cache_misses == 1
        assert embeddings_manager.cache_hits == 0
        
        # Segunda chamada - deve ser cache hit
        embedding2 = embeddings_manager.embed_text(test_text)
        assert embeddings_manager.cache_hits == 1
        
        # Embeddings devem ser idênticos
        assert embedding1 == embedding2
        
        logger.info(
            f"[TEST OK] Cache funcionando: "
            f"Hits={embeddings_manager.cache_hits}, "
            f"Misses={embeddings_manager.cache_misses}"
        )
    
    def test_embedding_cache_speedup(self, embeddings_manager):
        """Testa speedup do cache de embeddings."""
        import time
        
        if not embeddings_manager.cache_enabled:
            pytest.skip("Cache de embeddings desativado no .env")
        
        test_text = "KPIs financeiros no Balanced Scorecard incluem ROI e crescimento de receita"
        
        # Primeira execução - sem cache
        start = time.time()
        embeddings_manager.embed_text(test_text)
        time_without_cache = time.time() - start
        
        # Segunda execução - com cache
        start = time.time()
        embeddings_manager.embed_text(test_text)
        time_with_cache = time.time() - start
        
        # Cache deve ser significativamente mais rápido (pelo menos 10x)
        speedup = time_without_cache / time_with_cache if time_with_cache > 0 else 0
        
        logger.info(
            f"[TEST CACHE SPEEDUP] "
            f"Sem cache: {time_without_cache:.4f}s, "
            f"Com cache: {time_with_cache:.4f}s, "
            f"Speedup: {speedup:.1f}x"
        )
        
        assert speedup >= 10, f"Speedup esperado >=10x, obtido {speedup:.1f}x"
    
    def test_multilingual_search_pt_br_query(self, workflow):
        """Testa busca multilíngue com query em PT-BR recuperando docs EN."""
        # Query em português brasileiro
        query = "Quais são as perspectivas do Balanced Scorecard?"
        
        result = workflow.run(query, session_id="test-multilingual-pt")
        
        assert result is not None
        assert "final_response" in result
        
        # Verificar que documentos foram recuperados (docs estão em inglês)
        sources = result.get("sources", [])
        assert len(sources) > 0
        
        # Pelo menos um documento deve ter score alto (busca multilíngue funcionando)
        high_score_docs = [s for s in sources if s.get("score", 0) > 0.7]
        assert len(high_score_docs) > 0, "Busca multilíngue deve recuperar docs relevantes com score alto"
        
        logger.info(
            f"[TEST MULTILINGUAL] Query PT-BR recuperou {len(sources)} docs, "
            f"{len(high_score_docs)} com score >0.7"
        )
    
    def test_parallel_agent_execution(self, workflow):
        """Testa execução paralela de agentes (deve ser mais rápida que sequencial)."""
        import time
        
        # Query que ativa múltiplas perspectivas
        query = "Como criar um BSC completo com todas as perspectivas?"
        
        start = time.time()
        result = workflow.run(query, session_id="test-parallel")
        execution_time = time.time() - start
        
        perspectives = result.get("perspectives", [])
        num_perspectives = len(perspectives)
        
        # Se múltiplas perspectivas foram ativadas, tempo deve ser próximo do tempo
        # do agente mais lento (não soma dos tempos)
        # Assumindo ~5-10s por agente, 4 agentes sequenciais = 20-40s
        # Com paralelização, deve ser <15s
        
        logger.info(
            f"[TEST PARALLEL] {num_perspectives} perspectivas executadas em {execution_time:.2f}s"
        )
        
        # Se ativou 3+ perspectivas, tempo deve ser <20s (benefício da paralelização)
        if num_perspectives >= 3:
            assert execution_time < 20, f"Paralelização esperada, mas levou {execution_time:.2f}s"


class TestJudgeValidation:
    """Testes específicos do Judge Agent."""
    
    @pytest.fixture
    def workflow(self):
        """Cria instância do workflow para testes."""
        return get_workflow()
    
    def test_judge_approval_good_response(self, workflow):
        """Testa que Judge aprova respostas de boa qualidade."""
        # Query bem definida que deve gerar boa resposta
        query = "Quais são as quatro perspectivas do Balanced Scorecard?"
        
        result = workflow.run(query, session_id="test-judge-good")
        
        judge_eval = result.get("judge_evaluation", {})
        final_score = judge_eval.get("score", 0.0)
        judge_approved = judge_eval.get("approved", False)
        
        # Score deve ser razoável (>0.6)
        assert final_score > 0.6, f"Judge score baixo: {final_score}"
        
        # Deve ser aprovado
        assert judge_approved is True, "Judge deveria aprovar resposta de boa qualidade"
        
        logger.info(f"[TEST JUDGE OK] Score: {final_score:.2f}, Aprovado: {judge_approved}")
    
    def test_judge_metadata_completeness(self, workflow):
        """Testa que Judge retorna metadata completa."""
        query = "Como medir KPIs financeiros no BSC?"
        
        result = workflow.run(query, session_id="test-judge-metadata")
        
        metadata = result.get("metadata", {})
        judge_eval = result.get("judge_evaluation", {})
        
        # Verificar campos obrigatórios do Judge
        assert "final_score" in metadata
        assert "judge_approved" in metadata
        
        if judge_eval:
            # Se judge_evaluation existe, deve ter estrutura completa
            assert "feedback" in judge_eval or "completeness_score" in judge_eval
        
        logger.info(f"[TEST JUDGE METADATA] Campos presentes: {list(metadata.keys())}")


class TestMetrics:
    """Testes de métricas agregadas (latência, recall, precision)."""
    
    @pytest.fixture
    def workflow(self):
        """Cria instância do workflow para testes."""
        return get_workflow()
    
    def test_latency_percentiles(self, workflow):
        """Testa latência P50, P95, P99 com múltiplas queries."""
        import time
        import statistics
        import json
        from pathlib import Path
        
        # Carregar queries de teste
        queries_file = Path(__file__).parent / "test_queries.json"
        with open(queries_file, 'r', encoding='utf-8') as f:
            test_queries = json.load(f)
        
        # Selecionar amostra de queries (5 simples + 5 moderadas)
        sample_queries = []
        sample_queries.extend([q["query"] for q in test_queries["factual_queries"][:3]])
        sample_queries.extend([q["query"] for q in test_queries["conceptual_queries"][:3]])
        sample_queries.extend([q["query"] for q in test_queries["comparative_queries"][:2]])
        
        latencies = []
        
        logger.info(f"[TEST METRICS] Executando {len(sample_queries)} queries para medir latência...")
        
        for i, query in enumerate(sample_queries):
            start = time.time()
            result = workflow.run(query, session_id=f"test-metrics-{i}")
            latency = time.time() - start
            latencies.append(latency)
            
            logger.info(f"[QUERY {i+1}/{len(sample_queries)}] {latency:.2f}s - {query[:50]}...")
        
        # Calcular percentis
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        p99 = max(latencies)  # Aproximação para amostra pequena
        mean = statistics.mean(latencies)
        
        logger.info(
            f"[TEST METRICS LATENCY] "
            f"Mean: {mean:.2f}s, P50: {p50:.2f}s, P95: {p95:.2f}s, P99: {p99:.2f}s"
        )
        
        # Assertions: P95 deve ser <180s (3 min - MVP target realista com APIs externas)
        assert p95 < 180, f"P95 latency muito alta: {p95:.2f}s (esperado <180s)"
        
        # P50 deve ser <90s (1.5 min - mediana realista)
        assert p50 < 90, f"P50 latency muito alta: {p50:.2f}s (esperado <90s)"
    
    def test_judge_approval_rate(self, workflow):
        """Testa taxa de aprovação do Judge em múltiplas queries."""
        import json
        from pathlib import Path
        
        # Carregar queries de teste
        queries_file = Path(__file__).parent / "test_queries.json"
        with open(queries_file, 'r', encoding='utf-8') as f:
            test_queries = json.load(f)
        
        # Amostra: 3 de cada categoria (exceto edge cases)
        sample_queries = []
        sample_queries.extend([q["query"] for q in test_queries["factual_queries"][:2]])
        sample_queries.extend([q["query"] for q in test_queries["conceptual_queries"][:2]])
        sample_queries.extend([q["query"] for q in test_queries["complex_queries"][:2]])
        
        approvals = []
        scores = []
        
        logger.info(f"[TEST METRICS] Executando {len(sample_queries)} queries para medir approval rate...")
        
        for i, query in enumerate(sample_queries):
            result = workflow.run(query, session_id=f"test-approval-{i}")
            
            judge_eval = result.get("judge_evaluation", {})
            approved = judge_eval.get("approved", False)
            score = judge_eval.get("score", 0.0)
            
            approvals.append(approved)
            scores.append(score)
            
            logger.info(
                f"[QUERY {i+1}/{len(sample_queries)}] "
                f"Score: {score:.2f}, Approved: {approved} - {query[:50]}..."
            )
        
        # Calcular métricas
        approval_rate = (sum(approvals) / len(approvals)) * 100
        avg_score = sum(scores) / len(scores)
        
        logger.info(
            f"[TEST METRICS JUDGE] "
            f"Approval Rate: {approval_rate:.1f}%, "
            f"Avg Score: {avg_score:.2f}"
        )
        
        # Target: >70% approval rate para queries normais
        assert approval_rate >= 70, f"Approval rate baixa: {approval_rate:.1f}% (esperado >=70%)"
        
        # Target: score médio >0.7
        assert avg_score >= 0.7, f"Score médio baixo: {avg_score:.2f} (esperado >=0.7)"


class TestSystemReadiness:
    """Testes de prontidão do sistema (prerequisites)."""
    
    def test_qdrant_connection(self):
        """Testa conexão com Qdrant."""
        from qdrant_client import QdrantClient
        
        try:
            client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            # Testar conexão listando collections
            collections = client.get_collections()
            logger.info(f"[TEST QDRANT] Conexão OK - {len(collections.collections)} collections")
            assert True
        except Exception as e:
            pytest.fail(f"Qdrant não está rodando ou inacessível: {e}")
    
    def test_dataset_indexed(self):
        """Testa se dataset BSC está indexado no Qdrant."""
        from qdrant_client import QdrantClient
        
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        
        collection_name = settings.vector_store_index
        
        try:
            collection_info = client.get_collection(collection_name)
            num_vectors = collection_info.points_count
            
            logger.info(f"[TEST DATASET] Collection '{collection_name}' tem {num_vectors} vectors")
            
            # Deve ter pelo menos 1000 chunks indexados (dataset BSC)
            assert num_vectors >= 1000, f"Dataset muito pequeno: {num_vectors} chunks (esperado >=1000)"
            
        except Exception as e:
            pytest.fail(f"Collection '{collection_name}' não existe ou está vazia: {e}")
    
    def test_api_keys_configured(self):
        """Testa se API keys estão configuradas."""
        # OpenAI
        assert settings.openai_api_key is not None, "OPENAI_API_KEY não configurada no .env"
        assert len(settings.openai_api_key) > 20, "OPENAI_API_KEY inválida"
        
        # Anthropic
        assert settings.anthropic_api_key is not None, "ANTHROPIC_API_KEY não configurada no .env"
        assert len(settings.anthropic_api_key) > 20, "ANTHROPIC_API_KEY inválida"
        
        # Cohere
        assert settings.cohere_api_key is not None, "COHERE_API_KEY não configurada no .env"
        assert len(settings.cohere_api_key) > 20, "COHERE_API_KEY inválida"
        
        logger.info("[TEST API KEYS] Todas as API keys estão configuradas")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "-s"])



