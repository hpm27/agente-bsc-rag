"""Schemas Pydantic para ClientProfile e componentes relacionados.

Este módulo define os schemas de dados usados para armazenar
informações de clientes e engajamentos de consultoria BSC no Mem0.
"""

from datetime import datetime, timezone
from typing import Any, List, Literal, Optional
import re
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============================================================================
# SCHEMAS BASE (sem dependências)
# ============================================================================


class SWOTAnalysis(BaseModel):
    """Análise SWOT estruturada.
    
    Armazena as 4 dimensões da análise SWOT: Forças, Fraquezas,
    Oportunidades e Ameaças identificadas durante o diagnóstico.
    
    Attributes:
        strengths: Lista de forças internas da organização
        weaknesses: Lista de fraquezas internas da organização
        opportunities: Lista de oportunidades externas
        threats: Lista de ameaças externas
    
    Example:
        >>> swot = SWOTAnalysis(
        ...     strengths=["Equipe qualificada", "Marca forte"],
        ...     weaknesses=["Processos manuais"],
        ...     opportunities=["Expansão digital"],
        ...     threats=["Concorrência intensa"]
        ... )
    """
    
    strengths: List[str] = Field(
        default_factory=list,
        description="Forças internas da organização"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Fraquezas internas da organização"
    )
    opportunities: List[str] = Field(
        default_factory=list,
        description="Oportunidades externas"
    )
    threats: List[str] = Field(
        default_factory=list,
        description="Ameaças externas"
    )
    
    def is_complete(self, min_items_per_quadrant: int = 2) -> bool:
        """Verifica se análise SWOT está completa.
        
        Args:
            min_items_per_quadrant: Mínimo de itens por quadrante (default: 2)
            
        Returns:
            True se todos os 4 quadrantes têm >= min_items_per_quadrant, False caso contrário
            
        Example:
            >>> swot = SWOTAnalysis(strengths=["A", "B"], weaknesses=["C"])
            >>> swot.is_complete(min_items_per_quadrant=2)
            False  # weaknesses tem apenas 1 item
        """
        return (
            len(self.strengths) >= min_items_per_quadrant
            and len(self.weaknesses) >= min_items_per_quadrant
            and len(self.opportunities) >= min_items_per_quadrant
            and len(self.threats) >= min_items_per_quadrant
        )
    
    def quality_score(self, target_items: int = 4) -> float:
        """Calcula score de qualidade da análise SWOT.
        
        Score varia de 0.0 (vazio) a 1.0 (perfeito) baseado na quantidade
        de itens em cada quadrante em relação ao target.
        
        Args:
            target_items: Número ideal de itens por quadrante (default: 4)
            
        Returns:
            Float entre 0.0 e 1.0 representando qualidade da análise
            
        Example:
            >>> swot = SWOTAnalysis(
            ...     strengths=["A", "B"], 
            ...     weaknesses=["C"],
            ...     opportunities=["D", "E", "F"],
            ...     threats=[]
            ... )
            >>> swot.quality_score(target_items=4)
            0.375  # (2 + 1 + 3 + 0) / 16 = 6/16
        """
        total_items = (
            len(self.strengths)
            + len(self.weaknesses)
            + len(self.opportunities)
            + len(self.threats)
        )
        max_possible = target_items * 4  # 4 quadrantes
        return min(total_items / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def summary(self) -> str:
        """Retorna resumo textual da análise SWOT.
        
        Formata os 4 quadrantes em texto legível para visualização rápida.
        
        Returns:
            String formatada com os 4 quadrantes
            
        Example:
            >>> swot = SWOTAnalysis(strengths=["A"], weaknesses=["B"])
            >>> print(swot.summary())
            Strengths (Forças): 1 items
            - A
            ...
        """
        lines = []
        
        lines.append(f"Strengths (Forças): {len(self.strengths)} items")
        for item in self.strengths:
            lines.append(f"- {item}")
        
        lines.append(f"\nWeaknesses (Fraquezas): {len(self.weaknesses)} items")
        for item in self.weaknesses:
            lines.append(f"- {item}")
        
        lines.append(f"\nOpportunities (Oportunidades): {len(self.opportunities)} items")
        for item in self.opportunities:
            lines.append(f"- {item}")
        
        lines.append(f"\nThreats (Ameaças): {len(self.threats)} items")
        for item in self.threats:
            lines.append(f"- {item}")
        
        return "\n".join(lines)
    
    def total_items(self) -> int:
        """Retorna total de itens em todos os quadrantes.
        
        Returns:
            Soma do número de itens em strengths + weaknesses + opportunities + threats
        """
        return (
            len(self.strengths)
            + len(self.weaknesses)
            + len(self.opportunities)
            + len(self.threats)
        )
    
    def quadrant_summary(self) -> dict[str, int]:
        """Retorna resumo de quantidades por quadrante.
        
        Returns:
            Dicionário com contagem de itens por quadrante
            
        Example:
            >>> swot.quadrant_summary()
            {'strengths': 2, 'weaknesses': 1, 'opportunities': 3, 'threats': 2}
        """
        return {
            "strengths": len(self.strengths),
            "weaknesses": len(self.weaknesses),
            "opportunities": len(self.opportunities),
            "threats": len(self.threats),
        }


class WhyIteration(BaseModel):
    """Uma iteracao individual do metodo 5 Whys.
    
    Representa uma pergunta "Por que?" e sua resposta correspondente
    durante a analise de causa raiz.
    
    Attributes:
        iteration_number: Numero da iteracao (1-7)
        question: Pergunta "Por que?" formulada
        answer: Resposta que leva a proxima iteracao
        confidence: Confianca de que esta resposta e relevante (0.0-1.0)
    
    Example:
        >>> iteration = WhyIteration(
        ...     iteration_number=1,
        ...     question="Por que as vendas estao baixas?",
        ...     answer="Porque temos poucos leads qualificados",
        ...     confidence=0.9
        ... )
    """
    
    iteration_number: int = Field(
        ge=1,
        le=7,
        description="Numero da iteracao (1-7)"
    )
    question: str = Field(
        min_length=10,
        max_length=500,
        description="Pergunta 'Por que?' formulada"
    )
    answer: str = Field(
        min_length=10,
        max_length=1000,
        description="Resposta que leva a proxima iteracao"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=0.5,
        description="Confianca de que esta resposta e relevante (0.0-1.0)"
    )


class FiveWhysAnalysis(BaseModel):
    """Analise 5 Whys (5 Porques) para identificacao de causa raiz.
    
    Metodo de analise de causa raiz desenvolvido por Taiichi Ohno (Toyota)
    que pergunta "Por que?" iterativamente (3-7 vezes) ate identificar
    a causa fundamental de um problema.
    
    Attributes:
        problem_statement: Problema inicial a ser analisado
        iterations: Lista de iteracoes "Por que?" (min 3, max 7)
        root_cause: Causa raiz fundamental identificada
        confidence_score: Confianca de que root cause foi atingida (0-100)
        recommended_actions: Acoes recomendadas para resolver causa raiz
        context_from_rag: Contexto BSC recuperado via RAG (opcional)
    
    Example:
        >>> analysis = FiveWhysAnalysis(
        ...     problem_statement="Vendas baixas no ultimo trimestre",
        ...     iterations=[
        ...         WhyIteration(1, "Por que vendas baixas?", "Poucos leads", 0.9),
        ...         WhyIteration(2, "Por que poucos leads?", "Marketing fraco", 0.85),
        ...         # ... mais iteracoes
        ...     ],
        ...     root_cause="Falta de orcamento para marketing digital",
        ...     confidence_score=85.0,
        ...     recommended_actions=["Realocar orcamento", "Contratar especialista"]
        ... )
    """
    
    problem_statement: str = Field(
        min_length=10,
        max_length=500,
        description="Problema inicial a ser analisado"
    )
    iterations: List[WhyIteration] = Field(
        min_length=3,
        max_length=7,
        description="Lista de iteracoes 'Por que?' (min 3, max 7)"
    )
    root_cause: str = Field(
        min_length=20,
        max_length=1000,
        description="Causa raiz fundamental identificada"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Confianca de que root cause foi atingida (0-100%)"
    )
    recommended_actions: List[str] = Field(
        min_length=2,
        description="Acoes recomendadas para resolver causa raiz"
    )
    context_from_rag: List[str] = Field(
        default_factory=list,
        description="Contexto BSC recuperado via RAG (opcional)"
    )
    
    @field_validator("iterations")
    @classmethod
    def validate_iterations_sequence(cls, iterations: List[WhyIteration]) -> List[WhyIteration]:
        """Valida que iteration_number esta em sequencia (1, 2, 3, ...)."""
        if not iterations:
            return iterations
        
        expected_numbers = list(range(1, len(iterations) + 1))
        actual_numbers = [it.iteration_number for it in iterations]
        
        if actual_numbers != expected_numbers:
            raise ValueError(
                f"Iteration numbers devem estar em sequencia (1, 2, 3, ...). "
                f"Esperado: {expected_numbers}, Recebido: {actual_numbers}"
            )
        
        return iterations
    
    @field_validator("recommended_actions")
    @classmethod
    def validate_actions_not_empty(cls, actions: List[str]) -> List[str]:
        """Valida que cada acao tem conteudo (nao vazia)."""
        if not actions or len(actions) < 2:
            raise ValueError("Deve haver pelo menos 2 recommended_actions")
        
        for i, action in enumerate(actions):
            if not action or len(action.strip()) < 10:
                raise ValueError(
                    f"Action {i+1} deve ter pelo menos 10 caracteres (recebeu: '{action}')"
                )
        
        return actions
    
    def is_complete(self) -> bool:
        """Verifica se analise 5 Whys esta completa.
        
        Returns:
            True se tem >= 3 iteracoes, root_cause preenchida, e >= 2 acoes recomendadas
        
        Example:
            >>> analysis = FiveWhysAnalysis(...)
            >>> analysis.is_complete()
            True
        """
        return (
            len(self.iterations) >= 3
            and len(self.root_cause) >= 20
            and len(self.recommended_actions) >= 2
        )
    
    def depth_reached(self) -> int:
        """Retorna numero de iteracoes realizadas.
        
        Returns:
            Quantidade de iteracoes "Por que?" realizadas (3-7)
        
        Example:
            >>> analysis.depth_reached()
            5  # Realizou 5 iteracoes
        """
        return len(self.iterations)
    
    def root_cause_confidence(self) -> float:
        """Retorna score de confianca da causa raiz (0-100%).
        
        Returns:
            Confidence score normalizado (0.0-100.0)
        
        Example:
            >>> analysis.root_cause_confidence()
            85.0  # 85% de confianca
        """
        return self.confidence_score
    
    def summary(self) -> str:
        """Retorna resumo textual da analise 5 Whys.
        
        Formata problema, iteracoes, causa raiz e acoes em texto legivel
        para visualizacao rapida.
        
        Returns:
            String formatada com resumo executivo da analise
        
        Example:
            >>> print(analysis.summary())
            Problema: Vendas baixas no ultimo trimestre
            
            Iteracoes (5):
            1. Por que vendas baixas? -> Poucos leads qualificados
            2. Por que poucos leads? -> Marketing digital fraco
            ...
            
            Causa Raiz: Falta de orcamento para marketing digital
            Confianca: 85.0%
            
            Acoes Recomendadas (3):
            1. Realocar orcamento para marketing
            2. Contratar especialista em marketing digital
            3. Implementar campanha de inbound marketing
        """
        lines = []
        
        lines.append(f"Problema: {self.problem_statement}")
        lines.append("")
        
        lines.append(f"Iteracoes ({len(self.iterations)}):")
        for iteration in self.iterations:
            lines.append(
                f"{iteration.iteration_number}. {iteration.question} -> {iteration.answer}"
            )
        lines.append("")
        
        lines.append(f"Causa Raiz: {self.root_cause}")
        lines.append(f"Confianca: {self.confidence_score}%")
        lines.append("")
        
        lines.append(f"Acoes Recomendadas ({len(self.recommended_actions)}):")
        for i, action in enumerate(self.recommended_actions, 1):
            lines.append(f"{i}. {action}")
        
        if self.context_from_rag:
            lines.append("")
            lines.append(f"Contexto BSC (RAG): {len(self.context_from_rag)} insights recuperados")
        
        return "\n".join(lines)
    
    def average_confidence(self) -> float:
        """Calcula confianca media das iteracoes.
        
        Returns:
            Media aritmetica das confidences de todas iteracoes (0.0-1.0)
        
        Example:
            >>> analysis.average_confidence()
            0.85  # 85% de confianca media
        """
        if not self.iterations:
            return 0.0
        
        total_confidence = sum(it.confidence for it in self.iterations)
        return total_confidence / len(self.iterations)


# ============================================================================
# ISSUE TREE SCHEMAS (Fase 3.3 - Issue Tree Analyzer)
# ============================================================================


class IssueNode(BaseModel):
    """No individual de uma arvore de problemas (Issue Tree).
    
    Representa um problema/sub-problema na decomposicao hierarquica MECE.
    Cada no pode ter children (sub-problemas) e um parent (problema pai).
    
    Attributes:
        id: Identificador unico do no (UUID gerado automaticamente)
        text: Descricao do problema/sub-problema
        level: Nivel na hierarquia (0=root, 1=branch, 2+=leaf)
        parent_id: ID do no pai (None se root)
        children_ids: Lista de IDs dos nos filhos
        is_leaf: True se no e folha (sem children), False se tem sub-problemas
        category: Categoria opcional (ex: "Financeira", "Clientes")
    
    Example:
        >>> root = IssueNode(
        ...     text="Baixa lucratividade",
        ...     level=0,
        ...     parent_id=None
        ... )
        >>> branch1 = IssueNode(
        ...     text="Receita baixa",
        ...     level=1,
        ...     parent_id=root.id,
        ...     category="Financeira"
        ... )
    """
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Identificador unico do no (UUID)"
    )
    text: str = Field(
        min_length=5,
        max_length=300,
        description="Descricao do problema/sub-problema"
    )
    level: int = Field(
        ge=0,
        le=5,
        description="Nivel na hierarquia (0=root, max 5 niveis profundidade)"
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="ID do no pai (None se root)"
    )
    children_ids: List[str] = Field(
        default_factory=list,
        description="Lista de IDs dos nos filhos"
    )
    is_leaf: bool = Field(
        default=False,
        description="True se no e folha (sem children)"
    )
    category: Optional[str] = Field(
        default=None,
        description="Categoria opcional BSC (Financeira, Clientes, Processos, Aprendizado)"
    )
    
    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, value: str) -> str:
        """Valida que texto nao e apenas espacos."""
        if not value.strip():
            raise ValueError("Texto do no nao pode ser vazio ou apenas espacos")
        return value.strip()


class IssueTreeAnalysis(BaseModel):
    """Analise completa de Issue Tree (arvore de problemas MECE).
    
    Estrutura hierarquica que decompoe um problema complexo em sub-problemas
    seguindo principio MECE (Mutually Exclusive, Collectively Exhaustive).
    Tecnica McKinsey/BCG para case interviews e diagnostico estrategico.
    
    Attributes:
        root_problem: Problema raiz (nivel 0)
        nodes: Lista de todos os nos da arvore (incluindo root)
        max_depth: Profundidade maxima atingida (min 1, max 5)
        is_mece_compliant: Validacao manual se arvore segue MECE
        total_nodes: Numero total de nos (calculado automaticamente)
        leaf_nodes_count: Numero de nos folha (solucoes finais)
        solution_paths: Caminhos solucao recomendados (sintese leaf nodes)
        context_from_rag: Contexto BSC recuperado via RAG (opcional)
    
    Example:
        >>> tree = IssueTreeAnalysis(
        ...     root_problem="Baixa lucratividade empresa manufatura",
        ...     nodes=[
        ...         IssueNode(text="Baixa lucratividade", level=0),
        ...         IssueNode(text="Receita baixa", level=1),
        ...         IssueNode(text="Custos altos", level=1),
        ...         # ... mais nos
        ...     ],
        ...     max_depth=3,
        ...     is_mece_compliant=True,
        ...     solution_paths=[
        ...         "Aumentar volume vendas via marketing digital",
        ...         "Reduzir custos fixos com automacao processos"
        ...     ]
        ... )
    """
    
    root_problem: str = Field(
        min_length=10,
        max_length=500,
        description="Problema raiz a ser decomposto"
    )
    nodes: List[IssueNode] = Field(
        min_length=1,
        description="Lista de todos os nos da arvore (incluindo root)"
    )
    max_depth: int = Field(
        ge=1,
        le=5,
        description="Profundidade maxima atingida na arvore"
    )
    is_mece_compliant: bool = Field(
        default=False,
        description="Validacao se arvore segue principio MECE"
    )
    solution_paths: List[str] = Field(
        default_factory=list,
        description="Caminhos solucao recomendados (sintese leaf nodes)"
    )
    context_from_rag: Optional[str] = Field(
        default=None,
        description="Contexto BSC recuperado via RAG (opcional)"
    )
    
    @model_validator(mode="after")
    def validate_tree_structure(self):
        """Valida estrutura basica da arvore.
        
        Verifica:
        - Root node existe (level=0)
        - Nodes tem IDs unicos
        - Max depth coerente com nodes
        
        Raises:
            ValueError: Se estrutura invalida
        """
        # Verificar root node existe
        root_nodes = [n for n in self.nodes if n.level == 0]
        if len(root_nodes) != 1:
            raise ValueError(f"Arvore deve ter exatamente 1 root node (level=0), encontrado {len(root_nodes)}")
        
        # Verificar IDs unicos
        node_ids = [n.id for n in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Todos os nodes devem ter IDs unicos")
        
        # Verificar max_depth coerente
        actual_max_depth = max(n.level for n in self.nodes) if self.nodes else 0
        if self.max_depth != actual_max_depth:
            raise ValueError(f"max_depth ({self.max_depth}) inconsistente com nodes (max level {actual_max_depth})")
        
        return self
    
    def is_complete(self, min_branches: int = 2) -> bool:
        """Verifica se arvore esta completa (minimo branches por nivel).
        
        Args:
            min_branches: Minimo de branches por nivel (default: 2 para MECE)
            
        Returns:
            True se todos niveis >= 1 tem >= min_branches, False caso contrario
            
        Example:
            >>> tree.is_complete(min_branches=2)
            True  # Todos niveis intermediarios tem >= 2 branches
        """
        # Agrupar nodes por nivel
        levels = {}
        for node in self.nodes:
            if node.level not in levels:
                levels[node.level] = []
            levels[node.level].append(node)
        
        # Verificar niveis intermediarios (excluir root=0 e leaf=max)
        for level in range(1, self.max_depth):
            if len(levels.get(level, [])) < min_branches:
                return False
        
        return True
    
    def validate_mece(self) -> dict:
        """Valida se arvore segue principio MECE (heuristica basica).
        
        MECE = Mutually Exclusive (sem overlap) + Collectively Exhaustive (cobre tudo)
        
        Returns:
            Dict com validacao: {"is_mece": bool, "issues": list[str], "confidence": float}
            
        Example:
            >>> tree.validate_mece()
            {"is_mece": True, "issues": [], "confidence": 0.85}
        """
        issues = []
        
        # Verificar se todos niveis >= 1 tem >= 2 branches (Collectively Exhaustive basico)
        if not self.is_complete(min_branches=2):
            issues.append("Alguns niveis tem < 2 branches (pode nao ser Collectively Exhaustive)")
        
        # Verificar se leaf nodes tem solucoes
        leaf_nodes = self.get_leaf_nodes()
        if not leaf_nodes:
            issues.append("Arvore nao tem leaf nodes (decomposicao incompleta)")
        
        if len(self.solution_paths) < len(leaf_nodes) // 2:
            issues.append(f"Poucas solution paths ({len(self.solution_paths)}) vs leaf nodes ({len(leaf_nodes)})")
        
        # Calcular confidence (heuristica: quanto menos issues, maior confidence)
        confidence = max(0.0, 1.0 - (len(issues) * 0.25))
        
        return {
            "is_mece": len(issues) == 0,
            "issues": issues,
            "confidence": confidence
        }
    
    def get_leaf_nodes(self) -> List[IssueNode]:
        """Retorna todos os nos folha (sem children).
        
        Returns:
            Lista de IssueNodes que sao folhas (is_leaf=True ou children_ids vazio)
            
        Example:
            >>> leaf_nodes = tree.get_leaf_nodes()
            >>> len(leaf_nodes)
            8  # 8 solucoes finais identificadas
        """
        return [n for n in self.nodes if n.is_leaf or len(n.children_ids) == 0]
    
    def total_nodes(self) -> int:
        """Retorna numero total de nos na arvore.
        
        Returns:
            Numero total de nodes (incluindo root)
            
        Example:
            >>> tree.total_nodes()
            15  # 1 root + 14 sub-problemas
        """
        return len(self.nodes)
    
    def summary(self) -> str:
        """Gera resumo executivo da analise Issue Tree.
        
        Returns:
            String com resumo formatado (1 paragrafo)
            
        Example:
            >>> print(tree.summary())
            Problema raiz: Baixa lucratividade
            Decomposicao: 15 nos, 3 niveis profundidade, 8 solucoes finais
            MECE: Compliant (confidence 85%)
            Caminhos solucao: 6 recomendacoes acionaveis
        """
        lines = [
            f"Problema raiz: {self.root_problem}",
            f"Decomposicao: {self.total_nodes()} nos, {self.max_depth} niveis profundidade, {len(self.get_leaf_nodes())} solucoes finais"
        ]
        
        mece_validation = self.validate_mece()
        mece_status = "Compliant" if mece_validation["is_mece"] else "Non-compliant"
        lines.append(f"MECE: {mece_status} (confidence {mece_validation['confidence']:.0%})")
        
        lines.append(f"Caminhos solucao: {len(self.solution_paths)} recomendacoes acionaveis")
        
        if self.context_from_rag:
            lines.append(f"Contexto BSC (RAG): {len(self.context_from_rag)} insights recuperados")
        
        return "\n".join(lines)


class CompanyInfo(BaseModel):
    """Informações básicas da empresa cliente.
    
    Contém dados fundamentais sobre a empresa que serão coletados
    durante o onboarding inicial.
    
    Attributes:
        name: Nome da empresa (obrigatório)
        sector: Setor de atuação (ex: Tecnologia, Manufatura, Serviços)
        size: Porte da empresa (micro, pequena, média, grande)
        industry: Indústria específica (opcional)
        founded_year: Ano de fundação (opcional, 1800-2025)
    
    Example:
        >>> company = CompanyInfo(
        ...     name="TechCorp Brasil",
        ...     sector="Tecnologia",
        ...     size="média",
        ...     industry="Software as a Service",
        ...     founded_year=2015
        ... )
    """
    
    name: str = Field(
        min_length=2,
        description="Nome da empresa"
    )
    sector: str = Field(
        description="Setor de atuação (ex: Tecnologia, Manufatura, Serviços)"
    )
    size: str = Field(
        default="média",
        description="Porte da empresa"
    )
    industry: Optional[str] = Field(
        None,
        description="Indústria específica (opcional)"
    )
    founded_year: Optional[int] = Field(
        None,
        ge=1800,
        le=2025,
        description="Ano de fundação"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que nome da empresa não é vazio após trim."""
        v = v.strip()
        if not v:
            raise ValueError("Nome da empresa não pode ser vazio")
        return v

    @field_validator('size')
    @classmethod
    def validate_size(cls, v: str) -> str:
        """Permite porte em categorias (micro/pequena/média/grande) OU faixa numérica (ex: '50-100').

        Aceita sinônimos comuns no Brasil e normaliza para valores canônicos:
        - "médio porte", "medio porte", "medio", "média empresa" -> "média"
        - "pequeno porte", "pequeno", "pequena empresa" -> "pequena"
        - "grande porte", "grande empresa" -> "grande"
        - "microempresa", "micro empresa" -> "micro"
        """
        if not isinstance(v, str):
            raise ValueError("Porte da empresa deve ser texto")
        raw = v.strip()
        value = raw.lower()

        # Normalização leve: remover palavra 'porte' e hifens/underscores, colapsar espaços
        simplified = re.sub(r"\bporte\b", "", value)
        simplified = simplified.replace("-", " ").replace("_", " ")
        simplified = re.sub(r"\s+", " ", simplified).strip()

        # Mapeamento de sinônimos comuns -> valores canônicos
        if any(tok in simplified for tok in ["medio", "médio", "media", "média"]):
            return "média"
        if any(tok in simplified for tok in ["pequeno", "pequena"]):
            return "pequena"
        if "micro" in simplified or "microempresa" in simplified or "micro empresa" in simplified:
            return "micro"
        if "grande" in simplified:
            return "grande"

        # Checagem direta de valores canônicos
        allowed = {"micro", "pequena", "média", "grande"}
        if value in allowed:
            return raw  # mantém acentuação/forma original fornecida

        # Aceita formato de faixa numérica de colaboradores (ex: '50-100')
        if re.match(r'^\d+\s*-\s*\d+$', raw):
            return raw

        raise ValueError("Porte inválido: use 'micro', 'pequena', 'média', 'grande' ou faixa '50-100'")


# ============================================================================
# SCHEMAS INTERMEDIÁRIOS (contexto estratégico e diagnóstico)
# ============================================================================


class StrategicContext(BaseModel):
    """Contexto estratégico organizacional.
    
    Armazena informações sobre missão, visão, valores e objetivos
    estratégicos da organização, coletadas durante ONBOARDING e DISCOVERY.
    
    Attributes:
        mission: Declaração de missão da empresa (opcional)
        vision: Declaração de visão da empresa (opcional)
        core_values: Lista de valores centrais da organização
        strategic_objectives: Lista de objetivos estratégicos atuais
        current_challenges: Lista de desafios estratégicos enfrentados
    
    Example:
        >>> context = StrategicContext(
        ...     mission="Transformar a indústria através da inovação",
        ...     vision="Ser líder global até 2030",
        ...     core_values=["Inovação", "Integridade", "Excelência"],
        ...     strategic_objectives=["Crescer 30% ao ano", "Expandir para novos mercados"],
        ...     current_challenges=["Alta rotatividade", "Processos ineficientes"]
        ... )
    """
    
    mission: Optional[str] = Field(
        None,
        description="Declaração de missão da empresa"
    )
    vision: Optional[str] = Field(
        None,
        description="Declaração de visão da empresa"
    )
    core_values: List[str] = Field(
        default_factory=list,
        description="Valores centrais da organização"
    )
    strategic_objectives: List[str] = Field(
        default_factory=list,
        description="Objetivos estratégicos atuais"
    )
    current_challenges: List[str] = Field(
        default_factory=list,
        description="Desafios estratégicos atuais"
    )


class DiagnosticData(BaseModel):
    """Dados coletados durante fase DISCOVERY.
    
    Armazena todas as descobertas do diagnóstico organizacional,
    incluindo análise SWOT, pain points e oportunidades identificadas.
    
    Attributes:
        swot: Análise SWOT completa (opcional até DISCOVERY)
        pain_points: Lista de pontos de dor identificados
        opportunities: Lista de oportunidades de melhoria
        key_findings: Lista de descobertas-chave do diagnóstico
    
    Example:
        >>> swot = SWOTAnalysis(
        ...     strengths=["Equipe forte"],
        ...     weaknesses=["Processos manuais"]
        ... )
        >>> diagnostic = DiagnosticData(
        ...     swot=swot,
        ...     pain_points=["Falta de visibilidade de métricas"],
        ...     opportunities=["Automação de processos"],
        ...     key_findings=["BSC pode reduzir tempo de reporting em 70%"]
        ... )
    """
    
    swot: Optional[SWOTAnalysis] = Field(
        None,
        description="Análise SWOT completa"
    )
    pain_points: List[str] = Field(
        default_factory=list,
        description="Pontos de dor identificados"
    )
    opportunities: List[str] = Field(
        default_factory=list,
        description="Oportunidades de melhoria"
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="Descobertas-chave do diagnóstico"
    )


# ============================================================================
# ENGAGEMENT STATE (estado do engajamento consultoria)
# ============================================================================


class EngagementState(BaseModel):
    """Estado e progresso do engajamento de consultoria.
    
    Rastreia a fase atual do engajamento, progresso, milestones completados
    e timestamps relevantes.
    
    Attributes:
        current_phase: Fase atual do workflow (ONBOARDING -> COMPLETED)
        started_at: Data/hora de início do engajamento
        last_interaction: Data/hora da última interação com o agente
        progress_percentage: Percentual de progresso (0-100%)
        completed_milestones: Lista de milestones já completados
    
    Example:
        >>> engagement = EngagementState(
        ...     current_phase="DISCOVERY",
        ...     progress_percentage=35,
        ...     completed_milestones=["Onboarding realizado", "SWOT completado"]
        ... )
        >>> # started_at e last_interaction são auto-gerados
    """
    
    current_phase: Literal[
        "ONBOARDING",
        "DISCOVERY",
        "DESIGN",
        "APPROVAL_PENDING",
        "IMPLEMENTATION",
        "COMPLETED"
    ] = Field(
        default="ONBOARDING",
        description="Fase atual do engajamento consultoria"
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de início do engajamento"
    )
    last_interaction: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora da última interação"
    )
    progress_percentage: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Percentual de progresso (0-100%)"
    )
    completed_milestones: List[str] = Field(
        default_factory=list,
        description="Milestones já completados"
    )


# ============================================================================
# CLIENT PROFILE (schema principal agregador)
# ============================================================================


class ClientProfile(BaseModel):
    # Permite atributos extras (necessário para patch de métodos em testes)
    model_config = ConfigDict(extra='allow')
    """Perfil completo do cliente para engajamento de consultoria BSC.
    
    Schema principal que agrega todas as informações necessárias para
    conduzir um engajamento de consultoria em Balanced Scorecard, desde
    onboarding até implementação. Otimizado para armazenamento no Mem0.
    
    Attributes:
        client_id: Identificador único do cliente (UUID auto-gerado)
        company: Informações básicas da empresa (obrigatório)
        context: Contexto estratégico (missão, visão, objetivos)
        engagement: Estado atual do engajamento consultoria
        diagnostics: Dados de diagnóstico (SWOT, pain points) - opcional até DISCOVERY
        metadata: Dados customizados adicionais (dict livre)
        created_at: Data/hora de criação do perfil
        updated_at: Data/hora da última atualização (auto-atualizado)
    
    Example:
        >>> # Criar novo perfil de cliente
        >>> company = CompanyInfo(
        ...     name="TechCorp Brasil",
        ...     sector="Tecnologia",
        ...     size="média"
        ... )
        >>> profile = ClientProfile(company=company)
        >>> 
        >>> # Acessar dados
        >>> profile.client_id
        'a3b5c7d9-e1f2-4a5b-8c9d-0e1f2a3b4c5d'
        >>> profile.engagement.current_phase
        'ONBOARDING'
        >>> 
        >>> # Serializar para Mem0
        >>> mem0_data = profile.to_mem0()
        >>> type(mem0_data)
        <class 'dict'>
        >>> 
        >>> # Deserializar de Mem0
        >>> restored = ClientProfile.from_mem0(mem0_data)
        >>> restored.company.name
        'TechCorp Brasil'
    """
    
    client_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Identificador único do cliente (UUID)"
    )
    company: CompanyInfo = Field(
        default_factory=lambda: CompanyInfo(name="Empresa Desconhecida", sector="Desconhecido"),
        description="Informações básicas da empresa"
    )
    context: StrategicContext = Field(
        default_factory=StrategicContext,
        description="Contexto estratégico organizacional"
    )
    engagement: EngagementState = Field(
        default_factory=EngagementState,
        description="Estado atual do engajamento"
    )
    diagnostics: Optional[DiagnosticData] = Field(
        None,
        description="Dados de diagnóstico (preenchido em DISCOVERY)"
    )
    complete_diagnostic: Optional[dict] = Field(
        default=None,
        description="Diagnóstico completo serializado (CompleteDiagnostic.model_dump())"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Dados customizados adicionais"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de criação do perfil"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora da última atualização"
    )
    
    @model_validator(mode='after')
    def update_timestamp(self) -> 'ClientProfile':
        """Atualiza timestamp de atualização automaticamente."""
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def to_mem0(self) -> dict:
        """Serializa ClientProfile para formato Mem0 (JSON/dict).
        
        Converte o schema Pydantic para um dicionário JSON-serializável,
        incluindo conversão automática de datetime para ISO 8601 string.
        
        Returns:
            dict: Dicionário pronto para armazenamento no Mem0
        
        Example:
            >>> profile = ClientProfile(company=CompanyInfo(name="Test", sector="Tech"))
            >>> mem0_data = profile.to_mem0()
            >>> isinstance(mem0_data, dict)
            True
            >>> 'client_id' in mem0_data
            True
        """
        return self.model_dump(mode='json', exclude_none=True)
    
    @classmethod
    def from_mem0(cls, data: dict) -> 'ClientProfile':
        """Deserializa ClientProfile de formato Mem0 (JSON/dict).
        
        Reconstrói o schema Pydantic a partir de um dicionário,
        incluindo validação automática de todos os campos.
        
        IMPORTANTE: Usa model_construct() ao invés de model_validate() para
        evitar que default_factory de created_at/updated_at sobrescreva valores
        fornecidos no dict. Nested schemas são deserializados manualmente.
        
        Args:
            data: Dicionário retornado do Mem0
        
        Returns:
            ClientProfile: Instância validada do schema
        
        Raises:
            ValidationError: Se os dados não passarem nas validações Pydantic
        
        Example:
            >>> mem0_data = {...}  # Dados do Mem0
            >>> profile = ClientProfile.from_mem0(mem0_data)
            >>> isinstance(profile, ClientProfile)
            True
        """
        # Deserializar nested schemas manualmente
        data_copy = data.copy()
        
        # CompanyInfo
        if 'company' in data_copy and isinstance(data_copy['company'], dict):
            data_copy['company'] = CompanyInfo(**data_copy['company'])
        
        # StrategicContext
        if 'context' in data_copy and isinstance(data_copy['context'], dict):
            data_copy['context'] = StrategicContext(**data_copy['context'])
        
        # EngagementState
        if 'engagement' in data_copy and isinstance(data_copy['engagement'], dict):
            data_copy['engagement'] = EngagementState(**data_copy['engagement'])
        
        # DiagnosticData (opcional)
        if 'diagnostics' in data_copy and isinstance(data_copy['diagnostics'], dict):
            data_copy['diagnostics'] = DiagnosticData(**data_copy['diagnostics'])
        
        # Usa model_construct para evitar default_factory sobrescrever valores
        return cls.model_construct(**data_copy)


# ============================================================================
# DIAGNOSTIC SCHEMAS (Fase 2.5 - DiagnosticAgent)
# ============================================================================


class DiagnosticResult(BaseModel):
    """Análise diagnóstica de uma perspectiva BSC individual.
    
    Resultado estruturado da análise de uma das 4 perspectivas do
    Balanced Scorecard (Financeira, Clientes, Processos Internos,
    Aprendizado e Crescimento) realizada pelo DiagnosticAgent.
    
    Attributes:
        perspective: Nome da perspectiva BSC analisada
        current_state: Descrição do estado atual da perspectiva (mínimo 20 caracteres)
        gaps: Lista de gaps identificados (mínimo 1 item)
        opportunities: Lista de oportunidades de melhoria (mínimo 1 item)
        priority: Nível de prioridade da perspectiva (HIGH, MEDIUM, LOW)
        key_insights: Lista de insights principais da análise (opcional)
    
    Example:
        >>> result = DiagnosticResult(
        ...     perspective="Financeira",
        ...     current_state="Receita crescente mas margens comprimidas por custos operacionais altos",
        ...     gaps=["Falta de visibilidade de custos por produto", "Orçamento anual desatualizado"],
        ...     opportunities=["Implementar ABC Costing", "Revisar pricing strategy"],
        ...     priority="HIGH",
        ...     key_insights=["Margens caíram 5pp em 12 meses", "Top 3 produtos geram 80% receita"]
        ... )
    """
    
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"] = Field(
        description="Perspectiva BSC analisada"
    )
    current_state: str = Field(
        min_length=20,
        description="Descrição do estado atual da perspectiva"
    )
    gaps: list[str] = Field(
        min_length=1,  # CORRIGIDO: min_items para listas (era min_length)
        description="Gaps identificados na perspectiva"
    )
    opportunities: list[str] = Field(
        min_length=1,  # CORRIGIDO: min_items para listas (era min_length)
        description="Oportunidades de melhoria identificadas"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Nível de prioridade da perspectiva"
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="Insights principais da análise"
    )
    
    @field_validator('gaps', 'opportunities')
    @classmethod
    def validate_non_empty_lists(cls, v: list[str], info) -> list[str]:
        """Valida que listas não são vazias."""
        if not v or len(v) == 0:
            raise ValueError(f"{info.field_name} não pode ser lista vazia")
        return v


class Recommendation(BaseModel):
    """Recomendação acionável do diagnóstico BSC.
    
    Recomendação estratégica priorizada por impacto vs esforço, com
    ações específicas e timeframe estimado para implementação.
    
    Attributes:
        title: Título conciso da recomendação (mínimo 10 caracteres)
        description: Descrição detalhada da recomendação (mínimo 50 caracteres)
        impact: Impacto esperado da recomendação (HIGH, MEDIUM, LOW)
        effort: Esforço necessário para implementação (HIGH, MEDIUM, LOW)
        priority: Prioridade final da recomendação (HIGH, MEDIUM, LOW)
        timeframe: Prazo estimado de implementação (ex: "3-6 meses", "Curto prazo")
        next_steps: Lista de próximas ações específicas (mínimo 1 item)
    
    Example:
        >>> rec = Recommendation(
        ...     title="Implementar Activity-Based Costing",
        ...     description="Substituir sistema atual de custos por ABC para aumentar visibilidade de rentabilidade por produto e cliente, permitindo decisões estratégicas baseadas em dados precisos de margem.",
        ...     impact="HIGH",
        ...     effort="MEDIUM",
        ...     priority="HIGH",
        ...     timeframe="6-9 meses",
        ...     next_steps=[
        ...         "Contratar consultor especializado em ABC",
        ...         "Mapear processos e atividades atuais (2 meses)",
        ...         "Pilotar em 1 linha de produto (3 meses)"
        ...     ]
        ... )
    """
    
    title: str = Field(
        min_length=10,
        description="Título conciso da recomendação"
    )
    description: str = Field(
        min_length=50,
        description="Descrição detalhada da recomendação"
    )
    impact: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Impacto esperado da recomendação"
    )
    effort: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Esforço necessário para implementação"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Prioridade final (calculada por impacto vs esforço)"
    )
    timeframe: str = Field(
        description="Prazo estimado de implementação"
    )
    next_steps: list[str] = Field(
        min_length=1,
        description="Próximas ações específicas"
    )
    
    @field_validator('next_steps')
    @classmethod
    def validate_next_steps_non_empty(cls, v: list[str]) -> list[str]:
        """Valida que next_steps não é lista vazia."""
        if not v or len(v) == 0:
            raise ValueError("next_steps não pode ser lista vazia")
        return v
    
    @model_validator(mode='after')
    def validate_priority_logic(self) -> 'Recommendation':
        """Valida lógica de priorização: HIGH impact + LOW effort = HIGH priority.
        
        Ajusta priority automaticamente se:
        - HIGH impact + LOW effort -> priority = HIGH (quick win)
        - LOW impact + HIGH effort -> priority = LOW (evitar)
        """
        if self.impact == "HIGH" and self.effort == "LOW":
            if self.priority != "HIGH":
                self.priority = "HIGH"
        elif self.impact == "LOW" and self.effort == "HIGH":
            if self.priority != "LOW":
                self.priority = "LOW"
        return self


class RecommendationsList(BaseModel):
    """Lista de recomendações retornadas pelo LLM.
    
    Schema wrapper para structured output do LLM ao gerar recomendações.
    Garante que LLM retorna lista válida com todos os campos obrigatórios
    de Recommendation (incluindo 'impact') via function calling.
    
    Attributes:
        recommendations: Lista de recomendações acionáveis (mínimo 3, máximo 10)
    
    Example:
        >>> recs_list = RecommendationsList(
        ...     recommendations=[
        ...         Recommendation(
        ...             title="Implementar ABC Costing",
        ...             description="...",
        ...             impact="HIGH",
        ...             effort="MEDIUM",
        ...             priority="HIGH",
        ...             timeframe="6-9 meses",
        ...             next_steps=[...]
        ...         ),
        ...         # ... outras recomendações
        ...     ]
        ... )
    """
    
    recommendations: list[Recommendation] = Field(
        min_length=3,
        max_length=10,
        description="Lista de recomendações acionáveis priorizadas por impacto vs esforço"
    )


class ConsolidatedAnalysis(BaseModel):
    """Consolidação cross-perspective das análises diagnósticas.
    
    Schema intermediário usado pelo LLM para consolidar as 4 perspectivas BSC
    identificando synergies, gaps sistêmicos e resumo executivo.
    
    Attributes:
        cross_perspective_synergies: Lista de synergies identificadas entre perspectivas
        executive_summary: Resumo executivo da análise (mínimo 200 caracteres)
        next_phase: Próxima fase do workflow (sempre APPROVAL_PENDING)
    
    Example:
        >>> analysis = ConsolidatedAnalysis(
        ...     cross_perspective_synergies=[
        ...         "Baixa retenção clientes impacta receita financeira",
        ...         "Processos manuais aumentam custo operacional"
        ...     ],
        ...     executive_summary="A ENGELAR apresenta...",
        ...     next_phase="APPROVAL_PENDING"
        ... )
    """
    
    cross_perspective_synergies: list[str] = Field(
        min_length=2,
        max_length=8,
        description="Synergies cross-perspective identificadas (2-8 itens, cada um com 50-150 caracteres)"
    )
    executive_summary: str = Field(
        min_length=200,
        max_length=10000,
        description="Resumo executivo da análise diagnóstica (200-2000 caracteres)"
    )
    next_phase: Literal["APPROVAL_PENDING"] = Field(
        default="APPROVAL_PENDING",
        description="Próxima fase do workflow (sempre APPROVAL_PENDING após consolidação)"
    )
    
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class CompleteDiagnostic(BaseModel):
    """Diagnóstico BSC completo multi-perspectiva.
    
    Consolida análise diagnóstica completa das 4 perspectivas do Balanced
    Scorecard, incluindo recomendações priorizadas, synergies cross-perspective
    identificadas e executive summary para tomada de decisão.
    
    Este schema é o resultado final do DiagnosticAgent.run_diagnostic() e
    contém todos os insights necessários para a fase APPROVAL_PENDING.
    
    Attributes:
        financial: Análise da perspectiva Financeira
        customer: Análise da perspectiva Clientes
        process: Análise da perspectiva Processos Internos
        learning: Análise da perspectiva Aprendizado e Crescimento
        recommendations: Lista de 3+ recomendações priorizadas por impacto vs esforço
        cross_perspective_synergies: Lista de synergies cross-perspective identificadas (opcional)
        executive_summary: Resumo executivo completo do diagnóstico (mínimo 100 caracteres)
        next_phase: Próxima fase do workflow (geralmente APPROVAL_PENDING)
    
    Example:
        >>> financial = DiagnosticResult(
        ...     perspective="Financeira",
        ...     current_state="Receita crescente mas margens comprimidas",
        ...     gaps=["Falta visibilidade custos"],
        ...     opportunities=["Implementar ABC Costing"],
        ...     priority="HIGH"
        ... )
        >>> customer = DiagnosticResult(
        ...     perspective="Clientes",
        ...     current_state="NPS bom mas churn alto em clientes SMB",
        ...     gaps=["Falta programa retenção"],
        ...     opportunities=["Customer Success para SMB"],
        ...     priority="HIGH"
        ... )
        >>> process = DiagnosticResult(
        ...     perspective="Processos Internos",
        ...     current_state="Processos manuais geram retrabalho",
        ...     gaps=["Falta automação"],
        ...     opportunities=["RPA para processos repetitivos"],
        ...     priority="MEDIUM"
        ... )
        >>> learning = DiagnosticResult(
        ...     perspective="Aprendizado e Crescimento",
        ...     current_state="Turnover alto time comercial 25%/ano",
        ...     gaps=["Falta treinamento estruturado"],
        ...     opportunities=["Academia comercial interna"],
        ...     priority="MEDIUM"
        ... )
        >>> rec1 = Recommendation(
        ...     title="Implementar ABC Costing",
        ...     description="Sistema custeio baseado em atividades para melhorar visibilidade rentabilidade por produto",
        ...     impact="HIGH",
        ...     effort="MEDIUM",
        ...     priority="HIGH",
        ...     timeframe="6-9 meses",
        ...     next_steps=["Contratar consultor", "Mapear processos"]
        ... )
        >>> complete = CompleteDiagnostic(
        ...     financial=financial,
        ...     customer=customer,
        ...     process=process,
        ...     learning=learning,
        ...     recommendations=[rec1],
        ...     cross_perspective_synergies=["ABC Costing melhora pricing (Financial) e reduz churn SMB (Customer)"],
        ...     executive_summary="Empresa com crescimento forte mas margens comprimidas. Prioridades: (1) Implementar ABC Costing para visibilidade custos, (2) Customer Success SMB para reduzir churn 25->15%, (3) RPA para ganhar eficiência operacional. ROI esperado: +5pp margem em 12 meses.",
        ...     next_phase="APPROVAL_PENDING"
        ... )
    """
    
    financial: DiagnosticResult = Field(
        description="Análise da perspectiva Financeira"
    )
    customer: DiagnosticResult = Field(
        description="Análise da perspectiva Clientes"
    )
    process: DiagnosticResult = Field(
        description="Análise da perspectiva Processos Internos"
    )
    learning: DiagnosticResult = Field(
        description="Análise da perspectiva Aprendizado e Crescimento"
    )
    recommendations: list[Recommendation] = Field(
        min_length=3,
        description="Mínimo 3 recomendações priorizadas"
    )
    cross_perspective_synergies: list[str] = Field(
        default_factory=list,
        description="Synergies cross-perspective identificadas"
    )
    executive_summary: str = Field(
        min_length=100,
        description="Resumo executivo completo do diagnóstico"
    )
    next_phase: str = Field(
        default="APPROVAL_PENDING",
        description="Próxima fase do workflow consultivo"
    )
    
    @model_validator(mode='after')
    def validate_perspectives(self) -> 'CompleteDiagnostic':
        """Valida que as 4 perspectivas BSC estão corretas.
        
        Garante que cada campo (financial, customer, process, learning) contém
        a análise da perspectiva correta.
        
        Raises:
            ValueError: Se perspectivas não correspondem aos campos
        """
        if self.financial.perspective != "Financeira":
            raise ValueError(
                f"Campo 'financial' deve conter perspectiva 'Financeira', "
                f"recebeu '{self.financial.perspective}'"
            )
        if self.customer.perspective != "Clientes":
            raise ValueError(
                f"Campo 'customer' deve conter perspectiva 'Clientes', "
                f"recebeu '{self.customer.perspective}'"
            )
        if self.process.perspective != "Processos Internos":
            raise ValueError(
                f"Campo 'process' deve conter perspectiva 'Processos Internos', "
                f"recebeu '{self.process.perspective}'"
            )
        if self.learning.perspective != "Aprendizado e Crescimento":
            raise ValueError(
                f"Campo 'learning' deve conter perspectiva 'Aprendizado e Crescimento', "
                f"recebeu '{self.learning.perspective}'"
            )
        
        return self


# ============================================================================
# KPI FRAMEWORK SCHEMAS (FASE 3.4 - 2025-10-19)
# ============================================================================


class KPIDefinition(BaseModel):
    """Definicao de um KPI individual para BSC.
    
    Representa um Key Performance Indicator (KPI) especifico seguindo criterios
    SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
    
    Attributes:
        name: Nome do KPI (10-100 caracteres)
        description: Descricao detalhada do que o KPI mede (minimo 50 chars)
        perspective: Perspectiva BSC (Financeira, Clientes, Processos Internos, Aprendizado e Crescimento)
        metric_type: Tipo da metrica (quantidade, qualidade, tempo, custo)
        target_value: Valor alvo desejado (opcional, ex: "95%", ">10%", "< R$ 50k")
        measurement_frequency: Frequencia de medicao (diario, semanal, mensal, trimestral, anual)
        data_source: Origem dos dados para o KPI (ex: "ERP", "CRM", "Pesquisa NPS")
        calculation_formula: Formula de calculo (opcional, ex: "(Receita - Custos) / Receita * 100")
    
    Example:
        >>> kpi = KPIDefinition(
        ...     name="Net Promoter Score (NPS)",
        ...     description="Mede a lealdade dos clientes atraves da probabilidade de recomendacao",
        ...     perspective="Clientes",
        ...     metric_type="qualidade",
        ...     target_value="> 50",
        ...     measurement_frequency="trimestral",
        ...     data_source="Pesquisa NPS automatica pos-venda",
        ...     calculation_formula="% Promotores - % Detratores"
        ... )
    """
    
    name: str = Field(
        min_length=10,
        max_length=100,
        description="Nome do KPI (10-100 caracteres)"
    )
    description: str = Field(
        min_length=50,
        description="Descricao detalhada do que o KPI mede"
    )
    perspective: Literal[
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento"
    ] = Field(
        description="Perspectiva BSC do KPI"
    )
    metric_type: Literal[
        "quantidade",
        "qualidade",
        "tempo",
        "custo"
    ] = Field(
        description="Tipo da metrica"
    )
    target_value: Optional[str] = Field(
        default=None,
        description="Valor alvo desejado (ex: '95%', '>10%')"
    )
    measurement_frequency: Literal[
        "diario",
        "semanal",
        "mensal",
        "trimestral",
        "anual"
    ] = Field(
        description="Frequencia de medicao do KPI"
    )
    data_source: str = Field(
        min_length=5,
        description="Origem dos dados para o KPI"
    )
    calculation_formula: Optional[str] = Field(
        default=None,
        description="Formula de calculo do KPI (opcional)"
    )
    
    @field_validator('name')
    def validate_name_not_empty(cls, v: str) -> str:
        """Valida que nome nao e apenas espacos."""
        if not v.strip():
            raise ValueError("Nome do KPI nao pode ser vazio")
        return v.strip()
    
    @field_validator('description')
    def validate_description_not_empty(cls, v: str) -> str:
        """Valida que descricao nao e apenas espacos."""
        if not v.strip():
            raise ValueError("Descricao do KPI nao pode ser vazia")
        return v.strip()


class KPIFramework(BaseModel):
    """Framework completo de KPIs BSC para 4 perspectivas.
    
    Consolida todos os KPIs definidos para as 4 perspectivas do Balanced Scorecard
    em uma estrutura balanceada e completa.
    
    Attributes:
        financial_kpis: KPIs da perspectiva Financeira (2-8 items)
        customer_kpis: KPIs da perspectiva Clientes (2-8 items)
        process_kpis: KPIs da perspectiva Processos Internos (2-8 items)
        learning_kpis: KPIs da perspectiva Aprendizado e Crescimento (2-8 items)
    
    Example:
        >>> framework = KPIFramework(
        ...     financial_kpis=[
        ...         KPIDefinition(name="ROI", ...),
        ...         KPIDefinition(name="Margem Bruta", ...)
        ...     ],
        ...     customer_kpis=[
        ...         KPIDefinition(name="NPS", ...),
        ...         KPIDefinition(name="Churn Rate", ...)
        ...     ],
        ...     process_kpis=[...],
        ...     learning_kpis=[...]
        ... )
        >>> print(framework.total_kpis())  # 8 (2+2+2+2)
    """
    
    financial_kpis: list[KPIDefinition] = Field(
        min_length=2,
        max_length=8,
        description="KPIs da perspectiva Financeira (2-8 items)"
    )
    customer_kpis: list[KPIDefinition] = Field(
        min_length=2,
        max_length=8,
        description="KPIs da perspectiva Clientes (2-8 items)"
    )
    process_kpis: list[KPIDefinition] = Field(
        min_length=2,
        max_length=8,
        description="KPIs da perspectiva Processos Internos (2-8 items)"
    )
    learning_kpis: list[KPIDefinition] = Field(
        min_length=2,
        max_length=8,
        description="KPIs da perspectiva Aprendizado e Crescimento (2-8 items)"
    )
    
    @model_validator(mode='after')
    def validate_perspectives(self) -> 'KPIFramework':
        """Valida que KPIs estao nas perspectivas corretas.
        
        Garante que cada lista de KPIs contem apenas KPIs da perspectiva correspondente.
        
        Raises:
            ValueError: Se KPIs estao em perspectivas incorretas
        """
        # Validar financial_kpis
        for kpi in self.financial_kpis:
            if kpi.perspective != "Financeira":
                raise ValueError(
                    f"financial_kpis deve conter apenas KPIs da perspectiva 'Financeira', "
                    f"encontrado '{kpi.perspective}' em KPI '{kpi.name}'"
                )
        
        # Validar customer_kpis
        for kpi in self.customer_kpis:
            if kpi.perspective != "Clientes":
                raise ValueError(
                    f"customer_kpis deve conter apenas KPIs da perspectiva 'Clientes', "
                    f"encontrado '{kpi.perspective}' em KPI '{kpi.name}'"
                )
        
        # Validar process_kpis
        for kpi in self.process_kpis:
            if kpi.perspective != "Processos Internos":
                raise ValueError(
                    f"process_kpis deve conter apenas KPIs da perspectiva 'Processos Internos', "
                    f"encontrado '{kpi.perspective}' em KPI '{kpi.name}'"
                )
        
        # Validar learning_kpis
        for kpi in self.learning_kpis:
            if kpi.perspective != "Aprendizado e Crescimento":
                raise ValueError(
                    f"learning_kpis deve conter apenas KPIs da perspectiva 'Aprendizado e Crescimento', "
                    f"encontrado '{kpi.perspective}' em KPI '{kpi.name}'"
                )
        
        return self
    
    def total_kpis(self) -> int:
        """Retorna numero total de KPIs no framework.
        
        Returns:
            int: Soma de KPIs de todas as 4 perspectivas
        
        Example:
            >>> framework = KPIFramework(...)
            >>> framework.total_kpis()
            16  # 4 + 3 + 5 + 4
        """
        return (
            len(self.financial_kpis) +
            len(self.customer_kpis) +
            len(self.process_kpis) +
            len(self.learning_kpis)
        )
    
    def by_perspective(self, perspective: str) -> list[KPIDefinition]:
        """Retorna KPIs de uma perspectiva especifica.
        
        Args:
            perspective: Nome da perspectiva BSC
        
        Returns:
            list[KPIDefinition]: Lista de KPIs da perspectiva solicitada
        
        Raises:
            ValueError: Se perspectiva invalida
        
        Example:
            >>> framework = KPIFramework(...)
            >>> financial = framework.by_perspective("Financeira")
            >>> print(len(financial))  # 4
        """
        perspective_map = {
            "Financeira": self.financial_kpis,
            "Clientes": self.customer_kpis,
            "Processos Internos": self.process_kpis,
            "Aprendizado e Crescimento": self.learning_kpis
        }
        
        if perspective not in perspective_map:
            raise ValueError(
                f"Perspectiva '{perspective}' invalida. "
                f"Opcoes: {list(perspective_map.keys())}"
            )
        
        return perspective_map[perspective]
    
    def summary(self) -> str:
        """Retorna resumo textual do framework com contagem de KPIs por perspectiva.
        
        Returns:
            str: Resumo formatado multi-linha
        
        Example:
            >>> framework = KPIFramework(...)
            >>> print(framework.summary())
            Framework BSC com 16 KPIs distribuidos:
            - Financeira: 4 KPIs
            - Clientes: 3 KPIs
            - Processos Internos: 5 KPIs
            - Aprendizado e Crescimento: 4 KPIs
        """
        lines = []
        total = self.total_kpis()
        lines.append(f"Framework BSC com {total} KPIs distribuidos:")
        lines.append(f"- Financeira: {len(self.financial_kpis)} KPIs")
        lines.append(f"- Clientes: {len(self.customer_kpis)} KPIs")
        lines.append(f"- Processos Internos: {len(self.process_kpis)} KPIs")
        lines.append(f"- Aprendizado e Crescimento: {len(self.learning_kpis)} KPIs")
        return "\n".join(lines)


# ============================================================================
# STRATEGIC OBJECTIVES SCHEMAS (Fase 3.5 - Sessao 20)
# ============================================================================


class StrategicObjective(BaseModel):
    """Objetivo estrategico SMART para uma perspectiva BSC.
    
    Define um objetivo estrategico de longo prazo alinhado com uma das 4 perspectivas
    do Balanced Scorecard. Objetivos estrategicos fornecem direcao (onde queremos chegar)
    enquanto KPIs fornecem medicao (como saberemos que chegamos).
    
    Attributes:
        name: Nome conciso do objetivo (ex: "Aumentar rentabilidade sustentavel")
        description: Detalhamento completo SMART do objetivo
        perspective: Perspectiva BSC a qual o objetivo pertence
        timeframe: Prazo para alcance do objetivo (ex: "12 meses", "Q1 2026")
        success_criteria: Lista de criterios mensu

raveis que indicam sucesso
        related_kpis: Lista de nomes de KPIs que medem progresso deste objetivo
        priority: Prioridade do objetivo (Alta, Media, Baixa)
        dependencies: Lista de nomes de objetivos prerequisitos (opcional)
    
    Validacoes:
        - name e description nao podem ser vazios (field_validator)
        - perspective deve ser uma das 4 perspectivas BSC (Literal)
        - success_criteria deve ter pelo menos 2 criterios com min_length=20
        - priority deve ser Alta, Media ou Baixa (Literal)
    
    Example:
        >>> objetivo = StrategicObjective(
        ...     name="Aumentar rentabilidade sustentavel",
        ...     description="Aumentar margem EBITDA de 15% para 20% em 12 meses atraves de otimizacao de custos e crescimento de receita",
        ...     perspective="Financeira",
        ...     timeframe="12 meses",
        ...     success_criteria=[
        ...         "Margem EBITDA >= 20%",
        ...         "Crescimento receita >= 15% YoY"
        ...     ],
        ...     related_kpis=["Margem EBITDA", "Crescimento Receita"],
        ...     priority="Alta"
        ... )
    """
    
    name: str = Field(
        min_length=10,
        description="Nome conciso do objetivo estrategico"
    )
    description: str = Field(
        min_length=50,
        description="Detalhamento completo SMART do objetivo"
    )
    perspective: Literal[
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento"
    ] = Field(
        description="Perspectiva BSC do objetivo"
    )
    timeframe: str = Field(
        min_length=5,
        description="Prazo para alcance do objetivo (ex: 12 meses, Q1 2026)"
    )
    success_criteria: List[str] = Field(
        min_length=2,
        description="Lista de criterios mensuraveis de sucesso (minimo 2)"
    )
    related_kpis: List[str] = Field(
        default_factory=list,
        description="Lista de nomes de KPIs que medem progresso (opcional)"
    )
    priority: Literal["Alta", "Media", "Baixa"] = Field(
        default="Media",
        description="Prioridade do objetivo"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Lista de nomes de objetivos prerequisitos (opcional)"
    )
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Valida que name nao esta vazio apos strip."""
        if not v or not v.strip():
            raise ValueError("name nao pode ser vazio")
        return v
    
    @field_validator("description")
    @classmethod
    def validate_description_not_empty(cls, v: str) -> str:
        """Valida que description nao esta vazio apos strip."""
        if not v or not v.strip():
            raise ValueError("description nao pode ser vazio")
        return v
    
    @field_validator("success_criteria")
    @classmethod
    def validate_success_criteria_quality(cls, v: List[str]) -> List[str]:
        """Valida que cada criterio tem comprimento minimo e nao esta vazio."""
        if len(v) < 2:
            raise ValueError("success_criteria deve ter pelo menos 2 criterios")
        
        for i, criterion in enumerate(v):
            if not criterion or not criterion.strip():
                raise ValueError(f"success_criteria[{i}] nao pode ser vazio")
            if len(criterion.strip()) < 20:
                raise ValueError(
                    f"success_criteria[{i}] muito curto (minimo 20 caracteres, "
                    f"recebido {len(criterion.strip())})"
                )
        
        return v


class StrategicObjectivesFramework(BaseModel):
    """Framework completo de objetivos estrategicos BSC.
    
    Agrupa objetivos estrategicos das 4 perspectivas BSC em um unico
    framework estruturado. Prove metodos uteis para analise e filtragem.
    
    Attributes:
        financial_objectives: Objetivos da perspectiva Financeira
        customer_objectives: Objetivos da perspectiva Clientes
        process_objectives: Objetivos da perspectiva Processos Internos
        learning_objectives: Objetivos da perspectiva Aprendizado e Crescimento
        company_context: Contexto opcional da empresa (ex: resumo diagnostico)
    
    Metodos Uteis:
        - total_objectives() -> int: Total de objetivos em todas perspectivas
        - by_perspective(perspective) -> List[StrategicObjective]: Filtra por perspectiva
        - by_priority(priority) -> List[StrategicObjective]: Filtra por prioridade
        - with_related_kpis() -> List[StrategicObjective]: Apenas objetivos com KPIs vinculados
        - summary() -> str: Resumo textual distribuicao objetivos
    
    Validacoes:
        - model_validator verifica que cada lista contem APENAS objetivos da perspectiva correta
        - Similar a KPIFramework validator (validado Sessao 19)
    
    Example:
        >>> framework = StrategicObjectivesFramework(
        ...     financial_objectives=[obj1_financeira, obj2_financeira],
        ...     customer_objectives=[obj1_clientes],
        ...     process_objectives=[obj1_processos, obj2_processos],
        ...     learning_objectives=[obj1_aprendizado]
        ... )
        >>> print(framework.total_objectives())  # 6
        >>> high_priority = framework.by_priority("Alta")  # 3 objetivos
    """
    
    financial_objectives: List[StrategicObjective] = Field(
        default_factory=list,
        description="Objetivos da perspectiva Financeira"
    )
    customer_objectives: List[StrategicObjective] = Field(
        default_factory=list,
        description="Objetivos da perspectiva Clientes"
    )
    process_objectives: List[StrategicObjective] = Field(
        default_factory=list,
        description="Objetivos da perspectiva Processos Internos"
    )
    learning_objectives: List[StrategicObjective] = Field(
        default_factory=list,
        description="Objetivos da perspectiva Aprendizado e Crescimento"
    )
    company_context: Optional[str] = Field(
        default=None,
        description="Contexto opcional da empresa (ex: resumo diagnostico)"
    )
    
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    @model_validator(mode="after")
    def validate_cross_perspective_consistency(self):
        """Valida que cada lista contem APENAS objetivos da perspectiva correta.
        
        Previne bugs silenciosos onde objetivo da perspectiva errada e adicionado
        a lista incorreta (ex: objetivo Financeira em customer_objectives).
        
        Raises:
            ValueError: Se encontrar objetivo com perspectiva inconsistente
        """
        # Validar financial_objectives
        for obj in self.financial_objectives:
            if obj.perspective != "Financeira":
                raise ValueError(
                    f"financial_objectives deve conter apenas objetivos da perspectiva 'Financeira', "
                    f"encontrado '{obj.perspective}' em objetivo '{obj.name}'"
                )
        
        # Validar customer_objectives
        for obj in self.customer_objectives:
            if obj.perspective != "Clientes":
                raise ValueError(
                    f"customer_objectives deve conter apenas objetivos da perspectiva 'Clientes', "
                    f"encontrado '{obj.perspective}' em objetivo '{obj.name}'"
                )
        
        # Validar process_objectives
        for obj in self.process_objectives:
            if obj.perspective != "Processos Internos":
                raise ValueError(
                    f"process_objectives deve conter apenas objetivos da perspectiva 'Processos Internos', "
                    f"encontrado '{obj.perspective}' em objetivo '{obj.name}'"
                )
        
        # Validar learning_objectives
        for obj in self.learning_objectives:
            if obj.perspective != "Aprendizado e Crescimento":
                raise ValueError(
                    f"learning_objectives deve conter apenas objetivos da perspectiva 'Aprendizado e Crescimento', "
                    f"encontrado '{obj.perspective}' em objetivo '{obj.name}'"
                )
        
        return self
    
    def total_objectives(self) -> int:
        """Retorna numero total de objetivos no framework.
        
        Returns:
            int: Soma de objetivos de todas as 4 perspectivas
        
        Example:
            >>> framework = StrategicObjectivesFramework(...)
            >>> framework.total_objectives()
            12  # 3 + 2 + 4 + 3
        """
        return (
            len(self.financial_objectives) +
            len(self.customer_objectives) +
            len(self.process_objectives) +
            len(self.learning_objectives)
        )
    
    def by_perspective(self, perspective: str) -> List[StrategicObjective]:
        """Retorna objetivos de uma perspectiva especifica.
        
        Args:
            perspective: Nome da perspectiva BSC
        
        Returns:
            List[StrategicObjective]: Lista de objetivos da perspectiva solicitada
        
        Raises:
            ValueError: Se perspectiva invalida
        
        Example:
            >>> framework = StrategicObjectivesFramework(...)
            >>> financial = framework.by_perspective("Financeira")
            >>> print(len(financial))  # 3
        """
        perspective_map = {
            "Financeira": self.financial_objectives,
            "Clientes": self.customer_objectives,
            "Processos Internos": self.process_objectives,
            "Aprendizado e Crescimento": self.learning_objectives
        }
        
        if perspective not in perspective_map:
            raise ValueError(
                f"Perspectiva '{perspective}' invalida. "
                f"Opcoes: {list(perspective_map.keys())}"
            )
        
        return perspective_map[perspective]
    
    def by_priority(self, priority: str) -> List[StrategicObjective]:
        """Retorna objetivos de uma prioridade especifica em todas perspectivas.
        
        Args:
            priority: Prioridade (Alta, Media, Baixa)
        
        Returns:
            List[StrategicObjective]: Lista de objetivos com prioridade solicitada
        
        Raises:
            ValueError: Se prioridade invalida
        
        Example:
            >>> framework = StrategicObjectivesFramework(...)
            >>> high_priority = framework.by_priority("Alta")
            >>> print(len(high_priority))  # 5
        """
        valid_priorities = ["Alta", "Media", "Baixa"]
        if priority not in valid_priorities:
            raise ValueError(
                f"Prioridade '{priority}' invalida. "
                f"Opcoes: {valid_priorities}"
            )
        
        all_objectives = (
            self.financial_objectives +
            self.customer_objectives +
            self.process_objectives +
            self.learning_objectives
        )
        
        return [obj for obj in all_objectives if obj.priority == priority]
    
    def with_related_kpis(self) -> List[StrategicObjective]:
        """Retorna apenas objetivos que possuem KPIs vinculados (related_kpis nao vazio).
        
        Util para verificar alinhamento estrategico entre objetivos e KPIs.
        
        Returns:
            List[StrategicObjective]: Lista de objetivos com pelo menos 1 KPI vinculado
        
        Example:
            >>> framework = StrategicObjectivesFramework(...)
            >>> with_kpis = framework.with_related_kpis()
            >>> print(len(with_kpis))  # 8 de 12 objetivos tem KPIs
        """
        all_objectives = (
            self.financial_objectives +
            self.customer_objectives +
            self.process_objectives +
            self.learning_objectives
        )
        
        return [obj for obj in all_objectives if obj.related_kpis]
    
    def summary(self) -> str:
        """Retorna resumo textual do framework com contagem por perspectiva e prioridade.
        
        Returns:
            str: Resumo formatado multi-linha
        
        Example:
            >>> framework = StrategicObjectivesFramework(...)
            >>> print(framework.summary())
            Framework BSC com 12 objetivos estrategicos distribuidos:
            
            Por Perspectiva:
            - Financeira: 3 objetivos
            - Clientes: 2 objetivos
            - Processos Internos: 4 objetivos
            - Aprendizado e Crescimento: 3 objetivos
            
            Por Prioridade:
            - Alta: 5 objetivos
            - Media: 4 objetivos
            - Baixa: 3 objetivos
            
            Objetivos com KPIs vinculados: 8 de 12 (67%)
        """
        lines = []
        total = self.total_objectives()
        lines.append(f"Framework BSC com {total} objetivos estrategicos distribuidos:")
        lines.append("")
        
        # Por perspectiva
        lines.append("Por Perspectiva:")
        lines.append(f"- Financeira: {len(self.financial_objectives)} objetivos")
        lines.append(f"- Clientes: {len(self.customer_objectives)} objetivos")
        lines.append(f"- Processos Internos: {len(self.process_objectives)} objetivos")
        lines.append(f"- Aprendizado e Crescimento: {len(self.learning_objectives)} objetivos")
        lines.append("")
        
        # Por prioridade
        lines.append("Por Prioridade:")
        high = len(self.by_priority("Alta"))
        medium = len(self.by_priority("Media"))
        low = len(self.by_priority("Baixa"))
        lines.append(f"- Alta: {high} objetivos")
        lines.append(f"- Media: {medium} objetivos")
        lines.append(f"- Baixa: {low} objetivos")
        lines.append("")
        
        # Vinculacao com KPIs
        with_kpis = len(self.with_related_kpis())
        percentage = int((with_kpis / total * 100)) if total > 0 else 0
        lines.append(f"Objetivos com KPIs vinculados: {with_kpis} de {total} ({percentage}%)")
        
        return "\n".join(lines)


# ====================================================================================
# BENCHMARKING SCHEMAS
# ====================================================================================


class BenchmarkComparison(BaseModel):
    """Comparação de uma métrica específica com benchmark externo.
    
    Representa uma comparação individual entre o desempenho atual da empresa
    e benchmarks externos relevantes (setor, porte, região) para uma métrica
    específica de uma perspectiva BSC.
    
    Attributes:
        perspective: Perspectiva BSC da métrica
        metric_name: Nome da métrica comparada (ex: "Margem EBITDA", "NPS")
        company_value: Valor atual da empresa (pode ser numérico ou textual)
        benchmark_value: Valor benchmark do mercado/setor
        gap: Diferença percentual (benchmark - company). Positivo = empresa abaixo, Negativo = empresa acima
        gap_type: Classificação do gap (positive/negative/neutral)
        benchmark_source: Fonte específica do benchmark (ex: "Setor Tecnologia SaaS Brasil 2024")
        insight: Interpretação qualitativa do gap (min 50 caracteres)
        priority: Prioridade de ação para fechar o gap (HIGH/MEDIUM/LOW)
    
    Example:
        >>> comparison = BenchmarkComparison(
        ...     perspective="Financeira",
        ...     metric_name="Margem EBITDA",
        ...     company_value="18%",
        ...     benchmark_value="25%",
        ...     gap=7.0,
        ...     gap_type="negative",
        ...     benchmark_source="Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte)",
        ...     insight="Margem EBITDA 7pp abaixo do mercado, indicando custos operacionais elevados ou pricing subotimizado",
        ...     priority="HIGH"
        ... )
    """
    
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"] = Field(
        description="Perspectiva BSC da métrica"
    )
    metric_name: str = Field(
        min_length=3,
        max_length=80,
        description="Nome da métrica comparada"
    )
    company_value: str = Field(
        min_length=1,
        max_length=50,
        description="Valor atual da empresa (numérico ou textual)"
    )
    benchmark_value: str = Field(
        min_length=1,
        max_length=50,
        description="Valor benchmark do mercado/setor"
    )
    gap: float = Field(
        description="Diferença percentual (benchmark - company). Positivo = empresa abaixo"
    )
    gap_type: Literal["positive", "negative", "neutral"] = Field(
        description="Classificação do gap: positive (empresa acima benchmark), negative (empresa abaixo), neutral (igual)"
    )
    benchmark_source: str = Field(
        min_length=20,
        max_length=150,
        description="Fonte específica do benchmark (deve ser detalhada, não genérica)"
    )
    insight: str = Field(
        min_length=50,
        max_length=500,
        description="Interpretação qualitativa do gap e suas implicações"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Prioridade de ação para fechar o gap"
    )
    
    @field_validator('gap')
    @classmethod
    def validate_gap_realistic(cls, v: float) -> float:
        """Valida que gap está em range realista (-100% a +200%).
        
        Gaps extremos (ex: -300%, +500%) são improváveis e indicam possível erro
        ou alucinação do LLM.
        """
        if v < -100 or v > 200:
            raise ValueError(
                f"Gap {v}% parece irreal. Esperado range: -100% a +200%. "
                f"Verifique se benchmark e company value estão corretos."
            )
        return v
    
    @field_validator('gap_type')
    @classmethod
    def validate_gap_type_aligns_with_gap(cls, v: str, info) -> str:
        """Valida que gap_type alinha com valor numérico do gap.
        
        Regras:
        - gap > 5: gap_type deve ser "negative" (empresa abaixo benchmark)
        - gap < -5: gap_type deve ser "positive" (empresa acima benchmark)
        - -5 <= gap <= 5: gap_type deve ser "neutral" (empresa no benchmark)
        """
        if 'gap' not in info.data:
            return v  # Gap ainda não validado, skip
        
        gap = info.data['gap']
        
        if gap > 5 and v != "negative":
            raise ValueError(
                f"Gap {gap}% > 5 (empresa abaixo benchmark) mas gap_type='{v}'. Esperado: 'negative'"
            )
        elif gap < -5 and v != "positive":
            raise ValueError(
                f"Gap {gap}% < -5 (empresa acima benchmark) mas gap_type='{v}'. Esperado: 'positive'"
            )
        elif -5 <= gap <= 5 and v != "neutral":
            raise ValueError(
                f"Gap {gap}% próximo de zero mas gap_type='{v}'. Esperado: 'neutral'"
            )
        
        return v
    
    @field_validator('benchmark_source')
    @classmethod
    def validate_benchmark_source_specific(cls, v: str) -> str:
        """Valida que benchmark_source é específico (não genérico).
        
        Sources genéricos como "mercado", "setor", "indústria" são vagos demais.
        Esperado: "Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte)"
        """
        generic_terms = ["mercado", "setor", "indústria", "industry", "market", "sector"]
        v_lower = v.lower()
        
        # Se source contém APENAS termo genérico (sem contexto adicional), rejeitar
        if any(term in v_lower for term in generic_terms) and len(v) < 40:
            raise ValueError(
                f"benchmark_source '{v}' parece muito genérico. "
                f"Forneça fonte específica (ex: 'Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte)')"
            )
        
        return v
    
    def __str__(self) -> str:
        """String representation legível."""
        return f"{self.perspective} - {self.metric_name}: {self.company_value} vs {self.benchmark_value} (gap: {self.gap:+.1f}%)"


class BenchmarkReport(BaseModel):
    """Relatório completo de benchmarking BSC (4 perspectivas).
    
    Consolida todas as comparações de benchmarking nas 4 perspectivas do
    Balanced Scorecard, fornecendo visão holística do desempenho da empresa
    vs mercado/setor.
    
    Attributes:
        comparisons: Lista de comparações individuais (6-20 items, ~2-5 por perspectiva)
        overall_performance: Avaliação geral do desempenho (acima/no/abaixo mercado)
        priority_gaps: Top 3-5 gaps críticos que requerem ação imediata
        recommendations: 3-5 recomendações estratégicas de alto nível
    
    Example:
        >>> report = BenchmarkReport(
        ...     comparisons=[
        ...         BenchmarkComparison(perspective="Financeira", ...),
        ...         BenchmarkComparison(perspective="Financeira", ...),
        ...         BenchmarkComparison(perspective="Clientes", ...),
        ...         # ... mais 5+ comparações
        ...     ],
        ...     overall_performance="abaixo_mercado",
        ...     priority_gaps=[
        ...         "Margem EBITDA 7pp abaixo (Financeira)",
        ...         "NPS 15 pontos abaixo (Clientes)",
        ...         "Lead Time 40% maior (Processos Internos)"
        ...     ],
        ...     recommendations=[
        ...         "Priorizar redução de custos operacionais (impacto: +7pp EBITDA)",
        ...         "Implementar programa Voice of Customer (meta: NPS +15 em 12 meses)",
        ...         "Automatizar processos críticos (reduzir Lead Time 40%)"
        ...     ]
        ... )
        >>> print(report.summary())
    """
    
    comparisons: list[BenchmarkComparison] = Field(
        min_length=6,
        max_length=20,
        description="Comparações de benchmarking (6-20 items, balanceadas entre perspectivas)"
    )
    overall_performance: Literal["acima_mercado", "no_mercado", "abaixo_mercado"] = Field(
        description="Avaliação geral do desempenho da empresa vs benchmark"
    )
    priority_gaps: list[str] = Field(
        min_length=3,
        max_length=5,
        description="Top 3-5 gaps críticos que requerem ação imediata (ordenados por prioridade)"
    )
    recommendations: list[str] = Field(
        min_length=3,
        max_length=5,
        description="3-5 recomendações estratégicas de alto nível para fechar gaps"
    )
    
    @model_validator(mode='after')
    def validate_balanced_perspectives(self) -> 'BenchmarkReport':
        """Valida que comparisons estão balanceadas entre 4 perspectivas BSC.
        
        Cada perspectiva deve ter pelo menos 2 e no máximo 5 comparações.
        Garante cobertura equilibrada das 4 perspectivas.
        """
        perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        counts = {p: 0 for p in perspectives}
        
        # Contar comparisons por perspectiva
        for comp in self.comparisons:
            counts[comp.perspective] += 1
        
        # Validar balanceamento (2-5 por perspectiva)
        for perspective, count in counts.items():
            if count < 2:
                raise ValueError(
                    f"Perspectiva '{perspective}' tem apenas {count} comparação(ões). "
                    f"Mínimo esperado: 2 por perspectiva para balanceamento BSC."
                )
            if count > 5:
                raise ValueError(
                    f"Perspectiva '{perspective}' tem {count} comparações. "
                    f"Máximo recomendado: 5 por perspectiva (foco nas métricas mais críticas)."
                )
        
        return self
    
    @model_validator(mode='after')
    def validate_priority_gaps_specific(self) -> 'BenchmarkReport':
        """Valida que priority_gaps mencionam métrica E perspectiva específicas.
        
        Gaps devem ser específicos (ex: "Margem EBITDA 7pp abaixo (Financeira)")
        e não genéricos (ex: "Performance financeira ruim").
        """
        for gap in self.priority_gaps:
            if len(gap) < 30:
                raise ValueError(
                    f"Priority gap '{gap}' muito vago (< 30 chars). "
                    f"Forneça descrição específica com métrica e perspectiva (ex: 'NPS 15 pontos abaixo (Clientes)')"
                )
        
        return self
    
    def comparisons_by_perspective(self, perspective: str) -> list[BenchmarkComparison]:
        """Retorna comparisons de uma perspectiva específica."""
        return [c for c in self.comparisons if c.perspective == perspective]
    
    def high_priority_comparisons(self) -> list[BenchmarkComparison]:
        """Retorna apenas comparisons com prioridade HIGH."""
        return [c for c in self.comparisons if c.priority == "HIGH"]
    
    def gaps_statistics(self) -> dict[str, float]:
        """Calcula estatísticas dos gaps (média, min, max por perspectiva)."""
        perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        stats = {}
        
        for perspective in perspectives:
            comps = self.comparisons_by_perspective(perspective)
            if comps:
                gaps = [c.gap for c in comps]
                stats[perspective] = {
                    "mean": sum(gaps) / len(gaps),
                    "min": min(gaps),
                    "max": max(gaps),
                    "count": len(gaps)
                }
        
        return stats
    
    def summary(self) -> str:
        """Gera sumário executivo do benchmarking report.
        
        Returns:
            String formatada com sumário (perspectivas, performance geral, top gaps)
        """
        lines = []
        lines.append("=" * 60)
        lines.append("BENCHMARK REPORT - SUMÁRIO EXECUTIVO")
        lines.append("=" * 60)
        lines.append("")
        
        # Overall performance
        performance_map = {
            "acima_mercado": "ACIMA DO MERCADO",
            "no_mercado": "NO MERCADO",
            "abaixo_mercado": "ABAIXO DO MERCADO"
        }
        lines.append(f"Performance Geral: {performance_map[self.overall_performance]}")
        lines.append("")
        
        # Comparisons por perspectiva
        lines.append("Comparações por Perspectiva:")
        for perspective in ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]:
            comps = self.comparisons_by_perspective(perspective)
            lines.append(f"  - {perspective}: {len(comps)} comparações")
        lines.append("")
        
        # Top priority gaps
        lines.append("Top Priority Gaps:")
        for i, gap in enumerate(self.priority_gaps, 1):
            lines.append(f"  {i}. {gap}")
        lines.append("")
        
        # Recommendations
        lines.append("Recomendações Estratégicas:")
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# ===================================================================
# ONBOARDING CONVERSATIONAL SCHEMAS (Refatoracao Out/2025)
# ===================================================================


class ExtractedEntities(BaseModel):
    """Entidades extraidas simultaneamente de mensagem do usuario.
    
    Schema wrapper para extracao oportunistica de TODAS entidades possiveis
    em qualquer turn da conversacao, independente da ordem.
    
    Pattern: Opportunistic Extraction (FASE 1 Onboarding Conversacional)
    Baseado em: LangChain Blog July 2025 (Context Engineering)
    
    Attributes:
        company_info: Informacoes da empresa extraidas (opcional)
        challenges: Lista de desafios estrategicos mencionados
        objectives: Lista de objetivos estrategicos mencionados
        has_company_info: Flag indicando se company info foi fornecida
        has_challenges: Flag indicando se challenges foram fornecidos
        has_objectives: Flag indicando se objectives foram fornecidos
    
    Example:
        >>> # Usuario fornece objectives ANTES de challenges (fora da ordem esperada)
        >>> entities = ExtractedEntities(
        ...     company_info=None,
        ...     challenges=[],
        ...     objectives=["Crescer 30% ao ano", "Reduzir custos em 15%"],
        ...     has_company_info=False,
        ...     has_challenges=False,
        ...     has_objectives=True
        ... )
        >>> # Sistema reconhece e adapta fluxo automaticamente
    
    Notes:
        - Campos sao Optional para permitir extracao parcial
        - Flags has_* facilitam deteccao de cenarios especificos
        - Suporta extracao de multiplas entidades em 1 mensagem
        - Evita necessidade de seguir ordem rigida (COMPANY -> CHALLENGES -> OBJECTIVES)
    """
    
    company_info: CompanyInfo | None = Field(
        None,
        description="Informacoes basicas da empresa (nome, setor, tamanho) se mencionadas"
    )
    challenges: list[str] = Field(
        default_factory=list,
        description="Lista de desafios ou problemas estrategicos mencionados pelo usuario",
        examples=[
            ["Crescimento insuficiente", "Baixa eficiencia operacional"],
            ["Alta rotatividade de colaboradores", "Custos elevados"]
        ]
    )
    objectives: list[str] = Field(
        default_factory=list,
        description="Lista de objetivos ou metas estrategicas mencionados pelo usuario",
        examples=[
            ["Crescer 15% no proximo ano", "Automatizar 50% dos processos"],
            ["Aumentar receita em 20%", "Melhorar NPS para 80 pontos"]
        ]
    )
    has_company_info: bool = Field(
        False,
        description="True se usuario forneceu informacoes da empresa nesta mensagem"
    )
    has_challenges: bool = Field(
        False,
        description="True se usuario forneceu desafios nesta mensagem"
    )
    has_objectives: bool = Field(
        False,
        description="True se usuario forneceu objetivos nesta mensagem"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_info": {
                    "name": "TechCorp Brasil",
                    "sector": "Tecnologia",
                    "size": "media"
                },
                "challenges": [
                    "Dificuldade em escalar equipe sem perder qualidade",
                    "Processos operacionais ainda imaturos"
                ],
                "objectives": [
                    "Crescer 30% ao ano mantendo margem",
                    "Expandir para mercado enterprise"
                ],
                "has_company_info": True,
                "has_challenges": True,
                "has_objectives": True
            }
        }
    )


class ConversationContext(BaseModel):
    """Contexto conversacional analisado para respostas adaptativas.
    
    Resultado da analise de contexto multi-turn para detectar cenarios
    especiais que requerem respostas diferentes do fluxo padrao.
    
    Pattern: Context-Aware Response Generation (FASE 1 Onboarding Conversacional)
    Baseado em: LangChain Blog July 2025 (Select Context), Tribe AI May 2025
    
    Attributes:
        scenario: Cenario detectado (ex: objectives_before_challenges, frustration_detected)
        user_sentiment: Sentimento do usuario (frustrated, neutral, positive)
        missing_info: Lista de informacoes ainda faltantes
        completeness: Porcentagem de completude do perfil (0.0 a 1.0)
        should_confirm: True se deve gerar sumario de confirmacao
        context_summary: Sumario do que ja foi coletado (para respostas empaticas)
    
    Scenarios Suportados:
        - objectives_before_challenges: Usuario forneceu objectives antes de challenges
        - frustration_detected: Usuario mostrou frustracao ("como mencionado", "ja disse")
        - information_complete: Todas informacoes necessarias coletadas
        - information_repeated: Usuario repetiu informacao ignorada anteriormente
        - standard_flow: Fluxo normal sem situacao especial
    
    Example:
        >>> # Cenario: Usuario forneceu objectives mas sistema esperava challenges
        >>> context = ConversationContext(
        ...     scenario="objectives_before_challenges",
        ...     user_sentiment="neutral",
        ...     missing_info=["challenges"],
        ...     completeness=0.65,
        ...     should_confirm=False,
        ...     context_summary="Ja temos: empresa (TechCorp), 2 objectives"
        ... )
        >>> # Sistema gera resposta reconhecendo objectives e pedindo challenges
    
    Notes:
        - Usado por _analyze_conversation_context() e _generate_contextual_response()
        - Permite deteccao de frustracao via keywords e repeticao
        - Suporta sumarios periodicos a cada 3-4 turns (confirmacao)
        - Completeness baseia-se em: company_info (35%), challenges (30%), objectives (35%)
    """
    
    scenario: Literal[
        "objectives_before_challenges",
        "frustration_detected",
        "information_complete",
        "information_repeated",
        "standard_flow"
    ] = Field(
        description="Cenario conversacional detectado"
    )
    user_sentiment: Literal["frustrated", "neutral", "positive"] = Field(
        description="Sentimento do usuario neste turn"
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description="Lista de informacoes ainda faltantes (company_info, challenges, objectives)"
    )
    completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="Porcentagem de completude do perfil (0.0 = vazio, 1.0 = completo)"
    )
    should_confirm: bool = Field(
        False,
        description="True se deve gerar sumario de confirmacao periodico"
    )
    context_summary: str = Field(
        "",
        description="Sumario breve do que ja foi coletado (para respostas empaticas)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario": "objectives_before_challenges",
                "user_sentiment": "neutral",
                "missing_info": ["challenges"],
                "completeness": 0.65,
                "should_confirm": False,
                "context_summary": "Ja temos: TechCorp (tecnologia, media), 2 objectives estrategicos"
            }
        }
    )


# ============================================================================
# TOOL SELECTION (Tool Routing - FASE 3.7)
# ============================================================================


class ToolSelection(BaseModel):
    """Resultado da selecao inteligente de ferramenta consultiva BSC.
    
    Este schema e usado pelo ConsultingOrchestrator para sugerir qual
    ferramenta consultiva (SWOT, Five Whys, Issue Tree, KPI, Strategic 
    Objectives, Benchmarking) e mais adequada baseado no contexto do cliente.
    
    A selecao usa abordagem hibrida:
    - Heuristica (keywords/regex) para casos obvios (90%)
    - LLM Classifier (GPT-5 mini) para casos ambiguos (10%)
    
    Attributes:
        tool_name: Nome da ferramenta selecionada (6 opcoes validas)
        confidence: Score de confianca da selecao (0.0-1.0)
        reasoning: Justificativa da selecao (minimo 20 caracteres)
        alternative_tools: Lista opcional de ferramentas alternativas (ranking)
    
    Added: 2025-10-27 (FASE 3.7)
    
    Example:
        >>> selection = ToolSelection(
        ...     tool_name="FIVE_WHYS",
        ...     confidence=0.92,
        ...     reasoning="Cliente mencionou 'causa raiz' e 'investigar problema' - Five Whys e ideal para root cause analysis",
        ...     alternative_tools=["ISSUE_TREE"]
        ... )
    """
    
    tool_name: Literal[
        "SWOT",
        "FIVE_WHYS",
        "ISSUE_TREE",
        "KPI_DEFINER",
        "STRATEGIC_OBJECTIVES",
        "BENCHMARKING"
    ] = Field(
        description="Nome da ferramenta consultiva BSC selecionada"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Score de confianca da selecao (0.0 = baixa, 1.0 = alta)"
    )
    
    reasoning: str = Field(
        min_length=20,
        description="Justificativa da selecao baseada no contexto do cliente"
    )
    
    alternative_tools: List[str] = Field(
        default_factory=list,
        description="Lista opcional de ferramentas alternativas (em ordem de relevancia)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tool_name": "FIVE_WHYS",
                "confidence": 0.92,
                "reasoning": "Cliente mencionou 'causa raiz' e problema especifico de baixas vendas - Five Whys e ideal para investigacao profunda",
                "alternative_tools": ["ISSUE_TREE", "SWOT"]
            }
        }
    )


# ============================================================================
# ACTION PLAN SCHEMAS (FASE 3.11)
# ============================================================================


class ActionItem(BaseModel):
    """Item individual de ação em plano de implementação BSC.
    
    Representa uma ação específica, mensurável e acionável necessária
    para implementar estratégia BSC baseada em diagnóstico realizado.
    
    Segue 7 Best Practices para Action Planning (SME Strategy 2025):
    1. Align actions with goals
    2. Prioritize based on importance and time sensitivity
    3. Be specific rather than general
    4. Set deadlines & assign owners
    5. Ask for volunteers or delegate tasks
    6. Develop action plan for implementation
    7. Track and monitor progress
    
    Attributes:
        action_title: Título específico da ação (não genérico)
        description: Descrição detalhada da ação
        perspective: Perspectiva BSC à qual a ação pertence
        priority: Prioridade da ação (HIGH/MEDIUM/LOW)
        effort: Esforço estimado para executar (HIGH/MEDIUM/LOW)
        responsible: Pessoa/equipe responsável pela execução
        start_date: Data de início da ação
        due_date: Data limite para conclusão
        resources_needed: Lista de recursos necessários
        success_criteria: Critérios para medir sucesso
        dependencies: Lista de ações dependentes
    
    Example:
        >>> action = ActionItem(
        ...     action_title="Implementar sistema de coleta de feedback de clientes",
        ...     description="Configurar plataforma online para coleta sistemática...",
        ...     perspective="Clientes",
        ...     priority="HIGH",
        ...     effort="MEDIUM",
        ...     responsible="Equipe de Marketing",
        ...     start_date="2025-11-01",
        ...     due_date="2025-12-15",
        ...     resources_needed=["Plataforma CRM", "Treinamento equipe"],
        ...     success_criteria="80% dos clientes respondendo surveys mensais",
        ...     dependencies=["Definir métricas de satisfação"]
        ... )
    """
    
    action_title: str = Field(
        min_length=10,
        max_length=200,
        description="Título específico e acionável da ação (não genérico)"
    )
    
    description: str = Field(
        min_length=20,
        max_length=1000,
        description="Descrição detalhada da ação a ser executada"
    )
    
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"] = Field(
        description="Perspectiva BSC à qual esta ação pertence"
    )
    
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Prioridade da ação baseada em importância e urgência"
    )
    
    effort: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Esforço estimado para executar esta ação"
    )
    
    responsible: str = Field(
        min_length=3,
        max_length=100,
        description="Pessoa ou equipe responsável pela execução"
    )
    
    start_date: str = Field(
        description="Data de início da ação (formato YYYY-MM-DD)"
    )
    
    due_date: str = Field(
        description="Data limite para conclusão da ação (formato YYYY-MM-DD)"
    )
    
    resources_needed: List[str] = Field(
        default_factory=list,
        description="Lista de recursos necessários para executar a ação"
    )
    
    success_criteria: str = Field(
        min_length=10,
        max_length=500,
        description="Critérios específicos para medir sucesso da ação"
    )
    
    dependencies: List[str] = Field(
        default_factory=list,
        description="Lista de outras ações que devem ser concluídas antes desta"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action_title": "Implementar sistema de coleta de feedback de clientes",
                "description": "Configurar plataforma online para coleta sistemática de feedback de clientes sobre produtos e serviços, incluindo integração com CRM existente",
                "perspective": "Clientes",
                "priority": "HIGH",
                "effort": "MEDIUM",
                "responsible": "Equipe de Marketing",
                "start_date": "2025-11-01",
                "due_date": "2025-12-15",
                "resources_needed": ["Plataforma CRM", "Treinamento equipe", "Orçamento R$ 5.000"],
                "success_criteria": "80% dos clientes respondendo surveys mensais com NPS > 8",
                "dependencies": ["Definir métricas de satisfação", "Aprovar orçamento"]
            }
        }
    )
    
    def is_high_priority(self) -> bool:
        """Verifica se ação é de alta prioridade.
        
        Returns:
            True se priority == "HIGH", False caso contrário
        """
        return self.priority == "HIGH"
    
    def is_high_effort(self) -> bool:
        """Verifica se ação requer alto esforço.
        
        Returns:
            True se effort == "HIGH", False caso contrário
        """
        return self.effort == "HIGH"
    
    def has_dependencies(self) -> bool:
        """Verifica se ação possui dependências.
        
        Returns:
            True se tem dependências, False caso contrário
        """
        return len(self.dependencies) > 0


class ActionPlan(BaseModel):
    """Plano de ação estruturado para implementação BSC.
    
    Consolida todas as ações necessárias para implementar estratégia BSC
    baseada em diagnóstico realizado, organizadas por perspectiva e prioridade.
    
    Segue estrutura BSC (Mooncamp 2025) - Step 3: "Define actions to achieve 
    the strategic goals" com 7 Best Practices para Action Planning.
    
    Attributes:
        action_items: Lista de todas as ações do plano
        total_actions: Número total de ações
        high_priority_count: Quantidade de ações de alta prioridade
        by_perspective: Dicionário de ações agrupadas por perspectiva BSC
        summary: Resumo executivo do plano
        timeline_summary: Resumo do cronograma de execução
    
    Example:
        >>> plan = ActionPlan(
        ...     action_items=[
        ...         ActionItem(action_title="Ação 1", ...),
        ...         ActionItem(action_title="Ação 2", ...)
        ...     ]
        ... )
        >>> plan.by_perspective("Clientes")  # Retorna ações da perspectiva Clientes
    """
    
    action_items: List[ActionItem] = Field(
        min_length=3,
        max_length=50,
        description="Lista de ações específicas para implementação BSC"
    )
    
    total_actions: int = Field(
        description="Número total de ações no plano"
    )
    
    high_priority_count: int = Field(
        description="Quantidade de ações de alta prioridade"
    )
    
    by_perspective: dict = Field(
        description="Dicionário com ações agrupadas por perspectiva BSC"
    )
    
    summary: str = Field(
        min_length=50,
        max_length=2000,
        description="Resumo executivo do plano de ação"
    )
    
    timeline_summary: str = Field(
        min_length=30,
        max_length=1000,
        description="Resumo do cronograma de execução"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action_items": [
                    {
                        "action_title": "Implementar sistema de coleta de feedback",
                        "description": "Configurar plataforma online...",
                        "perspective": "Clientes",
                        "priority": "HIGH",
                        "effort": "MEDIUM",
                        "responsible": "Equipe de Marketing",
                        "start_date": "2025-11-01",
                        "due_date": "2025-12-15",
                        "resources_needed": ["Plataforma CRM"],
                        "success_criteria": "80% clientes respondendo surveys",
                        "dependencies": ["Definir métricas"]
                    }
                ],
                "total_actions": 1,
                "high_priority_count": 1,
                "by_perspective": {
                    "Clientes": 1,
                    "Financeira": 0,
                    "Processos Internos": 0,
                    "Aprendizado e Crescimento": 0
                },
                "summary": "Plano de ação focado em melhorar satisfação de clientes através de sistema de feedback estruturado...",
                "timeline_summary": "Execução em 3 fases: Nov-Dez 2025 (alta prioridade), Jan-Mar 2026 (média prioridade)..."
            }
        }
    )
    
    def get_actions_by_perspective(self, perspective: str) -> List[ActionItem]:
        """Retorna ações filtradas por perspectiva BSC.
        
        Args:
            perspective: Perspectiva BSC ("Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento")
            
        Returns:
            Lista de ActionItem da perspectiva especificada
            
        Example:
            >>> plan.get_actions_by_perspective("Clientes")
            [ActionItem(...), ActionItem(...)]
        """
        return [action for action in self.action_items if action.perspective == perspective]
    
    def get_high_priority_actions(self) -> List[ActionItem]:
        """Retorna apenas ações de alta prioridade.
        
        Returns:
            Lista de ActionItem com priority == "HIGH"
        """
        return [action for action in self.action_items if action.is_high_priority()]
    
    def get_actions_by_effort(self, effort: str) -> List[ActionItem]:
        """Retorna ações filtradas por nível de esforço.
        
        Args:
            effort: Nível de esforço ("HIGH", "MEDIUM", "LOW")
            
        Returns:
            Lista de ActionItem com o esforço especificado
        """
        return [action for action in self.action_items if action.effort == effort]
    
    def is_balanced(self, min_actions_per_perspective: int = 1) -> bool:
        """Verifica se plano está balanceado entre as 4 perspectivas BSC.
        
        Args:
            min_actions_per_perspective: Mínimo de ações por perspectiva (default: 1)
            
        Returns:
            True se todas as perspectivas têm >= min_actions_per_perspective, False caso contrário
        """
        perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        return all(
            len(self.get_actions_by_perspective(perspective)) >= min_actions_per_perspective
            for perspective in perspectives
        )
    
    def quality_score(self, target_actions: int = 12) -> float:
        """Calcula score de qualidade do plano de ação.
        
        Score varia de 0.0 (pouco acionável) a 1.0 (excelente) baseado em:
        - Quantidade de ações (target: 12 ações)
        - Balanceamento entre perspectivas
        - Distribuição de prioridades
        
        Args:
            target_actions: Número ideal de ações (default: 12)
            
        Returns:
            Float entre 0.0 e 1.0 representando qualidade do plano
        """
        # Score por quantidade (40% do peso)
        quantity_score = min(len(self.action_items) / target_actions, 1.0)
        
        # Score por balanceamento (30% do peso)
        balance_score = 1.0 if self.is_balanced() else 0.5
        
        # Score por distribuição de prioridades (30% do peso)
        high_priority_ratio = self.high_priority_count / len(self.action_items) if self.action_items else 0
        priority_score = 1.0 if 0.2 <= high_priority_ratio <= 0.6 else 0.7  # Ideal: 20-60% alta prioridade
        
        return (quantity_score * 0.4) + (balance_score * 0.3) + (priority_score * 0.3)


# ============================================================================
# TOOL OUTPUT PERSISTENCE (FASE 3.9 - Persist Tool Outputs)
# ============================================================================


class ToolOutput(BaseModel):
    """Wrapper genérico para persistir outputs de ferramentas consultivas BSC no Mem0.
    
    Este schema encapsula qualquer output de ferramenta consultiva (SWOT, Five Whys,
    Issue Tree, KPI, Strategic Objectives, Benchmarking) para salvamento unificado
    no sistema de memória Mem0.
    
    Pattern de persistência:
    - tool_name: Identifica qual ferramenta gerou o output (Literal type-safe)
    - tool_output_data: Dados serializados do output (Any - suporta todos schemas)
    - created_at: Timestamp do output
    - client_context: Contexto opcional do cliente para busca semântica
    
    Estratégia Mem0:
    - Usa metadata.tool_output_data para armazenar dados estruturados (JSON)
    - Usa messages contextuais para busca semântica futura
    - Suporta deleção/atualização de outputs antigos (1 output por ferramenta por client_id)
    
    Added: 2025-10-27 (FASE 3.9)
    
    Example:
        >>> swot_output = SWOTAnalysis(strengths=["A"], weaknesses=["B"], ...)
        >>> tool_output = ToolOutput(
        ...     tool_name="SWOT",
        ...     tool_output_data=swot_output.model_dump(),
        ...     created_at=datetime.now(timezone.utc),
        ...     client_context="TechCorp - Empresa de tecnologia, medio porte, setor SaaS"
        ... )
        >>> mem0_client.save_tool_output("cliente_123", tool_output)
    """
    
    tool_name: Literal[
        "SWOT",
        "FIVE_WHYS",
        "ISSUE_TREE",
        "KPI_DEFINER",
        "STRATEGIC_OBJECTIVES",
        "BENCHMARKING",
        "ACTION_PLAN",
        "PRIORITIZATION_MATRIX"
    ] = Field(
        description="Nome da ferramenta consultiva que gerou este output"
    )
    
    tool_output_data: Any = Field(
        description="Dados serializados do output da ferramenta (dict ou objeto Pydantic convertido)"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de quando o output foi gerado"
    )
    
    client_context: Optional[str] = Field(
        None,
        description="Contexto opcional do cliente para busca semântica futura"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tool_name": "SWOT",
                "tool_output_data": {
                    "strengths": ["Equipe qualificada", "Marca forte"],
                    "weaknesses": ["Processos manuais"],
                    "opportunities": ["Expansão digital"],
                    "threats": ["Concorrência intensa"]
                },
                "created_at": "2025-10-27T12:30:00Z",
                "client_context": "TechCorp - Empresa de tecnologia, medio porte, setor SaaS"
            }
        }
    )


# ============================================================================
# PRIORITIZATION MATRIX (FASE 3.12 - Strategic Objectives/Actions Prioritization)
# ============================================================================


class PrioritizationCriteria(BaseModel):
    """Critérios de avaliação para priorização de objetivos/ações estratégicas BSC.
    
    Framework híbrido adaptado de:
    - Impact/Effort Matrix 2x2 (Mirorim 2025, McKinsey)
    - RICE Scoring (Intercom - Sean McBride)
    - BSC-Specific Criteria (Kaplan & Norton)
    
    4 critérios principais (0-100 scale):
    1. Strategic Impact: Potencial contribuição para objetivos estratégicos BSC
    2. Implementation Effort: Recursos necessários (tempo, pessoas, orçamento) [INVERTIDO no score]
    3. Urgency: Time sensitivity e impacto timing
    4. Strategic Alignment: Alinhamento com 4 perspectivas BSC e visão empresa
    
    Pesos padrão no cálculo de score:
    - Strategic Impact: 40%
    - Implementation Effort: 30% (invertido: 100 - effort)
    - Urgency: 15%
    - Strategic Alignment: 15%
    
    Added: 2025-10-27 (FASE 3.12)
    
    Example:
        >>> criteria = PrioritizationCriteria(
        ...     strategic_impact=85.0,
        ...     implementation_effort=30.0,
        ...     urgency=70.0,
        ...     strategic_alignment=90.0
        ... )
        >>> criteria.calculate_score()
        79.0  # (85*0.4) + ((100-30)*0.3) + (70*0.15) + (90*0.15)
    """
    
    strategic_impact: float = Field(
        ge=0.0,
        le=100.0,
        description="Potencial contribuição para objetivos estratégicos BSC (0-100%)"
    )
    
    implementation_effort: float = Field(
        ge=0.0,
        le=100.0,
        description="Recursos necessários para implementação - tempo, pessoas, orçamento (0-100%)"
    )
    
    urgency: float = Field(
        ge=0.0,
        le=100.0,
        description="Time sensitivity e impacto de timing (0-100%)"
    )
    
    strategic_alignment: float = Field(
        ge=0.0,
        le=100.0,
        description="Alinhamento com 4 perspectivas BSC e visão empresa (0-100%)"
    )
    
    def calculate_score(
        self,
        impact_weight: float = 0.40,
        effort_weight: float = 0.30,
        urgency_weight: float = 0.15,
        alignment_weight: float = 0.15
    ) -> float:
        """Calcula score final de priorização baseado nos 4 critérios.
        
        Formula: score = (impact * w1) + ((100 - effort) * w2) + (urgency * w3) + (alignment * w4)
        
        Nota: Effort é invertido (100 - effort) porque menor esforço = maior score.
        
        Args:
            impact_weight: Peso strategic_impact (default: 0.40 = 40%)
            effort_weight: Peso implementation_effort (default: 0.30 = 30%)
            urgency_weight: Peso urgency (default: 0.15 = 15%)
            alignment_weight: Peso strategic_alignment (default: 0.15 = 15%)
            
        Returns:
            Float entre 0.0 e 100.0 representando score de priorização
        """
        # Validar que pesos somam 1.0 (100%)
        total_weight = impact_weight + effort_weight + urgency_weight + alignment_weight
        if not (0.99 <= total_weight <= 1.01):  # Tolerância para arredondamento
            raise ValueError(f"Pesos devem somar 1.0 (100%), atual: {total_weight}")
        
        # Calcular score (effort invertido)
        score = (
            (self.strategic_impact * impact_weight) +
            ((100 - self.implementation_effort) * effort_weight) +
            (self.urgency * urgency_weight) +
            (self.strategic_alignment * alignment_weight)
        )
        
        return round(score, 2)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "strategic_impact": 85.0,
                "implementation_effort": 30.0,
                "urgency": 70.0,
                "strategic_alignment": 90.0
            }
        }
    )


class PrioritizedItem(BaseModel):
    """Item (objetivo/ação estratégica) priorizado com critérios, score e rank.
    
    Encapsula:
    - item_id: Identificador único do item
    - item_type: Tipo ("strategic_objective", "action_item", "initiative")
    - title: Nome/título do item
    - description: Descrição detalhada
    - perspective: Perspectiva BSC associada
    - criteria: PrioritizationCriteria avaliados
    - final_score: Score calculado (0-100)
    - priority_level: Nível de prioridade baseado no score
    - rank: Posição relativa na lista priorizada (1 = mais prioritário)
    
    4 níveis de prioridade (baseado no score final):
    - CRITICAL (75-100): Quick wins + strategic imperatives
    - HIGH (50-74): Important projects
    - MEDIUM (25-49): Nice-to-have improvements
    - LOW (0-24): Deprioritize or eliminate
    
    Added: 2025-10-27 (FASE 3.12)
    
    Example:
        >>> item = PrioritizedItem(
        ...     item_id="obj_001",
        ...     item_type="strategic_objective",
        ...     title="Aumentar NPS em 20 pontos",
        ...     description="...",
        ...     perspective="Clientes",
        ...     criteria=PrioritizationCriteria(strategic_impact=85, ...),
        ...     final_score=79.0,
        ...     rank=1
        ... )
        >>> item.priority_level
        "HIGH"
    """
    
    item_id: str = Field(
        description="Identificador único do item"
    )
    
    item_type: Literal["strategic_objective", "action_item", "initiative", "project"] = Field(
        description="Tipo do item sendo priorizado"
    )
    
    title: str = Field(
        min_length=10,
        max_length=200,
        description="Título/nome do item (10-200 caracteres)"
    )
    
    description: str = Field(
        min_length=20,
        description="Descrição detalhada do item (mínimo 20 caracteres)"
    )
    
    perspective: Literal[
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento",
        "Cross-Perspective"
    ] = Field(
        description="Perspectiva BSC associada ao item"
    )
    
    criteria: PrioritizationCriteria = Field(
        description="Critérios de avaliação do item"
    )
    
    final_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Score final calculado (0-100)"
    )
    
    priority_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(
        description="Nível de prioridade baseado no score (CRITICAL: 75-100, HIGH: 50-74, MEDIUM: 25-49, LOW: 0-24)"
    )
    
    rank: int = Field(
        ge=1,
        description="Posição relativa na lista priorizada (1 = mais prioritário)"
    )
    
    @field_validator("title", "description", mode="after")
    @classmethod
    def validate_non_empty_after_strip(cls, v: str) -> str:
        """Valida que campos texto não são vazios após strip."""
        if not v.strip():
            raise ValueError("Campo não pode ser vazio após strip")
        return v
    
    @model_validator(mode="after")
    def validate_priority_level_matches_score(self) -> "PrioritizedItem":
        """Valida que priority_level está alinhado com final_score.
        
        Raises:
            ValueError: Se priority_level não corresponde ao range de final_score
        """
        score = self.final_score
        level = self.priority_level
        
        # Validar alinhamento score ↔ priority_level
        if 75 <= score <= 100 and level != "CRITICAL":
            raise ValueError(f"Score {score} deve ter priority_level='CRITICAL', encontrado '{level}'")
        elif 50 <= score < 75 and level != "HIGH":
            raise ValueError(f"Score {score} deve ter priority_level='HIGH', encontrado '{level}'")
        elif 25 <= score < 50 and level != "MEDIUM":
            raise ValueError(f"Score {score} deve ter priority_level='MEDIUM', encontrado '{level}'")
        elif 0 <= score < 25 and level != "LOW":
            raise ValueError(f"Score {score} deve ter priority_level='LOW', encontrado '{level}'")
        
        return self
    
    def is_critical(self) -> bool:
        """Retorna True se item é CRITICAL priority."""
        return self.priority_level == "CRITICAL"
    
    def is_high_or_critical(self) -> bool:
        """Retorna True se item é HIGH ou CRITICAL priority."""
        return self.priority_level in ["CRITICAL", "HIGH"]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": "obj_001",
                "item_type": "strategic_objective",
                "title": "Aumentar NPS em 20 pontos até Q4 2025",
                "description": "Melhorar experiência do cliente através de pesquisas trimestrais e implementação de melhorias baseadas em feedback",
                "perspective": "Clientes",
                "criteria": {
                    "strategic_impact": 85.0,
                    "implementation_effort": 30.0,
                    "urgency": 70.0,
                    "strategic_alignment": 90.0
                },
                "final_score": 79.0,
                "priority_level": "HIGH",
                "rank": 1
            }
        }
    )


class PrioritizationMatrix(BaseModel):
    """Matriz de priorização completa com lista de items, análise e métodos úteis.
    
    Encapsula resultado completo da priorização de múltiplos objetivos/ações estratégicas
    BSC usando framework híbrido (Impact/Effort + RICE + BSC-specific).
    
    Métodos úteis:
    - .top_n(n): Retorna top N items mais prioritários
    - .by_priority_level(level): Filtra items por nível de prioridade
    - .by_perspective(perspective): Filtra items por perspectiva BSC
    - .summary(): Gera resumo executivo da matriz
    - .is_balanced(): Verifica balanceamento entre perspectivas
    
    Added: 2025-10-27 (FASE 3.12)
    
    Example:
        >>> matrix = PrioritizationMatrix(
        ...     items=[item1, item2, item3],
        ...     prioritization_context="Priorização objetivos estratégicos Q1 2025",
        ...     weights_config={"impact_weight": 0.40, ...}
        ... )
        >>> matrix.top_n(3)
        [item1, item2, item3]  # Ordenados por rank
        >>> matrix.summary()
        "Matriz de 10 items priorizados: 3 CRITICAL, 4 HIGH, 2 MEDIUM, 1 LOW..."
    """
    
    items: List[PrioritizedItem] = Field(
        min_length=1,
        description="Lista de items priorizados (mínimo 1 item)"
    )
    
    prioritization_context: str = Field(
        min_length=20,
        description="Contexto da priorização (ex: 'Objetivos estratégicos Q1 2025', 'Ações plano de ação BSC')"
    )
    
    weights_config: dict[str, float] = Field(
        default={
            "impact_weight": 0.40,
            "effort_weight": 0.30,
            "urgency_weight": 0.15,
            "alignment_weight": 0.15
        },
        description="Configuração de pesos usados no cálculo dos scores"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de quando a matriz foi criada"
    )
    
    @field_validator("prioritization_context", mode="after")
    @classmethod
    def validate_non_empty_context(cls, v: str) -> str:
        """Valida que contexto não é vazio após strip."""
        if not v.strip():
            raise ValueError("Contexto não pode ser vazio após strip")
        return v
    
    @model_validator(mode="after")
    def validate_unique_ranks(self) -> "PrioritizationMatrix":
        """Valida que ranks são únicos e sequenciais (1, 2, 3, ..., N).
        
        Raises:
            ValueError: Se ranks não são únicos ou não são sequenciais
        """
        ranks = [item.rank for item in self.items]
        expected_ranks = list(range(1, len(self.items) + 1))
        
        if sorted(ranks) != expected_ranks:
            raise ValueError(f"Ranks devem ser únicos e sequenciais 1..{len(self.items)}, encontrado: {sorted(ranks)}")
        
        return self
    
    @property
    def total_items(self) -> int:
        """Retorna total de items na matriz."""
        return len(self.items)
    
    @property
    def critical_count(self) -> int:
        """Retorna contagem de items CRITICAL."""
        return sum(1 for item in self.items if item.priority_level == "CRITICAL")
    
    @property
    def high_count(self) -> int:
        """Retorna contagem de items HIGH priority."""
        return sum(1 for item in self.items if item.priority_level == "HIGH")
    
    @property
    def medium_count(self) -> int:
        """Retorna contagem de items MEDIUM priority."""
        return sum(1 for item in self.items if item.priority_level == "MEDIUM")
    
    @property
    def low_count(self) -> int:
        """Retorna contagem de items LOW priority."""
        return sum(1 for item in self.items if item.priority_level == "LOW")
    
    def top_n(self, n: int) -> List[PrioritizedItem]:
        """Retorna top N items mais prioritários (ordenados por rank).
        
        Args:
            n: Número de items a retornar
            
        Returns:
            Lista de até N items com menor rank (mais prioritários)
        """
        sorted_items = sorted(self.items, key=lambda x: x.rank)
        return sorted_items[:n]
    
    def by_priority_level(self, level: str) -> List[PrioritizedItem]:
        """Retorna items filtrados por nível de prioridade.
        
        Args:
            level: Nível de prioridade ("CRITICAL", "HIGH", "MEDIUM", "LOW")
            
        Returns:
            Lista de PrioritizedItem com o nível especificado
        """
        return [item for item in self.items if item.priority_level == level]
    
    def by_perspective(self, perspective: str) -> List[PrioritizedItem]:
        """Retorna items filtrados por perspectiva BSC.
        
        Args:
            perspective: Perspectiva BSC ("Financeira", "Clientes", etc)
            
        Returns:
            Lista de PrioritizedItem da perspectiva especificada
        """
        return [item for item in self.items if item.perspective == perspective]
    
    def is_balanced(self, min_items_per_perspective: int = 1) -> bool:
        """Verifica se matriz está balanceada entre as 4 perspectivas BSC.
        
        Args:
            min_items_per_perspective: Mínimo de items por perspectiva (default: 1)
            
        Returns:
            True se todas as 4 perspectivas principais têm >= min_items_per_perspective, False caso contrário
        """
        perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        return all(
            len(self.by_perspective(perspective)) >= min_items_per_perspective
            for perspective in perspectives
        )
    
    def summary(self) -> str:
        """Gera resumo executivo da matriz de priorização.
        
        Returns:
            String com resumo estruturado (total items, distribuição prioridades, perspectivas, top 3)
        """
        top_3 = self.top_n(3)
        top_3_titles = ", ".join([f"{i+1}. {item.title}" for i, item in enumerate(top_3)])
        
        # Calcular distribuição por perspectiva
        perspective_counts = {
            "Financeira": len(self.by_perspective("Financeira")),
            "Clientes": len(self.by_perspective("Clientes")),
            "Processos Internos": len(self.by_perspective("Processos Internos")),
            "Aprendizado e Crescimento": len(self.by_perspective("Aprendizado e Crescimento")),
            "Cross-Perspective": len(self.by_perspective("Cross-Perspective"))
        }
        
        return (
            f"Matriz de Priorização: {self.total_items} items priorizados\n"
            f"Distribuição Prioridades: {self.critical_count} CRITICAL, {self.high_count} HIGH, "
            f"{self.medium_count} MEDIUM, {self.low_count} LOW\n"
            f"Distribuição Perspectivas: Financeira ({perspective_counts['Financeira']}), "
            f"Clientes ({perspective_counts['Clientes']}), Processos ({perspective_counts['Processos Internos']}), "
            f"Aprendizado ({perspective_counts['Aprendizado e Crescimento']}), Cross-Perspective ({perspective_counts['Cross-Perspective']})\n"
            f"Top 3 Prioridades: {top_3_titles}\n"
            f"Balanceamento: {'Sim' if self.is_balanced() else 'Não'} (mínimo 1 item/perspectiva)"
        )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "item_id": "obj_001",
                        "item_type": "strategic_objective",
                        "title": "Aumentar NPS em 20 pontos",
                        "description": "...",
                        "perspective": "Clientes",
                        "criteria": {"strategic_impact": 85, "implementation_effort": 30, "urgency": 70, "strategic_alignment": 90},
                        "final_score": 79.0,
                        "priority_level": "HIGH",
                        "rank": 1
                    }
                ],
                "prioritization_context": "Priorização objetivos estratégicos Q1 2025 - TechCorp",
                "weights_config": {"impact_weight": 0.40, "effort_weight": 0.30, "urgency_weight": 0.15, "alignment_weight": 0.15}
            }
        }
    )