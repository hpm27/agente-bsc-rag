"""
Consulting Orchestrator - Coordenação de Agentes Consultivos BSC.

Responsável por:
1. Coordenar agentes consultivos (OnboardingAgent, DiagnosticAgent, ClientProfileAgent)
2. Validar transições entre fases (ONBOARDING → DISCOVERY → APPROVAL)
3. Gerenciar sessions multi-turn (onboarding)
4. Error handling centralizado

Arquitetura baseada em LangGraph Multi-Agent Patterns (2024-2025):
- Coordination Layer (não supervisor-agent)
- Lazy loading de agentes (circular imports prevention)
- In-memory sessions para workflows stateless
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from config.settings import settings
from src.graph.states import BSCState
from src.memory.factory import MemoryFactory

if TYPE_CHECKING:
    from src.agents.client_profile_agent import ClientProfileAgent
    from src.agents.diagnostic_agent import DiagnosticAgent
    from src.agents.onboarding_agent import OnboardingAgent
    from src.graph.consulting_states import ConsultingPhase


class ConsultingOrchestrator:
    """
    Orquestrador de agentes consultivos BSC.
    
    Coordena OnboardingAgent, DiagnosticAgent, ClientProfileAgent
    seguindo workflow: ONBOARDING → DISCOVERY → APPROVAL → SOLUTION_DESIGN.
    """
    
    def __init__(self):
        """Inicializa orchestrator com lazy loading de agentes."""
        self.memory_factory = MemoryFactory()
        
        # Lazy loading (previne circular imports)
        self._client_profile_agent = None
        self._onboarding_agent = None
        self._diagnostic_agent = None
        
        logger.info("[OK] ConsultingOrchestrator inicializado")
    
    @property
    def client_profile_agent(self) -> ClientProfileAgent:
        """Lazy loading ClientProfileAgent."""
        if self._client_profile_agent is None:
            from src.agents.client_profile_agent import ClientProfileAgent
            
            # ClientProfileAgent cria próprio LLM (GPT-4o-mini default)
            self._client_profile_agent = ClientProfileAgent()
            logger.info("[LOAD] ClientProfileAgent carregado")
        
        return self._client_profile_agent
    
    @property
    def onboarding_agent(self) -> OnboardingAgent:
        """Lazy loading OnboardingAgent."""
        if self._onboarding_agent is None:
            from langchain_openai import ChatOpenAI
            from src.agents.onboarding_agent import OnboardingAgent
            from src.memory.mem0_client import Mem0ClientWrapper
            
            # Criar LLM objeto (GPT-5 family para onboarding conversacional)
            # Suporta: gpt-5-2025-08-07 (default) ou gpt-5-mini-2025-08-07 (econômico)
            llm = ChatOpenAI(
                model=settings.onboarding_llm_model,
                temperature=1.0,  # GPT-5 family: temperature=1.0 obrigatório
                max_completion_tokens=settings.gpt5_max_completion_tokens,
                reasoning_effort="low"  # Low reasoning para conversação rápida (parâmetro direto)
            )
            
            # Obter memory client a partir do provider (evita inicialização indevida em testes)
            try:
                provider = self.memory_factory.get_provider()
                memory_client = getattr(provider, "client", None)
            except Exception:
                memory_client = None

            self._onboarding_agent = OnboardingAgent(
                llm=llm,
                client_profile_agent=self.client_profile_agent,
                memory_client=memory_client
            )
            logger.info("[LOAD] OnboardingAgent carregado")
        
        return self._onboarding_agent
    
    @property
    def diagnostic_agent(self) -> DiagnosticAgent:
        """Lazy loading DiagnosticAgent - FORCE RELOAD v3.4."""
        # FORÇA RELOAD SEMPRE (temporário para debug)
        # TODO: Remover após confirmar v3.4 funcionando
        from src.agents.diagnostic_agent import DiagnosticAgent
        
        logger.info("[ORCHESTRATOR v3.8-20251022-15:00] FORCE RELOAD DiagnosticAgent (bypass cache)...")
        
        # DiagnosticAgent cria próprio LLM (GPT-5 com max_completion_tokens=64000)
        # Specialist agents criados internamente pelo DiagnosticAgent
        self._diagnostic_agent = DiagnosticAgent()
        
        logger.info("[ORCHESTRATOR v3.8-20251022-15:00] DiagnosticAgent recarregado com sucesso")
        logger.info(f"[ORCHESTRATOR v3.8-20251022-15:00] DiagnosticAgent type: {type(self._diagnostic_agent)}")
        logger.info(f"[ORCHESTRATOR v3.8-20251022-15:00] DiagnosticAgent module: {self._diagnostic_agent.__module__}")
        
        return self._diagnostic_agent
    
    async def coordinate_onboarding(self, state: BSCState) -> dict[str, Any]:
        """
        Coordena processo de onboarding conversacional do cliente.
        
        NOVO FLUXO (FASE 1+2 - Refatoração Out/2025):
        - Usa OnboardingAgent.collect_client_info() unificado
        - Extração oportunística de entidades (ordem livre)
        - Validação semântica de challenges/objectives (FASE 2)
        - Perguntas contextuais adaptativas
        - Persistência automática em state.metadata["partial_profile"]
        
        Gerencia:
        - Coleta conversacional de informações (qualquer ordem)
        - Acumulação progressiva de conhecimento
        - Persistência de ClientProfile quando informações mínimas completas
        - Transição automática ONBOARDING → DISCOVERY
        
        Args:
            state: Estado BSC atual (será atualizado)
        
        Returns:
            Estado atualizado contendo:
            - final_response: Próxima pergunta ou mensagem de conclusão
            - is_complete: True se onboarding finalizado
            - current_phase: ONBOARDING ou DISCOVERY
            - previous_phase: Fase anterior
            - phase_history: Histórico de transições
        """
        try:
            user_id = state.user_id or "anonymous"
            user_message = state.query or ""
            
            logger.info(
                "[ORCHESTRATOR] coordinate_onboarding | user_id=%s | message=%s",
                user_id,
                user_message[:50] if len(user_message) > 50 else user_message
            )
            
            # NOVO FLUXO: collect_client_info() unificado (não mais start + process_turn)
            # Método async, acumula conhecimento em state.metadata["partial_profile"]
            result = await self.onboarding_agent.collect_client_info(
                user_id=user_id,
                user_message=user_message,
                state=state  # collect_client_info() atualiza state internamente
            )
            
            # Verificar se onboarding completo
            if result["is_complete"]:
                logger.info("[ORCHESTRATOR] ===== ONBOARDING COMPLETO! ===== | user_id=%s", user_id)
                logger.info("[ORCHESTRATOR] state.current_phase ANTES de transition: %s", state.current_phase)
                
                # Cleanup metadata (partial_profile não mais necessário)
                state.metadata.pop("partial_profile", None)
                
                # Preparar transição para DISCOVERY
                transition_data = self._prepare_phase_transition(
                    state=state,
                    to_phase=self._get_consulting_phase("DISCOVERY"),
                    trigger="profile_completed"
                )
                
                logger.info("[ORCHESTRATOR] transition_data: %s", transition_data)
                logger.info("[ORCHESTRATOR] state.current_phase DEPOIS de transition: %s", state.current_phase)
                logger.info("[ORCHESTRATOR] state.client_profile criado: %s", state.client_profile is not None)
                
                # CRÍTICO: Retornar client_profile para persistir no checkpoint!
                final_return = {
                    "final_response": result["question"],
                    "is_complete": True,
                    "client_profile": state.client_profile,  # Persistir no checkpoint
                    **transition_data
                }
                
                logger.info(
                    "[ORCHESTRATOR] ===== RETORNANDO (is_complete=True): current_phase=%s, has_client_profile=%s =====",
                    final_return.get("current_phase"),
                    final_return.get("client_profile") is not None
                )
                return final_return
            
            # Onboarding ainda em progresso
            logger.info("[ORCHESTRATOR] Onboarding em progresso | user_id=%s", user_id)
            
            transition_data = self._prepare_phase_transition(
                state=state,
                to_phase=self._get_consulting_phase("ONBOARDING"),
                trigger="onboarding_in_progress"
            )
            
            # CRÍTICO: Retornar metadata atualizado para persistir partial_profile entre turnos
            return {
                "final_response": result["question"],
                "metadata": state.metadata,  # Persistir acumulação de informações
                **transition_data
            }
            
        except Exception as e:
            logger.error("[ORCHESTRATOR] coordinate_onboarding error: %s", str(e))
            return self.handle_error(error=e, state=state, phase="ONBOARDING")
    
    async def coordinate_discovery(self, state: BSCState) -> dict[str, Any]:
        """
        Coordena processo de diagnóstico BSC (ASYNC para paralelizar 4 agentes).
        
        Gerencia:
        - Validação de ClientProfile existente
        - Chamada ao DiagnosticAgent.run_diagnostic()
        - Persistência de CompleteDiagnostic
        - Transição automática DISCOVERY → APPROVAL_PENDING
        
        Args:
            state: Estado com client_profile obrigatório
        
        Returns:
            Estado atualizado com:
            - diagnostic (CompleteDiagnostic serializado)
            - current_phase (APPROVAL_PENDING)
            - response (resumo diagnóstico)
        """
        try:
            logger.info("[INFO] [ORCHESTRATOR] coordinate_discovery iniciado")
            logger.debug(f"[DEBUG] [ORCHESTRATOR] state.client_profile existe? {state.client_profile is not None}")
            
            # Validar ClientProfile
            if not state.client_profile:
                logger.warning(
                    "[WARN] [ORCHESTRATOR] ClientProfile ausente. "
                    "Fallback para ONBOARDING"
                )
                transition_data = self._prepare_phase_transition(
                    state=state,
                    to_phase=self._get_consulting_phase("ONBOARDING"),
                    trigger="profile_missing"
                )
                if transition_data["current_phase"] == transition_data.get("previous_phase"):
                    transition_data.pop("previous_phase", None)
                return {
                    "final_response": (
                        "Perfil do cliente não encontrado. "
                        "Por favor, complete o onboarding primeiro."
                    ),
                    **transition_data
                }
            
            logger.debug("[DEBUG] [ORCHESTRATOR] Validação client_profile PASSOU")
            logger.debug(f"[DEBUG] [ORCHESTRATOR] Acessando self.diagnostic_agent (lazy loading)...")

            # Hardening: garantir que nested dicts foram convertidos antes do diagnóstico
            try:
                cp = state.client_profile
                # Se vier dict do checkpoint, converter aqui também (defensive)
                if isinstance(cp, dict):
                    from src.memory.schemas import ClientProfile, StrategicContext, CompanyInfo
                    if 'context' in cp and isinstance(cp['context'], dict):
                        cp['context'] = StrategicContext(**cp['context'])
                    if 'company' in cp and isinstance(cp['company'], dict):
                        cp['company'] = CompanyInfo(**cp['company'])
                    state.client_profile = ClientProfile(**cp)
                else:
                    # Se já for Pydantic, normalizar nested se necessário
                    from src.memory.schemas import StrategicContext, CompanyInfo
                    if hasattr(cp, 'context') and isinstance(cp.context, dict):
                        cp.context = StrategicContext(**cp.context)
                    if hasattr(cp, 'company') and isinstance(cp.company, dict):
                        cp.company = CompanyInfo(**cp.company)
            except Exception as norm_err:
                logger.warning(f"[ORCHESTRATOR] Falha ao normalizar client_profile nested dicts: {norm_err}")
            
            # Executar diagnóstico (ASYNC: 4 agentes em paralelo com asyncio.gather)
            logger.debug("[DEBUG] [ORCHESTRATOR] ANTES de chamar diagnostic_agent.run_diagnostic()")
            complete_diagnostic = await self.diagnostic_agent.run_diagnostic(state)
            logger.debug(f"[DEBUG] [ORCHESTRATOR] DEPOIS de chamar run_diagnostic() | Recomendações: {len(complete_diagnostic.recommendations)}")
            
            logger.info(
                f"[OK] [ORCHESTRATOR] Diagnóstico completo | "
                f"Perspectivas: 4 (Financial, Customer, Process, Learning) | "
                f"Recomendações: {len(complete_diagnostic.recommendations)} | "
                f"Transição → APPROVAL_PENDING"
            )
            
            # Serializar CompleteDiagnostic (BSCState aceita dict)
            diagnostic_dict = complete_diagnostic.model_dump()
            
            # Gerar resumo para resposta
            summary = self._generate_diagnostic_summary(complete_diagnostic)
            
            transition_data = self._prepare_phase_transition(
                state=state,
                to_phase=self._get_consulting_phase("APPROVAL_PENDING"),
                trigger="diagnostic_completed"
            )
            
            return {
                "diagnostic": diagnostic_dict,
                "final_response": summary,
                "is_complete": True,
                **transition_data
            }
            
        except Exception as e:
            # Log detalhado com traceback
            logger.exception("[ERROR] [ORCHESTRATOR] coordinate_discovery falhou com exceção")
            return self.handle_error(error=e, state=state, phase="DISCOVERY")
    
    def validate_transition(
        self,
        from_phase: ConsultingPhase | str,
        to_phase: ConsultingPhase | str,
        state: BSCState
    ) -> bool:
        """
        Valida se transição entre fases é permitida.
        
        Regras:
        - ONBOARDING → DISCOVERY: Requer onboarding_progress completo
        - DISCOVERY → APPROVAL_PENDING: Requer diagnostic presente
        - APPROVAL_PENDING → END: Requer approval_status = APPROVED
        - APPROVAL_PENDING → DISCOVERY: Permitido (refazer diagnóstico)
        
        Args:
            from_phase: Fase origem
            to_phase: Fase destino
            state: Estado atual para validação
        
        Returns:
            True se transição válida, False caso contrário
        """
        # Converter strings para enum se necessário
        from_phase_str = str(from_phase).split(".")[-1] if hasattr(from_phase, "value") else from_phase
        to_phase_str = str(to_phase).split(".")[-1] if hasattr(to_phase, "value") else to_phase
        
        logger.info(
            f"[VALIDATE] Transição: {from_phase_str} → {to_phase_str}"
        )
        
        # ONBOARDING → DISCOVERY
        if from_phase_str == "ONBOARDING" and to_phase_str == "DISCOVERY":
            is_complete = all(
                step_done for step_done in (state.onboarding_progress or {}).values()
            )
            if not is_complete:
                logger.warning(
                    "[WARN] [VALIDATE] Transição bloqueada: Onboarding incompleto"
                )
                return False
        
        # DISCOVERY → APPROVAL_PENDING
        elif from_phase_str == "DISCOVERY" and to_phase_str == "APPROVAL_PENDING":
            if not state.diagnostic:
                logger.warning(
                    "[WARN] [VALIDATE] Transição bloqueada: Diagnostic ausente"
                )
                return False
        
        # APPROVAL_PENDING → END
        elif from_phase_str == "APPROVAL_PENDING" and to_phase_str == "END":
            from src.graph.consulting_states import ApprovalStatus
            
            if state.approval_status != ApprovalStatus.APPROVED:
                logger.warning(
                    f"[WARN] [VALIDATE] Transição bloqueada: "
                    f"approval_status={state.approval_status} (esperado APPROVED)"
                )
                return False
        
        # Transição válida
        logger.info(f"[OK] [VALIDATE] Transição permitida: {from_phase_str} → {to_phase_str}")
        return True
    
    def handle_error(
        self,
        error: Exception,
        state: BSCState,
        phase: str = "UNKNOWN"
    ) -> dict[str, Any]:
        """
        Gerencia erros centralizadamente.
        
        Estratégia:
        - Log detalhado do erro
        - Fallback para fase segura (ONBOARDING)
        - Mensagem amigável para usuário
        - Metadata com erro para debugging
        
        Args:
            error: Exceção capturada
            state: Estado atual
            phase: Fase onde erro ocorreu
        
        Returns:
            Estado com fallback e mensagem de erro
        """
        error_msg = str(error)
        logger.error(
            f"[ERROR] [ORCHESTRATOR] Fase={phase} | Erro: {error_msg} | "
            f"Type: {type(error).__name__}"
        )
        
        # Defensive programming: verificar se state tem metadata
        existing_metadata = getattr(state, "metadata", {}) or {}
        
        return {
            "final_response": (
                f"Ocorreu um erro durante a fase {phase}. "
                f"Por favor, tente novamente ou entre em contato com o suporte.\n\n"
                f"Detalhes: {error_msg}"
            ),
            "current_phase": self._get_consulting_phase("ERROR"),
            "metadata": {
                **existing_metadata,
                f"{phase.lower()}_error": error_msg,
                "error_type": type(error).__name__
            }
        }
    
    async def facilitate_cot_consulting(
        self,
        client_profile: Any,
        client_query: str | None = None,
        bsc_knowledge: str | None = None
    ) -> str:
        """
        FASE 3.8: Facilitador Chain of Thought para consultoria BSC.
        
        Usa Chain of Thought reasoning para quebrar problemas complexos
        de consultoria BSC em etapas lógicas sequenciais com transparência
        completa no processo de raciocínio.
        
        Args:
            client_profile: ClientProfile Pydantic (contexto empresa)
            client_query: Query específica do cliente (opcional)
            bsc_knowledge: Conhecimento BSC adicional (opcional)
        
        Returns:
            Resposta estruturada com Chain of Thought (5 steps)
        
        Example:
            >>> orchestrator = ConsultingOrchestrator()
            >>> response = await orchestrator.facilitate_cot_consulting(
            ...     client_profile=profile,
            ...     client_query="Como implementar BSC em nossa empresa?"
            ... )
            >>> print(response)  # Chain of Thought estruturado
        
        Added: 2025-10-27 (FASE 3.8)
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
        
        from src.prompts.facilitator_cot_prompt import (
            FACILITATE_COT_PROMPT,
            FACILITATOR_COT_SYSTEM_PROMPT,
            build_company_context_for_cot,
            build_bsc_knowledge_context,
            build_client_query_context
        )
        
        try:
            logger.info("[FACILITATOR_COT] Iniciando consultoria Chain of Thought...")
            
            # Configurar LLM para CoT (GPT-5 mini para eficiência)
            llm = ChatOpenAI(
                model=settings.router_llm_model,  # GPT-5 mini
                temperature=1.0,  # GPT-5 family exige temperature=1.0
                max_completion_tokens=4000,  # Espaço para Chain of Thought completo
                reasoning_effort="medium"  # Raciocínio balanceado
            )
            
            # Construir contexto para CoT
            company_context = build_company_context_for_cot(client_profile)
            bsc_context = bsc_knowledge or build_bsc_knowledge_context()
            query_context = build_client_query_context(client_query)
            
            # Montar prompt CoT
            cot_prompt = FACILITATE_COT_PROMPT.format(
                company_context=company_context,
                bsc_knowledge=bsc_context,
                client_query=query_context
            )
            
            messages = [
                SystemMessage(content=FACILITATOR_COT_SYSTEM_PROMPT),
                HumanMessage(content=cot_prompt)
            ]
            
            # Executar Chain of Thought
            logger.info("[FACILITATOR_COT] Executando Chain of Thought reasoning...")
            response = await llm.ainvoke(messages)
            
            cot_result = response.content
            logger.info(
                f"[FACILITATOR_COT] [OK] Chain of Thought completo "
                f"({len(cot_result)} caracteres)"
            )
            
            return cot_result
            
        except Exception as e:
            logger.error(f"[FACILITATOR_COT] [ERROR] Falha: {e}")
            
            # Fallback: resposta estruturada básica
            fallback_response = f"""
**CHAIN OF THOUGHT FACILITATION - FALLBACK**

**STEP 1: ANÁLISE INICIAL**
- Tipo de problema: Consultoria BSC (análise limitada devido a erro técnico)
- Perspectivas BSC relevantes: Todas as 4 (Financeira, Cliente, Processos, Aprendizado)
- Complexidade: A determinar após análise completa
- Informações críticas: Erro técnico impediu análise detalhada

**STEP 2: DECOMPOSIÇÃO**
- Sub-problemas identificados: A definir após análise técnica
- Dependências: A mapear
- Priorização: A estabelecer

**STEP 3: ANÁLISE ESTRATÉGICA**
- Perspectiva Financeira: Análise pendente
- Perspectiva Cliente: Análise pendente  
- Perspectiva Processos: Análise pendente
- Perspectiva Aprendizado: Análise pendente
- Gaps identificados: A identificar

**STEP 4: ALTERNATIVAS**
- Alternativas: A desenvolver após análise completa

**STEP 5: RECOMENDAÇÃO**
- Recomendação principal: Resolver erro técnico e refazer análise
- Próximos passos: Contatar suporte técnico
- Responsáveis: Equipe técnica
- Cronograma: Imediato
- Métricas de sucesso: Resolução do erro e análise completa

**ERRO TÉCNICO:** {str(e)}
**AÇÃO:** Por favor, tente novamente ou entre em contato com o suporte.
"""
            
            return fallback_response

    def _generate_diagnostic_summary(self, diagnostic: Any) -> str:
        """
        Gera resumo executivo do diagnóstico BSC.
        
        Args:
            diagnostic: CompleteDiagnostic Pydantic
        
        Returns:
            Resumo em markdown
        """
        summary_parts = [
            "# [CHECK] Diagnóstico BSC Completo\n",
            f"**Executive Summary:** {diagnostic.executive_summary}\n",
            f"\n**Perspectivas Analisadas:** 4 (Financial, Customer, Process, Learning)",
            f"\n**Recomendações Prioritárias:** {len(diagnostic.recommendations)}\n"
        ]
        
        # Top 3 recomendações
        if diagnostic.recommendations:
            summary_parts.append("\n## Top 3 Recomendações:\n")
            for i, rec in enumerate(diagnostic.recommendations[:3], 1):
                summary_parts.append(
                    f"{i}. **{rec.title}** (Impacto: {rec.impact}, Prioridade: {rec.priority})\n"
                    f"   {rec.description}\n"
                )
        else:
            summary_parts.append("\n(Nenhuma recomendação gerada)\n")
        
        return "".join(summary_parts)
    
    def _get_consulting_phase(self, phase_str: str):
        """Helper para obter ConsultingPhase enum."""
        from src.graph.consulting_states import ConsultingPhase
        
        return getattr(ConsultingPhase, phase_str, ConsultingPhase.IDLE)

    def _prepare_phase_transition(
        self,
        state: BSCState,
        to_phase,
        trigger: str | None = None
    ) -> dict[str, Any]:
        """Prepara dados de transição de fase para o state.

        Retorna dict com `previous_phase`, `current_phase` e `phase_history` atualizado.
        """
        # Import lazy para evitar circular
        from src.graph.consulting_states import ConsultingPhase

        # Determinar fase anterior
        from_phase = state.current_phase
        if not from_phase:
            # Tentar derivar do ClientProfile.engagement
            try:
                if state.client_profile and state.client_profile.engagement and state.client_profile.engagement.current_phase:
                    phase_value = state.client_profile.engagement.current_phase.upper()
                    # Map básico
                    mapping = {
                        "ONBOARDING": ConsultingPhase.ONBOARDING,
                        "DISCOVERY": ConsultingPhase.DISCOVERY,
                        "DESIGN": ConsultingPhase.SOLUTION_DESIGN,
                        "APPROVAL_PENDING": ConsultingPhase.APPROVAL_PENDING,
                        "IMPLEMENTATION": ConsultingPhase.IMPLEMENTATION,
                        "COMPLETED": ConsultingPhase.IDLE,
                    }
                    from_phase = mapping.get(phase_value, ConsultingPhase.ONBOARDING)
            except Exception:
                from_phase = None

        # Atualizar histórico
        history = list(state.phase_history or [])
        try:
            from_phase_name = (from_phase.name if from_phase else "UNKNOWN")
            to_phase_name = (
                to_phase.name if hasattr(to_phase, "name") else str(to_phase).upper()
            )
            history.append({
                "from_phase": from_phase_name,
                "to_phase": to_phase_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **({"trigger": trigger} if trigger else {})
            })
        except Exception:
            # Em caso de tipos inesperados, garantir append mínimo
            history.append({
                "from_phase": "UNKNOWN",
                "to_phase": str(getattr(to_phase, "name", to_phase)).upper(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return {
            "previous_phase": from_phase,
            "current_phase": to_phase,
            "phase_history": history
        }
    
    # ========================================================================
    # TOOL SELECTION LOGIC (FASE 3.7 - Hybrid Heuristic+LLM)
    # ========================================================================
    
    def _classify_with_heuristics(
        self,
        query: str | None,
        diagnostic_result: Any | None
    ) -> str | None:
        """Classifica tool usando heuristica keyword-based (90% casos).
        
        Abordagem: Regex keywords para deteccao rapida de tool mais adequada.
        Se nenhuma keyword match, retorna None (escala para LLM classifier).
        
        Args:
            query: Query opcional do usuario (texto livre)
            diagnostic_result: Resultado diagnostico previo (context adicional)
        
        Returns:
            tool_name (str) se match encontrado, None caso contrario
        """
        import re
        
        # Heuristicas por tool (keywords + patterns regex)
        # Ordem de prioridade: More specific → More generic
        
        # Combinar query + diagnostic summary para analise
        combined_text = ""
        if query:
            combined_text += query.lower()
        if diagnostic_result:
            # Extrair texto do diagnostic se disponivel
            if isinstance(diagnostic_result, dict):
                summary = diagnostic_result.get('executive_summary', '')
                if summary:
                    combined_text += " " + summary[:200].lower()
        
        if not combined_text:
            return None
        
        # 1. FIVE_WHYS (causa raiz - alta prioridade)
        five_whys_patterns = [
            r'\b(causa raiz|root cause|por que|why)\b',
            r'\b(investigar|origem do problema|problema especifico)\b',
            r'\b(5 whys|five whys|5 porques|cinco porques)\b'
        ]
        for pattern in five_whys_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: FIVE_WHYS (pattern: {pattern})")
                return "FIVE_WHYS"
        
        # 2. SWOT (forcas/fraquezas - alta prioridade)
        swot_patterns = [
            r'\b(swot|analise swot)\b',
            r'\b(forcas|fraquezas|oportunidades|ameacas)\b',
            r'\b(strengths|weaknesses|opportunities|threats)\b',
            r'\b(analise competitiva|posicionamento)\b'
        ]
        for pattern in swot_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: SWOT (pattern: {pattern})")
                return "SWOT"
        
        # 3. ISSUE_TREE (decompor problema - media prioridade)
        issue_tree_patterns = [
            r'\b(decompor|decompose|decomposi[cç]ao)\b',
            r'\b(sub-problemas|sub problemas|issue tree|arvore)\b',
            r'\b(quebrar problema|estruturar problema|mece)\b'
        ]
        for pattern in issue_tree_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: ISSUE_TREE (pattern: {pattern})")
                return "ISSUE_TREE"
        
        # 4. KPI_DEFINER (metricas - media prioridade)
        kpi_patterns = [
            r'\b(kpi|kpis|indicadores|metricas)\b',
            r'\b(medir|measurement|acompanhar|rastrear)\b',
            r'\b(targets|metas numericas|metas mensuraveis)\b'
        ]
        for pattern in kpi_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: KPI_DEFINER (pattern: {pattern})")
                return "KPI_DEFINER"
        
        # 5. STRATEGIC_OBJECTIVES (objetivos estrategicos - media prioridade)
        strategic_obj_patterns = [
            r'\b(objetivos estrategicos|strategic objectives)\b',
            r'\b(metas estrategicas|goals estrategicos)\b',
            r'\b(visao|missao|onde queremos chegar)\b',
            r'\b(plano estrategico|estrategia de longo prazo)\b'
        ]
        for pattern in strategic_obj_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: STRATEGIC_OBJECTIVES (pattern: {pattern})")
                return "STRATEGIC_OBJECTIVES"
        
        # 6. BENCHMARKING (comparacao setor - media prioridade)
        benchmarking_patterns = [
            r'\b(benchmark|benchmarking|comparacao)\b',
            r'\b(concorrentes|competidores|setor|industria)\b',
            r'\b(best practices|padrao de mercado|mercado)\b'
        ]
        for pattern in benchmarking_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: BENCHMARKING (pattern: {pattern})")
                return "BENCHMARKING"
        
        # 7. ACTION_PLAN (implementacao estrategica - alta prioridade)
        action_plan_patterns = [
            r'\b(plano de acao|action plan|implementar|implementacao)\b',
            r'\b(como fazer|como executar|passos|etapas)\b',
            r'\b(cronograma|timeline|prazo|deadline)\b',
            r'\b(responsavel|responsabilidade|quem faz)\b',
            r'\b(recursos necessarios|orçamento|custo)\b'
        ]
        for pattern in action_plan_patterns:
            if re.search(pattern, combined_text):
                logger.info(f"[HEURISTIC] Match: ACTION_PLAN (pattern: {pattern})")
                return "ACTION_PLAN"
        
        # Nenhum match - escalar para LLM
        logger.info("[HEURISTIC] Nenhum match - escalando para LLM classifier")
        return None
    
    async def _classify_with_llm(
        self,
        client_profile: Any,
        diagnostic_result: Any | None,
        query: str | None
    ):
        """Classifica tool usando LLM classifier GPT-5 mini (10% casos ambiguos).
        
        Abordagem: LLM structured output com prompt engenheirado (tool descriptions
        + few-shot examples) para casos que heuristica nao consegue resolver.
        
        Args:
            client_profile: ClientProfile Pydantic (contexto empresa)
            diagnostic_result: CompleteDiagnostic previo (contexto analise)
            query: Query opcional do usuario
        
        Returns:
            ToolSelection Pydantic com tool_name, confidence, reasoning
        
        Raises:
            Exception: Se LLM falha completamente (fallback no metodo pai)
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
        
        from src.memory.schemas import ToolSelection
        from src.prompts.tool_selection_prompts import (
            TOOL_SELECTION_SYSTEM_PROMPT,
            build_client_context,
            build_diagnostic_context
        )
        
        # LLM custo-efetivo (GPT-5 mini suficiente para classificacao)
        # Reutilizar configuracao router_llm_model (ja e GPT-5 mini)
        llm = ChatOpenAI(
            model=settings.router_llm_model,  # gpt-5-mini-2025-08-07
            temperature=1.0,  # GPT-5 family exige temperature=1.0
            max_completion_tokens=512,  # Classificacao usa poucos tokens
            reasoning_effort="low"  # Low reasoning para tarefa simples
        )
        
        # Estruturar output Pydantic
        llm_structured = llm.with_structured_output(ToolSelection)
        
        # Construir contexto
        client_ctx = build_client_context(client_profile)
        diagnostic_ctx = build_diagnostic_context(diagnostic_result)
        query_ctx = f"Query do usuario: {query}" if query else "Query nao fornecida"
        
        # Prompt completo
        human_prompt = f"""
{client_ctx}

{diagnostic_ctx}

{query_ctx}

Com base no contexto acima, selecione a ferramenta consultiva BSC mais adequada.
Retorne JSON estruturado com: tool_name, confidence, reasoning, alternative_tools (opcional).
"""
        
        messages = [
            SystemMessage(content=TOOL_SELECTION_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ]
        
        # Invocar LLM
        try:
            logger.info("[LLM_CLASSIFIER] Invocando GPT-5 mini para tool selection...")
            result = await llm_structured.ainvoke(messages)
            
            logger.info(
                f"[LLM_CLASSIFIER] Result: tool={result.tool_name}, "
                f"confidence={result.confidence:.2f}, "
                f"reasoning={result.reasoning[:50]}..."
            )
            
            return result
        
        except Exception as e:
            logger.error(f"[LLM_CLASSIFIER] Falha: {e}")
            raise
    
    async def suggest_tool(
        self,
        client_profile: Any,
        diagnostic_result: Any | None = None,
        user_query: str | None = None
    ):
        """Sugere ferramenta consultiva BSC mais adequada (metodo publico).
        
        Abordagem Hibrida (FASE 3.7 - validada Query Router FASE 2A):
        1. Heuristica keyword-based (90% casos) - Zero custo, instant
        2. LLM Classifier GPT-5 mini (10% casos ambiguos) - $0.01/1K queries
        3. Fallback SWOT (casos extremos) - Tool mais generica
        
        Args:
            client_profile: ClientProfile Pydantic (contexto empresa)
            diagnostic_result: CompleteDiagnostic previo opcional
            user_query: Query opcional do usuario (texto livre)
        
        Returns:
            ToolSelection Pydantic com tool_name, confidence, reasoning
        
        Example:
            >>> orchestrator = ConsultingOrchestrator()
            >>> selection = await orchestrator.suggest_tool(
            ...     client_profile=profile,
            ...     user_query="Por que nossas vendas cairam 30%?"
            ... )
            >>> print(selection.tool_name)  # "FIVE_WHYS"
            >>> print(selection.confidence)  # 0.95
        
        Added: 2025-10-27 (FASE 3.7)
        """
        from src.memory.schemas import ToolSelection
        
        logger.info(
            f"[TOOL_SELECTION] Iniciando selecao | "
            f"Query: {user_query[:50] if user_query else 'N/A'}..."
        )
        
        # STEP 1: Tentar heuristica (90% casos)
        tool_name_heuristic = self._classify_with_heuristics(
            query=user_query,
            diagnostic_result=diagnostic_result
        )
        
        if tool_name_heuristic:
            # Match encontrado - retornar com alta confidence
            logger.info(
                f"[TOOL_SELECTION] [OK] Heuristica match: {tool_name_heuristic}"
            )
            
            return ToolSelection(
                tool_name=tool_name_heuristic,
                confidence=0.92,  # Alta confidence (heuristica e precisa)
                reasoning=(
                    f"Heuristica keyword-based identificou {tool_name_heuristic} "
                    f"como ferramenta ideal baseado em keywords na query/contexto"
                )
            )
        
        # STEP 2: Escalar para LLM classifier (10% casos ambiguos)
        try:
            result_llm = await self._classify_with_llm(
                client_profile=client_profile,
                diagnostic_result=diagnostic_result,
                query=user_query
            )
            
            logger.info(
                f"[TOOL_SELECTION] [OK] LLM classifier: {result_llm.tool_name} "
                f"(confidence={result_llm.confidence:.2f})"
            )
            
            return result_llm
        
        except Exception as e:
            # STEP 3: Fallback SWOT (casos extremos)
            logger.warning(
                f"[TOOL_SELECTION] [FALLBACK] LLM falhou: {e}. "
                f"Usando fallback: SWOT"
            )
            
            return ToolSelection(
                tool_name="SWOT",
                confidence=0.50,  # Baixa confidence (fallback generico)
                reasoning=(
                    "Fallback automatico para SWOT (ferramenta mais generica) "
                    "devido a falha na classificacao heuristica e LLM"
                ),
                alternative_tools=["FIVE_WHYS", "ISSUE_TREE", "KPI_DEFINER", "ACTION_PLAN"]
            )