"""Prompts conversacionais para definicao de objetivos estrategicos BSC.

Este modulo contem prompts especializados para facilitar a definicao de
objetivos estrategicos SMART alinhados com as 4 perspectivas do Balanced Scorecard.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.memory.schemas import CompleteDiagnostic

from src.memory.schemas import CompanyInfo, DiagnosticResult, KPIFramework

# ============================================================================
# CONTEXT BUILDERS - Funcoes reutilizaveis para montar contexto
# ============================================================================


def build_company_context(company_info: CompanyInfo) -> str:
    """Constroi contexto da empresa a partir de CompanyInfo.

    Args:
        company_info: Informacoes basicas da empresa

    Returns:
        str: Contexto formatado para inclusao em prompts

    Example:
        >>> company_info = CompanyInfo(name="TechCorp", sector="Tecnologia", size="media", industry="software")
        >>> context = build_company_context(company_info)
        >>> print(context)
        Empresa: TechCorp
        Setor: Tecnologia
        Porte: media
        Industria: software
    """
    lines = []
    lines.append(f"Empresa: {company_info.name}")
    lines.append(f"Setor: {company_info.sector}")
    lines.append(f"Porte: {company_info.size}")

    if company_info.industry:
        lines.append(f"Industria: {company_info.industry}")
    if company_info.founded_year:
        lines.append(f"Ano de fundacao: {company_info.founded_year}")

    return "\n".join(lines)


def build_diagnostic_context(diagnostic_result: DiagnosticResult) -> str:
    """Constroi contexto do diagnostico BSC realizado.

    Args:
        diagnostic_result: Resultado do diagnostico de UMA perspectiva BSC

    Returns:
        str: Contexto formatado para inclusao em prompts

    Example:
        >>> diagnostic_result = DiagnosticResult(...)
        >>> context = build_diagnostic_context(diagnostic_result)
        >>> print(context)
        Gaps identificados:
        - Margens EBITDA baixas (15% vs target 20%)
        - Falta visibilidade de custos por produto

        Estado atual resumido:
        Receita em crescimento acelerado...

        Oportunidades:
        - Implementar Activity-Based Costing
    """
    lines = []

    # Perspectiva
    lines.append(f"Perspectiva: {diagnostic_result.perspective}")
    lines.append("")

    # Gaps identificados
    if diagnostic_result.gaps:
        lines.append("Gaps identificados:")
        for gap in diagnostic_result.gaps[:5]:  # Top 5
            lines.append(f"- {gap}")
        lines.append("")

    # Estado atual
    if diagnostic_result.current_state:
        lines.append("Estado atual resumido:")
        # Limitar a 500 caracteres para nao estourar contexto
        state_summary = diagnostic_result.current_state[:500]
        if len(diagnostic_result.current_state) > 500:
            state_summary += "..."
        lines.append(state_summary)
        lines.append("")

    # Oportunidades
    if diagnostic_result.opportunities:
        lines.append("Oportunidades de melhoria:")
        for opp in diagnostic_result.opportunities[:3]:  # Top 3
            lines.append(f"- {opp}")
        lines.append("")

    # Prioridade
    lines.append(f"Prioridade desta perspectiva: {diagnostic_result.priority}")

    return "\n".join(lines)


def build_complete_diagnostic_context(complete_diagnostic: "CompleteDiagnostic") -> str:
    """Constroi contexto resumido do diagnostico completo (4 perspectivas).

    Args:
        complete_diagnostic: Diagnostico completo das 4 perspectivas BSC

    Returns:
        str: Contexto formatado resumido

    Example:
        >>> context = build_complete_diagnostic_context(complete_diagnostic)
        >>> print(context)
        Diagnostico BSC Completo:

        Financeira (HIGH): 3 gaps, 2 oportunidades
        Clientes (HIGH): 3 gaps, 2 oportunidades
        ...
    """
    lines = []
    lines.append("Diagnostico BSC Completo:")
    lines.append("")

    perspectives = [
        ("Financeira", complete_diagnostic.financial),
        ("Clientes", complete_diagnostic.customer),
        ("Processos Internos", complete_diagnostic.process),
        ("Aprendizado e Crescimento", complete_diagnostic.learning),
    ]

    for name, diag in perspectives:
        if diag:
            gaps_count = len(diag.gaps) if diag.gaps else 0
            opps_count = len(diag.opportunities) if diag.opportunities else 0
            lines.append(f"{name} ({diag.priority}): {gaps_count} gaps, {opps_count} oportunidades")

    lines.append("")
    lines.append(f"Resumo Executivo: {complete_diagnostic.executive_summary[:200]}...")

    return "\n".join(lines)


def build_kpi_context(kpi_framework: KPIFramework | None = None) -> str:
    """Constroi contexto de KPIs existentes (se fornecido).

    Args:
        kpi_framework: Framework de KPIs existente (opcional)

    Returns:
        str: Contexto formatado ou string vazia se nao fornecido

    Example:
        >>> kpi_framework = KPIFramework(...)
        >>> context = build_kpi_context(kpi_framework)
        >>> print(context)
        KPIs ja definidos (para vinculacao com objetivos):

        Perspectiva Financeira:
        - Margem EBITDA
        - Crescimento Receita

        Perspectiva Clientes:
        - NPS (Net Promoter Score)
    """
    if not kpi_framework:
        return ""

    lines = []
    lines.append("KPIs ja definidos (para vinculacao com objetivos):")
    lines.append("")

    # Financeira
    if kpi_framework.financial_kpis:
        lines.append("Perspectiva Financeira:")
        for kpi in kpi_framework.financial_kpis:
            lines.append(f"- {kpi.name}")
        lines.append("")

    # Clientes
    if kpi_framework.customer_kpis:
        lines.append("Perspectiva Clientes:")
        for kpi in kpi_framework.customer_kpis:
            lines.append(f"- {kpi.name}")
        lines.append("")

    # Processos
    if kpi_framework.process_kpis:
        lines.append("Perspectiva Processos Internos:")
        for kpi in kpi_framework.process_kpis:
            lines.append(f"- {kpi.name}")
        lines.append("")

    # Aprendizado
    if kpi_framework.learning_kpis:
        lines.append("Perspectiva Aprendizado e Crescimento:")
        for kpi in kpi_framework.learning_kpis:
            lines.append(f"- {kpi.name}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# PROMPTS PRINCIPAIS
# ============================================================================


FACILITATE_OBJECTIVES_DEFINITION_PROMPT = """Voce e um consultor estrategico especialista em Balanced Scorecard (BSC).

Sua missao e facilitar a definicao de objetivos estrategicos SMART para uma empresa,
alinhados com a perspectiva BSC especifica e baseados no diagnostico realizado.

CONTEXTO DA EMPRESA:
{company_context}

PERSPECTIVA BSC ATUAL:
{perspective}

DIAGNOSTICO REALIZADO:
{diagnostic_context}

{kpi_context}

OBJETIVO:
Defina entre 2 e 5 objetivos estrategicos SMART para a perspectiva "{perspective}".

CRITERIOS SMART:
- Specific (Especifico): Objetivo claro e bem definido
- Measurable (Mensuravel): Incluir criterios de sucesso quantificaveis
- Achievable (Atingivel): Realista considerando contexto da empresa
- Relevant (Relevante): Alinhado com desafios e recomendacoes do diagnostico
- Time-bound (Temporal): Prazo definido (geralmente 12-24 meses para estrategico)

DIRETRIZES POR PERSPECTIVA:

Se perspectiva FINANCEIRA:
- Foco em rentabilidade, crescimento de receita, otimizacao de custos, valor para acionistas
- Exemplo: "Aumentar margem EBITDA de 15% para 20% em 12 meses atraves de otimizacao de custos e crescimento de receita"

Se perspectiva CLIENTES:
- Foco em satisfacao, retencao, aquisicao, valor percebido, experiencia do cliente
- Exemplo: "Atingir NPS (Net Promoter Score) de 70 pontos em 18 meses atraves de melhoria continua da experiencia do cliente"

Se perspectiva PROCESSOS INTERNOS:
- Foco em eficiencia operacional, qualidade, inovacao, sustentabilidade, agilidade
- Exemplo: "Reduzir lead time de desenvolvimento de 6 para 3 semanas em 12 meses atraves de automacao e metodologias ageis"

Se perspectiva APRENDIZADO E CRESCIMENTO:
- Foco em capacitacao de pessoas, cultura organizacional, tecnologia, inovacao, conhecimento
- Exemplo: "Atingir taxa de retencao de talentos de 90% em 18 meses atraves de programa de desenvolvimento e engajamento"

VINCULAR COM KPIs (se fornecidos):
{kpi_linkage_instruction}

FORMATO DA RESPOSTA:
Para cada objetivo definido, retorne um objeto com os seguintes campos:

1. name (str): Nome conciso do objetivo (10-80 caracteres)
2. description (str): Detalhamento completo SMART (50-300 caracteres)
3. perspective (str): SEMPRE "{perspective}" (perspectiva atual sendo processada)
4. timeframe (str): Prazo para alcance (ex: "12 meses", "Q1 2026")
5. success_criteria (List[str]): 2-4 criterios mensuraveis de sucesso (cada um com 20+ caracteres)
6. related_kpis (List[str]): Lista de nomes de KPIs que medem progresso deste objetivo (se aplicavel)
7. priority (str): "Alta", "Média" ou "Baixa" baseado na urgencia e impacto
8. dependencies (List[str]): Lista de nomes de outros objetivos que sao prerequisitos (opcional)

IMPORTANTE:
- Definir ENTRE 2 E 5 objetivos para a perspectiva "{perspective}"
- Cada objetivo deve ser DISTINTO e cobrir uma area diferente da perspectiva
- Priorizar objetivos que abordam os principais desafios identificados no diagnostico
- success_criteria devem ser ESPECIFICOS e MENSURAVEIS (incluir numeros, percentuais, prazos)
- Se KPIs foram fornecidos, VINCULAR objetivos aos KPIs relevantes via campo related_kpis

Retorne apenas a lista de objetivos definidos (formato JSON).
"""


VALIDATE_OBJECTIVES_BALANCE_PROMPT = """Voce e um consultor estrategico especialista em Balanced Scorecard (BSC).

Sua missao e validar o balanceamento e alinhamento do framework de objetivos estrategicos
definidos para uma empresa, considerando as 4 perspectivas BSC.

CONTEXTO DA EMPRESA:
{company_context}

DIAGNOSTICO REALIZADO:
{diagnostic_context}

FRAMEWORK DE OBJETIVOS DEFINIDOS:
{objectives_summary}

CRITERIOS DE VALIDACAO:

1. BALANCEAMENTO ENTRE PERSPECTIVAS:
   - Nenhuma perspectiva deve ter mais de 50% dos objetivos totais
   - Idealmente, distribuicao entre 20-30% por perspectiva (margem: 15-35%)
   - Perspectivas criticas ao negocio podem ter pequena predominancia (ate 40%)

2. ALINHAMENTO COM DIAGNOSTICO:
   - Objetivos devem abordar os principais desafios identificados
   - Prioridades (Alta/Media/Baixa) alinhadas com urgencia dos problemas
   - Perspectivas mais criticas ao diagnostico devem ter mais objetivos de Alta prioridade

3. CONSISTENCIA INTERNA:
   - Objetivos de diferentes perspectivas devem ser complementares (nao contraditorios)
   - Dependencies entre objetivos devem fazer sentido (ex: processos eficientes -> clientes satisfeitos -> rentabilidade)
   - Timeframes coerentes (objetivos base antes de objetivos dependentes)

4. QUALIDADE SMART:
   - Cada objetivo tem criterios de sucesso mensuraveis e especificos
   - Timeframes realistas considerando complexidade e dependencies
   - Prioridades refletem impacto vs esforco

FORMATO DA RESPOSTA:

Retorne um objeto JSON com os seguintes campos:

1. is_balanced (bool): True se framework esta balanceado, False se precisa ajustes
2. balance_analysis (str): Analise textual da distribuicao entre perspectivas (100-200 caracteres)
3. alignment_score (float): Score 0.0-1.0 indicando alinhamento com diagnostico
4. alignment_analysis (str): Analise textual do alinhamento (100-200 caracteres)
5. consistency_issues (List[str]): Lista de inconsistencias encontradas (vazia se nenhuma)
6. recommendations (List[str]): Lista de 2-4 recomendacoes de ajustes (se necessario, vazia se ja OK)
7. overall_quality (str): "Excelente", "Bom", "Requer ajustes" ou "Insuficiente"

EXEMPLO DE RESPOSTA:

{{
    "is_balanced": true,
    "balance_analysis": "Distribuicao adequada: Financeira 25%, Clientes 30%, Processos 25%, Aprendizado 20%",
    "alignment_score": 0.85,
    "alignment_analysis": "Objetivos bem alinhados com desafios de escalabilidade e retencao identificados no diagnostico",
    "consistency_issues": [],
    "recommendations": [
        "Considerar adicionar objetivo de inovacao na perspectiva Processos Internos",
        "Revisar timeframe do objetivo 'Aumentar NPS' para 18 meses ao inves de 12 (mais realista)"
    ],
    "overall_quality": "Bom"
}}

Retorne apenas o objeto JSON de validacao.
"""


def build_kpi_linkage_instruction(kpi_framework: KPIFramework | None = None) -> str:
    """Constroi instrucao sobre vinculacao com KPIs baseado em disponibilidade.

    Args:
        kpi_framework: Framework de KPIs existente (opcional)

    Returns:
        str: Instrucao formatada

    Example:
        >>> kpi_framework = KPIFramework(...)
        >>> instruction = build_kpi_linkage_instruction(kpi_framework)
        >>> print(instruction)
        IMPORTANTE: KPIs ja foram definidos para esta empresa. Ao definir objetivos,
        utilize o campo 'related_kpis' para vincula-los aos KPIs relevantes listados acima.
    """
    if kpi_framework and kpi_framework.total_kpis() > 0:
        return (
            "IMPORTANTE: KPIs ja foram definidos para esta empresa. Ao definir objetivos, "
            "utilize o campo 'related_kpis' para vincula-los aos KPIs relevantes listados acima. "
            "Esta vinculacao e critica para garantir alinhamento entre direcao estrategica (objetivos) "
            "e medicao operacional (KPIs)."
        )
    return (
        "NOTA: KPIs ainda nao foram definidos para esta empresa. "
        "Deixe o campo 'related_kpis' vazio ou com lista vazia."
    )
