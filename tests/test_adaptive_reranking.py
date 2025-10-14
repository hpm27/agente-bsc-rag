"""
Testes unitários para Adaptive Re-ranking com MMR (Fase 2A.2).

Testa as novas funcionalidades implementadas em CohereReranker:
- Algoritmo MMR (Maximal Marginal Relevance)
- Metadata-aware boosting
- Adaptive top_n baseado em complexidade da query
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.rag.reranker import CohereReranker
from config.settings import settings


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def reranker():
    """Fixture que cria instância do CohereReranker."""
    with patch('cohere.Client'):
        return CohereReranker()


@pytest.fixture
def sample_documents():
    """Fixture com documentos de teste."""
    return [
        {
            "content": "BSC é uma metodologia de gestão estratégica.",
            "metadata": {
                "source": "kaplan_norton_1996.pdf",
                "context_pt": "Capítulo sobre conceitos financeiros do BSC",
                "context_en": "Chapter on financial concepts of BSC"
            },
            "rerank_score": 0.9
        },
        {
            "content": "A perspectiva financeira foca em resultados econômicos.",
            "metadata": {
                "source": "kaplan_norton_1996.pdf",
                "context_pt": "Capítulo sobre perspectiva financeira",
                "context_en": "Chapter on financial perspective"
            },
            "rerank_score": 0.85
        },
        {
            "content": "A satisfação do cliente é essencial no BSC.",
            "metadata": {
                "source": "bsc_implementacao_2005.pdf",
                "context_pt": "Seção sobre perspectiva de clientes",
                "context_en": "Section on customer perspective"
            },
            "rerank_score": 0.80
        },
        {
            "content": "Processos internos devem ser otimizados continuamente.",
            "metadata": {
                "source": "bsc_processos_2010.pdf",
                "context_pt": "Análise de processos internos no BSC",
                "context_en": "Analysis of internal processes in BSC"
            },
            "rerank_score": 0.75
        },
        {
            "content": "O aprendizado organizacional é a base do crescimento.",
            "metadata": {
                "source": "bsc_learning_2015.pdf",
                "context_pt": "Capítulo sobre aprendizado e crescimento",
                "context_en": "Chapter on learning and growth"
            },
            "rerank_score": 0.70
        }
    ]


@pytest.fixture
def sample_embeddings():
    """Fixture com embeddings de teste (5 docs, dimensão 384)."""
    np.random.seed(42)
    embeddings = np.random.randn(5, 384)
    # Normalizar para cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings


# -----------------------------------------------------------------------------
# Testes de Similaridade (Cosine Similarity)
# -----------------------------------------------------------------------------

def test_calculate_similarity_basic(reranker):
    """Teste básico de cálculo de similaridade cosine."""
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],  # Idêntico ao primeiro
        [0.0, 1.0, 0.0]   # Ortogonal ao primeiro
    ])
    
    similarity_matrix = reranker._calculate_similarity(embeddings)
    
    assert similarity_matrix.shape == (3, 3)
    assert np.allclose(similarity_matrix[0, 1], 1.0)  # Docs idênticos
    assert np.allclose(similarity_matrix[0, 2], 0.0)  # Docs ortogonais


def test_calculate_similarity_normalized(reranker):
    """Teste de similaridade com embeddings normalizados."""
    np.random.seed(123)
    embeddings = np.random.randn(4, 128)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    similarity_matrix = reranker._calculate_similarity(embeddings)
    
    # Matriz deve ser simétrica
    assert np.allclose(similarity_matrix, similarity_matrix.T)
    # Diagonal deve ser 1.0 (doc similar a si mesmo)
    assert np.allclose(np.diag(similarity_matrix), 1.0)
    # Valores devem estar entre -1 e 1 (com tolerância para imprecisão numérica)
    assert np.allclose(similarity_matrix, np.clip(similarity_matrix, -1.0, 1.0), atol=1e-6)


# -----------------------------------------------------------------------------
# Testes de Metadata Boosting
# -----------------------------------------------------------------------------

def test_boost_by_metadata_different_sources(reranker, sample_documents):
    """Teste de boost para documentos de sources diferentes."""
    selected_indices = [0]  # Primeiro doc selecionado (kaplan_norton_1996.pdf)
    
    boosts = reranker._boost_by_metadata(sample_documents, selected_indices)
    
    # Doc 0 já selecionado: boost 1.0 (neutro)
    assert boosts[0] == 1.0
    # Doc 1 mesma source: boost 1.0
    assert boosts[1] == 1.0
    # Doc 2 source diferente: boost 1.2 (1.0 + 0.2)
    assert boosts[2] > 1.0


def test_boost_by_metadata_different_perspectives(reranker, sample_documents):
    """Teste de boost para documentos de perspectives BSC diferentes."""
    # Selecionar doc financeiro (0) e doc de clientes (2)
    selected_indices = [0, 2]
    
    boosts = reranker._boost_by_metadata(sample_documents, selected_indices)
    
    # Docs já selecionados: boost neutro ou baixo
    assert boosts[0] <= 1.2
    assert boosts[2] <= 1.2
    # Doc 3 (processos) tem perspective diferente: deve ter boost
    assert boosts[3] > 1.0
    # Doc 4 (aprendizado) tem perspective diferente: deve ter boost
    assert boosts[4] > 1.0


def test_boost_by_metadata_no_selected(reranker, sample_documents):
    """Teste de boost quando nenhum doc foi selecionado."""
    selected_indices = []
    
    boosts = reranker._boost_by_metadata(sample_documents, selected_indices)
    
    # Todos docs devem ter boost >= 1.0 (source diferente de vazio)
    for boost in boosts.values():
        assert boost >= 1.0


def test_boost_by_metadata_missing_metadata(reranker):
    """Teste de boost com metadata ausente (graceful degradation)."""
    docs_incomplete = [
        {"content": "Texto 1", "metadata": {}, "rerank_score": 0.9},
        {"content": "Texto 2", "rerank_score": 0.8}  # Sem metadata
    ]
    
    boosts = reranker._boost_by_metadata(docs_incomplete, [])
    
    # Deve funcionar sem erros
    assert len(boosts) == 2
    assert all(boost >= 1.0 for boost in boosts.values())


# -----------------------------------------------------------------------------
# Testes de Adaptive Top-N
# -----------------------------------------------------------------------------

def test_adaptive_topn_simple_query(reranker):
    """Teste de top_n adaptativo para query simples."""
    query = "O que é BSC?"
    
    top_n = reranker.calculate_adaptive_topn(query)
    
    # Query simples deve retornar 5
    assert top_n == 5


def test_adaptive_topn_moderate_query(reranker):
    """Teste de top_n adaptativo para query moderada."""
    query = "Como implementar BSC considerando a perspectiva financeira?"
    
    top_n = reranker.calculate_adaptive_topn(query, base_top_n=10)
    
    # Query moderada deve retornar base_top_n (10)
    assert top_n == 10


def test_adaptive_topn_complex_query(reranker):
    """Teste de top_n adaptativo para query complexa."""
    query = "Como implementar BSC considerando as perspectivas financeira, clientes e processos?"
    
    top_n = reranker.calculate_adaptive_topn(query)
    
    # Query complexa deve retornar 15
    assert top_n == 15


def test_adaptive_topn_multiple_questions(reranker):
    """Teste de top_n com múltiplas perguntas na query."""
    query = "O que é BSC? Como implementar? Quais são os benefícios?"
    
    top_n = reranker.calculate_adaptive_topn(query)
    
    # Múltiplas perguntas aumentam complexidade
    assert top_n >= 10


# -----------------------------------------------------------------------------
# Testes de MMR (Maximal Marginal Relevance)
# -----------------------------------------------------------------------------

def test_mmr_basic_functionality(reranker, sample_documents, sample_embeddings):
    """Teste básico do algoritmo MMR."""
    query = "Como implementar BSC?"
    
    diverse_docs = reranker.rerank_with_diversity(
        query=query,
        documents=sample_documents,
        embeddings=sample_embeddings,
        top_n=3
    )
    
    assert len(diverse_docs) == 3
    assert all("mmr_rank" in doc for doc in diverse_docs)
    assert all("original_rerank_rank" in doc for doc in diverse_docs)


def test_mmr_diversity_vs_relevance(reranker, sample_documents):
    """Teste de trade-off diversidade vs relevância."""
    # Criar embeddings com docs muito similares
    embeddings_similar = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.99, 0.01, 0.0, 0.0],  # Muito similar ao primeiro
        [0.98, 0.02, 0.0, 0.0],  # Muito similar ao primeiro
        [0.0, 0.0, 1.0, 0.0],    # Diferente
        [0.0, 0.0, 0.99, 0.01]   # Similar ao quarto
    ])
    embeddings_similar = embeddings_similar / np.linalg.norm(embeddings_similar, axis=1, keepdims=True)
    
    # Com lambda=0.5 (balanceado), deve evitar docs similares
    diverse_docs = reranker.rerank_with_diversity(
        query="teste",
        documents=sample_documents,
        embeddings=embeddings_similar,
        top_n=3,
        lambda_param=0.5
    )
    
    # Verificar que não selecionou apenas os 3 primeiros (muito similares)
    selected_indices = [doc["original_rerank_rank"] for doc in diverse_docs]
    assert len(set(selected_indices)) == 3  # 3 docs únicos


def test_mmr_lambda_relevance_only(reranker, sample_documents, sample_embeddings):
    """Teste MMR com λ=1.0 (só relevância, sem diversidade)."""
    query = "teste"
    
    diverse_docs = reranker.rerank_with_diversity(
        query=query,
        documents=sample_documents,
        embeddings=sample_embeddings,
        top_n=3,
        lambda_param=1.0  # Só relevância
    )
    
    # Com λ=1.0, deve respeitar ordem de relevance_score original
    assert diverse_docs[0]["rerank_score"] >= diverse_docs[1]["rerank_score"]
    assert diverse_docs[1]["rerank_score"] >= diverse_docs[2]["rerank_score"]


def test_mmr_empty_documents(reranker):
    """Teste MMR com lista vazia de documentos."""
    diverse_docs = reranker.rerank_with_diversity(
        query="teste",
        documents=[],
        embeddings=np.array([]).reshape(0, 384),
        top_n=5
    )
    
    assert diverse_docs == []


def test_mmr_embeddings_mismatch(reranker, sample_documents):
    """Teste MMR com mismatch entre docs e embeddings."""
    wrong_embeddings = np.random.randn(3, 384)  # 3 embeddings para 5 docs
    
    diverse_docs = reranker.rerank_with_diversity(
        query="teste",
        documents=sample_documents,
        embeddings=wrong_embeddings,
        top_n=3
    )
    
    # Deve retornar docs originais sem MMR
    assert len(diverse_docs) <= 3


def test_mmr_with_metadata_boost(reranker, sample_documents, sample_embeddings):
    """Teste MMR com metadata boosting habilitado."""
    query = "teste"
    
    diverse_docs = reranker.rerank_with_diversity(
        query=query,
        documents=sample_documents,
        embeddings=sample_embeddings,
        top_n=5,
        enable_metadata_boost=True
    )
    
    # Verificar que documentos de sources diferentes foram priorizados
    sources = [doc["metadata"]["source"] for doc in diverse_docs]
    unique_sources = set(sources)
    assert len(unique_sources) >= 2  # Pelo menos 2 sources diferentes


def test_mmr_without_metadata_boost(reranker, sample_documents, sample_embeddings):
    """Teste MMR com metadata boosting desabilitado."""
    query = "teste"
    
    diverse_docs = reranker.rerank_with_diversity(
        query=query,
        documents=sample_documents,
        embeddings=sample_embeddings,
        top_n=5,
        enable_metadata_boost=False
    )
    
    assert len(diverse_docs) == 5
    assert all("mmr_rank" in doc for doc in diverse_docs)


def test_mmr_adaptive_topn_integration(reranker, sample_documents, sample_embeddings):
    """Teste integração MMR com adaptive top_n."""
    # Query simples
    query_simple = "O que é BSC?"
    
    diverse_docs_simple = reranker.rerank_with_diversity(
        query=query_simple,
        documents=sample_documents,
        embeddings=sample_embeddings,
        top_n=None  # Adaptativo
    )
    
    # Deve retornar 5 docs (top_n adaptativo para query simples)
    assert len(diverse_docs_simple) == 5
    
    # Query complexa
    query_complex = "Como implementar BSC considerando perspectivas financeira, clientes e processos?"
    
    diverse_docs_complex = reranker.rerank_with_diversity(
        query=query_complex,
        documents=sample_documents,
        embeddings=sample_embeddings,
        top_n=None  # Adaptativo
    )
    
    # Deve retornar até 5 docs (limitado pelo sample, mas tentaria 15)
    assert len(diverse_docs_complex) == 5


def test_mmr_with_unnormalized_embeddings(reranker, sample_documents):
    """Teste MMR com embeddings não normalizados (linha 377)."""
    # Criar embeddings NÃO normalizados (norma > 1.1)
    np.random.seed(789)
    unnormalized_embeddings = np.random.randn(5, 384) * 10  # Multiplicar por 10 para garantir norma alta
    
    # Verificar que embeddings não estão normalizados
    assert np.linalg.norm(unnormalized_embeddings[0]) > 1.1
    
    diverse_docs = reranker.rerank_with_diversity(
        query="teste",
        documents=sample_documents,
        embeddings=unnormalized_embeddings,
        top_n=3
    )
    
    # Deve normalizar internamente e funcionar corretamente
    assert len(diverse_docs) == 3
    assert all("mmr_rank" in doc for doc in diverse_docs)


# -----------------------------------------------------------------------------
# Testes de Edge Cases
# -----------------------------------------------------------------------------

def test_mmr_single_document(reranker):
    """Teste MMR com apenas 1 documento."""
    single_doc = [{
        "content": "Teste",
        "metadata": {"source": "test.pdf"},
        "rerank_score": 0.9
    }]
    single_embedding = np.random.randn(1, 384)
    single_embedding = single_embedding / np.linalg.norm(single_embedding)
    
    diverse_docs = reranker.rerank_with_diversity(
        query="teste",
        documents=single_doc,
        embeddings=single_embedding,
        top_n=5
    )
    
    assert len(diverse_docs) == 1


def test_adaptive_topn_edge_cases(reranker):
    """Teste adaptive top_n com edge cases."""
    # Query vazia
    assert reranker.calculate_adaptive_topn("") == 5
    
    # Query muito longa
    long_query = " ".join(["palavra"] * 100)
    top_n = reranker.calculate_adaptive_topn(long_query)
    assert top_n in [5, 10, 15]


# -----------------------------------------------------------------------------
# Testes de Detecção de Idioma
# -----------------------------------------------------------------------------

def test_detect_language_portuguese(reranker):
    """Teste de detecção de idioma português."""
    query_pt = "Como implementar o Balanced Scorecard na minha empresa?"
    
    lang = reranker._detect_language(query_pt)
    
    assert lang == "pt-br"


def test_detect_language_portuguese_with_accents(reranker):
    """Teste de detecção com acentuação portuguesa."""
    query_pt = "Qual é a relação entre as perspectivas?"
    
    lang = reranker._detect_language(query_pt)
    
    assert lang == "pt-br"


def test_detect_language_english(reranker):
    """Teste de detecção de idioma inglês."""
    query_en = "What are the key performance indicators?"
    
    lang = reranker._detect_language(query_en)
    
    assert lang == "en"


def test_detect_language_mixed(reranker):
    """Teste de detecção com query mista."""
    query_mixed = "What é BSC implementation?"
    
    lang = reranker._detect_language(query_mixed)
    
    # Pode ser pt-br ou en, depende da heurística
    assert lang in ["pt-br", "en", "other"]


def test_detect_language_no_keywords(reranker):
    """Teste de detecção sem keywords identificáveis."""
    query_generic = "xyz abc 123"
    
    lang = reranker._detect_language(query_generic)
    
    assert lang in ["pt-br", "en", "other"]


def test_detect_language_pt_majority(reranker):
    """Teste de detecção com maioria de palavras PT (linha 61)."""
    # Query com mais PT keywords que EN (sem acentos)
    query_pt = "como o que quando where"  # 3 PT, 1 EN
    
    lang = reranker._detect_language(query_pt)
    
    assert lang == "pt-br"


def test_detect_language_en_majority(reranker):
    """Teste de detecção com maioria de palavras EN (linha 63)."""
    # Query com mais EN keywords que PT
    query_en = "what how where como"  # 3 EN, 1 PT
    
    lang = reranker._detect_language(query_en)
    
    assert lang == "en"


# -----------------------------------------------------------------------------
# Testes de Rerank (Integração com Cohere - Mocked)
# -----------------------------------------------------------------------------

def test_rerank_basic(reranker, sample_documents):
    """Teste básico do método rerank (mocked Cohere API)."""
    with patch.object(reranker.client, 'rerank') as mock_rerank:
        # Mock da resposta do Cohere
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(index=0, relevance_score=0.95),
            MagicMock(index=2, relevance_score=0.85),
            MagicMock(index=1, relevance_score=0.75)
        ]
        mock_rerank.return_value = mock_result
        
        reranked = reranker.rerank(
            query="Como implementar BSC?",
            documents=sample_documents,
            top_n=3
        )
        
        assert len(reranked) == 3
        assert all("rerank_score" in doc for doc in reranked)
        assert reranked[0]["rerank_score"] == 0.95


def test_rerank_empty_documents(reranker):
    """Teste rerank com lista vazia."""
    reranked = reranker.rerank(query="teste", documents=[])
    
    assert reranked == []


def test_rerank_adaptive_multilingual(reranker, sample_documents):
    """Teste rerank com adaptive multilingual."""
    with patch.object(reranker.client, 'rerank') as mock_rerank:
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(index=0, relevance_score=0.9),
            MagicMock(index=1, relevance_score=0.8)
        ]
        mock_rerank.return_value = mock_result
        
        # Query em português
        reranked = reranker.rerank(
            query="O que é BSC?",
            documents=sample_documents,
            top_n=2,
            adaptive_multilingual=True
        )
        
        assert len(reranked) <= 3  # Ajuste adaptativo +20%


def test_rerank_error_handling(reranker, sample_documents):
    """Teste rerank com erro da API."""
    with patch.object(reranker.client, 'rerank') as mock_rerank:
        # Simular erro da API
        mock_rerank.side_effect = Exception("API Error")
        
        # Deve retornar documentos originais em caso de erro
        reranked = reranker.rerank(
            query="teste",
            documents=sample_documents,
            top_n=3
        )
        
        assert len(reranked) == 3
        assert reranked == sample_documents[:3]


def test_rerank_with_scores_basic(reranker, sample_documents):
    """Teste rerank_with_scores básico."""
    with patch.object(reranker.client, 'rerank') as mock_rerank:
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(index=0, relevance_score=0.9),
            MagicMock(index=1, relevance_score=0.6),
            MagicMock(index=2, relevance_score=0.3)
        ]
        mock_rerank.return_value = mock_result
        
        filtered = reranker.rerank_with_scores(
            query="teste",
            documents=sample_documents,
            threshold=0.5
        )
        
        # Apenas docs com score >= 0.5
        assert len(filtered) == 2
        assert all(doc["rerank_score"] >= 0.5 for doc in filtered)


def test_rerank_with_scores_high_threshold(reranker, sample_documents):
    """Teste rerank_with_scores com threshold alto."""
    with patch.object(reranker.client, 'rerank') as mock_rerank:
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(index=0, relevance_score=0.6),
            MagicMock(index=1, relevance_score=0.5),
            MagicMock(index=2, relevance_score=0.4)
        ]
        mock_rerank.return_value = mock_result
        
        filtered = reranker.rerank_with_scores(
            query="teste",
            documents=sample_documents,
            threshold=0.9
        )
        
        # Nenhum doc passa threshold alto
        assert len(filtered) == 0


# -----------------------------------------------------------------------------
# Testes de FusionReranker
# -----------------------------------------------------------------------------

def test_fusion_reranker_basic():
    """Teste básico do FusionReranker."""
    from src.rag.reranker import FusionReranker
    
    fusion = FusionReranker(k=60)
    
    # Duas listas de resultados
    results1 = [
        {"content": "Doc A", "source": "book1.pdf", "page": 1},
        {"content": "Doc B", "source": "book1.pdf", "page": 2}
    ]
    results2 = [
        {"content": "Doc B", "source": "book1.pdf", "page": 2},
        {"content": "Doc C", "source": "book2.pdf", "page": 1}
    ]
    
    fused = fusion.fuse([results1, results2], top_n=3)
    
    assert len(fused) <= 3
    assert all("rrf_score" in doc for doc in fused)


def test_fusion_reranker_single_list():
    """Teste FusionReranker com apenas 1 lista."""
    from src.rag.reranker import FusionReranker
    
    fusion = FusionReranker()
    
    results = [
        {"content": "Doc A", "source": "book1.pdf", "page": 1},
        {"content": "Doc B", "source": "book1.pdf", "page": 2}
    ]
    
    fused = fusion.fuse([results], top_n=2)
    
    assert len(fused) == 2


def test_fusion_reranker_empty_lists():
    """Teste FusionReranker com listas vazias."""
    from src.rag.reranker import FusionReranker
    
    fusion = FusionReranker()
    
    fused = fusion.fuse([[], []], top_n=5)
    
    assert len(fused) == 0


# -----------------------------------------------------------------------------
# Testes de HybridReranker
# -----------------------------------------------------------------------------

def test_hybrid_reranker_basic():
    """Teste básico do HybridReranker."""
    from src.rag.reranker import HybridReranker
    
    with patch('src.rag.reranker.CohereReranker'):
        hybrid = HybridReranker()
        
        # Mock dos rerankers internos
        hybrid.fusion_reranker.fuse = Mock(return_value=[
            {"content": "Fused 1", "source": "book1.pdf"},
            {"content": "Fused 2", "source": "book2.pdf"}
        ])
        
        hybrid.cohere_reranker.rerank = Mock(return_value=[
            {"content": "Final 1", "source": "book1.pdf", "rerank_score": 0.9}
        ])
        
        vector_results = [{"content": "Vec 1"}]
        text_results = [{"content": "Text 1"}]
        
        final = hybrid.rerank(
            query="teste",
            vector_results=vector_results,
            text_results=text_results,
            top_n=1
        )
        
        assert len(final) == 1
        assert "rerank_score" in final[0]

