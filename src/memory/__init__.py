"""Módulo de memória persistente para BSC Consulting Agent.

Este módulo fornece schemas Pydantic para armazenar perfis de clientes
e contexto de engajamento consultoria no Mem0.

Schemas disponíveis:
    - ClientProfile: Schema principal agregador
    - CompanyInfo: Informações básicas da empresa
    - StrategicContext: Contexto estratégico organizacional
    - EngagementState: Estado do engajamento consultoria
    - DiagnosticData: Dados de diagnóstico (SWOT, pain points)
    - SWOTAnalysis: Análise SWOT estruturada

Example:
    >>> from src.memory import ClientProfile, CompanyInfo
    >>> 
    >>> company = CompanyInfo(
    ...     name="TechCorp Brasil",
    ...     sector="Tecnologia",
    ...     size="média"
    ... )
    >>> profile = ClientProfile(company=company)
    >>> 
    >>> # Serializar para Mem0
    >>> mem0_data = profile.to_mem0()
"""

from .schemas import (
    ClientProfile,
    CompanyInfo,
    DiagnosticData,
    EngagementState,
    StrategicContext,
    SWOTAnalysis,
)

__all__ = [
    "ClientProfile",
    "CompanyInfo",
    "StrategicContext",
    "EngagementState",
    "DiagnosticData",
    "SWOTAnalysis",
]

