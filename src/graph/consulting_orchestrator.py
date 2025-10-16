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

from typing import TYPE_CHECKING, Any

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
        
        # In-memory sessions para onboarding multi-turn
        self._onboarding_sessions: dict[str, dict[str, Any]] = {}
        
        logger.info("[OK] ConsultingOrchestrator inicializado")
    
    @property
    def client_profile_agent(self) -> ClientProfileAgent:
        """Lazy loading ClientProfileAgent."""
        if self._client_profile_agent is None:
            from src.agents.client_profile_agent import ClientProfileAgent
            
            self._client_profile_agent = ClientProfileAgent(
                llm_model=settings.default_llm_model
            )
            logger.info("[LOAD] ClientProfileAgent carregado")
        
        return self._client_profile_agent
    
    @property
    def onboarding_agent(self) -> OnboardingAgent:
        """Lazy loading OnboardingAgent."""
        if self._onboarding_agent is None:
            from src.agents.onboarding_agent import OnboardingAgent
            
            self._onboarding_agent = OnboardingAgent(
                client_profile_agent=self.client_profile_agent,
                llm_model=settings.default_llm_model
            )
            logger.info("[LOAD] OnboardingAgent carregado")
        
        return self._onboarding_agent
    
    @property
    def diagnostic_agent(self) -> DiagnosticAgent:
        """Lazy loading DiagnosticAgent."""
        if self._diagnostic_agent is None:
            from src.agents.diagnostic_agent import DiagnosticAgent
            from src.rag.retriever import BSCRetriever
            
            retriever = BSCRetriever()
            
            # Criar specialist agents (Financial, Customer, Process, Learning)
            from src.agents.customer_agent import CustomerAgent
            from src.agents.financial_agent import FinancialAgent
            from src.agents.learning_agent import LearningAgent
            from src.agents.process_agent import ProcessAgent
            
            specialist_agents = {
                "financial": FinancialAgent(retriever=retriever),
                "customer": CustomerAgent(retriever=retriever),
                "process": ProcessAgent(retriever=retriever),
                "learning": LearningAgent(retriever=retriever)
            }
            
            self._diagnostic_agent = DiagnosticAgent(
                specialist_agents=specialist_agents,
                llm_model=settings.default_llm_model
            )
            logger.info("[LOAD] DiagnosticAgent carregado")
        
        return self._diagnostic_agent
    
    def coordinate_onboarding(self, state: BSCState) -> dict[str, Any]:
        """
        Coordena processo de onboarding multi-turn.
        
        Gerencia:
        - Sessões in-memory (stateless workflow)
        - Chamadas ao OnboardingAgent (start_onboarding, process_turn)
        - Criação de ClientProfile ao completar
        - Transição automática ONBOARDING → DISCOVERY
        
        Args:
            state: Estado atual com user_id, query (mensagem usuário)
        
        Returns:
            Estado atualizado com:
            - onboarding_progress (dict steps)
            - client_profile (se completo)
            - current_phase (ONBOARDING ou DISCOVERY)
            - response (mensagem para usuário)
        """
        try:
            user_id = state.user_id or "default_user"
            user_message = state.query or ""
            
            logger.info(
                f"[INFO] [ORCHESTRATOR] coordinate_onboarding | "
                f"user_id={user_id} | message={user_message[:50]}..."
            )
            
            # Load session (ou criar nova)
            session = self._onboarding_sessions.get(user_id, {})
            
            # Primeira interação? Iniciar onboarding
            if not session:
                response = self.onboarding_agent.start_onboarding()
                
                session = {
                    "started": True,
                    "progress": {},
                    "messages": [response]
                }
                
                self._onboarding_sessions[user_id] = session
                
                logger.info(
                    f"[INFO] [ORCHESTRATOR] Onboarding iniciado | user_id={user_id}"
                )
                
                return {
                    "onboarding_progress": session["progress"],
                    "final_response": response,
                    "current_phase": self._get_consulting_phase("ONBOARDING")
                }
            
            # Processar turn (resposta usuário)
            result = self.onboarding_agent.process_turn(
                user_message=user_message,
                state=state  # Passa state completo
            )
            
            # Atualizar session
            session["messages"].append(user_message)
            session["messages"].append(result["response"])
            session["progress"] = result.get("onboarding_progress", {})
            
            # Onboarding completo?
            if result.get("is_complete"):
                logger.info(
                    f"[OK] [ORCHESTRATOR] Onboarding completo | user_id={user_id} | "
                    f"Extraindo profile..."
                )
                
                # Extrair ClientProfile
                profile = self.client_profile_agent.extract_profile(state)
                
                # Cleanup session
                del self._onboarding_sessions[user_id]
                
                logger.info(
                    f"[OK] [ORCHESTRATOR] Profile criado | company={profile.company.name} | "
                    f"Transição → DISCOVERY"
                )
                
                return {
                    "client_profile": profile,
                    "onboarding_progress": session["progress"],
                    "final_response": result["response"],
                    "current_phase": self._get_consulting_phase("DISCOVERY")
                }
            
            # Ainda em andamento
            self._onboarding_sessions[user_id] = session
            
            return {
                "onboarding_progress": session["progress"],
                "final_response": result["response"],
                "current_phase": self._get_consulting_phase("ONBOARDING")
            }
            
        except Exception as e:
            logger.error(f"[ERROR] [ORCHESTRATOR] coordinate_onboarding: {e}")
            return self.handle_error(error=e, state=state, phase="ONBOARDING")
    
    def coordinate_discovery(self, state: BSCState) -> dict[str, Any]:
        """
        Coordena processo de diagnóstico BSC.
        
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
            
            # Validar ClientProfile
            if not state.client_profile:
                logger.warning(
                    "[WARN] [ORCHESTRATOR] ClientProfile ausente. "
                    "Fallback para ONBOARDING"
                )
                return {
                    "final_response": (
                        "Perfil do cliente não encontrado. "
                        "Por favor, complete o onboarding primeiro."
                    ),
                    "current_phase": self._get_consulting_phase("ONBOARDING")
                }
            
            # Executar diagnóstico
            complete_diagnostic = self.diagnostic_agent.run_diagnostic(state)
            
            logger.info(
                f"[OK] [ORCHESTRATOR] Diagnóstico completo | "
                f"Perspectivas: {len(complete_diagnostic.diagnostic_results)} | "
                f"Recomendações: {len(complete_diagnostic.recommendations)} | "
                f"Transição → APPROVAL_PENDING"
            )
            
            # Serializar CompleteDiagnostic (BSCState aceita dict)
            diagnostic_dict = complete_diagnostic.model_dump()
            
            # Gerar resumo para resposta
            summary = self._generate_diagnostic_summary(complete_diagnostic)
            
            return {
                "diagnostic": diagnostic_dict,
                "final_response": summary,
                "current_phase": self._get_consulting_phase("APPROVAL_PENDING")
            }
            
        except Exception as e:
            logger.error(f"[ERROR] [ORCHESTRATOR] coordinate_discovery: {e}")
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
        
        return {
            "final_response": (
                f"Ocorreu um erro durante a fase {phase}. "
                f"Por favor, tente novamente ou entre em contato com o suporte.\n\n"
                f"Detalhes: {error_msg}"
            ),
            "current_phase": self._get_consulting_phase("ERROR"),
            "metadata": {
                **state.metadata,
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
            f"\n**Perspectivas Analisadas:** {len(diagnostic.diagnostic_results)}",
            f"\n**Recomendações Prioritárias:** {len(diagnostic.recommendations)}\n"
        ]
        
        # Top 3 recomendações
        if diagnostic.recommendations:
            summary_parts.append("\n## Top 3 Recomendações:\n")
            for i, rec in enumerate(diagnostic.recommendations[:3], 1):
                summary_parts.append(
                    f"{i}. **{rec.title}** (Impacto: {rec.impact}, Prioridade: {rec.priority.value})\n"
                    f"   {rec.description}\n"
                )
        
        return "".join(summary_parts)
    
    def _get_consulting_phase(self, phase_str: str):
        """Helper para obter ConsultingPhase enum."""
        from src.graph.consulting_states import ConsultingPhase
        
        return getattr(ConsultingPhase, phase_str, ConsultingPhase.IDLE)

