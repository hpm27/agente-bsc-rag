"""Prompts conversacionais para Benchmarking Tool.

Este módulo contém prompts e context builders para facilitar a geração
de relatórios de benchmarking BSC comparando empresas com benchmarks externos.

Estrutura:
- BENCHMARKING_FACILITATION_PROMPT: Prompt principal para LLM structured output
- Context Builders (4):
  * build_company_context(): Formata informações da empresa (setor, porte, região)
  * build_diagnostic_context(): Formata diagnóstico BSC (4 perspectivas)
  * build_kpi_context(): Formata KPIs existentes com valores atuais (opcional)
  * build_rag_context(): Formata contexto da literatura BSC (opcional)

Padrão:
- Prompts conversacionais (tom facilitador, não imperativo)
- Contextos estruturados em seções delimitadas por '---'
- Instruções explícitas sobre validators Pydantic (evitar ValidationError)

Sessão: 21 (FASE 3.6 - Benchmarking Tool)
Autor: BSC RAG System
Data: 2025-10-19
"""

from src.memory.schemas import CompanyInfo, DiagnosticResult, KPIFramework

# ====================================================================================
# MAIN PROMPT - BENCHMARKING FACILITATION
# ====================================================================================


BENCHMARKING_FACILITATION_PROMPT = """Você é um especialista em **benchmarking estratégico BSC** com profundo conhecimento de práticas de mercado, benchmarks setoriais e análise competitiva.

Sua missão é gerar um **Benchmark Report** completo comparando o desempenho atual da empresa com benchmarks externos relevantes nas **4 perspectivas do Balanced Scorecard**.

---

## [EMOJI] CONTEXTO DA EMPRESA

{company_context}

---

## [EMOJI] DIAGNÓSTICO BSC ATUAL (4 Perspectivas)

{diagnostic_context}

---

{kpi_context_section}

{rag_context_section}

---

## [EMOJI] SUA TAREFA

Gere um **BenchmarkReport** completo com:

### 1. Comparações (6-20 items, balanceadas)
- **2-5 comparações POR PERSPECTIVA** BSC (Financeira, Clientes, Processos Internos, Aprendizado e Crescimento)
- Métricas específicas relevantes ao setor/porte da empresa
- Benchmarks de **fontes específicas** (ex: "Setor Tecnologia SaaS Brasil 2024 - empresas médio porte")

**ATENÇÃO aos validators Pydantic:**
- [OK] **gap**: range realista -100% a +200% (gaps extremos são inválidos)
- [OK] **gap_type**: deve alinhar com gap numérico
  * gap > 5 -> gap_type="negative" (empresa abaixo benchmark)
  * gap < -5 -> gap_type="positive" (empresa acima benchmark)
  * -5 <= gap <= 5 -> gap_type="neutral" (empresa no benchmark)
- [OK] **benchmark_source**: ESPECÍFICO (min 20 chars), NÃO genérico ("mercado", "setor")
  * BOM: "Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte - fonte: Gartner)"
  * RUIM: "mercado", "setor tecnologia"
- [OK] **insight**: mínimo 50 caracteres, explicar CAUSA do gap (não apenas constatar)
- [OK] **priority**: HIGH (crítico), MEDIUM (importante), LOW (monitorar)

### 2. Overall Performance
Classifique desempenho geral da empresa:
- **acima_mercado**: maioria dos gaps positivos (empresa supera benchmarks)
- **no_mercado**: gaps balanceados (empresa está na média)
- **abaixo_mercado**: maioria dos gaps negativos (empresa abaixo benchmarks)

### 3. Priority Gaps (3-5 items)
Top gaps críticos que requerem **ação imediata**:
- Ordenar por prioridade (HIGH primeiro)
- Ser **específico**: mencionar métrica E perspectiva (ex: "Margem EBITDA 7pp abaixo (Financeira)")
- Mínimo 30 caracteres por gap (validator Pydantic)

### 4. Recommendations (3-5 items)
Recomendações estratégicas de **alto nível** para fechar gaps:
- Ações concretas (não genéricas)
- Priorizar gaps HIGH
- Incluir impacto esperado quando possível (ex: "Reduzir custos operacionais (meta: +7pp EBITDA)")

---

## [WARN] DIRETRIZES CRÍTICAS

### Benchmarks REALISTAS
- Use conhecimento de benchmarks setoriais conhecidos até outubro 2025
- Se setor específico não conhecido, extrapolar de setores similares com disclaimer
- Evitar benchmarks extremos (-90%, +300%) - são improváveis e disparam validators

### Fontes ESPECÍFICAS
- [ERRO] EVITAR: "mercado", "setor", "indústria" (muito vago)
- [OK] PREFERIR: "Setor [específico] [região] [ano] ([detalhes porte/tipo])"
- Exemplo: "Setor Tecnologia SaaS Brasil 2024 (empresas médio porte B2B - ARR $5-20M)"

### Balanceamento OBRIGATÓRIO
- **2-5 comparações por perspectiva** (model_validator valida isso!)
- Se perspectiva tem < 2 comparações -> ValidationError
- Se perspectiva tem > 5 comparações -> Warning (foco demais em uma área)

### Insights QUALITATIVOS
- Explicar **POR QUÊ** o gap existe (não apenas "empresa está X% abaixo")
- Exemplo BOM: "NPS 15 pontos abaixo porque falta programa estruturado de Voice of Customer e onboarding é manual"
- Exemplo RUIM: "NPS é baixo"

---

## [EMOJI] OUTPUT ESPERADO

Retorne **APENAS** o JSON do BenchmarkReport com:
```json
{{
  "comparisons": [
    {{
      "perspective": "Financeira",
      "metric_name": "Margem EBITDA",
      "company_value": "18%",
      "benchmark_value": "25%",
      "gap": 7.0,
      "gap_type": "negative",
      "benchmark_source": "Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte B2B - ARR $5-20M)",
      "insight": "Margem EBITDA 7pp abaixo do mercado, indicando custos operacionais elevados ou pricing subotimizado. Empresas similares alcançam 25% via automação de processos e pricing value-based.",
      "priority": "HIGH"
    }},
    // ... 5-19 comparações adicionais (2-5 por perspectiva)
  ],
  "overall_performance": "abaixo_mercado",
  "priority_gaps": [
    "Margem EBITDA 7pp abaixo do benchmark setorial (Financeira) - impacto: 30% do potencial de lucro não realizado",
    "NPS 15 pontos abaixo do benchmark (Clientes) - risco: churn 20% maior que mercado",
    "Lead Time 40% maior que benchmark (Processos Internos) - impacto: perda de 15% oportunidades por lentidão"
  ],
  "recommendations": [
    "Priorizar redução de custos operacionais via automação (meta: +7pp EBITDA em 18 meses)",
    "Implementar programa Voice of Customer estruturado (meta: NPS +15 em 12 meses)",
    "Automatizar processos críticos de fulfillment (meta: Lead Time -40% em 9 meses)",
    "Revisar pricing strategy com abordagem value-based (meta: +3-5pp margem)"
  ]
}}
```

**IMPORTANTE**: Valide mentalmente contra validators Pydantic ANTES de gerar JSON!
"""


# ====================================================================================
# CONTEXT BUILDERS
# ====================================================================================


def build_company_context(company_info: CompanyInfo) -> str:
    """Formata informações da empresa para contexto de benchmarking.

    Args:
        company_info: Dados básicos da empresa (nome, setor, porte, etc.)

    Returns:
        String formatada com contexto da empresa (setor, porte, região, indústria)

    Example:
        >>> company = CompanyInfo(
        ...     name="TechCorp Brasil",
        ...     sector="Tecnologia",
        ...     size="média",
        ...     industry="Software as a Service",
        ...     region="Brasil"
        ... )
        >>> context = build_company_context(company)
        >>> print(context)
        Empresa: TechCorp Brasil
        Setor: Tecnologia
        Porte: média
        Indústria: Software as a Service
        Região: Brasil
    """
    lines = []
    lines.append(f"**Empresa**: {company_info.name}")
    lines.append(f"**Setor**: {company_info.sector}")
    lines.append(f"**Porte**: {company_info.size}")

    if hasattr(company_info, "industry") and company_info.industry:
        lines.append(f"**Indústria**: {company_info.industry}")

    if hasattr(company_info, "region") and company_info.region:
        lines.append(f"**Região**: {company_info.region}")

    if hasattr(company_info, "founded_year") and company_info.founded_year:
        lines.append(f"**Ano de Fundação**: {company_info.founded_year}")

    return "\n".join(lines)


def build_diagnostic_context(diagnostic: dict[str, DiagnosticResult]) -> str:
    """Formata diagnóstico BSC (4 perspectivas) para contexto.

    Args:
        diagnostic: Dict com 4 perspectivas BSC (keys: "Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento")
                   Values: DiagnosticResult objects

    Returns:
        String formatada com estado atual das 4 perspectivas

    Example:
        >>> diagnostic = {
        ...     "Financeira": DiagnosticResult(
        ...         perspective="Financeira",
        ...         current_state="Receita crescente mas margens comprimidas",
        ...         gaps=["Falta visibilidade de custos"],
        ...         opportunities=["Implementar ABC Costing"],
        ...         priority="HIGH"
        ...     ),
        ...     # ... outras 3 perspectivas
        ... }
        >>> context = build_diagnostic_context(diagnostic)
    """
    if not diagnostic or len(diagnostic) == 0:
        return "Diagnóstico BSC não disponível."

    lines = []

    # Perspectivas BSC na ordem padrão
    perspectives_order = [
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento",
    ]

    for perspective in perspectives_order:
        if perspective not in diagnostic:
            continue

        diag = diagnostic[perspective]
        lines.append(f"### {perspective} (Prioridade: {diag.priority})")
        lines.append(f"**Estado Atual**: {diag.current_state}")
        lines.append(f"**Gaps**: {', '.join(diag.gaps)}")
        lines.append(f"**Oportunidades**: {', '.join(diag.opportunities)}")
        lines.append("")

    return "\n".join(lines)


def build_kpi_context(kpi_framework: KPIFramework | None) -> str:
    """Formata KPIs existentes para contexto (opcional).

    Se empresa já tem KPIs definidos com valores atuais, inclui no contexto
    para LLM poder comparar com benchmarks.

    Args:
        kpi_framework: KPIFramework com KPIs das 4 perspectivas (None se não disponível)

    Returns:
        String formatada com KPIs e valores atuais, ou string vazia se None

    Example:
        >>> framework = KPIFramework(
        ...     financial_kpis=[
        ...         KPIDefinition(name="ROI", current_value="12%", target_value="18%", ...),
        ...         KPIDefinition(name="Margem Bruta", current_value="45%", ...)
        ...     ],
        ...     # ... outras perspectivas
        ... )
        >>> context = build_kpi_context(framework)
    """
    if kpi_framework is None:
        return ""

    lines = []
    lines.append("### Financeira")
    for kpi in kpi_framework.financial_kpis:
        value = getattr(kpi, "current_value", "N/A")
        lines.append(f"- {kpi.name}: {value}")
    lines.append("")

    lines.append("### Clientes")
    for kpi in kpi_framework.customer_kpis:
        value = getattr(kpi, "current_value", "N/A")
        lines.append(f"- {kpi.name}: {value}")
    lines.append("")

    lines.append("### Processos Internos")
    for kpi in kpi_framework.process_kpis:
        value = getattr(kpi, "current_value", "N/A")
        lines.append(f"- {kpi.name}: {value}")
    lines.append("")

    lines.append("### Aprendizado e Crescimento")
    for kpi in kpi_framework.learning_kpis:
        value = getattr(kpi, "current_value", "N/A")
        lines.append(f"- {kpi.name}: {value}")

    return "\n".join(lines)


def build_rag_context(retrieved_docs: list[str], query: str) -> str:
    """Formata contexto RAG da literatura BSC (opcional).

    Se RAG habilitado (use_rag=True), busca cases similares e best practices
    na literatura BSC indexada para enriquecer benchmarking.

    Args:
        retrieved_docs: Documentos recuperados do retriever RAG
        query: Query usada no retrieval (para referência)

    Returns:
        String formatada com contexto RAG, ou string vazia se sem docs

    Example:
        >>> docs = [
        ...     "Kaplan & Norton recomendam benchmarks externos...",
        ...     "Cases de empresas SaaS mostram margens EBITDA 20-30%..."
        ... ]
        >>> context = build_rag_context(docs, "benchmarking BSC technology sector")
    """
    if not retrieved_docs or len(retrieved_docs) == 0:
        return ""

    lines = []
    lines.append(f"**Query RAG**: {query}")
    lines.append(f"**Documentos Recuperados**: {len(retrieved_docs)}")
    lines.append("")

    for i, doc in enumerate(retrieved_docs, 1):
        # Truncar documento se muito longo (max 300 chars por doc)
        doc_preview = doc[:300] + "..." if len(doc) > 300 else doc
        lines.append(f"**Doc {i}**: {doc_preview}")
        lines.append("")

    return "\n".join(lines)


# ====================================================================================
# HELPER FUNCTIONS
# ====================================================================================


def format_benchmarking_prompt(
    company_info: CompanyInfo,
    diagnostic: dict[str, DiagnosticResult],
    kpi_framework: KPIFramework | None = None,
    rag_docs: list[str] | None = None,
    rag_query: str | None = None,
) -> str:
    """Formata prompt completo de benchmarking com todos os contextos.

    Combina prompt principal + context builders em um prompt completo pronto
    para envio ao LLM.

    Args:
        company_info: Informações básicas da empresa
        diagnostic: Diagnóstico BSC das 4 perspectivas
        kpi_framework: KPIs existentes (opcional)
        rag_docs: Documentos RAG recuperados (opcional)
        rag_query: Query usada no RAG (opcional)

    Returns:
        Prompt completo formatado pronto para LLM

    Example:
        >>> prompt = format_benchmarking_prompt(
        ...     company_info=company,
        ...     diagnostic=diagnostic,
        ...     kpi_framework=None,
        ...     rag_docs=None
        ... )
        >>> response = llm.invoke(prompt)
    """
    # Build contexts
    company_context = build_company_context(company_info)
    diagnostic_context = build_diagnostic_context(diagnostic)

    # KPI context (conditional)
    kpi_context_section = ""
    if kpi_framework is not None:
        kpi_context = build_kpi_context(kpi_framework)
        if kpi_context:
            kpi_context_section = f"""## [EMOJI] KPIs EXISTENTES (Valores Atuais)

{kpi_context}

---"""

    # RAG context (conditional)
    rag_context_section = ""
    if rag_docs and rag_query:
        rag_context = build_rag_context(rag_docs, rag_query)
        if rag_context:
            rag_context_section = f"""## [EMOJI] CONTEXTO DA LITERATURA BSC (RAG)

{rag_context}

---"""

    # Format final prompt
    return BENCHMARKING_FACILITATION_PROMPT.format(
        company_context=company_context,
        diagnostic_context=diagnostic_context,
        kpi_context_section=kpi_context_section,
        rag_context_section=rag_context_section,
    )
