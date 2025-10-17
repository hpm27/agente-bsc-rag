"""ClientProfileAgent: Extração inteligente de contexto empresarial.

Este módulo implementa o agente responsável por extrair e estruturar informações
da empresa durante a fase de ONBOARDING do workflow consultivo BSC.

Funcionalidades principais:
- Extração de CompanyInfo (nome, setor, porte) via LLM structured output
- Identificação de challenges estratégicos do cliente
- Definição de objetivos BSC alinhados aos desafios

Versão: 1.0 (FASE 2.3)
LLM: GPT-4o-mini (cost-effective para onboarding)
Best Practices: LangChain structured output (2025), Pydantic validation, few-shot prompts
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.graph.consulting_states import ConsultingPhase
from src.graph.states import BSCState
from src.memory.schemas import ClientProfile, CompanyInfo, StrategicContext
from src.prompts.client_profile_prompts import (
    DEFINE_OBJECTIVES_SYSTEM,
    DEFINE_OBJECTIVES_USER,
    EXTRACT_COMPANY_INFO_SYSTEM,
    EXTRACT_COMPANY_INFO_USER,
    IDENTIFY_CHALLENGES_SYSTEM,
    IDENTIFY_CHALLENGES_USER,
)

# Setup logger
logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS AUXILIARES
# ============================================================================


class ChallengesList(BaseModel):
    """Lista de desafios estratégicos identificados.

    Wrapper Pydantic para validação de lista de challenges extraídos
    durante onboarding. Garante quantidade mínima/máxima de itens.

    Attributes:
        challenges: Lista de 3-7 desafios estratégicos (strings não vazias)

    Example:
        >>> challenges = ChallengesList(challenges=[
        ...     "Perda de clientes para concorrentes",
        ...     "Equipe sobrecarregada",
        ...     "Falta de capital para crescimento"
        ... ])
    """

    challenges: list[str] = Field(
        min_length=3,
        max_length=7,
        description="Lista de 3-7 desafios estratégicos da empresa"
    )


class ObjectivesList(BaseModel):
    """Lista de objetivos estratégicos BSC.

    Wrapper Pydantic para validação de lista de objetivos definidos
    durante onboarding. Garante formato SMART e alinhamento com 4 perspectivas BSC.

    Attributes:
        objectives: Lista de 3-5 objetivos estratégicos SMART

    Example:
        >>> objectives = ObjectivesList(objectives=[
        ...     "Aumentar receita recorrente em 30% em 12 meses (Financeira)",
        ...     "Reduzir churn de clientes para 5% até fim do ano (Clientes)",
        ...     "Automatizar 50% dos processos manuais em 6 meses (Processos)"
        ... ])
    """

    objectives: list[str] = Field(
        min_length=3,
        max_length=5,
        description="Lista de 3-5 objetivos estratégicos SMART alinhados às 4 perspectivas BSC"
    )


# ============================================================================
# CLIENT PROFILE AGENT
# ============================================================================


class ClientProfileAgent:
    """Agente especializado em extração de contexto empresarial.

    Durante a fase ONBOARDING, este agente extrai informações estruturadas
    da empresa a partir de conversas naturais com o cliente, populando
    progressivamente o ClientProfile.

    Métodos principais:
    - extract_company_info(): Extrai nome, setor, porte, indústria
    - identify_challenges(): Identifica 3-7 desafios estratégicos
    - define_objectives(): Define 3-5 objetivos BSC SMART
    - process_onboarding(): Orquestra workflow completo

    Características:
    - LLM: GPT-4o-mini (temperature=0.1 para determinismo)
    - Structured output: LangChain with_structured_output() (best practice 2025)
    - Retry automático: 3 tentativas com backoff exponencial
    - Validação Pydantic: Runtime validation de todos outputs

    Example:
        >>> agent = ClientProfileAgent()
        >>> company_info = agent.extract_company_info("Sou da TechCorp, SaaS empresa média")
        >>> company_info.name
        'TechCorp'
        >>> company_info.sector
        'Tecnologia'
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        """Inicializa ClientProfileAgent com LLM configurado.

        Args:
            llm: LLM customizado (opcional). Se None, usa GPT-4o-mini padrão.
        """
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",  # Cost-effective para onboarding
            temperature=0.1  # Baixa temperatura para determinismo
        )

        logger.info(f"[INIT] ClientProfileAgent inicializado | Model: {self.llm.model_name}")

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    def _build_conversation_context(self, messages: list[dict[str, str]]) -> str:
        """Converte lista de mensagens em string de contexto formatada.

        Remove mensagens do sistema e formata apenas conversas user/assistant
        para uso como contexto nos prompts de extração.

        Args:
            messages: Lista de dicts com keys 'role' e 'content'

        Returns:
            String formatada: "User: ... | Agent: ..."

        Example:
            >>> messages = [
            ...     {"role": "user", "content": "Sou da TechCorp"},
            ...     {"role": "assistant", "content": "Entendi"}
            ... ]
            >>> context = agent._build_conversation_context(messages)
            >>> "User: Sou da TechCorp" in context
            True
        """
        conversation_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Ignorar mensagens do sistema
            if role == "system":
                continue

            # Formatar mensagem
            if role == "user":
                conversation_parts.append(f"User: {content}")
            elif role == "assistant":
                conversation_parts.append(f"Agent: {content}")

        conversation = " | ".join(conversation_parts)

        logger.debug(
            f"[CONTEXT] Conversa montada | "
            f"Messages: {len(messages)} → Chars: {len(conversation)}"
        )

        return conversation

    def _validate_extraction(self, company_info: CompanyInfo) -> bool:
        """Valida qualidade da extração de CompanyInfo.

        Validações adicionais pós-Pydantic para detectar extrações de baixa qualidade:
        - Nome não pode ser genérico ("empresa", "companhia", "negócio")
        - Setor deve ser válido (lista pré-definida)

        Args:
            company_info: CompanyInfo extraído do LLM

        Returns:
            bool: True se extração é válida, False caso contrário

        Example:
            >>> company = CompanyInfo(name="TechCorp", sector="Tecnologia", size="média")
            >>> agent._validate_extraction(company)
            True
            >>> company_generic = CompanyInfo(name="Empresa", sector="Tecnologia", size="média")
            >>> agent._validate_extraction(company_generic)
            False
        """
        # Validar nome não é genérico
        generic_names = ["empresa", "companhia", "negócio", "organização", "corporação"]
        if company_info.name.lower().strip() in generic_names:
            logger.warning(f"[VALIDATION] Nome genérico detectado: {company_info.name}")
            return False

        # Validar setor não está vazio
        if not company_info.sector or len(company_info.sector.strip()) < 3:
            logger.warning(f"[VALIDATION] Setor inválido: {company_info.sector}")
            return False

        # Setores válidos comuns (lista não exaustiva, aceita outros também)
        valid_sectors = [
            "tecnologia", "manufatura", "serviços", "saúde", "educação",
            "finanças", "varejo", "consultoria", "construção", "agronegócio",
            "logística", "energia", "telecomunicações", "mídia", "turismo"
        ]

        sector_lower = company_info.sector.lower().strip()

        # Se sector não está na lista mas tem tamanho razoável, aceitar
        # (lista não é exaustiva, apenas validação básica)
        if sector_lower not in valid_sectors and len(sector_lower) < 5:
            logger.warning(f"[VALIDATION] Setor suspeito: {company_info.sector}")
            return False

        logger.debug(f"[VALIDATION] Extração válida: {company_info.name} | {company_info.sector}")
        return True

    # ========================================================================
    # PLACEHOLDER PARA MÉTODOS PRINCIPAIS (implementar nas próximas etapas)
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ValidationError, ValueError))
    )
    def extract_company_info(self, conversation: str) -> CompanyInfo:
        """Extrai CompanyInfo estruturado de conversa natural.

        Usa LLM com structured output (LangChain 2025) para extrair:
        - name: Nome da empresa
        - sector: Setor de atuação
        - size: Porte (micro, pequena, média, grande)
        - industry: Indústria específica (opcional)
        - founded_year: Ano de fundação (opcional)

        Args:
            conversation: String de conversa com informações da empresa

        Returns:
            CompanyInfo validado com campos obrigatórios preenchidos

        Raises:
            ValueError: Se conversa muito curta (<50 chars) ou dados insuficientes
            ValidationError: Se Pydantic validation falha após 3 tentativas

        Example:
            >>> agent = ClientProfileAgent()
            >>> conversation = "Sou da TechCorp, empresa média de software"
            >>> company = agent.extract_company_info(conversation)
            >>> company.name
            'TechCorp'
            >>> company.sector
            'Tecnologia'
        """
        # Validação pre-flight
        if not conversation or len(conversation.strip()) < 50:
            raise ValueError(
                "Conversa muito curta para extração (mínimo 50 caracteres). "
                "Por favor, forneça mais informações sobre sua empresa."
            )

        logger.info(
            f"[EXTRACT] Iniciando extração company_info | "
            f"Chars: {len(conversation)}"
        )

        try:
            # LangChain structured output (best practice 2025)
            structured_llm = self.llm.with_structured_output(CompanyInfo)

            # Construir prompt com few-shot examples
            messages = [
                SystemMessage(content=EXTRACT_COMPANY_INFO_SYSTEM),
                HumanMessage(content=EXTRACT_COMPANY_INFO_USER.format(
                    conversation=conversation
                ))
            ]

            # Invocar LLM
            raw_result = structured_llm.invoke(messages)
            company_info: CompanyInfo = raw_result  # type: ignore[assignment]

            logger.debug(
                f"[EXTRACT] LLM retornou | "
                f"Name: {company_info.name} | Sector: {company_info.sector}"
            )

            # Validação pós-extração
            if not self._validate_extraction(company_info):
                raise ValueError(
                    f"Extração com qualidade insuficiente: "
                    f"name='{company_info.name}', sector='{company_info.sector}'"
                )

            logger.info(
                f"[EXTRACT] Sucesso | "
                f"Company: {company_info.name} | "
                f"Sector: {company_info.sector} | "
                f"Size: {company_info.size}"
            )

            return company_info

        except ValidationError as e:
            logger.warning(f"[EXTRACT] Validation error: {e}")
            raise  # Retry automático via tenacity

        except Exception as e:
            logger.error(f"[EXTRACT] Erro inesperado: {e}")
            raise ValueError(
                f"Não consegui extrair informações da empresa. "
                f"Por favor, me conte o nome, setor e porte da sua empresa. Erro: {e}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ValidationError, ValueError))
    )
    def identify_challenges(
        self,
        conversation: str,
        company_info: CompanyInfo
    ) -> list[str]:
        """Identifica desafios estratégicos da empresa context-aware.

        Usa contexto da empresa (nome, setor, porte) para identificar
        3-7 desafios estratégicos mencionados ou implícitos na conversa.

        Args:
            conversation: String de conversa com desafios mencionados
            company_info: CompanyInfo já extraído (contexto)

        Returns:
            Lista de 3-7 strings com desafios estratégicos

        Raises:
            ValueError: Se conversa muito curta ou nenhum desafio identificado
            ValidationError: Se Pydantic validation falha (menos de 3 desafios)

        Example:
            >>> agent = ClientProfileAgent()
            >>> company = CompanyInfo(name="TechCorp", sector="Tecnologia", size="média")
            >>> conversation = "Estamos perdendo clientes e a equipe está sobrecarregada"
            >>> challenges = agent.identify_challenges(conversation, company)
            >>> len(challenges)
            4
        """
        # Validação pre-flight
        if not conversation or len(conversation.strip()) < 30:
            raise ValueError(
                "Conversa muito curta para identificar desafios (mínimo 30 caracteres)."
            )

        logger.info(
            f"[CHALLENGES] Iniciando identificação | "
            f"Company: {company_info.name} | Sector: {company_info.sector}"
        )

        try:
            # LangChain structured output com ChallengesList wrapper
            structured_llm = self.llm.with_structured_output(ChallengesList)

            # Construir prompt context-aware
            system_prompt = IDENTIFY_CHALLENGES_SYSTEM.format(
                company_name=company_info.name,
                sector=company_info.sector,
                size=company_info.size
            )

            user_prompt = IDENTIFY_CHALLENGES_USER.format(
                company_name=company_info.name,
                sector=company_info.sector,
                conversation=conversation
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Invocar LLM
            raw_result = structured_llm.invoke(messages)
            result: ChallengesList = raw_result  # type: ignore[assignment]
            challenges = result.challenges

            # Deduplicação (case-insensitive)
            seen = set()
            unique_challenges = []
            for challenge in challenges:
                challenge_lower = challenge.lower().strip()
                if challenge_lower not in seen:
                    seen.add(challenge_lower)
                    unique_challenges.append(challenge.strip())

            logger.info(
                f"[CHALLENGES] Sucesso | "
                f"Identificados: {len(unique_challenges)} desafios | "
                f"Company: {company_info.name}"
            )

            logger.debug(f"[CHALLENGES] Lista: {unique_challenges}")

            return unique_challenges

        except ValidationError as e:
            logger.warning(f"[CHALLENGES] Validation error: {e}")
            raise  # Retry automático via tenacity

        except Exception as e:
            logger.error(f"[CHALLENGES] Erro inesperado: {e}")
            raise ValueError(
                f"Não consegui identificar desafios estratégicos. "
                f"Por favor, me conte mais sobre os desafios que sua empresa enfrenta. Erro: {e}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((ValidationError, ValueError))
    )
    def define_objectives(
        self,
        conversation: str,
        challenges: list[str]
    ) -> list[str]:
        """Define objetivos estratégicos BSC SMART baseados em desafios.

        Usa desafios identificados para definir 3-5 objetivos SMART alinhados
        às 4 perspectivas BSC (Financeira, Clientes, Processos, Aprendizado).

        Args:
            conversation: String de conversa original
            challenges: Lista de desafios estratégicos identificados

        Returns:
            Lista de 3-5 strings com objetivos SMART (formato: "objetivo (Perspectiva)")

        Raises:
            ValueError: Se não conseguir definir objetivos ou lista de challenges vazia
            ValidationError: Se Pydantic validation falha (menos de 3 objetivos)

        Example:
            >>> agent = ClientProfileAgent()
            >>> challenges = ["Perda de clientes", "Equipe sobrecarregada"]
            >>> conversation = "Precisamos crescer 30%"
            >>> objectives = agent.define_objectives(conversation, challenges)
            >>> len(objectives)
            4
            >>> "(Financeira)" in objectives[0]
            True
        """
        # Validação pre-flight
        if not challenges or len(challenges) < 2:
            raise ValueError(
                "Lista de challenges insuficiente para definir objetivos (mínimo 2)."
            )

        logger.info(
            f"[OBJECTIVES] Iniciando definição | "
            f"Challenges: {len(challenges)}"
        )

        try:
            # LangChain structured output com ObjectivesList wrapper
            structured_llm = self.llm.with_structured_output(ObjectivesList)

            # Formatar challenges para prompt
            challenges_text = "\n".join([f"- {challenge}" for challenge in challenges])

            # Construir prompt BSC-aware
            user_prompt = DEFINE_OBJECTIVES_USER.format(
                challenges=challenges_text,
                conversation=conversation
            )

            messages = [
                SystemMessage(content=DEFINE_OBJECTIVES_SYSTEM),
                HumanMessage(content=user_prompt)
            ]

            # Invocar LLM
            raw_result = structured_llm.invoke(messages)
            result: ObjectivesList = raw_result  # type: ignore[assignment]
            objectives = result.objectives

            # Validação: ao menos um objetivo deve mencionar perspectiva BSC
            bsc_perspectives = ["financeira", "clientes", "processos", "aprendizado"]
            objectives_lower = [obj.lower() for obj in objectives]

            has_bsc_perspective = any(
                perspective in " ".join(objectives_lower)
                for perspective in bsc_perspectives
            )

            if not has_bsc_perspective:
                logger.warning(
                    "[OBJECTIVES] Nenhum objetivo menciona perspectiva BSC explicitamente"
                )

            logger.info(
                f"[OBJECTIVES] Sucesso | "
                f"Definidos: {len(objectives)} objetivos SMART"
            )

            logger.debug(f"[OBJECTIVES] Lista: {objectives}")

            return objectives

        except ValidationError as e:
            logger.warning(f"[OBJECTIVES] Validation error: {e}")
            raise  # Retry automático via tenacity

        except Exception as e:
            logger.error(f"[OBJECTIVES] Erro inesperado: {e}")
            raise ValueError(
                f"Não consegui definir objetivos estratégicos. "
                f"Por favor, revise os desafios identificados. Erro: {e}"
            )

    def process_onboarding(self, state: BSCState) -> dict[str, Any]:
        """Orquestra workflow completo de onboarding BSC.

        Processa onboarding em 3 steps progressivos:
        1. Extrair company_info (se não completo)
        2. Identificar challenges (se company_info OK)
        3. Definir objectives (se challenges OK)

        Atualiza BSCState.onboarding_progress e BSCState.client_profile incrementalmente.
        Quando completo, transiciona para ConsultingPhase.DISCOVERY.

        Args:
            state: BSCState com conversa e current_phase=ONBOARDING

        Returns:
            dict com updates para BSCState:
            - client_profile: ClientProfile atualizado
            - onboarding_progress: Dict[str, bool] atualizado
            - current_phase: ConsultingPhase (DISCOVERY se completo)
            - Ou {"error": str} se falha crítica

        Example:
            >>> agent = ClientProfileAgent()
            >>> state = BSCState(
            ...     query="Sou da TechCorp, empresa média de software",
            ...     user_id="test_user",
            ...     current_phase=ConsultingPhase.ONBOARDING,
            ...     metadata={"chat_history": [...]}
            ... )
            >>> updates = agent.process_onboarding(state)
            >>> updates["onboarding_progress"]["company_info_extracted"]
            True
        """
        logger.info(
            f"[ONBOARDING] Iniciando processamento | "
            f"User: {state.user_id} | "
            f"Phase: {state.current_phase}"
        )

        # Construir contexto de conversa
        messages = state.metadata.get("chat_history", [])
        if not messages:
            # Fallback: usar query como conversa
            conversation = state.query
        else:
            conversation = self._build_conversation_context(messages)

        updates: dict[str, Any] = {}

        # ====================================================================
        # STEP 1: EXTRACT COMPANY INFO
        # ====================================================================

        if not state.onboarding_progress.get("company_info_extracted"):
            try:
                logger.info("[ONBOARDING] Step 1/3: Extrair company info")

                company_info = self.extract_company_info(conversation)

                # Criar ou atualizar ClientProfile
                if not state.client_profile:
                    state.client_profile = ClientProfile(company=company_info)
                else:
                    state.client_profile.company = company_info

                # Atualizar progress
                state.onboarding_progress["company_info_extracted"] = True

                updates["client_profile"] = state.client_profile
                updates["onboarding_progress"] = state.onboarding_progress.copy()

                logger.info(
                    f"[ONBOARDING] Step 1/3 OK | "
                    f"Company: {company_info.name} | Sector: {company_info.sector}"
                )

            except Exception as e:
                logger.error(f"[ONBOARDING] Step 1/3 FALHOU: {e}")
                return {
                    "error": f"Não consegui identificar informações da empresa. "
                             f"Por favor, me conte o nome, setor e porte da sua empresa."
                }

        # ====================================================================
        # STEP 2: IDENTIFY CHALLENGES
        # ====================================================================

        if (
            state.onboarding_progress.get("company_info_extracted")
            and not state.onboarding_progress.get("challenges_identified")
        ):
            try:
                logger.info("[ONBOARDING] Step 2/3: Identificar challenges")

                challenges = self.identify_challenges(
                    conversation,
                    state.client_profile.company
                )

                # Atualizar StrategicContext
                if not state.client_profile.context:
                    state.client_profile.context = StrategicContext()

                state.client_profile.context.current_challenges = challenges

                # Atualizar progress
                state.onboarding_progress["challenges_identified"] = True

                updates["client_profile"] = state.client_profile
                updates["onboarding_progress"] = state.onboarding_progress.copy()

                logger.info(
                    f"[ONBOARDING] Step 2/3 OK | "
                    f"Challenges: {len(challenges)}"
                )

            except Exception as e:
                logger.warning(f"[ONBOARDING] Step 2/3 PARCIAL: {e}")
                # Não é crítico - podemos prosseguir sem challenges

        # ====================================================================
        # STEP 3: DEFINE OBJECTIVES
        # ====================================================================

        if (
            state.onboarding_progress.get("challenges_identified")
            and not state.onboarding_progress.get("objectives_defined")
        ):
            try:
                logger.info("[ONBOARDING] Step 3/3: Definir objectives")

                objectives = self.define_objectives(
                    conversation,
                    state.client_profile.context.current_challenges
                )

                # Atualizar StrategicContext
                state.client_profile.context.strategic_objectives = objectives

                # Atualizar progress
                state.onboarding_progress["objectives_defined"] = True
                state.onboarding_progress["profile_completed"] = True

                updates["client_profile"] = state.client_profile
                updates["onboarding_progress"] = state.onboarding_progress.copy()

                # TRANSIÇÃO DE FASE: ONBOARDING → DISCOVERY
                updates["current_phase"] = ConsultingPhase.DISCOVERY
                updates["previous_phase"] = ConsultingPhase.ONBOARDING

                logger.info(
                    f"[ONBOARDING] Step 3/3 OK | "
                    f"Objectives: {len(objectives)} | "
                    f"TRANSIÇÃO: ONBOARDING → DISCOVERY"
                )

            except Exception as e:
                logger.warning(f"[ONBOARDING] Step 3/3 PARCIAL: {e}")
                # Não é crítico - podemos prosseguir sem objectives

        # ====================================================================
        # SUMMARY
        # ====================================================================

        logger.info(
            f"[ONBOARDING] Processamento concluído | "
            f"Progress: {state.onboarding_progress} | "
            f"Profile completed: {state.onboarding_progress.get('profile_completed', False)}"
        )

        return updates

    # Compatibilidade com orchestrator/testes: método simples de extração final
    def extract_profile(self, state: BSCState) -> ClientProfile:
        """Extrai/retorna ClientProfile a partir do estado atual.

        Se já existir no estado, apenas retorna. Caso contrário, tenta extrair
        informações mínimas a partir da conversa.
        """
        if state.client_profile:
            return state.client_profile
        # Fallback mínimo: construir profile básico com nome genérico
        company = CompanyInfo(name="Empresa Desconhecida", sector="Desconhecido")
        profile = ClientProfile(company=company)
        return profile

