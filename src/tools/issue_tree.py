"""Issue Tree Analyzer Tool - Ferramenta de decomposicao estruturada MECE.

Esta tool facilita analise Issue Tree (arvore de problemas) usando:
- ClientProfile do onboarding
- Conhecimento BSC via RAG (specialist agents)
- LLM structured output (Pydantic)
- Decomposicao iterativa MECE (2-4 branches por nivel, max depth 3-4)

Architecture Pattern: Iterative Tool → Prompt MECE → LLM + RAG → Tree Building → Synthesis

References:
- McKinsey MECE Framework Best Practices (2024-2025)
- Issue Tree Analysis Consulting (Management Consulted Mar 2025)
- Slideworks Problem-Solving Process (Nov 2024)

Created: 2025-10-19 (FASE 3.3)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import logging

from pydantic import ValidationError, BaseModel, Field
from langchain_core.language_models import BaseLLM

from src.memory.schemas import (
    IssueTreeAnalysis,
    IssueNode,
    CompanyInfo,
    StrategicContext,
)
from src.prompts.issue_tree_prompts import (
    build_facilitate_prompt,
    build_synthesize_prompt,
    build_nodes_hierarchy_text,
)

if TYPE_CHECKING:
    from src.agents.financial_agent import FinancialAgent
    from src.agents.customer_agent import CustomerAgent
    from src.agents.process_agent import ProcessAgent
    from src.agents.learning_agent import LearningAgent

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER SCHEMAS (para structured output iterativo)
# ============================================================================


class SubProblemOutput(BaseModel):
    """Output estruturado de um sub-problema na decomposicao."""
    
    text: str = Field(
        min_length=5,
        max_length=300,
        description="Descricao do sub-problema"
    )
    category: Optional[str] = Field(
        default=None,
        description="Perspectiva BSC (Financeira, Clientes, Processos, Aprendizado) ou None"
    )
    is_leaf: bool = Field(
        default=False,
        description="True se sub-problema e folha (nao precisa decompor mais)"
    )
    reasoning: str = Field(
        min_length=20,
        description="Breve explicacao da decomposicao MECE"
    )


class DecompositionOutput(BaseModel):
    """Output estruturado de uma iteracao de decomposicao."""
    
    sub_problems: list[SubProblemOutput] = Field(
        min_length=2,
        max_length=4,
        description="Sub-problemas identificados (2-4 para MECE)"
    )
    mece_validation: str = Field(
        min_length=20,
        description="Validacao manual MECE (Mutually Exclusive + Collectively Exhaustive)"
    )


class SolutionPathsOutput(BaseModel):
    """Output estruturado da sintese de solution paths."""
    
    solution_paths: list[str] = Field(
        min_length=2,
        max_length=8,
        description="Caminhos solucao acionaveis (transformacao leaf nodes)"
    )
    reasoning: str = Field(
        min_length=50,
        description="Explicacao de como leaf nodes foram sintetizados"
    )


# ============================================================================
# ISSUE TREE TOOL (Main Class)
# ============================================================================


class IssueTreeTool:
    """Ferramenta para facilitar analise Issue Tree estruturada com MECE + BSC.
    
    Esta tool combina:
    1. Contexto da empresa (ClientProfile)
    2. Conhecimento BSC (via RAG com specialist agents)
    3. LLM facilitation (GPT-4o-mini structured output)
    4. Decomposicao iterativa MECE (2-4 branches por nivel)
    5. Sintese final (leaf nodes → solution paths acionaveis)
    
    Attributes:
        llm: Language model para facilitation
        financial_agent: Agente financeira para RAG
        customer_agent: Agente clientes para RAG
        process_agent: Agente processos para RAG
        learning_agent: Agente aprendizado para RAG
        
    Example:
        >>> tool = IssueTreeTool(llm, financial, customer, process, learning)
        >>> tree = tool.facilitate_issue_tree(company_info, strategic_context, root_problem="Baixa lucratividade")
        >>> tree.is_complete()  # True se >= 2 branches por nivel
        >>> tree.validate_mece()  # {"is_mece": True, "issues": [], "confidence": 0.85}
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        financial_agent: FinancialAgent,
        customer_agent: CustomerAgent,
        process_agent: ProcessAgent,
        learning_agent: LearningAgent,
    ):
        """Inicializa Issue Tree tool com LLM e 4 specialist agents.
        
        Args:
            llm: LLM para structured output (recomendado GPT-4o-mini)
            financial_agent: Agente perspectiva financeira
            customer_agent: Agente perspectiva clientes
            process_agent: Agente perspectiva processos
            learning_agent: Agente perspectiva aprendizado
        """
        self.llm = llm
        self.financial_agent = financial_agent
        self.customer_agent = customer_agent
        self.process_agent = process_agent
        self.learning_agent = learning_agent
        
        # LLM configurado para structured outputs
        self.llm_decompose = self.llm.with_structured_output(DecompositionOutput)
        self.llm_synthesize = self.llm.with_structured_output(SolutionPathsOutput)
        
        logger.info("[Issue Tree Tool] Inicializado com 4 specialist agents para RAG")
    
    def facilitate_issue_tree(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        root_problem: str,
        max_depth: int = 3,
        use_rag: bool = True
    ) -> IssueTreeAnalysis:
        """Facilita analise Issue Tree completa (decomposicao + sintese).
        
        Processo:
        1. Cria root node (nivel 0)
        2. Decompoe iterativamente cada node nao-folha (niveis 1, 2, 3...)
        3. Para quando atinge max_depth OU todos nodes sao folhas
        4. Recupera conhecimento BSC via RAG (optional)
        5. Sintetiza leaf nodes em solution paths acionaveis
        
        Args:
            company_info: Informacoes da empresa
            strategic_context: Desafios e objetivos
            root_problem: Problema raiz a decompor (min 10 chars)
            max_depth: Profundidade maxima (default 3, min 1, max 4)
            use_rag: Se True, recupera conhecimento BSC via specialist agents
            
        Returns:
            IssueTreeAnalysis completo com nodes hierarquicos e solution paths
            
        Raises:
            ValueError: Se root_problem invalido ou max_depth fora do range
            Exception: Se LLM falha persistentemente (apos retry)
            
        Example:
            >>> tree = tool.facilitate_issue_tree(
            ...     company_info,
            ...     strategic_context,
            ...     root_problem="Baixa lucratividade empresa manufatura",
            ...     max_depth=3,
            ...     use_rag=True
            ... )
            >>> tree.total_nodes()
            15  # 1 root + 14 sub-problemas
            >>> tree.max_depth
            3
            >>> len(tree.solution_paths)
            6  # 6 caminhos solucao sintetizados
        """
        logger.info(f"[Issue Tree] Iniciando analise: root_problem='{root_problem[:50]}...', max_depth={max_depth}")
        
        # Validacoes
        if not root_problem or len(root_problem.strip()) < 10:
            raise ValueError(f"root_problem deve ter minimo 10 caracteres (recebido: {len(root_problem)})")
        
        if not (1 <= max_depth <= 4):
            raise ValueError(f"max_depth deve ser 1-4 (recebido: {max_depth})")
        
        # STEP 1: Criar root node (nivel 0)
        root_node = IssueNode(
            text=root_problem.strip(),
            level=0,
            parent_id=None,
            is_leaf=False  # Root nunca e folha (sempre decompoe)
        )
        
        nodes = [root_node]
        logger.info(f"[Issue Tree] Root node criado: id={root_node.id}, text='{root_node.text[:50]}...'")
        
        # STEP 2: Recuperar conhecimento BSC via RAG (optional, apenas 1x no inicio)
        rag_context = ""
        if use_rag:
            rag_context = self._retrieve_bsc_knowledge(
                company_info,
                strategic_context,
                root_problem
            )
            logger.info(f"[Issue Tree] RAG executado: {len(rag_context)} chars conhecimento BSC")
        else:
            logger.info("[Issue Tree] RAG desabilitado (use_rag=False)")
        
        # STEP 3: Decomposicao iterativa MECE (nivel por nivel)
        current_level = 0
        while current_level < max_depth:
            # Encontrar nodes nao-folha do nivel atual
            nodes_to_decompose = [
                n for n in nodes
                if n.level == current_level and not n.is_leaf and len(n.children_ids) == 0
            ]
            
            if not nodes_to_decompose:
                logger.info(f"[Issue Tree] Decomposicao completa no nivel {current_level} (sem nodes para decompor)")
                break
            
            logger.info(f"[Issue Tree] Decomposicao nivel {current_level}: {len(nodes_to_decompose)} nodes")
            
            # Decompor cada node nao-folha
            for parent_node in nodes_to_decompose:
                try:
                    children_nodes = self._decompose_node(
                        parent_node=parent_node,
                        company_info=company_info,
                        strategic_context=strategic_context,
                        current_level=current_level + 1,
                        max_depth=max_depth,
                        nodes=nodes,
                        rag_context=rag_context
                    )
                    
                    # Atualizar parent com children IDs
                    parent_node.children_ids = [c.id for c in children_nodes]
                    
                    # Adicionar children a lista de nodes
                    nodes.extend(children_nodes)
                    
                    logger.info(f"[Issue Tree] Node decomposto: parent='{parent_node.text[:30]}...', {len(children_nodes)} children criados")
                
                except Exception as e:
                    # Se decomposicao falha, marcar parent como leaf (fallback)
                    logger.warning(f"[Issue Tree] Falha ao decompor node '{parent_node.text[:30]}...': {e}")
                    parent_node.is_leaf = True
                    logger.info(f"[Issue Tree] Node marcado como leaf (fallback): {parent_node.id}")
                    continue
            
            # Proximo nivel
            current_level += 1
        
        # STEP 4: Calcular max_depth real atingido
        actual_max_depth = max(n.level for n in nodes) if nodes else 0
        
        # STEP 5: Marcar nodes sem children como folhas (se nao foram marcados ainda)
        for node in nodes:
            if len(node.children_ids) == 0 and not node.is_leaf and node.level > 0:
                node.is_leaf = True
        
        logger.info(f"[Issue Tree] Arvore construida: {len(nodes)} nodes, {actual_max_depth} niveis profundidade")
        
        # STEP 6: Sintetizar leaf nodes em solution paths
        solution_paths = self._synthesize_solution_paths(
            company_info=company_info,
            strategic_context=strategic_context,
            root_problem=root_problem,
            nodes=nodes,
            rag_context=rag_context
        )
        
        logger.info(f"[Issue Tree] Sintese completa: {len(solution_paths)} solution paths gerados")
        
        # STEP 7: Criar IssueTreeAnalysis final
        tree_analysis = IssueTreeAnalysis(
            root_problem=root_problem,
            nodes=nodes,
            max_depth=actual_max_depth,
            is_mece_compliant=False,  # Manual validation requerida
            solution_paths=solution_paths,
            context_from_rag=rag_context if rag_context else None
        )
        
        logger.info(f"[Issue Tree] Analise completa: {tree_analysis.summary()}")
        
        return tree_analysis
    
    def _decompose_node(
        self,
        parent_node: IssueNode,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        current_level: int,
        max_depth: int,
        nodes: list[IssueNode],
        rag_context: str
    ) -> list[IssueNode]:
        """Decompoe um node pai em 2-4 sub-problemas MECE.
        
        Args:
            parent_node: Node pai a decompor
            company_info: Informacoes da empresa
            strategic_context: Desafios e objetivos
            current_level: Nivel dos children (parent.level + 1)
            max_depth: Profundidade maxima
            nodes: Lista completa de nodes (para hierarquia)
            rag_context: Conhecimento BSC recuperado
            
        Returns:
            Lista de 2-4 IssueNodes children
            
        Raises:
            Exception: Se LLM falha ou retorna dados invalidos
        """
        # Construir prompt de decomposicao
        nodes_hierarchy = build_nodes_hierarchy_text(nodes)
        prompt = build_facilitate_prompt(
            company_name=company_info.name,
            sector=company_info.sector,
            size=company_info.size,
            current_challenges=strategic_context.current_challenges,
            strategic_objectives=strategic_context.strategic_objectives,
            parent_problem=parent_node.text,
            current_level=current_level,
            max_depth=max_depth,
            nodes_hierarchy=nodes_hierarchy,
            rag_context=rag_context
        )
        
        # LLM structured output
        try:
            decomposition: DecompositionOutput = self.llm_decompose.invoke(prompt)
            
            # Validar quantidade (2-4 sub-problemas)
            if not (2 <= len(decomposition.sub_problems) <= 4):
                raise ValueError(f"Decomposicao deve ter 2-4 sub-problemas (recebido: {len(decomposition.sub_problems)})")
            
            # Criar IssueNodes children
            children_nodes = []
            for sub_prob in decomposition.sub_problems:
                child_node = IssueNode(
                    text=sub_prob.text.strip(),
                    level=current_level,
                    parent_id=parent_node.id,
                    is_leaf=sub_prob.is_leaf or current_level >= max_depth,  # Leaf se LLM disse OU max depth
                    category=sub_prob.category
                )
                children_nodes.append(child_node)
            
            logger.debug(f"[Issue Tree] Decomposicao LLM: {len(children_nodes)} sub-problemas, MECE validation: {decomposition.mece_validation[:50]}...")
            
            return children_nodes
        
        except ValidationError as e:
            logger.error(f"[Issue Tree] Validacao Pydantic falhou: {e}")
            raise Exception(f"LLM retornou dados invalidos: {e}")
        
        except Exception as e:
            logger.error(f"[Issue Tree] Falha na decomposicao LLM: {e}")
            raise Exception(f"Falha ao decompor node: {e}")
    
    def _retrieve_bsc_knowledge(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        root_problem: str
    ) -> str:
        """Recupera conhecimento BSC via RAG (4 specialist agents).
        
        Args:
            company_info: Informacoes da empresa
            strategic_context: Desafios e objetivos
            root_problem: Problema raiz para query RAG
            
        Returns:
            String com conhecimento BSC consolidado (ou vazio se falha)
        """
        try:
            # Construir query RAG baseada no root problem + contexto
            rag_query = f"""Contexto empresa: {company_info.name} (setor {company_info.sector}, porte {company_info.size}).

Problema estrategico: {root_problem}

Desafios atuais: {', '.join(strategic_context.current_challenges[:3]) if strategic_context.current_challenges else 'Nao especificados'}

Buscar conhecimento BSC (Balanced Scorecard Kaplan & Norton) sobre decomposicao de problemas estrategicos similares, frameworks de analise, e recomendacoes para as 4 perspectivas BSC."""
            
            logger.info(f"[Issue Tree RAG] Query construida: {rag_query[:100]}...")
            
            # Executar RAG nos 4 specialist agents (paralelo seria ideal, mas sequential ok)
            knowledge_parts = []
            
            # Perspectiva Financeira
            try:
                financial_result = self.financial_agent.invoke(rag_query)
                if isinstance(financial_result, dict) and "response" in financial_result:
                    knowledge_parts.append(f"[Perspectiva Financeira BSC]\n{financial_result['response']}")
            except Exception as e:
                logger.warning(f"[Issue Tree RAG] Financial agent falhou: {e}")
            
            # Perspectiva Clientes
            try:
                customer_result = self.customer_agent.invoke(rag_query)
                if isinstance(customer_result, dict) and "response" in customer_result:
                    knowledge_parts.append(f"[Perspectiva Clientes BSC]\n{customer_result['response']}")
            except Exception as e:
                logger.warning(f"[Issue Tree RAG] Customer agent falhou: {e}")
            
            # Perspectiva Processos
            try:
                process_result = self.process_agent.invoke(rag_query)
                if isinstance(process_result, dict) and "response" in process_result:
                    knowledge_parts.append(f"[Perspectiva Processos Internos BSC]\n{process_result['response']}")
            except Exception as e:
                logger.warning(f"[Issue Tree RAG] Process agent falhou: {e}")
            
            # Perspectiva Aprendizado
            try:
                learning_result = self.learning_agent.invoke(rag_query)
                if isinstance(learning_result, dict) and "response" in learning_result:
                    knowledge_parts.append(f"[Perspectiva Aprendizado e Crescimento BSC]\n{learning_result['response']}")
            except Exception as e:
                logger.warning(f"[Issue Tree RAG] Learning agent falhou: {e}")
            
            # Consolidar conhecimento
            if knowledge_parts:
                consolidated = "\n\n".join(knowledge_parts)
                logger.info(f"[Issue Tree RAG] Conhecimento consolidado: {len(knowledge_parts)} perspectivas, {len(consolidated)} chars")
                return consolidated
            else:
                logger.warning("[Issue Tree RAG] Nenhum conhecimento recuperado (todos agents falharam)")
                return ""
        
        except Exception as e:
            logger.error(f"[Issue Tree RAG] Falha geral: {e}")
            return ""
    
    def _synthesize_solution_paths(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        root_problem: str,
        nodes: list[IssueNode],
        rag_context: str
    ) -> list[str]:
        """Sintetiza leaf nodes em solution paths acionaveis.
        
        Args:
            company_info: Informacoes da empresa
            strategic_context: Desafios e objetivos
            root_problem: Problema raiz original
            nodes: Lista completa de nodes da arvore
            rag_context: Conhecimento BSC recuperado
            
        Returns:
            Lista de solution paths (strings acionaveis)
        """
        try:
            # Identificar leaf nodes
            leaf_nodes = [n for n in nodes if n.is_leaf or len(n.children_ids) == 0]
            
            if not leaf_nodes:
                logger.warning("[Issue Tree Synthesis] Nenhum leaf node identificado (arvore incompleta)")
                return []
            
            # Construir representacoes textuais
            nodes_hierarchy = build_nodes_hierarchy_text(nodes)
            leaf_nodes_text = "\n".join(f"- {n.text} (nivel {n.level})" for n in leaf_nodes)
            
            # Construir prompt de sintese
            prompt = build_synthesize_prompt(
                company_name=company_info.name,
                sector=company_info.sector,
                size=company_info.size,
                current_challenges=strategic_context.current_challenges,
                strategic_objectives=strategic_context.strategic_objectives,
                root_problem=root_problem,
                nodes_hierarchy=nodes_hierarchy,
                leaf_nodes_text=leaf_nodes_text,
                rag_context=rag_context
            )
            
            # LLM structured output
            synthesis: SolutionPathsOutput = self.llm_synthesize.invoke(prompt)
            
            logger.info(f"[Issue Tree Synthesis] {len(synthesis.solution_paths)} solution paths gerados")
            logger.debug(f"[Issue Tree Synthesis] Reasoning: {synthesis.reasoning[:100]}...")
            
            return synthesis.solution_paths
        
        except ValidationError as e:
            logger.error(f"[Issue Tree Synthesis] Validacao Pydantic falhou: {e}")
            # Fallback: retornar leaf nodes como solution paths basicos
            return [f"Resolver: {n.text}" for n in leaf_nodes[:6]]
        
        except Exception as e:
            logger.error(f"[Issue Tree Synthesis] Falha na sintese LLM: {e}")
            # Fallback: retornar leaf nodes como solution paths basicos
            return [f"Resolver: {n.text}" for n in leaf_nodes[:6]]

