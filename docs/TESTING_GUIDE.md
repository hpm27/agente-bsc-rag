# Guia de Testes End-to-End - Agente BSC RAG

## [EMOJI] Visão Geral

Este guia detalha como executar e interpretar os **testes End-to-End (E2E)** do sistema Agente BSC RAG. Os testes validam o sistema completo funcionando de ponta a ponta, desde a ingestão de dados até a geração de respostas.

**Última atualização**: 14/10/2025

---

## [EMOJI] Objetivos dos Testes E2E

Os testes E2E validam:

1. **Fluxo Completo**: Ingestão -> Query -> Retrieval -> Agentes -> Synthesis -> Judge -> Resposta
2. **Performance**: Latência (P50/P95/P99), cache de embeddings, paralelização
3. **Qualidade**: Precisão de respostas, aprovação do Judge, scores de relevância
4. **Otimizações**: Cache 949x speedup, busca multilíngue +106% precisão, paralelização 3.34x
5. **Prontidão**: Qdrant UP, dataset indexado, API keys configuradas

---

## [EMOJI] Estrutura de Testes

### Arquivos

```
tests/integration/
├── test_e2e.py           # Suite principal de testes (550+ linhas)
└── test_queries.json     # Dataset de queries de teste (20 queries)
```

### Classes de Teste

| Classe | Testes | Foco |
|--------|--------|------|
| `TestE2EWorkflow` | 7 | Fluxo básico do workflow |
| `TestQueryScenarios` | 4 | Queries específicas por perspectiva |
| `TestPerformanceOptimizations` | 4 | Cache, paralelização, multilíngue |
| `TestJudgeValidation` | 2 | Validação do Judge Agent |
| `TestMetrics` | 2 | Latência P50/P95/P99, approval rate |
| `TestSystemReadiness` | 3 | Prerequisites (Qdrant, dataset, API keys) |
| **TOTAL** | **22 testes** | **Cobertura completa** |

---

## [EMOJI] Pré-requisitos

### 1. Sistema em Execução

Antes de executar os testes, certifique-se de que:

#### a) Docker Compose está rodando

```powershell
# Iniciar containers (Qdrant, Weaviate, Redis)
docker-compose up -d

# Verificar status
docker-compose ps
```

**Esperado**:
```
NAME                    STATUS
qdrant                  Up
weaviate                Up
redis                   Up
```

#### b) Dataset BSC está indexado

```powershell
# Indexar documentos BSC (se ainda não foi feito)
python scripts/build_knowledge_base.py
```

**Esperado**:
- Processamento de 5 livros BSC
- 7.965 chunks contextualizados indexados no Qdrant
- Tempo: ~10-15 minutos (primeira vez) ou ~10 segundos (com cache)

#### c) Variáveis de ambiente configuradas

Verificar arquivo `.env` na raiz do projeto:

```ini
# API Keys (OBRIGATÓRIAS)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...

# LLM Model
DEFAULT_LLM_MODEL=claude-sonnet-4-5-20250929

# Embedding Cache (RECOMENDADO)
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_DIR=.cache/embeddings

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=bsc_rag
```

### 2. Ambiente Python

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar dependências (se necessário)
pip install -r requirements.txt
```

---

## ▶ Executando Testes

### Executar Todos os Testes

```powershell
# Opção 1: Usando pytest diretamente
pytest tests/integration/test_e2e.py -v

# Opção 2: Com output detalhado
pytest tests/integration/test_e2e.py -v -s

# Opção 3: Com relatório HTML
pytest tests/integration/test_e2e.py -v --html=report.html --self-contained-html
```

### Executar Testes Específicos

#### Por Classe

```powershell
# Apenas testes de performance
pytest tests/integration/test_e2e.py::TestPerformanceOptimizations -v

# Apenas testes do Judge
pytest tests/integration/test_e2e.py::TestJudgeValidation -v

# Apenas testes de métricas
pytest tests/integration/test_e2e.py::TestMetrics -v

# Apenas testes de prontidão (rápidos)
pytest tests/integration/test_e2e.py::TestSystemReadiness -v
```

#### Por Teste Individual

```powershell
# Teste de cache de embeddings
pytest tests/integration/test_e2e.py::TestPerformanceOptimizations::test_embedding_cache_speedup -v

# Teste de latência P50/P95/P99
pytest tests/integration/test_e2e.py::TestMetrics::test_latency_percentiles -v

# Teste de busca multilíngue
pytest tests/integration/test_e2e.py::TestPerformanceOptimizations::test_multilingual_search_pt_br_query -v
```

#### Por Marker (se configurado)

```powershell
# Apenas testes rápidos
pytest tests/integration/test_e2e.py -m "not slow" -v

# Apenas testes lentos
pytest tests/integration/test_e2e.py -m "slow" -v
```

---

## [EMOJI] Interpretando Resultados

### Output Esperado

```
========================= test session starts =========================
collected 22 items

tests/integration/test_e2e.py::TestE2EWorkflow::test_simple_factual_query PASSED     [ 4%]
tests/integration/test_e2e.py::TestE2EWorkflow::test_conceptual_query PASSED        [ 9%]
tests/integration/test_e2e.py::TestE2EWorkflow::test_comparative_query PASSED       [13%]
tests/integration/test_e2e.py::TestE2EWorkflow::test_complex_query PASSED           [18%]
tests/integration/test_e2e.py::TestE2EWorkflow::test_workflow_latency PASSED        [22%]
tests/integration/test_e2e.py::TestE2EWorkflow::test_refinement_process PASSED      [27%]
tests/integration/test_e2e.py::TestE2EWorkflow::test_multiple_perspectives PASSED   [31%]
...
tests/integration/test_e2e.py::TestSystemReadiness::test_qdrant_connection PASSED   [95%]
tests/integration/test_e2e.py::TestSystemReadiness::test_dataset_indexed PASSED     [100%]

========================= 22 passed in 180.50s =========================
```

### Métricas Importantes

#### 1. Latência (P50/P95/P99)

```
[TEST METRICS LATENCY] Mean: 12.5s, P50: 11.2s, P95: 18.7s, P99: 22.3s
```

**Targets MVP**:
- P50 < 20s [OK]
- P95 < 30s [OK]
- P99 < 40s (aceitável)

#### 2. Cache de Embeddings

```
[TEST CACHE SPEEDUP] Sem cache: 3.721s, Com cache: 0.004s, Speedup: 930.3x
```

**Targets**:
- Speedup >= 10x (esperado: 100-1000x) [OK]
- Cache hit rate >= 80% [OK]

#### 3. Judge Approval Rate

```
[TEST METRICS JUDGE] Approval Rate: 83.3%, Avg Score: 0.82
```

**Targets**:
- Approval rate >= 70% [OK]
- Avg score >= 0.7 [OK]

#### 4. Busca Multilíngue

```
[TEST MULTILINGUAL] Query PT-BR recuperou 10 docs, 8 com score >0.7
```

**Target**:
- Pelo menos 50% dos docs com score >0.7 [OK]

#### 5. Paralelização de Agentes

```
[TEST PARALLEL] 4 perspectivas executadas em 14.2s
```

**Target**:
- <20s para 3+ perspectivas (vs ~30-40s sequencial) [OK]

---

## [WARN] Troubleshooting

### Problema 1: Qdrant não está rodando

**Erro**:
```
E   pytest.fail(f"Qdrant não está rodando ou inacessível: {e}")
```

**Solução**:
```powershell
# Verificar status do Docker
docker-compose ps

# Reiniciar containers
docker-compose restart

# Se necessário, rebuild
docker-compose down
docker-compose up -d
```

---

### Problema 2: Dataset não indexado

**Erro**:
```
E   AssertionError: Dataset muito pequeno: 0 chunks (esperado >=1000)
```

**Solução**:
```powershell
# Indexar dataset BSC
python scripts/build_knowledge_base.py

# Verificar indexação
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(host='localhost', port=6333)
info = client.get_collection('bsc_rag')
print(f'Chunks indexados: {info.points_count}')
"
```

**Esperado**: `Chunks indexados: 7965` (ou similar)

---

### Problema 3: API Keys inválidas

**Erro**:
```
E   AssertionError: OPENAI_API_KEY não configurada no .env
```

**Solução**:
1. Abrir `.env` na raiz do projeto
2. Configurar API keys válidas:

```ini
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
COHERE_API_KEY=...
```

3. Verificar configuração:

```powershell
python scripts/valida_env.py
```

---

### Problema 4: Testes lentos ou timeout

**Sintoma**: Testes demoram >5 minutos ou falham com timeout

**Causas possíveis**:
1. Rate limiting da API (muitas chamadas simultâneas)
2. Cache de embeddings desativado
3. Latência de rede alta

**Soluções**:

#### a) Ativar cache de embeddings

```ini
# .env
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_DIR=.cache/embeddings
```

#### b) Executar testes em grupos menores

```powershell
# Primeiro, testes rápidos (prerequisites)
pytest tests/integration/test_e2e.py::TestSystemReadiness -v

# Depois, testes básicos
pytest tests/integration/test_e2e.py::TestE2EWorkflow -v

# Por último, testes de métricas (lentos)
pytest tests/integration/test_e2e.py::TestMetrics -v
```

#### c) Ajustar timeout do pytest

```powershell
pytest tests/integration/test_e2e.py -v --timeout=300
```

---

### Problema 5: Testes falham com erros de import

**Erro**:
```
ModuleNotFoundError: No module named 'src'
```

**Solução**:
```powershell
# Garantir que está no diretório raiz
cd D:\Users\OneDrive - engelar.eng.br\Documentos\Hugo\ENGELAR\agente-bsc-rag

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Executar testes
pytest tests/integration/test_e2e.py -v
```

---

### Problema 6: Judge está rejeitando muitas respostas

**Sintoma**: Approval rate <70%

**Diagnóstico**:
```powershell
# Executar teste específico com output detalhado
pytest tests/integration/test_e2e.py::TestMetrics::test_judge_approval_rate -v -s
```

**Análise**:
- Verificar logs para feedback do Judge
- Identificar padrões de rejeição (completude, fundamentação, fontes)

**Possíveis causas**:
1. Prompts dos agentes precisam de refinamento
2. Retrieval não está recuperando docs suficientes
3. Threshold do Judge muito rígido

**Solução**:
- Revisar prompts em `src/prompts/specialist_prompts.py`
- Ajustar parâmetros de retrieval (top_k, score_threshold)
- Revisar critérios do Judge em `src/prompts/judge_prompt.py`

---

## [EMOJI] Métricas de Sucesso MVP

### Targets Alcançados (14/10/2025)

| Métrica | Target MVP | Atual | Status |
|---------|------------|-------|--------|
| **Latência P50** | <20s | ~12s | [OK] |
| **Latência P95** | <30s | ~19s | [OK] |
| **Cache Speedup** | >10x | 949x | [OK] |
| **Cache Hit Rate** | >80% | 87.5% | [OK] |
| **Judge Approval** | >70% | ~83% | [OK] |
| **Judge Avg Score** | >0.7 | ~0.82 | [OK] |
| **Multilingual Precision** | >50% docs score >0.7 | 80% | [OK] |
| **Paralelização** | <20s para 3+ persp. | ~14s | [OK] |

**Conclusão**: Sistema MVP **100% dentro dos targets** [EMOJI]

---

## [EMOJI] Customizando Testes

### Adicionar Nova Query de Teste

Editar `tests/integration/test_queries.json`:

```json
{
  "factual_queries": [
    {
      "id": "f005",
      "query": "Sua nova query aqui",
      "expected_perspectives": ["financial"],
      "complexity": "simple"
    }
  ]
}
```

### Criar Novo Teste

Editar `tests/integration/test_e2e.py`:

```python
@pytest.mark.asyncio
async def test_meu_caso_especifico(self, workflow):
    """Descrição do teste."""
    query = "Minha query de teste"

    result = await workflow.run(query, session_id="test-custom")

    # Suas assertions aqui
    assert result is not None
    assert "response" in result
```

### Ajustar Thresholds

Se métricas estiverem muito rígidas/flexíveis, ajustar em `test_e2e.py`:

```python
# Latência
assert p95 < 30  # Ajustar para 40 se necessário

# Judge approval rate
assert approval_rate >= 70  # Ajustar para 60 se necessário

# Cache speedup
assert speedup >= 10  # Ajustar para 5 se infra for mais lenta
```

---

## [EMOJI] CI/CD Integration

### GitHub Actions (Exemplo)

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Index dataset
        run: |
          python scripts/build_knowledge_base.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}

      - name: Run E2E tests
        run: |
          pytest tests/integration/test_e2e.py -v --junitxml=report.xml
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: pytest-results
          path: report.xml
```

---

## [EMOJI] Referências

- **Pytest Documentation**: https://docs.pytest.org/
- **Pytest Asyncio**: https://github.com/pytest-dev/pytest-asyncio
- **Testing Best Practices**: https://docs.python-guide.org/writing/tests/
- **LangGraph Testing**: https://python.langchain.com/docs/langgraph/how-tos/test
- **RAG Evaluation**: https://docs.ragas.io/

---

## [EMOJI] Changelog

### 14/10/2025 - v1.0 (Inicial)
- Suite completa de 22 testes E2E
- Cobertura: workflow, performance, Judge, métricas, prerequisites
- Testes de otimizações: cache 949x, multilíngue +106%, paralelização 3.34x
- Documentação completa com troubleshooting

---

**Última atualização**: 14/10/2025
**Versão**: 1.0
**Autor**: Agente BSC RAG Team
