"""Action Plan Tool - Ferramenta consultiva estruturada.

Esta tool facilita criação de planos de ação contextualizados usando:
- ClientProfile do onboarding
- Conhecimento BSC via RAG (specialist agents)
- LLM structured output (Pydantic)
- Optional refinement via diagnostic results

Architecture Pattern: Tool -> Prompt -> LLM + RAG -> Structured Output -> Validation

References:
- 7 Best Practices for Action Planning (SME Strategy 2025)
- Balanced Scorecard Implementation Guide (Mooncamp 2025)
- Strategic Planning Tools Comprehensive List (Spider Strategies 2024)

Created: 2025-10-27 (FASE 3.11)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseLLM
from pydantic import ValidationError

from src.memory.schemas import ActionItem, ActionPlan
from src.prompts.action_plan_prompts import (
    FACILITATE_ACTION_PLAN_PROMPT,
    SYNTHESIZE_ACTION_PLAN_PROMPT,
    build_company_context,
    build_diagnostic_context,
    format_action_plan_for_display,
)

if TYPE_CHECKING:
    from src.agents.customer_agent import CustomerAgent
    from src.agents.financial_agent import FinancialAgent
    from src.agents.learning_agent import LearningAgent
    from src.agents.process_agent import ProcessAgent
    from src.memory.schemas import CompleteDiagnostic

logger = logging.getLogger(__name__)


class ActionPlanTool:
    """Ferramenta para facilitar criação de planos de ação estruturados com contexto BSC.

    Esta tool combina:
    1. Contexto da empresa (ClientProfile)
    2. Conhecimento BSC da literatura (via RAG specialist agents)
    3. Resultados de diagnóstico BSC (opcional)
    4. LLM structured output para gerar ActionPlan

    Segue 7 Best Practices para Action Planning (SME Strategy 2025):
    1. Align actions with goals
    2. Prioritize based on importance and time sensitivity
    3. Be specific rather than general
    4. Set deadlines & assign owners
    5. Ask for volunteers or delegate tasks
    6. Develop action plan for implementation
    7. Track and monitor progress

    Example:
        >>> tool = ActionPlanTool(llm=get_llm())
        >>> action_plan = await tool.facilitate(
        ...     client_profile=profile,
        ...     financial_agent=financial_agent,
        ...     customer_agent=customer_agent,
        ...     process_agent=process_agent,
        ...     learning_agent=learning_agent,
        ...     diagnostic_results=diagnostic
        ... )
        >>> print(f"Plano criado com {action_plan.total_actions} ações")
    """

    def __init__(self, llm: BaseLLM):
        """Inicializa ActionPlanTool.

        Args:
            llm: Language model para structured output (GPT-5 mini recomendado)
        """
        self.llm = llm

        # Log para identificar temperatura do LLM
        if hasattr(llm, "temperature"):
            logger.info(f"[ActionPlanTool] LLM temperatura: {llm.temperature}")
        else:
            logger.warning("[ActionPlanTool] LLM não tem atributo 'temperature'")

        # Log para identificar modelo do LLM
        if hasattr(llm, "model"):
            logger.info(f"[ActionPlanTool] LLM modelo: {llm.model}")
        elif hasattr(llm, "model_name"):
            logger.info(f"[ActionPlanTool] LLM modelo: {llm.model_name}")
        else:
            logger.info("[ActionPlanTool] LLM tipo: %s", type(llm).__name__)

        self.structured_llm = llm.with_structured_output(ActionPlan)
        logger.info("ActionPlanTool inicializada com LLM structured output")

    async def facilitate(
        self,
        client_profile,
        financial_agent: FinancialAgent | None = None,
        customer_agent: CustomerAgent | None = None,
        process_agent: ProcessAgent | None = None,
        learning_agent: LearningAgent | None = None,
        diagnostic_results: CompleteDiagnostic | None = None,
        max_retries: int = 3,
    ) -> ActionPlan:
        """Facilita criação de plano de ação estruturado.

        Args:
            client_profile: ClientProfile com contexto da empresa
            financial_agent: Agent especialista em perspectiva financeira
            customer_agent: Agent especialista em perspectiva clientes
            process_agent: Agent especialista em perspectiva processos
            learning_agent: Agent especialista em perspectiva aprendizado
            diagnostic_results: Resultados de diagnóstico BSC (opcional)
            max_retries: Número máximo de tentativas em caso de erro

        Returns:
            ActionPlan estruturado com ações específicas e acionáveis

        Raises:
            ValidationError: Se LLM retornar dados inválidos após max_retries
            Exception: Se ocorrer erro durante execução

        Example:
            >>> action_plan = await tool.facilitate(
            ...     client_profile=profile,
            ...     financial_agent=financial_agent,
            ...     diagnostic_results=diagnostic
            ... )
            >>> print(f"Plano criado: {action_plan.summary}")
        """
        try:
            logger.info("Iniciando facilitação de Action Plan")

            # 1. Construir contexto da empresa
            company_context = build_company_context(client_profile)
            logger.debug(f"Contexto empresa: {company_context[:100]}...")

            # 2. Construir contexto do diagnóstico (se disponível)
            diagnostic_context = build_diagnostic_context(diagnostic_results)
            logger.debug(f"Contexto diagnóstico: {diagnostic_context[:100]}...")

            # 3. Construir conhecimento BSC via RAG (se agents disponíveis)
            bsc_knowledge = await self._build_bsc_knowledge_context(
                financial_agent, customer_agent, process_agent, learning_agent
            )
            logger.debug(f"Conhecimento BSC: {len(bsc_knowledge)} caracteres")

            # 4. Obter data atual formatada (referência temporal)
            # CRÍTICO: Capturar datetime.now() UMA VEZ para garantir consistência
            # Se executar próximo à meia-noite/mudança de mês, múltiplas chamadas
            # podem retornar datas diferentes causando inconsistência no contexto
            now = datetime.now()
            current_date_str = now.strftime("%Y-%m-%d")
            current_date_display = now.strftime("%d/%m/%Y")
            current_date_context = (
                f"Data atual: {current_date_display} ({current_date_str})\n"
                f"Dia da semana: {now.strftime('%A')}\n"
                f"Mês atual: {now.strftime('%B %Y')}"
            )

            # 5. Construir prompt final
            prompt = FACILITATE_ACTION_PLAN_PROMPT.format(
                current_date=current_date_context,
                company_context=company_context,
                diagnostic_context=diagnostic_context,
                bsc_knowledge=bsc_knowledge,
            )

            logger.info(
                f"Prompt construído: {len(prompt)} caracteres | "
                f"Data atual de referência: {current_date_display}"
            )

            # 6. Chamar LLM com retry logic
            action_plan = await self._call_llm_with_retry(prompt, max_retries=max_retries)

            # 6. Validar qualidade do plano
            self._validate_action_plan(action_plan)

            logger.info(f"Action Plan criado com sucesso: {action_plan.total_actions} ações")
            return action_plan

        except Exception as e:
            logger.error(f"Erro na facilitação de Action Plan: {e}")
            raise

    async def synthesize(
        self, individual_actions: list[ActionItem], client_profile, max_retries: int = 3
    ) -> ActionPlan:
        """Consolida ações individuais em plano estruturado.

        Args:
            individual_actions: Lista de ActionItem para consolidar
            client_profile: ClientProfile com contexto da empresa
            max_retries: Número máximo de tentativas em caso de erro

        Returns:
            ActionPlan consolidado com summary e timeline

        Raises:
            ValidationError: Se LLM retornar dados inválidos após max_retries
            Exception: Se ocorrer erro durante consolidação
        """
        try:
            logger.info(f"Iniciando síntese de {len(individual_actions)} ações")

            # Construir contexto
            company_context = build_company_context(client_profile)

            # Construir prompt de síntese
            actions_text = "\n".join(
                [
                    f"- {action.action_title} ({action.perspective}, {action.priority})"
                    for action in individual_actions
                ]
            )

            prompt = SYNTHESIZE_ACTION_PLAN_PROMPT.format(
                individual_actions=actions_text, company_context=company_context
            )

            logger.info(f"Prompt de síntese construído: {len(prompt)} caracteres")

            # Chamar LLM com retry logic
            action_plan = await self._call_llm_with_retry(prompt, max_retries=max_retries)

            # Validar qualidade do plano consolidado
            self._validate_action_plan(action_plan)

            logger.info(f"Action Plan consolidado com sucesso: {action_plan.total_actions} ações")
            return action_plan

        except Exception as e:
            logger.error(f"Erro na síntese de Action Plan: {e}")
            raise

    async def _build_bsc_knowledge_context(
        self,
        financial_agent: FinancialAgent | None = None,
        customer_agent: CustomerAgent | None = None,
        process_agent: ProcessAgent | None = None,
        learning_agent: LearningAgent | None = None,
        max_chars_per_perspective: int = 50000,
    ) -> str:
        """Constrói contexto de conhecimento BSC via RAG agents.

        ESTRATÉGIA: Maximizar qualidade do conhecimento BSC sem limitações.
        BSC é complexo e demanda contexto rico. Com 200K+ tokens disponíveis,
        usamos 50K chars (12.5K tokens) por perspectiva = 200K chars total
        = 50K tokens BSC. Captura análise completa sem truncamento.

        Args:
            financial_agent: Agent especialista em perspectiva financeira
            customer_agent: Agent especialista em perspectiva clientes
            process_agent: Agent especialista em perspectiva processos
            learning_agent: Agent especialista em perspectiva aprendizado
            max_chars_per_perspective: Máximo de caracteres por perspectiva
                (default: 50000 = ~12500 tokens, análise completa do agent)

        Returns:
            String com conhecimento BSC consolidado
        """

        def _normalize_output_to_string(output_value) -> str:
            """Normaliza output do agent para string (defensivo).

            Agents podem retornar output como string, lista, ou outro tipo.
            Esta função garante sempre string antes de processar.

            Args:
                output_value: Valor do campo "output" do agent (pode ser qualquer tipo)

            Returns:
                String normalizada (vazia se output_value for None/empty)
            """
            if output_value is None:
                return ""
            if isinstance(output_value, str):
                return output_value
            if isinstance(output_value, list):
                # Se for lista, juntar elementos com espaço
                return " ".join(str(item) for item in output_value if item)
            # Outros tipos: converter para string
            return str(output_value)

        try:
            # Query para buscar conhecimento relevante sobre implementação BSC
            query = "Como implementar Balanced Scorecard ações práticas estratégicas"

            knowledge_parts = []

            # Buscar conhecimento de cada perspectiva (se agents disponíveis)
            if financial_agent:
                try:
                    result = await financial_agent.ainvoke(query)
                    financial_knowledge = (
                        _normalize_output_to_string(result.get("output", ""))
                        if isinstance(result, dict)
                        else _normalize_output_to_string(result)
                    )
                    if financial_knowledge and financial_knowledge.strip():
                        truncated = (
                            financial_knowledge[:max_chars_per_perspective]
                            if len(financial_knowledge) > max_chars_per_perspective
                            else financial_knowledge
                        )
                        knowledge_parts.append(f"FINANCEIRA: {truncated}")
                except Exception as e:
                    logger.warning(f"Erro ao buscar conhecimento financeiro: {e}")

            if customer_agent:
                try:
                    result = await customer_agent.ainvoke(query)
                    customer_knowledge = (
                        _normalize_output_to_string(result.get("output", ""))
                        if isinstance(result, dict)
                        else _normalize_output_to_string(result)
                    )
                    if customer_knowledge and customer_knowledge.strip():
                        truncated = (
                            customer_knowledge[:max_chars_per_perspective]
                            if len(customer_knowledge) > max_chars_per_perspective
                            else customer_knowledge
                        )
                        knowledge_parts.append(f"CLIENTES: {truncated}")
                except Exception as e:
                    logger.warning(f"Erro ao buscar conhecimento clientes: {e}")

            if process_agent:
                try:
                    result = await process_agent.ainvoke(query)
                    process_knowledge = (
                        _normalize_output_to_string(result.get("output", ""))
                        if isinstance(result, dict)
                        else _normalize_output_to_string(result)
                    )
                    if process_knowledge and process_knowledge.strip():
                        truncated = (
                            process_knowledge[:max_chars_per_perspective]
                            if len(process_knowledge) > max_chars_per_perspective
                            else process_knowledge
                        )
                        knowledge_parts.append(f"PROCESSOS: {truncated}")
                except Exception as e:
                    logger.warning(f"Erro ao buscar conhecimento processos: {e}")

            if learning_agent:
                try:
                    result = await learning_agent.ainvoke(query)
                    learning_knowledge = (
                        _normalize_output_to_string(result.get("output", ""))
                        if isinstance(result, dict)
                        else _normalize_output_to_string(result)
                    )
                    if learning_knowledge and learning_knowledge.strip():
                        truncated = (
                            learning_knowledge[:max_chars_per_perspective]
                            if len(learning_knowledge) > max_chars_per_perspective
                            else learning_knowledge
                        )
                        knowledge_parts.append(f"APRENDIZADO: {truncated}")
                except Exception as e:
                    logger.warning(f"Erro ao buscar conhecimento aprendizado: {e}")

            if not knowledge_parts:
                logger.warning("Nenhum conhecimento BSC obtido via RAG")
                return "Conhecimento BSC da literatura não disponível."

            return "\n\n".join(knowledge_parts)

        except Exception as e:
            logger.error(f"Erro ao construir contexto BSC: {e}")
            return "Erro ao obter conhecimento BSC da literatura."

    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> ActionPlan:
        """Chama LLM com retry logic para structured output.

        Args:
            prompt: Prompt para enviar ao LLM
            max_retries: Número máximo de tentativas

        Returns:
            ActionPlan estruturado

        Raises:
            ValidationError: Se todas as tentativas falharem
        """
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"[ActionPlanTool] Tentativa {attempt + 1}/{max_retries} - Chamando LLM structured output"
                )

                # Chamar LLM structured output diretamente
                messages = [{"role": "user", "content": prompt}]
                action_plan = await self.structured_llm.ainvoke(messages)

                if action_plan:
                    logger.debug(
                        f"[ActionPlanTool] LLM retornou ActionPlan válido na tentativa {attempt + 1}"
                    )
                    return action_plan
                logger.warning(f"[ActionPlanTool] LLM retornou None na tentativa {attempt + 1}")

            except ValidationError as e:
                logger.warning(f"[ActionPlanTool] ValidationError na tentativa {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.warning(f"[ActionPlanTool] Erro na tentativa {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise

        # Se chegou aqui, todas as tentativas falharam
        raise ValidationError("Falha ao gerar ActionPlan após todas as tentativas", [])

    def _validate_action_plan(self, action_plan: ActionPlan) -> None:
        """Valida qualidade do ActionPlan gerado.

        Args:
            action_plan: ActionPlan para validar

        Raises:
            ValueError: Se plano não atender critérios de qualidade
        """
        if not action_plan:
            raise ValueError("ActionPlan não pode ser None")

        # Validar quantidade mínima de ações
        if action_plan.total_actions < 3:
            raise ValueError(
                f"Plano deve ter pelo menos 3 ações, encontrado: {action_plan.total_actions}"
            )

        # Validar balanceamento entre perspectivas
        if not action_plan.is_balanced(min_actions_per_perspective=1):
            logger.warning("ActionPlan não está balanceado entre as 4 perspectivas BSC")

        # Validar distribuição de prioridades
        high_priority_ratio = action_plan.high_priority_count / action_plan.total_actions
        if high_priority_ratio < 0.1 or high_priority_ratio > 0.8:
            logger.warning(
                f"Distribuição de prioridades pode estar inadequada: {high_priority_ratio:.1%} HIGH"
            )

        # Validar qualidade geral
        quality_score = action_plan.quality_score()
        if quality_score < 0.3:
            logger.warning(f"Score de qualidade baixo: {quality_score:.1%}")

        logger.info(
            f"ActionPlan validado - Score: {quality_score:.1%}, Balanceado: {action_plan.is_balanced()}"
        )

    def format_for_display(self, action_plan: ActionPlan) -> str:
        """Formata ActionPlan para exibição amigável.

        Args:
            action_plan: ActionPlan para formatar

        Returns:
            String formatada para exibição
        """
        return format_action_plan_for_display(action_plan)

    def get_quality_metrics(self, action_plan: ActionPlan) -> dict:
        """Retorna métricas de qualidade do ActionPlan.

        Args:
            action_plan: ActionPlan para analisar

        Returns:
            Dict com métricas de qualidade
        """
        return {
            "total_actions": action_plan.total_actions,
            "high_priority_count": action_plan.high_priority_count,
            "high_priority_ratio": action_plan.high_priority_count / action_plan.total_actions,
            "is_balanced": action_plan.is_balanced(),
            "quality_score": action_plan.quality_score(),
            "by_perspective": action_plan.by_perspective,
            "actions_with_dependencies": sum(
                1 for action in action_plan.action_items if action.has_dependencies()
            ),
            "high_effort_actions": sum(
                1 for action in action_plan.action_items if action.is_high_effort()
            ),
        }
