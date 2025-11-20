"""Prompts para Five Whys (5 Porques) Analysis Tool.

Este módulo contém prompts otimizados para facilitar análise de causa raiz
usando o método 5 Whys desenvolvido por Taiichi Ohno (Toyota).

Pattern: Iterative Root Cause Analysis + Structured Output (2025)
References:
- 5 Whys Root Cause Analysis Best Practices (Reliability Center Inc. May 2025)
- AI-assisted 5 Whys Guide (LinkedIn Dr. T. Justin W. Feb 2025)
- Root Cause Analysis with AI (skan.ai Aug 2025)

Created: 2025-10-19 (FASE 3.2)
"""

# ============================================================================
# FIVE WHYS FACILITATION PROMPT (Iterativo)
# ============================================================================

FACILITATE_FIVE_WHYS_PROMPT = """Você é um consultor especialista em Balanced Scorecard facilitando uma análise de causa raiz usando o método 5 Whys.

SEU PAPEL:
- Guiar o processo de investigação perguntando "Por quê?" iterativamente
- Identificar a causa raiz fundamental (não apenas sintomas superficiais)
- Usar conhecimento da literatura BSC para enriquecer a análise
- Garantir que cada iteração avança em profundidade causal

CONTEXTO DA EMPRESA:
{company_context}

PROBLEMA IDENTIFICADO:
{problem_statement}

CONHECIMENTO BSC RELEVANTE (casos similares):
{bsc_knowledge}

ITERAÇÃO ATUAL: {current_iteration} de {max_iterations}

{iteration_context}

INSTRUÇÕES PARA ESTA ITERAÇÃO:

1. ANALISE O CONTEXTO:
   - Problema inicial: {problem_statement}
{previous_iterations_text}

2. FORMULE A PRÓXIMA PERGUNTA "Por quê?":
   - Baseada na última resposta fornecida
   - Mais específica e profunda que a anterior
   - Focada em CAUSA (não consequência)
   - Evite perguntas vagas ou genéricas

3. IDENTIFIQUE A RESPOSTA:
   - Baseada no contexto empresarial fornecido
   - Consulte conhecimento BSC se relevante
   - Seja ESPECÍFICO (ex: "Falta de budget" > "Recursos inadequados")
   - Se informação insuficiente, indique explicitamente

4. AVALIE PROFUNDIDADE:
   - Esta resposta é uma CAUSA ou um SINTOMA?
   - Chegamos à causa raiz (constraint, decisão passada, recurso limitante)?
   - Ou ainda há camadas causais mais profundas?

HEURÍSTICAS DE CAUSA RAIZ:
Uma causa raiz verdadeira geralmente:
[OK] Menciona recursos limitados (budget, tempo, pessoas)
[OK] Refere decisões estratégicas passadas
[OK] Identifica gaps de competência ou conhecimento
[OK] Aponta estrutura organizacional ou processos
[OK] É acionável (pode-se criar plano para resolver)

NÃO é causa raiz se:
[X] Ainda usa verbos de ação/gerúndio ("vendendo mal", "falhando")
[X] É consequência óbvia ("vendas baixas porque não vendemos")
[X] É muito vaga ("problemas na empresa")

FORMATO DE SAÍDA (JSON):
{{
    "question": "Por que [resposta_anterior] ocorre?",
    "answer": "Resposta específica baseada no contexto",
    "confidence": 0.85,
    "is_root_cause": false,
    "reasoning": "Breve explicação do raciocínio"
}}

IMPORTANTE:
- Confiança (confidence): 0.0-1.0 - Quão certo está desta resposta
- is_root_cause: true apenas se REALMENTE chegamos à causa fundamental
- NÃO force 5 iterações se root cause for atingida em 3-4
- NÃO pare prematuramente se ainda houver camadas causais
"""

# ============================================================================
# ROOT CAUSE SYNTHESIS PROMPT (Final)
# ============================================================================

SYNTHESIZE_ROOT_CAUSE_PROMPT = """Você é um consultor BSC sintetizando a causa raiz fundamental após análise 5 Whys.

PROBLEMA ORIGINAL:
{problem_statement}

ITERAÇÕES REALIZADAS ({num_iterations}):
{iterations_summary}

SEU OBJETIVO:
Identificar a CAUSA RAIZ FUNDAMENTAL que, se resolvida, eliminaria o problema original.

ANÁLISE CRÍTICA:

1. VALIDAR PROFUNDIDADE:
   - As iterações chegaram a uma causa acionável?
   - Ou pararam em sintomas intermediários?
   - A última resposta é uma constraint real (recurso, decisão, estrutura)?

2. FORMULAR CAUSA RAIZ:
   - Deve ser específica e verificável
   - Formato: "[Constraint/Gap] leva a [problema original]"
   - Exemplo: "Falta de budget para treinamento digital -> Equipe sem competências -> Marketing fraco -> Poucos leads -> Vendas baixas"

3. AVALIAR CONFIANÇA:
   - Baseada na qualidade das iterações
   - Baseada na consistência lógica causa-efeito
   - Baseada na especificidade da análise
   - Score: 0-100%

4. RECOMENDAR AÇÕES:
   - Mínimo 2 ações concretas para resolver causa raiz
   - Ações devem ser acionáveis (não vagas)
   - Conectar às 4 perspectivas BSC quando relevante
   - Exemplo: "Realocar 15% budget para programa treinamento digital" (Aprendizado)

FORMATO DE SAÍDA (JSON):
{{
    "root_cause": "Causa raiz fundamental identificada (específica)",
    "confidence_score": 85.0,
    "reasoning": "Explicação de como chegamos a esta causa",
    "recommended_actions": [
        "Ação 1 concreta e acionável",
        "Ação 2 concreta e acionável"
    ]
}}

VALIDAÇÃO CRÍTICA:
- Root cause deve ser diferente do problema original
- Confidence >= 70% para considerarmos análise confiável
- Se confidence < 70%, indique na reasoning que análise precisa ser aprofundada
- Ações devem atacar a CAUSA, não o SINTOMA
"""

# ============================================================================
# HELPER: Construir contexto da empresa para prompts
# ============================================================================


def build_company_context(company_info, strategic_context) -> str:
    """Constrói texto descritivo do contexto empresarial.

    Args:
        company_info: CompanyInfo Pydantic model
        strategic_context: StrategicContext Pydantic model

    Returns:
        String formatada com contexto completo

    Example:
        >>> context = build_company_context(company_info, strategic_context)
        >>> "EMPRESA: TechCorp" in context
        True
    """
    context_parts = []

    # Informações básicas
    context_parts.append(f"EMPRESA: {company_info.name}")
    context_parts.append(f"SETOR: {company_info.sector}")
    context_parts.append(f"PORTE: {company_info.size}")

    if company_info.industry:
        context_parts.append(f"INDÚSTRIA: {company_info.industry}")

    # Missão e Visão
    if strategic_context.mission:
        context_parts.append(f"\nMISSÃO:\n{strategic_context.mission}")

    if strategic_context.vision:
        context_parts.append(f"\nVISÃO:\n{strategic_context.vision}")

    # Valores
    if strategic_context.core_values:
        values_text = ", ".join(strategic_context.core_values)
        context_parts.append(f"\nVALORES: {values_text}")

    # Desafios atuais
    if strategic_context.current_challenges:
        challenges_text = "\n- ".join(strategic_context.current_challenges)
        context_parts.append(f"\nDESAFIOS ATUAIS:\n- {challenges_text}")

    # Objetivos estratégicos
    if strategic_context.strategic_objectives:
        objectives_text = "\n- ".join(strategic_context.strategic_objectives)
        context_parts.append(f"\nOBJETIVOS ESTRATÉGICOS:\n- {objectives_text}")

    return "\n\n".join(context_parts)


def build_bsc_knowledge_context(rag_results: list[str]) -> str:
    """Formata resultados RAG como conhecimento BSC.

    Args:
        rag_results: Lista de chunks de literatura BSC recuperados via RAG

    Returns:
        String formatada com conhecimento estruturado

    Example:
        >>> context = build_bsc_knowledge_context(["Chunk 1", "Chunk 2"])
        >>> "[REFERÊNCIA 1]" in context
        True
    """
    if not rag_results:
        return "Nenhum conhecimento BSC adicional recuperado."

    # Limitar a 5 chunks mais relevantes para não exceder context window
    top_chunks = rag_results[:5]

    knowledge_parts = []
    for idx, chunk in enumerate(top_chunks, 1):
        knowledge_parts.append(f"[REFERÊNCIA {idx}]\n{chunk}")

    return "\n\n".join(knowledge_parts)


def build_iterations_context(iterations: list) -> str:
    """Formata iterações anteriores para contexto do prompt.

    Args:
        iterations: Lista de WhyIteration Pydantic models

    Returns:
        String formatada com histórico de iterações

    Example:
        >>> context = build_iterations_context([iteration1, iteration2])
        >>> "Iteração 1:" in context
        True
    """
    if not iterations:
        return "Nenhuma iteração anterior."

    iterations_parts = []
    for iteration in iterations:
        iterations_parts.append(
            f"Iteração {iteration.iteration_number}: {iteration.question}\n"
            f"Resposta: {iteration.answer}\n"
            f"Confiança: {iteration.confidence:.2f}"
        )

    return "\n\n".join(iterations_parts)


def build_previous_iterations_text(iterations: list) -> str:
    """Constrói texto de iterações anteriores para prompt de iteração atual.

    Args:
        iterations: Lista de WhyIteration Pydantic models

    Returns:
        String formatada para inserção no prompt

    Example:
        >>> text = build_previous_iterations_text([iteration1])
        >>> "   - Iteração 1:" in text or text == ""
        True
    """
    if not iterations:
        return ""

    lines = []
    for iteration in iterations:
        lines.append(
            f"   - Iteração {iteration.iteration_number}: "
            f"{iteration.question} -> {iteration.answer}"
        )

    return "\n".join(lines)
