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
from collections import defaultdict
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseLLM


def _get_current_date_pt_br() -> tuple[str, str]:
    """Retorna data atual formatada em português brasileiro.

    SESSAO 45: Função helper para incluir data atual nos prompts LLM,
    evitando que o modelo sugira datas passadas em planos de ação.

    Returns:
        Tuple com:
        - Data curta (DD/MM/YYYY)
        - Data por extenso em português (ex: "terça-feira, 25 de novembro de 2025")
    """
    now = datetime.now()
    date_short = now.strftime("%d/%m/%Y")

    # Mapeamento dias da semana
    days_pt = {
        "Monday": "segunda-feira",
        "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira",
        "Friday": "sexta-feira",
        "Saturday": "sábado",
        "Sunday": "domingo",
    }

    # Mapeamento meses
    months_pt = {
        "January": "janeiro",
        "February": "fevereiro",
        "March": "março",
        "April": "abril",
        "May": "maio",
        "June": "junho",
        "July": "julho",
        "August": "agosto",
        "September": "setembro",
        "October": "outubro",
        "November": "novembro",
        "December": "dezembro",
    }

    day_name = days_pt.get(now.strftime("%A"), now.strftime("%A"))
    month_name = months_pt.get(now.strftime("%B"), now.strftime("%B"))
    day = now.day
    year = now.year

    date_full = f"{day_name}, {day} de {month_name} de {year}"

    return date_short, date_full


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
    """Steps do processo de onboarding BSC.

    SESSAO 49 (Dez/2025): Atualizado baseado em Kaplan & Norton best practices.
    - Adicionadas perguntas de estrategia/visao ANTES dos desafios
    - Adicionada identificacao de estagio do negocio (Growth/Sustain/Harvest)
    - Adicionadas perguntas de segmentacao de clientes

    Steps 1-6: OBRIGATORIOS (minimo para diagnostico BSC completo)
    Steps 7-10: OPCIONAIS (enriquecem diagnostico se coletados)
    Steps 11-14: PERSPECTIVAS BSC (sob demanda para aprofundamento)

    Fluxo adaptativo: coleta oportunistica permite pular steps se
    informacoes ja foram fornecidas em mensagens anteriores.
    """

    # OBRIGATORIOS - Core do diagnostico BSC (ordem Kaplan & Norton)
    COMPANY_INFO = 1  # Nome, setor, tamanho da empresa
    STRATEGY_VISION = 2  # NOVO: Visao, proposta de valor, diferenciais
    BUSINESS_STAGE = 3  # NOVO: Growth/Sustain/Harvest (determina KPIs)
    CUSTOMER_SEGMENTATION = 4  # NOVO: Segmentos-alvo, proposta por segmento
    CHALLENGES = 5  # Desafios estrategicos atuais (minimo 2)
    OBJECTIVES = 6  # Objetivos nas 4 perspectivas BSC (minimo 3)

    # OPCIONAIS - Enriquecem diagnostico (Kaplan & Norton best practices)
    MVV = 7  # Missao, Visao, Valores (Stage 1 - Execution Premium)
    COMPETITIVE_CONTEXT = 8  # Concorrentes, diferenciacao
    ORGANIZATION_STRUCTURE = 9  # Departamentos, sistemas, pessoas, processos
    PROJECT_CONSTRAINTS = 10  # Timeline, sponsor, criterios de sucesso

    # PERSPECTIVAS BSC DETALHADAS (sob demanda para aprofundamento)
    BSC_FINANCIAL = 11  # Perspectiva Financeira detalhada
    BSC_CUSTOMER = 12  # Perspectiva Clientes detalhada
    BSC_PROCESS = 13  # Perspectiva Processos detalhada
    BSC_LEARNING = 14  # Perspectiva Aprendizado detalhada


class OnboardingAgent:
    """
    Agente orquestrador conversacional para fase ONBOARDING.

    Responsabilidades:
    - Gerenciar diálogo multi-turn com cliente
    - Integrar ClientProfileAgent para extração progressiva
    - Implementar follow-up inteligente quando informações incompletas
    - Atualizar BSCState.onboarding_progress
    - Transicao automatica ONBOARDING -> DISCOVERY quando completo

    Workflow de 7 Steps (Kaplan & Norton + Consulting Best Practices 2025):

    OBRIGATÓRIOS (Core do diagnóstico):
    1. COMPANY_INFO: Nome, setor, tamanho da empresa
    2. CHALLENGES: Principais desafios estratégicos (mínimo 2)
    3. OBJECTIVES: Objetivos nas 4 perspectivas BSC (mínimo 3)

    OPCIONAIS (Enriquecem diagnóstico - pergunta se completude básica >= 60%):
    4. MVV: Missão, Visão, Valores da empresa
    5. COMPETITIVE_CONTEXT: Concorrentes, diferenciação, clientes-alvo
    6. ORGANIZATION_STRUCTURE: Departamentos, sistemas, pessoas, processos
    7. PROJECT_CONSTRAINTS: Timeline, sponsor, critérios de sucesso

    Fluxo Adaptativo:
    - Se usuário fornecer info avançada ANTES, registra e pula step
    - Confirmação quando completude >= 90% OU steps 1-3 100% completos
    - Steps 4-7 são perguntados apenas se tempo/interesse do usuário permitir

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
        # SESSAO 50 (Dez/2025): Usar defaultdict para evitar KeyError quando acessar
        # qualquer step (int ou IntEnum). defaultdict(int) retorna 0 para keys inexistentes.
        self.followup_count: dict[int, int] = defaultdict(int)

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
        # SESSAO 50: Manter como defaultdict para evitar KeyError com novos steps
        self.followup_count = defaultdict(int)

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
        # SESSAO 50 (Dez/2025): Expandir debug para mostrar TODOS os campos relevantes
        print(
            f"[DEBUG COLLECT] Extração completa: "
            f"has_company_info={extraction_result.has_company_info}, "
            f"company_name={extraction_result.company_info.name if extraction_result.company_info else None}, "
            f"challenges={len(extraction_result.challenges)}, "
            f"objectives={len(extraction_result.objectives)}, "
            f"has_investments_projects={extraction_result.has_investments_projects}, "
            f"pending_projects={len(extraction_result.pending_projects)}, "
            f"investments_needed={len(extraction_result.investments_needed)}, "
            f"has_mvv={extraction_result.has_mvv}, "
            f"has_competitive_context={extraction_result.has_competitive_context}, "
            f"business_stage={extraction_result.business_stage}, "
            f"has_business_stage={extraction_result.has_business_stage}",
            flush=True,
        )

        # ========================================================================
        # SESSAO 46: Adapter expandido com TODOS os novos campos
        # Best Practice Microsoft (Mar 2025): Incremental Extraction
        # ========================================================================
        extracted_entities = {
            # CORE (obrigatórios)
            "company_name": (
                extraction_result.company_info.name if extraction_result.company_info else None
            ),
            "industry": (
                extraction_result.company_info.sector if extraction_result.company_info else None
            ),
            "size": extraction_result.company_info.size if extraction_result.company_info else None,
            "revenue": None,
            "challenges": extraction_result.challenges,
            "goals": extraction_result.objectives,
            # MVV
            "mission": extraction_result.mission,
            "vision": extraction_result.vision,
            "core_values": extraction_result.core_values,
            # COMPETITIVE
            "competitors": extraction_result.competitors,
            "competitive_advantages": extraction_result.competitive_advantages,
            "target_customers": extraction_result.target_customers,
            # BUSINESS STAGE (SESSAO 50)
            "business_stage": extraction_result.business_stage,
            # ORGANIZATION
            "departments": extraction_result.departments,
            "key_systems": extraction_result.key_systems,
            "current_metrics": extraction_result.current_metrics,
            # SESSAO 46: NOVOS CAMPOS DETALHADOS
            "key_people": extraction_result.key_people,
            "business_process_description": extraction_result.business_process_description,
            "process_bottlenecks": extraction_result.process_bottlenecks,
            "employee_count": extraction_result.employee_count,
            "team_distribution": extraction_result.team_distribution,
            "production_metrics": extraction_result.production_metrics,
            "financial_metrics": extraction_result.financial_metrics,
            "investments_needed": extraction_result.investments_needed,
            "pending_projects": extraction_result.pending_projects,
            "pain_points": extraction_result.pain_points,
            "technology_gaps": extraction_result.technology_gaps,
            # PROJECT CONSTRAINTS
            "timeline": extraction_result.timeline,
            "sponsor_name": extraction_result.sponsor_name,
            "success_criteria": extraction_result.success_criteria,
            "previous_initiatives": extraction_result.previous_initiatives,  # SESSAO 47: Bug fix - campo estava no schema mas nao sendo extraido
        }

        # SESSAO 46: Confidence scores expandidos
        confidence_scores = {
            # CORE
            "company_name": 1.0 if extraction_result.has_company_info else 0.0,
            "industry": 1.0 if extraction_result.has_company_info else 0.0,
            "size": 1.0 if extraction_result.has_company_info else 0.0,
            "challenges": 1.0 if extraction_result.has_challenges else 0.0,
            "goals": 1.0 if extraction_result.has_objectives else 0.0,
            # MVV
            "mission": 1.0 if extraction_result.has_mvv else 0.0,
            "vision": 1.0 if extraction_result.has_mvv else 0.0,
            "core_values": 1.0 if extraction_result.has_mvv else 0.0,
            # COMPETITIVE
            "competitors": 1.0 if extraction_result.has_competitive_context else 0.0,
            "competitive_advantages": 1.0 if extraction_result.has_competitive_context else 0.0,
            "target_customers": 1.0 if extraction_result.has_competitive_context else 0.0,
            # BUSINESS STAGE (SESSAO 50)
            "business_stage": 1.0 if extraction_result.has_business_stage else 0.0,
            # ORGANIZATION
            "departments": 1.0 if extraction_result.has_organization_structure else 0.0,
            "key_systems": 1.0 if extraction_result.has_organization_structure else 0.0,
            "current_metrics": 1.0 if extraction_result.has_operational_metrics else 0.0,
            # NOVOS CAMPOS SESSAO 46
            "key_people": 1.0 if extraction_result.has_key_people else 0.0,
            "business_process_description": 1.0 if extraction_result.has_business_process else 0.0,
            "process_bottlenecks": 1.0 if extraction_result.has_business_process else 0.0,
            "employee_count": 1.0 if extraction_result.has_team_structure else 0.0,
            "team_distribution": 1.0 if extraction_result.has_team_structure else 0.0,
            "production_metrics": 1.0 if extraction_result.has_operational_metrics else 0.0,
            "financial_metrics": 1.0 if extraction_result.has_operational_metrics else 0.0,
            "investments_needed": 1.0 if extraction_result.has_investments_projects else 0.0,
            "pending_projects": 1.0 if extraction_result.has_investments_projects else 0.0,
            "pain_points": 1.0 if extraction_result.has_pain_points else 0.0,
            "technology_gaps": 1.0 if extraction_result.has_pain_points else 0.0,
            # PROJECT CONSTRAINTS
            "timeline": 1.0 if extraction_result.has_project_constraints else 0.0,
            "sponsor_name": 1.0 if extraction_result.has_project_constraints else 0.0,
            "success_criteria": 1.0 if extraction_result.has_project_constraints else 0.0,
            "previous_initiatives": (
                1.0 if extraction_result.has_project_constraints else 0.0
            ),  # SESSAO 47: Bug fix
        }

        # ========================================================================
        # STEP 2: Inicializar partial_profile se não existir
        # SESSAO 46: Expandido com TODOS os novos campos (Best Practice Microsoft)
        # ========================================================================
        if "partial_profile" not in state.metadata:
            print("[DEBUG COLLECT] INICIALIZANDO partial_profile (PRIMEIRA VEZ)", flush=True)
            logger.info("[COLLECT] INICIALIZANDO partial_profile (PRIMEIRA VEZ)")
            state.metadata["partial_profile"] = {
                # CORE (obrigatórios)
                "company_name": None,
                "industry": None,
                "size": None,
                "revenue": None,
                "challenges": [],
                "goals": [],
                # MVV
                "mission": None,
                "vision": None,
                "core_values": [],
                # COMPETITIVE
                "competitors": [],
                "competitive_advantages": [],
                "target_customers": [],
                # BUSINESS STAGE (SESSAO 50)
                "business_stage": None,
                # ORGANIZATION
                "departments": [],
                "key_systems": [],
                "current_metrics": [],
                # SESSAO 46: NOVOS CAMPOS DETALHADOS
                "key_people": [],  # list[dict] com name, role, responsibilities
                "business_process_description": None,  # string descritiva do fluxo
                "process_bottlenecks": [],  # gargalos identificados
                "employee_count": None,  # int
                "team_distribution": {},  # dict com departamento -> headcount
                "production_metrics": {},  # métricas atuais vs metas
                "financial_metrics": {},  # métricas financeiras
                "investments_needed": [],  # investimentos necessários
                "pending_projects": [],  # projetos em andamento
                "pain_points": [],  # dores específicas
                "technology_gaps": [],  # gaps tecnológicos
                # PROJECT CONSTRAINTS
                "timeline": None,
                "sponsor_name": None,
                "success_criteria": [],
                "previous_initiatives": [],  # SESSAO 47: Bug fix - campo estava no schema mas nao inicializado
                # CONFIDENCE TRACKING (Best Practice Sparkco 2025)
                "confidence_scores": {},  # score por campo
                # SESSAO 49: Rastrear perguntas já feitas para evitar repetição
                # mesmo quando usuário responde "não sei/não sabemos"
                "questions_asked": [],  # lista de topics já perguntados
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

        # SESSAO 49: Bug fix - Salvar profile ANTES da atualizacao para detectar repeticao corretamente
        # Problema: _detect_user_repetition comparava mensagem com dados recem-extraidos dela mesma
        # Solucao: Usar profile ANTERIOR para detectar repeticao (nao o atualizado)
        import copy

        partial_profile_before_update = copy.deepcopy(partial_profile)

        # ========================================================================
        # STEP 3: Acumular conhecimento com Update-on-Change
        # SESSAO 46: Best Practice Microsoft (Mar 2025) - Incremental Extraction
        # Regras:
        # - Listas: APPEND (não substituir) + deduplicate
        # - Strings: UPDATE se novo valor é mais completo/específico
        # - Dicts: DEEP MERGE (preservar chaves existentes)
        # ========================================================================

        # Definir campos por tipo para aplicar regras corretas
        LIST_FIELDS = [
            "challenges",
            "goals",
            "core_values",
            "competitors",
            "competitive_advantages",
            "target_customers",
            "departments",
            "key_systems",
            "current_metrics",
            "key_people",
            "process_bottlenecks",
            "investments_needed",
            "pending_projects",
            "pain_points",
            "technology_gaps",
            "success_criteria",
        ]
        DICT_FIELDS = ["team_distribution", "production_metrics", "financial_metrics"]
        # SESSAO 50 (Dez/2025): Adicionado business_stage para fluxo de 14 steps
        STRING_FIELDS = [
            "company_name",
            "industry",
            "size",
            "revenue",
            "mission",
            "vision",
            "business_stage",  # NOVO: Growth/Sustain/Harvest
            "business_process_description",
            "timeline",
            "sponsor_name",
        ]
        INT_FIELDS = ["employee_count"]

        for field, value in extracted_entities.items():
            current_value = partial_profile.get(field)
            confidence = confidence_scores.get(field, 0.0)

            # Skip se valor novo é None ou vazio
            if value is None or (isinstance(value, (list, dict, str)) and not value):
                continue

            # REGRA 1: Listas - APPEND com deduplicate
            if field in LIST_FIELDS:
                if isinstance(value, list):
                    current_list = current_value if isinstance(current_value, list) else []
                    for item in value:
                        # Deduplicate: verificar se item já existe
                        # Para dicts (key_people, pending_projects), comparar por 'name'
                        if isinstance(item, dict):
                            item_name = item.get("name", str(item))
                            existing_names = [
                                i.get("name", str(i)) for i in current_list if isinstance(i, dict)
                            ]
                            if item_name not in existing_names:
                                current_list.append(item)
                        elif item not in current_list:
                            current_list.append(item)
                    partial_profile[field] = current_list

            # REGRA 2: Dicts - DEEP MERGE
            elif field in DICT_FIELDS:
                if isinstance(value, dict):
                    current_dict = current_value if isinstance(current_value, dict) else {}
                    # Merge: novas chaves + update existentes se mais específicas
                    for k, v in value.items():
                        if k not in current_dict or (v is not None and current_dict.get(k) is None):
                            current_dict[k] = v
                    partial_profile[field] = current_dict

            # REGRA 3: Strings - UPDATE se mais completo
            elif field in STRING_FIELDS:
                if confidence > 0.5:
                    # Update se: (a) atual é None, (b) novo é mais longo/específico
                    if current_value is None:
                        partial_profile[field] = value
                    elif isinstance(value, str) and isinstance(current_value, str):
                        # Update se novo valor é mais longo (mais específico)
                        if len(value) > len(current_value):
                            partial_profile[field] = value

            # REGRA 4: Inteiros - UPDATE se atual é None
            elif field in INT_FIELDS:
                if value is not None and confidence > 0.5:
                    if current_value is None:
                        partial_profile[field] = value

        # Salvar confidence scores para tracking
        partial_profile["confidence_scores"] = {
            **partial_profile.get("confidence_scores", {}),
            **{k: v for k, v in confidence_scores.items() if v > 0},
        }

        # Atualizar metadata
        state.metadata["partial_profile"] = partial_profile

        # DEBUGGING: Log completo do partial_profile
        # SESSAO 50 (Dez/2025): Expandir para incluir pending_projects, investments_needed
        print(
            f"[DEBUG COLLECT] Perfil acumulado: "
            f"company_name={partial_profile.get('company_name')}, "
            f"industry={partial_profile.get('industry')}, "
            f"size={partial_profile.get('size')}, "
            f"challenges={len(partial_profile.get('challenges', []))}, "
            f"goals={len(partial_profile.get('goals', []))}, "
            f"pending_projects={len(partial_profile.get('pending_projects', []))}, "
            f"investments_needed={len(partial_profile.get('investments_needed', []))}",
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

        # ========================================================================
        # SESSAO DEZ/2025: PROCESSAMENTO FASES 2 E 3 (Steps 7-14)
        # Kaplan & Norton best practices: Enriquecimento + Perspectivas BSC
        # ========================================================================
        current_onboarding_phase = state.metadata.get("onboarding_phase", "identification")
        current_enrichment_step = state.metadata.get("current_enrichment_step")

        print(
            f"[DEBUG COLLECT] Fase atual: {current_onboarding_phase} | Step: {current_enrichment_step}",
            flush=True,
        )

        # Verificar se estamos em FASE 2 (enrichment) ou FASE 3 (bsc_kpis)
        if current_onboarding_phase in ["enrichment", "bsc_kpis"]:
            # Processar resposta do usuario para os steps 7-14
            result = await self._process_enrichment_step(
                user_message=user_message,
                state=state,
                partial_profile=partial_profile,
                extracted_entities=extracted_entities,
                extraction_result=extraction_result,
            )

            if result is not None:
                # Step processado, retornar resultado
                return result

        # STEP 4: Verificar se informações mínimas estão completas
        # STEP 1: COMPANY_INFO - Dados básicos da empresa
        has_company_name = partial_profile.get("company_name") is not None
        has_industry = partial_profile.get("industry") is not None
        has_size_or_revenue = (
            partial_profile.get("size") is not None or partial_profile.get("revenue") is not None
        )

        # STEP 2: STRATEGY_VISION - Proposta de valor única (OBRIGATÓRIO desde Dez/2025)
        # Usa campos existentes: vision, competitive_advantages, mission
        # IMPORTANTE: competitive_advantages é LISTA, verificar len > 0
        has_strategy_vision = (
            (partial_profile.get("vision") is not None and partial_profile.get("vision") != "")
            or len(partial_profile.get("competitive_advantages", [])) > 0
            or (partial_profile.get("mission") is not None and partial_profile.get("mission") != "")
        )

        # STEP 3: BUSINESS_STAGE - Fase do negócio (OBRIGATÓRIO desde Dez/2025)
        has_business_stage = partial_profile.get("business_stage") is not None

        # STEP 4: CUSTOMER_SEGMENTATION - Segmentos de clientes (OBRIGATÓRIO desde Dez/2025)
        # Usa campo existente: target_customers (lista)
        has_customer_segmentation = (
            partial_profile.get("target_customers") is not None
            and len(partial_profile.get("target_customers", [])) > 0
        )

        # STEP 5: CHALLENGES - Mínimo 2 desafios estratégicos
        has_min_challenges = len(partial_profile.get("challenges", [])) >= 2

        # STEP 6: OBJECTIVES - Mínimo 2 objetivos (reduzido de 3 para 2)
        has_min_objectives = len(partial_profile.get("goals", [])) >= 2

        # SESSAO DEZ/2025: Verificar TODOS os 6 steps obrigatórios do BSC Onboarding Workflow
        minimum_info_complete = (
            # Step 1: Company Info
            has_company_name
            and has_industry
            and has_size_or_revenue
            # Step 2: Strategy Vision (NOVO)
            and has_strategy_vision
            # Step 3: Business Stage (NOVO)
            and has_business_stage
            # Step 4: Customer Segmentation (NOVO)
            and has_customer_segmentation
            # Step 5: Challenges
            and has_min_challenges
            # Step 6: Objectives
            and has_min_objectives
        )

        # DEBUG: Mostrar quais steps estão completos
        print(
            f"[DEBUG COLLECT] Steps Status: "
            f"1.CompanyInfo={has_company_name and has_industry and has_size_or_revenue} | "
            f"2.StrategyVision={has_strategy_vision} | "
            f"3.BusinessStage={has_business_stage} | "
            f"4.CustomerSeg={has_customer_segmentation} | "
            f"5.Challenges={has_min_challenges} | "
            f"6.Objectives={has_min_objectives} | "
            f"COMPLETE={minimum_info_complete}",
            flush=True,
        )

        # DEBUG EXTRA: Mostrar valores dos campos para diagnóstico
        print(
            f"[DEBUG COLLECT] Campos Step 2: vision={partial_profile.get('vision')}, "
            f"competitive_advantages={partial_profile.get('competitive_advantages')}, "
            f"mission={partial_profile.get('mission')}",
            flush=True,
        )
        print(
            f"[DEBUG COLLECT] Campos Step 3-4: business_stage={partial_profile.get('business_stage')}, "
            f"target_customers={partial_profile.get('target_customers')}",
            flush=True,
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

                # BEST PRACTICE Nov/2025: Usar Concat-and-Retry para confirmação
                # Gerar confirmação com contexto LIMPO (evita Lost in Middle)
                # Fallback para mensagem estruturada se LLM falhar
                try:
                    confirmation_message = await self._generate_confirmation_clean_context(
                        partial_profile
                    )
                    # Adicionar instrução de confirmação ao final
                    confirmation_message += (
                        "\n\n_(Responda 'sim' para continuar ou 'não' se quiser corrigir algo)_"
                    )
                except Exception as e:
                    logger.warning(
                        "[COLLECT] Erro ao gerar confirmação com contexto limpo: %s. Usando fallback.",
                        e,
                    )
                    # Fallback: mensagem estruturada EXPANDIDA (SESSAO 46)
                    # CORRECAO SESSAO 46: Indentação corrigida - código deve estar DENTRO do except
                    company_name = partial_profile.get("company_name", "sua empresa")
                    sector = partial_profile.get("industry", "N/A")
                    size = partial_profile.get("size", "N/A")
                    challenges = partial_profile.get("challenges", [])
                    goals = partial_profile.get("goals", [])

                    # SESSAO 46: Novos campos
                    key_people = partial_profile.get("key_people", [])
                    employee_count = partial_profile.get("employee_count")
                    business_process = partial_profile.get("business_process_description")
                    process_bottlenecks = partial_profile.get("process_bottlenecks", [])
                    production_metrics = partial_profile.get("production_metrics", {})
                    investments_needed = partial_profile.get("investments_needed", [])
                    pending_projects = partial_profile.get("pending_projects", [])
                    pain_points = partial_profile.get("pain_points", [])
                    technology_gaps = partial_profile.get("technology_gaps", [])

                    # Formatar listas base
                    challenges_text = "\n".join([f"  - {c}" for c in challenges[:8]])
                    goals_text = "\n".join([f"  - {g}" for g in goals[:5]])

                    # SESSAO 46: Formatar novos campos
                    key_people_text = ""
                    if key_people:
                        people_items = []
                        for p in key_people[:5]:
                            name = p.get("name", "N/A")
                            role = p.get("role", "")
                            resp = ", ".join(p.get("responsibilities", [])[:3])
                            people_items.append(f"  - **{name}** ({role}): {resp}")
                        key_people_text = "\n".join(people_items)

                    metrics_text = ""
                    if production_metrics:
                        metrics_items = [f"  - {k}: {v}" for k, v in production_metrics.items()]
                        metrics_text = "\n".join(metrics_items[:5])

                    investments_text = ""
                    if investments_needed:
                        investments_text = "\n".join([f"  - {i}" for i in investments_needed[:5]])

                    projects_text = ""
                    if pending_projects:
                        proj_items = []
                        for proj in pending_projects[:3]:
                            proj_name = proj.get("name", "Projeto")
                            proj_deadline = proj.get("deadline", "N/A")
                            proj_items.append(f"  - {proj_name} (prazo: {proj_deadline})")
                        projects_text = "\n".join(proj_items)

                    bottlenecks_text = ""
                    if process_bottlenecks:
                        bottlenecks_text = "\n".join([f"  - {b}" for b in process_bottlenecks[:5]])

                    pain_tech_text = ""
                    all_pains = (pain_points or []) + (technology_gaps or [])
                    if all_pains:
                        pain_tech_text = "\n".join([f"  - {p}" for p in all_pains[:5]])

                    # Construir mensagem de confirmação COMPLETA
                    confirmation_parts = [
                        f"""Perfeito! Deixa eu confirmar as informacoes coletadas:

**EMPRESA**
- Nome: {company_name}
- Setor: {sector}
- Porte: {size}"""
                    ]

                    if employee_count:
                        confirmation_parts.append(f"- Funcionarios: {employee_count}")

                    if key_people_text:
                        confirmation_parts.append(
                            f"\n**PESSOAS-CHAVE ({len(key_people)})**\n{key_people_text}"
                        )

                    if business_process:
                        confirmation_parts.append(
                            f"\n**PROCESSO DE NEGOCIO**\n  {business_process[:150]}..."
                        )

                    if bottlenecks_text:
                        confirmation_parts.append(
                            f"\n**GARGALOS IDENTIFICADOS ({len(process_bottlenecks)})**\n{bottlenecks_text}"
                        )

                    if challenges_text:
                        confirmation_parts.append(
                            f"\n**DESAFIOS ESTRATEGICOS ({len(challenges)})**\n{challenges_text}"
                        )

                    if goals_text:
                        confirmation_parts.append(f"\n**OBJETIVOS ({len(goals)})**\n{goals_text}")

                    if metrics_text:
                        confirmation_parts.append(f"\n**METRICAS DE PRODUCAO**\n{metrics_text}")

                    if investments_text:
                        confirmation_parts.append(
                            f"\n**INVESTIMENTOS NECESSARIOS ({len(investments_needed)})**\n{investments_text}"
                        )

                    if projects_text:
                        confirmation_parts.append(
                            f"\n**PROJETOS EM ANDAMENTO ({len(pending_projects)})**\n{projects_text}"
                        )

                    if pain_tech_text:
                        confirmation_parts.append(
                            f"\n**DORES E GAPS TECNOLOGICOS ({len(all_pains)})**\n{pain_tech_text}"
                        )

                    confirmation_parts.append(
                        "\nEsta correto? Posso prosseguir para o diagnostico BSC?\n\n_(Responda 'sim' para continuar ou 'nao' para corrigir)_"
                    )

                    confirmation_message = "\n".join(confirmation_parts)

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
                # CONFIRMADO Steps 1-6! Verificar em qual fase estamos
                current_onboarding_phase = state.metadata.get("onboarding_phase", "identification")

                logger.info(
                    "[COLLECT] ===== CONFIRMACAO RECEBIDA! Fase atual: %s =====",
                    current_onboarding_phase,
                )

                # Atualizar ClientProfile no state (fazer em qualquer fase)
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

                # SESSAO DEZ/2025: FLUXO DE 14 STEPS (Kaplan & Norton)
                # FASE 1 (identification) -> FASE 2 (enrichment) -> FASE 3 (bsc_kpis) -> DISCOVERY

                if current_onboarding_phase == "identification":
                    # Steps 1-6 completos! Iniciar FASE 2 (Steps 7-10 - Enriquecimento)
                    logger.info(
                        "[COLLECT] ===== INICIANDO FASE 2 - ENRIQUECIMENTO (Steps 7-10) ====="
                    )

                    state.metadata["awaiting_confirmation"] = False
                    state.metadata["onboarding_phase"] = "enrichment"
                    state.metadata["current_enrichment_step"] = 7  # MVV

                    # Pergunta Step 7: MVV (Missao, Visao, Valores)
                    enrichment_intro = (
                        f"Perfeito! As informacoes basicas de {partial_profile.get('company_name', 'sua empresa')} "
                        f"estao registradas.\n\n"
                        f"Agora vou fazer algumas perguntas de **enriquecimento** para um diagnostico BSC mais completo. "
                        f"Se voce nao souber ou preferir pular, basta responder 'nao sei' ou 'pular'.\n\n"
                        f"**Step 7 - Missao, Visao e Valores:**\n"
                        f"Qual a **missao** (razao de existir), **visao** (onde querem chegar em 5-10 anos) "
                        f"e **valores** (principios que guiam a empresa) da {partial_profile.get('company_name', 'empresa')}?"
                    )

                    return {
                        "question": enrichment_intro,
                        "is_complete": False,
                        "extracted_entities": extracted_entities,
                        "accumulated_profile": partial_profile,
                        "metadata": {
                            "partial_profile": partial_profile,
                            "awaiting_confirmation": False,
                            "onboarding_phase": "enrichment",
                            "current_enrichment_step": 7,
                            "conversation_history": state.metadata.get("conversation_history", []),
                        },
                    }

                elif current_onboarding_phase == "enrichment":
                    # FASE 2 completa! Iniciar FASE 3 (Steps 11-14 - Perspectivas BSC)
                    logger.info(
                        "[COLLECT] ===== INICIANDO FASE 3 - PERSPECTIVAS BSC (Steps 11-14) ====="
                    )

                    state.metadata["awaiting_confirmation"] = False
                    state.metadata["onboarding_phase"] = "bsc_kpis"
                    state.metadata["current_enrichment_step"] = 11  # Financeira

                    # Pergunta Step 11: Perspectiva Financeira
                    bsc_intro = (
                        f"Otimo! Agora vamos detalhar os **KPIs por perspectiva BSC**.\n\n"
                        f"**Step 11 - Perspectiva Financeira:**\n"
                        f"Quais **KPIs financeiros** a {partial_profile.get('company_name', 'empresa')} "
                        f"acompanha ou gostaria de acompanhar?\n"
                        f"_Exemplos: ROI, EBITDA, Margem Bruta, Margem Liquida, Faturamento, Fluxo de Caixa, etc._"
                    )

                    return {
                        "question": bsc_intro,
                        "is_complete": False,
                        "extracted_entities": extracted_entities,
                        "accumulated_profile": partial_profile,
                        "metadata": {
                            "partial_profile": partial_profile,
                            "awaiting_confirmation": False,
                            "onboarding_phase": "bsc_kpis",
                            "current_enrichment_step": 11,
                            "conversation_history": state.metadata.get("conversation_history", []),
                        },
                    }

                elif current_onboarding_phase == "bsc_kpis":
                    # FASE 3 completa! Agora sim, transicionar para DISCOVERY
                    logger.info(
                        "[COLLECT] ===== TODAS FASES COMPLETAS! Transicionando para DISCOVERY ====="
                    )

                    # Transicao para DISCOVERY
                    state.current_phase = ConsultingPhase.DISCOVERY
                    logger.info(
                        "[COLLECT] ===== STATE.CURRENT_PHASE ATUALIZADO PARA: %s =====",
                        state.current_phase,
                    )

                    # Limpar flags
                    state.metadata["awaiting_confirmation"] = False
                    state.metadata["onboarding_phase"] = "complete"

                    completion_message = (
                        f"Excelente! Onboarding completo para {partial_profile.get('company_name')}!\n\n"
                        f"Coletamos:\n"
                        f"- **FASE 1:** Informacoes basicas, desafios e objetivos\n"
                        f"- **FASE 2:** MVV, contexto competitivo, estrutura e projetos\n"
                        f"- **FASE 3:** KPIs das 4 perspectivas BSC\n\n"
                        f"Iniciando **diagnostico BSC completo**...\n"
                        f"_Isso vai levar alguns minutos enquanto analiso as 4 perspectivas._"
                    )

                    return {
                        "question": completion_message,
                        "is_complete": True,
                        "extracted_entities": extracted_entities,
                        "accumulated_profile": partial_profile,
                        "metadata": {
                            "partial_profile": partial_profile,
                            "awaiting_confirmation": False,
                            "onboarding_phase": "complete",
                        },
                    }

                else:
                    # Fallback: fase desconhecida, ir para DISCOVERY
                    logger.warning(
                        "[COLLECT] Fase de onboarding desconhecida: %s. Indo para DISCOVERY.",
                        current_onboarding_phase,
                    )
                    state.current_phase = ConsultingPhase.DISCOVERY
                    state.metadata["awaiting_confirmation"] = False

                    return {
                        "question": f"Iniciando diagnostico BSC para {partial_profile.get('company_name')}...",
                        "is_complete": True,
                        "extracted_entities": extracted_entities,
                        "accumulated_profile": partial_profile,
                        "metadata": {"partial_profile": partial_profile},
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
        # BEST PRACTICE Nov/2025: Passar partial_profile para Progressive Summarization
        # Evita "Lost in Middle" (MS/Salesforce: -39% performance em multi-turn sem isso)
        try:
            context = await self._analyze_conversation_context(
                conversation_history=conversation_history,
                extracted_entities=extraction_result,
                partial_profile=partial_profile,  # NOVO: dados acumulados para contexto efetivo
            )

            logger.info(
                "[COLLECT] Contexto analisado: scenario=%s, sentiment=%s, completeness=%.0f%%",
                context.scenario,
                context.user_sentiment,
                context.completeness,
            )

            # STEP 6.3: Gerar resposta contextual adaptativa (BLOCO 1 - ETAPA 5)
            # CRÍTICO: Passar partial_profile (acumulado) ao invés de extraction_result (só turno atual)
            # SESSAO 49: Passar profile ANTES da atualizacao para detectar repeticao corretamente
            next_question = await self._generate_contextual_response(
                context=context,
                user_message=user_message,
                extracted_entities=extraction_result,
                partial_profile=partial_profile,  # NOVO: dados acumulados
                profile_before_update=partial_profile_before_update,  # SESSAO 49: Para detectar repeticao
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
    # MÉTODOS PRIVADOS (AUXILIARES) - CONTEXT MANAGEMENT (Best Practices 2025)
    # ========================================================================

    def _get_effective_context(
        self, conversation_history: list[dict[str, str]], partial_profile: dict[str, Any] | None
    ) -> str:
        """Retorna contexto efetivo (sumarizado) para LLM - evita 'Lost in Middle'.

        Implementa Progressive Summarization pattern (Dr. Ankit Malviya, Medium Oct/2025):
        - Se poucos turnos (<=4): usa histórico completo
        - Se muitos turnos (>4): sumariza antigos + mantém últimos 2 turnos

        Resolve problema "LLMs Get Lost in Multi-Turn Conversation" (MS/Salesforce 2025):
        - 39% drop performance em multi-turn
        - Modelo ancora em suposições iniciais e resiste correções
        - Solução: contexto compacto com informações consolidadas

        Args:
            conversation_history: Lista de dicts com 'role' e 'content'
            partial_profile: Perfil acumulado (dados já extraídos)

        Returns:
            str: Contexto formatado para LLM (sumarizado se necessário)

        Example:
            >>> history = [{"role": "user", "content": "msg1"}, ...10 msgs...]
            >>> profile = {"company_name": "TechCorp", "challenges": ["alta rotatividade"]}
            >>> ctx = agent._get_effective_context(history, profile)
            >>> # Retorna: [SUMÁRIO] + últimas 4 mensagens (não todas 10)
        """
        # Se poucos turnos, usar histórico completo
        if not conversation_history or len(conversation_history) <= 4:
            return self._format_conversation_history(conversation_history or [])

        # PROGRESSIVE SUMMARIZATION: Sumarizar turnos antigos
        recent_turns = conversation_history[-4:]  # Últimos 2 pares user/assistant

        # Construir sumário estruturado dos dados ACUMULADOS (fonte de verdade)
        summary_parts = ["[CONTEXTO ACUMULADO - Informações já coletadas]"]

        if partial_profile:
            if partial_profile.get("company_name"):
                summary_parts.append(f"• Empresa: {partial_profile['company_name']}")
            if partial_profile.get("industry"):
                summary_parts.append(f"• Setor: {partial_profile['industry']}")
            if partial_profile.get("size"):
                summary_parts.append(f"• Porte: {partial_profile['size']}")
            if partial_profile.get("challenges"):
                challenges_str = ", ".join(partial_profile["challenges"][:3])
                summary_parts.append(f"• Desafios identificados: {challenges_str}")
            if partial_profile.get("goals"):
                goals_str = ", ".join(partial_profile["goals"][:3])
                summary_parts.append(f"• Objetivos mencionados: {goals_str}")

        if len(summary_parts) == 1:  # Só o título, sem dados
            summary_parts.append("• (Nenhuma informação coletada ainda)")

        summary = "\n".join(summary_parts)

        # Formatar últimas mensagens
        recent_formatted = self._format_conversation_history(recent_turns)

        return f"{summary}\n\n[ÚLTIMAS MENSAGENS]\n{recent_formatted}"

    def _detect_user_repetition(
        self, user_message: str, partial_profile: dict[str, Any] | None
    ) -> list[str]:
        """Detecta se usuário está repetindo informações já coletadas.

        Evita o antipadrão de perguntar novamente sobre dados já fornecidos.
        Baseado em paper "User Frustration Detection in TOD Systems" (Telepathy Labs 2025):
        - Repetição é sinal de frustração (+38% F1 quando detectado)
        - Deve-se reconhecer e não perguntar novamente

        Args:
            user_message: Mensagem atual do usuário
            partial_profile: Perfil acumulado com dados já coletados

        Returns:
            list[str]: Lista de campos repetidos (ex: ["company_name", "challenge: alta rotatividade"])

        Example:
            >>> profile = {"company_name": "TechCorp", "challenges": ["alta rotatividade"]}
            >>> repeated = agent._detect_user_repetition("A TechCorp tem alta rotatividade", profile)
            >>> repeated  # ["company_name", "challenge: alta rotatividade"]
        """
        if not partial_profile:
            return []

        repeated_info = []
        user_lower = user_message.lower()

        # Verificar se mencionou empresa já conhecida
        company_name = partial_profile.get("company_name")
        if company_name:
            # Verificar variações do nome
            company_variations = [
                company_name.lower(),
                company_name.lower().replace(" ", ""),
                company_name.lower().replace("-", ""),
            ]
            for variation in company_variations:
                if len(variation) >= 3 and variation in user_lower:
                    repeated_info.append("company_name")
                    break

        # SESSAO 49: Detectar respostas negativas e registrar tópico da última pergunta
        NEGATIVE_RESPONSES = [
            "nao sei",
            "nao sabemos",
            "desconheco",
            "nao tenho",
            "nao temos",
            "nao possuo",
            "nao possuimos",
            "sem essa informacao",
            "nao mensuro",
            "nao mensuramos",
            "nao acompanho",
            "nao acompanhamos",
        ]
        is_negative_response = any(neg in user_lower for neg in NEGATIVE_RESPONSES)
        if is_negative_response:
            # Registrar que o usuário não sabe - devemos avançar para outro tópico
            repeated_info.append("_negative_response_")

        # Verificar setor já mencionado
        industry = partial_profile.get("industry")
        if industry and len(industry) >= 4:
            if industry.lower() in user_lower:
                repeated_info.append("industry")

        # Verificar desafios já mencionados (match parcial - primeiras 3 palavras)
        for challenge in partial_profile.get("challenges", []):
            challenge_words = challenge.lower().split()[:3]
            if len(challenge_words) >= 2:
                # Se 2+ palavras do desafio aparecem na mensagem
                matches = sum(1 for word in challenge_words if word in user_lower and len(word) > 3)
                if matches >= 2:
                    repeated_info.append(f"challenge: {challenge[:50]}")

        # Verificar objetivos já mencionados
        for goal in partial_profile.get("goals", []):
            goal_words = goal.lower().split()[:3]
            if len(goal_words) >= 2:
                matches = sum(1 for word in goal_words if word in user_lower and len(word) > 3)
                if matches >= 2:
                    repeated_info.append(f"goal: {goal[:50]}")

        if repeated_info:
            logger.info(
                "[REPETITION_DETECT] Usuário repetiu informações: %s", ", ".join(repeated_info)
            )

        return repeated_info

    async def _generate_confirmation_clean_context(self, partial_profile: dict[str, Any]) -> str:
        """Gera mensagem de confirmação usando contexto LIMPO (Concat-and-Retry).

        Implementa "Concat-and-Retry" pattern (KeywordsAI/MS Research 2025):
        - Reúne todas informações coletadas
        - Chama LLM com prompt LIMPO (sem histórico conversacional)
        - Evita que LLM se "perca" no meio do histórico

        Impacto esperado: Restaura performance para >90% (igual single-turn)

        Args:
            partial_profile: Perfil acumulado com todos dados coletados

        Returns:
            str: Mensagem de confirmação natural e concisa

        Example:
            >>> profile = {"company_name": "TechCorp", "industry": "Tecnologia", ...}
            >>> msg = await agent._generate_confirmation_clean_context(profile)
            >>> # "Perfeito! Então temos a TechCorp, do setor de Tecnologia..."
        """
        import asyncio

        # CONCAT: Consolidar todas informações em prompt estruturado
        # SESSAO 46: Expandido para incluir TODOS os novos campos
        company_name = partial_profile.get("company_name", "sua empresa")
        industry = partial_profile.get("industry", "")
        size = partial_profile.get("size", "")
        challenges = partial_profile.get("challenges", [])
        goals = partial_profile.get("goals", [])

        # SESSAO 46: Novos campos
        key_people = partial_profile.get("key_people", [])
        employee_count = partial_profile.get("employee_count")
        business_process = partial_profile.get("business_process_description", "")
        process_bottlenecks = partial_profile.get("process_bottlenecks", [])
        production_metrics = partial_profile.get("production_metrics", {})
        investments_needed = partial_profile.get("investments_needed", [])
        pending_projects = partial_profile.get("pending_projects", [])
        pain_points = partial_profile.get("pain_points", [])
        technology_gaps = partial_profile.get("technology_gaps", [])

        # Formatar listas para o prompt
        challenges_str = ", ".join(challenges[:5]) if challenges else ""
        goals_str = ", ".join(goals[:4]) if goals else ""

        # Formatar key_people
        key_people_str = ""
        if key_people:
            people_items = [f"{p.get('name', 'N/A')} ({p.get('role', '')})" for p in key_people[:5]]
            key_people_str = ", ".join(people_items)

        # Formatar production_metrics
        metrics_str = ""
        if production_metrics:
            metrics_items = [f"{k}: {v}" for k, v in production_metrics.items()]
            metrics_str = ", ".join(metrics_items[:4])

        # Formatar investments
        investments_str = ", ".join(investments_needed[:3]) if investments_needed else ""

        # Formatar projects
        projects_str = ""
        if pending_projects:
            proj_items = [
                f"{p.get('name', 'Projeto')} ({p.get('deadline', 'N/A')})"
                for p in pending_projects[:3]
            ]
            projects_str = ", ".join(proj_items)

        # Formatar bottlenecks
        bottlenecks_str = ", ".join(process_bottlenecks[:3]) if process_bottlenecks else ""

        # Formatar pain points
        all_pains = (pain_points or []) + (technology_gaps or [])
        pains_str = ", ".join(all_pains[:4]) if all_pains else ""

        # Prompt LIMPO (sem histórico) - EXPANDIDO SESSAO 46
        consolidated_prompt = f"""Voce e um consultor BSC experiente e profissional.

TAREFA: Gerar mensagem de CONFIRMACAO estruturada das informacoes coletadas.

DADOS COLETADOS:
- Empresa: {company_name}
- Setor: {industry or 'nao informado'}
- Porte: {size or 'nao informado'}
- Funcionarios: {employee_count or 'nao informado'}
- Pessoas-chave: {key_people_str or 'nao identificadas'}
- Processo de negocio: {business_process[:100] + '...' if business_process else 'nao descrito'}
- Gargalos: {bottlenecks_str or 'nao identificados'}
- Desafios: {challenges_str or 'nao informados'}
- Objetivos: {goals_str or 'nao informados'}
- Metricas de producao: {metrics_str or 'nao informadas'}
- Investimentos necessarios: {investments_str or 'nao identificados'}
- Projetos em andamento: {projects_str or 'nenhum mencionado'}
- Dores/Gaps: {pains_str or 'nao identificados'}

REGRAS:
1. Mensagem ESTRUTURADA com secoes claras (use markdown)
2. Tom PROFISSIONAL e objetivo
3. Listar TODAS as informacoes relevantes coletadas
4. Perguntar se esta correto para prosseguir
5. NAO usar linguagem informal (evitar "legal", "beleza", "show")
6. Incluir contagens (ex: "3 desafios", "5 pessoas-chave")

Gere a mensagem de confirmacao:"""

        try:
            # RETRY: Chamar LLM com contexto limpo (sem histórico)
            # SESSAO 47: Bug fix - usar SystemMessage para consistencia e robustez cross-provider
            from langchain_core.messages import SystemMessage

            messages = [SystemMessage(content=consolidated_prompt)]
            response = await asyncio.wait_for(self.llm.ainvoke(messages), timeout=60)

            confirmation = response.content.strip()

            # Validação básica
            if not confirmation or len(confirmation) < 20:
                logger.warning("[CONFIRM_CLEAN] Resposta muito curta, usando fallback")
                return self._get_confirmation_fallback(partial_profile)

            logger.info(
                "[CONFIRM_CLEAN] Confirmação gerada com contexto limpo | len=%d", len(confirmation)
            )

            return confirmation

        except Exception as e:
            logger.error("[CONFIRM_CLEAN] Erro ao gerar confirmação: %s", e)
            return self._get_confirmation_fallback(partial_profile)

    def _get_confirmation_fallback(self, partial_profile: dict[str, Any]) -> str:
        """Fallback para confirmação quando LLM falha.

        SESSAO 46: Expandido para incluir resumo dos novos campos.
        """
        company = partial_profile.get("company_name", "sua empresa")
        industry = partial_profile.get("industry", "")
        challenges = partial_profile.get("challenges", [])
        goals = partial_profile.get("goals", [])
        key_people = partial_profile.get("key_people", [])
        employee_count = partial_profile.get("employee_count")
        investments = partial_profile.get("investments_needed", [])

        # Construir resumo compacto
        parts = [f"**{company}**"]
        if industry:
            parts.append(f"setor {industry}")
        if employee_count:
            parts.append(f"{employee_count} funcionarios")

        summary = " | ".join(parts)

        counts = []
        if challenges:
            counts.append(f"{len(challenges)} desafios")
        if goals:
            counts.append(f"{len(goals)} objetivos")
        if key_people:
            counts.append(f"{len(key_people)} pessoas-chave")
        if investments:
            counts.append(f"{len(investments)} investimentos")

        counts_str = ", ".join(counts) if counts else "informacoes basicas"

        return (
            f"Registrei as informacoes: {summary}.\n"
            f"Coletei: {counts_str}.\n\n"
            "Esta correto? Posso prosseguir para o diagnostico?"
        )

    # ========================================================================
    # MÉTODOS PRIVADOS (AUXILIARES) - PERGUNTAS E EXTRAÇÃO
    # ========================================================================

    def _generate_initial_question(self, step: int) -> str:
        """
        Gera pergunta inicial para um step específico.

        Args:
            step: OnboardingStep (1-7)

        Returns:
            str: Pergunta conversacional adequada ao step

        Steps:
            1-3: Obrigatórios (sempre pergunta)
            4-7: Opcionais (pergunta se há tempo/interesse)
        """
        # SESSAO 48: TOM PROFISSIONAL - Usar prompts de onboarding_prompts.py
        # Best Practice McKinsey: Perguntas específicas e quantificadas
        # Removido tom casual ("perrengues", "legal") - agora usa tom consultivo
        from src.prompts.onboarding_prompts import get_initial_question

        # get_initial_question retorna prompts V2 (com métricas e SMART)
        step_number = step.value if hasattr(step, "value") else step
        prompt = get_initial_question(step_number)

        # Fallback para prompts inline se modulo nao retornar nada
        # SESSAO 49: Atualizado para 14 steps (Kaplan & Norton best practices)
        if not prompt:
            questions = {
                # OBRIGATORIOS (Core do diagnostico BSC - ordem Kaplan & Norton)
                OnboardingStep.COMPANY_INFO: (
                    "Para iniciar o diagnostico BSC, preciso conhecer sua empresa. "
                    "Qual o nome da empresa, setor de atuacao e numero aproximado de colaboradores?"
                ),
                OnboardingStep.STRATEGY_VISION: (
                    "Para um diagnostico efetivo, preciso entender a estrategia. "
                    "Qual a visao de longo prazo da empresa? Por que os clientes compram de voces?"
                ),
                OnboardingStep.BUSINESS_STAGE: (
                    "A empresa esta focada em CRESCER rapidamente, MANTER lucratividade "
                    "ou MAXIMIZAR fluxo de caixa?"
                ),
                OnboardingStep.CUSTOMER_SEGMENTATION: (
                    "Quais sao os principais tipos/segmentos de clientes que voces atendem? "
                    "Qual e o mais lucrativo?"
                ),
                OnboardingStep.CHALLENGES: (
                    "Quais sao os principais desafios estrategicos que a empresa enfrenta atualmente? "
                    "Podem ser relacionados a crescimento, eficiencia operacional ou gestao de pessoas."
                ),
                OnboardingStep.OBJECTIVES: (
                    "Quais sao os objetivos estrategicos da empresa para os proximos 12 meses? "
                    "Tente incluir metricas (%, R$, unidades) e prazos."
                ),
                # OPCIONAIS (Enriquecem diagnostico - Kaplan & Norton 2004/2008)
                OnboardingStep.MVV: (
                    "Voces tem missao, visao ou valores definidos? Se sim, pode compartilhar?"
                ),
                OnboardingStep.COMPETITIVE_CONTEXT: (
                    "Quem sao seus principais concorrentes? O que diferencia voces deles?"
                ),
                OnboardingStep.ORGANIZATION_STRUCTURE: (
                    "Como a empresa esta organizada? Quantos colaboradores, departamentos, "
                    "sistemas de gestao (ERP, CRM, BI)?"
                ),
                OnboardingStep.PROJECT_CONSTRAINTS: (
                    "Qual o prazo ideal para implementar o BSC? "
                    "Quem sera o patrocinador/responsavel pelo projeto?"
                ),
                # PERSPECTIVAS BSC DETALHADAS (sob demanda)
                OnboardingStep.BSC_FINANCIAL: (
                    "Para a perspectiva Financeira: qual o faturamento atual e meta? "
                    "Qual a margem EBITDA atual e meta?"
                ),
                OnboardingStep.BSC_CUSTOMER: (
                    "Para a perspectiva Clientes: quantos clientes ativos? "
                    "Qual a taxa de retencao? Como esta a satisfacao (NPS)?"
                ),
                OnboardingStep.BSC_PROCESS: (
                    "Para a perspectiva Processos: qual o lead time atual? "
                    "Qual o principal gargalo operacional?"
                ),
                OnboardingStep.BSC_LEARNING: (
                    "Para a perspectiva Aprendizado: quantos funcionarios? "
                    "Taxa de rotatividade? Quais sistemas utilizam?"
                ),
            }
            prompt = questions.get(step, "")

        return prompt

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
        # SESSAO 45: Incluir data atual para LLM não sugerir datas passadas
        current_date, current_date_full = _get_current_date_pt_br()

        messages = [
            SystemMessage(content=EXTRACT_ALL_ENTITIES_PROMPT),
            HumanMessage(
                content=f"""DATA ATUAL: {current_date} ({current_date_full})

MENSAGEM DO USUARIO:
"{user_message}"

HISTORICO CONVERSACAO (ultimos 5 turns):
{history_text if history_text else "(inicio da conversacao)"}

Analise a mensagem e historico. Extraia TODAS entidades mencionadas (company_info, challenges, objectives).
Se o usuario mencionar prazos/timelines, considere a data atual ({current_date}) como referencia.
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
        self,
        conversation_history: list[dict[str, str]],
        extracted_entities: ExtractedEntities,
        partial_profile: dict[str, Any] | None = None,
    ) -> ConversationContext:
        """Analisa contexto conversacional completo para detectar cenarios especiais.

        Implementa Context-Aware Response Generation pattern para onboarding conversacional.
        Detecta 5 cenarios: objectives_before_challenges, frustration_detected,
        information_complete, information_repeated, standard_flow.

        ATUALIZAÇÃO Nov/2025 (Best Practices Brightdata Research):
        - Usa Progressive Summarization para evitar "Lost in Middle" (MS/Salesforce 2025)
        - Passa partial_profile para contexto efetivo (dados acumulados = fonte de verdade)
        - Reduz tokens em 60-80% comparado com histórico completo

        Baseado em:
        - Paper "LLMs Get Lost in Multi-Turn Conversation" (MS/Salesforce 2025)
          - 39% drop performance em multi-turn
          - Solução: Progressive Summarization + Concat-and-Retry
        - Paper "User Frustration Detection in TOD Systems" (Telepathy Labs 2025)
          - Full conversation context > last utterance (+38% F1: 0.86 vs 0.48)
          - ICL zero-shot com LLMs suficiente (F1 0.86-0.87)
          - Frustracao via padroes (repeticao, escalacao) nao apenas keywords
        - Tidio Chatbot Analytics 2024-2025 (completeness metric, confirmacao periodica)

        Args:
            conversation_history: Lista de dicts com 'role' e 'content'
                                  [{"role": "user", "content": "..."}, ...]
            extracted_entities: Entidades ja extraidas (para calcular completeness)
            partial_profile: Perfil acumulado para Progressive Summarization (opcional)

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
                # SESSAO 48: Usar partial_profile se disponivel (mesmo com historico vazio)
                if partial_profile:
                    _completeness = self._calculate_completeness_from_profile(partial_profile)
                    _missing = self._calculate_missing_info_from_profile(partial_profile)
                else:
                    _completeness = self._calculate_completeness(extracted_entities)
                    _missing = self._calculate_missing_info(extracted_entities)
                return ConversationContext(
                    scenario="standard_flow",
                    user_sentiment="neutral",
                    missing_info=_missing,
                    completeness=_completeness,
                    should_confirm=False,
                    context_summary="Conversa iniciando",
                )

            # STEP 1: Calcular completeness e missing_info MANUALMENTE (nao confiar apenas no LLM)
            # SESSAO 48: CORRECAO CRITICA - Usar partial_profile (acumulado) ao inves de
            # extracted_entities (turno atual) para evitar loop de perguntas repetidas.
            # Best Practice Context Engineering (LangChain Jul/2025):
            # "Use dados escritos no scratchpad/state como fonte de verdade"
            if partial_profile:
                completeness = self._calculate_completeness_from_profile(partial_profile)
                missing_info = self._calculate_missing_info_from_profile(partial_profile)
                logger.info(
                    "[ANALYZE_CONTEXT] Usando partial_profile (ACUMULADO) | "
                    "completeness=%.2f | missing=%s",
                    completeness,
                    missing_info[:3],  # Log apenas primeiros 3 para brevidade
                )
            else:
                # Fallback para extracted_entities (primeira mensagem, sem historico)
                completeness = self._calculate_completeness(extracted_entities)
                missing_info = self._calculate_missing_info(extracted_entities)
                logger.info(
                    "[ANALYZE_CONTEXT] Usando extracted_entities (TURNO ATUAL - sem partial_profile)"
                )

            # STEP 2: Determinar should_confirm
            # CRÍTICO: Só confirmar quando dados estiverem COMPLETOS (completeness >= 1.0)
            # Confirmação prematura causa loop infinito!
            should_confirm = completeness >= 1.0

            # STEP 2.5: FASE 3 - Validacoes MECE e SMART (Dez/2025)
            # Best Practice McKinsey: Garantir cobertura balanceada das 4 perspectivas BSC
            mece_validation = None
            smart_validation = None

            if partial_profile:
                # Validar cobertura MECE (perspectivas BSC)
                mece_validation = self._validate_mece_coverage(partial_profile)

                # Validar objetivos SMART
                goals = partial_profile.get("goals", [])
                if goals:
                    smart_validation = self._validate_smart_objectives(goals)

                # Se cobertura MECE desbalanceada, adicionar perspectivas faltantes ao missing_info
                if mece_validation and not mece_validation["is_balanced"]:
                    for perspective in mece_validation["missing_perspectives"]:
                        perspective_missing = f"challenges_{perspective}"
                        if perspective_missing not in missing_info and len(missing_info) < 5:
                            missing_info.append(perspective_missing)

                # Log validacoes
                logger.info(
                    f"[ANALYZE_CONTEXT] MECE: balanced={mece_validation.get('is_balanced') if mece_validation else 'N/A'} | "
                    f"SMART: score={smart_validation.get('overall_score') if smart_validation else 'N/A'}"
                )

            # STEP 3: Usar contexto EFETIVO (Progressive Summarization) - Best Practice Nov/2025
            # Evita "Lost in Middle" problem (MS/Salesforce 2025: -39% performance em multi-turn)
            # Se >4 mensagens: sumariza antigos + mantém últimos 2 pares user/assistant
            formatted_history = self._get_effective_context(conversation_history, partial_profile)

            logger.info(
                "[ANALYZE_CONTEXT] Iniciando analise | turns=%d | completeness=%.2f | should_confirm=%s | "
                "context_len=%d (effective, not full)",
                len(conversation_history) // 2,  # Aproximacao de turns
                completeness,
                should_confirm,
                len(formatted_history),
            )

            # STEP 4: Construir messages para LLM
            from src.prompts.client_profile_prompts import ANALYZE_CONVERSATION_CONTEXT_PROMPT

            # SESSAO 45: Incluir data atual para contexto temporal
            current_date, _ = _get_current_date_pt_br()

            prompt = ANALYZE_CONVERSATION_CONTEXT_PROMPT.format(
                conversation_history=formatted_history
            )

            # Adicionar data atual no início do prompt
            prompt = f"DATA ATUAL: {current_date}\n\n{prompt}"

            # SESSAO 47: Bug fix - usar SystemMessage para consistencia e robustez cross-provider
            from langchain_core.messages import SystemMessage

            messages = [SystemMessage(content=prompt)]

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
            # SESSAO 48: Usar partial_profile se disponivel (mesmo em erro)
            if partial_profile:
                _completeness = self._calculate_completeness_from_profile(partial_profile)
                _missing = self._calculate_missing_info_from_profile(partial_profile)
            else:
                _completeness = self._calculate_completeness(extracted_entities)
                _missing = self._calculate_missing_info(extracted_entities)
            return ConversationContext(
                scenario="standard_flow",
                user_sentiment="neutral",
                missing_info=_missing,
                completeness=_completeness,
                should_confirm=False,
                context_summary=f"Erro na analise: {str(e)[:50]}",
            )

    def _calculate_completeness(self, entities: ExtractedEntities) -> float:
        """Calcula porcentagem de completude do perfil (0.0 a 1.0).

        SESSAO 46: Expandido para ~15 subcategorias com granularidade fina.
        Best Practice Microsoft (Mar 2025): Incremental Extraction + Schema Enforcement

        Formula:
        - OBRIGATÓRIOS (Steps 1-3): 40% do peso total
          - Company info: 15%
          - Challenges: 15%
          - Objectives: 10%

        - ESTRUTURA ORGANIZACIONAL (CRÍTICO BSC): 30% do peso total
          - Key People: 10% (stakeholders são CRÍTICOS)
          - Team Structure: 5%
          - Business Process: 10%
          - Organization/Systems: 5%

        - MÉTRICAS E CONTEXTO: 20% do peso total
          - Production/Financial Metrics: 10%
          - Competitive Context: 5%
          - Pain Points/Technology Gaps: 5%

        - OPCIONAIS (enriquecimento): 10% do peso total
          - MVV: 5%
          - Project Constraints: 5%

        Args:
            entities: Entidades extraidas

        Returns:
            Float entre 0.0 e 1.0
        """
        completeness = 0.0

        # ====================================================================
        # OBRIGATÓRIOS (40% do peso total)
        # ====================================================================

        # Company info: 15%
        if entities.has_company_info and entities.company_info is not None:
            completeness += 0.15

        # Challenges: 15% (precisa >=2 para completude total)
        if entities.has_challenges and len(entities.challenges) >= 2:
            completeness += 0.15
        elif entities.has_challenges and len(entities.challenges) == 1:
            completeness += 0.08

        # Objectives: 10% (precisa >=3 para completude total)
        if entities.has_objectives and len(entities.objectives) >= 3:
            completeness += 0.10
        elif entities.has_objectives and len(entities.objectives) >= 1:
            completeness += 0.10 * (len(entities.objectives) / 3.0)

        # ====================================================================
        # ESTRUTURA ORGANIZACIONAL (30% - CRÍTICO PARA BSC!)
        # SESSAO 46: Novos campos de alta importância
        # ====================================================================

        # Key People: 10% (stakeholders são CRÍTICOS para BSC)
        if entities.has_key_people and entities.key_people:
            # Mais pessoas = mais completo
            people_count = len(entities.key_people)
            if people_count >= 3:
                completeness += 0.10  # 3+ pessoas-chave = completo
            elif people_count >= 1:
                completeness += 0.10 * (people_count / 3.0)

        # Team Structure: 5%
        if entities.has_team_structure:
            team_score = 0.0
            if entities.employee_count:
                team_score += 0.03
            if entities.team_distribution:
                team_score += 0.02
            completeness += min(team_score, 0.05)

        # Business Process: 10% (crítico para perspectiva Processos)
        if entities.has_business_process:
            proc_score = 0.0
            if entities.business_process_description:
                proc_score += 0.07
            if entities.process_bottlenecks:
                proc_score += 0.03
            completeness += min(proc_score, 0.10)

        # Organization/Systems: 5%
        if entities.has_organization_structure or entities.departments or entities.key_systems:
            org_score = 0.0
            if entities.departments:
                org_score += 0.02
            if entities.key_systems:
                org_score += 0.02
            if entities.current_metrics:
                org_score += 0.01
            completeness += min(org_score, 0.05)

        # ====================================================================
        # MÉTRICAS E CONTEXTO (20%)
        # ====================================================================

        # Production/Financial Metrics: 10%
        if entities.has_operational_metrics:
            metrics_score = 0.0
            if entities.production_metrics:
                metrics_score += 0.05
            if entities.financial_metrics:
                metrics_score += 0.05
            completeness += min(metrics_score, 0.10)

        # Competitive Context: 5%
        if entities.has_competitive_context or entities.competitors or entities.target_customers:
            comp_score = 0.0
            if entities.competitors:
                comp_score += 0.02
            if entities.competitive_advantages:
                comp_score += 0.02
            if entities.target_customers:
                comp_score += 0.01
            completeness += min(comp_score, 0.05)

        # Pain Points/Technology Gaps: 5%
        if entities.has_pain_points or entities.pain_points or entities.technology_gaps:
            pain_score = 0.0
            if entities.pain_points:
                pain_score += 0.03
            if entities.technology_gaps:
                pain_score += 0.02
            completeness += min(pain_score, 0.05)

        # ====================================================================
        # OPCIONAIS - ENRIQUECIMENTO (10%)
        # ====================================================================

        # MVV: 5%
        if entities.has_mvv or entities.mission or entities.vision or entities.core_values:
            mvv_score = 0.0
            if entities.mission:
                mvv_score += 0.02
            if entities.vision:
                mvv_score += 0.02
            if entities.core_values:
                mvv_score += 0.01
            completeness += min(mvv_score, 0.05)

        # Project Constraints: 5%
        if entities.has_project_constraints or entities.timeline or entities.sponsor_name:
            proj_score = 0.0
            if entities.timeline:
                proj_score += 0.02
            if entities.sponsor_name:
                proj_score += 0.02
            if entities.success_criteria:
                proj_score += 0.01
            completeness += min(proj_score, 0.05)

        # Investments/Projects: 5% (bônus extra)
        if (
            entities.has_investments_projects
            or entities.investments_needed
            or entities.pending_projects
        ):
            inv_score = 0.0
            if entities.investments_needed:
                inv_score += 0.03
            if entities.pending_projects:
                inv_score += 0.02
            completeness += min(inv_score, 0.05)

        return round(min(completeness, 1.0), 2)  # Cap at 1.0

    def _calculate_completeness_from_profile(self, partial_profile: dict[str, Any]) -> float:
        """Calcula completeness baseado em partial_profile (dados ACUMULADOS).

        SESSAO 48: Correcao bug loop de perguntas.
        Best Practice Context Engineering (LangChain Jul/2025):
        - Usar dados acumulados (scratchpad/state) como fonte de verdade
        - NAO recalcular apenas do turno atual (extracted_entities)

        Args:
            partial_profile: Dict com dados acumulados entre turnos

        Returns:
            Float entre 0.0 e 1.0

        Notes:
            Mapeamento partial_profile -> ExtractedEntities:
            - company_name, industry, size -> company_info
            - challenges -> challenges
            - goals -> objectives
        """
        completeness = 0.0

        # ====================================================================
        # OBRIGATORIOS (40% do peso total) - Simplificado para campos CORE
        # ====================================================================

        # Company info: 15%
        has_company = bool(partial_profile.get("company_name") and partial_profile.get("industry"))
        if has_company:
            completeness += 0.15

        # Challenges: 15%
        challenges = partial_profile.get("challenges", [])
        if len(challenges) >= 2:
            completeness += 0.15
        elif len(challenges) >= 1:
            completeness += 0.08

        # Objectives/Goals: 10%
        goals = partial_profile.get("goals", [])
        if len(goals) >= 3:
            completeness += 0.10
        elif len(goals) >= 1:
            completeness += 0.10 * (len(goals) / 3.0)

        # ====================================================================
        # ESTRUTURA ORGANIZACIONAL (30%)
        # ====================================================================

        # Key People: 10%
        key_people = partial_profile.get("key_people", [])
        if key_people:
            people_count = len(key_people)
            if people_count >= 3:
                completeness += 0.10
            elif people_count >= 1:
                completeness += 0.10 * (people_count / 3.0)

        # Team Structure: 5%
        if partial_profile.get("employee_count") or partial_profile.get("team_distribution"):
            team_score = 0.0
            if partial_profile.get("employee_count"):
                team_score += 0.03
            if partial_profile.get("team_distribution"):
                team_score += 0.02
            completeness += min(team_score, 0.05)

        # Business Process: 10%
        if partial_profile.get("business_process_description") or partial_profile.get(
            "process_bottlenecks"
        ):
            proc_score = 0.0
            if partial_profile.get("business_process_description"):
                proc_score += 0.07
            if partial_profile.get("process_bottlenecks"):
                proc_score += 0.03
            completeness += min(proc_score, 0.10)

        # Organization/Systems: 5%
        if partial_profile.get("departments") or partial_profile.get("key_systems"):
            org_score = 0.0
            if partial_profile.get("departments"):
                org_score += 0.02
            if partial_profile.get("key_systems"):
                org_score += 0.02
            if partial_profile.get("current_metrics"):
                org_score += 0.01
            completeness += min(org_score, 0.05)

        # ====================================================================
        # METRICAS E CONTEXTO (20%)
        # ====================================================================

        # Production/Financial Metrics: 10%
        if partial_profile.get("production_metrics") or partial_profile.get("financial_metrics"):
            metrics_score = 0.0
            if partial_profile.get("production_metrics"):
                metrics_score += 0.05
            if partial_profile.get("financial_metrics"):
                metrics_score += 0.05
            completeness += min(metrics_score, 0.10)

        # Competitive Context: 5%
        if partial_profile.get("competitors") or partial_profile.get("target_customers"):
            comp_score = 0.0
            if partial_profile.get("competitors"):
                comp_score += 0.02
            if partial_profile.get("competitive_advantages"):
                comp_score += 0.02
            if partial_profile.get("target_customers"):
                comp_score += 0.01
            completeness += min(comp_score, 0.05)

        # Pain Points/Technology Gaps: 5%
        if partial_profile.get("pain_points") or partial_profile.get("technology_gaps"):
            pain_score = 0.0
            if partial_profile.get("pain_points"):
                pain_score += 0.03
            if partial_profile.get("technology_gaps"):
                pain_score += 0.02
            completeness += min(pain_score, 0.05)

        # ====================================================================
        # OPCIONAIS (10%)
        # ====================================================================

        # MVV: 5%
        if (
            partial_profile.get("mission")
            or partial_profile.get("vision")
            or partial_profile.get("core_values")
        ):
            mvv_score = 0.0
            if partial_profile.get("mission"):
                mvv_score += 0.02
            if partial_profile.get("vision"):
                mvv_score += 0.02
            if partial_profile.get("core_values"):
                mvv_score += 0.01
            completeness += min(mvv_score, 0.05)

        # Project Constraints: 5%
        if partial_profile.get("timeline") or partial_profile.get("sponsor_name"):
            proj_score = 0.0
            if partial_profile.get("timeline"):
                proj_score += 0.02
            if partial_profile.get("sponsor_name"):
                proj_score += 0.02
            if partial_profile.get("success_criteria"):
                proj_score += 0.01
            completeness += min(proj_score, 0.05)

        return round(min(completeness, 1.0), 2)  # Cap at 1.0

    def _calculate_missing_info(self, entities: ExtractedEntities) -> list[str]:
        """Identifica categorias de informacao ainda faltantes.

        SESSAO 46: Expandido para ~15 subcategorias com priorização.
        Best Practice Microsoft (Mar 2025): Incremental Extraction

        Args:
            entities: Entidades extraidas

        Returns:
            Lista de strings ordenada por prioridade:
            - ALTA: ["company_info", "challenges", "objectives", "key_people", "business_process"]
            - MÉDIA: ["operational_metrics", "pain_points", "team_structure"]
            - BAIXA: ["mvv", "competitive_context", "project_constraints"]

        Notes:
            - Retorna apenas os campos mais importantes faltando
            - Limita a 3-5 itens para não sobrecarregar o usuário
        """
        missing_high = []  # Alta prioridade
        missing_medium = []  # Média prioridade
        missing_low = []  # Baixa prioridade

        # ====================================================================
        # ALTA PRIORIDADE (obrigatórios para diagnóstico básico)
        # ====================================================================

        if not entities.has_company_info or entities.company_info is None:
            missing_high.append("company_info")

        if not entities.has_challenges or len(entities.challenges) < 2:
            missing_high.append("challenges")

        if not entities.has_objectives or len(entities.objectives) < 3:
            missing_high.append("objectives")

        # Key People é CRÍTICO para BSC (stakeholders)
        if not entities.has_key_people or not entities.key_people:
            missing_high.append("key_people")

        # Business Process é CRÍTICO para perspectiva Processos
        if not entities.has_business_process or not entities.business_process_description:
            missing_high.append("business_process")

        # ====================================================================
        # MÉDIA PRIORIDADE (enriquece diagnóstico significativamente)
        # ====================================================================

        # Métricas operacionais (perspectiva Financeira/Processos)
        if not entities.has_operational_metrics:
            if not entities.production_metrics and not entities.financial_metrics:
                missing_medium.append("operational_metrics")

        # Pain points (detalhes importantes)
        if not entities.has_pain_points:
            if not entities.pain_points and not entities.technology_gaps:
                missing_medium.append("pain_points")

        # Team structure (perspectiva Aprendizado)
        if not entities.has_team_structure:
            if not entities.employee_count and not entities.team_distribution:
                missing_medium.append("team_structure")

        # Organization structure
        if not entities.has_organization_structure:
            if not entities.departments and not entities.key_systems:
                missing_medium.append("organization_structure")

        # ====================================================================
        # BAIXA PRIORIDADE (opcionais, enriquecimento adicional)
        # ====================================================================

        if not entities.has_mvv and not entities.mission and not entities.vision:
            missing_low.append("mvv")

        if not entities.has_competitive_context and not entities.competitors:
            missing_low.append("competitive_context")

        if not entities.has_project_constraints and not entities.timeline:
            missing_low.append("project_constraints")

        if not entities.has_investments_projects:
            if not entities.investments_needed and not entities.pending_projects:
                missing_low.append("investments_projects")

        # ====================================================================
        # Retornar priorizado (máx 5 itens para não sobrecarregar)
        # ====================================================================
        result = missing_high + missing_medium + missing_low
        return result[:5]  # Limitar a 5 itens mais importantes

    def _calculate_missing_info_from_profile(self, partial_profile: dict[str, Any]) -> list[str]:
        """Identifica informacoes faltantes baseado em partial_profile (dados ACUMULADOS).

        SESSAO 48: Correcao bug loop de perguntas.
        Best Practice ChatMetrics (Dec/2024):
        - Tracking de conversation history para evitar re-perguntas
        - Usar dados acumulados para decidir o que perguntar

        Args:
            partial_profile: Dict com dados acumulados entre turnos

        Returns:
            Lista de strings ordenada por prioridade (max 5 itens)

        Notes:
            Mapeamento partial_profile -> missing_info:
            - company_name + industry -> "company_info"
            - challenges -> "challenges"
            - goals -> "objectives"
        """
        missing_high = []  # Alta prioridade
        missing_medium = []  # Media prioridade
        missing_low = []  # Baixa prioridade

        # ====================================================================
        # ALTA PRIORIDADE (obrigatorios para diagnostico basico)
        # ====================================================================

        # Company info
        if not partial_profile.get("company_name") or not partial_profile.get("industry"):
            missing_high.append("company_info")

        # Challenges (minimo 2)
        challenges = partial_profile.get("challenges", [])
        if len(challenges) < 2:
            missing_high.append("challenges")

        # Objectives/Goals (minimo 3)
        goals = partial_profile.get("goals", [])
        if len(goals) < 3:
            missing_high.append("objectives")

        # Key People (CRITICO para BSC)
        key_people = partial_profile.get("key_people", [])
        if not key_people:
            missing_high.append("key_people")

        # Business Process (CRITICO para perspectiva Processos)
        if not partial_profile.get("business_process_description"):
            missing_high.append("business_process")

        # ====================================================================
        # MEDIA PRIORIDADE
        # ====================================================================

        # Metricas operacionais
        if not partial_profile.get("production_metrics") and not partial_profile.get(
            "financial_metrics"
        ):
            missing_medium.append("operational_metrics")

        # Pain points
        if not partial_profile.get("pain_points") and not partial_profile.get("technology_gaps"):
            missing_medium.append("pain_points")

        # Team structure
        if not partial_profile.get("employee_count") and not partial_profile.get(
            "team_distribution"
        ):
            missing_medium.append("team_structure")

        # Organization structure
        if not partial_profile.get("departments") and not partial_profile.get("key_systems"):
            missing_medium.append("organization_structure")

        # ====================================================================
        # BAIXA PRIORIDADE
        # ====================================================================

        if not partial_profile.get("mission") and not partial_profile.get("vision"):
            missing_low.append("mvv")

        if not partial_profile.get("competitors"):
            missing_low.append("competitive_context")

        if not partial_profile.get("timeline"):
            missing_low.append("project_constraints")

        if not partial_profile.get("investments_needed") and not partial_profile.get(
            "pending_projects"
        ):
            missing_low.append("investments_projects")

        # Retornar priorizado (max 5 itens)
        result = missing_high + missing_medium + missing_low
        return result[:5]

    # =========================================================================
    # FASE 3 - VALIDACAO MECE E SMART (Dez/2025)
    # Best Practice McKinsey: Issue Tree / MECE Framework
    # Best Practice BCG: Objetivos SMART
    # =========================================================================

    def _validate_mece_coverage(self, partial_profile: dict[str, Any]) -> dict[str, Any]:
        """Valida cobertura MECE dos desafios nas 4 perspectivas BSC.

        MECE = Mutuamente Exclusivo, Coletivamente Exaustivo
        Garante que desafios cobrem todas perspectivas BSC sem sobreposicao excessiva.

        Args:
            partial_profile: Dados acumulados do cliente

        Returns:
            {
                "is_balanced": bool,  # True se cobertura >= 2 perspectivas
                "missing_perspectives": list[str],  # Perspectivas sem desafios
                "dominant_perspective": str | None,  # Perspectiva com mais desafios (se desbalanceado)
                "coverage": dict[str, int],  # Contagem por perspectiva
                "recommendations": list[str]  # Sugestoes de melhoria
            }
        """
        BSC_PERSPECTIVES = ["financeira", "clientes", "processos", "aprendizado"]

        challenges = partial_profile.get("challenges", [])
        goals = partial_profile.get("goals", [])

        # Keywords por perspectiva BSC
        FINANCIAL_KEYWORDS = [
            "faturamento",
            "receita",
            "margem",
            "custo",
            "lucro",
            "ebitda",
            "roi",
            "fluxo de caixa",
            "rentabilidade",
            "capital",
            "investimento",
            "preco",
            "orcamento",
            "reducao de custos",
            "r$",
            "milhoes",
        ]
        CUSTOMER_KEYWORDS = [
            "cliente",
            "nps",
            "churn",
            "satisfacao",
            "retencao",
            "market share",
            "segmento",
            "fidelizacao",
            "reclamacao",
            "atendimento",
            "vendas",
            "prospect",
            "conversao",
            "aquisicao",
            "relacionamento",
        ]
        PROCESS_KEYWORDS = [
            "producao",
            "lead time",
            "capacidade",
            "processo",
            "gargalo",
            "eficiencia",
            "qualidade",
            "defeito",
            "produtividade",
            "estoque",
            "logistica",
            "entrega",
            "operacao",
            "setup",
            "perfiladeira",
            "maquina",
            "equipamento",
            "ton/mes",
            "toneladas",
        ]
        LEARNING_KEYWORDS = [
            "funcionario",
            "equipe",
            "treinamento",
            "rotatividade",
            "cultura",
            "competencia",
            "capacitacao",
            "engajamento",
            "lideranca",
            "rh",
            "sistema",
            "erp",
            "crm",
            "bi",
            "tecnologia",
            "inovacao",
            "desenvolvimento",
            "aprendizado",
        ]

        # Classificar desafios e objetivos por perspectiva
        perspective_coverage = dict.fromkeys(BSC_PERSPECTIVES, 0)
        all_items = challenges + goals

        for item in all_items:
            item_lower = str(item).lower()

            # Classificar (pode cair em multiplas, mas contamos a primeira match)
            if any(kw in item_lower for kw in FINANCIAL_KEYWORDS):
                perspective_coverage["financeira"] += 1
            elif any(kw in item_lower for kw in CUSTOMER_KEYWORDS):
                perspective_coverage["clientes"] += 1
            elif any(kw in item_lower for kw in PROCESS_KEYWORDS):
                perspective_coverage["processos"] += 1
            elif any(kw in item_lower for kw in LEARNING_KEYWORDS):
                perspective_coverage["aprendizado"] += 1
            # Se nao classificou, conta como "processos" (default mais comum)
            else:
                perspective_coverage["processos"] += 1

        # Analise de balanceamento
        missing = [p for p, count in perspective_coverage.items() if count == 0]
        covered = [p for p, count in perspective_coverage.items() if count > 0]
        dominant = max(perspective_coverage, key=perspective_coverage.get)
        dominant_count = perspective_coverage[dominant]

        # Balanceado se: cobertura >= 2 perspectivas E nenhuma perspectiva tem >60% dos itens
        total_items = sum(perspective_coverage.values())
        is_balanced = len(covered) >= 2 and (dominant_count / max(total_items, 1)) <= 0.6

        # Recomendacoes
        recommendations = []
        if missing:
            perspective_names = {
                "financeira": "Financeira (faturamento, margens, custos)",
                "clientes": "Clientes (NPS, churn, satisfacao)",
                "processos": "Processos (lead time, capacidade, gargalos)",
                "aprendizado": "Aprendizado (pessoas, sistemas, cultura)",
            }
            missing_names = [perspective_names.get(p, p) for p in missing]
            recommendations.append(
                f"Explorar perspectiva(s) faltante(s): {', '.join(missing_names)}"
            )

        if dominant_count > 3 and len(all_items) > 4:
            recommendations.append(
                f"Muitos itens na perspectiva '{dominant}' ({dominant_count}/{total_items}). "
                f"Diversificar para outras perspectivas."
            )

        if len(all_items) < 3:
            recommendations.append(
                "Coletar mais desafios/objetivos (minimo 3 para diagnostico BSC completo)"
            )

        logger.info(
            f"[VALIDATE_MECE] Coverage: {perspective_coverage} | "
            f"Balanced: {is_balanced} | Missing: {missing}"
        )

        return {
            "is_balanced": is_balanced,
            "missing_perspectives": missing,
            "dominant_perspective": dominant if not is_balanced and dominant_count > 2 else None,
            "coverage": perspective_coverage,
            "total_items": total_items,
            "recommendations": recommendations,
        }

    def _validate_smart_objectives(self, objectives: list[str]) -> dict[str, Any]:
        """Valida se objetivos sao SMART.

        SMART = Especifico, Mensuravel, Alcancavel, Relevante, Temporal

        Args:
            objectives: Lista de objetivos do cliente

        Returns:
            {
                "valid_count": int,  # Objetivos SMART validos
                "total_count": int,  # Total de objetivos
                "invalid_objectives": list[dict],  # Objetivos invalidos com sugestoes
                "overall_score": float  # 0.0 a 1.0
            }
        """
        if not objectives:
            return {
                "valid_count": 0,
                "total_count": 0,
                "invalid_objectives": [],
                "overall_score": 0.0,
            }

        invalid = []
        valid_count = 0

        # Keywords que indicam metrica (Mensuravel)
        METRIC_KEYWORDS = [
            "%",
            "r$",
            "milhao",
            "milhoes",
            "ton",
            "toneladas",
            "dias",
            "horas",
            "unidades",
            "pedidos",
            "clientes",
            "funcionarios",
            "colaboradores",
            "meta",
            "reducao",
            "aumento",
            "crescimento",
            "dobrar",
            "triplicar",
            "duplicar",
        ]

        # Keywords que indicam prazo (Temporal)
        TIMELINE_KEYWORDS = [
            "mes",
            "meses",
            "ano",
            "anos",
            "trimestre",
            "semestre",
            "dezembro",
            "janeiro",
            "fevereiro",
            "marco",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "2025",
            "2026",
            "2027",
            "curto prazo",
            "medio prazo",
            "longo prazo",
            "em 6",
            "em 12",
            "em 18",
            "em 24",
            "ate o final",
            "proximo ano",
        ]

        for obj in objectives:
            obj_lower = str(obj).lower()

            # Verifica se tem NUMERO (Mensuravel)
            has_number = any(char.isdigit() for char in obj)
            has_metric_keyword = any(kw in obj_lower for kw in METRIC_KEYWORDS)
            is_measurable = has_number or has_metric_keyword

            # Verifica se tem PRAZO (Temporal)
            has_timeline = any(kw in obj_lower for kw in TIMELINE_KEYWORDS)

            # Verifica se e ESPECIFICO (nao generico) - pelo menos 6 palavras
            word_count = len(obj.split())
            is_specific = word_count >= 6

            # Score do objetivo (0-1)
            score = (is_measurable + has_timeline + is_specific) / 3.0

            if score >= 0.66:  # Pelo menos 2 de 3 criterios
                valid_count += 1
            else:
                issues = []
                suggestions = []

                if not is_measurable:
                    issues.append("falta_metrica")
                    suggestions.append(
                        "adicionar numero ou % (ex: 'aumentar 30%', 'atingir R$30M')"
                    )

                if not has_timeline:
                    issues.append("falta_prazo")
                    suggestions.append("definir prazo (ex: 'em 12 meses', 'ate dezembro 2025')")

                if not is_specific:
                    issues.append("muito_generico")
                    suggestions.append("detalhar mais (ex: 'reduzir lead time de 40 para 25 dias')")

                invalid.append(
                    {
                        "objective": obj,
                        "issues": issues,
                        "suggestions": suggestions,
                        "score": round(score, 2),
                    }
                )

        overall_score = valid_count / max(len(objectives), 1)

        logger.info(
            f"[VALIDATE_SMART] Valid: {valid_count}/{len(objectives)} | "
            f"Score: {overall_score:.2f} | Invalid: {len(invalid)}"
        )

        return {
            "valid_count": valid_count,
            "total_count": len(objectives),
            "invalid_objectives": invalid,
            "overall_score": round(overall_score, 2),
        }

    def _suggest_smart_improvement(self, objective: str, issues: list[str]) -> str:
        """Gera sugestao para tornar objetivo SMART.

        Args:
            objective: Objetivo original
            issues: Lista de issues identificados

        Returns:
            Sugestao de melhoria formatada
        """
        suggestions = []

        if "falta_metrica" in issues:
            suggestions.append("adicionar metrica quantitativa (%, R$, unidades)")

        if "falta_prazo" in issues:
            suggestions.append("definir prazo (ex: 'em 12 meses', 'ate dezembro 2025')")

        if "muito_generico" in issues:
            suggestions.append("ser mais especifico sobre o que sera alcancado")

        obj_preview = objective[:40] + "..." if len(objective) > 40 else objective
        return f"Objetivo '{obj_preview}' - melhorar: {', '.join(suggestions)}"

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

    def _validate_question_not_redundant(
        self,
        proposed_response: str,
        partial_profile: dict[str, Any] | None,
    ) -> tuple[bool, str | None]:
        """Valida se resposta proposta contem pergunta redundante com dados ja coletados.

        FASE 1.2 - Implementado para resolver loop de perguntas repetidas identificado
        na conversa Engelar (Dez/2025). Problema: agente reconhecia informacao mas
        perguntava novamente ("capacidade ja consta... qual a capacidade?").

        Args:
            proposed_response: Resposta gerada pelo LLM para o usuario
            partial_profile: Dados acumulados do cliente

        Returns:
            (True, None) se resposta e valida (nao tem pergunta redundante)
            (False, suggestion) se redundante (retorna sugestao de aprofundamento)
        """
        if not partial_profile:
            return True, None

        response_lower = proposed_response.lower()

        # STEP 1: Detectar se LLM esta repetindo pergunta "equipamento, pessoas ou processo"
        # Bug identificado Dez/2025: Esta pergunta especifica causa loop infinito
        REPETITIVE_PATTERNS = [
            "equipamento, pessoas ou processo",
            "limitacao de equipamento",
            "por equipamento, pessoas",
        ]

        for pattern in REPETITIVE_PATTERNS:
            if pattern in response_lower:
                # Verificar se usuario JA respondeu (challenges contem "equipamento")
                challenges = partial_profile.get("challenges", [])
                challenges_str = " ".join(challenges).lower() if challenges else ""

                if "equipamento" in challenges_str or "perfiladeira" in challenges_str:
                    # Usuario JA respondeu! Avancar para outra perspectiva
                    logger.warning(
                        "[VALIDATE_REDUNDANT] Loop detectado! Pergunta 'equipamento/pessoas/processo' "
                        "ja respondida. Avancando para proxima perspectiva."
                    )
                    # Verificar qual perspectiva falta e sugerir
                    return False, self._get_next_perspective_question(partial_profile)

        # STEP 2: Mapeia keywords de metricas para campos do partial_profile
        METRIC_CHECKS = [
            {
                "keywords": ["capacidade", "toneladas", "ton/mes", "producao mensal"],
                "fields": ["challenges", "production_metrics"],
                "check_content": ["ton", "capacidade", "producao", "perfiladeira", "equipamento"],
                # Followup DIFERENTE - avanca para financeiro
                "followup": "Qual o investimento estimado para resolver esse gargalo de capacidade?",
            },
            {
                "keywords": ["faturamento", "receita", "revenue"],
                "fields": ["financial_metrics", "goals"],
                "check_content": ["faturamento", "receita", "milhoes", "milhao", "R$"],
                "followup": "Qual a margem EBITDA atual e a meta para 12 meses?",
            },
            # SESSAO 49: Adicionar verificacao para margem EBITDA
            {
                "keywords": ["margem", "ebitda", "lucratividade"],
                "fields": ["financial_metrics", "goals"],
                "check_content": ["ebitda", "margem", "%", "35%", "25%"],
                "followup": "Qual o fluxo de caixa operacional medio mensal nos ultimos 12 meses?",
            },
            # SESSAO 49: Adicionar verificacao para fluxo de caixa
            {
                "keywords": ["fluxo de caixa", "caixa operacional", "cash flow"],
                "fields": ["financial_metrics"],
                "check_content": ["fluxo", "caixa", "mensal"],
                "followup": "Quantos clientes ativos a empresa possui atualmente?",
            },
            {
                "keywords": ["lead time", "prazo de entrega", "tempo de entrega"],
                "fields": ["challenges", "production_metrics"],
                "check_content": ["lead time", "dias", "prazo"],
                "followup": "Qual etapa do processo mais contribui para esse lead time?",
            },
            {
                "keywords": ["funcionarios", "colaboradores", "equipe", "headcount"],
                "fields": ["employee_count", "team_info"],
                "check_content": ["funcionarios", "colaboradores", "pessoas"],
                "followup": "Qual a taxa de rotatividade anual e as competencias mais criticas?",
            },
            {
                "keywords": ["nps", "satisfacao cliente", "churn"],
                "fields": ["customer_metrics", "challenges"],
                "check_content": ["nps", "satisfacao", "churn", "cliente"],
                "followup": "Quais os principais motivos de insatisfacao dos clientes?",
            },
        ]

        # Verifica se a resposta esta perguntando algo ja coletado
        # SESSAO 49: Verificar questions_asked para evitar repetir perguntas
        # mesmo quando usuário respondeu "não sei/não sabemos"
        questions_asked = partial_profile.get("questions_asked", [])

        # SESSAO 50 (Dez/2025): Helper para converter field_value em string buscavel
        def _field_value_to_searchable_string(field_value: Any) -> str:
            """Converte valor de campo em string buscavel.

            BUGFIX Dez/2025: financial_metrics e dict com keys como 'margem_atual'
            que nao contem 'ebitda'. Precisamos verificar VALORES + KEYS do dict.
            """
            if field_value is None:
                return ""
            if isinstance(field_value, dict):
                # Extrair keys E values do dict para busca
                parts = []
                for k, v in field_value.items():
                    parts.append(str(k).lower())
                    parts.append(str(v).lower())
                return " ".join(parts)
            if isinstance(field_value, list):
                # Juntar lista em string
                return " ".join(str(item).lower() for item in field_value)
            return str(field_value).lower()

        # SESSAO 50 (Dez/2025): Helper para verificar se um followup tambem ja foi respondido
        def _is_followup_also_answered(followup: str) -> bool:
            """Verifica se a pergunta de followup tambem ja foi respondida."""
            followup_lower = followup.lower()
            for other_check in METRIC_CHECKS:
                # Verifica se o followup contem keywords de outro check
                if not any(kw in followup_lower for kw in other_check["keywords"]):
                    continue
                # Verifica se esse check ja foi respondido
                for field in other_check["fields"]:
                    field_value = partial_profile.get(field)
                    if not field_value:
                        continue
                    # BUGFIX Dez/2025: Usar helper para extrair string buscavel
                    field_str = _field_value_to_searchable_string(field_value)
                    if any(content in field_str for content in other_check["check_content"]):
                        logger.debug(
                            f"[FOLLOWUP_CHECK] Followup ja respondido! "
                            f"followup='{followup[:50]}', field={field}, "
                            f"matched_content={[c for c in other_check['check_content'] if c in field_str]}"
                        )
                        return True
            return False

        def _get_next_unanswered_followup(current_check_idx: int) -> str | None:
            """Encontra o proximo followup que ainda nao foi respondido."""
            for i in range(current_check_idx + 1, len(METRIC_CHECKS)):
                candidate = METRIC_CHECKS[i]["followup"]
                if not _is_followup_also_answered(candidate):
                    return candidate
            # Se todos os followups foram respondidos, usar perspectiva diferente
            return self._get_next_perspective_question(partial_profile)

        for check_idx, check in enumerate(METRIC_CHECKS):
            # Verifica se a resposta contem keyword de pergunta
            question_keywords_in_response = any(kw in response_lower for kw in check["keywords"])
            if not question_keywords_in_response:
                continue

            # SESSAO 49: Verificar se esse tópico já foi perguntado
            topic_id = "_".join(check["keywords"][:2])  # ID único do tópico
            if topic_id in questions_asked:
                logger.warning(
                    f"[VALIDATE_REDUNDANT] Tópico já perguntado! "
                    f"topic_id: {topic_id}, questions_asked: {questions_asked}"
                )
                # SESSAO 50: Verificar se followup tambem ja foi respondido
                followup = check["followup"]
                if _is_followup_also_answered(followup):
                    followup = _get_next_unanswered_followup(check_idx)
                    # BUGFIX Dez/2025: Null check antes de substring (followup pode ser None)
                    followup_preview = followup[:50] if followup else "[nenhum disponivel]"
                    logger.warning(
                        f"[VALIDATE_REDUNDANT] Followup original ja respondido! Usando: {followup_preview}..."
                    )
                return False, followup

            # Verifica se ja temos esse dado no partial_profile
            for field in check["fields"]:
                field_value = partial_profile.get(field)
                if not field_value:
                    continue

                # Se o campo tem valor, verifica se contem a metrica
                # BUGFIX Dez/2025: Usar helper para extrair string buscavel (evita falsos negativos em dicts)
                field_str = _field_value_to_searchable_string(field_value)
                has_metric = any(content in field_str for content in check["check_content"])

                if has_metric:
                    # Pergunta e redundante! Ja temos essa informacao
                    logger.warning(
                        f"[VALIDATE_REDUNDANT] Pergunta redundante detectada! "
                        f"Keywords: {check['keywords']}, Campo: {field}, Valor: {field_value[:100] if isinstance(field_value, str) else field_value}"
                    )
                    # SESSAO 50: Verificar se followup tambem ja foi respondido
                    followup = check["followup"]
                    if _is_followup_also_answered(followup):
                        followup = _get_next_unanswered_followup(check_idx)
                        # BUGFIX Dez/2025: Null check antes de substring (followup pode ser None)
                        followup_preview = followup[:50] if followup else "[nenhum disponivel]"
                        logger.warning(
                            f"[VALIDATE_REDUNDANT] Followup original ja respondido! Usando: {followup_preview}..."
                        )
                    return False, followup

        return True, None

    def _extract_question_topic(self, question: str) -> str | None:
        """Extrai o topico BSC de uma pergunta para rastreamento.

        SESSAO 49: Best Practice Crisp.chat (Nov 2025) - Track Topics Asked
        Usado para evitar loops mesmo quando usuario responde negativamente.

        Args:
            question: Pergunta a analisar

        Returns:
            str: Topico identificado (financeira, clientes, processos, aprendizado) ou None
        """
        question_lower = question.lower()

        TOPIC_KEYWORDS = {
            "financeira_faturamento": ["faturamento", "receita", "revenue"],
            "financeira_ebitda": ["ebitda", "margem", "lucratividade"],
            "financeira_fluxo_caixa": ["fluxo de caixa", "caixa operacional", "cash flow"],
            "clientes_quantidade": ["clientes ativos", "quantos clientes", "numero de clientes"],
            "clientes_nps": ["nps", "satisfacao", "churn", "retencao"],
            "clientes_motivos": ["motivos de insatisfacao", "principais motivos"],
            "processos_capacidade": ["capacidade", "toneladas", "producao"],
            "processos_lead_time": ["lead time", "prazo de entrega", "tempo de entrega"],
            "aprendizado_sistemas": ["sistema", "erp", "crm", "bi"],
            "aprendizado_equipe": ["funcionario", "equipe", "rotatividade", "treinamento"],
        }

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in question_lower for kw in keywords):
                return topic

        return None

    def _register_question_asked(self, partial_profile: dict[str, Any], question: str) -> None:
        """Registra topico da pergunta feita para evitar repeticao.

        SESSAO 49: Best Practice Tencent Cloud (Sep 2025) - Context Awareness
        Mantém memória de curto prazo do que já foi perguntado.

        Args:
            partial_profile: Perfil acumulado
            question: Pergunta feita
        """
        topic = self._extract_question_topic(question)
        if topic:
            questions_asked = partial_profile.get("questions_asked", [])
            if topic not in questions_asked:
                questions_asked.append(topic)
                partial_profile["questions_asked"] = questions_asked
                logger.info(
                    f"[QUESTIONS_ASKED] Registrado topico: {topic} | Total: {len(questions_asked)}"
                )

    def _get_next_perspective_question(self, partial_profile: dict[str, Any]) -> str:
        """Retorna pergunta da proxima perspectiva BSC nao coberta.

        Usado para quebrar loops de perguntas repetidas, avancando
        para uma perspectiva diferente.

        SESSAO 49: Best Practice Medium/Faruk Alpay (Aug 2025) - Escape Saddle Points
        Quando detecta estagnacao, muda de abordagem radicalmente.
        """
        challenges = partial_profile.get("challenges", [])
        goals = partial_profile.get("goals", [])
        challenges_str = " ".join(challenges).lower() if challenges else ""
        goals_str = " ".join(goals).lower() if goals else ""
        questions_asked = partial_profile.get("questions_asked", [])

        # Verificar cobertura MECE das 4 perspectivas
        # SESSAO 49: Adicionar topics para verificar se ja foi perguntado
        PERSPECTIVES = {
            "financeira": {
                "keywords": [
                    "faturamento",
                    "receita",
                    "margem",
                    "custo",
                    "lucro",
                    "ebitda",
                    "investimento",
                ],
                "topics": ["financeira_faturamento", "financeira_ebitda", "financeira_fluxo_caixa"],
                "question": "Qual o faturamento anual atual e qual a meta para os proximos 12 meses?",
            },
            "clientes": {
                "keywords": ["cliente", "nps", "satisfacao", "churn", "contrato"],
                "topics": ["clientes_quantidade", "clientes_nps", "clientes_motivos"],
                "question": "Quantos clientes ativos a empresa possui e qual a taxa de conversao de orcamentos em contratos?",
            },
            "processos": {
                "keywords": [
                    "lead time",
                    "prazo",
                    "producao",
                    "capacidade",
                    "eficiencia",
                    "gargalo",
                ],
                "topics": ["processos_capacidade", "processos_lead_time"],
                "question": "Qual o tempo medio entre o pedido do cliente e a entrega final (lead time)?",
            },
            "aprendizado": {
                "keywords": [
                    "funcionario",
                    "equipe",
                    "rotatividade",
                    "treinamento",
                    "cultura",
                    "sistema",
                ],
                "topics": ["aprendizado_sistemas", "aprendizado_equipe"],
                "question": "Quais sistemas de gestao a empresa utiliza atualmente (ERP, CRM, BI)?",
            },
        }

        all_text = f"{challenges_str} {goals_str}"

        # SESSAO 49: Encontrar perspectiva menos coberta E nao perguntada
        for perspective, config in PERSPECTIVES.items():
            has_coverage = any(kw in all_text for kw in config["keywords"])
            already_asked = any(topic in questions_asked for topic in config["topics"])

            if not has_coverage and not already_asked:
                logger.info(
                    f"[NEXT_PERSPECTIVE] Avancando para perspectiva: {perspective} "
                    f"(coverage={has_coverage}, asked={already_asked})"
                )
                # Registrar que vamos perguntar sobre esta perspectiva
                self._register_question_asked(partial_profile, config["question"])
                return config["question"]

        # SESSAO 49: Se todas perspectivas ja foram perguntadas, avançar para objetivos
        if len(goals) < 3:
            return "Quais sao os 3 principais objetivos estrategicos para os proximos 12 meses, com metas especificas?"

        # Fallback: perguntar sobre indicadores
        return "Quais indicadores (KPIs) a empresa acompanha atualmente para medir desempenho?"

    def _replace_redundant_question(
        self,
        original_response: str,
        followup_suggestion: str,
    ) -> str:
        """Substitui pergunta redundante por aprofundamento de causa-raiz.

        Args:
            original_response: Resposta original com pergunta redundante
            followup_suggestion: Sugestao de pergunta de aprofundamento

        Returns:
            Resposta corrigida com pergunta de aprofundamento
        """
        # Encontra a ultima sentenca (provavelmente a pergunta)
        sentences = original_response.replace("?", "?.").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            # Resposta muito curta, retorna sugestao diretamente
            return followup_suggestion

        # Mantem as sentencas de contexto, substitui a pergunta
        context_sentences = sentences[:-1]  # Todas menos a ultima (pergunta)
        new_response = ". ".join(context_sentences) + ". " + followup_suggestion

        return new_response

    def _validate_premature_confirmation(
        self,
        generated_text: str,
        context: ConversationContext,
    ) -> tuple[bool, str | None]:
        """OUTPUT GUARDRAIL: Detecta confirmacao prematura na resposta.

        Best Practice 2025 (Leanware, Orq.ai): Output validation pos-LLM
        para garantir que respostas sigam regras de negocio mesmo quando
        LLM ignora instrucoes do prompt.

        Problema resolvido (Dez/2025 - Conversa Engelar):
        LLM gerou "Confirmacao das Informacoes Coletadas" apos apenas 3 turnos,
        com completeness ~40% e should_confirm=False. Isso causa:
        - Experiencia ruim (usuario confirma dados incompletos)
        - Perda de metricas importantes (MECE nao atingido)
        - Diagnostico BSC superficial

        Args:
            generated_text: Resposta gerada pelo LLM
            context: ConversationContext com should_confirm e completeness

        Returns:
            (True, None) se resposta e valida
            (False, "premature_confirmation") se confirmacao prematura detectada
        """
        import re

        # Se should_confirm=True E completeness >= 1.0, confirmacao e permitida
        if context.should_confirm and context.completeness >= 1.0:
            return True, None

        response_lower = generated_text.lower()

        # Padroes que indicam confirmacao estruturada (extraidos da conversa real Engelar)
        CONFIRMATION_PATTERNS = [
            r"confirm[aç]",  # confirmar, confirmacao
            r"informac[oõ]es?\s+coletadas?",
            r"responda.*sim.*continuar",
            r"resumo\s*:",
            r"\d+\.\s*(dados|empresa|processos|desafios|objetivos|metricas)",  # Lista numerada
            r"posso\s+(confirmar|prosseguir)",
            r"estas?\s+corretas?",
            r"sim.*para\s+continuar",
            r"nao.*corrigir",
            r"consolidac[aã]o\s+estruturada",
        ]

        for pattern in CONFIRMATION_PATTERNS:
            if re.search(pattern, response_lower):
                logger.warning(
                    f"[OUTPUT_GUARDRAIL] Confirmacao prematura detectada! "
                    f"Pattern: '{pattern}' | should_confirm={context.should_confirm} | "
                    f"completeness={context.completeness}"
                )
                return False, "premature_confirmation"

        return True, None

    async def _generate_contextual_response(
        self,
        context: ConversationContext,
        user_message: str,
        extracted_entities: ExtractedEntities,
        partial_profile: dict[str, Any] | None = None,
        profile_before_update: (
            dict[str, Any] | None
        ) = None,  # SESSAO 49: Profile ANTES da atualizacao
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

            # STEP 0: Detectar se usuário está REPETINDO informações já coletadas
            # Best Practice Nov/2025 (Telepathy Labs): Repetição indica frustração
            # SESSAO 49: Usar profile ANTES da atualizacao para evitar falso positivo
            # Bug fix: Antes comparava mensagem com dados recem-extraidos dela mesma
            profile_for_repetition = profile_before_update or partial_profile
            repeated_info = self._detect_user_repetition(user_message, profile_for_repetition)

            # SESSAO 49: Tratamento especial para respostas negativas ("não sei/não sabemos")
            # Quando usuário responde negativamente, devemos avançar para outra perspectiva
            is_negative_response = "_negative_response_" in repeated_info
            if is_negative_response:
                logger.info(
                    "[GENERATE_RESPONSE] Resposta negativa detectada ('não sei/não sabemos'). "
                    "Avançando para próxima perspectiva."
                )
                # Registrar última pergunta como "já feita" para evitar repetição
                # (será tratado na validação da resposta)
                context.scenario = "negative_response"
                context.user_sentiment = "cooperative"
            elif repeated_info:
                logger.warning(
                    "[GENERATE_RESPONSE] REPETIÇÃO DETECTADA: %s | "
                    "Usuário pode estar frustrado - adaptar resposta",
                    repeated_info,
                )
                # Forçar cenário de repetição detectada
                context.scenario = "information_repeated"
                context.user_sentiment = "possibly_frustrated"

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

            # SESSAO 45: Incluir data atual para LLM não sugerir datas passadas
            current_date, _ = _get_current_date_pt_br()

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

            # Adicionar data atual no início do prompt
            prompt = f"DATA ATUAL: {current_date}\n\n{prompt}"

            # STEP 3: Chamar LLM (free-form text, NAO structured output)
            # Usar temperatura 0.8 para respostas mais naturais/variadas (vs 1.0 padrao GPT-5)
            llm = self.llm  # GPT-5 mini configurado no construtor

            # SESSAO 47: Bug fix - usar SystemMessage para consistencia e robustez cross-provider
            from langchain_core.messages import SystemMessage

            # Chamar LLM com timeout 120s
            messages = [SystemMessage(content=prompt)]

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

            # STEP 6: FASE 1.2 - Validar se resposta contem pergunta redundante
            # Resolve loop de perguntas identificado na conversa Engelar (Dez/2025)
            is_valid, followup_suggestion = self._validate_question_not_redundant(
                generated_text, partial_profile
            )

            if not is_valid and followup_suggestion:
                logger.warning(
                    f"[GENERATE_RESPONSE] Pergunta redundante detectada! "
                    f"Substituindo por aprofundamento: {followup_suggestion[:50]}..."
                )
                generated_text = self._replace_redundant_question(
                    generated_text, followup_suggestion
                )

            # STEP 7: OUTPUT GUARDRAIL - Detectar confirmacao prematura (Best Practice 2025)
            # Leanware/Orq.ai: Validacao pos-LLM para garantir regras de negocio
            # Problema: LLM pode ignorar should_confirm=False e gerar confirmacao estruturada
            is_valid_confirm, confirm_reason = self._validate_premature_confirmation(
                generated_text, context
            )

            if not is_valid_confirm:
                logger.warning(
                    f"[GENERATE_RESPONSE] Confirmacao prematura bloqueada! "
                    f"Reason: {confirm_reason} | completeness={context.completeness} | "
                    f"should_confirm={context.should_confirm} | Usando fallback..."
                )
                return self._get_fallback_response(context, extracted_entities, partial_profile)

            logger.info(
                f"[GENERATE_RESPONSE] Resposta gerada com sucesso | "
                f"Length: {len(generated_text)} chars | Redundancy_fixed: {not is_valid} | "
                f"Confirmation_blocked: {not is_valid_confirm}"
            )

            return generated_text

        except asyncio.TimeoutError:
            logger.error("[GENERATE_RESPONSE] Timeout ao gerar resposta (>120s)")
            return self._get_fallback_response(context, extracted_entities, partial_profile)

        except Exception as e:
            logger.error(f"[GENERATE_RESPONSE] Erro ao gerar resposta: {e}", exc_info=True)
            return self._get_fallback_response(context, extracted_entities, partial_profile)

    # ========================================================================
    # SESSAO DEZ/2025: PROCESSAMENTO STEPS 7-14 (FASES 2 E 3)
    # Kaplan & Norton - Execution Premium (2008): Fluxo completo de 14 steps
    # ========================================================================

    async def _process_enrichment_step(
        self,
        user_message: str,
        state: BSCState,
        partial_profile: dict[str, Any],
        extracted_entities: dict[str, Any],
        extraction_result: ExtractedEntities,
    ) -> dict[str, Any] | None:
        """Processa respostas do usuario para Steps 7-14 (FASES 2 e 3).

        FASE 2 - ENRIQUECIMENTO (Steps 7-10):
        - Step 7: MVV (Missao, Visao, Valores)
        - Step 8: COMPETITIVE_CONTEXT (Concorrentes, Market Share)
        - Step 9: ORGANIZATION_STRUCTURE (Pessoas-chave, Organograma)
        - Step 10: PROJECT_CONSTRAINTS (Timeline, Sponsor, Criterios)

        FASE 3 - PERSPECTIVAS BSC (Steps 11-14):
        - Step 11: BSC_FINANCIAL (ROI, EBITDA, Margem)
        - Step 12: BSC_CUSTOMER (NPS, Churn, LTV)
        - Step 13: BSC_PROCESS (Lead Time, Produtividade)
        - Step 14: BSC_LEARNING (Retencao, Treinamento)

        Regra "Nao Sei": Aceitar sem julgamento e avancar imediatamente.

        Args:
            user_message: Mensagem do usuario
            state: BSCState atual
            partial_profile: Perfil acumulado
            extracted_entities: Entidades extraidas neste turno
            extraction_result: ExtractedEntities (objeto Pydantic)

        Returns:
            Dict com proxima pergunta ou None se nao estiver em fase de enriquecimento
        """
        current_phase = state.metadata.get("onboarding_phase", "identification")
        current_step = state.metadata.get("current_enrichment_step")

        if current_phase not in ["enrichment", "bsc_kpis"] or current_step is None:
            return None

        logger.info(
            "[ENRICHMENT] Processando Step %d (Fase: %s) | Mensagem: %s",
            current_step,
            current_phase,
            user_message[:100],
        )

        # Detectar resposta "nao sei" / "pular"
        user_lower = user_message.lower().strip()
        skip_keywords = [
            "nao sei",
            "não sei",
            "desconheco",
            "desconheço",
            "pular",
            "skip",
            "proximo",
            "próximo",
            "nao temos",
            "não temos",
            "nao sabemos",
            "não sabemos",
            "ainda nao",
            "ainda não",
        ]
        is_skip = any(kw in user_lower for kw in skip_keywords)

        company_name = partial_profile.get("company_name", "sua empresa")

        # ========================================================================
        # SESSAO 50 (Dez/2025): DETECTAR CONFIRMACAO PARA TRANSICAO DE FASE
        # Quando awaiting_confirmation=True e usuario responde "sim", avançar para proxima fase
        # ========================================================================
        awaiting_confirmation = state.metadata.get("awaiting_confirmation", False)
        confirmation_keywords = ["sim", "confirmo", "ok", "pode continuar", "vamos", "confirma"]
        is_confirmation = any(kw in user_lower for kw in confirmation_keywords) and len(user_lower) < 50

        if awaiting_confirmation and is_confirmation:
            logger.info(
                "[ENRICHMENT] ===== CONFIRMACAO DETECTADA! Transicionando de %s Step %d =====",
                current_phase,
                current_step,
            )

            if current_phase == "enrichment" and current_step == 10:
                # Transicionar para FASE 3 (bsc_kpis)
                logger.info("[ENRICHMENT] ===== INICIANDO FASE 3 - PERSPECTIVAS BSC =====")

                state.metadata["onboarding_phase"] = "bsc_kpis"
                state.metadata["current_enrichment_step"] = 11
                state.metadata["awaiting_confirmation"] = False

                bsc_intro = (
                    f"Otimo! Agora vamos detalhar os **KPIs por perspectiva BSC**.\n\n"
                    f"**Step 11 - Perspectiva Financeira:**\n"
                    f"Quais **KPIs financeiros** a {company_name} acompanha ou gostaria de acompanhar?\n"
                    f"_Exemplos: ROI, EBITDA, Margem Bruta, Margem Liquida, Faturamento, Fluxo de Caixa, etc._"
                )

                return {
                    "question": bsc_intro,
                    "is_complete": False,
                    "extracted_entities": extracted_entities,
                    "accumulated_profile": partial_profile,
                    "metadata": {
                        "partial_profile": partial_profile,
                        "onboarding_phase": "bsc_kpis",
                        "current_enrichment_step": 11,
                        "awaiting_confirmation": False,
                        "conversation_history": state.metadata.get("conversation_history", []),
                    },
                }

            elif current_phase == "bsc_kpis" and current_step == 14:
                # Transicionar para DISCOVERY (onboarding completo!)
                logger.info("[ENRICHMENT] ===== ONBOARDING COMPLETO! Iniciando DISCOVERY =====")

                # Retornar None para deixar o fluxo principal lidar com a transição
                state.metadata["awaiting_confirmation"] = False
                state.metadata["onboarding_complete"] = True
                return None

        # Se awaiting_confirmation mas usuario pulou (nao confirmou)
        if awaiting_confirmation and is_skip:
            logger.info("[ENRICHMENT] Usuario escolheu PULAR a fase de confirmacao")

            if current_phase == "enrichment" and current_step == 10:
                # Pular FASE 3, ir direto para completion
                logger.info("[ENRICHMENT] Pulando FASE 3 (KPIs BSC) - Indo para DISCOVERY")

                state.metadata["awaiting_confirmation"] = False
                state.metadata["onboarding_complete"] = True
                return None

        # ========================================================================
        # DEFINICAO DAS PERGUNTAS POR STEP
        # ========================================================================
        step_questions = {
            # FASE 2 - ENRIQUECIMENTO
            7: {
                "name": "MVV - Missao, Visao, Valores",
                "question": (
                    f"**Step 7 - Missao, Visao e Valores:**\n"
                    f"Qual a **missao** (razao de existir), **visao** (onde querem chegar em 5-10 anos) "
                    f"e **valores** (principios que guiam a empresa) da {company_name}?"
                ),
                "fields": ["mission", "vision", "core_values"],
            },
            8: {
                "name": "Contexto Competitivo",
                "question": (
                    f"**Step 8 - Contexto Competitivo:**\n"
                    f"Quem sao os **principais concorrentes** da {company_name}? "
                    f"Qual o **market share** estimado? "
                    f"Quais os **diferenciais competitivos**?"
                ),
                "fields": ["competitors", "competitive_advantages"],
            },
            9: {
                "name": "Estrutura Organizacional",
                "question": (
                    f"**Step 9 - Estrutura Organizacional:**\n"
                    f"Quem sao as **pessoas-chave** (lideres, gestores) da {company_name}? "
                    f"Como e o **organograma** simplificado? "
                    f"Quantos colaboradores em cada area principal?"
                ),
                "fields": ["key_people", "departments", "employee_count", "team_distribution"],
            },
            10: {
                "name": "Restricoes do Projeto",
                "question": (
                    "**Step 10 - Restricoes do Projeto BSC:**\n"
                    "Qual o **timeline** desejado para implementacao do BSC? "
                    "Quem e o **sponsor** (patrocinador executivo)? "
                    "Quais os **criterios de sucesso** do projeto?"
                ),
                "fields": ["timeline", "sponsor_name", "success_criteria"],
            },
            # FASE 3 - PERSPECTIVAS BSC
            11: {
                "name": "Perspectiva Financeira",
                "question": (
                    f"**Step 11 - Perspectiva Financeira:**\n"
                    f"Quais **KPIs financeiros** a {company_name} acompanha ou gostaria de acompanhar?\n"
                    f"_Exemplos: ROI, EBITDA, Margem Bruta, Margem Liquida, Faturamento, Fluxo de Caixa, etc._"
                ),
                "fields": ["financial_metrics"],
            },
            12: {
                "name": "Perspectiva Clientes",
                "question": (
                    f"**Step 12 - Perspectiva Clientes:**\n"
                    f"Quais **KPIs de clientes** a {company_name} acompanha ou gostaria de acompanhar?\n"
                    f"_Exemplos: NPS, Taxa de Churn, LTV, CAC, Satisfacao, Retencao, etc._"
                ),
                "fields": ["current_metrics"],
            },
            13: {
                "name": "Perspectiva Processos Internos",
                "question": (
                    f"**Step 13 - Perspectiva Processos Internos:**\n"
                    f"Quais **KPIs de processos** a {company_name} acompanha ou gostaria de acompanhar?\n"
                    f"_Exemplos: Lead Time, Produtividade, Taxa de Defeitos, Eficiencia, Cycle Time, etc._"
                ),
                "fields": ["production_metrics", "process_bottlenecks"],
            },
            14: {
                "name": "Perspectiva Aprendizado e Crescimento",
                "question": (
                    f"**Step 14 - Perspectiva Aprendizado e Crescimento:**\n"
                    f"Quais **KPIs de pessoas/aprendizado** a {company_name} acompanha ou gostaria?\n"
                    f"_Exemplos: Retencao Talentos, Horas Treinamento, Engajamento, eNPS, Turnover, etc._"
                ),
                "fields": ["technology_gaps", "key_systems"],
            },
        }

        # ========================================================================
        # LOGICA DE AVANCO DE STEPS
        # ========================================================================

        # Registrar resposta do step atual (a menos que seja skip)
        if not is_skip:
            logger.info("[ENRICHMENT] Registrando resposta do Step %d", current_step)
            # A extracao ja foi feita acima (extracted_entities), apenas logar
            step_info = step_questions.get(current_step, {})
            logger.info(
                "[ENRICHMENT] Step %d (%s) - Campos extraidos: %s",
                current_step,
                step_info.get("name", "Unknown"),
                {f: extracted_entities.get(f) for f in step_info.get("fields", [])},
            )
        else:
            logger.info(
                "[ENRICHMENT] Step %d PULADO (usuario disse 'nao sei' / 'pular')", current_step
            )
            # Registrar como GAP no metadata
            gaps = state.metadata.get("onboarding_gaps", [])
            step_info = step_questions.get(current_step, {})
            gaps.append(
                {
                    "step": current_step,
                    "name": step_info.get("name", f"Step {current_step}"),
                    "reason": "Usuario nao possui informacao",
                }
            )
            state.metadata["onboarding_gaps"] = gaps

        # Determinar proximo step
        next_step = current_step + 1

        # Verificar transicoes de fase
        if current_phase == "enrichment" and current_step == 10:
            # Fim da FASE 2, pedir confirmacao para FASE 3
            logger.info("[ENRICHMENT] ===== FIM DA FASE 2 - Pedindo confirmacao para FASE 3 =====")

            state.metadata["current_enrichment_step"] = 10
            state.metadata["awaiting_confirmation"] = True

            confirmation_msg = (
                f"Perfeito! **FASE 2 (Enriquecimento) concluida** para {company_name}.\n\n"
                f"Agora vou coletar informacoes sobre **KPIs das 4 perspectivas BSC** (Steps 11-14).\n\n"
                f"_(Responda 'sim' para continuar ou 'pular' para ir direto ao diagnostico)_"
            )

            return {
                "question": confirmation_msg,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
                "metadata": {
                    "partial_profile": partial_profile,
                    "onboarding_phase": "enrichment",
                    "current_enrichment_step": 10,
                    "awaiting_confirmation": True,
                    "conversation_history": state.metadata.get("conversation_history", []),
                },
            }

        elif current_phase == "bsc_kpis" and current_step == 14:
            # Fim da FASE 3, pedir confirmacao final
            logger.info("[ENRICHMENT] ===== FIM DA FASE 3 - Pedindo confirmacao final =====")

            state.metadata["current_enrichment_step"] = 14
            state.metadata["awaiting_confirmation"] = True

            # Contar gaps
            gaps = state.metadata.get("onboarding_gaps", [])
            gaps_text = ""
            if gaps:
                gaps_text = f"\n\n_Obs: {len(gaps)} informacoes foram marcadas como 'nao disponivel' (gaps)._"

            confirmation_msg = (
                f"Excelente! **FASE 3 (KPIs BSC) concluida** para {company_name}.\n\n"
                f"Todas as 14 etapas do onboarding foram coletadas!{gaps_text}\n\n"
                f"_(Responda 'sim' para iniciar o diagnostico BSC completo)_"
            )

            return {
                "question": confirmation_msg,
                "is_complete": False,
                "extracted_entities": extracted_entities,
                "accumulated_profile": partial_profile,
                "metadata": {
                    "partial_profile": partial_profile,
                    "onboarding_phase": "bsc_kpis",
                    "current_enrichment_step": 14,
                    "awaiting_confirmation": True,
                    "conversation_history": state.metadata.get("conversation_history", []),
                },
            }

        # Avancar para proximo step
        logger.info("[ENRICHMENT] Avancando para Step %d", next_step)

        state.metadata["current_enrichment_step"] = next_step
        state.metadata["awaiting_confirmation"] = False

        # Obter pergunta do proximo step
        next_step_info = step_questions.get(next_step, {})
        next_question = next_step_info.get(
            "question", f"Step {next_step}: Por favor, forneca mais informacoes."
        )

        # Adicionar instrucao de skip
        next_question += "\n\n_(Se nao souber, responda 'nao sei' ou 'pular')_"

        return {
            "question": next_question,
            "is_complete": False,
            "extracted_entities": extracted_entities,
            "accumulated_profile": partial_profile,
            "metadata": {
                "partial_profile": partial_profile,
                "onboarding_phase": current_phase,
                "current_enrichment_step": next_step,
                "awaiting_confirmation": False,
                "conversation_history": state.metadata.get("conversation_history", []),
            },
        }

    def _get_fallback_response(
        self,
        context: ConversationContext,
        entities: ExtractedEntities,
        partial_profile: dict[str, Any] | None = None,
    ) -> str:
        """Gera resposta fallback generica quando LLM falha.

        Resposta segura baseada em missing_info (proxima informacao faltante).
        Usa partial_profile quando disponível para personalizar perguntas.

        SESSAO 49: Best Practice Tencent Cloud (Sep 2025) - Fallback Detection
        Quando detecta loop, triggar: "Vamos para outra perspectiva."

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

        # SESSAO 49: Tratamento especial para respostas negativas ("nao sei/nao sabemos")
        # Best Practice Crisp.chat (Nov 2025): Aceitar e avancar para outra perspectiva
        if context.scenario == "negative_response" and partial_profile:
            logger.info(
                "[FALLBACK] Resposta negativa detectada. Avancando para proxima perspectiva."
            )
            next_question = self._get_next_perspective_question(partial_profile)
            return f"Entendido. Para avancar no diagnostico, {next_question.lower()}"

        # Se frustration detectada, oferecer ajuda
        if context.scenario == "frustration_detected":
            return (
                "Entendo sua frustracao. Vou garantir que suas informacoes sejam "
                "registradas corretamente. Pode me contar o que falta?"
            )

        # SESSAO 50 (Dez/2025): Fluxo estruturado de 14 steps (Kaplan & Norton)
        # Ordem: COMPANY_INFO -> STRATEGY_VISION -> BUSINESS_STAGE -> CUSTOMER_SEGMENTATION -> CHALLENGES -> OBJECTIVES
        # Depois: MVV, COMPETITIVE_CONTEXT, OPERATIONAL_METRICS, INVESTMENTS_PROJECTS (opcionais)

        # Verificar partial_profile para determinar proximo step
        # SESSAO DEZ/2025: Corrigido para verificar listas com len() e strings com != ""
        has_company = bool(partial_profile and partial_profile.get("company_name"))
        has_strategy = bool(
            partial_profile
            and (
                (partial_profile.get("vision") and partial_profile.get("vision") != "")
                or len(partial_profile.get("competitive_advantages", [])) > 0
                or (partial_profile.get("mission") and partial_profile.get("mission") != "")
            )
        )
        has_business_stage = bool(partial_profile and partial_profile.get("business_stage"))
        has_customer_seg = bool(
            partial_profile and len(partial_profile.get("target_customers", [])) > 0
        )
        has_challenges = bool(partial_profile and len(partial_profile.get("challenges", [])) >= 2)
        has_objectives = bool(partial_profile and len(partial_profile.get("goals", [])) >= 2)

        # STEP 1: COMPANY_INFO (obrigatorio)
        if not has_company or "company_info" in context.missing_info:
            return "Para comecar, pode me contar o nome da empresa e o setor de atuacao?"

        # STEP 2: STRATEGY_VISION (Kaplan & Norton - Strategy Maps 2004)
        if not has_strategy:
            name_part = f" da {company_name}" if company_name else ""
            return (
                f"Para um diagnostico BSC efetivo{name_part}, preciso entender a estrategia. "
                "Qual a visao de longo prazo? Por que os clientes compram de voces?"
            )

        # STEP 3: BUSINESS_STAGE (Growth/Sustain/Harvest - determina KPIs)
        if not has_business_stage:
            name_part = f"A {company_name}" if company_name else "A empresa"
            return (
                f"{name_part} esta focada em CRESCER rapidamente, MANTER lucratividade, "
                "ou MAXIMIZAR fluxo de caixa? Isso determina os KPIs prioritarios."
            )

        # STEP 4: CUSTOMER_SEGMENTATION (Strategy Maps - Customer Perspective)
        if not has_customer_seg:
            return (
                "Quais sao os principais tipos/segmentos de clientes que voces atendem? "
                "Qual e o mais lucrativo?"
            )

        # STEP 5: CHALLENGES (minimo 2)
        if not has_challenges or "challenges" in context.missing_info:
            name_part = f" na {company_name}" if company_name else ""
            return f"Quais sao os principais desafios estrategicos{name_part} que voces enfrentam atualmente?"

        # STEP 6: OBJECTIVES (minimo 2)
        if not has_objectives or "objectives" in context.missing_info:
            name_part = f" da {company_name}" if company_name else ""
            return f"Quais sao os principais objetivos estrategicos{name_part}?"

        # STEPS OPCIONAIS (7-14): Se chegou aqui, dados minimos coletados
        # Verificar se falta algum dado opcional relevante
        has_operational_metrics = bool(
            partial_profile and partial_profile.get("production_metrics")
        )
        has_investments = bool(
            partial_profile
            and (
                partial_profile.get("investments_needed") or partial_profile.get("pending_projects")
            )
        )

        if not has_operational_metrics:
            name_part = f" da {company_name}" if company_name else ""
            return f"Para completar o diagnostico{name_part}, quais sao as principais metricas operacionais atuais (producao, vendas, etc)?"

        if not has_investments:
            return "Ha algum investimento planejado ou projeto em andamento que devo considerar no diagnostico?"

        return (
            "Entendi. Pode me contar mais detalhes que considere relevantes para o diagnostico BSC?"
        )

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

        SESSAO 50 (Dez/2025): Atualizado para incluir todos os 14 steps do enum.

        Args:
            step: Step a marcar (1-14)
            state: BSCState atual
        """
        step_keys = {
            # Steps obrigatorios (1-6)
            OnboardingStep.COMPANY_INFO: "company_info",
            OnboardingStep.STRATEGY_VISION: "strategy_vision",
            OnboardingStep.BUSINESS_STAGE: "business_stage",
            OnboardingStep.CUSTOMER_SEGMENTATION: "customer_segmentation",
            OnboardingStep.CHALLENGES: "challenges",
            OnboardingStep.OBJECTIVES: "objectives",
            # Steps opcionais (7-10)
            OnboardingStep.MVV: "mvv",
            OnboardingStep.COMPETITIVE_CONTEXT: "competitive_context",
            OnboardingStep.ORGANIZATION_STRUCTURE: "organization_structure",
            OnboardingStep.PROJECT_CONSTRAINTS: "project_constraints",
            # Perspectivas BSC (11-14)
            OnboardingStep.BSC_FINANCIAL: "bsc_financial",
            OnboardingStep.BSC_CUSTOMER: "bsc_customer",
            OnboardingStep.BSC_PROCESS: "bsc_process",
            OnboardingStep.BSC_LEARNING: "bsc_learning",
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

        # SESSAO 47: Bug fix - usar SystemMessage/HumanMessage para consistencia e robustez cross-provider
        from langchain_core.messages import HumanMessage, SystemMessage

        # Chamar LLM com structured output (JSON)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
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