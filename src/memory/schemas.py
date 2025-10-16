"""Schemas Pydantic para ClientProfile e componentes relacionados.

Este módulo define os schemas de dados usados para armazenar
informações de clientes e engajamentos de consultoria BSC no Mem0.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# SCHEMAS BASE (sem dependências)
# ============================================================================


class SWOTAnalysis(BaseModel):
    """Análise SWOT estruturada.
    
    Armazena as 4 dimensões da análise SWOT: Forças, Fraquezas,
    Oportunidades e Ameaças identificadas durante o diagnóstico.
    
    Attributes:
        strengths: Lista de forças internas da organização
        weaknesses: Lista de fraquezas internas da organização
        opportunities: Lista de oportunidades externas
        threats: Lista de ameaças externas
    
    Example:
        >>> swot = SWOTAnalysis(
        ...     strengths=["Equipe qualificada", "Marca forte"],
        ...     weaknesses=["Processos manuais"],
        ...     opportunities=["Expansão digital"],
        ...     threats=["Concorrência intensa"]
        ... )
    """
    
    strengths: List[str] = Field(
        default_factory=list,
        description="Forças internas da organização"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Fraquezas internas da organização"
    )
    opportunities: List[str] = Field(
        default_factory=list,
        description="Oportunidades externas"
    )
    threats: List[str] = Field(
        default_factory=list,
        description="Ameaças externas"
    )


class CompanyInfo(BaseModel):
    """Informações básicas da empresa cliente.
    
    Contém dados fundamentais sobre a empresa que serão coletados
    durante o onboarding inicial.
    
    Attributes:
        name: Nome da empresa (obrigatório)
        sector: Setor de atuação (ex: Tecnologia, Manufatura, Serviços)
        size: Porte da empresa (micro, pequena, média, grande)
        industry: Indústria específica (opcional)
        founded_year: Ano de fundação (opcional, 1800-2025)
    
    Example:
        >>> company = CompanyInfo(
        ...     name="TechCorp Brasil",
        ...     sector="Tecnologia",
        ...     size="média",
        ...     industry="Software as a Service",
        ...     founded_year=2015
        ... )
    """
    
    name: str = Field(
        min_length=2,
        description="Nome da empresa"
    )
    sector: str = Field(
        description="Setor de atuação (ex: Tecnologia, Manufatura, Serviços)"
    )
    size: Literal["micro", "pequena", "média", "grande"] = Field(
        default="média",
        description="Porte da empresa"
    )
    industry: Optional[str] = Field(
        None,
        description="Indústria específica (opcional)"
    )
    founded_year: Optional[int] = Field(
        None,
        ge=1800,
        le=2025,
        description="Ano de fundação"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Valida que nome da empresa não é vazio após trim."""
        v = v.strip()
        if not v:
            raise ValueError("Nome da empresa não pode ser vazio")
        return v


# ============================================================================
# SCHEMAS INTERMEDIÁRIOS (contexto estratégico e diagnóstico)
# ============================================================================


class StrategicContext(BaseModel):
    """Contexto estratégico organizacional.
    
    Armazena informações sobre missão, visão, valores e objetivos
    estratégicos da organização, coletadas durante ONBOARDING e DISCOVERY.
    
    Attributes:
        mission: Declaração de missão da empresa (opcional)
        vision: Declaração de visão da empresa (opcional)
        core_values: Lista de valores centrais da organização
        strategic_objectives: Lista de objetivos estratégicos atuais
        current_challenges: Lista de desafios estratégicos enfrentados
    
    Example:
        >>> context = StrategicContext(
        ...     mission="Transformar a indústria através da inovação",
        ...     vision="Ser líder global até 2030",
        ...     core_values=["Inovação", "Integridade", "Excelência"],
        ...     strategic_objectives=["Crescer 30% ao ano", "Expandir para novos mercados"],
        ...     current_challenges=["Alta rotatividade", "Processos ineficientes"]
        ... )
    """
    
    mission: Optional[str] = Field(
        None,
        description="Declaração de missão da empresa"
    )
    vision: Optional[str] = Field(
        None,
        description="Declaração de visão da empresa"
    )
    core_values: List[str] = Field(
        default_factory=list,
        description="Valores centrais da organização"
    )
    strategic_objectives: List[str] = Field(
        default_factory=list,
        description="Objetivos estratégicos atuais"
    )
    current_challenges: List[str] = Field(
        default_factory=list,
        description="Desafios estratégicos atuais"
    )


class DiagnosticData(BaseModel):
    """Dados coletados durante fase DISCOVERY.
    
    Armazena todas as descobertas do diagnóstico organizacional,
    incluindo análise SWOT, pain points e oportunidades identificadas.
    
    Attributes:
        swot: Análise SWOT completa (opcional até DISCOVERY)
        pain_points: Lista de pontos de dor identificados
        opportunities: Lista de oportunidades de melhoria
        key_findings: Lista de descobertas-chave do diagnóstico
    
    Example:
        >>> swot = SWOTAnalysis(
        ...     strengths=["Equipe forte"],
        ...     weaknesses=["Processos manuais"]
        ... )
        >>> diagnostic = DiagnosticData(
        ...     swot=swot,
        ...     pain_points=["Falta de visibilidade de métricas"],
        ...     opportunities=["Automação de processos"],
        ...     key_findings=["BSC pode reduzir tempo de reporting em 70%"]
        ... )
    """
    
    swot: Optional[SWOTAnalysis] = Field(
        None,
        description="Análise SWOT completa"
    )
    pain_points: List[str] = Field(
        default_factory=list,
        description="Pontos de dor identificados"
    )
    opportunities: List[str] = Field(
        default_factory=list,
        description="Oportunidades de melhoria"
    )
    key_findings: List[str] = Field(
        default_factory=list,
        description="Descobertas-chave do diagnóstico"
    )


# ============================================================================
# ENGAGEMENT STATE (estado do engajamento consultoria)
# ============================================================================


class EngagementState(BaseModel):
    """Estado e progresso do engajamento de consultoria.
    
    Rastreia a fase atual do engajamento, progresso, milestones completados
    e timestamps relevantes.
    
    Attributes:
        current_phase: Fase atual do workflow (ONBOARDING → COMPLETED)
        started_at: Data/hora de início do engajamento
        last_interaction: Data/hora da última interação com o agente
        progress_percentage: Percentual de progresso (0-100%)
        completed_milestones: Lista de milestones já completados
    
    Example:
        >>> engagement = EngagementState(
        ...     current_phase="DISCOVERY",
        ...     progress_percentage=35,
        ...     completed_milestones=["Onboarding realizado", "SWOT completado"]
        ... )
        >>> # started_at e last_interaction são auto-gerados
    """
    
    current_phase: Literal[
        "ONBOARDING",
        "DISCOVERY",
        "DESIGN",
        "APPROVAL_PENDING",
        "IMPLEMENTATION",
        "COMPLETED"
    ] = Field(
        default="ONBOARDING",
        description="Fase atual do engajamento consultoria"
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de início do engajamento"
    )
    last_interaction: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora da última interação"
    )
    progress_percentage: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Percentual de progresso (0-100%)"
    )
    completed_milestones: List[str] = Field(
        default_factory=list,
        description="Milestones já completados"
    )


# ============================================================================
# CLIENT PROFILE (schema principal agregador)
# ============================================================================


class ClientProfile(BaseModel):
    """Perfil completo do cliente para engajamento de consultoria BSC.
    
    Schema principal que agrega todas as informações necessárias para
    conduzir um engajamento de consultoria em Balanced Scorecard, desde
    onboarding até implementação. Otimizado para armazenamento no Mem0.
    
    Attributes:
        client_id: Identificador único do cliente (UUID auto-gerado)
        company: Informações básicas da empresa (obrigatório)
        context: Contexto estratégico (missão, visão, objetivos)
        engagement: Estado atual do engajamento consultoria
        diagnostics: Dados de diagnóstico (SWOT, pain points) - opcional até DISCOVERY
        metadata: Dados customizados adicionais (dict livre)
        created_at: Data/hora de criação do perfil
        updated_at: Data/hora da última atualização (auto-atualizado)
    
    Example:
        >>> # Criar novo perfil de cliente
        >>> company = CompanyInfo(
        ...     name="TechCorp Brasil",
        ...     sector="Tecnologia",
        ...     size="média"
        ... )
        >>> profile = ClientProfile(company=company)
        >>> 
        >>> # Acessar dados
        >>> profile.client_id
        'a3b5c7d9-e1f2-4a5b-8c9d-0e1f2a3b4c5d'
        >>> profile.engagement.current_phase
        'ONBOARDING'
        >>> 
        >>> # Serializar para Mem0
        >>> mem0_data = profile.to_mem0()
        >>> type(mem0_data)
        <class 'dict'>
        >>> 
        >>> # Deserializar de Mem0
        >>> restored = ClientProfile.from_mem0(mem0_data)
        >>> restored.company.name
        'TechCorp Brasil'
    """
    
    client_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Identificador único do cliente (UUID)"
    )
    company: CompanyInfo = Field(
        description="Informações básicas da empresa"
    )
    context: StrategicContext = Field(
        default_factory=StrategicContext,
        description="Contexto estratégico organizacional"
    )
    engagement: EngagementState = Field(
        default_factory=EngagementState,
        description="Estado atual do engajamento"
    )
    diagnostics: Optional[DiagnosticData] = Field(
        None,
        description="Dados de diagnóstico (preenchido em DISCOVERY)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Dados customizados adicionais"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de criação do perfil"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora da última atualização"
    )
    
    @model_validator(mode='after')
    def update_timestamp(self) -> 'ClientProfile':
        """Atualiza timestamp de atualização automaticamente."""
        self.updated_at = datetime.now(timezone.utc)
        return self
    
    def to_mem0(self) -> dict:
        """Serializa ClientProfile para formato Mem0 (JSON/dict).
        
        Converte o schema Pydantic para um dicionário JSON-serializável,
        incluindo conversão automática de datetime para ISO 8601 string.
        
        Returns:
            dict: Dicionário pronto para armazenamento no Mem0
        
        Example:
            >>> profile = ClientProfile(company=CompanyInfo(name="Test", sector="Tech"))
            >>> mem0_data = profile.to_mem0()
            >>> isinstance(mem0_data, dict)
            True
            >>> 'client_id' in mem0_data
            True
        """
        return self.model_dump(mode='json', exclude_none=True)
    
    @classmethod
    def from_mem0(cls, data: dict) -> 'ClientProfile':
        """Deserializa ClientProfile de formato Mem0 (JSON/dict).
        
        Reconstrói o schema Pydantic a partir de um dicionário,
        incluindo validação automática de todos os campos.
        
        Args:
            data: Dicionário retornado do Mem0
        
        Returns:
            ClientProfile: Instância validada do schema
        
        Raises:
            ValidationError: Se os dados não passarem nas validações Pydantic
        
        Example:
            >>> mem0_data = {...}  # Dados do Mem0
            >>> profile = ClientProfile.from_mem0(mem0_data)
            >>> isinstance(profile, ClientProfile)
            True
        """
        return cls.model_validate(data)


# ============================================================================
# DIAGNOSTIC SCHEMAS (Fase 2.5 - DiagnosticAgent)
# ============================================================================


class DiagnosticResult(BaseModel):
    """Análise diagnóstica de uma perspectiva BSC individual.
    
    Resultado estruturado da análise de uma das 4 perspectivas do
    Balanced Scorecard (Financeira, Clientes, Processos Internos,
    Aprendizado e Crescimento) realizada pelo DiagnosticAgent.
    
    Attributes:
        perspective: Nome da perspectiva BSC analisada
        current_state: Descrição do estado atual da perspectiva (mínimo 20 caracteres)
        gaps: Lista de gaps identificados (mínimo 1 item)
        opportunities: Lista de oportunidades de melhoria (mínimo 1 item)
        priority: Nível de prioridade da perspectiva (HIGH, MEDIUM, LOW)
        key_insights: Lista de insights principais da análise (opcional)
    
    Example:
        >>> result = DiagnosticResult(
        ...     perspective="Financeira",
        ...     current_state="Receita crescente mas margens comprimidas por custos operacionais altos",
        ...     gaps=["Falta de visibilidade de custos por produto", "Orçamento anual desatualizado"],
        ...     opportunities=["Implementar ABC Costing", "Revisar pricing strategy"],
        ...     priority="HIGH",
        ...     key_insights=["Margens caíram 5pp em 12 meses", "Top 3 produtos geram 80% receita"]
        ... )
    """
    
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"] = Field(
        description="Perspectiva BSC analisada"
    )
    current_state: str = Field(
        min_length=20,
        description="Descrição do estado atual da perspectiva"
    )
    gaps: list[str] = Field(
        min_length=1,
        description="Gaps identificados na perspectiva"
    )
    opportunities: list[str] = Field(
        min_length=1,
        description="Oportunidades de melhoria identificadas"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Nível de prioridade da perspectiva"
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="Insights principais da análise"
    )
    
    @field_validator('gaps', 'opportunities')
    @classmethod
    def validate_non_empty_lists(cls, v: list[str], info) -> list[str]:
        """Valida que listas não são vazias."""
        if not v or len(v) == 0:
            raise ValueError(f"{info.field_name} não pode ser lista vazia")
        return v


class Recommendation(BaseModel):
    """Recomendação acionável do diagnóstico BSC.
    
    Recomendação estratégica priorizada por impacto vs esforço, com
    ações específicas e timeframe estimado para implementação.
    
    Attributes:
        title: Título conciso da recomendação (mínimo 10 caracteres)
        description: Descrição detalhada da recomendação (mínimo 50 caracteres)
        impact: Impacto esperado da recomendação (HIGH, MEDIUM, LOW)
        effort: Esforço necessário para implementação (HIGH, MEDIUM, LOW)
        priority: Prioridade final da recomendação (HIGH, MEDIUM, LOW)
        timeframe: Prazo estimado de implementação (ex: "3-6 meses", "Curto prazo")
        next_steps: Lista de próximas ações específicas (mínimo 1 item)
    
    Example:
        >>> rec = Recommendation(
        ...     title="Implementar Activity-Based Costing",
        ...     description="Substituir sistema atual de custos por ABC para aumentar visibilidade de rentabilidade por produto e cliente, permitindo decisões estratégicas baseadas em dados precisos de margem.",
        ...     impact="HIGH",
        ...     effort="MEDIUM",
        ...     priority="HIGH",
        ...     timeframe="6-9 meses",
        ...     next_steps=[
        ...         "Contratar consultor especializado em ABC",
        ...         "Mapear processos e atividades atuais (2 meses)",
        ...         "Pilotar em 1 linha de produto (3 meses)"
        ...     ]
        ... )
    """
    
    title: str = Field(
        min_length=10,
        description="Título conciso da recomendação"
    )
    description: str = Field(
        min_length=50,
        description="Descrição detalhada da recomendação"
    )
    impact: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Impacto esperado da recomendação"
    )
    effort: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Esforço necessário para implementação"
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Prioridade final (calculada por impacto vs esforço)"
    )
    timeframe: str = Field(
        description="Prazo estimado de implementação"
    )
    next_steps: list[str] = Field(
        min_length=1,
        description="Próximas ações específicas"
    )
    
    @field_validator('next_steps')
    @classmethod
    def validate_next_steps_non_empty(cls, v: list[str]) -> list[str]:
        """Valida que next_steps não é lista vazia."""
        if not v or len(v) == 0:
            raise ValueError("next_steps não pode ser lista vazia")
        return v
    
    @model_validator(mode='after')
    def validate_priority_logic(self) -> 'Recommendation':
        """Valida lógica de priorização: HIGH impact + LOW effort = HIGH priority.
        
        Ajusta priority automaticamente se:
        - HIGH impact + LOW effort → priority = HIGH (quick win)
        - LOW impact + HIGH effort → priority = LOW (evitar)
        """
        if self.impact == "HIGH" and self.effort == "LOW":
            if self.priority != "HIGH":
                self.priority = "HIGH"
        elif self.impact == "LOW" and self.effort == "HIGH":
            if self.priority != "LOW":
                self.priority = "LOW"
        return self


class CompleteDiagnostic(BaseModel):
    """Diagnóstico BSC completo multi-perspectiva.
    
    Consolida análise diagnóstica completa das 4 perspectivas do Balanced
    Scorecard, incluindo recomendações priorizadas, synergies cross-perspective
    identificadas e executive summary para tomada de decisão.
    
    Este schema é o resultado final do DiagnosticAgent.run_diagnostic() e
    contém todos os insights necessários para a fase APPROVAL_PENDING.
    
    Attributes:
        financial: Análise da perspectiva Financeira
        customer: Análise da perspectiva Clientes
        process: Análise da perspectiva Processos Internos
        learning: Análise da perspectiva Aprendizado e Crescimento
        recommendations: Lista de 3+ recomendações priorizadas por impacto vs esforço
        cross_perspective_synergies: Lista de synergies cross-perspective identificadas (opcional)
        executive_summary: Resumo executivo completo do diagnóstico (mínimo 100 caracteres)
        next_phase: Próxima fase do workflow (geralmente APPROVAL_PENDING)
    
    Example:
        >>> financial = DiagnosticResult(
        ...     perspective="Financeira",
        ...     current_state="Receita crescente mas margens comprimidas",
        ...     gaps=["Falta visibilidade custos"],
        ...     opportunities=["Implementar ABC Costing"],
        ...     priority="HIGH"
        ... )
        >>> customer = DiagnosticResult(
        ...     perspective="Clientes",
        ...     current_state="NPS bom mas churn alto em clientes SMB",
        ...     gaps=["Falta programa retenção"],
        ...     opportunities=["Customer Success para SMB"],
        ...     priority="HIGH"
        ... )
        >>> process = DiagnosticResult(
        ...     perspective="Processos Internos",
        ...     current_state="Processos manuais geram retrabalho",
        ...     gaps=["Falta automação"],
        ...     opportunities=["RPA para processos repetitivos"],
        ...     priority="MEDIUM"
        ... )
        >>> learning = DiagnosticResult(
        ...     perspective="Aprendizado e Crescimento",
        ...     current_state="Turnover alto time comercial 25%/ano",
        ...     gaps=["Falta treinamento estruturado"],
        ...     opportunities=["Academia comercial interna"],
        ...     priority="MEDIUM"
        ... )
        >>> rec1 = Recommendation(
        ...     title="Implementar ABC Costing",
        ...     description="Sistema custeio baseado em atividades para melhorar visibilidade rentabilidade por produto",
        ...     impact="HIGH",
        ...     effort="MEDIUM",
        ...     priority="HIGH",
        ...     timeframe="6-9 meses",
        ...     next_steps=["Contratar consultor", "Mapear processos"]
        ... )
        >>> complete = CompleteDiagnostic(
        ...     financial=financial,
        ...     customer=customer,
        ...     process=process,
        ...     learning=learning,
        ...     recommendations=[rec1],
        ...     cross_perspective_synergies=["ABC Costing melhora pricing (Financial) e reduz churn SMB (Customer)"],
        ...     executive_summary="Empresa com crescimento forte mas margens comprimidas. Prioridades: (1) Implementar ABC Costing para visibilidade custos, (2) Customer Success SMB para reduzir churn 25→15%, (3) RPA para ganhar eficiência operacional. ROI esperado: +5pp margem em 12 meses.",
        ...     next_phase="APPROVAL_PENDING"
        ... )
    """
    
    financial: DiagnosticResult = Field(
        description="Análise da perspectiva Financeira"
    )
    customer: DiagnosticResult = Field(
        description="Análise da perspectiva Clientes"
    )
    process: DiagnosticResult = Field(
        description="Análise da perspectiva Processos Internos"
    )
    learning: DiagnosticResult = Field(
        description="Análise da perspectiva Aprendizado e Crescimento"
    )
    recommendations: list[Recommendation] = Field(
        min_length=3,
        description="Mínimo 3 recomendações priorizadas"
    )
    cross_perspective_synergies: list[str] = Field(
        default_factory=list,
        description="Synergies cross-perspective identificadas"
    )
    executive_summary: str = Field(
        min_length=100,
        description="Resumo executivo completo do diagnóstico"
    )
    next_phase: str = Field(
        default="APPROVAL_PENDING",
        description="Próxima fase do workflow consultivo"
    )
    
    @model_validator(mode='after')
    def validate_perspectives(self) -> 'CompleteDiagnostic':
        """Valida que as 4 perspectivas BSC estão corretas.
        
        Garante que cada campo (financial, customer, process, learning) contém
        a análise da perspectiva correta.
        
        Raises:
            ValueError: Se perspectivas não correspondem aos campos
        """
        if self.financial.perspective != "Financeira":
            raise ValueError(
                f"Campo 'financial' deve conter perspectiva 'Financeira', "
                f"recebeu '{self.financial.perspective}'"
            )
        if self.customer.perspective != "Clientes":
            raise ValueError(
                f"Campo 'customer' deve conter perspectiva 'Clientes', "
                f"recebeu '{self.customer.perspective}'"
            )
        if self.process.perspective != "Processos Internos":
            raise ValueError(
                f"Campo 'process' deve conter perspectiva 'Processos Internos', "
                f"recebeu '{self.process.perspective}'"
            )
        if self.learning.perspective != "Aprendizado e Crescimento":
            raise ValueError(
                f"Campo 'learning' deve conter perspectiva 'Aprendizado e Crescimento', "
                f"recebeu '{self.learning.perspective}'"
            )
        
        return self