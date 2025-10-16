"""Schemas Pydantic para ClientProfile e componentes relacionados.

Este módulo define os schemas de dados usados para armazenar
informações de clientes e engajamentos de consultoria BSC no Mem0.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
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
    complete_diagnostic: Optional[Dict[str, Any]] = Field(
        None,
        description="Diagnóstico BSC completo (4 perspectivas + recomendações). CompleteDiagnostic serializado."
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
# DIAGNOSTIC SCHEMAS (análise diagnóstica BSC)
# ============================================================================


class DiagnosticResult(BaseModel):
    """Resultado da análise diagnóstica de uma perspectiva BSC.
    
    Representa a análise detalhada de uma única perspectiva do Balanced Scorecard
    (Financeira, Clientes, Processos, Aprendizado), identificando situação atual,
    gaps, oportunidades e prioridade de ação.
    
    Attributes:
        perspective: Nome da perspectiva BSC analisada
        current_state: Descrição da situação atual na perspectiva
        gaps: Lista de lacunas identificadas comparando atual vs ideal BSC
        opportunities: Lista de oportunidades de melhoria identificadas
        priority: Nível de prioridade desta perspectiva (LOW/MEDIUM/HIGH)
        key_insights: Insights-chave relevantes da literatura BSC
    
    Example:
        >>> result = DiagnosticResult(
        ...     perspective="Financeira",
        ...     current_state="Empresa possui bom EBITDA mas falta visibilidade de custos por projeto",
        ...     gaps=["Ausência de cost accounting detalhado", "KPIs financeiros não conectados a processos"],
        ...     opportunities=["Implementar ABC costing", "Dashboard financeiro integrado"],
        ...     priority="HIGH",
        ...     key_insights=["Kaplan & Norton: 60% empresas falham em conectar finanças a processos"]
        ... )
    """
    
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"] = Field(
        description="Perspectiva BSC analisada"
    )
    current_state: str = Field(
        min_length=20,
        description="Descrição da situação atual na perspectiva"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Lacunas identificadas (atual vs ideal BSC)"
    )
    opportunities: list[str] = Field(
        default_factory=list,
        description="Oportunidades de melhoria identificadas"
    )
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Nível de prioridade desta perspectiva"
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="Insights-chave da literatura BSC"
    )
    
    @field_validator('gaps', 'opportunities', 'key_insights')
    @classmethod
    def validate_list_not_empty_strings(cls, v: list[str]) -> list[str]:
        """Valida que listas não contêm strings vazias."""
        return [item.strip() for item in v if item.strip()]


class Recommendation(BaseModel):
    """Recomendação acionável BSC.
    
    Representa uma recomendação específica e acionável para implementação
    do Balanced Scorecard, priorizada por impacto esperado e esforço necessário.
    
    Attributes:
        title: Título curto da recomendação (SMART)
        description: Descrição detalhada da recomendação
        perspective: Perspectiva BSC principal desta recomendação
        related_perspectives: Outras perspectivas impactadas (cross-perspective)
        expected_impact: Impacto esperado se implementada (LOW/MEDIUM/HIGH)
        effort: Esforço necessário para implementação (LOW/MEDIUM/HIGH)
        priority: Prioridade global considerando impacto vs esforço
        timeframe: Prazo sugerido (quick win: 1-3 meses, médio prazo: 3-6, longo: 6+)
        next_steps: Lista de próximas ações concretas (action items)
    
    Example:
        >>> recommendation = Recommendation(
        ...     title="Implementar Dashboard Financeiro Integrado",
        ...     description="Criar dashboard executivo conectando KPIs financeiros a processos operacionais",
        ...     perspective="Financeira",
        ...     related_perspectives=["Processos Internos"],
        ...     expected_impact="HIGH",
        ...     effort="MEDIUM",
        ...     priority="HIGH",
        ...     timeframe="médio prazo (3-6 meses)",
        ...     next_steps=["Definir 5-7 KPIs financeiros críticos", "Mapear processos que impactam KPIs"]
        ... )
    """
    
    title: str = Field(
        min_length=10,
        max_length=150,
        description="Título curto e acionável da recomendação"
    )
    description: str = Field(
        min_length=50,
        description="Descrição detalhada da recomendação"
    )
    perspective: Literal["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"] = Field(
        description="Perspectiva BSC principal"
    )
    related_perspectives: list[str] = Field(
        default_factory=list,
        description="Outras perspectivas impactadas (synergies cross-perspective)"
    )
    expected_impact: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Impacto esperado se implementada"
    )
    effort: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Esforço necessário para implementação"
    )
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        description="Prioridade global (impacto vs esforço)"
    )
    timeframe: str = Field(
        description="Prazo sugerido (ex: 'quick win (1-3 meses)', 'médio prazo (3-6 meses)')"
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Próximas ações concretas (action items SMART)"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Valida que título não é vazio após trim."""
        v = v.strip()
        if not v:
            raise ValueError("Título não pode ser vazio")
        return v
    
    @model_validator(mode='after')
    def validate_priority_logic(self) -> 'Recommendation':
        """Valida que prioridade alta requer impacto alto ou esforço baixo."""
        if self.priority == "HIGH":
            if self.expected_impact == "LOW" and self.effort == "HIGH":
                raise ValueError(
                    "Prioridade HIGH inconsistente: impacto LOW + esforço HIGH"
                )
        return self


class CompleteDiagnostic(BaseModel):
    """Diagnóstico BSC completo (4 perspectivas + recomendações).
    
    Resultado consolidado da análise diagnóstica BSC multi-perspectiva,
    incluindo análises específicas por perspectiva, synergies cross-perspective,
    e recomendações priorizadas para implementação.
    
    Attributes:
        financial: Análise da perspectiva Financeira
        customer: Análise da perspectiva Clientes
        process: Análise da perspectiva Processos Internos
        learning: Análise da perspectiva Aprendizado e Crescimento
        recommendations: Lista de recomendações priorizadas (ordenadas por priority)
        cross_perspective_synergies: Synergies identificadas entre perspectivas
        executive_summary: Resumo executivo do diagnóstico (200-500 palavras)
        next_phase: Próxima fase sugerida do engajamento (DESIGN, APPROVAL_PENDING)
        generated_at: Data/hora de geração do diagnóstico
    
    Example:
        >>> diagnostic = CompleteDiagnostic(
        ...     financial=DiagnosticResult(perspective="Financeira", ...),
        ...     customer=DiagnosticResult(perspective="Clientes", ...),
        ...     process=DiagnosticResult(perspective="Processos Internos", ...),
        ...     learning=DiagnosticResult(perspective="Aprendizado e Crescimento", ...),
        ...     recommendations=[Recommendation(title="...", ...), ...],
        ...     cross_perspective_synergies=["Processos manuais impactam custos E satisfação cliente"],
        ...     executive_summary="Empresa TechCorp possui forte EBITDA mas...",
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
        default_factory=list,
        description="Recomendações priorizadas (ordenadas por priority: HIGH → LOW)"
    )
    cross_perspective_synergies: list[str] = Field(
        default_factory=list,
        description="Synergies identificadas entre perspectivas"
    )
    executive_summary: str = Field(
        min_length=200,
        max_length=2000,
        description="Resumo executivo do diagnóstico (200-500 palavras ideal)"
    )
    next_phase: Literal["APPROVAL_PENDING", "DESIGN", "IMPLEMENTATION"] = Field(
        default="APPROVAL_PENDING",
        description="Próxima fase sugerida do engajamento"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Data/hora de geração do diagnóstico"
    )
    
    @model_validator(mode='after')
    def validate_perspectives_match(self) -> 'CompleteDiagnostic':
        """Valida que cada DiagnosticResult está na perspectiva correta."""
        if self.financial.perspective != "Financeira":
            raise ValueError(f"financial.perspective deve ser 'Financeira', não '{self.financial.perspective}'")
        if self.customer.perspective != "Clientes":
            raise ValueError(f"customer.perspective deve ser 'Clientes', não '{self.customer.perspective}'")
        if self.process.perspective != "Processos Internos":
            raise ValueError(f"process.perspective deve ser 'Processos Internos', não '{self.process.perspective}'")
        if self.learning.perspective != "Aprendizado e Crescimento":
            raise ValueError(f"learning.perspective deve ser 'Aprendizado e Crescimento', não '{self.learning.perspective}'")
        return self
    
    @model_validator(mode='after')
    def validate_recommendations_count(self) -> 'CompleteDiagnostic':
        """Valida que existem recomendações (mínimo 3)."""
        if len(self.recommendations) < 3:
            raise ValueError(f"Diagnóstico deve ter ao menos 3 recomendações, encontrado {len(self.recommendations)}")
        return self
    
    def get_high_priority_recommendations(self) -> list[Recommendation]:
        """Retorna apenas recomendações de prioridade HIGH.
        
        Returns:
            list[Recommendation]: Recomendações priorizadas como HIGH
        
        Example:
            >>> diagnostic = CompleteDiagnostic(...)
            >>> high_priority = diagnostic.get_high_priority_recommendations()
            >>> len(high_priority)
            5
        """
        return [rec for rec in self.recommendations if rec.priority == "HIGH"]
    
    def to_mem0(self) -> dict:
        """Serializa CompleteDiagnostic para formato Mem0 (JSON/dict).
        
        Returns:
            dict: Dicionário pronto para armazenamento no Mem0
        """
        return self.model_dump(mode='json', exclude_none=True)
    
    @classmethod
    def from_mem0(cls, data: dict) -> 'CompleteDiagnostic':
        """Deserializa CompleteDiagnostic de formato Mem0.
        
        Args:
            data: Dicionário retornado do Mem0
        
        Returns:
            CompleteDiagnostic: Instância validada do schema
        """
        return cls.model_validate(data)
