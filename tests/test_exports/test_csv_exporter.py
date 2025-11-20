"""Testes unitários para CsvExporter (pandas).

Suite: 8 testes
Cobertura: CSV generation, DataFrame, validation
Fase: 4.2 - Reports & Exports
"""

import pandas as pd
import pytest

from src.exports.csv_exporter import CsvExporter
from src.memory.schemas import (
    ClientProfile,
    CompanyInfo,
    CompleteDiagnostic,
    DiagnosticResult,
    Recommendation,
    StrategicContext,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def csv_exporter(tmp_path):
    """CsvExporter configurado com diretório temporário."""
    return CsvExporter(output_dir=str(tmp_path / "csv"))


@pytest.fixture
def sample_profiles():
    """Lista de ClientProfile para testes."""
    profiles = []

    for i in range(3):
        company = CompanyInfo(name=f"Company{i+1}", sector=f"Sector{i+1}", size="média")

        context = StrategicContext(
            current_challenges=[f"Challenge{i+1}A", f"Challenge{i+1}B"],
            strategic_objectives=[f"Obj{i+1}A", f"Obj{i+1}B", f"Obj{i+1}C"],
        )

        profile = ClientProfile(company=company, context=context)

        # Configurar engagement e metadata
        profile.engagement.current_phase = "DISCOVERY"
        profile.metadata["approval_status"] = (
            "PENDING"  # approval_status está em metadata, não engagement
        )
        profiles.append(profile)

    return profiles


@pytest.fixture
def sample_diagnostic_with_recs():
    """CompleteDiagnostic com recomendações para testes."""
    financial = DiagnosticResult(
        perspective="Financeira",
        current_state="Test",
        gaps=["Gap1"],
        opportunities=["Opp1"],
        priority="HIGH",
    )

    recommendations = [
        Recommendation(
            title="Rec 1 HIGH - Implementar sistema XYZ para melhorar visibilidade",
            description="Description detalhada da primeira recomendação com mínimo de 50 caracteres necessários para validação",
            impact="HIGH",
            effort="LOW",
            priority="HIGH",
            timeframe="1-3 meses",
            next_steps=["Step 1", "Step 2"],
            quick_win=True,
            expected_outcomes=["Outcome 1A", "Outcome 1B"],
        ),
        Recommendation(
            title="Rec 2 MEDIUM - Criar programa de capacitação avançada",
            description="Description detalhada da segunda recomendação também com pelo menos 50 caracteres obrigatórios",
            impact="MEDIUM",
            effort="MEDIUM",
            priority="MEDIUM",
            timeframe="3-6 meses",
            next_steps=["Step A"],
            quick_win=False,
        ),
        Recommendation(
            title="Rec 3 LOW - Otimizar processos internos de comunicação",
            description="Description detalhada da terceira recomendação necessária para completar o mínimo de 3 items",
            impact="LOW",
            effort="LOW",
            priority="LOW",
            timeframe="6-12 meses",
            next_steps=["Step X", "Step Y"],
            quick_win=False,
        ),
    ]

    return CompleteDiagnostic(
        financial=financial,
        customer=financial,  # Reuse para simplificar
        process=financial,
        learning=financial,
        recommendations=recommendations,
        cross_perspective_synergies=[],
        executive_summary="Test summary",
        next_phase="APPROVAL_PENDING",
    )


# ============================================================================
# TESTES EXPORT CLIENTS LIST
# ============================================================================


def test_export_clients_list_success(csv_exporter, sample_profiles):
    """export_clients_list deve criar CSV sem erros."""
    csv_path = csv_exporter.export_clients_list(sample_profiles)

    assert csv_path is not None
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"


def test_export_clients_list_has_correct_columns(csv_exporter, sample_profiles):
    """CSV deve ter colunas esperadas."""
    csv_path = csv_exporter.export_clients_list(sample_profiles)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    expected_columns = [
        "client_id",
        "company_name",
        "sector",
        "size",
        "current_phase",
        "approval_status",
        "created_at",
        "updated_at",
        "total_challenges",
        "total_objectives",
    ]

    for col in expected_columns:
        assert col in df.columns


def test_export_clients_list_row_count(csv_exporter, sample_profiles):
    """CSV deve ter número correto de linhas."""
    csv_path = csv_exporter.export_clients_list(sample_profiles)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    assert len(df) == len(sample_profiles)


def test_export_clients_list_encoding_utf8(csv_exporter, sample_profiles):
    """CSV deve ser legível com encoding UTF-8."""
    csv_path = csv_exporter.export_clients_list(sample_profiles)

    # Tentar ler com pandas
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    assert len(df) > 0
    assert df["company_name"].iloc[0] == "Company1"


def test_empty_profiles_list_raises_error(csv_exporter):
    """export_clients_list deve lançar erro se lista vazia."""
    with pytest.raises(ValueError, match="Lista de profiles vazia"):
        csv_exporter.export_clients_list([])


# ============================================================================
# TESTES EXPORT RECOMMENDATIONS
# ============================================================================


def test_export_recommendations_success(csv_exporter, sample_diagnostic_with_recs, sample_profiles):
    """export_recommendations deve criar CSV."""
    csv_path = csv_exporter.export_recommendations(sample_diagnostic_with_recs, sample_profiles[0])

    assert csv_path.exists()
    assert "recommendations" in csv_path.name.lower()


def test_export_recommendations_priority_high_first(
    csv_exporter, sample_diagnostic_with_recs, sample_profiles
):
    """CSV deve ordenar recomendações por priority (HIGH primeiro)."""
    csv_path = csv_exporter.export_recommendations(sample_diagnostic_with_recs, sample_profiles[0])

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Primeira linha deve ser HIGH
    assert df["priority"].iloc[0] == "HIGH"
    # Segunda linha deve ser MEDIUM
    assert df["priority"].iloc[1] == "MEDIUM"


def test_csv_parseable_by_pandas(csv_exporter, sample_profiles):
    """CSV exportado deve ser parseável por pandas novamente."""
    csv_path = csv_exporter.export_clients_list(sample_profiles)

    # Ler CSV de volta
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "company_name" in df.columns
