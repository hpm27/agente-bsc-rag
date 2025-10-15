"""Testes unitários para schemas de memória (ClientProfile e componentes).

Testa criação válida, validações, serialização Mem0 e edge cases.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.memory.schemas import (
    ClientProfile,
    CompanyInfo,
    DiagnosticData,
    EngagementState,
    StrategicContext,
    SWOTAnalysis,
)


# ============================================================================
# TESTES DE CRIAÇÃO VÁLIDA (Happy Path)
# ============================================================================


def test_swot_analysis_creation():
    """Testa criação de SWOTAnalysis válida."""
    swot = SWOTAnalysis(
        strengths=["Equipe qualificada", "Marca forte"],
        weaknesses=["Processos manuais"],
        opportunities=["Expansão digital"],
        threats=["Concorrência intensa"]
    )
    
    assert len(swot.strengths) == 2
    assert len(swot.weaknesses) == 1
    assert "Equipe qualificada" in swot.strengths


def test_swot_analysis_empty():
    """Testa criação de SWOTAnalysis vazio (válido)."""
    swot = SWOTAnalysis()
    
    assert swot.strengths == []
    assert swot.weaknesses == []
    assert swot.opportunities == []
    assert swot.threats == []


def test_company_info_valid_creation():
    """Testa criação de CompanyInfo válida."""
    company = CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média",
        industry="Software as a Service",
        founded_year=2015
    )
    
    assert company.name == "TechCorp Brasil"
    assert company.sector == "Tecnologia"
    assert company.size == "média"
    assert company.founded_year == 2015


def test_company_info_minimal():
    """Testa CompanyInfo com campos mínimos obrigatórios."""
    company = CompanyInfo(
        name="Empresa Teste",
        sector="Serviços"
    )
    
    assert company.name == "Empresa Teste"
    assert company.size == "média"  # Default
    assert company.industry is None
    assert company.founded_year is None


def test_strategic_context_creation():
    """Testa criação de StrategicContext válido."""
    context = StrategicContext(
        mission="Transformar a indústria",
        vision="Ser líder global até 2030",
        core_values=["Inovação", "Integridade"],
        strategic_objectives=["Crescer 30%", "Expandir mercados"],
        current_challenges=["Alta rotatividade"]
    )
    
    assert context.mission == "Transformar a indústria"
    assert len(context.core_values) == 2
    assert len(context.strategic_objectives) == 2


def test_strategic_context_empty():
    """Testa StrategicContext vazio (válido)."""
    context = StrategicContext()
    
    assert context.mission is None
    assert context.vision is None
    assert context.core_values == []


def test_diagnostic_data_creation():
    """Testa criação de DiagnosticData válido."""
    swot = SWOTAnalysis(strengths=["Forte marca"])
    diagnostic = DiagnosticData(
        swot=swot,
        pain_points=["Falta de visibilidade de métricas"],
        opportunities=["Automação de processos"],
        key_findings=["BSC pode reduzir tempo de reporting"]
    )
    
    assert diagnostic.swot is not None
    assert len(diagnostic.pain_points) == 1
    assert "Automação de processos" in diagnostic.opportunities


def test_engagement_state_creation():
    """Testa criação de EngagementState válido."""
    engagement = EngagementState(
        current_phase="DISCOVERY",
        progress_percentage=35,
        completed_milestones=["Onboarding realizado", "SWOT completado"]
    )
    
    assert engagement.current_phase == "DISCOVERY"
    assert engagement.progress_percentage == 35
    assert len(engagement.completed_milestones) == 2
    assert isinstance(engagement.started_at, datetime)


def test_engagement_state_defaults():
    """Testa defaults de EngagementState."""
    engagement = EngagementState()
    
    assert engagement.current_phase == "ONBOARDING"
    assert engagement.progress_percentage == 0
    assert engagement.completed_milestones == []
    assert engagement.started_at is not None


def test_client_profile_valid_creation():
    """Testa criação de ClientProfile completo válido."""
    company = CompanyInfo(name="TechCorp", sector="Tecnologia")
    profile = ClientProfile(company=company)
    
    assert profile.client_id is not None
    assert len(profile.client_id) > 0
    assert profile.company.name == "TechCorp"
    assert profile.engagement.current_phase == "ONBOARDING"
    assert isinstance(profile.created_at, datetime)


# ============================================================================
# TESTES DE VALIDAÇÃO (Dados Inválidos)
# ============================================================================


def test_company_info_empty_name():
    """Testa que nome vazio gera erro de validação."""
    with pytest.raises(ValidationError) as exc_info:
        CompanyInfo(name="   ", sector="Tecnologia")
    
    assert "Nome da empresa não pode ser vazio" in str(exc_info.value)


def test_company_info_name_too_short():
    """Testa que nome com < 2 caracteres gera erro."""
    with pytest.raises(ValidationError):
        CompanyInfo(name="A", sector="Tecnologia")


def test_company_info_invalid_size():
    """Testa que tamanho inválido gera erro."""
    with pytest.raises(ValidationError):
        CompanyInfo(name="Empresa", sector="Tecnologia", size="gigante")


def test_company_info_invalid_founded_year():
    """Testa que ano de fundação inválido gera erro."""
    with pytest.raises(ValidationError):
        CompanyInfo(
            name="Empresa",
            sector="Tecnologia",
            founded_year=1500  # Antes de 1800
        )
    
    with pytest.raises(ValidationError):
        CompanyInfo(
            name="Empresa",
            sector="Tecnologia",
            founded_year=2030  # Futuro
        )


def test_engagement_state_invalid_progress_negative():
    """Testa que progress_percentage negativo gera erro."""
    with pytest.raises(ValidationError):
        EngagementState(progress_percentage=-10)


def test_engagement_state_invalid_progress_over_100():
    """Testa que progress_percentage > 100 gera erro."""
    with pytest.raises(ValidationError):
        EngagementState(progress_percentage=150)


def test_engagement_state_invalid_phase():
    """Testa que fase inválida gera erro."""
    with pytest.raises(ValidationError):
        EngagementState(current_phase="INVALID_PHASE")


# ============================================================================
# TESTES DE SERIALIZAÇÃO (Mem0 Integration)
# ============================================================================


def test_client_profile_to_mem0():
    """Testa serialização ClientProfile para dict Mem0."""
    company = CompanyInfo(name="Test Corp", sector="Tech")
    profile = ClientProfile(company=company)
    
    mem0_data = profile.to_mem0()
    
    assert isinstance(mem0_data, dict)
    assert "client_id" in mem0_data
    assert "company" in mem0_data
    assert mem0_data["company"]["name"] == "Test Corp"
    assert "engagement" in mem0_data


def test_client_profile_from_mem0():
    """Testa deserialização ClientProfile de dict Mem0."""
    company = CompanyInfo(name="Test Corp", sector="Tech")
    profile = ClientProfile(company=company)
    
    # Serializar e deserializar (round-trip)
    mem0_data = profile.to_mem0()
    restored = ClientProfile.from_mem0(mem0_data)
    
    assert restored.client_id == profile.client_id
    assert restored.company.name == profile.company.name
    assert restored.engagement.current_phase == profile.engagement.current_phase


def test_client_profile_round_trip_complex():
    """Testa round-trip completo com dados complexos."""
    swot = SWOTAnalysis(
        strengths=["Forte equipe"],
        weaknesses=["Processos manuais"]
    )
    diagnostic = DiagnosticData(
        swot=swot,
        pain_points=["Falta de métricas"],
        key_findings=["BSC necessário"]
    )
    company = CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média",
        founded_year=2015
    )
    context = StrategicContext(
        mission="Inovar sempre",
        core_values=["Inovação", "Excelência"]
    )
    engagement = EngagementState(
        current_phase="DISCOVERY",
        progress_percentage=50
    )
    
    profile = ClientProfile(
        company=company,
        context=context,
        engagement=engagement,
        diagnostics=diagnostic,
        metadata={"custom_field": "test_value"}
    )
    
    # Round-trip
    mem0_data = profile.to_mem0()
    restored = ClientProfile.from_mem0(mem0_data)
    
    # Validar todos os campos
    assert restored.company.name == "TechCorp Brasil"
    assert restored.context.mission == "Inovar sempre"
    assert restored.engagement.current_phase == "DISCOVERY"
    assert restored.diagnostics.swot.strengths == ["Forte equipe"]
    assert restored.metadata["custom_field"] == "test_value"


# ============================================================================
# TESTES DE EDGE CASES
# ============================================================================


def test_client_profile_without_diagnostics():
    """Testa ClientProfile sem diagnóstico (válido em ONBOARDING)."""
    company = CompanyInfo(name="Test", sector="Tech")
    profile = ClientProfile(company=company)
    
    assert profile.diagnostics is None


def test_company_name_with_whitespace():
    """Testa que nome com whitespace é trimmed."""
    company = CompanyInfo(name="  TechCorp  ", sector="Tecnologia")
    
    assert company.name == "TechCorp"


def test_engagement_state_progress_boundaries():
    """Testa valores limites de progress_percentage."""
    engagement_0 = EngagementState(progress_percentage=0)
    engagement_100 = EngagementState(progress_percentage=100)
    
    assert engagement_0.progress_percentage == 0
    assert engagement_100.progress_percentage == 100


def test_client_profile_metadata_custom():
    """Testa adição de metadados customizados."""
    company = CompanyInfo(name="Test", sector="Tech")
    profile = ClientProfile(
        company=company,
        metadata={
            "custom_field_1": "value1",
            "custom_field_2": 123,
            "nested": {"key": "value"}
        }
    )
    
    assert profile.metadata["custom_field_1"] == "value1"
    assert profile.metadata["custom_field_2"] == 123
    assert profile.metadata["nested"]["key"] == "value"


# ============================================================================
# TESTE DE INTEGRAÇÃO (Workflow Completo)
# ============================================================================


def test_client_profile_complete_workflow():
    """Testa workflow completo: ONBOARDING → DISCOVERY → DESIGN."""
    # ONBOARDING
    company = CompanyInfo(name="Inovadora Ltda", sector="Serviços", size="pequena")
    profile = ClientProfile(company=company)
    
    assert profile.engagement.current_phase == "ONBOARDING"
    assert profile.diagnostics is None
    
    # DISCOVERY - Adicionar diagnóstico
    swot = SWOTAnalysis(
        strengths=["Equipe comprometida"],
        weaknesses=["Falta de processos"],
        opportunities=["Mercado em crescimento"],
        threats=["Concorrência acirrada"]
    )
    profile.diagnostics = DiagnosticData(
        swot=swot,
        pain_points=["Visibilidade estratégica baixa"],
        key_findings=["BSC pode estruturar gestão estratégica"]
    )
    profile.engagement.current_phase = "DISCOVERY"
    profile.engagement.progress_percentage = 40
    profile.engagement.completed_milestones.append("Diagnóstico SWOT realizado")
    
    # Validar
    assert profile.diagnostics.swot is not None
    assert len(profile.diagnostics.swot.strengths) == 1
    assert profile.engagement.progress_percentage == 40
    
    # Serializar para Mem0
    mem0_data = profile.to_mem0()
    assert mem0_data["engagement"]["current_phase"] == "DISCOVERY"
    assert mem0_data["diagnostics"]["swot"]["strengths"] == ["Equipe comprometida"]
    
    # Deserializar
    restored = ClientProfile.from_mem0(mem0_data)
    assert restored.engagement.current_phase == "DISCOVERY"
    assert restored.diagnostics.key_findings[0] == "BSC pode estruturar gestão estratégica"

