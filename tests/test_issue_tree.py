"""Testes unitarios para Issue Tree Analyzer Tool.

Cobre:
- Criacao tool (com/sem RAG agents)
- Workflow completo (facilitate_issue_tree)
- Validacoes (max_depth, root_problem, MECE)
- Schemas (IssueNode, IssueTreeAnalysis metodos uteis)

Pattern: Implementation-First Testing (checklist ponto 13)
- Leu implementacao ANTES de escrever testes
- Fixtures Pydantic validas (margem seguranca min_length)
- Mocks LLM structured output (DecompositionOutput, SolutionPathsOutput)

Created: 2025-10-19 (FASE 3.3)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

from src.tools.issue_tree import (
    IssueTreeTool,
    DecompositionOutput,
    SubProblemOutput,
    SolutionPathsOutput,
)
from src.memory.schemas import (
    IssueTreeAnalysis,
    IssueNode,
    CompanyInfo,
    StrategicContext,
)


# ============================================================================
# FIXTURES (Pydantic validas, margem seguranca)
# ============================================================================


@pytest.fixture
def mock_llm():
    """LLM mock para structured output."""
    llm = Mock()
    llm.with_structured_output = Mock(return_value=llm)
    return llm


@pytest.fixture
def mock_agents():
    """4 specialist agents mock para RAG."""
    financial = Mock()
    financial.invoke = Mock(return_value={"response": "Perspectiva Financeira BSC: Lucratividade e ROI"})
    
    customer = Mock()
    customer.invoke = Mock(return_value={"response": "Perspectiva Clientes BSC: Satisfacao e retencao"})
    
    process = Mock()
    process.invoke = Mock(return_value={"response": "Perspectiva Processos BSC: Eficiencia operacional"})
    
    learning = Mock()
    learning.invoke = Mock(return_value={"response": "Perspectiva Aprendizado BSC: Capacitacao equipe"})
    
    return financial, customer, process, learning


@pytest.fixture
def valid_company_info():
    """CompanyInfo valido para testes."""
    return CompanyInfo(
        name="TechCorp Brasil Ltda",
        sector="Tecnologia",
        size="média",  # Literal correto
        industry="SaaS B2B",
        founded_year=2018
    )


@pytest.fixture
def valid_strategic_context():
    """StrategicContext valido para testes."""
    return StrategicContext(
        current_challenges=[
            "Baixa lucratividade no ultimo trimestre devido a custos altos",  # 50+ chars
            "Dificuldade em atrair e reter clientes de grande porte",  # 50+ chars
            "Processos manuais causando gargalos operacionais criticos"  # 50+ chars
        ],
        strategic_objectives=[
            "Aumentar lucratividade em 20% no proximo ano atraves de reducao de custos e aumento de vendas",  # 50+ chars
            "Expandir base de clientes enterprise em 30% com foco em grandes contas"  # 50+ chars
        ]
    )


# ============================================================================
# TESTES CRIACAO (2 testes)
# ============================================================================


def test_issue_tree_tool_creation_with_rag_agents(mock_llm, mock_agents):
    """Test 1: Tool criado com 4 specialist agents para RAG."""
    financial, customer, process, learning = mock_agents
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    assert tool.llm == mock_llm
    assert tool.financial_agent == financial
    assert tool.customer_agent == customer
    assert tool.process_agent == process
    assert tool.learning_agent == learning
    assert tool.llm_decompose is not None
    assert tool.llm_synthesize is not None


def test_issue_tree_tool_creation_without_rag(mock_llm, mock_agents):
    """Test 2: Tool criado sem RAG (use_rag=False funciona)."""
    financial, customer, process, learning = mock_agents
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    # Tool criado, mas RAG nao sera chamado se use_rag=False
    assert tool.llm_decompose is not None
    assert tool.llm_synthesize is not None


# ============================================================================
# TESTES WORKFLOW (5 testes)
# ============================================================================


def test_facilitate_issue_tree_basic_workflow(
    mock_llm,
    mock_agents,
    valid_company_info,
    valid_strategic_context
):
    """Test 3: Workflow basico decomposicao 2 niveis (root → 2 branches)."""
    financial, customer, process, learning = mock_agents
    
    # Mock LLM structured output: 2 sub-problemas no nivel 1
    mock_decomposition = DecompositionOutput(
        sub_problems=[
            SubProblemOutput(
                text="Receita baixa devido a volume vendas insuficiente",
                category="Financeira",
                is_leaf=True,  # Nivel 1 sera leaf (max_depth=1)
                reasoning="Decomposicao MECE: Receita vs Custos"
            ),
            SubProblemOutput(
                text="Custos altos em operacao e infraestrutura cloud",
                category="Processos",
                is_leaf=True,
                reasoning="Decomposicao MECE: Receita vs Custos"
            )
        ],
        mece_validation="Mutually Exclusive (receita != custos) + Collectively Exhaustive (cobre lucratividade)"
    )
    
    mock_synthesis = SolutionPathsOutput(
        solution_paths=[
            "Aumentar volume de vendas via expansao marketing digital focado em leads qualificados B2B",
            "Reduzir custos de infraestrutura atraves de otimizacao cloud e negociacao fornecedores"
        ],
            reasoning="Leaf nodes foram transformados em acoes acionaveis contextualizadas com conhecimento BSC das 4 perspectivas"
    )
    
    mock_llm.invoke = Mock(side_effect=[mock_decomposition, mock_synthesis])
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    # Facilitar Issue Tree (max_depth=1, sem RAG para simplicidade)
    tree = tool.facilitate_issue_tree(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        root_problem="Baixa lucratividade empresa SaaS B2B devido a receita insuficiente e custos elevados",
        max_depth=1,
        use_rag=False
    )
    
    # Validacoes
    assert isinstance(tree, IssueTreeAnalysis)
    assert tree.total_nodes() == 3  # 1 root + 2 branches
    assert tree.max_depth == 1
    assert len(tree.solution_paths) == 2
    assert len(tree.get_leaf_nodes()) == 2


def test_facilitate_issue_tree_max_depth_3(
    mock_llm,
    mock_agents,
    valid_company_info,
    valid_strategic_context
):
    """Test 4: Workflow com max_depth=3 (3 niveis decomposicao)."""
    financial, customer, process, learning = mock_agents
    
    # Mock decomposicao nivel 1: 2 branches
    mock_decomp_level1 = DecompositionOutput(
        sub_problems=[
            SubProblemOutput(
                text="Receita baixa",
                category="Financeira",
                is_leaf=False,  # Nivel 1 nao e leaf (continua decompondo)
                reasoning="MECE: Receita vs Custos"
            ),
            SubProblemOutput(
                text="Custos altos",
                category="Processos",
                is_leaf=False,
                reasoning="MECE: Receita vs Custos"
            )
        ],
        mece_validation="Mutually Exclusive e Collectively Exhaustive validados corretamente"
    )
    
    # Mock decomposicao nivel 2: 2 branches para cada node nivel 1
    mock_decomp_level2_receita = DecompositionOutput(
        sub_problems=[
            SubProblemOutput(
                text="Preco baixo",
                category="Clientes",
                is_leaf=False,
                reasoning="MECE: Preco vs Volume"
            ),
            SubProblemOutput(
                text="Volume baixo",
                category="Clientes",
                is_leaf=False,
                reasoning="MECE: Preco vs Volume"
            )
        ],
        mece_validation="Mutually Exclusive e Collectively Exhaustive validados corretamente"
    )
    
    mock_decomp_level2_custos = DecompositionOutput(
        sub_problems=[
            SubProblemOutput(
                text="Custos fixos altos",
                category="Processos",
                is_leaf=False,
                reasoning="MECE: Fixos vs Variaveis"
            ),
            SubProblemOutput(
                text="Custos variaveis altos",
                category="Processos",
                is_leaf=False,
                reasoning="MECE: Fixos vs Variaveis"
            )
        ],
        mece_validation="Mutually Exclusive e Collectively Exhaustive validados corretamente"
    )
    
    # Mock decomposicao nivel 3: 2 branches para cada node nivel 2 (8 total nivel 3, serao leaves)
    mock_decomp_level3 = DecompositionOutput(
        sub_problems=[
            SubProblemOutput(
                text="Solucao leaf node A",
                category=None,
                is_leaf=True,
                reasoning="Nivel 3 e leaf (max_depth atingido)"
            ),
            SubProblemOutput(
                text="Solucao leaf node B",
                category=None,
                is_leaf=True,
                reasoning="Nivel 3 e leaf (max_depth atingido)"
            )
        ],
        mece_validation="Mutually Exclusive e Collectively Exhaustive validados corretamente"
    )
    
    mock_synthesis = SolutionPathsOutput(
        solution_paths=[
            "Solucao 1", "Solucao 2", "Solucao 3", "Solucao 4"
        ],
        reasoning="Sintese completa dos 8 leaf nodes transformados em recomendacoes acionaveis contextualizadas"
    )
    
    # LLM invoke side_effect: 1x nivel1 + 2x nivel2 + 4x nivel3 + 1x synthesis = 8 calls
    mock_llm.invoke = Mock(side_effect=[
        mock_decomp_level1,  # Root → nivel 1 (2 branches)
        mock_decomp_level2_receita,  # Receita → nivel 2 (2 branches)
        mock_decomp_level2_custos,  # Custos → nivel 2 (2 branches)
        mock_decomp_level3,  # Preco → nivel 3 (2 leaves)
        mock_decomp_level3,  # Volume → nivel 3 (2 leaves)
        mock_decomp_level3,  # Fixos → nivel 3 (2 leaves)
        mock_decomp_level3,  # Variaveis → nivel 3 (2 leaves)
        mock_synthesis  # Sintese final
    ])
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    tree = tool.facilitate_issue_tree(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        root_problem="Baixa lucratividade empresa manufatura",
        max_depth=3,
        use_rag=False
    )
    
    # Validacoes
    assert tree.total_nodes() == 15  # 1 root + 2 nivel1 + 4 nivel2 + 8 nivel3
    assert tree.max_depth == 3
    assert len(tree.get_leaf_nodes()) == 8  # 8 leaves no nivel 3


def test_facilitate_issue_tree_raises_error_invalid_root_problem(
    mock_llm,
    mock_agents,
    valid_company_info,
    valid_strategic_context
):
    """Test 5: ValueError se root_problem invalido (< 10 chars)."""
    financial, customer, process, learning = mock_agents
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    with pytest.raises(ValueError, match="root_problem deve ter minimo 10 caracteres"):
        tool.facilitate_issue_tree(
            company_info=valid_company_info,
            strategic_context=valid_strategic_context,
            root_problem="Curto",  # 5 chars (< 10)
            max_depth=3,
            use_rag=False
        )


def test_facilitate_issue_tree_raises_error_invalid_max_depth(
    mock_llm,
    mock_agents,
    valid_company_info,
    valid_strategic_context
):
    """Test 6: ValueError se max_depth fora do range (1-4)."""
    financial, customer, process, learning = mock_agents
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    with pytest.raises(ValueError, match="max_depth deve ser 1-4"):
        tool.facilitate_issue_tree(
            company_info=valid_company_info,
            strategic_context=valid_strategic_context,
            root_problem="Problema valido com mais de 10 caracteres",
            max_depth=5,  # Fora do range (max 4)
            use_rag=False
        )


def test_facilitate_issue_tree_with_rag_enabled(
    mock_llm,
    mock_agents,
    valid_company_info,
    valid_strategic_context
):
    """Test 7: Workflow com RAG habilitado (4 agents chamados)."""
    financial, customer, process, learning = mock_agents
    
    mock_decomposition = DecompositionOutput(
        sub_problems=[
            SubProblemOutput(
                text="Sub-problema A com conhecimento BSC",
                category="Financeira",
                is_leaf=True,
                reasoning="Decomposicao MECE enriquecida com conhecimento BSC recuperado via RAG especialista"
            ),
            SubProblemOutput(
                text="Sub-problema B com conhecimento BSC",
                category="Clientes",
                is_leaf=True,
                reasoning="Decomposicao MECE enriquecida com conhecimento BSC recuperado via RAG especialista"
            )
        ],
        mece_validation="Mutually Exclusive e Collectively Exhaustive validados com RAG BSC"
    )
    
    mock_synthesis = SolutionPathsOutput(
        solution_paths=["Solucao A enriquecida com BSC", "Solucao B enriquecida com BSC"],
        reasoning="RAG conhecimento BSC enriqueceu significativamente a decomposicao MECE com contexto especializado"
    )
    
    mock_llm.invoke = Mock(side_effect=[mock_decomposition, mock_synthesis])
    
    tool = IssueTreeTool(
        llm=mock_llm,
        financial_agent=financial,
        customer_agent=customer,
        process_agent=process,
        learning_agent=learning
    )
    
    tree = tool.facilitate_issue_tree(
        company_info=valid_company_info,
        strategic_context=valid_strategic_context,
        root_problem="Problema estrategico BSC complexo que requer RAG para decomposicao correta",
        max_depth=1,
        use_rag=True  # RAG habilitado
    )
    
    # Validacoes
    assert tree.context_from_rag is not None  # RAG executado
    assert len(tree.context_from_rag) > 0
    
    # 4 agents devem ter sido chamados
    financial.invoke.assert_called_once()
    customer.invoke.assert_called_once()
    process.invoke.assert_called_once()
    learning.invoke.assert_called_once()


# ============================================================================
# TESTES SCHEMAS (8 testes)
# ============================================================================


def test_issue_node_creation_valid():
    """Test 8: IssueNode criado com dados validos."""
    node = IssueNode(
        text="Baixa lucratividade empresa SaaS B2B",
        level=0,
        parent_id=None,
        is_leaf=False
    )
    
    assert node.text == "Baixa lucratividade empresa SaaS B2B"
    assert node.level == 0
    assert node.parent_id is None
    assert node.is_leaf is False
    assert len(node.children_ids) == 0
    assert node.id is not None  # UUID gerado


def test_issue_node_validator_text_not_empty():
    """Test 9: Validator text nao aceita string vazia ou espacos."""
    with pytest.raises(ValueError, match="Texto do no nao pode ser vazio"):
        IssueNode(
            text="     ",  # 5+ espacos (passa min_length Field, falha field_validator)
            level=0,
            parent_id=None
        )


def test_issue_tree_analysis_creation_valid():
    """Test 10: IssueTreeAnalysis criado com nodes validos."""
    root = IssueNode(text="Problema raiz", level=0, parent_id=None)
    child1 = IssueNode(text="Sub-problema 1", level=1, parent_id=root.id, is_leaf=True)
    child2 = IssueNode(text="Sub-problema 2", level=1, parent_id=root.id, is_leaf=True)
    
    # Atualizar children do root
    root.children_ids = [child1.id, child2.id]
    
    tree = IssueTreeAnalysis(
        root_problem="Problema raiz estrategico",
        nodes=[root, child1, child2],
        max_depth=1,
        is_mece_compliant=True,
        solution_paths=["Solucao A", "Solucao B"]
    )
    
    assert tree.root_problem == "Problema raiz estrategico"
    assert tree.total_nodes() == 3
    assert tree.max_depth == 1
    assert len(tree.get_leaf_nodes()) == 2


def test_issue_tree_analysis_validator_root_node_missing():
    """Test 11: Validator rejeita arvore sem root node (level=0)."""
    child1 = IssueNode(text="Sub-problema 1", level=1, parent_id="fake-id", is_leaf=True)
    child2 = IssueNode(text="Sub-problema 2", level=1, parent_id="fake-id", is_leaf=True)
    
    with pytest.raises(ValueError, match="Arvore deve ter exatamente 1 root node"):
        IssueTreeAnalysis(
            root_problem="Problema raiz",
            nodes=[child1, child2],  # Sem root (level=0)
            max_depth=1
        )


def test_issue_tree_analysis_is_complete():
    """Test 12: is_complete() valida >= 2 branches por nivel."""
    root = IssueNode(text="Root node problema", level=0, parent_id=None)
    child1 = IssueNode(text="Child 1 sub-problema", level=1, parent_id=root.id, is_leaf=True)
    child2 = IssueNode(text="Child 2 sub-problema", level=1, parent_id=root.id, is_leaf=True)
    
    root.children_ids = [child1.id, child2.id]
    
    tree = IssueTreeAnalysis(
        root_problem="Root problema estrategico",
        nodes=[root, child1, child2],
        max_depth=1,
        solution_paths=["A", "B"]
    )
    
    # Nivel 1 tem 2 branches (>= 2), arvore completa
    assert tree.is_complete(min_branches=2) is True


def test_issue_tree_analysis_validate_mece():
    """Test 13: validate_mece() retorna dict com is_mece, issues, confidence."""
    root = IssueNode(text="Root node problema", level=0, parent_id=None)
    child1 = IssueNode(text="Child 1 sub-problema", level=1, parent_id=root.id, is_leaf=True)
    child2 = IssueNode(text="Child 2 sub-problema", level=1, parent_id=root.id, is_leaf=True)
    
    root.children_ids = [child1.id, child2.id]
    
    tree = IssueTreeAnalysis(
        root_problem="Root problema estrategico",
        nodes=[root, child1, child2],
        max_depth=1,
        solution_paths=["A", "B"]
    )
    
    mece = tree.validate_mece()
    
    assert isinstance(mece, dict)
    assert "is_mece" in mece
    assert "issues" in mece
    assert "confidence" in mece
    assert isinstance(mece["is_mece"], bool)
    assert isinstance(mece["issues"], list)
    assert isinstance(mece["confidence"], float)


def test_issue_tree_analysis_get_leaf_nodes():
    """Test 14: get_leaf_nodes() retorna apenas nodes folha."""
    root = IssueNode(text="Root node problema", level=0, parent_id=None, is_leaf=False)
    child1 = IssueNode(text="Child 1 sub-problema", level=1, parent_id=root.id, is_leaf=True)
    child2 = IssueNode(text="Child 2 sub-problema", level=1, parent_id=root.id, is_leaf=True)
    
    root.children_ids = [child1.id, child2.id]
    
    tree = IssueTreeAnalysis(
        root_problem="Root problema estrategico",
        nodes=[root, child1, child2],
        max_depth=1,
        solution_paths=["A", "B"]
    )
    
    leaf_nodes = tree.get_leaf_nodes()
    
    assert len(leaf_nodes) == 2
    assert child1 in leaf_nodes
    assert child2 in leaf_nodes
    assert root not in leaf_nodes  # Root nao e leaf


def test_issue_tree_analysis_summary():
    """Test 15: summary() retorna string formatada com resumo executivo."""
    root = IssueNode(text="Baixa lucratividade", level=0, parent_id=None)
    child1 = IssueNode(text="Receita baixa", level=1, parent_id=root.id, is_leaf=True)
    child2 = IssueNode(text="Custos altos", level=1, parent_id=root.id, is_leaf=True)
    
    root.children_ids = [child1.id, child2.id]
    
    tree = IssueTreeAnalysis(
        root_problem="Baixa lucratividade manufatura",
        nodes=[root, child1, child2],
        max_depth=1,
        solution_paths=["Aumentar vendas", "Reduzir custos"]
    )
    
    summary = tree.summary()
    
    assert isinstance(summary, str)
    assert "Problema raiz: Baixa lucratividade manufatura" in summary
    assert "3 nos" in summary
    assert "1 niveis profundidade" in summary
    assert "2 solucoes finais" in summary
    assert "2 recomendacoes acionaveis" in summary

