"""
OnboardingAgent - Orquestrador conversacional multi-turn para fase ONBOARDING.

Este agente gerencia o diálogo progressivo com o cliente para extrair informações
da empresa usando o ClientProfileAgent. Implementa follow-up inteligente e
tracking de progresso em 3 steps.

Autor: BSC Consulting Agent v2.0
Data: 2025-10-15
"""
from __future__ import annotations  # PEP 563: Postponed annotations

import logging
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseLLM

# TYPE_CHECKING: Imports apenas para type checkers, evitando circular imports
if TYPE_CHECKING:
    from src.agents.client_profile_agent import ClientProfileAgent

from src.graph.consulting_states import ConsultingPhase
from src.graph.states import BSCState
from src.memory.mem0_client import Mem0ClientWrapper

logger = logging.getLogger(__name__)


class OnboardingStep(IntEnum):
    """Steps do processo de onboarding."""

    COMPANY_INFO = 1
    CHALLENGES = 2
    OBJECTIVES = 3


class OnboardingAgent:
    """
    Agente orquestrador conversacional para fase ONBOARDING.

    Responsabilidades:
    - Gerenciar diálogo multi-turn com cliente
    - Integrar ClientProfileAgent para extração progressiva
    - Implementar follow-up inteligente quando informações incompletas
    - Atualizar BSCState.onboarding_progress
    - Transição automática ONBOARDING → DISCOVERY quando completo

    Workflow de 3 Steps:
    1. COMPANY_INFO: Nome, setor, tamanho da empresa
    2. CHALLENGES: Principais desafios estratégicos (mínimo 2)
    3. OBJECTIVES: Objetivos nas 4 perspectivas BSC (mínimo 3)

    Best Practices Aplicadas (2025):
    - LangChain ConversationBufferMemory pattern (chat history)
    - LangGraph StateGraph integration (BSCState sync)
    - Evaluator-Optimizer loop (follow-up até qualidade)
    - Human-centered design (tom conversacional, não robótico)

    Attributes:
        llm: LLM para geração de perguntas follow-up
        profile_agent: ClientProfileAgent para extração de informações
        memory: Mem0ClientWrapper para persistência
        conversation_history: Buffer local do histórico de conversação
        max_followups_per_step: Limite de follow-ups por step (default: 2)
    """

    def __init__(
        self,
        llm: BaseLLM,
        client_profile_agent: ClientProfileAgent,
        memory_client: Mem0ClientWrapper,
        max_followups_per_step: int = 2,
    ):
        """
        Inicializa OnboardingAgent.

        Args:
            llm: LLM para geração de follow-up questions
            client_profile_agent: ClientProfileAgent configurado
            memory_client: Mem0ClientWrapper para persistência
            max_followups_per_step: Máximo de follow-ups por step (default: 2)
        """
        self.llm = llm
        self.profile_agent = client_profile_agent
        self.memory = memory_client
        self.max_followups_per_step = max_followups_per_step

        # Buffer local de conversação (resetado a cada onboarding)
        self.conversation_history: list[dict[str, str]] = []
        self.followup_count: dict[int, int] = {1: 0, 2: 0, 3: 0}

        logger.info(
            "[INIT] OnboardingAgent inicializado com max_followups=%d", max_followups_per_step
        )

    def start_onboarding(self, user_id: str, state: BSCState) -> dict[str, Any]:
        """
        Inicia processo de onboarding com cliente.

        Gera mensagem de boas-vindas e primeira pergunta (COMPANY_INFO).
        Inicializa conversation_history e onboarding_progress no state.

        Args:
            user_id: ID único do cliente
            state: BSCState atual (será atualizado)

        Returns:
            Dict contendo:
            - question: str - Pergunta gerada
            - step: int - Step atual (1)
            - is_complete: bool - False (recém iniciado)
            - followup_count: int - 0 (primeira pergunta)

        Example:
            >>> agent = OnboardingAgent(llm, profile_agent, mem0)
            >>> result = agent.start_onboarding("user_123", state)
            >>> print(result["question"])
            "Olá! Vou conhecer melhor sua empresa. Me conte sobre ela..."
        """
        logger.info("[START] Iniciando onboarding para user_id=%s", user_id)

        # Reset buffer local
        self.conversation_history = []
        self.followup_count = {1: 0, 2: 0, 3: 0}

        # Garantir ClientProfile inicializado
        if state.client_profile is None:
            from src.memory.schemas import ClientProfile
            state.client_profile = ClientProfile()

        # Inicializar onboarding_progress no state
        if not state.onboarding_progress:
            state.onboarding_progress = {
                "company_info": False,
                "challenges": False,
                "objectives": False,
                "current_step": OnboardingStep.COMPANY_INFO,
                "followup_counts": {1: 0, 2: 0, 3: 0},
            }

        # Gerar primeira pergunta
        welcome_message = (
            "Olá! Sou o Agente Consultor BSC e vou ajudá-lo a estruturar sua estratégia empresarial. "
            "Primeiro, preciso conhecer melhor sua empresa.\n\n"
        )

        initial_question = self._generate_initial_question(OnboardingStep.COMPANY_INFO)
        full_message = welcome_message + initial_question

        # Adicionar ao histórico
        self.conversation_history.append(
            {"role": "assistant", "content": full_message, "step": OnboardingStep.COMPANY_INFO}
        )

        logger.info("[START] Primeira pergunta gerada para step=%d", OnboardingStep.COMPANY_INFO)

        return {
            "question": full_message,
            "step": OnboardingStep.COMPANY_INFO,
            "is_complete": False,
            "followup_count": 0,
            "onboarding_progress": state.onboarding_progress  # CRÍTICO: Retornar progress!
        }

    def process_turn(self, user_id: str, user_message: str, state: BSCState) -> dict[str, Any]:
        """
        Processa um turn da conversação de onboarding.

        Workflow:
        1. Adiciona user_message ao conversation_history
        2. Extrai informações usando ClientProfileAgent
        3. Valida completude da extração
        4. Decide: follow-up vs next step vs complete
        5. Atualiza BSCState.onboarding_progress
        6. Retorna próxima pergunta ou confirmação de conclusão

        Args:
            user_id: ID único do cliente
            user_message: Mensagem do usuário
            state: BSCState atual (será atualizado)

        Returns:
            Dict contendo:
            - question: str - Próxima pergunta ou mensagem de conclusão
            - step: int - Step atual ou próximo
            - is_complete: bool - True se onboarding finalizado
            - followup_count: int - Contador de follow-ups do step atual
            - extraction: Dict - Dados extraídos (opcional)

        Example:
            >>> result = agent.process_turn("user_123", "Empresa X, healthcare, 200 funcionários", state)
            >>> print(result["question"])
            "Ótimo! Agora, quais são os principais desafios estratégicos..."
        """
        logger.info(
            "[TURN] Processando turn para user_id=%s, step=%d",
            user_id,
            state.onboarding_progress["current_step"],
        )

        # Adicionar user message ao histórico
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
                "step": state.onboarding_progress["current_step"],
            }
        )

        current_step = state.onboarding_progress["current_step"]

        # Extrair informações usando ClientProfileAgent
        extraction_result = self._extract_information(user_message, current_step, state)

        # Validar completude
        is_complete, missing_info = self._validate_extraction(extraction_result, current_step)

        # Decidir: follow-up, next step, ou complete
        if not is_complete and self.followup_count[current_step] < self.max_followups_per_step:
            # Gerar follow-up question
            followup_question = self._generate_followup_question(
                user_message, missing_info, current_step
            )

            self.followup_count[current_step] += 1
            state.onboarding_progress["followup_counts"][current_step] = self.followup_count[
                current_step
            ]

            logger.info(
                "[TURN] Follow-up gerado para step=%d (count=%d/%d)",
                current_step,
                self.followup_count[current_step],
                self.max_followups_per_step,
            )

            return {
                "question": followup_question,
                "step": current_step,
                "is_complete": False,
                "followup_count": self.followup_count[current_step],
                "extraction": extraction_result,
                "onboarding_progress": state.onboarding_progress,
            }

        # Informação suficiente (ou max follow-ups atingido) → avançar
        self._mark_step_complete(current_step, state)

        # Verificar se onboarding completo
        if current_step == OnboardingStep.OBJECTIVES:
            logger.info("[TURN] Onboarding COMPLETO para user_id=%s", user_id)

            # Transição para DISCOVERY
            state.current_phase = ConsultingPhase.DISCOVERY

            completion_message = (
                "Perfeito! Tenho todas as informações necessárias para começarmos o diagnóstico estratégico. "
                "Vamos agora aprofundar a análise dos seus desafios e objetivos usando ferramentas consultivas. "
                "Preparado para a próxima etapa?"
            )

            return {
                "question": completion_message,
                "step": current_step,
                "is_complete": True,
                "followup_count": self.followup_count[current_step],
                "extraction": extraction_result,
                "onboarding_progress": state.onboarding_progress,
            }

        # Avançar para próximo step
        next_step = current_step + 1
        state.onboarding_progress["current_step"] = next_step
        self.followup_count[next_step] = 0

        confirmation = self._generate_confirmation_message(current_step, extraction_result)
        next_question = self._generate_initial_question(next_step)
        full_message = f"{confirmation}\n\n{next_question}"

        logger.info("[TURN] Avançando para step=%d", next_step)

        return {
            "question": full_message,
            "step": next_step,
            "is_complete": False,
            "followup_count": 0,
            "extraction": extraction_result,
            "onboarding_progress": state.onboarding_progress,
        }

    async def collect_client_info(
        self, 
        user_id: str, 
        user_message: str, 
        state: BSCState
    ) -> dict[str, Any]:
        """
        Coleta informações do cliente usando Opportunistic Extraction (FASE 1).
        
        Fluxo adaptativo:
        1. Extrai TODAS entidades possíveis da mensagem do usuário (_extract_all_entities)
        2. Acumula conhecimento em partial_profile (preserva entre turnos)
        3. Decide próxima ação baseada em informações faltantes:
           - Se informações mínimas completas → finaliza onboarding
           - Se informações mínimas incompletas → gera próxima pergunta contextual
        4. Atualiza BSCState.client_profile progressivamente
        
        Informações mínimas necessárias:
        - company_name (obrigatório)
        - industry (obrigatório)
        - size OU revenue (ao menos um)
        - challenges (mínimo 2)
        
        Args:
            user_id: ID único do cliente
            user_message: Mensagem do usuário (texto livre)
            state: BSCState atual (será atualizado)
        
        Returns:
            Dict contendo:
            - question: str - Próxima pergunta ou mensagem de conclusão
            - is_complete: bool - True se onboarding finalizado
            - extracted_entities: Dict - Entidades extraídas neste turno
            - accumulated_profile: Dict - Perfil acumulado até agora
        
        Example:
            >>> result = await agent.collect_client_info(
            ...     "user_123", 
            ...     "Sou da TechCorp, startup de software em SP",
            ...     state
            ... )
            >>> print(result["question"])
            "TechCorp, como startup de tecnologia, quais são os 2-3 principais desafios..."
        """
        from src.prompts.client_profile_prompts import (
            CONTEXT_AWARE_QUESTION_SYSTEM,
            CONTEXT_AWARE_QUESTION_USER,
        )
        
        logger.info(
            "[COLLECT] Coletando informações do cliente user_id=%s (length=%d chars)",
            user_id,
            len(user_message),
        )
        
        # STEP 1: Extrair entidades da mensagem atual
        extraction_result = await self._extract_all_entities(user_message)
        extracted_entities = extraction_result["entities"]
        confidence_scores = extraction_result["confidence_scores"]
        
        # STEP 2: Inicializar partial_profile se não existir (usar metadata dict)
        if "partial_profile" not in state.metadata:
            state.metadata["partial_profile"] = {
                "company_name": None,
                "industry": None,
                "size": None,
                "revenue": None,
                "challenges": [],
                "goals": [],
                "timeline": None,
                "budget": None,
                "location": None,
            }
        
        partial_profile = state.metadata["partial_profile"]
        
        # STEP 3: Acumular conhecimento (merge com dados existentes)
        # Usar confidence_score para decidir se sobrescrever ou manter
        for field, value in extracted_entities.items():
            current_value = partial_profile.get(field)
            confidence = confidence_scores.get(field, 0.0)
            
            # Regras de acumulação
            if field in ["challenges", "goals"]:
                # Listas: adicionar novos itens (evitar duplicatas)
                if value and isinstance(value, list):
                    current_list = current_value if current_value else []
                    for item in value:
                        if item not in current_list:
                            current_list.append(item)
                    partial_profile[field] = current_list
            else:
                # Strings: sobrescrever se confidence > 0.5 e valor atual é None
                if value is not None and confidence > 0.5:
                    if current_value is None:
                        partial_profile[field] = value
                    # Se já existe valor, manter (não sobrescrever)
                    # Usuário poderia corrigir em follow-up específico
        
        # Atualizar metadata
        state.metadata["partial_profile"] = partial_profile
        
        logger.info(
            "[COLLECT] Perfil acumulado: company_name=%s, industry=%s, challenges=%d, goals=%d",
            partial_profile.get("company_name"),
            partial_profile.get("industry"),
            len(partial_profile.get("challenges", [])),
            len(partial_profile.get("goals", [])),
        )
        
        # STEP 4: Verificar se informações mínimas estão completas
        has_company_name = partial_profile.get("company_name") is not None
        has_industry = partial_profile.get("industry") is not None
        has_size_or_revenue = (
            partial_profile.get("size") is not None
            or partial_profile.get("revenue") is not None
        )
        has_min_challenges = len(partial_profile.get("challenges", [])) >= 2
        
        minimum_info_complete = (
            has_company_name
            and has_industry
            and has_size_or_revenue
            and has_min_challenges
        )
        
        # STEP 5: Decidir próxima ação
        if minimum_info_complete:
            # Onboarding completo! Atualizar ClientProfile e transicionar
            logger.info("[COLLECT] Informações mínimas completas! Finalizando onboarding.")
            
            # Atualizar ClientProfile no state
            if state.client_profile is None:
                from src.memory.schemas import ClientProfile
                state.client_profile = ClientProfile()
            
            # Copiar dados do partial_profile para ClientProfile
            if partial_profile.get("company_name"):
                state.client_profile.company.name = partial_profile["company_name"]
            if partial_profile.get("industry"):
                state.client_profile.company.sector = partial_profile["industry"]
            if partial_profile.get("size"):
                state.client_profile.company.size = partial_profile["size"]
            if partial_profile.get("challenges"):
                state.client_profile.context.current_challenges = partial_profile["challenges"]
            if partial_profile.get("goals"):
                state.client_profile.context.strategic_objectives = partial_profile["goals"]
            
            # Transição para DISCOVERY
            state.current_phase = ConsultingPhase.DISCOVERY
            
            # Mensagem de conclusão
            company_name = partial_profile.get("company_name", "sua empresa")
            num_challenges = len(partial_profile.get("challenges", []))
            
            completion_message = (
                f"Perfeito, {company_name}! Tenho as informações essenciais:\n\n"
                f"- Setor: {partial_profile.get('industry')}\n"
                f"- Porte: {partial_profile.get('size', 'Não informado')}\n"
                f"- Desafios principais: {num_challenges} identificados\n\n"
                "Agora vamos aprofundar a análise estratégica usando ferramentas consultivas. "
                "Preparado para a próxima etapa?"
            )
            
            return {
                "question": completion_message,
                "is_complete": True,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
            }
        
        # STEP 6: Informações incompletas → gerar próxima pergunta contextual
        logger.info("[COLLECT] Informações incompletas. Gerando próxima pergunta contextual.")
        
        # Identificar campos faltando
        missing_fields = []
        if not has_company_name:
            missing_fields.append("company_name")
        if not has_industry:
            missing_fields.append("industry")
        if not has_size_or_revenue:
            missing_fields.append("size ou revenue")
        if not has_min_challenges:
            missing_fields.append(f"challenges (tem {len(partial_profile.get('challenges', []))}, precisa 2)")
        
        # Formatar contexto para prompt
        known_fields_str = "\n".join(
            [
                f"- {field}: {value}"
                for field, value in partial_profile.items()
                if value is not None and value != [] and value != ""
            ]
        )
        missing_fields_str = "\n".join([f"- {field}" for field in missing_fields])
        
        # Gerar próxima pergunta usando LLM
        system_prompt = CONTEXT_AWARE_QUESTION_SYSTEM
        user_prompt = CONTEXT_AWARE_QUESTION_USER.format(
            known_fields=known_fields_str if known_fields_str else "Nenhum campo coletado ainda",
            missing_fields=missing_fields_str,
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            next_question = response.content if hasattr(response, "content") else str(response)
            
            logger.info("[COLLECT] Próxima pergunta gerada (length=%d chars)", len(next_question))
            
            return {
                "question": next_question,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
            }
            
        except Exception as e:
            logger.error("[COLLECT] Erro ao gerar próxima pergunta: %s", str(e))
            
            # Fallback: pergunta genérica baseada no primeiro campo faltando
            if not has_company_name:
                fallback_question = "Para começarmos, qual o nome da sua empresa?"
            elif not has_industry:
                fallback_question = "Em qual setor/indústria sua empresa atua?"
            elif not has_size_or_revenue:
                fallback_question = "Qual o porte da empresa? (micro, pequena, média, grande)"
            else:
                fallback_question = "Quais são os 2-3 principais desafios estratégicos que sua empresa enfrenta hoje?"
            
            return {
                "question": fallback_question,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
            }

    def is_onboarding_complete(self, state: BSCState) -> bool:
        """
        Verifica se onboarding está completo.

        Args:
            state: BSCState atual

        Returns:
            bool: True se todos os 3 steps estão marcados como completos
        """
        if state.onboarding_progress is None:
            return False

        return all(
            [
                state.onboarding_progress.get("company_info", False),
                state.onboarding_progress.get("challenges", False),
                state.onboarding_progress.get("objectives", False),
            ]
        )

    # ========================================================================
    # MÉTODOS PRIVADOS (AUXILIARES)
    # ========================================================================

    def _generate_initial_question(self, step: int) -> str:
        """
        Gera pergunta inicial para um step específico.

        Args:
            step: OnboardingStep (1, 2, ou 3)

        Returns:
            str: Pergunta conversacional adequada ao step
        """
        questions = {
            OnboardingStep.COMPANY_INFO: (
                "**Sobre sua empresa:**\n"
                "Por favor, me conte:\n"
                "- Qual o nome da empresa?\n"
                "- Em qual setor/indústria vocês atuam?\n"
                "- Qual o tamanho aproximado (número de funcionários)?"
            ),
            OnboardingStep.CHALLENGES: (
                "**Desafios Estratégicos:**\n"
                "Quais são os **3 principais desafios estratégicos** que sua empresa enfrenta atualmente? "
                "Pode ser relacionado a crescimento, competição, eficiência operacional, qualidade, etc."
            ),
            OnboardingStep.OBJECTIVES: (
                "**Objetivos Estratégicos (4 Perspectivas BSC):**\n"
                "Vamos definir seus objetivos usando o Balanced Scorecard:\n"
                "- **Financeira**: Quais metas financeiras (receita, lucro, EBITDA)?\n"
                "- **Clientes**: O que querem alcançar com clientes (satisfação, retenção, NPS)?\n"
                "- **Processos Internos**: Melhorias operacionais desejadas?\n"
                "- **Aprendizado e Crescimento**: Desenvolvimento de pessoas e cultura?"
            ),
        }

        return questions.get(step, "")

    def _extract_information(
        self, user_message: str, current_step: int, state: BSCState
    ) -> dict[str, Any]:
        """
        Extrai informações usando ClientProfileAgent.

        Args:
            user_message: Mensagem do usuário
            current_step: Step atual (1, 2, ou 3)
            state: BSCState atual

        Returns:
            Dict com informações extraídas
        """
        conversation_context = self._build_conversation_context()

        if current_step == OnboardingStep.COMPANY_INFO:
            result = self.profile_agent.extract_company_info(
                user_message, conversation_history=conversation_context
            )

            # Atualizar state
            if state.client_profile is None:
                from src.memory.schemas import ClientProfile
                state.client_profile = ClientProfile()

            if result and hasattr(result, "name"):
                state.client_profile.company.name = result.name or state.client_profile.company.name
                state.client_profile.company.sector = (
                    result.sector or state.client_profile.company.sector
                )
                state.client_profile.company.size = result.size or state.client_profile.company.size

            return result.model_dump() if hasattr(result, "model_dump") else (result.dict() if hasattr(result, "dict") else result)

        elif current_step == OnboardingStep.CHALLENGES:
            # Garantir ClientProfile e company_info
            if state.client_profile is None:
                from src.memory.schemas import ClientProfile
                state.client_profile = ClientProfile()
            company_info = state.client_profile.company

            result = self.profile_agent.identify_challenges(
                user_message,
                company_info,
                conversation_history=conversation_context
            )

            # Atualizar state
            if result and hasattr(result, "challenges"):
                state.client_profile.context.current_challenges = result.challenges
            elif isinstance(result, list):
                state.client_profile.context.current_challenges = result

            # Normalizar retorno para dict esperado pelo validador
            if isinstance(result, list):
                return {"challenges": result}
            return result.model_dump() if hasattr(result, "model_dump") else (result.dict() if hasattr(result, "dict") else result)

        elif current_step == OnboardingStep.OBJECTIVES:
            # Garantir ClientProfile inicializado
            if state.client_profile is None:
                from src.memory.schemas import ClientProfile
                state.client_profile = ClientProfile()

            # Obter desafios atuais do state
            challenges = []
            if state.client_profile and state.client_profile.context and getattr(state.client_profile.context, 'current_challenges', None):
                challenges = state.client_profile.context.current_challenges

            # Se ainda não há desafios suficientes, pedir desafios antes de objetivos
            if len(challenges) < 2:
                self.followup_count[OnboardingStep.CHALLENGES] = self.followup_count.get(OnboardingStep.CHALLENGES, 0)
                state.onboarding_progress["current_step"] = OnboardingStep.CHALLENGES
                msg = (
                    "Antes de definirmos objetivos SMART, preciso de pelo menos **2-3 desafios estratégicos**. "
                    "Quais são os principais desafios hoje?"
                )
                return {
                    "question": msg,
                    "step": OnboardingStep.CHALLENGES,
                    "is_complete": False,
                    "followup_count": self.followup_count[OnboardingStep.CHALLENGES],
                    "extraction": {"objectives": []},
                    "onboarding_progress": state.onboarding_progress,
                }

            result = self.profile_agent.define_objectives(
                user_message,
                challenges,
                conversation_history=conversation_context
            )

            # Atualizar state
            if result and hasattr(result, "objectives"):
                state.client_profile.context.strategic_objectives = result.objectives
            elif isinstance(result, list):
                state.client_profile.context.strategic_objectives = result

            # Normalizar retorno para dict esperado pelo validador
            if isinstance(result, list):
                return {"objectives": result}
            return result.model_dump() if hasattr(result, "model_dump") else (result.dict() if hasattr(result, "dict") else result)

        return {}

    def _validate_extraction(self, extraction: dict[str, Any], step: int) -> tuple[bool, list[str]]:
        """
        Valida se extração está completa para o step.

        Args:
            extraction: Dados extraídos
            step: Step atual (1, 2, ou 3)

        Returns:
            Tuple[bool, List[str]]:
            - bool: True se completo, False se falta informação
            - List[str]: Lista de campos faltando (vazio se completo)
        """
        missing = []

        if step == OnboardingStep.COMPANY_INFO:
            if not extraction.get("name"):
                missing.append("nome da empresa")
            if not extraction.get("sector"):
                missing.append("setor/indústria")
            if not extraction.get("size"):
                missing.append("tamanho (número de funcionários)")

        if step == OnboardingStep.CHALLENGES:
            challenges = extraction.get("challenges", [])
            if len(challenges) < 2:
                missing.append("pelo menos 2 desafios estratégicos")

        if step == OnboardingStep.OBJECTIVES:
            objectives = extraction.get("objectives", [])
            if len(objectives) < 3:
                missing.append("pelo menos 3 objetivos estratégicos")

        is_complete = len(missing) == 0
        return is_complete, missing

    def _generate_followup_question(
        self, user_message: str, missing_info: list[str], step: int
    ) -> str:
        """
        Gera pergunta de follow-up para informações faltantes.

        Args:
            user_message: Mensagem original do usuário
            missing_info: Lista de informações faltando
            step: Step atual

        Returns:
            str: Pergunta de follow-up conversacional
        """
        # Prompt simples para geração (LLM não é necessário aqui, templates funcionam)
        if step == OnboardingStep.COMPANY_INFO:
            if "nome da empresa" in str(missing_info):
                return "Entendi! Mas não identifiquei o **nome da empresa**. Pode me informar?"
            if "setor/indústria" in str(missing_info):
                return "Certo! Mas qual o **setor ou indústria** que a empresa atua?"
            if "tamanho" in str(missing_info):
                return "OK! E qual o **tamanho aproximado** da empresa (número de funcionários)?"

        if step == OnboardingStep.CHALLENGES:
            return (
                "Entendi o contexto! Mas preciso de **pelo menos 2-3 desafios estratégicos específicos** "
                "para fazer uma boa análise. Pode detalhar mais?"
            )

        if step == OnboardingStep.OBJECTIVES:
            return (
                "Ótimo início! Mas preciso de **pelo menos 3 objetivos estratégicos** distribuídos nas "
                "4 perspectivas BSC (Financeira, Clientes, Processos, Aprendizado). Pode complementar?"
            )

        return "Pode fornecer mais detalhes sobre essa informação?"

    def _generate_confirmation_message(
        self, completed_step: int, extraction: dict[str, Any]
    ) -> str:
        """
        Gera mensagem de confirmação ao completar um step.

        Args:
            completed_step: Step recém completado
            extraction: Dados extraídos

        Returns:
            str: Mensagem de confirmação
        """
        if completed_step == OnboardingStep.COMPANY_INFO:
            company_name = extraction.get("name", "sua empresa")
            sector = extraction.get("sector", "seu setor")
            return f"Entendi, **{company_name}** atua no setor de **{sector}**. Vamos prosseguir!"

        if completed_step == OnboardingStep.CHALLENGES:
            challenges = extraction.get("challenges", [])
            num_challenges = len(challenges)
            if num_challenges > 0:
                # Mostrar os desafios identificados para confirmar
                challenges_list = "\n".join([f"• {c}" for c in challenges[:3]])
                return f"Perfeito! Identifiquei {num_challenges} desafios principais:\n\n{challenges_list}\n\nVamos prosseguir!"
            return "Certo, vamos prosseguir para os objetivos estratégicos."

        if completed_step == OnboardingStep.OBJECTIVES:
            objectives = extraction.get("objectives", [])
            num_objectives = len(objectives)
            if num_objectives > 0:
                return f"Ótimo! Mapeei {num_objectives} objetivos estratégicos nas perspectivas BSC. Agora posso iniciar o diagnóstico!"
            return "Certo, vamos iniciar o diagnóstico!"

        return "Informações registradas!"

    def _mark_step_complete(self, step: int, state: BSCState) -> None:
        """
        Marca step como completo no onboarding_progress.

        Args:
            step: Step a marcar (1, 2, ou 3)
            state: BSCState atual
        """
        step_keys = {
            OnboardingStep.COMPANY_INFO: "company_info",
            OnboardingStep.CHALLENGES: "challenges",
            OnboardingStep.OBJECTIVES: "objectives",
        }

        key = step_keys.get(step)
        if key:
            state.onboarding_progress[key] = True
            logger.info("[COMPLETE] Step %s marcado como completo", key)

    async def _validate_extraction(
        self,
        entity: str,
        entity_type: str
    ) -> dict[str, Any]:
        """
        Valida semanticamente se entidade corresponde ao tipo esperado (challenge ou objective).
        
        Implementa Intelligent Validation (FASE 2): usa LLM para classificar semanticamente
        se um texto é realmente um challenge (problema/desafio) ou objective (meta/objetivo),
        evitando confusões comuns (ex: "Aumentar vendas" classificado como challenge).
        
        Args:
            entity: Texto a validar (ex: "Baixa satisfação de clientes")
            entity_type: Tipo esperado ("challenge" ou "objective")
        
        Returns:
            Dict contendo:
            - is_valid: bool - True se classificação correta
            - classified_as: str - "challenge", "objective" ou "ambiguous"
            - confidence: float - 0.0-1.0
            - reasoning: str - Explicação da classificação
            - correction_suggestion: str | None - Sugestão de correção se misclassificado
        
        Example:
            >>> result = await agent._validate_extraction("Aumentar vendas em 20%", "challenge")
            >>> result["is_valid"]
            False
            >>> result["classified_as"]
            "objective"
            >>> result["correction_suggestion"]
            "Isto parece ser um 'objective', não um 'challenge'."
        """
        from src.prompts.client_profile_prompts import (
            SEMANTIC_VALIDATION_SYSTEM,
            SEMANTIC_VALIDATION_USER,
        )
        import json
        
        logger.info(
            "[VALIDATE] Validando entity='%s' como type='%s'",
            entity[:50],
            entity_type
        )
        
        # Formatar prompts
        system_prompt = SEMANTIC_VALIDATION_SYSTEM
        user_prompt = SEMANTIC_VALIDATION_USER.format(entity=entity, entity_type=entity_type)
        
        # Chamar LLM com structured output (JSON)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # Parse JSON response (LLM pode retornar com markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            parsed = json.loads(response_text)
            
            # Validar estrutura esperada
            if "classified_as" not in parsed or "confidence" not in parsed:
                logger.warning(
                    "[VALIDATE] LLM retornou JSON sem estrutura esperada, usando fallback"
                )
                return {
                    "is_valid": True,  # Fallback: assumir válido
                    "classified_as": entity_type,
                    "confidence": 0.5,
                    "reasoning": "Estrutura JSON inválida, fallback aplicado",
                    "correction_suggestion": None,
                }
            
            # Calcular is_valid
            classified_as = parsed["classified_as"]
            confidence = parsed["confidence"]
            reasoning = parsed.get("reasoning", "")
            
            is_valid = (
                (classified_as == entity_type and confidence > 0.7)
                or (confidence < 0.5)  # Ambíguo também é "válido" (não reclassificar)
            )
            
            # Gerar correction_suggestion se misclassificado com alta confiança
            correction_suggestion = None
            if classified_as != entity_type and confidence > 0.7:
                correction_suggestion = (
                    f"Isto parece ser um '{classified_as}', não um '{entity_type}'."
                )
            
            logger.info(
                "[VALIDATE] Resultado: classified_as='%s', confidence=%.2f, is_valid=%s",
                classified_as,
                confidence,
                is_valid
            )
            
            return {
                "is_valid": is_valid,
                "classified_as": classified_as,
                "confidence": confidence,
                "reasoning": reasoning,
                "correction_suggestion": correction_suggestion,
            }
            
        except json.JSONDecodeError as e:
            logger.error("[VALIDATE] Erro ao parsear JSON do LLM: %s", str(e))
            logger.error("[VALIDATE] Response text: %s", response_text[:500])
            
            # Fallback: assumir válido
            return {
                "is_valid": True,
                "classified_as": entity_type,
                "confidence": 0.5,
                "reasoning": "Erro ao parsear JSON, fallback aplicado",
                "correction_suggestion": None,
            }
        
        except Exception as e:
            logger.error("[VALIDATE] Erro inesperado na validação: %s", str(e))
            
            # Fallback: assumir válido
            return {
                "is_valid": True,
                "classified_as": entity_type,
                "confidence": 0.5,
                "reasoning": "Erro inesperado, fallback aplicado",
                "correction_suggestion": None,
            }

    async def _extract_all_entities(self, user_text: str) -> dict[str, Any]:
        """
        Extrai todas as entidades possíveis do texto do usuário usando LLM.
        
        Implementa Opportunistic Extraction (FASE 1): identifica company_name, industry,
        size, revenue, challenges, goals, timeline, budget, location em qualquer ordem.
        
        Usa GPT-4o-mini com temperatura 0.1 para extração precisa e econômica.
        
        Args:
            user_text: Texto livre do usuário (pode conter 1+ entidades)
        
        Returns:
            Dict contendo:
            - entities: Dict com 9 campos (str/list/null)
            - confidence_scores: Dict com scores 0.0-1.0 para cada campo
        
        Example:
            >>> result = await agent._extract_all_entities("Sou da TechCorp, startup de software")
            >>> result["entities"]["company_name"]
            "TechCorp"
            >>> result["confidence_scores"]["company_name"]
            1.0
        """
        from src.prompts.client_profile_prompts import (
            ENTITY_EXTRACTION_SYSTEM,
            ENTITY_EXTRACTION_USER,
        )
        import json
        
        logger.info("[EXTRACT] Extraindo entidades do texto (length=%d chars)", len(user_text))
        
        # Formatar prompts
        system_prompt = ENTITY_EXTRACTION_SYSTEM
        user_prompt = ENTITY_EXTRACTION_USER.format(user_text=user_text)
        
        # Chamar LLM com structured output (JSON)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            response_text = response.content if hasattr(response, "content") else str(response)
            
            # Parse JSON response
            # LLM pode retornar com markdown code blocks, extrair JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            parsed = json.loads(response_text)
            
            # Validar estrutura esperada
            if "entities" not in parsed or "confidence_scores" not in parsed:
                logger.warning("[EXTRACT] LLM retornou JSON sem estrutura esperada, usando fallback")
                return {
                    "entities": {
                        "company_name": None,
                        "industry": None,
                        "size": None,
                        "revenue": None,
                        "challenges": [],
                        "goals": [],
                        "timeline": None,
                        "budget": None,
                        "location": None,
                    },
                    "confidence_scores": {
                        "company_name": 0.0,
                        "industry": 0.0,
                        "size": 0.0,
                        "revenue": 0.0,
                        "challenges": 0.0,
                        "goals": 0.0,
                        "timeline": 0.0,
                        "budget": 0.0,
                        "location": 0.0,
                    },
                }
            
            logger.info(
                "[EXTRACT] Entidades extraídas com sucesso: %d campos com confidence > 0.5",
                sum(1 for score in parsed["confidence_scores"].values() if score > 0.5),
            )
            
            # FASE 2: Validar semanticamente challenges e objectives
            extracted_entities = parsed["entities"]
            
            # Validar challenges
            logger.info("[EXTRACT] Validando %d challenges...", len(extracted_entities.get("challenges", [])))
            validated_challenges = []
            reclassified_to_objectives = []
            
            for challenge in extracted_entities.get("challenges", []):
                validation = await self._validate_extraction(challenge, "challenge")
                
                if validation["classified_as"] == "challenge":
                    # Corretamente classificado
                    validated_challenges.append(challenge)
                elif validation["classified_as"] == "objective" and validation["confidence"] > 0.7:
                    # Reclassificar para objective
                    logger.info(
                        "[EXTRACT] Reclassificando '%s' de challenge → objective (confidence=%.2f)",
                        challenge[:50],
                        validation["confidence"]
                    )
                    reclassified_to_objectives.append(challenge)
                else:
                    # Ambíguo ou baixa confidence, manter como challenge
                    logger.info(
                        "[EXTRACT] Mantendo '%s' como challenge (ambíguo ou baixa confidence)",
                        challenge[:50]
                    )
                    validated_challenges.append(challenge)
            
            # Validar objectives (goals)
            logger.info("[EXTRACT] Validando %d objectives...", len(extracted_entities.get("goals", [])))
            validated_objectives = []
            reclassified_to_challenges = []
            
            for objective in extracted_entities.get("goals", []):
                validation = await self._validate_extraction(objective, "objective")
                
                if validation["classified_as"] == "objective":
                    # Corretamente classificado
                    validated_objectives.append(objective)
                elif validation["classified_as"] == "challenge" and validation["confidence"] > 0.7:
                    # Reclassificar para challenge
                    logger.info(
                        "[EXTRACT] Reclassificando '%s' de objective → challenge (confidence=%.2f)",
                        objective[:50],
                        validation["confidence"]
                    )
                    reclassified_to_challenges.append(objective)
                else:
                    # Ambíguo ou baixa confidence, manter como objective
                    logger.info(
                        "[EXTRACT] Mantendo '%s' como objective (ambíguo ou baixa confidence)",
                        objective[:50]
                    )
                    validated_objectives.append(objective)
            
            # Atualizar listas com reclassificações
            extracted_entities["challenges"] = validated_challenges + reclassified_to_challenges
            extracted_entities["goals"] = validated_objectives + reclassified_to_objectives
            
            # Adicionar flag de validação
            parsed["validated"] = True
            
            logger.info(
                "[EXTRACT] Validação completa: challenges=%d (reclassified_in=%d), goals=%d (reclassified_in=%d)",
                len(extracted_entities["challenges"]),
                len(reclassified_to_challenges),
                len(extracted_entities["goals"]),
                len(reclassified_to_objectives)
            )
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error("[EXTRACT] Erro ao parsear JSON do LLM: %s", str(e))
            logger.error("[EXTRACT] Response text: %s", response_text[:500])
            
            # Fallback: retornar estrutura vazia
            return {
                "entities": {
                    "company_name": None,
                    "industry": None,
                    "size": None,
                    "revenue": None,
                    "challenges": [],
                    "goals": [],
                    "timeline": None,
                    "budget": None,
                    "location": None,
                },
                "confidence_scores": {
                    "company_name": 0.0,
                    "industry": 0.0,
                    "size": 0.0,
                    "revenue": 0.0,
                    "challenges": 0.0,
                    "goals": 0.0,
                    "timeline": 0.0,
                    "budget": 0.0,
                    "location": 0.0,
                },
            }
        
        except Exception as e:
            logger.error("[EXTRACT] Erro inesperado na extração: %s", str(e))
            
            # Fallback: retornar estrutura vazia
            return {
                "entities": {
                    "company_name": None,
                    "industry": None,
                    "size": None,
                    "revenue": None,
                    "challenges": [],
                    "goals": [],
                    "timeline": None,
                    "budget": None,
                    "location": None,
                },
                "confidence_scores": {
                    "company_name": 0.0,
                    "industry": 0.0,
                    "size": 0.0,
                    "revenue": 0.0,
                    "challenges": 0.0,
                    "goals": 0.0,
                    "timeline": 0.0,
                    "budget": 0.0,
                    "location": 0.0,
                },
            }

    def _build_conversation_context(self) -> str:
        """
        Constrói contexto de conversação do histórico.

        Returns:
            str: Histórico formatado como string
        """
        if not self.conversation_history:
            return ""

        context_lines = []
        for turn in self.conversation_history[-5:]:  # Últimos 5 turns
            role = "Agente" if turn["role"] == "assistant" else "Cliente"
            context_lines.append(f"{role}: {turn['content']}")

        return "\n".join(context_lines)
