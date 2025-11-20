# [EMOJI] Tutorial Completo - Agente BSC RAG

> Guia passo-a-passo para dominar o sistema BSC RAG: uso básico, avançado, customização e casos práticos

---

## [EMOJI] Índice

- [Parte 1: Usando a Interface Streamlit](#parte-1-usando-a-interface-streamlit)
- [Parte 2: Uso Programático (API)](#parte-2-uso-programático-api)
- [Parte 3: Customização](#parte-3-customização)
- [Parte 4: Análise Avançada](#parte-4-análise-avançada)
- [Parte 5: Casos de Uso Práticos](#parte-5-casos-de-uso-práticos)
- [FAQ](#faq)
- [Glossário BSC](#glossário-bsc)

---

## [EMOJI] Parte 1: Usando a Interface Streamlit

### 1.1 Primeiro Acesso

1. **Iniciar a aplicação**:

```powershell
python run_streamlit.py
```

2. **Acessar interface**: Abra [http://localhost:8501](http://localhost:8501)

3. **Interface inicial**:
   - [EMOJI] Campo de input de query (centro)
   - [EMOJI] Sidebar (esquerda) com configurações
   - [EMOJI] Área de histórico (abaixo do input)

### 1.2 Anatomia da Interface

```
┌──────────────────────────────────────────────────────────────┐
│  SIDEBAR                │  ÁREA PRINCIPAL                    │
│  ┌────────────────┐     │  ┌──────────────────────────────┐ │
│  │ Configurações  │     │  │  [EMOJI] Agente BSC RAG           │ │
│  │                │     │  └──────────────────────────────┘ │
│  │ Perspectivas:  │     │                                   │
│  │ [EMOJI] Financeira   │     │  ┌──────────────────────────────┐│
│  │ [EMOJI] Clientes     │     │  │ Sua pergunta sobre BSC:      ││
│  │ [EMOJI] Processos    │     │  │ [_____________________][Enviar]│
│  │ [EMOJI] Aprendizado  │     │  └──────────────────────────────┘│
│  │                │     │                                   │
│  │ Parâmetros:    │     │  ┌──────────────────────────────┐│
│  │ Top-K: 10      │     │  │  HISTÓRICO                   ││
│  │ Threshold: 0.7 │     │  │  ─────────────               ││
│  │                │     │  │  [Q1] Quais são...           ││
│  └────────────────┘     │  │  [R1] Os principais...       ││
│                          │  │                              ││
│                          │  │  [Q2] Como implementar...    ││
│                          │  │  [R2] Para implementar...    ││
│                          │  └──────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

### 1.3 Fazendo Sua Primeira Query

**Query Simples** (Perspectiva Única):

```
Digite: "Quais são os principais KPIs da perspectiva financeira?"
```

**Resultado esperado** (30-60s):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPOSTA FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Segundo Kaplan & Norton, os principais KPIs da perspectiva
financeira no Balanced Scorecard incluem:

1. **ROI (Return on Investment)**
   - Retorno sobre investimento
   - Mede eficiência na alocação de capital

2. **Crescimento de Receita**
   - Taxa de crescimento ano-a-ano
   - Mix de produtos (% receita de novos produtos)

3. **Produtividade e Redução de Custos**
   - Receita por funcionário
   - Margem operacional
   - Custo unitário

4. **Utilização de Ativos**
   - ROA (Return on Assets)
   - Ciclo de caixa

[...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSPECTIVAS CONSULTADAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Financial (Financeira) - Confidence: 0.92

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FONTES (Top 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] Score: 0.96
    Fonte: The Balanced Scorecard
    Seção: 65
    Conteúdo: "Financial perspective focuses on traditional
              financial metrics such as ROI, revenue growth..."

[2] Score: 0.94
    Fonte: The Strategy-Focused Organization
    Seção: 42
    [...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVALIAÇÃO DO JUDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Score Geral: 0.92 / 1.00 (APROVADO)

Completude:        ████████████████████░ 0.95
Fundamentação:     ██████████████████░░░ 0.91
Citação de Fontes: █████████████████░░░░ 0.89

Feedback: "Resposta abrangente cobrindo os principais KPIs
          financeiros. Bem fundamentada em literatura BSC.
          Estrutura clara e exemplos adequados."

Sugestões:
- Adicionar exemplo numérico de cálculo de ROI
```

### 1.4 Interpretando os Resultados

**1. Resposta Final**:
- [OK] Texto sintetizado combinando insights dos agentes
- [OK] Formatado em Markdown (negrito, listas, etc.)
- [OK] Focado na query do usuário

**2. Perspectivas Consultadas**:
- [EMOJI] Quais agentes BSC foram acionados
- [EMOJI] Confidence score de cada perspectiva (0-1)
- [EMOJI] 1-4 perspectivas dependendo da query

**3. Fontes**:
- [EMOJI] Top 5-10 documentos mais relevantes
- [EMOJI] Score de relevância (0-1, quanto maior melhor)
- [EMOJI] Fonte e seção exatas
- [EMOJI] Preview do conteúdo

**4. Avaliação do Judge**:
- ⭐ Score geral (0-1, threshold padrão: 0.7)
- [OK]/[ERRO] Aprovado ou reprovado
- [EMOJI] Breakdown: Completude, Fundamentação, Citação
- [EMOJI] Feedback textual detalhado
- [EMOJI] Sugestões de melhoria

### 1.5 Queries Complexas (Multi-Perspectiva)

**Exemplo**:

```
"Como a satisfação do cliente impacta a lucratividade da empresa?"
```

**Resultado**:
- [OK] Perspectivas consultadas: **Customer** + **Financial**
- [OK] Resposta sintetizada conectando as duas perspectivas
- [OK] Relação causa-efeito explicada

**Resposta esperada**:

```
A satisfação do cliente impacta a lucratividade através de
múltiplos mecanismos:

1. PERSPECTIVA DE CLIENTES:
   - Clientes satisfeitos têm maior retenção
   - NPS alto gera marketing boca-a-boca
   - Redução de churn (taxa de cancelamento)

2. IMPACTO NA PERSPECTIVA FINANCEIRA:
   - Receita recorrente aumenta (retention)
   - Custo de aquisição (CAC) reduz
   - Lifetime Value (LTV) cresce
   - Margem de lucro melhora

3. CADEIA DE CAUSA E EFEITO:
   Satisfação -> Retenção -> Receita Recorrente -> Lucratividade
```

### 1.6 Configurando Parâmetros na Sidebar

**Perspectivas BSC**:
- [EMOJI] **Financeira**: Marque se query envolve ROI, receita, custos
- [EMOJI] **Clientes**: Marque se envolve satisfação, NPS, retenção
- [EMOJI] **Processos**: Marque se envolve eficiência, qualidade
- [EMOJI] **Aprendizado**: Marque se envolve capacitação, inovação

[EMOJI] **Dica**: Deixe **todas marcadas** para queries gerais. O Orchestrator escolherá automaticamente.

**Parâmetros de Retrieval**:

| Parâmetro | Padrão | Descrição | Quando Ajustar |
|-----------|--------|-----------|----------------|
| **Top-K** | 10 | Documentos a recuperar | Aumente (15-20) se resposta superficial |
| **Threshold** | 0.7 | Score mínimo de relevância | Reduza (0.6) se poucos resultados |
| **Rerank Top-N** | 5 | Docs após re-ranking | Aumente (7-10) para mais diversidade |

**Judge Threshold**:
- [EMOJI] **0.7** (padrão): Balanceado
- [EMOJI] **0.8-0.9**: Mais rigoroso (menos refinamentos)
- [EMOJI] **0.5-0.6**: Mais permissivo (mais refinamentos)

### 1.7 Histórico de Conversação

**Acessar histórico**:
- Scroll down na interface principal
- Histórico é **persistente** por sessão
- Cada query tem timestamp

**Limpar histórico**:
- Recarregar página (Ctrl+R)
- OU clicar em "Clear Chat History" (se disponível na sidebar)

---

## [EMOJI] Parte 2: Uso Programático (API)

### 2.1 Exemplo Básico (Workflow Completo)

```python
from src.graph.workflow import get_workflow

# Inicializar workflow (singleton)
workflow = get_workflow()

# Executar query
result = workflow.run(
    query="Como definir objetivos para a perspectiva financeira?",
    session_id="tutorial-session-001"
)

# Acessar resposta
print("RESPOSTA:")
print(result["final_response"])

# Verificar perspectivas consultadas
print(f"\nPERSPECTIVAS CONSULTADAS: {len(result['perspectives'])}")
for p in result["perspectives"]:
    print(f"  - {p}")

# Verificar aprovação do Judge
judge = result["judge_evaluation"]
if judge["approved"]:
    print(f"\n[OK] Resposta aprovada com score {judge['score']:.2f}")
else:
    print(f"\n[WARN] Resposta reprovada")
    print(f"Issues: {', '.join(judge['issues'])}")
```

**Saída esperada**:

```
RESPOSTA:
Para definir objetivos para a perspectiva financeira no BSC,
Kaplan & Norton recomendam...
[...]

PERSPECTIVAS CONSULTADAS: 1
  - Financial

[OK] Resposta aprovada com score 0.91
```

### 2.2 Acesso Direto a Agentes

**Executar agente específico**:

```python
from src.agents.financial_agent import FinancialAgent

# Inicializar agente
financial_agent = FinancialAgent()

# Invocar (síncrono)
response = financial_agent.invoke(
    "Quais são os melhores KPIs para medir crescimento de receita?"
)

print(f"Confidence: {response['confidence']:.2f}")
print(f"\nResposta:\n{response['response']}")

print(f"\nFontes ({len(response['sources'])}):")
for src in response['sources']:
    print(f"  - {src['source']}, p. {src['page']}: Score {src['score']:.2f}")
```

**Executar múltiplos agentes em paralelo** (AsyncIO):

```python
import asyncio
from src.agents.orchestrator import Orchestrator

async def main():
    orchestrator = Orchestrator()

    # Executar 4 agentes em paralelo
    responses = await orchestrator.ainvoke_agents(
        query="Como implementar BSC na empresa?",
        agents_to_use=["financeira", "cliente", "processos", "aprendizado"]
    )

    for resp in responses:
        print(f"\n{resp['perspective']} (confidence {resp['confidence']:.2f}):")
        print(resp['response'][:200] + "...")

# Executar
asyncio.run(main())
```

**Performance**:
- [FAST] 4 agentes sequencial: ~120s
- [FAST] 4 agentes paralelo (AsyncIO): ~36s
- [FAST] **Speedup: 3.34x**

### 2.3 Busca RAG Direta

**Sem agentes, apenas retrieval**:

```python
from src.rag.retriever import BSCRetriever

# Inicializar retriever
retriever = BSCRetriever()

# Busca multilíngue (PT-BR query, docs EN)
results = retriever.retrieve(
    query="Quais são os objetivos da perspectiva de processos?",
    top_k=10,
    threshold=0.7,
    multilingual=True  # Query expansion PT-BR <-> EN
)

# Processar resultados
print(f"Encontrados {len(results)} documentos relevantes:\n")

for i, result in enumerate(results, 1):
    print(f"[{i}] Score: {result['score']:.3f}")
    print(f"    Fonte: {result['source']}, Seção {result['page']}")
    print(f"    Conteúdo: {result['content'][:150]}...")
    print()
```

**Saída esperada**:

```
Encontrados 10 documentos relevantes:

[1] Score: 0.984
    Fonte: The Balanced Scorecard, Seção 78
    Conteúdo: Process objectives focus on operational excellence,
              innovation, and regulatory compliance...

[2] Score: 0.961
    Fonte: The Strategy-Focused Organization, Seção 92
    [...]
```

### 2.4 Integração com Aplicação Externa

**Exemplo: API FastAPI**:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.graph.workflow import get_workflow

app = FastAPI()
workflow = get_workflow()

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    max_iterations: int = 2

class QueryResponse(BaseModel):
    final_response: str
    perspectives: list
    judge_score: float
    approved: bool

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        result = workflow.run(
            query=request.query,
            session_id=request.session_id,
            max_iterations=request.max_iterations
        )

        return QueryResponse(
            final_response=result["final_response"],
            perspectives=result["perspectives"],
            judge_score=result["judge_evaluation"]["score"],
            approved=result["judge_evaluation"]["approved"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Executar: uvicorn api:app --reload
```

**Testar API**:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "O que é Balanced Scorecard?", "session_id": "api-test-001"}'
```

---

## [EMOJI] Parte 3: Customização

### 3.1 Adicionar Novos Documentos BSC

**Passo 1: Adicionar arquivos**:

```bash
# Copiar PDFs ou Markdowns para:
cp seu-documento-bsc.pdf data/bsc_literature/
cp outro-documento.md data/bsc_literature/
```

**Formatos suportados**:
- [OK] `.md` (Markdown)
- [OK] `.pdf` (PDF)
- [OK] `.txt` (Texto plano)
- [OK] `.docx` (Word) - experimental

**Passo 2: Reindexar**:

```bash
python scripts/build_knowledge_base.py
```

**Saída**:

```
[INFO] Encontrados 7 documentos (5 antigos + 2 novos)
[INFO] Processando novos documentos...
[PROGRESS] Processando seu-documento-bsc.pdf... OK
[PROGRESS] Processando outro-documento.md... OK
[STATS] 9.234 chunks totais indexados (+1.269 novos)
[OK] Knowledge base atualizada!
```

[EMOJI] **Dica**: Cache otimizado reutiliza chunks já processados (apenas processa documentos novos).

### 3.2 Modificar Prompts de Agentes

**Localização**: `src/prompts/specialist_prompts.py`

**Exemplo: Customizar Financial Agent**:

```python
# src/prompts/specialist_prompts.py

FINANCIAL_AGENT_PROMPT = """Você é um especialista em Perspectiva Financeira do BSC.

Sua expertise inclui:
- ROI, crescimento de receita, lucratividade
- Produtividade, redução de custos
- Valor para acionistas, mix de produtos

[CUSTOMIZAÇÃO AQUI]
Foco especial em empresas de tecnologia (SaaS):
- MRR (Monthly Recurring Revenue)
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Churn rate

Quando responder, sempre priorize métricas SaaS quando aplicável.
"""
```

**Reload**: Reinicie a aplicação para aplicar mudanças.

### 3.3 Ajustar Thresholds do Judge

**Localização**: `.env`

```env
# Judge mais rigoroso (menos refinamentos)
JUDGE_THRESHOLD=0.85

# Judge mais permissivo (mais refinamentos)
JUDGE_THRESHOLD=0.60
```

**OU programaticamente**:

```python
result = workflow.run(
    query="...",
    judge_threshold=0.85  # Sobrescreve .env
)
```

### 3.4 Customizar Perspectivas BSC

**Adicionar 5ª perspectiva** (exemplo: Sustentabilidade):

**Passo 1: Criar novo agente**:

```python
# src/agents/sustainability_agent.py

from src.agents.base_agent import BaseAgent

class SustainabilityAgent(BaseAgent):
    """Agente para perspectiva de Sustentabilidade."""

    def __init__(self):
        super().__init__(
            name="Sustainability Agent",
            perspective="Sustainability",
            system_prompt="""Você é especialista em Sustentabilidade no BSC.

            Foco em:
            - Impacto ambiental (carbon footprint, energia renovável)
            - Responsabilidade social (diversidade, inclusão)
            - Governança (ESG, compliance)
            """
        )
```

**Passo 2: Registrar no Orchestrator**:

```python
# src/agents/orchestrator.py

from src.agents.sustainability_agent import SustainabilityAgent

class Orchestrator:
    def __init__(self):
        self.agents = {
            "financeira": FinancialAgent(),
            "cliente": CustomerAgent(),
            "processos": ProcessAgent(),
            "aprendizado": LearningAgent(),
            "sustentabilidade": SustainabilityAgent()  # NOVO
        }
```

**Passo 3: Atualizar routing prompt**:

```python
# src/agents/orchestrator.py - _create_routing_prompt()

template = """...
**Agentes Disponíveis:**
- financeira: ...
- cliente: ...
- processos: ...
- aprendizado: ...
- sustentabilidade: Impacto ambiental, ESG, responsabilidade social  # NOVO
"""
```

**Passo 4: Testar**:

```python
result = workflow.run("Como integrar ESG no BSC?")
print(result["perspectives"])  # Deve incluir "Sustainability"
```

### 3.5 Configurar Cache de Embeddings

**Aumentar tamanho do cache**:

```env
# .env
EMBEDDING_CACHE_SIZE_GB=20  # Padrão: 5 GB
EMBEDDING_CACHE_TTL_DAYS=90  # Padrão: 30 dias
```

**Limpar cache manualmente**:

```bash
rm -rf .cache/embeddings/*
```

**Estatísticas do cache**:

```python
from src.rag.embeddings import EmbeddingManager

manager = EmbeddingManager()
stats = manager.get_cache_stats()

print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit Rate: {stats['hit_rate']:.1%}")
print(f"Tamanho: {stats['size_mb']:.2f} MB")
```

---

## [EMOJI] Parte 4: Análise Avançada

### 4.1 Interpretar Métricas E2E

**Executar testes E2E**:

```bash
pytest tests/integration/test_e2e.py::TestMetrics -v
```

**Métricas coletadas**:

```python
# tests/integration/test_e2e.py - test_latency_percentiles

RESULTADOS:
┌──────────┬──────────┬───────────┐
│ Métrica  │ Valor    │ Threshold │
├──────────┼──────────┼───────────┤
│ P50      │ 71.2s    │ <90s      │
│ P95      │ 122.4s   │ <180s     │
│ P99      │ 122.4s   │ <180s     │
│ Mean     │ 79.8s    │ -         │
└──────────┴──────────┴───────────┘
```

**Interpretação**:

- **P50 (Mediana)**: 50% das queries respondem em <71s
- **P95**: 95% das queries respondem em <122s
- **P99**: 99% respondem em <122s
- [OK] **Todas abaixo dos thresholds** = Performance OK

**Se P95 > 180s**: Investigar gargalos (cache, API externa, paralelização).

### 4.2 Otimizar Performance

**Problema: Latência alta**

**Diagnóstico**:

```python
import time

# Medir tempo de cada etapa
start = time.time()

# 1. Retrieval
results = retriever.retrieve(query, top_k=10)
retrieval_time = time.time() - start
print(f"Retrieval: {retrieval_time:.2f}s")

# 2. Agentes
start = time.time()
responses = await orchestrator.ainvoke_agents(query, agents_to_use)
agents_time = time.time() - start
print(f"Agentes (paralelo): {agents_time:.2f}s")

# 3. Synthesis
start = time.time()
synthesis = orchestrator.synthesize_response(query, responses)
synthesis_time = time.time() - start
print(f"Synthesis: {synthesis_time:.2f}s")
```

**Soluções**:

| Gargalo | Solução | Ganho Esperado |
|---------|---------|----------------|
| Embeddings | Ativar cache (`ENABLE_EMBEDDING_CACHE=true`) | 949x speedup |
| Agentes | Usar `ainvoke_agents()` (AsyncIO) | 3.34x speedup |
| Retrieval | Reduzir `top_k` (10 -> 5) | -20% latência |
| Re-ranking | Reduzir `rerank_top_n` (5 -> 3) | -15% latência |
| API calls | Upgrade tier OpenAI/Anthropic | -30% latência |

### 4.3 Debug de Queries Problemáticas

**Query retorna "Não encontrei informações relevantes"**:

**Diagnóstico**:

```python
# 1. Verificar retrieval
results = retriever.retrieve(query, top_k=10, threshold=0.5)  # Threshold baixo
print(f"Encontrados {len(results)} docs")

if len(results) == 0:
    print("[PROBLEMA] Nenhum doc encontrado. Possíveis causas:")
    print("  - Query muito específica (não há info no dataset)")
    print("  - Threshold muito alto")
    print("  - Problema com embeddings")
else:
    print("Top 3 scores:")
    for r in results[:3]:
        print(f"  - {r['score']:.3f}: {r['content'][:100]}")
```

**Soluções**:

1. **Reduzir threshold**: `threshold=0.5` (vs 0.7 padrão)
2. **Aumentar top_k**: `top_k=20` (vs 10 padrão)
3. **Reformular query**: "Quais KPIs..." -> "KPIs da perspectiva financeira segundo Kaplan"
4. **Adicionar documentos**: Dataset pode não cobrir o tópico

**Query retorna resposta reprovada pelo Judge**:

```python
# Ver feedback detalhado do Judge
result = workflow.run(query)
judge = result["judge_evaluation"]

if not judge["approved"]:
    print(f"Score: {judge['score']:.2f}")
    print(f"\nIssues:")
    for issue in judge["issues"]:
        print(f"  - {issue}")

    print(f"\nSugestões:")
    for suggestion in judge["suggestions"]:
        print(f"  - {suggestion}")
```

**Ações**:

- [EMOJI] Refinar query baseado em sugestões
- [EMOJI] Reduzir `judge_threshold` se muito rigoroso
- [EMOJI] Adicionar documentos mais específicos ao dataset

---

## [EMOJI] Parte 5: Casos de Uso Práticos

### Caso 1: Análise Financeira de BSC

**Contexto**: Você está consultando um cliente sobre KPIs financeiros.

**Query 1: Identificar KPIs**:

```
"Quais KPIs da perspectiva financeira são mais adequados para uma
empresa de tecnologia SaaS?"
```

**Resultado esperado**:
- MRR (Monthly Recurring Revenue)
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Churn rate
- Rule of 40 (crescimento% + margem%)

**Query 2: Relação com outras perspectivas**:

```
"Como os KPIs de satisfação do cliente (NPS) impactam o churn rate
e consequentemente o MRR?"
```

**Resultado esperado**:
- Perspectivas consultadas: Customer + Financial
- Cadeia causa-efeito: NPS ↑ -> Churn ↓ -> MRR ↑

**Query 3: Benchmarking**:

```
"Quais são os benchmarks de CAC e LTV para empresas SaaS segundo
melhores práticas BSC?"
```

---

### Caso 2: Planejamento Estratégico

**Contexto**: Definir objetivos BSC para empresa de manufatura.

**Workflow**:

1. **Objetivo Financeiro**:

```
"Quais objetivos financeiros são típicos para empresas de manufatura
no BSC?"
```

2. **Cascateamento para Clientes**:

```
"Como objetivos de crescimento de receita se traduzem em objetivos
da perspectiva de clientes?"
```

3. **Processos Internos**:

```
"Quais processos internos suportam melhoria de satisfação do cliente
em manufatura?"
```

4. **Aprendizado e Crescimento**:

```
"Que capacidades organizacionais são necessárias para melhorar
processos de manufatura?"
```

**Resultado**: Mapa estratégico completo (4 perspectivas conectadas).

---

### Caso 3: Design de KPIs

**Contexto**: Criar KPIs personalizados para perspectiva de processos.

**Query 1: Exemplos de KPIs**:

```
"Quais são os KPIs típicos da perspectiva de processos internos
segundo Kaplan & Norton?"
```

**Query 2: Critérios de bons KPIs**:

```
"Quais critérios tornam um KPI efetivo no BSC?"
```

**Resultado esperado**:
- Alinhado com estratégia
- Mensurável e quantificável
- Acionável (influenciável pela equipe)
- Relevante para objetivo

**Query 3: Customização para indústria**:

```
"Como adaptar KPIs de processos para uma empresa de logística?"
```

---

### Caso 4: Implementação de BSC Completo

**Passo-a-passo**:

**1. Entender Metodologia**:

```python
queries = [
    "O que é Balanced Scorecard?",
    "Quais são as 4 perspectivas do BSC?",
    "Como funciona o processo de implementação de BSC?"
]

for query in queries:
    result = workflow.run(query)
    print(f"\n{'='*60}")
    print(f"Q: {query}")
    print(f"{'='*60}")
    print(result["final_response"])
```

**2. Definir Visão e Estratégia**:

```
"Como traduzir a visão da empresa em objetivos BSC nas 4 perspectivas?"
```

**3. Criar Mapa Estratégico**:

```
"Como construir um mapa estratégico BSC mostrando relações
causa-efeito entre objetivos?"
```

**4. Selecionar KPIs**:

```
"Como escolher indicadores (KPIs) adequados para cada objetivo BSC?"
```

**5. Definir Metas e Iniciativas**:

```
"Como estabelecer metas SMART para KPIs do BSC?"
```

**6. Cascatear para Níveis Organizacionais**:

```
"Como cascatear o BSC corporativo para unidades de negócio e departamentos?"
```

---

### Caso 5: Consultoria BSC

**Contexto**: Você é consultor e cliente pediu análise do BSC atual.

**Script Automatizado**:

```python
from src.graph.workflow import get_workflow

workflow = get_workflow()

# Questionário de diagnóstico
diagnostic_queries = [
    "Quais são os elementos essenciais de um BSC bem implementado?",
    "Quais erros comuns na implementação de BSC?",
    "Como garantir alinhamento estratégico no BSC?",
    "Como integrar BSC com orçamento e planejamento?",
    "Quais ferramentas de suporte para gestão de BSC?"
]

print("RELATÓRIO DE DIAGNÓSTICO BSC\n")
print("="*60)

for i, query in enumerate(diagnostic_queries, 1):
    result = workflow.run(query, session_id=f"diagnostic-{i}")

    print(f"\n{i}. {query}")
    print("-" * 60)
    print(result["final_response"][:500] + "...\n")
    print(f"Score do Judge: {result['judge_evaluation']['score']:.2f}")
    print("="*60)

print("\n[OK] Relatório completo gerado!")
```

---

## [?] FAQ

### Q1: Como melhorar a precisão das respostas?

**A**:
1. [OK] Adicione documentos mais específicos ao dataset
2. [OK] Reformule queries de forma mais clara
3. [OK] Aumente `top_k` (10 -> 15)
4. [OK] Ative busca multilíngue (`ENABLE_MULTILINGUAL_SEARCH=true`)
5. [OK] Use queries completas vs fragmentadas

### Q2: Sistema está lento. Como otimizar?

**A**:
1. [FAST] Ative cache de embeddings (`ENABLE_EMBEDDING_CACHE=true`)
2. [FAST] Use AsyncIO para agentes (`ainvoke_agents()`)
3. [FAST] Reduza `top_k` (10 -> 5) se aceitável
4. [FAST] Upgrade tier das APIs (OpenAI/Anthropic tier 2+)
5. [FAST] Use servidor com mais CPU cores (4 -> 8)

### Q3: Judge reprova muitas respostas. O que fazer?

**A**:
1. [EMOJI] Reduzir `JUDGE_THRESHOLD` (0.7 -> 0.6)
2. [EMOJI] Adicionar documentos mais relevantes
3. [EMOJI] Melhorar clareza das queries
4. [EMOJI] Verificar se perspectivas corretas foram acionadas

### Q4: Como adicionar suporte a outro idioma?

**A**: Sistema já suporta **busca multilíngue PT-BR <-> EN**. Para adicionar outro idioma (ex: ES):

1. Atualizar `src/rag/query_translator.py`:

```python
def translate(self, query, source_lang="auto", target_lang="en"):
    # Adicionar suporte a ES
    if target_lang == "es":
        prompt = f"Translate to Spanish: {query}"
    # ...
```

2. Adicionar documentos em espanhol ao dataset
3. Contextual chunker criará contextos ES automaticamente

### Q5: Posso usar outro LLM além de Claude/GPT?

**A**: Sim! Edite `config/settings.py`:

```python
def get_llm(temperature=0.7):
    # Exemplo: Usar LLaMA local
    from langchain_community.llms import Ollama
    return Ollama(model="llama3:70b", temperature=temperature)
```

Modelos suportados:
- [OK] Claude (Anthropic)
- [OK] GPT-4/5 (OpenAI)
- [OK] LLaMA (local via Ollama)
- [OK] Mistral (local ou API)
- [OK] Gemini (Google - experimental)

### Q6: Como integrar com ferramentas BI (Power BI, Tableau)?

**A**: Crie API REST (FastAPI) e conecte via conector HTTP:

```python
# api.py
@app.post("/query")
async def query_bsc(query: str):
    result = workflow.run(query)
    return {
        "response": result["final_response"],
        "score": result["judge_evaluation"]["score"],
        "perspectives": result["perspectives"]
    }
```

**Power BI**: Web.Contents() -> JSON parsing
**Tableau**: Web Data Connector (WDC)

### Q7: Sistema funciona offline?

**A**: **Parcialmente**:
- [ERRO] LLMs (Claude/GPT): **Requerem internet** (API externas)
- [OK] Qdrant: **Funciona offline** (local)
- [OK] Cache embeddings: **Funciona offline** (disco local)
- [WARN] Query translation: Requer internet (GPT-5 mini)

**Para 100% offline**: Use LLaMA local (Ollama) + embeddings locais.

### Q8: Como exportar resultados para PDF/Word?

**A**: Use bibliotecas Python:

```python
from fpdf import FPDF

result = workflow.run("O que é BSC?")

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, result["final_response"])
pdf.output("bsc_response.pdf")
```

**Word (docx)**:

```python
from docx import Document

doc = Document()
doc.add_heading("Resposta BSC", 0)
doc.add_paragraph(result["final_response"])
doc.save("bsc_response.docx")
```

---

## [EMOJI] Glossário BSC

| Termo | Definição |
|-------|-----------|
| **BSC (Balanced Scorecard)** | Metodologia de gestão estratégica criada por Kaplan & Norton |
| **Perspectiva Financeira** | Foco em ROI, receita, lucratividade, valor acionista |
| **Perspectiva de Clientes** | Foco em satisfação, retenção, proposta de valor |
| **Perspectiva de Processos** | Foco em eficiência operacional, qualidade, inovação |
| **Perspectiva de Aprendizado** | Foco em capacitação, cultura, sistemas de informação |
| **KPI (Key Performance Indicator)** | Indicador-chave de desempenho |
| **Mapa Estratégico (Strategy Map)** | Diagrama visual de objetivos BSC e relações causa-efeito |
| **Iniciativa Estratégica** | Projeto ou programa para atingir objetivo BSC |
| **Target (Meta)** | Valor alvo para um KPI |
| **Cascateamento** | Desdobramento do BSC corporativo para níveis inferiores |
| **Judge Agent** | Agente de IA que valida qualidade das respostas (LLM as Judge) |
| **RAG (Retrieval Augmented Generation)** | Geração aumentada por recuperação de documentos |
| **Hybrid Search** | Combinação de busca semântica + lexical (BM25) |
| **Re-ranking** | Reordenação de resultados por relevância (Cohere) |
| **Query Expansion** | Expansão multilíngue de queries (PT-BR <-> EN) |
| **RRF (Reciprocal Rank Fusion)** | Fusão de rankings de múltiplas queries |

---

## [EMOJI] Suporte

Para mais ajuda:

- [EMOJI] [README.md](../README.md) - Overview do projeto
- [EMOJI] [QUICKSTART.md](QUICKSTART.md) - Guia de instalação
- [EMOJI] [API_REFERENCE.md](API_REFERENCE.md) - Referência técnica
- [EMOJI] [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy em produção
- [EMOJI] [Issues](https://github.com/seu-usuario/agente-bsc-rag/issues) - Reportar bugs

---

<p align="center">
  <strong>[EMOJI] Tutorial Completo v1.0</strong><br>
  <em>Agente BSC RAG - MVP Out/2025</em>
</p>
