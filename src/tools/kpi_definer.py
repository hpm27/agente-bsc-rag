"""KPI Definer Tool - Definicao de KPIs SMART para BSC.

Ferramenta consultiva que facilita a definicao estruturada de Key Performance
Indicators (KPIs) customizados para as 4 perspectivas do Balanced Scorecard,
seguindo criterios SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
"""

import logging
from typing import Optional, Protocol

from langchain_core.language_models import BaseLLM


class SpecialistAgent(Protocol):
    """Protocol para specialist agents com metodo invoke."""
    
    def invoke(self, query: str) -> dict:
        """Invoca agente especialista com query."""
        ...

from src.memory.schemas import (
    CompanyInfo,
    StrategicContext,
    CompleteDiagnostic,
    KPIDefinition,
    KPIFramework
)
from src.prompts.kpi_prompts import (
    FACILITATE_KPI_DEFINITION_PROMPT,
    build_company_context,
    build_diagnostic_context,
    build_bsc_knowledge_context
)


logger = logging.getLogger(__name__)


class KPIDefinerTool:
    """Ferramenta para definir KPIs SMART customizados para BSC.
    
    Usa LLM com structured output para gerar KPIs especificos, mensuraveis,
    atingiveis, relevantes e temporizados para as 4 perspectivas BSC.
    
    Attributes:
        llm: Modelo de linguagem para geracao de KPIs (GPT-4o-mini recomendado)
        financial_agent: Agente especialista perspectiva Financeira (Optional[SpecialistAgent])
        customer_agent: Agente especialista perspectiva Clientes (Optional[SpecialistAgent])
        process_agent: Agente especialista perspectiva Processos Internos (Optional[SpecialistAgent])
        learning_agent: Agente especialista perspectiva Aprendizado e Crescimento (Optional[SpecialistAgent])
    
    Example:
        >>> tool = KPIDefinerTool(
        ...     llm=get_llm("gpt-4o-mini"),
        ...     financial_agent=FinancialAgent(),
        ...     customer_agent=CustomerAgent(),
        ...     process_agent=ProcessAgent(),
        ...     learning_agent=LearningAgent()
        ... )
        >>> framework = tool.define_kpis(
        ...     company_info=CompanyInfo(...),
        ...     strategic_context=StrategicContext(...),
        ...     diagnostic_result=CompleteDiagnostic(...),
        ...     use_rag=True
        ... )
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        financial_agent: Optional[SpecialistAgent] = None,
        customer_agent: Optional[SpecialistAgent] = None,
        process_agent: Optional[SpecialistAgent] = None,
        learning_agent: Optional[SpecialistAgent] = None
    ):
        """Inicializa KPI Definer Tool.
        
        Args:
            llm: Modelo de linguagem (GPT-4o-mini recomendado)
            financial_agent: Agente Financial (opcional, para RAG)
            customer_agent: Agente Customer (opcional, para RAG)
            process_agent: Agente Process (opcional, para RAG)
            learning_agent: Agente Learning (opcional, para RAG)
        """
        self.llm = llm
        self.financial_agent: Optional[SpecialistAgent] = financial_agent
        self.customer_agent: Optional[SpecialistAgent] = customer_agent
        self.process_agent: Optional[SpecialistAgent] = process_agent
        self.learning_agent: Optional[SpecialistAgent] = learning_agent
        
        logger.info(
            "[KPI Definer Tool] Inicializado com LLM e "
            f"{4 if all([financial_agent, customer_agent, process_agent, learning_agent]) else 0} specialist agents"
        )
    
    def define_kpis(
        self,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        diagnostic_result: CompleteDiagnostic,
        use_rag: bool = True
    ) -> KPIFramework:
        """Define KPIs para as 4 perspectivas BSC.
        
        Metodo principal que orquestra a definicao completa de KPIs SMART
        customizados para empresa especifica baseado em diagnostico BSC.
        
        Args:
            company_info: Informacoes basicas da empresa
            strategic_context: Desafios e objetivos estrategicos
            diagnostic_result: Diagnostico BSC completo (4 perspectivas)
            use_rag: Se True, recupera conhecimento BSC via specialist agents
        
        Returns:
            KPIFramework: Framework completo com 2-8 KPIs por perspectiva (8-32 total)
        
        Raises:
            ValueError: Se parametros invalidos ou LLM falha
            ValidationError: Se KPIs gerados nao passam em validacoes Pydantic
        
        Example:
            >>> framework = tool.define_kpis(
            ...     company_info=CompanyInfo(name="TechCorp", sector="Tecnologia", size="Media"),
            ...     strategic_context=StrategicContext(...),
            ...     diagnostic_result=CompleteDiagnostic(...),
            ...     use_rag=True
            ... )
            >>> print(framework.total_kpis())  # 14 (4+3+4+3)
        """
        # Validacoes (ANTES de acessar qualquer atributo)
        if not company_info:
            raise ValueError("company_info ausente. Dados insuficientes para KPIs.")
        
        if not strategic_context:
            raise ValueError(
                "strategic_context ausente. "
                "Execute onboarding completo antes de definir KPIs."
            )
        
        if not diagnostic_result:
            raise ValueError(
                "diagnostic_result ausente. "
                "Execute run_diagnostic() antes de definir KPIs para contextualizar."
            )
        
        logger.info(
            f"[KPI Definer Tool] Definindo KPIs para {company_info.name} "
            f"(use_rag={use_rag})"
        )
        
        # Definir KPIs para cada perspectiva
        perspectives = [
            "Financeira",
            "Clientes",
            "Processos Internos",
            "Aprendizado e Crescimento"
        ]
        
        kpis_by_perspective = {}
        
        for perspective in perspectives:
            logger.info(f"[KPI Definer Tool] Definindo KPIs para perspectiva: {perspective}")
            
            kpis = self._define_perspective_kpis(
                perspective=perspective,
                company_info=company_info,
                strategic_context=strategic_context,
                diagnostic_result=diagnostic_result,
                use_rag=use_rag
            )
            
            kpis_by_perspective[perspective] = kpis
            logger.info(
                f"[KPI Definer Tool] {len(kpis)} KPIs definidos para {perspective}"
            )
        
        # Montar framework completo
        framework = KPIFramework(
            financial_kpis=kpis_by_perspective["Financeira"],
            customer_kpis=kpis_by_perspective["Clientes"],
            process_kpis=kpis_by_perspective["Processos Internos"],
            learning_kpis=kpis_by_perspective["Aprendizado e Crescimento"]
        )
        
        # Validar balanceamento
        is_balanced = self._validate_kpi_balance(framework)
        
        logger.info(
            f"[KPI Definer Tool] Framework completo gerado: "
            f"{framework.total_kpis()} KPIs total "
            f"(Financeira: {len(framework.financial_kpis)}, "
            f"Clientes: {len(framework.customer_kpis)}, "
            f"Processos: {len(framework.process_kpis)}, "
            f"Aprendizado: {len(framework.learning_kpis)}), "
            f"balanced={is_balanced}"
        )
        
        return framework
    
    def _define_perspective_kpis(
        self,
        perspective: str,
        company_info: CompanyInfo,
        strategic_context: StrategicContext,
        diagnostic_result: CompleteDiagnostic,
        use_rag: bool
    ) -> list[KPIDefinition]:
        """Define KPIs para uma perspectiva BSC especifica.
        
        Metodo privado que usa LLM structured output para gerar 2-8 KPIs
        customizados para perspectiva especifica.
        
        Args:
            perspective: Perspectiva BSC ("Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento")
            company_info: Informacoes basicas da empresa
            strategic_context: Desafios e objetivos estrategicos
            diagnostic_result: Diagnostico BSC completo
            use_rag: Se True, recupera conhecimento BSC via specialist agents
        
        Returns:
            list[KPIDefinition]: Lista de 2-8 KPIs para a perspectiva
        
        Raises:
            ValueError: Se LLM falha ou perspectiva invalida
        """
        # STEP 1: Construir contexto empresa
        company_context = build_company_context(company_info, strategic_context)
        
        # STEP 2: Construir contexto diagnostico perspectiva
        diagnostic_context = build_diagnostic_context(diagnostic_result, perspective)
        
        # STEP 3: (Opcional) RAG - Recuperar conhecimento BSC
        bsc_knowledge = ""
        if use_rag:
            rag_results = self._retrieve_bsc_knowledge(perspective, company_context)
            bsc_knowledge = build_bsc_knowledge_context(rag_results)
        else:
            bsc_knowledge = "RAG desabilitado. Definindo KPIs baseado apenas em contexto fornecido."
        
        # STEP 4: Construir prompt completo
        prompt = FACILITATE_KPI_DEFINITION_PROMPT.format(
            company_context=company_context,
            diagnostic_context=diagnostic_context,
            bsc_knowledge=bsc_knowledge,
            perspective=perspective
        )
        
        # STEP 5: LLM Structured Output
        try:
            # Criar structured output LLM para lista de KPIDefinition
            from pydantic import BaseModel
            
            class KPIListOutput(BaseModel):
                kpis: list[KPIDefinition]
            
            llm_structured = self.llm.with_structured_output(KPIListOutput)
            result = llm_structured.invoke(prompt)
            
            # Acessar .kpis (structured output sempre retorna objeto Pydantic)
            kpis = result.kpis
            
            # Validar quantidade (2-8 KPIs por perspectiva)
            if len(kpis) < 2:
                raise ValueError(
                    f"Perspectiva {perspective} gerou apenas {len(kpis)} KPIs, "
                    f"minimo 2 necessario"
                )
            
            if len(kpis) > 8:
                logger.warning(
                    f"[KPI Definer Tool] Perspectiva {perspective} gerou {len(kpis)} KPIs, "
                    f"limitando a 8"
                )
                kpis = kpis[:8]
            
            logger.info(
                f"[KPI Definer Tool] {len(kpis)} KPIs gerados para {perspective}: "
                f"{[kpi.name for kpi in kpis]}"
            )
            
            return kpis
        
        except Exception as e:
            logger.error(
                f"[KPI Definer Tool] Erro ao gerar KPIs para perspectiva {perspective}: {e}"
            )
            raise ValueError(
                f"Falha ao gerar KPIs para perspectiva {perspective}: {e}"
            ) from e
    
    def _retrieve_bsc_knowledge(
        self,
        perspective: str,
        context: str
    ) -> list[dict]:
        """Recupera conhecimento BSC via specialist agents (RAG opcional).
        
        Args:
            perspective: Perspectiva BSC
            context: Contexto da empresa para query RAG
        
        Returns:
            list[dict]: Lista de resultados RAG dos specialist agents
        """
        if not self._has_rag_agents():
            logger.warning("[KPI Definer Tool] Specialist agents nao configurados, RAG desabilitado")
            return []
        
        # Mapear perspectiva para agente
        agent_map = {
            "Financeira": self.financial_agent,
            "Clientes": self.customer_agent,
            "Processos Internos": self.process_agent,
            "Aprendizado e Crescimento": self.learning_agent
        }
        
        agent = agent_map.get(perspective)
        
        if not agent:
            logger.warning(
                f"[KPI Definer Tool] Agente para perspectiva {perspective} nao encontrado"
            )
            return []
        
        # Query RAG
        try:
            query = f"KPIs recomendados para perspectiva {perspective} no Balanced Scorecard segundo Kaplan e Norton"
            result = agent.invoke(query)
            
            return [result]
        
        except Exception as e:
            logger.warning(
                f"[KPI Definer Tool] Erro ao recuperar conhecimento BSC via RAG "
                f"para perspectiva {perspective}: {e}"
            )
            return []
    
    def _has_rag_agents(self) -> bool:
        """Verifica se specialist agents estao configurados para RAG.
        
        Returns:
            bool: True se todos os 4 agents estao configurados
        """
        return all([
            self.financial_agent,
            self.customer_agent,
            self.process_agent,
            self.learning_agent
        ])
    
    def _validate_kpi_balance(self, framework: KPIFramework) -> bool:
        """Valida se framework KPI esta balanceado entre perspectivas.
        
        Verifica se cada perspectiva tem entre 2-8 KPIs e se total esta
        entre 8-32 KPIs (ideal: 12-20).
        
        Args:
            framework: Framework completo de KPIs
        
        Returns:
            bool: True se framework balanceado, False caso contrario
        """
        total = framework.total_kpis()
        
        # Validar total (8-32, ideal 12-20)
        if total < 8:
            logger.warning(
                f"[KPI Definer Tool] Framework tem apenas {total} KPIs total, "
                f"recomendado minimo 8"
            )
            return False
        
        if total > 32:
            logger.warning(
                f"[KPI Definer Tool] Framework tem {total} KPIs total, "
                f"recomendado maximo 32"
            )
            return False
        
        # Validar distribuicao por perspectiva (2-8 cada)
        counts = {
            "Financeira": len(framework.financial_kpis),
            "Clientes": len(framework.customer_kpis),
            "Processos": len(framework.process_kpis),
            "Aprendizado": len(framework.learning_kpis)
        }
        
        for perspective, count in counts.items():
            if count < 2:
                logger.warning(
                    f"[KPI Definer Tool] Perspectiva {perspective} tem apenas {count} KPIs, "
                    f"minimo 2 recomendado"
                )
                return False
            
            if count > 8:
                logger.warning(
                    f"[KPI Definer Tool] Perspectiva {perspective} tem {count} KPIs, "
                    f"maximo 8 recomendado"
                )
                return False
        
        # Validar balanceamento relativo (nenhuma perspectiva com >40% do total)
        max_count = max(counts.values())
        max_percentage = (max_count / total) * 100
        
        if max_percentage > 40:
            logger.warning(
                f"[KPI Definer Tool] Desbalanceamento detectado: uma perspectiva tem "
                f"{max_percentage:.0f}% dos KPIs (maximo recomendado 40%)"
            )
            return False
        
        logger.info("[KPI Definer Tool] Framework KPI validado como balanceado")
        return True

