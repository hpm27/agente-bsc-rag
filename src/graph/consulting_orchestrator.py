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
