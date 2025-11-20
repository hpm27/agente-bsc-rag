"""
Testes unitários para schemas do Strategy Map (Sprint 2).

Valida schemas Pydantic: CauseEffectConnection, StrategyMapPerspective, 
StrategyMap, AlignmentReport.

Best Practice aplicada: Fixtures válidas com margem de segurança (checklist PONTO 15).
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.memory.schemas import (
    CauseEffectConnection,
    StrategyMapPerspective,
    StrategyMap,
    AlignmentReport,
    StrategicObjective
)


# ============================================================================
# FIXTURES VÁLIDAS (com margem de segurança - PONTO 15)
# ============================================================================


@pytest.fixture
def valid_strategic_objective_financial():
    """Fixture de StrategicObjective válido (perspectiva Financeira)."""
    return StrategicObjective(
        name="Aumentar EBITDA para 18% até 2026",
        description="Atingir margem EBITDA de 18% através de eficiência operacional e mix de produtos premium, com foco em redução de custos e aumento de preços",
        perspective="Financeira",
        timeframe="12 meses",
        success_criteria=[
            "Margem EBITDA >= 18% até Q4 2026",
            "Redução de custo operacional >= 15% YoY"
        ],
        related_kpis=["Margem EBITDA", "Custo por unidade"],
        priority="Alta"
    )


@pytest.fixture
def valid_strategic_objective_customer():
    """Fixture de StrategicObjective válido (perspectiva Clientes)."""
    return StrategicObjective(
        name="Atingir NPS 50+ e reduzir churn para menos de 5%",
        description="Melhorar satisfação e retenção de clientes através de programa de customer success estruturado e onboarding personalizado",
        perspective="Clientes",
        timeframe="6 meses",
        success_criteria=[
            "NPS >= 50 pontos até Q2 2026",
            "Churn rate < 5% ao ano"
        ],
        related_kpis=["NPS", "Churn Rate"],
        priority="Alta"
    )


@pytest.fixture
def valid_strategic_objective_process():
    """Fixture de StrategicObjective válido (perspectiva Processos)."""
    return StrategicObjective(
        name="Reduzir lead time de produção em 30%",
        description="Implementar Lean Manufacturing e VSM para eliminar waste e reduzir lead time de 45 para 31 dias através de mapeamento de fluxo de valor",
        perspective="Processos Internos",
        timeframe="3 meses",
        success_criteria=[
            "Lead time <= 31 dias até Q1 2026",
            "Waste identificado e eliminado >= 25%"
        ],
        related_kpis=["Lead Time", "Waste Percentage"],
        priority="Alta"
    )


@pytest.fixture
def valid_strategic_objective_learning():
    """Fixture de StrategicObjective válido (perspectiva Aprendizado)."""
    return StrategicObjective(
        name="Certificar 80% da equipe em Lean Six Sigma Green Belt",
        description="Programa de certificação Lean Six Sigma (120h) para capacitar equipe a identificar e eliminar waste, com meta de 80% de certificação até Q2 2026",
        perspective="Aprendizado e Crescimento",
        timeframe="6 meses",
        success_criteria=[
            "80% da equipe certificada Green Belt até Q2 2026",
            "100% participação no programa de treinamento"
        ],
        related_kpis=["% Equipe Certificada", "Horas Treinamento"],
        priority="Alta"
    )


@pytest.fixture
def valid_cause_effect_connection():
    """Fixture de CauseEffectConnection válida."""
    return CauseEffectConnection(
        source_objective_id="learning_obj_1",
        target_objective_id="process_obj_2",
        relationship_type="enables",
        strength="strong",
        rationale="Certificação Lean Six Sigma Green Belt (120h) capacita equipe a identificar e eliminar waste nos processos de manufatura, habilitando redução de 30% no lead time de produção através de mapeamento de fluxo de valor e eliminação de gargalos"
    )


@pytest.fixture
def valid_strategy_map_perspective_financial(valid_strategic_objective_financial):
    """Fixture de StrategyMapPerspective válida (Financeira)."""
    obj1 = valid_strategic_objective_financial
    obj2 = StrategicObjective(
        name="Reduzir custo operacional em 15% até 2026",
        description="Reduzir custo por unidade produzida através de automação de processos manuais e implementação de Lean Manufacturing com foco em eliminação de waste",
        perspective="Financeira",
        target_date=datetime(2026, 6, 30),
        owner="CFO",
        status="Planejado",
        timeframe="6 meses",
        success_criteria=["Custo por unidade <= R$50", "ROI automação >= 150%"]
    )
    
    return StrategyMapPerspective(
        name="Financeira",
        objectives=[obj1, obj2]
    )


@pytest.fixture
def valid_strategy_map(
    valid_strategy_map_perspective_financial,
    valid_strategic_objective_customer,
    valid_strategic_objective_process,
    valid_strategic_objective_learning,
    valid_cause_effect_connection
):
    """Fixture de StrategyMap válido completo."""
    
    # Criar perspectivas
    financial_perspective = valid_strategy_map_perspective_financial
    
    customer_perspective = StrategyMapPerspective(
        name="Clientes",
        objectives=[
            valid_strategic_objective_customer,
            StrategicObjective(
                name="Reduzir churn para menos de 5% ao ano",
                description="Implementar programa de customer success com onboarding estruturado e acompanhamento proativo para reduzir churn de clientes premium",
                perspective="Clientes",
                target_date=datetime(2026, 12, 31),
                owner="CMO",
                status="Em andamento",
                timeframe="12 meses",
                success_criteria=["Churn anual menor ou igual a 5%", "NPS acima de 50 pontos em Q4/2026"]
            )
        ]
    )
    
    process_perspective = StrategyMapPerspective(
        name="Processos Internos",
        objectives=[
            valid_strategic_objective_process,
            StrategicObjective(
                name="Atingir OEE de 85% nas linhas críticas",
                description="Melhorar Overall Equipment Effectiveness através de manutenção preventiva, SMED e balanceamento de linha para atingir OEE de 85% nas linhas de maior volume",
                perspective="Processos Internos",
                target_date=datetime(2026, 9, 30),
                owner="Gerente Industrial",
                status="Planejado",
                timeframe="9 meses",
                success_criteria=["OEE >= 85% nas linhas críticas", "Disponibilidade >= 90% (redução paradas não programadas)"]
            )
        ]
    )
    
    learning_perspective = StrategyMapPerspective(
        name="Aprendizado e Crescimento",
        objectives=[
            valid_strategic_objective_learning,
            StrategicObjective(
                name="Implementar cultura de melhoria contínua com 50+ kaizens/ano",
                description="Criar sistema de sugestões estruturado e programa de reconhecimento para gerar 50+ kaizens implementados por ano com envolvimento de 70% da equipe",
                perspective="Aprendizado e Crescimento",
                target_date=datetime(2026, 12, 31),
                owner="CHRO",
                status="Planejado",
                timeframe="12 meses",
                success_criteria=["Mínimo 50 kaizens implementados no ano", "Participação de 70% ou mais da equipe no programa"]
            )
        ]
    )
    
    # Criar conexões causa-efeito (mínimo 4)
    connections = [
        valid_cause_effect_connection,
        CauseEffectConnection(
            source_objective_id="process_obj_1",
            target_objective_id="customer_obj_1",
            relationship_type="drives",
            strength="strong",
            rationale="Redução de 30% no lead time de produção (de 45 para 31 dias) permite entregas mais rápidas e previsíveis, impulsionando NPS de 40 para 50+ através de melhoria na promessa de entrega cumprida"
        ),
        CauseEffectConnection(
            source_objective_id="customer_obj_1",
            target_objective_id="financial_obj_1",
            relationship_type="drives",
            strength="medium",
            rationale="Aumento de NPS de 40 para 50+ e redução de churn de 8% para <5% gera aumento de 20% na receita recorrente através de maior retenção de clientes premium e aumento de 30% em referrals"
        ),
        CauseEffectConnection(
            source_objective_id="learning_obj_2",
            target_objective_id="process_obj_2",
            relationship_type="supports",
            strength="medium",
            rationale="Cultura de melhoria contínua com 50+ kaizens/ano contribui para aumento de OEE de 75% para 85% através de identificação e eliminação proativa de perdas e gargalos pela própria equipe operacional"
        )
    ]
    
    return StrategyMap(
        financial=financial_perspective,
        customer=customer_perspective,
        process=process_perspective,
        learning=learning_perspective,
        cause_effect_connections=connections,
        strategic_priorities=[
            "Excelência Operacional",
            "Customer Intimacy",
            "Inovação de Produto"
        ],
        mission="Ser líder em soluções manufatureiras de alta qualidade para o mercado brasileiro",
        vision="Transformar 1000+ empresas através de excelência operacional até 2030",
        values=["Excelência", "Inovação", "Cliente no Centro", "Melhoria Contínua"]
    )


@pytest.fixture
def valid_alignment_report():
    """Fixture de AlignmentReport válido."""
    return AlignmentReport(
        score=87.5,
        is_balanced=True,
        gaps=[
            "Perspective Processos Internos tem apenas 1 objective (mínimo 2 para balanceamento)"
        ],
        warnings=[
            "Objective 'Aumentar vendas' é operacional (deveria ser estratégico)",
            "Objective 'Melhorar eficiência' usa jargon genérico"
        ],
        recommendations=[
            "Adicionar pelo menos 1 objective estratégico na perspective Processos Internos",
            "Substituir 'Aumentar vendas' por objective estratégico específico (ex: 'Expandir presença em mercado B2B com crescimento de 40% em 2 anos')",
            "Substituir 'Melhorar eficiência' por objective mensurável (ex: 'Reduzir lead time de produção em 30% através de implementação de Lean Manufacturing')"
        ],
        validation_checks={
            "balanced_perspectives": False,
            "all_objectives_have_kpis": True,
            "cause_effect_exists": True,
            "no_isolated_objectives": True,
            "kpis_are_smart": True,
            "goals_are_strategic": False,
            "has_rationale": True,
            "no_jargon": False
        }
    )


# ============================================================================
# TESTES CAUSEEFFECTCONNECTION
# ============================================================================


def test_cause_effect_connection_valid(valid_cause_effect_connection):
    """CauseEffectConnection válida deve passar validação."""
    assert valid_cause_effect_connection.source_objective_id == "learning_obj_1"
    assert valid_cause_effect_connection.target_objective_id == "process_obj_2"
    assert valid_cause_effect_connection.relationship_type == "enables"
    assert valid_cause_effect_connection.strength == "strong"
    assert len(valid_cause_effect_connection.rationale) >= 30


def test_cause_effect_connection_rationale_too_short():
    """CauseEffectConnection com rationale <30 chars deve falhar."""
    with pytest.raises(ValidationError) as exc_info:
        CauseEffectConnection(
            source_objective_id="learning_obj_1",
            target_objective_id="process_obj_2",
            relationship_type="enables",
            strength="strong",
            rationale="Muito curto"  # <30 chars
        )
    
    assert "rationale" in str(exc_info.value).lower()


def test_cause_effect_connection_invalid_relationship_type():
    """CauseEffectConnection com relationship_type inválido deve falhar."""
    with pytest.raises(ValidationError) as exc_info:
        CauseEffectConnection(
            source_objective_id="learning_obj_1",
            target_objective_id="process_obj_2",
            relationship_type="contribui para",  # Não é Literal válido
            strength="strong",
            rationale="Rationale válido com mais de 30 caracteres para passar validação mínima"
        )
    
    assert "relationship_type" in str(exc_info.value).lower()


def test_cause_effect_connection_invalid_strength():
    """CauseEffectConnection com strength inválido deve falhar."""
    with pytest.raises(ValidationError) as exc_info:
        CauseEffectConnection(
            source_objective_id="learning_obj_1",
            target_objective_id="process_obj_2",
            relationship_type="enables",
            strength="very_strong",  # Não é Literal válido
            rationale="Rationale válido com mais de 30 caracteres para passar validação mínima"
        )
    
    assert "strength" in str(exc_info.value).lower()


def test_cause_effect_connection_default_strength(valid_cause_effect_connection):
    """CauseEffectConnection sem strength deve usar default 'medium'."""
    connection = CauseEffectConnection(
        source_objective_id="learning_obj_1",
        target_objective_id="process_obj_2",
        relationship_type="enables",
        # strength omitido
        rationale="Rationale válido com mais de 30 caracteres para passar validação mínima"
    )
    
    assert connection.strength == "medium"


# ============================================================================
# TESTES STRATEGYMAPPERSPECTIVE
# ============================================================================


def test_strategy_map_perspective_valid(valid_strategy_map_perspective_financial):
    """StrategyMapPerspective válida deve passar validação."""
    perspective = valid_strategy_map_perspective_financial
    
    assert perspective.name == "Financeira"
    assert len(perspective.objectives) == 2
    assert all(obj.perspective == "Financeira" for obj in perspective.objectives)


def test_strategy_map_perspective_min_objectives_violated():
    """StrategyMapPerspective com <2 objectives deve falhar."""
    obj = StrategicObjective(
        name="Único objetivo",
        description="Descrição válida com mais de 50 caracteres para passar validação mínima exigida pelo schema Pydantic",
        perspective="Financeira",
        target_date=datetime(2026, 12, 31),
        owner="CFO",
        status="Planejado",
        timeframe="12 meses",
        success_criteria=["Critério de sucesso específico número um", "Critério de sucesso específico número dois"]
    )
    
    with pytest.raises(ValidationError) as exc_info:
        StrategyMapPerspective(
            name="Financeira",
            objectives=[obj]  # Apenas 1 objective (mínimo 2)
        )
    
    assert "objectives" in str(exc_info.value).lower()


def test_strategy_map_perspective_max_objectives_violated():
    """StrategyMapPerspective com >10 objectives deve falhar (RED FLAG BSCDesigner 2025)."""
    objectives = [
        StrategicObjective(
            name=f"Objective {i}",
            description=f"Descrição do objective {i} com mais de 50 caracteres necessários para validação Pydantic min_length",
            perspective="Financeira",
            target_date=datetime(2026, 12, 31),
            owner="CFO",
            status="Planejado",
            timeframe="12 meses",
            success_criteria=["Critério de sucesso específico número um", "Critério de sucesso específico número dois"]
        )
        for i in range(11)  # 11 objectives (máximo 10)
    ]
    
    with pytest.raises(ValidationError) as exc_info:
        StrategyMapPerspective(
            name="Financeira",
            objectives=objectives
        )
    
    assert "objectives" in str(exc_info.value).lower()


def test_strategy_map_perspective_wrong_perspective_objectives():
    """StrategyMapPerspective com objectives de perspectiva errada deve falhar."""
    obj_financial = StrategicObjective(
        name="Objective Financeiro",
        description="Descrição válida com mais de 50 caracteres para passar validação mínima exigida pelo schema Pydantic",
        perspective="Financeira",  # Perspectiva ERRADA (deveria ser Clientes)
        target_date=datetime(2026, 12, 31),
        owner="CFO",
        status="Planejado",
        timeframe="12 meses",
        success_criteria=["Critério de sucesso específico número um", "Critério de sucesso específico número dois"]
    )
    
    obj_customer = StrategicObjective(
        name="Objective Clientes",
        description="Descrição válida com mais de 50 caracteres para passar validação mínima exigida pelo schema Pydantic",
        perspective="Clientes",
        target_date=datetime(2026, 12, 31),
        owner="CMO",
        status="Planejado",
        timeframe="12 meses",
        success_criteria=["Critério de sucesso específico número um", "Critério de sucesso específico número dois"]
    )
    
    with pytest.raises(ValueError) as exc_info:
        StrategyMapPerspective(
            name="Clientes",  # Nome da perspective
            objectives=[obj_financial, obj_customer]  # obj_financial tem perspectiva errada
        )
    
    assert "Clientes" in str(exc_info.value)
    assert "Financeira" in str(exc_info.value)


# ============================================================================
# TESTES STRATEGYMAP
# ============================================================================


def test_strategy_map_valid(valid_strategy_map):
    """StrategyMap válido completo deve passar validação."""
    strategy_map = valid_strategy_map
    
    # Validar 4 perspectivas
    assert strategy_map.financial.name == "Financeira"
    assert strategy_map.customer.name == "Clientes"
    assert strategy_map.process.name == "Processos Internos"
    assert strategy_map.learning.name == "Aprendizado e Crescimento"
    
    # Validar conexões causa-efeito (mínimo 4)
    assert len(strategy_map.cause_effect_connections) >= 4
    
    # Validar strategic priorities (1-3)
    assert 1 <= len(strategy_map.strategic_priorities) <= 3
    
    # Validar métodos auxiliares
    assert strategy_map.total_objectives() == 8  # 2 por perspectiva
    assert strategy_map.is_balanced(min_per_perspective=2, max_per_perspective=10)


def test_strategy_map_min_connections_violated():
    """StrategyMap com <4 conexões causa-efeito deve falhar."""
    # Criar perspectives válidas (mínimo)
    financial = StrategyMapPerspective(
        name="Financeira",
        objectives=[
            StrategicObjective(name="Objetivo Financeiro 1", description="Desc" * 20, perspective="Financeira", target_date=datetime(2026, 12, 31), owner="CFO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"]),
            StrategicObjective(name="Objetivo Financeiro 2", description="Desc" * 20, perspective="Financeira", target_date=datetime(2026, 12, 31), owner="CFO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"])
        ]
    )
    
    customer = StrategyMapPerspective(
        name="Clientes",
        objectives=[
            StrategicObjective(name="Objetivo Cliente 1", description="Desc" * 20, perspective="Clientes", target_date=datetime(2026, 12, 31), owner="CMO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"]),
            StrategicObjective(name="Objetivo Cliente 2", description="Desc" * 20, perspective="Clientes", target_date=datetime(2026, 12, 31), owner="CMO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"])
        ]
    )
    
    process = StrategyMapPerspective(
        name="Processos Internos",
        objectives=[
            StrategicObjective(name="Objetivo Processo 1", description="Desc" * 20, perspective="Processos Internos", target_date=datetime(2026, 12, 31), owner="COO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"]),
            StrategicObjective(name="Objetivo Processo 2", description="Desc" * 20, perspective="Processos Internos", target_date=datetime(2026, 12, 31), owner="COO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"])
        ]
    )
    
    learning = StrategyMapPerspective(
        name="Aprendizado e Crescimento",
        objectives=[
            StrategicObjective(name="Objetivo Learning 1", description="Desc" * 20, perspective="Aprendizado e Crescimento", target_date=datetime(2026, 12, 31), owner="CHRO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"]),
            StrategicObjective(name="Objetivo Learning 2", description="Desc" * 20, perspective="Aprendizado e Crescimento", target_date=datetime(2026, 12, 31), owner="CHRO", status="Planejado", timeframe="12 meses", success_criteria=["Critério sucesso válido número 1", "Critério sucesso válido número 2"])
        ]
    )
    
    # Apenas 3 conexões (mínimo 4)
    connections = [
        CauseEffectConnection(source_objective_id="l1", target_objective_id="p1", relationship_type="enables", rationale="R" * 50),
        CauseEffectConnection(source_objective_id="p1", target_objective_id="c1", relationship_type="drives", rationale="R" * 50),
        CauseEffectConnection(source_objective_id="c1", target_objective_id="f1", relationship_type="drives", rationale="R" * 50)
    ]
    
    with pytest.raises(ValidationError) as exc_info:
        StrategyMap(
            financial=financial,
            customer=customer,
            process=process,
            learning=learning,
            cause_effect_connections=connections,  # Apenas 3 (mínimo 4)
            strategic_priorities=["Excelência Operacional"]
        )
    
    assert "cause_effect_connections" in str(exc_info.value).lower()


def test_strategy_map_strategic_priorities_bounds(valid_strategy_map):
    """StrategyMap deve ter 1-3 strategic priorities."""
    # Já testado no valid_strategy_map (3 priorities)
    # Testar boundary: 1 priority (mínimo) - CRIAR NOVO OBJETO para triggar validação
    map_1_priority = StrategyMap(
        financial=valid_strategy_map.financial,
        customer=valid_strategy_map.customer,
        process=valid_strategy_map.process,
        learning=valid_strategy_map.learning,
        cause_effect_connections=valid_strategy_map.cause_effect_connections,
        strategic_priorities=["Excelência Operacional"]  # 1 priority (mínimo)
    )
    assert len(map_1_priority.strategic_priorities) == 1
    
    # Testar boundary: 4 priorities (deveria falhar) - CRIAR NOVO OBJETO
    with pytest.raises(ValidationError):
        StrategyMap(
            financial=valid_strategy_map.financial,
            customer=valid_strategy_map.customer,
            process=valid_strategy_map.process,
            learning=valid_strategy_map.learning,
            cause_effect_connections=valid_strategy_map.cause_effect_connections,
            strategic_priorities=[
                "Priority 1", "Priority 2", "Priority 3", "Priority 4"  # 4 priorities (máximo 3)
            ]
        )


def test_strategy_map_methods(valid_strategy_map):
    """Testar métodos auxiliares do StrategyMap."""
    strategy_map = valid_strategy_map
    
    # total_objectives()
    assert strategy_map.total_objectives() == 8
    
    # objectives_per_perspective()
    counts = strategy_map.objectives_per_perspective()
    assert counts["Financeira"] == 2
    assert counts["Clientes"] == 2
    assert counts["Processos Internos"] == 2
    assert counts["Aprendizado e Crescimento"] == 2
    
    # is_balanced()
    assert strategy_map.is_balanced(min_per_perspective=2, max_per_perspective=10)


# ============================================================================
# TESTES ALIGNMENTREPORT
# ============================================================================


def test_alignment_report_valid(valid_alignment_report):
    """AlignmentReport válido deve passar validação."""
    report = valid_alignment_report
    
    assert 0 <= report.score <= 100
    assert report.score == 87.5
    assert report.is_balanced is True
    assert len(report.gaps) == 1
    assert len(report.warnings) == 2
    assert len(report.recommendations) == 3
    assert len(report.validation_checks) == 8


def test_alignment_report_score_bounds():
    """AlignmentReport score deve estar entre 0-100."""
    # Score válido (0)
    report_min = AlignmentReport(
        score=0,
        is_balanced=False,
        validation_checks={"check1": False}
    )
    assert report_min.score == 0
    
    # Score válido (100)
    report_max = AlignmentReport(
        score=100,
        is_balanced=True,
        validation_checks={"check1": True}
    )
    assert report_max.score == 100
    
    # Score inválido (<0)
    with pytest.raises(ValidationError):
        AlignmentReport(
            score=-1,
            is_balanced=False,
            validation_checks={"check1": False}
        )
    
    # Score inválido (>100)
    with pytest.raises(ValidationError):
        AlignmentReport(
            score=101,
            is_balanced=True,
            validation_checks={"check1": True}
        )


def test_alignment_report_is_approved(valid_alignment_report):
    """Testar método is_approved() com thresholds diferentes."""
    report = valid_alignment_report  # score=87.5
    
    # Threshold default (80)
    assert report.is_approved() is True
    
    # Threshold 85
    assert report.is_approved(threshold=85.0) is True
    
    # Threshold 90
    assert report.is_approved(threshold=90.0) is False


def test_alignment_report_critical_gaps_count(valid_alignment_report):
    """Testar método critical_gaps_count()."""
    report = valid_alignment_report  # 1 gap
    assert report.critical_gaps_count() == 1
    
    # Report sem gaps
    report_no_gaps = AlignmentReport(
        score=100,
        is_balanced=True,
        gaps=[],  # Sem gaps
        validation_checks={"check1": True}
    )
    assert report_no_gaps.critical_gaps_count() == 0

