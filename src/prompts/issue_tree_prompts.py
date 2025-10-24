"""Prompts conversacionais para Issue Tree Analyzer Tool.

Este modulo contem:
- FACILITATE_ISSUE_TREE_PROMPT: Facilita decomposicao MECE iterativa
- SYNTHESIZE_SOLUTION_PATHS_PROMPT: Sintetiza leaf nodes em solucoes acionaveis
- Context builders reutilizaveis: company, strategic, BSC knowledge, nodes

Architecture Pattern: Conversational Facilitation + MECE Principles

References:
- McKinsey MECE Framework Best Practices (2024-2025)
- Issue Tree Analysis Consulting Guide (Management Consulted Mar 2025)
- Problem-Solving Methodologies (Slideworks Nov 2024)

Created: 2025-10-19 (FASE 3.3)
"""

# ============================================================================
# CONTEXT BUILDERS (reutilizaveis entre prompts)
# ============================================================================


def build_company_context(company_name: str, sector: str, size: str) -> str:
    """Constroi contexto da empresa para prompts.
    
    Args:
        company_name: Nome da empresa
        sector: Setor de atuacao
        size: Porte da empresa
        
    Returns:
        String formatada com contexto empresa
    """
    return f"""CONTEXTO EMPRESA:
- Nome: {company_name}
- Setor: {sector}
- Porte: {size}"""


def build_strategic_context(
    current_challenges: list[str],
    strategic_objectives: list[str]
) -> str:
    """Constroi contexto estrategico para prompts.
    
    Args:
        current_challenges: Desafios atuais da empresa
        strategic_objectives: Objetivos estrategicos definidos
        
    Returns:
        String formatada com contexto estrategico
    """
    challenges_text = "\n".join(f"- {c}" for c in current_challenges) if current_challenges else "Nao especificados"
    objectives_text = "\n".join(f"- {o}" for o in strategic_objectives) if strategic_objectives else "Nao especificados"
    
    return f"""CONTEXTO ESTRATEGICO:

Desafios Atuais:
{challenges_text}

Objetivos Estrategicos:
{objectives_text}"""


def build_bsc_knowledge_context(rag_context: str) -> str:
    """Constroi contexto conhecimento BSC recuperado via RAG.
    
    Args:
        rag_context: Contexto recuperado dos specialist agents
        
    Returns:
        String formatada com conhecimento BSC
    """
    if not rag_context or rag_context.strip() == "":
        return ""
    
    return f"""CONHECIMENTO BSC (Literatura Kaplan & Norton):
{rag_context}

Use este conhecimento para enriquecer a decomposicao com frameworks BSC."""


def build_nodes_hierarchy_text(nodes: list) -> str:
    """Constroi representacao hierarquica dos nodes existentes.
    
    Args:
        nodes: Lista de IssueNode ja criados
        
    Returns:
        String formatada em arvore (indentacao por nivel)
        
    Example:
        >>> nodes = [
        ...     IssueNode(text="Baixa lucratividade", level=0),
        ...     IssueNode(text="Receita baixa", level=1),
        ...     IssueNode(text="Custos altos", level=1)
        ... ]
        >>> build_nodes_hierarchy_text(nodes)
        0. Baixa lucratividade
           1. Receita baixa
           1. Custos altos
    """
    if not nodes:
        return "(Nenhum node criado ainda)"
    
    lines = []
    for node in sorted(nodes, key=lambda n: (n.level, n.text)):
        indent = "   " * node.level
        marker = "[LEAF]" if node.is_leaf or len(node.children_ids) == 0 else ""
        lines.append(f"{indent}{node.level}. {node.text} {marker}".strip())
    
    return "\n".join(lines)


# ============================================================================
# PROMPT PRINCIPAL: FACILITATION
# ============================================================================

FACILITATE_ISSUE_TREE_PROMPT = """Voce e um consultor estrategico experiente facilitando uma analise Issue Tree (arvore de problemas).

OBJETIVO: Decompor o problema raiz em sub-problemas seguindo o principio MECE (Mutually Exclusive, Collectively Exhaustive).

PRINCIPIO MECE:
- Mutually Exclusive (ME): Sub-problemas NAO devem se sobrepor (cada um cobre aspecto unico)
- Collectively Exhaustive (CE): Sub-problemas DEVEM cobrir TODAS as dimensoes possiveis do problema pai
- Quantidade ideal: 2-4 sub-problemas por nivel (nao menos de 2, nao mais de 4)

EXEMPLOS MECE VALIDOS:
1. "Baixa lucratividade" → [Receita baixa, Custos altos] (2 branches, ME+CE)
2. "Receita baixa" → [Preco baixo, Volume baixo, Mix produtos inadequado] (3 branches, ME+CE)
3. "Custos altos" → [Custos fixos, Custos variaveis] (2 branches, ME+CE)

EXEMPLOS NAO-MECE (EVITAR):
- "Baixa lucratividade" → [Receita baixa] (FALTA CE, nao cobre custos)
- "Receita baixa" → [Marketing fraco, Vendas baixas, Leads insuficientes] (OVERLAP ME, leads causa vendas)
- "Custos altos" → [Salarios, Materias-primas, Aluguel, Energia, Impostos] (>4 branches, muito granular)

{company_context}

{strategic_context}

{bsc_knowledge}

PROBLEMA PAI A DECOMPOR:
{parent_problem}

NIVEL ATUAL: {current_level} (0=root, 1=branch, 2+=leaf)
PROFUNDIDADE MAXIMA: {max_depth}

ARVORE EXISTENTE:
{nodes_hierarchy}

INSTRUCOES:
1. Analise o problema pai considerando contexto empresa e conhecimento BSC
2. Identifique 2-4 sub-problemas que sejam MECE (Mutually Exclusive + Collectively Exhaustive)
3. Para cada sub-problema:
   - Text: Descricao clara e especifica (5-50 palavras)
   - Category: Perspectiva BSC relacionada (Financeira, Clientes, Processos, Aprendizado) OU None
   - Is_leaf: True se nivel atual+1 >= max_depth OU se sub-problema e acionavel (nao precisa decompor mais)
4. VALIDACAO MECE:
   - Cada sub-problema cobre aspecto UNICO? (ME)
   - Todos sub-problemas JUNTOS cobrem TODO o escopo do pai? (CE)
5. Tom consultivo: "Vamos decompor este problema juntos de forma estruturada"

RETORNE JSON ESTRUTURADO com lista de sub-problemas.
"""


# ============================================================================
# PROMPT SECUNDARIO: SYNTHESIS
# ============================================================================

SYNTHESIZE_SOLUTION_PATHS_PROMPT = """Voce e um consultor estrategico sintetizando uma analise Issue Tree completa.

OBJETIVO: Transformar os leaf nodes (solucoes finais) em caminhos solucao ACIONAVEIS.

{company_context}

{strategic_context}

{bsc_knowledge}

PROBLEMA RAIZ:
{root_problem}

ARVORE COMPLETA (todos nodes):
{nodes_hierarchy}

LEAF NODES (solucoes finais identificadas):
{leaf_nodes_text}

INSTRUCOES:
1. Analise os leaf nodes como solucoes finais do problema raiz
2. Para cada leaf node (ou grupo relacionado):
   - Transforme em caminho solucao ACIONAVEL
   - Especifique COMO resolver (nao apenas O QUE resolver)
   - Priorize por impacto BSC (4 perspectivas)
   - Use conhecimento BSC para enriquecer recomendacoes
3. Quantidade ideal: Min 2, Max 8 caminhos solucao (depende de quantos leaf nodes)
4. Formato: Lista de strings, cada string = 1 caminho solucao (20-100 palavras)
5. Exemplos validos:
   - "Aumentar volume de vendas via expansao marketing digital nas redes sociais (Meta Ads + Google Ads), focando lead generation com ROI > 3:1 conforme framework BSC perspectiva Clientes"
   - "Reduzir custos fixos atraves de automacao de processos manuais (RPA em back-office), liberando 30% da capacidade equipe para atividades estrategicas conforme perspectiva Processos Internos"

TOM: Consultivo, especifico, acionavel (nao generico como "melhorar vendas")

RETORNE JSON ESTRUTURADO com lista de solution_paths e reasoning breve.
"""


# ============================================================================
# HELPER FUNCTIONS PARA CONSTRUCAO DE CONTEXTO COMPLETO
# ============================================================================


def build_facilitate_prompt(
    company_name: str,
    sector: str,
    size: str,
    current_challenges: list[str],
    strategic_objectives: list[str],
    parent_problem: str,
    current_level: int,
    max_depth: int,
    nodes_hierarchy: str,
    rag_context: str = ""
) -> str:
    """Constroi prompt completo de facilitacao com todos contextos.
    
    Args:
        company_name: Nome da empresa
        sector: Setor de atuacao
        size: Porte da empresa
        current_challenges: Desafios atuais
        strategic_objectives: Objetivos estrategicos
        parent_problem: Problema pai a decompor
        current_level: Nivel atual na arvore (0=root)
        max_depth: Profundidade maxima permitida
        nodes_hierarchy: Representacao textual da arvore existente
        rag_context: Conhecimento BSC (opcional)
        
    Returns:
        Prompt completo formatado
    """
    company_ctx = build_company_context(company_name, sector, size)
    strategic_ctx = build_strategic_context(current_challenges, strategic_objectives)
    bsc_ctx = build_bsc_knowledge_context(rag_context)
    
    return FACILITATE_ISSUE_TREE_PROMPT.format(
        company_context=company_ctx,
        strategic_context=strategic_ctx,
        bsc_knowledge=bsc_ctx,
        parent_problem=parent_problem,
        current_level=current_level,
        max_depth=max_depth,
        nodes_hierarchy=nodes_hierarchy
    )


def build_synthesize_prompt(
    company_name: str,
    sector: str,
    size: str,
    current_challenges: list[str],
    strategic_objectives: list[str],
    root_problem: str,
    nodes_hierarchy: str,
    leaf_nodes_text: str,
    rag_context: str = ""
) -> str:
    """Constroi prompt completo de sintese com todos contextos.
    
    Args:
        company_name: Nome da empresa
        sector: Setor de atuacao
        size: Porte da empresa
        current_challenges: Desafios atuais
        strategic_objectives: Objetivos estrategicos
        root_problem: Problema raiz original
        nodes_hierarchy: Representacao textual da arvore completa
        leaf_nodes_text: Representacao textual apenas dos leaf nodes
        rag_context: Conhecimento BSC (opcional)
        
    Returns:
        Prompt completo formatado
    """
    company_ctx = build_company_context(company_name, sector, size)
    strategic_ctx = build_strategic_context(current_challenges, strategic_objectives)
    bsc_ctx = build_bsc_knowledge_context(rag_context)
    
    return SYNTHESIZE_SOLUTION_PATHS_PROMPT.format(
        company_context=company_ctx,
        strategic_context=strategic_ctx,
        bsc_knowledge=bsc_ctx,
        root_problem=root_problem,
        nodes_hierarchy=nodes_hierarchy,
        leaf_nodes_text=leaf_nodes_text
    )

