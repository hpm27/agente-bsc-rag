"""Prompts para SWOT Analysis Tool.

Este módulo contém prompts otimizados para facilitar análise SWOT
estruturada baseada em contexto empresarial BSC.

Pattern: Conversational Facilitation + Structured Output (2025)
References:
- LLM-based conversational agents for behaviour change (ScienceDirect 2025)
- AI-Agent Applications Challenges Strategies and Best Practices (Medium 2024)
- Kore.ai Large Language Model (LLM) SWOT Analysis (Jul 2024)

Created: 2025-10-19 (FASE 3.1)
"""

# ============================================================================
# SWOT ANALYSIS FACILITATION PROMPT
# ============================================================================

FACILITATE_SWOT_PROMPT = """Você é um consultor especialista em Balanced Scorecard facilitando uma análise SWOT estruturada.

SEU PAPEL:
- Analisar o contexto da empresa fornecido
- Identificar Forças, Fraquezas, Oportunidades e Ameaças relevantes para implementação BSC
- Usar conhecimento da literatura BSC para contexto adicional (fornecido abaixo)
- Gerar análise SWOT completa e acionável

CONTEXTO DA EMPRESA:
{company_context}

CONHECIMENTO BSC RELEVANTE (da literatura):
{bsc_knowledge}

INSTRUÇÕES:
1. FORÇAS (Strengths): Identifique capacidades internas POSITIVAS que AJUDAM na implementação BSC
   - Recursos disponíveis (financeiros, humanos, tecnológicos)
   - Competências organizacionais únicas
   - Cultura favorável à estratégia
   - Processos já existentes que facilitam BSC

2. FRAQUEZAS (Weaknesses): Identifique limitações internas que DIFICULTAM implementação BSC
   - Gaps de competência ou recursos
   - Resistências culturais ou estruturais
   - Processos fragmentados ou ineficientes
   - Falta de clareza estratégica atual

3. OPORTUNIDADES (Opportunities): Identifique fatores EXTERNOS favoráveis para adotar BSC
   - Tendências de mercado alinhadas com BSC
   - Demandas de stakeholders por transparência/performance
   - Tecnologias emergentes que facilitam medição
   - Benchmarks de sucesso no setor

4. AMEAÇAS (Threats): Identifique riscos EXTERNOS que podem comprometer BSC
   - Volatilidade do ambiente de negócios
   - Concorrência agressiva que demanda respostas rápidas
   - Regulações que conflitam com métricas BSC
   - Pressões de curto prazo vs visão longo prazo

REQUISITOS CRÍTICOS:
- Mínimo 2 itens por quadrante (idealmente 3-5)
- Itens ESPECÍFICOS à empresa (não genéricos)
- Linguagem clara e acionável (evitar jargão desnecessário)
- Conectar itens às 4 perspectivas BSC quando relevante (Financeira, Clientes, Processos, Aprendizado)

FORMATO DE SAÍDA:
Retorne um objeto SWOTAnalysis estruturado JSON com 4 listas:
{{
    "strengths": ["Item 1", "Item 2", ...],
    "weaknesses": ["Item 1", "Item 2", ...],
    "opportunities": ["Item 1", "Item 2", ...],
    "threats": ["Item 1", "Item 2", ...]
}}

IMPORTANTE:
- NÃO invente informações sobre a empresa que não estão no contexto
- SE informação insuficiente, indique gaps explicitamente nos itens
- Priorize qualidade sobre quantidade (melhor 3 itens fortes que 10 genéricos)
"""

# ============================================================================
# SWOT SYNTHESIS PROMPT (para refinar SWOT inicial)
# ============================================================================

SYNTHESIZE_SWOT_PROMPT = """Você é um consultor BSC refinando uma análise SWOT preliminar.

SWOT PRELIMINAR:
{preliminary_swot}

CONTEXTO ADICIONAL DO DIAGNOSTIC BSC:
{diagnostic_context}

SEU OBJETIVO:
Refinar e enriquecer o SWOT preliminar com insights do diagnóstico BSC completo.

INSTRUÇÕES DE REFINAMENTO:
1. VALIDAR: Confirme se itens preliminares são coerentes com diagnóstico BSC
2. ENRIQUECER: Adicione nuances baseadas nas 4 perspectivas BSC analisadas
3. PRIORIZAR: Reordene itens por relevância estratégica (mais importante primeiro)
4. CONECTAR: Identifique relações entre quadrantes (ex: Força X mitiga Ameaça Y)

VALIDAÇÃO DE QUALIDADE:
- Cada quadrante deve ter 2-5 itens ESPECÍFICOS
- Evitar duplicações entre quadrantes (ex: mesma ideia em Strength e Opportunity)
- Linguagem consistente e profissional
- Itens acionáveis (não apenas descritivos)

FORMATO DE SAÍDA:
Retorne SWOTAnalysis JSON refinado com estrutura idêntica ao preliminar.

CRITICAL: Mantenha foco BSC - itens devem ser relevantes para implementação/uso do BSC, não análise genérica da empresa.
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
    """
    if not rag_results:
        return "Nenhum conhecimento BSC adicional recuperado."

    # Limitar a 5 chunks mais relevantes para não exceder context window
    top_chunks = rag_results[:5]

    knowledge_parts = []
    for idx, chunk in enumerate(top_chunks, 1):
        knowledge_parts.append(f"[REFERÊNCIA {idx}]\n{chunk}")

    return "\n\n".join(knowledge_parts)


def build_diagnostic_context(diagnostic_result) -> str:
    """Extrai contexto do diagnóstico BSC completo.

    Args:
        diagnostic_result: CompleteDiagnostic Pydantic model

    Returns:
        String formatada com insights diagnósticos
    """
    context_parts = []

    # Executive summary
    context_parts.append(f"RESUMO EXECUTIVO:\n{diagnostic_result.executive_summary}")

    # Insights por perspectiva (apenas key_insights, não análise completa)
    for perspective_name, perspective_field in [
        ("FINANCEIRA", "financial"),
        ("CLIENTES", "customer"),
        ("PROCESSOS", "process"),
        ("APRENDIZADO", "learning"),
    ]:
        perspective_data = getattr(diagnostic_result, perspective_field, None)
        if perspective_data and hasattr(perspective_data, "key_insights"):
            insights_text = "\n- ".join(perspective_data.key_insights)
            context_parts.append(f"\nINSIGHTS {perspective_name}:\n- {insights_text}")

    # Sinergias cross-perspective
    if diagnostic_result.cross_perspective_synergies:
        synergies_text = "\n- ".join(diagnostic_result.cross_perspective_synergies)
        context_parts.append(f"\nSINERGIAS IDENTIFICADAS:\n- {synergies_text}")

    return "\n\n".join(context_parts)
