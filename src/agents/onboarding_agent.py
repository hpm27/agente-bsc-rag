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
