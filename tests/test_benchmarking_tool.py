"""Testes unitários para Benchmarking Tool.

Este módulo testa a BenchmarkingTool que compara desempenho da empresa
com benchmarks externos nas 4 perspectivas BSC.

Cobertura:
- Schemas Pydantic (BenchmarkComparison, BenchmarkReport)
- BenchmarkingTool.generate_benchmarks()
- Context builders (company, diagnostic, kpi, rag)
- Validators (gaps realistas, balanceamento, sources específicas)
- Integração DiagnosticAgent

PONTO 15 APLICADO: Schemas lidos via grep ANTES de criar fixtures
(ver grep commands no docstring de cada fixture)

Sessão: 21 (FASE 3.6 - Benchmarking Tool)
Autor: BSC RAG System
Data: 2025-10-19
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.memory.schemas import (
    BenchmarkComparison,
    BenchmarkReport,
    CompanyInfo,
    DiagnosticResult,
    KPIDefinition,
    KPIFramework,
)
from src.prompts.benchmarking_prompts import (
    build_company_context,
    build_diagnostic_context,
    build_kpi_context,
)
from src.tools.benchmarking_tool import BenchmarkingTool

# ====================================================================================
# FIXTURES - SCHEMAS PYDANTIC (PONTO 15 APLICADO)
# ====================================================================================


@pytest.fixture
def valid_company_info() -> CompanyInfo:
    """Company

    Info válida para benchmarking.

        PONTO 15 APLICADO:
        grep "class CompanyInfo" src/memory/schemas.py -A 30

        Campos validados (2025-10-19):
        - name: str (min_length=2, obrigatório)
        - sector: str (obrigatório)
        - size: Literal["micro", "pequena", "média", "grande"] (obrigatório)
        - industry: str (opcional)
        - region: str (opcional)
        - founded_year: int (opcional, 1800-2025)
    """
    return CompanyInfo(
        name="TechCorp Brasil Ltda",  # > 2 chars [OK]
        sector="Tecnologia",  # obrigatório [OK]
        size="média",  # Literal válido [OK]
        industry="Software as a Service (SaaS)",  # opcional fornecido [OK]
        region="Brasil",  # opcional fornecido [OK]
        founded_year=2018,  # 1800-2025 [OK]
    )


@pytest.fixture
def valid_diagnostic_four_perspectives() -> dict[str, DiagnosticResult]:
    """Diagnóstico BSC completo (4 perspectivas) para benchmarking.

    PONTO 15 APLICADO:
    grep "class DiagnosticResult" src/memory/schemas.py -A 50

    Campos validados (2025-10-19):
    - perspective: Literal[4 perspectivas BSC] (obrigatório)
    - current_state: str (min_length=20, obrigatório)
    - gaps: list[str] (min_length=1, obrigatório)
    - opportunities: list[str] (min_length=1, obrigatório)
    - priority: Literal["HIGH", "MEDIUM", "LOW"] (obrigatório)
    - key_insights: list[str] (opcional, default_factory=list)
    """
    return {
        "Financeira": DiagnosticResult(
            perspective="Financeira",
            current_state="Receita recorrente crescendo 25% ao ano mas margem EBITDA de apenas 18% devido custos operacionais elevados",  # > 20 chars [OK]
            gaps=["Falta visibilidade de custos por produto", "Pricing subotimizado"],  # min 1 [OK]
            opportunities=["Implementar ABC Costing", "Revisar pricing strategy"],  # min 1 [OK]
            priority="HIGH",
            key_insights=["Margem 7pp abaixo do mercado SaaS"],
        ),
        "Clientes": DiagnosticResult(
            perspective="Clientes",
            current_state="NPS de 42 pontos está 15 pontos abaixo do benchmark setorial, indicando insatisfação com onboarding manual",  # > 20 chars [OK]
            gaps=["Onboarding manual e lento", "Sem programa Voice of Customer"],
            opportunities=["Automatizar onboarding", "Implementar VoC estruturado"],
            priority="HIGH",
            key_insights=["Churn 20% maior que mercado"],
        ),
        "Processos Internos": DiagnosticResult(
            perspective="Processos Internos",
            current_state="Lead Time de 14 dias está 40% acima do benchmark (10 dias) devido processos manuais em fulfillment",  # > 20 chars [OK]
            gaps=["Processos manuais em fulfillment", "Falta automação"],
            opportunities=["Automatizar processos críticos", "Implementar workflow engine"],
            priority="MEDIUM",
            key_insights=["Perda de 15% oportunidades por lentidão"],
        ),
        "Aprendizado e Crescimento": DiagnosticResult(
            perspective="Aprendizado e Crescimento",
            current_state="Retenção de talentos de 85% ao ano está no mercado mas falta programa estruturado de desenvolvimento",  # > 20 chars [OK]
            gaps=["Sem programa de desenvolvimento estruturado", "Treinamento ad-hoc"],
            opportunities=[
                "Criar programa de desenvolvimento",
                "Implementar IDP (Individual Development Plan)",
            ],
            priority="LOW",
            key_insights=["Engajamento médio mas sem progressão de carreira clara"],
        ),
    }


@pytest.fixture
def valid_kpi_framework() -> KPIFramework:
    """KPI Framework válido (12 KPIs, 3 por perspectiva).

    PONTO 15 APLICADO:
    grep "class KPIFramework" src/memory/schemas.py -A 40

    Campos validados (2025-10-19):
    - financial_kpis: list[KPIDefinition] (min_length=2, max_length=8)
    - customer_kpis: list[KPIDefinition] (min_length=2, max_length=8)
    - process_kpis: list[KPIDefinition] (min_length=2, max_length=8)
    - learning_kpis: list[KPIDefinition] (min_length=2, max_length=8)
    """
    return KPIFramework(
        financial_kpis=[
            KPIDefinition(
                name="Margem EBITDA Anual",  # min_length=10 [OK]
                perspective="Financeira",
                description="Margem EBITDA anual calculada como EBITDA dividido por Receita Total, expressa em percentual",  # > 50 chars [OK]
                metric_type="custo",  # obrigatório [OK]
                target_value="25%",
                measurement_frequency="mensal",  # lowercase [OK]
                data_source="Demonstrações Financeiras (ERP)",  # obrigatório, > 5 chars [OK]
            ),
            KPIDefinition(
                name="ROI - Return on Investment Total",  # min_length=10 [OK]
                perspective="Financeira",
                description="Return on Investment calculado como (Ganho do Investimento - Custo do Investimento) / Custo do Investimento",  # > 50 chars [OK]
                metric_type="quantidade",  # obrigatório [OK]
                target_value="20%",
                measurement_frequency="trimestral",  # lowercase [OK]
                data_source="Relatórios Financeiros Trimestrais",  # obrigatório [OK]
            ),
        ],
        customer_kpis=[
            KPIDefinition(
                name="NPS - Net Promoter Score Clientes",  # min_length=10 [OK]
                perspective="Clientes",
                description="Net Promoter Score medindo lealdade dos clientes através da probabilidade de recomendação da empresa",  # > 50 chars [OK]
                metric_type="qualidade",  # obrigatório [OK]
                target_value="60",
                measurement_frequency="trimestral",  # lowercase [OK]
                data_source="Pesquisa NPS Automatizada (CRM)",  # obrigatório [OK]
            ),
            KPIDefinition(
                name="Churn Rate Mensal Clientes",  # min_length=10 [OK]
                perspective="Clientes",
                description="Taxa de churn mensal calculada como percentual de clientes perdidos em relação à base total de clientes ativos",  # > 50 chars [OK]
                metric_type="quantidade",  # obrigatório [OK]
                target_value="3%",
                measurement_frequency="mensal",  # lowercase [OK]
                data_source="Sistema de Gestão de Clientes (CRM)",  # obrigatório [OK]
            ),
        ],
        process_kpis=[
            KPIDefinition(
                name="Lead Time Fulfillment Médio",  # min_length=10 [OK]
                perspective="Processos Internos",
                description="Lead Time médio de fulfillment calculado como tempo total desde recebimento do pedido até entrega ao cliente",  # > 50 chars [OK]
                metric_type="tempo",  # obrigatório [OK]
                target_value="10",
                measurement_frequency="mensal",  # lowercase [OK]
                data_source="Sistema ERP - Módulo de Operações",  # obrigatório [OK]
            ),
            KPIDefinition(
                name="Cycle Time Processos Críticos",  # min_length=10 [OK]
                perspective="Processos Internos",
                description="Cycle Time médio dos processos críticos medindo tempo total de execução de início ao fim de cada processo",  # > 50 chars [OK]
                metric_type="tempo",  # obrigatório [OK]
                target_value="24",
                measurement_frequency="semanal",  # lowercase [OK]
                data_source="Plataforma BPM (Business Process Management)",  # obrigatório [OK]
            ),
        ],
        learning_kpis=[
            KPIDefinition(
                name="Retenção de Talentos Anual",  # min_length=10 [OK]
                perspective="Aprendizado e Crescimento",
                description="Taxa de retenção anual calculada como percentual de colaboradores que permaneceram na empresa durante o ano completo",  # > 50 chars [OK]
                metric_type="quantidade",  # obrigatório [OK]
                target_value="90%",
                measurement_frequency="anual",  # lowercase [OK]
                data_source="Sistema RH - Turnover Analytics",  # obrigatório [OK]
            ),
            KPIDefinition(
                name="Horas Treinamento por Funcionário Ano",  # min_length=10 [OK]
                perspective="Aprendizado e Crescimento",
                description="Horas médias de treinamento por funcionário ao ano, incluindo treinamentos técnicos, comportamentais e estratégicos",  # > 50 chars [OK]
                metric_type="quantidade",  # obrigatório [OK]
                target_value="80",
                measurement_frequency="anual",  # lowercase [OK]
                data_source="LMS (Learning Management System) + RH",  # obrigatório [OK]
            ),
        ],
    )


@pytest.fixture
def valid_benchmark_comparison() -> BenchmarkComparison:
    """BenchmarkComparison válida exemplo.

    PONTO 15 APLICADO:
    grep "class BenchmarkComparison" src/memory/schemas.py -A 80

    Campos validados (2025-10-19):
    - perspective: Literal[4 BSC] (obrigatório)
    - metric_name: str (min=3, max=80, obrigatório)
    - company_value: str (min=1, max=50, obrigatório)
    - benchmark_value: str (min=1, max=50, obrigatório)
    - gap: float (range: -100 a +200, obrigatório)
    - gap_type: Literal["positive", "negative", "neutral"] (obrigatório)
    - benchmark_source: str (min=20, max=150, obrigatório, específico)
    - insight: str (min=50, max=500, obrigatório)
    - priority: Literal["HIGH", "MEDIUM", "LOW"] (obrigatório)

    Validators:
    - gap range: -100% a +200%
    - gap_type alinha com gap numérico
    - benchmark_source específico (não genérico)
    """
    return BenchmarkComparison(
        perspective="Financeira",
        metric_name="Margem EBITDA",
        company_value="18%",
        benchmark_value="25%",
        gap=7.0,  # benchmark - company (positivo = empresa abaixo)
        gap_type="negative",  # gap > 5 -> negative [OK]
        benchmark_source="Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte B2B - ARR $5-20M)",  # > 20 chars, específico [OK]
        insight="Margem EBITDA 7pp abaixo do mercado, indicando custos operacionais elevados ou pricing subotimizado. Empresas similares alcançam 25% via automação de processos e pricing value-based.",  # > 50 chars [OK]
        priority="HIGH",
    )


@pytest.fixture
def valid_benchmark_report_8_comparisons() -> BenchmarkReport:
    """BenchmarkReport válido com 8 comparações balanceadas (2 por perspectiva).

    PONTO 15 APLICADO:
    grep "class BenchmarkReport" src/memory/schemas.py -A 100

    Campos validados (2025-10-19):
    - comparisons: list[BenchmarkComparison] (min=6, max=20, obrigatório)
    - overall_performance: Literal["acima_mercado", "no_mercado", "abaixo_mercado"] (obrigatório)
    - priority_gaps: list[str] (min=3, max=5, obrigatório, min 30 chars cada)
    - recommendations: list[str] (min=3, max=5, obrigatório)

    Model Validators:
    - validate_balanced_perspectives: 2-5 comparações por perspectiva
    - validate_priority_gaps_specific: gaps min 30 chars (métrica + perspectiva)
    """
    return BenchmarkReport(
        comparisons=[
            # Financeira (2)
            BenchmarkComparison(
                perspective="Financeira",
                metric_name="Margem EBITDA",
                company_value="18%",
                benchmark_value="25%",
                gap=7.0,
                gap_type="negative",
                benchmark_source="Setor Tecnologia SaaS Brasil 2024 (média empresas médio porte B2B - ARR $5-20M)",
                insight="Margem EBITDA 7pp abaixo do mercado, indicando custos operacionais elevados ou pricing subotimizado",
                priority="HIGH",
            ),
            BenchmarkComparison(
                perspective="Financeira",
                metric_name="ROI",
                company_value="15%",
                benchmark_value="21%",
                gap=6.0,  # > 5 -> gap_type="negative" válido [OK]
                gap_type="negative",
                benchmark_source="Benchmark Tecnologia SaaS Global 2024 (empresas B2B médio porte)",
                insight="ROI 6pp abaixo, indicando retorno sobre investimento menor que concorrentes diretos",
                priority="MEDIUM",
            ),
            # Clientes (2)
            BenchmarkComparison(
                perspective="Clientes",
                metric_name="NPS",
                company_value="42 pontos",
                benchmark_value="57 pontos",
                gap=15.0,
                gap_type="negative",
                benchmark_source="Benchmark NPS B2B SaaS Brasil 2024 (empresas mid-market)",
                insight="NPS 15 pontos abaixo do benchmark, indicando insatisfação com onboarding manual e suporte reativo",
                priority="HIGH",
            ),
            BenchmarkComparison(
                perspective="Clientes",
                metric_name="Churn Rate",
                company_value="5%",
                benchmark_value="3%",
                gap=2.0,
                gap_type="neutral",
                benchmark_source="Churn Rate SaaS Brasil 2024 (empresas médio porte B2B)",
                insight="Churn 2pp acima do mercado, correlacionado com NPS baixo e onboarding deficiente",
                priority="HIGH",
            ),
            # Processos Internos (2)
            BenchmarkComparison(
                perspective="Processos Internos",
                metric_name="Lead Time",
                company_value="14 dias",
                benchmark_value="10 dias",
                gap=40.0,  # (14-10)/10 = 40% maior
                gap_type="negative",
                benchmark_source="Lead Time Fulfillment SaaS 2024 (empresas médio porte)",
                insight="Lead Time 40% maior que benchmark devido processos manuais em fulfillment, causando perda de 15% oportunidades",
                priority="MEDIUM",
            ),
            BenchmarkComparison(
                perspective="Processos Internos",
                metric_name="Cycle Time",
                company_value="36 horas",
                benchmark_value="24 horas",
                gap=50.0,
                gap_type="negative",
                benchmark_source="Cycle Time Processos Críticos Tech 2024 (empresas B2B médio porte)",
                insight="Cycle Time 50% acima do mercado, indicando necessidade de automação de processos críticos",
                priority="LOW",
            ),
            # Aprendizado e Crescimento (2)
            BenchmarkComparison(
                perspective="Aprendizado e Crescimento",
                metric_name="Retenção de Talentos",
                company_value="85%",
                benchmark_value="88%",
                gap=3.0,
                gap_type="neutral",  # gap < 5 -> neutral [OK]
                benchmark_source="Retenção Talentos Tech Brasil 2024 (empresas médio porte)",
                insight="Retenção no mercado mas margem de melhoria com programa estruturado de desenvolvimento e carreira",
                priority="LOW",
            ),
            BenchmarkComparison(
                perspective="Aprendizado e Crescimento",
                metric_name="Horas de Treinamento",
                company_value="60 horas/ano",
                benchmark_value="80 horas/ano",
                gap=25.0,
                gap_type="negative",
                benchmark_source="Investimento em Treinamento Tech 2024 (empresas inovadoras)",
                insight="Investimento em treinamento 25% abaixo do mercado, limitando desenvolvimento de competências estratégicas",
                priority="MEDIUM",
            ),
        ],
        overall_performance="abaixo_mercado",  # Maioria gaps negativos [OK]
        priority_gaps=[
            "Margem EBITDA 7pp abaixo do benchmark setorial (Financeira) - impacto: 30% do potencial de lucro não realizado",  # > 30 chars [OK]
            "NPS 15 pontos abaixo do benchmark (Clientes) - risco: churn 20% maior que mercado",  # > 30 chars [OK]
            "Lead Time 40% maior que benchmark (Processos Internos) - impacto: perda de 15% oportunidades por lentidão",  # > 30 chars [OK]
        ],
        recommendations=[
            "Priorizar redução de custos operacionais via automação (meta: +7pp EBITDA em 18 meses)",
            "Implementar programa Voice of Customer estruturado (meta: NPS +15 em 12 meses)",
            "Automatizar processos críticos de fulfillment (meta: Lead Time -40% em 9 meses)",
            "Revisar pricing strategy com abordagem value-based (meta: +3-5pp margem)",
        ],
    )


# ====================================================================================
# FIXTURES - MOCKS
# ====================================================================================


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock LLM que retorna BenchmarkReport válido.

    NOTA: Mock ESTÁTICO (return_value fixo) é SUFICIENTE aqui!
    Diferente de KPI Definer (4 chamadas sequenciais), Benchmarking Tool
    faz 1 única chamada LLM que retorna BenchmarkReport completo.

    NÃO precisa itertools.cycle (checklist ponto 14 não se aplica).
    """
    llm = MagicMock(spec=["invoke", "with_structured_output"])

    # BenchmarkReport mock (8 comparações balanceadas)
    mock_report = BenchmarkReport(
        comparisons=[
            BenchmarkComparison(
                perspective="Financeira",
                metric_name="Margem EBITDA",
                company_value="18%",
                benchmark_value="25%",
                gap=7.0,
                gap_type="negative",
                benchmark_source="Setor Tecnologia SaaS Brasil 2024 (médio porte)",
                insight="Margem EBITDA 7pp abaixo indicando custos operacionais elevados",
                priority="HIGH",
            ),
            BenchmarkComparison(
                perspective="Financeira",
                metric_name="ROI",
                company_value="15%",
                benchmark_value="21%",
                gap=6.0,  # > 5 -> gap_type="negative" válido [OK]
                gap_type="negative",
                benchmark_source="Benchmark SaaS Global 2024 (B2B médio porte)",
                insight="ROI 6pp abaixo indicando retorno menor que concorrentes",
                priority="MEDIUM",
            ),
            BenchmarkComparison(
                perspective="Clientes",
                metric_name="NPS",
                company_value="42",
                benchmark_value="57",
                gap=15.0,
                gap_type="negative",
                benchmark_source="NPS B2B SaaS Brasil 2024 (empresas médio porte B2B)",
                insight="NPS 15 pontos abaixo indicando insatisfação com onboarding",
                priority="HIGH",
            ),
            BenchmarkComparison(
                perspective="Clientes",
                metric_name="Churn",
                company_value="5%",
                benchmark_value="3%",
                gap=2.0,
                gap_type="neutral",
                benchmark_source="Churn SaaS Brasil 2024 (médio porte B2B)",
                insight="Churn 2pp acima do mercado correlacionado com NPS baixo e onboarding deficiente",
                priority="HIGH",
            ),
            BenchmarkComparison(
                perspective="Processos Internos",
                metric_name="Lead Time",
                company_value="14 dias",
                benchmark_value="10 dias",
                gap=40.0,
                gap_type="negative",
                benchmark_source="Lead Time SaaS 2024 (empresas médio porte)",
                insight="Lead Time 40% maior devido processos manuais em fulfillment causando perda de oportunidades",
                priority="MEDIUM",
            ),
            BenchmarkComparison(
                perspective="Processos Internos",
                metric_name="Cycle Time",
                company_value="36h",
                benchmark_value="24h",
                gap=50.0,
                gap_type="negative",
                benchmark_source="Cycle Time Tech 2024 (empresas B2B médio porte)",
                insight="Cycle Time 50% acima do mercado necessitando automação de processos críticos",
                priority="LOW",
            ),
            BenchmarkComparison(
                perspective="Aprendizado e Crescimento",
                metric_name="Retenção",
                company_value="85%",
                benchmark_value="88%",
                gap=3.0,
                gap_type="neutral",
                benchmark_source="Retenção Talentos Tech Brasil 2024 (médio porte)",
                insight="Retenção no mercado mas margem de melhoria com programa estruturado de desenvolvimento e carreira",
                priority="LOW",
            ),
            BenchmarkComparison(
                perspective="Aprendizado e Crescimento",
                metric_name="Treinamento",
                company_value="60h/ano",
                benchmark_value="80h/ano",
                gap=25.0,
                gap_type="negative",
                benchmark_source="Investimento Treinamento Tech 2024 (inovadoras)",
                insight="Treinamento 25% abaixo do mercado limitando desenvolvimento de competências estratégicas",
                priority="MEDIUM",
            ),
        ],
        overall_performance="abaixo_mercado",
        priority_gaps=[
            "Margem EBITDA 7pp abaixo (Financeira) - 30% potencial lucro não realizado",
            "NPS 15 pontos abaixo (Clientes) - churn 20% maior que mercado",
            "Lead Time 40% maior (Processos) - perda 15% oportunidades",
        ],
        recommendations=[
            "Reduzir custos operacionais via automação (meta: +7pp EBITDA)",
            "Implementar Voice of Customer (meta: NPS +15)",
            "Automatizar fulfillment (meta: Lead Time -40%)",
            "Revisar pricing value-based (meta: +3-5pp margem)",
        ],
    )

    # Mock structured LLM (return_value fixo - 1 chamada apenas)
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = mock_report
    llm.with_structured_output.return_value = mock_structured_llm

    return llm


@pytest.fixture
def mock_retriever() -> MagicMock:
    """Mock BSCRetriever para RAG opcional."""
    retriever = MagicMock(spec=["get_relevant_documents"])

    # Mock docs RAG
    mock_doc1 = MagicMock()
    mock_doc1.page_content = (
        "Kaplan & Norton recomendam benchmarking externo para contextualizar "
        "performance BSC. Empresas SaaS B2B médio porte alcançam margens EBITDA 20-30%."
    )

    mock_doc2 = MagicMock()
    mock_doc2.page_content = (
        "Benchmarking competitivo deve considerar setor, porte, região e maturidade. "
        "NPS acima de 50 é considerado excelente em B2B SaaS."
    )

    retriever.get_relevant_documents.return_value = [mock_doc1, mock_doc2]

    return retriever


# ====================================================================================
# TESTES - SCHEMAS PYDANTIC
# ====================================================================================


def test_benchmark_comparison_valid_data(valid_benchmark_comparison):
    """Teste 1: BenchmarkComparison com dados válidos."""
    comp = valid_benchmark_comparison

    assert comp.perspective == "Financeira"
    assert comp.metric_name == "Margem EBITDA"
    assert comp.company_value == "18%"
    assert comp.benchmark_value == "25%"
    assert comp.gap == 7.0
    assert comp.gap_type == "negative"
    assert len(comp.benchmark_source) >= 20  # min_length validator
    assert len(comp.insight) >= 50  # min_length validator
    assert comp.priority == "HIGH"


def test_benchmark_comparison_gap_validator_extreme_positive():
    """Teste 2: BenchmarkComparison com gap extremo positivo (+250%) -> ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        BenchmarkComparison(
            perspective="Financeira",
            metric_name="Margem",
            company_value="10%",
            benchmark_value="35%",
            gap=250.0,  # > 200% -> ValidationError [OK]
            gap_type="negative",
            benchmark_source="Setor Tecnologia SaaS Brasil 2024 (médio porte)",
            insight="Gap extremo irreal indicando possível erro nos dados ou benchmark desatualizado",
            priority="HIGH",
        )

    assert "Gap 250.0% parece irreal" in str(exc_info.value)


def test_benchmark_comparison_gap_validator_extreme_negative():
    """Teste 3: BenchmarkComparison com gap extremo negativo (-150%) -> ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        BenchmarkComparison(
            perspective="Financeira",
            metric_name="Custo",
            company_value="5%",
            benchmark_value="20%",
            gap=-150.0,  # < -100% -> ValidationError [OK]
            gap_type="positive",
            benchmark_source="Benchmark Custos Operacionais Tech 2024",
            insight="Gap extremo irreal indicando possível erro nos dados",
            priority="MEDIUM",
        )

    assert "Gap -150.0% parece irreal" in str(exc_info.value)


def test_benchmark_comparison_gap_type_misalignment():
    """Teste 4: gap_type não alinha com gap numérico -> ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        BenchmarkComparison(
            perspective="Clientes",
            metric_name="NPS",
            company_value="40",
            benchmark_value="60",
            gap=20.0,  # > 5 -> esperado gap_type="negative"
            gap_type="positive",  # ERRADO! [ERRO]
            benchmark_source="NPS B2B SaaS Brasil 2024 (mid-market companies)",
            insight="NPS 20 pontos abaixo do benchmark indicando insatisfação clientes",
            priority="HIGH",
        )

    assert "Gap 20.0% > 5" in str(exc_info.value)
    assert "gap_type='positive'" in str(exc_info.value)
    assert "Esperado: 'negative'" in str(exc_info.value)


def test_benchmark_comparison_source_too_generic():
    """Teste 5: benchmark_source muito genérico (< 40 chars com termo genérico) -> ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        BenchmarkComparison(
            perspective="Financeira",
            metric_name="ROI",
            company_value="12%",
            benchmark_value="18%",
            gap=6.0,
            gap_type="negative",
            benchmark_source="mercado tech empresas médias",  # 30 chars mas termo genérico -> ValidationError [OK]
            insight="ROI 6pp abaixo do benchmark indicando retorno sobre investimento menor",
            priority="MEDIUM",
        )

    assert "benchmark_source 'mercado tech empresas médias' parece muito genérico" in str(
        exc_info.value
    )


def test_benchmark_report_valid_8_comparisons(valid_benchmark_report_8_comparisons):
    """Teste 6: BenchmarkReport válido com 8 comparações balanceadas."""
    report = valid_benchmark_report_8_comparisons

    assert len(report.comparisons) == 8
    assert report.overall_performance == "abaixo_mercado"
    assert len(report.priority_gaps) == 3
    assert len(report.recommendations) == 4

    # Validar balanceamento (2 por perspectiva)
    assert len(report.comparisons_by_perspective("Financeira")) == 2
    assert len(report.comparisons_by_perspective("Clientes")) == 2
    assert len(report.comparisons_by_perspective("Processos Internos")) == 2
    assert len(report.comparisons_by_perspective("Aprendizado e Crescimento")) == 2


def test_benchmark_report_unbalanced_perspectives():
    """Teste 7: BenchmarkReport desbalanceado (6 Financeira, 0 Aprendizado) -> ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        BenchmarkReport(
            comparisons=[
                # 5 comparações Financeira (máximo permitido)
                BenchmarkComparison(
                    perspective="Financeira",
                    metric_name="EBITDA",
                    company_value="18%",
                    benchmark_value="25%",
                    gap=7.0,
                    gap_type="negative",
                    benchmark_source="Setor Tech SaaS Brasil 2024 (médio porte B2B)",
                    insight="Margem EBITDA 7pp abaixo indicando custos operacionais elevados",
                    priority="HIGH",
                ),
                BenchmarkComparison(
                    perspective="Financeira",
                    metric_name="ROI",
                    company_value="15%",
                    benchmark_value="21%",
                    gap=6.0,
                    gap_type="negative",
                    benchmark_source="Benchmark SaaS Global 2024 (B2B médio porte)",
                    insight="ROI 6pp abaixo indicando retorno menor que concorrentes",
                    priority="MEDIUM",
                ),
                BenchmarkComparison(
                    perspective="Financeira",
                    metric_name="CAC",
                    company_value="$500",
                    benchmark_value="$400",
                    gap=25.0,
                    gap_type="negative",
                    benchmark_source="CAC SaaS Brasil 2024 (empresas médio porte B2B)",
                    insight="CAC 25% acima do benchmark setorial indicando custos de aquisição elevados",
                    priority="LOW",
                ),
                BenchmarkComparison(
                    perspective="Financeira",
                    metric_name="LTV",
                    company_value="$5k",
                    benchmark_value="$7k",
                    gap=28.0,
                    gap_type="negative",
                    benchmark_source="LTV SaaS Brasil 2024 (empresas B2B médio porte)",
                    insight="LTV 28% abaixo do mercado indicando necessidade de retenção melhor",
                    priority="MEDIUM",
                ),
                BenchmarkComparison(
                    perspective="Financeira",
                    metric_name="ARR",
                    company_value="$2M",
                    benchmark_value="$3M",
                    gap=33.0,
                    gap_type="negative",
                    benchmark_source="ARR SaaS Brasil 2024 (empresas B2B médio porte)",
                    insight="ARR 33% abaixo do benchmark indicando crescimento de receita menor",
                    priority="LOW",
                ),
                # 2 Clientes
                BenchmarkComparison(
                    perspective="Clientes",
                    metric_name="NPS",
                    company_value="42",
                    benchmark_value="57",
                    gap=15.0,
                    gap_type="negative",
                    benchmark_source="NPS B2B SaaS Brasil 2024 (empresas médio porte B2B)",
                    insight="NPS 15 pontos abaixo do benchmark indicando insatisfação clientes",
                    priority="HIGH",
                ),
                BenchmarkComparison(
                    perspective="Clientes",
                    metric_name="CSAT",
                    company_value="70%",
                    benchmark_value="85%",
                    gap=15.0,
                    gap_type="negative",
                    benchmark_source="CSAT SaaS Brasil 2024 (empresas médio porte)",
                    insight="CSAT abaixo do benchmark setorial indicando satisfação menor",
                    priority="MEDIUM",
                ),
                # 2 Processos
                BenchmarkComparison(
                    perspective="Processos Internos",
                    metric_name="Lead Time",
                    company_value="14d",
                    benchmark_value="10d",
                    gap=40.0,
                    gap_type="negative",
                    benchmark_source="Lead Time SaaS Brasil 2024 (médio porte)",
                    insight="Lead Time alto indicando processos lentos e ineficientes",
                    priority="MEDIUM",
                ),
                BenchmarkComparison(
                    perspective="Processos Internos",
                    metric_name="Cycle Time",
                    company_value="36h",
                    benchmark_value="24h",
                    gap=50.0,
                    gap_type="negative",
                    benchmark_source="Cycle Time Tech 2024 (empresas B2B médio porte)",
                    insight="Cycle Time alto indicando necessidade de automação processos",
                    priority="LOW",
                ),
                # 0 Aprendizado e Crescimento -> ValidationError! [ERRO]
            ],
            overall_performance="abaixo_mercado",
            priority_gaps=["Gap 1", "Gap 2", "Gap 3"],
            recommendations=["Rec 1", "Rec 2", "Rec 3"],
        )

    assert "Perspectiva 'Aprendizado e Crescimento' tem apenas 0 comparação" in str(exc_info.value)
    assert "Mínimo esperado: 2 por perspectiva" in str(exc_info.value)


# ====================================================================================
# TESTES - CONTEXT BUILDERS
# ====================================================================================


def test_build_company_context(valid_company_info):
    """Teste 8: build_company_context formata CompanyInfo corretamente."""
    context = build_company_context(valid_company_info)

    assert "TechCorp Brasil Ltda" in context
    assert "Tecnologia" in context
    assert "média" in context
    assert "Software as a Service" in context
    assert "Brasil" in context
    assert "2018" in context


def test_build_diagnostic_context(valid_diagnostic_four_perspectives):
    """Teste 9: build_diagnostic_context formata 4 perspectivas corretamente."""
    context = build_diagnostic_context(valid_diagnostic_four_perspectives)

    assert "Financeira" in context
    assert "Clientes" in context
    assert "Processos Internos" in context
    assert "Aprendizado e Crescimento" in context
    assert "HIGH" in context  # Priority
    assert "Receita recorrente crescendo" in context  # current_state


def test_build_kpi_context_with_kpis(valid_kpi_framework):
    """Teste 10: build_kpi_context com KPIs lista todos os KPIs."""
    context = build_kpi_context(valid_kpi_framework)

    # KPIDefinition não tem current_value -> context mostra "N/A"
    assert "Margem EBITDA Anual: N/A" in context
    assert "NPS - Net Promoter Score Clientes: N/A" in context
    assert "Lead Time Fulfillment Médio: N/A" in context
    assert "Retenção de Talentos Anual: N/A" in context

    # Verifica estrutura de seções
    assert "### Financeira" in context
    assert "### Clientes" in context
    assert "### Processos Internos" in context
    assert "### Aprendizado e Crescimento" in context


def test_build_kpi_context_without_kpis():
    """Teste 11: build_kpi_context sem KPIs retorna string vazia."""
    context = build_kpi_context(None)

    assert context == ""


# ====================================================================================
# TESTES - BENCHMARKING TOOL
# ====================================================================================


def test_generate_benchmarks_without_rag(
    mock_llm, valid_company_info, valid_diagnostic_four_perspectives
):
    """Teste 12: generate_benchmarks sem RAG (happy path)."""
    tool = BenchmarkingTool(llm=mock_llm, retriever=None)

    report = tool.generate_benchmarks(
        company_info=valid_company_info,
        diagnostic=valid_diagnostic_four_perspectives,
        kpi_framework=None,
        use_rag=False,
    )

    assert isinstance(report, BenchmarkReport)
    assert len(report.comparisons) == 8
    assert report.overall_performance == "abaixo_mercado"
    assert len(report.priority_gaps) == 3
    assert len(report.recommendations) == 4

    # Verificar balanceamento (2 por perspectiva)
    for perspective in [
        "Financeira",
        "Clientes",
        "Processos Internos",
        "Aprendizado e Crescimento",
    ]:
        comps = report.comparisons_by_perspective(perspective)
        assert len(comps) == 2, f"Perspectiva {perspective} deve ter 2 comparações"


def test_generate_benchmarks_with_rag(
    mock_llm, mock_retriever, valid_company_info, valid_diagnostic_four_perspectives
):
    """Teste 13: generate_benchmarks com RAG (contexto adicional)."""
    tool = BenchmarkingTool(llm=mock_llm, retriever=mock_retriever)

    report = tool.generate_benchmarks(
        company_info=valid_company_info,
        diagnostic=valid_diagnostic_four_perspectives,
        kpi_framework=None,
        use_rag=True,
    )

    # Verificar que retriever foi chamado
    mock_retriever.get_relevant_documents.assert_called_once()
    call_args = mock_retriever.get_relevant_documents.call_args
    assert "benchmarking BSC" in call_args[0][0]  # query
    assert call_args[1]["k"] == 10  # top-10

    # Report válido
    assert isinstance(report, BenchmarkReport)
    assert len(report.comparisons) >= 6


def test_generate_benchmarks_with_kpi_framework(
    mock_llm, valid_company_info, valid_diagnostic_four_perspectives, valid_kpi_framework
):
    """Teste 14: generate_benchmarks com KPI Framework (contexto enriquecido)."""
    tool = BenchmarkingTool(llm=mock_llm, retriever=None)

    report = tool.generate_benchmarks(
        company_info=valid_company_info,
        diagnostic=valid_diagnostic_four_perspectives,
        kpi_framework=valid_kpi_framework,
        use_rag=False,
    )

    # KPI context foi incluído no prompt (verificar via mock call)
    assert mock_llm.with_structured_output.called
    structured_llm = mock_llm.with_structured_output.return_value
    assert structured_llm.invoke.called

    prompt_used = structured_llm.invoke.call_args[0][0]
    assert "Margem EBITDA" in prompt_used  # KPI name
    assert "18%" in prompt_used  # current_value


def test_generate_benchmarks_missing_company_info(mock_llm, valid_diagnostic_four_perspectives):
    """Teste 15: generate_benchmarks sem company_info -> ValueError."""
    tool = BenchmarkingTool(llm=mock_llm, retriever=None)

    with pytest.raises(ValueError) as exc_info:
        tool.generate_benchmarks(
            company_info=None,  # None -> ValidationError [OK]
            diagnostic=valid_diagnostic_four_perspectives,
            kpi_framework=None,
            use_rag=False,
        )

    assert "company_info obrigatório" in str(exc_info.value)


def test_generate_benchmarks_incomplete_diagnostic(mock_llm, valid_company_info):
    """Teste 16: generate_benchmarks com diagnostic incompleto (< 4 perspectivas) -> ValueError."""
    tool = BenchmarkingTool(llm=mock_llm, retriever=None)

    # Diagnostic com apenas 2 perspectivas (incompleto)
    incomplete_diagnostic = {
        "Financeira": DiagnosticResult(
            perspective="Financeira",
            current_state="Estado financeiro atual da empresa está em crescimento",
            gaps=["Gap 1"],
            opportunities=["Opp 1"],
            priority="HIGH",
        ),
        "Clientes": DiagnosticResult(
            perspective="Clientes",
            current_state="Base de clientes em expansão mas NPS baixo",
            gaps=["Gap 2"],
            opportunities=["Opp 2"],
            priority="MEDIUM",
        ),
        # Faltam: Processos Internos, Aprendizado e Crescimento
    }

    with pytest.raises(ValueError) as exc_info:
        tool.generate_benchmarks(
            company_info=valid_company_info,
            diagnostic=incomplete_diagnostic,
            kpi_framework=None,
            use_rag=False,
        )

    assert "Diagnóstico BSC incompleto" in str(exc_info.value)
    assert "Processos Internos" in str(exc_info.value) or "Aprendizado" in str(exc_info.value)
