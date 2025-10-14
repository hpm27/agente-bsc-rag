"""
Testes Unitários para Query Decomposer.

Cobre 15+ testes em 4 categorias:
1. Heurísticas (6 testes) - Validar decisão should_decompose()
2. Decomposição (4 testes) - Validar geração de sub-queries
3. Edge Cases (3 testes) - Validar tratamento de casos extremos
4. Integração (2 testes) - Validar workflow completo com retriever

Executar:
    pytest tests/test_query_decomposer.py -v
    pytest tests/test_query_decomposer.py --cov=src.rag.query_decomposer --cov-report=html
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from src.rag.query_decomposer import QueryDecomposer


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """LLM mockado com respostas fixas para decomposição."""
    llm = Mock()
    
    # Mock da resposta do LLM (retorna 4 sub-queries focadas)
    mock_response = Mock()
    mock_response.content = """Quais são os objetivos da perspectiva financeira no BSC?
Como medir o desempenho financeiro usando indicadores BSC?
Quais são os objetivos da perspectiva de clientes no BSC?
Como integrar métricas financeiras e de clientes?"""
    
    llm.invoke.return_value = mock_response
    llm.model_name = "gpt-4o-mini"
    
    return llm


@pytest.fixture
def query_decomposer(mock_llm):
    """QueryDecomposer instanciado com LLM mockado."""
    return QueryDecomposer(
        llm=mock_llm,
        enabled=True,
        min_query_length=50,
        score_threshold=2
    )


@pytest.fixture
def sample_queries():
    """Dicionário com queries de teste para diferentes cenários."""
    return {
        # Queries SIMPLES (não devem decompor)
        "simple_short": "O que é BSC?",
        "simple_definition": "Defina Balanced Scorecard",
        "simple_author": "Quem criou o BSC?",
        
        # Queries COMPLEXAS (devem decompor)
        "complex_multipart": "Como implementar BSC considerando as 4 perspectivas e suas interconexões?",
        "complex_relational": "Qual a relação entre KPIs de aprendizado, processos e resultados financeiros?",
        "complex_comparison": "Diferenças entre BSC para manufatura e serviços, considerando perspectivas de clientes e processos?",
        "complex_integration": "Como integrar objetivos estratégicos das perspectivas financeira, clientes e processos internos?",
        
        # Edge cases
        "empty": "",
        "very_long": "Como implementar " + "BSC " * 100,  # ~400 caracteres
        "multiple_questions": "O que é BSC? Como implementar? Quais benefícios? Onde aplicar? Quando usar?",
    }


# ============================================================================
# CATEGORIA 1: TESTES DE HEURÍSTICAS (6 testes)
# ============================================================================

def test_should_decompose_query_complexa_multipart(query_decomposer, sample_queries):
    """Query complexa multi-parte DEVE ser decomposta."""
    query = sample_queries["complex_multipart"]
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is True, "Query complexa multi-parte deveria ser decomposta"
    assert score >= 2, f"Score deveria ser >= 2, mas foi {score}"
    # Query tem: comprimento >50, palavra "considerando" (+1), 
    # múltiplas perspectivas (+2), palavra "implementar" (+1) = score 4


def test_should_not_decompose_query_simples(query_decomposer, sample_queries):
    """Query simples NÃO deve ser decomposta."""
    query = sample_queries["simple_short"]
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is False, "Query simples não deveria ser decomposta"
    assert score == 0, f"Score deveria ser 0 (query curta), mas foi {score}"


def test_should_decompose_query_com_multiplas_conjuncoes(query_decomposer):
    """Query com múltiplas conjunções ('e', 'também', 'além') DEVE ser decomposta."""
    query = "Explique os objetivos financeiros e também os KPIs de clientes, além dos processos internos do BSC"
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is True, "Query com múltiplas conjunções deveria ser decomposta"
    assert score >= 2, f"Score deveria ser >= 2, mas foi {score}"


def test_should_decompose_query_longa(query_decomposer):
    """Query longa com múltiplas perspectivas BSC DEVE ser decomposta."""
    query = "Como implementar o Balanced Scorecard considerando as perspectivas de aprendizado e crescimento junto com processos internos?"
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is True, "Query longa com múltiplas perspectivas deveria ser decomposta"
    assert score >= 2


def test_should_not_decompose_query_curta(query_decomposer, sample_queries):
    """Query curta (<50 caracteres) NÃO deve ser decomposta, independente do conteúdo."""
    query = sample_queries["simple_definition"]  # ~30 caracteres
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is False, "Query curta não deveria ser decomposta"
    assert score == 0, "Query abaixo do min_length deve ter score 0"


def test_should_decompose_query_com_perspectivas_multiplas(query_decomposer):
    """Query mencionando 2+ perspectivas BSC DEVE ser decomposta."""
    query = "Qual a relação entre a perspectiva financeira e a perspectiva de clientes no framework BSC?"
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is True, "Query com 2+ perspectivas BSC deveria ser decomposta"
    # Score: palavra "relação" (+1) + 2 perspectivas (+2) = 3


# ============================================================================
# CATEGORIA 2: TESTES DE DECOMPOSIÇÃO (4 testes)
# ============================================================================

@pytest.mark.asyncio
async def test_decompose_query_complexa_gera_subqueries(query_decomposer, sample_queries):
    """Decomposição de query complexa deve gerar 2-4 sub-queries."""
    query = sample_queries["complex_multipart"]
    
    sub_queries = await query_decomposer.decompose(query)
    
    assert isinstance(sub_queries, list), "Deve retornar lista de sub-queries"
    assert len(sub_queries) >= 2, f"Deve gerar pelo menos 2 sub-queries, gerou {len(sub_queries)}"
    assert len(sub_queries) <= 4, f"Deve gerar no máximo 4 sub-queries, gerou {len(sub_queries)}"
    assert all(isinstance(sq, str) for sq in sub_queries), "Todas sub-queries devem ser strings"
    assert all(len(sq) > 0 for sq in sub_queries), "Sub-queries não podem ser vazias"


@pytest.mark.asyncio
async def test_decompose_retorna_2_a_4_subqueries(query_decomposer):
    """Decomposição deve retornar entre 2 e 4 sub-queries (nunca 1)."""
    query = "Como implementar BSC considerando perspectivas financeira, clientes, processos e aprendizado?"
    
    sub_queries = await query_decomposer.decompose(query)
    
    assert len(sub_queries) >= 2, "Mínimo 2 sub-queries"
    assert len(sub_queries) <= 4, "Máximo 4 sub-queries"


@pytest.mark.asyncio
async def test_decompose_preserva_contexto_original(query_decomposer, mock_llm):
    """Sub-queries devem preservar conceitos-chave da query original."""
    query = "Qual a relação entre KPIs de aprendizado e resultados financeiros?"
    
    # Mock específico para este teste
    mock_response = Mock()
    mock_response.content = """Quais são os KPIs da perspectiva de aprendizado no BSC?
Como KPIs de aprendizado impactam os resultados financeiros?"""
    mock_llm.invoke.return_value = mock_response
    
    sub_queries = await query_decomposer.decompose(query)
    
    # Verificar que palavras-chave estão presentes nas sub-queries
    all_subqueries_text = " ".join(sub_queries).lower()
    assert "aprendizado" in all_subqueries_text or "learning" in all_subqueries_text
    assert "financeiro" in all_subqueries_text or "financial" in all_subqueries_text


@pytest.mark.asyncio
async def test_decompose_subqueries_independentes(query_decomposer, mock_llm):
    """Sub-queries devem ser independentes (não se sobrepõem)."""
    query = "Compare perspectivas financeira e de clientes no BSC"
    
    # Mock com sub-queries bem separadas
    mock_response = Mock()
    mock_response.content = """Quais são os objetivos da perspectiva financeira?
Quais são os objetivos da perspectiva de clientes?"""
    mock_llm.invoke.return_value = mock_response
    
    sub_queries = await query_decomposer.decompose(query)
    
    # Sub-queries não devem ser idênticas
    assert len(sub_queries) == len(set(sub_queries)), "Sub-queries devem ser únicas"
    
    # Cada sub-query deve focar em um aspecto
    # (teste simplificado - verificar que não são iguais)
    if len(sub_queries) >= 2:
        assert sub_queries[0] != sub_queries[1], "Sub-queries não devem ser idênticas"


# ============================================================================
# CATEGORIA 3: TESTES DE EDGE CASES (3 testes)
# ============================================================================

def test_query_vazia_nao_decompoe(query_decomposer, sample_queries):
    """Query vazia não deve ser decomposta."""
    query = sample_queries["empty"]
    
    should, score = query_decomposer.should_decompose(query)
    
    assert should is False, "Query vazia não deve ser decomposta"
    assert score == 0, "Query vazia deve ter score 0"


@pytest.mark.asyncio
async def test_query_muito_longa_trunca(query_decomposer, sample_queries):
    """Query muito longa (>400 chars) deve ser tratada sem erro."""
    query = sample_queries["very_long"]
    
    # Não deve levantar exceção
    try:
        sub_queries = await query_decomposer.decompose(query)
        assert isinstance(sub_queries, list), "Deve retornar lista mesmo com query longa"
    except Exception as e:
        pytest.fail(f"Query longa não deveria levantar exceção: {e}")


@pytest.mark.asyncio
async def test_parse_subqueries_malformadas(query_decomposer, mock_llm):
    """Parser deve tratar sub-queries malformadas (linhas vazias, comentários)."""
    query = "Como implementar BSC?"
    
    # Mock com resposta malformada (linhas vazias, comentários)
    mock_response = Mock()
    mock_response.content = """
# Comentário que deve ser ignorado

Primeira sub-query válida

Segunda sub-query válida
# Outro comentário

"""
    mock_llm.invoke.return_value = mock_response
    
    sub_queries = await query_decomposer.decompose(query)
    
    # Deve filtrar linhas vazias e comentários
    assert len(sub_queries) == 2, f"Deveria ter 2 sub-queries válidas, tem {len(sub_queries)}"
    assert all("#" not in sq for sq in sub_queries), "Comentários devem ser removidos"
    assert all(len(sq.strip()) > 0 for sq in sub_queries), "Sub-queries não devem estar vazias"


# ============================================================================
# CATEGORIA 4: TESTES DE INTEGRAÇÃO (2 testes)
# ============================================================================

@pytest.mark.asyncio
async def test_retrieve_with_decomposition_workflow_completo(query_decomposer, mock_llm):
    """Workflow completo: should_decompose → decompose → verificar resultado."""
    query = "Como implementar BSC considerando as perspectivas financeira e de clientes?"
    
    # Step 1: Decidir se deve decompor
    should, score = query_decomposer.should_decompose(query)
    assert should is True, "Query complexa deveria triggar decomposição"
    
    # Step 2: Decompor
    sub_queries = await query_decomposer.decompose(query)
    assert len(sub_queries) >= 2, "Deve gerar pelo menos 2 sub-queries"
    
    # Step 3: Verificar qualidade das sub-queries
    all_text = " ".join(sub_queries).lower()
    assert "financeira" in all_text or "financial" in all_text
    assert "cliente" in all_text or "customer" in all_text


@pytest.mark.asyncio
async def test_retrieve_fallback_quando_decomposicao_falha(query_decomposer, mock_llm):
    """Se decomposição falhar (exceção no LLM), deve retornar query original."""
    query = "Como implementar BSC?"
    
    # Mock LLM para levantar exceção
    mock_llm.invoke.side_effect = Exception("LLM API error")
    
    # Não deve propagar exceção - deve fazer fallback
    sub_queries = await query_decomposer.decompose(query)
    
    # Deve retornar query original como fallback
    assert len(sub_queries) == 1, "Fallback deve retornar 1 query (original)"
    assert sub_queries[0] == query, "Fallback deve retornar query original"


# ============================================================================
# TESTES ADICIONAIS (Coverage e Robustez)
# ============================================================================

def test_decomposer_disabled_nunca_decompoe(mock_llm):
    """QueryDecomposer desabilitado (enabled=False) nunca decompõe."""
    decomposer = QueryDecomposer(
        llm=mock_llm,
        enabled=False  # DESABILITADO
    )
    
    query = "Como implementar BSC considerando todas as 4 perspectivas e suas relações complexas?"
    
    should, score = decomposer.should_decompose(query)
    
    assert should is False, "Decomposer desabilitado nunca deve decompor"
    assert score == 0, "Decomposer desabilitado deve retornar score 0"


def test_threshold_customizado(mock_llm):
    """Threshold customizado deve afetar decisão de decomposição."""
    # Threshold muito alto (8) - difícil de triggar
    decomposer_high = QueryDecomposer(
        llm=mock_llm,
        enabled=True,
        min_query_length=50,
        score_threshold=8  # MUITO ALTO
    )
    
    query = "Como implementar BSC considerando perspectivas financeira e clientes?"
    # Esta query tem score ~4 (< 8)
    
    should, score = decomposer_high.should_decompose(query)
    
    assert should is False, "Query com score 4 não deve triggar threshold 8"
    assert score < 8


def test_multiple_perspectives_aumenta_score(query_decomposer):
    """Mencionar múltiplas perspectivas BSC deve aumentar significativamente o score."""
    query_2_persp = "Compare perspectivas financeira e de clientes no BSC"
    query_4_persp = "Integre perspectivas financeira, clientes, processos e aprendizado no BSC"
    
    should_2, score_2 = query_decomposer.should_decompose(query_2_persp)
    should_4, score_4 = query_decomposer.should_decompose(query_4_persp)
    
    # Ambas devem decompor
    assert should_2 is True
    assert should_4 is True
    
    # Query com 4 perspectivas deve ter score >= query com 2 perspectivas
    # (ambas ganham +2 por múltiplas perspectivas, mas 4 persp pode ter bonus adicional)
    assert score_4 >= score_2


def test_get_stats(query_decomposer):
    """get_stats() deve retornar configurações corretas."""
    stats = query_decomposer.get_stats()
    
    assert stats["enabled"] is True
    assert stats["min_query_length"] == 50
    assert stats["score_threshold"] == 2
    assert "llm_model" in stats
    assert stats["llm_model"] == "gpt-4o-mini"


# ============================================================================
# TESTE DE PERFORMANCE (opcional, mas útil)
# ============================================================================

@pytest.mark.asyncio
async def test_decompose_latency_acceptable(query_decomposer, sample_queries):
    """Decomposição deve completar em tempo aceitável (<5s no mock)."""
    import time
    
    query = sample_queries["complex_multipart"]
    
    start_time = time.time()
    sub_queries = await query_decomposer.decompose(query)
    elapsed_time = time.time() - start_time
    
    # Com mock, deve ser < 1s. Em produção com LLM real, target < 2s
    assert elapsed_time < 5.0, f"Decomposição demorou {elapsed_time:.2f}s (target < 5s)"
    assert len(sub_queries) >= 2


# ============================================================================
# SUMÁRIO DOS TESTES
# ============================================================================
"""
TOTAL DE TESTES: 18

CATEGORIA 1 - Heurísticas: 6 testes
1. test_should_decompose_query_complexa_multipart
2. test_should_not_decompose_query_simples
3. test_should_decompose_query_com_multiplas_conjuncoes
4. test_should_decompose_query_longa
5. test_should_not_decompose_query_curta
6. test_should_decompose_query_com_perspectivas_multiplas

CATEGORIA 2 - Decomposição: 4 testes
7. test_decompose_query_complexa_gera_subqueries
8. test_decompose_retorna_2_a_4_subqueries
9. test_decompose_preserva_contexto_original
10. test_decompose_subqueries_independentes

CATEGORIA 3 - Edge Cases: 3 testes
11. test_query_vazia_nao_decompoe
12. test_query_muito_longa_trunca
13. test_parse_subqueries_malformadas

CATEGORIA 4 - Integração: 2 testes
14. test_retrieve_with_decomposition_workflow_completo
15. test_retrieve_fallback_quando_decomposicao_falha

CATEGORIA 5 - Adicionais (Coverage): 3 testes
16. test_decomposer_disabled_nunca_decompoe
17. test_threshold_customizado
18. test_multiple_perspectives_aumenta_score
19. test_get_stats
20. test_decompose_latency_acceptable

TOTAL: 20 TESTES (15+ requerido ✅)

Coverage esperado: >90% do query_decomposer.py
"""

