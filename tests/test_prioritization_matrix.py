"""Testes para Prioritization Matrix Tool.

Test Strategy:
- Fixtures válidas com margem +20% (PONTO 15.4)
- Alinhamento score <-> priority_level (validator crítico)
- Ranks únicos e sequenciais (validator crítico)
- 15+ testes unitários (FASE 3.12 requirement)

Created: 2025-10-27 (FASE 3.12)
"""

import pytest
from pydantic import ValidationError

from src.memory.schemas import PrioritizationCriteria, PrioritizationMatrix, PrioritizedItem
from src.prompts.prioritization_prompts import (
    build_items_context,
    format_prioritization_matrix_for_display,
)

# ============================================================================
# FIXTURES - PRIORITIZATION CRITERIA
# ============================================================================


@pytest.fixture
def valid_criteria_high_impact():
    """Fixture PrioritizationCriteria válida - alto impacto, baixo esforço (margem +20%)."""
    return PrioritizationCriteria(
        strategic_impact=85.0,  # Alto impacto
        implementation_effort=30.0,  # Baixo esforço (invertido = 70)
        urgency=70.0,  # Média-alta urgência
        strategic_alignment=90.0,  # Alinhamento alto
    )


@pytest.fixture
def valid_criteria_medium_impact():
    """Fixture PrioritizationCriteria válida - impacto médio."""
    return PrioritizationCriteria(
        strategic_impact=60.0,  # Médio impacto
        implementation_effort=50.0,  # Médio esforço (invertido = 50)
        urgency=55.0,  # Média urgência
        strategic_alignment=65.0,  # Alinhamento médio
    )


@pytest.fixture
def valid_criteria_low_impact():
    """Fixture PrioritizationCriteria válida - baixo impacto, alto esforço."""
    return PrioritizationCriteria(
        strategic_impact=30.0,  # Baixo impacto
        implementation_effort=80.0,  # Alto esforço (invertido = 20)
        urgency=20.0,  # Baixa urgência
        strategic_alignment=25.0,  # Alinhamento baixo
    )


# ============================================================================
# FIXTURES - PRIORITIZED ITEM
# ============================================================================


@pytest.fixture
def valid_prioritized_item_high(valid_criteria_high_impact):
    """Fixture PrioritizedItem válida - HIGH priority (score 50-74).

    CRÍTICO: priority_level='HIGH' DEVE alinhar com final_score no range 50-74.
    """
    return PrioritizedItem(
        item_id="obj_001",
        item_type="strategic_objective",
        title="Aumentar NPS em 20 pontos",  # 28 chars (min=10, margem +180%)
        description="Melhorar experiência do cliente através de pesquisas trimestrais",  # 72 chars (min=20, margem +260%)
        perspective="Clientes",
        criteria=valid_criteria_high_impact,
        final_score=72.0,  # HIGH range (50-74)
        priority_level="HIGH",  # ALINHADO com score 72.0
        rank=1,
    )


@pytest.fixture
def valid_prioritized_item_critical(valid_criteria_high_impact):
    """Fixture PrioritizedItem válida - CRITICAL priority (score 75-100)."""
    return PrioritizedItem(
        item_id="obj_002",
        item_type="strategic_objective",
        title="Reduzir custos operacionais 15%",  # 34 chars
        description="Otimizar processos e eliminar desperdícios para melhorar margem",  # 66 chars
        perspective="Financeira",
        criteria=valid_criteria_high_impact,
        final_score=85.0,  # CRITICAL range (75-100)
        priority_level="CRITICAL",  # ALINHADO com score 85.0
        rank=1,
    )


@pytest.fixture
def valid_prioritized_item_medium(valid_criteria_medium_impact):
    """Fixture PrioritizedItem válida - MEDIUM priority (score 25-49)."""
    return PrioritizedItem(
        item_id="obj_003",
        item_type="action_item",
        title="Padronizar templates internos",  # 30 chars
        description="Criar templates padronizados para documentos internos da empresa",  # 67 chars
        perspective="Processos Internos",
        criteria=valid_criteria_medium_impact,
        final_score=40.0,  # MEDIUM range (25-49)
        priority_level="MEDIUM",  # ALINHADO com score 40.0
        rank=2,
    )


@pytest.fixture
def valid_prioritized_item_low(valid_criteria_low_impact):
    """Fixture PrioritizedItem válida - LOW priority (score 0-24)."""
    return PrioritizedItem(
        item_id="obj_004",
        item_type="project",
        title="Projeto exploratorio inovacao disruptiva",  # 42 chars
        description="Explorar novas tecnologias emergentes sem ROI definido ou prazo claro",  # 74 chars
        perspective="Aprendizado e Crescimento",
        criteria=valid_criteria_low_impact,
        final_score=15.0,  # LOW range (0-24)
        priority_level="LOW",  # ALINHADO com score 15.0
        rank=3,
    )


# ============================================================================
# FIXTURES - PRIORITIZATION MATRIX
# ============================================================================


@pytest.fixture
def valid_prioritization_matrix(
    valid_prioritized_item_high, valid_prioritized_item_medium, valid_prioritized_item_low
):
    """Fixture PrioritizationMatrix válida com 3 items (ranks únicos e sequenciais 1, 2, 3).

    CRÍTICO: Ranks DEVEM ser únicos e sequenciais (1, 2, 3).
    """
    # Ajustar ranks para serem sequenciais
    valid_prioritized_item_high.rank = 1
    valid_prioritized_item_medium.rank = 2
    valid_prioritized_item_low.rank = 3

    return PrioritizationMatrix(
        items=[
            valid_prioritized_item_high,
            valid_prioritized_item_medium,
            valid_prioritized_item_low,
        ],
        prioritization_context="Priorização objetivos estratégicos Q1 2025 - TechCorp Software",  # 71 chars (min=20, margem +255%)
        weights_config={
            "impact_weight": 0.40,
            "effort_weight": 0.30,
            "urgency_weight": 0.15,
            "alignment_weight": 0.15,
        },
    )


# ============================================================================
# TESTES - PRIORITIZATION CRITERIA
# ============================================================================


def test_prioritization_criteria_valid(valid_criteria_high_impact):
    """Teste 1: PrioritizationCriteria válida aceita valores 0-100."""
    assert valid_criteria_high_impact.strategic_impact == 85.0
    assert valid_criteria_high_impact.implementation_effort == 30.0
    assert valid_criteria_high_impact.urgency == 70.0
    assert valid_criteria_high_impact.strategic_alignment == 90.0


def test_prioritization_criteria_calculate_score(valid_criteria_high_impact):
    """Teste 2: calculate_score() calcula corretamente com pesos padrão.

    Formula: (85*0.4) + ((100-30)*0.3) + (70*0.15) + (90*0.15)
             = 34 + 21 + 10.5 + 13.5 = 79.0
    """
    score = valid_criteria_high_impact.calculate_score()
    assert score == 79.0  # Score esperado para high impact + low effort


def test_prioritization_criteria_calculate_score_custom_weights(valid_criteria_high_impact):
    """Teste 3: calculate_score() aceita pesos customizados."""
    score = valid_criteria_high_impact.calculate_score(
        impact_weight=0.50,  # Aumentar peso impacto
        effort_weight=0.25,
        urgency_weight=0.15,
        alignment_weight=0.10,
    )
    # (85*0.5) + ((100-30)*0.25) + (70*0.15) + (90*0.10)
    # = 42.5 + 17.5 + 10.5 + 9 = 79.5
    assert score == 79.5


def test_prioritization_criteria_invalid_weights_sum():
    """Teste 4: calculate_score() rejeita pesos que não somam 1.0."""
    criteria = PrioritizationCriteria(
        strategic_impact=80.0, implementation_effort=40.0, urgency=60.0, strategic_alignment=70.0
    )

    with pytest.raises(ValueError, match="Pesos devem somar 1.0"):
        criteria.calculate_score(
            impact_weight=0.50,
            effort_weight=0.30,  # Soma = 0.95 (não 1.0)
            urgency_weight=0.10,
            alignment_weight=0.05,
        )


def test_prioritization_criteria_invalid_values_out_of_range():
    """Teste 5: PrioritizationCriteria rejeita valores fora do range 0-100."""
    with pytest.raises(ValidationError):
        PrioritizationCriteria(
            strategic_impact=120.0,  # INVÁLIDO (> 100)
            implementation_effort=30.0,
            urgency=70.0,
            strategic_alignment=90.0,
        )

    with pytest.raises(ValidationError):
        PrioritizationCriteria(
            strategic_impact=80.0,
            implementation_effort=-10.0,  # INVÁLIDO (< 0)
            urgency=70.0,
            strategic_alignment=90.0,
        )


# ============================================================================
# TESTES - PRIORITIZED ITEM
# ============================================================================


def test_prioritized_item_valid(valid_prioritized_item_high):
    """Teste 6: PrioritizedItem válido aceita todos os campos obrigatórios."""
    assert valid_prioritized_item_high.item_id == "obj_001"
    assert valid_prioritized_item_high.title == "Aumentar NPS em 20 pontos"
    assert valid_prioritized_item_high.final_score == 72.0
    assert valid_prioritized_item_high.priority_level == "HIGH"
    assert valid_prioritized_item_high.rank == 1


def test_prioritized_item_priority_level_matches_score_high():
    """Teste 7: VALIDATOR priority_level alinha com final_score (HIGH: 50-74)."""
    item = PrioritizedItem(
        item_id="test_001",
        item_type="strategic_objective",
        title="Test Objective High Priority",
        description="Test description with 20+ characters for validation",
        perspective="Clientes",
        criteria=PrioritizationCriteria(
            strategic_impact=70.0,
            implementation_effort=40.0,
            urgency=60.0,
            strategic_alignment=75.0,
        ),
        final_score=65.0,  # HIGH range
        priority_level="HIGH",  # ALINHADO
        rank=1,
    )

    assert item.priority_level == "HIGH"
    assert 50 <= item.final_score < 75


def test_prioritized_item_priority_level_mismatch_score():
    """Teste 8: VALIDATOR rejeita priority_level desalinhado com final_score."""
    with pytest.raises(ValidationError, match="deve ter priority_level='HIGH'"):
        PrioritizedItem(
            item_id="test_002",
            item_type="strategic_objective",
            title="Test Mismatched Priority",
            description="Test description with 20+ characters for validation",
            perspective="Clientes",
            criteria=PrioritizationCriteria(
                strategic_impact=70.0,
                implementation_effort=40.0,
                urgency=60.0,
                strategic_alignment=75.0,
            ),
            final_score=65.0,  # HIGH range (50-74)
            priority_level="CRITICAL",  # DESALINHADO (deveria ser HIGH)
            rank=1,
        )


def test_prioritized_item_is_critical_method():
    """Teste 9: is_critical() retorna True se priority_level='CRITICAL'."""
    item = PrioritizedItem(
        item_id="test_003",
        item_type="strategic_objective",
        title="Test Critical Item",
        description="Test description with 20+ characters for validation",
        perspective="Financeira",
        criteria=PrioritizationCriteria(
            strategic_impact=90.0,
            implementation_effort=20.0,
            urgency=80.0,
            strategic_alignment=95.0,
        ),
        final_score=85.0,  # CRITICAL range (75-100)
        priority_level="CRITICAL",
        rank=1,
    )

    assert item.is_critical() is True
    assert item.is_high_or_critical() is True


def test_prioritized_item_is_high_or_critical_method():
    """Teste 10: is_high_or_critical() retorna True se HIGH ou CRITICAL."""
    item_high = PrioritizedItem(
        item_id="test_004",
        item_type="action_item",
        title="Test High Priority Item",
        description="Test description with 20+ characters for validation",
        perspective="Processos Internos",
        criteria=PrioritizationCriteria(
            strategic_impact=70.0,
            implementation_effort=40.0,
            urgency=60.0,
            strategic_alignment=65.0,
        ),
        final_score=60.0,  # HIGH range
        priority_level="HIGH",
        rank=1,
    )

    assert item_high.is_high_or_critical() is True
    assert item_high.is_critical() is False


def test_prioritized_item_invalid_title_too_short():
    """Teste 11: PrioritizedItem rejeita title < 10 caracteres."""
    with pytest.raises(ValidationError):
        PrioritizedItem(
            item_id="test_005",
            item_type="strategic_objective",
            title="Teste",  # INVÁLIDO (5 chars < 10)
            description="Test description with 20+ characters for validation",
            perspective="Clientes",
            criteria=PrioritizationCriteria(
                strategic_impact=70.0,
                implementation_effort=40.0,
                urgency=60.0,
                strategic_alignment=70.0,
            ),
            final_score=65.0,
            priority_level="HIGH",
            rank=1,
        )


def test_prioritized_item_invalid_description_too_short():
    """Teste 12: PrioritizedItem rejeita description < 20 caracteres."""
    with pytest.raises(ValidationError):
        PrioritizedItem(
            item_id="test_006",
            item_type="strategic_objective",
            title="Test Objective Valid Title",
            description="Short",  # INVÁLIDO (5 chars < 20)
            perspective="Clientes",
            criteria=PrioritizationCriteria(
                strategic_impact=70.0,
                implementation_effort=40.0,
                urgency=60.0,
                strategic_alignment=70.0,
            ),
            final_score=65.0,
            priority_level="HIGH",
            rank=1,
        )


# ============================================================================
# TESTES - PRIORITIZATION MATRIX
# ============================================================================


def test_prioritization_matrix_valid(valid_prioritization_matrix):
    """Teste 13: PrioritizationMatrix válida aceita lista de items com ranks únicos."""
    assert valid_prioritization_matrix.total_items == 3
    assert valid_prioritization_matrix.prioritization_context.startswith("Priorização objetivos")
    assert len(valid_prioritization_matrix.prioritization_context) >= 20  # min_length


def test_prioritization_matrix_unique_ranks_validator(
    valid_prioritized_item_high, valid_prioritized_item_medium
):
    """Teste 14: VALIDATOR unique_ranks rejeita ranks duplicados."""
    # Criar items com ranks duplicados (1, 1 - INVÁLIDO)
    valid_prioritized_item_high.rank = 1
    valid_prioritized_item_medium.rank = 1  # DUPLICADO

    with pytest.raises(ValidationError, match="Ranks devem ser únicos e sequenciais"):
        PrioritizationMatrix(
            items=[valid_prioritized_item_high, valid_prioritized_item_medium],
            prioritization_context="Priorização teste ranks duplicados Q1 2025",
        )


def test_prioritization_matrix_sequential_ranks_validator(
    valid_prioritized_item_high, valid_prioritized_item_medium, valid_prioritized_item_low
):
    """Teste 15: VALIDATOR unique_ranks rejeita ranks não-sequenciais."""
    # Criar items com ranks não-sequenciais (1, 2, 5 - INVÁLIDO, deveria ser 1, 2, 3)
    valid_prioritized_item_high.rank = 1
    valid_prioritized_item_medium.rank = 2
    valid_prioritized_item_low.rank = 5  # NÃO-SEQUENCIAL (gap: 3, 4 ausentes)

    with pytest.raises(ValidationError, match="Ranks devem ser únicos e sequenciais"):
        PrioritizationMatrix(
            items=[
                valid_prioritized_item_high,
                valid_prioritized_item_medium,
                valid_prioritized_item_low,
            ],
            prioritization_context="Priorização teste ranks não-sequenciais Q1 2025",
        )


def test_prioritization_matrix_top_n_method(valid_prioritization_matrix):
    """Teste 16: top_n() retorna top N items ordenados por rank."""
    top_2 = valid_prioritization_matrix.top_n(2)

    assert len(top_2) == 2
    assert top_2[0].rank == 1  # Primeiro item (rank mais baixo = mais prioritário)
    assert top_2[1].rank == 2  # Segundo item


def test_prioritization_matrix_by_priority_level_method(valid_prioritization_matrix):
    """Teste 17: by_priority_level() filtra items por priority_level."""
    high_items = valid_prioritization_matrix.by_priority_level("HIGH")

    assert len(high_items) == 1
    assert high_items[0].priority_level == "HIGH"


def test_prioritization_matrix_by_perspective_method(valid_prioritization_matrix):
    """Teste 18: by_perspective() filtra items por perspectiva BSC."""
    clientes_items = valid_prioritization_matrix.by_perspective("Clientes")

    assert len(clientes_items) == 1
    assert clientes_items[0].perspective == "Clientes"


def test_prioritization_matrix_is_balanced_method():
    """Teste 19: is_balanced() retorna True se 4 perspectivas têm >= 1 item."""
    # Criar matriz balanceada (1 item por perspectiva)
    items = [
        PrioritizedItem(
            item_id=f"obj_{i}",
            item_type="strategic_objective",
            title=f"Test Objective {i+1} for Perspective",
            description=f"Test description with 20+ characters for validation {i}",
            perspective=perspective,
            criteria=PrioritizationCriteria(
                strategic_impact=70.0,
                implementation_effort=40.0,
                urgency=60.0,
                strategic_alignment=70.0,
            ),
            final_score=65.0,
            priority_level="HIGH",
            rank=i + 1,
        )
        for i, perspective in enumerate(
            ["Financeira", "Clientes", "Processos Internos", "Aprendizado e Crescimento"]
        )
    ]

    matrix = PrioritizationMatrix(
        items=items, prioritization_context="Priorização teste balanceamento Q1 2025"
    )

    assert matrix.is_balanced() is True
    assert matrix.total_items == 4


def test_prioritization_matrix_summary_method(valid_prioritization_matrix):
    """Teste 20: summary() gera resumo executivo estruturado."""
    summary = valid_prioritization_matrix.summary()

    assert "Matriz de Priorização: 3 items priorizados" in summary
    assert "CRITICAL" in summary or "HIGH" in summary  # Contém distribuição prioridades
    assert "Top 3 Prioridades:" in summary
    assert "Balanceamento:" in summary


def test_format_prioritization_matrix_for_display(valid_prioritization_matrix):
    """Teste 21: format_prioritization_matrix_for_display() formata matriz amigavelmente."""
    formatted = format_prioritization_matrix_for_display(valid_prioritization_matrix)

    assert "MATRIZ DE PRIORIZAÇÃO BSC" in formatted
    assert "RESUMO EXECUTIVO:" in formatted
    assert "ITEMS PRIORIZADOS" in formatted
    assert "#1" in formatted  # Mostra ranks


def test_build_items_context():
    """Teste 22: build_items_context() formata lista de items para prompt."""
    items = [
        {
            "id": "obj_001",
            "type": "strategic_objective",
            "title": "Aumentar NPS",
            "description": "Melhorar experiência cliente",
            "perspective": "Clientes",
        },
        {
            "id": "obj_002",
            "type": "action_item",
            "title": "Reduzir custos",
            "description": "Otimizar processos",
            "perspective": "Financeira",
        },
    ]

    context = build_items_context(items)

    assert "Total de 2 items a priorizar" in context
    assert "Aumentar NPS" in context
    assert "Reduzir custos" in context
    assert "Clientes" in context
    assert "Financeira" in context
