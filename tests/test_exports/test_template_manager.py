"""Testes unitários para TemplateManager (Jinja2 templates).

Suite: 8 testes
Cobertura: Template loading, rendering, filtros customizados
Fase: 4.2 - Reports & Exports
"""

import pytest
from datetime import datetime
from pathlib import Path
from jinja2 import TemplateNotFound

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
def sample_profile():
    """ClientProfile válido para testes."""
    company = CompanyInfo(
        name="TechCorp Brasil",
        sector="Tecnologia",
        size="média"
    )
    
    context = StrategicContext(
        current_challenges=["Baixa conversão vendas", "Alta rotatividade"],
        strategic_objectives=["Crescer 30% receita", "Reduzir turnover 50%", "Aumentar NPS"]
    )
    
    return ClientProfile(company=company, context=context)


@pytest.fixture
def sample_diagnostic():
    """CompleteDiagnostic válido para testes."""
    financial = DiagnosticResult(
        perspective="Financeira",
        current_state="Receita crescente mas margens comprimidas",
        gaps=["Falta visibilidade custos", "Baixa previsibilidade fluxo caixa"],
        opportunities=["Implementar ABC Costing", "Criar forecasting rolling"],
        priority="HIGH"
    )
    
    customer = DiagnosticResult(
        perspective="Clientes",
        current_state="NPS bom mas churn alto em clientes SMB",
        gaps=["Falta segmentação clientes", "Baixo engagement pós-venda"],
        opportunities=["Criar programa fidelidade", "Implementar Customer Success"],
        priority="MEDIUM"
    )
    
    process = DiagnosticResult(
        perspective="Processos Internos",
        current_state="Processos manuais causando retrabalho",
        gaps=["Falta automação", "Processos não documentados"],
        opportunities=["Implementar RPA", "Mapear processos críticos (BPMN)"],
        priority="HIGH"
    )
    
    learning = DiagnosticResult(
        perspective="Aprendizado e Crescimento",
        current_state="Equipe desmotivada, falta capacitação",
        gaps=["Sem plano treinamento", "Cultura reativa"],
        opportunities=["Criar universidade corporativa", "Implementar OKRs"],
        priority="MEDIUM"
    )
    
    recommendations = [
        Recommendation(
            title="Implementar ABC Costing para visibilidade de custos",
            description="Sistema de custeio baseado em atividades para rastrear custos por produto/cliente e permitir decisões estratégicas data-driven",
            impact="HIGH",
            effort="MEDIUM",
            priority="HIGH",
            timeframe="3-6 meses",
            next_steps=["Contratar consultor ABC", "Mapear processos", "Pilotar em 1 produto"],
            quick_win=False,
            expected_outcomes=["Visibilidade custos +90%", "Margem produto +15%"]
        ),
        Recommendation(
            title="Criar programa Customer Success para reduzir churn",
            description="Equipe dedicada ao sucesso do cliente com playbooks pós-venda estruturados e métricas de health score",
            impact="HIGH",
            effort="LOW",
            priority="HIGH",
            timeframe="1-3 meses",
            next_steps=["Contratar CS Manager", "Criar playbooks", "Treinar equipe"],
            quick_win=True,
            expected_outcomes=["Churn -30%", "NPS +20 pontos"]
        ),
        Recommendation(
            title="Implementar automação RPA para processos manuais",
            description="Robotic Process Automation para eliminar retrabalho e aumentar produtividade operacional em processos repetitivos",
            impact="MEDIUM",
            effort="MEDIUM",
            priority="MEDIUM",
            timeframe="6-9 meses",
            next_steps=["Mapear processos candidatos", "Selecionar ferramenta RPA", "Pilotar em 2 processos"],
            quick_win=False,
            expected_outcomes=["Produtividade +40%", "Retrabalho -60%"]
        )
    ]
    
    return CompleteDiagnostic(
        financial=financial,
        customer=customer,
        process=process,
        learning=learning,
        recommendations=recommendations,
        cross_perspective_synergies=[
            "ABC Costing + Customer Success = ROI por cliente",
            "RPA + Treinamento = Produtividade +40%"
        ],
        executive_summary=(
            "TechCorp Brasil apresenta sólido crescimento de receita mas margens comprimidas devido à "
            "falta de visibilidade de custos. Processos manuais causam retrabalho e impactam produtividade. "
            "Churn alto em clientes SMB exige programa de Customer Success estruturado."
        ),
        next_phase="APPROVAL_PENDING"
    )


# ============================================================================
# TESTES INICIALIZAÇÃO
# ============================================================================

def test_template_manager_loads_templates(template_manager):
    """TemplateManager deve carregar templates do diretório."""
    templates = template_manager.list_templates()
    
    assert "base.html" in templates
    assert "diagnostic_full.html" in templates
    assert "diagnostic_perspective.html" in templates


def test_template_manager_invalid_directory_raises_error():
    """TemplateManager deve lançar erro se diretório não existe."""
    with pytest.raises(FileNotFoundError, match="Template directory não encontrado"):
        TemplateManager(template_dir="invalid/path")


# ============================================================================
# TESTES RENDERING
# ============================================================================

def test_render_full_diagnostic_returns_html(template_manager, sample_diagnostic, sample_profile):
    """render_full_diagnostic deve retornar HTML válido."""
    html = template_manager.render_full_diagnostic(sample_diagnostic, sample_profile)
    
    assert isinstance(html, str)
    assert len(html) > 1000  # HTML substancial
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_rendered_html_contains_company_name(template_manager, sample_diagnostic, sample_profile):
    """HTML renderizado deve conter nome da empresa."""
    html = template_manager.render_full_diagnostic(sample_diagnostic, sample_profile)
    
    assert "TechCorp Brasil" in html


def test_rendered_html_contains_executive_summary(template_manager, sample_diagnostic, sample_profile):
    """HTML renderizado deve conter executive summary."""
    html = template_manager.render_full_diagnostic(sample_diagnostic, sample_profile)
    
    assert sample_diagnostic.executive_summary in html
    assert "Executive Summary" in html


def test_render_perspective_financial(template_manager, sample_diagnostic, sample_profile):
    """render_perspective deve renderizar perspectiva Financeira."""
    html = template_manager.render_perspective(
        sample_diagnostic, sample_profile, perspective="Financeira"
    )
    
    assert "Financeira" in html
    assert "Receita crescente mas margens comprimidas" in html
    assert "ABC Costing" in html  # Opportunity


def test_render_perspective_invalid_raises_error(template_manager, sample_diagnostic, sample_profile):
    """render_perspective deve lançar erro se perspectiva inválida."""
    with pytest.raises(ValueError, match="Perspectiva inválida"):
        template_manager.render_perspective(
            sample_diagnostic, sample_profile, perspective="Invalid"
        )


# ============================================================================
# TESTES FILTROS CUSTOMIZADOS
# ============================================================================

def test_format_date_filter_brazilian_format(template_manager):
    """Filtro format_date deve formatar datas no padrão brasileiro."""
    dt = datetime(2025, 11, 18, 14, 30)
    formatted = template_manager._format_date(dt)
    
    assert formatted == "18/11/2025"


def test_format_datetime_filter_brazilian_format(template_manager):
    """Filtro format_datetime deve incluir hora."""
    dt = datetime(2025, 11, 18, 14, 30)
    formatted = template_manager._format_datetime(dt)
    
    assert formatted == "18/11/2025 14:30"


def test_format_number_filter_brazilian_format(template_manager):
    """Filtro format_number deve usar separadores brasileiros."""
    formatted = template_manager._format_number(1234.56)
    
    assert formatted == "1.234,56"


def test_priority_badge_class_mapping(template_manager):
    """Filtro priority_badge deve mapear priority para CSS class."""
    assert template_manager._priority_badge_class("HIGH") == "badge-high"
    assert template_manager._priority_badge_class("MEDIUM") == "badge-medium"
    assert template_manager._priority_badge_class("LOW") == "badge-low"
    assert template_manager._priority_badge_class("INVALID") == "badge-medium"  # Default


# ============================================================================
# TESTES EDGE CASES
# ============================================================================

def test_template_not_found_raises_error(template_manager):
    """get_template deve lançar erro se template não existe."""
    with pytest.raises(TemplateNotFound):
        template_manager.get_template("nonexistent.html")


def test_html_length_reasonable(template_manager, sample_diagnostic, sample_profile):
    """HTML renderizado não deve ser excessivamente grande."""
    html = template_manager.render_full_diagnostic(sample_diagnostic, sample_profile)
    
    # HTML deve ser < 100KB (razoável para diagnóstico completo)
    assert len(html) < 100_000
    # Mas deve ter conteúdo substancial (> 5KB mínimo)
    assert len(html) > 5_000

