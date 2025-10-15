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

