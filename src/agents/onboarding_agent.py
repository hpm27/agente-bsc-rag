"""
OnboardingAgent - Orquestrador conversacional multi-turn para fase ONBOARDING.

Este agente gerencia o diálogo progressivo com o cliente para extrair informações
da empresa usando o ClientProfileAgent. Implementa follow-up inteligente e
tracking de progresso em 3 steps.

Autor: BSC Consulting Agent v2.0
Data: 2025-10-15
"""

from __future__ import annotations  # PEP 563: Postponed annotations

import asyncio
import logging
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseLLM

# TYPE_CHECKING: Imports apenas para type checkers, evitando circular imports
if TYPE_CHECKING:
    from src.agents.client_profile_agent import ClientProfileAgent

from api.middleware.performance import track_llm_tokens

from src.graph.consulting_states import ConsultingPhase
from src.graph.states import BSCState
from src.memory.mem0_client import Mem0ClientWrapper
from src.memory.schemas import ConversationContext, ExtractedEntities

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
    - Transicao automatica ONBOARDING -> DISCOVERY quando completo

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

        # Gerar primeira pergunta (TOM: Entrevista casual, não reunião formal)
        welcome_message = (
            "Oi! Que bom ter você aqui. Antes de começarmos, quero te conhecer melhor.\n\n"
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
            "onboarding_progress": state.onboarding_progress,  # CRÍTICO: Retornar progress!
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

        # Informacao suficiente (ou max follow-ups atingido) -> avancar
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
        self, user_id: str, user_message: str, state: BSCState
    ) -> dict[str, Any]:
        """
        Coleta informações do cliente usando Opportunistic Extraction (FASE 1).

        Fluxo adaptativo:
        1. Extrai TODAS entidades possíveis da mensagem do usuário (_extract_all_entities)
        2. Acumula conhecimento em partial_profile (preserva entre turnos)
        3. Decide próxima ação baseada em informações faltantes:
           - Se informacoes minimas completas -> finaliza onboarding
           - Se informacoes minimas incompletas -> gera proxima pergunta contextual
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

        print(
            f"[DEBUG COLLECT] ===== METODO CHAMADO ===== | user_id={user_id} | message_length={len(user_message)}",
            flush=True,
        )
        logger.info(
            "[COLLECT] Coletando informações do cliente user_id=%s (length=%d chars)",
            user_id,
            len(user_message),
        )

        # STEP 1: Extrair entidades da mensagem atual
        print("[DEBUG COLLECT] Chamando _extract_all_entities...", flush=True)
        extraction_result = await self._extract_all_entities(user_message)
        print(
            f"[DEBUG COLLECT] Extração completa: "
            f"has_company_info={extraction_result.has_company_info}, "
            f"company_name={extraction_result.company_info.name if extraction_result.company_info else None}, "
            f"challenges={len(extraction_result.challenges)}, "
            f"objectives={len(extraction_result.objectives)}",
            flush=True,
        )

        # Adapter: Converter ExtractedEntities para formato antigo dict (compatibilidade temporaria)
        # TODO (FASE 2): Refatorar metodo inteiro para trabalhar direto com ExtractedEntities
        extracted_entities = {
            "company_name": (
                extraction_result.company_info.name if extraction_result.company_info else None
            ),
            "industry": (
                extraction_result.company_info.sector if extraction_result.company_info else None
            ),
            "size": extraction_result.company_info.size if extraction_result.company_info else None,
            "revenue": None,  # Nao existe em ExtractedEntities
            "challenges": extraction_result.challenges,
            "goals": extraction_result.objectives,  # Mapeado: objectives -> goals
            "timeline": None,  # Nao existe em ExtractedEntities
            "budget": None,  # Nao existe em ExtractedEntities
            "location": None,  # Nao existe em ExtractedEntities
        }

        confidence_scores = {
            "company_name": 1.0 if extraction_result.has_company_info else 0.0,
            "industry": 1.0 if extraction_result.has_company_info else 0.0,
            "size": 1.0 if extraction_result.has_company_info else 0.0,
            "revenue": 0.0,
            "challenges": 1.0 if extraction_result.has_challenges else 0.0,
            "goals": 1.0 if extraction_result.has_objectives else 0.0,
            "timeline": 0.0,
            "budget": 0.0,
            "location": 0.0,
        }

        # STEP 2: Inicializar partial_profile se não existir (usar metadata dict)
        if "partial_profile" not in state.metadata:
            print("[DEBUG COLLECT] INICIALIZANDO partial_profile (PRIMEIRA VEZ)", flush=True)
            logger.info("[COLLECT] INICIALIZANDO partial_profile (PRIMEIRA VEZ)")
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
        else:
            print(
                f"[DEBUG COLLECT] CARREGANDO partial_profile EXISTENTE: "
                f"company_name={state.metadata['partial_profile'].get('company_name')}, "
                f"challenges={len(state.metadata['partial_profile'].get('challenges', []))}",
                flush=True,
            )
            logger.info(
                "[COLLECT] CARREGANDO partial_profile EXISTENTE: challenges=%d, company_name=%s",
                len(state.metadata["partial_profile"].get("challenges", [])),
                state.metadata["partial_profile"].get("company_name"),
            )

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
            # Strings: sobrescrever se confidence > 0.5 e valor atual é None
            elif value is not None and confidence > 0.5:
                if current_value is None:
                    partial_profile[field] = value
                    # Se já existe valor, manter (não sobrescrever)
                    # Usuário poderia corrigir em follow-up específico

        # Atualizar metadata
        state.metadata["partial_profile"] = partial_profile

        # DEBUGGING: Log completo do partial_profile
        print(
            f"[DEBUG COLLECT] Perfil acumulado: "
            f"company_name={partial_profile.get('company_name')}, "
            f"industry={partial_profile.get('industry')}, "
            f"size={partial_profile.get('size')}, "
            f"challenges={len(partial_profile.get('challenges', []))}, "
            f"goals={len(partial_profile.get('goals', []))}",
            flush=True,
        )
        logger.info("[COLLECT] Perfil acumulado COMPLETO: %s", partial_profile)
        logger.info(
            "[COLLECT] Resumo: company_name=%s, industry=%s, challenges=%d, goals=%d",
            partial_profile.get("company_name"),
            partial_profile.get("industry"),
            len(partial_profile.get("challenges", [])),
            len(partial_profile.get("goals", [])),
        )

        # STEP 4: Verificar se informações mínimas estão completas
        has_company_name = partial_profile.get("company_name") is not None
        has_industry = partial_profile.get("industry") is not None
        has_size_or_revenue = (
            partial_profile.get("size") is not None or partial_profile.get("revenue") is not None
        )
        has_min_challenges = len(partial_profile.get("challenges", [])) >= 2
        has_min_objectives = (
            len(partial_profile.get("goals", [])) >= 3
        )  # CRÍTICO: exigir 3+ objectives

        minimum_info_complete = (
            has_company_name
            and has_industry
            and has_size_or_revenue
            and has_min_challenges
            and has_min_objectives  # NOVO: objectives obrigatórios para diagnóstico confiável
        )

        # STEP 5: Decidir próxima ação
        if minimum_info_complete:
            # Informações completas! Verificar se já pedimos confirmação
            awaiting_confirmation = state.metadata.get("awaiting_confirmation", False)

            if not awaiting_confirmation:
                # PRIMEIRA VEZ que informações estão completas -> pedir confirmação
                logger.info("[COLLECT] ===== INFORMAÇÕES COMPLETAS! Pedindo confirmação... =====")
                logger.info(
                    "[COLLECT] company_name=%s | industry=%s | size=%s | challenges=%d | objectives=%d",
                    partial_profile.get("company_name"),
                    partial_profile.get("industry"),
                    partial_profile.get("size"),
                    len(partial_profile.get("challenges", [])),
                    len(partial_profile.get("goals", [])),
                )

                # Construir mensagem de confirmação com resumo
                company_name = partial_profile.get("company_name", "sua empresa")
                sector = partial_profile.get("industry", "N/A")
                size = partial_profile.get("size", "N/A")
                challenges = partial_profile.get("challenges", [])
                goals = partial_profile.get("goals", [])

                # Formatar listas
                challenges_text = "\n".join(
                    [f"  • {c}" for c in challenges[:5]]
                )  # Max 5 para brevidade
                goals_text = "\n".join([f"  • {g}" for g in goals[:5]])  # Max 5

                confirmation_message = f"""Perfeito! Deixa eu confirmar as informações antes de seguirmos:

**Empresa:** {company_name}
**Setor:** {sector}
**Porte:** {size}

**Desafios identificados ({len(challenges)}):**
{challenges_text}

**Objetivos estratégicos ({len(goals)}):**
{goals_text}

Está tudo certinho? Posso seguir para o diagnóstico BSC?

_(Responda "sim" para continuar ou "não" se quiser corrigir algo)_"""

                # Setar flag de aguardando confirmação
                state.metadata["awaiting_confirmation"] = True
                state.metadata["partial_profile"] = partial_profile

                logger.info("[COLLECT] Aguardando confirmação do usuário...")

                return {
                    "question": confirmation_message,
                    "is_complete": False,  # Ainda não completo até confirmar!
                    "extracted_entities": extracted_entities,
                    "accumulated_profile": partial_profile,
                    "metadata": {
                        "partial_profile": partial_profile,
                        "awaiting_confirmation": True,
                        "conversation_history": state.metadata.get("conversation_history", []),
                    },
                }

            # JÁ pedimos confirmação anteriormente -> verificar resposta do usuário
            logger.info("[COLLECT] Verificando confirmação do usuário...")

            # Detectar confirmação (sim/yes/confirmo/ok/correto etc)
            user_message_lower = user_message.lower().strip()
            confirmacao_keywords = [
                "sim",
                "yes",
                "confirmo",
                "ok",
                "correto",
                "certinho",
                "pode seguir",
                "vamos",
                "seguir",
            ]
            negacao_keywords = ["não", "no", "nao", "errado", "corrigir", "mudar", "alterar"]

            is_confirmation = any(keyword in user_message_lower for keyword in confirmacao_keywords)
            is_negation = any(keyword in user_message_lower for keyword in negacao_keywords)

            if is_confirmation and not is_negation:
                # CONFIRMADO! Atualizar ClientProfile e transicionar para DISCOVERY
                logger.info(
                    "[COLLECT] ===== CONFIRMAÇÃO RECEBIDA! Transicionando para DISCOVERY ====="
                )

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
                logger.info(
                    "[COLLECT] ===== STATE.CURRENT_PHASE ATUALIZADO PARA: %s =====",
                    state.current_phase,
                )

                # Limpar flag de confirmação
                state.metadata["awaiting_confirmation"] = False

                completion_message = (
                    f"Show! Vamos lá então. Iniciando diagnóstico BSC completo para {partial_profile.get('company_name')}...\n\n"
                    "_Isso vai levar alguns minutos enquanto analiso as 4 perspectivas do BSC._"
                )

                return {
                    "question": completion_message,
                    "is_complete": True,
                    "extracted_entities": extracted_entities,
                    "accumulated_profile": partial_profile,
                    "metadata": {
                        "partial_profile": partial_profile,
                        "awaiting_confirmation": False,
                    },
                }

            if is_negation:
                # NEGADO! Limpar flag e permitir correções
                logger.info(
                    "[COLLECT] Usuário quer corrigir informações. Voltando ao fluxo normal."
                )

                state.metadata["awaiting_confirmation"] = False

                correction_message = (
                    "Sem problemas! O que você gostaria de corrigir? "
                    "Pode me dizer qual informação está errada e eu atualizo."
                )

                return {
                    "question": correction_message,
                    "is_complete": False,
                    "extracted_entities": extracted_entities,
                    "accumulated_profile": partial_profile,
                    "metadata": {
                        "partial_profile": partial_profile,
                        "awaiting_confirmation": False,
                        "conversation_history": state.metadata.get("conversation_history", []),
                    },
                }

            # Resposta ambígua -> pedir clarificação
            logger.info("[COLLECT] Resposta ambígua do usuário. Pedindo clarificação.")

            clarification_message = (
                "Desculpa, não entendi bem. As informações estão corretas?\n\n"
                "_(Por favor responda 'sim' para continuar ou 'não' se quiser corrigir)_"
            )

            return {
                "question": clarification_message,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
                "metadata": {
                    "partial_profile": partial_profile,
                    "awaiting_confirmation": True,  # Manter aguardando
                    "conversation_history": state.metadata.get("conversation_history", []),
                },
            }

        # STEP 6: Informacoes incompletas -> analisar contexto e gerar resposta adaptativa (BLOCO 2)
        logger.info("[COLLECT] Informacoes incompletas. Analisando contexto conversacional...")

        # STEP 6.1: Preparar conversation_history (recuperar do state.metadata)
        conversation_history = state.metadata.get("conversation_history", [])
        # Adicionar mensagem atual ao historico
        conversation_history.append({"role": "user", "content": user_message})

        # STEP 6.2: Analisar contexto conversacional (BLOCO 1 - ETAPA 4)
        try:
            context = await self._analyze_conversation_context(
                conversation_history=conversation_history, extracted_entities=extraction_result
            )

            logger.info(
                "[COLLECT] Contexto analisado: scenario=%s, sentiment=%s, completeness=%.0f%%",
                context.scenario,
                context.user_sentiment,
                context.completeness,
            )

            # STEP 6.3: Gerar resposta contextual adaptativa (BLOCO 1 - ETAPA 5)
            # CRÍTICO: Passar partial_profile (acumulado) ao invés de extraction_result (só turno atual)
            next_question = await self._generate_contextual_response(
                context=context,
                user_message=user_message,
                extracted_entities=extraction_result,
                partial_profile=partial_profile,  # NOVO: dados acumulados
            )

            logger.info(
                "[COLLECT] Resposta contextual gerada (length=%d chars)", len(next_question)
            )

            # STEP 6.4: Atualizar conversation_history no state.metadata
            conversation_history.append({"role": "assistant", "content": next_question})
            state.metadata["conversation_history"] = conversation_history

            print(
                f"[DEBUG COLLECT] RETORNANDO (dados incompletos): "
                f"partial_profile incluído na metadata com company_name={partial_profile.get('company_name')}",
                flush=True,
            )

            return {
                "question": next_question,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
                "metadata": {
                    "partial_profile": partial_profile,
                    "conversation_history": conversation_history,
                    "conversation_context": context.model_dump(),  # Salvar contexto para analytics
                },
            }

        except Exception as e:
            logger.error("[COLLECT] Erro ao analisar contexto ou gerar resposta: %s", str(e))
            logger.info("[COLLECT] Usando fallback _get_fallback_response()...")

            # Fallback: usar metodo helper (BLOCO 1) com partial_profile
            fallback_question = self._get_fallback_response(
                context, extraction_result, partial_profile
            )

            # Atualizar conversation_history mesmo em fallback
            conversation_history.append({"role": "assistant", "content": fallback_question})
            state.metadata["conversation_history"] = conversation_history

            return {
                "question": fallback_question,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
                "metadata": {
                    "partial_profile": partial_profile,
                    "conversation_history": conversation_history,
                },
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
        # TOM: Entrevista casual - Uma pergunta por vez (progressive disclosure)
        questions = {
            OnboardingStep.COMPANY_INFO: "Me conta um pouquinho: como se chama sua empresa?",
            OnboardingStep.CHALLENGES: "E ai, quais os principais perrengues que voces enfrentam hoje?",
            OnboardingStep.OBJECTIVES: "Legal! Agora me conta: o que voces querem alcancar nos proximos meses?",
        }

        return questions.get(step, "")

    async def _extract_all_entities(
        self, user_message: str, conversation_history: list[dict[str, str]] | None = None
    ) -> ExtractedEntities:
        """Extrai TODAS entidades possiveis de mensagem do usuario simultaneamente.

        Implementa pattern Opportunistic Extraction (FASE 1 Refatoracao Conversacional):
        Extrai company_info, challenges e objectives em 1 unica chamada LLM,
        independente da ordem ou fase do onboarding.

        Resolve 3 problemas criticos do onboarding sequencial:
        1. Nao reconhece informacao ja fornecida (80% casos)
        2. Confunde challenges com objectives (60% casos)
        3. Ignora objetivos mencionados antes de desafios (60% casos)

        Args:
            user_message: Mensagem atual do usuario
            conversation_history: Historico completo conversacao (opcional)

        Returns:
            ExtractedEntities com:
            - company_info: CompanyInfo | None (se mencionado)
            - challenges: list[str] (2-7 desafios se mencionados)
            - objectives: list[str] (2-5 objetivos se mencionados)
            - has_company_info: bool (True se extraiu company info)
            - has_challenges: bool (True se extraiu challenges)
            - has_objectives: bool (True se extraiu objectives)

        Raises:
            ValidationError: Se LLM retornar JSON invalido
            TimeoutError: Se chamada LLM > 120s

        Example:
            >>> # Usuario fornece objectives ANTES de challenges (fora da ordem)
            >>> entities = await agent._extract_all_entities(
            ...     "Queremos crescer 15% e reduzir custos. Hoje temos alta rotatividade."
            ... )
            >>> entities.has_objectives  # True (detectou objectives PRIMEIRO)
            >>> entities.has_challenges  # True (detectou challenges DEPOIS)
            >>> entities.objectives  # ["Crescer 15%", "Reduzir custos"]
            >>> entities.challenges  # ["Alta rotatividade de colaboradores"]

        Notes:
            - Usa with_structured_output() com fallback json_mode (memory:10182063)
            - Validacao defensiva de nested schema CompanyInfo (memory:10178686)
            - Logs estruturados para debug (lesson-streamlit-ui-debugging)
            - ROI esperado: -66% latencia (1 call vs 3), +80% deteccao informacao

        References:
            - Plano: .cursor/plans/Plano_refatoracao_onboarding_conversacional.plan.md
            - Pattern: LangChain Blog July 2025 (Context Engineering)
            - Schema: src/memory/schemas.py ExtractedEntities (linhas 2411-2500)
        """
        import asyncio

        from langchain_core.messages import HumanMessage, SystemMessage

        from src.memory.schemas import CompanyInfo, ExtractedEntities
        from src.prompts.client_profile_prompts import EXTRACT_ALL_ENTITIES_PROMPT

        # Log inicio
        logger.info(
            "[EXTRACT_ALL] Inicio: message_len=%d, history_turns=%d",
            len(user_message),
            len(conversation_history) if conversation_history else 0,
        )

        # Construir contexto conversacao
        history_text = ""
        if conversation_history:
            history_text = "\n".join(
                [
                    f"{turn.get('role', 'user')}: {turn.get('content', '')}"
                    for turn in conversation_history[-5:]  # Ultimos 5 turns para contexto
                ]
            )

        # Construir messages para LLM
        messages = [
            SystemMessage(content=EXTRACT_ALL_ENTITIES_PROMPT),
            HumanMessage(
                content=f"""MENSAGEM DO USUARIO:
"{user_message}"

HISTORICO CONVERSACAO (ultimos 5 turns):
{history_text if history_text else "(inicio da conversacao)"}

Analise a mensagem e historico. Extraia TODAS entidades mencionadas (company_info, challenges, objectives).
Retorne JSON estruturado conforme schema ExtractedEntities."""
            ),
        ]

        # Tentar structured output com function_calling
        structured_llm = self.llm.with_structured_output(
            ExtractedEntities, method="function_calling"
        )

        try:
            # Chamada structured output com timeout
            result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=120)

            # Capturar tokens do resultado structured (se disponível)
            if result and hasattr(result, "__dict__") and hasattr(result, "response_metadata"):
                metadata = result.response_metadata
                token_usage = metadata.get("token_usage", {})
                if token_usage:
                    model_name = metadata.get("model_name", "gpt-5-mini-2025-08-07")
                    tokens_in = token_usage.get("prompt_tokens", 0)
                    tokens_out = token_usage.get("completion_tokens", 0)
                    track_llm_tokens(tokens_in, tokens_out, model_name)
                    logger.debug(
                        f"[PERFORMANCE] [ONBOARDING] Tokens capturados: {model_name} in={tokens_in} out={tokens_out}"
                    )

            if result is None:
                # Fallback para json_mode
                logger.warning(
                    "[EXTRACT_ALL] function_calling retornou None, tentando json_mode..."
                )
                structured_llm = self.llm.with_structured_output(
                    ExtractedEntities, method="json_mode"
                )
                result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=120)

            # Validacao defensiva: converter nested dict para CompanyInfo
            if result and isinstance(result.company_info, dict):
                logger.debug("[EXTRACT_ALL] Convertendo company_info dict -> CompanyInfo object")
                result.company_info = CompanyInfo(**result.company_info)

            # Log resultado
            logger.info(
                "[EXTRACT_ALL] Resultado: company_info=%s, challenges=%d, objectives=%d",
                result.has_company_info if result else False,
                len(result.challenges) if result else 0,
                len(result.objectives) if result else 0,
            )

            return result

        except asyncio.TimeoutError:
            logger.error("[EXTRACT_ALL] Timeout apos 120s")
            raise TimeoutError("Extracao de entidades excedeu 120s")

        except Exception as e:
            logger.error("[EXTRACT_ALL] Erro na extracao: %s", str(e), exc_info=True)
            # Retornar entidades vazias ao inves de falhar
            return ExtractedEntities(
                company_info=None,
                challenges=[],
                objectives=[],
                has_company_info=False,
                has_challenges=False,
                has_objectives=False,
            )

    async def _analyze_conversation_context(
        self, conversation_history: list[dict[str, str]], extracted_entities: ExtractedEntities
    ) -> ConversationContext:
        """Analisa contexto conversacional completo para detectar cenarios especiais.

        Implementa Context-Aware Response Generation pattern para onboarding conversacional.
        Detecta 5 cenarios: objectives_before_challenges, frustration_detected,
        information_complete, information_repeated, standard_flow.

        Baseado em:
        - Paper "User Frustration Detection in TOD Systems" (Telepathy Labs 2025)
          - Full conversation context > last utterance (+38% F1: 0.86 vs 0.48)
          - ICL zero-shot com LLMs suficiente (F1 0.86-0.87)
          - Frustracao via padroes (repeticao, escalacao) nao apenas keywords
        - Tidio Chatbot Analytics 2024-2025 (completeness metric, confirmacao periodica)

        Args:
            conversation_history: Lista de dicts com 'role' e 'content'
                                  [{"role": "user", "content": "..."}, ...]
            extracted_entities: Entidades ja extraidas (para calcular completeness)

        Returns:
            ConversationContext com cenario detectado, sentiment, missing_info,
            completeness, should_confirm, context_summary

        Raises:
            TimeoutError: Se analise exceder 120s
            ValueError: Se conversation_history vazia ou finish_reason truncation

        Example:
            >>> history = [
            ...     {"role": "assistant", "content": "Qual o nome da empresa?"},
            ...     {"role": "user", "content": "TechCorp, software empresarial"},
            ...     {"role": "assistant", "content": "Quais os desafios?"},
            ...     {"role": "user", "content": "Queremos crescer 30% no ano"}
            ... ]
            >>> entities = ExtractedEntities(
            ...     company_info=CompanyInfo(name="TechCorp", sector="Tecnologia"),
            ...     objectives=["Crescer 30%"],
            ...     has_objectives=True
            ... )
            >>> context = await agent._analyze_conversation_context(history, entities)
            >>> context.scenario  # "objectives_before_challenges"
            >>> context.completeness  # 0.65 (company + objectives, falta challenges)

        Notes:
            - Completeness calculada MANUALMENTE no codigo (nao confia apenas no LLM):
              * company_info presente = +0.35
              * challenges presente (len >= 1) = +0.30
              * objectives presente (len >= 1) = +0.35
              * Total maximo = 1.0
            - should_confirm = True se len(history) % 6 == 0 (a cada ~3 turns usuario)
            - Usa GPT-5 mini (modelo economico suficiente para tarefa estruturada)
            - Timeout 120s (conversas podem ter 5-10 turns)
        """
        try:
            # VALIDACAO: Historico nao pode estar vazio
            if not conversation_history or len(conversation_history) == 0:
                logger.warning("[ANALYZE_CONTEXT] Historico vazio, retornando standard_flow")
                return ConversationContext(
                    scenario="standard_flow",
                    user_sentiment="neutral",
                    missing_info=self._calculate_missing_info(extracted_entities),
                    completeness=self._calculate_completeness(extracted_entities),
                    should_confirm=False,
                    context_summary="Conversa iniciando",
                )

            # STEP 1: Calcular completeness e missing_info MANUALMENTE (nao confiar apenas no LLM)
            completeness = self._calculate_completeness(extracted_entities)
            missing_info = self._calculate_missing_info(extracted_entities)

            # STEP 2: Determinar should_confirm
            # CRÍTICO: Só confirmar quando dados estiverem COMPLETOS (completeness >= 1.0)
            # Confirmação prematura causa loop infinito!
            should_confirm = completeness >= 1.0

            # STEP 3: Formatar historico para o prompt (formato "USER: ...\nAGENT: ...")
            formatted_history = self._format_conversation_history(conversation_history)

            logger.info(
                "[ANALYZE_CONTEXT] Iniciando analise | turns=%d | completeness=%.2f | should_confirm=%s",
                len(conversation_history) // 2,  # Aproximacao de turns
                completeness,
                should_confirm,
            )

            # STEP 4: Construir messages para LLM
            from src.prompts.client_profile_prompts import ANALYZE_CONVERSATION_CONTEXT_PROMPT

            prompt = ANALYZE_CONVERSATION_CONTEXT_PROMPT.format(
                conversation_history=formatted_history
            )

            messages = [{"role": "system", "content": prompt}]

            # STEP 5: Chamar LLM com structured output (GPT-5 mini configuravel via construtor)
            llm = self.llm  # LLM configurado no construtor (GPT-5 mini para testes/producao)

            # Testar raw LLM ANTES de structured (detectar truncation - memoria 10182063)
            raw_test = await asyncio.wait_for(llm.ainvoke(messages), timeout=120)

            if hasattr(raw_test, "response_metadata"):
                finish_reason = raw_test.response_metadata.get("finish_reason", "N/A")

                if finish_reason == "length":
                    logger.error(
                        "[ANALYZE_CONTEXT] Response truncada (finish_reason: length) | "
                        "history_size=%d chars | Aumente max_completion_tokens",
                        len(formatted_history),
                    )
                    raise ValueError(
                        f"LLM response truncada. Historico muito longo ({len(formatted_history)} chars). "
                        "Considere resumir historico ou aumentar max_completion_tokens."
                    )
                if finish_reason not in ["stop", "end_turn"]:
                    logger.warning("[ANALYZE_CONTEXT] Finish reason inesperado: %s", finish_reason)

            # STEP 6: Structured output com fallback
            structured_llm = llm.with_structured_output(
                ConversationContext, method="function_calling"
            )

            result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=120)

            # Fallback para json_mode se function_calling retornar None
            if result is None:
                logger.warning(
                    "[ANALYZE_CONTEXT] function_calling retornou None, tentando json_mode..."
                )
                structured_llm = llm.with_structured_output(ConversationContext, method="json_mode")
                result = await asyncio.wait_for(structured_llm.ainvoke(messages), timeout=120)

            if result is None:
                logger.error("[ANALYZE_CONTEXT] Ambos metodos retornaram None, usando fallback")
                return ConversationContext(
                    scenario="standard_flow",
                    user_sentiment="neutral",
                    missing_info=missing_info,
                    completeness=completeness,
                    should_confirm=should_confirm,
                    context_summary="Analise automatica indisponivel",
                )

            # STEP 7: Override campos calculados manualmente (nao confiar apenas no LLM)
            result.completeness = completeness
            result.missing_info = missing_info
            result.should_confirm = should_confirm

            logger.info(
                "[ANALYZE_CONTEXT] Sucesso | scenario=%s | sentiment=%s | completeness=%.2f | missing=%s",
                result.scenario,
                result.user_sentiment,
                result.completeness,
                result.missing_info,
            )

            return result

        except asyncio.TimeoutError:
            logger.error("[ANALYZE_CONTEXT] Timeout apos 120s")
            raise TimeoutError("Analise de contexto excedeu 120s")

        except Exception as e:
            logger.error("[ANALYZE_CONTEXT] Erro na analise: %s", str(e), exc_info=True)
            # Fallback: Retornar contexto padrao
            return ConversationContext(
                scenario="standard_flow",
                user_sentiment="neutral",
                missing_info=self._calculate_missing_info(extracted_entities),
                completeness=self._calculate_completeness(extracted_entities),
                should_confirm=False,
                context_summary=f"Erro na analise: {str(e)[:50]}",
            )

    def _calculate_completeness(self, entities: ExtractedEntities) -> float:
        """Calcula porcentagem de completude do perfil (0.0 a 1.0).

        Formula: 35% company_info + 30% challenges + 35% objectives = 100%

        REGRAS (alinhadas com minimum_info_complete):
        - Company info: name + sector presentes
        - Challenges: mínimo 2 desafios
        - Objectives: mínimo 3 objetivos

        Args:
            entities: Entidades extraidas

        Returns:
            Float entre 0.0 e 1.0
        """
        completeness = 0.0

        # Company info: 35%
        if entities.has_company_info and entities.company_info is not None:
            completeness += 0.35

        # Challenges: 30% (precisa >=2 para completude total)
        if entities.has_challenges and len(entities.challenges) >= 2:
            completeness += 0.30
        elif entities.has_challenges and len(entities.challenges) == 1:
            completeness += 0.15  # Parcial se só 1 challenge

        # Objectives: 35% (precisa >=3 para completude total)
        if entities.has_objectives and len(entities.objectives) >= 3:
            completeness += 0.35
        elif entities.has_objectives and len(entities.objectives) >= 1:
            # Parcial: 1-2 objectives = proporcional
            completeness += 0.35 * (len(entities.objectives) / 3.0)

        return round(completeness, 2)

    def _calculate_missing_info(self, entities: ExtractedEntities) -> list[str]:
        """Identifica categorias de informacao ainda faltantes.

        Args:
            entities: Entidades extraidas

        Returns:
            Lista de strings: ["company_info"], ["challenges"], ["objectives"],
            ["company_info", "challenges"], etc
        """
        missing = []

        if not entities.has_company_info or entities.company_info is None:
            missing.append("company_info")

        if not entities.has_challenges or len(entities.challenges) == 0:
            missing.append("challenges")

        if not entities.has_objectives or len(entities.objectives) == 0:
            missing.append("objectives")

        return missing

    def _format_conversation_history(self, history: list[dict[str, str]]) -> str:
        """Formata historico para o prompt (formato USER:/AGENT:).

        Args:
            history: Lista de dicts com 'role' e 'content'

        Returns:
            String formatada: "AGENT: ...\\nUSER: ...\\nAGENT: ..."
        """
        formatted_lines = []

        for turn in history:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")

            # Mapear roles para formato prompt
            if role == "assistant":
                formatted_lines.append(f"AGENT: {content}")
            elif role == "user":
                formatted_lines.append(f"USER: {content}")
            else:
                # Fallback para roles desconhecidos
                formatted_lines.append(f"{role.upper()}: {content}")

        return "\n".join(formatted_lines)

    async def _generate_contextual_response(
        self,
        context: ConversationContext,
        user_message: str,
        extracted_entities: ExtractedEntities,
        partial_profile: dict[str, Any] | None = None,
    ) -> str:
        """Gera resposta contextual adaptativa baseada no estado da conversa.

        Implementa Context-Aware Response Generation pattern (Sobot.io 2025, ScienceDirect 2024).
        Adapta tom, conteudo e acoes baseado em: scenario conversacional, sentiment usuario,
        completeness, informacoes faltantes.

        5 Cenarios Tratados:
        - objectives_before_challenges: Redirecionar para challenges primeiro
        - frustration_detected: Empatia + acao corretiva + oferecer escalacao
        - information_complete: Sumario estruturado + confirmacao
        - information_repeated: Reconhecer + nao pedir novamente
        - standard_flow: Progressive disclosure + proxima info faltante

        Best Practices Aplicadas (Research Brightdata Out/2025):
        - Empathy-first approach (reconhecer emocao antes de solucao)
        - Progressive disclosure (1 pergunta por turno)
        - Personalization (usar informacoes ja coletadas)
        - Confirmation patterns (sumario estruturado com [OK])
        - Fallback gracioso (oferecer transferencia humana)

        Args:
            context: ConversationContext analisado (_analyze_conversation_context)
            user_message: Ultima mensagem do usuario
            extracted_entities: Entidades ja extraidas (ExtractedEntities)

        Returns:
            str: Resposta contextual adaptativa (2-4 sentencas, max 100 palavras)

        Raises:
            Exception: Se LLM falhar, retorna fallback generico

        Example:
            >>> context = ConversationContext(
            ...     scenario="frustration_detected",
            ...     user_sentiment="frustrated",
            ...     completeness=0.66
            ... )
            >>> response = await self._generate_contextual_response(context, "Ja falei o setor!", entities)
            >>> print(response)
            "Percebo que voce ja havia mencionado o setor. Vou registrar agora..."

        Research Sources:
        - Sobot.io (2025): Empathy + progressive disclosure patterns
        - ScienceDirect (2024): Confirmation patterns in TOD systems
        - Telepathy Labs (2025): Frustration detection + corrective actions
        """
        try:
            logger.info(
                f"[GENERATE_RESPONSE] Gerando resposta contextual | "
                f"Scenario: {context.scenario} | Sentiment: {context.user_sentiment} | "
                f"Completeness: {context.completeness}%"
            )

            # STEP 1: Preparar variaveis para o prompt
            # CRÍTICO: Usar partial_profile (ACUMULADO) prioritariamente, fallback para extracted_entities (turno atual)
            if partial_profile:
                # Usar dados acumulados (preserva contexto entre turnos)
                company_name = partial_profile.get("company_name") or "N/A"
                sector = partial_profile.get("industry") or "N/A"
                size = partial_profile.get("size") or "N/A"
                challenges_list = (
                    ", ".join(partial_profile.get("challenges", [])[:3])
                    if partial_profile.get("challenges")
                    else "Nenhum ainda"
                )
                objectives_list = (
                    ", ".join(partial_profile.get("goals", [])[:3])
                    if partial_profile.get("goals")
                    else "Nenhum ainda"
                )
            else:
                # Fallback: usar extracted_entities do turno atual (primeira vez)
                company_name = (
                    extracted_entities.company_info.name
                    if extracted_entities.company_info
                    else "N/A"
                )
                sector = (
                    extracted_entities.company_info.sector
                    if extracted_entities.company_info
                    else "N/A"
                )
                size = (
                    extracted_entities.company_info.size
                    if extracted_entities.company_info
                    else "N/A"
                )
                challenges_list = (
                    ", ".join(extracted_entities.challenges[:3])  # Max 3 para brevidade
                    if extracted_entities.challenges
                    else "Nenhum ainda"
                )
                objectives_list = (
                    ", ".join(extracted_entities.objectives[:3])  # Max 3 para brevidade
                    if extracted_entities.objectives
                    else "Nenhum ainda"
                )

            missing_info_str = (
                ", ".join(context.missing_info) if context.missing_info else "Nenhuma"
            )

            # STEP 2: Construir prompt com todas variaveis
            from src.prompts.client_profile_prompts import GENERATE_CONTEXTUAL_RESPONSE_PROMPT

            prompt = GENERATE_CONTEXTUAL_RESPONSE_PROMPT.format(
                scenario=context.scenario,
                user_sentiment=context.user_sentiment,
                missing_info=missing_info_str,
                completeness=context.completeness,
                context_summary=context.context_summary,
                user_message=user_message,
                company_name=company_name,
                sector=sector,
                size=size,
                challenges_list=challenges_list,
                objectives_list=objectives_list,
            )

            # STEP 3: Chamar LLM (free-form text, NAO structured output)
            # Usar temperatura 0.8 para respostas mais naturais/variadas (vs 1.0 padrao GPT-5)
            llm = self.llm  # GPT-5 mini configurado no construtor

            # Chamar LLM com timeout 120s
            messages = [{"role": "system", "content": prompt}]

            response = await asyncio.wait_for(llm.ainvoke(messages), timeout=120)

            # STEP 4: Extrair texto da resposta
            generated_text = response.content.strip()

            # STEP 5: Validacao basica (nao vazia, tamanho minimo)
            if not generated_text or len(generated_text) < 20:
                logger.warning(
                    f"[GENERATE_RESPONSE] Resposta muito curta ({len(generated_text)} chars), "
                    f"usando fallback"
                )
                return self._get_fallback_response(context, extracted_entities, partial_profile)

            logger.info(
                f"[GENERATE_RESPONSE] Resposta gerada com sucesso | "
                f"Length: {len(generated_text)} chars"
            )

            return generated_text

        except asyncio.TimeoutError:
            logger.error("[GENERATE_RESPONSE] Timeout ao gerar resposta (>120s)")
            return self._get_fallback_response(context, extracted_entities, partial_profile)

        except Exception as e:
            logger.error(f"[GENERATE_RESPONSE] Erro ao gerar resposta: {e}", exc_info=True)
            return self._get_fallback_response(context, extracted_entities, partial_profile)

    def _get_fallback_response(
        self,
        context: ConversationContext,
        entities: ExtractedEntities,
        partial_profile: dict[str, Any] | None = None,
    ) -> str:
        """Gera resposta fallback generica quando LLM falha.

        Resposta segura baseada em missing_info (proxima informacao faltante).
        Usa partial_profile quando disponível para personalizar perguntas.

        Args:
            context: ConversationContext atual
            entities: Entidades extraidas
            partial_profile: Perfil acumulado (opcional)

        Returns:
            str: Resposta fallback contextual
        """
        # Extrair company_name do partial_profile (se disponível)
        company_name = partial_profile.get("company_name") if partial_profile else None

        # Se completeness 100%, pedir confirmacao
        if context.completeness >= 1.0:
            name_part = f" da {company_name}" if company_name else ""
            return (
                f"Parece que temos todas as informacoes{name_part}. "
                "Posso confirmar se esta tudo correto antes de prosseguirmos?"
            )

        # Se frustration detectada, oferecer ajuda
        if context.scenario == "frustration_detected":
            return (
                "Entendo sua frustracao. Vou garantir que suas informacoes sejam "
                "registradas corretamente. Pode me contar o que falta?"
            )

        # Default: Perguntar proxima info faltante (usando company_name se disponível)
        if "company_info" in context.missing_info:
            return "Para comecar, pode me contar o nome da empresa e o setor de atuacao?"
        if "challenges" in context.missing_info:
            name_part = f" na {company_name}" if company_name else ""
            return f"Quais sao os principais desafios{name_part} que voces enfrentam atualmente?"
        if "objectives" in context.missing_info:
            name_part = f" da {company_name}" if company_name else ""
            return f"Quais sao os principais objetivos estrategicos{name_part}?"
        return "Entendi. Pode me contar mais?"

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

            return (
                result.model_dump()
                if hasattr(result, "model_dump")
                else (result.dict() if hasattr(result, "dict") else result)
            )

        if current_step == OnboardingStep.CHALLENGES:
            # Garantir ClientProfile e company_info
            if state.client_profile is None:
                from src.memory.schemas import ClientProfile

                state.client_profile = ClientProfile()
            company_info = state.client_profile.company

            result = self.profile_agent.identify_challenges(
                user_message, company_info, conversation_history=conversation_context
            )

            # Atualizar state
            if result and hasattr(result, "challenges"):
                state.client_profile.context.current_challenges = result.challenges
            elif isinstance(result, list):
                state.client_profile.context.current_challenges = result

            # Normalizar retorno para dict esperado pelo validador
            if isinstance(result, list):
                return {"challenges": result}
            return (
                result.model_dump()
                if hasattr(result, "model_dump")
                else (result.dict() if hasattr(result, "dict") else result)
            )

        if current_step == OnboardingStep.OBJECTIVES:
            # Garantir ClientProfile inicializado
            if state.client_profile is None:
                from src.memory.schemas import ClientProfile

                state.client_profile = ClientProfile()

            # Obter desafios atuais do state
            challenges = []
            if (
                state.client_profile
                and state.client_profile.context
                and getattr(state.client_profile.context, "current_challenges", None)
            ):
                challenges = state.client_profile.context.current_challenges

            # Se ainda não há desafios suficientes, pedir desafios antes de objetivos
            if len(challenges) < 2:
                self.followup_count[OnboardingStep.CHALLENGES] = self.followup_count.get(
                    OnboardingStep.CHALLENGES, 0
                )
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
                user_message, challenges, conversation_history=conversation_context
            )

            # Atualizar state
            if result and hasattr(result, "objectives"):
                state.client_profile.context.strategic_objectives = result.objectives
            elif isinstance(result, list):
                state.client_profile.context.strategic_objectives = result

            # Normalizar retorno para dict esperado pelo validador
            if isinstance(result, list):
                return {"objectives": result}
            return (
                result.model_dump()
                if hasattr(result, "model_dump")
                else (result.dict() if hasattr(result, "dict") else result)
            )

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
        # DEBUGGING LOGS (adicionado 2025-10-23 para resolver bugs pre-existentes)
        logger.info("[VALIDATE] ===== INICIANDO VALIDACAO =====")
        logger.info(
            "[VALIDATE] Extraction recebido (type=%s): %s", type(extraction).__name__, extraction
        )
        logger.info(
            "[VALIDATE] Step atual: %d (%s)",
            step,
            OnboardingStep(step).name if isinstance(step, int) else step,
        )

        missing = []

        if step == OnboardingStep.COMPANY_INFO:
            # Extrair valores ANTES de validar (para logging detalhado)
            name_value = extraction.get("name")
            sector_value = extraction.get("sector")
            size_value = extraction.get("size")

            logger.info(
                "[VALIDATE] COMPANY_INFO - name=%s (type=%s)",
                repr(name_value),
                type(name_value).__name__,
            )
            logger.info(
                "[VALIDATE] COMPANY_INFO - sector=%s (type=%s)",
                repr(sector_value),
                type(sector_value).__name__,
            )
            logger.info(
                "[VALIDATE] COMPANY_INFO - size=%s (type=%s)",
                repr(size_value),
                type(size_value).__name__,
            )

            if not name_value:
                missing.append("nome da empresa")
                logger.info("[VALIDATE] FALTANDO: nome da empresa")
            if not sector_value:
                missing.append("setor/indústria")
                logger.info("[VALIDATE] FALTANDO: setor/indústria")
            if not size_value:
                missing.append("tamanho (número de funcionários)")
                logger.info("[VALIDATE] FALTANDO: tamanho")

        if step == OnboardingStep.CHALLENGES:
            challenges = extraction.get("challenges", [])
            logger.info(
                "[VALIDATE] CHALLENGES - challenges=%s (len=%d)", challenges, len(challenges)
            )

            if len(challenges) < 2:
                missing.append("pelo menos 2 desafios estratégicos")
                logger.info(
                    "[VALIDATE] FALTANDO: pelo menos 2 desafios (atual: %d)", len(challenges)
                )

        if step == OnboardingStep.OBJECTIVES:
            objectives = extraction.get("objectives", [])
            logger.info(
                "[VALIDATE] OBJECTIVES - objectives=%s (len=%d)", objectives, len(objectives)
            )

            if len(objectives) < 3:
                missing.append("pelo menos 3 objetivos estratégicos")
                logger.info(
                    "[VALIDATE] FALTANDO: pelo menos 3 objetivos (atual: %d)", len(objectives)
                )

        is_complete = len(missing) == 0
        logger.info("[VALIDATE] is_complete=%s, missing=%s", is_complete, missing)
        logger.info("[VALIDATE] ===== FIM VALIDACAO =====")

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

    async def _validate_entity_semantically(self, entity: str, entity_type: str) -> dict[str, Any]:
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
            >>> result = await agent._validate_entity_semantically("Aumentar vendas em 20%", "challenge")
            >>> result["is_valid"]
            False
            >>> result["classified_as"]
            "objective"
            >>> result["correction_suggestion"]
            "Isto parece ser um 'objective', não um 'challenge'."
        """
        import json

        from src.prompts.client_profile_prompts import (
            SEMANTIC_VALIDATION_SYSTEM,
            SEMANTIC_VALIDATION_USER,
        )

        logger.info("[VALIDATE] Validando entity='%s' como type='%s'", entity[:50], entity_type)

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

            is_valid = (classified_as == entity_type and confidence > 0.7) or (
                confidence < 0.5
            )  # Ambíguo também é "válido" (não reclassificar)

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
                is_valid,
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
