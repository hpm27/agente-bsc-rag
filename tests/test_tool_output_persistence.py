"""Testes E2E para persistência de Tool Outputs no Mem0.

Suite completa de testes para validação do salvamento e recuperação de outputs
de ferramentas consultivas BSC (SWOT, Five Whys, Issue Tree, KPI, Strategic Objectives,
Benchmarking) no sistema de memória persistente Mem0 Platform.

Cobertura:
- save_tool_output() para cada um dos 6 tipos de ferramentas
- get_tool_output() com recuperação por tool_name
- Validação de automatic cleanup (outputs antigos deletados)
- Edge cases (output não existente, múltiplos outputs, etc.)

Created: 2025-10-27 (FASE 3.10)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch

from src.memory.schemas import (
    ToolOutput,
    SWOTAnalysis,
    FiveWhysAnalysis,
    WhyIteration,
    IssueTreeAnalysis,
    IssueNode,
    KPIDefinition,
    KPIFramework,
    StrategicObjective,
    StrategicObjectivesFramework,
    BenchmarkReport,
)
from src.memory.mem0_client import Mem0ClientWrapper


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def real_mem0_client():
    """Cliente Mem0 real para testes E2E."""
    from config.settings import settings
    return Mem0ClientWrapper(api_key=settings.mem0_api_key)


@pytest.fixture
def test_client_id():
    """ID único para cada teste E2E."""
    import uuid
    return f"test_e2e_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_swot_output():
    """Output de exemplo para SWOT."""
    return SWOTAnalysis(
        strengths=["Equipe qualificada", "Marca forte no mercado"],
        weaknesses=["Processos manuais", "Falta de automação"],
        opportunities=["Expansão digital", "Novos mercados"],
        threats=["Concorrência intensa", "Mudanças regulatórias"]
    )


@pytest.fixture
def sample_five_whys_output():
    """Output de exemplo para Five Whys."""
    return FiveWhysAnalysis(
        problem_statement="Alta rotatividade de funcionários (turnover 40%)",
        iterations=[
            WhyIteration(
                question="Por que temos alta rotatividade?",
                answer="Salários abaixo do mercado e falta de plano de carreira",
                confidence=0.85,
                is_root_cause=False,
                reasoning="Esse é um fator importante mas não a causa raiz fundamental"
            ),
            WhyIteration(
                question="Por que os salários estão abaixo do mercado?",
                answer="Empresa não realiza benchmarking salarial regularmente",
                confidence=0.90,
                is_root_cause=True,
                reasoning="Este é o problema fundamental que causa os outros"
            )
        ],
        root_cause_summary="Ausência de estratégia de compensação competitiva"
    )


@pytest.fixture
def sample_issue_tree_output():
    """Output de exemplo para Issue Tree."""
    root = IssueNode(
        id="root_1",
        text="Baixa margem de lucro (15% vs indústria 25%)",
        category="Financeira",
        is_leaf=False,
        children=[
            IssueNode(
                id="node_1_1",
                text="Custos operacionais elevados",
                category="Financeira",
                is_leaf=False,
                children=[
                    IssueNode(id="leaf_1_1_1", text="Mão de obra cara", category="Financeira", is_leaf=True, children=[]),
                    IssueNode(id="leaf_1_1_2", text="Processos ineficientes", category="Processos", is_leaf=True, children=[])
                ]
            ),
            IssueNode(
                id="node_1_2",
                text="Preços de venda não competitivos",
                category="Clientes",
                is_leaf=False,
                children=[
                    IssueNode(id="leaf_1_2_1", text="Benchmarking insuficiente", category="Aprendizado", is_leaf=True, children=[])
                ]
            )
        ]
    )
    
    return IssueTreeAnalysis(
        root_problem="Baixa margem de lucro (15% vs indústria 25%)",
        tree=root,
        solution_paths=["Otimizar processos operacionais", "Revisar política de preços"]
    )


@pytest.fixture
def sample_kpi_framework():
    """Output de exemplo para KPI Framework."""
    return KPIFramework(
        financial=[
            KPIDefinition(
                name="EBITDA Margin",
                description="Margem EBITDA sobre receita total",
                target_value=22.0,
                current_value=15.0,
                unit="percent",
                perspective="Financeira",
                smart_criteria={
                    "specific": "Margem EBITDA mensal",
                    "measurable": "percentual sobre receita",
                    "achievable": "Indústria média: 20-25%",
                    "relevant": "Indica saúde financeira",
                    "time_bound": "Meta anual: 25% até Q4 2026"
                }
            )
        ],
        customer=[
            KPIDefinition(
                name="Customer Satisfaction Score (NPS)",
                description="Net Promoter Score de clientes",
                target_value=50,
                current_value=35,
                unit="score",
                perspective="Clientes",
                smart_criteria={
                    "specific": "NPS calculado mensalmente",
                    "measurable": "Escala -100 a +100",
                    "achievable": "Aumentar gradualmente",
                    "relevant": "Indica retenção e crescimento",
                    "time_bound": "Meta: 60 em 12 meses"
                }
            )
        ],
        process=[
            KPIDefinition(
                name="Process Automation Rate",
                description="Percentual de processos automatizados",
                target_value=70.0,
                current_value=45.0,
                unit="percent",
                perspective="Processos",
                smart_criteria={
                    "specific": "Processos automatizados vs totais",
                    "measurable": "Percentual mensurado trimestralmente",
                    "achievable": "Aumento gradual com investimento",
                    "relevant": "Indica eficiência operacional",
                    "time_bound": "Meta: 70% em 6 meses"
                }
            )
        ],
        learning=[
            KPIDefinition(
                name="Employee Training Hours",
                description="Horas de treinamento por funcionário por ano",
                target_value=40,
                current_value=18,
                unit="hours",
                perspective="Aprendizado",
                smart_criteria={
                    "specific": "Horas de treinamento/ano/funcionário",
                    "measurable": "Total de horas registradas",
                    "achievable": "Expansão gradual do programa",
                    "relevant": "Indica desenvolvimento de talentos",
                    "time_bound": "Meta: 40h em 2026"
                }
            )
        ]
    )


@pytest.fixture
def sample_strategic_objectives_framework():
    """Output de exemplo para Strategic Objectives Framework."""
    return StrategicObjectivesFramework(
        financial=[
            StrategicObjective(
                name="Aumentar rentabilidade em 35% em 3 anos",
                description="Melhorar margem operacional de 15% para 20%",
                perspective="Financeira",
                priority="high",
                target_timeline="Q4 2027",
                linked_kpis=["EBITDA Margin", "Operating Margin"]
            ),
            StrategicObjective(
                name="Diversificar receitas (70% recorrente até 2026)",
                description="Expandir base de receita recorrente vs one-time",
                perspective="Financeira",
                priority="medium",
                target_timeline="Q2 2026",
                linked_kpis=["Recurring Revenue Ratio"]
            )
        ],
        customer=[
            StrategicObjective(
                name="Atingir NPS de 60+ em 12 meses",
                description="Melhorar satisfação e advocacy dos clientes",
                perspective="Clientes",
                priority="high",
                target_timeline="Q4 2026",
                linked_kpis=["Customer NPS", "Customer Retention Rate"]
            )
        ],
        process=[
            StrategicObjective(
                name="Automatizar 70% dos processos em 6 meses",
                description="Reduzir manual work e aumentar eficiência",
                perspective="Processos",
                priority="high",
                target_timeline="Q2 2026",
                linked_kpis=["Process Automation Rate", "Time to Market"]
            )
        ],
        learning=[
            StrategicObjective(
                name="Desenvolver liderança de alto potencial em 20% do quadro",
                description="Programa de talent management e succession planning",
                perspective="Aprendizado",
                priority="medium",
                target_timeline="Q4 2027",
                linked_kpis=["Leadership Readiness Index", "Internal Promotion Rate"]
            )
        ]
    )


@pytest.fixture
def sample_benchmark_report():
    """Output de exemplo para Benchmarking Report."""
    return BenchmarkReport(
        company_name="TechCorp Brasil",
        industry="Software as a Service",
        benchmark_date="2025-10",
        metrics={
            "revenue_growth": {"company": 18.5, "industry_avg": 25.0, "industry_top_25": 35.0, "gap": -6.5},
            "ebitda_margin": {"company": 15.0, "industry_avg": 22.0, "industry_top_25": 30.0, "gap": -7.0},
            "customer_satisfaction": {"company": 7.2, "industry_avg": 7.8, "industry_top_25": 8.5, "gap": -0.6},
            "employee_engagement": {"company": 6.8, "industry_avg": 7.0, "industry_top_25": 8.2, "gap": -0.2}
        },
        insights=["Abaixo da média em receita e EBITDA", "Performance satisfatória em engajamento"],
        recommendations=["Acelerar estratégia de pricing", "Investir em automação"]
    )


# ============================================================================
# TESTES E2E REAIS: save_tool_output()
# ============================================================================


def test_e2e_save_swot_output(real_mem0_client, test_client_id, sample_swot_output):
    """Testa salvamento de output SWOT no Mem0."""
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump(),
        client_context="TechCorp - Empresa de tecnologia, medio porte"
    )
    
    # Salvar
    result = real_mem0_client.save_tool_output(test_client_id, tool_output)
    
    # Validar
    assert result == test_client_id
    
def test_e2e_save_and_get_swot_output(real_mem0_client, sample_swot_output):
    """Testa salvamento e recuperação de output SWOT no Mem0 em um único teste."""
    
    # Usar client_id fixo
    client_id = "test_e2e_swot_integrated"
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump(),
        client_context="TechCorp - Empresa de tecnologia, medio porte"
    )
    
    # Salvar
    save_result = real_mem0_client.save_tool_output(client_id, tool_output)
    assert save_result == client_id
    
    # Recuperar imediatamente
    print(f"[DEBUG] Tentando recuperar tool output para client_id={client_id}, tool_name=SWOT")
    retrieved_data = real_mem0_client.get_tool_output(client_id, "SWOT")
    print(f"[DEBUG] retrieved_data = {retrieved_data}")
    
    # Validar
    assert retrieved_data is not None
    assert retrieved_data["strengths"] == ["Equipe qualificada", "Marca forte no mercado"]
    assert retrieved_data["weaknesses"] == ["Processos manuais", "Falta de automação"]
    assert retrieved_data["opportunities"] == ["Expansão digital", "Novos mercados"]
    assert retrieved_data["threats"] == ["Concorrência intensa", "Mudanças regulatórias"]


def test_save_five_whys_output(mock_mem0_client, sample_five_whys_output):
    """Testa salvamento de output Five Whys no Mem0."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="FIVE_WHYS",
        tool_output_data=sample_five_whys_output.model_dump(),
        client_context="TechCorp - Alta rotatividade de funcionários"
    )
    
    # Salvar
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar
    assert result == "client_123"
    assert mock_add.called
    
    call_args = mock_add.call_args
    kwargs = call_args.kwargs
    
    # Validar metadata
    assert kwargs["metadata"]["tool_name"] == "FIVE_WHYS"
    assert kwargs["metadata"]["report_type"] == "tool_output_five_whys"
    assert "problem_statement" in str(kwargs["metadata"]["tool_output_data"])


def test_save_issue_tree_output(mock_mem0_client, sample_issue_tree_output):
    """Testa salvamento de output Issue Tree no Mem0."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="ISSUE_TREE",
        tool_output_data=sample_issue_tree_output.model_dump(),
        client_context="TechCorp - Problema de lucratividade"
    )
    
    # Salvar
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar
    assert result == "client_123"
    assert mock_add.called
    
    call_args = mock_add.call_args
    kwargs = call_args.kwargs
    
    # Validar metadata
    assert kwargs["metadata"]["tool_name"] == "ISSUE_TREE"
    assert kwargs["metadata"]["report_type"] == "tool_output_issue_tree"
    assert "root_problem" in str(kwargs["metadata"]["tool_output_data"])


def test_save_kpi_framework_output(mock_mem0_client, sample_kpi_framework):
    """Testa salvamento de output KPI Framework no Mem0."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="KPI_DEFINER",
        tool_output_data=sample_kpi_framework.model_dump(),
        client_context="TechCorp - Framework de indicadores BSC"
    )
    
    # Salvar
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar
    assert result == "client_123"
    assert mock_add.called
    
    call_args = mock_add.call_args
    kwargs = call_args.kwargs
    
    # Validar metadata
    assert kwargs["metadata"]["tool_name"] == "KPI_DEFINER"
    assert kwargs["metadata"]["report_type"] == "tool_output_kpi_definer"
    assert "financial" in str(kwargs["metadata"]["tool_output_data"])


def test_save_strategic_objectives_output(mock_mem0_client, sample_strategic_objectives_framework):
    """Testa salvamento de output Strategic Objectives no Mem0."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="STRATEGIC_OBJECTIVES",
        tool_output_data=sample_strategic_objectives_framework.model_dump(),
        client_context="TechCorp - Objetivos estratégicos alinhados BSC"
    )
    
    # Salvar
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar
    assert result == "client_123"
    assert mock_add.called
    
    call_args = mock_add.call_args
    kwargs = call_args.kwargs
    
    # Validar metadata
    assert kwargs["metadata"]["tool_name"] == "STRATEGIC_OBJECTIVES"
    assert kwargs["metadata"]["report_type"] == "tool_output_strategic_objectives"
    assert "financial" in str(kwargs["metadata"]["tool_output_data"])


def test_save_benchmarking_output(mock_mem0_client, sample_benchmark_report):
    """Testa salvamento de output Benchmarking no Mem0."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="BENCHMARKING",
        tool_output_data=sample_benchmark_report.model_dump(),
        client_context="TechCorp - Benchmarking indústria SaaS"
    )
    
    # Salvar
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar
    assert result == "client_123"
    assert mock_add.called
    
    call_args = mock_add.call_args
    kwargs = call_args.kwargs
    
    # Validar metadata
    assert kwargs["metadata"]["tool_name"] == "BENCHMARKING"
    assert kwargs["metadata"]["report_type"] == "tool_output_benchmarking"
    assert "benchmark_date" in str(kwargs["metadata"]["tool_output_data"])


# ============================================================================
# TESTES: get_tool_output()
# ============================================================================


def test_get_tool_output_existing(mock_mem0_client, sample_swot_output):
    """Testa recuperação de output existente."""
    
    client, mock_add, mock_get_all, _ = mock_mem0_client
    
    # Mock de memória existente
    mock_memory = {
        "id": "memory_123",
        "user_id": "client_123",
        "metadata": {
            "tool_output_data": sample_swot_output.model_dump(),
            "tool_name": "SWOT",
            "report_type": "tool_output_swot"
        }
    }
    mock_get_all.return_value = [mock_memory]
    
    # Recuperar
    result = client.get_tool_output("client_123", "SWOT")
    
    # Validar
    assert result is not None
    assert "strengths" in str(result)
    assert "weaknesses" in str(result)


def test_get_tool_output_not_found(mock_mem0_client):
    """Testa recuperação quando output não existe."""
    
    client, _, mock_get_all, _ = mock_mem0_client
    
    # Mock de listas vazias
    mock_get_all.return_value = []
    
    # Recuperar
    result = client.get_tool_output("client_123", "SWOT")
    
    # Validar
    assert result is None


def test_get_tool_output_wrong_tool_name(mock_mem0_client, sample_swot_output):
    """Testa recuperação quando tool_name não corresponde."""
    
    client, _, mock_get_all, _ = mock_mem0_client
    
    # Mock de memória com tool_name diferente
    mock_memory = {
        "id": "memory_123",
        "metadata": {
            "tool_output_data": sample_swot_output.model_dump(),
            "tool_name": "SWOT",
            "report_type": "tool_output_swot"
        }
    }
    mock_get_all.return_value = [mock_memory]
    
    # Tentar recuperar com tool_name diferente
    result = client.get_tool_output("client_123", "KPI_DEFINER")
    
    # Validar
    assert result is None


def test_get_tool_output_multiple_outputs_same_client(mock_mem0_client):
    """Testa recuperação quando múltiplos outputs existem para mesmo client."""
    
    client, _, mock_get_all, _ = mock_mem0_client
    
    # Mock de múltiplas memórias
    mock_memories = [
        {
            "id": "memory_1",
            "metadata": {"tool_output_data": {"strengths": ["A"]}, "tool_name": "SWOT"}
        },
        {
            "id": "memory_2",
            "metadata": {"tool_output_data": {"kpis": ["B"]}, "tool_name": "KPI_DEFINER"}
        }
    ]
    mock_get_all.return_value = mock_memories
    
    # Recuperar SWOT
    result = client.get_tool_output("client_123", "SWOT")
    
    # Validar
    assert result is not None
    assert "strengths" in str(result)
    assert "kpis" not in str(result)


# ============================================================================
# TESTES: Automatic Cleanup (Edge Cases)
# ============================================================================


def test_save_deletes_old_output_same_tool(mock_mem0_client, sample_swot_output):
    """Testa que save_tool_output deleta output antigo da mesma ferramenta."""
    
    client, mock_add, mock_get_all, mock_delete = mock_mem0_client
    
    # Mock de memória antiga (output anterior)
    old_memory = {
        "id": "memory_old_123",
        "user_id": "client_123",
        "metadata": {
            "tool_output_data": {"strengths": ["Old strength"]},
            "tool_name": "SWOT",
            "report_type": "tool_output_swot"
        }
    }
    mock_get_all.return_value = [old_memory]
    
    # Criar novo ToolOutput
    new_tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump()
    )
    
    # Salvar (deve deletar output antigo)
    client.save_tool_output("client_123", new_tool_output)
    
    # Validar que delete() foi chamado
    assert mock_delete.called
    assert mock_delete.call_args[0][0] == "memory_old_123"


def test_save_not_delete_different_tool(mock_mem0_client, sample_swot_output, sample_kpi_framework):
    """Testa que save_tool_output NÃO deleta outputs de outras ferramentas."""
    
    client, mock_add, mock_get_all, mock_delete = mock_mem0_client
    
    # Mock de múltiplas memórias (SWOT e KPI)
    mock_memories = [
        {
            "id": "memory_swot",
            "metadata": {"tool_output_data": {"old": "data"}, "tool_name": "SWOT"}
        },
        {
            "id": "memory_kpi",
            "metadata": {"tool_output_data": {"kpis": ["B"]}, "tool_name": "KPI_DEFINER"}
        }
    ]
    mock_get_all.return_value = mock_memories
    
    # Salvar novo SWOT (deve deletar apenas memory_swot, não memory_kpi)
    new_tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump()
    )
    
    client.save_tool_output("client_123", new_tool_output)
    
    # Validar que delete foi chamado apenas 1 vez (apenas SWOT antigo)
    assert mock_delete.call_count == 1
    
    # Validar que foi deletado o memory_swot
    assert mock_delete.call_args[0][0] == "memory_swot"


# ============================================================================
# TESTES: Validações de Erro
# ============================================================================


def test_save_tool_output_invalid_tool_output(mock_mem0_client):
    """Testa que save_tool_output valida que é ToolOutput válido."""
    
    client, _, _, _ = mock_mem0_client
    
    # Tentar salvar objeto inválido
    with pytest.raises(ValueError, match="tool_output deve ser uma instância de ToolOutput"):
        client.save_tool_output("client_123", "not a ToolOutput")


def test_save_tool_output_empty_client_context(mock_mem0_client, sample_swot_output):
    """Testa que save_tool_output funciona mesmo sem client_context."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Criar ToolOutput sem client_context
    tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump(),
        client_context=None
    )
    
    # Salvar (deve funcionar)
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar
    assert result == "client_123"
    assert mock_add.called


# ============================================================================
# TESTES: Retry Logic (Network Failures)
# ============================================================================


def test_save_tool_output_with_connection_error(mock_mem0_client, sample_swot_output):
    """Testa que save_tool_output retry em ConnectionError."""
    
    client, mock_add, _, _ = mock_mem0_client
    
    # Mock para lançar ConnectionError 2x, depois sucesso
    mock_add.side_effect = [
        ConnectionError("Network error"),
        ConnectionError("Network error again"),
        {"id": "memory_123"}
    ]
    
    # Criar ToolOutput
    tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump()
    )
    
    # Salvar (deve retry e eventualmente funcionar)
    result = client.save_tool_output("client_123", tool_output)
    
    # Validar que add foi chamado 3 vezes (2 retries + 1 sucesso)
    assert mock_add.call_count == 3
    assert result == "client_123"


def test_get_tool_output_with_timeout_error(mock_mem0_client):
    """Testa que get_tool_output retry em TimeoutError."""
    
    client, _, mock_get_all, _ = mock_mem0_client
    
    # Mock para lançar TimeoutError 2x, depois retornar dados
    mock_get_all.side_effect = [
        TimeoutError("Timeout error"),
        TimeoutError("Timeout error again"),
        []
    ]
    
    # Recuperar (deve retry e eventualmente retornar None)
    result = client.get_tool_output("client_123", "SWOT")
    
    # Validar que get_all foi chamado 3 vezes
    assert mock_get_all.call_count == 3
    assert result is None


# ============================================================================
# TESTES: Integration (Save + Get)
# ============================================================================


def test_save_and_get_swot_output(mock_mem0_client, sample_swot_output):
    """Testa integração completa: salvar e recuperar SWOT."""
    
    client, mock_add, mock_get_all, _ = mock_mem0_client
    
    # STEP 1: Salvar
    tool_output = ToolOutput(
        tool_name="SWOT",
        tool_output_data=sample_swot_output.model_dump(),
        client_context="TechCorp"
    )
    
    saved_id = client.save_tool_output("client_123", tool_output)
    assert saved_id == "client_123"
    
    # STEP 2: Mock get_all para retornar memória salva
    mock_get_all.return_value = [
        {
            "id": "memory_123",
            "metadata": {
                "tool_output_data": sample_swot_output.model_dump(),
                "tool_name": "SWOT",
                "report_type": "tool_output_swot"
            }
        }
    ]
    
    # STEP 3: Recuperar
    retrieved = client.get_tool_output("client_123", "SWOT")
    
    # Validar
    assert retrieved is not None
    assert "strengths" in str(retrieved)
    assert "weaknesses" in str(retrieved)
    assert len(retrieved["strengths"]) >= 2
    assert len(retrieved["weaknesses"]) >= 2


def test_save_and_get_five_whys_output(mock_mem0_client, sample_five_whys_output):
    """Testa integração completa: salvar e recuperar Five Whys."""
    
    client, mock_add, mock_get_all, _ = mock_mem0_client
    
    # STEP 1: Salvar
    tool_output = ToolOutput(
        tool_name="FIVE_WHYS",
        tool_output_data=sample_five_whys_output.model_dump()
    )
    
    saved_id = client.save_tool_output("client_123", tool_output)
    assert saved_id == "client_123"
    
    # STEP 2: Mock get_all
    mock_get_all.return_value = [
        {
            "id": "memory_123",
            "metadata": {
                "tool_output_data": sample_five_whys_output.model_dump(),
                "tool_name": "FIVE_WHYS"
            }
        }
    ]
    
    # STEP 3: Recuperar
    retrieved = client.get_tool_output("client_123", "FIVE_WHYS")
    
    # Validar
    assert retrieved is not None
    assert "problem_statement" in str(retrieved)
    assert "iterations" in str(retrieved)
    assert retrieved["problem_statement"] == "Alta rotatividade de funcionários (turnover 40%)"
    assert len(retrieved["iterations"]) >= 2

