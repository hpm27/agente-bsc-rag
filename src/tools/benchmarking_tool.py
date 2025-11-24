"""Benchmarking Tool - Comparação com Benchmarks Externos BSC.

Esta tool compara o desempenho atual da empresa com benchmarks externos relevantes
(setor, porte, região) nas 4 perspectivas do Balanced Scorecard, identificando gaps
e oportunidades de melhoria através de análise competitiva estruturada.

Features:
- Comparação estruturada por perspectiva BSC (Financeira, Clientes, Processos, Aprendizado)
- Benchmarks de fontes específicas (setor + porte + região + ano)
- Identificação de gaps (positive/negative/neutral)
- Priorização de gaps críticos (HIGH/MEDIUM/LOW)
- Recomendações estratégicas de alto nível
- RAG opcional para contexto da literatura BSC
- Validators Pydantic para garantir qualidade

Quando usar:
- Após diagnóstico BSC completo (4 perspectivas)
- Objetivos estratégicos definidos (opcional)
- KPIs definidos (opcional mas recomendado)
- Empresa precisa contexto externo (vs mercado/setor)

Sessão: 21 (FASE 3.6 - Benchmarking Tool)
Autor: BSC RAG System
Data: 2025-10-19
"""

import logging
from typing import cast

from config.settings import settings
from langchain_core.language_models import BaseLLM
from pydantic import ValidationError

from src.memory.schemas import BenchmarkReport, CompanyInfo, DiagnosticResult, KPIFramework
from src.prompts.benchmarking_prompts import format_benchmarking_prompt
from src.rag.retriever import BSCRetriever

logger = logging.getLogger(__name__)


class BenchmarkingTool:
    """Tool para geração de relatórios de benchmarking BSC.

    Compara desempenho atual da empresa com benchmarks externos relevantes
    nas 4 perspectivas BSC, usando LLM structured output para garantir qualidade.

    Attributes:
        llm: Language model para generation (GPT-5 ou Claude Sonnet)
        retriever: BSC retriever para RAG opcional (None se RAG desabilitado)
        max_retries: Número máximo de tentativas em caso de ValidationError

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> from src.rag.retriever import BSCRetriever
        >>>
        >>> llm = ChatOpenAI(model="gpt-5-2025-08-07")
        >>> retriever = BSCRetriever(search_type="hybrid")
        >>> tool = BenchmarkingTool(llm=llm, retriever=retriever)
        >>>
        >>> report = tool.generate_benchmarks(
        ...     company_info=company,
        ...     diagnostic=diagnostic,
        ...     kpi_framework=kpi_framework,
        ...     use_rag=True
        ... )
        >>> print(report.summary())
    """

    def __init__(self, llm: BaseLLM, retriever: BSCRetriever | None = None, max_retries: int = 3):
        """Inicializa BenchmarkingTool.

        Args:
            llm: Language model para generation
            retriever: BSC retriever para RAG opcional (None se RAG desabilitado)
            max_retries: Número máximo de tentativas em caso de ValidationError
        """
        self.llm = llm
        self.retriever = retriever
        self.max_retries = max_retries

        # Structured output LLM
        self.structured_llm = self.llm.with_structured_output(BenchmarkReport)

        logger.info("[BenchmarkingTool] Inicializado (RAG: %s)", retriever is not None)

    def generate_benchmarks(
        self,
        company_info: CompanyInfo,
        diagnostic: dict[str, DiagnosticResult],
        kpi_framework: KPIFramework | None = None,
        use_rag: bool = False,
    ) -> BenchmarkReport:
        """Gera relatório de benchmarking BSC completo.

        Workflow:
        1. Validações pré-flight (company_info, diagnostic completo)
        2. Retrieval RAG opcional (contexto literatura BSC)
        3. Build prompt completo (company + diagnostic + kpi + rag)
        4. LLM structured output (BenchmarkReport com validators)
        5. Validações pós-generation (balanceamento, gaps realistas)

        Args:
            company_info: Informações básicas da empresa (setor, porte, região)
            diagnostic: Diagnóstico BSC das 4 perspectivas (dict com keys: Financeira, Clientes, Processos Internos, Aprendizado e Crescimento)
            kpi_framework: KPIs existentes com valores atuais (opcional)
            use_rag: Se True, busca contexto na literatura BSC (default: False)

        Returns:
            BenchmarkReport com 6-20 comparações balanceadas, gaps identificados, recomendações

        Raises:
            ValueError: Se company_info None ou diagnostic incompleto (< 4 perspectivas)
            ValidationError: Se LLM gerar BenchmarkReport inválido (após max_retries tentativas)

        Example:
            >>> report = tool.generate_benchmarks(
            ...     company_info=CompanyInfo(name="TechCorp", sector="Tecnologia", size="média"),
            ...     diagnostic={
            ...         "Financeira": DiagnosticResult(...),
            ...         "Clientes": DiagnosticResult(...),
            ...         "Processos Internos": DiagnosticResult(...),
            ...         "Aprendizado e Crescimento": DiagnosticResult(...)
            ...     },
            ...     kpi_framework=None,
            ...     use_rag=False
            ... )
            >>> print(f"Comparações: {len(report.comparisons)}")
            >>> print(f"Performance: {report.overall_performance}")
        """
        # ========== VALIDAÇÕES PRÉ-FLIGHT ==========

        if company_info is None:
            raise ValueError("company_info obrigatório para benchmarking")

        logger.info(
            "[BenchmarkingTool] Gerando benchmarks (empresa: %s, RAG: %s)",
            company_info.name,
            use_rag,
        )

        if diagnostic is None or len(diagnostic) == 0:
            raise ValueError(
                "diagnostic obrigatório para benchmarking. " "Execute diagnóstico BSC primeiro."
            )

        # Validar que diagnostic tem 4 perspectivas BSC
        expected_perspectives = [
            "Financeira",
            "Clientes",
            "Processos Internos",
            "Aprendizado e Crescimento",
        ]
        missing_perspectives = [p for p in expected_perspectives if p not in diagnostic]

        if missing_perspectives:
            raise ValueError(
                f"Diagnóstico BSC incompleto. Faltam perspectivas: {missing_perspectives}. "
                f"Benchmarking requer 4 perspectivas para comparação equilibrada."
            )

        logger.debug(
            "[BenchmarkingTool] Validações OK (setor: %s, porte: %s, 4 perspectivas)",
            company_info.sector,
            company_info.size,
        )

        # ========== RETRIEVAL RAG OPCIONAL ==========

        rag_docs = None
        rag_query = None

        if use_rag and self.retriever is not None:
            logger.info("[BenchmarkingTool] Retrieving RAG context...")

            # Query RAG para benchmarks BSC setoriais
            rag_query = f"benchmarking BSC {company_info.sector} {company_info.size} best practices external metrics"

            try:
                # Retrieval (configurável via .env: TOP_K_RETRIEVAL)
                retrieved_results = self.retriever.get_relevant_documents(
                    rag_query, k=settings.top_k_retrieval
                )
                rag_docs = [doc.page_content for doc in retrieved_results]

                logger.info("[BenchmarkingTool] RAG context retrieved (%d docs)", len(rag_docs))
            except Exception as e:
                logger.warning(
                    "[BenchmarkingTool] RAG retrieval falhou (%s). Continuando sem RAG.", str(e)
                )
                rag_docs = None

        # ========== BUILD PROMPT ==========

        prompt = format_benchmarking_prompt(
            company_info=company_info,
            diagnostic=diagnostic,
            kpi_framework=kpi_framework,
            rag_docs=rag_docs,
            rag_query=rag_query,
        )

        logger.debug(
            "[BenchmarkingTool] Prompt formatado (~%d chars, RAG docs: %s)",
            len(prompt),
            len(rag_docs) if rag_docs else 0,
        )

        # ========== LLM STRUCTURED OUTPUT (com retries) ==========

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "[BenchmarkingTool] Invoking LLM (attempt %d/%d)...", attempt, self.max_retries
                )

                # LLM structured output com BenchmarkReport schema
                result = self.structured_llm.invoke(prompt)

                # Type cast (structured output garante BenchmarkReport)
                report = cast(BenchmarkReport, result)

                logger.info(
                    "[BenchmarkingTool] BenchmarkReport gerado OK (%d comparações, performance: %s)",
                    len(report.comparisons),
                    report.overall_performance,
                )

                # ========== VALIDAÇÕES PÓS-GENERATION ==========

                self._validate_report_quality(report, company_info)

                return report

            except ValidationError as e:
                logger.error(
                    "[BenchmarkingTool] ValidationError (attempt %d/%d): %s",
                    attempt,
                    self.max_retries,
                    str(e),
                )

                if attempt == self.max_retries:
                    # Última tentativa falhou - relançar erro
                    logger.error(
                        "[BenchmarkingTool] Falha após %d tentativas. Validators Pydantic não satisfeitos.",
                        self.max_retries,
                    )
                    raise

                # Tentar novamente
                logger.info("[BenchmarkingTool] Retrying...")

        # Fallback (não deveria chegar aqui)
        raise RuntimeError("BenchmarkingTool: max_retries alcançado sem resultado válido")

    def _validate_report_quality(self, report: BenchmarkReport, company_info: CompanyInfo) -> None:
        """Valida qualidade do report gerado (além de validators Pydantic).

        Validações adicionais:
        - Comparisons estão balanceadas (2-5 por perspectiva) - já validado por model_validator
        - Gaps estão em range realista (-100% a +200%) - já validado por field_validator
        - Benchmark sources específicas (min 20 chars) - já validado por field_validator
        - Priority gaps específicos (min 30 chars) - já validado por model_validator

        Warnings (não bloqueiam):
        - Todos gaps positivos OU todos negativos (possível viés)
        - Número de comparações muito baixo (< 8) ou muito alto (> 16)

        Args:
            report: BenchmarkReport gerado pelo LLM
            company_info: Informações da empresa (para contexto nos logs)

        Raises:
            Nenhuma (validações críticas já feitas por Pydantic)

        Side effects:
            Logs warnings se detectar padrões suspeitos
        """
        # Validação 1: Viés em gaps (todos positivos OU todos negativos)
        positive_gaps = [c for c in report.comparisons if c.gap_type == "positive"]
        negative_gaps = [c for c in report.comparisons if c.gap_type == "negative"]

        if len(positive_gaps) == len(report.comparisons):
            logger.warning(
                "[BenchmarkingTool] TODOS gaps são positivos (empresa acima de todos benchmarks). "
                "Possível viés ou benchmarks desatualizados. Revisar manualmente."
            )
        elif len(negative_gaps) == len(report.comparisons):
            logger.warning(
                "[BenchmarkingTool] TODOS gaps são negativos (empresa abaixo de todos benchmarks). "
                "Possível viés ou empresa em situação crítica. Revisar manualmente."
            )

        # Validação 2: Número de comparações
        num_comps = len(report.comparisons)
        if num_comps < 8:
            logger.warning(
                "[BenchmarkingTool] Apenas %d comparações (recomendado: 8-16). "
                "Considerar mais métricas para análise abrangente.",
                num_comps,
            )
        elif num_comps > 16:
            logger.info(
                "[BenchmarkingTool] %d comparações (acima de 16). "
                "Report completo mas pode ser denso para apresentação executiva.",
                num_comps,
            )

        # Validação 3: Distribuição de prioridades
        high_priority = len(report.high_priority_comparisons())
        if high_priority == 0:
            logger.warning(
                "[BenchmarkingTool] ZERO comparações com prioridade HIGH. "
                "Revisar se gaps críticos foram identificados corretamente."
            )
        elif high_priority > 8:
            logger.warning(
                "[BenchmarkingTool] %d comparações com prioridade HIGH (> 8). "
                "Muitos gaps críticos podem indicar falta de priorização.",
                high_priority,
            )

        logger.info(
            "[BenchmarkingTool] Report quality validated (warnings: %s)",
            (
                "none"
                if len(positive_gaps) != len(report.comparisons)
                and len(negative_gaps) != len(report.comparisons)
                else "viés detectado"
            ),
        )
