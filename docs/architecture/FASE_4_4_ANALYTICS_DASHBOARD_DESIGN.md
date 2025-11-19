# FASE 4.4 - Advanced Analytics Dashboard: Design Técnico

**Data Início:** 2025-11-19  
**Versão:** 1.0  
**Status:** 📐 DESIGN APROVADO - Pronto para implementação

---

## 🎯 Objetivos

Implementar dashboard de analytics enterprise-ready para monitoramento da API REST (FASE 4.3):

1. **Coleta Automática de Métricas** - Middleware FastAPI que intercepta todos os requests
2. **Armazenamento Time-Series** - Redis para métricas históricas (últimos 30 dias)
3. **Dashboard Interativo** - UI Streamlit com gráficos e KPIs em tempo real
4. **API de Métricas** - Endpoints REST para acesso programático aos dados
5. **Alertas e Notificações** - Thresholds configuráveis para métricas críticas

**Estimativa:** 4-5h (1 sessão)  
**Dependências:** FASE 4.3 completa (Integration APIs) ✅

---

## 📊 Stack Tecnológico (Decisões Fundamentadas - Brightdata Nov 2025)

### **1. Redis Time-Series para Métricas**

**Escolha:** Redis Hash Sets com timestamps como keys  
**Alternativas consideradas:** Prometheus, InfluxDB, TimescaleDB

**Razões:**
- ✅ **Já temos Redis:** Reutilizar infraestrutura existente (rate limiting FASE 4.3)
- ✅ **Performance:** Redis é extremamente rápido para writes/reads (<1ms latência)
- ✅ **Simplicidade:** Sem dependências externas adicionais
- ✅ **Suficiente para MVP:** <1M métricas/dia (Redis suporta milhões)

**Estrutura Redis proposta:**
```
# Requests por endpoint (minuto)
metrics:requests:/api/v1/clients:2025-11-19:10:00 → {"count": 45, "errors": 2}

# Latência por endpoint (minuto)
metrics:latency:/api/v1/clients:2025-11-19:10:00 → {"p50": 120, "p95": 250, "p99": 500}

# Uso por API key (hora)
metrics:consumer:bsc_test_engelar:2025-11-19:10 → {"requests": 150, "endpoints": 5}

# Rate limit hits (dia)
metrics:ratelimit:2025-11-19 → {"hits": 12, "endpoints": ["/api/v1/clients"]}
```

**Fontes:**
- Redis.io (2025): "Time-Series Data Structures Best Practices"
- Medium (Aug 2025): "Building Event-Driven Notification with FastAPI and Webhooks"

---

### **2. Middleware FastAPI para Coleta**

**Escolha:** Custom ASGI middleware  
**Alternativas consideradas:** Prometheus client, OpenTelemetry

**Razões:**
- ✅ **Controle total:** Coletar exatamente as métricas que precisamos
- ✅ **Performance:** Middleware async nativo (zero overhead)
- ✅ **Integração perfeita:** Acesso a request/response objects completos
- ✅ **Customização:** Fácil adicionar novas métricas no futuro

**Implementação proposta:**
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Executar request
        response = await call_next(request)
        
        # Calcular latência
        latency_ms = (time.time() - start_time) * 1000
        
        # Coletar métricas
        await self._record_metrics(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
            api_key=self._extract_api_key(request)
        )
        
        return response
```

**Fontes:**
- FastAPI Docs (2025): "Custom Middleware"
- TokenMetrics (2025): "FastAPI High Performance & Best Practices"

---

### **3. Dashboard Streamlit**

**Escolha:** Streamlit (já usado no projeto)  
**Alternativas consideradas:** Grafana, Plotly Dash, React

**Razões:**
- ✅ **Já integrado:** Projeto já usa Streamlit (app/main.py)
- ✅ **Rápido desenvolvimento:** Dashboard em 1-2h vs 8-12h React
- ✅ **Python nativo:** Mesma stack do projeto (sem JavaScript)
- ✅ **Gráficos nativos:** st.line_chart, st.bar_chart, st.metric

**Componentes do Dashboard:**
1. **Overview KPIs** - Total requests, taxa de erros, latência média
2. **Traffic Chart** - Requests/min ao longo do tempo (line chart)
3. **Performance Chart** - Latência P50/P95/P99 por endpoint (bar chart)
4. **Errors Chart** - Taxa de erros 4xx/5xx por endpoint
5. **Consumers Table** - Top 10 API keys por volume de requests
6. **Endpoints Table** - Top endpoints por volume, latência, erros

**Fontes:**
- Streamlit Docs (2025): "Building Dashboards"
- Medium (Oct 2025): "Streamlit Analytics Dashboard Best Practices"

---

## 🏗️ Arquitetura Completa

### **Fluxo de Dados**

```
┌─────────────────┐
│  FastAPI App    │
│  (31 endpoints) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analytics       │
│ Middleware      │ ◄─── Intercepta TODOS requests
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MetricsService  │ ◄─── Armazena em Redis (time-series)
│ (Redis)         │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ API     │ │ Dashboard    │
│ Endpoints│ │ Streamlit    │ ◄─── Consome dados do Redis
│ /metrics│ │ /analytics   │
└─────────┘ └──────────────┘
```

---

### **Componentes Principais**

**1. `api/middleware/analytics.py`** (150 linhas)
- Classe `AnalyticsMiddleware` (BaseHTTPMiddleware)
- Coleta: endpoint, method, status_code, latency, api_key, timestamp
- Chama `MetricsService.record_request()` assíncrono

**2. `api/services/metrics_service.py`** (300 linhas)
- Classe `MetricsService` (Redis client)
- Métodos:
  - `record_request()` - Armazena métrica em Redis
  - `get_requests_by_endpoint()` - Agrega requests por endpoint (intervalo)
  - `get_latency_percentiles()` - Calcula P50/P95/P99
  - `get_errors_by_endpoint()` - Conta erros 4xx/5xx
  - `get_top_consumers()` - Top API keys por volume
  - `get_top_endpoints()` - Top endpoints por volume/latência

**3. `api/routers/analytics.py`** (200 linhas)
- Endpoints REST para métricas:
  - `GET /api/v1/analytics/overview` - KPIs principais
  - `GET /api/v1/analytics/traffic` - Requests/min (time-series)
  - `GET /api/v1/analytics/performance` - Latência por endpoint
  - `GET /api/v1/analytics/errors` - Taxa de erros
  - `GET /api/v1/analytics/consumers` - Uso por API key
  - `GET /api/v1/analytics/endpoints` - Métricas por endpoint

**4. `app/pages/analytics.py`** (400 linhas)
- Dashboard Streamlit completo
- 6 seções com gráficos interativos
- Filtros: período, endpoint, API key

**5. `tests/test_api/test_analytics.py`** (250 linhas)
- Testes unitários: MetricsService
- Testes E2E: Middleware coleta métricas
- Testes E2E: Endpoints retornam dados corretos

---

## 📈 Métricas a Coletar

### **1. Requests (Volume)**

**O que coletar:**
- Total de requests por minuto/hora/dia
- Requests por endpoint (path)
- Requests por método HTTP (GET, POST, etc)
- Requests por API key (cliente)

**Estrutura Redis:**
```
metrics:requests:{endpoint}:{timestamp} → {"count": 45, "errors": 2}
metrics:requests:total:{timestamp} → {"count": 1200}
metrics:requests:consumer:{api_key}:{timestamp} → {"count": 150}
```

**Uso:** Gráfico de tráfego ao longo do tempo, identificar picos, tendências

---

### **2. Latência (Performance)**

**O que coletar:**
- Latência por endpoint (milissegundos)
- Percentis: P50 (mediana), P95, P99
- Latência média por endpoint

**Estrutura Redis:**
```
metrics:latency:{endpoint}:{timestamp} → {
  "p50": 120,
  "p95": 250,
  "p99": 500,
  "mean": 135,
  "max": 1200,
  "samples": 45
}
```

**Cálculo de percentis:**
- Armazenar todas latências em lista Redis (sorted set)
- Calcular percentis via Redis ZRANGE (O(log N))

**Uso:** Identificar endpoints lentos, detectar degradação de performance

---

### **3. Erros (Reliability)**

**O que coletar:**
- Total de erros por endpoint
- Breakdown por status code (4xx vs 5xx)
- Taxa de erro (erros / total requests)

**Estrutura Redis:**
```
metrics:errors:{endpoint}:{timestamp} → {
  "4xx": 2,
  "5xx": 0,
  "total": 2,
  "rate": 0.044  // 2/45 = 4.4%
}
```

**Uso:** Alertas quando taxa de erro > 5%, identificar endpoints problemáticos

---

### **4. Uso por Cliente (Consumers)**

**O que coletar:**
- Total de requests por API key
- Endpoints mais usados por cliente
- Distribuição de uso ao longo do tempo

**Estrutura Redis:**
```
metrics:consumer:{api_key}:{timestamp} → {
  "requests": 150,
  "endpoints": ["/api/v1/clients", "/api/v1/tools/swot"],
  "unique_endpoints": 5
}
```

**Uso:** Identificar clientes mais ativos, detectar uso anormal

---

### **5. Rate Limit Hits**

**O que coletar:**
- Total de rate limit hits por dia
- Endpoints mais afetados
- API keys que mais excedem limites

**Estrutura Redis:**
```
metrics:ratelimit:{date} → {
  "hits": 12,
  "endpoints": ["/api/v1/clients"],
  "consumers": ["bsc_test_user1"]
}
```

**Uso:** Identificar necessidade de ajustar limites, detectar abuso

---

### **6. Webhook Deliveries**

**O que coletar:**
- Total de webhooks enviados
- Taxa de sucesso vs falha
- Latência de entrega

**Estrutura Redis:**
```
metrics:webhooks:{date} → {
  "total": 50,
  "success": 48,
  "failed": 2,
  "success_rate": 0.96,
  "avg_latency_ms": 250
}
```

**Uso:** Monitorar saúde do sistema de webhooks, detectar problemas de entrega

---

## 🔧 Estrutura Redis Detalhada

### **Keys Pattern**

**Formato geral:**
```
metrics:{metric_type}:{dimension}:{timestamp}
```

**Exemplos:**
```
# Requests por endpoint (minuto)
metrics:requests:/api/v1/clients:2025-11-19:10:00

# Latência por endpoint (minuto)
metrics:latency:/api/v1/clients:2025-11-19:10:00

# Uso por API key (hora)
metrics:consumer:bsc_test_engelar:2025-11-19:10

# Rate limit hits (dia)
metrics:ratelimit:2025-11-19

# Webhooks (dia)
metrics:webhooks:2025-11-19
```

### **Valores (JSON)**

**Requests:**
```json
{
  "count": 45,
  "errors": 2,
  "methods": {"GET": 30, "POST": 15}
}
```

**Latência:**
```json
{
  "p50": 120,
  "p95": 250,
  "p99": 500,
  "mean": 135,
  "max": 1200,
  "samples": 45
}
```

**Consumer:**
```json
{
  "requests": 150,
  "endpoints": ["/api/v1/clients", "/api/v1/tools/swot"],
  "unique_endpoints": 5
}
```

### **TTL (Time To Live)**

**Retenção de dados:**
- **Minutos:** 7 dias (métricas detalhadas)
- **Horas:** 30 dias (agregações)
- **Dias:** 90 dias (tendências longas)

**Implementação:**
```python
# Ao armazenar métrica
await redis.setex(
    key,
    ttl=7 * 24 * 60 * 60,  # 7 dias em segundos
    value=json.dumps(data)
)
```

---

## 📱 Dashboard Streamlit - Layout Detalhado

### **Seção 1: Overview KPIs**

**4 métricas principais:**
- **Total Requests (hoje)** - Contador grande
- **Taxa de Erros (%)** - Com delta vs ontem
- **Latência Média (ms)** - Com delta vs ontem
- **API Keys Ativas** - Contador

**Layout:**
```python
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Requests", "12,450", delta="+5.2%")
with col2:
    st.metric("Taxa de Erros", "2.1%", delta="-0.3%")
with col3:
    st.metric("Latência Média", "145ms", delta="+12ms")
with col4:
    st.metric("API Keys Ativas", "23")
```

---

### **Seção 2: Traffic Chart**

**Gráfico:** Line chart (requests/min ao longo do tempo)

**Filtros:**
- Período: Última hora / Dia / Semana / Mês
- Endpoint específico (opcional)

**Dados:**
```python
# Agregar requests por minuto
data = metrics_service.get_requests_by_endpoint(
    endpoint="/api/v1/clients",
    start_time=datetime.now() - timedelta(hours=24),
    interval="minute"
)

# Plotar
st.line_chart(data, x="timestamp", y="count")
```

---

### **Seção 3: Performance Chart**

**Gráfico:** Bar chart (latência P50/P95/P99 por endpoint)

**Dados:**
```python
# Top 10 endpoints por latência média
endpoints = metrics_service.get_top_endpoints(
    metric="latency",
    limit=10,
    period="24h"
)

# Plotar
st.bar_chart(endpoints, x="endpoint", y=["p50", "p95", "p99"])
```

---

### **Seção 4: Errors Chart**

**Gráfico:** Bar chart (taxa de erros por endpoint)

**Dados:**
```python
# Taxa de erros por endpoint
errors = metrics_service.get_errors_by_endpoint(
    period="24h"
)

# Plotar
st.bar_chart(errors, x="endpoint", y="error_rate")
```

---

### **Seção 5: Consumers Table**

**Tabela:** Top 10 API keys por volume de requests

**Colunas:**
- API Key (mascarado: `bsc_test_***`)
- Total Requests
- Endpoints Únicos
- Última Requisição

**Dados:**
```python
consumers = metrics_service.get_top_consumers(
    limit=10,
    period="24h"
)

st.dataframe(consumers)
```

---

### **Seção 6: Endpoints Table**

**Tabela:** Métricas detalhadas por endpoint

**Colunas:**
- Endpoint
- Total Requests
- Latência P50/P95/P99
- Taxa de Erros
- Método HTTP Mais Usado

**Dados:**
```python
endpoints = metrics_service.get_endpoints_metrics(
    period="24h"
)

st.dataframe(endpoints)
```

---

## 🚀 Plano de Implementação (5 Etapas)

### **Etapa 1: Middleware de Analytics** (1h)

**Objetivo:** Criar middleware que intercepta requests e coleta métricas básicas

**Arquivos:**
- `api/middleware/__init__.py`
- `api/middleware/analytics.py`

**Implementação:**
1. Criar classe `AnalyticsMiddleware` (BaseHTTPMiddleware)
2. Interceptar request/response
3. Calcular latência
4. Extrair API key do header
5. Chamar `MetricsService.record_request()` (mock inicial)

**Validação:**
- Middleware registrado no FastAPI app
- Logs mostram métricas coletadas
- Zero impacto na performance (<1ms overhead)

---

### **Etapa 2: MetricsService (Redis)** (1h 30min)

**Objetivo:** Implementar serviço completo de armazenamento/recuperação de métricas

**Arquivos:**
- `api/services/metrics_service.py`

**Implementação:**
1. Classe `MetricsService` com Redis client
2. Método `record_request()` - Armazenar em Redis
3. Método `get_requests_by_endpoint()` - Agregar por intervalo
4. Método `get_latency_percentiles()` - Calcular P50/P95/P99
5. Método `get_errors_by_endpoint()` - Contar erros
6. Método `get_top_consumers()` - Top API keys
7. Método `get_top_endpoints()` - Top endpoints

**Validação:**
- Métricas armazenadas corretamente em Redis
- Queries retornam dados agregados corretos
- TTL configurado (7 dias minutos, 30 dias horas)

---

### **Etapa 3: Endpoints API** (1h)

**Objetivo:** Criar endpoints REST para acesso programático às métricas

**Arquivos:**
- `api/routers/analytics.py`

**Endpoints:**
- `GET /api/v1/analytics/overview` - KPIs principais
- `GET /api/v1/analytics/traffic` - Requests/min (time-series)
- `GET /api/v1/analytics/performance` - Latência por endpoint
- `GET /api/v1/analytics/errors` - Taxa de erros
- `GET /api/v1/analytics/consumers` - Uso por API key
- `GET /api/v1/analytics/endpoints` - Métricas por endpoint

**Validação:**
- Endpoints retornam JSON válido
- Filtros funcionam (período, endpoint, API key)
- Autenticação requerida (API key)

---

### **Etapa 4: Dashboard Streamlit** (1h 30min)

**Objetivo:** Criar UI interativa com gráficos e tabelas

**Arquivos:**
- `app/pages/analytics.py`

**Implementação:**
1. Seção Overview (4 KPIs)
2. Seção Traffic Chart (line chart)
3. Seção Performance Chart (bar chart)
4. Seção Errors Chart (bar chart)
5. Seção Consumers Table (dataframe)
6. Seção Endpoints Table (dataframe)
7. Filtros (período, endpoint, API key)

**Validação:**
- Dashboard carrega sem erros
- Gráficos exibem dados corretos
- Filtros funcionam
- UI responsiva e profissional

---

### **Etapa 5: Testes** (30min)

**Objetivo:** Validar implementação completa com testes

**Arquivos:**
- `tests/test_api/test_analytics_middleware.py`
- `tests/test_api/test_metrics_service.py`
- `tests/test_api/test_analytics_endpoints.py`

**Testes:**
- Unitários: MetricsService (10 testes)
- E2E: Middleware coleta métricas (3 testes)
- E2E: Endpoints retornam dados (6 testes)

**Validação:**
- 19 testes passando (100%)
- Coverage >80%

---

## 📖 Referências (Brightdata Nov 2025)

### **FastAPI Middleware:**
1. **FastAPI Docs (2025):** "Custom Middleware"
   - BaseHTTPMiddleware, ASGI middleware patterns
2. **TokenMetrics (2025):** "FastAPI High Performance & Best Practices"
   - Middleware performance, async patterns

### **Redis Time-Series:**
3. **Redis.io (2025):** "Time-Series Data Structures Best Practices"
   - Hash sets, sorted sets, TTL strategies
4. **Medium (Aug 2025):** "Building Event-Driven Notification with FastAPI and Webhooks"
   - Redis patterns para métricas

### **Streamlit Dashboards:**
5. **Streamlit Docs (2025):** "Building Dashboards"
   - Charts, metrics, dataframes
6. **Medium (Oct 2025):** "Streamlit Analytics Dashboard Best Practices"
   - Layout, performance, UX

### **API Analytics:**
7. **Apitally.io (2025):** "API monitoring & analytics for FastAPI"
   - Métricas essenciais, KPIs, alertas
8. **Speakeasy (Sep 2025):** "Rate Limiting Best Practices in REST API Design"
   - Métricas de rate limiting

---

## 🎯 Próximas Etapas (Pós-FASE 4.4)

**Após FASE 4.4 completa, considerar:**
1. **Alertas Automáticos:** Email/Slack quando métricas excedem thresholds
2. **Export de Dados:** CSV/JSON para análise externa
3. **Comparação Períodos:** Comparar métricas semana vs semana
4. **Anomaly Detection:** Detectar padrões anormais automaticamente
5. **Integração Prometheus:** Expor métricas em formato Prometheus (opcional)

---

**Última Atualização:** 2025-11-19  
**Status:** 📐 DESIGN APROVADO - Pronto para implementação  
**Próximo:** Etapa 1 - Middleware de Analytics

