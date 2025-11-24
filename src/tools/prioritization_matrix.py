"""Prioritization Matrix Tool - Ferramenta consultiva estruturada.

Esta tool facilita priorização de objetivos/ações estratégicas BSC usando:
- ClientProfile do onboarding
- Conhecimento BSC via RAG (specialist agents)
- LLM structured output (Pydantic)
- Framework híbrido (Impact/Effort + RICE + BSC-specific)

Architecture Pattern: Tool -> Prompt -> LLM + RAG -> Structured Output -> Validation

References:
- Impact/Effort Matrix 2x2 Ultimate Guide (Mirorim 2025)
- RICE Scoring Framework (Intercom - Sean McBride 2024-2025)
- Strategic Prioritization Best Practices (McKinsey, Mooncamp 2025)

Created: 2025-10-27 (FASE 3.12)
"""

# pylint: disable=logging-fstring-interpolation,too-many-arguments,too-many-locals
# pylint: disable=too-many-positional-arguments,broad-exception-caught,too-many-branches

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseLLM
from pydantic import ValidationError

from src.memory.schemas import PrioritizationMatrix
from src.prompts.prioritization_prompts import (
    FACILITATE_PRIORITIZATION_PROMPT,
    build_company_context,
    build_items_context,
    format_prioritization_matrix_for_display,
)

if TYPE_CHECKING:
    from src.agents.customer_agent import CustomerAgent
    from src.agents.financial_agent import FinancialAgent
    from src.agents.learning_agent import LearningAgent
    from src.agents.process_agent import ProcessAgent

logger = logging.getLogger(__name__)


class PrioritizationMatrixTool:
    """Ferramenta para facilitar priorização de objetivos/ações estratégicas BSC.

    Esta tool combina:
    1. Items a priorizar (objetivos, ações, iniciativas, projetos)
    2. Contexto da empresa (ClientProfile)
    3. Conhecimento BSC da literatura (via RAG specialist agents)
    4. Framework híbrido de avaliação (Impact/Effort + RICE + BSC-specific)
    5. LLM structured output para gerar PrioritizationMatrix

    Framework de Priorização (4 critérios, 0-100 scale):
    - Strategic Impact (40% peso): Potencial contribuição objetivos BSC
    - Implementation Effort (30% peso, invertido): Recursos necessários
    - Urgency (15% peso): Time sensitivity
    - Strategic Alignment (15% peso): Alinhamento com 4 perspectivas BSC

    4 Níveis de Prioridade (baseado no score final):
    - CRITICAL (75-100): Quick wins + strategic imperatives
    - HIGH (50-74): Important projects
    - MEDIUM (25-49): Nice-to-have improvements
    - LOW (0-24): Deprioritize or eliminate

    Example:
        >>> tool = PrioritizationMatrixTool(llm=get_llm())
        >>> items = [
        ...     {"id": "obj_001", "title": "Aumentar NPS", "description": "...", "perspective": "Clientes"},
        ...     {"id": "obj_002", "title": "Reduzir custos", "description": "...", "perspective": "Financeira"}
        ... ]
        >>> matrix = await tool.prioritize(
        ...     items_to_prioritize=items,
        ...     client_profile=profile,
        ...     financial_agent=financial_agent
        ... )
        >>> print(f"Matriz criada com {matrix.total_items} items priorizados")
        >>> top_3 = matrix.top_n(3)
        >>> print(f"Top 3: {[item.title for item in top_3]}")
    """

    def __init__(self, llm: BaseLLM):
        """Inicializa PrioritizationMatrixTool.

        Args:
            llm: Language model para structured output (GPT-5 mini recomendado)
        """
        self.llm = llm

        # Log para identificar temperatura do LLM
        if hasattr(llm, "temperature"):
            logger.info(f"[PrioritizationMatrixTool] LLM temperatura: {llm.temperature}")
        else:
            logger.warning("[PrioritizationMatrixTool] LLM não tem atributo 'temperature'")

        # Log para identificar modelo do LLM
        if hasattr(llm, "model"):
            logger.info(f"[PrioritizationMatrixTool] LLM modelo: {llm.model}")
        elif hasattr(llm, "model_name"):
            logger.info(f"[PrioritizationMatrixTool] LLM modelo: {llm.model_name}")
        else:
            logger.info("[PrioritizationMatrixTool] LLM tipo: %s", type(llm).__name__)

        self.structured_llm = llm.with_structured_output(PrioritizationMatrix)
        logger.info("PrioritizationMatrixTool inicializada com LLM structured output")

    async def prioritize(
        self,
        items_to_prioritize: list[dict],
        client_profile,
        prioritization_context: str,
        financial_agent: FinancialAgent | None = None,
        customer_agent: CustomerAgent | None = None,
        process_agent: ProcessAgent | None = None,
        learning_agent: LearningAgent | None = None,
        weights_config: dict[str, float] | None = None,
        max_retries: int = 3,
        bsc_knowledge_max_chars: int = 50000,
    ) -> PrioritizationMatrix:
        """Prioriza objetivos/ações estratégicas BSC usando framework híbrido.

        Args:
            items_to_prioritize: Lista de items a priorizar (cada item: dict com id, type, title, description, perspective)
            client_profile: ClientProfile com contexto da empresa
            prioritization_context: Contexto da priorização (ex: "Objetivos estratégicos Q1 2025")
            financial_agent: Agent especialista em perspectiva financeira
            customer_agent: Agent especialista em perspectiva clientes
            process_agent: Agent especialista em perspectiva processos
            learning_agent: Agent especialista em perspectiva aprendizado
            weights_config: Configuração de pesos customizada
                (default: impact 40%, effort 30%, urgency 15%, alignment 15%)
            max_retries: Número máximo de tentativas em caso de erro
            bsc_knowledge_max_chars: Caracteres máximos por perspectiva BSC
                (default: 50000 = ~12500 tokens/perspectiva,
                200K chars total = ~50K tokens de conhecimento BSC completo)

        Returns:
            PrioritizationMatrix com items avaliados, scores calculados e ranks definidos

        Raises:
            ValidationError: Se LLM retornar dados inválidos após max_retries
            ValueError: Se items_to_prioritize estiver vazio ou inválido
            Exception: Se ocorrer erro durante execução

        Example:
            >>> items = [
            ...     {"id": "obj_001", "type": "strategic_objective", "title": "Aumentar NPS em 20 pontos",
            ...      "description": "Melhorar experiência cliente...", "perspective": "Clientes"},
            ...     {"id": "obj_002", "type": "strategic_objective", "title": "Reduzir custos operacionais 15%",
            ...      "description": "Otimizar processos...", "perspective": "Financeira"}
            ... ]
            >>> matrix = await tool.prioritize(
            ...     items_to_prioritize=items,
            ...     client_profile=profile,
            ...     prioritization_context="Objetivos estratégicos Q1 2025 - TechCorp",
            ...     financial_agent=financial_agent
            ... )
            >>> print(matrix.summary())
        """
        try:
            logger.info(f"Iniciando priorização de {len(items_to_prioritize)} items")

            # Validar items_to_prioritize
            if not items_to_prioritize:
                raise ValueError("items_to_prioritize não pode ser vazio")

            self._validate_items_structure(items_to_prioritize)

            # 1. Construir contexto da empresa
            company_context = build_company_context(client_profile)
            logger.debug(f"Contexto empresa: {company_context[:100]}...")

            # 2. Construir contexto dos items a priorizar
            items_ctx = build_items_context(items_to_prioritize)
            logger.debug(f"Contexto items: {len(items_ctx)} caracteres")

            # 3. Construir conhecimento BSC via RAG (se agents disponíveis)
            bsc_knowledge = await self._build_bsc_knowledge_context(
                financial_agent,
                customer_agent,
                process_agent,
                learning_agent,
                max_chars_per_perspective=bsc_knowledge_max_chars,
            )
            logger.debug(f"Conhecimento BSC: {len(bsc_knowledge)} caracteres")

            # 4. Construir prompt final
            prompt = FACILITATE_PRIORITIZATION_PROMPT.format(
                company_context=company_context,
                items_context=items_ctx,
                bsc_knowledge=bsc_knowledge,
            )

            # Estimar tokens aproximadamente (1 token ~ 4 chars)
            estimated_tokens = len(prompt) // 4
            logger.info(
                f"Prompt construído: {len(prompt)} caracteres (~{estimated_tokens} tokens estimados)"
            )

            # ESTRATÉGIA AGRESSIVA: Usar máximo de contexto possível
            # Claude Sonnet 4.5: 200K input / GPT-5.1: 272K input
            # Limite warning: 150K tokens (margem confortável)
            if estimated_tokens > 150000:
                logger.warning(
                    f"Prompt muito grande ({estimated_tokens} tokens) - "
                    "aproximando limite. Considere reduzir "
                    "bsc_knowledge_max_chars se houver timeout."
                )

            # 5. Chamar LLM com retry logic
            matrix = await self._call_llm_with_retry(
                prompt, prioritization_context, weights_config, max_retries=max_retries
            )

            # 6. Validar qualidade da matriz
            self._validate_prioritization_matrix(matrix)

            logger.info(
                f"PrioritizationMatrix criada com sucesso: {matrix.total_items} items priorizados"
            )
            logger.info(
                f"Distribuição prioridades: {matrix.critical_count} CRITICAL, {matrix.high_count} HIGH, "
                f"{matrix.medium_count} MEDIUM, {matrix.low_count} LOW"
            )

            return matrix

        except Exception as e:
            logger.error(f"Erro na priorização: {e}")
            raise

    def _validate_items_structure(self, items: list[dict]) -> None:
        """Valida estrutura dos items a priorizar.

        Args:
            items: Lista de items a priorizar

        Raises:
            ValueError: Se items não tiverem campos obrigatórios
        """
        required_fields = ["title", "description", "perspective"]

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i} deve ser dict, encontrado: {type(item)}")

            for field in required_fields:
                if field not in item:
                    raise ValueError(f"Item {i} deve ter campo '{field}'")

                if not item[field] or not str(item[field]).strip():
                    raise ValueError(f"Item {i} campo '{field}' não pode ser vazio")

        logger.debug(f"Estrutura de {len(items)} items validada")

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
        try:
            # Query para buscar conhecimento relevante sobre priorização BSC
            query = "Como priorizar objetivos estratégicos Balanced Scorecard impacto esforço critérios avaliação"

            knowledge_parts = []

            # Buscar conhecimento de cada perspectiva (se agents disponíveis)
            if financial_agent:
                try:
                    result = await financial_agent.ainvoke(query)
                    financial_knowledge = (
                        result.get("output", "") if isinstance(result, dict) else str(result)
                    )
                    if financial_knowledge and financial_knowledge.strip():
                        # Limitar caracteres para evitar prompt muito grande
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
                        result.get("output", "") if isinstance(result, dict) else str(result)
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
                        result.get("output", "") if isinstance(result, dict) else str(result)
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
                        result.get("output", "") if isinstance(result, dict) else str(result)
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

    async def _call_llm_with_retry(
        self,
        prompt: str,
        prioritization_context: str,
        weights_config: dict[str, float] | None,
        max_retries: int = 3,
        timeout: int = 300,
    ) -> PrioritizationMatrix:
        """Chama LLM com retry logic para structured output.

        Args:
            prompt: Prompt para enviar ao LLM
            prioritization_context: Contexto da priorização
            weights_config: Configuração de pesos (opcional)
            max_retries: Número máximo de tentativas
            timeout: Timeout em segundos para chamada LLM (default: 300s/5min)

        Returns:
            PrioritizationMatrix estruturada

        Raises:
            ValidationError: Se todas as tentativas falharem
            TimeoutError: Se timeout for atingido
        """
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"[PrioritizationMatrixTool] Tentativa {attempt + 1}/{max_retries} - Chamando LLM structured output (timeout: {timeout}s)"
                )

                # Chamar LLM structured output com timeout
                messages = [{"role": "user", "content": prompt}]
                matrix = await asyncio.wait_for(
                    self.structured_llm.ainvoke(messages), timeout=timeout
                )

                if matrix:
                    # Sobrescrever prioritization_context e weights_config se fornecidos
                    if prioritization_context:
                        matrix.prioritization_context = prioritization_context

                    if weights_config:
                        matrix.weights_config = weights_config

                    logger.debug(
                        f"[PrioritizationMatrixTool] LLM retornou PrioritizationMatrix válida na tentativa {attempt + 1}"
                    )
                    return matrix
                logger.warning(
                    f"[PrioritizationMatrixTool] LLM retornou None na tentativa {attempt + 1}"
                )

            except ValidationError as e:
                logger.warning(
                    f"[PrioritizationMatrixTool] ValidationError na tentativa {attempt + 1}: {e}"
                )
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.warning(f"[PrioritizationMatrixTool] Erro na tentativa {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise

        # Se chegou aqui, todas as tentativas falharam
        raise ValidationError("Falha ao gerar PrioritizationMatrix após todas as tentativas", [])

    def _validate_prioritization_matrix(self, matrix: PrioritizationMatrix) -> None:
        """Valida qualidade da PrioritizationMatrix gerada.

        Args:
            matrix: PrioritizationMatrix para validar

        Raises:
            ValueError: Se matriz não atender critérios de qualidade
        """
        if not matrix:
            raise ValueError("PrioritizationMatrix não pode ser None")

        # Validar quantidade mínima de items
        if matrix.total_items < 1:
            raise ValueError(f"Matriz deve ter pelo menos 1 item, encontrado: {matrix.total_items}")

        # Validar distribuição de prioridades (não pode ter 100% CRITICAL ou 100% LOW)
        if matrix.total_items >= 3:
            critical_ratio = matrix.critical_count / matrix.total_items
            low_ratio = matrix.low_count / matrix.total_items

            if critical_ratio > 0.5:
                logger.warning(
                    f"Distribuição de prioridades pode estar inflacionada: {critical_ratio:.1%} CRITICAL"
                )

            if low_ratio > 0.5:
                logger.warning(
                    f"Distribuição de prioridades pode estar inadequada: {low_ratio:.1%} LOW"
                )

        # Validar balanceamento entre perspectivas (se matriz tiver 4+ items)
        if matrix.total_items >= 4 and not matrix.is_balanced():
            logger.warning("PrioritizationMatrix não está balanceada entre as 4 perspectivas BSC")

        # Validar que ranks são únicos e sequenciais
        ranks = [item.rank for item in matrix.items]
        expected_ranks = list(range(1, matrix.total_items + 1))

        if sorted(ranks) != expected_ranks:
            raise ValueError(
                f"Ranks devem ser únicos e sequenciais 1..{matrix.total_items}, encontrado: {sorted(ranks)}"
            )

        logger.info(
            f"PrioritizationMatrix validada - {matrix.total_items} items, Balanceada: {matrix.is_balanced()}"
        )

    def format_for_display(self, matrix: PrioritizationMatrix) -> str:
        """Formata PrioritizationMatrix para exibição amigável.

        Args:
            matrix: PrioritizationMatrix para formatar

        Returns:
            String formatada para exibição
        """
        return format_prioritization_matrix_for_display(matrix)

    def get_quality_metrics(self, matrix: PrioritizationMatrix) -> dict:
        """Retorna métricas de qualidade da PrioritizationMatrix.

        Args:
            matrix: PrioritizationMatrix para analisar

        Returns:
            Dict com métricas de qualidade
        """
        return {
            "total_items": matrix.total_items,
            "critical_count": matrix.critical_count,
            "high_count": matrix.high_count,
            "medium_count": matrix.medium_count,
            "low_count": matrix.low_count,
            "critical_ratio": (
                matrix.critical_count / matrix.total_items if matrix.total_items > 0 else 0
            ),
            "high_ratio": matrix.high_count / matrix.total_items if matrix.total_items > 0 else 0,
            "is_balanced": matrix.is_balanced(),
            "weights_config": matrix.weights_config,
        }
