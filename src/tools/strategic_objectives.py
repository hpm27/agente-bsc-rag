"""Tool para definicao de objetivos estrategicos SMART alinhados com BSC.

Este modulo implementa StrategicObjectivesTool, uma ferramenta especializada
em facilitar a definicao de objetivos estrategicos de longo prazo para empresas,
alinhados com as 4 perspectivas do Balanced Scorecard (BSC).
"""

import logging

from langchain_core.language_models import BaseLLM

from src.memory.schemas import (
    CompanyInfo,
    CompleteDiagnostic,
    KPIFramework,
    StrategicObjective,
    StrategicObjectivesFramework,
)
from src.prompts.strategic_objectives_prompts import (
    FACILITATE_OBJECTIVES_DEFINITION_PROMPT,
    VALIDATE_OBJECTIVES_BALANCE_PROMPT,
    build_company_context,
    build_complete_diagnostic_context,
    build_diagnostic_context,
    build_kpi_context,
    build_kpi_linkage_instruction,
)

logger = logging.getLogger(__name__)


class StrategicObjectivesTool:
    """Tool para definicao de objetivos estrategicos BSC.

    Facilita a definicao de 2-5 objetivos estrategicos SMART por perspectiva BSC,
    alinhados com o diagnostico realizado e vinculados opcionalmente com KPIs
    existentes.

    Attributes:
        llm: Modelo de linguagem para geração de objetivos
        use_rag: Se True, integra com RAG agents BSC para contexto adicional
        rag_agents: Tupla opcional de (financial, customer, process, learning) agents

    Methods:
        define_objectives: Define objetivos estrategicos para todas as 4 perspectivas BSC

    Example:
        >>> tool = StrategicObjectivesTool(llm=llm, use_rag=False)
        >>> framework = tool.define_objectives(
        ...     company_info=company_info,
        ...     strategic_context="Escalar operacoes mantendo qualidade",
        ...     diagnostic_result=diagnostic_result,
        ...     existing_kpis=kpi_framework  # opcional
        ... )
        >>> print(framework.total_objectives())
        12  # 3 + 2 + 4 + 3
    """

    def __init__(self, llm: BaseLLM, use_rag: bool = False, rag_agents: tuple | None = None):
        """Inicializa StrategicObjectivesTool.

        Args:
            llm: Modelo de linguagem (GPT-4o-mini recomendado para custo-efetividade)
            use_rag: Se True, integra com RAG agents BSC specialists
            rag_agents: Tupla (financial, customer, process, learning) agents (opcional)

        Raises:
            ValueError: Se use_rag=True mas rag_agents nao fornecido
        """
        self.llm = llm
        self.use_rag = use_rag
        self.rag_agents = rag_agents

        if use_rag and not rag_agents:
            raise ValueError(
                "rag_agents obrigatorio quando use_rag=True. "
                "Fornecer tupla (financial_agent, customer_agent, process_agent, learning_agent)"
            )

        logger.info(
            "[StrategicObjectivesTool] Inicializada "
            f"(use_rag={use_rag}, rag_agents={'configurados' if rag_agents else 'nao configurados'})"
        )

    def define_objectives(
        self,
        company_info: CompanyInfo,
        strategic_context: str,
        diagnostic_result: "CompleteDiagnostic",
        existing_kpis: KPIFramework | None = None,
    ) -> StrategicObjectivesFramework:
        """Define objetivos estrategicos SMART para as 4 perspectivas BSC.

        Workflow:
        1. Valida inputs obrigatorios
        2. Para cada perspectiva BSC:
           a. Busca conhecimento BSC via RAG (se use_rag=True)
           b. Monta prompt com contexto completo
           c. Chama LLM com structured output
           d. Retorna 2-5 objetivos SMART
        3. Agrega objetivos das 4 perspectivas em StrategicObjectivesFramework
        4. Valida balanceamento e alinhamento com diagnostico
        5. Retorna framework completo

        Args:
            company_info: Informacoes basicas da empresa (obrigatorio)
            strategic_context: Contexto estrategico de alto nivel (obrigatorio)
            diagnostic_result: Resultado do diagnostico BSC (obrigatorio)
            existing_kpis: Framework de KPIs existente para vinculacao (opcional)

        Returns:
            StrategicObjectivesFramework: Framework completo com objetivos das 4 perspectivas

        Raises:
            ValueError: Se inputs obrigatorios invalidos
            RuntimeError: Se LLM falha ao gerar objetivos

        Example:
            >>> tool = StrategicObjectivesTool(llm=llm)
            >>> framework = tool.define_objectives(
            ...     company_info=company_info,
            ...     strategic_context="Escalar operacoes mantendo qualidade",
            ...     diagnostic_result=diagnostic_result
            ... )
            >>> print(framework.summary())
            Framework BSC com 12 objetivos estrategicos distribuidos:
            ...
        """
        # Validar inputs
        self._validate_inputs(company_info, strategic_context, diagnostic_result)

        logger.info(
            f"[StrategicObjectivesTool] Definindo objetivos estrategicos para {company_info.name} "
            f"(use_rag={self.use_rag}, com_kpis={existing_kpis is not None})"
        )

        # Definir objetivos por perspectiva
        perspectives = ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]

        financial_objectives = self._define_perspective_objectives(
            perspective=perspectives[0],
            company_info=company_info,
            strategic_context=strategic_context,
            diagnostic_result=diagnostic_result,
            existing_kpis=existing_kpis,
        )

        customer_objectives = self._define_perspective_objectives(
            perspective=perspectives[1],
            company_info=company_info,
            strategic_context=strategic_context,
            diagnostic_result=diagnostic_result,
            existing_kpis=existing_kpis,
        )

        process_objectives = self._define_perspective_objectives(
            perspective=perspectives[2],
            company_info=company_info,
            strategic_context=strategic_context,
            diagnostic_result=diagnostic_result,
            existing_kpis=existing_kpis,
        )

        learning_objectives = self._define_perspective_objectives(
            perspective=perspectives[3],
            company_info=company_info,
            strategic_context=strategic_context,
            diagnostic_result=diagnostic_result,
            existing_kpis=existing_kpis,
        )

        # Agregar em framework
        framework = StrategicObjectivesFramework(
            financial_objectives=financial_objectives,
            customer_objectives=customer_objectives,
            process_objectives=process_objectives,
            learning_objectives=learning_objectives,
            company_context=f"{company_info.name} - {strategic_context}",
        )

        logger.info(
            f"[StrategicObjectivesTool] Framework criado com {framework.total_objectives()} objetivos "
            f"(F:{len(financial_objectives)}, C:{len(customer_objectives)}, "
            f"P:{len(process_objectives)}, A:{len(learning_objectives)})"
        )

        # Validar balanceamento (log warning se desbalanceado, mas nao bloqueia)
        validation_result = self._validate_objectives_balance(
            framework=framework, company_info=company_info, diagnostic_result=diagnostic_result
        )

        if not validation_result.get("is_balanced"):
            logger.warning(
                f"[StrategicObjectivesTool] Framework desbalanceado: "
                f"{validation_result.get('balance_analysis')}"
            )
            logger.warning(
                f"[StrategicObjectivesTool] Recomendacoes: "
                f"{validation_result.get('recommendations')}"
            )
        else:
            logger.info(
                f"[StrategicObjectivesTool] Framework balanceado: "
                f"{validation_result.get('balance_analysis')} "
                f"(quality: {validation_result.get('overall_quality')})"
            )

        return framework

    def _define_perspective_objectives(
        self,
        perspective: str,
        company_info: CompanyInfo,
        strategic_context: str,
        diagnostic_result: "CompleteDiagnostic",
        existing_kpis: KPIFramework | None = None,
    ) -> list[StrategicObjective]:
        """Define objetivos SMART para uma perspectiva BSC especifica.

        Args:
            perspective: Nome da perspectiva BSC
            company_info: Informacoes da empresa
            strategic_context: Contexto estrategico
            diagnostic_result: Resultado completo do diagnostico (CompleteDiagnostic)
            existing_kpis: KPIs existentes (opcional)

        Returns:
            list[StrategicObjective]: Lista de 2-5 objetivos definidos

        Raises:
            RuntimeError: Se LLM falha ao gerar objetivos
        """
        logger.info(
            f"[StrategicObjectivesTool] Definindo objetivos para perspectiva: {perspective}"
        )

        # Extrair DiagnosticResult da perspectiva especifica
        perspective_mapping = {
            "Financeira": diagnostic_result.financial,
            "Clientes": diagnostic_result.customer,
            "Processos Internos": diagnostic_result.process,
            "Aprendizado e Crescimento": diagnostic_result.learning,
        }
        perspective_diagnostic = perspective_mapping.get(perspective)
        if not perspective_diagnostic:
            raise ValueError(f"Perspectiva invalida: {perspective}")

        # Buscar conhecimento BSC via RAG (se habilitado)
        rag_knowledge = ""
        if self.use_rag and self.rag_agents:
            rag_knowledge = self._retrieve_bsc_knowledge(
                perspective=perspective, strategic_context=strategic_context
            )

        # Montar contexto completo
        company_context = build_company_context(company_info)
        diagnostic_context = build_diagnostic_context(perspective_diagnostic)
        kpi_context = build_kpi_context(existing_kpis)
        kpi_linkage = build_kpi_linkage_instruction(existing_kpis)

        # Montar prompt
        prompt = FACILITATE_OBJECTIVES_DEFINITION_PROMPT.format(
            company_context=company_context,
            perspective=perspective,
            diagnostic_context=diagnostic_context,
            kpi_context=kpi_context if kpi_context else "Nenhum KPI definido ainda.",
            kpi_linkage_instruction=kpi_linkage,
        )

        if rag_knowledge:
            prompt += f"\n\nCONHECIMENTO BSC ADICIONAL:\n{rag_knowledge}"

        # Chamar LLM com structured output
        try:
            # Definir output schema como lista de StrategicObjective
            structured_llm = self.llm.with_structured_output(
                schema={
                    "type": "object",
                    "properties": {
                        "objectives": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "perspective": {"type": "string"},
                                    "timeframe": {"type": "string"},
                                    "success_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "related_kpis": {"type": "array", "items": {"type": "string"}},
                                    "priority": {"type": "string"},
                                    "dependencies": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": [
                                    "name",
                                    "description",
                                    "perspective",
                                    "timeframe",
                                    "success_criteria",
                                ],
                            },
                            "minItems": 2,
                            "maxItems": 5,
                        }
                    },
                    "required": ["objectives"],
                }
            )

            result = structured_llm.invoke(prompt)

            # Extrair objetivos do resultado (result pode ser dict ou Pydantic model)
            objectives_data = (
                result["objectives"] if isinstance(result, dict) else result.objectives
            )

            # Converter para StrategicObjective Pydantic
            objectives = []
            for obj_item in objectives_data:
                # Converter para dict se necessario
                obj_dict = (
                    obj_item
                    if isinstance(obj_item, dict)
                    else obj_item.dict() if hasattr(obj_item, "dict") else dict(obj_item)
                )

                # Garantir que perspective esta correta (override se LLM errar)
                obj_dict["perspective"] = perspective
                obj = StrategicObjective(**obj_dict)
                objectives.append(obj)

            logger.info(
                f"[StrategicObjectivesTool] {len(objectives)} objetivos definidos para {perspective}"
            )

            return objectives

        except Exception as e:
            logger.error(
                f"[StrategicObjectivesTool] Erro ao gerar objetivos para {perspective}: {e}"
            )
            raise RuntimeError(
                f"Falha ao gerar objetivos para perspectiva {perspective}: {e!s}"
            ) from e

    def _retrieve_bsc_knowledge(self, perspective: str, strategic_context: str) -> str:
        """Busca conhecimento BSC via RAG specialists para enriquecer definicao de objetivos.

        Args:
            perspective: Perspectiva BSC
            strategic_context: Contexto estrategico

        Returns:
            str: Conhecimento BSC relevante (vazio se RAG desabilitado)
        """
        if not self.use_rag or not self.rag_agents:
            return ""

        logger.info(f"[StrategicObjectivesTool] Buscando conhecimento BSC para {perspective}")

        # Mapear perspectiva para agent index
        perspective_map = {
            "Financeira": 0,
            "Clientes": 1,
            "Processos Internos": 2,
            "Aprendizado e Crescimento": 3,
        }

        agent_index = perspective_map.get(perspective, 0)
        specialist_agent = self.rag_agents[agent_index]

        # Buscar conhecimento
        query = (
            f"Quais sao os principais objetivos estrategicos da perspectiva {perspective} "
            f"do Balanced Scorecard considerando o contexto: {strategic_context}"
        )

        try:
            result = specialist_agent.invoke(query)
            knowledge = result.get("output", "")

            # Limitar a 500 caracteres para nao estourar contexto LLM
            if len(knowledge) > 500:
                knowledge = knowledge[:500] + "..."

            logger.info(
                f"[StrategicObjectivesTool] Conhecimento recuperado "
                f"({len(knowledge)} chars) para {perspective}"
            )

            return knowledge

        except Exception as e:
            logger.warning(
                f"[StrategicObjectivesTool] Erro ao buscar conhecimento RAG para {perspective}: {e}. "
                "Prosseguindo sem RAG."
            )
            return ""

    def _validate_objectives_balance(
        self,
        framework: StrategicObjectivesFramework,
        company_info: CompanyInfo,
        diagnostic_result: CompleteDiagnostic,
    ) -> dict:
        """Valida balanceamento e alinhamento do framework de objetivos.

        Args:
            framework: Framework completo de objetivos
            company_info: Informacoes da empresa
            diagnostic_result: Diagnostico completo das 4 perspectivas

        Returns:
            dict: Resultado da validacao com campos:
                - is_balanced: bool
                - balance_analysis: str
                - alignment_score: float
                - alignment_analysis: str
                - consistency_issues: List[str]
                - recommendations: List[str]
                - overall_quality: str
        """
        logger.info("[StrategicObjectivesTool] Validando balanceamento do framework")

        # Montar contexto
        company_context = build_company_context(company_info)
        diagnostic_context = build_complete_diagnostic_context(diagnostic_result)
        objectives_summary = framework.summary()

        # Montar prompt
        prompt = VALIDATE_OBJECTIVES_BALANCE_PROMPT.format(
            company_context=company_context,
            diagnostic_context=diagnostic_context,
            objectives_summary=objectives_summary,
        )

        try:
            # Chamar LLM com structured output
            structured_llm = self.llm.with_structured_output(
                schema={
                    "type": "object",
                    "properties": {
                        "is_balanced": {"type": "boolean"},
                        "balance_analysis": {"type": "string"},
                        "alignment_score": {"type": "number"},
                        "alignment_analysis": {"type": "string"},
                        "consistency_issues": {"type": "array", "items": {"type": "string"}},
                        "recommendations": {"type": "array", "items": {"type": "string"}},
                        "overall_quality": {"type": "string"},
                    },
                    "required": [
                        "is_balanced",
                        "balance_analysis",
                        "alignment_score",
                        "alignment_analysis",
                        "overall_quality",
                    ],
                }
            )

            result = structured_llm.invoke(prompt)

            logger.info(
                f"[StrategicObjectivesTool] Validacao completa: "
                f"balanceado={result.get('is_balanced')}, "
                f"quality={result.get('overall_quality')}"
            )

            return result

        except Exception as e:
            logger.warning(
                f"[StrategicObjectivesTool] Erro ao validar balanceamento: {e}. "
                "Retornando validacao default (assumir OK)."
            )
            return {
                "is_balanced": True,
                "balance_analysis": "Validacao nao disponivel",
                "alignment_score": 0.8,
                "alignment_analysis": "Validacao nao disponivel",
                "consistency_issues": [],
                "recommendations": [],
                "overall_quality": "Nao validado",
            }

    def _validate_inputs(
        self,
        company_info: CompanyInfo,
        strategic_context: str,
        diagnostic_result: CompleteDiagnostic,
    ) -> None:
        """Valida inputs obrigatorios.

        Args:
            company_info: Informacoes da empresa
            strategic_context: Contexto estrategico
            diagnostic_result: Resultado completo do diagnostico

        Raises:
            ValueError: Se algum input obrigatorio invalido
        """
        if not company_info:
            raise ValueError("company_info obrigatorio")

        if not strategic_context or not strategic_context.strip():
            raise ValueError("strategic_context obrigatorio e nao pode ser vazio")

        if not diagnostic_result:
            raise ValueError("diagnostic_result obrigatorio")
