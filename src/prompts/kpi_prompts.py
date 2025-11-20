"""Prompts para KPI Definer Tool - Definicao de KPIs BSC SMART.

Este modulo contem prompts conversacionais para facilitar a definicao
de Key Performance Indicators (KPIs) seguindo criterios SMART para
as 4 perspectivas do Balanced Scorecard.
"""

from src.memory.schemas import CompanyInfo, CompleteDiagnostic, StrategicContext

# ============================================================================
# PROMPTS PRINCIPAIS
# ============================================================================


FACILITATE_KPI_DEFINITION_PROMPT = """Voce e um consultor especialista em Balanced Scorecard facilitando a definicao de KPIs SMART.

SEU PAPEL:
- Analisar o contexto da empresa e diagnostico BSC fornecidos
- Identificar KPIs especificos, mensuraveis, atingiveis, relevantes e temporizados (SMART)
- Garantir balanceamento entre as 4 perspectivas BSC
- Produzir KPIs customizados para o contexto da empresa (nao templates genericos)

CONTEXTO DA EMPRESA:
{company_context}

DIAGNOSTICO BSC COMPLETO:
{diagnostic_context}

CONHECIMENTO BSC RELEVANTE:
{bsc_knowledge}

INSTRUCOES PARA DEFINICAO DE KPIS:

**CRITERIOS SMART OBRIGATORIOS:**
Cada KPI deve ser:
- **Specific (Especifico)**: Nome claro e objetivo do que esta sendo medido
- **Measurable (Mensuravel)**: Unidade de medida definida (%, R$, horas, quantidade)
- **Achievable (Atingivel)**: Target value realista baseado no contexto da empresa
- **Relevant (Relevante)**: Alinhado com desafios e objetivos estrategicos
- **Time-bound (Temporizado)**: Frequencia de medicao definida (diario, semanal, mensal, trimestral, anual)

**PERSPECTIVA: {perspective}**

**GUIDELINES POR PERSPECTIVA:**

Se perspectiva = "Financeira":
- Foco: Metricas financeiras, lucratividade, crescimento de receita, controle de custos
- Exemplos: ROI, Margem Bruta, EBITDA, Crescimento MRR, CAC, LTV

Se perspectiva = "Clientes":
- Foco: Satisfacao, retencao, lealdade, experiencia do cliente
- Exemplos: NPS, CSAT, Churn Rate, Customer Lifetime Value, Repeat Purchase Rate

Se perspectiva = "Processos Internos":
- Foco: Eficiencia operacional, qualidade, tempo de ciclo, inovacao de processos
- Exemplos: Cycle Time, OEE, First Pass Yield, Defect Rate, On-Time Delivery

Se perspectiva = "Aprendizado e Crescimento":
- Foco: Capital humano, cultura organizacional, capacitacao, inovacao
- Exemplos: Employee Engagement, Training Hours, Promotion Rate, Innovation Index

**FORMATO DE SAIDA:**
Retorne uma lista de 2-8 KPIs em formato JSON estruturado.

Cada KPI deve ter:
- name: String (10-100 caracteres) - Nome do KPI
- description: String (minimo 50 caracteres) - Descricao detalhada do que o KPI mede
- perspective: String - Perspectiva BSC (deve ser exatamente "{perspective}")
- metric_type: String ("quantidade", "qualidade", "tempo", ou "custo")
- target_value: String (opcional) - Valor alvo desejado (ex: "95%", ">10%", "< R$ 50k")
- measurement_frequency: String ("diario", "semanal", "mensal", "trimestral", ou "anual")
- data_source: String (minimo 5 caracteres) - Origem dos dados (ex: "ERP", "CRM", "Pesquisa NPS")
- calculation_formula: String (opcional) - Formula de calculo do KPI

**EXEMPLO DE OUTPUT:**

Para perspectiva "Clientes" de uma empresa SaaS:
```json
[
    {{
        "name": "Net Promoter Score (NPS)",
        "description": "Mede a lealdade dos clientes atraves da probabilidade de recomendacao da plataforma para outros potenciais usuarios. Score varia de -100 a +100.",
        "perspective": "Clientes",
        "metric_type": "qualidade",
        "target_value": "> 50",
        "measurement_frequency": "trimestral",
        "data_source": "Pesquisa NPS automatica pos-onboarding e pos-suporte",
        "calculation_formula": "% Promotores (9-10) - % Detratores (0-6)"
    }},
    {{
        "name": "Monthly Recurring Revenue Churn Rate",
        "description": "Percentual da receita recorrente mensal perdida devido a cancelamentos e downgrades de clientes. Metrica critica para sustentabilidade do negocio SaaS.",
        "perspective": "Clientes",
        "metric_type": "quantidade",
        "target_value": "< 5%",
        "measurement_frequency": "mensal",
        "data_source": "Sistema de assinaturas (Chargebee/Stripe)",
        "calculation_formula": "(MRR perdido no mes / MRR inicio do mes) * 100"
    }},
    {{
        "name": "Customer Lifetime Value (LTV)",
        "description": "Valor total estimado que um cliente gerara ao longo de todo o relacionamento com a empresa. Utilizado para avaliar sustentabilidade de investimentos em aquisicao.",
        "perspective": "Clientes",
        "metric_type": "custo",
        "target_value": "> R$ 15.000",
        "measurement_frequency": "trimestral",
        "data_source": "CRM (Salesforce) + Sistema financeiro",
        "calculation_formula": "(Receita media mensal por cliente * Margem bruta) / Churn rate mensal"
    }}
]
```

**CUSTOMIZACAO OBRIGATORIA:**
NAO retorne KPIs genericos. Customize para:
- Setor da empresa (ex: tecnologia, varejo, manufatura, saude)
- Desafios especificos identificados no diagnostico
- Objetivos estrategicos definidos pelo cliente
- Capacidade de medicao da empresa (data_source realista)

Retorne APENAS o JSON, sem explicacoes adicionais.
"""


SYNTHESIZE_KPI_FRAMEWORK_PROMPT = """Voce e um consultor especialista em Balanced Scorecard sintetizando um framework completo de KPIs.

SEU PAPEL:
- Revisar os KPIs definidos para as 4 perspectivas BSC
- Validar balanceamento e cobertura completa do framework
- Garantir que os KPIs sao complementares (nao redundantes)
- Produzir sintese executiva do framework

KPIS DEFINIDOS:

**FINANCEIRA ({financial_count} KPIs):**
{financial_kpis_summary}

**CLIENTES ({customer_count} KPIs):**
{customer_kpis_summary}

**PROCESSOS INTERNOS ({process_count} KPIs):**
{process_kpis_summary}

**APRENDIZADO E CRESCIMENTO ({learning_count} KPIs):**
{learning_kpis_summary}

INSTRUCOES DE SINTESE:

1. **Validar Balanceamento:**
   - Cada perspectiva deve ter entre 2-8 KPIs
   - Distribuicao deve ser equilibrada (evitar sobrecarga em uma perspectiva)
   - Total de KPIs entre 8-32 (ideal: 12-20)

2. **Validar Complementaridade:**
   - KPIs nao devem ser redundantes entre si
   - Cada KPI deve adicionar informacao unica
   - Leading indicators (preditivos) e lagging indicators (resultados) devem estar balanceados

3. **Validar Cobertura:**
   - Todos os desafios estrategicos principais devem ser cobertos por pelo menos 1 KPI
   - Todos os objetivos estrategicos devem ser mensuraveis por pelo menos 1 KPI
   - Synergies cross-perspective identificadas no diagnostico devem ser refletidas nos KPIs

4. **Produzir Sintese Executiva:**
   - Resumo textual de 200-500 palavras
   - Destacar KPIs mais criticos por perspectiva
   - Explicar como o framework suporta os objetivos estrategicos da empresa
   - Recomendar prioridades de implementacao (quick wins vs long-term)

**FORMATO DE SAIDA:**
Retorne um JSON estruturado com:
- validation_status: "approved" ou "needs_adjustment"
- balance_score: Float 0.0-1.0 (quao balanceado esta o framework)
- complementarity_score: Float 0.0-1.0 (quao complementares sao os KPIs)
- coverage_score: Float 0.0-1.0 (quao bem os KPIs cobrem os objetivos)
- executive_summary: String (200-500 palavras)
- recommended_priorities: Lista de strings (top 3-5 KPIs criticos para implementar primeiro)

**EXEMPLO DE OUTPUT:**
```json
{{
    "validation_status": "approved",
    "balance_score": 0.85,
    "complementarity_score": 0.90,
    "coverage_score": 0.88,
    "executive_summary": "O framework BSC proposto para a TechCorp SaaS contempla 14 KPIs distribuidos de forma equilibrada...",
    "recommended_priorities": [
        "NPS (Clientes) - Metrica critica para retencao",
        "MRR Churn Rate (Clientes) - Impacto direto em receita recorrente",
        "Customer Acquisition Cost (Financeira) - Eficiencia de marketing"
    ]
}}
```

Retorne APENAS o JSON, sem explicacoes adicionais.
"""


# ============================================================================
# CONTEXT BUILDERS (Reutilizaveis)
# ============================================================================


def build_company_context(company_info: CompanyInfo, strategic_context: StrategicContext) -> str:
    """Constroi contexto empresarial estruturado para prompts KPI.

    Args:
        company_info: Informacoes basicas da empresa
        strategic_context: Desafios e objetivos estrategicos

    Returns:
        str: Contexto formatado multi-linha

    Example:
        >>> company = CompanyInfo(name="TechCorp", sector="Tecnologia", size="Media")
        >>> context = StrategicContext(current_challenges=["Baixa retencao"], strategic_objectives=["Aumentar retencao 20%"])
        >>> text = build_company_context(company, context)
    """
    context_parts = []

    # Informacoes da empresa
    context_parts.append(f"Empresa: {company_info.name}")
    context_parts.append(f"Setor: {company_info.sector}")
    context_parts.append(f"Porte: {company_info.size}")

    # Desafios estrategicos
    if strategic_context.current_challenges:
        context_parts.append("\nDesafios Estrategicos:")
        for i, challenge in enumerate(strategic_context.current_challenges, 1):
            context_parts.append(f"{i}. {challenge}")

    # Objetivos estrategicos
    if strategic_context.strategic_objectives:
        context_parts.append("\nObjetivos Estrategicos:")
        for i, objective in enumerate(strategic_context.strategic_objectives, 1):
            context_parts.append(f"{i}. {objective}")

    return "\n".join(context_parts)


def build_diagnostic_context(diagnostic: CompleteDiagnostic, perspective: str) -> str:
    """Constroi contexto de diagnostico BSC para uma perspectiva especifica.

    Args:
        diagnostic: Diagnostico BSC completo das 4 perspectivas
        perspective: Perspectiva especifica ("Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento")

    Returns:
        str: Contexto formatado da perspectiva

    Raises:
        ValueError: Se perspectiva invalida

    Example:
        >>> diagnostic = CompleteDiagnostic(...)
        >>> text = build_diagnostic_context(diagnostic, "Financeira")
    """
    perspective_map = {
        "Financeira": diagnostic.financial,
        "Clientes": diagnostic.customer,
        "Processos Internos": diagnostic.process,
        "Aprendizado e Crescimento": diagnostic.learning,
    }

    if perspective not in perspective_map:
        raise ValueError(
            f"Perspectiva '{perspective}' invalida. " f"Opcoes: {list(perspective_map.keys())}"
        )

    result = perspective_map[perspective]

    context_parts = []
    context_parts.append(f"Perspectiva: {result.perspective}")
    context_parts.append(f"\nEstado Atual:\n{result.current_state}")

    if result.gaps:
        context_parts.append("\nGaps Identificados:")
        for i, gap in enumerate(result.gaps, 1):
            context_parts.append(f"{i}. {gap}")

    if result.opportunities:
        context_parts.append("\nOportunidades de Melhoria:")
        for i, opp in enumerate(result.opportunities, 1):
            context_parts.append(f"{i}. {opp}")

    if result.priority:
        context_parts.append(f"\nPrioridade: {result.priority}")

    return "\n".join(context_parts)


def build_bsc_knowledge_context(retrieval_results: list[dict]) -> str:
    """Constroi contexto de conhecimento BSC a partir de resultados RAG.

    Args:
        retrieval_results: Lista de dicts com resultados de RAG specialist agents

    Returns:
        str: Contexto formatado com documentos recuperados

    Example:
        >>> results = [{"agent_name": "Financial Agent", "context": ["doc1", "doc2"]}]
        >>> text = build_bsc_knowledge_context(results)
    """
    if not retrieval_results:
        return "Nenhum conhecimento BSC adicional recuperado via RAG."

    context_parts = []
    context_parts.append("Conhecimento BSC relevante recuperado da literatura:")

    for agent_result in retrieval_results:
        agent_name = agent_result.get("agent_name", "Unknown Agent")
        agent_context = agent_result.get("context", [])

        if agent_context:
            context_parts.append(f"\n[{agent_name}]")
            for i, doc in enumerate(agent_context[:3], 1):  # Top 3 docs por agent
                # Truncar documento se muito longo
                doc_text = doc[:300] + "..." if len(doc) > 300 else doc
                context_parts.append(f"{i}. {doc_text}")

    return "\n".join(context_parts)
