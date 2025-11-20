"""Dashboard de Analytics para monitoramento da API REST.

Este componente exibe métricas coletadas pelo AnalyticsMiddleware:
- KPIs principais (total requests, error rate, latency, active API keys)
- Gráficos de tráfego (time-series)
- Métricas de performance (latência por endpoint)
- Taxa de erros por endpoint
- Top consumers (API keys)
- Métricas detalhadas por endpoint

Fase: 4.4 - Advanced Analytics Dashboard
"""

import logging
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

# Adicionar diretório raiz ao path para imports
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))


logger = logging.getLogger(__name__)

# URL base da API
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "bsc_test_valid"  # Mock API key para desenvolvimento


def _make_api_request(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Faz requisição HTTP para API de analytics.

    Args:
        endpoint: Endpoint da API (ex: /analytics/overview)
        params: Parâmetros de query (opcional)

    Returns:
        Dict com dados da resposta JSON

    Raises:
        Exception: Se requisição falhar
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"X-API-Key": API_KEY}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"[ANALYTICS] Erro ao buscar {endpoint}: {e}")
        st.error(f"Erro ao conectar com API: {e}")
        return {}


def render_analytics_dashboard() -> None:
    """Renderiza dashboard completo de analytics.

    Componente principal que exibe todas as métricas coletadas
    pela API REST em formato visual interativo.
    """
    # Injetar CSS customizado
    _inject_custom_css()

    st.title("Analytics Dashboard")
    st.markdown("Monitoramento em tempo real da API REST BSC")

    # Filtros globais
    col1, col2, col3 = st.columns(3)

    with col1:
        period = st.selectbox(
            "Período",
            options=["1h", "24h", "7d", "30d"],
            index=1,  # Default: 24h
            key="analytics_period",
        )

    with col2:
        endpoint_filter = st.selectbox(
            "Endpoint", options=["Todos"] + _get_all_endpoints(), index=0, key="analytics_endpoint"
        )

    with col3:
        refresh_btn = st.button("Atualizar", type="primary", use_container_width=True)

    st.markdown("---")

    # Seção 1: Overview KPIs
    _render_overview_kpis(period)

    st.markdown("---")

    # Seção 2: Traffic Chart
    _render_traffic_chart(period, endpoint_filter if endpoint_filter != "Todos" else None)

    st.markdown("---")

    # Seção 3: Performance Chart
    _render_performance_chart(period)

    st.markdown("---")

    # Seção 4: Errors Chart
    _render_errors_chart(period)

    st.markdown("---")

    # Seção 5: Consumers Table
    _render_consumers_table(period)

    st.markdown("---")

    # Seção 6: Endpoints Table
    _render_endpoints_table(period)


def _render_overview_kpis(period: str) -> None:
    """Renderiza KPIs principais (4 métricas)."""
    st.subheader("Overview - KPIs Principais")

    with st.spinner("Carregando métricas..."):
        data = _make_api_request("/analytics/overview", params={"period": period})

    if not data:
        st.warning("Não foi possível carregar métricas. Verifique se a API está rodando.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Requests",
            f"{data.get('total_requests', 0):,}",
            help="Total de requests HTTP no período selecionado",
        )

    with col2:
        error_rate = data.get("error_rate", 0.0)
        error_rate_pct = error_rate * 100
        st.metric(
            "Taxa de Erros",
            f"{error_rate_pct:.2f}%",
            delta=f"{error_rate_pct:.2f}%" if error_rate > 0 else None,
            delta_color="inverse",
            help="Percentual de requests com erro (4xx ou 5xx)",
        )

    with col3:
        avg_latency = data.get("avg_latency_ms", 0.0)
        st.metric(
            "Latência Média",
            f"{avg_latency:.0f}ms",
            help="Latência média de resposta em milissegundos",
        )

    with col4:
        active_keys = data.get("active_api_keys", 0)
        st.metric(
            "API Keys Ativas",
            active_keys,
            help="Número de API keys que fizeram requests no período",
        )


def _render_traffic_chart(period: str, endpoint: str | None = None) -> None:
    """Renderiza gráfico de tráfego (requests/min)."""
    st.subheader("Tráfego - Requests ao Longo do Tempo")

    # Determinar intervalo baseado no período
    if period == "1h" or period == "24h":
        interval = "minute"
    elif period == "7d":
        interval = "hour"
    else:  # 30d
        interval = "day"

    with st.spinner("Carregando dados de tráfego..."):
        params = {"period": period, "interval": interval}
        if endpoint:
            params["endpoint"] = endpoint

        data = _make_api_request("/analytics/traffic", params=params)

    if not data or not data.get("data"):
        st.info("Nenhum dado de tráfego disponível para o período selecionado.")
        return

    # Preparar dados para gráfico
    traffic_data = data.get("data", [])

    if not traffic_data:
        st.info("Nenhum dado de tráfego disponível.")
        return

    # Criar DataFrame para gráfico
    import pandas as pd

    df = pd.DataFrame(traffic_data)

    # Converter timestamp para datetime se necessário
    if "timestamp" in df.columns:
        # Formato esperado: "2025-11-19:10:00" ou "2025-11-19:10" ou "2025-11-19"
        try:
            if ":" in df["timestamp"].iloc[0] and df["timestamp"].iloc[0].count(":") == 2:
                df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d:%H:%M")
            elif ":" in df["timestamp"].iloc[0]:
                df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d:%H")
            else:
                df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d")
        except:
            pass

    # Gráfico de linha
    st.line_chart(df.set_index("timestamp")[["count", "errors"]], use_container_width=True)

    # Estatísticas resumidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", f"{df['count'].sum():,}")
    with col2:
        st.metric("Total Erros", f"{df['errors'].sum():,}")
    with col3:
        st.metric("Pico de Requests", f"{df['count'].max():,}")


def _render_performance_chart(period: str) -> None:
    """Renderiza gráfico de performance (latência por endpoint)."""
    st.subheader("Performance - Latência por Endpoint")

    with st.spinner("Carregando métricas de performance..."):
        endpoints_data = _make_api_request(
            "/analytics/endpoints", params={"metric": "latency", "limit": 10, "period": period}
        )

    if not endpoints_data:
        st.info("Nenhum dado de performance disponível.")
        return

    # Filtrar apenas endpoints com dados de latência
    endpoints_with_latency = [e for e in endpoints_data if e.get("latency_p50") is not None]

    if not endpoints_with_latency:
        st.info("Nenhum endpoint com dados de latência disponível.")
        return

    # Criar DataFrame
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "endpoint": e["endpoint"],
                "P50": e.get("latency_p50", 0),
                "P95": e.get("latency_p95", 0),
                "P99": e.get("latency_p99", 0),
            }
            for e in endpoints_with_latency[:10]  # Top 10
        ]
    )

    # Gráfico de barras
    st.bar_chart(df.set_index("endpoint")[["P50", "P95", "P99"]], use_container_width=True)

    # Tabela detalhada
    with st.expander("Ver detalhes de latência"):
        st.dataframe(df, use_container_width=True)


def _render_errors_chart(period: str) -> None:
    """Renderiza gráfico de erros por endpoint."""
    st.subheader("Erros - Taxa de Erros por Endpoint")

    with st.spinner("Carregando métricas de erros..."):
        errors_data = _make_api_request("/analytics/errors", params={"period": period})

    if not errors_data:
        st.info("Nenhum dado de erros disponível.")
        return

    # Filtrar apenas endpoints com erros
    endpoints_with_errors = [e for e in errors_data if e.get("errors", 0) > 0]

    if not endpoints_with_errors:
        st.success("Nenhum erro registrado no período selecionado!")
        return

    # Criar DataFrame
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "endpoint": e["endpoint"],
                "Taxa de Erro (%)": e.get("error_rate", 0) * 100,
                "Total Erros": e.get("errors", 0),
                "Total Requests": e.get("total_requests", 0),
            }
            for e in sorted(
                endpoints_with_errors, key=lambda x: x.get("error_rate", 0), reverse=True
            )[:10]
        ]
    )

    # Gráfico de barras
    st.bar_chart(df.set_index("endpoint")[["Taxa de Erro (%)"]], use_container_width=True)

    # Tabela detalhada
    with st.expander("Ver detalhes de erros"):
        st.dataframe(df, use_container_width=True)


def _render_consumers_table(period: str) -> None:
    """Renderiza tabela de top consumers (API keys)."""
    st.subheader("Consumers - Top API Keys por Volume")

    with st.spinner("Carregando dados de consumers..."):
        consumers_data = _make_api_request(
            "/analytics/consumers", params={"limit": 10, "period": period}
        )

    if not consumers_data:
        st.info("Nenhum dado de consumers disponível.")
        return

    # Criar DataFrame
    import pandas as pd

    df = pd.DataFrame(consumers_data)

    # Renomear colunas para português
    df = df.rename(
        columns={
            "api_key": "API Key",
            "requests": "Total Requests",
            "unique_endpoints": "Endpoints Únicos",
            "last_request": "Última Requisição",
        }
    )

    # Exibir tabela
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_endpoints_table(period: str) -> None:
    """Renderiza tabela de métricas por endpoint."""
    st.subheader("Endpoints - Métricas Detalhadas")

    with st.spinner("Carregando métricas de endpoints..."):
        endpoints_data = _make_api_request(
            "/analytics/endpoints", params={"metric": "requests", "limit": 20, "period": period}
        )

    if not endpoints_data:
        st.info("Nenhum dado de endpoints disponível.")
        return

    # Criar DataFrame
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "Endpoint": e["endpoint"],
                "Requests": e.get("requests", 0),
                "Erros": e.get("errors", 0),
                "Taxa Erro (%)": f"{e.get('error_rate', 0) * 100:.2f}",
                "Latência P50 (ms)": (
                    f"{e.get('latency_p50', 0):.0f}" if e.get("latency_p50") else "N/A"
                ),
                "Latência P95 (ms)": (
                    f"{e.get('latency_p95', 0):.0f}" if e.get("latency_p95") else "N/A"
                ),
                "Latência P99 (ms)": (
                    f"{e.get('latency_p99', 0):.0f}" if e.get("latency_p99") else "N/A"
                ),
            }
            for e in endpoints_data
        ]
    )

    # Exibir tabela
    st.dataframe(df, use_container_width=True, hide_index=True)


def _get_all_endpoints() -> list[str]:
    """Retorna lista de todos os endpoints disponíveis.

    Returns:
        Lista de endpoints únicos
    """
    # Buscar endpoints únicos da API
    try:
        endpoints_data = _make_api_request(
            "/analytics/endpoints", params={"limit": 100, "period": "24h"}
        )
        if endpoints_data:
            return [e["endpoint"] for e in endpoints_data]
    except:
        pass

    # Fallback: lista hardcoded de endpoints conhecidos
    return [
        "/api/v1/clients",
        "/api/v1/diagnostics",
        "/api/v1/tools/swot",
        "/api/v1/tools/five-whys",
        "/api/v1/reports/pdf/diagnostic",
    ]


def _inject_custom_css() -> None:
    """Injeta CSS customizado para melhorar visual do dashboard."""
    st.markdown(
        """
    <style>
    /* Métricas do header */
    div[data-testid="metric-container"] {
        background: #f8f9fb;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #4285f4;
    }

    /* Títulos das seções */
    h3 {
        color: #1f1f1f;
        margin-bottom: 12px;
    }

    /* Espaçamento entre elementos */
    p {
        line-height: 1.6;
        margin-bottom: 8px;
    }

    /* Dividers */
    hr {
        margin: 16px 0;
        border: none;
        border-top: 1px solid #e8eaed;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
