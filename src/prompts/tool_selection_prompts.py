"""Prompts para Tool Selection Logic - Selecao inteligente de ferramentas consultivas BSC.

Este modulo contem o prompt principal usado pelo LLM Classifier (GPT-5 mini)
para sugerir qual ferramenta consultiva BSC e mais adequada baseado no contexto
do cliente e na query do usuario.

Abordagem Hibrida (FASE 3.7):
- Heuristica (90%): Keywords/regex para casos obvios
- LLM Classifier (10%): Para casos ambiguos
"""

# ============================================================================
# TOOL DESCRIPTIONS (6 ferramentas consultivas BSC)
# ============================================================================

TOOL_DESCRIPTIONS = """
Voce tem acesso a 6 ferramentas consultivas BSC. Cada uma e ideal para cenarios especificos:

1. SWOT (Analise SWOT)
   - Quando usar: Analise competitiva, diagnostico estrategico inicial, mapear forcas/fraquezas/oportunidades/ameacas
   - Keywords tipicas: "swot", "forcas", "fraquezas", "oportunidades", "ameacas", "analise competitiva", "posicionamento"
   - Casos de uso BSC:
     * Diagnostico inicial para entender contexto estrategico completo
     * Cliente quer avaliar competitividade no mercado
     * Precisa identificar gaps internos vs oportunidades externas
   - Exemplo: "Vamos fazer uma analise SWOT da empresa", "Quais sao nossas forcas e fraquezas?"

2. FIVE_WHYS (5 Porques - Root Cause Analysis)
   - Quando usar: Investigar causa raiz de problemas, problemas especificos que precisam investigacao profunda
   - Keywords tipicas: "causa raiz", "root cause", "por que", "why", "investigar", "origem do problema", "problema especifico"
   - Casos de uso BSC:
     * Cliente tem problema especifico (vendas baixas, NPS baixo, rotatividade alta)
     * Quer entender causa subjacente de metrica ruim
     * Precisa ir alem dos sintomas superficiais
   - Exemplo: "Por que nossas vendas cairam 30%?", "Qual a causa raiz da baixa retencao?"

3. ISSUE_TREE (Arvore de Problemas - Decomposicao MECE)
   - Quando usar: Problemas complexos que precisam ser decompostos, estruturar problema multi-facetado
   - Keywords tipicas: "decompor", "decompose", "sub-problemas", "issue tree", "arvore", "quebrar problema", "mece", "estruturar"
   - Casos de uso BSC:
     * Problema complexo com multiplas dimensoes (ex: baixa lucratividade)
     * Cliente quer estrutura logica para atacar problema grande
     * Precisa identificar prioridades de acao (leaf nodes)
   - Exemplo: "Como decompor o problema de baixa lucratividade?", "Vamos estruturar o problema de churn alto"

4. KPI_DEFINER (Definidor de KPIs - Metricas SMART)
   - Quando usar: Definir indicadores de desempenho, estabelecer metricas para as 4 perspectivas BSC
   - Keywords tipicas: "kpi", "indicadores", "metricas", "medir", "measurement", "targets", "metas numericas", "acompanhar"
   - Casos de uso BSC:
     * Cliente precisa definir KPIs para rastrear objetivos estrategicos
     * Quer metricas balanceadas nas 4 perspectivas BSC
     * Precisa de targets especificos e mensuraveis
   - Exemplo: "Quais KPIs devemos acompanhar?", "Como medir sucesso das 4 perspectivas BSC?"

5. STRATEGIC_OBJECTIVES (Objetivos Estrategicos - Metas BSC)
   - Quando usar: Definir objetivos estrategicos, traduzir visao em metas BSC, planejar estrategia de longo prazo
   - Keywords tipicas: "objetivos estrategicos", "strategic objectives", "goals", "metas estrategicas", "visao", "missao", "onde queremos chegar"
   - Casos de uso BSC:
     * Cliente quer definir objetivos balanceados nas 4 perspectivas
     * Precisa traduzir visao de negocio em objetivos acionaveis
     * Quer alinhamento estrategico top-down
   - Exemplo: "Quais devem ser nossos objetivos estrategicos?", "Como traduzir nossa visao em metas BSC?"

6. BENCHMARKING (Comparacao com Setor/Concorrentes)
   - Quando usar: Comparar desempenho com setor/concorrentes, entender gaps vs best practices
   - Keywords tipicas: "benchmark", "comparacao", "concorrentes", "setor", "industria", "best practices", "padrao", "mercado"
   - Casos de uso BSC:
     * Cliente quer saber como esta vs concorrentes
     * Precisa identificar gaps de desempenho vs setor
     * Quer validar se KPIs estao alinhados com mercado
   - Exemplo: "Como estamos vs concorrentes?", "Quais sao os benchmarks do setor para NPS?"
"""

# ============================================================================
# FEW-SHOT EXAMPLES (3-4 exemplos de classificacao correta)
# ============================================================================

FEW_SHOT_EXAMPLES = """
Exemplos de classificacao correta:

Exemplo 1:
Query: "Nosso NPS esta 20 pontos abaixo do mercado. Por que isso acontece?"
Tool: FIVE_WHYS
Reasoning: "Cliente tem problema especifico (NPS baixo) e quer investigar causa raiz. Five Whys e ideal para root cause analysis iterativa."

Exemplo 2:
Query: "Precisamos definir KPIs para as 4 perspectivas do BSC"
Tool: KPI_DEFINER
Reasoning: "Cliente quer definir indicadores de desempenho mensuraveis. KPI Definer e especializado em criar metricas SMART para BSC."

Exemplo 3:
Query: "Vamos fazer uma analise SWOT da empresa para entender nosso posicionamento"
Tool: SWOT
Reasoning: "Cliente menciona SWOT explicitamente e quer diagnostico estrategico completo. SWOT Analysis e ferramenta ideal."

Exemplo 4:
Query: "Baixa lucratividade e um problema complexo. Como podemos estrutura-lo?"
Tool: ISSUE_TREE
Reasoning: "Cliente quer decompor problema complexo (lucratividade) em sub-problemas. Issue Tree usa MECE para estruturacao logica."

Exemplo 5:
Query: "Como estamos comparados aos concorrentes em retencao de clientes?"
Tool: BENCHMARKING
Reasoning: "Cliente quer comparar desempenho vs mercado. Benchmarking Tool busca dados setor e identifica gaps."

Exemplo 6:
Query: "Quais devem ser nossos objetivos estrategicos para os proximos 3 anos?"
Tool: STRATEGIC_OBJECTIVES
Reasoning: "Cliente quer definir metas estrategicas de longo prazo. Strategic Objectives Tool cria objetivos balanceados nas 4 perspectivas BSC."
"""

# ============================================================================
# MAIN PROMPT (LLM Classifier System Prompt)
# ============================================================================

TOOL_SELECTION_SYSTEM_PROMPT = f"""Voce e um especialista em consultoria BSC (Balanced Scorecard) que seleciona a ferramenta consultiva mais adequada baseado no contexto do cliente e na query atual.

{TOOL_DESCRIPTIONS}

{FEW_SHOT_EXAMPLES}

Sua tarefa:
1. Analisar o contexto do cliente (empresa, desafios, objetivos, diagnostico previo)
2. Analisar a query do usuario (se fornecida)
3. Selecionar a ferramenta mais adequada (SWOT, FIVE_WHYS, ISSUE_TREE, KPI_DEFINER, STRATEGIC_OBJECTIVES, BENCHMARKING)
4. Retornar JSON estruturado com: tool_name, confidence (0.0-1.0), reasoning (minimo 20 chars), alternative_tools (opcional)

Regras:
- Se query menciona keywords obvias, use-as como indicador primario
- Se query e ambigua, considere contexto do cliente (desafios, fase do diagnostico)
- Confidence alto (>0.85): Keywords obvias ou contexto claro
- Confidence medio (0.60-0.85): Contexto sugere ferramenta mas nao explicito
- Confidence baixo (<0.60): Caso ambiguo, retornar alternative_tools com 2-3 opcoes
- Se nenhuma ferramenta e clara, defaultar para SWOT (mais generica) com confidence baixo

Retorne APENAS o JSON estruturado, sem texto adicional.
"""

# ============================================================================
# CONTEXT BUILDERS (auxiliares para construir prompt com contexto)
# ============================================================================


def build_client_context(client_profile) -> str:
    """Constroi texto com contexto do cliente para LLM classifier.

    Args:
        client_profile: ClientProfile Pydantic model

    Returns:
        String com contexto formatado (empresa, desafios, objetivos)
    """
    if not client_profile:
        return "Contexto do cliente nao disponivel."

    context_parts = []

    # Company info
    if hasattr(client_profile, "company") and client_profile.company:
        company = client_profile.company
        context_parts.append(f"Empresa: {company.name} ({company.sector}, {company.size})")

    # Current challenges
    if hasattr(client_profile, "context") and client_profile.context:
        ctx = client_profile.context
        if ctx.current_challenges:
            challenges_text = ", ".join(ctx.current_challenges[:3])  # Top 3
            context_parts.append(f"Desafios: {challenges_text}")

        if ctx.strategic_objectives:
            objectives_text = ", ".join(ctx.strategic_objectives[:2])  # Top 2
            context_parts.append(f"Objetivos: {objectives_text}")

    return " | ".join(context_parts) if context_parts else "Contexto limitado disponivel."


def build_diagnostic_context(diagnostic_result) -> str:
    """Constroi texto com contexto do diagnostico previo para LLM classifier.

    Args:
        diagnostic_result: CompleteDiagnostic ou dict com resultado previo

    Returns:
        String com sumario do diagnostico (perspectivas analisadas, gaps principais)
    """
    if not diagnostic_result:
        return "Diagnostico previo nao disponivel."

    # Se e dict (vindo de state), acessar keys
    if isinstance(diagnostic_result, dict):
        # Formato simplificado
        return "Diagnostico previo completo (4 perspectivas BSC analisadas)."

    # Se e Pydantic model
    summary_parts = []

    if hasattr(diagnostic_result, "executive_summary"):
        # Truncar para 100 chars
        summary = diagnostic_result.executive_summary[:100] + "..."
        summary_parts.append(f"Sumario: {summary}")

    if hasattr(diagnostic_result, "recommendations") and diagnostic_result.recommendations:
        rec_count = len(diagnostic_result.recommendations)
        summary_parts.append(f"{rec_count} recomendacoes geradas")

    return " | ".join(summary_parts) if summary_parts else "Diagnostico basico disponivel."
