"""Testes unitários para PdfExporter (WeasyPrint).

Suite: 10 testes
Cobertura: PDF generation, file creation, validation
Fase: 4.2 - Reports & Exports
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.exports.pdf_exporter import PdfExporter
from src.exports.template_manager import TemplateManager
from src.memory.schemas import (
    CompanyInfo,
    StrategicContext,
    ClientProfile,
    DiagnosticResult,
    Recommendation,
    CompleteDiagnostic,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def template_manager():
    """TemplateManager configurado."""
    return TemplateManager()


@pytest.fixture
def pdf_exporter(template_manager, tmp_path):
    """PdfExporter configurado com diretório temporário."""
    return PdfExporter(template_manager, output_dir=str(tmp_path / "pdf"))


@pytest.fixture
def sample_profile():
    """ClientProfile válido para testes."""
    company = CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média"
    )
    
    context = StrategicContext(
        challenges=["Baixa conversão vendas", "Alta rotatividade"],
        objectives=["Crescer 30% receita", "Reduzir turnover 50%", "Aumentar NPS"]
    )
    
    return ClientProfile(company=company, context=context)


@pytest.fixture
def complete_diagnostic():
    """CompleteDiagnostic válido completo."""
    financial = DiagnosticResult(
        perspective="Financeira",
        current_state="Receita crescente mas margens comprimidas",
        gaps=["Falta visibilidade custos", "Baixa previsibilidade fluxo caixa"],
        opportunities=["Implementar ABC Costing", "Criar forecasting rolling"],
        priority="HIGH"
    )
    
    customer = DiagnosticResult(
        perspective="Clientes",
        current_state="NPS bom mas churn alto",
        gaps=["Falta segmentação", "Baixo engagement"],
        opportunities=["Programa fidelidade", "Customer Success"],
        priority="MEDIUM"
    )
    
    process = DiagnosticResult(
        perspective="Processos Internos",
        current_state="Processos manuais",
        gaps=["Falta automação"],
        opportunities=["RPA"],
        priority="HIGH"
    )
    
    learning = DiagnosticResult(
        perspective="Aprendizado e Crescimento",
        current_state="Equipe desmotivada",
        gaps=["Sem treinamento"],
        opportunities=["Universidade corporativa"],
        priority="MEDIUM"
    )
    
    recommendations = [
        Recommendation(
            title="Implementar ABC Costing",
            description="Sistema de custeio baseado em atividades",
            impact="HIGH",
            effort="MEDIUM",
            priority="HIGH",
            timeframe="3-6 meses",
            next_steps=["Contratar consultor", "Mapear processos"],
            quick_win=False
        )
    ]
    
    return CompleteDiagnostic(
        financial=financial,
        customer=customer,
        process=process,
        learning=learning,
        recommendations=recommendations,
        cross_perspective_synergies=["ABC + CS = ROI cliente"],
        executive_summary="TechCorp apresenta crescimento mas margens comprimidas.",
        next_phase="APPROVAL_PENDING"
    )


# ============================================================================
# TESTES EXPORT COMPLETO
# ============================================================================

def test_export_full_diagnostic_success(pdf_exporter, complete_diagnostic, sample_profile):
    """export_full_diagnostic deve criar PDF sem erros."""
    pdf_path = pdf_exporter.export_full_diagnostic(complete_diagnostic, sample_profile)
    
    assert pdf_path is not None
    assert isinstance(pdf_path, Path)


def test_export_full_diagnostic_generates_pdf_file(pdf_exporter, complete_diagnostic, sample_profile):
    """PDF gerado deve existir no filesystem."""
    pdf_path = pdf_exporter.export_full_diagnostic(complete_diagnostic, sample_profile)
    
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"


def test_export_full_diagnostic_uses_custom_output_path(pdf_exporter, complete_diagnostic, sample_profile, tmp_path):
    """export_full_diagnostic deve respeitar output_path customizado."""
    custom_path = tmp_path / "custom_report.pdf"
    
    pdf_path = pdf_exporter.export_full_diagnostic(
        complete_diagnostic, sample_profile, output_path=custom_path
    )
    
    assert pdf_path == custom_path
    assert pdf_path.exists()


def test_pdf_file_size_reasonable(pdf_exporter, complete_diagnostic, sample_profile):
    """PDF gerado deve ter tamanho razoável (não vazio, não > 1MB)."""
    pdf_path = pdf_exporter.export_full_diagnostic(complete_diagnostic, sample_profile)
    
    file_size = pdf_path.stat().st_size
    
    # PDF deve ter conteúdo (> 10KB mínimo)
    assert file_size > 10_000
    # Mas não deve ser excessivamente grande (< 1MB)
    assert file_size < 1_000_000


# ============================================================================
# TESTES EXPORT PERSPECTIVA
# ============================================================================

def test_export_perspective_financial(pdf_exporter, complete_diagnostic, sample_profile):
    """export_perspective deve gerar PDF da perspectiva Financeira."""
    pdf_path = pdf_exporter.export_perspective(
        complete_diagnostic, sample_profile, perspective="Financeira"
    )
    
    assert pdf_path.exists()
    assert "financeira" in pdf_path.name.lower()


def test_export_perspective_customer(pdf_exporter, complete_diagnostic, sample_profile):
    """export_perspective deve gerar PDF da perspectiva Clientes."""
    pdf_path = pdf_exporter.export_perspective(
        complete_diagnostic, sample_profile, perspective="Clientes"
    )
    
    assert pdf_path.exists()
    assert "clientes" in pdf_path.name.lower()


def test_export_invalid_perspective_raises_error(pdf_exporter, complete_diagnostic, sample_profile):
    """export_perspective deve lançar erro se perspectiva inválida."""
    with pytest.raises(ValueError, match="Perspectiva inválida"):
        pdf_exporter.export_perspective(
            complete_diagnostic, sample_profile, perspective="Invalid"
        )


# ============================================================================
# TESTES VALIDAÇÃO
# ============================================================================

def test_export_incomplete_diagnostic_raises_error(pdf_exporter, sample_profile):
    """export_full_diagnostic deve validar diagnostic completo."""
    # Diagnostic sem customer perspective
    incomplete = CompleteDiagnostic(
        financial=DiagnosticResult(
            perspective="Financeira",
            current_state="Test",
            gaps=[],
            opportunities=[],
            priority="HIGH"
        ),
        customer=None,  # Missing!
        process=DiagnosticResult(
            perspective="Processos Internos",
            current_state="Test",
            gaps=[],
            opportunities=[],
            priority="HIGH"
        ),
        learning=DiagnosticResult(
            perspective="Aprendizado e Crescimento",
            current_state="Test",
            gaps=[],
            opportunities=[],
            priority="HIGH"
        ),
        recommendations=[],
        cross_perspective_synergies=[],
        executive_summary="Test",
        next_phase="APPROVAL_PENDING"
    )
    
    with pytest.raises(ValueError, match="Diagnóstico incompleto"):
        pdf_exporter.export_full_diagnostic(incomplete, sample_profile)


# ============================================================================
# TESTES HELPERS
# ============================================================================

def test_slugify_converts_to_valid_filename(pdf_exporter):
    """_slugify deve converter texto para filename válido."""
    assert pdf_exporter._slugify("TechCorp Brasil") == "techcorp_brasil"
    assert pdf_exporter._slugify("Processos Internos") == "processos_internos"
    assert pdf_exporter._slugify("Café & Companhia") == "cafe_companhia"

